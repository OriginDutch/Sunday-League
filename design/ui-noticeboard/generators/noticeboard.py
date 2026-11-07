import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import icon
from concepts import page, crest_svg, NAV, STATS, TICKER

OUT = "/home/claude/canvas/project"
HAND, SANS = "'Kalam', cursive", "'Work Sans', sans-serif"
FONTS = "family=Kalam:wght@400;700&amp;family=Work+Sans:wght@500;600;700"

LIGHT = dict(
    INK="#24313A", MUTED="#5E6A72", PAPER="#F3EFE6", CARD="#FBF8F1", NOTE="#FFE58A", NOTE_INK="#24313A",
    NOTE_MUTED="#4A4A3A", TAG_BG="#FFFFFF", TAG_BORDER="#D9D3C3", DIV="#D9D3C3", BTN_BG="#FFFFFF",
    BTN_BORDER="#C9C2B0", PEN="#2B59C3", PIN="#E0483E", TAPE="rgba(240,232,200,0.82)",
    PRIMARY="#2B59C3", PRIMARY_FG="#FFFFFF", PRIMARY_SH="#1D3E8C", SEL_BG="#FFE58A", SEL_FG="#24313A",
    HATCH1="#2B59C3", HATCH2="#4E78D6", BAR_BG="#FFF6C9", LINES="rgba(43,89,195,0.13)", OK="#1F7A3E",
    SHADOW="0 8px 16px rgba(0,0,0,0.28), 0 1px 2px rgba(0,0,0,0.2)", CREST="#24313A", STRIPE="#E0483E",
    LINK_BG="rgba(255,255,255,0.5)", TAG_ICON="#2B59C3")

DARK = dict(LIGHT,
    INK="#F1ECDF", MUTED="#B9B3A6", PAPER="#2B3034", CARD="#262B2F", NOTE="#4A4024", NOTE_INK="#F6EBC4",
    NOTE_MUTED="#D9CC9E", TAG_BG="#343A3F", TAG_BORDER="#4A5258", DIV="#4A5258", BTN_BG="#343A3F",
    BTN_BORDER="#566067", PEN="#8FB0F5", TAPE="rgba(215,205,170,0.30)", PRIMARY="#8FB0F5", PRIMARY_FG="#13213F",
    PRIMARY_SH="#4B6FBF", SEL_BG="#4A4024", SEL_FG="#F6EBC4", HATCH1="#8FB0F5", HATCH2="#6E93E3",
    BAR_BG="#2F2915", LINES="rgba(143,176,245,0.10)", OK="#7FD39A",
    SHADOW="0 10px 22px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.4)", CREST="#F1ECDF",
    LINK_BG="rgba(255,255,255,0.06)", TAG_ICON="#8FB0F5")

EVENING = dict(LIGHT,
    INK="#2A2620", MUTED="#5A5246", PAPER="#D9CDB3", CARD="#E3D8C0", NOTE="#E3C46A", NOTE_INK="#2A2620",
    NOTE_MUTED="#4A3F25", TAG_BG="#EAE0CA", TAG_BORDER="#B9AC90", DIV="#B9AC90", BTN_BG="#EAE0CA",
    BTN_BORDER="#A89B80", PEN="#2B4F9E", TAPE="rgba(214,200,160,0.85)", PRIMARY="#2B4F9E", PRIMARY_SH="#1B3470",
    SEL_BG="#E3C46A", HATCH1="#2B4F9E", HATCH2="#4466B5", BAR_BG="#EBD68E", LINES="rgba(43,79,158,0.14)",
    OK="#1E6B37", SHADOW="0 12px 24px rgba(20,10,0,0.55), 0 2px 3px rgba(20,10,0,0.35), inset 0 0 40px rgba(90,60,20,0.18)",
    LINK_BG="rgba(255,255,255,0.35)", TAG_ICON="#2B4F9E")

