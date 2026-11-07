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
 ("Sunday League — economy reference model v4 (2026-11-07): income, stand prices, expenses, transfers & ratings", BOLD),
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
 ("Tabs: Reference club · Stand prices · Expenses · Transfers · Sources", BOLD),
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
 ("S21", "Wages/revenue: Premier League 65% (2024/25, wages £4.4bn); Championship wages £903m vs revenue £942m (2024/25)", "65% / ~96%", "Deloitte Annual Review of Football Finance 2026; Inside World Football", "https://www.deloitte.com/uk/en/services/consulting/research/annual-review-of-football-finance-premier-league-clubs.html ; https://www.insideworldfootball.com/2026/07/08/big-5-european-league-revenue-breaks-e40bn-but-deloitte-warns-growth-will-slow/"),
 ("S22", "Average weekly pay: National League £1,000–1,500, League Two ~£2,500, League One just under £5,000, Championship ~£12,600; Premier League ~£60,000", "per player per week", "90min; Football Park", "https://www.90min.com/posts/how-much-do-national-league-players-get-paid ; https://footballpark.com/football-blogs/how-much-do-footballers-make"),
 ("S23", "Non-league pay: Step 3 ~£350–600/week; Step 4 ~£200–350/week; Step 5 £40–80 per game; Step 6 £20–40", "per player", "Bournemouth University (Buzz)", "https://buzz.bournemouth.ac.uk/?p=363074"),
 ("S24", "Grassroots team running costs ~£2,000–5,000+ per season (fees, pitch hire, insurance)", "per season", "Avec Sport", "https://avecsport.com/blog/what-are-the-costs-of-running-a-football-club"),
 ("S25", "Step 5/6 players often paid only small match fees or expenses", "-", "Football in Berkshire", "https://footballinberkshire.co.uk/features/opinion/36476/the-insider-on-player-wages-at-non-league-step-5-and-6/"),
 ("S26", "Referees for adult grassroots games £20–45 per match", "per match", "The Soccer Store", "https://www.thesoccerstore.co.uk/blog/latest-news/how-much-does-it-cost-to-set-up-a-grassroots-football-team/"),
 ("S27", "Average pre-tax result per club 2024/25: PL −£31.1m, Championship −£15.1m, League One −£5.0m, League Two −£2.6m", "per club", "FootballTransfers (Swiss Ramble)", "https://www.footballtransfers.com/us/transfer-news/uk-premier-league/2026/03/only-four-clubs-in-the-top-four-divisions-in-england-in-profit-for-202425"),
 ("S28", "Gross transfer spend summer 2025: Premier League £3.0bn (net £1.2bn); Championship £240m (receipts £355m)", "per league", "Deloitte", "https://www.deloitte.com/uk/en/about/press-room/deloitte-premier-league-spending-record-eclipsed.html"),
 ("S29", "EA FC 26 ratings: Salah 91; Rodri, Van Dijk, Haaland 90; top-26 PL players 85–91; Mbappé 92 highest overall", "rating anchor", "GOAL; Everything Edinburgh", "https://www.goal.com/en/lists/ea-sports-fc-26-premier-league-player-ratings-mohamed-salah-erling-haaland-rodri-alexander-isak/blt9b473388c755fa75 ; https://everythingedinburgh.com/games/gaming/ea-fc-26-player-ratings/"),
 ("S30", "Non-league fees: AFC Fylde → Peterborough £600k guaranteed (2nd-highest National League transfer); Vardy £1m (2012); record £1.5m (Abdulmalik)", "outliers", "Peterborough Today; DAZN", "https://www.peterboroughtoday.co.uk/sport/football/peterborough-united/peterborough-united-have-signed-a-new-striker-from-non-league-football-for-ps600k-8944375 ; https://www.dazn.com/en-CA/news/soccer/most-expensive-transfers-national-league-history-abdulmalik-vardy-jalal-taylor/ebal4uu1am5710yamz1y6zkip"),
 ("S31", "Newly promoted Championship club Charlton paid £3.5m (up to £5m) for one player; Wrexham spent £32.7m in one window", "outliers", "EFL Analysis", "https://eflanalysis.com/transfers/every-championship-teams-summer-spending-compared/"),
 ("S20", "Non-league sponsorship: 'five figure' shirt deal at NL North level; a 'six-figure' deal called among the biggest in non-league", "order of magnitude", "Pink Un; Erewash Sound", "https://www.pinkun.com/news/22711788.kings-lynn-town-secure-five-figure-sponsorship-deal/ ; https://www.erewashsound.com/node/51640"),
]
for r, s_ in enumerate(S, 2):
    for c, v in enumerate(s_, 1):
        cell = so.cell(r, c, v); cell.font = BLACK; cell.alignment = Alignment(wrap_text=True, vertical="top")
