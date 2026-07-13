"""
Tests for coordinate transformation module.
坐标转换模块测试
"""
import math
import pytest

from geoboundary.coord_transform import (
    bd09mc_to_bd09,
    bd09mc_to_wgs84,
    bd09mc_to_gcj02,
    bd09_to_gcj02,
    gcj02_to_wgs84,
    wgs84_to_gcj02,
    gcj02_to_bd09,
    wgs84_to_bd09,
    bd09_to_wgs84,
)


# Known test point: West Lake (西湖) first coordinate in BD-09 MC
XIHU_BD09MC = (13375504.5348571, 3509072.6704933)
# Expected approximate WGS84 result (West Lake center ≈ 120.15, 30.25)
XIHU_WGS84_APPROX = (120.15, 30.25)


class TestBd09mcToBd09:
    def test_xihu_point(self):
        lng, lat = bd09mc_to_bd09(*XIHU_BD09MC)
        # BD-09 should be close to 120.16, 30.25 (with Baidu offset)
        assert 120.0 < lng < 121.0
        assert 30.0 < lat < 31.0

    def test_negative_coordinates(self):
        # Southern hemisphere point
        lng, lat = bd09mc_to_bd09(-13375504.0, -3509072.0)
        assert lng < 0
        assert lat < 0

    def test_zero_point(self):
        lng, lat = bd09mc_to_bd09(0, 0)
        assert abs(lng) < 1
        assert abs(lat) < 1


class TestBd09ToGcj02:
    def test_basic_conversion(self):
        # BD-09 to GCJ-02 should remove ~0.006 degree offset
        bd_lng, bd_lat = 120.16, 30.26
        gcj_lng, gcj_lat = bd09_to_gcj02(bd_lng, bd_lat)
        assert abs(gcj_lng - bd_lng) < 0.01
        assert abs(gcj_lat - bd_lat) < 0.01

    def test_roundtrip(self):
        # BD-09 → GCJ-02 → BD-09 should be close to original
        original_lng, original_lat = 116.404, 39.915  # Beijing
        gcj_lng, gcj_lat = bd09_to_gcj02(original_lng, original_lat)
        back_lng, back_lat = gcj02_to_bd09(gcj_lng, gcj_lat)
        assert abs(back_lng - original_lng) < 0.0001
        assert abs(back_lat - original_lat) < 0.0001


class TestGcj02ToWgs84:
    def test_beijing_point(self):
        # Beijing: GCJ-02 ≈ (116.404, 39.915), WGS84 should differ by <0.01°
        wgs_lng, wgs_lat = gcj02_to_wgs84(116.404, 39.915)
        assert abs(wgs_lng - 116.404) < 0.01
        assert abs(wgs_lat - 39.915) < 0.01

    def test_accuracy(self):
        # WGS84 → GCJ-02 → WGS84 roundtrip should be < 0.5m
        # 0.5m ≈ 0.0000045° at equator
        original_lng, original_lat = 120.15, 30.25
        gcj_lng, gcj_lat = wgs84_to_gcj02(original_lng, original_lat)
        back_lng, back_lat = gcj02_to_wgs84(gcj_lng, gcj_lat)
        # Allow 0.000005° tolerance (≈ 0.5m)
        assert abs(back_lng - original_lng) < 0.000005
        assert abs(back_lat - original_lat) < 0.000005

    def test_multiple_locations(self):
        """Test accuracy across different regions of China."""
        test_points = [
            (116.404, 39.915),   # Beijing
            (121.474, 31.230),   # Shanghai
            (120.150, 30.250),   # Hangzhou
            (104.066, 30.572),   # Chengdu
            (113.264, 23.129),   # Guangzhou
        ]
        for lng, lat in test_points:
            gcj_lng, gcj_lat = wgs84_to_gcj02(lng, lat)
            back_lng, back_lat = gcj02_to_wgs84(gcj_lng, gcj_lat)
            assert abs(back_lng - lng) < 0.000005, f"Failed at ({lng}, {lat})"
            assert abs(back_lat - lat) < 0.000005, f"Failed at ({lng}, {lat})"


class TestFullChain:
    def test_bd09mc_to_wgs84(self):
        """Full chain: BD-09 MC → WGS84 for West Lake."""
        lng, lat = bd09mc_to_wgs84(*XIHU_BD09MC)
        # Should be near West Lake (120.15, 30.25)
        assert abs(lng - XIHU_WGS84_APPROX[0]) < 0.02
        assert abs(lat - XIHU_WGS84_APPROX[1]) < 0.02

    def test_bd09mc_to_gcj02(self):
        """BD-09 MC → GCJ-02 for West Lake."""
        lng, lat = bd09mc_to_gcj02(*XIHU_BD09MC)
        # GCJ-02 has offset from WGS84, but still near 120.15, 30.25
        assert abs(lng - 120.15) < 0.02
        assert abs(lat - 30.25) < 0.02

    def test_bd09_to_wgs84(self):
        """BD-09 → WGS84 shortcut."""
        lng, lat = bd09_to_wgs84(120.16, 30.26)
        assert 120.0 < lng < 121.0
        assert 30.0 < lat < 31.0

    def test_wgs84_to_bd09(self):
        """WGS84 → BD-09."""
        lng, lat = wgs84_to_bd09(120.15, 30.25)
        assert 120.0 < lng < 121.0
        assert 30.0 < lat < 31.0


class TestEdgeCases:
    def test_extreme_latitude(self):
        """Test near polar regions."""
        lng, lat = gcj02_to_wgs84(116.0, 1.0)
        assert 115 < lng < 117
        assert 0 < lat < 2

    def test_large_mercator_values(self):
        """Test with large BD-09 MC values."""
        lng, lat = bd09mc_to_wgs84(12000000, 5000000)
        assert -180 <= lng <= 180
        assert -90 <= lat <= 90
