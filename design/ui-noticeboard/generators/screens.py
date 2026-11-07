import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from nbkit import *
from lib import icon, HUB_BG, BUILD_BG

OUT = "/home/claude/canvas/project"
T = RED_WHITE


# ---------------------------------------------------------------- Hub, squad short (Next match disabled)
def hub_short(T=T):
    goal = f'''<section style="{note(T, 'top: 146px; left: 40px; width: 410px; padding: 28px 26px 24px; display: flex; flex-direction: column; gap: 12px')}">
{tape(T, "top: -14px; left: 156px", 2)}
{h2(T, "Our Goal", col=T["NOTE_INK"])}
<p style="margin: 0; font: 600 20px/26px {SANS}; color: {T["NOTE_INK"]}">Reach 100 paying supporters</p>
<div style="display: flex; justify-content: space-between"><span style="font: 500 16px/22px {SANS}; color: {T["NOTE_MUTED"]}">Paying supporters</span><span style="font: 700 18px/22px {SANS}; color: {T["NOTE_INK"]}">24 / 100</span></div>
{progress(T, 24)}
<span style="font: 400 19px/24px {HAND}; color: {T["NOTE_MUTED"]}">76 to go!! Ask your nan. And her mates. — Chairman</span>
<div>{link_btn(T, "Build seats", "stadium", True)}</div>
</section>'''
    match = f'''<section style="{card(T, 'top: 140px; right: 40px; width: 440px; padding: 26px 26px 24px; display: flex; flex-direction: column; gap: 16px', 0.9)}">
{pin(T)}
<div style="display: flex; justify-content: space-between; align-items: baseline">{h2(T, "Next Match")}{label(T, "Friendly")}</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: center">
<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{crest_svg("home", 64, T["CREST"])}<span style="font: 700 18px/22px {SANS}; color: {T["INK"]}">Oakridge Rovers</span></div>
<span style="text-align: center; font: 700 34px/34px {HAND}; color: {T["PEN"]}">vs</span>
<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{crest_svg("away", 64, T["INK"])}<span style="font: 700 18px/22px {SANS}; color: {T["INK"]}">Railway Tavern Athletic</span></div></div>
{primary(T, "Play Match", "play", disabled=True)}
<div style="display: flex; align-items: flex-start; gap: 10px; padding: 12px 14px; border-radius: 6px; border: 2px dashed {danger(T)}">
<span style="color: {danger(T)}; display: flex; padding-top: 1px">{icon("warn", 20)}</span>
<div style="display: flex; flex-direction: column; gap: 8px; flex: 1"><span style="font: 600 16px/22px {SANS}; color: {T["INK"]}">You need 11 players. You have 9.</span>
<span style="font: 400 18px/22px {HAND}; color: {T["MUTED"]}">The ref won't start with nine. We asked.</span>
<div>{link_btn(T, "Recruit 2 more", "recruit")}</div></div></div>
</section>'''
    return page("Hub · Next match disabled (squad 9/11)", topbar(T, squad="9 / 11") + goal + match + strip(T, "Club"))


# ---------------------------------------------------------------- Recruitment
CANDIDATES = [("Sunil Rao", "Regular at the pub", False), ("Mick O'Hara", "Neighbour across the road", True),
              ("Jamie Fenwick", "Says he had a trial at Stoke", False), ("Lee Barker", "Works at the chippy", False),
              ("Callum Reid", "Your cousin's mate", False), ("Ollie Grant", "Walks his dog past the pitch", False),
              ("Ray Whitlock", "Retired. Very keen.", False), ("Danny Cole", "Found our ball in his garden", False)]


def recruitment(T=T):
    rots = [-1.2, 0.8, -0.5, 1.1, 0.6, -0.9, 1.0, -0.6]
    cards = ""
    for (n, o, signed), r in zip(CANDIDATES, rots):
        if signed:
            action = f'''<div style="display: flex; align-items: center; justify-content: space-between">
<span style="display: flex; align-items: center; gap: 6px; font: 600 15px/20px {SANS}; color: {T["OK"]}">{icon("check", 18)}In the squad</span></div>
<span aria-hidden="true" style="position: absolute; right: 18px; top: 44px; padding: 2px 12px; border: 3px solid {T["PRIMARY"]}; border-radius: 6px; font: 700 26px/30px {HAND}; color: {T["PRIMARY"]}; transform: rotate(-12deg); opacity: 0.9">Signed!</span>'''
        else:
            action = f'''<div style="display: flex; align-items: center; justify-content: space-between; gap: 10px">
<span style="font: 500 14px/18px {SANS}; color: {T["MUTED"]}">Free</span>{primary(T, "Recruit", "plus", h=44, size=16, full=False)}</div>'''
        cards += f'''<article style="position: relative; box-sizing: border-box; padding: 22px 20px 18px; background: {T["CARD"]}; border-radius: 3px; transform: rotate({r}deg); box-shadow: {T["SHADOW"]}; display: flex; flex-direction: column; gap: 10px; min-height: 196px">
{pin(T)}
<div style="display: flex; align-items: center; gap: 12px"><span style="width: 44px; height: 44px; border-radius: 22px; border: 2px solid {T["INK"]}; display: flex; align-items: center; justify-content: center; color: {T["INK"]}; flex-shrink: 0">{icon("recruit", 22)}</span>
<span style="font: 700 20px/24px {SANS}; color: {T["INK"]}">{n}</span></div>
<span style="font: 400 20px/24px {HAND}; color: {T["PEN"]}; flex: 1">{o}</span>
{action}</article>'''
    side = f'''<section style="{note(T, 'top: 150px; left: 40px; width: 380px; padding: 28px 26px 24px; display: flex; flex-direction: column; gap: 12px', -1.2)}">
{tape(T, "top: -14px; left: 140px", -2)}
{h2(T, "Who can play for you", 36, T["NOTE_INK"])}
<p style="margin: 0; font: 500 16px/22px {SANS}; color: {T["NOTE_INK"]}">Recruiting is free. You need 11 players to play a match.</p>
<div style="display: flex; justify-content: space-between"><span style="font: 500 16px/22px {SANS}; color: {T["NOTE_MUTED"]}">Squad</span><span style="font: 700 18px/22px {SANS}; color: {T["NOTE_INK"]}">8 / 11</span></div>
{progress(T, 73)}
<span style="font: 400 19px/24px {HAND}; color: {T["NOTE_MUTED"]}">3 more. Someone always knows a lad.</span>
</section>'''
    grid = f'''<div style="position: absolute; top: 150px; left: 470px; right: 40px; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 28px 26px">{cards}</div>'''
    return page("Recruitment", topbar(T, squad="8 / 11") + side + grid + strip(T, "Recruitment"))


# ---------------------------------------------------------------- Squad
SQUAD = [("GK", "Dave Harper", "Regular at the pub"), ("LB", "Kev Mullins", "Neighbour across the road"),
         ("CB", "Steve Okafor", "Works at the builders' yard"), ("CB", "Paul Jennings", "Darts team captain"),
         ("RB", "Liam Walsh", "Your landlord's son"), ("CM", "Sam Pritchard", "Says he had a trial at Stoke"),
         ("CDM", "Gaz Doyle", "Ran a half-marathon. Once."), ("CM", "Ade Bello", "Delivers the post"),
         ("LW", "Ryan Moss", "Lives above the chippy"), ("ST", "Tom Price", "The barman's brother-in-law"),
         ("RW", "Josh Kerr", "Walks his dog past the pitch")]


