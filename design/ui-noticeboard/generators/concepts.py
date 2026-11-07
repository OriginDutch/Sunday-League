import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from lib import icon, crest, HUB_BG

OUT = "/home/claude/canvas/project"

NAV = [("club", "Club"), ("stadium", "Stadium"), ("recruit", "Recruitment"), ("squad", "Squad"), ("finances", "Finances")]
STATS = [("fans", "30", "Fans"), ("approval", "58%", "Fan approval"), ("cash", "£34", "Cash"),
         ("seat", "24", "Seats"), ("shirt", "11 / 11", "Squad"), ("record", "W4 D1 L3", "Friendlies only")]
TICKER = "Rumour has it the chairman is eyeing a second-hand scoreboard. Fancy."


def crest_svg(kind, w, col):
    s = crest(kind, w)
    return s.replace("#E8D9A8", col).replace("#F5F0DF", col)


def page(title, fonts, body, css=""):
    props = json.dumps({"$preview": {"width": 1920, "height": 1080}})
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?{fonts}&amp;display=swap" rel="stylesheet">
<style>
body{{margin:0}}
{css}
a{{color:inherit}}a:hover{{color:inherit}}
</style>
</helmet>
<main style="position: relative; width: 1920px; height: 1080px; overflow: hidden; background: #263B2E">
<img src="{HUB_BG}" alt="Your ground: the far touchline with benches, chairs and dugouts" style="position: absolute; inset: 0; width: 1920px; height: 1080px; object-fit: cover">
{body}
</main>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{props}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
'''


# =====================================================================
# 1. MATCHDAY PROGRAMME
def programme():
    INK, PAPER, RED, RULE, SOFT = "#1C2541", "#F4EFE4", "#C8102E", "#CBC2AE", "#5A6178"
    SERIF, SANS = "'DM Serif Display', serif", "'Archivo', sans-serif"
    card = f"background: {PAPER}; border: 2px solid {INK}; border-radius: 4px; box-shadow: 4px 4px 0 rgba(28,37,65,0.85); box-sizing: border-box"
    stats = "".join(f'''<div style="display: flex; flex-direction: column; padding: 0 18px; border-left: 1px solid {RULE}">
<span style="font: 800 22px/24px {SANS}; color: {INK}; white-space: nowrap">{v}</span>
<span style="font: 600 14px/16px {SANS}; color: {SOFT}; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap">{l}</span></div>''' for _, v, l in STATS)
    top = f'''<header style="{card} position: absolute; top: 24px; left: 32px; right: 32px; height: 84px; display: flex; align-items: stretch; overflow: hidden">
<div style="display: flex; align-items: center; gap: 14px; padding: 0 22px 0 16px; background: {INK}; color: {PAPER}">
{crest_svg("home", 44, PAPER)}
<div style="display: flex; flex-direction: column">
<span style="font: 400 30px/32px {SERIF}; color: {PAPER}; white-space: nowrap">Oakridge Rovers</span>
<span style="font: italic 500 14px/18px {SANS}; color: #C9CEDD; white-space: nowrap">Official Matchday Programme · Issue 9 · 50p</span></div></div>
<div style="width: 10px; background: {RED}"></div>
<div style="flex: 1"></div>
<div style="display: flex; align-items: center">{stats}</div>
<div style="display: flex; align-items: center; gap: 8px; padding: 0 16px; border-left: 1px solid {RULE}">
<button type="button" aria-label="Settings" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; justify-content: center; border: 2px solid {INK}; border-radius: 4px; background: transparent; color: {INK}; cursor: pointer">{icon("settings", 22)}</button>
<button type="button" aria-label="Quit to menu" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; justify-content: center; border: 2px solid {INK}; border-radius: 4px; background: transparent; color: {INK}; cursor: pointer">{icon("quit", 22)}</button></div>
</header>'''

    def band(t, page_no):
        return f'''<div style="display: flex; justify-content: space-between; align-items: center; height: 40px; padding: 0 18px; background: {INK}; color: {PAPER}">
