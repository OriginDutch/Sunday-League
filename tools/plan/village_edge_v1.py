"""Village edge v1 — the town gets an end. Two options side by side, for Marcel to choose (2026-11-09).
python3 tools/plan/village_edge_v1.py  ->  design/world/village_edge_A.png, village_edge_B.png

Marcel on village plan v5: "het is nog steeds een vierkant dorp. Het kapt af. ... een volledig dorp, waarmee je eventueel ook
cinematics kan maken. Dus er moet een einde zitten, niet het gevoel dat het door gaat."
  A: map stays 1.5 x 1.5 km; the town shrinks, the corners become countryside.
  B: the town stays about as big as v5; a ring of countryside round it, map ~2.2 x 2.2 km.
Both: an irregular town boundary along something that makes sense (a brook, the bypass, the industrial estate),
ribbon houses along the roads out, then fields with hedgerows, woods, farms, country lanes; hills on the horizon.
Everything on the edge is Claude's PROPOSAL. Line plan only: v5 is shown faded for reference.
"""
import math
import os
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Polygon, Point, box, MultiPoint
from shapely.ops import unary_union
from shapely import voronoi_polygons

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import village_plan_v5 as P5          # runs the v5 plan (a few minutes)
import village_plan_v1 as V
import village_skeleton_v1 as SK

OUT = os.path.join(HERE, "../../design/world")


def blob(r0, amps, seed_phase, n=160):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = r0 + sum(A * math.sin(k * a + ph) for k, A, ph in amps)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return Polygon(pts)


# brook (proposal): comes in at the top left, runs round the north-west of the town and joins the canal on the left
def brook(scale):
    pts = [(-1.0, 0.95), (-0.86, 0.80), (-0.90, 0.62), (-0.80, 0.48), (-0.86, 0.36), (-0.93, 0.24)]
    return LineString([(x * scale, y * scale) for x, y in pts])


OPTIONS = {
    "A": dict(R=750, town=blob(585, [(2, 70, 0.6), (3, 45, 2.0), (5, 25, 1.1)], 0), ribbon=140, brook_scale=760),
    "B": dict(R=1100, town=blob(740, [(2, 35, 0.6), (3, 30, 2.0), (5, 18, 1.1)], 0), ribbon=170, brook_scale=1000),
}
# the industrial estate and the bypass are natural edges: the town takes them in
for k, o in OPTIONS.items():
    t = o["town"].union(SK.IND_POLY.buffer(15)).buffer(25).buffer(-25)
    if k == "A":
        t = t.intersection(box(-735, -735, 735, 735))
    o["town"] = t


def roads_out(o):
    """Main roads carried on past the map edge of v5 as country roads; returns (name, line, width)."""
    R = o["R"]
    out = []
    for n, (pts, w, k) in V.ROADS.items():
        ln = LineString(pts)
        out.append((n, ln, w))
        for e in (0, -1):
            p = Point(pts[e])
            if max(abs(p.x), abs(p.y)) < 749:
                continue
            q = Point(pts[1] if e == 0 else pts[-2])
            dx, dy = p.x - q.x, p.y - q.y
            L = math.hypot(dx, dy) or 1
            ext = LineString([(p.x, p.y), (p.x + dx / L * 700, p.y + dy / L * 700)]).intersection(box(-R, -R, R, R))
            if not ext.is_empty:
                out.append((n + " (lane)", ext, max(5.5, w - 2)))
    return out


def ribbon(o, roads):
    """Ribbon houses along the roads out: a short run past the town edge, then fields."""
    town = o["town"]
    hs = []
    rr = random.Random(7)
    for n, ln, w in roads:
        outside = ln.difference(town)
        for seg in getattr(outside, "geoms", [outside]):
            if seg.geom_type != "LineString" or seg.length < 30:
                continue
            # start at the end that touches the town
            if Point(seg.coords[-1]).distance(town) < Point(seg.coords[0]).distance(town):
                seg = LineString(list(seg.coords)[::-1])
            if Point(seg.coords[0]).distance(town) > 5:
                continue
            run = o["ribbon"] * rr.uniform(0.6, 1.2)
            d = 6.0
            while d < min(run, seg.length - 5):
                p = seg.interpolate(d)
                q = seg.interpolate(min(d + 1, seg.length))
                tx, ty = q.x - p.x, q.y - p.y
                L = math.hypot(tx, ty) or 1
                tx, ty = tx / L, ty / L
                for side in (1, -1):
                    if rr.random() < 0.25:
                        continue
                    nx, ny = -ty * side, tx * side
                    c = (p.x + nx * (w / 2 + 12), p.y + ny * (w / 2 + 12))
                    hw, hd = rr.uniform(4.5, 6.5), rr.uniform(4.0, 5.5)
                    hs.append(Polygon([(c[0] - tx * hw - nx * hd, c[1] - ty * hw - ny * hd), (c[0] + tx * hw - nx * hd, c[1] + ty * hw - ny * hd),
                                       (c[0] + tx * hw + nx * hd, c[1] + ty * hw + ny * hd), (c[0] - tx * hw + nx * hd, c[1] - ty * hw + ny * hd)]))
                d += rr.uniform(16, 26)
    return hs


