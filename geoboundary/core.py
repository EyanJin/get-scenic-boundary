"""
Core orchestration module — multi-source boundary query with fallback.
核心编排模块 — 多源查询 + 降级策略
"""
import os
import json

from geoboundary.geometry import (
    parse_baidu_geo, rings_to_geometry, geojson_to_geometry, transform_geometry
)
from geoboundary.coord_transform import (
    bd09mc_to_wgs84, bd09mc_to_gcj02, gcj02_to_wgs84, wgs84_to_gcj02
)
from geoboundary.export import to_geojson_feature


def get_boundary(name, source='auto', crs='wgs84', province=''):
    """Get boundary polygon for a place name.
    获取地名的边界多边形

    Args:
        name: place name (地名)
        source: data source — 'auto' | 'osm' | 'baidu' | 'amap' | 'nominatim'
        crs: output coordinate system — 'wgs84' | 'gcj02'
        province: province hint for disambiguation (省份提示)

    Returns:
        GeoJSON Feature dict, or None if no boundary found

    Example:
        >>> from geoboundary import get_boundary
        >>> result = get_boundary("西湖风景名胜区")
        >>> result['geometry']['type']
        'Polygon'
    """
    if source == 'auto':
        # Priority: Baidu (best Chinese coverage ~95%) → Amap → OSM
        # This matches proven coverage hierarchy from real-world testing.
        # Baidu requires Playwright; if unavailable, falls through to Amap/OSM.
        sources = ['baidu', 'amap', 'osm']
    else:
        sources = [source]

    for src_name in sources:
        result = _query_source(src_name, name, province)
        if result:
            geometry = _extract_geometry(result)
            if geometry and _validate_geometry(geometry):
                geometry = _transform_to_crs(geometry, result.get('crs', 'wgs84'), crs)
                properties = {
                    'name': result.get('name', name),
                    'source': result.get('source', src_name),
                    'query': name,
                }
                if result.get('osm_id'):
                    properties['osm_id'] = result['osm_id']
                if result.get('uid'):
                    properties['uid'] = result['uid']
                if result.get('poi_id'):
                    properties['poi_id'] = result['poi_id']
                return to_geojson_feature(geometry, properties)

    return None


def batch_query(names, source='auto', crs='wgs84', output_dir=None, progress=True, resume=True):
    """Query boundaries for multiple place names.
    批量查询多个地名的边界

    Args:
        names: list of place names, or list of dicts with 'name' and 'province'
        source: data source
        crs: output coordinate system
        output_dir: if provided, save individual GeoJSON files + merged output
        progress: print progress to stdout
        resume: skip names that already have output files in output_dir

    Returns:
        list of (name, GeoJSON Feature or None) tuples
    """
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    results = []
    total = len(names)
    found_count = 0
    skipped_count = 0

    for i, item in enumerate(names):
        if isinstance(item, dict):
            name = item['name']
            province = item.get('province', '')
        else:
            name = item
            province = ''

        # Resume: skip if output file already exists
        if resume and output_dir:
            safe_name = name.replace('/', '_').replace('\\', '_')[:50]
            existing_path = os.path.join(output_dir, f'{safe_name}.geojson')
            if os.path.exists(existing_path):
                try:
                    with open(existing_path, 'r', encoding='utf-8') as f:
                        cached = json.load(f)
                    results.append((name, cached))
                    skipped_count += 1
                    if cached:
                        found_count += 1
                    if progress:
                        print(f'[{i+1}/{total}] {name} ... skipped (cached)')
                    continue
                except (json.JSONDecodeError, IOError):
                    pass  # Re-query if file is corrupted

        if progress:
            print(f'[{i+1}/{total}] {name} ...', end=' ', flush=True)

        feature = get_boundary(name, source=source, crs=crs, province=province)

        if feature:
            found_count += 1
            if progress:
                print(f'OK ({feature["geometry"]["type"]})')
        elif progress:
            print('not found')

        results.append((name, feature))

        # Save individual file (also serves as checkpoint for resume)
        if output_dir:
            safe_name = name.replace('/', '_').replace('\\', '_')[:50]
            filepath = os.path.join(output_dir, f'{safe_name}.geojson')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(feature, f, ensure_ascii=False, indent=2)

    # Generate merged output + report
    if output_dir:
        _write_merged_output(results, output_dir, crs)
        _write_batch_report(results, output_dir, source, skipped_count)

    return results


