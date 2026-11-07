from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.worksheet.datavalidation import DataValidation

F = "Arial"
BLUE = Font(name=F, color="0000FF")
BLACK = Font(name=F)
GREEN = Font(name=F, color="008000")
BOLD = Font(name=F, bold=True)
HEAD = Font(name=F, bold=True, color="FFFFFF")
HFILL = PatternFill("solid", fgColor="20372A")
YEL = PatternFill("solid", fgColor="FFFF00")
EUR = '€#,##0;(€#,##0);-'
EUR2 = '€#,##0.00;(€#,##0.00);-'
NUM = '#,##0;(#,##0);-'
X = '0.0"x"'
thin = Side(style="thin", color="C0C9B9")

wb = Workbook()

# ---------------------------------------------------------------- Read me
rm = wb.active; rm.title = "Read me"
lines = [
 ("Sunday League — economy reference model (draft, 2026-11-07)", BOLD),
 ("Purpose: fix one 'reference club' per division (an average club at that level). Stand prices are derived from it and then stay FIXED in the game,", BLACK),
 ("so a player who does better than average can afford things sooner, and prices never punish good play.", BLACK),
 ("", BLACK),
 ("How to use", BOLD),
 ("Blue numbers = inputs you can change (all are Claude's first guesses, not decisions).", BLUE),
 ("Black numbers = formulas, do not type over them. Green = pulled from another tab.", BLACK),
 ("Yellow fill = the key levers: target payback per stage (seasons) and the global assumptions.", BLACK),
 ("", BLACK),
 ("Tabs", BOLD),
 ("Reference club — one row per division: attendance, prices, sponsors, TV, prize money → income per home match and per season.", BLACK),
 ("Stand prices — one row per stand stage: typical division, target payback (seasons), build time, places → cost per section, per place, for a full ground.", BLACK),
 ("", BLACK),
 ("Example: change 'Avg attendance' for League 10 and change a target payback and watch the cost of The Shed move on the Stand prices tab.", BLACK),
 ("Source of the decisions behind this: GDD §10b (economy), §10d (pace), §10i (stand stages). Division names follow GDD §6 (names still open).", BLACK),
]
for i, (t, f) in enumerate(lines, 1):
    rm.cell(i, 1, t).font = f
rm.column_dimensions["A"].width = 140

# ---------------------------------------------------------------- Reference club
rc = wb.create_sheet("Reference club")
rc["A1"] = "Home matches per season"; rc["A1"].font = BOLD
rc["B1"] = 19; rc["B1"].font = BLUE; rc["B1"].fill = YEL
rc["C1"] = "20 teams → 38 league matches, half at home (GDD §6). Cups not included."; rc["C1"].font = Font(name=F, italic=True, color="666666")
heads = ["Division", "Avg attendance", "Ticket price (€)", "Spend per visitor (€)\nfood, drinks, merch",
         "Sponsors per season (€)", "TV per season (€)", "Prize money per season (€)",
         "Matchday income per home match (€)", "Season income (€)", "Reference income per home match, all-in (€)", "Growth vs division below"]
for c, h in enumerate(heads, 1):
    cell = rc.cell(3, c, h); cell.font = HEAD; cell.fill = HFILL
    cell.alignment = Alignment(wrap_text=True, vertical="center")
