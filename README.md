# Open Plain-Language Research Guides

**Live Site:** https://open-research-guides.vercel.app/

A public-interest, zero-affiliate collection of citation-backed guides, reproducible public-data analyses, and free interactive tools turning messy government datasets and peer-reviewed studies into clear everyday decisions.

### Project Principles
- **Step 0 Prior-Art Check:** Before building, we check what already exists and target real gaps where ordinary people face clunky government portals, paywalls, or SEO/affiliate spam.
- **Primary Data & Open Code:** Every data-driven guide includes the reproducible Python script pulling directly from official open APIs and bulk filings (WHO, CMS, FDIC, EIA, OSHA, NHTSA, Dept. of Ed, NOAA, U.S. Census F-33, openFDA, OpenFEMA, World Bank).
- **Honest About Traps & Uncertainty:** Every guide explicitly flags data artifacts, confounders, and what science or agencies still haven't settled.

---

## Published Guides & Interactive Tools (16)

1. **Guide #01 — Microplastics in Drinking Water:** [`guides/microplastics/`](./guides/microplastics/) + [Interactive Decision Calculator](./microplastics-calculator/) + [Markdown Guide](./microplastics-drinking-water-guide.md) + [1-Min Shareable Summary](./microplastics-shareable-summary.md)
2. **Guide #02 — Global Traffic Safety (158 Countries):** [`guides/traffic-safety/`](./guides/traffic-safety/) + [Python WHO Analysis](./data/traffic-safety/analyze_who_road_deaths.py)
3. **Guide #03 (Flagship #01) — U.S. Nursing Home Accountability Platform (14,686 Homes, 612 Chains & FY2024 Finances):** [`guides/nursing-homes/`](./guides/nursing-homes/) + [5-Dataset Python CMS Pipeline](./data/nursing-homes/analyze_cms_nursing_homes.py) + [Linked Dataset (.csv.gz)](./data/nursing-homes/cms-nursing-homes-linked.csv.gz) *(auto-refreshed monthly)*
4. **Guide #04 — Airline Reliability & Wheelchair Safety Scorecard (2024–2025 DOT/BTS):** [`guides/airline-safety/`](./guides/airline-safety/)
5. **Guide #05 — Food Recalls Decoded: Allergens vs. Severe Pathogens (29,634 openFDA Records):** [`guides/food-recalls/`](./guides/food-recalls/) + [Python openFDA Analysis](./data/food-recalls/analyze_openfda_food_recalls.py)
6. **Guide #06 — Financial Disputes, Credit-Repair Spam & P2P Fraud Reality (CFPB):** [`guides/financial-disputes/`](./guides/financial-disputes/)
7. **Guide #07 — Flood Insurance Payout Reality & Zone X Risk (5,000 OpenFEMA v3 Claims):** [`guides/flood-claims/`](./guides/flood-claims/) + [Python OpenFEMA v3 Analysis](./data/flood-claims/analyze_openfema_flood_claims.py)
8. **Guide #08 (Flagship #02) — U.S. Hospital Charity Care, Chargemaster Markups & Financial Reality (5,435 Hospitals):** [`guides/hospitals/`](./guides/hospitals/) + [4-Dataset Python CMS Pipeline](./data/hospitals/analyze_cms_hospitals.py) + [Linked Dataset (.csv.gz)](./data/hospitals/cms-hospitals-linked.csv.gz) *(auto-refreshed monthly)*
9. **Guide #09 (Flagship #03) — The U.S. Dialysis Duopoly & Clinic Accountability Platform (7,471 Clinics):** [`guides/dialysis/`](./guides/dialysis/) + [Python CMS Dialysis Pipeline](./data/dialysis/analyze_cms_dialysis.py) + [Linked Dataset (.csv.gz)](./data/dialysis/cms-dialysis-clinics-linked.csv.gz) *(auto-refreshed monthly)*
10. **Guide #10 (Flagship #04) — The Great Bank Deposit Skim: All 4,204 FDIC U.S. Banks (2021–2025 Call Reports):** [`guides/banks/`](./guides/banks/) + [Python FDIC Pipeline](./data/banks/analyze_fdic_banks.py) + [Linked Dataset (.csv.gz)](./data/banks/fdic-banks-2021-2025.csv.gz) *(auto-refreshed monthly)*
11. **Guide #11 (Flagship #05) — The Power Bill Divide: All 1,390 U.S. Electric Utilities (2020–2025 EIA Form 861):** [`guides/utilities/`](./guides/utilities/) + [Python EIA-861 Pipeline](./data/utilities/analyze_eia_utilities.py) + [Linked Dataset (.csv.gz)](./data/utilities/eia-861-utilities-2020-2025.csv.gz) *(auto-refreshed monthly)*
12. **Guide #12 (Flagship #06) — America's Workplace Injury & Amputation Reality (377,415 OSHA Workplaces & 5,744 Employers):** [`guides/workplace-safety/`](./guides/workplace-safety/) + [Python OSHA Pipeline](./data/workplace-safety/analyze_osha_safety.py) + [Linked Dataset (.csv.gz)](./data/workplace-safety/osha-employers-2025.csv.gz) *(auto-refreshed monthly)*
13. **Guide #13 (Flagship #07) — Used-Car & Automaker Safety Reality (4,056 Models, 13,785 NHTSA Recalls & 438,178 Complaints):** [`guides/auto-safety/`](./guides/auto-safety/) + [Python NHTSA Pipeline](./data/auto-safety/analyze_nhtsa_safety.py) + [Linked Dataset (.csv.gz)](./data/auto-safety/nhtsa-models-2010-2026.csv.gz) *(auto-refreshed monthly)*
14. **Guide #14 (Flagship #08) — The College Debt & Parent PLUS Reality (All 6,232 Active U.S. Colleges, 2026 Scorecard):** [`guides/colleges/`](./guides/colleges/) + [Python Scorecard Pipeline](./data/colleges/analyze_college_scorecard.py) + [Linked Dataset (.csv.gz)](./data/colleges/college-scorecard-2026.csv.gz) *(auto-refreshed monthly)*
15. **Guide #15 (Flagship #09) — America's Extreme Weather & Homebuyer Hazard Map (All 3,259 U.S. Counties, NOAA 2016–2026):** [`guides/weather-risk/`](./guides/weather-risk/) + [Python NOAA Pipeline](./data/weather-risk/analyze_noaa_storms.py) + [Linked Dataset (.csv.gz)](./data/weather-risk/noaa-counties-2016-2026.csv.gz) *(auto-refreshed monthly)*
16. **Guide #16 (Flagship #10) — Follow the School Dollar (All 13,251 U.S. Public School Districts, Census F-33 FY2019–FY2024):** [`guides/school-finances/`](./guides/school-finances/) + [Python F-33 Pipeline](./data/school-finances/analyze_school_finances.py) + [Linked Dataset (.csv.gz)](./data/school-finances/census-school-districts-2019-2024.csv.gz) *(auto-refreshed monthly)*

---

## Suggest a Topic or Spot an Error
Open an issue on GitHub with the topic gap or primary source/DOI:
https://github.com/tinhnhatpham/open-research-guides/issues

## License
Released for open public benefit under **CC BY 4.0** (guides) and **MIT** (interactive tools & analysis scripts).
