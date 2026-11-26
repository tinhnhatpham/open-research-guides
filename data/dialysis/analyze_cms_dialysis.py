"""
Reproducible Analysis: U.S. Dialysis Clinic Accountability & The DaVita/Fresenius Duopoly
Primary Source: CMS Provider Data Catalog — Dialysis Facility Compare (Dataset 23ew-n7w9)
Covers all ~7,471 Medicare-certified dialysis facilities in the United States (through Dec 2025).

Run:
  python analyze_cms_dialysis.py
  python analyze_cms_dialysis.py --export-csv cms-dialysis-clinics-linked.csv.gz

Outputs:
  - summary.json
  - summary-data.js
  - clinics.json (compact lookup index for all ~7,471 clinics)
  - (optional) cms-dialysis-clinics-linked.csv.gz
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import gzip
import json
import shutil
import statistics
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).resolve().parent
CURL_BIN = shutil.which("curl.exe") or shutil.which("curl") or "curl"
BASE_URL = "https://data.cms.gov/provider-data/api/1/datastore/query/23ew-n7w9/0"
PAGE_SIZE = 500

US_STATES_DC = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN",
    "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
    "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
    "VT", "VA", "WA", "WV", "WI", "WY",
}


def curl_json(url: str, timeout: int = 60, retries: int = 3) -> Any:
    last_err = None
    for attempt in range(retries):
        try:
            raw = subprocess.check_output([CURL_BIN, "-sS", "--fail", url], timeout=timeout)
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def norm_ccn(v: Any) -> str:
    s = str(v or "").strip().upper()
    return s.zfill(6) if s.isdigit() else s


def to_float(v: Any) -> float | None:
    if v in (None, "", "Not Available", "N/A"):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def norm_chain(raw: str | None, chain_owned: str | None) -> str:
    s = (raw or "").strip()
    if not s or s.lower() == "independent" or (chain_owned or "").strip().lower() == "no":
        return "Independent"
    su = s.upper()
    if "DAVITA" in su:
        return "DaVita"
    if "FRESENIUS" in su:
        return "Fresenius Medical Care"
    if "U.S. RENAL" in su or "US RENAL" in su:
        return "U.S. Renal Care"
    if "DIALYSIS CLINIC" in su or su == "DCI":
        return "Dialysis Clinic, Inc. (DCI)"
    if "AMERICAN RENAL" in su or "INNOVATIVE RENAL" in su:
        return "Innovative Renal Care"
    if "SATELLITE" in su:
        return "Satellite Healthcare"
    if "NORTHWEST KIDNEY" in su:
        return "Northwest Kidney Centers"
    if "SANDERS" in su or "ROGOSIN" in su:
        return s.title()
    return s


def norm_profit(raw: str | None) -> str:
    s = (raw or "").strip().lower()
    if "non" in s:
        return "Non-Profit"
    if "profit" in s:
        return "For-Profit"
    return "Other"


def avg(arr: list[float], d: int = 2) -> float | None:
    return round(statistics.mean(arr), d) if arr else None


def med(arr: list[float], d: int = 2) -> float | None:
    return round(statistics.median(arr), d) if arr else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-csv", default="", help="Optional CSV/CSV.GZ filename in data/dialysis/")
    args = parser.parse_args()

    t0 = time.time()
    first = curl_json(f"{BASE_URL}?limit={PAGE_SIZE}&offset=0")
    total = int(first["count"])
    raw_rows = list(first["results"])
    offsets = list(range(PAGE_SIZE, total, PAGE_SIZE))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for res in ex.map(lambda o: curl_json(f"{BASE_URL}?limit={PAGE_SIZE}&offset={o}"), offsets):
            raw_rows.extend(res.get("results", []))

    clinics = []
    for r in raw_rows:
        ccn = norm_ccn(r.get("cms_certification_number_ccn"))
        if not ccn:
            continue
        name = (r.get("facility_name") or "").strip()
        city = (r.get("citytown") or "").strip()
        state = (r.get("state") or "").strip().upper()
        zip5 = str(r.get("zip_code") or "").strip()[:5]
        profit = norm_profit(r.get("profit_or_nonprofit"))
        chain = norm_chain(r.get("chain_organization"), r.get("chain_owned"))
        stars_f = to_float(r.get("five_star"))
        stars = int(stars_f) if stars_f is not None else None
        stations = to_float(r.get("of_dialysis_stations"))
        late_shift = (r.get("late_shift") or "").strip().lower() == "yes"
        pd = (r.get("offers_peritoneal_dialysis") or "").strip().lower() == "yes"
        home_hd = (r.get("offers_home_hemodialysis_training") or "").strip().lower() == "yes"
        offers_home = pd or home_hd

        mort = to_float(r.get("mortality_rate_facility"))
        mort_cat = (r.get("patient_survival_category_text") or "").strip()
        hosp = to_float(r.get("hospitalization_rate_facility"))
        hosp_cat = (r.get("patient_hospitalization_category_text") or "").strip()
        readm = to_float(r.get("readmission_rate_facility"))
        sir = to_float(r.get("standard_infection_ratio"))
        sir_cat = (r.get("patient_infection_category_text") or "").strip()
        fistula = to_float(r.get("fistula_rate_facility"))
        catheter = to_float(r.get("percentage_of_adult_patients_with_long_term_catheter_in_use"))
        pppw = to_float(r.get("percentage_of_prevalent_patients_waitlisted_for_kidney_tran_ecca"))
        pppw_cat = (r.get("pppw_category_text") or "").strip()
        fyswr = to_float(r.get("first_year_standardized_kidney_transplant_waitlist_ratio"))
        smosr = to_float(r.get("smosr_standardized_modality_switch_ratio_facility"))

        flags = []
        if mort_cat == "Worse than Expected":
            flags.append("WORSE_MORTALITY")
        if hosp_cat == "Worse than Expected":
            flags.append("WORSE_HOSP")
        if sir_cat == "Worse than Expected":
            flags.append("WORSE_INFECTION")
        if pppw_cat == "Worse than Expected":
            flags.append("LOW_TRANSPLANT")
        if stars is not None and stars <= 2:
            flags.append("LOW_STAR")
        if profit == "Non-Profit":
            flags.append("NONPROFIT")
        if offers_home:
            flags.append("HOME_DIALYSIS")
        if late_shift:
            flags.append("LATE_SHIFT")
        if catheter is not None and catheter >= 20.0:
            flags.append("HIGH_CATHETER")

        clinics.append({
            "ccn": ccn,
            "name": name,
            "city": city,
            "state": state,
            "zip": zip5,
            "profit": profit,
            "chain": chain,
            "stars": stars,
            "stations": int(stations) if stations is not None else None,
            "late_shift": late_shift,
            "pd": pd,
            "home_hd": home_hd,
            "offers_home": offers_home,
            "mort": mort,
            "mort_cat": mort_cat,
            "hosp": hosp,
            "hosp_cat": hosp_cat,
            "readm": readm,
            "sir": sir,
            "sir_cat": sir_cat,
            "fistula": fistula,
            "catheter": catheter,
            "pppw": pppw,
            "pppw_cat": pppw_cat,
            "fyswr": fyswr,
            "smosr": smosr,
            "flags": flags,
        })

    n = len(clinics)

    def summarize_group(label: str, grp: list[dict[str, Any]]) -> dict[str, Any]:
        gn = len(grp)
        mort_rated = [x for x in grp if x["mort_cat"] in ("Better than Expected", "As Expected", "Worse than Expected")]
        hosp_rated = [x for x in grp if x["hosp_cat"] in ("Better than Expected", "As Expected", "Worse than Expected")]
        pppw_rated = [x for x in grp if x["pppw_cat"] in ("Better than Expected", "As Expected", "Worse than Expected")]
        sir_rated = [x for x in grp if x["sir_cat"] in ("Better than Expected", "As Expected", "Worse than Expected")]
        return {
            "group": label,
            "clinics": gn,
            "share_pct": round(gn / n * 100, 1) if n else 0,
            "nonprofit_pct": round(sum(1 for x in grp if x["profit"] == "Non-Profit") / gn * 100, 1) if gn else 0,
            "avg_stars": avg([x["stars"] for x in grp if x["stars"] is not None], 2),
            "avg_mort": avg([x["mort"] for x in grp if x["mort"] is not None], 1),
            "pct_worse_mort": round(sum(1 for x in mort_rated if x["mort_cat"] == "Worse than Expected") / len(mort_rated) * 100, 1) if mort_rated else None,
            "avg_hosp": avg([x["hosp"] for x in grp if x["hosp"] is not None], 1),
            "pct_worse_hosp": round(sum(1 for x in hosp_rated if x["hosp_cat"] == "Worse than Expected") / len(hosp_rated) * 100, 1) if hosp_rated else None,
            "avg_sir": avg([x["sir"] for x in grp if x["sir"] is not None], 2),
            "pct_worse_sir": round(sum(1 for x in sir_rated if x["sir_cat"] == "Worse than Expected") / len(sir_rated) * 100, 1) if sir_rated else None,
            "avg_fistula": avg([x["fistula"] for x in grp if x["fistula"] is not None], 1),
            "avg_catheter": avg([x["catheter"] for x in grp if x["catheter"] is not None], 1),
            "avg_pppw": avg([x["pppw"] for x in grp if x["pppw"] is not None], 1),
            "pct_worse_pppw": round(sum(1 for x in pppw_rated if x["pppw_cat"] == "Worse than Expected") / len(pppw_rated) * 100, 1) if pppw_rated else None,
            "pct_offers_home": round(sum(1 for x in grp if x["offers_home"]) / gn * 100, 1) if gn else 0,
            "pct_late_shift": round(sum(1 for x in grp if x["late_shift"]) / gn * 100, 1) if gn else 0,
        }

    national = summarize_group("National", clinics)
    by_profit = [
        summarize_group(p, [x for x in clinics if x["profit"] == p])
        for p in ("Non-Profit", "For-Profit")
    ]

    # Duopoly stats
    davita_n = sum(1 for x in clinics if x["chain"] == "DaVita")
    fresenius_n = sum(1 for x in clinics if x["chain"] == "Fresenius Medical Care")
    duopoly = {
        "davita_clinics": davita_n,
        "davita_share_pct": round(davita_n / n * 100, 1),
        "fresenius_clinics": fresenius_n,
        "fresenius_share_pct": round(fresenius_n / n * 100, 1),
        "combined_clinics": davita_n + fresenius_n,
        "combined_share_pct": round((davita_n + fresenius_n) / n * 100, 1),
    }

    # Chain breakdown (all chains with >= 15 clinics + Independent split by Profit/Non-Profit)
    chain_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in clinics:
        if x["chain"] == "Independent":
            key = f"Independent ({x['profit']})"
        else:
            key = x["chain"]
        chain_buckets[key].append(x)

    major_chains = [
        summarize_group(k, v)
        for k, v in chain_buckets.items()
        if len(v) >= 15
    ]
    major_chains.sort(key=lambda x: x["clinics"], reverse=True)

    # 50 states + DC
    by_state = []
    for st in sorted(US_STATES_DC):
        grp = [x for x in clinics if x["state"] == st]
        if not grp:
            continue
        s = summarize_group(st, grp)
        s["state"] = st
        s["duopoly_pct"] = round(sum(1 for x in grp if x["chain"] in ("DaVita", "Fresenius Medical Care")) / len(grp) * 100, 1)
        by_state.append(s)
    by_state.sort(key=lambda x: x["avg_pppw"] if x["avg_pppw"] is not None else -1, reverse=True)

    counts = {
        "worse_mortality": sum(1 for x in clinics if x["mort_cat"] == "Worse than Expected"),
        "worse_hosp": sum(1 for x in clinics if x["hosp_cat"] == "Worse than Expected"),
        "worse_infection": sum(1 for x in clinics if x["sir_cat"] == "Worse than Expected"),
        "worse_transplant": sum(1 for x in clinics if x["pppw_cat"] == "Worse than Expected"),
        "low_star_1_2": sum(1 for x in clinics if x["stars"] is not None and x["stars"] <= 2),
        "nonprofit": sum(1 for x in clinics if x["profit"] == "Non-Profit"),
        "offers_home": sum(1 for x in clinics if x["offers_home"]),
        "late_shift": sum(1 for x in clinics if x["late_shift"]),
        "high_catheter_20plus": sum(1 for x in clinics if x["catheter"] is not None and x["catheter"] >= 20.0),
    }

    summary = {
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "runtime_sec": round(time.time() - t0, 1),
            "source": "CMS Provider Data Catalog — Dialysis Facility Compare (23ew-n7w9, clinical windows through Dec 2025)",
            "total_clinics": n,
        },
        "national": national,
        "duopoly": duopoly,
        "counts": counts,
        "by_profit": by_profit,
        "major_chains": major_chains,
        "by_state": by_state,
    }

    cols = [
        "ccn", "name", "city", "state", "zip", "profit", "chain", "stars", "stations",
        "offers_home", "late_shift", "mort", "mort_cat", "hosp", "hosp_cat", "sir",
        "fistula", "catheter", "pppw", "pppw_cat", "flags",
    ]
    rows_compact = [
        [
            x["ccn"], x["name"], x["city"], x["state"], x["zip"], x["profit"], x["chain"],
            x["stars"], x["stations"], 1 if x["offers_home"] else 0, 1 if x["late_shift"] else 0,
            x["mort"], x["mort_cat"], x["hosp"], x["hosp_cat"], x["sir"], x["fistula"],
            x["catheter"], x["pppw"], x["pppw_cat"], "|".join(x["flags"]),
        ]
        for x in clinics
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "summary-data.js").write_text(
        "window.CMS_DIALYSIS_DATA = " + json.dumps(summary, indent=2) + ";\n",
        encoding="utf-8",
    )
    (OUT_DIR / "clinics.json").write_text(
        json.dumps({"cols": cols, "rows": rows_compact}, separators=(",", ":")),
        encoding="utf-8",
    )

    if args.export_csv:
        csv_path = OUT_DIR / args.export_csv
        fields = [
            "ccn", "name", "city", "state", "zip", "profit", "chain", "stars", "stations",
            "late_shift", "pd", "home_hd", "mort", "mort_cat", "hosp", "hosp_cat", "readm",
            "sir", "sir_cat", "fistula", "catheter", "pppw", "pppw_cat", "fyswr", "smosr", "flags",
        ]
        opener = gzip.open if str(csv_path).endswith(".gz") else open
        with opener(csv_path, "wt", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(fields)
            for x in clinics:
                w.writerow(["|".join(x[k]) if k == "flags" else x[k] for k in fields])

    print(f"Dialysis clinics analyzed: {n:,} ({round(time.time()-t0, 1)}s)")
    print("Duopoly:", duopoly)
    print("Counts:", counts)
    print("\nFor-Profit vs Non-Profit:")
    for o in by_profit:
        print(f"  {o['group']:12s} | n={o['clinics']:4d} ({o['share_pct']:4.1f}%) | stars={o['avg_stars']} | mort={o['avg_mort']} (worse {o['pct_worse_mort']}%) | hosp={o['avg_hosp']} | SIR={o['avg_sir']} | cath={o['avg_catheter']}% | waitlist={o['avg_pppw']}% (low {o['pct_worse_pppw']}%) | home={o['pct_offers_home']}%")
    print("\nTop Chains (>=15 clinics):")
    for c in major_chains[:10]:
        print(f"  {c['group']:30s} | n={c['clinics']:4d} ({c['share_pct']:4.1f}%) | stars={c['avg_stars']} | mort={c['avg_mort']} | cath={c['avg_catheter']}% | waitlist={c['avg_pppw']}% | home={c['pct_offers_home']}% | late={c['pct_late_shift']}%")


if __name__ == "__main__":
    main()