<span style="font: 800 16px/20px {SANS}; letter-spacing: 0.12em; text-transform: uppercase">{t}</span>
<span style="font: italic 500 14px/18px {SANS}; color: #C9CEDD">p. {page_no}</span></div>'''

    goal = f'''<section style="{card} position: absolute; top: 136px; left: 32px; width: 420px; overflow: hidden">
{band("Our Goal", 3)}
<div style="padding: 20px 22px 22px; display: flex; flex-direction: column; gap: 14px">
<div style="display: flex; align-items: baseline; gap: 10px"><span style="font: 400 72px/64px {SERIF}; color: {RED}">24</span><span style="font: 700 20px/24px {SANS}; color: {INK}">/ 100 paying supporters</span></div>
<div style="height: 12px; border: 2px solid {INK}; background: #FFFFFF"><div style="width: 24%; height: 100%; background: {RED}"></div></div>
<p style="margin: 0; font: 500 16px/22px {SANS}; color: {SOFT}">Only seated fans pay (£2 each). More seats, more supporters.</p>
<div style="display: flex; gap: 14px; align-items: center; padding: 12px 14px; border: 2px dashed {RULE}">
<div style="display: flex; flex-direction: column; flex: 1"><span style="font: 800 14px/18px {SANS}; color: {INK}; text-transform: uppercase; letter-spacing: 0.06em">Advertise here</span><span style="font: italic 500 15px/20px {SANS}; color: {SOFT}">Ask for Pete at the bar. He'll do you a deal.</span></div>
<a href="#" style="display: flex; align-items: center; gap: 8px; height: 44px; padding: 0 16px; border: 2px solid {INK}; border-radius: 4px; text-decoration: none; color: {INK}; font: 700 16px/20px {SANS}; white-space: nowrap">{icon("stadium", 20)}Build seats</a></div>
</div></section>'''

    match = f'''<section style="{card} position: absolute; top: 136px; right: 32px; width: 440px; overflow: hidden">
{band("Next Match · Friendly", 1)}
<div style="padding: 20px 22px 22px; display: flex; flex-direction: column; gap: 16px">
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: center">
<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{crest_svg("home", 64, INK)}<span style="font: 400 22px/24px {SERIF}; color: {INK}">Oakridge Rovers</span></div>
<span style="text-align: center; font: italic 400 36px/36px {SERIF}; color: {RED}">v</span>
<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{crest_svg("away", 64, INK)}<span style="font: 400 22px/24px {SERIF}; color: {INK}">Riverside United</span></div></div>
<div style="height: 1px; background: {RULE}"></div>
<span style="font: italic 500 15px/20px {SANS}; color: {SOFT}; text-align: center">Kick-off: when everyone's found their boots.</span>
<button type="button" style="display: flex; align-items: center; justify-content: center; gap: 10px; height: 56px; border: 2px solid {INK}; border-radius: 4px; background: {RED}; color: #FFFFFF; font: 800 20px/24px {SANS}; letter-spacing: 0.04em; text-transform: uppercase; box-shadow: 3px 3px 0 {INK}; cursor: pointer">{icon("play", 20, "#FFFFFF")}Play Match</button>
<div style="display: flex; align-items: center; gap: 8px; font: 600 16px/22px {SANS}; color: #1F7A3E">{icon("check", 18)}All 11 players available.</div>
</div></section>'''

    nav = ""
    for ic, l in NAV:
        sel = l == "Club"
        st = f"background: {PAPER}; color: {INK}" if sel else f"background: transparent; color: {PAPER}"
        nav += f'<a href="#"{" aria-current=\"page\"" if sel else ""} style="display: flex; align-items: center; gap: 10px; height: 52px; padding: 0 18px; border-radius: 3px; text-decoration: none; font: 700 16px/20px {SANS}; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; {st}">{icon(ic, 22)}<span>{l}</span></a>'
    strip = f'''<nav aria-label="Club" style="position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); width: 1360px; height: 72px; box-sizing: border-box; display: flex; align-items: center; gap: 16px; padding: 0 10px 0 0; background: {INK}; border: 2px solid {INK}; border-radius: 4px; box-shadow: 4px 4px 0 rgba(0,0,0,0.35); overflow: hidden">
