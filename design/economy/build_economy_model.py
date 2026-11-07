from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as L

F = "Arial"
BLUE = Font(name=F, color="0000FF"); BLACK = Font(name=F); GREEN = Font(name=F, color="008000")
GREY = Font(name=F, color="555555"); GREYI = Font(name=F, italic=True, color="666666")
BOLD = Font(name=F, bold=True); HEAD = Font(name=F, bold=True, color="FFFFFF")
HFILL = PatternFill("solid", fgColor="20372A"); RFILL = PatternFill("solid", fgColor="EEF0EA")
YEL = PatternFill("solid", fgColor="FFFF00")
EUR = '€#,##0;(€#,##0);-'; EUR2 = '€#,##0.00;(€#,##0.00);-'
GBP = '£#,##0;(£#,##0);-'; GBP2 = '£#,##0.00;(£#,##0.00);-'
NUM = '#,##0;(#,##0);-'; X = '0.0"x"'
thin = Side(style="thin", color="C0C9B9")

wb = Workbook()
rm = wb.active; rm.title = "Read me"
lines = [
 ("Sunday League — economy reference model v2 (2026-11-07)", BOLD),
 ("One 'reference club' per division (an average club at that level). Stand prices are derived from it and then stay FIXED in the game,", BLACK),
 ("so a player who does better than average can afford things sooner, and prices never punish good play.", BLACK),
 ("", BLACK),
 ("v2: every division now has a REAL-WORLD column (grey, £, English football 2024/25, with sources) next to the GAME value (blue, €, the middle ground).", BLACK),
 ("Formulas only use the GAME values. The real columns are there to compare against.", BLACK),
 ("", BLACK),
 ("Colours: blue = game inputs you can change · grey = real-world reference (sourced or marked 'est.') · black = formulas · green = pulled from another tab · yellow = key levers.", BLACK),
 ("", BLACK),
 ("Mapping (Claude's proposal): our 14 divisions on the real English pyramid —", BOLD),
 ("Premier Division = Premier League · League 1 = Championship · League 2 = League One · League 3 = League Two · League 4 = National League (Step 1)", BLACK),
 ("League 5 = National League North/South (Step 2) · League 6 = Step 3 · League 7 = Step 4 · League 8 = Step 5 · League 9 = Step 6 · League 10 = Step 7", BLACK),
 ("Non-League 1–3 = below the official pyramid (lower county leagues, Sunday league, park football). No published figures there: estimates only.", BLACK),
 ("", BLACK),
 ("Middle ground: the game values follow reality where it's smooth, but the two real cliffs are flattened so the pace stays smooth —", BOLD),
 ("(1) National League → League Two (central money jumps ~25x in reality) and (2) Championship → Premier League (central money ~15x, commercial ~10x).", BLACK),
 ("The bottom stays on v0.1's values (€2 ticket; GDD's '€1.70 TV money for a season: one beer'). Real figures are £, game figures €; Claude treats them roughly 1:1 for feel.", BLACK),
 ("", BLACK),
 ("Tabs: Reference club · Stand prices · Sources", BOLD),
]
for i, (t, f) in enumerate(lines, 1):
    rm.cell(i, 1, t).font = f
rm.column_dimensions["A"].width = 150

# ---------------------------------------------------------------- Reference club
rc = wb.create_sheet("Reference club")
rc["A1"] = "Home matches per season"; rc["A1"].font = BOLD
rc["B1"] = 19; rc["B1"].font = BLUE; rc["B1"].fill = YEL
rc["C1"] = "20 teams → 38 league matches, half at home (GDD §6). Real leagues mostly have 23 home games; not used."; rc["C1"].font = GREYI
heads = ["Division (game)", "Real-world equivalent",
 "Attendance REAL", "Attendance GAME",
 "Ticket REAL (£)", "Ticket GAME (€)",
 "Spend per visitor REAL (£)\nfood, drink, programme, merch", "Spend per visitor GAME (€)",
 "Sponsors & commercial per season REAL (£)", "Sponsors & commercial per season GAME (€)",
 "TV, solidarity & prize money per season REAL (£)", "TV, solidarity & prize money per season GAME (€)",
 "Matchday income per home match (€)", "Season income (€)", "Reference income per home match, all-in (€)", "Growth vs division below",
 "Basis of the REAL numbers (see Sources tab)"]