def squad(T=T):
    rows = ""
    for i, (p, n, o) in enumerate(SQUAD):
        sel = n == "Tom Price"
        bg = f"background: rgba(208,32,46,0.10); box-shadow: inset 4px 0 0 {T['SEL_BG']};" if sel else ""
        rows += f'''<div style="display: grid; grid-template-columns: 40px 70px minmax(0, 1fr) minmax(0, 1.3fr) 110px; align-items: center; gap: 14px; height: 48px; padding: 0 16px; border-bottom: 1px solid {T["TAG_BORDER"]}; {bg}">
<span style="font: 600 15px/18px {SANS}; color: {T["MUTED"]}">{i + 1}</span>
<span style="justify-self: start; min-width: 48px; height: 28px; padding: 0 8px; border: 2px solid {T["INK"]}; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; font: 700 14px/16px {SANS}; color: {T["INK"]}; box-sizing: border-box">{p}</span>
<span style="font: 600 17px/20px {SANS}; color: {T["INK"]}">{n}</span>
<span style="font: 400 19px/22px {HAND}; color: {T["PEN"]}">{o}</span>
<span style="display: flex; align-items: center; gap: 6px; font: 600 15px/18px {SANS}; color: {T["OK"]}">{icon("check", 16)}Available</span></div>'''
    table = f'''<section style="{card(T, 'top: 140px; left: 500px; width: 920px; padding: 24px 24px 20px; display: flex; flex-direction: column; gap: 14px', 0.3, lines=False)}">
{pin(T, "30%")}{pin(T, "70%")}
<div style="display: flex; justify-content: space-between; align-items: baseline">{h2(T, "Squad")}<span style="font: 700 18px/22px {SANS}; color: {T["OK"]}">11 / 11 · ready to play</span></div>
<div role="table" style="border-top: 2px solid {T["INK"]}">
<div style="display: grid; grid-template-columns: 40px 70px minmax(0, 1fr) minmax(0, 1.3fr) 110px; gap: 14px; height: 36px; align-items: center; padding: 0 16px; border-bottom: 1px solid {T["TAG_BORDER"]}">{"".join(label(T, h, T["MUTED"]) for h in ["#", "Pos", "Name", "Where from", "Status"])}</div>
{rows}</div></section>'''
    # formation sketch (4-3-3) on a card
    pts = [("GK", 50, 90), ("LB", 14, 70), ("CB", 37, 74), ("CB", 63, 74), ("RB", 86, 70), ("CM", 28, 48),
           ("CDM", 50, 56), ("CM", 72, 48), ("LW", 16, 22), ("ST", 50, 15), ("RW", 84, 22)]
    dots = "".join(f'<span style="position: absolute; left: {x}%; top: {y}%; transform: translate(-50%, -50%); min-width: 40px; height: 40px; padding: 0 4px; box-sizing: border-box; border-radius: 20px; border: 2px solid {T["INK"]}; background: {T["SEL_BG"] if p == "ST" else T["CARD"]}; color: {T["SEL_FG"] if p == "ST" else T["INK"]}; display: flex; align-items: center; justify-content: center; font: 700 13px/16px {SANS}">{p}</span>' for p, x, y in pts)
    pitch = f'''<div style="position: relative; height: 470px; border: 2px solid {T["PEN"]}; border-radius: 4px">
<span style="position: absolute; left: 0; right: 0; top: 50%; border-top: 2px solid {T["PEN"]}; opacity: 0.6"></span>
<span style="position: absolute; left: 50%; top: 50%; width: 90px; height: 90px; transform: translate(-50%, -50%); border: 2px solid {T["PEN"]}; border-radius: 50%; opacity: 0.6"></span>
<span style="position: absolute; left: 25%; right: 25%; bottom: 0; height: 70px; border: 2px solid {T["PEN"]}; border-bottom: none; opacity: 0.6"></span>
<span style="position: absolute; left: 25%; right: 25%; top: 0; height: 70px; border: 2px solid {T["PEN"]}; border-top: none; opacity: 0.6"></span>
{dots}</div>'''
    form = f'''<section style="{card(T, 'top: 150px; left: 40px; width: 420px; padding: 24px 22px 22px; display: flex; flex-direction: column; gap: 14px', -0.8, stripe=False, lines=False)}">
{tape(T, "top: -14px; left: 160px", 3)}
<div style="display: flex; justify-content: space-between; align-items: baseline">{h2(T, "Formation", 34)}{label(T, "4-3-3")}</div>
{pitch}
<span style="font: 400 19px/24px {HAND}; color: {T["MUTED"]}">Drawn by the gaffer on a beer mat. Copied out neatly.</span></section>'''
    tip = f'''<section style="{note(T, 'top: 170px; right: 44px; width: 400px; padding: 26px 24px 22px; display: flex; flex-direction: column; gap: 10px', 1.6)}">
{tape(T, "top: -14px; left: 150px", -3)}
{h2(T, "Tom Price", 32, T["NOTE_INK"])}
<span style="font: 700 14px/18px {SANS}; color: {T["NOTE_MUTED"]}; text-transform: uppercase; letter-spacing: 0.08em">ST · Striker</span>
<p style="margin: 0; font: 500 16px/22px {SANS}; color: {T["NOTE_INK"]}">Stats, positions and personality come later, with the player detail screen.</p>
<span style="font: 400 19px/24px {HAND}; color: {T["NOTE_MUTED"]}">Scores. Celebrates like he's won the league.</span></section>'''
    return page("Squad", topbar(T) + form + table + tip + strip(T, "Squad"))


