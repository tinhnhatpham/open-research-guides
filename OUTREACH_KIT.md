# Share & Outreach Kit — Open Plain-Language Research Guides

*Ready-to-use, zero-hype templates designed to share your open datasets and public tools respectfully with communities, families, researchers, and local journalists. Edit freely to match your own voice!*

> **Golden Rule Before Posting Anywhere:** Never spam links. Lead with 2–3 concrete, verified findings and honest caveats, credit existing tools (Medicare Care Compare, ProPublica, The Oversight Report, Lown Institute, Dollar For), and ask for corrections or feedback!

---

## 1. Hacker News — "Show HN" Post

**Title (keep under 80 chars):**
`Show HN: Open lookup + linked CMS datasets for 14,686 nursing homes & 5,435 hospitals`

**Body (post as first comment right after submitting `https://open-research-guides.vercel.app/`):**
> I built a small, zero-affiliate, open-source public-interest site that joins live federal CMS datasets into fast client-side lookups and downloadable `.csv.gz` files, with reproducible Python scripts (MIT/CC BY 4.0) refreshed monthly via GitHub Actions.
>
> Two flagship datasets we linked and audited:
>
> **1. All 14,686 U.S. Nursing Homes (5 CMS datasets joined):**
> https://open-research-guides.vercel.app/guides/nursing-homes/
> Joins Provider Info (`4pq5-n9py`), Chain Performance Measures (612 chains), SNF Enrollments, SNF All Owners (302,718 PECOS rows), and FY2024 SNF Cost Reports (Form 2540-10). A few surprising catches in the raw federal data:
> - **Broken PE/REIT transparency:** 24.5% of Private Equity org rows and 19.9% of REIT org rows in CMS's own file have completely blank organization names, and public REIT Omega Healthcare Investors shows up under PE.
> - **TX/IN "Government Chain" distortion:** 286 of 353 "government chain" nursing homes are in TX (195) and IN (91) — overwhelmingly private corporate chains operating under hospital-district Medicaid pass-through leases (averaging 3.59 nurse hrs/day vs. 4.77 at government independents).
> - **True operating margin vs. total net margin:** Including contract labor + benefits, non-profits spend +$23 to +$78/day more on direct labor in every Medicaid bracket and run negative patient-care operating margins (-1.3% to -12.4%), subsidized by other income/endowments.
> - **Inspection backlog:** 955 homes (6.5%) are overdue >2 years (AL 85.3%, VA 57.1%, DC 56.2%), including 4 active 5-star AL homes uninspected since 2020.
>
> **2. All 5,435 U.S. Hospitals (4 CMS datasets joined):**
> https://open-research-guides.vercel.app/guides/hospitals/
> Joins Hospital General Info (`xubh-q36u`), FY2024 Hospital Cost Reports (Form 2552-10 Worksheet S-10), Enrollments, and 147,029 PECOS owner rows:
> - **Worksheet S-10 accounting trap:** In CMS's flat extract, `Cost of Charity Care` is cost-adjusted while `Total Bad Debt Expense` is reported at inflated chargemaster prices ($33.3B raw vs. $7.68B cost-adjusted at non-profits). We compute true cost-adjusted bad debt (`Cost of Uncompensated Care - Cost of Charity Care`).
> - Across 2,579 tax-exempt acute/CAH S-10 filers, median charity care is 1.53% of operating expenses (vs. 2.16% at for-profits); 31.7% spend <1%, and 408 spend <1% while earning ≥5% total net margins. Median chargemaster markup is 3.74× (6.40× at for-profits; 266 hospitals ≥10×).
>
> Existing tools like Medicare Care Compare, ProPublica Nursing Home Inspect, The Oversight Report, Lown Institute, and Dollar For do great work — we deep-link directly to Care Compare, ProPublica (`h-{CCN}`), and Dollar For while publishing the joined FY2024 Cost Report `.csv.gz` files and Python scripts openly here: https://github.com/tinhnhatpham/open-research-guides
>
> Would love feedback, bug reports, or pointers to methodological nuances we should tighten!

---

