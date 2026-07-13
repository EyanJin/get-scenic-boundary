"""
OSM data source — query OpenStreetMap via Overpass API.
OSM 数据源 — 通过 Overpass API 查询 OpenStreetMap

No API key required. Returns WGS84 coordinates natively.
"""
import json
import re
import time
import urllib.request
import urllib.parse

from geoboundary.config import OVERPASS_URL, USER_AGENT, REQUEST_DELAY


def query(name, radius_km=20, timeout=30):
    """Query OSM for a place boundary by name.
    通过名称查询 OSM 边界

    Strategy:
      1. Search by name tag with boundary/leisure/tourism filters
      2. If center coordinates provided, do proximity search

    Args:
        name: place name (Chinese or English)
        radius_km: search radius for proximity queries (km)
        timeout: Overpass API timeout (seconds)

    Returns:
        dict with 'geometry' (GeoJSON dict) and metadata, or None
    """
    # Try name-based search first
    result = _search_by_name(name, timeout)
    if result:
        return result
    return None


def query_nearby(name, lat, lng, radius_km=20, timeout=30):
    """Query OSM for a place boundary near given coordinates.
    在指定坐标附近查询 OSM 边界

    Args:
        name: place name for validation
        lat, lng: center point (WGS84)
        radius_km: search radius
        timeout: Overpass API timeout

    Returns:
        dict with 'geometry' (GeoJSON dict) and metadata, or None
    """
    radius_m = radius_km * 1000
    core = _extract_core_name(name)

    ql = f'''[out:json][timeout:{timeout}];
(
  way["boundary"~"protected_area|national_park"](around:{radius_m},{lat},{lng});
  way["leisure"~"nature_reserve"](around:{radius_m},{lat},{lng});
  way["tourism"="attraction"]["name"](around:{int(radius_m/2)},{lat},{lng});
  relation["boundary"~"protected_area|national_park"](around:{radius_m},{lat},{lng});
  relation["leisure"~"nature_reserve"](around:{radius_m},{lat},{lng});
);
out geom;'''

    elements = _overpass_query(ql)
    if not elements:
        return None

    # Find best name match among results
    best = None
    best_score = 0
    for elem in elements:
        elem_name = elem.get('tags', {}).get('name', '')
        if not elem_name:
            continue
        score = _name_similarity(name, elem_name)
        if score == 0 and core and len(core) >= 2:
            elem_core = _extract_core_name(elem_name)
            if core == elem_core:
                score = 1.0
            elif core in elem_core:
                score = 0.85
        if score > best_score:
            best_score = score
            best = elem

    if best and best_score >= 0.7:
        geojson = _element_to_geojson(best)
        if geojson:
            return {
                'geometry': geojson,
                'name': best.get('tags', {}).get('name', ''),
                'osm_type': best['type'],
                'osm_id': best['id'],
                'match_score': best_score,
                'source': 'osm',
                'crs': 'wgs84',
            }
    return None


def _search_by_name(name, timeout=30):
    """Search Overpass by name tags."""
    core = _extract_core_name(name)
    search_term = _escape_overpass_regex(core if core else name)

    ql = f'''[out:json][timeout:{timeout}];
(
  way["name"~"{search_term}"]["boundary"~"protected_area|national_park"](18,73,54,135);
  way["name"~"{search_term}"]["leisure"~"nature_reserve|park"](18,73,54,135);
  way["name"~"{search_term}"]["tourism"~"attraction|theme_park"](18,73,54,135);
  relation["name"~"{search_term}"]["boundary"~"protected_area|national_park"](18,73,54,135);
  relation["name"~"{search_term}"]["leisure"~"nature_reserve|park"](18,73,54,135);
  relation["name"~"{search_term}"]["tourism"~"attraction|theme_park"](18,73,54,135);
);
out geom;'''

    elements = _overpass_query(ql)
    if not elements:
        return None

    # Find best match
    best = None
    best_score = 0
    for elem in elements:
        for tag_key in ['name', 'name:zh', 'alt_name']:
            elem_name = elem.get('tags', {}).get(tag_key, '')
            if not elem_name:
                continue
            score = _name_similarity(name, elem_name)
            if score > best_score:
                best_score = score
                best = elem

    if best and best_score >= 0.9:
        geojson = _element_to_geojson(best)
        if geojson:
            return {
                'geometry': geojson,
                'name': best.get('tags', {}).get('name', ''),
                'osm_type': best['type'],
                'osm_id': best['id'],
                'match_score': best_score,
                'source': 'osm',
                'crs': 'wgs84',
            }
    return None


def _overpass_query(ql):
    """Execute an Overpass QL query and return elements."""
    data = urllib.parse.urlencode({'data': ql}).encode('utf-8')
    req = urllib.request.Request(OVERPASS_URL, data=data)
    req.add_header('User-Agent', USER_AGENT)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        return result.get('elements', [])
    except Exception:
        return []


