#!/usr/bin/env python3
"""
U.S. Public School District Finances Pipeline (Census F-33 FY2019 vs FY2024).

Downloads official plain-text U.S. Census Bureau Annual Survey of School System
Finances tables (zero API key, zero external packages):
  - FY2024: https://www2.census.gov/programs-surveys/school-finances/tables/2024/secondary-education-finance/elsec24t.txt (CSV)
  - FY2019: https://www2.census.gov/programs-surveys/school-finances/tables/2019/secondary-education-finance/elsec19t.txt (TSV)

Joins all operating K-12 public school districts (ENROLL > 0) on official 7-digit
NCESID across FY2019 (pre-COVID) and FY2024, computing:
  - Per-pupil current spending (PPCSTOT) & 5-year spending surge (%)
  - Classroom Instruction Share (% of current spending going to classrooms)
  - Administration Spending per pupil (General/Central + School Admin)
  - Post-COVID Enrollment Cliff (FY2019 -> FY2024 % student change)
  - Funding Source Split (% Local Property/Local, % State, % Federal)
  - Long-Term District Debt per student (DEBTOUT * 1000 / ENROLL)
  - Within-state inequality (90th vs 10th percentile per-pupil spending gap)

Accounting safeguards:
  - Excludes non-operating/zero-enrollment administrative units (ENROLL <= 0 or
    TCURSPND <= 0) from per-pupil rankings so regional service agencies (BOCES/
    ESAs with 0 enrolled students) never distort district medians.
  - Reports all Census dollar fields accurately (Census F-33 raw totals are in
    thousands of dollars; PPCSTOT/PPITOTAL/PPSGENAD/PPSSCHAD are exact dollars
    per pupil).
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import shutil
import statistics
import subprocess
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CURL_BIN = shutil.which("curl.exe") or shutil.which("curl") or "curl"

URL_2024 = "https://www2.census.gov/programs-surveys/school-finances/tables/2024/secondary-education-finance/elsec24t.txt"
URL_2019 = "https://www2.census.gov/programs-surveys/school-finances/tables/2019/secondary-education-finance/elsec19t.txt"

CACHE_DIR = Path(
    os.environ.get("SCHOOLS_CACHE_DIR", str(Path(tempfile.gettempdir()) / "schools_f33_cache"))
)

FIPS_TO_ST = {
    "01": ("AL", "Alabama"), "02": ("AK", "Alaska"), "04": ("AZ", "Arizona"), "05": ("AR", "Arkansas"),
    "06": ("CA", "California"), "08": ("CO", "Colorado"), "09": ("CT", "Connecticut"), "10": ("DE", "Delaware"),
    "11": ("DC", "District of Columbia"), "12": ("FL", "Florida"), "13": ("GA", "Georgia"), "15": ("HI", "Hawaii"),
    "16": ("ID", "Idaho"), "17": ("IL", "Illinois"), "18": ("IN", "Indiana"), "19": ("IA", "Iowa"),
    "20": ("KS", "Kansas"), "21": ("KY", "Kentucky"), "22": ("LA", "Louisiana"), "23": ("ME", "Maine"),
    "24": ("MD", "Maryland"), "25": ("MA", "Massachusetts"), "26": ("MI", "Michigan"), "27": ("MN", "Minnesota"),
    "28": ("MS", "Mississippi"), "29": ("MO", "Missouri"), "30": ("MT", "Montana"), "31": ("NE", "Nebraska"),
    "32": ("NV", "Nevada"), "33": ("NH", "New Hampshire"), "34": ("NJ", "New Jersey"), "35": ("NM", "New Mexico"),
    "36": ("NY", "New York"), "37": ("NC", "North Carolina"), "38": ("ND", "North Dakota"), "39": ("OH", "Ohio"),
    "40": ("OK", "Oklahoma"), "41": ("OR", "Oregon"), "42": ("PA", "Pennsylvania"), "44": ("RI", "Rhode Island"),
    "45": ("SC", "South Carolina"), "46": ("SD", "South Dakota"), "47": ("TN", "Tennessee"), "48": ("TX", "Texas"),
    "49": ("UT", "Utah"), "50": ("VT", "Vermont"), "51": ("VA", "Virginia"), "53": ("WA", "Washington"),
    "54": ("WV", "West Virginia"), "55": ("WI", "Wisconsin"), "56": ("WY", "Wyoming"),
}


def flt(v: Any) -> float:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return 0.0


def fetch_txt(filename: str, url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / filename
    if dst.exists() and dst.stat().st_size > 1_000_000:
        return dst
    tmp = dst.with_suffix(".tmp")
    code = subprocess.check_output(
        [CURL_BIN, "-sL", "-w", "%{http_code}", "-o", str(tmp), url], text=True
    ).strip()
    if code != "200" or not tmp.exists() or tmp.stat().st_size < 1_000_000:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed downloading {url}: HTTP {code}")
    tmp.replace(dst)
    print(f"Downloaded {filename} ({dst.stat().st_size:,} bytes)")
    return dst


def main() -> None:
    p24 = fetch_txt("elsec24t.txt", URL_2024)
    p19 = fetch_txt("elsec19t.txt", URL_2019)

    # 1. Index FY2019 by NCESID (TSV)
    d19: dict[str, dict[str, float]] = {}
    with open(p19, "r", encoding="latin-1", errors="replace") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            nid = (row.get("NCESID") or "").strip()
            enr = flt(row.get("ENROLL"))
            pp = flt(row.get("PPCSTOT"))
            if nid and nid != "N" and enr > 0 and pp > 0:
                d19[nid] = {
                    "enroll": enr,
                    "pp": pp,
                    "cur_k": flt(row.get("TCURSPND")),
                    "inst_k": flt(row.get("TCURINST")),
                }

    # 2. Parse FY2024 (CSV) & join FY2019
    records: list[dict[str, Any]] = []
    tot_enr24 = 0.0
    tot_rev_k = 0.0
    tot_fed_k = 0.0
    tot_st_k = 0.0
    tot_loc_k = 0.0
    tot_cur_k = 0.0
    tot_inst_k = 0.0
    tot_gen_k = 0.0
    tot_sch_k = 0.0
    tot_debt_k = 0.0
    tot_enr19_matched = 0.0
    tot_enr24_matched = 0.0

    with open(p24, "r", encoding="latin-1", errors="replace") as f:
        r = csv.DictReader(f)
        for row in r:
            fipst = (row.get("FIPST") or "").strip().zfill(2)
            if fipst not in FIPS_TO_ST:
                continue
            st, st_name = FIPS_TO_ST[fipst]
            enr = flt(row.get("ENROLL"))
            cur_k = flt(row.get("TCURSPND"))
            pp = flt(row.get("PPCSTOT"))
            # Exclude non-operating/zero-enrollment administrative agencies (ESAs/BOCES)
            if enr < 1 or cur_k <= 0 or pp <= 0:
                continue

            nid = (row.get("NCESID") or "").strip()
            name = (row.get("NAME") or "").strip().title()
            rev_k = flt(row.get("TOTALREV"))
            fed_k = flt(row.get("TFEDREV"))
            st_k = flt(row.get("TSTREV"))
            loc_k = flt(row.get("TLOCREV"))
            inst_k = flt(row.get("TCURINST"))
            gen_k = flt(row.get("TCURSGEN"))
            sch_k = flt(row.get("TCURSSCH"))
            debt_k = flt(row.get("DEBTOUT"))

            pp_inst = flt(row.get("PPITOTAL"))
            pp_sal = flt(row.get("PPISALWG"))
            pp_gen = flt(row.get("PPSGENAD"))
            pp_sch = flt(row.get("PPSSCHAD"))
            pp_adm = pp_gen + pp_sch
            inst_pct = round(inst_k / cur_k * 100.0, 1) if cur_k > 0 else None
            adm_pct = round((gen_k + sch_k) / cur_k * 100.0, 1) if cur_k > 0 else None
            loc_pct = round(loc_k / rev_k * 100.0, 1) if rev_k > 0 else None
            st_pct = round(st_k / rev_k * 100.0, 1) if rev_k > 0 else None
            fed_pct = round(fed_k / rev_k * 100.0, 1) if rev_k > 0 else None
            debt_pp = round(debt_k * 1000.0 / enr) if enr > 0 else 0

            tot_enr24 += enr; tot_rev_k += rev_k; tot_fed_k += fed_k; tot_st_k += st_k
            tot_loc_k += loc_k; tot_cur_k += cur_k; tot_inst_k += inst_k
            tot_gen_k += gen_k; tot_sch_k += sch_k; tot_debt_k += debt_k

            prev = d19.get(nid)
            enr19 = int(round(prev["enroll"])) if prev else None
            pp19 = int(round(prev["pp"])) if prev else None
            enr_chg = round((enr / prev["enroll"] - 1.0) * 100.0, 1) if prev and prev["enroll"] >= 20 else None
            pp_chg = round((pp / prev["pp"] - 1.0) * 100.0, 1) if prev and prev["pp"] > 0 else None
            if prev:
                tot_enr19_matched += prev["enroll"]
                tot_enr24_matched += enr

            records.append({
                "nid": nid,
                "name": name,
                "state": st,
                "enroll": int(round(enr)),
                "enroll19": enr19,
                "enr_chg_pct": enr_chg,
                "pp24": int(round(pp)),
                "pp19": pp19,
                "pp_chg_pct": pp_chg,
                "pp_inst": int(round(pp_inst)),
                "pp_sal": int(round(pp_sal)),
                "pp_adm": int(round(pp_adm)),
                "inst_pct": inst_pct,
                "adm_pct": adm_pct,
                "loc_pct": loc_pct,
                "st_pct": st_pct,
                "fed_pct": fed_pct,
                "debt_pp": int(debt_pp),
                "cur_m": round(cur_k / 1000.0, 2),
            })

    records.sort(key=lambda x: (-x["enroll"], x["name"]))

    # State summary + within-state p90/p10 funding inequality (for districts >= 500 students)
    by_st_map = defaultdict(list)
    for r in records:
        by_st_map[r["state"]].append(r)

    by_state = []
    for fipst, (st, st_name) in sorted(FIPS_TO_ST.items()):
        sub = by_st_map.get(st, [])
        if not sub:
            continue
        se = sum(x["enroll"] for x in sub)
        sc = sum(x["cur_m"] for x in sub)
        wpp = round(sc * 1e6 / se) if se > 0 else 0
        sub500 = sorted([x["pp24"] for x in sub if x["enroll"] >= 500])
        p10 = sub500[len(sub500) // 10] if len(sub500) >= 10 else None
        p90 = sub500[(9 * len(sub500)) // 10] if len(sub500) >= 10 else None
        ineq = round(p90 / p10, 2) if (p10 and p90 and p10 > 0) else None
        inst_med = round(statistics.median([x["inst_pct"] for x in sub if x["inst_pct"] is not None]), 1)
        loc_med = round(statistics.median([x["loc_pct"] for x in sub if x["loc_pct"] is not None]), 1)
        m19 = sum(x["enroll19"] for x in sub if x["enroll19"])
        m24 = sum(x["enroll"] for x in sub if x["enroll19"])
        st_enr_chg = round((m24 / m19 - 1.0) * 100.0, 1) if m19 > 0 else None
        by_state.append({
            "state": st, "name": st_name, "districts": len(sub), "enroll": se,
            "wavg_pp24": wpp, "p10_pp": p10, "p90_pp": p90, "ineq_ratio": ineq,
            "med_inst_pct": inst_med, "med_loc_pct": loc_med, "enr_chg_pct": st_enr_chg,
        })
    by_state.sort(key=lambda x: -x["wavg_pp24"])

    # Largest 25 U.S. School Districts (Post-COVID Enrollment Cliff + Spending)
    top_25_largest = records[:25]
    # Steepest enrollment drops among large districts (>= 25,000 students in 2019)
    big_drops = sorted(
        [r for r in records if r["enroll19"] and r["enroll19"] >= 25_000 and r["enr_chg_pct"] is not None],
        key=lambda x: x["enr_chg_pct"],
    )[:15]

    nat_wpp = round(tot_cur_k * 1000.0 / tot_enr24)
    nat_inst_pct = round(tot_inst_k / tot_cur_k * 100.0, 1)
    nat_adm_pct = round((tot_gen_k + tot_sch_k) / tot_cur_k * 100.0, 1)
    nat_enr_chg = round((tot_enr24_matched / tot_enr19_matched - 1.0) * 100.0, 1) if tot_enr19_matched else None
    enr_lost = int(round(tot_enr19_matched - tot_enr24_matched))

    summary = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "U.S. Census Bureau Annual Survey of School System Finances (F-33, FY2019 & FY2024)",
            "source_url": "https://www.census.gov/programs-surveys/school-finances.html",
        },
        "national": {
            "districts": len(records),
            "enroll24": int(round(tot_enr24)),
            "enr_chg_19_24_pct": nat_enr_chg,
            "students_lost_19_24": enr_lost,
            "total_rev_b": round(tot_rev_k / 1e6, 1),
            "cur_spend_b": round(tot_cur_k / 1e6, 1),
            "total_debt_b": round(tot_debt_k / 1e6, 1),
            "wavg_pp24": nat_wpp,
            "med_pp24": int(round(statistics.median([r["pp24"] for r in records]))),
            "inst_share_pct": nat_inst_pct,
            "adm_share_pct": nat_adm_pct,
            "loc_rev_pct": round(tot_loc_k / tot_rev_k * 100.0, 1),
            "st_rev_pct": round(tot_st_k / tot_rev_k * 100.0, 1),
            "fed_rev_pct": round(tot_fed_k / tot_rev_k * 100.0, 1),
        },
        "top_25_largest": top_25_largest,
        "big_enrollment_drops": big_drops,
        "by_state": by_state,
    }

    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ROOT / "summary-data.js").write_text(
        "window.SCHOOL_SUMMARY = " + json.dumps(summary, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    cols = ["nid", "name", "state", "enroll", "enroll19", "enr_chg_pct", "pp24", "pp19", "pp_chg_pct", "pp_inst", "pp_adm", "inst_pct", "adm_pct", "loc_pct", "st_pct", "fed_pct", "debt_pp"]
    rows = [[r[c] for c in cols] for r in records]
    (ROOT / "districts.json").write_text(
        json.dumps({"cols": cols, "rows": rows}, separators=(",", ":")),
        encoding="utf-8",
    )

    with gzip.open(ROOT / "census-school-districts-2019-2024.csv.gz", "wt", encoding="utf-8", newline="") as gz:
        w = csv.writer(gz)
        w.writerow(cols)
        for r in records:
            w.writerow([r[c] for c in cols])

    print(f"\n=== CENSUS F-33 SCHOOL FINANCES COMPLETE ({len(records):,} active districts, {int(tot_enr24):,} students) ===")
    print(f"Total Rev=${tot_rev_k/1e6:.1f}B | Cur Spend=${tot_cur_k/1e6:.1f}B | Wtd Per-Pupil=${nat_wpp:,} | Inst={nat_inst_pct}% | Admin={nat_adm_pct}% | Debt=${tot_debt_k/1e6:.1f}B")
    print(f"Matched 2019->2024 Enrollment: {nat_enr_chg:+.1f}% ({enr_lost:+,} students lost!)")
    print("\nTOP 5 HIGHEST-SPENDING STATES vs BOTTOM 5:")
    for s in by_state[:5]:
        print(f"  HIGH {s['name']:18s}: ${s['wavg_pp24']:,}/pupil | p90/p10={s['ineq_ratio']}x | enr {s['enr_chg_pct']}%")
    for s in by_state[-5:]:
        print(f"  LOW  {s['name']:18s}: ${s['wavg_pp24']:,}/pupil | p90/p10={s['ineq_ratio']}x | enr {s['enr_chg_pct']}%")
    print("\nTOP 8 LARGEST ENROLLMENT DROPS (>=25k students in 2019):")
    for r in big_drops[:8]:
        print(f"  {r['name'][:38]:38s} ({r['state']}): {r['enroll19']:,} -> {r['enroll']:,} ({r['enr_chg_pct']:+.1f}%) | ${r['pp19']:,} -> ${r['pp24']:,}/pupil ({r['pp_chg_pct']:+.1f}%)")


if __name__ == "__main__":
    main()