<span style="align-self: stretch; display: flex; align-items: center; padding: 0 16px; background: {RED}; color: #FFFFFF; font: 800 15px/18px {SANS}; letter-spacing: 0.1em; text-transform: uppercase; white-space: nowrap">Stop press</span>
<span style="flex: 1; min-width: 0; font: italic 500 18px/22px {SANS}; color: {PAPER}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{TICKER}</span>
<div style="display: flex; gap: 4px">{nav}</div></nav>'''
    fonts = "family=Archivo:ital,wght@0,500;0,600;0,700;0,800;1,500&amp;family=DM+Serif+Display:ital@0;1"
    return page("Concept 1 · Matchday Programme", fonts, top + goal + match + strip)


# =====================================================================
# 2. CLUBHOUSE NOTICEBOARD
def noticeboard():
    INK, PEN, PIN, NOTE, CARD, PAPER = "#24313A", "#2B59C3", "#E0483E", "#FFE58A", "#FBF8F1", "#F3EFE6"
    HAND, SANS = "'Kalam', cursive", "'Work Sans', sans-serif"
    def tape(pos, rot):
        return f'<span aria-hidden="true" style="position: absolute; {pos}; width: 96px; height: 28px; background: rgba(240,232,200,0.82); border-left: 2px dotted rgba(0,0,0,0.08); border-right: 2px dotted rgba(0,0,0,0.08); transform: rotate({rot}deg); box-shadow: 0 1px 2px rgba(0,0,0,0.15)"></span>'
    def pin(left):
        return f'<span aria-hidden="true" style="position: absolute; top: -9px; left: {left}; width: 20px; height: 20px; border-radius: 10px; background: {PIN}; box-shadow: inset -3px -3px 0 rgba(0,0,0,0.25), 0 3px 4px rgba(0,0,0,0.35)"></span>'
    shadow = "box-shadow: 0 8px 16px rgba(0,0,0,0.28), 0 1px 2px rgba(0,0,0,0.2)"
    stats = "".join(f'''<div style="position: relative; display: flex; align-items: center; gap: 8px; height: 52px; padding: 0 14px; background: #FFFFFF; border: 1px solid #D9D3C3; border-radius: 3px; transform: rotate({r}deg); box-shadow: 0 2px 4px rgba(0,0,0,0.15)">