# ---------------------------------------------------------------- Post-match
def postmatch(T=T, title="Post-match summary"):
    D = danger(T)

    def row(lab, val, col=None, bold=False):
        return f'<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 12px; padding: 6px 0; border-bottom: 1px dashed {T["TAG_BORDER"]}"><span style="font: 500 16px/22px {SANS}; color: {T["MUTED"]}">{lab}</span><span style="font: {700 if bold else 600} {20 if bold else 17}px/24px {SANS}; color: {col or T["INK"]}; white-space: nowrap">{val}</span></div>'

    def col(head, ic, body):
        return f'<div style="display: flex; flex-direction: column; gap: 6px"><div style="display: flex; align-items: center; gap: 8px; color: {T["PEN"]}">{icon(ic, 20)}{label(T, head)}</div>{body}</div>'

    att = col("Attendance", "fans", row("Seated (paying)", "24") + row("Standing (free)", "6") + row("Total", "30", bold=True)
              + f'<div aria-hidden="true" style="display: flex; height: 12px; border: 2px solid {T["INK"]}; border-radius: 6px; overflow: hidden; margin-top: 6px"><span style="width: 80%; background: {T["PRIMARY"]}"></span><span style="width: 20%; background: {T["TAG_BG"]}"></span></div>'
              + f'<span style="font: 500 14px/18px {SANS}; color: {T["MUTED"]}">Every seat was taken.</span>')
    money = col("Money", "cash", row("Ticket income (24 × £2)", "+£48", T["OK"]) + row("Cash before", "£34") + row("Cash now", "£82", bold=True))
    fans = col("Fans", "approval", row("Fans", f'30 → 34 <span style="color: {T["OK"]}">+4</span>')
               + row("Fan approval", f'58% → 61% <span style="color: {T["OK"]}">+3</span>', bold=True)
               + row("· Result (win)", "+4", T["OK"]) + row("· Entertainment (3 goals)", "+1", T["OK"]) + row("· Seating (only 24 seats)", "−2", D))
    report = f'''<section style="{card(T, 'top: 132px; left: 50%; margin-left: -560px; width: 1120px; padding: 30px 36px 30px; display: flex; flex-direction: column; gap: 22px', 0.4)}">
{pin(T, "20%")}{pin(T, "80%")}
<div style="display: flex; justify-content: space-between; align-items: baseline">{h2(T, "Full time", 44)}{label(T, "Friendly")}</div>
<div style="display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center; gap: 28px">
<div style="display: flex; align-items: center; justify-content: flex-end; gap: 16px"><span style="font: 700 24px/28px {SANS}; color: {T["INK"]}; text-align: right">Oakridge Rovers</span>{crest_svg("home", 60, T["CREST"])}</div>
<span style="font: 700 64px/64px {SANS}; color: {T["INK"]}; letter-spacing: 0.04em">2 – 1</span>
<div style="display: flex; align-items: center; gap: 16px">{crest_svg("away", 60, T["INK"])}<span style="font: 700 24px/28px {SANS}; color: {T["INK"]}">Riverside United</span></div></div>
<div style="height: 2px; background: {T["INK"]}"></div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 40px">{att}{money}{fans}</div>
<div style="display: flex; justify-content: flex-end; gap: 12px; padding-top: 6px">{primary(T, "Back to the club", "club", full=False)}</div>
</section>'''
    motm = f'''<aside style="{note(T, 'top: 560px; left: 50px; width: 320px; padding: 24px 22px 20px; display: flex; flex-direction: column; gap: 6px', -3)}">
{tape(T, "top: -14px; left: 116px", 4)}
{label(T, "Man of the match", T["NOTE_MUTED"])}
<span style="font: 700 28px/32px {HAND}; color: {T["NOTE_INK"]}">Tom Price</span>
<span style="font: 400 19px/24px {HAND}; color: {T["NOTE_MUTED"]}">Honourable mention: Dave's van, for getting us here.</span></aside>'''
    scrim = '<div aria-hidden="true" style="position: absolute; inset: 0; background: rgba(0,0,0,0.35)"></div>'
    return page(title, scrim + report + motm)


# ---------------------------------------------------------------- Settings (modal over the hub)
def settings(T=T):
    scrim = '<div aria-hidden="true" style="position: absolute; inset: 0; background: rgba(0,0,0,0.45); z-index: 6"></div>'
    stepper = f'''<div style="display: flex; align-items: center; gap: 10px">{ibtn(T, "minus", "Shorter")}
<span style="min-width: 150px; text-align: center; font: 700 18px/22px {SANS}; color: {T["INK"]}">3 min per half</span>{ibtn(T, "plus", "Longer")}</div>'''
    box = f'''<section role="dialog" aria-label="Settings" style="{card(T, 'top: 120px; left: 50%; margin-left: -380px; width: 760px; padding: 28px 34px 28px; display: flex; flex-direction: column; gap: 20px; z-index: 7', 0, lines=False)}">
{pin(T, "50%")}
<div style="display: flex; justify-content: space-between; align-items: center">{h2(T, "Settings", 42)}{ibtn(T, "close", "Close settings")}</div>
{label(T, "Sound")}
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px">{slider(T, "Music", 70, "%")}{slider(T, "Effects", 80, "%")}{slider(T, "Crowd", 100, "%")}</div>
<div style="height: 1px; background: {T["TAG_BORDER"]}"></div>
{label(T, "Match")}
<div style="display: flex; justify-content: space-between; align-items: center"><span style="font: 600 16px/20px {SANS}; color: {T["INK"]}">Match length</span>{stepper}</div>
<div style="height: 1px; background: {T["TAG_BORDER"]}"></div>
{label(T, "Camera & look")}
{slider(T, "Camera speed", 50, "%")}
<div style="display: flex; justify-content: space-between; align-items: center; gap: 24px"><span style="font: 600 16px/20px {SANS}; color: {T["INK"]}">Appearance</span><div style="width: 320px">{segmented(T, ["Light", "Dark"], "Light")}</div></div>
<div style="display: flex; justify-content: flex-end">{primary(T, "Done", "check", full=False)}</div>
</section>
<aside style="{note(T, 'top: 640px; left: 1360px; width: 300px; padding: 24px 20px 20px; z-index: 8', 3)}">{tape(T, "top: -14px; left: 100px", -5)}
<span style="font: 400 20px/26px {HAND}; color: {T["NOTE_INK"]}">Turning the crowd down won't make them any nicer.</span></aside>'''
    return page("Settings", topbar(T) + strip(T, "Club") + scrim + box)


# ---------------------------------------------------------------- Main menu
def mainmenu(T=T):
    title = f'''<div style="{paper(T, 'top: 150px; left: 50%; margin-left: -420px; width: 840px; padding: 34px 40px 30px; text-align: center; transform: rotate(-0.8deg)')}">
{tape(T, "top: -14px; left: 80px", -6, 120)}{tape(T, "top: -14px; right: 80px", 5, 120)}
<h1 style="margin: 0; font: 700 104px/104px {HAND}; color: {T["INK"]}">Sunday League</h1>
<p style="margin: 6px 0 0; font: 400 26px/32px {HAND}; color: {T["PEN"]}">From a field and some chairs to the very top.</p></div>'''
    menu = f'''<nav aria-label="Main menu" style="{card(T, 'top: 430px; left: 50%; margin-left: -280px; width: 560px; padding: 30px 30px 28px; display: flex; flex-direction: column; gap: 14px', 0.6, lines=False)}">
{pin(T, "50%")}
<a href="#" style="display: flex; align-items: center; gap: 14px; padding: 12px 20px; border-radius: 8px; background: {T["PRIMARY"]}; color: {T["PRIMARY_FG"]}; text-decoration: none; box-shadow: 0 3px 0 {T["PRIMARY_SH"]}">
{icon("play", 22)}<div style="display: flex; flex-direction: column"><span style="font: 700 22px/26px {SANS}">Continue</span><span style="font: 500 15px/20px {SANS}; opacity: 0.9">Oakridge Rovers · W4 D1 L3 · 24 seats</span></div></a>
<a href="#" style="display: flex; align-items: center; gap: 14px; height: 56px; padding: 0 20px; border: 2px solid {T["INK"]}; border-radius: 8px; color: {T["INK"]}; text-decoration: none; font: 600 19px/24px {SANS}">{icon("plus", 22)}Start a new club</a>
<a href="#" style="display: flex; align-items: center; gap: 14px; height: 56px; padding: 0 20px; border: 2px solid {T["INK"]}; border-radius: 8px; color: {T["INK"]}; text-decoration: none; font: 600 19px/24px {SANS}">{icon("settings", 22)}Settings</a>
<a href="#" style="display: flex; align-items: center; gap: 14px; height: 56px; padding: 0 20px; border: 2px solid transparent; border-radius: 8px; color: {T["MUTED"]}; text-decoration: none; font: 600 19px/24px {SANS}">{icon("quit", 22)}Quit</a>
</nav>'''
    side = f'''<aside style="{note(T, 'top: 470px; left: 1400px; width: 320px; padding: 26px 22px 22px; display: flex; flex-direction: column; gap: 6px', 2.5)}">{tape(T, "top: -14px; left: 110px", -4)}
{label(T, "Club news", T["NOTE_MUTED"])}
<span style="font: 400 21px/26px {HAND}; color: {T["NOTE_INK"]}">The kettle's fixed. Training resumes Weds 7pm.</span></aside>
<span style="position: absolute; left: 32px; bottom: 24px; padding: 6px 10px; border-radius: 3px; background: {T["PAPER"]}; font: 500 14px/18px {SANS}; color: {T["MUTED"]}">v0.1</span>'''
    return page("Main menu", title + menu + side)


