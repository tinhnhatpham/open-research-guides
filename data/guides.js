// Central catalog of all research guides and interactive tools.
// Add a new object here whenever you publish a new research project!
window.RESEARCH_GUIDES = [
  {
    id: "workplace-safety-osha",
    number: "Guide #12",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Labor & Workplace Safety",
    title: "America's Workplace Injury & Amputation Reality: 377,415 Workplaces & 5,744 Employers (OSHA 2025)",
    summary:
      "Deduplicated audit joining 2025 OSHA Form 300A filings (377,415 workplaces, 44.9M workers, 1.35M injuries, 780 deaths) with 11 years of Federal OSHA Severe Injury Reports (105,996 events; 86,518 hospitalizations; 27,978 amputations)—exposing 3,837 duplicate OSHA submissions, massive intra-industry gaps (Southwest 10.78 & American 8.92 vs. Delta 3.45 DART; FedEx 9.86 vs. UPS 6.51), and the Meatpacking Amputation Paradox.",
    highlights: [
      "Interactive Employer Risk Checker + searchable database of 5,744 employers, 267 industries & 1,000 injury hotspots",
      "NAICS-weighted peer industry benchmarks + 11-year Federal OSHA amputation & hospitalization counts",
      "Open bulk datasets (.csv.gz) & reproducible OSHA Python pipeline with duplicate/outlier forensics"
    ],
    guideUrl: "./guides/workplace-safety/",
    toolUrl: "./guides/workplace-safety/#checker",
    toolLabel: "Check an Employer",
    sourcesCount: "Live OSHA 300A (377k sites) + SIR (106k)"
  },
  {
    id: "electric-utility-divide",
    number: "Guide #11",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Energy & Cost of Living",
    title: "The Power Bill Divide: U.S. Electric Utility Rate Hikes, Blackouts & The Monopoly Premium (2020–2025)",
    summary:
      "Zero-affiliate EIA Form 861 audit of all 1,390 full-form U.S. residential electric utilities (140.8M households; 98.1% of U.S. homes): exposing the +31.0% 5-year rate surge (+$69.2B/yr), why Investor-Owned Utilities charge more than Public Power in 41 of 44 states ($33.54B/yr same-state excess), and Municipal utilities' 3.5× lower median blackout minutes (57.3 vs 205.7 SAIDI).",
    highlights: [
      "Interactive Power Bill & Monopoly Premium calculator + county-level search across all 1,390 U.S. utilities",
      "Same-state head-to-head showdowns (PG&E vs SMUD +$2,008/yr, SDG&E vs SMUD +$2,899/yr, TXU vs San Antonio +$752/yr)",
      "Open linked dataset (.csv.gz) & reproducible EIA-861 Python pipeline (Bundled vs Delivery safeguarded)"
    ],
    guideUrl: "./guides/utilities/",
    toolUrl: "./guides/utilities/#calculator",
    toolLabel: "Check Your Utility",
    sourcesCount: "Live EIA Form 861 (1,390 utilities)"
  },
  {
    id: "bank-deposit-skim",
    number: "Guide #10",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Consumer Finance & Banking",
    title: "The Great Bank Deposit Skim: All 4,204 FDIC U.S. Banks (2021–2025)",
    summary:
      "Zero-affiliate audit of all 4,204 active FDIC-insured U.S. banks ($18.06T domestic deposits, FY2021 & FY2025 Call Reports): exposing the $38B/yr Big 4 interest gap (1.71% weighted paid vs. 2.30% p75), $34.38B in deposit service fees (65% from 16 megabanks), 2021–2025 rate pass-through, and uninsured deposit exposure.",
    highlights: [
      "Interactive 'How Much Is YOUR Bank Costing You?' calculator across all 4,204 U.S. banks",
      "Reports BOTH blended & interest-bearing deposit rates plus exact ISERCHG service fees",
      "Open linked dataset (.csv.gz) & reproducible FDIC Call Report Python pipeline"
    ],
    guideUrl: "./guides/banks/",
    toolUrl: "./guides/banks/#calculator",
    toolLabel: "Check Your Bank",
    sourcesCount: "Live FDIC Call Reports (4,204 banks)"
  },
  {
    id: "dialysis-accountability",
    number: "Guide #09",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Healthcare & Kidney Care",
    title: "The U.S. Dialysis Duopoly & Clinic Accountability Platform (7,471 Clinics)",
    summary:
      "Flagship analysis of all 7,471 Medicare-certified U.S. dialysis clinics (CMS Dialysis Facility Compare through Dec 2025): exposing DaVita + Fresenius's 73.5% duopoly, the non-profit vs. for-profit kidney transplant waitlist gap (19.3% vs 16.3%; Kaiser 41.9%), 2,915 high-catheter clinics, and why small independent for-profits actually post the worst raw averages.",
    highlights: [
      "Instant lookup across all 7,471 clinics with mortality, hospitalizations, catheters, home dialysis & evening shifts",
      "Operator scorecard comparing DaVita, Fresenius, U.S. Renal Care, DCI, Kaiser & independents",
      "Open linked dataset (.csv.gz) + Care Compare & SRTR Transplant Center links"
    ],
    guideUrl: "./guides/dialysis/",
    toolUrl: "./guides/dialysis/#lookup",
    toolLabel: "Search All 7,471 Clinics",
    sourcesCount: "Live CMS Dialysis Dataset (7,471 clinics)"
  },
  {
    id: "hospital-charity-care",
    number: "Guide #08",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Healthcare & Billing",
    title: "U.S. Hospital Charity Care, Chargemaster Markups & Financial Reality (5,435 Hospitals)",
    summary:
      "Flagship 4-dataset CMS join uniting all 5,435 U.S. hospitals, 5,078 full-year FY2024 Form 2552-10 Cost Reports, and 147,029 PECOS owner rows—showing why 31.7% of tax-exempt hospitals spend <1% on charity care (408 while earning ≥5% net margins), median markups hit 3.74× (6.40× at for-profits), and how patients can invoke IRS Section 501(r).",
    highlights: [
      "Instant lookup across all 5,435 hospitals with FY2024 financials, markups & Care Compare / Dollar For links",
      "Interactive IRS Section 501(r) Charity Care Eligibility Checker + 50-state table",
      "Open linked dataset (.csv.gz) & reproducible 4-endpoint Python pipeline (catching the S-10 bad-debt charges trap)"
    ],
    guideUrl: "./guides/hospitals/",
    toolUrl: "./guides/hospitals/#lookup",
    toolLabel: "Search All 5,435 Hospitals",
    sourcesCount: "4 Live CMS Datasets (5,435 hospitals)"
  },
  {
    id: "nursing-home-reality",
    number: "Guide #03",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Elder Care & Health",
    title: "U.S. Nursing Home Accountability Platform (14,686 Homes, 612 Chains & FY2024 Finances)",
    summary:
      "Flagship 5-dataset CMS join uniting all 14,686 U.S. nursing homes, 612 corporate chains, 302,718 PECOS ownership rows, and 13,819 matched FY2024 Cost Reports—exposing broken PE/REIT disclosures (14,257 nameless org rows), Medicaid-controlled labor & margin gaps (+$25–$80/day more at non-profits), the TX/IN government-chain lease distortion, state inspection backlogs (AL 85.3%, VA 57.1%, DC 56.2%), and the 46.8% 5-star red-flag illusion.",
    highlights: [
      "Instant search across all 14,686 homes with full 5-dataset dossiers & Care Compare / ProPublica links",
      "612-chain scorecard + Medicaid-controlled FY2024 true operating margins & direct labor spending",
      "Open linked dataset (.csv.gz + JSON) & reproducible 5-endpoint Python pipeline"
    ],
    guideUrl: "./guides/nursing-homes/",
    toolUrl: "./guides/nursing-homes/#lookup",
    toolLabel: "Search All 14,686 Homes",
    sourcesCount: "5 Live CMS Datasets (14,686 homes & 612 chains)"
  },
  {
    id: "airline-wheelchair-scorecard",
    number: "Guide #04",
    status: "published",
    date: "November 2026",
    category: "Consumer Rights",
    title: "Airline Reliability & Wheelchair Safety Scorecard (2024–2025)",
    summary:
      "A zero-affiliate carrier scorecard built from mandatory U.S. DOT Air Travel Consumer Reports—ranking actual wheelchair/scooter mishandling rates (0.43% at Delta vs. 1.44% at JetBlue) and 2025 on-time performance.",
    highlights: [
      "Interactive sortable scorecard across 10 U.S. carriers (2024 vs. 2025 DOT logs)",
      "Separates marketing promises from legally reported mobility & delay failure rates",
      "Practical gate-check & DOT cash-refund rights checklist"
    ],
    guideUrl: "./guides/airline-safety/",
    toolUrl: "./guides/airline-safety/#rights",
    toolLabel: "Traveler Rights Checklist",
    sourcesCount: "U.S. DOT / BTS ATCR (2024–2025)"
  },
  {
    id: "food-recalls-decoded",
    number: "Guide #05",
    status: "published",
    date: "November 2026",
    category: "Everyday Science & Health",
    title: "Food Recalls Decoded: Allergens vs. Severe Pathogens (29,634 FDA Records)",
    summary:
      "Live openFDA Food Enforcement API analysis separating high-volume allergen labeling errors (24.7% of recalls) from high-lethality Class I Salmonella (88.4% Class I) and Listeria (79.2% Class I) outbreaks—vs. foreign material at just 0.7% Class I.",
    highlights: [
      "Interactive Volume vs. Class I Severity chart across 9,192 recent recalls (2021–2026)",
      "Exact allergen risk breakdown (Milk #1 by volume; Egg 65.6% Class I)",
      "Open Python script querying api.fda.gov directly"
    ],
    guideUrl: "./guides/food-recalls/",
    toolUrl: "./guides/food-recalls/#allergens",
    toolLabel: "Explore Allergen Risks",
    sourcesCount: "Live openFDA API (29,634 records)"
  },
  {
    id: "financial-disputes-cfpb",
    number: "Guide #06",
    status: "published",
    date: "November 2026",
    category: "Consumer Finance",
    title: "Financial Disputes, Credit-Repair Spam & P2P Fraud Reality",
    summary:
      "Built from CFPB Consumer Response Annual Reports (2024–2026): why credit bureaus get 85% of complaints yet pay <0.1% cash relief, how Regulation E splits Zelle hacks from scams, and how to avoid predatory 'credit sweep' schemes.",
    highlights: [
      "Interactive Dispute Reality Checker across 6 common money & fraud scenarios",
      "Documents the copy-paste 'credit washing' spam skewing raw CFPB volumes",
      "Clear, free federal dispute paths under Reg E, FCRA, FCBA & FDCPA"
    ],
    guideUrl: "./guides/financial-disputes/",
    toolUrl: "./guides/financial-disputes/#dispute-tool",
    toolLabel: "Open Dispute Checker",
    sourcesCount: "CFPB Annual Reports & Reg E / FCRA"
  },
  {
    id: "flood-insurance-payout-reality",
    number: "Guide #07",
    status: "published",
    date: "November 2026",
    category: "Housing & Climate Risk",
    title: "Flood Insurance Payout Reality & Zone X Risk (5,000 OpenFEMA Claims)",
    summary:
      "Live OpenFEMA NFIP v3 analysis showing why 28.7% of paid flood claims happen outside mapped high-risk zones (with higher median payouts than Zone A/V!), why 73.7% receive $0 for contents, and how the $250k cap catches homeowners off guard.",
    highlights: [
      "Interactive Homebuyer & Renter Flood Coverage Gap Checker",
      "State-by-state Zone X claim share (51.6% in TX, 46.2% in FL, 41.3% in LA)",
      "Open Python script pulling directly from OpenFEMA v3 NfipClaims"
    ],
    guideUrl: "./guides/flood-claims/",
    toolUrl: "./guides/flood-claims/#gap-checker",
    toolLabel: "Check Your Flood Gap",
    sourcesCount: "Live OpenFEMA API v3 (5,000 claims)"
  },
  {
    id: "microplastics-drinking-water",
    number: "Guide #01",
    status: "published",
    date: "November 2026",
    category: "Everyday Science & Health",
    title: "Microplastics in Drinking Water: What Actually Works (on Any Budget)",
    summary:
      "Separating peer-reviewed lab evidence from marketing hype across boiling, loose-carbon pitchers, membrane filters, solid carbon blocks, reverse osmosis, plastic kettles, and bottled water.",
    highlights: [
      "Compares real annual costs ($15–$200/yr vs. $300–$700+/yr for bottled water)",
      "Flags critical caveats: plastic kettle shedding & boiling concentrating lead/PFAS",
      "Verified against 2023–2025 primary papers & NSF/ANSI 401 standards"
    ],
    guideUrl: "./guides/microplastics/",
    toolUrl: "./microplastics-calculator/",
    toolLabel: "Open Decision Calculator",
    sourcesCount: "7 primary sources & standards"
  },
  {
    id: "global-traffic-safety",
    number: "Guide #02",
    status: "published",
    date: "November 2026",
    category: "Society & Public Data",
    title: "Global Traffic Safety: Which Countries Cut Road Deaths Fastest — and How?",
    summary:
      "A reproducible public-data investigation across 158 countries (WHO Global Health Observatory + ITF/IRTAD & NHTSA) examining how leaders like Norway, Japan, South Korea, Lithuania, Poland, and Oman slashed road deaths—and why the U.S. diverged.",
    highlights: [
      "Interactive 158-country trend chart & searchable data explorer (WHO 2010–2021)",
      "5 proven policies: Safe System engineering, 50/30 urban speed caps, cameras & crosswalk priority",
      "Documents WHO 2022–2023 extrapolation artifacts vs. NHTSA actuals"
    ],
    guideUrl: "./guides/traffic-safety/",
    toolUrl: "./guides/traffic-safety/#explorer",
    toolLabel: "Explore 158-Country Data",
    sourcesCount: "WHO GHO (158 countries) + ITF/IRTAD + NHTSA"
  }
];
