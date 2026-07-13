#!/usr/bin/env python3
"""
Example: Coordinate transformation between Chinese map services.
示例：中国地图服务坐标系转换

This module has ZERO external dependencies (only uses math).
You can copy coord_transform.py into any project and use it standalone.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geoboundary.coord_transform import (
    gcj02_to_wgs84,
    wgs84_to_gcj02,
    bd09mc_to_wgs84,
    bd09_to_wgs84,
    bd09_to_gcj02,
)

# ============================================================
# Example 1: GCJ-02 (高德/腾讯) → WGS84 (GPS/国际标准)
# ============================================================
print("=== GCJ-02 → WGS84 ===")
# 杭州西湖在高德地图上的坐标
gcj_lng, gcj_lat = 120.1551, 30.2741
wgs_lng, wgs_lat = gcj02_to_wgs84(gcj_lng, gcj_lat)
print(f"  高德坐标: ({gcj_lng}, {gcj_lat})")
print(f"  GPS坐标:  ({wgs_lng:.6f}, {wgs_lat:.6f})")
print(f"  偏移量:   ({abs(gcj_lng-wgs_lng)*111:.0f}m, {abs(gcj_lat-wgs_lat)*111:.0f}m)")
print()

# ============================================================
# Example 2: WGS84 → GCJ-02 (GPS 坐标标到高德地图上)
# ============================================================
print("=== WGS84 → GCJ-02 ===")
wgs_lng, wgs_lat = 116.3912, 39.9073  # 天安门 GPS 坐标
gcj_lng, gcj_lat = wgs84_to_gcj02(wgs_lng, wgs_lat)
print(f"  GPS坐标:  ({wgs_lng}, {wgs_lat})")
print(f"  高德坐标: ({gcj_lng:.6f}, {gcj_lat:.6f})")
print()

# ============================================================
# Example 3: 百度墨卡托 → WGS84 (百度 API 原始数据转换)
# ============================================================
print("=== BD-09 MC → WGS84 ===")
# 百度地图 API 返回的墨卡托坐标
bd_mc_x, bd_mc_y = 13375504.5348571, 3509072.6704933
wgs_lng, wgs_lat = bd09mc_to_wgs84(bd_mc_x, bd_mc_y)
print(f"  百度墨卡托: ({bd_mc_x}, {bd_mc_y})")
print(f"  GPS坐标:   ({wgs_lng:.6f}, {wgs_lat:.6f})")
print()

# ============================================================
# Example 4: BD-09 → WGS84 (百度经纬度 → GPS)
# ============================================================
print("=== BD-09 → WGS84 ===")
bd_lng, bd_lat = 120.1617, 30.2801  # 西湖在百度地图上的经纬度
wgs_lng, wgs_lat = bd09_to_wgs84(bd_lng, bd_lat)
print(f"  百度经纬度: ({bd_lng}, {bd_lat})")
print(f"  GPS坐标:   ({wgs_lng:.6f}, {wgs_lat:.6f})")
print()

# ============================================================
# Example 5: 精度验证 — 往返转换误差
# ============================================================
print("=== 精度验证 ===")
original = (120.15, 30.25)
gcj = wgs84_to_gcj02(*original)
back = gcj02_to_wgs84(*gcj)
error_m = ((back[0]-original[0])**2 + (back[1]-original[1])**2)**0.5 * 111000
print(f"  原始 WGS84: {original}")
print(f"  → GCJ-02:   ({gcj[0]:.8f}, {gcj[1]:.8f})")
print(f"  → 还原:     ({back[0]:.8f}, {back[1]:.8f})")
print(f"  往返误差:   {error_m:.6f} 米")
