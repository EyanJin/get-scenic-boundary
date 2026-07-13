# Coordinate Systems in Chinese Map Services
# 中国地图服务坐标系详解

## Overview 概述

China mandates coordinate obfuscation for all publicly available map services. This means that raw GPS coordinates (WGS84) will appear offset by 100-700 meters when plotted directly on Chinese maps.

中国法规要求所有公开地图服务对坐标进行加偏处理。直接将 GPS 坐标（WGS84）标注到中国地图上会产生 100-700 米的偏移。

## The Four Systems 四种坐标系

### WGS84 (EPSG:4326)
- **Used by**: GPS, OpenStreetMap, Google Earth, international services
- **Characteristics**: True geographic coordinates, no offset
- **When to use**: International exchange, academic research, GPS applications

### GCJ-02 (国测局坐标/火星坐标)
- **Used by**: Amap (高德), Tencent Maps (腾讯), Apple Maps China
- **Characteristics**: Non-linear offset from WGS84 (varies by location, typically 100-700m)
- **Legal basis**: Chinese Surveying and Mapping Law requires this for public maps
- **When to use**: Any application displaying maps in China using Amap/Tencent tiles

### BD-09 (百度坐标)
- **Used by**: Baidu Maps only
- **Characteristics**: Additional offset on top of GCJ-02
- **When to use**: Only when working with Baidu Maps API/tiles

### BD-09 MC (百度墨卡托)
- **Used by**: Baidu Maps internal API responses
- **Characteristics**: Mercator projection of BD-09 (unit: meters, not degrees)
- **When to use**: Parsing raw Baidu API responses (e.g., `guoke_geo` field)

## Transformation Chain 转换链路

```
BD-09 MC (meters) ──→ BD-09 (degrees) ──→ GCJ-02 ──→ WGS84
   百度墨卡托            百度经纬度           国测局        国际标准

       Polynomial               Fixed            5-iteration
       lookup table              offset           convergence
       (6 bands)                (±0.006°)         (<0.5m accuracy)
```

## Accuracy 精度

| Conversion | Method | Accuracy |
|-----------|--------|----------|
| BD-09 MC → BD-09 | Polynomial interpolation (6 bands) | Exact (same as Baidu SDK) |
| BD-09 → GCJ-02 | Fixed offset formula | Exact (reversible) |
| GCJ-02 → WGS84 | 5-iteration convergence | < 0.5 meters |
| WGS84 → GCJ-02 | Direct formula | Exact |

## Usage in geoboundary

```python
from geoboundary.coord_transform import (
    bd09mc_to_wgs84,    # Baidu raw API → international
    bd09mc_to_gcj02,    # Baidu raw API → Chinese standard
    gcj02_to_wgs84,     # Amap/Tencent → international
    wgs84_to_gcj02,     # GPS → Chinese maps
    bd09_to_wgs84,      # Baidu degrees → international
)

# Example: Convert Baidu API coordinate to GPS
lng, lat = bd09mc_to_wgs84(13375504.53, 3509072.67)
# → approximately (120.148, 30.242) — West Lake, Hangzhou
```

## Important Notes 注意事项

1. **Never mix coordinate systems** on the same map. A GCJ-02 point on a WGS84 basemap will be offset.
2. **Data from Baidu Maps** is always BD-09 MC in API responses. Always convert before using.
3. **Data from Amap** is always GCJ-02. Convert to WGS84 for international use.
4. **OSM data** is always WGS84. Convert to GCJ-02 before overlaying on Chinese map tiles.
5. The GCJ-02 offset is **non-linear** — it varies by location. You cannot use a single fixed offset for all of China.
