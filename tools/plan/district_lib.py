"""The rules worked out in district A (Marcel, 2026-11-10), as one library so every district is built the same way.

  streets   real widths; kerb radii at the junctions; a district's streets stop at the far kerb of a main road
  houses    one by one: 5.5 m wide along the street, 9 m deep, 1.5 m back, side walls square to the street; built only where the
            whole house fits (not on a street, main road, water, green, a kept-clear area, another house); no house ends
            slanted; no lone houses; the busier streets build first
  corners   one corner house closes the gap where two rows stop short of a corner (only if it is >= ~3 m wide everywhere)
  backs     the backland is shared out per house (nearest back wall), side walls running straight back, so the yards fill the
            block; a 3 m ginnel on the line where two rows' yards meet (and along a main road behind a row); rear
            extensions 2.6 x 3.5 m in mirrored pairs; a tunnel back through the end house where a ginnel reaches no street
"""
import math

import numpy as np
import shapely
from shapely import voronoi_polygons
from shapely.geometry import LineString, MultiPoint, Point, Polygon, box
from shapely.ops import nearest_points, unary_union
from shapely.validation import make_valid

HOUSE_W, HOUSE_D, FRONT_SET = 5.5, 9.0, 1.5
GINNEL, OUT_W, OUT_D = 3.0, 2.6, 3.5
GINNEL_MIN_YARD = 5.0          # Marcel 2026-11-11: below this (median yard beside a ginnel) the ginnel goes


