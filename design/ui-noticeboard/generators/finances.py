"""Finances tab mock-up (2026-11-08): this season's in/out, per-match ledger, cash over time, coming up.
python finances.py  -> mockups/S_Finances.dc.html (canvas) + ../finances_preview.png (local render, headless Chrome)
Numbers are an example club halfway through a Non-League 3 season with Claude's proposed bottom-tier economy."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from nbkit import *
from lib import icon, HUB_BG

T = RED_WHITE
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

# --- example season (week 12 of 42, 6 matches played) -------------------------------------------------
MATCHES = [  # week, opponent, home, fans, seated, result
    (1, "Railway Tavern Athletic", True, 22, 16, "W 2-1"),
    (2, "Quarry Road Casuals", False, 0, 0, "L 0-3"),
    (4, "The Plough FC", True, 25, 20, "D 1-1"),
    (6, "Hollybush Wanderers", False, 0, 0, "W 1-0"),
    (8, "St. Mary's Old Boys", True, 28, 24, "W 3-0"),
    (11, "Red Lion FC", True, 31, 24, "L 1-2"),
]
TICKET, TEA, SUBS = 2, 1, 1          # £ per seated fan / per visitor / per player per match
PITCH, REF, KIT, TRAVEL = 8, 5, 2, 3  # £ per home match / per home match / per match / per away match
SPONSOR, LEAGUE_FEE = 50, 30         # £ per season, paid at the start


def match_lines(m):
    wk, opp, home, fans, seated, res = m
    inc = {"Tickets": seated * TICKET if home else 0, "Tea hut": fans * TEA if home else 0, "Match subs": 11 * SUBS}
    out = {"Pitch hire": PITCH if home else 0, "Referee": REF if home else 0, "Kit washing": KIT, "Travel": 0 if home else TRAVEL}
    return inc, out


def season_totals():
    inc = {"Tickets": 0, "Tea hut": 0, "Match subs": 0, "Sponsor": SPONSOR, "Prize money": 0}
    out = {"Pitch hire": 0, "Referee": 0, "Kit washing": 0, "Travel": 0, "League fee": LEAGUE_FEE, "Building": 0}
    for m in MATCHES:
        i, o = match_lines(m)
        for k, v in i.items():
            inc[k] += v
        for k, v in o.items():
            out[k] += v
    out["Building"] = 12 * 4 + 40   # four chairs and a bench this season
    return inc, out


def money(v, sign=False):
    s = "-" if v < 0 else ("+" if sign and v > 0 else "")
    return f"{s}£{abs(v):,}"


def row(lab, val, col=None, bold=False, sub=""):
    w = 700 if bold else 600
    s = f'<span style="font: 400 17px/20px {HAND}; color: {T["MUTED"]}; margin-left: 8px">{sub}</span>' if sub else ""
    return (f'<div style="display: flex; justify-content: space-between; align-items: baseline; height: 32px">'
            f'<span style="font: 500 16px/20px {SANS}; color: {T["MUTED"] if not bold else T["INK"]}">{lab}{s}</span>'
            f'<span style="font: {w} {19 if bold else 17}px/22px {SANS}; color: {col or T["INK"]}">{val}</span></div>')


def season_card():
    inc, out = season_totals()
    ti, to = sum(inc.values()), sum(out.values())
    notes = {"Sponsor": "Dave's Plumbing", "Prize money": "end of season", "League fee": "paid in week 1", "Building": "4 chairs, 1 bench"}
    ins = "".join(row(k, money(v), T["OK"] if v else T["MUTED"], sub=notes.get(k, "")) for k, v in inc.items())
    outs = "".join(row(k, money(-v) if v else "£0", danger(T) if v else T["MUTED"], sub=notes.get(k, "")) for k, v in out.items())
    net = ti - to
    return f'''<section style="{card(T, 'top: 140px; left: 40px; width: 430px; padding: 24px 26px 20px; display: flex; flex-direction: column; gap: 6px', -0.6)}">
{pin(T)}
<div style="display: flex; justify-content: space-between; align-items: baseline">{h2(T, "This season", 36)}{label(T, "Week 12 / 42")}</div>
{label(T, "Money in", T["MUTED"])}{ins}
<div style="height: 1px; background: {T["DIV"]}; margin: 4px 0"></div>
{label(T, "Money out", T["MUTED"])}{outs}
<div style="height: 2px; background: {T["INK"]}; margin: 6px 0 2px"></div>
{row("In − out", money(net, True), T["OK"] if net >= 0 else danger(T), True)}
<span style="font: 400 19px/24px {HAND}; color: {T["PEN"]}">Up on the season. The tea hut is carrying us.</span>
</section>'''


def ledger_card():
    rows = ""
    for m in reversed(MATCHES):
        wk, opp, home, fans, seated, res = m
        i, o = match_lines(m)
        ti, to = sum(i.values()), sum(o.values())
        net = ti - to
        rc = T["OK"] if res.startswith("W") else (danger(T) if res.startswith("L") else T["MUTED"])
        rows += f'''<div style="display: grid; grid-template-columns: 52px minmax(0, 1fr) 46px 64px 70px 70px 78px; align-items: center; gap: 10px; height: 46px; padding: 0 14px; border-bottom: 1px solid {T["TAG_BORDER"]}">
<span style="font: 600 15px/18px {SANS}; color: {T["MUTED"]}">Wk {wk}</span>
<span style="font: 600 16px/20px {SANS}; color: {T["INK"]}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{opp}</span>
<span style="justify-self: start; width: 30px; height: 26px; border: 2px solid {T["INK"]}; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; font: 700 13px/16px {SANS}; color: {T["INK"]}; box-sizing: border-box">{"H" if home else "A"}</span>
<span style="font: 700 15px/18px {SANS}; color: {rc}">{res}</span>
<span style="font: 600 16px/20px {SANS}; color: {T["OK"]}; text-align: right">{money(ti)}</span>
<span style="font: 600 16px/20px {SANS}; color: {danger(T)}; text-align: right">{money(-to)}</span>
<span style="font: 700 16px/20px {SANS}; color: {T["OK"] if net >= 0 else danger(T)}; text-align: right">{money(net, True)}</span></div>'''
    head = "".join(f'<span style="text-align: {a}">{label(T, h, T["MUTED"])}</span>' for h, a in
                   [("Week", "left"), ("Opponent", "left"), ("", "left"), ("Result", "left"), ("In", "right"), ("Out", "right"), ("Net", "right")])
    return f'''<section style="{card(T, 'top: 140px; left: 500px; width: 820px; padding: 24px 24px 18px; display: flex; flex-direction: column; gap: 12px', 0.3, lines=False)}">
{pin(T, "30%")}{pin(T, "70%")}
<div style="display: flex; justify-content: space-between; align-items: baseline">{h2(T, "Match by match", 36)}<span style="font: 500 15px/20px {SANS}; color: {T["MUTED"]}">Click a match for the breakdown</span></div>
<div role="table" style="border-top: 2px solid {T["INK"]}">
<div style="display: grid; grid-template-columns: 52px minmax(0, 1fr) 46px 64px 70px 70px 78px; gap: 10px; height: 34px; align-items: center; padding: 0 14px; border-bottom: 1px solid {T["TAG_BORDER"]}">{head}</div>
{rows}</div>
<span style="font: 400 19px/24px {HAND}; color: {T["PEN"]}">Away days cost a fiver. Home days pay the bills.</span>
</section>'''


def cash_card():
    # balance per week: start £60, -£30 league fee +£50 sponsor in wk 1, matches, builds
    bal, pts = 60, []
    events = {1: SPONSOR - LEAGUE_FEE, 3: -48, 9: -40}
    for wk in range(0, 13):
        bal += events.get(wk, 0)
        for m in MATCHES:
            if m[0] == wk:
                i, o = match_lines(m)
                bal += sum(i.values()) - sum(o.values())
        pts.append(bal)
    W, H, pad = 760, 230, 30
    lo, hi = 0, max(pts) * 1.15
    xy = [(pad + (W - 2 * pad) * k / 42, H - pad - (H - 2 * pad) * (v - lo) / (hi - lo)) for k, v in enumerate(pts)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    marks = ""
    for wk, txt in ((3, "chairs"), (9, "bench")):
        x, y = xy[wk]
        marks += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{danger(T)}"/>'
                  f'<text x="{x + 8:.1f}" y="{y + 20:.1f}" font-family="Kalam" font-size="17" fill="{T["PEN"]}">{txt}</text>')
    lx, ly = xy[-1]
    grid = "".join(f'<line x1="{pad}" x2="{W - pad}" y1="{H - pad - (H - 2 * pad) * g:.1f}" y2="{H - pad - (H - 2 * pad) * g:.1f}" stroke="{T["LINES"]}" stroke-width="1"/>' for g in (0.25, 0.5, 0.75))
    weeks = "".join(f'<text x="{pad + (W - 2 * pad) * w / 42:.1f}" y="{H - 8}" font-family="Work Sans" font-size="13" fill="{T["MUTED"]}" text-anchor="middle">{w}</text>' for w in (1, 10, 20, 30, 42))
    svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-label="Cash per week">
{grid}<line x1="{pad}" x2="{W - pad}" y1="{H - pad}" y2="{H - pad}" stroke="{T["INK"]}" stroke-width="2"/>
<polyline points="{poly}" fill="none" stroke="{T["PRIMARY"]}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>
{marks}<circle cx="{lx:.1f}" cy="{ly:.1f}" r="7" fill="{T["PRIMARY"]}"/>
<text x="{lx + 12:.1f}" y="{ly + 6:.1f}" font-family="Work Sans" font-weight="700" font-size="18" fill="{T["INK"]}">{money(pts[-1])}</text>
<line x1="{lx:.1f}" x2="{W - pad}" y1="{ly:.1f}" y2="{ly:.1f}" stroke="{T["MUTED"]}" stroke-width="2" stroke-dasharray="4 6"/>
{weeks}</svg>'''
    return f'''<section style="{card(T, 'top: 640px; left: 500px; width: 820px; height: 300px; padding: 18px 24px 10px; display: flex; flex-direction: column; gap: 4px', -0.4, stripe=False, lines=False)}">
{tape(T, "top: -14px; left: 360px", 2)}
<div style="display: flex; justify-content: space-between; align-items: baseline">{h2(T, "Cash", 34)}{label(T, "This season, per week")}</div>
{svg}</section>'''


def coming_card():
    items = [("clock", "Section 7 bleachers", "paid · ready week 14", T["INK"]),
             ("stadium", "Next home match", "about +£64 (pitch, ref, kit −£15)", T["OK"]),
             ("cash", "Prize money", "+£1.70 at the end of the season", T["OK"]),
             ("warn", "League fee next season", "−£30 in week 1", danger(T))]
    lis = "".join(f'''<div style="display: flex; gap: 12px; align-items: flex-start"><span style="color: {c}; display: flex; padding-top: 2px">{icon(ic, 20)}</span>
<div style="display: flex; flex-direction: column"><span style="font: 600 16px/20px {SANS}; color: {T["NOTE_INK"]}">{a}</span><span style="font: 500 15px/20px {SANS}; color: {T["NOTE_MUTED"]}">{b}</span></div></div>'''
                  for ic, a, b, c in items)
    return f'''<section style="{note(T, 'top: 160px; right: 44px; width: 360px; padding: 26px 24px 22px; display: flex; flex-direction: column; gap: 14px', 1.4)}">
{tape(T, "top: -14px; left: 130px", -3)}
{h2(T, "Coming up", 34, T["NOTE_INK"])}
{lis}
<span style="font: 400 19px/24px {HAND}; color: {T["NOTE_MUTED"]}">Nan says the urn needs replacing. Not yet, Nan.</span>
</section>'''


def finances():
    body = topbar(T, cash="£262", seats="24", fans="31", approval="61%", record="W3 D1 L2") + season_card() + ledger_card() + cash_card() + coming_card() + strip(T, "Finances")
    return page("Finances", body)


if __name__ == "__main__":
    html = finances()
    out_dir = os.path.join(HERE, "..", "mockups")
    open(os.path.join(out_dir, "S_Finances.dc.html"), "w").write(html)
    # local preview: game screenshot behind it, local fonts, no canvas runtime
    bg = os.path.join(HERE, "..", "game", "hub_club.png")
    fonts = os.path.join(ROOT, "assets", "fonts")
    local = html.replace(HUB_BG, "file://" + os.path.abspath(bg)).replace('<script src="./support.js"></script>', "")
    ff = (f"@font-face{{font-family:'Kalam';font-weight:400;src:url('file://{fonts}/Kalam-Regular.ttf')}}"
          f"@font-face{{font-family:'Kalam';font-weight:700;src:url('file://{fonts}/Kalam-Bold.ttf')}}"
          f"@font-face{{font-family:'Work Sans';font-weight:100 900;src:url('file://{fonts}/WorkSans-Variable.ttf')}}")
    local = local.replace("body{margin:0}", ff + "body{margin:0}main>img:first-child{filter:blur(10px) brightness(.85)}")
    tmp = "/tmp/S_Finances_local.html"
    open(tmp, "w").write(local)
    png = os.path.abspath(os.path.join(HERE, "..", "finances_preview.png"))
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--allow-file-access-from-files", "--window-size=1920,1080", f"--screenshot={png}", "file://" + tmp],
                   check=True, capture_output=True)
    print("wrote", png)