<span style="color: {PEN}">{icon(ic, 20)}</span><div style="display: flex; flex-direction: column"><span style="font: 700 20px/22px {SANS}; color: {INK}; white-space: nowrap">{v}</span><span style="font: 500 14px/16px {SANS}; color: #5E6A72; white-space: nowrap">{l}</span></div></div>'''
                    for (ic, v, l), r in zip(STATS, [-1, 0.8, -0.4, 1, -0.8, 0.5]))
    top = f'''<header style="position: absolute; top: 24px; left: 32px; right: 32px; height: 84px; box-sizing: border-box; display: flex; align-items: center; gap: 14px; padding: 0 16px 0 20px; background: {PAPER}; border-radius: 3px; {shadow}">
{tape("top: -12px; left: 40px", -4)}{tape("top: -12px; right: 60px", 3)}
{crest_svg("home", 44, INK)}
<div style="display: flex; flex-direction: column"><span style="font: 700 30px/32px {HAND}; color: {INK}; white-space: nowrap">Oakridge Rovers</span><span style="font: 400 16px/18px {HAND}; color: #5E6A72; white-space: nowrap">The changing rooms are technically a shed.</span></div>
<div style="flex: 1"></div>
<div style="display: flex; gap: 10px">{stats}</div>
<div style="width: 1px; height: 44px; background: #D9D3C3"></div>
<button type="button" aria-label="Settings" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; justify-content: center; border: 1px solid #C9C2B0; border-radius: 6px; background: #FFFFFF; color: {INK}; cursor: pointer">{icon("settings", 22)}</button>
<button type="button" aria-label="Quit to menu" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; justify-content: center; border: 1px solid #C9C2B0; border-radius: 6px; background: #FFFFFF; color: {INK}; cursor: pointer">{icon("quit", 22)}</button>
</header>'''
    goal = f'''<section style="position: absolute; top: 146px; left: 40px; width: 410px; box-sizing: border-box; padding: 28px 26px 24px; background: {NOTE}; border-radius: 2px; transform: rotate(-1.4deg); {shadow}; display: flex; flex-direction: column; gap: 12px">
{tape("top: -14px; left: 156px", 2)}
<h2 style="margin: 0; font: 700 38px/40px {HAND}; color: {INK}">Our Goal</h2>
<p style="margin: 0; font: 600 20px/26px {SANS}; color: {INK}">Reach 100 paying supporters</p>
<div style="display: flex; justify-content: space-between"><span style="font: 500 16px/22px {SANS}; color: #4A4A3A">Paying supporters</span><span style="font: 700 18px/22px {SANS}; color: {INK}">24 / 100</span></div>
<div style="height: 14px; border: 2px solid {INK}; border-radius: 7px; background: #FFF6C9; overflow: hidden"><div style="width: 24%; height: 100%; background: repeating-linear-gradient(-45deg, {PEN} 0 4px, #4E78D6 4px 8px)"></div></div>
<span style="font: 400 19px/24px {HAND}; color: #4A4A3A">76 to go!! Ask your nan. And her mates. — Chairman</span>
<a href="#" style="align-self: flex-start; display: flex; align-items: center; gap: 8px; height: 44px; padding: 0 16px; border: 2px solid {INK}; border-radius: 6px; text-decoration: none; color: {INK}; background: rgba(255,255,255,0.5); font: 600 16px/20px {SANS}">{icon("stadium", 20)}Build seats</a>
</section>'''
    lines = "background-image: repeating-linear-gradient(to bottom, transparent 0 31px, rgba(43,89,195,0.13) 31px 32px); background-position: 0 56px"
    match = f'''<section style="position: absolute; top: 140px; right: 40px; width: 440px; box-sizing: border-box; padding: 26px 26px 24px; background-color: {CARD}; {lines}; border-radius: 3px; transform: rotate(0.9deg); {shadow}; display: flex; flex-direction: column; gap: 16px; border-top: 6px solid {PIN}">
{pin("50%")}
<div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="margin: 0; font: 700 38px/40px {HAND}; color: {INK}">Next Match</h2><span style="font: 700 14px/18px {SANS}; color: {PIN}; text-transform: uppercase; letter-spacing: 0.08em">Friendly</span></div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: center">
<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{crest_svg("home", 64, INK)}<span style="font: 700 18px/22px {SANS}; color: {INK}">Oakridge Rovers</span></div>
<span style="text-align: center; font: 700 34px/34px {HAND}; color: {PEN}">vs</span>
<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{crest_svg("away", 64, INK)}<span style="font: 700 18px/22px {SANS}; color: {INK}">Riverside United</span></div></div>
<span style="font: 400 19px/24px {HAND}; color: {PEN}; text-align: center">Lifts: Gaz has 3 seats. Bring oranges.</span>
<button type="button" style="display: flex; align-items: center; justify-content: center; gap: 10px; height: 56px; border: none; border-radius: 8px; background: {PEN}; color: #FFFFFF; font: 700 20px/24px {SANS}; box-shadow: 0 3px 0 #1D3E8C; cursor: pointer">{icon("play", 20, "#FFFFFF")}Play Match</button>
<div style="display: flex; align-items: center; gap: 8px; font: 600 16px/22px {SANS}; color: #1F7A3E">{icon("check", 18)}All 11 players available.</div>
</section>'''
    nav = ""
    for ic, l in NAV:
        sel = l == "Club"
        st = f"background: {NOTE}; color: {INK}; transform: translateY(-4px); box-shadow: 0 3px 6px rgba(0,0,0,0.2)" if sel else f"background: transparent; color: {INK}"
        nav += f'<a href="#"{" aria-current=\"page\"" if sel else ""} style="display: flex; align-items: center; gap: 10px; height: 52px; padding: 0 18px; border-radius: 4px; text-decoration: none; font: 600 17px/20px {SANS}; white-space: nowrap; {st}">{icon(ic, 22)}<span>{l}</span></a>'
    strip = f'''<nav aria-label="Club" style="position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); width: 1340px; height: 72px; box-sizing: border-box; display: flex; align-items: center; gap: 16px; padding: 0 10px 0 22px; background: {PAPER}; border-radius: 3px; {shadow}">
{tape("top: -14px; left: -20px", -8)}
<span style="color: {PIN}">{icon("news", 22)}</span>
<span style="flex: 1; min-width: 0; font: 700 20px/24px {HAND}; color: {INK}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{TICKER}</span>
<div style="width: 1px; height: 40px; background: #D9D3C3"></div>
<div style="display: flex; gap: 4px">{nav}</div></nav>'''
    fonts = "family=Kalam:wght@400;700&amp;family=Work+Sans:wght@500;600;700"
    return page("Concept 2 · Clubhouse Noticeboard", fonts, top + goal + match + strip)


# =====================================================================
# 3. SCOREBOARD
def scoreboard():
    BG, PANEL, LINE, TEXT, MUTED, LED, LIVE, OK = "#0E1A24", "rgba(14,26,36,0.92)", "#2A4153", "#EAF2F7", "#9FB3C2", "#FFB21E", "#FF5A4E", "#3DDC84"
    LEDF, SANS = "'VT323', monospace", "'Chakra Petch', sans-serif"
    card = f"background: {PANEL}; border: 1px solid {LINE}; border-radius: 6px; box-shadow: 0 6px 18px rgba(0,0,0,0.35); box-sizing: border-box"
    stats = "".join(f'''<div style="display: flex; flex-direction: column; padding: 0 18px; border-left: 1px solid {LINE}">
