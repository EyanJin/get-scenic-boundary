"""
Export module — output boundaries in various formats.
导出模块 — 将边界数据输出为多种格式
"""
import json
import csv
import os
from pathlib import Path


def to_geojson(features, output_path=None, indent=2):
    """Export features as GeoJSON FeatureCollection.
    导出为 GeoJSON FeatureCollection

    Args:
        features: list of dicts with 'geometry' (Shapely) and properties
        output_path: file path to write (None = return dict)
        indent: JSON indent (use None for compact)

    Returns:
        GeoJSON dict if output_path is None
    """
    from shapely.geometry import mapping

    fc = {
        'type': 'FeatureCollection',
        'features': []
    }

    for feat in features:
        geom = feat.get('geometry')
        if geom is None:
            continue
        properties = {k: v for k, v in feat.items() if k != 'geometry'}
        fc['features'].append({
            'type': 'Feature',
            'geometry': mapping(geom),
            'properties': properties,
        })

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(fc, f, ensure_ascii=False, indent=indent)
        return str(output_path)

    return fc


def to_geojson_feature(geometry, properties=None):
    """Create a single GeoJSON Feature dict.
    创建单个 GeoJSON Feature

    Args:
        geometry: Shapely geometry
        properties: dict of feature properties

    Returns:
        GeoJSON Feature dict
    """
    from shapely.geometry import mapping

    return {
        'type': 'Feature',
        'geometry': mapping(geometry),
        'properties': properties or {},
    }


def to_shapefile(features, output_path, crs='EPSG:4326'):
    """Export features as Shapefile.
    导出为 Shapefile

    Requires geopandas (install with: pip install geoboundary[export])

    Args:
        features: list of dicts with 'geometry' (Shapely) and properties
        output_path: .shp file path
        crs: coordinate reference system (default EPSG:4326)
    """
    try:
        import geopandas as gpd
    except ImportError:
        raise ImportError(
            "geopandas is required for Shapefile export. "
            "Install with: pip install geoboundary[export]"
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    gdf = gpd.GeoDataFrame(features, crs=crs)
    gdf.to_file(str(output_path), encoding='utf-8')
    return str(output_path)


def to_csv(features, output_path, include_wkt=True):
    """Export features as CSV with WKT geometry column.
    导出为 CSV（含 WKT 几何列）

    Args:
        features: list of dicts with 'geometry' (Shapely) and properties
        output_path: .csv file path
        include_wkt: include WKT geometry column
    """
    if not features:
        return None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine field names from first feature
    fieldnames = [k for k in features[0].keys() if k != 'geometry']
    if include_wkt:
        fieldnames.append('wkt')

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for feat in features:
            row = {k: v for k, v in feat.items() if k != 'geometry'}
            if include_wkt and feat.get('geometry'):
                row['wkt'] = feat['geometry'].wkt
            writer.writerow(row)

    return str(output_path)


def to_wkt(geometry):
    """Return WKT string for a geometry.
    返回几何体的 WKT 字符串
    """
    if geometry is None:
        return None
    return geometry.wkt
