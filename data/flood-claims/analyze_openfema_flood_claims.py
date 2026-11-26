"""
Reproducible Analysis: U.S. Flood Insurance Claims & Payout Gaps (OpenFEMA NFIP v3 API)
Primary Source: FEMA OpenFEMA API v3 (https://www.fema.gov/api/open/v3/NfipClaims)
Pulls 5,000 recent paid NFIP flood claims (2020–2026) to measure:
  - Share of claims occurring outside Special Flood Hazard Areas (Zone X / moderate-to-low risk)
  - Median vs. mean building payouts and building-payout-to-damage ratios
  - Contents coverage gap and top states in the sample

Run: python analyze_openfema_flood_claims.py
Outputs: summary.json, summary-data.js
"""

import json
import statistics
import subprocess
import urllib.parse
from collections import defaultdict
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
BASE = "https://www.fema.gov/api/open/v3/NfipClaims"


def fetch_batch(skip: int, top: int = 1000):
    params = {
        "$filter": "yearOfLoss ge 2020 and amountPaidOnBuildingClaim gt 0",
        "$select": "state,yearOfLoss,ratedFloodZone,amountPaidOnBuildingClaim,amountPaidOnContentsClaim,buildingDamageAmount,contentsDamageAmount,waterDepth",
        "$orderby": "dateOfLoss desc",
        "$top": str(top),
        "$skip": str(skip),
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    raw = subprocess.check_output(["curl.exe", "-s", url], timeout=45)
    return json.loads(raw.decode("utf-8"))


def classify_zone(z: str | None) -> str:
    if not z:
        return "Unknown"
    zu = z.strip().upper()
    if zu.startswith(("A", "V")):
        return "High-Risk (Zone A/V SFHA)"
    if zu.startswith(("X", "B", "C", "D")):
        return "Moderate/Low-Risk (Zone X/B/C)"
    return "Other"


def main():
    records = []
    for skip in range(0, 5000, 1000):
        resp = fetch_batch(skip, 1000)
        batch = resp.get("NfipClaims", [])
        if not batch:
            break
        records.extend(batch)

    total = len(records)
    by_zone = defaultdict(lambda: {"count": 0, "bldg_paid": [], "bldg_dmg": [], "ratios": []})
    by_state = defaultdict(lambda: {"count": 0, "bldg_paid": [], "zone_x": 0})
    by_year = defaultdict(int)
    depths = []
    has_contents_payout = 0

    for r in records:
        zcat = classify_zone(r.get("ratedFloodZone"))
        bp = float(r.get("amountPaidOnBuildingClaim") or 0)
        cp = float(r.get("amountPaidOnContentsClaim") or 0)
        bd = float(r.get("buildingDamageAmount") or 0)
        st = r.get("state") or "UNK"
        yr = int(r.get("yearOfLoss") or 0)
        wd = r.get("waterDepth")

        by_year[yr] += 1
        by_zone[zcat]["count"] += 1
        by_zone[zcat]["bldg_paid"].append(bp)
        if cp > 0:
            has_contents_payout += 1
        if bd > 0:
            by_zone[zcat]["bldg_dmg"].append(bd)
            by_zone[zcat]["ratios"].append(min(1.5, bp / bd))
        if wd is not None and 0 <= float(wd) <= 30:
            depths.append(float(wd))

        by_state[st]["count"] += 1
        by_state[st]["bldg_paid"].append(bp)
        if zcat.startswith("Moderate"):
            by_state[st]["zone_x"] += 1

    zone_summary = []
    for z, vals in by_zone.items():
        if vals["count"] == 0:
            continue
        zone_summary.append({
            "zone_group": z,
            "count": vals["count"],
            "share_pct": round(vals["count"] / total * 100, 1),
            "median_bldg_paid": round(statistics.median(vals["bldg_paid"])),
            "mean_bldg_paid": round(statistics.mean(vals["bldg_paid"])),
            "median_bldg_damage": round(statistics.median(vals["bldg_dmg"])) if vals["bldg_dmg"] else None,
            "median_payout_ratio_pct": round(statistics.median(vals["ratios"]) * 100, 1) if vals["ratios"] else None,
        })
    zone_summary.sort(key=lambda x: x["count"], reverse=True)

    state_summary = []
    for st, vals in by_state.items():
        if vals["count"] < 15:
            continue
        state_summary.append({
            "state": st,
            "count": vals["count"],
            "median_bldg_paid": round(statistics.median(vals["bldg_paid"])),
            "mean_bldg_paid": round(statistics.mean(vals["bldg_paid"])),
            "zone_x_pct": round(vals["zone_x"] / vals["count"] * 100, 1),
        })
    state_summary.sort(key=lambda x: x["count"], reverse=True)

    all_paid = [float(r.get("amountPaidOnBuildingClaim") or 0) for r in records]
    all_ratios = [
        min(1.5, float(r["amountPaidOnBuildingClaim"]) / float(r["buildingDamageAmount"]))
        for r in records
        if (r.get("buildingDamageAmount") or 0) > 0 and (r.get("amountPaidOnBuildingClaim") or 0) > 0
    ]

    summary = {
        "source": "FEMA OpenFEMA API v3 (NfipClaims — 5,000 most recent paid claims from 2020–2026)",
        "sample_size": total,
        "years_covered": sorted(by_year.keys()),
        "overall_median_bldg_paid": round(statistics.median(all_paid)),
        "overall_mean_bldg_paid": round(statistics.mean(all_paid)),
        "contents_payout_share_pct": round(has_contents_payout / total * 100, 1),
        "median_payout_to_damage_pct": round(statistics.median(all_ratios) * 100, 1) if all_ratios else None,
        "median_water_depth_ft": round(statistics.median(depths), 1) if depths else None,
        "by_zone": zone_summary,
        "top_states": state_summary[:20],
    }

    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "summary-data.js").write_text(
        "window.OPENFEMA_FLOOD_DATA = " + json.dumps(summary, indent=2) + ";\n",
        encoding="utf-8",
    )

    print(f"OpenFEMA paid claims sampled: {total:,} | Years: {summary['years_covered']}")
    print(f"Median building payout: ${summary['overall_median_bldg_paid']:,} | Mean: ${summary['overall_mean_bldg_paid']:,}")
    print(f"Claims with contents payout: {summary['contents_payout_share_pct']}% | Median payout/damage ratio: {summary['median_payout_to_damage_pct']}% | Median water depth: {summary['median_water_depth_ft']} ft")
    print("\nBy Flood Zone:")
    for z in zone_summary:
        print(f"  {z['zone_group']:32s} | n={z['count']:4d} ({z['share_pct']:4.1f}%) | median paid=${z['median_bldg_paid']:,} | payout/dmg={z['median_payout_ratio_pct']}%")
    print("\nTop 10 States in Sample:")
    for s in state_summary[:10]:
        print(f"  {s['state']:4s} | n={s['count']:4d} | median paid=${s['median_bldg_paid']:,} | Zone X share={s['zone_x_pct']}%")


if __name__ == "__main__":
    main()
