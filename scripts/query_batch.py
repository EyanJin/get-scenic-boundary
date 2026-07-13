#!/usr/bin/env python3
"""
Batch query boundaries for multiple place names.
批量查询地名边界

Usage:
    python scripts/query_batch.py places.txt --output ./results
    python scripts/query_batch.py places.txt --source osm --crs wgs84

Input file format (one name per line):
    西湖风景名胜区
    黄山
    庐山
    # comments are skipped
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geoboundary.core import batch_query


def main():
    parser = argparse.ArgumentParser(description='Batch query place boundaries')
    parser.add_argument('input', help='Input file (one place name per line)')
    parser.add_argument('--output', '-o', default='./geoboundary_output',
                        help='Output directory (default: ./geoboundary_output)')
    parser.add_argument('--source', '-s', default='auto',
                        choices=['auto', 'osm', 'baidu', 'amap', 'nominatim'])
    parser.add_argument('--crs', default='wgs84', choices=['wgs84', 'gcj02'])
    args = parser.parse_args()

    # Load names
    names = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                names.append(line)

    if not names:
        print(f"No names found in {args.input}")
        sys.exit(1)

    print(f"Querying {len(names)} place names...")
    print(f"Source: {args.source} | CRS: {args.crs}")
    print(f"Output: {args.output}/")
    print()

    results = batch_query(
        names,
        source=args.source,
        crs=args.crs,
        output_dir=args.output,
    )

    found = sum(1 for _, f in results if f)
    print(f"\nDone: {found}/{len(results)} boundaries found")


if __name__ == '__main__':
    main()
