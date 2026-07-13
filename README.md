# get-scenic-boundary

**中国风景名胜区边界数据获取工具** — 输入景区名，获取边界多边形。

Get boundary polygons for Chinese scenic areas from map services.

[中文](#中文) · [English](#english)

---

## 核心数据

**1004 个景区** 的完整边界多边形 | 覆盖率 **99.1%** (1004/1013) | 输出 GeoJSON / Shapefile

---

## 最快使用方式：直接下载

不需要编程。[Releases](https://github.com/EyanJin/get-scenic-boundary/releases) 页面有现成数据：

1. 下载 [`scenic_areas_wgs84.geojson`](https://github.com/EyanJin/get-scenic-boundary/releases)
2. 拖入 [geojson.io](https://geojson.io) → 立即看到 1004 个景区在地图上的边界

也可以用 [QGIS](https://qgis.org)（免费桌面 GIS）或任何支持 GeoJSON 的工具打开。

---

## 命令行查询单个景区

```bash
pip install get-scenic-boundary[baidu]
playwright install chromium

get-scenic-boundary "西湖风景名胜区" --open    # 自动在浏览器中预览
get-scenic-boundary "黄山" -o huangshan.geojson  # 保存到文件
```

## Python API

```python
from geoboundary import get_boundary

result = get_boundary("西湖风景名胜区")
# → GeoJSON Feature: { "type": "Feature", "geometry": {"type": "Polygon", ...} }
```

## 批量查询

```bash
get-scenic-boundary --batch places.txt -o ./output/
# 自动断点续传，生成合并 GeoJSON + 统计报告
```

---

## 数据来源与覆盖率

| 来源 | 方式 | 覆盖率 | 坐标系 |
|------|------|--------|--------|
| 百度地图 | 浏览器自动化 | ~95% | BD-09 MC → WGS84 |
| 高德地图 | REST API | ~60% | GCJ-02 → WGS84 |
| OpenStreetMap | Overpass API | ~20% | WGS84 |

`auto` 模式按覆盖率从高到低尝试：百度 → 高德 → OSM。

## 坐标系

输出默认 **WGS84**（GPS/国际标准）。也支持 GCJ-02（高德/腾讯）。

所有转换精度 < 0.5 米。详见 [docs/coordinate_systems.md](docs/coordinate_systems.md)。

## 安装选项

```bash
pip install get-scenic-boundary           # 基础（OSM）
pip install get-scenic-boundary[baidu]    # 含百度（推荐，覆盖率最高）
pip install get-scenic-boundary[all]      # 全部功能
```

或者直接克隆：

```bash
git clone https://github.com/EyanJin/get-scenic-boundary.git
cd get-scenic-boundary
pip install -r requirements-full.txt && playwright install chromium
python scripts/query_single.py "西湖" --open
```

## 配置

百度源无需配置。高德源需要免费 API Key：

```bash
# .env
AMAP_API_KEY=your_key    # 免费申请：https://lbs.amap.com/dev/key
```

---

## 适用场景

- 学术研究：空间分析、生态研究的景区边界底图
- 数据新闻：可视化景区范围
- GIS 教学：真实边界数据教学素材
- 旅游应用：景区范围展示

## 数据来源说明

数据通过公开地图服务获取：
- **百度地图** — 中国景区边界主要来源
- **高德地图** — 公开 REST API
- **OpenStreetMap** — [ODbL](https://opendatacommons.org/licenses/odbl/) 许可

每个要素的 `source` 字段标识其来源。

## License

MIT — see [LICENSE](LICENSE).

---

<a name="english"></a>

## English

### What is this?

A tool + dataset for Chinese scenic area boundaries. Input a scenic area name → get its boundary polygon as GeoJSON.

**Dataset**: 1004 scenic areas with polygon boundaries (99.1% coverage). Download from [Releases](https://github.com/EyanJin/get-scenic-boundary/releases).

**Tool**: Query boundaries programmatically via CLI or Python API.

### Quick Start

```bash
pip install get-scenic-boundary[baidu]
playwright install chromium
get-scenic-boundary "West Lake" --open
```

```python
from geoboundary import get_boundary
result = get_boundary("黄山风景名胜区", crs="wgs84")
```

### Data Sources

Sources tried in order (highest coverage first): Baidu Maps (~95%) → Amap (~60%) → OSM (~20%).

All coordinates converted to WGS84 by default. Sub-meter accuracy (< 0.5m).

See [docs/data_sources.md](docs/data_sources.md) and [docs/coordinate_systems.md](docs/coordinate_systems.md) for details.