rc.row_dimensions[3].height = 46
data = [  # bottom → top
 ("Non-League 3", 30, 2, 1, 50, 1.70, 20),
 ("Non-League 2", 60, 3, 1.5, 150, 10, 50),
 ("Non-League 1", 120, 4, 2, 400, 50, 150),
 ("League 10", 220, 5, 2.5, 1000, 200, 400),
 ("League 9", 380, 6, 3, 2500, 700, 1000),
 ("League 8", 650, 7, 3.5, 6000, 2000, 2500),
 ("League 7", 1100, 8, 4, 15000, 6000, 6000),
 ("League 6", 1800, 10, 5, 35000, 15000, 15000),
 ("League 5", 3000, 12, 6, 80000, 40000, 35000),
 ("League 4", 5000, 15, 7.5, 200000, 120000, 80000),
 ("League 3", 8000, 18, 9, 500000, 400000, 200000),
 ("League 2", 13000, 22, 11, 1500000, 1500000, 500000),
 ("League 1", 20000, 28, 14, 5000000, 8000000, 1500000),
 ("Premier Division", 35000, 40, 20, 25000000, 60000000, 10000000),
]
for r, row in enumerate(data, 4):
    rc.cell(r, 1, row[0]).font = BLACK
    for c, v in enumerate(row[1:], 2):
        cell = rc.cell(r, c, v); cell.font = BLUE
        cell.number_format = NUM if c == 2 else (EUR2 if c in (3, 4) or v < 10 else EUR)
    rc.cell(r, 8, f"=B{r}*(C{r}+D{r})").number_format = EUR
    rc.cell(r, 9, f"=H{r}*$B$1+E{r}+F{r}+G{r}").number_format = EUR
    rc.cell(r, 10, f"=IFERROR(I{r}/$B$1,0)").number_format = EUR
    rc.cell(r, 11, "-" if r == 4 else f"=IFERROR(J{r}/J{r-1},0)")
    rc.cell(r, 11).number_format = X
    for c in range(8, 12):
        rc.cell(r, c).font = BLACK
    for c in range(1, 12):
        rc.cell(r, c).border = Border(bottom=thin)
rc["F4"].comment = Comment("GDD §10b: in the lowest tiers TV money is tiny — '€1.70 for a whole season: one beer'.", "Claude")
rc["B4"].comment = Comment("Average club at this level, not your starting club (v0.1 starts with 5 fans).", "Claude")
rc["C4"].comment = Comment("v0.1 uses a €2 ticket (scripts/club_state.gd).", "Claude")
rc.cell(19, 1, "All blue values are Claude's first estimates (2026-11-07), loosely shaped on English non-league → Premier League attendances; to be tuned with Marcel and a simulation.").font = Font(name=F, italic=True, color="666666")
widths = [18, 14, 13, 16, 18, 15, 16, 18, 16, 20, 12]
for i, w in enumerate(widths):
    rc.column_dimensions[chr(65 + i)].width = w
rc.freeze_panes = "B4"

# ---------------------------------------------------------------- Stand prices
sp = wb.create_sheet("Stand prices")
glob = [("Sections in a full ground", 28, "9 × 5 × 9 × 5 (GDD §10e)"),
        ("Assumed occupancy for payback", 0.7, "share of places sold per home match")]
for i, (k, v, note) in enumerate(glob, 1):
    sp.cell(i, 1, k).font = BOLD
    c = sp.cell(i, 2, v); c.font = BLUE; c.fill = YEL
    if isinstance(v, float): c.number_format = "0%"
    sp.cell(i, 3, note).font = Font(name=F, italic=True, color="666666")
heads = ["Stage", "Typical division", "Target payback (seasons)", "Build time (weeks)", "Rows / steps",
         "Places per row", "Places per section", "Ticket + spend per visitor at that division (€)",
         "Extra income per home match (€)", "Cost per section (€)", "Cost per place (€)",
         "Full ground, 28 sections (€)", "Cost in home matches of the reference club's all-in income"]
for c, h in enumerate(heads, 1):
    cell = sp.cell(4, c, h); cell.font = HEAD; cell.fill = HFILL
    cell.alignment = Alignment(wrap_text=True, vertical="center")
