# get-scenic-boundary

**中国风景名胜区边界数据获取工具**

输入景区名称 → 获取该景区的边界多边形（GeoJSON 格式）。

已收录 **1004 个景区**，覆盖率 **99.1%**。

---

## 四种使用方式

根据你的需求选择：

| 方式 | 适合谁 | 需要编程吗 |
|------|--------|-----------|
| [1. 直接下载数据](#1-直接下载数据) | 只想要数据的人 | 不需要 |
| [2. 命令行查询](#2-命令行查询) | 想查个别景区的人 | 需要 Python |
| [3. Python API](#3-python-api) | 开发者集成到自己项目 | 需要 Python |
| [4. 批量处理](#4-批量处理) | 有一批景区名单要查 | 需要 Python |

---

### 1. 直接下载数据

**不需要编程。** 全部 1004 个景区边界已经生成好了：

1. 进入 [Releases 页面](https://github.com/EyanJin/get-scenic-boundary/releases)
2. 下载 `scenic_areas_wgs84.geojson`
3. 拖入 [geojson.io](https://geojson.io) → 立即在地图上看到所有景区边界

其他打开方式：[QGIS](https://qgis.org)（免费）、ArcGIS、Python、R、JavaScript。

---

### 2. 命令行查询

查询任意一个景区的边界：

```bash
# 安装（一次性）
pip install get-scenic-boundary[baidu]
playwright install chromium

# 查询
get-scenic-boundary "西湖风景名胜区"              # 输出 GeoJSON
get-scenic-boundary "黄山" --open                 # 在浏览器中预览
get-scenic-boundary "九寨沟" -o jiuzhaigou.geojson # 保存到文件
```

---

### 3. Python API

在你的 Python 项目中调用：

```python
from geoboundary import get_boundary

# 获取边界
result = get_boundary("西湖风景名胜区")

# 返回 GeoJSON Feature
print(result['geometry']['type'])  # "Polygon"
print(result['properties']['name'])  # "西湖风景名胜区"
print(result['properties']['source'])  # "baidu"
```

也支持坐标转换（零外部依赖）：

```python
from geoboundary import gcj02_to_wgs84, bd09mc_to_wgs84

lng, lat = gcj02_to_wgs84(120.15, 30.25)  # 高德坐标 → GPS
```

---

### 4. 批量处理

准备一个文本文件（每行一个景区名）：

```text
西湖风景名胜区
黄山风景名胜区
庐山风景名胜区
九寨沟风景名胜区
```

执行：

```bash
get-scenic-boundary --batch places.txt -o ./output/
```

输出：
- `output/` 目录下每个景区一个 `.geojson` 文件
- `output/_merged.geojson` — 所有结果合并为一个文件
- `output/_report.txt` — 统计报告（成功/失败/来源分布）
- 支持**断点续传** — 中断后重新运行会跳过已完成的景区

---

## 安装

```bash
# 推荐（含百度源，覆盖率最高）
pip install get-scenic-boundary[baidu]
playwright install chromium

# 基础版（仅 OSM 源，覆盖率约 20%）
pip install get-scenic-boundary

# 全部功能（含 Shapefile 导出）
pip install get-scenic-boundary[all]
```

不想用 pip？直接克隆仓库：

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
| 百度地图 | ~95% | 慢（5-10秒/个） | 不需要 |
| 高德地图 | ~60% | 中 | 需要免费 API Key |
| OpenStreetMap | ~20% | 快 | 不需要 |

默认按覆盖率从高到低自动尝试。可以用 `--source baidu/amap/osm` 指定。

高德 API Key 免费申请：https://lbs.amap.com/dev/key （配置在 `.env` 文件中）

## 坐标系

输出默认 **WGS84**（GPS/国际通用）。支持 `--crs gcj02` 输出高德/腾讯坐标。

所有转换精度 < 0.5 米。详见 [docs/coordinate_systems.md](docs/coordinate_systems.md)。

## 适用场景

- 学术研究：景区边界空间分析
- 数据新闻：景区范围可视化
- GIS 教学：真实数据教学素材
- 旅游开发：景区范围底图

## 数据说明

数据来自公开可访问的地图服务（百度地图、高德地图、OpenStreetMap）。OSM 数据遵循 [ODbL](https://opendatacommons.org/licenses/odbl/) 许可。每个要素的 `source` 字段标注来源。

## License

MIT

---

## English

A tool and dataset for retrieving boundary polygons of Chinese scenic areas (风景名胜区).

**Dataset**: [Download from Releases](https://github.com/EyanJin/get-scenic-boundary/releases) — 1004 scenic areas, 99.1% coverage, GeoJSON format.

**Tool**: Query individual boundaries via CLI or Python API.

```bash
pip install get-scenic-boundary[baidu] && playwright install chromium
get-scenic-boundary "West Lake Scenic Area" --open
```

```python
from geoboundary import get_boundary
result = get_boundary("黄山风景名胜区", crs="wgs84")
```

Sources: Baidu Maps (~95%) → Amap (~60%) → OSM (~20%). All output in WGS84.

See [docs/data_sources.md](docs/data_sources.md) for details.
