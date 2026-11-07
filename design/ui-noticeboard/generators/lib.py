import random, json

HUB_BG = "/_blob/1f9bcd845cc8a3a41faefaa2c5b5313a"
BUILD_BG = "/_blob/c067863772e2619585f732d703d5949b"

C = {
    "bg": "#263B2E", "panel": "#20372A", "border": "#526D57", "text": "#F5F0DF",
    "muted": "#C0C9B9", "accent": "#E8D9A8", "accent_hover": "#F4E8C2",
    "accent_pressed": "#D1BE86", "success": "#79C68B", "warning": "#E5AE54",
    "danger": "#D66B61", "on_accent": "#263B2E", "disabled_bg": "#526357",
    "disabled_text": "#AEB8AB",
}
PANEL_FILL = "rgba(32,55,42,0.93)"
UI = "'Barlow Semi Condensed', sans-serif"
HAND = "'Caveat', cursive"

ICONS = {
    "club": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    "stadium": '<path d="M2 20h20"/><path d="M4 20V10l8-4 8 4v10"/><path d="M8 20v-5h8v5"/>',
    "recruit": '<circle cx="9" cy="8" r="4"/><path d="M2 20c0-3.5 3-6 7-6s7 2.5 7 6"/><path d="M19 8v6"/><path d="M16 11h6"/>',
    "squad": '<circle cx="9" cy="8" r="3.5"/><path d="M2 20c0-3 3-5.5 7-5.5s7 2.5 7 5.5"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7"/><path d="M18 14.5c2.4.6 4 2.6 4 5.5"/>',
    "finances": '<path d="M16 6.5a4 4 0 0 0-7 2.5V20"/><path d="M6 13h8"/><path d="M6 20h12"/>',
    "fans": '<path d="M5 21V4"/><path d="M5 4h11l-2 4 2 4H5"/>',
    "approval": '<circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9.5h.01"/><path d="M15 9.5h.01"/>',
    "cash": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M6 12h.01"/><path d="M18 12h.01"/>',
    "seat": '<path d="M7 3v10"/><path d="M7 13h10v8"/><path d="M7 13v8"/><path d="M7 8h7"/>',
    "shirt": '<path d="M8 3L3 6l2 5 3-1v11h8V10l3 1 2-5-5-3c-.5 1.5-2 2.5-4 2.5S8.5 4.5 8 3z"/>',
    "record": '<path d="M4 20V11"/><path d="M10 20V5"/><path d="M16 20v-7"/><path d="M2 20h20"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="7.5"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="M2 12h2"/><path d="M20 12h2"/>',
    "quit": '<path d="M14 4h5v16h-5"/><path d="M10 8l-4 4 4 4"/><path d="M6 12h10"/>',
    "news": '<path d="M3 10v4h3l7 4V6l-7 4H3z"/><path d="M17 9a4 4 0 0 1 0 6"/>',
    "shop": '<path d="M3 9l2-5h14l2 5"/><path d="M4 9v11h16V9"/><path d="M3 9h18"/><path d="M10 20v-6h4v6"/>',
    "demolish": '<path d="M4 7h16"/><path d="M9 7V4h6v3"/><path d="M6 7l1 13h10l1-13"/>',
    "rail": '<path d="M3 9h18"/><path d="M5 9v11"/><path d="M19 9v11"/><path d="M12 9v11"/><path d="M3 14h18"/>',
    "rotate": '<path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v4h-4"/>',
    "check": '<path d="M5 12l5 5 9-10"/>',
    "close": '<path d="M6 6l12 12"/><path d="M18 6L6 18"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
    "play": '<path d="M7 4l13 8-13 8z"/>',
    "warn": '<path d="M12 3l10 18H2z"/><path d="M12 10v5"/><path d="M12 18h.01"/>',
    "minus": '<path d="M5 12h14"/>',
    "plus": '<path d="M12 5v14"/><path d="M5 12h14"/>',
    "back": '<path d="M15 5l-7 7 7 7"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
}


