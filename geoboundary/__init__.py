"""
geoboundary — Get boundary polygon for any place name from map services.
地名边界获取工具 — 从地图服务获取任意地名的边界多边形

Usage:
    from geoboundary import get_boundary, batch_query
    result = get_boundary("西湖风景名胜区")
"""

__version__ = "0.1.0"

from geoboundary.core import get_boundary, batch_query
from geoboundary.coord_transform import (
    bd09mc_to_wgs84,
    bd09mc_to_gcj02,
    bd09mc_to_bd09,
    bd09_to_gcj02,
    gcj02_to_bd09,
    gcj02_to_wgs84,
    wgs84_to_gcj02,
    wgs84_to_bd09,
    bd09_to_wgs84,
)

__all__ = [
    'get_boundary',
    'batch_query',
    'bd09mc_to_wgs84',
    'bd09mc_to_gcj02',
    'bd09mc_to_bd09',
    'bd09_to_gcj02',
    'gcj02_to_bd09',
    'gcj02_to_wgs84',
    'wgs84_to_gcj02',
    'wgs84_to_bd09',
    'bd09_to_wgs84',
]