RED_WHITE = dict(LIGHT,
    PEN="#C21B2A", PIN="#D0202E", TAPE="rgba(208,32,46,0.78)", PRIMARY="#D0202E", PRIMARY_FG="#FFFFFF",
    PRIMARY_SH="#8E1520", SEL_BG="#D0202E", SEL_FG="#FFFFFF", HATCH1="#D0202E", HATCH2="#E85662",
    LINES="rgba(208,32,46,0.10)", CREST="#C21B2A", STRIPE="#D0202E", TAG_ICON="#C21B2A")

BLUE_YELLOW = dict(LIGHT,
    PEN="#1F4AA8", PIN="#1F4AA8", TAPE="rgba(245,197,24,0.88)", PRIMARY="#1F4AA8", PRIMARY_FG="#FFFFFF",
    PRIMARY_SH="#132F6E", SEL_BG="#F5C518", SEL_FG="#1B2440", HATCH1="#1F4AA8", HATCH2="#3D68C9",
    LINES="rgba(31,74,168,0.12)", CREST="#1F4AA8", STRIPE="#F5C518", TAG_ICON="#1F4AA8")


def build(t, title, club_swatch=None):
    INK, MUTED = t["INK"], t["MUTED"]
    SH = t["SHADOW"]

    def tape(pos, rot):
        return (f'<span aria-hidden="true" style="position: absolute; {pos}; width: 96px; height: 28px; background: {t["TAPE"]}; '
                f'border-left: 2px dotted rgba(0,0,0,0.08); border-right: 2px dotted rgba(0,0,0,0.08); transform: rotate({rot}deg); '
                f'box-shadow: 0 1px 2px rgba(0,0,0,0.15)"></span>')

    def pin(left):
        return (f'<span aria-hidden="true" style="position: absolute; top: -9px; left: {left}; width: 20px; height: 20px; border-radius: 10px; '
                f'background: {t["PIN"]}; box-shadow: inset -3px -3px 0 rgba(0,0,0,0.25), 0 3px 4px rgba(0,0,0,0.35)"></span>')

    def ibtn(ic, label):
        return (f'<button type="button" aria-label="{label}" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; '
                f'justify-content: center; border: 1px solid {t["BTN_BORDER"]}; border-radius: 6px; background: {t["BTN_BG"]}; color: {INK}; cursor: pointer">{icon(ic, 22)}</button>')

    stats = "".join(f'''<div style="position: relative; display: flex; align-items: center; gap: 8px; height: 52px; padding: 0 14px; background: {t["TAG_BG"]}; border: 1px solid {t["TAG_BORDER"]}; border-radius: 3px; transform: rotate({r}deg); box-shadow: 0 2px 4px rgba(0,0,0,0.15)">
<span style="color: {t["TAG_ICON"]}">{icon(ic, 20)}</span><div style="display: flex; flex-direction: column"><span style="font: 700 20px/22px {SANS}; color: {INK}; white-space: nowrap">{v}</span><span style="font: 500 14px/16px {SANS}; color: {MUTED}; white-space: nowrap">{l}</span></div></div>'''
                    for (ic, v, l), r in zip(STATS, [-1, 0.8, -0.4, 1, -0.8, 0.5]))

    swatch = ""
    if club_swatch:
        swatch = "".join(f'<span style="width: 16px; height: 16px; border-radius: 3px; background: {c}; border: 1px solid rgba(0,0,0,0.25)"></span>' for c in club_swatch)
        swatch = f'<div aria-label="Club colours" style="display: flex; gap: 4px; margin-left: 4px">{swatch}</div>'

    top = f'''<header style="position: absolute; top: 24px; left: 32px; right: 32px; height: 84px; box-sizing: border-box; display: flex; align-items: center; gap: 14px; padding: 0 16px 0 20px; background: {t["PAPER"]}; border-radius: 3px; box-shadow: {SH}">
{tape("top: -12px; left: 40px", -4)}{tape("top: -12px; right: 60px", 3)}
{crest_svg("home", 44, t["CREST"])}
<div style="display: flex; flex-direction: column"><div style="display: flex; align-items: center; gap: 8px"><span style="font: 700 30px/32px {HAND}; color: {INK}; white-space: nowrap">Oakridge Rovers</span>{swatch}</div><span style="font: 400 16px/18px {HAND}; color: {MUTED}; white-space: nowrap">The changing rooms are technically a shed.</span></div>
<div style="flex: 1"></div>
<div style="display: flex; gap: 10px">{stats}</div>
<div style="width: 1px; height: 44px; background: {t["DIV"]}"></div>
{ibtn("settings", "Settings")}
{ibtn("quit", "Quit to menu")}
</header>'''

    goal = f'''<section style="position: absolute; top: 146px; left: 40px; width: 410px; box-sizing: border-box; padding: 28px 26px 24px; background: {t["NOTE"]}; border-radius: 2px; transform: rotate(-1.4deg); box-shadow: {SH}; display: flex; flex-direction: column; gap: 12px">
{tape("top: -14px; left: 156px", 2)}
<h2 style="margin: 0; font: 700 38px/40px {HAND}; color: {t["NOTE_INK"]}">Our Goal</h2>
<p style="margin: 0; font: 600 20px/26px {SANS}; color: {t["NOTE_INK"]}">Reach 100 paying supporters</p>
<div style="display: flex; justify-content: space-between"><span style="font: 500 16px/22px {SANS}; color: {t["NOTE_MUTED"]}">Paying supporters</span><span style="font: 700 18px/22px {SANS}; color: {t["NOTE_INK"]}">24 / 100</span></div>
<div style="height: 14px; border: 2px solid {t["NOTE_INK"]}; border-radius: 7px; background: {t["BAR_BG"]}; overflow: hidden"><div style="width: 24%; height: 100%; background: repeating-linear-gradient(-45deg, {t["HATCH1"]} 0 4px, {t["HATCH2"]} 4px 8px)"></div></div>
<span style="font: 400 19px/24px {HAND}; color: {t["NOTE_MUTED"]}">76 to go!! Ask your nan. And her mates. — Chairman</span>
<a href="#" style="align-self: flex-start; display: flex; align-items: center; gap: 8px; height: 44px; padding: 0 16px; border: 2px solid {t["NOTE_INK"]}; border-radius: 6px; text-decoration: none; color: {t["NOTE_INK"]}; background: {t["LINK_BG"]}; font: 600 16px/20px {SANS}">{icon("stadium", 20)}Build seats</a>
</section>'''

    lines = f"background-image: repeating-linear-gradient(to bottom, transparent 0 31px, {t['LINES']} 31px 32px); background-position: 0 56px"
    match = f'''<section style="position: absolute; top: 140px; right: 40px; width: 440px; box-sizing: border-box; padding: 26px 26px 24px; background-color: {t["CARD"]}; {lines}; border-radius: 3px; transform: rotate(0.9deg); box-shadow: {SH}; display: flex; flex-direction: column; gap: 16px; border-top: 6px solid {t["STRIPE"]}">
{pin("50%")}
<div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="margin: 0; font: 700 38px/40px {HAND}; color: {INK}">Next Match</h2><span style="font: 700 14px/18px {SANS}; color: {t["PEN"]}; text-transform: uppercase; letter-spacing: 0.08em">Friendly</span></div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: center">
<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{crest_svg("home", 64, t["CREST"])}<span style="font: 700 18px/22px {SANS}; color: {INK}">Oakridge Rovers</span></div>
<span style="text-align: center; font: 700 34px/34px {HAND}; color: {t["PEN"]}">vs</span>
<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{crest_svg("away", 64, INK)}<span style="font: 700 18px/22px {SANS}; color: {INK}">Riverside United</span></div></div>
<span style="font: 400 19px/24px {HAND}; color: {t["PEN"]}; text-align: center">Lifts: Gaz has 3 seats. Bring oranges.</span>
<button type="button" style="display: flex; align-items: center; justify-content: center; gap: 10px; height: 56px; border: none; border-radius: 8px; background: {t["PRIMARY"]}; color: {t["PRIMARY_FG"]}; font: 700 20px/24px {SANS}; box-shadow: 0 3px 0 {t["PRIMARY_SH"]}; cursor: pointer">{icon("play", 20, t["PRIMARY_FG"])}Play Match</button>
<div style="display: flex; align-items: center; gap: 8px; font: 600 16px/22px {SANS}; color: {t["OK"]}">{icon("check", 18)}All 11 players available.</div>
</section>'''

    nav = ""
    for ic, l in NAV:
        sel = l == "Club"
        st = (f"background: {t['SEL_BG']}; color: {t['SEL_FG']}; transform: translateY(-4px); box-shadow: 0 3px 6px rgba(0,0,0,0.2)"
              if sel else f"background: transparent; color: {INK}")
        cur = ' aria-current="page"' if sel else ""
        nav += f'<a href="#"{cur} style="display: flex; align-items: center; gap: 10px; height: 52px; padding: 0 18px; border-radius: 4px; text-decoration: none; font: 600 17px/20px {SANS}; white-space: nowrap; {st}">{icon(ic, 22)}<span>{l}</span></a>'
    strip = f'''<nav aria-label="Club" style="position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); width: 1340px; height: 72px; box-sizing: border-box; display: flex; align-items: center; gap: 16px; padding: 0 10px 0 22px; background: {t["PAPER"]}; border-radius: 3px; box-shadow: {SH}">
{tape("top: -14px; left: -20px", -8)}
<span style="color: {t["PIN"]}">{icon("news", 22)}</span>
<span style="flex: 1; min-width: 0; font: 700 20px/24px {HAND}; color: {INK}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{TICKER}</span>
<div style="width: 1px; height: 40px; background: {t["DIV"]}"></div>
<div style="display: flex; gap: 4px">{nav}</div></nav>'''
    return page(title, FONTS, top + goal + match + strip)


