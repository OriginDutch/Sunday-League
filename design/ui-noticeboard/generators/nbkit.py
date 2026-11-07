"""Clubhouse Noticeboard building blocks (club colours red/white by default)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from lib import icon, crest, HUB_BG, BUILD_BG
from noticeboard import RED_WHITE, DARK_RW

HAND, SANS = "'Kalam', cursive", "'Work Sans', sans-serif"
FONTS = "family=Kalam:wght@400;700&amp;family=Work+Sans:wght@500;600;700"
DANGER_L, DANGER_D = "#B8322A", "#FF8A7A"
NAV = [("club", "Club"), ("stadium", "Stadium"), ("recruit", "Recruitment"), ("squad", "Squad"), ("finances", "Finances")]


def danger(T):
    return DANGER_D if T["PAPER"] == "#25292D" else DANGER_L


def crest_svg(kind, w, col):
    return crest(kind, w).replace("#E8D9A8", col).replace("#F5F0DF", col)


def tape(T, pos, rot, w=96):
    return (f'<span aria-hidden="true" style="position: absolute; {pos}; width: {w}px; height: 28px; background: {T["TAPE"]}; '
            f'border-left: 2px dotted rgba(0,0,0,0.08); border-right: 2px dotted rgba(0,0,0,0.08); transform: rotate({rot}deg); '
            f'box-shadow: 0 1px 2px rgba(0,0,0,0.15); z-index: 2"></span>')


def pin(T, left="50%", top=-9):
    return (f'<span aria-hidden="true" style="position: absolute; top: {top}px; left: {left}; width: 20px; height: 20px; border-radius: 10px; '
            f'background: {T["PIN"]}; box-shadow: inset -3px -3px 0 rgba(0,0,0,0.25), 0 3px 4px rgba(0,0,0,0.35); z-index: 2"></span>')


def paper(T, extra=""):
    return f"position: absolute; box-sizing: border-box; background: {T['PAPER']}; border-radius: 3px; box-shadow: {T['SHADOW']}; {extra}"


def note(T, extra="", rot=-1.4):
    return f"position: absolute; box-sizing: border-box; background: {T['NOTE']}; border-radius: 2px; transform: rotate({rot}deg); box-shadow: {T['SHADOW']}; {extra}"


def card(T, extra="", rot=0.0, stripe=True, lines=True):
    ln = (f"background-image: repeating-linear-gradient(to bottom, transparent 0 31px, {T['LINES']} 31px 32px); background-position: 0 56px;"
          if lines else "")
    st = f"border-top: 6px solid {T['STRIPE']};" if stripe else ""
    return (f"position: absolute; box-sizing: border-box; background-color: {T['CARD']}; {ln} {st} border-radius: 3px; "
            f"transform: rotate({rot}deg); box-shadow: {T['SHADOW']}; {extra}")


def h2(T, text, size=38, col=None):
    return f'<h2 style="margin: 0; font: 700 {size}px/{size + 2}px {HAND}; color: {col or T["INK"]}">{text}</h2>'


def label(T, text, col=None):
    return f'<span style="font: 700 14px/18px {SANS}; color: {col or T["PEN"]}; text-transform: uppercase; letter-spacing: 0.08em">{text}</span>'


def primary(T, text, ic="play", disabled=False, h=56, size=20, full=True, extra=""):
    w = "width: 100%;" if full else ""
    if disabled:
        return (f'<button type="button" disabled style="{w} display: flex; align-items: center; justify-content: center; gap: 10px; height: {h}px; padding: 0 22px; '
                f'border: none; border-radius: 8px; background: {T["TAG_BORDER"]}; color: {T["MUTED"]}; font: 700 {size}px/24px {SANS}; box-sizing: border-box; {extra}">{icon(ic, 20) if ic else ""}{text}</button>')
    return (f'<button type="button" style="{w} display: flex; align-items: center; justify-content: center; gap: 10px; height: {h}px; padding: 0 22px; '
            f'border: none; border-radius: 8px; background: {T["PRIMARY"]}; color: {T["PRIMARY_FG"]}; font: 700 {size}px/24px {SANS}; '
            f'box-shadow: 0 3px 0 {T["PRIMARY_SH"]}; cursor: pointer; box-sizing: border-box; {extra}">{icon(ic, 20) if ic else ""}{text}</button>')


def link_btn(T, text, ic=None, on_note=False, h=44, state="default", href="#"):
    ink = T["NOTE_INK"] if on_note else T["INK"]
    bg = T["LINK_BG"]
    tr = ""
    if state == "hover":
        bg = "rgba(255,255,255,0.8)" if T["PAPER"] != "#25292D" else "rgba(255,255,255,0.12)"
    if state == "pressed":
        tr = "transform: translateY(1px);"
    if state == "disabled":
        ink = T["MUTED"]
    return (f'<a href="{href}" style="display: inline-flex; align-items: center; gap: 8px; height: {h}px; padding: 0 16px; border: 2px solid {ink}; border-radius: 6px; '
            f'text-decoration: none; color: {ink}; background: {bg}; font: 600 16px/20px {SANS}; white-space: nowrap; box-sizing: border-box; {tr}">{icon(ic, 20) if ic else ""}{text}</a>')


def ibtn(T, ic, lab, state="default"):
    border, col = T["BTN_BORDER"], T["INK"]
    if state in ("hover", "pressed"):
        border = T["INK"]
    if state == "selected":
        border, col = T["PEN"], T["PEN"]
    if state == "disabled":
        col = T["MUTED"]
    tr = "transform: translateY(1px);" if state == "pressed" else ""
    return (f'<button type="button" aria-label="{lab}" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; justify-content: center; '
            f'border: 1px solid {border}; border-radius: 6px; background: {T["BTN_BG"]}; color: {col}; cursor: pointer; flex-shrink: 0; {tr}">{icon(ic, 22)}</button>')


def stat_tag(T, ic, v, l, rot=0, val_col=None, delta=None):
    d = ""
    if delta:
        dc = T["OK"] if delta.startswith("+") else danger(T)
        d = f'<span style="font: 700 14px/16px {SANS}; color: {dc}; margin-left: 4px">{delta}</span>'
    return (f'<div style="display: flex; align-items: center; gap: 8px; height: 52px; padding: 0 14px; background: {T["TAG_BG"]}; border: 1px solid {T["TAG_BORDER"]}; '
            f'border-radius: 3px; transform: rotate({rot}deg); box-shadow: 0 2px 4px rgba(0,0,0,0.15); box-sizing: border-box">'
            f'<span style="color: {T["TAG_ICON"]}; display: flex">{icon(ic, 20)}</span><div style="display: flex; flex-direction: column">'
            f'<span style="font: 700 20px/22px {SANS}; color: {val_col or T["INK"]}; white-space: nowrap">{v}{d}</span>'
            f'<span style="font: 500 14px/16px {SANS}; color: {T["MUTED"]}; white-space: nowrap">{l}</span></div></div>')


def topbar(T, squad="11 / 11", cash="£34", seats="24", fans="30", approval="58%", record="W4 D1 L3"):
    sq_col = danger(T) if not squad.startswith("11") else None
    stats = [("fans", fans, "Fans", None), ("approval", approval, "Fan approval", None), ("cash", cash, "Cash", None),
             ("seat", seats, "Seats", None), ("shirt", squad, "Squad", sq_col), ("record", record, "Friendlies only", None)]
    rots = [-1, 0.8, -0.4, 1, -0.8, 0.5]
    tags = "".join(stat_tag(T, ic, v, l, r, c) for (ic, v, l, c), r in zip(stats, rots))
    sw = "".join(f'<span style="width: 16px; height: 16px; border-radius: 3px; background: {c}; border: 1px solid rgba(0,0,0,0.25)"></span>' for c in ["#D0202E", "#FFFFFF"])
    return f'''<header style="{paper(T, 'top: 24px; left: 32px; right: 32px; height: 84px; display: flex; align-items: center; gap: 14px; padding: 0 16px 0 20px; z-index: 5')}">
{tape(T, "top: -12px; left: 40px", -4)}{tape(T, "top: -12px; right: 60px", 3)}
{crest_svg("home", 44, T["CREST"])}
<div style="display: flex; flex-direction: column"><div style="display: flex; align-items: center; gap: 8px"><span style="font: 700 30px/32px {HAND}; color: {T["INK"]}; white-space: nowrap">Oakridge Rovers</span><div aria-label="Club colours" style="display: flex; gap: 4px">{sw}</div></div><span style="font: 400 16px/18px {HAND}; color: {T["MUTED"]}; white-space: nowrap">The changing rooms are technically a shed.</span></div>
<div style="flex: 1"></div>
<div style="display: flex; gap: 10px">{tags}</div>
<div style="width: 1px; height: 44px; background: {T["DIV"]}"></div>
{ibtn(T, "settings", "Settings")}
{ibtn(T, "quit", "Quit to menu")}
</header>'''


def nav_item(T, ic, l, state="default"):
    st = {"default": f"background: transparent; color: {T['INK']}",
          "hover": f"background: rgba(36,49,58,0.06); color: {T['INK']}",
          "pressed": f"background: rgba(36,49,58,0.10); color: {T['INK']}",
          "selected": f"background: {T['SEL_BG']}; color: {T['SEL_FG']}; transform: translateY(-4px); box-shadow: 0 3px 6px rgba(0,0,0,0.2)",
          "disabled": f"background: transparent; color: {T['MUTED']}"}[state]
    cur = ' aria-current="page"' if state == "selected" else ""
    return (f'<a href="#"{cur} style="display: flex; align-items: center; gap: 10px; height: 52px; padding: 0 18px; border-radius: 4px; text-decoration: none; '
            f'font: 600 17px/20px {SANS}; white-space: nowrap; box-sizing: border-box; {st}">{icon(ic, 22)}<span>{l}</span></a>')


def strip(T, selected="Club", ticker="Rumour has it the chairman is eyeing a second-hand scoreboard. Fancy."):
    nav = "".join(nav_item(T, ic, l, "selected" if l == selected else "default") for ic, l in NAV)
    return f'''<nav aria-label="Club" style="{paper(T, 'bottom: 24px; left: 50%; transform: translateX(-50%); width: 1340px; height: 72px; display: flex; align-items: center; gap: 16px; padding: 0 10px 0 22px; z-index: 5')}">
{tape(T, "top: -14px; left: -20px", -8)}
<span style="color: {T["PIN"]}; display: flex">{icon("news", 22)}</span>
<span style="flex: 1; min-width: 0; font: 700 20px/24px {HAND}; color: {T["INK"]}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{ticker}</span>
<div style="width: 1px; height: 40px; background: {T["DIV"]}"></div>
<div style="display: flex; gap: 4px">{nav}</div></nav>'''


def progress(T, pct, on_note=True, w="100%"):
    ink = T["NOTE_INK"] if on_note else T["INK"]
    track = T["BAR_BG"] if on_note else T["TAG_BG"]
    return (f'<div style="width: {w}; height: 14px; border: 2px solid {ink}; border-radius: 7px; background: {track}; overflow: hidden; box-sizing: border-box">'
            f'<div style="width: {pct}%; height: 100%; background: repeating-linear-gradient(-45deg, {T["HATCH1"]} 0 4px, {T["HATCH2"]} 4px 8px)"></div></div>')


def slider(T, lab, val, sub=""):
    return f'''<div style="display: flex; flex-direction: column; gap: 6px">
<div style="display: flex; justify-content: space-between"><label style="font: 600 16px/20px {SANS}; color: {T["INK"]}">{lab}</label><span style="font: 700 16px/20px {SANS}; color: {T["INK"]}">{val}{sub}</span></div>
<div style="position: relative; height: 44px; display: flex; align-items: center">
<div style="width: 100%; height: 8px; border-radius: 4px; background: {T["TAG_BG"]}; border: 2px solid {T["INK"]}; box-sizing: border-box; overflow: hidden"><div style="width: {val}%; height: 100%; background: {T["PRIMARY"]}"></div></div>
<span style="position: absolute; left: calc({val}% - 12px); width: 24px; height: 24px; border-radius: 12px; background: {T["TAG_BG"]}; border: 2px solid {T["INK"]}; box-sizing: border-box; box-shadow: 0 2px 3px rgba(0,0,0,0.25)"></span>
</div></div>'''


def segmented(T, options, selected):
    items = ""
    for o in options:
        sel = o == selected
        st = f"background: {T['SEL_BG']}; color: {T['SEL_FG']}" if sel else f"background: transparent; color: {T['INK']}"
        items += f'<button type="button" aria-pressed="{"true" if sel else "false"}" style="flex: 1; height: 44px; border: none; border-radius: 4px; font: 600 16px/20px {SANS}; cursor: pointer; {st}">{o}</button>'
    return f'<div role="group" style="display: flex; gap: 4px; padding: 4px; border: 2px solid {T["INK"]}; border-radius: 6px; background: {T["TAG_BG"]}">{items}</div>'


def page(title, body, bg=HUB_BG, w=1920, h=1080, bg_flip=False, bg_color="#263B2E", alt="Your ground, behind the menus"):
    props = json.dumps({"$preview": {"width": w, "height": h}})
    img = ""
    if bg:
        fl = "transform: scaleX(-1);" if bg_flip else ""
        img = f'<img src="{bg}" alt="{alt}" style="position: absolute; inset: 0; width: 1920px; height: 1080px; object-fit: cover; {fl}">'
    size = f"width: {w}px; height: {h}px;" if h else f"width: {w}px;"
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
<link href="https://fonts.googleapis.com/css2?{FONTS}&amp;display=swap" rel="stylesheet">
<style>
body{{margin:0}}
a{{color:inherit}}a:hover{{color:inherit}}
</style>
</helmet>
<main style="position: relative; {size} overflow: hidden; background: {bg_color}; font-family: {SANS}">
{img}
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
