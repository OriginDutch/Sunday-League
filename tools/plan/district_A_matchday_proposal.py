"""District A — match-day proposal (Claude, 2026-11-10, for Marcel to judge): gates, pubs, corner shops, away coach bay, car-park
entrance, the away fans' route. Built on stadium plan v5's agreed approaches (GDD), moved onto the new streets.
python3 tools/plan/district_A_matchday_proposal.py -> design/world/village_district_A_matchday_proposal.png
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import matplotlib
matplotlib.use("Agg")
from shapely.geometry import LineString, Point, box
import village_district_A_v1 as A

OUT = os.path.join(HERE, "../../design/world/village_district_A_matchday_proposal.png")


def corner_at(x, y):
    return min(A.CORNERS, key=lambda c: c.distance(Point(x, y)))


# gates on the plot fence (position, label, colour)
GATES = [((-10, -129), "1  MAIN GATE\nticket office, home turnstiles\n(main stand, High Road)", "#1f5fa8"),
         ((-150, -129), "2  club square gate\n(hard core, from the square)", "#1f5fa8"),
         ((-139, 50), "3  HOME END turnstiles\n(straight up Turnstile Lane)", "#1f5fa8"),
         ((139, 100), "4  AWAY GATE\n(away end, from the green)", "#c0392b"),
         ((40, -160), "5  car park entrance\n(Car Park Lane)", "#555")]
PUBS = [(corner_at(25, -150), "Main Gate pub\n(opposite the main gate)"),
        (corner_at(196, 81), "away pub\n(by the road bridge)")]
SHOPS = [(corner_at(-162, 39), "corner shop\n(home end)"), (corner_at(93, -198), "corner shop"), (corner_at(162, -92), "corner shop")]
COACH_BAY = box(139.8, 0, 143.4, 60)                          # 3.6 m on the ground side of South Street: 4 coaches
AWAY_ROUTE = LineString([(206, 145), (196, 129), (174, 125), (168, 112), (164, 103), (150, 100), (139, 100)])   # road bridge -> along the quay walk -> green -> gate


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    _orig_savefig = plt.Figure.savefig

    def _hook(fig, path, *a, **k):
        ax = fig.axes[0]
        for (x, y), t, c in GATES:
            ax.plot([x], [y], marker="o", ms=13, mfc=c, mec="white", mew=2, zorder=40)
            dx = 14 if x < 100 else -14
            off = {(-10, -129): (-60, 38), (-150, -129): (14, -22), (40, -160): (14, -16)}.get((x, y), (dx, 12))
            ax.annotate(t, (x, y), (x + off[0], y + off[1]), fontsize=7.5, color=c, weight="bold", zorder=41,
                        ha="left" if off[0] > 0 else "right", arrowprops=dict(arrowstyle="-", color=c, lw=1),
                        bbox=dict(fc="white", ec=c, alpha=0.9, pad=0.25, boxstyle="round"))
        for g, t in PUBS:
            xs, ys = g.exterior.xy
            ax.fill(xs, ys, fc="#a0522d", ec="#222", lw=1.0, zorder=39)
            ax.annotate(t, g.centroid.coords[0], (g.centroid.x + 22, g.centroid.y - 4) if g.centroid.x < 100 else (g.centroid.x - 10, g.centroid.y + 16),
                        fontsize=7, color="#7a3010", zorder=41, ha="left" if g.centroid.x < 100 else "right", arrowprops=dict(arrowstyle="-", color="#7a3010", lw=0.8),
                        bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.2))
        for g, t in SHOPS:
            xs, ys = g.exterior.xy
            ax.fill(xs, ys, fc="#d9a23a", ec="#222", lw=1.0, zorder=39)
            ax.annotate(t, g.centroid.coords[0], (g.centroid.x + 10, g.centroid.y - 14), fontsize=7, color="#7a5a10", zorder=41,
                        arrowprops=dict(arrowstyle="-", color="#7a5a10", lw=0.8), bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.2))
        xs, ys = COACH_BAY.exterior.xy
        ax.fill(xs, ys, fc="#c0392b", ec="#222", lw=0.8, alpha=0.8, zorder=39)
        ax.text(132, 30, "away coach bay\n(4 coaches)", fontsize=7, color="#c0392b", ha="right", zorder=41, weight="bold",
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.2))
        xs, ys = AWAY_ROUTE.xy
        ax.plot(xs, ys, color="#c0392b", lw=2.5, ls=(0, (3, 2)), zorder=38)
        ax.text(214, 125, "away fans from the station:\nroad bridge → quay walk → green → gate", fontsize=7, color="#c0392b", zorder=41, ha="left",
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.2))
        ax.set_title("DISTRICT A — MATCH-DAY PROPOSAL (Claude): blue = home gates, red = away, brown = pubs, ochre = corner shops",
                     fontsize=10.5, loc="left")
        return _orig_savefig(fig, path, *a, **k)

    plt.Figure.savefig = _hook
    A.main(OUT)
