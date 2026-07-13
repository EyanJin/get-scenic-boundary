# geoboundary

Get boundary polygon for any place name from map services.

地名边界获取工具 — 输入地名，获取该地点的边界多边形数据。

[中文文档](README_CN.md)

---

## What does it do? / 这是什么？

Input a place name → get its boundary shape, ready for mapping.

```
"西湖风景名胜区" → Polygon with 143 coordinate points → visualize on any map
```

**Example output** (drag any `.geojson` file into [geojson.io](https://geojson.io) to see it on a map instantly):

```json
{
  "type": "Feature",
  "geometry": { "type": "Polygon", "coordinates": [[[120.12, 30.22], ...]] },
  "properties": { "name": "西湖风景名胜区", "source": "baidu" }
}
```

**Use cases:**
- Academic research: get park/scenic area boundaries for spatial analysis
- Data journalism: map boundaries for stories about places
- Urban planning: quick boundary reference data
- Education: teach GIS concepts with real data

---

## No Code Required: Pre-built Dataset / 无需编程：直接下载数据

The [Releases](https://github.com/EyanJin/geoboundary/releases) page includes boundary data for **1013 Chinese scenic areas** — just download and use:

1. Go to [Releases](https://github.com/EyanJin/geoboundary/releases)
2. Download `scenic_areas_wgs84.geojson`
3. Open it:
   - **Quick preview**: drag into [geojson.io](https://geojson.io)
   - **Desktop GIS**: open in [QGIS](https://qgis.org) (free)
   - **Google Earth**: convert to KML with online tools
   - **Programming**: load with Python, R, or JavaScript

---

## Features

- Multi-source: OpenStreetMap, Baidu Maps, Amap (高德地图)
- Coordinate systems: WGS84, GCJ-02, BD-09, BD-09 MC
- Output formats: GeoJSON, Shapefile, CSV/WKT
- Three usage modes: pip package, standalone scripts, AI Skill
- Pre-built dataset: 1013 Chinese National/Provincial Scenic Areas (see [Releases](https://github.com/EyanJin/geoboundary/releases))

## Quick Start

```bash
pip install geoboundary
geoboundary "西湖风景名胜区"
```

### Python API

```python
from geoboundary import get_boundary

result = get_boundary("西湖风景名胜区")
print(result['geometry']['type'])  # Polygon
```

### Without installing (clone & run)

```bash
git clone https://github.com/EyanJin/geoboundary.git
cd geoboundary

# Basic (OSM only):
pip install -r requirements.txt

# Full (all sources including Baidu):
pip install -r requirements-full.txt
playwright install chromium

python scripts/query_single.py "西湖风景名胜区"
python scripts/query_single.py "西湖" --open    # preview in browser
```

## Installation

```bash
# Basic (OSM source, coordinate transforms)
pip install geoboundary

# With Baidu Maps support (requires Playwright)
pip install geoboundary[baidu]
playwright install chromium

# With Shapefile export
pip install geoboundary[export]

# All features
pip install geoboundary[all]
```

## Usage

### CLI

```bash
# Simple query (outputs GeoJSON to stdout)
geoboundary "黄山"

# Specify source and coordinate system
geoboundary "黄山" --source baidu --crs gcj02

# Save to file
geoboundary "黄山" -o huangshan.geojson

# Batch mode
geoboundary --batch places.txt -o ./boundaries/
```

### Python API

```python
from geoboundary import get_boundary, batch_query

# Single query
feature = get_boundary("庐山", source="auto", crs="wgs84")

# Batch query
results = batch_query(["西湖", "黄山", "庐山"], output_dir="./output")
```

### Coordinate Transforms (zero dependencies)

```python
from geoboundary import gcj02_to_wgs84, bd09mc_to_wgs84, wgs84_to_gcj02

# GCJ-02 (Amap/高德) → WGS84
lng, lat = gcj02_to_wgs84(120.15, 30.25)

# Baidu Mercator → WGS84
lng, lat = bd09mc_to_wgs84(13375504.53, 3509072.67)
```

## Data Sources

| Source | Method | API Key | Coordinates | Speed |
|--------|--------|---------|-------------|-------|
| OSM | Overpass API | Not needed | WGS84 | Fast |
| Amap | REST API + Browser | Required (free) | GCJ-02 | Medium |
| Baidu | Browser automation | Not needed | BD-09 MC | Slow |

In `auto` mode, sources are tried in order: Baidu → Amap → OSM (highest coverage first).

## Configuration

Create a `.env` file (see `.env.example`):

```env
AMAP_API_KEY=your_key_here
```

Get a free Amap key at https://lbs.amap.com/dev/key

## Pre-built Dataset

The [Releases](https://github.com/EyanJin/geoboundary/releases) page includes boundary data for **1013 Chinese National/Provincial Scenic Areas** (风景名胜区):

- `scenic_areas_wgs84.geojson` — WGS84 coordinates
- `scenic_areas_gcj02.geojson` — GCJ-02 coordinates
- `scenic_areas.shp.zip` — Shapefile format
- `scenic_areas_metadata.csv` — Metadata (name, grade, province, source)

Coverage: 1004/1013 (99.1%) with polygon boundaries.

## Coordinate Systems

| System | Used By | Notes |
|--------|---------|-------|
| WGS84 | GPS, OSM, international | Default output |
| GCJ-02 | Amap, Tencent Maps, Chinese law | Required for China map services |
| BD-09 | Baidu Maps | Baidu's proprietary offset |
| BD-09 MC | Baidu Maps API responses | Mercator projection |

All conversions achieve sub-meter accuracy (< 0.5m for GCJ-02 ↔ WGS84).

## Data Attribution

Boundary data is collected from publicly accessible map services:
- **Baidu Maps** (百度地图) — primary source for Chinese POI boundaries
- **Amap** (高德地图) — secondary source via public REST API
- **OpenStreetMap** — tertiary source, [ODbL](https://opendatacommons.org/licenses/odbl/) licensed

OSM-sourced boundaries are subject to the Open Database License (ODbL).
Each feature's `source` property indicates its origin.

## AI Skill

This project includes an AI Skill definition (`skill/SKILL.md`) for use with Claude Code or Codex. Install as a skill to enable natural language boundary queries.

## License

MIT — see [LICENSE](LICENSE).
