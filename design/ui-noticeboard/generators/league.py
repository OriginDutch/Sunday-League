import sys, os, json, random
sys.path.insert(0, os.path.dirname(__file__))
from nbkit import *
from lib import icon

OUT = "/home/claude/canvas/project"
L = RED_WHITE
TNUM = "font-variant-numeric: tabular-nums"

TEAMS = ["Red Lion XI", "Gasworks Rovers", "Canal Side Old Boys", "Riverside United", "Railway Tavern Athletic",
         "Dog & Duck Rovers", "Kings Arms FC", "Millpond Wanderers", "Bus Depot United", "Allotment Athletic",
         "Royal Oak Reserves", "Chippy Lane FC", "St Bart's Old Boys", "The Plough XI", "Laundrette Town",
         "Bowling Green Rangers", "Coach & Horses FC", "Brewery Lane Athletic", "Sunday Market FC", "Your club"]
US = "Your club"


def simulate():
    """Round-robin rounds with random scores until 'Your club' is 3rd on W4 D1 L3 (matches the hub record)."""
    for seed in range(200000):
        r = random.Random(seed)
        t = TEAMS[:]
        st = {n: [0, 0, 0, 0, 0] for n in t}  # W D L GF GA
        # circle method, 8 rounds
        teams = t[:]
        for rnd in range(8):
            for i in range(10):
                a, b = teams[i], teams[19 - i]
                ga = r.choice([0, 0, 1, 1, 1, 2, 2, 3, 4])
                gb = r.choice([0, 0, 1, 1, 1, 2, 2, 3, 4])
                st[a][3] += ga; st[a][4] += gb; st[b][3] += gb; st[b][4] += ga
                if ga > gb: st[a][0] += 1; st[b][2] += 1
                elif gb > ga: st[b][0] += 1; st[a][2] += 1
                else: st[a][1] += 1; st[b][1] += 1
            teams = [teams[0]] + [teams[-1]] + teams[1:-1]
        if st[US][:3] != [4, 1, 3]:
            continue
        rows = sorted(t, key=lambda n: (-(3 * st[n][0] + st[n][1]), -(st[n][3] - st[n][4]), -st[n][3], n))
        if rows.index(US) != 2:
            continue
        # avoid ties with us on points+GD for clarity
        pts = lambda n: 3 * st[n][0] + st[n][1]
        gd = lambda n: st[n][3] - st[n][4]
        if (pts(rows[1]), gd(rows[1])) == (pts(US), gd(US)) or (pts(rows[3]), gd(rows[3])) == (pts(US), gd(US)):
            continue
        return [(i + 1, n, 8, st[n][0], st[n][1], st[n][2], gd(n), pts(n)) for i, n in enumerate(rows)]
    raise SystemExit("no seed")


TABLE = simulate()


def gd_s(g):
    return f"+{g}" if g > 0 else ("−" + str(-g) if g < 0 else "0")


def highlighter(T):
    col = "rgba(255,122,131,0.32)" if T["PAPER"] == "#25292D" else "rgba(208,32,46,0.26)"
    return (f'<span aria-hidden="true" style="position: absolute; left: -6px; right: -4px; top: 5px; bottom: 4px; background: {col}; '
            f'border-radius: 40% 18% 34% 22% / 60% 45% 55% 40%; transform: rotate(-0.6deg) skewX(-6deg); z-index: 0"></span>')