<span style="font: 400 34px/30px {LEDF}; color: {LED}; white-space: nowrap; text-shadow: 0 0 8px rgba(255,178,30,0.45)">{v}</span>
<span style="font: 600 14px/16px {SANS}; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.06em; white-space: nowrap">{l}</span></div>''' for _, v, l in STATS)
    top = f'''<header style="{card} position: absolute; top: 24px; left: 32px; right: 32px; height: 84px; display: flex; align-items: center; gap: 0; padding: 0 16px 0 0; border-top: 3px solid {LED}; overflow: hidden">
<div style="align-self: stretch; display: flex; align-items: center; gap: 14px; padding: 0 22px 0 18px; background: #133047">
{crest_svg("home", 44, TEXT)}
<div style="display: flex; flex-direction: column"><span style="font: 700 26px/30px {SANS}; color: {TEXT}; text-transform: uppercase; letter-spacing: 0.04em; white-space: nowrap">Oakridge Rovers</span><span style="font: 500 14px/18px {SANS}; color: {MUTED}; white-space: nowrap">Est. last Tuesday</span></div></div>
<div style="flex: 1"></div>
<div style="display: flex; align-items: center">{stats}</div>
<div style="display: flex; gap: 8px; padding-left: 16px; border-left: 1px solid {LINE}; margin-left: 8px">
<button type="button" aria-label="Settings" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; justify-content: center; border: 1px solid {LINE}; border-radius: 6px; background: transparent; color: {TEXT}; cursor: pointer">{icon("settings", 22)}</button>
<button type="button" aria-label="Quit to menu" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; justify-content: center; border: 1px solid {LINE}; border-radius: 6px; background: transparent; color: {TEXT}; cursor: pointer">{icon("quit", 22)}</button></div>
</header>'''
    def head(t, right=""):
        return f'<div style="display: flex; justify-content: space-between; align-items: center; height: 44px; padding: 0 18px; border-bottom: 1px solid {LINE}; background: rgba(19,48,71,0.7)"><span style="font: 700 16px/20px {SANS}; color: {TEXT}; letter-spacing: 0.12em; text-transform: uppercase">{t}</span>{right}</div>'
    segs = "".join(f'<span style="flex: 1; height: 16px; border-radius: 2px; background: {LED if i < 5 else "#1E3242"}; {"box-shadow: 0 0 6px rgba(255,178,30,0.6)" if i < 5 else ""}"></span>' for i in range(20))
    goal = f'''<section style="{card} position: absolute; top: 132px; left: 32px; width: 420px; overflow: hidden">
{head("Our Goal")}
<div style="padding: 18px 20px 22px; display: flex; flex-direction: column; gap: 14px">
<div style="display: flex; align-items: baseline; gap: 12px"><span style="font: 400 76px/60px {LEDF}; color: {LED}; text-shadow: 0 0 12px rgba(255,178,30,0.5)">024</span><span style="font: 600 18px/22px {SANS}; color: {TEXT}">/ 100 paying<br>supporters</span></div>
<div style="display: flex; gap: 3px">{segs}</div>
<p style="margin: 0; font: 500 16px/22px {SANS}; color: {MUTED}">Only seated fans pay (£2 each). More seats, more supporters.</p>
<a href="#" style="align-self: flex-start; display: flex; align-items: center; gap: 8px; height: 44px; padding: 0 16px; border: 1px solid {LED}; border-radius: 6px; text-decoration: none; color: {LED}; font: 700 15px/20px {SANS}; text-transform: uppercase; letter-spacing: 0.06em">{icon("stadium", 20)}Build seats</a>
</div></section>'''
    def team(abbr, name, col, kind):
        return f'''<div style="display: flex; align-items: center; height: 56px; border-bottom: 1px solid {LINE}">
