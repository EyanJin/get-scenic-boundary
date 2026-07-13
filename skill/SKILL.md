---
name: geoboundary
description: |
  Get boundary polygon data for any named place from map services.
  Supports Baidu Maps, Amap (高德), and OpenStreetMap.
  输入地名，获取该地点的边界多边形数据。
triggers:
  - get boundary for
  - get the boundary of
  - 获取边界
  - 地名边界
  - boundary polygon
  - scenic area boundary
  - place boundary
  - fetch boundary
  - 查边界
  - 获取地图边界
---

# geoboundary Skill

You are a geospatial data assistant that retrieves boundary polygons for named places using the `geoboundary` Python package.

## Capabilities

- Query boundary polygons for any place name (Chinese or English)
- Support multiple data sources: OSM (free), Amap (高德), Baidu Maps
- Output in GeoJSON, Shapefile, or WKT format
- Coordinate system conversion: WGS84, GCJ-02, BD-09

## Workflow

1. **Understand the request**: Identify the place name(s) and desired output format/CRS.
2. **Locate geoboundary**: Check if installed (`python -c "import geoboundary"`) or find the repo directory.
3. **Run the query**: Use the CLI, Python API, or scripts/ directory.
4. **Return results**: Show the GeoJSON or save to file as requested.

## Setup Detection

```bash
# Check if geoboundary is installed as a package
python -c "import geoboundary; print(geoboundary.__version__)" 2>/dev/null

# If not installed, check if the repo exists locally
# Look for geoboundary/ directory with __init__.py
```

If the package is not installed but the repo is available locally, use:
```python
import sys
sys.path.insert(0, '/path/to/geoboundary')
from geoboundary import get_boundary
```

## Usage Patterns

### Single place query
```bash
cd <project_with_geoboundary>
python -c "
import sys; sys.path.insert(0, '.') # if not pip-installed
from geoboundary import get_boundary
import json
result = get_boundary('西湖风景名胜区', source='auto', crs='wgs84')
if result:
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    print('No boundary found')
"
```

### If geoboundary is installed as a package
```bash
geoboundary "西湖风景名胜区"
geoboundary "黄山" --source baidu --crs gcj02 -o huangshan.geojson
geoboundary --batch places.txt -o ./boundaries/
```

### Coordinate conversion only
```bash
python -c "
from geoboundary.coord_transform import gcj02_to_wgs84, bd09mc_to_wgs84
# GCJ-02 to WGS84
print(gcj02_to_wgs84(120.15, 30.25))
# Baidu Mercator to WGS84
print(bd09mc_to_wgs84(13375504.53, 3509072.67))
"
```

### Batch query
```python
from geoboundary import batch_query

places = ["西湖", "黄山", "庐山", "九寨沟"]
results = batch_query(places, source='auto', output_dir='./output')
for name, feature in results:
    status = 'found' if feature else 'not found'
    print(f"{name}: {status}")
```

## Source Priority (auto mode)

1. **Baidu** — Best coverage for Chinese places (~95%), requires Playwright
2. **Amap** — Good coverage (~60%), requires AMAP_API_KEY
3. **OSM** — Free, no API key, but lower Chinese coverage (~20%)

## Setup Requirements

```bash
# Basic (OSM only, no extra deps needed beyond shapely+requests)
pip install geoboundary

# With Baidu Maps support
pip install geoboundary[baidu]
playwright install chromium

# With Shapefile export
pip install geoboundary[export]

# All features
pip install geoboundary[all]
```

## Environment Variables

Set in `.env` file or export:
- `AMAP_API_KEY` — Amap API key (get free at https://lbs.amap.com)
- `OVERPASS_URL` — Custom Overpass endpoint (default: overpass-api.de)
- `REQUEST_DELAY` — Delay between requests in seconds (default: 2)

## Output Format

The `get_boundary()` function returns a GeoJSON Feature:
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[lng, lat], ...]]
  },
  "properties": {
    "name": "西湖风景名胜区",
    "source": "osm",
    "query": "西湖风景名胜区"
  }
}
```

## Error Handling

- If no boundary found: returns `None` (CLI exits with code 1)
- If source unavailable (e.g., no playwright): silently skips to next source
- If API key missing: Amap source is skipped

## Notes

- Baidu source is slowest (browser automation) but has best coverage for Chinese POIs
- OSM coverage for Chinese scenic areas is moderate (~20% have boundaries)
- Results are cached in memory only; re-run for fresh data
- For pre-built dataset of 1013 Chinese scenic areas, check GitHub Releases
