"""
Tests for geometry processing module.
几何处理模块测试
"""
import pytest
from shapely.geometry import Polygon, MultiPolygon, Point

from geoboundary.geometry import (
    parse_baidu_geo,
    convert_ring,
    rings_to_geometry,
    transform_geometry,
    geojson_to_geometry,
    parse_amap_shape,
)


class TestParseBaiduGeo:
    def test_polygon_simple(self):
        # Simple polygon: type=4, one ring
        geo_str = "4|0,0,100,100|1-10,20,30,40,50,60,10,20;"
        geo_type, data = parse_baidu_geo(geo_str)
        assert geo_type == 'polygon'
        assert len(data) == 1
        assert data[0] == [(10, 20), (30, 40), (50, 60), (10, 20)]

    def test_polygon_multi_ring(self):
        # Two rings
        geo_str = "4|0,0,100,100|1-10,20,30,40,50,60;2-70,80,90,100,110,120;"
        geo_type, data = parse_baidu_geo(geo_str)
        assert geo_type == 'polygon'
        assert len(data) == 2

    def test_point(self):
        # Point: type=1
        geo_str = "1|0,0|13375504,3509072;"
        geo_type, data = parse_baidu_geo(geo_str)
        assert geo_type == 'point'
        assert len(data) == 1
        assert data[0] == (13375504, 3509072)

    def test_invalid_type(self):
        geo_str = "3|0,0|some_data"
        geo_type, data = parse_baidu_geo(geo_str)
        assert geo_type is None

    def test_empty_string(self):
        geo_type, data = parse_baidu_geo('')
        assert geo_type is None

    def test_none_input(self):
        geo_type, data = parse_baidu_geo(None)
        assert geo_type is None

    def test_no_pipe(self):
        geo_type, data = parse_baidu_geo('no_pipe_character')
        assert geo_type is None

    def test_ring_with_fewer_than_3_points(self):
        geo_str = "4|0,0,100,100|1-10,20,30,40;"
        geo_type, data = parse_baidu_geo(geo_str)
        # Only 2 points, not enough for a polygon
        assert geo_type is None


class TestConvertRing:
    def test_identity_conversion(self):
        ring = [(1, 2), (3, 4), (5, 6)]
        result = convert_ring(ring, lambda x, y: (x, y))
        # Should close the ring
        assert result == [(1, 2), (3, 4), (5, 6), (1, 2)]

    def test_already_closed(self):
        ring = [(1, 2), (3, 4), (5, 6), (1, 2)]
        result = convert_ring(ring, lambda x, y: (x, y))
        assert result == [(1, 2), (3, 4), (5, 6), (1, 2)]

    def test_with_offset(self):
        ring = [(0, 0), (1, 0), (1, 1)]
        result = convert_ring(ring, lambda x, y: (x + 10, y + 20))
        assert result == [(10, 20), (11, 20), (11, 21), (10, 20)]


class TestRingsToGeometry:
    def test_single_ring(self):
        rings = [[(0, 0), (1, 0), (1, 1), (0, 1)]]
        geom = rings_to_geometry(rings, lambda x, y: (x, y))
        assert isinstance(geom, Polygon)
        assert geom.area > 0

    def test_two_separate_rings(self):
        # Two non-overlapping rings → MultiPolygon
        rings = [
            [(0, 0), (1, 0), (1, 1), (0, 1)],
            [(5, 5), (6, 5), (6, 6), (5, 6)],
        ]
        geom = rings_to_geometry(rings, lambda x, y: (x, y))
        assert isinstance(geom, MultiPolygon)
        assert len(geom.geoms) == 2

    def test_ring_with_hole(self):
        # Outer ring containing inner ring → Polygon with hole
        rings = [
            [(0, 0), (10, 0), (10, 10), (0, 10)],       # outer
            [(2, 2), (8, 2), (8, 8), (2, 8)],             # inner (hole)
        ]
        geom = rings_to_geometry(rings, lambda x, y: (x, y))
        assert isinstance(geom, Polygon)
        # Area should be outer - inner
        outer_area = 10 * 10
        inner_area = 6 * 6
        assert abs(geom.area - (outer_area - inner_area)) < 0.1

    def test_empty_rings(self):
        geom = rings_to_geometry([], lambda x, y: (x, y))
        assert geom is None

    def test_none_input(self):
        geom = rings_to_geometry(None, lambda x, y: (x, y))
        assert geom is None


class TestTransformGeometry:
    def test_polygon_offset(self):
        poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        result = transform_geometry(poly, lambda x, y: (x + 10, y + 20))
        bounds = result.bounds
        assert bounds[0] >= 10  # min x
        assert bounds[1] >= 20  # min y

    def test_preserves_area(self):
        poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        # Pure translation should preserve area
        result = transform_geometry(poly, lambda x, y: (x + 10, y + 20))
        assert abs(result.area - poly.area) < 0.0001


class TestGeojsonToGeometry:
    def test_polygon(self):
        geojson = {
            'type': 'Polygon',
            'coordinates': [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]]
        }
        geom = geojson_to_geometry(geojson)
        assert isinstance(geom, Polygon)
        assert geom.is_valid

    def test_multipolygon(self):
        geojson = {
            'type': 'MultiPolygon',
            'coordinates': [
                [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]],
                [[(5, 5), (6, 5), (6, 6), (5, 6), (5, 5)]],
            ]
        }
        geom = geojson_to_geometry(geojson)
        assert isinstance(geom, MultiPolygon)


class TestParseAmapShape:
    def test_valid_shape(self):
        shape_str = "120.1,30.2;120.2,30.2;120.2,30.3;120.1,30.3;120.1,30.2"
        geom = parse_amap_shape(shape_str)
        assert isinstance(geom, Polygon)
        assert geom.is_valid

    def test_auto_close(self):
        # Not closed
        shape_str = "120.1,30.2;120.2,30.2;120.2,30.3;120.1,30.3"
        geom = parse_amap_shape(shape_str)
        assert isinstance(geom, Polygon)
        assert geom.is_valid

    def test_too_few_points(self):
        shape_str = "120.1,30.2;120.2,30.2"
        geom = parse_amap_shape(shape_str)
        assert geom is None

    def test_empty(self):
        assert parse_amap_shape('') is None
        assert parse_amap_shape(None) is None
