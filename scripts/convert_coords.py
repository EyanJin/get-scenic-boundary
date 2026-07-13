#!/usr/bin/env python3
"""
Standalone coordinate conversion tool.
独立坐标转换工具

Usage:
    python scripts/convert_coords.py --from bd09mc --to wgs84 13375504.53 3509072.67
    python scripts/convert_coords.py --from gcj02 --to wgs84 120.15 30.25
    python scripts/convert_coords.py --from gcj02 --to wgs84 --input coords.csv
"""
import argparse
import csv
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geoboundary.coord_transform import (
    bd09mc_to_wgs84, bd09mc_to_gcj02, bd09mc_to_bd09,
    bd09_to_gcj02, bd09_to_wgs84,
    gcj02_to_wgs84, gcj02_to_bd09,
    wgs84_to_gcj02, wgs84_to_bd09,
)

CONVERTERS = {
    ('bd09mc', 'wgs84'): bd09mc_to_wgs84,
    ('bd09mc', 'gcj02'): bd09mc_to_gcj02,
    ('bd09mc', 'bd09'): bd09mc_to_bd09,
    ('bd09', 'gcj02'): bd09_to_gcj02,
    ('bd09', 'wgs84'): bd09_to_wgs84,
    ('gcj02', 'wgs84'): gcj02_to_wgs84,
    ('gcj02', 'bd09'): gcj02_to_bd09,
    ('wgs84', 'gcj02'): wgs84_to_gcj02,
    ('wgs84', 'bd09'): wgs84_to_bd09,
}

CRS_OPTIONS = ['wgs84', 'gcj02', 'bd09', 'bd09mc']


def main():
    parser = argparse.ArgumentParser(
        description='Convert coordinates between Chinese map coordinate systems'
    )
    parser.add_argument('x', nargs='?', type=float, help='X coordinate (longitude)')
    parser.add_argument('y', nargs='?', type=float, help='Y coordinate (latitude)')
    parser.add_argument('--from', dest='src', required=True, choices=CRS_OPTIONS,
                        help='Source coordinate system')
    parser.add_argument('--to', dest='dst', required=True, choices=CRS_OPTIONS,
                        help='Target coordinate system')
    parser.add_argument('--input', '-i', metavar='FILE',
                        help='CSV input file (columns: x/lng, y/lat)')
    parser.add_argument('--output', '-o', metavar='FILE',
                        help='CSV output file (default: stdout)')
    args = parser.parse_args()

    key = (args.src, args.dst)
    if key not in CONVERTERS:
        if args.src == args.dst:
            converter = lambda x, y: (x, y)
        else:
            print(f"Error: conversion from {args.src} to {args.dst} not supported",
                  file=sys.stderr)
            print(f"Supported: {list(CONVERTERS.keys())}", file=sys.stderr)
            sys.exit(1)
    else:
        converter = CONVERTERS[key]

    # Single point mode
    if args.x is not None and args.y is not None:
        out_x, out_y = converter(args.x, args.y)
        print(f"{args.src}: ({args.x}, {args.y})")
        print(f"{args.dst}: ({out_x:.8f}, {out_y:.8f})")
        return

    # CSV batch mode
    if not args.input:
        parser.print_help()
        sys.exit(1)

    rows = []
    with open(args.input, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 2:
                try:
                    x, y = float(row[0]), float(row[1])
                    ox, oy = converter(x, y)
                    rows.append([ox, oy] + row[2:])
                except ValueError:
                    rows.append(row)

    # Output
    out_file = open(args.output, 'w', encoding='utf-8', newline='') if args.output else sys.stdout
    writer = csv.writer(out_file)
    writer.writerow([f'lng_{args.dst}', f'lat_{args.dst}'] + (header[2:] if header and len(header) > 2 else []))
    for row in rows:
        writer.writerow(row)
    if args.output:
        out_file.close()
        print(f"Saved: {args.output} ({len(rows)} points)")


if __name__ == '__main__':
    main()