for c, h in enumerate(heads, 1):
    cell = rc.cell(3, c, h); cell.font = HEAD; cell.fill = HFILL
    cell.alignment = Alignment(wrap_text=True, vertical="center")
rc.row_dimensions[3].height = 72
# name, real level, att R, att G, tic R, tic G, spend R, spend G, spons R, spons G, central R, central G, basis
D = [
 ("Non-League 3", "Park / pub football", 10, 15, 0, 2, 1, 1, 50, 50, 0, 1.70, "All estimates (no published data). Game ticket = v0.1; central €1.70 = GDD joke"),
 ("Non-League 2", "Sunday league", 20, 30, 1, 3, 1.5, 1.5, 150, 150, 0, 10, "All estimates"),
 ("Non-League 1", "Lower county leagues (Step 8+)", 35, 45, 3, 3.5, 2, 2, 300, 350, 0, 25, "All estimates"),
 ("League 10", "Step 7 (county senior)", 50, 65, 4, 4.5, 2.5, 2.5, 600, 700, 0, 50, "Estimates; Step 6 prices from [S13] as upper bound"),
 ("League 9", "Step 6", 100, 110, 5.5, 6, 4, 3.5, 1000, 1500, 0, 100, "Att [S10] (67–139); ticket [S13]; spend [S14]; sponsors est."),
 ("League 8", "Step 5", 218, 220, 7.5, 8, 5, 4.5, 3000, 3500, 0, 250, "Att [S9]; ticket [S13]; spend [S14]; sponsors est."),
 ("League 7", "Step 4", 290, 330, 10, 11, 5.5, 5.5, 8000, 9000, 0, 700, "Att [S8]; ticket [S13]; spend est.; sponsors est."),
 ("League 6", "Step 3", 764, 650, 13, 14, 6, 6.5, 20000, 22000, 0, 2500, "Att [S7]; ticket [S13]; spend est.; sponsors est."),
 ("League 5", "National League North/South (Step 2)", 1250, 1400, 16, 17, 7, 7.5, 50000, 55000, 13636, 15000, "Att [S6]; ticket [S12]; central [S17]; sponsors est. from [S20]"),
 ("League 4", "National League (Step 1)", 2652, 2800, 18, 20, 8, 8.5, 150000, 150000, 58333, 60000, "Att [S5]; ticket [S12]; central [S17]; sponsors est. from [S20]"),
 ("League 3", "League Two", 6100, 6000, 20.5, 22, 9, 9.5, 1500000, 700000, 1500000, 450000, "Att [S4]; ticket [S11]; central [S16]; commercial est. ([S19] sanity check). GAME flattened: cliff 1"),
 ("League 2", "League One", 10057, 10000, 23.7, 26, 10, 11, 2500000, 2000000, 2100000, 1500000, "Att [S3]; ticket [S11]; central [S16]; commercial est. ([S19])"),
 ("League 1", "Championship", 22181, 21000, 30.1, 32, 12, 13, 11400000, 6000000, 9000000, 5000000, "Att [S2]; ticket [S11]; central [S16]; commercial [S18]. GAME flattened"),
 ("Premier Division", "Premier League", 40423, 40000, 46.3, 48, 15, 16, 115000000, 25000000, 141500000, 30000000, "Att [S1]; ticket [S11]; spend [S14]; commercial [S18]; central [S15]. GAME flattened: cliff 2"),
]
for r, row in enumerate(D, 4):
    rc.cell(r, 1, row[0]).font = BOLD
    rc.cell(r, 2, row[1]).font = GREY
    vals = row[2:12]
    for i, v in enumerate(vals):
        c = 3 + i
        real = (i % 2 == 0)
        cell = rc.cell(r, c, v)
        cell.font = GREY if real else BLUE
        if real: cell.fill = RFILL
        if i in (0, 1): cell.number_format = NUM
        elif i in (2, 3, 4, 5): cell.number_format = (GBP2 if real else EUR2)
        else: cell.number_format = (GBP if real else EUR2 if v < 10 else EUR)
    rc.cell(r, 13, f"=D{r}*(F{r}+H{r})").number_format = EUR
    rc.cell(r, 14, f"=M{r}*$B$1+J{r}+L{r}").number_format = EUR
    rc.cell(r, 15, f"=IFERROR(N{r}/$B$1,0)").number_format = EUR
    rc.cell(r, 16, "-" if r == 4 else f"=IFERROR(N{r}/N{r-1},0)"); rc.cell(r, 16).number_format = X
    for c in (13, 14, 15, 16): rc.cell(r, c).font = BLACK
    rc.cell(r, 17, row[12]).font = GREYI
    rc.cell(r, 17).alignment = Alignment(wrap_text=True)
    for c in range(1, 18): rc.cell(r, c).border = Border(bottom=thin)