<span style="width: 8px; align-self: stretch; background: {col}"></span>
<span style="padding: 0 12px">{crest_svg(kind, 32, TEXT)}</span>
<span style="font: 700 24px/28px {SANS}; color: {TEXT}; letter-spacing: 0.06em; width: 70px">{abbr}</span>
<span style="flex: 1; font: 500 16px/20px {SANS}; color: {MUTED}">{name}</span>
<span style="width: 56px; text-align: center; font: 400 38px/34px {LEDF}; color: #33495A">-</span></div>'''
    match = f'''<section style="{card} position: absolute; top: 132px; right: 32px; width: 440px; overflow: hidden">
{head("Next Match", f'<span style="display: flex; align-items: center; gap: 6px; font: 700 13px/16px {SANS}; color: {LIVE}; letter-spacing: 0.1em"><span style="width: 8px; height: 8px; border-radius: 4px; background: {LIVE}"></span>FRIENDLY</span>')}
{team("OAK", "Oakridge Rovers", "#3DDC84", "home")}
{team("RIV", "Riverside United", "#4EA8FF", "away")}
<div style="padding: 18px 20px 20px; display: flex; flex-direction: column; gap: 12px">
<span style="font: 400 24px/24px {LEDF}; color: {LED}">KICK-OFF: WHEN THE REF TURNS UP</span>
<button type="button" style="display: flex; align-items: center; justify-content: center; gap: 10px; height: 56px; border: none; border-radius: 6px; background: {LED}; color: {BG}; font: 700 20px/24px {SANS}; text-transform: uppercase; letter-spacing: 0.08em; box-shadow: 0 0 18px rgba(255,178,30,0.35); cursor: pointer">{icon("play", 20, BG)}Play Match</button>
<div style="display: flex; align-items: center; gap: 8px; font: 600 16px/22px {SANS}; color: {OK}">{icon("check", 18)}All 11 players available.</div>
</div></section>'''
    nav = ""
    for ic, l in NAV:
        sel = l == "Club"
        st = f"background: rgba(255,178,30,0.14); color: {LED}; box-shadow: inset 0 -3px 0 {LED}" if sel else f"background: transparent; color: {TEXT}"
        nav += f'<a href="#"{" aria-current=\"page\"" if sel else ""} style="display: flex; align-items: center; gap: 10px; height: 52px; padding: 0 16px; border-radius: 4px; text-decoration: none; font: 700 15px/20px {SANS}; text-transform: uppercase; letter-spacing: 0.08em; white-space: nowrap; {st}">{icon(ic, 22)}<span>{l}</span></a>'
    strip = f'''<nav aria-label="Club" style="{card} position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); width: 1360px; height: 72px; display: flex; align-items: center; gap: 14px; padding: 0 10px 0 0; overflow: hidden">
<span style="align-self: stretch; display: flex; align-items: center; padding: 0 16px; background: {LIVE}; color: #FFFFFF; font: 700 14px/18px {SANS}; letter-spacing: 0.12em">RUMOUR</span>
<span style="flex: 1; min-width: 0; font: 400 28px/28px {LEDF}; color: {LED}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-shadow: 0 0 8px rgba(255,178,30,0.4)">{TICKER.upper()}</span>
<div style="width: 1px; height: 40px; background: {LINE}"></div>
<div style="display: flex; gap: 2px">{nav}</div></nav>'''
    fonts = "family=Chakra+Petch:wght@500;600;700&amp;family=VT323"
    return page("Concept 3 · Scoreboard", fonts, top + goal + match + strip)


# =====================================================================
# 4. STICKER ALBUM
def stickers():
    INK, PAGE, TEAL, SUN, CORAL, MUTED = "#1B1B1F", "#FFFDF7", "#0E7C7B", "#FFC93C", "#FF6B57", "#5B5B66"
    DISP, SANS = "'Bricolage Grotesque', sans-serif", "'Inter', sans-serif"
    card = f"background: {PAGE}; border: 3px solid {INK}; border-radius: 16px; box-shadow: 0 5px 0 {INK}; box-sizing: border-box"
    cols = [TEAL, SUN, CORAL, TEAL, SUN, CORAL]
    txt = ["#FFFFFF", INK, INK, "#FFFFFF", INK, INK]
    stats = "".join(f'''<div style="position: relative; display: flex; align-items: center; gap: 8px; height: 52px; padding: 0 14px 0 12px; background: {c}; color: {t}; border: 2px solid {INK}; border-radius: 10px; overflow: hidden">
{icon(ic, 20)}<div style="display: flex; flex-direction: column"><span style="font: 800 20px/22px {DISP}; white-space: nowrap">{v}</span><span style="font: 600 14px/16px {SANS}; white-space: nowrap; opacity: 0.85">{l}</span></div>
<span aria-hidden="true" style="position: absolute; right: -1px; bottom: -1px; width: 14px; height: 14px; background: linear-gradient(135deg, transparent 50%, #FFFFFF 50%); border-top-left-radius: 3px"></span></div>'''
                    for (ic, v, l), c, t in zip(STATS, cols, txt))
    top = f'''<header style="{card} position: absolute; top: 24px; left: 32px; right: 32px; height: 84px; display: flex; align-items: center; gap: 12px; padding: 0 14px 0 16px">