for col, w in zip("ABCDE", [6, 70, 26, 38, 90]):
    so.column_dimensions[col].width = w


# ---------------------------------------------------------------- Expenses
ex = wb.create_sheet("Expenses", 2)
ex["A1"] = "Expenses per division: REAL (grey, English football, with sources) vs GAME (blue, % of the reference club's season income)"; ex["A1"].font = BOLD
ex["A2"] = "Real clubs mostly LOSE money (wages alone are 65% of revenue in the PL and ~96% in the Championship). A tycoon game needs a surplus to build with, so the game deliberately keeps one: bigger at the bottom (fast start), smaller at the top (GDD §10d)."; ex["A2"].font = GREYI
heads = ["Division (game)", "Real-world equivalent",
 "Player pay REAL", "Wages / revenue REAL", "Avg pre-tax result per club REAL (£)",
 "Wages GAME (% of income)", "Staff GAME (%)", "Ground running & maintenance GAME (%)", "Travel, referees & match costs GAME (%)",
 "Total costs (%)", "Surplus (%)", "Season income (€)", "Surplus per season (€)",
 "Stand stage you'd be building here", "Cost per section of that stage (€)", "Sections you can afford per season",
 "Basis of the REAL numbers (see Sources tab)"]
for c, h in enumerate(heads, 1):
    cell = ex.cell(4, c, h); cell.font = HEAD; cell.fill = HFILL
    cell.alignment = Alignment(wrap_text=True, vertical="center")
ex.row_dimensions[4].height = 72
E = [
 ("Park football, players pay subs; a grassroots team costs ~£2–5k/season to run", "-", "-", 0, 0, 25, 20, "Loose chairs (have)", "Players unpaid [S25]; running costs [S24]"),
 ("Unpaid (Sunday league)", "-", "-", 10, 0, 20, 18, "Open bleachers", "Est.; refs £20–45 per match [S26]"),
 ("~£0–20 per game (est.)", "-", "-", 20, 2, 18, 15, "Standing terrace (first tier only)", "Est."),
 ("~£0–20 per game (est.)", "-", "-", 28, 4, 15, 13, "The Shed (covered)", "Est."),
 ("£20–40 per game", "-", "-", 35, 5, 14, 11, "The Shed (covered)", "Pay [S23]"),
 ("£40–80 per game; some only expenses", "-", "-", 40, 6, 13, 10, "Main stand, roof on columns", "Pay [S23]"),
 ("~£200–350 per week (club level, unclear if per player)", "-", "-", 45, 7, 12, 8, "Main stand, roof on columns", "Pay [S23]"),
 ("£350–600 per week (some up to £700)", "-", "-", 48, 8, 11, 7, "Main stand, roof on columns", "Pay [S23]"),
 ("~£500 per week (weak source)", "-", "-", 50, 9, 10, 6, "Modern tier, cantilever", "Pay est. ([S22] mentions it, weak)"),
 ("£1,000–1,500 per week", "-", "-", 52, 9, 10, 5, "Modern tier, cantilever", "Pay [S22]"),
 ("~£2,500 per week", "-", -2600000, 54, 10, 9, 4, "+ Second tier", "Pay [S22]; result [S27]"),
 ("~£5,000 per week", "-", -5000000, 55, 10, 9, 4, "+ Second tier", "Pay [S22]; result [S27]"),
 ("~£12,600 per week", 0.96, -15100000, 57, 10, 9, 3, "+ Second tier", "Pay [S22]; wages £903m vs revenue £942m [S21]; result [S27]"),
 ("~£60,000 per week", 0.65, -31100000, 60, 10, 8, 2, "+ Third tier", "Pay [S22]; wages/revenue [S21]; result [S27]"),
]
dv2 = DataValidation(type="list", formula1="='Stand prices'!$A$5:$A$13", allow_blank=False)
ex.add_data_validation(dv2)
for i, row in enumerate(E):
    r = 5 + i
    rc_row = 4 + i
    ex.cell(r, 1, f"='Reference club'!A{rc_row}").font = GREEN
    ex.cell(r, 2, f"='Reference club'!B{rc_row}").font = GREEN
    for c, v in zip((3, 4, 5), row[0:3]):
        cell = ex.cell(r, c, v); cell.font = GREY; cell.fill = RFILL
    ex.cell(r, 4).number_format = "0%"; ex.cell(r, 5).number_format = GBP
    for c, v in zip((6, 7, 8, 9), row[3:7]):
        cell = ex.cell(r, c, v / 100); cell.font = BLUE; cell.number_format = "0%"
    ex.cell(r, 6).fill = YEL
    ex.cell(r, 10, f"=SUM(F{r}:I{r})").number_format = "0%"
    ex.cell(r, 11, f"=1-J{r}").number_format = "0%"
    ex.cell(r, 12, f"='Reference club'!N{rc_row}").number_format = EUR; ex.cell(r, 12).font = GREEN
    ex.cell(r, 13, f"=L{r}*K{r}").number_format = EUR
    c14 = ex.cell(r, 14, row[7]); c14.font = BLUE; dv2.add(c14)
    ex.cell(r, 15, f"=INDEX('Stand prices'!$J$5:$J$13,MATCH(N{r},'Stand prices'!$A$5:$A$13,0))").number_format = EUR
    ex.cell(r, 15).font = GREEN
    ex.cell(r, 16, f"=IFERROR(M{r}/O{r},0)").number_format = "0.0"
    for c in (10, 11, 13, 16): ex.cell(r, c).font = BLACK
    ex.cell(r, 17, row[8]).font = GREYI
    for c in range(1, 18): ex.cell(r, c).border = Border(bottom=thin)
