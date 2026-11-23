"""한국 OSM 원본에서 달리기 코스 후보만 뽑아 칸(tile) 파일로 나눈다.

출력 형식은 Overpass 응답과 같다: {"elements":[{"type":"way","id":..,"tags":{..},"geometry":[{"lat":..,"lon":..}]}]}
그래서 앱의 기존 코스 해석 코드를 그대로 쓸 수 있다.

사용: python extract.py <원본.pbf> <출력폴더> [칸 크기(도), 기본 0.1]
"""
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import osmium

pbf, outdir = sys.argv[1], sys.argv[2]
TILE = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
PATHS = {"footway", "path", "cycleway"}
TOL_M = 3.0  # 모양 단순화 허용 오차(미터)


class Handler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.ways = []

    def way(self, w):
        t = w.tags
        leisure, highway, name = t.get("leisure"), t.get("highway"), t.get("name")
        if not (leisure == "track" or (leisure == "park" and name) or (highway in PATHS and name)):
            return
        try:
            pts = [(n.location.lat, n.location.lon) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        if len(pts) < 2:
            return
        tags = {k: t.get(k) for k in ("name", "leisure", "highway", "sport") if t.get(k)}
        self.ways.append((w.id, tags, pts))


def simplify(pts):
    """더글러스-포이커. 위도 기준 평면으로 근사해 미터 단위 오차로 줄인다."""
    if len(pts) < 3:
        return pts
    lat0 = math.radians(pts[0][0])
    xy = [(p[1] * 111320 * math.cos(lat0), p[0] * 110540) for p in pts]
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = xy[a], xy[b]
        dx, dy = bx - ax, by - ay
        seg = math.hypot(dx, dy)
        best, idx = 0.0, -1
        for i in range(a + 1, b):
            px, py = xy[i]
            d = abs(dy * (px - ax) - dx * (py - ay)) / seg if seg > 0 else math.hypot(px - ax, py - ay)
            if d > best:
                best, idx = d, i
        if best > TOL_M and idx > 0:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


h = Handler()
h.apply_file(pbf, locations=True, idx="flex_mem")

tiles = defaultdict(list)
raw_pts = kept_pts = 0
for wid, tags, pts in h.ways:
    raw_pts += len(pts)
    s = simplify(pts)
    kept_pts += len(s)
    el = {
        "type": "way",
        "id": wid,
        "tags": tags,
        "geometry": [{"lat": round(a, 5), "lon": round(o, 5)} for a, o in s],
    }
    for key in {(math.floor(a / TILE), math.floor(o / TILE)) for a, o in s}:
        tiles[key].append(el)

os.makedirs(outdir, exist_ok=True)
sizes = []
for (ty, tx), els in tiles.items():
    data = json.dumps({"elements": els}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with open(os.path.join(outdir, f"{ty}_{tx}.json"), "wb") as f:
        f.write(data)
    sizes.append(len(data))

with open(os.path.join(outdir, "meta.json"), "w", encoding="utf-8") as f:
    json.dump({
        "tile": TILE,
        "ways": len(h.ways),
        "tiles": len(tiles),
        "source": os.environ.get("SOURCE_DATE", ""),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }, f)

sizes.sort()
print(f"ways={len(h.ways)} points {raw_pts}->{kept_pts} tiles={len(tiles)} tile={TILE}")
print(f"total={sum(sizes) / 1e6:.1f}MB median={sizes[len(sizes) // 2] / 1e3:.1f}KB "
      f"p95={sizes[int(len(sizes) * .95)] / 1e3:.1f}KB max={sizes[-1] / 1e3:.1f}KB")
