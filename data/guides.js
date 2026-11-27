// Central catalog of all research guides and interactive tools.
// Add a new object here whenever you publish a new research project.
window.RESEARCH_GUIDES = [
  {
    id: "home-insurance-crisis-2026",
    number: "Guide 19",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Climate, Housing & Insurance Risk",
    title: "The 2026 U.S. Home Insurance Crisis and Home-Hardening Reality",
    summary:
      "Multi-agent primary-source audit (Treasury FIO, NAIC, S&P GMI, Swiss Re, FHFA, IBHS, and State DOIs): why bills still hurt even after insurers posted an 87.9 combined ratio in 2025 and rate hikes cooled to +1.8% in 2026, exposing the March 2026 FHFA roof ACV shift, 2% to 5% wind/hail deductibles, CA FAIR Plan's $773B surge vs. FL Citizens' 80% drop, and 18-state hardening grants.",
    highlights: [
      "Interactive 'Should I File This Claim?' & Roof ACV Shock Calculator modeling depreciation, % deductibles, and 4-year C.L.U.E. surcharges",
      "Searchable 18-state directory of $4,000 to $10,000 roof grants, mandatory discounts, and credit-score bans",
      "Verified consumer playbook for challenging faulty AI aerial-imagery non-renewals and FCRA C.L.U.E. errors"
    ],
    guideUrl: "./guides/home-insurance/",
    toolUrl: "./guides/home-insurance/#calculator",
    toolLabel: "Open Claim Calculator",
    sourcesCount: "Treasury FIO, NAIC, FHFA, Swiss Re & IBHS"
  },
  {
    id: "credit-unions-ncua",
    number: "Guide 18",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Consumer Finance & Banking",
    title: "The Credit Union Reality Check: All 4,363 U.S. Credit Unions vs. Big Banks (NCUA 2021–2025)",
    summary:
      "Zero-affiliate NCUA 5300 Call Report audit of all 4,363 federally insured U.S. credit unions (145.9M members, $2.46T assets) vs. 4,204 FDIC banks: busting the savings-yield myth (1.86% wavg / 1.24% med vs. FDIC 1.99%) while proving where CUs truly beat banks: auto loans (5.50%), credit cards (11.57% med APR), and deposit safety (3.7% med uninsured vs. 45.2% Megabanks).",
    highlights: [
      "Direct Head-to-Head Scorecard: 4,363 Credit Unions vs. 4,204 FDIC Banks vs. Big 4 Megabanks",
      "Instant lookup across all 4,363 CUs with savings yield, auto and card APRs, fee/member, and official NCUA links",
      "Open bulk dataset (.csv.gz) and reproducible NCUA 5300 Python pipeline"
    ],
    guideUrl: "./guides/credit-unions/",
    toolUrl: "./guides/credit-unions/#lookup",
    toolLabel: "Check Your Credit Union",
    sourcesCount: "Live NCUA 5300 (4,363 credit unions)"
  },
  {
    id: "aging-dams-usace",
    number: "Guide 17",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Public Infrastructure & Safety",
    title: "America's Aging High-Hazard Dams: All 14,266 Life-Safety Dams (USACE NID Nov 2026)",
    summary:
      "Live audit of all 62,569 publicly listed U.S. dams and all 14,266 High-Hazard Potential dams (U.S. Army Corps of Engineers NID, Nov 2026): exposing 2,447 rated Poor or Unsatisfactory (17.2%), 3,090 lacking an Emergency Action Plan (629 with both failures), a 64-year median age, and private owners' 34.8% missing-EAP rate vs. 4.4% at Federal dams.",
    highlights: [
      "Instant lookup across all 14,266 U.S. High-Hazard dams by county, nearest city, river, or owner",
      "Direct links to official USACE NID records plus 52-state and ownership preparedness scorecards",
      "Open bulk dataset (.csv.gz) and reproducible USACE NID Python pipeline"
    ],
    guideUrl: "./guides/dams/",
    toolUrl: "./guides/dams/#lookup",
    toolLabel: "Check Dams Near You",
    sourcesCount: "Live USACE NID (62,569 dams; 14,266 High-Hazard)"
  },
  {
    id: "school-district-finances",
    number: "Guide 16",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Public Education & Taxes",
    title: "Follow the School Dollar: All 13,251 U.S. Public School Districts (FY2019–FY2024)",
    summary:
      "Zero-ad Census F-33 audit of all 13,251 operating U.S. public school districts (46.37M students, $990.2B annual revenue, $570.2B debt): exposing the 1.65M-student post-COVID enrollment cliff (-3.4%; big urban drops up to -22%), the 3.1x interstate spending gap ($34,607 NY vs. $11,119 ID), and exact classroom instruction vs. admin share for every district.",
    highlights: [
      "Instant lookup across all 13,251 U.S. school districts with FY2019 to FY2024 spending and enrollment dossiers",
      "51-state within-state inequality scorecard (90th vs. 10th percentile district funding gap)",
      "Open bulk dataset (.csv.gz) and reproducible Census F-33 Python pipeline (zero API keys)"
    ],
    guideUrl: "./guides/school-finances/",
    toolUrl: "./guides/school-finances/#lookup",
    toolLabel: "Look Up Your District",
    sourcesCount: "Live Census F-33 (13,251 districts)"
  },
  {
    id: "weather-risk-noaa",
    number: "Guide 15",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Climate, Housing & Insurance Risk",
    title: "America's Extreme Weather & Homebuyer Hazard Map: All 3,259 U.S. Counties (NOAA 2016–2026)",
    summary:
      "Zero-paywall audit of 687,227 observed NOAA Storm Events (2016 to Nov 2026; $245.83B property damage, $14.91B crop loss, 10,485 deaths) across 3,259 U.S. counties, tracking +15.3% 5-year storm acceleration, county-level hail, flood, tornado, and wildfire profiles, and the silent killers (Extreme Heat and Cold) driving U.S. fatalities.",
    highlights: [
      "Instant county lookup across all 3,259 U.S. counties with top local hazard, damage percentile, and 5-year trend",
      "Property Damage ($96B Flood, $82B Hurricane, $32B Wildfire, $12B Hail) vs. Deadliest Hazards breakdown",
      "Open bulk dataset (.csv.gz) and reproducible NOAA NCEI Python pipeline (handling County vs. NWS Zone mapping)"
    ],
    guideUrl: "./guides/weather-risk/",
    toolUrl: "./guides/weather-risk/#lookup",
    toolLabel: "Check Your County",
    sourcesCount: "Live NOAA NCEI (687,227 events, 3,259 counties)"
  },
  {
    id: "college-debt-roi",
    number: "Guide 14",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Higher Education & Family Finance",
    title: "The College Debt & Parent PLUS Reality: All 6,232 Active U.S. Colleges (2026 Scorecard)",
    summary:
      "Zero-affiliate audit of the June 2026 U.S. Dept. of Education College Scorecard (6,232 active colleges, 14.46M undergrads): exposing 914 schools failing the High-School Earnings Test (85.4% For-Profit), why Public 4-year colleges beat Private Non-Profits on median 10-year earnings ($54.7k vs. $54.1k) at $7,938/yr less net price, and 392 schools with $40k+ Parent PLUS debt traps (peaking above $108k).",
    highlights: [
      "Interactive Income-Bracket ROI and Payback Calculator across all 5 federal family income brackets",
      "Instant searchable lookup of all 6,232 U.S. colleges with Student and Parent PLUS debt plus official Scorecard links",
      "Stratified 4-Yr vs. 2-Yr comparison plus open .csv.gz and reproducible College Scorecard Python pipeline"
    ],
    guideUrl: "./guides/colleges/",
    toolUrl: "./guides/colleges/#calculator",
    toolLabel: "Check College ROI",
    sourcesCount: "Live Dept. of Ed Scorecard (6,232 colleges)"
  },
  {
    id: "auto-safety-nhtsa",
    number: "Guide 13",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Auto Safety & Consumer Rights",
    title: "Used-Car & Automaker Safety Reality: 4,056 Models, 13,785 Recalls & 438,178 Complaints (NHTSA 2010–2026)",
    summary:
      "Zero-affiliate, deduplicated audit of daily-updated NHTSA recall campaigns (2010 to Nov 2026; 541.2M units; 307 Do-Not-Drive and Park-Outside advisories) joined with 438,178 unique 2020–2026 owner complaints (removing 199,155 duplicate ODINO rows), exposing Hyundai/Kia's fire dominance (9 of Top 10 fire models), Ford's 657 recall campaigns, and Tesla's fire-vs-crash split.",
    highlights: [
      "Interactive Used-Car Pre-Buy Check comparing every MY 2010–2026 model year side-by-side",
      "Searchable catalog of 4,056 vehicles plus all 307 Do-Not-Drive and Park-Outside fire warnings",
      "36-brand scorecard plus open .csv.gz downloads and reproducible NHTSA flat-file Python pipeline"
    ],
    guideUrl: "./guides/auto-safety/",
    toolUrl: "./guides/auto-safety/#prebuy",
    toolLabel: "Check a Used Car",
    sourcesCount: "Live NHTSA ODI (13,785 recalls + 438k complaints)"
  },
  {
    id: "workplace-safety-osha",
    number: "Guide 12",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Labor & Workplace Safety",
    title: "America's Workplace Injury & Amputation Reality: 377,415 Workplaces & 5,744 Employers (OSHA 2025)",
    summary:
      "Deduplicated audit joining 2025 OSHA Form 300A filings (377,415 workplaces, 44.9M workers, 1.35M injuries, 780 deaths) with 11 years of Federal OSHA Severe Injury Reports (105,996 events; 86,518 hospitalizations; 27,978 amputations), exposing 3,837 duplicate OSHA submissions, massive intra-industry gaps (Southwest 10.78 and American 8.92 vs. Delta 3.45 DART; FedEx 9.86 vs. UPS 6.51), and the Meatpacking Amputation Paradox.",
    highlights: [
      "Interactive Employer Risk Checker plus searchable database of 5,744 employers, 267 industries, and 1,000 injury hotspots",
      "NAICS-weighted peer industry benchmarks plus 11-year Federal OSHA amputation and hospitalization counts",
      "Open bulk datasets (.csv.gz) and reproducible OSHA Python pipeline with duplicate and outlier forensics"
    ],
    guideUrl: "./guides/workplace-safety/",
    toolUrl: "./guides/workplace-safety/#checker",
    toolLabel: "Check an Employer",
    sourcesCount: "Live OSHA 300A (377k sites) + SIR (106k)"
  },
  {
    id: "electric-utility-divide",
    number: "Guide 11",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Energy & Cost of Living",
    title: "The Power Bill Divide: U.S. Electric Utility Rate Hikes, Blackouts & The Monopoly Premium (2020–2025)",
    summary:
      "Zero-affiliate EIA Form 861 audit of all 1,390 full-form U.S. residential electric utilities (140.8M households; 98.1% of U.S. homes): exposing the +31.0% 5-year rate surge (+$69.2B/yr), why Investor-Owned Utilities charge more than Public Power in 41 of 44 states ($33.54B/yr same-state excess), and Municipal utilities' 3.5x lower median blackout minutes (57.3 vs. 205.7 SAIDI).",
    highlights: [
      "Interactive Power Bill and Monopoly Premium calculator plus county-level search across all 1,390 U.S. utilities",
      "Same-state head-to-head showdowns (PG&E vs. SMUD +$2,008/yr, SDG&E vs. SMUD +$2,899/yr, TXU vs. San Antonio +$752/yr)",
      "Open linked dataset (.csv.gz) and reproducible EIA-861 Python pipeline (Bundled vs. Delivery safeguarded)"
    ],
    guideUrl: "./guides/utilities/",
    toolUrl: "./guides/utilities/#calculator",
    toolLabel: "Check Your Utility",
    sourcesCount: "Live EIA Form 861 (1,390 utilities)"
  },
  {
    id: "bank-deposit-skim",
    number: "Guide 10",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Consumer Finance & Banking",
    title: "The Great Bank Deposit Skim: All 4,204 FDIC U.S. Banks (2021–2025)",
    summary:
      "Zero-affiliate audit of all 4,204 active FDIC-insured U.S. banks ($18.06T domestic deposits, FY2021 and FY2025 Call Reports): exposing the $38B/yr Big 4 interest gap (1.71% weighted paid vs. 2.30% p75), $34.38B in deposit service fees (65% from 16 megabanks), 2021–2025 rate pass-through, and uninsured deposit exposure.",
    highlights: [
      "Interactive 'How Much Is Your Bank Costing You?' calculator across all 4,204 U.S. banks",
      "Reports both blended and interest-bearing deposit rates plus exact ISERCHG service fees",
      "Open linked dataset (.csv.gz) and reproducible FDIC Call Report Python pipeline"
    ],
    guideUrl: "./guides/banks/",
    toolUrl: "./guides/banks/#calculator",
    toolLabel: "Check Your Bank",
    sourcesCount: "Live FDIC Call Reports (4,204 banks)"
  },
  {
    id: "dialysis-accountability",
    number: "Guide 09",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Healthcare & Kidney Care",
    title: "The U.S. Dialysis Duopoly & Clinic Accountability Platform (7,471 Clinics)",
    summary:
      "Flagship analysis of all 7,471 Medicare-certified U.S. dialysis clinics (CMS Dialysis Facility Compare through Dec 2025): exposing DaVita and Fresenius's 73.5% duopoly, the non-profit vs. for-profit kidney transplant waitlist gap (19.3% vs. 16.3%; Kaiser 41.9%), 2,915 high-catheter clinics, and why small independent for-profits post the worst raw averages.",
    highlights: [
      "Instant lookup across all 7,471 clinics with mortality, hospitalizations, catheters, home dialysis, and evening shifts",
      "Operator scorecard comparing DaVita, Fresenius, U.S. Renal Care, DCI, Kaiser, and independents",
      "Open linked dataset (.csv.gz) plus Care Compare and SRTR Transplant Center links"
    ],
    guideUrl: "./guides/dialysis/",
    toolUrl: "./guides/dialysis/#lookup",
    toolLabel: "Search All 7,471 Clinics",
    sourcesCount: "Live CMS Dialysis Dataset (7,471 clinics)"
  },
  {
    id: "hospital-charity-care",
    number: "Guide 08",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Healthcare & Billing",
    title: "U.S. Hospital Charity Care, Chargemaster Markups & Financial Reality (5,435 Hospitals)",
    summary:
      "Flagship 4-dataset CMS join uniting all 5,435 U.S. hospitals, 5,078 full-year FY2024 Form 2552-10 Cost Reports, and 147,029 PECOS owner rows, showing why 31.7% of tax-exempt hospitals spend under 1% on charity care (408 while earning 5%+ net margins), median markups hit 3.74x (6.40x at for-profits), and how patients can invoke IRS Section 501(r).",
    highlights: [
      "Instant lookup across all 5,435 hospitals with FY2024 financials, markups, and Care Compare / Dollar For links",
      "Interactive IRS Section 501(r) Charity Care Eligibility Checker plus 50-state table",
      "Open linked dataset (.csv.gz) and reproducible 4-endpoint Python pipeline (catching the S-10 bad-debt charges trap)"
    ],
    guideUrl: "./guides/hospitals/",
    toolUrl: "./guides/hospitals/#lookup",
    toolLabel: "Search All 5,435 Hospitals",
    sourcesCount: "4 Live CMS Datasets (5,435 hospitals)"
  },
  {
    id: "nursing-home-reality",
    number: "Guide 03",
    flagship: true,
    status: "published",
    date: "November 2026",
    category: "Elder Care & Health",
    title: "U.S. Nursing Home Accountability Platform (14,686 Homes, 612 Chains & FY2024 Finances)",
    summary:
      "Flagship 5-dataset CMS join uniting all 14,686 U.S. nursing homes, 612 corporate chains, 302,718 PECOS ownership rows, and 13,819 matched FY2024 Cost Reports, exposing broken PE/REIT disclosures (14,257 nameless org rows), Medicaid-controlled labor and margin gaps (+$25 to $80/day more at non-profits), the TX/IN government-chain lease distortion, state inspection backlogs (AL 85.3%, VA 57.1%, DC 56.2%), and the 46.8% 5-star red-flag illusion.",
    highlights: [
      "Instant search across all 14,686 homes with full 5-dataset dossiers and Care Compare / ProPublica links",
      "612-chain scorecard plus Medicaid-controlled FY2024 true operating margins and direct labor spending",
      "Open linked dataset (.csv.gz + JSON) and reproducible 5-endpoint Python pipeline"
    ],
    guideUrl: "./guides/nursing-homes/",
    toolUrl: "./guides/nursing-homes/#lookup",
    toolLabel: "Search All 14,686 Homes",
    sourcesCount: "5 Live CMS Datasets (14,686 homes & 612 chains)"
  },
  {
    id: "airline-wheelchair-scorecard",
    number: "Guide 04",
    status: "published",
    date: "November 2026",
    category: "Consumer Rights",
    title: "Airline Reliability & Wheelchair Safety Scorecard (2024–2025)",
    summary:
      "A zero-affiliate carrier scorecard built from mandatory U.S. DOT Air Travel Consumer Reports, ranking actual wheelchair and scooter mishandling rates (0.43% at Delta vs. 1.44% at JetBlue) and 2025 on-time performance.",
    highlights: [
      "Interactive sortable scorecard across 10 U.S. carriers (2024 vs. 2025 DOT logs)",
      "Separates marketing promises from legally reported mobility and delay failure rates",
      "Practical gate-check and DOT cash-refund rights checklist"
    ],
    guideUrl: "./guides/airline-safety/",
    toolUrl: "./guides/airline-safety/#rights",
    toolLabel: "Traveler Rights Checklist",
    sourcesCount: "U.S. DOT / BTS ATCR (2024–2025)"
  },
  {
    id: "food-recalls-decoded",
    number: "Guide 05",
    status: "published",
    date: "November 2026",
    category: "Everyday Science & Health",
    title: "Food Recalls Decoded: Allergens vs. Severe Pathogens (29,634 FDA Records)",
    summary:
      "Live openFDA Food Enforcement API analysis separating high-volume allergen labeling errors (24.7% of recalls) from high-lethality Class I Salmonella (88.4% Class I) and Listeria (79.2% Class I) outbreaks, vs. foreign material at just 0.7% Class I.",
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
    number: "Guide 06",
    status: "published",
    date: "November 2026",
    category: "Consumer Finance & Banking",
    title: "Financial Disputes, Credit-Repair Spam & P2P Fraud Reality",
    summary:
      "Built from CFPB Consumer Response Annual Reports (2024–2026): why credit bureaus get 85% of complaints yet pay under 0.1% cash relief, how Regulation E splits Zelle hacks from scams, and how to avoid predatory 'credit sweep' schemes.",
    highlights: [
      "Interactive Dispute Reality Checker across 6 common money and fraud scenarios",
      "Documents the copy-paste 'credit washing' spam skewing raw CFPB volumes",
      "Clear, free federal dispute paths under Reg E, FCRA, FCBA, and FDCPA"
    ],
    guideUrl: "./guides/financial-disputes/",
    toolUrl: "./guides/financial-disputes/#dispute-tool",
    toolLabel: "Open Dispute Checker",
    sourcesCount: "CFPB Annual Reports & Reg E / FCRA"
  },
  {
    id: "flood-insurance-payout-reality",
    number: "Guide 07",
    status: "published",
    date: "November 2026",
    category: "Climate, Housing & Insurance Risk",
    title: "Flood Insurance Payout Reality & Zone X Risk (5,000 OpenFEMA Claims)",
    summary:
      "Live OpenFEMA NFIP v3 analysis showing why 28.7% of paid flood claims happen outside mapped high-risk zones (with higher median payouts than Zone A/V), why 73.7% receive $0 for contents, and how the $250k cap catches homeowners off guard.",
    highlights: [
      "Interactive Homebuyer and Renter Flood Coverage Gap Checker",
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
    number: "Guide 01",
    status: "published",
    date: "November 2026",
    category: "Everyday Science & Health",
    title: "Microplastics in Drinking Water: What Actually Works (on Any Budget)",
    summary:
      "Separating peer-reviewed lab evidence from marketing hype across boiling, loose-carbon pitchers, membrane filters, solid carbon blocks, reverse osmosis, plastic kettles, and bottled water.",
    highlights: [
      "Compares real annual costs ($15 to $200/yr vs. $300 to $700+/yr for bottled water)",
      "Flags critical caveats: plastic kettle shedding and boiling concentrating lead or PFAS",
      "Verified against 2023–2025 primary papers and NSF/ANSI 401 standards"
    ],
    guideUrl: "./guides/microplastics/",
    toolUrl: "./microplastics-calculator/",
    toolLabel: "Open Decision Calculator",
    sourcesCount: "7 primary sources & standards"
  },
  {
    id: "global-traffic-safety",
    number: "Guide 02",
    status: "published",
    date: "November 2026",
    category: "Public Infrastructure & Safety",
    title: "Global Traffic Safety: Which Countries Cut Road Deaths Fastest, and How?",
    summary:
      "A reproducible public-data investigation across 158 countries (WHO Global Health Observatory, ITF/IRTAD, and NHTSA) examining how leaders like Norway, Japan, South Korea, Lithuania, Poland, and Oman slashed road deaths while the U.S. diverged.",
    highlights: [
      "Interactive 158-country trend chart and searchable data explorer (WHO 2010–2021)",
      "5 proven policies: Safe System engineering, 50/30 urban speed caps, cameras, and crosswalk priority",
      "Documents WHO 2022–2023 extrapolation artifacts vs. NHTSA actuals"
    ],
    guideUrl: "./guides/traffic-safety/",
    toolUrl: "./guides/traffic-safety/#explorer",
    toolLabel: "Explore 158-Country Data",
    sourcesCount: "WHO GHO (158 countries) + ITF/IRTAD + NHTSA"
  }
];