<div style="width: 52px; height: 60px; display: flex; align-items: center; justify-content: center; background: {TEAL}; border: 2px solid {INK}; border-radius: 10px; transform: rotate(-4deg)">{crest_svg("home", 38, "#FFFFFF")}</div>
<div style="display: flex; flex-direction: column"><span style="font: 800 28px/30px {DISP}; color: {INK}; white-space: nowrap">Oakridge Rovers</span><span style="font: 500 15px/18px {SANS}; color: {MUTED}; white-space: nowrap">Season 1 album · got, got, need</span></div>
<div style="flex: 1"></div>
<div style="display: flex; gap: 8px">{stats}</div>
<button type="button" aria-label="Settings" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; justify-content: center; border: 2px solid {INK}; border-radius: 10px; background: {PAGE}; color: {INK}; cursor: pointer">{icon("settings", 22)}</button>
<button type="button" aria-label="Quit to menu" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; justify-content: center; border: 2px solid {INK}; border-radius: 10px; background: {PAGE}; color: {INK}; cursor: pointer">{icon("quit", 22)}</button>
</header>'''
    slots = ""
    for i in range(10):
        if i < 2:
            slots += f'<div style="aspect-ratio: 3 / 4; border: 2px solid {INK}; border-radius: 8px; background: {[CORAL, SUN][i]}; display: flex; align-items: center; justify-content: center; color: {INK}; transform: rotate({[-3, 2][i]}deg)">{icon("fans", 22)}</div>'
        elif i == 2:
            slots += f'<div style="aspect-ratio: 3 / 4; border: 2px dashed {INK}; border-radius: 8px; background: linear-gradient(to top, rgba(14,124,123,0.35) 40%, transparent 40%); display: flex; align-items: center; justify-content: center; font: 800 15px/18px {DISP}; color: {INK}">4/10</div>'
        else:
            slots += f'<div style="aspect-ratio: 3 / 4; border: 2px dashed #B9B5A8; border-radius: 8px; display: flex; align-items: center; justify-content: center; font: 700 15px/18px {DISP}; color: #9A968A">{(i + 1) * 10}</div>'
    goal = f'''<section style="{card} position: absolute; top: 136px; left: 32px; width: 420px; padding: 20px 22px 22px; display: flex; flex-direction: column; gap: 14px">
