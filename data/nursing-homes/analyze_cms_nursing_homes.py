"""
Reproducible Analysis: U.S. Nursing Home Staffing, Turnover, Weekend Drops & Fines
Primary Source: CMS Provider Data Catalog — Provider Information (Dataset 4pq5-n9py)
Covers all ~14,686 Medicare/Medicaid-certified nursing homes in the United States.

Run: python analyze_cms_nursing_homes.py
Outputs: summary.json, summary-data.js
"""

import concurrent.futures
import json
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
BASE = "https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0"
PAGE_SIZE = 500


def fetch_page(offset: int):
    url = f"{BASE}?limit={PAGE_SIZE}&offset={offset}"
    raw = subprocess.check_output(["curl.exe", "-s", url], timeout=45)
    return json.loads(raw.decode("utf-8"))


def to_float(v):
    try:
        return float(v) if v not in (None, "", "N/A") else None
    except ValueError:
        return None


def classify_owner(o: str) -> str:
    ol = (o or "").lower()
    if "for profit" in ol:
        return "For-Profit"
    if "non profit" in ol:
        return "Non-Profit"
    if "government" in ol:
        return "Government"
    return "Other"


def mean_or_none(arr, digits=2):
    return round(statistics.mean(arr), digits) if arr else None


def med_or_none(arr, digits=2):
    return round(statistics.median(arr), digits) if arr else None


