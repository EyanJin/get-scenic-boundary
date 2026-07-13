"""
Tests for export module.
导出模块测试
"""
import json
import os
import tempfile
import pytest
from shapely.geometry import Polygon, Point

from geoboundary.export import to_geojson, to_geojson_feature, to_csv, to_wkt


@pytest.fixture
def sample_features():
    """Create sample features for testing."""
    return [
        {
            'name': '西湖',
            'source': 'osm',
            'geometry': Polygon([(120.1, 30.2), (120.2, 30.2), (120.2, 30.3), (120.1, 30.3)]),
        },
        {
            'name': '黄山',
            'source': 'baidu',
            'geometry': Polygon([(118.1, 30.1), (118.2, 30.1), (118.2, 30.2), (118.1, 30.2)]),
        },
    ]


class TestToGeojson:
    def test_returns_dict(self, sample_features):
        result = to_geojson(sample_features)
        assert result['type'] == 'FeatureCollection'
        assert len(result['features']) == 2

    def test_feature_structure(self, sample_features):
        result = to_geojson(sample_features)
        feat = result['features'][0]
        assert feat['type'] == 'Feature'
        assert 'geometry' in feat
        assert 'properties' in feat
        assert feat['properties']['name'] == '西湖'

    def test_geometry_type(self, sample_features):
        result = to_geojson(sample_features)
        assert result['features'][0]['geometry']['type'] == 'Polygon'

    def test_write_to_file(self, sample_features):
        with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False, mode='w') as f:
            filepath = f.name
        try:
            to_geojson(sample_features, filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert data['type'] == 'FeatureCollection'
            assert len(data['features']) == 2
        finally:
            os.unlink(filepath)

    def test_empty_features(self):
        result = to_geojson([])
        assert result['type'] == 'FeatureCollection'
        assert result['features'] == []

    def test_skip_none_geometry(self):
        features = [{'name': 'test', 'geometry': None}]
        result = to_geojson(features)
        assert len(result['features']) == 0


class TestToGeojsonFeature:
    def test_basic(self):
        geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        result = to_geojson_feature(geom, {'name': 'test'})
        assert result['type'] == 'Feature'
        assert result['geometry']['type'] == 'Polygon'
        assert result['properties']['name'] == 'test'

    def test_no_properties(self):
        geom = Point(120.15, 30.25)
        result = to_geojson_feature(geom)
        assert result['properties'] == {}


class TestToCsv:
    def test_write_csv(self, sample_features):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
            filepath = f.name
        try:
            to_csv(sample_features, filepath)
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            assert len(lines) == 3  # header + 2 rows
            assert 'wkt' in lines[0]
            assert 'POLYGON' in lines[1]
        finally:
            os.unlink(filepath)

    def test_empty_features(self):
        result = to_csv([], 'dummy.csv')
        assert result is None


class TestToWkt:
    def test_polygon(self):
        geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        wkt = to_wkt(geom)
        assert 'POLYGON' in wkt

    def test_none(self):
        assert to_wkt(None) is None