# ---------------------------------------------------------------- 1. Hub with mini table
def hub_mini(T=L):
    i = [r[1] for r in TABLE].index(US)
    rows = TABLE[i - 2:i + 3]
    cols = "36px minmax(0, 1fr) 32px 40px"
    head = "".join(f'<span style="font: 700 13px/16px {SANS}; color: {T["MUTED"]}; text-transform: uppercase; letter-spacing: 0.06em; {"text-align: right" if k > 1 else ""}">{h}</span>' for k, h in enumerate(["Pos", "Team", "P", "Pts"]))
    body = ""
    for pos, n, p, w, d, l, g, pts in rows:
        us = n == US
        fw = 700 if us else 500
        body += f'''<div style="position: relative; display: grid; grid-template-columns: {cols}; gap: 8px; align-items: center; height: 30px; padding: 0 6px">
{highlighter(T) if us else ""}
<span style="position: relative; font: {fw} 15px/18px {SANS}; color: {T["INK"]}; {TNUM}">{pos}</span>
<span style="position: relative; font: {fw} 15px/18px {SANS}; color: {T["INK"]}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{n}</span>
<span style="position: relative; font: {fw} 15px/18px {SANS}; color: {T["INK"]}; text-align: right; {TNUM}">{p}</span>
<span style="position: relative; font: 700 15px/18px {SANS}; color: {T["INK"]}; text-align: right; {TNUM}">{pts}</span></div>'''
    mini = f'''<div style="display: flex; flex-direction: column; gap: 2px; padding-top: 4px; border-top: 2px solid {T["INK"]}">
<div style="display: grid; grid-template-columns: {cols}; gap: 8px; height: 26px; align-items: center; padding: 0 6px">{head}</div>
{body}
<a href="#" style="align-self: flex-end; display: inline-flex; align-items: center; min-height: 44px; padding: 0 4px; font: 700 19px/22px {HAND}; color: {T["PEN"]}; text-decoration: underline; text-decoration-thickness: 1.5px; text-underline-offset: 4px">Full table →</a></div>'''
    goal = f'''<section style="{note(T, 'top: 146px; left: 40px; width: 410px; padding: 28px 26px 24px; display: flex; flex-direction: column; gap: 12px')}">
{tape(T, "top: -14px; left: 156px", 2)}
{h2(T, "Our Goal", col=T["NOTE_INK"])}
<p style="margin: 0; font: 600 20px/26px {SANS}; color: {T["NOTE_INK"]}">Reach 100 paying supporters</p>
<div style="display: flex; justify-content: space-between"><span style="font: 500 16px/22px {SANS}; color: {T["NOTE_MUTED"]}">Paying supporters</span><span style="font: 700 18px/22px {SANS}; color: {T["NOTE_INK"]}">24 / 100</span></div>
{progress(T, 24)}
<span style="font: 400 19px/24px {HAND}; color: {T["NOTE_MUTED"]}">76 to go!! Ask your nan. And her mates. — Chairman</span>
<div>{link_btn(T, "Build seats", "stadium", True)}</div></section>'''
    match = f'''<section style="{card(T, 'top: 132px; right: 40px; width: 440px; padding: 24px 24px 18px; display: flex; flex-direction: column; gap: 14px', 0.9)}">
{pin(T)}
<div style="display: flex; justify-content: space-between; align-items: baseline">{h2(T, "Next Match")}{label(T, "League")}</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: center">
<div style="display: flex; flex-direction: column; align-items: center; gap: 6px; text-align: center">{crest_svg("home", 56, T["CREST"])}<span style="font: 700 17px/20px {SANS}; color: {T["INK"]}">Your club</span></div>
<span style="text-align: center; font: 700 32px/32px {HAND}; color: {T["PEN"]}">vs</span>
<div style="display: flex; flex-direction: column; align-items: center; gap: 6px; text-align: center">{crest_svg("away", 56, T["INK"])}<span style="font: 700 17px/20px {SANS}; color: {T["INK"]}">Riverside United</span></div></div>
{primary(T, "Play Match", "play")}
{mini}</section>'''
    return page("Hub · mini league table", topbar(T) + goal + match + strip(T, "Club"))