# ---------------------------------------------------------------- In-match HUD
def hud(T=T):
    score = f'''<div style="{paper(T, 'top: 24px; left: 32px; height: 64px; display: flex; align-items: center; gap: 14px; padding: 0 18px')}">
{crest_svg("home", 32, T["CREST"])}<span style="font: 700 22px/26px {SANS}; color: {T["INK"]}; letter-spacing: 0.04em">OAK</span>
<span style="padding: 2px 12px; border-radius: 4px; background: {T["INK"]}; color: {T["PAPER"]}; font: 700 26px/34px {SANS}">1 – 0</span>
<span style="font: 700 22px/26px {SANS}; color: {T["INK"]}; letter-spacing: 0.04em">RIV</span>{crest_svg("away", 32, T["INK"])}
<div style="width: 1px; height: 36px; background: {T["DIV"]}"></div>
<span style="font: 600 16px/20px {SANS}; color: {T["MUTED"]}">2nd half</span><span style="font: 700 22px/26px {SANS}; color: {T["INK"]}; font-variant-numeric: tabular-nums">2:41</span></div>'''
    goal = f'''<div role="status" style="{note(T, 'top: 150px; left: 50%; margin-left: -190px; width: 380px; padding: 18px 24px 16px; text-align: center', -4)}">{tape(T, "top: -14px; left: 142px", 3)}
<span style="display: block; font: 700 88px/88px {HAND}; color: {T["PRIMARY"]}">GOAL!</span>
<span style="font: 600 17px/22px {SANS}; color: {T["NOTE_INK"]}">Tom Price · 2:41</span></div>'''
    nametag = f'''<div style="position: absolute; left: 900px; top: 560px; display: flex; flex-direction: column; align-items: center">
<span style="padding: 4px 10px; border-radius: 3px; background: {T["PAPER"]}; border: 2px solid {T["SEL_BG"]}; font: 700 15px/18px {SANS}; color: {T["INK"]}; box-shadow: 0 2px 4px rgba(0,0,0,0.3)">Tom Price</span>
<span style="width: 0; height: 0; border-left: 8px solid transparent; border-right: 8px solid transparent; border-top: 9px solid {T["SEL_BG"]}"></span>
<span aria-hidden="true" style="margin-top: 26px; width: 46px; height: 14px; border-radius: 50%; border: 3px solid {T["SEL_BG"]}"></span></div>'''
    def arrow(side, y, name):
        rot = 180 if side == "left" else 0
        pos = "left: 16px" if side == "left" else "right: 16px"
        return (f'<div style="position: absolute; {pos}; top: {y}px; display: flex; align-items: center; gap: 6px; flex-direction: {"row" if side == "left" else "row-reverse"}; '
                f'padding: 4px 8px; border-radius: 3px; background: {T["PAPER"]}; box-shadow: 0 2px 4px rgba(0,0,0,0.3)">'
                f'<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" style="transform: rotate({rot}deg)"><path d="M4 4l16 8-16 8z" fill="{T["PRIMARY"]}"/></svg>'
                f'<span style="font: 700 14px/18px {SANS}; color: {T["INK"]}">{name}</span></div>')
    arrows = arrow("left", 470, "Kev") + arrow("right", 640, "Josh")
    power = f'''<div style="{paper(T, 'bottom: 96px; left: 50%; margin-left: -210px; width: 420px; padding: 12px 18px; display: flex; flex-direction: column; gap: 8px')}">
<div style="display: flex; justify-content: space-between"><span style="font: 700 14px/18px {SANS}; color: {T["MUTED"]}; text-transform: uppercase; letter-spacing: 0.08em">Shot power</span><span style="font: 700 16px/18px {SANS}; color: {T["INK"]}">72%</span></div>
{progress(T, 72, on_note=False)}</div>'''
    dots_us = [(30, 50), (45, 30), (45, 70), (60, 40), (62, 62), (70, 50), (52, 52), (38, 48), (78, 30), (80, 66), (10, 50)]
    dots_them = [(90, 50), (75, 40), (75, 60), (68, 25), (68, 75), (58, 50), (55, 30), (55, 70), (40, 40), (40, 60), (48, 50)]
    md = "".join(f'<span style="position: absolute; left: {x}%; top: {y}%; width: 10px; height: 10px; margin: -5px; border-radius: 5px; background: {T["PRIMARY"]}"></span>' for x, y in dots_us)
    md += "".join(f'<span style="position: absolute; left: {x}%; top: {y}%; width: 10px; height: 10px; margin: -5px; border-radius: 5px; background: {T["INK"]}"></span>' for x, y in dots_them)
    md += f'<span style="position: absolute; left: 66%; top: 46%; width: 10px; height: 10px; margin: -5px; border-radius: 5px; background: #FFFFFF; border: 2px solid {T["INK"]}"></span>'
    minimap = f'''<div aria-label="Minimap" style="{card(T, 'right: 32px; bottom: 24px; width: 320px; height: 210px; padding: 14px', 0, stripe=False, lines=False)}">
<div style="position: relative; width: 100%; height: 100%; border: 2px solid {T["PEN"]}; border-radius: 3px; box-sizing: border-box">
<span style="position: absolute; top: 0; bottom: 0; left: 50%; border-left: 2px solid {T["PEN"]}; opacity: 0.5"></span>
<span style="position: absolute; left: 50%; top: 50%; width: 44px; height: 44px; margin: -22px; border: 2px solid {T["PEN"]}; border-radius: 50%; opacity: 0.5"></span>
<span style="position: absolute; left: 0; top: 30%; bottom: 30%; width: 36px; border: 2px solid {T["PEN"]}; border-left: none; opacity: 0.5"></span>
<span style="position: absolute; right: 0; top: 30%; bottom: 30%; width: 36px; border: 2px solid {T["PEN"]}; border-right: none; opacity: 0.5"></span>
{md}</div></div>'''
    hint = f'''<div style="{paper(T, 'left: 32px; bottom: 24px; max-width: 760px; padding: 10px 14px')}"><span style="font: 500 14px/20px {SANS}; color: {T["INK"]}">WASD move (sprint by default) · Shift walk · LMB pass · hold RMB shoot · Space tackle · Q switch · R restart · Esc quit</span></div>'''
    return page("In-match HUD", score + goal + nametag + arrows + power + minimap + hint, alt="The pitch during a match")