rc["L4"].comment = Comment("GDD §10b: in the lowest tiers TV money is tiny — '€1.70 for a whole season: one beer'.", "Claude")
rc["F4"].comment = Comment("v0.1 uses a €2 ticket (scripts/club_state.gd).", "Claude")
rc["K16"].comment = Comment("Average of £2.83bn total central payments over 20 clubs; includes merit (prize) money and facility fees.", "Claude")
rc["I16"].comment = Comment("Deloitte: ~£2.3bn PL commercial revenue projected for 2024/25 ÷ 20. Very skewed: big six shirt deals alone are £40–60m.", "Claude")
widths = [17, 30, 11, 11, 10, 10, 15, 13, 17, 17, 17, 17, 16, 16, 18, 10, 60]
for i, w in enumerate(widths, 1): rc.column_dimensions[L(i)].width = w
rc.freeze_panes = "C4"
rc.cell(19, 1, "Real columns: English football, mostly 2024/25. Grey 'est.' = Claude's estimate where no figure was found. Game columns = Claude's middle-ground proposal (2026-11-07), nothing decided.").font = GREYI

# ---------------------------------------------------------------- Stand prices
sp = wb.create_sheet("Stand prices")
glob = [("Sections in a full ground", 28, "9 × 5 × 9 × 5 (GDD §10e)"),
        ("Assumed occupancy for payback", 0.7, "share of places sold per home match")]
for i, (k, v, note) in enumerate(glob, 1):
    sp.cell(i, 1, k).font = BOLD
    c = sp.cell(i, 2, v); c.font = BLUE; c.fill = YEL
    if isinstance(v, float): c.number_format = "0%"
    sp.cell(i, 3, note).font = GREYI
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
        sp.cell(r, c, v).font = BLUE
    sp.cell(r, 3).fill = YEL; sp.cell(r, 3).number_format = "0.0"
    dv.add(sp.cell(r, 2))
    sp.cell(r, 7, f"=E{r}*F{r}").number_format = NUM
    sp.cell(r, 8, "=" + LK.format(c="F", r=r) + "+" + LK.format(c="H", r=r)).number_format = EUR2
    sp.cell(r, 8).font = GREEN
    sp.cell(r, 9, f"=G{r}*$B$2*H{r}").number_format = EUR
    sp.cell(r, 10, f"=C{r}*'Reference club'!$B$1*I{r}").number_format = EUR
    sp.cell(r, 11, f"=IFERROR(J{r}/G{r},0)").number_format = EUR
    sp.cell(r, 12, f"=J{r}*$B$1").number_format = EUR
    sp.cell(r, 13, f"=IFERROR(J{r}/" + LK.format(c="O", r=r) + ",0)").number_format = "0.0"
    for c in (7, 9, 10, 11, 12, 13): sp.cell(r, c).font = BLACK
    for c in range(1, 14): sp.cell(r, c).border = Border(bottom=thin)
