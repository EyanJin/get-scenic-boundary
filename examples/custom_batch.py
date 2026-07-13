#!/usr/bin/env python3
"""
Example: Batch query boundaries for a custom list of places.
示例：批量获取自定义地名列表的边界数据

This example shows how to use the Python API for batch processing.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geoboundary import get_boundary, batch_query


# ============================================================
# Method 1: Simple batch with list of names
# ============================================================
print("=== 方法 1: 简单列表 ===")
places = ["西湖", "黄山", "庐山", "九寨沟"]

results = batch_query(places, source='osm', output_dir='./output_demo')

found = sum(1 for _, f in results if f)
print(f"\nResults: {found}/{len(results)} found")
print()


# ============================================================
# Method 2: With province hints for disambiguation
# ============================================================
print("=== 方法 2: 带省份提示 ===")
places_with_province = [
    {'name': '西湖风景名胜区', 'province': '浙江省'},
    {'name': '黄山风景名胜区', 'province': '安徽省'},
    {'name': '庐山风景名胜区', 'province': '江西省'},
]

results = batch_query(places_with_province, source='osm')
for name_item, feature in results:
    name = name_item['name'] if isinstance(name_item, dict) else name_item
    if feature:
        geom_type = feature['geometry']['type']
        num_coords = len(feature['geometry']['coordinates'][0])
        print(f"  {name}: {geom_type} ({num_coords} points)")
    else:
        print(f"  {name}: not found")
print()


# ============================================================
# Method 3: Single query with full control
# ============================================================
print("=== 方法 3: 单个查询完整控制 ===")
result = get_boundary("西湖风景名胜区", source='osm', crs='wgs84')
if result:
    print(f"  Name: {result['properties']['name']}")
    print(f"  Source: {result['properties']['source']}")
    print(f"  Type: {result['geometry']['type']}")

    # Save to file
    with open('./xihu_boundary.geojson', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  Saved to: ./xihu_boundary.geojson")
    print(f"  Tip: drag the file into https://geojson.io to visualize!")
else:
    print("  Not found (try --source baidu with playwright installed)")