ex["K4"].comment = Comment("What the reference club keeps each season to build with. Real clubs: mostly negative.", "Claude")
ex["F4"].comment = Comment("Non-league in the game: amateur contracts are free; you may pay a small fee per match (GDD §10b).", "Claude")
ex.cell(20, 1, "Game percentages are Claude's proposal (2026-11-07): surplus 55% at the bottom → 20% at the top. 'Sections per season' is a pace check against GDD §10d, to be verified with a simulation.").font = GREYI
widths = [17, 28, 30, 11, 16, 11, 9, 13, 13, 9, 9, 15, 15, 30, 15, 12, 50]
for i, w in enumerate(widths, 1): ex.column_dimensions[L(i)].width = w
ex.freeze_panes = "C5"


# ---------------------------------------------------------------- Transfers
tr = wb.create_sheet("Transfers", 3)
tr["A1"] = "Transfers & player ratings (1–99). Marcel: the surplus is a free choice — build the stadium or strengthen the squad; you need both. 99 = 'a Messi, but even better', almost unreachable."; tr["A1"].font = BOLD
tr["A3"] = "Value of a rating-80 player (€)"; tr["A3"].font = BOLD
tr["B3"] = 4500000; tr["B3"].font = BLUE; tr["B3"].fill = YEL; tr["B3"].number_format = EUR
tr["C3"] = "Calibrated to the GAME economy (top income is flattened), not real-world fees. A top club can afford ~2–3 signings around 82 per season."; tr["C3"].font = GREYI
tr["A4"] = "Value multiplier per rating point"; tr["A4"].font = BOLD
tr["B4"] = 1.25; tr["B4"].font = BLUE; tr["B4"].fill = YEL; tr["B4"].number_format = '0.00"x"'
tr["C4"] = "Exponential: +1 rating = ×1.25 value, so +10 ≈ ×9. Low ratings become practically free (fits GDD: amateurs are free)."; tr["C4"].font = GREYI
for c, h in enumerate(["Rating", "Player value (€)", "Rough real-world feel"], 1):
    cell = tr.cell(6, c, h); cell.font = HEAD; cell.fill = HFILL
feel = {99: "mythical: better than Messi at his peak", 95: "best player in the world", 90: "world class (EA FC 26 top: Salah 91, Rodri/Haaland 90)", 85: "Premier League star", 80: "solid Premier League starter", 75: "Premier League squad / Championship star", 70: "Championship regular", 65: "League One regular", 60: "League Two regular", 55: "National League", 50: "National League North/South", 45: "Step 3–4", 40: "Step 5", 30: "Step 7 / county", 20: "Sunday league", 10: "park kickabout", 1: "your mate who came along"}
ratings = [99, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 30, 20, 10, 1]
for i, rt in enumerate(ratings):
    r = 7 + i
    tr.cell(r, 1, rt).font = BLACK
    tr.cell(r, 2, f"=$B$3*$B$4^(A{r}-80)").number_format = EUR2 if rt < 40 else EUR
    tr.cell(r, 3, feel[rt]).font = GREYI