VARIANTS = [
    ("NB_Dark.dc.html", DARK, "Noticeboard · dark paper", None),
    ("NB_Evening.dc.html", EVENING, "Noticeboard · evening (dimmed paper)", None),
    ("NB_Club_RedWhite.dc.html", RED_WHITE, "Noticeboard · club colours red/white", ["#D0202E", "#FFFFFF"]),
    ("NB_Club_BlueYellow.dc.html", BLUE_YELLOW, "Noticeboard · club colours blue/yellow", ["#1F4AA8", "#F5C518"]),
]
if __name__ == "__main__":
    for fn, th, title, sw in VARIANTS:
        open(os.path.join(OUT, fn), "w").write(build(th, title, sw))
    print("ok")


def darkify(base, pen_text, crest):
    """Simple dark mode: white/cream surfaces -> dark, text on them inverted.
    Sticky note, tape, pins, primary button, selected tab stay as in light mode."""
    return dict(base,
        INK="#F1ECDF", MUTED="#B4B8B4", PAPER="#25292D", CARD="#2C3135", TAG_BG="#33383D", TAG_BORDER="#4A5056",
        DIV="#4A5056", BTN_BG="#33383D", BTN_BORDER="#5A6168", LINES="rgba(255,255,255,0.06)", OK="#7FD39A",
        SHADOW="0 8px 18px rgba(0,0,0,0.45), 0 1px 2px rgba(0,0,0,0.3)",
        PEN=pen_text, TAG_ICON=pen_text, CREST=crest)


DARK_RW = darkify(RED_WHITE, "#FF7A83", "#FF7A83")
DARK_BY = darkify(BLUE_YELLOW, "#8FAEF2", "#8FAEF2")