# ---------------------------------------------------------------- Build mode
def shopcard(T, name, price, adds, ic, note_txt, flavour, state="default"):
    stripe = f"border-top: 6px solid {T['STRIPE']};" if state == "selected" else f"border-top: 6px solid transparent;"
    lift = "transform: translateY(-3px); box-shadow: 0 10px 18px rgba(0,0,0,0.3);" if state in ("hover", "selected") else "box-shadow: 0 2px 5px rgba(0,0,0,0.18);"
    pc = danger(T) if state == "disabled" else T["INK"]
    tc = T["MUTED"] if state == "disabled" else T["INK"]
    foot = (f'<span style="display: flex; align-items: center; gap: 6px; font: 600 14px/18px {SANS}; color: {danger(T)}">{icon("lock", 16)}£6 short</span>'
            if state == "disabled" else f'<span style="font: 500 14px/18px {SANS}; color: {T["MUTED"]}">{note_txt}</span>')
    pn = pin(T, "50%") if state == "selected" else ""
    return f'''<div style="position: relative; box-sizing: border-box; padding: 14px 16px 14px; background: {T["CARD"]}; border-radius: 3px; border: 1px solid {T["TAG_BORDER"]}; {stripe} {lift} display: flex; flex-direction: column; gap: 8px">{pn}
<div style="display: flex; align-items: center; gap: 10px; color: {tc}">{icon(ic, 26)}<span style="font: 700 19px/22px {SANS}">{name}</span></div>
<span style="font: 400 18px/22px {HAND}; color: {T["PEN"] if state != "disabled" else T["MUTED"]}">{flavour}</span>
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font: 700 20px/22px {SANS}; color: {pc}">{price}</span><span style="font: 600 15px/18px {SANS}; color: {T["OK"] if state != "disabled" else T["MUTED"]}">{adds}</span></div>
{foot}</div>'''


def catalogue(T, active, cards, hint):
    tabs = ""
    for n, ic in [("Seating", "seat"), ("Stands", "stadium"), ("Buildings", "shop"), ("Demolish", "demolish")]:
        sel = n == active
        st = (f"background: {T['SEL_BG']}; color: {T['SEL_FG']}; transform: translateY(-3px); box-shadow: 0 3px 6px rgba(0,0,0,0.2)" if sel
              else f"background: transparent; color: {T['INK']}")
        tabs += f'<a href="#" style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; height: 62px; border-radius: 4px; text-decoration: none; font: 600 15px/18px {SANS}; {st}">{icon(ic, 22)}<span>{n}</span></a>'
    return f'''<aside aria-label="Build catalogue" style="{card(T, 'top: 140px; left: 40px; width: 444px; padding: 22px 18px 18px; display: flex; flex-direction: column; gap: 14px', -0.5, lines=False)}">
{pin(T, "50%")}
<div style="display: flex; justify-content: space-between; align-items: baseline">{h2(T, "Build", 34)}<span style="font: 500 14px/18px {SANS}; color: {T["MUTED"]}">Esc to stop building</span></div>
<div role="tablist" style="display: flex; gap: 4px">{tabs}</div>
<div style="height: 2px; background: {T["INK"]}"></div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px">{cards}</div>
<div style="display: flex; gap: 8px; font: 500 15px/20px {SANS}; color: {T["MUTED"]}"><span style="color: {T["PEN"]}; display: flex">{icon("info", 18)}</span><span>{hint}</span></div></aside>'''


def camera_tag(T):
    return f'''<div style="{paper(T, 'right: 32px; bottom: 120px; height: 60px; display: flex; align-items: center; gap: 10px; padding: 0 8px 0 16px; z-index: 5')}">
<span style="font: 500 15px/20px {SANS}; color: {T["MUTED"]}; white-space: nowrap">Rotate: Q / E or hold right mouse</span>
<button type="button" aria-label="Rotate left" style="width: 44px; height: 44px; padding: 0; display: flex; align-items: center; justify-content: center; border: 1px solid {T["BTN_BORDER"]}; border-radius: 6px; background: {T["BTN_BG"]}; color: {T["INK"]}; cursor: pointer; transform: scaleX(-1)">{icon("rotate", 22)}</button>
{ibtn(T, "rotate", "Rotate right")}</div>'''


def bline(T, lab, val, col=None, big=False):
    return f'<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 12px"><span style="font: 500 16px/22px {SANS}; color: {T["MUTED"]}">{lab}</span><span style="font: {700 if big else 600} {22 if big else 17}px/24px {SANS}; color: {col or T["INK"]}; white-space: nowrap">{val}</span></div>'


def badd(T, ic, text, col=None):
    return f'<div style="display: flex; align-items: center; gap: 10px; font: 600 16px/22px {SANS}; color: {col or T["OK"]}">{icon(ic, 20)}<span>{text}</span></div>'


def build_actions(T):
    return f'''<div style="display: flex; gap: 10px">{link_btn(T, "Cancel", "close", h=56)}{primary(T, "Build it", "check", extra="flex: 1;", full=False)}</div>
<span style="font: 500 14px/18px {SANS}; color: {T["MUTED"]}">Left click or Enter to build · right click or Esc to cancel</span>'''


def tag3d(T, x, y, text, col, ic):
    return f'<div style="position: absolute; left: {x}px; top: {y}px; display: flex; align-items: center; gap: 8px; height: 36px; padding: 0 12px; border-radius: 3px; background: {T["PAPER"]}; border: 2px solid {col}; color: {col}; font: 700 15px/18px {SANS}; white-space: nowrap; box-shadow: 0 3px 8px rgba(0,0,0,0.3)">{icon(ic, 18)}<span style="color: {T["INK"]}">{text}</span></div>'


def build_preview(T=T):
    cards = (shopcard(T, "Chair", "£12", "+1 seat", "seat", "Instant · stack up to 4", "Folding. Mostly.", "selected")
             + shopcard(T, "Bench", "£40", "+4 seats", "seat", "Instant", "Seats four. Five if you're friendly."))
    ghost = f'''<div aria-hidden="true" style="position: absolute; left: 1490px; top: 548px; width: 330px; height: 92px; border: 3px dashed {T["PRIMARY"]}; border-radius: 6px; background: rgba(255,255,255,0.18)"></div>
<div aria-hidden="true" style="position: absolute; left: 1630px; top: 560px; width: 56px; height: 72px; border-radius: 4px; background: rgba(255,255,255,0.6); border: 3px solid {T["PRIMARY"]}"></div>
{tag3d(T, 1500, 492, "Spot 3 of 5 · £12", T["PRIMARY"], "seat")}'''
    prev = f'''<aside aria-label="Preview" style="{card(T, 'top: 236px; left: 1060px; width: 400px; padding: 24px 24px 20px; display: flex; flex-direction: column; gap: 14px', 0.6, lines=False)}">{pin(T)}
<div>{h2(T, "Chair", 34)}<span style="display: block; margin-top: 4px; font: 500 16px/20px {SANS}; color: {T["MUTED"]}">North side · Section 4 · Spot 3</span></div>
<div style="display: flex; flex-direction: column; gap: 6px">{label(T, "Cost", T["MUTED"])}{bline(T, "Price", "£12")}{bline(T, "Refund", "—", T["MUTED"])}<div style="height: 2px; background: {T["INK"]}; margin: 4px 0"></div>{bline(T, "You pay", "£12", T["INK"], True)}{bline(T, "Cash after", "£22")}</div>
<div style="display: flex; flex-direction: column; gap: 8px">{label(T, "Adds", T["MUTED"])}{badd(T, "seat", "+1 seat (24 → 25)")}{badd(T, "cash", "+£2 per home match when filled")}{badd(T, "clock", "Ready instantly", T["INK"])}</div>
<span style="font: 400 19px/24px {HAND}; color: {T["PEN"]}">Stack up to 4 per spot. They don't match. Nobody minds.</span>
{build_actions(T)}</aside>'''
    body = (ghost + topbar(T) + catalogue(T, "Seating", cards, "Pick an item, then hover a free spot in the ground. It shows up there before you pay.")
            + prev + camera_tag(T) + strip(T, "Stadium"))
    return page("Build mode · live preview", body, bg=BUILD_BG, alt="Close-up of the ground: bleachers, a bench, chairs and the ad boards")


