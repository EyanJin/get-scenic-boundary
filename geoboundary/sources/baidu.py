"""
Baidu Maps data source — browser automation via Playwright.
百度地图数据源 — Playwright 浏览器自动化

Requires: pip install geoboundary[baidu]
Returns: BD-09 MC coordinates (use coord_transform to convert)
"""
import time

from geoboundary.config import (
    BROWSER_HEADLESS, BROWSER_VIEWPORT, BROWSER_USER_AGENT, REQUEST_DELAY
)


def query(name, province=''):
    """Query Baidu Maps for a place boundary.
    查询百度地图获取地点边界

    Args:
        name: place name (Chinese)
        province: province hint for disambiguation

    Returns:
        dict with 'geo_str' (raw Baidu geo), 'name', 'uid', etc. or None
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright is required for Baidu Maps source. "
            "Install with: pip install geoboundary[baidu]\n"
            "Then run: playwright install chromium"
        )

    queries = _generate_search_queries(name, province)
    result = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=BROWSER_HEADLESS)
        context = browser.new_context(
            viewport=BROWSER_VIEWPORT,
            user_agent=BROWSER_USER_AGENT,
        )
        page = context.new_page()

        detail_data = {}

        def on_response(response):
            url = response.url
            try:
                if 'qt=detailConInfo' in url:
                    data = response.json()
                    content = data.get('content', {})
                    if isinstance(content, dict) and content.get('uid'):
                        detail_data['last'] = content
                elif ('qt=s&' in url or 'qt=con&' in url) and 'qt=spot' not in url:
                    data = response.json()
                    content = data.get('content', [])
                    if isinstance(content, list) and content:
                        detail_data['last_search'] = content
            except Exception:
                pass

        page.on('response', on_response)

        # Open Baidu Maps
        for retry in range(3):
            try:
                page.goto('https://map.baidu.com/', timeout=60000,
                          wait_until='domcontentloaded')
                page.wait_for_timeout(3000)
                break
            except Exception:
                if retry == 2:
                    browser.close()
                    return None

        for q_idx, search_query in enumerate(queries):
            try:
                detail_data.clear()

                # Remove modal overlays
                page.evaluate('''() => {
                    document.querySelectorAll(
                        '[class*="passMod"], [class*="dialog-mask"], [class*="modal-mask"], '
                        + '[class*="passport"], [class*="login-dialog"]'
                    ).forEach(el => el.remove());
                }''')
                page.wait_for_timeout(200)

                # Search
                search_input = page.locator('#sole-input')
                search_input.fill(search_query)
                page.wait_for_timeout(300)
                page.locator('#search-button').click(force=True)
                page.wait_for_timeout(4000)

                # Handle city switch prompt
                city_hint = page.locator('text=当前城市没有找到结果')
                if city_hint.is_visible():
                    search_content = detail_data.get('last_search', [])
                    if search_content and isinstance(search_content[0], dict):
                        best_city = None
                        for city_item in search_content:
                            cn = city_item.get('name', '')
                            if not cn:
                                continue
                            if not best_city:
                                best_city = cn
                            if province and province[:2] in cn:
                                best_city = cn
                                break
                        if best_city:
                            try:
                                city_el = page.locator(f'text="{best_city}"').first
                                if city_el.is_visible(timeout=2000):
                                    detail_data.clear()
                                    city_el.click()
                                    page.wait_for_timeout(4000)
                            except Exception:
                                pass

                # Click best POI match
                core_name = _extract_core_name(name)
                detail_data.pop('last', None)

                page.evaluate('''(coreName) => {
                    const links = Array.from(document.querySelectorAll('a'));
                    const candidates = [];
                    // Sub-POI filter keywords (not main scenic areas)
                    const filterKw = [
                        '售票', '直通车', '代售', '乘车站', '票务',
                        '游客中心', '停车场', '正门', '入口', '检票', '大厅',
                        '小吃', '餐厅', '酒店', '民宿', '公寓', '旅游公司',
                        '加油站', '充电站', '退役军人', '卫生院', '派出所',
                        '人民法院', '人民政府', '服务站'
                    ];
                    // Management structure keywords (heavy penalty)
                    const mgmtKw = ['管理', '委员会', '管理处', '管理局', '办公室', '办公区', '管委会'];
                    // Geographic entity keywords (slight bonus)
                    const geoKw = ['山', '湖', '河', '江', '洞', '峡', '岛', '泉', '林', '瀑', '谷', '峰'];

                    for (const link of links) {
                        const t = link.textContent.trim();
                        if (t.length < 3 || t.length > 40) continue;
                        if (filterKw.some(kw => t.includes(kw))) continue;

                        let score = 0;
                        if (t.includes(coreName)) score += 10;
                        else if (coreName.length >= 2 && t.includes(coreName.substring(0, 2))) score += 5;
                        if (t.includes('风景')) score += 3;
                        if (t.includes('景区')) score += 2;
                        if (t.includes('名胜')) score += 2;
                        if (t.includes('5A') || t.includes('4A')) score += 1;
                        // Geographic entity bonus
                        if (geoKw.some(c => t.includes(c))) score += 1;
                        // Management structure penalty
                        if (mgmtKw.some(kw => t.includes(kw))) score -= 5;
                        // Entrance/station penalty
                        if (t.includes('门') || t.includes('处') || t.includes('站')) score -= 2;

                        if (score > 0) candidates.push({el: link, text: t, score: score});
                    }
                    candidates.sort((a, b) => b.score - a.score);
                    if (candidates.length > 0) {
                        candidates[0].el.click();
                        return candidates[0].text;
                    }
                    return null;
                }''', core_name)

                page.wait_for_timeout(4000)

                # Extract result
                detail = detail_data.get('last')
                if detail:
                    matched_name = detail.get('name', '')
                    guoke = detail.get('ext', {}).get('detail_info', {}).get('guoke_geo', {})
                    geo = guoke.get('geo', '') if isinstance(guoke, dict) else ''
                    is_valid = _validate_name_match(name, matched_name, province)

                    if geo and geo.startswith('4') and is_valid:
                        result = {
                            'geo_str': geo,
                            'name': matched_name,
                            'uid': detail.get('uid', ''),
                            'addr': detail.get('addr', ''),
                            'x': detail.get('x'),
                            'y': detail.get('y'),
                            'source': 'baidu',
                            'crs': 'bd09mc',
                        }
                        break

            except Exception:
                continue

            time.sleep(REQUEST_DELAY)

        browser.close()

    return result


# ========== Name matching utilities ==========

def _extract_core_name(name):
    """Extract core place name."""
    import re
    for suffix in ['风景名胜区', '国家级风景名胜区', '风景区', '景区', '名胜区']:
        name = name.replace(suffix, '')
    name = name.strip().strip('"').strip('\u201c').strip('\u201d')
    if '—' in name:
        return name.split('—')[0].strip()
    if '-' in name:
        return name.split('-')[-1].strip()
    return name.strip()


def _generate_core_variants(name):
    """Generate name variants by removing city prefixes and splitting compounds.
    生成名称变体（去城市前缀、拆分复合名）

    Examples:
        "合阳洽川风景名胜区" → ["合阳洽川", "洽川"]
        "青城山—都江堰" → ["青城山", "都江堰"]
        "临潼骊山" → ["临潼骊山", "骊山"]
    """
    import re
    core = _extract_core_name(name)
    variants = [core]

    # Split A—B compound names: both parts as variants
    original_no_suffix = name
    for suffix in ['风景名胜区', '国家级风景名胜区', '风景区', '景区', '名胜区']:
        original_no_suffix = original_no_suffix.replace(suffix, '')
    original_no_suffix = original_no_suffix.strip()

    for sep in ['—', '-', '·', '～']:
        if sep in original_no_suffix:
            parts = original_no_suffix.split(sep)
            for p in parts:
                p = p.strip()
                if p and len(p) >= 2 and p not in variants:
                    variants.append(p)
            break

    # Remove 2-char city prefix (e.g., "合阳洽川" → "洽川")
    if len(core) >= 4:
        no_2char = core[2:]
        if len(no_2char) >= 2 and no_2char not in variants:
            variants.append(no_2char)

    # Remove 3-char city prefix (e.g., "老河口梨花湖" → "梨花湖")
    if len(core) >= 5:
        no_3char = core[3:]
        if len(no_3char) >= 2 and no_3char not in variants:
            variants.append(no_3char)

    # Remove province/city prefix via regex
    stripped = re.sub(r'^[\u4e00-\u9fff]{2,3}(省|市|县|区)', '', core)
    if stripped and len(stripped) >= 2 and stripped != core and stripped not in variants:
        variants.append(stripped)

    return variants


def _validate_name_match(search_name, matched_name, province=''):
    """Validate that search result matches the intended place."""
    if not matched_name:
        return False

    core_search = _extract_core_name(search_name)
    core_matched = _extract_core_name(matched_name)

    if core_search in matched_name or core_matched in search_name:
        return True
    if len(core_search) >= 2 and core_search[:2] in matched_name:
        return True
    if len(core_matched) >= 2 and core_matched[:2] in search_name:
        return True

    noise = set('的了风景名胜区省市县国家级')
    search_chars = set(core_search) - noise
    matched_chars = set(core_matched) - noise
    if len(search_chars & matched_chars) >= 2:
        return True

    return False


def _generate_search_queries(name, province=''):
    """Generate search queries in priority order, using name variants."""
    variants = _generate_core_variants(name)
    core = variants[0] if variants else _extract_core_name(name)
    queries = []

    # Highest priority: province + full name
    if province:
        queries.append(f"{province} {name}")

    # Province + variants with scenic suffix
    if province:
        for v in variants:
            queries.append(f"{province} {v}风景名胜区")
            queries.append(f"{province} {v}风景区")

    # Variants + scenic suffix (no province)
    for v in variants:
        if f"{v}风景区" != name.replace('名胜', ''):
            queries.append(f"{v}风景区")
        queries.append(f"{v}景区")

    # Bare variants (geographic entity focus)
    if province:
        for v in variants:
            queries.append(f"{province} {v}")

    for v in variants:
        queries.append(v)

    # Original name as last resort
    queries.append(name)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for q in queries:
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            unique.append(q)
    return unique