def _write_merged_output(results, output_dir, crs):
    """Write a merged GeoJSON FeatureCollection from batch results."""
    features = []
    for name, feature in results:
        if feature:
            features.append(feature)

    if not features:
        return

    fc = {
        'type': 'FeatureCollection',
        'features': features,
    }

    merged_path = os.path.join(output_dir, '_merged.geojson')
    with open(merged_path, 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False)
    print(f"\nMerged: {merged_path} ({len(features)} features)")


def _write_batch_report(results, output_dir, source, skipped_count):
    """Write a batch processing report."""
    import os

    total = len(results)
    found = sum(1 for _, f in results if f)
    not_found = total - found

    report_path = os.path.join(output_dir, '_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("geoboundary Batch Query Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total: {total}\n")
        f.write(f"Found: {found} ({found/total*100:.1f}%)\n")
        f.write(f"Not found: {not_found}\n")
        f.write(f"Skipped (cached): {skipped_count}\n")
        f.write(f"Source: {source}\n\n")

        if not_found > 0:
            f.write("--- Not found ---\n")
            for name, feat in results:
                if not feat:
                    f.write(f"  {name}\n")

    print(f"Report: {report_path}")


def _query_source(source_name, name, province=''):
    """Dispatch query to the specified source."""
    try:
        if source_name == 'osm':
            from geoboundary.sources import osm
            return osm.query(name)
        elif source_name == 'baidu':
            from geoboundary.sources import baidu
            return baidu.query(name, province=province)
        elif source_name == 'amap':
            from geoboundary.sources import amap
            return amap.query(name, province=province)
        elif source_name == 'nominatim':
            from geoboundary.sources import nominatim
            return nominatim.query(name)
    except ImportError:
        return None
    except Exception:
        return None
    return None


def _extract_geometry(result):
    """Extract Shapely geometry from a source result."""
    if not result:
        return None

    # OSM/Amap/Nominatim: GeoJSON geometry dict
    if 'geometry' in result and isinstance(result['geometry'], dict):
        return geojson_to_geometry(result['geometry'])

    # Baidu: raw geo string
    if 'geo_str' in result:
        geo_type, geo_data = parse_baidu_geo(result['geo_str'])
        if geo_type == 'polygon' and geo_data:
            # Keep in BD-09 MC for now, transform later
            return rings_to_geometry(geo_data, lambda x, y: (x, y))

    return None


def _validate_geometry(geometry):
    """Validate that a geometry is reasonable (not too small or too large).
    验证几何体面积合理性

    Rejects:
      - Area < 0.01 km² (likely a point or parsing error)
      - Area > 100,000 km² (likely wrong boundary or parsing error)

    Note: area is approximated using degree-to-km conversion at mid-latitudes.
    For geometries still in BD-09 MC (Mercator meters), skip validation
    (they will be validated after coordinate transform).
    """
    if geometry.is_empty:
        return False

    bounds = geometry.bounds  # (minx, miny, maxx, maxy)

    # Detect BD-09 MC coordinates (values in millions) — skip area check,
    # will be validated after transform
    if bounds[0] > 1000000 or bounds[2] > 1000000:
        return True

    # For degree-based coordinates (WGS84/GCJ-02/BD-09)
    # Rough area: 1° lat ≈ 111km, 1° lng ≈ 111*cos(lat) km
    import math
    mid_lat = (bounds[1] + bounds[3]) / 2
    cos_lat = math.cos(math.radians(mid_lat)) if abs(mid_lat) < 90 else 0.5
    area_deg2 = geometry.area
    area_km2 = area_deg2 * (111 * 111 * cos_lat)

    # Reject absurdly small (<0.01 km²) or large (>100,000 km²) boundaries
    if area_km2 < 0.01:
        return False
    if area_km2 > 100000:
        return False

    return True


def _transform_to_crs(geometry, src_crs, target_crs):
    """Transform geometry between coordinate systems."""
    if src_crs == target_crs:
        return geometry

    if src_crs == 'bd09mc':
        if target_crs == 'wgs84':
            return transform_geometry(geometry, bd09mc_to_wgs84)
        elif target_crs == 'gcj02':
            return transform_geometry(geometry, bd09mc_to_gcj02)

    if src_crs == 'gcj02':
        if target_crs == 'wgs84':
            return transform_geometry(geometry, gcj02_to_wgs84)

    if src_crs == 'wgs84':
        if target_crs == 'gcj02':
            return transform_geometry(geometry, wgs84_to_gcj02)

    return geometry