# per division
R0 = 26
tr.cell(R0 - 1, 1, "Per division: reference transfer spend and what is left for the stadium").font = BOLD
heads = ["Division (game)", "Real-world equivalent", "Gross transfer spend per club per season REAL (£)",
 "Avg squad rating GAME", "Share of surplus spent on transfers GAME (%)", "Surplus per season (€)",
 "Transfer budget (€)", "Value of a signing at avg + 2 (€)", "≈ Signings per season",
 "Left for the stadium (€)", "Stand stage you'd be building", "Cost per section (€)", "Sections per season after transfers",
 "Basis of the REAL numbers"]
for c, h in enumerate(heads, 1):
    cell = tr.cell(R0, c, h); cell.font = HEAD; cell.fill = HFILL
    cell.alignment = Alignment(wrap_text=True, vertical="center")
tr.row_dimensions[R0].height = 72
T = [  # real gross spend £, avg rating, transfer share %, basis
 ("~0 (players walk in)", 15, 0, "No fees at this level (GDD: amateurs free)"),
 ("~0", 22, 0, "No fees"),
 ("~0", 28, 5, "No fees"),
 ("~0", 33, 10, "No fees; est."),
 ("~0", 37, 15, "Fees rare; est."),
 ("~0", 41, 20, "Fees rare; est."),
 ("small (compensation)", 45, 25, "Est."),
 ("small (compensation)", 49, 30, "Est."),
 ("~£5k (est.)", 53, 40, "Est."),
 (30000, 57, 50, "Est.; record fees received £0.6–1.5m are outliers [S30]"),
 (200000, 62, 60, "Est."),
 (1000000, 65, 70, "Est.; e.g. a newly promoted club paying £3.5m for one player is an outlier [S31]"),
 (10000000, 70, 80, "£240m gross across 24 clubs, summer 2025 [S28]"),
 (150000000, 80, 85, "£3.0bn gross across 20 clubs, summer 2025 [S28]; ratings anchor: EA FC 26 top 91 [S29]"),
]
for i, row in enumerate(T):
    r = R0 + 1 + i
    er = 5 + i    # Expenses row
    rr = 4 + i    # Reference club row
    tr.cell(r, 1, f"='Reference club'!A{rr}").font = GREEN
    tr.cell(r, 2, f"='Reference club'!B{rr}").font = GREEN
    c3 = tr.cell(r, 3, row[0]); c3.font = GREY; c3.fill = RFILL
    if isinstance(row[0], (int, float)): c3.number_format = GBP
    tr.cell(r, 4, row[1]).font = BLUE
    c5 = tr.cell(r, 5, row[2] / 100); c5.font = BLUE; c5.number_format = "0%"; c5.fill = YEL
    tr.cell(r, 6, f"=Expenses!M{er}").number_format = EUR; tr.cell(r, 6).font = GREEN
    tr.cell(r, 7, f"=F{r}*E{r}").number_format = EUR
    tr.cell(r, 8, f"=$B$3*$B$4^(D{r}+2-80)").number_format = EUR
    tr.cell(r, 9, f"=IFERROR(G{r}/H{r},0)").number_format = "0.0"
    tr.cell(r, 10, f"=F{r}-G{r}").number_format = EUR
    tr.cell(r, 11, f"=Expenses!N{er}").font = GREEN
    tr.cell(r, 12, f"=Expenses!O{er}").number_format = EUR; tr.cell(r, 12).font = GREEN
    tr.cell(r, 13, f"=IFERROR(J{r}/L{r},0)").number_format = "0.0"
    for c in (7, 8, 9, 10, 13): tr.cell(r, c).font = BLACK
    tr.cell(r, 14, row[3]).font = GREYI
    for c in range(1, 15): tr.cell(r, c).border = Border(bottom=thin)
tr.cell(R0 + 16, 1, "Avg ratings below the Premier League are Claude's estimates on the 1–99 scale (EA FC only rates the top of the pyramid). Shares and the value curve are proposals, nothing decided.").font = GREYI
tr.cell(R0 + 17, 1, "≈ Signings per season counts only fees; at the bottom players are free, so 0 there is expected.").font = GREYI
widths = [17, 28, 22, 10, 13, 15, 14, 15, 10, 15, 30, 14, 12, 55]
for i, w in enumerate(widths, 1): tr.column_dimensions[L(i)].width = w
tr.column_dimensions["C"].width = 22

wb.active = 1
wb.save("Sunday_League_economy_model.xlsx")
print("saved")
