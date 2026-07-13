"""
Configuration module — loads settings from environment variables / .env file.
配置模块 — 从环境变量或 .env 文件加载设置
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Look for .env in project root or current directory
    for env_path in [Path.cwd() / '.env', Path(__file__).parent.parent / '.env']:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass


# Amap (高德) API key — get free at https://lbs.amap.com/dev/key
AMAP_API_KEY = os.getenv('AMAP_API_KEY', '')

# Overpass API endpoint (OSM)
OVERPASS_URL = os.getenv('OVERPASS_URL', 'https://overpass-api.de/api/interpreter')

# Request delay in seconds (avoid rate limiting)
REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '2'))

# User-Agent for HTTP requests
USER_AGENT = os.getenv('USER_AGENT', 'geoboundary/0.1.0')

# Browser settings
BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true'
BROWSER_VIEWPORT = {'width': 1280, 'height': 800}
BROWSER_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)