def countryside(o, roads, ribbon_hs):
    R = o["R"]
    world = box(-R, -R, R, R)
    rr = random.Random(3 if o["R"] == 750 else 4)
    road_a = unary_union([ln.buffer(w / 2 + 2) for n, ln, w in roads])
    water = unary_union([V.CANAL.buffer(8), brook(o["brook_scale"]).buffer(5), V.RAIL.buffer(8)])
    # canal + railway carry on out of the v5 square
    canal_ext = LineString([(-R, 150 - (R - 750) * 0.12)] + list(V.CANAL.coords) + [(R, 292 + (R - 750) * 0.17)])
    rail_ext = LineString([(-R, -560 - (R - 750) * 0.25)] + list(V.RAIL.coords) + [(R, -352 + (R - 750) * 0.32)])
    water = water.union(canal_ext.buffer(8)).union(rail_ext.buffer(8))
    country = world.difference(o["town"].buffer(10)).difference(road_a).difference(water)
    country = country.difference(unary_union([h.buffer(14) for h in ribbon_hs]))
    # woods (proposal): on the far side of the brook, and on the corners
    woods = []
    for (cx, cy, r0) in ((-0.88, 0.70, 0.11), (0.82, 0.86, 0.10), (-0.80, -0.86, 0.09), (0.93, -0.12, 0.07)):
        w_ = blob(r0 * R, [(3, r0 * R * 0.25, 1.3), (5, r0 * R * 0.12, 0.4)], 0)
        from shapely.affinity import translate
        woods.append(translate(w_, cx * R, cy * R))
    woods = unary_union(woods).intersection(country)
    fields_area = country.difference(woods.buffer(3))
    # fields: irregular patchwork, hedgerows on the edges
    pts = []
    bx0, by0, bx1, by1 = fields_area.bounds
    target = int(fields_area.area / (8500 if o["R"] == 750 else 11000))
    pf = fields_area.buffer(0)
    while len(pts) < target:
        x, y = rr.uniform(bx0, bx1), rr.uniform(by0, by1)
        if pf.contains(Point(x, y)):
            pts.append((x, y))
    cells = voronoi_polygons(MultiPoint(pts), extend_to=world)
    fields = []
    for c in cells.geoms:
        f = c.intersection(fields_area).buffer(-2.5)
        for g in getattr(f, "geoms", [f]):
            if g.geom_type == "Polygon" and g.area > 400:
                fields.append(g)
    # farms (proposal): a farmhouse + barns + yard, on a lane
    farms = []
    for (fx, fy) in ((-0.62, -0.95), (0.70, 0.70), (-0.95, -0.30), (0.20, 0.96)):
        x, y = fx * R, fy * R
        if o["town"].buffer(60).contains(Point(x, y)) or abs(x) > R - 30 or abs(y) > R - 30:
            continue
        farms.append([box(x - 30, y - 22, x + 30, y + 22), box(x - 24, y - 14, x - 10, y - 4), box(x - 2, y - 16, x + 24, y + 2),
                      box(x - 2, y + 6, x + 20, y + 16)])
    return dict(fields=fields, woods=woods, farms=farms, canal_ext=canal_ext, rail_ext=rail_ext)


