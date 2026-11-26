# Open Plain-Language Research Guides

A small, independent public-interest project turning peer-reviewed studies and public datasets into calm, honest, citation-backed guides and simple tools that ordinary people can actually use.

### Project Principles
- **Primary sources first:** Claims are checked against peer-reviewed papers, official testing standards, and public datasets—not viral posts or sponsored reviews.
- **Honest about uncertainty:** Every guide explicitly states what scientists still do *not* know and notes legitimate methodological critiques.
- **Practical & zero-agenda:** No affiliate links, no tracking, no fearmongering—just clear trade-offs across real household budgets.

---

## Guides & Tools

### 1. Microplastics in Drinking Water: What Actually Works (on Any Budget)
- **Full Evidence Guide:** [`microplastics-drinking-water-guide.md`](./microplastics-drinking-water-guide.md) — Peer-reviewed lab evidence (2023–2025), 5 myth checks, annual budget breakdown, safety caveats, and open scientific gaps.
- **Interactive Decision Calculator:** [`microplastics-calculator/index.html`](./microplastics-calculator/index.html) — Open directly in any web browser (zero setup, runs 100% locally) to get a tailored household recommendation and 3-year cost comparison.
- **1-Minute Shareable Summary:** [`microplastics-shareable-summary.md`](./microplastics-shareable-summary.md) — Ready to share with family or community groups.

### 2. Global Traffic Safety: Which Countries Cut Road Deaths Fastest — and How?
- **Interactive Data Guide & 158-Country Explorer:** [`guides/traffic-safety/index.html`](./guides/traffic-safety/index.html) — Live multi-country SVG trend chart, regional progress breakdown, searchable 158-country table, and 5 proven policy lessons.
- **Markdown Brief:** [`traffic-safety-global-guide.md`](./traffic-safety-global-guide.md)
- **Reproducible Analysis Code & Data:** [`data/traffic-safety/analyze_who_road_deaths.py`](./data/traffic-safety/analyze_who_road_deaths.py) & [`data/traffic-safety/summary.json`](./data/traffic-safety/summary.json) (pulls directly from the WHO Global Health Observatory `RS_198` & World Bank APIs).

---

## How to Use or Publish This Project

- **Try locally:** Double-click `index.html` (Research Hub) or `microplastics-calculator/index.html` to open in any web browser.
- **Publish for free on Vercel (recommended):** Push this folder to a public GitHub repository and import it in [Vercel](https://vercel.com/new) (Framework Preset: **Other**, Output Directory: `.`). Every future push auto-deploys live!
- **Contribute or spot a correction:** If a newer peer-reviewed study updates or contradicts a finding here, please open an issue or pull request with the primary citation (DOI or official agency link).

## License
Released for open public benefit under **CC BY 4.0** (guides) and **MIT** (interactive tool code). Feel free to share, adapt, or translate with attribution.
