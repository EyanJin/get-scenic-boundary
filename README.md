# get-scenic-boundary

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/EyanJin/get-scenic-boundary)](https://github.com/EyanJin/get-scenic-boundary/releases)
[![Scenic Areas](https://img.shields.io/badge/景区数据-1004%2F1013%20(99.1%25)-orange)](https://github.com/EyanJin/get-scenic-boundary/releases)

**中国风景名胜区边界数据** — 输入景区名称，获取边界多边形。

1004 scenic area boundaries in China. Input name → get polygon.

**[中文文档](#中文文档)** | **[English Documentation](#english-documentation)**

---

<!-- 中文文档 -->

<a name="中文文档"></a>

## 这个项目能做什么？

把景区名称变成一个可以在地图上显示的**边界形状**：

```
"西湖风景名胜区" → 143 个坐标点围成的多边形 → 在地图上画出西湖的轮廓
```

**已有数据**：全国 1004 个风景名胜区的边界（覆盖率 99.1%）

**也可以查新的**：输入任意景区名，自动从百度地图/高德/OSM 获取边界

---

## 六种使用方式

| # | 方式 | 适合谁 | 需要编程吗 |
|---|------|--------|-----------|
| 1 | [直接下载数据](#方式-1直接下载数据) | 只想要数据 | 不需要 |
| 2 | [命令行查询](#方式-2命令行查询) | 想查个别景区 | 需要 Python |
| 3 | [Python API](#方式-3python-api) | 开发者集成 | 需要 Python |
| 4 | [批量处理](#方式-4批量处理) | 有一批景区要查 | 需要 Python |
| 5 | [坐标转换](#方式-5坐标转换工具) | 只想转换坐标 | 需要 Python |
| 6 | [AI 对话](#方式-6ai-skill) | AI 编程助手用户 | 用自然语言 |

---

### 方式 1：直接下载数据

> 不需要安装任何东西。5 分钟内拿到数据并看到地图效果。

**第一步**：进入 [Releases 页面](https://github.com/EyanJin/get-scenic-boundary/releases)，下载 `scenic_areas_wgs84.geojson`

**第二步**：打开 [geojson.io](https://geojson.io)，把下载的文件拖进去

**完成** — 你会看到 1004 个景区的边界显示在地图上。

> 也可以用 [QGIS](https://qgis.org)（免费专业 GIS 软件）、ArcGIS、Python、R 等工具打开。

---

### 方式 2：命令行查询

> 查询任意一个景区，一行命令搞定。

```bash
# 首次安装（只需要一次）
pip install get-scenic-boundary[baidu]
playwright install chromium

# 查询并在浏览器中预览
get-scenic-boundary "西湖风景名胜区" --open

# 保存到文件
get-scenic-boundary "黄山" -o huangshan.geojson

# 指定坐标系（默认 WGS84，可选 GCJ-02）
get-scenic-boundary "庐山" --crs gcj02
```

---

### 方式 3：Python API

> 在你的项目中调用，两行代码获取边界。

```python
from geoboundary import get_boundary

result = get_boundary("西湖风景名胜区")
print(result['geometry']['type'])       # "Polygon"
print(result['properties']['source'])   # "baidu"
```

返回标准 GeoJSON Feature，可直接用于 geopandas、folium、leaflet 等工具。

---

### 方式 4：批量处理

> 有一批景区名单？一次查完，自动断点续传。

准备文本文件 `places.txt`（每行一个景区名）：

```text
西湖风景名胜区
黄山风景名胜区
庐山风景名胜区
```

执行：

```bash
get-scenic-boundary --batch places.txt -o ./output/
```

输出：
- 每个景区单独的 `.geojson` 文件
- `_merged.geojson` — 所有结果合并
- `_report.txt` — 统计报告
- 中断后重新运行 → 自动跳过已完成项

---

### 方式 5：坐标转换工具

> 中国地图坐标系互转。零外部依赖，精度 < 0.5 米。

支持：百度墨卡托(BD-09 MC) ↔ 百度经纬度(BD-09) ↔ 国测局(GCJ-02) ↔ GPS(WGS84)

```python
from geoboundary import gcj02_to_wgs84, bd09mc_to_wgs84, wgs84_to_gcj02

# 高德/腾讯坐标 → GPS
lng, lat = gcj02_to_wgs84(120.15, 30.25)

# 百度 API 原始数据 → GPS
lng, lat = bd09mc_to_wgs84(13375504, 3509072)
```

命令行版：

```bash
python scripts/convert_coords.py --from gcj02 --to wgs84 120.15 30.25
python scripts/convert_coords.py --from bd09mc --to wgs84 --input data.csv -o result.csv
```

---

### 方式 6：AI Skill

> 在 AI 编程助手中用自然语言查询边界。支持 Claude Code、Codex、Cursor 等。

```
你: 获取西湖风景名胜区的边界数据
AI: [自动调用 get_boundary，返回 GeoJSON]

你: get boundary for 黄山
AI: [returns GeoJSON polygon with 256 coordinates]
```

安装方式：将 [`skill/SKILL.md`](skill/SKILL.md) 复制到你的 AI 编程工具的 skills 目录：
- **Claude Code**: `~/.claude/skills/`
- **Codex / Cursor**: 对应的自定义指令或 skills 目录
- **其他 AI 工具**: 将 SKILL.md 内容作为系统提示词或工具描述

---

## 安装

```bash
# 推荐安装（百度源覆盖率最高 ~95%）
pip install get-scenic-boundary[baidu]
playwright install chromium

# 基础安装（仅 OSM 源，覆盖率 ~20%）
pip install get-scenic-boundary

# 完整安装（全部数据源 + Shapefile 导出）
pip install get-scenic-boundary[all]
playwright install chromium
```

或直接克隆仓库使用：

```bash
git clone https://github.com/EyanJin/get-scenic-boundary.git
cd get-scenic-boundary
pip install -r requirements-full.txt && playwright install chromium
python scripts/query_single.py "西湖" --open
```

---

## 数据来源

| 来源 | 覆盖率 | 速度 | 需要配置 |
|------|--------|------|----------|
| 百度地图 | ~95% | 5-10 秒/个 | 不需要 |
| 高德地图 | ~60% | 2-3 秒/个 | 需要 [免费 API Key](https://lbs.amap.com/dev/key) |
| OpenStreetMap | ~20% | 1-2 秒/个 | 不需要 |

默认自动按覆盖率从高到低尝试。用 `--source` 指定数据源。

## 适用场景

- **学术研究** — 景区边界空间分析、生态研究底图
- **数据新闻** — 景区范围可视化报道
- **GIS 教学** — 真实边界数据作为教学素材
- **旅游应用** — 景区轮廓展示、地理围栏

## 项目文档

- [坐标系详解](docs/coordinate_systems.md) — BD-09 / GCJ-02 / WGS84 的区别和转换原理
- [数据源说明](docs/data_sources.md) — 各数据源的工作原理、限制和配置方法

## 数据许可

数据来自公开地图服务。OSM 数据遵循 [ODbL](https://opendatacommons.org/licenses/odbl/)。每个要素的 `source` 字段标注来源。

**代码许可**：MIT

---

<!-- English Documentation -->

<a name="english-documentation"></a>

## English Documentation

### What is this?

A tool and dataset for **Chinese scenic area (风景名胜区) boundary polygons**.

- **Dataset**: 1004 scenic areas with polygon boundaries (99.1% coverage)
- **Tool**: Input a scenic area name → get its boundary as GeoJSON

### Six Ways to Use

| # | Method | For | Coding? |
|---|--------|-----|---------|
| 1 | [Download data](#1-download-dataset) | Just want the data | No |
| 2 | [CLI query](#2-cli-query) | Look up one area | Python |
| 3 | [Python API](#3-python-api-1) | Integrate into your project | Python |
| 4 | [Batch processing](#4-batch-processing) | Query a list of areas | Python |
| 5 | [Coordinate conversion](#5-coordinate-conversion) | Convert between Chinese map CRS | Python |
| 6 | [AI Skill](#6-ai-skill-1) | Natural language queries | No code |

---

#### 1. Download Dataset

No coding required. Get the boundary data in 2 minutes:

1. Go to [Releases](https://github.com/EyanJin/get-scenic-boundary/releases)
2. Download `scenic_areas_wgs84.geojson`
3. Drag into [geojson.io](https://geojson.io) to see all 1004 boundaries on a map

Also works with [QGIS](https://qgis.org) (free), ArcGIS, Python, R, JavaScript.

---

#### 2. CLI Query

```bash
# Install (one time)
pip install get-scenic-boundary[baidu]
playwright install chromium

# Query with browser preview
get-scenic-boundary "西湖风景名胜区" --open

# Save to file
get-scenic-boundary "黄山" -o huangshan.geojson

# Specify coordinate system (default WGS84)
get-scenic-boundary "庐山" --crs gcj02
```

---

#### 3. Python API

```python
from geoboundary import get_boundary

result = get_boundary("西湖风景名胜区", crs="wgs84")
print(result['geometry']['type'])       # "Polygon"
print(result['properties']['source'])   # "baidu"
```

Returns standard GeoJSON Feature. Works with geopandas, folium, leaflet, etc.

---

#### 4. Batch Processing

```bash
get-scenic-boundary --batch places.txt -o ./output/
```

Output:
- Individual `.geojson` per area
- `_merged.geojson` — all results combined
- `_report.txt` — statistics
- Auto-resumes on interruption (skips completed items)

---

#### 5. Coordinate Conversion

Zero external dependencies. Sub-meter accuracy (< 0.5m).

```python
from geoboundary import gcj02_to_wgs84, bd09mc_to_wgs84, wgs84_to_gcj02

# Amap/Tencent (GCJ-02) → GPS (WGS84)
lng, lat = gcj02_to_wgs84(120.15, 30.25)

# Baidu API raw data → GPS
lng, lat = bd09mc_to_wgs84(13375504, 3509072)

# GPS → Amap/Tencent
lng, lat = wgs84_to_gcj02(120.15, 30.25)
```

CLI version:

```bash
python scripts/convert_coords.py --from gcj02 --to wgs84 120.15 30.25
```

---

#### 6. AI Skill

Use natural language to query boundaries in AI coding tools (Claude Code, Codex, Cursor, etc.):

```
You: get boundary for West Lake scenic area
AI: [calls get_boundary, returns GeoJSON polygon]
```

Install: copy [`skill/SKILL.md`](skill/SKILL.md) to your AI tool's skills directory.

---

### Data Sources

| Source | Coverage | Speed | Setup |
|--------|----------|-------|-------|
| Baidu Maps | ~95% | 5-10s | None |
| Amap (高德) | ~60% | 2-3s | [Free API key](https://lbs.amap.com/dev/key) |
| OpenStreetMap | ~20% | 1-2s | None |

Auto mode tries sources in coverage order: Baidu → Amap → OSM.

### Installation

```bash
# Recommended (Baidu source, highest coverage)
pip install get-scenic-boundary[baidu]
playwright install chromium

# Basic (OSM only, ~20% coverage)
pip install get-scenic-boundary

# All features (all sources + Shapefile export)
pip install get-scenic-boundary[all]
playwright install chromium
```

### Documentation

- [Coordinate Systems](docs/coordinate_systems.md) — BD-09 / GCJ-02 / WGS84 explained
- [Data Sources](docs/data_sources.md) — How each source works

### License

Code: MIT. OSM-sourced data: [ODbL](https://opendatacommons.org/licenses/odbl/).