def draw(key):
    o = OPTIONS[key]
    R = o["R"]
    town = o["town"]
    roads = roads_out(o)
    rib = ribbon(o, roads)
    cs = countryside(o, roads, rib)
    fig, ax = plt.subplots(figsize=(15, 15), dpi=115)
    ax.set_aspect("equal")
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_facecolor("#E8EBD8")
    rr = random.Random(5)
    tones = ["#D9E4B8", "#CFDDA8", "#E4E1B2", "#C9D9A4", "#DDE6C4", "#E6DCA6"]
    for f in cs["fields"]:
        P5.draw_geom(ax, f, rr.choice(tones), "#5d7f3e", 0.9, 1)          # hedge = the dark edge
    P5.draw_geom(ax, cs["woods"], "#7FA868", "#3d6b2c", 0.8, 2)
    tp = []
    bx0, by0, bx1, by1 = cs["woods"].bounds if not cs["woods"].is_empty else (0, 0, 0, 0)
    for _ in range(9000):
        x, y = rr.uniform(bx0, bx1), rr.uniform(by0, by1)
        if cs["woods"].contains(Point(x, y)):
            tp.append((x, y))
    if tp:
        ax.scatter([p[0] for p in tp], [p[1] for p in tp], s=5, c="#3d6b2c", alpha=0.6, zorder=3, linewidths=0)
    for fm in cs["farms"]:
        P5.draw_geom(ax, fm[0], "#e3dccb", "#8a7f6a", 0.6, 4)
        for b in fm[1:]:
            P5.draw_geom(ax, b, "#9b8a74", "#3d3a36", 0.6, 5)
    # town: v5 faded, only what lies inside the boundary
    P5.draw_geom(ax, town, "#F4F2EC", "#6b5a45", 2.2, 6)
    inside = town.buffer(-2)
    for b in P5.BUILD:
        for h in b["houses"]:
            if inside.contains(h):
                P5.draw_geom(ax, h, "#c9a48c", "none", 0, 7)
    for f in P5.FLATS + P5.SHEDS:
        if inside.contains(f):
            P5.draw_geom(ax, f, "#a8a49c", "none", 0, 7)
    for h in P5.W.HOUSES:
        if P5.V5_BOX.contains(h["house"]):
            P5.draw_geom(ax, h["house"], "#c9a48c", "none", 0, 7)
    P5.draw_geom(ax, P5.ROADS_ALL.intersection(town), "#d8d4cc", "none", 0, 6.5)
    for nm, g, col in P5.LMK:
        if town.contains(g.centroid):
            P5.draw_geom(ax, g, "#9fc489" if "green" in nm or "park" in nm or "Park" in nm or "playing" in nm or "rec" in nm else col, "#555", 0.5, 7)
    P5.draw_geom(ax, P5.W.PLOT, "#E3EFD9", "#2F5B3F", 1.0, 8)
    # water + rail
    P5.draw_geom(ax, cs["canal_ext"].buffer(6), "#BFD9E6", "#5f95b3", 0.8, 9)
    P5.draw_geom(ax, brook(o["brook_scale"]).buffer(3), "#BFD9E6", "#5f95b3", 0.6, 9)
    xs, ys = cs["rail_ext"].xy
    ax.plot(xs, ys, color="#444", lw=3, zorder=10)
    ax.plot(xs, ys, color="white", lw=1.2, zorder=10, ls=(0, (3, 3)))
    # roads: main roads through the town, lanes out into the country
    for n, ln, w in roads:
        xs, ys = ln.xy
        lane = "(lane)" in n
        ax.plot(xs, ys, color="#8a7f6a" if lane else "#4d5258", lw=2.0 if lane else 3.0, zorder=11, solid_capstyle="round")
    for h in rib:
        P5.draw_geom(ax, h, "#c98a6a", "#3d3a36", 0.4, 12)
    # labels
    def lab(x, y, t, fs=9, col="#222", style="normal"):
        ax.text(x, y, t, ha="center", va="center", fontsize=fs, color=col, style=style, weight="bold", zorder=30,
                bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.4))
    lab(-0.86 * o["brook_scale"], 0.52 * o["brook_scale"], "Mill Brook", col="#245")
    for (cx, cy, t) in ((-0.88, 0.70, "wood"), (0.82, 0.86, "wood"), (-0.80, -0.86, "wood"), (0.93, -0.12, "copse")):
        if cs["woods"].distance(Point(cx * R, cy * R)) < 5:
            lab(cx * R, cy * R, t, fs=8, col="#1d3b14", style="italic")
    for fm in cs["farms"]:
        c = fm[0].centroid
        lab(c.x, c.y + 40, "farm", fs=8, col="#4a3b22")
    lab(0, 0, "THE GROUND", fs=9)
    homes_in = sum(sum(1 for h in b["houses"] if inside.contains(h)) for b in P5.BUILD) + \
        sum(1 for h in P5.W.HOUSES if P5.V5_BOX.contains(h["house"]))
    homes_all = sum(len(b["houses"]) for b in P5.BUILD) + sum(1 for h in P5.W.HOUSES if P5.V5_BOX.contains(h["house"]))
    title = {"A": "OPTION A — map stays 1.5 x 1.5 km, the town shrinks, the corners become countryside",
             "B": "OPTION B — the town stays ~v5 size, a ring of countryside round it, map 2.2 x 2.2 km"}[key]
    ax.text(-R + 15, R - 15, f"{title}\nbrown line = town edge · houses inside: ~{homes_in} of v5's ~{homes_all} buildings "
            f"(v5 shown faded) · ribbon houses along the roads out: {len(rib)}\n"
            "country: fields + hedgerows, woods, farms, Mill Brook, lanes to the next villages · beyond: low hills on the horizon (backdrop)",
            ha="left", va="top", fontsize=10, zorder=40, bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.5"))
    sb = 200
    ax.plot([R - 40 - sb, R - 40], [-R + 30, -R + 30], color="#222", lw=3, zorder=40)
    ax.text(R - 40 - sb / 2, -R + 50, "200 m", ha="center", fontsize=10, zorder=40)
    if key == "B":
        ax.add_patch(plt.Rectangle((-750, -750), 1500, 1500, fc="none", ec="#c0392b", lw=1.2, ls=(0, (6, 4)), zorder=35))
        ax.text(-740, -735, "v5 map edge (1.5 km)", fontsize=8, color="#c0392b", zorder=35, va="bottom")
    path = os.path.join(OUT, f"village_edge_{key}.png")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print("saved", os.path.relpath(path), "homes inside", homes_in, "of", homes_all, "ribbon", len(rib))


if __name__ == "__main__":
    for k in ("A", "B"):
        draw(k)
