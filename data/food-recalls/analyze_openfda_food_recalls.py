"""
Reproducible Analysis: U.S. Food Recalls (openFDA Food Enforcement API)
Primary Source: U.S. FDA openFDA API (https://api.fda.gov/food/enforcement.json)
Pulls live aggregate counts across classification, year, hazard category, state, and recall volume.

Run: python analyze_openfda_food_recalls.py
Outputs: summary.json, summary-data.js
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
BASE = "https://api.fda.gov/food/enforcement.json"


def fda_get(params: dict):
    qs = urllib.parse.urlencode(params, safe=":+[]\"()")
    url = f"{BASE}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "OpenResearchGuides/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def count_total(search: str | None = None) -> int:
    params = {"limit": 1}
    if search:
        params["search"] = search
    try:
        d = fda_get(params)
        return int(d["meta"]["results"]["total"])
    except Exception:
        return 0


def main():
    # 1. Overall classification split (all-time in openFDA, 2012-present)
    cls_all = fda_get({"count": "classification.exact"})["results"]
    total_all = sum(x["count"] for x in cls_all)

    # 2. Recent 5-year window (2021-01-01 to 2026-12-31)
    recent_filter = "report_date:[20210101+TO+20261231]"
    cls_recent = fda_get({"search": recent_filter, "count": "classification.exact"})["results"]
    total_recent = sum(x["count"] for x in cls_recent)

    # 3. Yearly counts (2015..2025) by total and Class I
    yearly = []
    for yr in range(2015, 2026):
        rng = f"report_date:[{yr}0101+TO+{yr}1231]"
        tot = count_total(rng)
        c1 = count_total(f'{rng}+AND+classification:"Class I"')
        yearly.append({"year": yr, "total": tot, "class_i": c1, "class_i_pct": round(c1 / tot * 100, 1) if tot else 0})

    # 4. Hazard breakdown (recent 2021-2026): total vs Class I share!
    hazards_spec = [
        ("Undeclared Allergens", 'reason_for_recall:"undeclared"'),
        ("Listeria monocytogenes", 'reason_for_recall:"listeria"'),
        ("Salmonella", 'reason_for_recall:"salmonella"'),
        ("Foreign Material (plastic/metal/glass)", '(reason_for_recall:"foreign"+OR+reason_for_recall:"plastic"+OR+reason_for_recall:"metal"+OR+reason_for_recall:"glass")'),
        ("E. coli", 'reason_for_recall:"coli"'),
        ("Botulism / Clostridium", '(reason_for_recall:"botulinum"+OR+reason_for_recall:"botulism")'),
        ("Lead / Heavy Metals", '(reason_for_recall:"lead"+OR+reason_for_recall:"arsenic"+OR+reason_for_recall:"cadmium")'),
    ]
    hazards = []
    for label, expr in hazards_spec:
        tot = count_total(f"{recent_filter}+AND+{expr}")
        c1 = count_total(f'{recent_filter}+AND+{expr}+AND+classification:"Class I"')
        hazards.append({
            "hazard": label,
            "total": tot,
            "class_i": c1,
            "class_i_pct": round(c1 / tot * 100, 1) if tot else 0,
            "share_of_recent_pct": round(tot / total_recent * 100, 1) if total_recent else 0,
        })

    # 5. Specific allergen breakdown (recent 2021-2026)
    allergens = []
    for a in ["milk", "soy", "wheat", "egg", "peanut", "almond", "sesame", "walnut", "cashew", "fish", "sulfites"]:
        tot = count_total(f'{recent_filter}+AND+reason_for_recall:"undeclared"+AND+reason_for_recall:"{a}"')
        c1 = count_total(f'{recent_filter}+AND+reason_for_recall:"undeclared"+AND+reason_for_recall:"{a}"+AND+classification:"Class I"')
        allergens.append({"allergen": a.capitalize(), "total": tot, "class_i": c1, "class_i_pct": round(c1 / tot * 100, 1) if tot else 0})
    allergens.sort(key=lambda x: x["total"], reverse=True)

    # 6. Top states of recalling firms (recent 2021-2026)
    top_states = fda_get({"search": recent_filter, "count": "state.exact"})["results"][:15]

    summary = {
        "source": "U.S. FDA openFDA Food Enforcement API (api.fda.gov/food/enforcement.json)",
        "window_recent": "2021–2026",
        "total_all_time": total_all,
        "classification_all_time": cls_all,
        "total_recent": total_recent,
        "classification_recent": cls_recent,
        "yearly": yearly,
        "hazards_recent": hazards,
        "allergens_recent": allergens,
        "top_states_recent": top_states,
    }

    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "summary-data.js").write_text(
        "window.OPENFDA_FOOD_DATA = " + json.dumps(summary, indent=2) + ";\n",
        encoding="utf-8",
    )

    print(f"openFDA all-time records: {total_all:,} | 2021-2026 records: {total_recent:,}")
    print("\nHazard Severity Breakdown (2021-2026):")
    for h in hazards:
        print(f"  {h['hazard']:40s} | n={h['total']:5d} ({h['share_of_recent_pct']:4.1f}%) | Class I: {h['class_i']:5d} ({h['class_i_pct']:5.1f}%)")
    print("\nTop Undeclared Allergens (2021-2026):")
    for a in allergens[:8]:
        print(f"  {a['allergen']:12s} | n={a['total']:4d} | Class I: {a['class_i_pct']:5.1f}%")


if __name__ == "__main__":
    main()
