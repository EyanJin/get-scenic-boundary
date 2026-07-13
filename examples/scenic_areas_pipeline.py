#!/usr/bin/env python3
"""
Scenic Areas Pipeline: Generate the pre-built dataset from raw data.
景区数据集生成管道：从原始抓取数据生成发布用 GeoJSON

This script demonstrates how the 1013 Chinese Scenic Areas dataset was built.
You can adapt it as a template for building your own boundary dataset.

Usage:
    python examples/scenic_areas_pipeline.py --input ../scenic-area-shp/data/baidu_results.json
    python examples/scenic_areas_pipeline.py --input data.json --output ./release/

Output:
    scenic_areas_wgs84.geojson   — WGS84 coordinates (international standard)
    scenic_areas_gcj02.geojson   — GCJ-02 coordinates (Chinese map services)
    scenic_areas_metadata.csv    — Metadata table (name, grade, province, source)
    report.txt                   — Processing statistics
"""
import sys
import os
import json
import csv
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geoboundary.geometry import (
    parse_baidu_geo, rings_to_geometry, geojson_to_geometry, transform_geometry
)
from geoboundary.coord_transform import (
    bd09mc_to_wgs84, bd09mc_to_gcj02, gcj02_to_wgs84, wgs84_to_gcj02
)
from geoboundary.export import to_geojson


def main():
    parser = argparse.ArgumentParser(
        description='Generate scenic areas boundary dataset from raw data'
    )
    parser.add_argument('--input', '-i', required=True,
                        help='Path to baidu_results.json (raw boundary data collected via Baidu Maps)')
    parser.add_argument('--output', '-o', default='./release',
                        help='Output directory (default: ./release)')
    args = parser.parse_args()

    # Load raw data
    print(f"Loading: {args.input}")
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Total records: {len(data)}")

    os.makedirs(args.output, exist_ok=True)

    # Process all entries
    features_wgs84 = []
    features_gcj02 = []
    metadata_rows = []
    stats = {'baidu': 0, 'convex_hull': 0, 'osm': 0, 'buffer': 0, 'point_only': 0, 'no_data': 0}

    for search_name, entry in data.items():
        name = entry.get('name', entry.get('osm_name', search_name))
        grade = entry.get('grade', '')
        province = entry.get('province', '')
        source = entry.get('boundary_source', 'baidu_geo')

        properties = {
            'name': name,
            'grade': grade,
            'province': province,
            'source': source,
        }

        geom_wgs84 = None
        geom_gcj02 = None

        # --- Convex hull / buffer source (GCJ-02 GeoJSON) ---
        if entry.get('hull_geojson_gcj02') and source.startswith(('convex_hull', 'buffer')):
            try:
                geom_gcj02 = geojson_to_geometry(entry['hull_geojson_gcj02'])
                if geom_gcj02 and not geom_gcj02.is_empty and geom_gcj02.area > 0:
                    geom_wgs84 = transform_geometry(geom_gcj02, gcj02_to_wgs84)
                    stats['convex_hull' if 'convex_hull' in source else 'buffer'] += 1
                else:
                    geom_gcj02 = None
            except Exception:
                geom_gcj02 = None

        # --- OSM source (WGS84 GeoJSON) ---
        elif source == 'osm' and entry.get('osm_geojson'):
            try:
                geom_wgs84 = geojson_to_geometry(entry['osm_geojson'])
                if geom_wgs84 and not geom_wgs84.is_empty and geom_wgs84.area > 0:
                    geom_gcj02 = transform_geometry(geom_wgs84, wgs84_to_gcj02)
                    stats['osm'] += 1
                else:
                    geom_wgs84 = None
            except Exception:
                geom_wgs84 = None

        # --- Baidu guoke_geo source (BD-09 MC) ---
        elif entry.get('guoke_geo', '').startswith('4'):
            geo_type, rings = parse_baidu_geo(entry['guoke_geo'])
            if geo_type == 'polygon' and rings:
                geom_wgs84 = rings_to_geometry(rings, bd09mc_to_wgs84)
                geom_gcj02 = rings_to_geometry(rings, bd09mc_to_gcj02)
                if geom_wgs84 and geom_wgs84.area > 0:
                    stats['baidu'] += 1
                else:
                    geom_wgs84 = None
                    geom_gcj02 = None

        # Add to feature lists
        if geom_wgs84 and geom_gcj02:
            features_wgs84.append({**properties, 'geometry': geom_wgs84})
            features_gcj02.append({**properties, 'geometry': geom_gcj02})
            metadata_rows.append({
                'name': name, 'grade': grade, 'province': province, 'source': source
            })
        elif not geom_wgs84:
            if entry.get('x') and entry.get('y'):
                stats['point_only'] += 1
            else:
                stats['no_data'] += 1

    # --- Output GeoJSON files ---
    wgs84_path = os.path.join(args.output, 'scenic_areas_wgs84.geojson')
    to_geojson(features_wgs84, wgs84_path, indent=None)  # compact for smaller file
    print(f"  WGS84: {wgs84_path} ({len(features_wgs84)} features)")

    gcj02_path = os.path.join(args.output, 'scenic_areas_gcj02.geojson')
    to_geojson(features_gcj02, gcj02_path, indent=None)
    print(f"  GCJ-02: {gcj02_path} ({len(features_gcj02)} features)")

    # --- Output metadata CSV ---
    csv_path = os.path.join(args.output, 'scenic_areas_metadata.csv')
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'grade', 'province', 'source'])
        writer.writeheader()
        writer.writerows(metadata_rows)
    print(f"  Metadata: {csv_path}")

    # --- Output report ---
    report_path = os.path.join(args.output, 'report.txt')
    total_boundaries = len(features_wgs84)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Scenic Areas Boundary Dataset Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total records: {len(data)}\n")
        f.write(f"With polygon boundary: {total_boundaries}\n")
        f.write(f"  - Baidu Maps: {stats['baidu']}\n")
        f.write(f"  - Convex hull: {stats['convex_hull']}\n")
        f.write(f"  - OSM: {stats['osm']}\n")
        f.write(f"  - Buffer: {stats['buffer']}\n")
        f.write(f"Point only (no boundary): {stats['point_only']}\n")
        f.write(f"No data: {stats['no_data']}\n")
        f.write(f"\nCoverage: {total_boundaries}/{len(data)} ({total_boundaries/len(data)*100:.1f}%)\n")
    print(f"  Report: {report_path}")

    # --- Summary ---
    print()
    print("=" * 50)
    print(f"Dataset generated: {total_boundaries}/{len(data)} boundaries ({total_boundaries/len(data)*100:.1f}%)")
    print(f"  Baidu: {stats['baidu']} | Convex hull: {stats['convex_hull']} | OSM: {stats['osm']} | Buffer: {stats['buffer']}")
    print(f"  Point only: {stats['point_only']} | No data: {stats['no_data']}")
    print()
    print(f"Files saved to: {args.output}/")
    print(f"Tip: upload scenic_areas_wgs84.geojson to GitHub Releases")


if __name__ == '__main__':
    main()