def clean(g, min_area=0.5):
    g = make_valid(g)
    ps = [q for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon" and q.area > min_area]
    return max(ps, key=lambda q: q.area) if ps else None


def polys(g):
    return [q for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon" and not q.is_empty]


def street_union(streets, region, main, kerb_r=6.0):
    u = unary_union([ln.buffer(w / 2) for nm, ln, w, k in streets])
    u = u.buffer(kerb_r, join_style=1).buffer(-kerb_r, join_style=1).union(u)
    return u.intersection(region.union(main.buffer(5.0)))


def blocks(view, roads, open_, region, min_area=200):
    b = box(*view).difference(roads).difference(open_).intersection(region)
    return [q for q in polys(b) if q.area > min_area]


def build_houses(streets, allowed, extra_front=()):
    """streets: (name, line, width, kind); 'ring'/'main' kinds build first. extra_front: frontage-only lines (e.g. a main road
    where houses are allowed), as (name, line, width, 'mainfront')."""
    houses = []
    order = sorted(streets, key=lambda s: 0 if s[3] in ("ring", "main") else 1) + list(extra_front)
    for nm, ln, w, k in order:
        r0, r1 = w / 2 + FRONT_SET, w / 2 + FRONT_SET + HOUSE_D
        others = unary_union([l2.buffer(w2 / 2 + 1.0) for n2, l2, w2, k2 in streets if (n2 != nm or k == "mainfront")])
        for side in (1, -1):
            def edge(d):
                p = ln.interpolate(d)
                if d + 0.5 <= ln.length:
                    q = ln.interpolate(d + 0.5)
                    tx, ty = q.x - p.x, q.y - p.y
                else:
                    q0 = ln.interpolate(d - 0.5)
                    tx, ty = p.x - q0.x, p.y - q0.y
                T = math.hypot(tx, ty) or 1
                nx_, ny_ = -ty / T * side, tx / T * side
                return (p.x + nx_ * r0, p.y + ny_ * r0), (p.x + nx_ * r1, p.y + ny_ * r1)
            d = 0.0
            while d + HOUSE_W <= ln.length:
                (f0, b0), (f1, b1) = edge(d), edge(d + HOUSE_W)
                cell = Polygon([f0, f1, b1, b0])
                if (cell.is_valid and allowed.contains(cell.buffer(-0.15)) and not cell.intersects(others)
                        and all(cell.intersection(h).area < 0.3 for h in houses if h.distance(cell) < 1)):
                    houses.append(cell)
                d += HOUSE_W
    return [h for h in houses if sum(1 for g in houses if g is not h and g.distance(h) < 0.3) >= 1]


def corner_houses(streets, houses, allowed, extra_front=()):
    bands = []
    for nm, ln, w, k in list(streets) + list(extra_front):
        r0, r1 = w / 2 + FRONT_SET, w / 2 + FRONT_SET + HOUSE_D
        bands.append((nm, ln.buffer(r1, cap_style=2).difference(ln.buffer(r0, cap_style=2))))
    built = unary_union(houses)
    gap = unary_union([b for n, b in bands]).intersection(allowed).difference(built.buffer(0.05))
    gap = gap.difference(unary_union([ln.buffer(w / 2 + 1.0) for nm, ln, w, k in streets]))
    out = []
    for g in polys(gap):
        if not (30 < g.area < 260) or g.buffer(-1.4).is_empty:
            continue
        st = [n for n, b in bands if b.intersection(g).area > 8]
        rows = sum(1 for h in houses if h.distance(g) < 0.2)
        if len(st) >= 2 and rows >= 2:
            c = clean(g.buffer(0.05).intersection(allowed), 20)
            if c is not None and all(c.intersection(h).area < 0.5 for h in houses):
                out.append(c)
    return out


def backs(houses, corners, block_list, street_u, main, no_yard, view, main_ginnel=True):
    """Yards, rear extensions, ginnels and tunnel backs. no_yard: land that is not backland (greens, squares, buildings...)."""
    corner_ids = {id(c) for c in corners}
    hu = unary_union(houses)
    backland = unary_union(block_list).difference(hu).difference(unary_union([street_u.buffer(0.5), main.buffer(6.0), no_yard]))
    backland = unary_union(polys(backland))
    # rows: houses joined wall to wall (a corner house is its own row)
    row_of, rid = {}, 0
    for h in houses:
        if id(h) in row_of:
            continue
        row_of[id(h)] = rid
        stack = [h]
        while stack and id(h) not in corner_ids:
            g = stack.pop()
            for k in houses:
                if id(k) not in row_of and id(k) not in corner_ids and k.distance(g) < 0.3:
                    row_of[id(k)] = rid
                    stack.append(k)
        rid += 1

    def back_edge(h):
        cs = list(h.exterior.coords)[:-1]
        if len(cs) == 4 and id(h) not in corner_ids:
            return LineString([cs[3], cs[2]])
        return h.exterior.difference(street_u.buffer(1.0))

    pts, own = [], []
    for i, h in enumerate(houses):
        e = back_edge(h)
        for seg in getattr(e, "geoms", [e]):
            if seg.geom_type != "LineString" or seg.length < 0.2:
                continue
            for d in np.arange(0.25, seg.length, 0.5):
                q = seg.interpolate(d)
                pts.append((q.x, q.y))
                own.append(i)
    vor = voronoi_polygons(MultiPoint(pts), extend_to=box(*view).buffer(50), ordered=True)
    terr = {}
    for k, cell in enumerate(vor.geoms):
        terr.setdefault(own[k], []).append(cell)
    bl_parts = polys(backland)
    terr = {i: shapely.union_all([c.buffer(0.001) for c in v], grid_size=0.01) for i, v in terr.items()}
    terr = {i: unary_union([t.intersection(q) for q in bl_parts if q.intersects(back_edge(houses[i]).buffer(0.8))])
            for i, t in terr.items()}
    row_terr = {}
    for i, t in terr.items():
        row_terr.setdefault(row_of[id(houses[i])], []).append(t)
    row_terr = {r: unary_union(polys(shapely.union_all(v, grid_size=0.01))) for r, v in row_terr.items()}
    row_terr = {r: g for r, g in row_terr.items() if not g.is_empty}
    edges = unary_union([hu.buffer(0.4), backland.boundary.buffer(0.4)])
    lines = [g.boundary.difference(edges) for g in row_terr.values()]
    lines = [l for l in lines if not l.is_empty]
    ginnel = unary_union([l.buffer(GINNEL / 2, cap_style=2, join_style=2) for l in lines]) if lines else Point(0, 0).buffer(0)
    if main_ginnel:
        ginnel = unary_union([ginnel, backland.intersection(main.buffer(6.0 + GINNEL))])
    ginnel = ginnel.intersection(backland)

    def make_yards(ginnel):
        yards, outs, depth = [], [], []
        for i, h in enumerate(houses):
            t = terr.get(i)
            if t is None or t.is_empty:
                continue
            y = t.difference(ginnel)
            cs = list(h.exterior.coords)[:-1]
            regular = len(cs) == 4 and id(h) not in corner_ids
            if regular:
                f0, f1, b1, b0 = cs

                def ext(p, q, dd):
                    sx, sy = p[0] - q[0], p[1] - q[1]
                    sl = math.hypot(sx, sy) or 1
                    return (p[0] + sx / sl * dd, p[1] + sy / sl * dd)
                band = clean(Polygon([b0, b1, ext(b1, f1, 45), ext(b0, f0, 45)]))
                if band is not None:
                    y = y.intersection(band)
            y = clean(y, 4.0)
            if y is None or y.buffer(-0.9).is_empty:
                continue
            yards.append(y)
            depth.append(y.area / math.dist(cs[3], cs[2]) if regular else None)
            if regular:
                w_ = math.dist(b0, b1)
                t_ = ((b1[0] - b0[0]) / w_, (b1[1] - b0[1]) / w_)
                nx, ny = b0[0] - f0[0], b0[1] - f0[1]
                nl = math.hypot(nx, ny) or 1
                nx, ny = nx / nl, ny / nl
                u0 = 0.0 if i % 2 == 0 else w_ - OUT_W
                p0 = (b0[0] + t_[0] * u0, b0[1] + t_[1] * u0)
                p1 = (b0[0] + t_[0] * (u0 + OUT_W), b0[1] + t_[1] * (u0 + OUT_W))
                o = Polygon([p0, p1, (p1[0] + nx * OUT_D, p1[1] + ny * OUT_D), (p0[0] + nx * OUT_D, p0[1] + ny * OUT_D)])
                if y.buffer(0.05).contains(o) and not y.difference(o).buffer(-0.9).is_empty:
                    outs.append(o)
        return yards, outs, depth

    yards, outs, depth = make_yards(ginnel)
    # Marcel 2026-11-11: where a ginnel leaves the yards beside it under 5 m deep (median), there is no ginnel — the two rows
    # share the land wall to wall (and it gives the blocks variety)
    dropped = []
    keep = []
    for q in polys(ginnel):
        ds = [d for y, d in zip(yards, depth) if d is not None and y.distance(q) < 0.3]
        if len(ds) >= 3 and sorted(ds)[len(ds) // 2] < GINNEL_MIN_YARD:
            dropped.append(q)
        else:
            keep.append(q)
    if dropped:
        ginnel = unary_union(keep)
        yards, outs, depth = make_yards(ginnel)
    yard_u = unary_union(yards)
    ginnel = unary_union([q for q in polys(ginnel) if q.distance(yard_u) < 0.3 and q.area > 20])
    # tunnel backs
    open_to = unary_union([street_u, main.buffer(5.0)]).buffer(2.0)
    tunnels = []
    for g in polys(ginnel):
        if g.area < 20 or g.intersects(open_to):
            continue
        best = None
        for h in houses:
            if h.distance(g) > 2.0:
                continue
            P = nearest_points(g, h)[0]                     # the passage ends in the ginnel
            S = nearest_points(street_u.boundary, nearest_points(h, g)[0])[0]
            ln = LineString([(S.x, S.y), (P.x, P.y)])
            if ln.length < 22 and (best is None or ln.length < best[1].length):
                best = (h, ln)
        if best is not None:
            tunnels.append(best)
    return dict(backland=backland, yards=yards, outriggers=outs, ginnel=ginnel, tunnels=tunnels, open_to=open_to,
                dropped_ginnels=dropped)


def split_sharp(line, max_turn_deg=55.0):
    """Split a traced street where it turns sharply (a chain that ran round a corner is two streets)."""
    cs = list(line.coords)
    out, cur = [], [cs[0]]
    for i in range(1, len(cs) - 1):
        a = math.atan2(cs[i][1] - cs[i - 1][1], cs[i][0] - cs[i - 1][0])
        b = math.atan2(cs[i + 1][1] - cs[i][1], cs[i + 1][0] - cs[i][0])
        turn = abs(((b - a + math.pi) % (2 * math.pi)) - math.pi)
        cur.append(cs[i])
        if math.degrees(turn) > max_turn_deg:
            out.append(LineString(cur))
            cur = [cs[i]]
    cur.append(cs[-1])
    out.append(LineString(cur))
    return [o for o in out if o.length > 5]
