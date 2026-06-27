#!/usr/bin/env python3
"""Build simplified, CSV-matched South Korea GeoJSON for vanishing_map.

Input  : southkorea-maps (kostat 2018) province + municipality GeoJSON.
Output : data/korea-sido.geojson, data/korea-sigungu.geojson

Each output feature carries:
  - name      : original Korean name
  - province  : sido full name (sigungu tagged via geometric containment)
  - match     : the CSV `origin`/`destination` name this polygon belongs to
                (split 시 are folded back to their 시 name)

No runtime dependency: the website ships these files and projects them inline.
"""
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(HERE, ".geocache")

SIDO_URL = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-provinces-2018-geo.json"
SIGUNGU_URL = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-municipalities-2018-geo.json"

# Rename GeoJSON(2018) sido names to the CSV/website canonical names.
CANON_SIDO = {"강원도": "강원특별자치도", "전라북도": "전북특별자치도"}

# CSV reports these cities at 시 level; GeoJSON splits them into 구 with the
# 시 prefixed into the name (e.g. "수원시장안구"). Fold by prefix back to the 시.
SPLIT_CITIES = ["수원시", "성남시", "안양시", "안산시", "고양시", "용인시",
                "창원시", "포항시", "천안시", "청주시", "전주시"]
# Names whose CSV form differs from the GeoJSON(2018) name (province-scoped to
# avoid ambiguity: 남구 also exists in 부산/대구/광주/울산).
NAME_REMAP = {
    ("세종특별자치시", "세종시"): "세종특별자치시",
    ("인천광역시", "남구"): "미추홀구",  # 인천 남구 -> 미추홀구 (renamed 2018)
}
# 군위군 moved 경상북도 -> 대구광역시 in 2023; CSV reflects this, GeoJSON(2018) does not.
PROVINCE_OVERRIDE = {"군위군": "대구광역시"}


def fold_match(province, name):
    """Return the CSV name this polygon belongs to."""
    if (province, name) in NAME_REMAP:
        return NAME_REMAP[(province, name)]
    for city in SPLIT_CITIES:
        if name.startswith(city):
            return city
    return name


