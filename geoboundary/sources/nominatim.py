"""
Nominatim data source — geocoding and basic boundary lookup.
Nominatim 数据源 — 地理编码和基础边界查询

Free, no API key required. Returns WGS84 coordinates.
Rate limit: 1 request per second.
"""
import json
import time
import urllib.request
import urllib.parse

from geoboundary.config import USER_AGENT


def query(name, country_code='cn'):
    """Query Nominatim for a place boundary.
    通过 Nominatim 查询地点边界

    Note: Nominatim's polygon data coverage for Chinese places is limited.
    Consider using OSM source for better boundary results.

    Args:
        name: place name
        country_code: ISO country code filter (default: 'cn')

    Returns:
        dict with 'geometry' (GeoJSON dict) and metadata, or None
    """
    params = {
        'q': name,
        'format': 'json',
        'polygon_geojson': '1',
        'limit': '5',
    }
    if country_code:
        params['countrycodes'] = country_code

    url = f"https://nominatim.openstreetmap.org/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', USER_AGENT)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            results = json.loads(resp.read().decode('utf-8'))
    except Exception:
        return None

    if not results:
        return None

    # Find first result with polygon geometry
    for r in results:
        geojson = r.get('geojson')
        if geojson and geojson.get('type') in ('Polygon', 'MultiPolygon'):
            return {
                'geometry': geojson,
                'name': r.get('display_name', ''),
                'osm_type': r.get('osm_type', ''),
                'osm_id': r.get('osm_id', ''),
                'source': 'nominatim',
                'crs': 'wgs84',
            }

    return None