def icon(name, size=24, color=None, sw=2):
    col = color or "currentColor"
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{col}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
            f'style="flex-shrink: 0">{ICONS[name]}</svg>')


CREST_HOME = ('<svg width="{w}" height="{h}" viewBox="0 0 96 112" aria-hidden="true" style="flex-shrink: 0">'
              '<g fill="none" stroke="#E8D9A8" stroke-linecap="round" stroke-linejoin="round">'
              '<path d="M12 9 L48 3 L84 9 L82 62 Q78 88 48 106 Q18 88 14 62 Z" stroke-width="4"/>'
              '<path d="M23 19 L48 14 L73 19 L71 60 Q67 79 48 91 Q29 79 25 60 Z" stroke-width="1.8" opacity=".72"/>'
              '<path d="M48 31 L48 76 M48 44 L35 35 M48 54 L62 43 M48 63 L34 56 M48 70 L61 61" stroke-width="3.2"/>'
              '<path d="M35 35 Q30 25 25 32 Q24 42 40 45 M61 43 Q69 31 75 38 Q76 48 56 51 M34 56 Q24 51 24 61 Q28 69 43 66 M61 61 Q72 55 73 66 Q68 75 54 71" stroke-width="2.8"/>'
              '</g></svg>')
CREST_AWAY = ('<svg width="{w}" height="{h}" viewBox="0 0 96 112" aria-hidden="true" style="flex-shrink: 0">'
              '<g stroke="#F5F0DF" stroke-linejoin="round" stroke-linecap="round" fill="none">'
              '<path d="M12 9 L48 3 L84 9 L82 62 Q78 88 48 106 Q18 88 14 62 Z" stroke-width="4"/>'
              '<path d="M24 19 L72 19 L70 60 Q66 79 48 91 Q30 79 26 60 Z" stroke-width="2"/>'
              '<circle cx="48" cy="53" r="22" stroke-width="3"/>'
              '<path d="M48 39 L57 45 L54 56 L42 56 L39 45 Z M39 45 L31 42 M57 45 L65 42 M42 56 L38 66 M54 56 L59 66 M38 66 L48 74 L59 66" stroke-width="2.5"/>'
              '</g></svg>')


def crest(kind, w):
    h = round(w * 112 / 96)
    return (CREST_HOME if kind == "home" else CREST_AWAY).format(w=w, h=h)


def underline(width=150, variant=1):
    p = {1: ("M3 4.7 C28 3.1 49 5.2 76 3.8 S124 4.7 151 3.5 S207 4.8 237 3.2", "M8 6.1 C42 5.3 71 6.6 104 5.4 S176 6.2 229 5.4"),
         2: ("M3 4.2 C34 5.5 58 2.2 91 3.8 S145 5.3 177 3.6 S216 3.4 237 4.4", "M18 6.2 C65 5.1 91 6.7 139 5.6 S195 6.1 224 5.7")}[variant]
    return (f'<svg width="{width}" height="8" viewBox="0 0 240 8" preserveAspectRatio="none" aria-hidden="true" style="display: block">'
            f'<path d="{p[0]}" fill="none" stroke="#E8D9A8" stroke-width="3.1" stroke-linecap="round"/>'
            f'<path d="{p[1]}" fill="none" stroke="#E8D9A8" stroke-width=".7" stroke-linecap="round" opacity=".48"/></svg>')


# ---------- panel treatments ----------

def _rough_rect(w, h, seed, inset=3, jit=1.6):
    r = random.Random(seed)
    pts = []
    step = 60
    def j():
        return r.uniform(-jit, jit)
    x = inset
    while x < w - inset:
        pts.append((x, inset + j())); x += step
    y = inset
    while y < h - inset:
        pts.append((w - inset + j(), y)); y += step
    x = w - inset
    while x > inset:
        pts.append((x, h - inset + j())); x -= step
    y = h - inset
    while y > inset:
        pts.append((inset + j(), y)); y -= step
    d = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts) + " Z"
    return d