# ========== Geometry conversion ==========

def _element_to_geojson(element):
    """Convert OSM element to GeoJSON geometry."""
    if element['type'] == 'way':
        return _way_to_geojson(element)
    elif element['type'] == 'relation':
        return _relation_to_geojson(element)
    return None


def _way_to_geojson(element):
    """Convert OSM way to GeoJSON Polygon."""
    geometry = element.get('geometry', [])
    if not geometry:
        return None
    coords = [(node['lon'], node['lat']) for node in geometry]
    if len(coords) < 3:
        return None
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return {'type': 'Polygon', 'coordinates': [coords]}


def _relation_to_geojson(element):
    """Convert OSM relation to GeoJSON Polygon/MultiPolygon."""
    members = element.get('members', [])
    if not members:
        return None

    outer_rings = []
    inner_rings = []

    for member in members:
        if member.get('type') != 'way':
            continue
        role = member.get('role', '')
        geometry = member.get('geometry', [])
        if not geometry:
            continue
        coords = [(node['lon'], node['lat']) for node in geometry]
        if len(coords) < 3:
            continue
        if role == 'inner':
            inner_rings.append(coords)
        else:
            outer_rings.append(coords)

    if not outer_rings:
        return None

    merged_outer = _merge_way_segments(outer_rings)

    if len(merged_outer) == 1:
        rings = [merged_outer[0]]
        for inner in inner_rings:
            if inner[0] != inner[-1]:
                inner.append(inner[0])
            rings.append(inner)
        return {'type': 'Polygon', 'coordinates': rings}
    else:
        polygons = []
        for outer in merged_outer:
            polygons.append([outer])
        if inner_rings and polygons:
            for inner in inner_rings:
                if inner[0] != inner[-1]:
                    inner.append(inner[0])
                polygons[0].append(inner)
        return {'type': 'MultiPolygon', 'coordinates': polygons}


def _merge_way_segments(segments):
    """Merge disconnected way segments into closed rings."""
    if not segments:
        return []
    if len(segments) == 1:
        ring = segments[0]
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        return [ring]

    merged = []
    remaining = list(segments)
    current = remaining.pop(0)

    max_iter = len(remaining) * len(remaining)
    iter_count = 0
    while remaining and iter_count < max_iter:
        iter_count += 1
        found = False
        for i, seg in enumerate(remaining):
            if current[-1] == seg[0]:
                current = current + seg[1:]
                remaining.pop(i)
                found = True
                break
            elif current[-1] == seg[-1]:
                current = current + list(reversed(seg))[1:]
                remaining.pop(i)
                found = True
                break
            elif current[0] == seg[-1]:
                current = seg + current[1:]
                remaining.pop(i)
                found = True
                break
            elif current[0] == seg[0]:
                current = list(reversed(seg)) + current[1:]
                remaining.pop(i)
                found = True
                break

        if not found:
            if current[0] != current[-1]:
                current.append(current[0])
            merged.append(current)
            if remaining:
                current = remaining.pop(0)
            break

    if current:
        if current[0] != current[-1]:
            current.append(current[0])
        merged.append(current)

    for seg in remaining:
        if len(seg) >= 3:
            if seg[0] != seg[-1]:
                seg.append(seg[0])
            merged.append(seg)

    return merged


# ========== Name matching ==========

def _escape_overpass_regex(s):
    """Escape special regex characters for Overpass QL queries.
    防止用户输入注入 Overpass QL 命令
    """
    # Escape regex special chars and Overpass QL quote
    return re.sub(r'([.+?*\[\](){}^$|\\"])', r'\\\1', s)


def _extract_core_name(name):
    """Extract core place name by removing common affixes."""
    name = re.sub(r'^[\u4e00-\u9fff]{2,4}(省|市|县|区|州|地区)', '', name)
    for suffix in ['国家级风景名胜区', '风景名胜区', '风景区', '景区', '名胜区',
                   '旅游区', '旅游风景区', '自然保护区', '国家公园', '地质公园',
                   '水利风景区', '森林公园']:
        name = name.replace(suffix, '')
    for sep in ['—', '-', '·', '～', '、', '─']:
        if sep in name:
            name = name.split(sep)[0]
    return name.strip()


def _name_similarity(name1, name2):
    """Calculate name similarity score (0-1), strict mode."""
    core1 = _extract_core_name(name1)
    core2 = _extract_core_name(name2)

    if not core1 or not core2:
        return 0

    if core1 == core2:
        return 1.0

    if len(core1) >= 3 and core1 in core2:
        return 0.9
    if len(core2) >= 3 and core2 in core1:
        return 0.9

    return 0
