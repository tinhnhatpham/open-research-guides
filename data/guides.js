// Central catalog of all research guides and interactive tools.
// Add a new object here whenever you publish a new research project!
window.RESEARCH_GUIDES = [
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
      "Includes reproducible Python analysis code & data-literacy caveats on modeled projections"
    ],
    guideUrl: "./guides/traffic-safety/",
    toolUrl: "./guides/traffic-safety/#explorer",
    toolLabel: "Explore 158-Country Data",
    sourcesCount: "WHO GHO (158 countries) + ITF/IRTAD + NHTSA"
  }
];