sp["C4"].comment = Comment("The lever: how many seasons of extra tickets + spend from these places pay the section back. GDD §10d: faster at the bottom, slower at the top.", "Claude")
sp["F8"].comment = Comment("Standing: ~25 per step per 11.5 m section (Claude's estimate). Seated: 20 per row (GDD §10i).", "Claude")
sp["F5"].comment = Comment("v0.1: up to 4 chairs per slot, ~3 slots per section → 12. Chair price in v0.1: €12, bench €40.", "Claude")
sp["E11"].comment = Comment("Lower tier can grow to 40 rows (Marcel). Max 40 + 30 + 20 (GDD §10i).", "Claude")
sp.cell(15, 1, "Cost per section = target payback (seasons) × home matches × places × occupancy × (ticket + spend). Sponsors/TV are not counted in payback.").font = GREYI
sp.cell(16, 1, "Build times: 1 week = 1 match week. Stage jump = 1 week demolition first, then build (Marcel, 2026-11-07).").font = GREYI
sp.cell(17, 1, "Real-world check: new stands cost roughly a few thousand £ per seat at the top — in line with the third tier here (see chat; not separately sourced).").font = GREYI
widths = [32, 18, 12, 11, 10, 10, 12, 18, 16, 16, 13, 18, 20]
for i, w in enumerate(widths, 1): sp.column_dimensions[L(i)].width = w
sp.freeze_panes = "B5"

# ---------------------------------------------------------------- Sources
so = wb.create_sheet("Sources")
for c, h in enumerate(["ID", "What", "Figure", "Source", "URL"], 1):
    cell = so.cell(1, c, h); cell.font = HEAD; cell.fill = HFILL