def build_replace(T=T):
    cards = (shopcard(T, "Bleachers", "£1,800", "+60 seats", "stadium", "1 week · per section", "Three rows of scaffold-chic.", "selected")
             + shopcard(T, "+2 rows", "£1,200", "+40 seats", "plus", "½ week · on bleachers", "Higher. Wobblier. Prouder."))
    D = danger(T)
    ghost = f'''<div aria-hidden="true" style="position: absolute; left: 1450px; top: 500px; width: 470px; height: 150px; border: 3px solid {D}; border-right: none; border-radius: 6px 0 0 6px; background: rgba(184,50,42,0.25)"></div>
<svg aria-hidden="true" width="520" height="300" viewBox="0 0 520 300" style="position: absolute; left: 1400px; top: 352px; transform: scaleX(-1)">
<path d="M0 290 L500 290 L500 250 L470 250 L470 180 L440 180 L440 110 L410 110 L410 40 L0 40" fill="rgba(255,255,255,0.22)" stroke="{T["PRIMARY"]}" stroke-width="3" stroke-dasharray="10 7" stroke-linejoin="round"/>
<path d="M0 110 L410 110 M0 180 L440 180 M0 250 L470 250" stroke="{T["PRIMARY"]}" stroke-width="2" stroke-dasharray="6 6" opacity=".7"/></svg>
{tag3d(T, 1560, 300, "Bleachers · 60 seats", T["PRIMARY"], "stadium")}
{tag3d(T, 1500, 664, "Removed: 5 benches · £150 back", D, "demolish")}'''
    prev = f'''<aside aria-label="Preview" style="{card(T, 'top: 132px; left: 944px; width: 432px; padding: 24px 24px 20px; display: flex; flex-direction: column; gap: 12px', -0.4, lines=False)}">{pin(T)}
<div>{h2(T, "Bleachers", 34)}<span style="display: block; margin-top: 4px; font: 500 16px/20px {SANS}; color: {T["MUTED"]}">North side · Section 1 · replaces what's there</span></div>
<div style="display: flex; flex-direction: column; gap: 6px; padding: 10px 12px; border: 2px dashed {D}; border-radius: 6px">
<div style="display: flex; align-items: center; gap: 8px; font: 700 16px/20px {SANS}; color: {D}">{icon("demolish", 18)}Removes</div>
{bline(T, "5 benches · 20 seats", "+£150 back", T["OK"])}
<span style="font: 500 14px/18px {SANS}; color: {T["MUTED"]}">Worth 75% when new, down to 10% after ~3 seasons. These are new.</span></div>
<div style="display: flex; flex-direction: column; gap: 6px">{label(T, "Cost", T["MUTED"])}{bline(T, "Price", "£1,800")}{bline(T, "Refund", "−£150", T["OK"])}<div style="height: 2px; background: {T["INK"]}; margin: 4px 0"></div>{bline(T, "You pay", "£1,650", T["INK"], True)}{bline(T, "Cash after", "£490")}</div>
<div style="display: flex; flex-direction: column; gap: 8px">{label(T, "Adds", T["MUTED"])}{badd(T, "seat", "+40 seats net (60 new, 20 removed)")}{badd(T, "cash", "Up to +£80 per home match")}{badd(T, "clock", "2 weeks: 1 demolition + 1 build", "#9A6A00")}
<span style="font: 500 14px/18px {SANS}; color: {T["MUTED"]}; padding-left: 30px">Section closed meanwhile. 20 seats out of use.</span></div>
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px">
<div style="display: flex; align-items: center; gap: 12px"><span role="switch" aria-checked="false" aria-disabled="true" style="position: relative; width: 52px; height: 30px; border-radius: 15px; background: {T["TAG_BG"]}; border: 2px solid {T["TAG_BORDER"]}; box-sizing: border-box; display: block"><span style="position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 10px; background: {T["TAG_BORDER"]}"></span></span><span style="font: 600 16px/20px {SANS}; color: {T["MUTED"]}">Rush build</span></div>
<span style="font: 500 14px/18px {SANS}; color: {D}; text-align: right">£2,550 · 1¾ weeks<br>£410 short</span></div>
{build_actions(T)}</aside>'''
    body = (ghost + topbar(T, cash="£2,140", seats="84") + catalogue(T, "Stands", cards, "Stands replace whatever is on the section. You always see what goes and what you get back.")
            + prev + camera_tag(T) + strip(T, "Stadium"))
    return page("Build mode · replace", body, bg=BUILD_BG, bg_flip=True, alt="Close-up of the ground (mirrored): benches with fans, bleachers and ad boards")


SCREENS = [
    ("S_Hub_SquadShort.dc.html", hub_short, "Hub · Next match disabled (9/11)"),
    ("S_Recruitment.dc.html", recruitment, "Recruitment"),
    ("S_Squad.dc.html", squad, "Squad"),
    ("S_PostMatch.dc.html", postmatch, "Post-match summary"),
    ("S_PostMatch_Dark.dc.html", lambda: postmatch(DARK_RW, "Post-match summary · dark"), "Post-match summary · dark check"),
    ("S_Settings.dc.html", settings, "Settings"),
    ("S_MainMenu.dc.html", mainmenu, "Main menu"),
    ("S_HUD.dc.html", hud, "In-match HUD"),
    ("S_Build_Preview.dc.html", build_preview, "Build mode · live preview"),
    ("S_Build_Replace.dc.html", build_replace, "Build mode · replace"),
]

if __name__ == "__main__":
    for fn, f, _ in SCREENS:
        open(os.path.join(OUT, fn), "w").write(f())
    print("ok")


