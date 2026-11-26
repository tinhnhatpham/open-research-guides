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
