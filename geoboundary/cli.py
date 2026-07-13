"""
CLI entry point — command-line interface for geoboundary.
命令行界面

Usage:
    geoboundary "西湖风景名胜区"
    geoboundary "黄山" --source baidu --crs gcj02
    geoboundary "黄山" -o huangshan.geojson
    geoboundary --batch places.txt -o boundaries/
"""
import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(
        prog='get-scenic-boundary',
        description='Get boundary polygons for Chinese scenic areas from map services.\n'
                    '中国风景名胜区边界数据获取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  get-scenic-boundary "西湖风景名胜区"
  get-scenic-boundary "黄山" --source baidu --crs gcj02
  get-scenic-boundary "黄山" -o huangshan.geojson
  get-scenic-boundary --batch places.txt -o ./boundaries/

Sources:
  auto (default)  Try Baidu → Amap → OSM (highest coverage first)
  baidu           Baidu Maps (best Chinese coverage, requires playwright)
  amap            Amap/高德 (requires AMAP_API_KEY in .env)
  osm             OpenStreetMap (free, no key needed)
  nominatim       Nominatim geocoding
        ''',
    )

    parser.add_argument('name', nargs='?', help='Place name to query (地名)')
    parser.add_argument('--batch', '-b', metavar='FILE',
                        help='Batch mode: file with one place name per line')
    parser.add_argument('--source', '-s', default='auto',
                        choices=['auto', 'osm', 'baidu', 'amap', 'nominatim'],
                        help='Data source (default: auto)')
    parser.add_argument('--crs', default='wgs84',
                        choices=['wgs84', 'gcj02'],
                        help='Output coordinate system (default: wgs84)')
    parser.add_argument('--output', '-o', metavar='PATH',
                        help='Output file path (.geojson) or directory (batch mode)')
    parser.add_argument('--format', '-f', default='geojson',
                        choices=['geojson', 'wkt', 'shapefile'],
                        help='Output format (default: geojson)')
    parser.add_argument('--province', '-p', default='',
                        help='Province hint for disambiguation (省份提示)')
    parser.add_argument('--open', action='store_true',
                        help='Open result in geojson.io for visual preview (在浏览器中预览)')
    parser.add_argument('--no-resume', action='store_true',
                        help='Disable resume: re-query all names even if cached (禁用断点续传)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress progress output')
    parser.add_argument('--version', '-V', action='version',
                        version='%(prog)s 0.1.0')

    args = parser.parse_args()

    if not args.name and not args.batch:
        parser.print_help()
        sys.exit(1)

    from geoboundary.core import get_boundary, batch_query

    # Batch mode
    if args.batch:
        names = _load_batch_file(args.batch)
        if not names:
            print(f"Error: no names found in {args.batch}", file=sys.stderr)
            sys.exit(1)

        output_dir = args.output or './geoboundary_output'
        results = batch_query(
            names,
            source=args.source,
            crs=args.crs,
            output_dir=output_dir,
            progress=not args.quiet,
            resume=not args.no_resume,
        )

        found = sum(1 for _, f in results if f)
        if not args.quiet:
            print(f"\nDone: {found}/{len(results)} boundaries found")
            print(f"Output: {output_dir}/")
            print(f"Merged: {output_dir}/_merged.geojson")
        return

    # Single query
    result = get_boundary(
        args.name,
        source=args.source,
        crs=args.crs,
        province=args.province,
    )

    if not result:
        if not args.quiet:
            print(f"No boundary found for: {args.name}", file=sys.stderr)
            print(file=sys.stderr)
            # Diagnose why
            _print_source_hints(args.source)
        sys.exit(1)

    # Output
    if args.format == 'wkt':
        from shapely.geometry import shape
        geom = shape(result['geometry'])
        output_str = geom.wkt
    elif args.format == 'shapefile':
        if not args.output:
            print("Error: --output required for shapefile format", file=sys.stderr)
            sys.exit(1)
        from shapely.geometry import shape
        from geoboundary.export import to_shapefile
        geom = shape(result['geometry'])
        record = {**result.get('properties', {}), 'geometry': geom}
        to_shapefile([record], args.output, crs='EPSG:4326')
        if not args.quiet:
            print(f"Saved: {args.output}")
        return
    else:
        output_str = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_str)
        if not args.quiet:
            print(f"Saved: {args.output}")
    else:
        print(output_str)

    # Open in browser for visual preview
    if args.open:
        _open_in_geojson_io(result)


def _open_in_geojson_io(geojson_data):
    """Open GeoJSON result in geojson.io for visual preview."""
    import urllib.parse
    import webbrowser

    geojson_str = json.dumps(geojson_data, ensure_ascii=False)
    # geojson.io accepts data via URL hash
    encoded = urllib.parse.quote(geojson_str)
    url = f"https://geojson.io/#data=data:application/json,{encoded}"

    # URL length limit ~8000 chars; for large geometries, save to file first
    if len(url) > 8000:
        import tempfile
        tmp = tempfile.mktemp(suffix='.geojson')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, ensure_ascii=False)
        print(f"Boundary too large for URL preview. Saved to: {tmp}", file=sys.stderr)
        print(f"Open https://geojson.io and drag the file in.", file=sys.stderr)
        return

    webbrowser.open(url)


def _print_source_hints(source):
    """Print diagnostic hints when no boundary is found."""
    import shutil

    hints = []

    # Check Playwright availability
    try:
        import playwright
        pw_ok = True
    except ImportError:
        pw_ok = False

    # Check Amap key
    from geoboundary.config import AMAP_API_KEY
    amap_ok = bool(AMAP_API_KEY)

    if source == 'auto':
        print("Sources tried (in order):", file=sys.stderr)
        if pw_ok:
            print(f"  Baidu (百度):    available (playwright installed)", file=sys.stderr)
        else:
            print(f"  Baidu (百度):    skipped (playwright not installed)", file=sys.stderr)
            hints.append("pip install geoboundary[baidu] && playwright install chromium")
        if amap_ok:
            print(f"  Amap (高德):     available (API key configured)", file=sys.stderr)
        else:
            print(f"  Amap (高德):     skipped (no AMAP_API_KEY in .env)", file=sys.stderr)
            hints.append("Set AMAP_API_KEY in .env (free at https://lbs.amap.com)")
        print(f"  OSM (Overpass):  available, but Chinese coverage is ~20%", file=sys.stderr)

    if hints:
        print(file=sys.stderr)
        print("To improve coverage:", file=sys.stderr)
        for h in hints:
            print(f"  $ {h}", file=sys.stderr)


def _load_batch_file(filepath):
    """Load place names from a text file (one per line) or CSV."""
    names = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    names.append(line)
    except FileNotFoundError:
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    return names


if __name__ == '__main__':
    main()
