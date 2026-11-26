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
    status: "upcoming",
    date: "In Progress",
    category: "Society & Public Data",
    title: "Global Traffic Safety: Which Countries Cut Road Deaths Fastest — and How?",
    summary:
      "An upcoming public-data investigation analyzing international road-fatality datasets alongside the concrete street design, speed, and enforcement policies that saved the most lives.",
    highlights: [
      "Reproducible analysis of open international road-fatality data",
      "Before-and-after policy case studies from top improvers",
      "Interactive charts & plain-language takeaways"
    ],
    guideUrl: null,
    toolUrl: null,
    toolLabel: null,
    sourcesCount: "Public data analysis upcoming"
  }
];
