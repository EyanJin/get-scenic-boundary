#!/usr/bin/env python3
"""
Query boundary for a single place name.
单个地名查询

Usage:
    python scripts/query_single.py "西湖风景名胜区"
    python scripts/query_single.py "黄山" --source baidu --crs gcj02
    python scripts/query_single.py "黄山" -o huangshan.geojson
"""
import sys
import os

# Allow running from project root without installing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geoboundary.cli import main

if __name__ == '__main__':
    main()