def layer_illustrated(w, h, seed=1):
    """B: stylised vector chalk: wiped swooshes + hand-drawn double border."""
    r = random.Random(seed)
    sw = []
    for i in range(3):
        y0 = h * (0.2 + 0.3 * i) + r.uniform(-12, 12)
        x0 = -20 + r.uniform(0, w * 0.1)
        x1 = w * r.uniform(0.55, 1.05)
        cy = y0 + r.uniform(-h * 0.18, h * 0.18)
        width = r.uniform(26, 54)
        op = r.uniform(0.035, 0.06)
        sw.append(f'<path d="M{x0:.0f} {y0:.0f} Q{(x0 + x1) / 2:.0f} {cy:.0f} {x1:.0f} {y0 + r.uniform(-20, 20):.0f}" '
                  f'stroke="#F5F0DF" stroke-opacity="{op:.3f}" stroke-width="{width:.0f}" stroke-linecap="round" fill="none"/>')
    b1 = _rough_rect(w, h, seed, 3, 1.4)
    b2 = _rough_rect(w, h, seed + 7, 6, 1.8)
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true" '
            f'style="position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none">'
            + "".join(sw) +
            f'<path d="{b1}" fill="none" stroke="#C9C2A0" stroke-opacity="0.55" stroke-width="1.6" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
            f'<path d="{b2}" fill="none" stroke="#C9C2A0" stroke-opacity="0.22" stroke-width="1" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
            '</svg>')


def layer_corners():
    """C: chalk corner marks, 4 small svgs."""
    def corner(pos, rot):
        return (f'<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true" '
                f'style="position: absolute; {pos}; transform: rotate({rot}deg); pointer-events: none">'
                '<path d="M2.5 19 C2.2 12 2.8 7 2.6 2.8 C7 2.4 12 3.1 19 2.6" fill="none" stroke="#E8D9A8" '
                'stroke-width="2.4" stroke-linecap="round" opacity=".85"/></svg>')
    return (corner("top: 6px; left: 6px", 0) + corner("top: 6px; right: 6px", 90)
            + corner("bottom: 6px; right: 6px", 180) + corner("bottom: 6px; left: 6px", 270))


def panel_style(variant, radius=9, extra=""):
    if variant == "A":
        return (f"position: relative; border: 1px solid rgba(8,16,11,0.65); border-radius: {radius}px; "
                f"box-shadow: 0 3px 10px rgba(0,0,0,0.22), inset 0 0 18px rgba(0,0,0,0.35); box-sizing: border-box; {extra}")
    if variant == "B":
        border = "border: 1px solid transparent"
    else:
        border = f"border: 1px solid {C['border']}"
    return (f"position: relative; background: {PANEL_FILL}; {border}; border-radius: {radius}px; "
            f"box-shadow: 0 3px 10px rgba(0,0,0,0.22); box-sizing: border-box; {extra}")


def decor(variant, w, h, seed):
    if variant == "B":
        return layer_illustrated(w, h, seed)
    if variant == "C":
        return layer_corners()
    return ""


def progress_fill(variant):
    if variant == "flat":
        return C["accent"]
    return ("repeating-linear-gradient(100deg, #E8D9A8 0px, #E8D9A8 5px, #D9CA98 5px, #D9CA98 7px, "
            "#EFE3BC 7px, #EFE3BC 11px)")


HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>%%TITLE%%</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;500;600;700&amp;family=Caveat:wght@500;600&amp;display=swap" rel="stylesheet">
<style>
body{margin:0}
a{color:#E8D9A8}a:hover{color:#F4E8C2}
</style>
</helmet>
"""

TAIL = """
</x-dc>
<script type="text/x-dc" data-dc-script data-props='%%PROPS%%'>
class Component extends DCLogic {
renderVals() {
return {};
}
}
</script>
</body>
</html>
"""


def page(title, body, w, h, css=""):
    props = json.dumps({"$preview": {"width": w, "height": h}})
    return HEAD.replace("%%TITLE%%", title).replace("a{color:#E8D9A8}", css + "a{color:#E8D9A8}") + body + TAIL.replace("%%PROPS%%", props)