def main():
    first = fetch_page(0)
    total_count = int(first["count"])
    rows = list(first["results"])

    offsets = list(range(PAGE_SIZE, total_count, PAGE_SIZE))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for res in ex.map(fetch_page, offsets):
            rows.extend(res.get("results", []))

    n = len(rows)
    by_owner = defaultdict(lambda: {"n": 0, "stars": [], "tot_h": [], "wknd_h": [], "rn_h": [], "rn_wknd_h": [], "turn": [], "rn_turn": [], "fines_amt": [], "fined_n": 0, "abuse_n": 0})
    by_state = defaultdict(lambda: {"n": 0, "stars": [], "tot_h": [], "wknd_h": [], "turn": [], "rn_turn": [], "fines_amt": [], "fined_n": 0, "abuse_n": 0})
    all_tot_h, all_wknd_h, all_rn_h, all_rn_wknd, all_turn, all_rn_turn, all_fines = [], [], [], [], [], [], []

    five_star_n = 0
    five_star_high_turnover = 0  # >= 50% total nursing turnover
    five_star_fined = 0
    five_star_big_wknd_drop = 0  # >= 15% weekend nurse hour drop
    fined_total_n = 0
    abuse_total_n = 0

    for r in rows:
        st = r.get("state") or "UNK"
        own = classify_owner(r.get("ownership_type"))
        stars = to_float(r.get("overall_rating"))
        tot_h = to_float(r.get("reported_total_nurse_staffing_hours_per_resident_per_day"))
        wknd_h = to_float(r.get("total_number_of_nurse_staff_hours_per_resident_per_day_on_t_4a14"))
        rn_h = to_float(r.get("reported_rn_staffing_hours_per_resident_per_day"))
        rn_wknd = to_float(r.get("registered_nurse_hours_per_resident_per_day_on_the_weekend"))
        turn = to_float(r.get("total_nursing_staff_turnover"))
        rn_turn = to_float(r.get("registered_nurse_turnover"))
        fines_n = to_float(r.get("number_of_fines")) or 0
        fines_amt = to_float(r.get("total_amount_of_fines_in_dollars")) or 0.0
        abuse = (r.get("abuse_icon") == "Y")

        if tot_h is not None: all_tot_h.append(tot_h)
        if wknd_h is not None: all_wknd_h.append(wknd_h)
        if rn_h is not None: all_rn_h.append(rn_h)
        if rn_wknd is not None: all_rn_wknd.append(rn_wknd)
        if turn is not None: all_turn.append(turn)
        if rn_turn is not None: all_rn_turn.append(rn_turn)
        all_fines.append(fines_amt)
        if fines_n > 0: fined_total_n += 1
        if abuse: abuse_total_n += 1

        if stars == 5:
            five_star_n += 1
            if turn is not None and turn >= 50: five_star_high_turnover += 1
            if fines_n > 0: five_star_fined += 1
            if tot_h and wknd_h and ((tot_h - wknd_h) / tot_h) >= 0.15: five_star_big_wknd_drop += 1

        for bucket in (by_owner[own], by_state[st]):
            bucket["n"] += 1
            if stars is not None: bucket["stars"].append(stars)
            if tot_h is not None: bucket["tot_h"].append(tot_h)
            if wknd_h is not None: bucket["wknd_h"].append(wknd_h)
            if turn is not None: bucket["turn"].append(turn)
            if rn_turn is not None: bucket["rn_turn"].append(rn_turn)
            bucket["fines_amt"].append(fines_amt)
            if fines_n > 0: bucket["fined_n"] += 1
            if abuse: bucket["abuse_n"] += 1

        if rn_h is not None: by_owner[own]["rn_h"].append(rn_h)
        if rn_wknd is not None: by_owner[own]["rn_wknd_h"].append(rn_wknd)

    owner_summary = []
    for own in ("Non-Profit", "Government", "For-Profit"):
        b = by_owner[own]
        if b["n"] == 0:
            continue
        th = mean_or_none(b["tot_h"])
        wh = mean_or_none(b["wknd_h"])
        drop_pct = round((th - wh) / th * 100, 1) if th and wh else None
        owner_summary.append({
            "ownership": own,
            "facilities": b["n"],
            "share_pct": round(b["n"] / n * 100, 1),
            "avg_stars": mean_or_none(b["stars"]),
            "avg_total_hprd": th,
            "avg_weekend_hprd": wh,
            "weekend_drop_pct": drop_pct,
            "avg_rn_hprd": mean_or_none(b["rn_h"]),
            "avg_rn_weekend_hprd": mean_or_none(b["rn_wknd_h"]),
            "avg_turnover_pct": mean_or_none(b["turn"], 1),
            "avg_rn_turnover_pct": mean_or_none(b["rn_turn"], 1),
            "pct_fined": round(b["fined_n"] / b["n"] * 100, 1),
            "avg_fine_dollars": round(mean_or_none(b["fines_amt"], 0) or 0),
            "pct_abuse_icon": round(b["abuse_n"] / b["n"] * 100, 1),
        })

    state_summary = []
    for st, b in by_state.items():
        if b["n"] < 10 or len(st) != 2:
            continue
        th = mean_or_none(b["tot_h"])
        wh = mean_or_none(b["wknd_h"])
        drop_pct = round((th - wh) / th * 100, 1) if th and wh else None
        state_summary.append({
            "state": st,
            "facilities": b["n"],
            "avg_stars": mean_or_none(b["stars"]),
            "avg_total_hprd": th,
            "avg_weekend_hprd": wh,
            "weekend_drop_pct": drop_pct,
            "avg_turnover_pct": mean_or_none(b["turn"], 1),
            "avg_rn_turnover_pct": mean_or_none(b["rn_turn"], 1),
            "pct_fined": round(b["fined_n"] / b["n"] * 100, 1),
            "avg_fine_dollars": round(mean_or_none(b["fines_amt"], 0) or 0),
        })
    state_summary.sort(key=lambda x: x["avg_total_hprd"] or 0, reverse=True)

    nat_tot = mean_or_none(all_tot_h)
    nat_wknd = mean_or_none(all_wknd_h)
    nat_rn = mean_or_none(all_rn_h)
    nat_rn_wknd = mean_or_none(all_rn_wknd)

    summary = {
        "source": "CMS Provider Data Catalog — Nursing Home Provider Information (Dataset 4pq5-n9py, PBJ staffing & penalties)",
        "total_facilities": n,
        "national": {
            "avg_total_hprd": nat_tot,
            "avg_weekend_hprd": nat_wknd,
            "weekend_drop_pct": round((nat_tot - nat_wknd) / nat_tot * 100, 1) if nat_tot and nat_wknd else None,
            "avg_rn_hprd": nat_rn,
            "avg_rn_weekend_hprd": nat_rn_wknd,
            "rn_weekend_drop_pct": round((nat_rn - nat_rn_wknd) / nat_rn * 100, 1) if nat_rn and nat_rn_wknd else None,
            "avg_turnover_pct": mean_or_none(all_turn, 1),
            "median_turnover_pct": med_or_none(all_turn, 1),
            "avg_rn_turnover_pct": mean_or_none(all_rn_turn, 1),
            "pct_fined": round(fined_total_n / n * 100, 1),
            "total_fines_millions": round(sum(all_fines) / 1_000_000, 1),
            "pct_abuse_icon": round(abuse_total_n / n * 100, 1),
        },
        "five_star_reality": {
            "five_star_count": five_star_n,
            "pct_high_turnover_50plus": round(five_star_high_turnover / five_star_n * 100, 1) if five_star_n else 0,
            "pct_with_fines": round(five_star_fined / five_star_n * 100, 1) if five_star_n else 0,
            "pct_big_weekend_drop_15plus": round(five_star_big_wknd_drop / five_star_n * 100, 1) if five_star_n else 0,
        },
        "by_ownership": owner_summary,
        "by_state": state_summary,
    }

    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "summary-data.js").write_text(
        "window.CMS_NURSING_HOME_DATA = " + json.dumps(summary, indent=2) + ";\n",
        encoding="utf-8",
    )

    print(f"CMS facilities analyzed: {n:,}")
    print("National:", summary["national"])
    print("5-Star Reality:", summary["five_star_reality"])
    print("\nBy Ownership:")
    for o in owner_summary:
        print(f"  {o['ownership']:12s} | n={o['facilities']:5d} ({o['share_pct']:4.1f}%) | stars={o['avg_stars']} | tot={o['avg_total_hprd']}h wknd={o['avg_weekend_hprd']}h (-{o['weekend_drop_pct']}%) | turn={o['avg_turnover_pct']}% | fined={o['pct_fined']}% (${o['avg_fine_dollars']:,})")


if __name__ == "__main__":
    main()
