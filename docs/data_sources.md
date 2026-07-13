# Data Sources
# 数据源详解

## OpenStreetMap (via Overpass API)

### How it works
- Queries the Overpass API with name-based filters
- Searches for ways/relations tagged as protected areas, parks, or tourist attractions
- Returns GeoJSON geometry in WGS84

### Strengths
- Free, no API key needed
- International coverage
- Stable, well-documented API
- Data is openly licensed (ODbL)

### Limitations
- Coverage for Chinese scenic areas: ~20% have detailed boundaries
- Rate limit: 1 request per second recommended
- Some areas may have simplified boundaries

### Configuration
```env
OVERPASS_URL=https://overpass-api.de/api/interpreter
```

---

## Baidu Maps (Browser Automation)

### How it works
1. Opens Baidu Maps in a headless Chromium browser (Playwright)
2. Searches for the place name
3. Clicks the best matching POI result
4. Intercepts the detail API response containing `guoke_geo` boundary data
5. Returns raw BD-09 MC polygon string

### Strengths
- Best coverage for Chinese POIs (~95% success rate for scenic areas)
- No API key required
- Detailed boundaries from official map data

### Limitations
- Slowest source (~5-10 seconds per query)
- Requires Playwright + Chromium installed
- May break if Baidu changes their frontend
- May be blocked by bot detection (mitigated by request delays and standard browser User-Agent headers)

### Installation
```bash
pip install geoboundary[baidu]
playwright install chromium
```

---

## Amap / 高德地图 (REST API + Browser)

### How it works
1. **Step 1 (API)**: Search POI via REST API to get POI ID
2. **Step 2 (Browser)**: Navigate to POI detail page, intercept `mining_shape` response

### Strengths
- Good coverage for Chinese POIs
- Step 1 is fast (pure REST API)
- Official API with documented rate limits

### Limitations
- Requires free API key (register at lbs.amap.com)
- Step 2 requires Playwright for boundary extraction
- CAPTCHA may appear after many requests
- Rate limit: varies by key level

### Configuration
```env
AMAP_API_KEY=your_key_here
```

Get a key: https://lbs.amap.com/dev/key (free tier: 5000 requests/day)

---

## Nominatim (Geocoding)

### How it works
- Queries the Nominatim geocoding API with `polygon_geojson=1`
- Returns the first result that has a polygon geometry

### Strengths
- Simple REST API, no key needed
- Good for well-known places with OSM boundaries
- Returns full display name for disambiguation

### Limitations
- Same data as OSM (just a different interface)
- Lower polygon coverage than direct Overpass queries
- Strict rate limit: 1 request per second, max 1 req/second per IP
- User-Agent required

---

## Source Priority (auto mode)

When `source='auto'`:

1. **Baidu** — Best coverage for Chinese places (~95%), requires Playwright
2. **Amap** — Good coverage (~60%), requires API key
3. **OSM** — Free, no setup needed, but lower Chinese coverage (~20%)

This order prioritizes result quality. If Baidu is unavailable (no Playwright installed), it falls through to Amap, then OSM.

---

## Data Quality Comparison

| Metric | OSM | Amap | Baidu |
|--------|-----|------|-------|
| Chinese scenic area coverage | ~20% | ~60% | ~95% |
| Boundary detail level | High | High | High |
| Coordinate accuracy | Excellent | Good (GCJ-02 offset) | Good (BD-09 offset) |
| Update frequency | Community-driven | Unknown | Unknown |
| Legal clarity | ODbL license | ToS apply | ToS apply |