<div style="display: flex; justify-content: space-between; align-items: center"><h2 style="margin: 0; font: 800 30px/34px {DISP}; color: {INK}">Our Goal</h2><span style="padding: 4px 10px; border: 2px solid {INK}; border-radius: 999px; background: {SUN}; font: 800 15px/18px {DISP}; color: {INK}">24 / 100</span></div>
<p style="margin: 0; font: 600 17px/22px {SANS}; color: {INK}">Fill the page: 100 paying supporters. One sticker = 10 fans.</p>
<div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px">{slots}</div>
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px">
<span style="font: 500 15px/20px {SANS}; color: {MUTED}">Only seated fans pay (£2 each).</span>
<a href="#" style="display: flex; align-items: center; gap: 8px; height: 44px; padding: 0 16px; border: 2px solid {INK}; border-radius: 10px; text-decoration: none; color: {INK}; background: {PAGE}; font: 700 16px/20px {SANS}; white-space: nowrap; box-shadow: 0 3px 0 {INK}">{icon("stadium", 20)}Build seats</a></div>
</section>'''
    def sticker(kind, name, col, fg, rot):
        return f'''<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 14px 10px 12px; background: {col}; border: 3px solid {INK}; border-radius: 12px; transform: rotate({rot}deg); box-shadow: 0 4px 0 {INK}">{crest_svg(kind, 58, fg)}<span style="font: 800 17px/20px {DISP}; color: {fg}; text-align: center">{name}</span></div>'''
    match = f'''<section style="{card} position: absolute; top: 136px; right: 32px; width: 440px; padding: 20px 22px 22px; display: flex; flex-direction: column; gap: 18px">
<div style="display: flex; justify-content: space-between; align-items: center"><h2 style="margin: 0; font: 800 30px/34px {DISP}; color: {INK}">Next Match</h2><span style="padding: 4px 10px; border: 2px solid {INK}; border-radius: 999px; background: {PAGE}; font: 700 14px/18px {SANS}; color: {INK}">Friendly</span></div>
<div style="display: grid; grid-template-columns: minmax(0, 1fr) 64px minmax(0, 1fr); align-items: center; gap: 6px">
{sticker("home", "Oakridge Rovers", TEAL, "#FFFFFF", -3)}
<div style="width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: {CORAL}; border: 3px solid {INK}; clip-path: polygon(50% 0, 61% 18%, 82% 10%, 80% 32%, 100% 40%, 84% 55%, 96% 75%, 74% 76%, 70% 98%, 50% 84%, 30% 98%, 26% 76%, 4% 75%, 16% 55%, 0 40%, 20% 32%, 18% 10%, 39% 18%); font: 800 22px/22px {DISP}; color: {INK}">vs</div>
{sticker("away", "Riverside United", SUN, INK, 2.5)}</div>
<span style="font: 500 15px/20px {SANS}; color: {MUTED}; text-align: center">Their keeper is a shiny. Very rare. Very tall.</span>
<button type="button" style="display: flex; align-items: center; justify-content: center; gap: 10px; height: 56px; border: 3px solid {INK}; border-radius: 12px; background: {SUN}; color: {INK}; font: 800 21px/24px {DISP}; box-shadow: 0 5px 0 {INK}; cursor: pointer">{icon("play", 20, INK)}Play Match</button>
<div style="display: flex; align-items: center; gap: 8px; font: 600 16px/22px {SANS}; color: {TEAL}">{icon("check", 18)}All 11 players available.</div>
</section>'''
    nav = ""
    for ic, l in NAV:
        sel = l == "Club"
        st = f"background: {TEAL}; color: #FFFFFF; border: 2px solid {INK}" if sel else f"background: transparent; color: {INK}; border: 2px solid transparent"
        nav += f'<a href="#"{" aria-current=\"page\"" if sel else ""} style="display: flex; align-items: center; gap: 10px; height: 52px; padding: 0 16px; border-radius: 12px; box-sizing: border-box; text-decoration: none; font: 700 17px/20px {SANS}; white-space: nowrap; {st}">{icon(ic, 22)}<span>{l}</span></a>'
    strip = f'''<nav aria-label="Club" style="{card} position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); width: 1340px; height: 72px; border-radius: 999px; display: flex; align-items: center; gap: 14px; padding: 0 10px 0 12px">
<span style="display: flex; align-items: center; gap: 6px; height: 44px; padding: 0 14px; border-radius: 999px; background: {CORAL}; border: 2px solid {INK}; font: 800 15px/18px {DISP}; color: {INK}; white-space: nowrap">{icon("news", 18)}Swaps</span>
<span style="flex: 1; min-width: 0; font: 600 18px/22px {SANS}; color: {INK}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{TICKER}</span>
<div style="display: flex; gap: 4px">{nav}</div></nav>'''
    fonts = "family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&amp;family=Inter:wght@500;600;700"
    return page("Concept 4 · Sticker Album", fonts, top + goal + match + strip)


for fn, f in [("Concept_Programme.dc.html", programme), ("Concept_Noticeboard.dc.html", noticeboard),
              ("Concept_Scoreboard.dc.html", scoreboard), ("Concept_StickerAlbum.dc.html", stickers)]:
    open(os.path.join(OUT, fn), "w").write(f())
print("ok")
