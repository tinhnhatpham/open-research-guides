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