def fetch(url, name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print(f"downloading {name} ...")
        urllib.request.urlretrieve(url, path)
    with open(path) as f:
        return json.load(f)


def each_ring(geom):
    """Yield each linear ring (list of [lon,lat]) of a Polygon/MultiPolygon."""
    t = geom["type"]
    if t == "Polygon":
        for ring in geom["coordinates"]:
            yield ring
    elif t == "MultiPolygon":
        for poly in geom["coordinates"]:
            for ring in poly:
                yield ring


def point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def point_in_geom(x, y, geom):
    """Even-odd test across all rings (outer adds, holes subtract)."""
    inside = False
    for ring in each_ring(geom):
        if point_in_ring(x, y, ring):
            inside = not inside
    return inside


def representative_point(geom):
    """A point guaranteed to lie inside the geometry.

    Try the largest ring's vertex average; if that falls in a hole or sea
    (concave/coastal shapes), scan a grid over the bbox for the first inside
    point. This keeps sigungo->sido containment correct.
    """
    best, best_len = None, -1
    for ring in each_ring(geom):
        if len(ring) > best_len:
            best, best_len = ring, len(ring)
    sx = sum(p[0] for p in best) / len(best)
    sy = sum(p[1] for p in best) / len(best)
    if point_in_geom(sx, sy, geom):
        return sx, sy
    xs = [p[0] for p in best]
    ys = [p[1] for p in best]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    n = 12
    for i in range(1, n):
        for j in range(1, n):
            x = x0 + (x1 - x0) * i / n
            y = y0 + (y1 - y0) * j / n
            if point_in_geom(x, y, geom):
                return x, y
    return sx, sy


# ---- Douglas-Peucker simplification ------------------------------------
def _dp(points, eps):
    if len(points) < 3:
        return points
    ax, ay = points[0]
    bx, by = points[-1]
    dx, dy = bx - ax, by - ay
    denom = (dx * dx + dy * dy) ** 0.5 or 1e-12
    dmax, idx = 0.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        d = abs(dx * (ay - py) - (ax - px) * dy) / denom
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        left = _dp(points[: idx + 1], eps)
        right = _dp(points[idx:], eps)
        return left[:-1] + right
    return [points[0], points[-1]]


def round_pt(p, nd=4):
    return [round(p[0], nd), round(p[1], nd)]


def simplify_ring(ring, eps):
    if len(ring) <= 4:
        return [round_pt(p) for p in ring]
    closed = ring[0] == ring[-1]
    if closed:
        # A closed ring's start->end chord is degenerate, which collapses DP.
        # Split at the vertex farthest from the start and simplify both arcs.
        pts = ring[:-1]
        x0, y0 = pts[0]
        far = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
        a = _dp(pts[: far + 1], eps)
        b = _dp(pts[far:] + [pts[0]], eps)
        s = a[:-1] + b
        if s[0] != s[-1]:
            s = s + [s[0]]
    else:
        s = _dp(ring, eps)
    if len(s) < 4:  # keep a valid ring
        s = ring[:: max(1, len(ring) // 4)]
        if s[0] != s[-1]:
            s = s + [s[0]]
    return [round_pt(p) for p in s]


def simplify_geom(geom, eps):
    t = geom["type"]
    if t == "Polygon":
        rings = [simplify_ring(r, eps) for r in geom["coordinates"]]
        return {"type": "Polygon", "coordinates": [r for r in rings if len(r) >= 4]}
    polys = []
    for poly in geom["coordinates"]:
        rings = [simplify_ring(r, eps) for r in poly]
        rings = [r for r in rings if len(r) >= 4]
        if rings:
            polys.append(rings)
    return {"type": "MultiPolygon", "coordinates": polys}


def build():
    sido = fetch(SIDO_URL, "sido.json")
    sigungu = fetch(SIGUNGU_URL, "sigungu.json")

    # --- sido: standard 2-digit code, rename to canonical names ---
    sido_out = []
    for f in sido["features"]:
        name = CANON_SIDO.get(f["properties"]["name"], f["properties"]["name"])
        sido_out.append({
            "type": "Feature",
            "properties": {"name": name, "code": f["properties"]["code"],
                           "province": name, "match": name},
            "geometry": simplify_geom(f["geometry"], 0.0025),
        })

    # --- sigungu: tag province by geometric containment ---
    missing_prov = 0
    sig_out = []
    for f in sigungu["features"]:
        name = f["properties"]["name"]
        if name in PROVINCE_OVERRIDE:
            province = PROVINCE_OVERRIDE[name]
        else:
            rx, ry = representative_point(f["geometry"])
            province = None
            for sf in sido["features"]:
                if point_in_geom(rx, ry, sf["geometry"]):
                    province = CANON_SIDO.get(sf["properties"]["name"], sf["properties"]["name"])
                    break
            if province is None:  # fallback: nearest sido centroid
                best_d = None
                for sf in sido["features"]:
                    cx, cy = representative_point(sf["geometry"])
                    d = (cx - rx) ** 2 + (cy - ry) ** 2
                    if best_d is None or d < best_d:
                        best_d, province = d, CANON_SIDO.get(
                            sf["properties"]["name"], sf["properties"]["name"])
                missing_prov += 1

        sig_out.append({
            "type": "Feature",
            "properties": {"name": name, "code": f["properties"]["code"],
                           "province": province, "match": fold_match(province, name)},
            "geometry": simplify_geom(f["geometry"], 0.0016),
        })

    write(os.path.join(DATA, "korea-sido.geojson"), sido_out)
    write(os.path.join(DATA, "korea-sigungu.geojson"), sig_out)

    print(f"sido features   : {len(sido_out)}")
    print(f"sigungu features: {len(sig_out)}  (fallback-prov: {missing_prov})")
    verify(sig_out)


def write(path, features):
    fc = {"type": "FeatureCollection", "features": features}
    with open(path, "w") as f:
        json.dump(fc, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {os.path.relpath(path, ROOT)}  {os.path.getsize(path)//1024} KB")


def verify(sig_out):
    """Cross-check CSV origin names resolve to a polygon via `match`."""
    import csv
    csv_path = os.path.join(DATA, "mois-ppltn-data-stus-sigungu-od-202605-age-gender.csv")
    if not os.path.exists(csv_path):
        return
    match_by_prov = {}
    for f in sig_out:
        p = f["properties"]
        match_by_prov.setdefault(p["province"], set()).add(p["match"])
    miss = []
    seen = set()
    with open(csv_path) as fh:
        for r in csv.DictReader(fh):
            key = (r["origin_province"], r["origin"])
            if key in seen:
                continue
            seen.add(key)
            prov, name = key
            if name not in match_by_prov.get(prov, set()):
                miss.append(key)
    print(f"CSV names unmatched: {len(miss)}")
    for k in miss[:20]:
        print("   ", k)


if __name__ == "__main__":
    build()
