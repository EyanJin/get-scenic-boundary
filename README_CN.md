# geoboundary 地名边界获取工具

输入地名，获取该地点的边界多边形数据。支持百度地图、高德地图和 OpenStreetMap。

[English](README.md)

---

## 这是什么？

输入一个地名 → 获取它的边界形状 → 在地图上展示。

```
"西湖风景名胜区" → 143 个坐标点组成的多边形 → 可视化到任意地图
```

**用途举例：**
- 学术研究：获取景区/公园边界用于空间分析
- 数据新闻：在地图上标注地点边界
- 城市规划：快速获取边界参考数据
- 教学：用真实数据教 GIS 概念

## 无需编程：直接下载数据

[Releases](https://github.com/EyanJin/geoboundary/releases) 页面提供 **1013 个中国风景名胜区** 的现成边界数据：

1. 进入 [Releases](https://github.com/EyanJin/geoboundary/releases) 页面
2. 下载 `scenic_areas_wgs84.geojson`
3. 打开方式：
   - **快速预览**：拖入 [geojson.io](https://geojson.io) 立即看到地图效果
   - **桌面 GIS**：用 [QGIS](https://qgis.org)（免费）打开
   - **Google Earth**：用在线工具转为 KML 格式
   - **编程使用**：Python / R / JavaScript 直接读取

---

- 多数据源：OpenStreetMap、百度地图、高德地图
- 坐标系转换：WGS84、GCJ-02、BD-09、BD-09 MC
- 输出格式：GeoJSON、Shapefile、CSV/WKT
- 三种使用方式：pip 安装包、纯脚本运行、AI Skill
- 预置数据集：全国 1013 个风景名胜区边界数据（见 [Releases](https://github.com/EyanJin/geoboundary/releases)）

## 快速开始

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

### 不安装直接使用

```bash
git clone https://github.com/EyanJin/geoboundary.git
cd geoboundary

# 基础版（仅 OSM）：
pip install -r requirements.txt

# 完整版（含百度，覆盖率最高）：
pip install -r requirements-full.txt
playwright install chromium

python scripts/query_single.py "西湖风景名胜区"
python scripts/query_single.py "西湖" --open    # 浏览器中预览
```

## 安装

```bash
# 基础版（OSM 数据源 + 坐标转换）
pip install geoboundary

# 含百度地图支持（需要 Playwright）
pip install geoboundary[baidu]
playwright install chromium

# 含 Shapefile 导出
pip install geoboundary[export]

# 全部功能
pip install geoboundary[all]
```

## 使用方法

### 命令行

```bash
# 简单查询（输出 GeoJSON 到终端）
geoboundary "黄山"

# 指定数据源和坐标系
geoboundary "黄山" --source baidu --crs gcj02

# 保存到文件
geoboundary "黄山" -o huangshan.geojson

# 批量查询
geoboundary --batch places.txt -o ./boundaries/
```

### Python API

```python
from geoboundary import get_boundary, batch_query

# 单个查询
feature = get_boundary("庐山", source="auto", crs="wgs84")

# 批量查询
results = batch_query(["西湖", "黄山", "庐山"], output_dir="./output")
```

### 坐标转换（零外部依赖）

```python
from geoboundary import gcj02_to_wgs84, bd09mc_to_wgs84, wgs84_to_gcj02

# GCJ-02（高德） → WGS84
lng, lat = gcj02_to_wgs84(120.15, 30.25)

# 百度墨卡托 → WGS84
lng, lat = bd09mc_to_wgs84(13375504.53, 3509072.67)
```

## 数据源

| 数据源 | 方式 | 是否需要 Key | 坐标系 | 速度 |
|--------|------|-------------|--------|------|
| OSM | Overpass API | 不需要 | WGS84 | 快 |
| 高德 | REST API + 浏览器 | 需要（免费申请） | GCJ-02 | 中 |
| 百度 | 浏览器自动化 | 不需要 | BD-09 MC | 慢 |

`auto` 模式按覆盖率从高到低尝试：百度 → 高德 → OSM。

## 配置

创建 `.env` 文件（参考 `.env.example`）：

```env
AMAP_API_KEY=你的高德key
```

高德 Key 免费申请地址：https://lbs.amap.com/dev/key

## 预置数据集

[Releases](https://github.com/EyanJin/geoboundary/releases) 页面包含 **全国 1013 个风景名胜区** 的边界数据：

- `scenic_areas_wgs84.geojson` — WGS84 坐标
- `scenic_areas_gcj02.geojson` — GCJ-02 坐标
- `scenic_areas.shp.zip` — Shapefile 格式
- `scenic_areas_metadata.csv` — 元数据（名称、等级、省份、数据源）

覆盖率：1004/1013（99.1%）有多边形边界。

## 坐标系说明

| 坐标系 | 使用方 | 说明 |
|--------|--------|------|
| WGS84 | GPS、OSM、国际通用 | 默认输出 |
| GCJ-02 | 高德、腾讯、中国法规要求 | 国内地图服务必须使用 |
| BD-09 | 百度地图 | 百度专有偏移 |
| BD-09 MC | 百度地图 API 原始响应 | 墨卡托投影 |

所有坐标转换精度 < 0.5 米（GCJ-02 ↔ WGS84 采用 5 次迭代收敛）。

## 数据来源

边界数据来自公开可访问的地图服务：
- **百度地图** — 中国 POI 边界的主要来源
- **高德地图** — 通过公开 REST API 获取
- **OpenStreetMap** — [ODbL](https://opendatacommons.org/licenses/odbl/) 许可证

来自 OSM 的边界数据遵循 ODbL 许可证。每个要素的 `source` 字段标识其来源。

## AI Skill

项目包含 AI Skill 定义（`skill/SKILL.md`），可在 Claude Code 或 Codex 中使用。安装为 skill 后可通过自然语言查询边界。

## 许可证

MIT — 见 [LICENSE](LICENSE)。
