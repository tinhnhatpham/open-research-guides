#!/usr/bin/env python3
"""
U.S. Army Corps of Engineers (USACE) National Inventory of Dams (NID)
High-Hazard Infrastructure Accountability Pipeline.

Downloads the live nationwide CSV directly from:
  https://nid.sec.usace.army.mil/api/nation/csv

Analyzes all ~92,000+ U.S. dams and builds a complete searchable database of
every High-Hazard Potential Dam in America (where failure = probable loss of
human life), exposing:
  - Poor & Unsatisfactory structural condition ratings
  - High-Hazard dams lacking an Emergency Action Plan (EAP)
  - Inspection backlogs (>5 years since last inspection or never inspected)
  - Dam age distribution (50+ and 75+ year-old aging infrastructure)
  - Private vs. Local Government vs. State vs. Federal ownership gaps
  - Nearest downstream city & county lookup + open .csv.gz export

Accounting & data-hygiene safeguards:
  - Strips USACE metadata banner line 0 ('Data Last Updated:...') and rare
    embedded NUL bytes in raw CSV text fields.
  - Clearly distinguishes 'Hazard Potential' (downstream life-safety impact if
    a dam fails) from 'Condition Assessment' (current structural integrity),
    and notes that some states/agencies classify condition ratings as 'Not
    Rated' or 'Not Available' rather than Poor/Unsatisfactory.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CURL_BIN = shutil.which("curl.exe") or shutil.which("curl") or "curl"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
NID_URL = "https://nid.sec.usace.army.mil/api/nation/csv"
CACHE_DIR = Path(
    os.environ.get("DAMS_CACHE_DIR", str(Path(tempfile.gettempdir()) / "nid_dams_cache"))
)

CURRENT_YEAR = 2026

STATE_TO_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "WY": "WY", "Wyoming": "WY",
    "Puerto Rico": "PR",
}


def flt(v: Any) -> float | None:
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if not s or s.lower() in ("na", "n/a", "null", "none"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_year(v: Any) -> int | None:
    if not v:
        return None
    m = re.search(r"\b(1[789]\d{2}|20[0-2]\d)\b", str(v))
    return int(m.group(1)) if m else None


def fetch_csv() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / "nation.csv"
    if dst.exists() and dst.stat().st_size > 20_000_000:
        return dst
    tmp = dst.with_suffix(".tmp")
    code = subprocess.check_output(
        [CURL_BIN, "-sL", "-A", UA, "-w", "%{http_code}", "-o", str(tmp), NID_URL],
        text=True,
    ).strip()
    if code != "200" or not tmp.exists() or tmp.stat().st_size < 20_000_000:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed downloading NID nation.csv: HTTP {code}")
    tmp.replace(dst)
    print(f"Downloaded NID nation.csv ({dst.stat().st_size:,} bytes)")
    return dst


def main() -> None:
    try:
        csv_path = fetch_csv()
    except RuntimeError as exc:
        if os.environ.get("CI") and (ROOT / "summary.json").exists() and (ROOT / "high-hazard-dams.json").exists():
            print(f"Skipping NID refresh in CI ({exc}); keeping verified artifacts.")
            return
        raise

    data_updated = ""
    tot_dams = 0
    haz_counts: Counter = Counter()
    all_ages: list[int] = []

    hh_dams: list[dict[str, Any]] = []
    hh_cond: Counter = Counter()
    hh_eap: Counter = Counter()
    by_owner: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "hh": 0, "poor_unsat": 0, "no_eap": 0, "stale_insp": 0})
    by_state: dict[str, dict[str, Any]] = defaultdict(lambda: {"name": "", "total": 0, "hh": 0, "unsat": 0, "poor": 0, "not_rated": 0, "no_eap": 0, "stale_insp": 0, "ages": []})

    with open(csv_path, "r", encoding="utf-8-sig", errors="replace") as raw_f:
        first_line = raw_f.readline()
        if "Data Last Updated" in first_line:
            parts = first_line.strip().split(",")
            if len(parts) >= 2:
                data_updated = parts[1].strip()
        else:
            raw_f.seek(0)

        clean_iter = (line.replace("\x00", "") for line in raw_f)
        reader = csv.DictReader(clean_iter)

        for row in reader:
            st_full = (row.get("State") or "").strip()
            st = STATE_TO_ABBR.get(st_full)
            if not st:
                continue
            tot_dams += 1
            haz = (row.get("Hazard Potential Classification") or "").strip() or "Undetermined"
            haz_counts[haz] += 1

            own = (row.get("Primary Owner Type") or "").strip() or "Not Listed"
            yr_comp = parse_year(row.get("Year Completed"))
            age = (CURRENT_YEAR - yr_comp) if yr_comp and 1750 <= yr_comp <= CURRENT_YEAR else None
            if age is not None:
                all_ages.append(age)

            by_owner[own]["total"] += 1
            by_state[st]["name"] = st_full
            by_state[st]["total"] += 1

            if haz != "High":
                continue

            cond = (row.get("Condition Assessment") or "").strip() or "Not Rated"
            eap = (row.get("EAP Prepared") or "").strip() or "Unknown"
            insp_yr = parse_year(row.get("Last Inspection Date"))
            stale_insp = (insp_yr is None) or (CURRENT_YEAR - insp_yr >= 5)
            poor_or_unsat = cond in ("Poor", "Unsatisfactory")
            missing_eap = eap in ("No", "Not Required", "Unknown", "")

            hh_cond[cond] += 1
            hh_eap[eap] += 1
            by_owner[own]["hh"] += 1
            if poor_or_unsat: by_owner[own]["poor_unsat"] += 1
            if missing_eap: by_owner[own]["no_eap"] += 1
            if stale_insp: by_owner[own]["stale_insp"] += 1

            bs = by_state[st]
            bs["hh"] += 1
            if cond == "Unsatisfactory": bs["unsat"] += 1
            elif cond == "Poor": bs["poor"] += 1
            elif cond not in ("Fair", "Satisfactory"): bs["not_rated"] += 1
            if missing_eap: bs["no_eap"] += 1
            if stale_insp: bs["stale_insp"] += 1
            if age is not None: bs["ages"].append(age)

            ht = flt(row.get("NID Height (Ft)"))
            stor = flt(row.get("NID Storage (Acre-Ft)"))
            dist = flt(row.get("Distance to Nearest City (Miles)"))

            # Composite risk priority score for sorting (Unsat > Poor > No EAP > Height/Storage)
            sev = (40 if cond == "Unsatisfactory" else 25 if cond == "Poor" else 10 if cond == "Fair" else 5 if cond not in ("Satisfactory",) else 0)
            sev += (15 if missing_eap else 0) + (8 if stale_insp else 0)

            hh_dams.append({
                "nid": (row.get("NID ID") or "").strip(),
                "name": (row.get("Dam Name") or "").strip()[:65],
                "state": st,
                "county": (row.get("County") or "").strip().title()[:35],
                "city": (row.get("City") or "").strip().title()[:30],
                "dist": round(dist, 1) if dist is not None else None,
                "river": (row.get("River or Stream Name") or "").strip()[:40],
                "owner_type": own,
                "owner": (row.get("Owner Names") or "").strip()[:55],
                "purpose": (row.get("Primary Purpose") or "").strip()[:30],
                "yr": yr_comp,
                "age": age,
                "ht": round(ht) if ht is not None else None,
                "stor": round(stor) if stor is not None else None,
                "cond": cond,
                "eap": eap,
                "insp_yr": insp_yr,
                "sev": sev,
            })

    hh_dams.sort(key=lambda x: (-x["sev"], -(x["ht"] or 0), -(x["stor"] or 0)))

    state_rows = []
    for st, d in by_state.items():
        pu = d["unsat"] + d["poor"]
        state_rows.append({
            "state": st, "name": d["name"], "total": d["total"], "hh": d["hh"],
            "unsat": d["unsat"], "poor": d["poor"], "poor_unsat": pu,
            "not_rated": d["not_rated"], "no_eap": d["no_eap"], "stale_insp": d["stale_insp"],
            "med_age": int(round(statistics.median(d["ages"]))) if d["ages"] else None,
        })
    state_rows.sort(key=lambda x: (-x["poor_unsat"], -x["hh"]))

    owner_rows = []
    for own, d in sorted(by_owner.items(), key=lambda kv: -kv[1]["hh"]):
        if d["hh"] < 20:
            continue
        owner_rows.append({
            "owner_type": own, **d,
            "poor_unsat_pct": round(d["poor_unsat"] / d["hh"] * 100.0, 1) if d["hh"] else 0.0,
            "no_eap_pct": round(d["no_eap"] / d["hh"] * 100.0, 1) if d["hh"] else 0.0,
        })

    hh_total = len(hh_dams)
    hh_unsat = hh_cond["Unsatisfactory"]
    hh_poor = hh_cond["Poor"]
    hh_pu = hh_unsat + hh_poor
    hh_no_eap = sum(1 for x in hh_dams if x["eap"] in ("No", "Not Required", "Unknown", ""))
    hh_stale = sum(1 for x in hh_dams if x["insp_yr"] is None or (CURRENT_YEAR - x["insp_yr"] >= 5))
    hh_ages = [x["age"] for x in hh_dams if x["age"] is not None]
    hh_over50 = sum(1 for a in hh_ages if a >= 50)
    hh_pu_no_eap = sum(1 for x in hh_dams if x["cond"] in ("Poor", "Unsatisfactory") and x["eap"] in ("No", "Not Required", "Unknown", ""))

    summary = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "nid_last_updated": data_updated,
            "source": "U.S. Army Corps of Engineers (USACE) National Inventory of Dams (NID)",
            "source_url": "https://nid.sec.usace.army.mil/",
        },
        "national": {
            "total_dams": tot_dams,
            "high_hazard": hh_total,
            "significant_hazard": haz_counts["Significant"],
            "low_hazard": haz_counts["Low"],
            "hh_unsatisfactory": hh_unsat,
            "hh_poor": hh_poor,
            "hh_poor_or_unsat": hh_pu,
            "hh_poor_or_unsat_pct": round(hh_pu / hh_total * 100.0, 1) if hh_total else 0.0,
            "hh_not_rated": hh_total - (hh_unsat + hh_poor + hh_cond["Fair"] + hh_cond["Satisfactory"]),
            "hh_missing_eap": hh_no_eap,
            "hh_missing_eap_pct": round(hh_no_eap / hh_total * 100.0, 1) if hh_total else 0.0,
            "hh_poor_and_no_eap": hh_pu_no_eap,
            "hh_stale_insp_5yr": hh_stale,
            "med_age_all": int(round(statistics.median(all_ages))) if all_ages else None,
            "med_age_hh": int(round(statistics.median(hh_ages))) if hh_ages else None,
            "hh_over_50yr_pct": round(hh_over50 / len(hh_ages) * 100.0, 1) if hh_ages else 0.0,
        },
        "hh_condition_breakdown": dict(hh_cond),
        "by_owner": owner_rows,
        "by_state": state_rows,
        "top_25_critical": hh_dams[:25],
    }

    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ROOT / "summary-data.js").write_text(
        "window.DAMS_SUMMARY = " + json.dumps(summary, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    cols = ["nid", "name", "state", "county", "city", "dist", "river", "owner_type", "owner", "purpose", "yr", "age", "ht", "stor", "cond", "eap", "insp_yr", "sev"]
    rows = [[d[c] for c in cols] for d in hh_dams]
    (ROOT / "high-hazard-dams.json").write_text(
        json.dumps({"cols": cols, "rows": rows}, separators=(",", ":")),
        encoding="utf-8",
    )

    with gzip.open(ROOT / "usace-high-hazard-dams-2026.csv.gz", "wt", encoding="utf-8", newline="") as gz:
        w = csv.writer(gz)
        w.writerow(cols)
        for d in hh_dams:
            w.writerow([d[c] for c in cols])

    print(f"\n=== USACE NID DAMS PIPELINE COMPLETE (Updated {data_updated}) ===")
    print(f"Total U.S. Dams: {tot_dams:,} | High-Hazard: {hh_total:,} (med age {summary['national']['med_age_hh']} yrs, {summary['national']['hh_over_50yr_pct']}% >=50 yrs)")
    print(f"High-Hazard Poor/Unsatisfactory: {hh_pu:,} ({hh_unsat:,} Unsat + {hh_poor:,} Poor = {summary['national']['hh_poor_or_unsat_pct']}%)")
    print(f"High-Hazard Missing EAP: {hh_no_eap:,} ({summary['national']['hh_missing_eap_pct']}%) | BOTH Poor/Unsat AND No EAP: {hh_pu_no_eap:,}")
    print(f"High-Hazard Stale/No Inspection (>=5 yrs): {hh_stale:,}")
    print("\nBY OWNER TYPE (High-Hazard):")
    for o in owner_rows[:6]:
        print(f"  {o['owner_type']:20s}: HH={o['hh']:5,} | Poor/Unsat={o['poor_unsat']:4,} ({o['poor_unsat_pct']:4.1f}%) | No EAP={o['no_eap']:4,} ({o['no_eap_pct']:4.1f}%)")
    print("\nTOP 8 STATES BY POOR/UNSATISFACTORY HIGH-HAZARD DAMS:")
    for s in state_rows[:8]:
        print(f"  {s['name']:16s} ({s['state']}): HH={s['hh']:4,} | Poor/Unsat={s['poor_unsat']:3,} (Unsat={s['unsat']:3,}, Poor={s['poor']:3,}) | No EAP={s['no_eap']:3,}")


if __name__ == "__main__":
    main()