# ---------------------------------------------------------------- 2/3/4. Full table modal
def full_table(T=L, zones=False, title="League table", rules=("promo", "playoff", "p18", "releg")):
    cols = "40px minmax(0, 1fr) 40px 40px 40px 40px 52px 52px"
    ROW = 36
    head = "".join(f'<span style="font: 700 13px/16px {SANS}; color: {T["MUTED"]}; text-transform: uppercase; letter-spacing: 0.06em; {"text-align: right" if k > 1 else ""}">{h}</span>'
                   for k, h in enumerate(["#", "Team", "P", "W", "D", "L", "GD", "Pts"]))
    body = ""
    for pos, n, p, w, d, l, g, pts in TABLE:
        us = n == US
        fw = 700 if us else 500
        cells = "".join(f'<span style="position: relative; font: {fw} 16px/20px {SANS}; color: {T["INK"]}; text-align: right; {TNUM}">{v}</span>' for v in [p, w, d, l, gd_s(g)])
        zone = ""
        P = T["PEN"]
        lab = lambda txt, top, rot: f'<span style="position: absolute; right: -164px; top: {top}px; width: 130px; font: 700 20px/22px {HAND}; color: {P}; white-space: nowrap; transform: rotate({rot}deg)">{txt}</span>'
        line_b = f'<div aria-hidden="true" style="position: absolute; left: -10px; right: -10px; bottom: -2px; border-bottom: 2.5px dashed {P}"></div>'
        line_t = f'<div aria-hidden="true" style="position: absolute; left: -10px; right: -10px; top: -2px; border-top: 2.5px dashed {P}"></div>'
        if zones and "promo" in rules and pos == 2:
            zone = line_b + lab("Promotion ↑", 8, -3)
        if zones and "playoff" in rules and pos == 3:
            zone = (f'<svg aria-hidden="true" width="18" height="176" viewBox="0 0 18 176" style="position: absolute; right: -24px; top: 2px">'
                    f'<path d="M2 2 C10 2 9 10 9 30 L9 74 C9 84 12 88 16 88 C12 88 9 92 9 102 L9 146 C9 166 10 174 2 174" fill="none" stroke="{P}" stroke-width="2.5" stroke-linecap="round"/></svg>'
                    + lab("Play-offs", 66, -2)
                    + f'<span style="position: absolute; right: -164px; top: 90px; width: 130px; font: 400 16px/19px {HAND}; color: {T["MUTED"]}">+ 18th of the<br>division above</span>')
        if zones and "playoff" in rules and pos == 7:
            zone = line_b
        if zones and "p18" in rules and pos == 18:
            zone = line_t + lab("Play-off ↕", 6, 2)
        if zones and "releg" in rules and pos == 19:
            zone = line_t + lab("Relegation ↓", 10, 2)
        body += f'''<div role="row" style="position: relative; display: grid; grid-template-columns: {cols}; gap: 8px; align-items: center; height: {ROW}px; padding: 0 10px">
{highlighter(T) if us else ""}{zone}
<span style="position: relative; font: {fw} 16px/20px {SANS}; color: {T["INK"]}; {TNUM}">{pos}</span>
<span style="position: relative; font: {fw} 16px/20px {SANS}; color: {T["INK"]}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{n}</span>
{cells}
<span style="position: relative; font: 700 16px/20px {SANS}; color: {T["INK"]}; text-align: right; {TNUM}">{pts}</span></div>'''
    margin_col = "rgba(255,122,131,0.35)" if T["PAPER"] == "#25292D" else "rgba(208,32,46,0.35)"
    wide = "margin-left: -440px; width: 880px; padding: 40px 170px 30px 76px;" if zones else "margin-left: -370px; width: 740px; padding: 40px 44px 30px 76px;"
    sheet = f'''<section role="dialog" aria-label="League table" style="position: absolute; top: 46px; left: 50%; {wide} height: 990px; box-sizing: border-box;
background-color: {T["CARD"]}; background-image: repeating-linear-gradient(to bottom, transparent 0 {ROW - 1}px, {T["LINES"]} {ROW - 1}px {ROW}px); background-position: 0 {176 + 0}px;
border-radius: 2px; transform: rotate(-0.8deg); box-shadow: 0 16px 36px rgba(0,0,0,0.45); z-index: 7; display: flex; flex-direction: column; gap: 10px">
<span aria-hidden="true" style="position: absolute; top: 0; bottom: 0; left: 58px; border-left: 2px solid {margin_col}"></span>
{pin(T, "50%", -9)}
<div style="display: flex; justify-content: space-between; align-items: flex-start; {'margin-right: -130px' if zones else ''}">
<div><h2 style="margin: 0; font: 700 44px/48px {HAND}; color: {T["INK"]}">League table — Season 1</h2>
<span style="font: 500 15px/20px {SANS}; color: {T["MUTED"]}">Non-League 3 · after 8 of 38 matches</span></div>
{ibtn(T, "close", "Close league table")}</div>
<div role="table" style="display: flex; flex-direction: column; margin-top: 6px">
<div role="row" style="display: grid; grid-template-columns: {cols}; gap: 8px; height: 32px; align-items: center; padding: 0 10px; border-bottom: 2px solid {T["INK"]}">{head}</div>
{body}</div>
<span style="margin-top: auto; font: 400 18px/22px {HAND}; color: {T["MUTED"]}">Copied off the noticeboard in the clubhouse. Mind the tea stain.</span>
</section>'''
    scrim = '<div aria-hidden="true" style="position: absolute; inset: 0; background: rgba(0,0,0,0.45); z-index: 6"></div>'
    return page(title, topbar(T) + strip(T, "Club") + scrim + sheet)


FILES = [
    ("LT_Hub_Mini.dc.html", hub_mini, "Hub · mini league table"),
    ("LT_Full.dc.html", lambda: full_table(L), "Full table (modal)"),
    ("LT_Full_Zones.dc.html", lambda: full_table(L, True, "League table · promotion / relegation"), "Full table · promotion / relegation lines (later)"),
    ("LT_Full_Zones_Bottom.dc.html", lambda: full_table(L, True, "League table · bottom division (no relegation)", ("promo", "playoff")), "Full table · Non-League 3 (bottom division)"),
    ("LT_Full_Dark.dc.html", lambda: full_table(DARK_RW, False, "League table · dark"), "Full table · dark check"),
]

if __name__ == "__main__":
    for pos, n, p, w, d, l, g, pts in TABLE:
        print(pos, n, p, w, d, l, g, pts)
    print("sum GD", sum(r[6] for r in TABLE), "W", sum(r[3] for r in TABLE), "L", sum(r[5] for r in TABLE))
    for fn, f, _ in FILES:
        open(os.path.join(OUT, fn), "w").write(f())
    print("ok")
