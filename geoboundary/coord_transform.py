"""
Coordinate transformation module for Chinese map services.
坐标转换模块：支持 BD-09 MC / BD-09 / GCJ-02 / WGS84 互转

Zero external dependencies (only uses math).
All functions accept (lng, lat) or (x, y) and return (lng, lat).

Accuracy: < 0.5m for GCJ-02 ↔ WGS84 (5-iteration convergence)

Coordinate Systems:
  - WGS84: International standard (GPS, OpenStreetMap)
  - GCJ-02: Chinese national standard (Amap/高德, Tencent Maps)
  - BD-09: Baidu Maps latitude/longitude
  - BD-09 MC: Baidu Maps Mercator projection (raw API responses)
"""
import math

PI = math.pi
X_PI = PI * 3000.0 / 180.0
A = 6378245.0  # Semi-major axis (长半轴)
EE = 0.00669342162296594323  # Eccentricity squared (偏心率平方)

# Baidu Mercator band thresholds and polynomial coefficients
MCBAND = [12890594.86, 8362377.87, 5591021.0, 3481989.83, 1678043.12, 0]
MC2LL = [
    [1.410526172116255e-8, 8.98305509648872e-6, -1.9939833816331,
     200.9824383106796, -187.2403703815547, 91.6087516669843,
     -23.38765649603339, 2.57121317296198, -0.03801003308653, 17337981.2],
    [-7.435856389565537e-9, 8.983055097726239e-6, -0.78625201886289,
     96.32687599759846, -1.85204757529826, -59.36935905485877,
     47.40033549296737, -16.50741931063887, 2.28786674699375, 10260144.86],
    [-3.030883460898826e-8, 8.98305509983578e-6, 0.30071316287616,
     59.74293618442277, 7.357984074871, -25.38371002664745,
     13.45380521110908, -3.29883767235584, 0.32710905363475, 6856817.37],
    [-1.981981304930552e-8, 8.983055099779535e-6, 0.03278182852591,
     40.31678527705744, 0.65659298677277, -4.44255534477492,
     0.85341911805263, 0.12923347998204, -0.04625736007561, 4482777.06],
    [3.09191371068437e-9, 8.983055096812155e-6, 6.995724062e-5,
     23.10934304144901, -0.00023663490511, -0.6321817810242,
     -0.00663494467042, 0.03430082397953, -0.00466043876332, 2555164.4],
    [2.890871144776878e-9, 8.983055095805407e-6, -3.068298e-8,
     7.47137025468032, -3.56722925735e-5, -0.02117647551069,
     4.01673318142e-5, 7.849639672e-5, -3.23514337524e-5, 826088.5],
]


# ========== BD-09 MC → BD-09 ==========

def bd09mc_to_bd09(x, y):
    """Baidu Mercator → BD-09 (lat/lng)
    百度墨卡托投影坐标 → BD-09 经纬度
    """
    cF = None
    y_abs = abs(y)
    for i, band in enumerate(MCBAND):
        if y_abs >= band:
            cF = MC2LL[i]
            break
    if cF is None:
        cF = MC2LL[-1]

    T = cF
    lng = T[0] + T[1] * abs(x)
    c = abs(y) / T[9]
    lat = (T[2] + T[3] * c + T[4] * c * c + T[5] * c ** 3 +
           T[6] * c ** 4 + T[7] * c ** 5 + T[8] * c ** 6)
    lng = lng * (-1 if x < 0 else 1)
    lat = lat * (-1 if y < 0 else 1)
    return lng, lat


# ========== BD-09 ↔ GCJ-02 ==========

def bd09_to_gcj02(bd_lng, bd_lat):
    """BD-09 → GCJ-02"""
    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * X_PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * X_PI)
    gcj_lng = z * math.cos(theta)
    gcj_lat = z * math.sin(theta)
    return gcj_lng, gcj_lat


def gcj02_to_bd09(lng, lat):
    """GCJ-02 → BD-09"""
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * X_PI)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * X_PI)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lng, bd_lat


# ========== GCJ-02 ↔ WGS84 ==========

def _transform_lat(lng, lat):
    ret = (-100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat +
           0.1 * lng * lat + 0.2 * math.sqrt(abs(lng)))
    ret += (20.0 * math.sin(6.0 * lng * PI) +
            20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * PI) +
            40.0 * math.sin(lat / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * PI) +
            320.0 * math.sin(lat * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(lng, lat):
    ret = (300.0 + lng + 2.0 * lat + 0.1 * lng * lng +
           0.1 * lng * lat + 0.1 * math.sqrt(abs(lng)))
    ret += (20.0 * math.sin(6.0 * lng * PI) +
            20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * PI) +
            40.0 * math.sin(lng / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * PI) +
            300.0 * math.sin(lng / 30.0 * PI)) * 2.0 / 3.0
    return ret


def wgs84_to_gcj02(lng, lat):
    """WGS84 → GCJ-02"""
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    return lng + dlng, lat + dlat


def gcj02_to_wgs84(lng, lat):
    """GCJ-02 → WGS84 (iterative, accuracy < 0.5m)
    GCJ-02 → WGS84（迭代法，精度 < 0.5 米）
    """
    wlng, wlat = lng, lat
    for _ in range(5):
        glng, glat = wgs84_to_gcj02(wlng, wlat)
        wlng += lng - glng
        wlat += lat - glat
    return wlng, wlat


# ========== Composite transforms 组合转换 ==========

def bd09mc_to_wgs84(x, y):
    """Baidu Mercator → WGS84 (full chain)
    百度墨卡托 → WGS84（完整链路）
    """
    bd_lng, bd_lat = bd09mc_to_bd09(x, y)
    gcj_lng, gcj_lat = bd09_to_gcj02(bd_lng, bd_lat)
    return gcj02_to_wgs84(gcj_lng, gcj_lat)


def bd09mc_to_gcj02(x, y):
    """Baidu Mercator → GCJ-02
    百度墨卡托 → GCJ-02
    """
    bd_lng, bd_lat = bd09mc_to_bd09(x, y)
    return bd09_to_gcj02(bd_lng, bd_lat)


def wgs84_to_bd09(lng, lat):
    """WGS84 → BD-09"""
    gcj_lng, gcj_lat = wgs84_to_gcj02(lng, lat)
    return gcj02_to_bd09(gcj_lng, gcj_lat)


def bd09_to_wgs84(bd_lng, bd_lat):
    """BD-09 → WGS84"""
    gcj_lng, gcj_lat = bd09_to_gcj02(bd_lng, bd_lat)
    return gcj02_to_wgs84(gcj_lng, gcj_lat)