## 2. Reddit — `r/datasets` (Open Civic Data Release)

**Title:**
`[OC] Two open, monthly-refreshed linked CMS datasets (.csv.gz + Python): all 14,686 U.S. nursing homes (5 APIs joined) and 5,435 U.S. hospitals (4 APIs joined)`

**Body:**
> Sharing two clean, reproducible healthcare datasets built straight from live federal CMS APIs (no API keys required, CC BY 4.0 / MIT, refreshed monthly via GitHub Actions):
>
> 1. **U.S. Nursing Homes (`14,686` rows × `49` cols):** Joins CMS Provider Info (`4pq5-n9py`), 612 Corporate Chains, PECOS Enrollments & All Owners (302,718 rows), and FY2024 SNF Cost Reports (Form 2540-10).
>    - Direct `.csv.gz`: `https://open-research-guides.vercel.app/data/nursing-homes/cms-nursing-homes-linked.csv.gz`
>    - Web explorer: `https://open-research-guides.vercel.app/guides/nursing-homes/`
> 2. **U.S. Hospitals (`5,435` rows × `32` cols):** Joins CMS Hospital General Info (`xubh-q36u`), FY2024 Hospital Cost Reports (Worksheet S-10 charity care, cost-adjusted bad debt, chargemaster markup, operating & total net margins), and PECOS Owners.
>    - Direct `.csv.gz`: `https://open-research-guides.vercel.app/data/hospitals/cms-hospitals-linked.csv.gz`
>    - Web explorer: `https://open-research-guides.vercel.app/guides/hospitals/`
>
> Full reproducible Python scripts: `https://github.com/tinhnhatpham/open-research-guides`
>
> Notable data quirks handled in the scripts (in case you use CMS HCRIS/PECOS yourself):
> - Blank `Total Days Title XIX` in SNF Cost Reports = 0 Medicaid days (Medicare/private-pay SNFs — don't drop nulls!).
> - Use `Less Total Operating Expense` (Worksheet G-3), NOT `Total Costs` in CMS flat extracts.
> - Hospital `Total Bad Debt Expense` is reported at billed charges, NOT cost — compute `Cost of Uncompensated Care - Cost of Charity Care` for apples-to-apples cost-adjusted bad debt.

---

## 3. Family & Patient Help Communities (`r/AgingParents`, `r/HospitalBills`, Neighborhood Groups)

### For Families Choosing a Nursing Home (`r/AgingParents` — check subreddit rules before posting links!)
> When comparing nursing homes on Medicare's website, it's easy to stop at the 5-star badge. I pulled the latest federal CMS payroll-verified staffing logs and inspection records across all 14,686 U.S. nursing homes and noticed a few things worth checking before signing paperwork:
> - **Visit on a weekend:** Nationally, Registered Nurse hours drop **30.4%** on weekends (nearly a 38% drop from Monday–Friday). Even among **5-star** homes, 23.7% cut weekend total nursing by 15%+.
> - **Check inspection dates:** 955 homes nationwide haven't had a standard health inspection in over 2 years (85% in Alabama, 57% in Virginia, 56% in DC).
> - **Check turnover & ownership:** Non-profits average ~44 more minutes of nursing care per resident every day than for-profits, though there are great and terrible homes in both groups.
>
> If it helps anyone researching facilities, I put together a free, zero-ad search tool for all 14,686 homes (with direct links to Medicare Care Compare and ProPublica's inspection reports): https://open-research-guides.vercel.app/guides/nursing-homes/#lookup

### For Patients With Overwhelming Hospital Bills (`r/HospitalBills` / Personal Finance)
> Quick reminder that saves families thousands: under federal law (**IRS Section 501(r)**), every tax-exempt non-profit hospital must have a written **Financial Assistance Policy (charity care)** and pause collections while your application is reviewed—and you have at least 240 days after the first post-discharge bill to apply.
>
> Many patients never get told this (CMS FY2024 cost reports show 31.7% of non-profit hospitals spend under 1% of expenses on charity care, and median hospital list markups are 3.74× actual cost—up to 6.40× at for-profits).
>
> You can check whether your exact hospital is non-profit, see its FY2024 charity care % and markup, and estimate your Federal Poverty Level eligibility for free here (no sign-up, zero ads, links straight to Dollar For): https://open-research-guides.vercel.app/guides/hospitals/

---

## 4. Short Data-Tip Email for Local Health / Investigative Journalists & State Ombudsman Offices

*Best states to target first based on our strongest localized findings: **Alabama, Virginia, DC** (inspection backlog), **Texas & Indiana** (286 private-chain "government chain" leases), or local beat reporters covering high-margin / low-charity flagship hospitals.*

**Subject:** Free open CMS dataset: [State] nursing home inspection backlogs / hospital charity care (FY2024)

> Hi [Name],
>
> I follow your reporting on [healthcare / elder care in State] and wanted to share a free, open dataset I compiled from live federal CMS APIs in case it's useful for a future story.
>
> Using CMS Provider Info (`4pq5-n9py`), PECOS Ownership files, and FY2024 Medicare Cost Reports, a couple of [State]-specific numbers jumped out:
> - **[Pick 1 exact local stat — e.g., for AL:]** 85.3% of Alabama nursing homes (191 of 224) have gone more than 2 years without a standard federal health inspection, including 4 active 5-star facilities last inspected in 2020 (`015392`, `015426`, `015089`, `015460`).
> - **[Or for TX/IN:]** [195 in TX / 91 in IN] facilities classified as "government" nursing homes are actually operated by private multi-state chains under county/hospital-district leases, averaging 71 fewer minutes of nursing care per resident/day than genuine government independents.
> - **[Or for Hospitals:]** [Hospital Name] reported [X]% of operating expenses in FY2024 Worksheet S-10 charity care alongside a [Y]% total net margin and [Z]× chargemaster markup.
>
> Everything is free, open-source, and reproducible (including the raw joined `.csv.gz` and Python scripts fetching directly from `data.cms.gov`):
> - Nursing Homes (14,686 homes): https://open-research-guides.vercel.app/guides/nursing-homes/
> - Hospitals (5,435 hospitals): https://open-research-guides.vercel.app/guides/hospitals/
> - GitHub & Python code: https://github.com/tinhnhatpham/open-research-guides
>
> Happy to send a state-filtered CSV if that saves you time — no credit or reply needed.
>
> Best,
> [Your Name]

---

## 5. Personal Finance & Energy Communities (`r/personalfinance`, `r/Bogleheads`, `r/dataisbeautiful`, Hacker News)

### A. The Great Bank Deposit Skim — All 4,204 FDIC Banks (`r/personalfinance` / `r/Bogleheads` / HN)

**Title:**
`I audited all 4,204 FDIC-insured U.S. banks (2021 vs 2025 Call Reports): The Big 4 hold 35.7% of deposits, paid 1.71% weighted interest, and extracted 47% of all U.S. deposit fees ($16.2B)`

**Body:**
> Most "best savings account" lists are affiliate ads for ~15 sponsor banks. I pulled the official FY2021 and FY2025 FDIC Call Reports across all 4,204 active U.S. banks ($18.06T in domestic deposits) to see what every bank *actually* paid depositors vs. kept after Fed rate hikes—zero ads, zero affiliates, open Python script + `.csv.gz`.
>
> A few findings from the raw federal filings:
> - **The Big 4 interest gap:** JPMorgan ($2.17T), Bank of America ($1.96T), Wells Fargo ($1.48T), and Citibank ($832B) hold 35.7% of U.S. domestic deposits and paid a weighted **1.71%** in FY2025 (JPM 1.60%, BofA 1.56%, WF 1.44%, Citi 2.80%). Just matching the 75th-percentile bank (2.30%) equals **$38.0B/yr** in extra interest—and >$100B/yr vs. zero-fee large FDIC online banks (Synchrony 4.10%, Sallie Mae 3.92%, Barclays 3.84%, Goldman Sachs Bank USA 3.49%).
> - **Rate pass-through ("Deposit Beta"):** From 2021→2025, Megabanks ($250B+) passed through a median **68.9%** of asset yield gains (JPM 49.2%, WF 53.0%) vs. **85.7%** at Mid-Size banks ($1B–$10B).
> - **Deposit fee concentration (`ISERCHG`):** U.S. banks collected **$34.38B** in deposit account service charges in FY2025; the Big 4 alone took **$16.16B (47.0%)** while top high-yield online banks reported **$0.0M**.
> - **Methodological note:** We report *both* blended domestic deposit rate (`EDEPDOM/DEPDOM`) and interest-bearing-only rate (`EDEPDOM/DEPIDOM`) so free checking balances don't skew comparisons.
>
> Interactive lookup + personal savings cost calculator + `.csv.gz`: https://open-research-guides.vercel.app/guides/banks/

### B. The Power Bill Divide — All 1,390 U.S. Electric Utilities (`r/personalfinance` / `r/energy` / Local CA, NY, MA, TX, FL Subreddits)

**Title:**
`[OC] I joined 2020–2025 EIA Form 861 filings across 1,390 U.S. electric utilities (140.8M homes): For-profit IOUs charge more than Public Power in 41 of 44 states ($33.5B/yr gap) with 3.5× more blackout minutes`

**Body:**
> Electricity bills are one of the fastest-rising household costs in America, jumping **+31.0%** nationwide from 2020 to 2025 (13.15¢ → 17.23¢/kWh, adding **+$69.2B/yr** to residential bills). I built a free, ad-free lookup tool + open `.csv.gz` joining EIA Form 861 sales, reliability (`SAIDI`/`SAIFI`), and county service territories across 1,390 full-form U.S. utilities (98.1% of U.S. households).
>
> Key numbers from the official 2020–2025 EIA filings:
> - **Same-state Investor-Owned vs. Public Power gap:** In **41 of 44 states (93.2%)** with both major IOUs and Public Power utilities, IOUs charge higher residential rates—totaling **$33.54B/yr** in higher same-state bills (e.g., PG&E 37.52¢ & 273 min blackouts vs. SMUD 18.93¢ & 50 min in CA; SDG&E 45.77¢ vs. SMUD 18.93¢; Duke FL 18.36¢ vs. JEA 13.84¢; TXU 19.36¢ vs. San Antonio CPS 12.40¢).
> - **14 of the 15 steepest large-utility rate hikes (≥100k homes)** since 2020 were Investor-Owned Utilities (led by NYSEG +96.6%, SDG&E +79.4%, Pepco DC +76.2%, RG&E +74.6%, SCE +72.8%, Tampa Electric +71.9%, Ameren IL +71.5%, BGE +66.7%).
> - **Reliability:** 2025 median SAIDI was **57.3 min/yr** at Municipal utilities (37.5 min routine non-storm) vs. **205.7 min/yr** at IOUs (109.0 min routine) and **232.4 min** at Rural Co-ops (sparse rural lines).
> - **Honest caveats included:** Legacy public hydro allocations (NYPA/BPA), wildfire-prone rural transmission mileage, urban vs. rural line density, and strict separation of `Bundled` vs. `Delivery`-only deregulated rates.
>
> Search by utility name or U.S. county + open `.csv.gz`: https://open-research-guides.vercel.app/guides/utilities/

### C. America's Workplace Injury & Amputation Reality — 377,415 OSHA Workplaces (`r/datasets` / `r/workreform` / Labor Journalists / HN)

**Title:**
`[OC] I deduplicated 400,288 OSHA 2025 workplace injury filings (catching 3,837 exact duplicates) and joined them with 105,996 Severe Injury Reports (27,978 amputations)`

**Body:**
> OSHA publishes establishment-level 2025 Form 300A injury logs (`400,288` rows) and 2015–2025 Severe Injury Reports (`105,996` hospitalizations & amputations) as separate raw CSVs with fragmented corporate LLC names—and thousands of unflagged duplicate submissions (e.g., Costco submitted 1,513 rows for 731 U.S. locations; H-E-B submitted 894 rows for 459 locations with extra spaces).
>
> After removing 3,837 exact duplicate filings and 19,036 clerical hours/size outliers (leaving 377,415 clean workplaces covering 44.9M workers, 1.35M injuries, and 780 deaths), a few stark findings stood out:
> - **Same-industry corporate gaps:** Southwest Airlines (`10.78` DART) and American Airlines (`8.92`) post 2.5×–3.1× higher serious injury rates than Delta (`3.45`) and United (`3.99`). FedEx (`9.86` DART, 1.41× peer) vs. UPS (`6.51`, 0.89× peer). Costco (`5.19` DART, 1.80× peer) vs. Walmart (`2.53`) and Target (`2.88`). Amazon's `4.57` DART represents 92% of all its recordable injuries.
> - **The Meatpacking Amputation Paradox:** Tyson Foods (`3.35` TCR), JBS/Pilgrim's Pride (`3.21`), and Smithfield (`2.48`) post below-average Form 300A rates yet account for **318 worker amputations** in Federal OSHA jurisdictions alone.
> - **Honest caveat:** Form 300A covers all 50 states, while Federal OSHA Severe Injury Reports cover the 29 Federal OSHA jurisdictions (21 State-Plan states report separately).
>
> Interactive lookup across 5,744 employers, 267 industries & 1,000 injury hotspots + open `.csv.gz`: https://open-research-guides.vercel.app/guides/workplace-safety/

### D. Used-Car & Automaker Safety Reality — 4,056 Models & 438,178 NHTSA Complaints (`r/whatcarshouldibuy`, `r/cars`, `r/personalfinance`, `r/datasets`)

**Title:**
`[OC] I deduplicated 637,333 NHTSA owner complaints (2020–2026) and joined them with 13,785 post-2010 recalls into a free Used-Car Model-Year Safety Checker (4,056 vehicles)`

**Body:**
> When shopping for a used car, NHTSA's site only checks one VIN or model-year at a time, and its raw complaint CSVs repeat the same `ODINO` ID whenever an owner lists multiple failing parts (overcounting fires by +63% and deaths by +86%). I cleaned out **199,155 duplicate component rows** and joined all 13,785 post-2010 recalls (including NHTSA's 307 Do-Not-Drive & Park-Outside fire advisories) with 438,178 unique 2020–2026 owner complaints.
>
> A few findings straight from the federal filings:
> - **Hyundai & Kia dominate U.S. vehicle fires:** Kia (`44.2` fires per 1,000 complaints; 1,100 fires) and Hyundai (`30.6/1k`; 876 fires) account for **9 of the Top 10 most fire-prone model-years** in America and 35 combined Park-Outside fire advisories.
> - **Tesla cuts through both myths:** One of the *lowest* fire rates (`5.8/1k` complaints), yet `106.4` crash complaints per 1,000 (`1,383` crashes)—3×–4× the crash share of Ford (`26.0/1k`), Chevy (`34.2/1k`), or Honda (`36.2/1k`).
> - **Ford leads total recall volume by >2×:** 657 vehicle recall campaigns (2016–2026) including 77 ODI-forced probes and 18 Do-Not-Drive advisories (vs. Chevy 270, Toyota 203, Honda 180).
>
> Compare any car's MY 2010–2026 years side-by-side (zero ads/affiliates) + open `.csv.gz`: https://open-research-guides.vercel.app/guides/auto-safety/

### E. The College Debt & Parent PLUS Reality — All 6,232 Active U.S. Colleges (`r/ApplyingToCollege`, `r/StudentLoans`, `r/personalfinance`)

**Title:**
`[OC] I analyzed the June 2026 U.S. College Scorecard across all 6,232 active colleges: 914 leave most students earning less than a HS grad (85% For-Profit), and 392 carry ≥$40k in hidden Parent PLUS debt`

**Body:**
> Most college rankings reward prestige and ad budgets, while the official federal Scorecard hides Parent PLUS loan medians inside buried tabs and only shows 10 schools per page. I built a free, zero-affiliate lookup + income-bracket ROI calculator covering all **6,232 active U.S. colleges (14.46M undergrads)** from the June 2026 Dept. of Education release.
>
> Key stratified 4-year findings:
> - **Public vs. Private Non-Profit 4-Year:** Public universities (`$14,647/yr` median net price) actually beat Private Non-Profits (`$22,585/yr`) on median 10-year earnings (`$54,670` vs `$54,056`) while carrying `$12,660` less Parent PLUS debt (`$18.7k` vs `$31.3k`).
> - **The Parent PLUS Trap:** 392 schools carry `≥$40k` in median Parent PLUS debt—peaking above `$100k` at Ringling (`$114k`), SCAD (`$109k`), Berklee (`$108k`), Spelman (`$106k`), and Pratt (`$100k`) *on top of* student loans.
> - **For-Profit 4-Year Reality:** `$30,716/yr` median net price (2.1× Public), `33.7%` graduation rate, `$40,092` 10-yr earnings, and only `10%` making 2-year loan principal progress. Nationwide, 781 of the 914 schools failing the High-School Earnings Test (`85.4%`) are For-Profit.
>
> Income-bracket ROI calculator + all 6,232 colleges + `.csv.gz`: https://open-research-guides.vercel.app/guides/colleges/

### F. America's Extreme Weather & Homebuyer Hazard Map — All 3,259 U.S. Counties (`r/RealEstate`, `r/FirstTimeHomeBuyer`, `r/datasets`)

**Title:**
`[OC] I mapped 687,227 observed NOAA Storm Events (2016–2026) across all 3,259 U.S. counties into a free, zero-paywall Homebuyer Hazard Lookup`

**Body:**
> Most homebuyer climate-risk scores are paywalled, while NOAA's Storm Events portal only runs single-county dropdown queries and splits County FIPS events (hail/tornado/flood) from NWS Forecast Zones (hurricanes/wildfires/heat). I compiled all 11 latest NOAA annual files (2016–Nov 2026; 687,227 events, $245.8B NWS property damage, 10,485 deaths) into a fast lookup across 3,259 counties + open `.csv.gz`.
>
> Highlights:
> - Severe events jumped **+15.3%** in 2021–2025 vs. 2016–2020 (`291k → 336k`).
> - Property losses are dominated by Floods (`$96.2B`), Hurricanes (`$82.1B`), Wildfires (`$31.8B`), Tornadoes (`$13.3B`), and Hail (`$11.8B`—Colorado's #1 hazard!), while low-property-damage Extreme Heat & Cold drive the largest share of U.S. weather deaths.
>
> Search any U.S. county + open `.csv.gz`: https://open-research-guides.vercel.app/guides/weather-risk/

### G. Follow the School Dollar — All 13,251 U.S. Public School Districts (`r/Teachers`, `r/education`, `r/datasets`, Local School Board Parents)

**Title:**
`[OC] I joined FY2019 & FY2024 Census F-33 finances across all 13,251 U.S. public school districts (46.4M kids, $990B): 1.65M-student enrollment cliff, 3.1× state funding gap, and classroom vs. admin share`

**Body:**
> Commercial school sites rate districts with opaque 1–10 scores that mostly mirror neighborhood home prices, without showing where property-tax dollars actually go. I parsed the official FY2019 and FY2024 U.S. Census F-33 finance files across all **13,251 operating K–12 public school districts** (`46.37M` students, `$990.2B` revenue, `$570.2B` debt).
>
> Key numbers:
> - **Post-COVID Enrollment Cliff:** `-1.65M` students (`-3.4%`) nationwide from FY2019 to FY2024—with major districts like Rochester NY (`-22.0%`), Montebello CA (`-21.4%`), Santa Ana CA (`-19.0%`), Minneapolis MN (`-18.3%`), Indianapolis (`-17.2%`), and Fort Worth TX (`-15.9%`) seeing per-pupil operating costs jump `+35%` to `+73%` over the same span.
> - **3.1× Interstate Spending Gap:** New York averages `$34,607/pupil` vs. Idaho `$11,119/pupil` (U.S. average `$17,846`; `59.2%` classroom instruction vs. `7.2%` central/school admin).
>
> Look up your exact district + open `.csv.gz`: https://open-research-guides.vercel.app/guides/school-finances/

### H. America's Aging High-Hazard Dams — All 14,266 Life-Safety Dams (`r/civilengineering`, `r/urbanplanning`, Local Reporters in NC/TX/GA/SC/PA/MS)

**Title:**
`[OC] I audited all 62,569 public U.S. dams (Nov 2026 USACE NID): 2,447 High-Hazard dams are rated Poor/Unsatisfactory, 3,090 lack an Emergency Action Plan, and 629 fail both`

**Body:**
> Using the U.S. Army Corps of Engineers' November 20, 2026 National Inventory of Dams release (`62,569` publicly listed dams; `14,266` High-Hazard Potential dams where failure means probable loss of life), I built a free county/city lookup + open `.csv.gz`.
>
> Findings:
> - **2,447 High-Hazard dams (`17.2%`)** are rated Poor (`2,013`) or Unsatisfactory (`434`)—led by NC (`230`), TX (`179`, including `101` Unsatisfactory), GA (`173`), SC (`151`), PA (`136`), MS (`134`), NM (`131`), and OH (`129`).
> - **3,090 High-Hazard dams (`21.7%`)** lack an Emergency Action Plan, including **629 dams** that are *both* Poor/Unsatisfactory and missing an EAP.
> - **Private-owner gap:** `34.8%` of private High-Hazard dams lack an EAP (accounting for 70.5% of all missing EAPs nationwide) vs. `4.4%` at Federal dams. Median High-Hazard dam age is **64 years** (`79.7%` ≥50 yrs).
>
> Search by county, nearest city, or river + open `.csv.gz`: https://open-research-guides.vercel.app/guides/dams/

### I. The Credit Union Reality Check — All 4,363 U.S. Credit Unions vs. Big Banks (`r/personalfinance`, `r/Bogleheads`, `r/CreditUnions`)

**Title:**
`[OC] I audited all 4,363 U.S. credit unions (NCUA 5300 Call Reports) against all 4,204 FDIC banks: Credit unions actually pay LESS on savings than overall banks—but crush them on auto loans (5.5%), credit cards (11.6%), and deposit safety (3.7% uninsured)`

**Body:**
> Everyone tells you "ditch Big Banks and switch to a Credit Union." I pulled the Q4 2021 and Q4 2025 NCUA 5300 Call Reports across all **4,363 U.S. credit unions** (`145.9M` members, `$2.46T` assets) and benchmarked them directly against all **4,204 FDIC banks** (`$18.06T` deposits).
>
> What the audited federal filings actually show:
> - **Savings rate myth:** Credit unions paid `1.86%` weighted (`1.24%` median; `46.9%` pass-through)—beating Big 4 Megabanks (`1.71%`), yet *below* overall FDIC banks (`1.99%` wavg, `1.85%` median) and far below top zero-fee online FDIC banks (`3.5%–4.1%`). Small CUs (`<$100M`) paid just `1.14%`.
> - **Where CUs genuinely dominate:** Median Credit Card APR is **11.57%**, New Auto APR is **5.50%** (Navy Federal `4.59%`, SchoolsFirst `4.74%`), and median uninsured deposits are just **3.7%** vs **45.2%** at Megabanks.
> - **Fee watch:** CUs collected `$10.14B` in member fees (`$69.50/member` avg), ranging from `$18.40/member` at BECU and `$20.70` at State Employees' CU (NC) up to `$89.60` avg at mid-size CUs.
>
> Search all 4,363 credit unions + open `.csv.gz`: https://open-research-guides.vercel.app/guides/credit-unions/

### J. The 2026 U.S. Home Insurance Crisis & Home-Hardening Reality (`r/homeowners`, `r/RealEstate`, `r/personalfinance`)

**Title:**
`[OC] Why home insurance still hurts after 2026 rate hikes cooled (+1.8%): Roof ACV schedules (new March 2026 FHFA rule), 2%–5% wind/hail deductibles, and a free "Should I File This Claim?" calculator`

**Body:**
> Headlines note that U.S. homeowners insurers just posted their best underwriting year in over a decade (`87.9` combined ratio in 2025) and approved rate hikes cooled to `+1.8%` through July 2026. Yet homeowners are quietly absorbing far more out-of-pocket risk than five years ago.
>
> Key verified takeaways from primary Treasury FIO, NAIC, S&P GMI, Swiss Re, FHFA, IBHS, and State DOI data:
> - **The Double Trap:** On March 18, 2026, FHFA allowed Fannie Mae and Freddie Mac mortgages to accept **Actual Cash Value (ACV)** roof policies. Pair a typical 15-year-old roof schedule (`30%` payout) with a `2%` Coverage A wind/hail deductible (`$9,000` on a `$450,000` policy), and a `$20,000` or even `$30,000` hail-destroyed roof yields a **$0 insurer payout** while logging a closed claim on LexisNexis C.L.U.E. for 7 years.
> - **FAIR Plan Divergence:** California's FAIR Plan reached `$773B` exposure across ~700,000 policies (with 50% of its `$1B` assessment recoupable statewide, upheld June 30, 2026), while Florida Citizens shrank ~80% (`1.41M` → `~254k–278k`) after 2022–2023 tort reforms.
> - **Hardening Science & Honest Limits:** IBHS FORTIFIED Roof cut Hurricane Sally claim frequency `66%–73%` across 40,000+ Alabama homes, and states like AL, FL, LA, SC, NC, and OK offer up to `$10,000` grants—yet windows close in minutes or run lotteries, discounts apply only to the wind/wildfire slice, and no statute blocks non-renewal.
>
> Free interactive Claim & Roof ACV Shock Calculator + 18-state grants & credit-ban directory (zero ads/affiliates): https://open-research-guides.vercel.app/guides/home-insurance/

### K. 3D Model Motion: Skeleton Rigging, Handgrip Mechanics & Physics RL (`r/gamedev`, `r/blender`, `r/unrealengine`, `r/robotics`, `r/MachineLearning`)

**Title:**
`[OC] Interactive 3D Skeleton IK, 21-Keypoint Handgrip & LBS/DQS Skinning Lab + 2022–2026 synthesis of Meta MHR, UniRig, UE5 Motion Matching, InterMimic & mocap stacks`

**Body:**
> I synthesized 2022–2026 primary literature and official engine docs across the three layers of 3D character motion—skeleton/rigging, character locomotion/physics, and dexterous handgrip/HOI—and built a zero-dependency interactive 3D browser lab so anyone can inspect the actual failure modes:
> - **Skeleton & IK mode:** Toggle Foot-Lock IK vs. raw kinematic foot skating and drag an analytical 2-bone right-arm IK target.
> - **21-Keypoint Handgrip mode:** Switch Feix GRASP presets (Power Cylinder, Precision Pinch, Tripod Tool, Lateral Key), twist forearm pronation/supination, and simulate mesh interpenetration, floating air-gaps, and 4-finger stylized retarget loss.
> - **Skinning Twist mode:** Twist a 3D forearm up to 180° to compare single-bone LBS candy-wrapper collapse vs. Dual Quaternion Skinning vs. UE5-style twist bones.
>
> Includes full reference tables (SMPL-X vs. Meta's Apache-2.0 MHR, UniRig/MagicArticulate/Make-It-Animatable, DART/CLoSD/HY-Motion 1.0, GigaHands/OakInk2/HIMO), a budget-tiered 2026 mocap/glove/video-AI directory, and a **100% browser-side `.glb`/`.vrm`/`.gltf`/`.bvh` Rig & Motion QA Linter** (zero uploads, detects foot skating, >4-weight bloat, missing twist bones, Euler flips, and exports cleaned `.bvh` + JSON QA reports):
> - Interactive 3D Lab & Research: https://open-research-guides.vercel.app/guides/3d-model-motion/
> - Browser GLB / BVH QA Linter: https://open-research-guides.vercel.app/tools/rig-motion-linter/
> - Open MIT Production Kit (Blender 4.x Feix Handgrip Rig Script, Verified 58-Joint `.glb`, Local Video-to-3D Foot-Lock Python Pipeline): https://github.com/tinhnhatpham/open-research-guides/tree/main/data/3d-model-motion
