"""Turn skeleton pieces traced from Marcel's sketch into whole streets: snap the ends that meet, then join the pieces that run
on straight through a junction (a street keeps going; a side street stops at it). Used for district B onwards."""
import math
from shapely.geometry import LineString, Point


def _ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def merge(paths, snap=5.0, straight_deg=35.0, min_len=12.0, simplify=1.5):
    segs = [LineString(p).simplify(simplify) for p in paths if len(p) >= 2]
    segs = [s for s in segs if s.length > 1.0]
    # cluster end points
    ends = []
    for i, s in enumerate(segs):
        ends.append([i, 0, s.coords[0]])
        ends.append([i, 1, s.coords[-1]])
    nodes = []
    for e in ends:
        for k, n in enumerate(nodes):
            if math.dist(n["c"], e[2]) < snap:
                n["m"].append(e)
                break
        else:
            nodes.append({"c": e[2], "m": [e]})
    for n in nodes:
        xs = [e[2][0] for e in n["m"]]
        ys = [e[2][1] for e in n["m"]]
        n["c"] = (sum(xs) / len(xs), sum(ys) / len(ys))
    node_of = {}
    for k, n in enumerate(nodes):
        for e in n["m"]:
            node_of[(e[0], e[1])] = k
    pts = []
    for i, s in enumerate(segs):
        cs = list(s.coords)
        cs[0] = nodes[node_of[(i, 0)]]["c"]
        cs[-1] = nodes[node_of[(i, 1)]]["c"]
        pts.append(cs)

    def out_dir(i, end):          # direction leaving the node along segment i
        cs = pts[i]
        if end == 0:
            a, b = cs[0], cs[min(1, len(cs) - 1)]
        else:
            a, b = cs[-1], cs[max(-2, -len(cs))]
        return _ang(a, b)
    # at each node pair up the straightest continuations
    link = {}
    for k, n in enumerate(nodes):
        es = [(e[0], e[1]) for e in n["m"]]
        cand = []
        for x in range(len(es)):
            for y in range(x + 1, len(es)):
                d = abs(((out_dir(*es[x]) - out_dir(*es[y]) + math.pi) % (2 * math.pi)) - math.pi)
                dev = math.degrees(math.pi - d)
                if dev < straight_deg:
                    cand.append((dev, es[x], es[y]))
        cand.sort()
        used = set()
        for dev, a, b in cand:
            if a in used or b in used:
                continue
            used |= {a, b}
            link[a] = b
            link[b] = a
    # walk chains
    seen = set()
    streets = []
    for i in range(len(pts)):
        if i in seen:
            continue
        # go to one end of the chain
        cur, end = i, 0
        guard = 0
        while (cur, end) in link and guard < 500:
            nxt = link[(cur, end)]
            if nxt[0] == i:
                break
            cur, end = nxt[0], 1 - nxt[1]
            guard += 1
        # now walk from (cur, end) forwards
        chain = []
        start_end = end
        c, e = cur, end
        guard = 0
        while guard < 500:
            seen.add(c)
            cs = pts[c] if e == 0 else pts[c][::-1]
            chain += cs if not chain else cs[1:]
            nxt = link.get((c, 1 - e))
            if nxt is None or nxt[0] in seen:
                break
            c, e = nxt
            guard += 1
        ln = LineString(chain)
        if ln.length >= min_len:
            streets.append(ln)
    return streets