# ---------------------------------------------------------------- Component sheet (noticeboard)
def components(T=T):
    def sec(title, body, span=1, sub=""):
        sb = f'<span style="font: 500 15px/20px {SANS}; color: {T["MUTED"]}">{sub}</span>' if sub else ""
        return f'''<section style="position: relative; grid-column: span {span}; box-sizing: border-box; padding: 26px 26px 26px; background: {T["CARD"]}; border-radius: 3px; box-shadow: {T["SHADOW"]}; display: flex; flex-direction: column; gap: 16px">{pin(T, "40px")}
<div style="display: flex; flex-direction: column; gap: 2px">{h2(T, title, 30)}{sb}</div>{body}</section>'''

    def st(lab, el):
        return f'<div style="display: flex; flex-direction: column; gap: 8px; align-items: flex-start">{label(T, lab, T["MUTED"])}{el}</div>'

    def row(*els, gap=18):
        return f'<div style="display: flex; flex-wrap: wrap; gap: {gap}px; align-items: flex-start">' + "".join(els) + "</div>"

    def sw(name, hexv, role, border=True):
        return f'<div style="display: flex; flex-direction: column; gap: 6px"><div style="height: 52px; border-radius: 3px; background: {hexv}; border: 1px solid rgba(0,0,0,0.2)"></div><span style="font: 700 15px/18px {SANS}; color: {T["INK"]}">{name}</span><span style="font: 600 14px/16px {SANS}; color: {T["PEN"]}">{hexv}</span><span style="font: 500 14px/16px {SANS}; color: {T["MUTED"]}">{role}</span></div>'

    def swgrid(items):
        return '<div style="display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 14px">' + "".join(sw(*i) for i in items) + "</div>"

    colours = sec("Colour", f'''{label(T, "Light (default)", T["MUTED"])}
{swgrid([("ink", "#24313A", "text on paper"), ("muted", "#5E6A72", "labels"), ("paper", "#F3EFE6", "strips"), ("card", "#FBF8F1", "index cards"), ("tag", "#FFFFFF", "stat tags"), ("tag_border", "#D9D3C3", "borders")])}
{label(T, "Dark (option)", T["MUTED"])}
{swgrid([("ink", "#F1ECDF", "text"), ("muted", "#B4B8B4", "labels"), ("paper", "#25292D", "strips"), ("card", "#2C3135", "index cards"), ("tag", "#33383D", "stat tags"), ("tag_border", "#4A5056", "borders")])}
{label(T, "Fixed + club (red / white shown)", T["MUTED"])}
{swgrid([("note", "#FFE58A", "sticky note, both modes"), ("primary", "#D0202E", "button, pins, hatch"), ("highlight", "#D0202E", "tape, tab, stripe"), ("pen light", "#C21B2A", "text accents"), ("pen dark", "#FF7A83", "text accents (dark)"), ("success", "#1F7A3E", "gains, ready")])}''', 3,
                  "Paper stays paper; the club colour only touches the accents. Blue/yellow example: tape, tab and stripe turn yellow, button and pins blue.")

    types = [("hand_heading 38/40 · 700", HAND, 700, 38, "Our Goal"), ("hand_note 19/24 · 400", HAND, 400, 19, "76 to go!! Ask your nan."),
             ("lead 20/26 · 600", SANS, 600, 20, "Reach 100 paying supporters"), ("stat_value 20/22 · 700", SANS, 700, 20, "£1,650"),
             ("nav 17/20 · 600", SANS, 600, 17, "Recruitment"), ("body 16/22 · 500", SANS, 500, 16, "Only seated fans pay for a ticket."),
             ("label_caps 14/18 · 700", SANS, 700, 14, "FRIENDLY"), ("caption 14/16 · 500", SANS, 500, 14, "Refund drops to 10% over ~3 seasons")]
    ty = "".join(f'<div style="display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 16px; align-items: baseline; padding: 8px 0; border-bottom: 1px dashed {T["TAG_BORDER"]}"><span style="font: 500 14px/18px {SANS}; color: {T["MUTED"]}">{n}</span><span style="font: {w} {s}px/{s + 6}px {f}; color: {T["INK"]}">{t}</span></div>' for n, f, w, s, t in types)
    typesec = sec("Type", f"<div>{ty}</div>", 2, "Kalam for headings, notes and jokes. Work Sans for everything you read to play.")

    names = ["club", "stadium", "recruit", "squad", "finances", "fans", "approval", "cash", "seat", "shirt", "record", "settings", "quit", "news",
             "shop", "rail", "demolish", "rotate", "check", "close", "clock", "info", "warn", "play", "lock", "plus", "minus", "back"]
    ig = "".join(f'<div style="display: flex; flex-direction: column; align-items: center; gap: 4px; color: {T["INK"]}">{icon(n, 24)}<span style="font: 500 14px/16px {SANS}; color: {T["MUTED"]}">{n}</span></div>' for n in names)
    icons = sec("Icons", f'<div style="display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 14px 6px">{ig}</div>', 1, "24 grid, 2 px stroke, one colour.")

    def prim(state):
        if state == "disabled":
            return primary(T, "Play Match", "play", disabled=True, full=False)
        bg = {"default": T["PRIMARY"], "hover": "#DE3A47", "pressed": T["PRIMARY"]}[state]
        sh = "none" if state == "pressed" else f"0 3px 0 {T['PRIMARY_SH']}"
        tr = "transform: translateY(3px);" if state == "pressed" else ""
        return f'<button type="button" style="display: flex; align-items: center; gap: 10px; height: 56px; padding: 0 24px; border: none; border-radius: 8px; background: {bg}; color: #FFFFFF; font: 700 20px/24px {SANS}; box-shadow: {sh}; {tr} cursor: pointer">{icon("play", 20)}Play Match</button>'

    btns = sec("Buttons", f'''{label(T, "Primary · 56 high · club primary", T["MUTED"])}
{row(st("default", prim("default")), st("hover", prim("hover")), st("pressed", prim("pressed")), st("disabled", prim("disabled")))}
<span style="display: flex; align-items: center; gap: 8px; font: 600 16px/22px {SANS}; color: {danger(T)}">{icon("warn", 18)}Disabled always says why: "You need 11 players. You have 9."</span>
{label(T, "Link button · 44 high · 2 px ink border", T["MUTED"])}
{row(st("default", link_btn(T, "Build seats", "stadium")), st("hover", link_btn(T, "Build seats", "stadium", state="hover")), st("pressed", link_btn(T, "Build seats", "stadium", state="pressed")), st("disabled", link_btn(T, "Build seats", "stadium", state="disabled")))}
{label(T, "Icon button · 44 × 44", T["MUTED"])}
{row(st("default", ibtn(T, "settings", "Settings")), st("hover", ibtn(T, "settings", "Settings", "hover")), st("pressed", ibtn(T, "settings", "Settings", "pressed")), st("selected", ibtn(T, "rotate", "Rotate", "selected")), st("disabled", ibtn(T, "settings", "Settings", "disabled")))}''', 2)

    navs = sec("Nav item", f'''{row(st("default", nav_item(T, "stadium", "Stadium")), st("hover", nav_item(T, "stadium", "Stadium", "hover")))}
{row(st("pressed", nav_item(T, "stadium", "Stadium", "pressed")), st("selected", nav_item(T, "club", "Club", "selected")))}
{row(st("disabled", nav_item(T, "finances", "Finances", "disabled")))}''', 1, "Selected = highlight colour, lifted 4 px.")

    cards = sec("Shop card", row(st("default", shopcard(T, "Bench", "£40", "+4 seats", "seat", "Instant", "Seats four.")),
                                   st("hover", shopcard(T, "Bench", "£40", "+4 seats", "seat", "Instant", "Seats four.", "hover")),
                                   st("selected", shopcard(T, "Chair", "£12", "+1 seat", "seat", "Instant", "Folding. Mostly.", "selected")),
                                   st("disabled", shopcard(T, "Bench", "£40", "+4 seats", "seat", "", "Seats four.", "disabled")), gap=16)
                .replace('<div style="position: relative; box-sizing: border-box; padding: 14px 16px 14px;', '<div style="position: relative; width: 196px; box-sizing: border-box; padding: 14px 16px 14px;'), 2,
                "Selected = the item following your mouse in the ground: stripe + pin. Disabled shows the shortfall.")

    tags = sec("Stat tag & label", f'''{row(stat_tag(T, "cash", "£34", "Cash", -1), stat_tag(T, "fans", "30", "Fans", 0.8, delta="+4"), stat_tag(T, "approval", "58%", "Fan approval", -0.4, delta="−3"))}
{row(stat_tag(T, "shirt", "9 / 11", "Squad", 0.6, danger(T)), label(T, "Friendly"))}''', 1, "Small fixed rotations per tag (−1° to 1°).")

    def toggle(on, dis=False, lab="Show controls hint"):
        trk = T["PRIMARY"] if on else T["TAG_BG"]
        bd = T["PRIMARY"] if on else (T["TAG_BORDER"] if dis else T["INK"])
        kn = "#FFFFFF" if on else (T["TAG_BORDER"] if dis else T["INK"])
        pos = "left: 25px" if on else "left: 3px"
        return f'<div style="display: flex; align-items: center; gap: 12px; min-height: 44px"><span role="switch" aria-checked="{"true" if on else "false"}" style="position: relative; width: 52px; height: 30px; border-radius: 15px; background: {trk}; border: 2px solid {bd}; box-sizing: border-box; display: block"><span style="position: absolute; top: 3px; {pos}; width: 20px; height: 20px; border-radius: 10px; background: {kn}"></span></span><span style="font: 500 16px/20px {SANS}; color: {T["MUTED"] if dis else T["INK"]}">{lab}</span></div>'

    controls = sec("Inputs", f'''{slider(T, "Music", 70, "%")}
{segmented(T, ["Light", "Dark"], "Light")}
{toggle(True)}{toggle(False, lab="Invert camera rotation")}{toggle(False, True, "Controller vibration")}
<div style="display: flex; flex-direction: column; gap: 6px"><span style="font: 500 16px/22px {SANS}; color: {T["MUTED"]}">Progress (on a note: note track)</span>{progress(T, 24, on_note=False)}</div>''', 1)

    feedback = sec("Tooltip, toast, modal", f'''<div style="display: flex; gap: 12px; align-items: center">{ibtn(T, "info", "What is fan approval?", "hover")}
<div role="tooltip" style="max-width: 300px; padding: 10px 14px; border-radius: 3px; background: {T["NOTE"]}; color: {T["NOTE_INK"]}; font: 500 15px/20px {SANS}; box-shadow: 0 4px 10px rgba(0,0,0,0.25)">Fan approval: how happy your supporters are. Wins, good football and a seat all help.</div></div>
<div role="status" style="position: relative; width: 420px; box-sizing: border-box; padding: 18px 18px 14px; background: {T["NOTE"]}; border-radius: 2px; transform: rotate(-1deg); box-shadow: {T["SHADOW"]}; display: flex; gap: 12px">{tape(T, "top: -14px; left: 160px", 3)}
<span style="color: {T["OK"]}; display: flex">{icon("check", 22)}</span><div style="display: flex; flex-direction: column; gap: 2px"><span style="font: 700 17px/22px {SANS}; color: {T["NOTE_INK"]}">Bench built</span><span style="font: 400 18px/22px {HAND}; color: {T["NOTE_MUTED"]}">Somebody's nan has already claimed the end spot.</span></div></div>
<div style="position: relative; padding: 30px 20px 20px; border-radius: 3px; background: rgba(0,0,0,0.5)">
<div role="dialog" aria-label="Demolish" style="position: relative; box-sizing: border-box; padding: 26px 22px 20px; background: {T["CARD"]}; border-radius: 3px; box-shadow: 0 12px 30px rgba(0,0,0,0.45); display: flex; flex-direction: column; gap: 12px">{pin(T)}
{h2(T, "Demolish 5 benches?", 28)}<p style="margin: 0; font: 500 16px/22px {SANS}; color: {T["MUTED"]}">You get £150 back. 20 seats will be gone.</p>
<div style="display: flex; gap: 10px; justify-content: flex-end">{link_btn(T, "Cancel")}<button type="button" style="height: 44px; padding: 0 18px; border: none; border-radius: 8px; background: {danger(T)}; color: #FFFFFF; font: 700 16px/20px {SANS}; cursor: pointer">Demolish</button></div></div></div>''', 1)

    def trow(state, p, n, o):
        bg = {"default": "", "hover": "background: rgba(36,49,58,0.05);", "selected": f"background: rgba(208,32,46,0.10); box-shadow: inset 4px 0 0 {T['SEL_BG']};", "disabled": ""}[state]
        c = T["MUTED"] if state == "disabled" else T["INK"]
        return f'<div style="display: grid; grid-template-columns: 70px minmax(0, 1fr) minmax(0, 1.3fr) 110px; align-items: center; gap: 14px; height: 48px; padding: 0 16px; border-bottom: 1px solid {T["TAG_BORDER"]}; {bg}"><span style="justify-self: start; min-width: 48px; height: 28px; border: 2px solid {c}; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; font: 700 14px/16px {SANS}; color: {c}; box-sizing: border-box">{p}</span><span style="font: 600 17px/20px {SANS}; color: {c}">{n}</span><span style="font: 400 19px/22px {HAND}; color: {T["PEN"] if state != "disabled" else T["MUTED"]}">{o}</span><span style="font: 500 14px/18px {SANS}; color: {T["MUTED"]}">{state.capitalize()}</span></div>'
    table = sec("Table row", f'<div style="border-top: 2px solid {T["INK"]}">{trow("default", "GK", "Dave Harper", "Regular at the pub")}{trow("hover", "CB", "Steve Okafor", "Works at the builders\' yard")}{trow("selected", "ST", "Tom Price", "The barman\'s brother-in-law")}{trow("disabled", "CM", "Gaz Doyle", "Injured. Ladder incident.")}</div>', 2)

    pieces = sec("Pieces", f'''<div style="display: flex; gap: 30px; align-items: flex-start; flex-wrap: wrap; padding-top: 10px">
<div style="position: relative; width: 120px; height: 60px">{tape(T, "top: 16px; left: 12px", -4)}</div>
<div style="position: relative; width: 40px; height: 40px">{pin(T, "10px", 10)}</div>
<div style="position: relative; width: 150px; height: 110px; background: {T["NOTE"]}; transform: rotate(-1.4deg); box-shadow: {T["SHADOW"]}; padding: 14px; box-sizing: border-box; font: 400 18px/22px {HAND}; color: {T["NOTE_INK"]}">sticky note</div>
<div style="position: relative; width: 170px; height: 110px; background-color: {T["CARD"]}; border-top: 6px solid {T["STRIPE"]}; background-image: repeating-linear-gradient(to bottom, transparent 0 21px, {T["LINES"]} 21px 22px); box-shadow: {T["SHADOW"]}; padding: 14px; box-sizing: border-box; font: 600 15px/20px {SANS}; color: {T["INK"]}">{pin(T)}index card</div>
<div style="position: relative; width: 200px; height: 56px; background: {T["PAPER"]}; box-shadow: {T["SHADOW"]}; padding: 16px; box-sizing: border-box; font: 600 15px/20px {SANS}; color: {T["INK"]}">paper strip</div></div>''', 1)

    body = f'''<div style="box-sizing: border-box; width: 1920px; padding: 64px; display: flex; flex-direction: column; gap: 34px">
<div style="position: relative; align-self: flex-start; padding: 22px 30px; background: {T["PAPER"]}; border-radius: 3px; box-shadow: {T["SHADOW"]}; transform: rotate(-0.6deg)">{tape(T, "top: -14px; left: 40px", -5)}
<h1 style="margin: 0; font: 700 60px/64px {HAND}; color: {T["INK"]}">Sunday League · components</h1>
<p style="margin: 4px 0 0; font: 500 18px/24px {SANS}; color: {T["MUTED"]}">Clubhouse Noticeboard · club colours red/white · light mode. Exact values: UI Spec v2.</p></div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 30px; align-items: start">
{colours}{typesec}{icons}{btns}{navs}{cards}{tags}{controls}{feedback}{pieces}{table}</div></div>'''
    return page("Components · noticeboard", body, bg=None, h=3400, bg_color="#5F6E61")


SCREENS.append(("S_Components.dc.html", components, "Components & states · noticeboard"))
if __name__ == "__main__":
    open(os.path.join(OUT, "S_Components.dc.html"), "w").write(components())
    print("components ok")