sp.row_dimensions[4].height = 58
stages = [
 ("Loose chairs (have)", "Non-League 3", 0.3, 0, 1, 12),
 ("Benches (have)", "Non-League 3", 0.4, 0, 1, 12),
 ("Open bleachers", "Non-League 2", 0.5, 1, 3, 20),
 ("Standing terrace (first tier only)", "Non-League 1", 0.5, 2, 6, 25),
 ("The Shed (covered)", "League 10", 1.0, 2, 3, 20),
 ("Main stand, roof on columns", "League 8", 1.5, 4, 10, 20),
 ("Modern tier, cantilever", "League 5", 2.0, 8, 15, 20),
 ("+ Second tier", "League 3", 2.5, 12, 10, 20),
 ("+ Third tier", "Premier Division", 3.0, 16, 10, 20),
]
dv = DataValidation(type="list", formula1="='Reference club'!$A$4:$A$17", allow_blank=False)
sp.add_data_validation(dv)
LK = "INDEX('Reference club'!${c}$4:${c}$17,MATCH(B{r},'Reference club'!$A$4:$A$17,0))"
for r, s_ in enumerate(stages, 5):
    sp.cell(r, 1, s_[0]).font = BLACK
    for c, v in enumerate(s_[1:], 2):
        cell = sp.cell(r, c, v); cell.font = BLUE
    sp.cell(r, 3).fill = YEL
    sp.cell(r, 3).number_format = "0.0"
    dv.add(sp.cell(r, 2))
    sp.cell(r, 7, f"=E{r}*F{r}").number_format = NUM
    sp.cell(r, 8, "=" + LK.format(c="C", r=r) + "+" + LK.format(c="D", r=r)).number_format = EUR2
    sp.cell(r, 8).font = GREEN
    sp.cell(r, 9, f"=G{r}*$B$2*H{r}").number_format = EUR
    sp.cell(r, 10, f"=C{r}*'Reference club'!$B$1*I{r}").number_format = EUR
    sp.cell(r, 11, f"=IFERROR(J{r}/G{r},0)").number_format = EUR
    sp.cell(r, 12, f"=J{r}*$B$1").number_format = EUR
    sp.cell(r, 13, f"=IFERROR(J{r}/" + LK.format(c="J", r=r) + ",0)").number_format = "0.0"
    for c in (7, 9, 10, 11, 12, 13):
        sp.cell(r, c).font = BLACK
    for c in range(1, 14):
        sp.cell(r, c).border = Border(bottom=thin)
sp["C4"].comment = Comment("The lever: how many seasons of extra tickets + spend from these places pay the section back. GDD §10d: faster at the bottom, slower at the top (2–3 seasons per division higher up).", "Claude")
sp["F8"].comment = Comment("Standing: ~25 per step per 11.5 m section (Claude's estimate). Seated: 20 per row (GDD §10i).", "Claude")
sp["F5"].comment = Comment("v0.1: up to 4 chairs per slot, ~3 slots per section → 12. Chair price in v0.1: €12, bench €40.", "Claude")
sp["E9"].comment = Comment("Rows within a stage are upgrades (e.g. Shed 3 → 5 → 8). This row prices the first step only.", "Claude")
sp["E11"].comment = Comment("Lower tier can grow to 40 rows (Marcel). Max 40 + 30 + 20 (GDD §10i).", "Claude")
sp.cell(15, 1, "Cost per section = target payback (seasons) × home matches × places × occupancy × (ticket + spend). Sponsors/TV are not counted in payback.").font = Font(name=F, italic=True, color="666666")
sp.cell(16, 1, "First try priced stands as 'N home matches of all-in income' — that exploded at the top (TV/sponsors), e.g. ~€530k per place for a third tier. Kept as the last column for reference.").font = Font(name=F, italic=True, color="666666")
sp.cell(17, 1, "Build times: 1 week = 1 match week. Stage jump = 1 week demolition first, then build (Marcel, 2026-11-07).").font = Font(name=F, italic=True, color="666666")
widths = [32, 18, 12, 11, 10, 10, 12, 18, 16, 16, 13, 18, 20]
for i, w in enumerate(widths):
    sp.column_dimensions[chr(65 + i)].width = w
sp.freeze_panes = "B5"

wb.active = 1
wb.save("Sunday_League_economy_model.xlsx")
print("saved")
