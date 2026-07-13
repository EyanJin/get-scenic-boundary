"""
Geometry processing module — parse raw boundary data into Shapely geometries.
几何处理模块 — 将原始边界数据解析为 Shapely 几何体
"""
from shapely.geometry import Polygon, MultiPolygon, Point, shape as shapely_shape


def parse_baidu_geo(geo_str):
    """Parse Baidu Maps geo string into coordinate rings.
    解析百度地图 geo 字符串为坐标环列表

    Format: type|bbox|ring_data
      type=4: polygon, type=1: point
      ring_data: ring_id-x1,y1,x2,y2,...[;ring_id-x1,y1,...]

    Returns:
        tuple: (geo_type, data) where geo_type is 'polygon'|'point'|None
               and data is list of rings or list of point coords
    """
    if not geo_str or '|' not in geo_str:
        return None, None

    parts = geo_str.split('|')
    geo_type = int(parts[0])

    if geo_type == 1:
        if len(parts) >= 3:
            coords = parts[2].strip().rstrip(';').split(',')
            if len(coords) >= 2:
                try:
                    return 'point', [(float(coords[0]), float(coords[1]))]
                except ValueError:
                    return None, None
        return None, None

    if geo_type != 4:
        return None, None

    rings_data = parts[2] if len(parts) > 2 else ''
    rings = []

    ring_strs = rings_data.split(';')
    for ring_str in ring_strs:
        ring_str = ring_str.strip()
        if not ring_str:
            continue
        # Strip ring index prefix (e.g., "1-")
        if '-' in ring_str[:5]:
            ring_str = ring_str.split('-', 1)[1]

        values = ring_str.split(',')
        coords = []
        i = 0
        while i < len(values) - 1:
            try:
                x = float(values[i].rstrip(';'))
                y = float(values[i + 1].rstrip(';'))
                coords.append((x, y))
                i += 2
            except (ValueError, IndexError):
                i += 1
                continue

        if len(coords) >= 3:
            rings.append(coords)

    return ('polygon', rings) if rings else (None, None)


def convert_ring(ring, converter):
    """Convert a coordinate ring using a transformation function.
    使用坐标转换函数转换一个坐标环

    Args:
        ring: list of (x, y) tuples
        converter: function(x, y) -> (lng, lat)

    Returns:
        list of (lng, lat) tuples, closed ring
    """
    converted = []
    for x, y in ring:
        lng, lat = converter(x, y)
        converted.append((lng, lat))
    if converted and converted[0] != converted[-1]:
        converted.append(converted[0])
    return converted


def rings_to_geometry(rings, converter):
    """Convert coordinate rings to a Shapely geometry.
    将坐标环列表转换为 Shapely 几何体

    Uses area and containment to determine outer/inner rings (holes).
    Produces MultiPolygon for non-contiguous areas.

    Args:
        rings: list of coordinate rings (raw coordinates)
        converter: function(x, y) -> (lng, lat)

    Returns:
        Shapely Polygon, MultiPolygon, or None
    """
    if not rings:
        return None

    converted_rings = [convert_ring(r, converter) for r in rings]

    candidates = []
    for ring in converted_rings:
        try:
            p = Polygon(ring)
            if not p.is_valid:
                p = p.buffer(0)
            if not p.is_empty and p.area > 0:
                candidates.append(p)
        except Exception:
            continue

    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # Sort by area descending
    candidates.sort(key=lambda p: p.area, reverse=True)

    # Determine containment: smaller polygons inside larger ones are holes
    outer_polys = []
    used = set()

    for i, big in enumerate(candidates):
        if i in used:
            continue
        holes = []
        for j, small in enumerate(candidates):
            if j <= i or j in used:
                continue
            if big.contains(small):
                holes.append(small)
                used.add(j)
        if holes:
            result = big
            for hole in holes:
                result = result.difference(hole)
            outer_polys.append(result)
        else:
            outer_polys.append(big)
        used.add(i)

    for i, p in enumerate(candidates):
        if i not in used:
            outer_polys.append(p)

    if len(outer_polys) == 1:
        return outer_polys[0]

    polys = []
    for p in outer_polys:
        if isinstance(p, Polygon):
            polys.append(p)
        elif isinstance(p, MultiPolygon):
            polys.extend(p.geoms)
    return MultiPolygon(polys)


def transform_geometry(geom, converter):
    """Apply a coordinate transformation to an entire geometry.
    对整个几何体应用坐标转换

    Args:
        geom: Shapely geometry
        converter: function(lng, lat) -> (new_lng, new_lat)

    Returns:
        Transformed Shapely geometry
    """
    from shapely.ops import transform as shapely_transform

    def _transform_coords(x, y):
        results_x, results_y = [], []
        for xi, yi in zip(x, y):
            nx, ny = converter(xi, yi)
            results_x.append(nx)
            results_y.append(ny)
        return results_x, results_y

    return shapely_transform(_transform_coords, geom)


def geojson_to_geometry(geojson_dict):
    """Convert a GeoJSON geometry dict to a Shapely geometry.
    将 GeoJSON 几何字典转为 Shapely 几何体

    Args:
        geojson_dict: dict with 'type' and 'coordinates'

    Returns:
        Shapely geometry, repaired if invalid
    """
    geom = shapely_shape(geojson_dict)
    if not geom.is_valid:
        geom = geom.buffer(0)
    return geom


def parse_amap_shape(shape_str):
    """Parse Amap mining_shape string into a Shapely polygon.
    解析高德 mining_shape 字符串为 Shapely 多边形

    Format: "lng,lat;lng,lat;..." (GCJ-02 coordinates)

    Returns:
        Shapely Polygon or None
    """
    if not shape_str or ';' not in shape_str:
        return None

    pts = shape_str.split(';')
    coords = []
    for pt in pts:
        pt = pt.strip()
        if ',' in pt:
            try:
                x, y = pt.split(',')
                coords.append((float(x), float(y)))
            except ValueError:
                continue

    if len(coords) < 3:
        return None

    if coords[0] != coords[-1]:
        coords.append(coords[0])

    poly = Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly if not poly.is_empty else None