S = [
 ("S1", "Premier League average attendance 2024/25", "40,423", "2024–25 Premier League (Wikipedia mirror)", "https://wiki.krisyotam.com/content/wikipedia_en_all_nopic_2026-03/2024%E2%80%9325_Premier_League"),
 ("S2", "Championship average attendance 2024/25", "22,181", "Football Web Pages", "https://www.footballwebpages.co.uk/scottish-championship/attendances/scottish-league-two/championship"),
 ("S3", "League One average attendance 2024/25", "10,057", "Football Web Pages", "https://www.footballwebpages.co.uk/leagueone/attendances"),
 ("S4", "League Two average attendance", "away avg 6,135 (2024/25); record avg 6,274 (2023/24)", "Football Web Pages; EFL League Two (mdwiki)", "https://www.footballwebpages.co.uk/league-two/attendances/away ; https://www.mdwiki.org/wiki/Football_League_2"),
 ("S5", "National League average attendance 2024/25", "2,652", "Football Web Pages", "https://www.footballwebpages.co.uk/national-league/attendances"),
 ("S6", "National League North / South averages 2024/25", "1,271 / 1,226", "Football Web Pages", "https://www.footballwebpages.co.uk/national-league-north/attendances ; https://www.footballwebpages.co.uk/national-league-south/attendances"),
 ("S7", "Step 3: Isthmian Premier average 2024/25", "764", "SW Londoner", "https://www.swlondoner.co.uk/?p=152112"),
 ("S8", "Step 4: Isthmian North / South Central / South East averages", "266 / 244 / 367", "Isthmian League archive", "https://isthmianarchive.co.uk/2025.26A.pdf"),
 ("S9", "Step 5: North West Counties League average", "218", "Wikipedia, 2025–26 NWCFL", "https://en.wikipedia.org/wiki/2025%E2%80%9326_North_West_Counties_Football_League"),
 ("S10", "Step 6: Northern League Div Two / Combined Counties Div One averages 2024/25", "139 / 67", "Football Web Pages", "https://www.footballwebpages.co.uk/northern-league-division-two/attendances ; https://www.footballwebpages.co.uk/combined-counties-league-division-one/attendances"),
 ("S11", "Match tickets, avg of clubs' cheapest / top price: PL £29.63/£63.06, Champ £23.78/£36.50, L1 £21.00/£26.40, L2 £18.26/£22.84", "midpoint used", "BBC Price of Football (via inkl)", "https://www.inkl.com/news/true-cost-of-football-investigation-ticket-and-shirt-prices-and-soaring-tv-subscriptions"),
 ("S12", "National League cheapest ticket £17; NL South adult £14–20 (2024/25)", "£17–20 / ~£16", "Football Ground Guide; St Albans City away guide", "https://footballgroundguide.com/news/cheapest-matchday-options-in-england.html ; https://stalbanscityfc.com/internal/national-league-south-away-days-guide"),
 ("S13", "Non-league price points: Step 1 £20, Step 2 £15–18, Step 3 £13, Step 4 £10, Step 5 £7, Step 6 £6; Step 5 club £8; Step 6 mostly £5–6", "per step", "Football Writing Blog; Harwich & Parkeston FC; Clapton CFC", "https://footballwritingblog.substack.com/p/friday-freebie-non-league-has-its ; https://www.harwichandparkeston.com/news/202526-ticket-prices-announced-2925475.html ; https://www.claptoncfc.co.uk/2023/07/31/admission-prices-for-clapton-cfc-womens-and-mens-first-team-games-for-the-2023-2024-season/"),
 ("S14", "Spend: PL fans £8.90 on food & drink inside the ground; Step 5/6 a pint ~£3 + pie ~£2", "£8.90 / ~£5", "Barclays via A1 Retail Magazine; Football Writing Blog", "https://www.a1retailmagazine.com/?p=54920 ; https://footballwritingblog.substack.com/p/pie-and-a-pint-for-your-money"),
 ("S15", "PL central payments 2024/25: £2.83bn total; equal share £94.9m per club; merit up to £53.1m", "~£141.5m avg", "Football365; NBC Sports", "https://www.football365.com/news/2025-26-premier-league-prize-money-table-tv ; https://nbcsports.com/soccer/news/premier-league-prize-money-how-much-is-each-table-position-worth"),
 ("S16", "EFL central money per club: Championship ~£7–11m (basic award + PL solidarity); League One ~€2.5m; League Two ~€1.8m", "per club", "FootballTransfers; Peterborough Today", "https://www.footballtransfers.com/en/transfer-news/uk-championship/2026/05/efl-tv-money-parachute-payments-explained-championship-league-one-league-two ; https://www.peterboroughtoday.co.uk/sport/football/peterborough-united/peterborough-united-will-lose-out-on-a-huge-cash-injection-if-they-fail-to-win-promotion-and-it-could-be-about-to-get-worse-for-efl-clubs-plus-the-staggering-coronavirus-losses-of-a-league-one-promotion-2875075"),
 ("S17", "PL solidarity to non-league: National League £58,333 per club; NL North/South £13,636 per club", "per club", "Kentish Football", "https://kentishfootball.co.uk/news/NationalLeague140420"),
 ("S18", "Commercial revenue: PL ~£2.3bn (2024/25 projection); Championship £273m (2024/25)", "÷20 / ÷24", "Deloitte; FC Business", "https://www.deloitte.com/uk/en/services/consulting-financial/research/annual-review-of-football-finance-premier-league-clubs.html ; https://fcbusiness.co.uk/news/premier-league-revenues-hit-6-8bn-but-faces-widening-financial-divide/"),
 ("S19", "Average total club revenue 2023/24: League One £9.1m, League Two £6.6m (sanity check)", "per club", "Deloitte via Sports Marketing", "https://www.sportsmarketing.com.ng/2025/06/european-football-clubs-report-record.html"),
 ("S20", "Non-league sponsorship: 'five figure' shirt deal at NL North level; a 'six-figure' deal called among the biggest in non-league", "order of magnitude", "Pink Un; Erewash Sound", "https://www.pinkun.com/news/22711788.kings-lynn-town-secure-five-figure-sponsorship-deal/ ; https://www.erewashsound.com/node/51640"),
]
for r, s_ in enumerate(S, 2):
    for c, v in enumerate(s_, 1):
        cell = so.cell(r, c, v); cell.font = BLACK; cell.alignment = Alignment(wrap_text=True, vertical="top")
for col, w in zip("ABCDE", [6, 70, 26, 38, 90]):
    so.column_dimensions[col].width = w

wb.active = 1
wb.save("Sunday_League_economy_model.xlsx")
print("saved")
