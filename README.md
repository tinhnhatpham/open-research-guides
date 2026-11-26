# Open Plain-Language Research Guides

**Live Site:** https://open-research-guides.vercel.app/

A public-interest, zero-affiliate collection of citation-backed guides, reproducible public-data analyses, and free interactive tools turning messy government datasets and peer-reviewed studies into clear everyday decisions.

### Project Principles
- **Step 0 Prior-Art Check:** Before building, we check what already exists and target real gaps where ordinary people face clunky government portals, paywalls, or SEO/affiliate spam.
- **Primary Data & Open Code:** Every data-driven guide includes the reproducible Python script pulling directly from official open APIs (WHO, CMS, openFDA, OpenFEMA, World Bank).
- **Honest About Traps & Uncertainty:** Every guide explicitly flags data artifacts, confounders, and what science or agencies still haven't settled.

---

## Published Guides & Interactive Tools (10)

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

---

## Suggest a Topic or Spot an Error
Open an issue on GitHub with the topic gap or primary source/DOI:
https://github.com/tinhnhatpham/open-research-guides/issues

## License
Released for open public benefit under **CC BY 4.0** (guides) and **MIT** (interactive tools & analysis scripts).
