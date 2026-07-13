"""
Amap (高德地图) data source — REST API + optional browser automation.
高德地图数据源 — REST API + 可选浏览器自动化

Uses the public Place API (requires free API key).
Returns GCJ-02 coordinates.
"""
import json
import re
import time
import urllib.request
import urllib.parse

from geoboundary.config import AMAP_API_KEY, USER_AGENT, REQUEST_DELAY


def query(name, province=''):
    """Query Amap for a place boundary.
    查询高德地图获取地点边界

    Strategy:
      1. Search POI via REST API to get POI ID
      2. If browser available, fetch detail page for mining_shape

    Args:
        name: place name (Chinese)
        province: province/city hint

    Returns:
        dict with 'geometry' (GeoJSON dict, GCJ-02) and metadata, or None
    """
    if not AMAP_API_KEY:
        return None

    # Step 1: Search for POI ID
    poi = _search_poi(name, province)
    if not poi:
        return None

    poi_id = poi.get('id')
    if not poi_id:
        return None

    # Step 2: Try to get boundary from detail page
    boundary = _fetch_boundary(poi_id)
    if boundary:
        return {
            'geometry': boundary,
            'name': poi.get('name', ''),
            'poi_id': poi_id,
            'location': poi.get('location', ''),
            'source': 'amap',
            'crs': 'gcj02',
        }

    return None


def search_poi(name, province=''):
    """Public wrapper for POI search.
    公开的 POI 搜索接口

    Args:
        name: place name
        province: province/city filter

    Returns:
        dict with POI info or None
    """
    return _search_poi(name, province)


# ========== Internal functions ==========

def _search_poi(name, province=''):
    """Search Amap REST API for a matching POI."""
    if not AMAP_API_KEY:
        return None

    core = _extract_core_name(name)
    queries = [name]
    if core:
        queries.append(f'{core}风景区')
        queries.append(f'{core}景区')
        if len(core) >= 2:
            queries.append(core)

    city = province.replace('省', '').replace('市', '') if province else ''

    for keyword in queries:
        pois = _api_search(keyword, city)
        time.sleep(0.1)

        for p in pois:
            poi_id = p.get('id', p.get('poiid', ''))
            poi_name = p.get('name', '')
            if poi_id and _validate_name(name, poi_name):
                return {
                    'id': poi_id,
                    'name': poi_name,
                    'location': p.get('location', ''),
                    'type': p.get('type', ''),
                }

    return None


def _api_search(keyword, city=''):
    """Call Amap Place Text Search API."""
    params = {
        'key': AMAP_API_KEY,
        'keywords': keyword,
        'types': '110200|110201|110202|110203|110204|110205',
        'offset': '10',
        'page': '1',
        'extensions': 'base',
    }
    if city:
        params['city'] = city

    url = f"https://restapi.amap.com/v3/place/text?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', USER_AGENT)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('status') == '1':
                return data.get('pois', [])
    except Exception:
        pass
    return []


def _fetch_boundary(poi_id):
    """Fetch boundary geometry from Amap detail page via Playwright.
    通过 Playwright 获取高德详情页边界数据

    Returns GeoJSON geometry dict (GCJ-02) or None.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    detail_data = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                # Standard headless browser config — prevents sites from
                # refusing service to automated clients
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                           '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768},
            )
            # Standard browser fingerprint — Playwright's default webdriver
            # property causes some sites to block automated access
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            page = context.new_page()

            captured = {}

            def handle_response(response):
                if 'detail/get/detail' in response.url and poi_id in response.url:
                    try:
                        captured['data'] = response.json()
                    except Exception:
                        pass

            page.on('response', handle_response)

            poi_url = f'https://ditu.amap.com/place/{poi_id}'
            page.goto(poi_url, timeout=20000, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)

            browser.close()

            if captured.get('data'):
                detail_data = captured['data']
    except Exception:
        return None

    if not detail_data:
        return None

    # Parse mining_shape from response
    spec = detail_data.get('data', {}).get('spec', {})
    shape_str = spec.get('mining_shape', {}).get('shape', '')

    if not shape_str or ';' not in shape_str:
        return None

    # Parse "lng,lat;lng,lat;..." format
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

    return {
        'type': 'Polygon',
        'coordinates': [coords],
    }


# ========== Name utilities ==========

def _extract_core_name(name):
    """Extract core place name."""
    name = re.sub(r'^[\u4e00-\u9fff]{2,4}(省|市|县|区|州)', '', name)
    for suffix in ['国家级风景名胜区', '风景名胜区', '风景区', '景区', '名胜区',
                   '旅游区', '自然保护区']:
        name = name.replace(suffix, '')
    for sep in ['—', '-', '·', '～', '、']:
        if sep in name:
            name = name.split(sep)[0]
    return name.strip()


def _validate_name(search_name, poi_name):
    """Validate that a POI name matches the search intent."""
    core_search = _extract_core_name(search_name)
    core_poi = _extract_core_name(poi_name)
    if not core_search or not core_poi:
        return False
    if core_search == core_poi:
        return True
    if len(core_search) >= 3 and core_search in core_poi:
        return True
    if len(core_poi) >= 3 and core_poi in core_search:
        return True
    if len(core_search) >= 2 and len(core_poi) >= 2 and core_search[:2] == core_poi[:2]:
        return True
    return False
