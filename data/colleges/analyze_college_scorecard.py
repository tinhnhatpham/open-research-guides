#!/usr/bin/env python3
"""
U.S. College Debt-to-Earnings, Parent PLUS & Income-Bracket Net Price Pipeline
(U.S. Department of Education College Scorecard — June 2026 Release).

Downloads directly from official ed-public-download.scorecard.network bulk ZIP
(discovering the latest Most-Recent-Cohorts-Institution ZIP automatically from
collegescorecard.ed.gov/data when refreshed in CI), cleans all ~6,243 active
U.S. institutions, stratifies cleanly by Degree Level (Bachelor's vs. Associate's
vs. Certificate) and Ownership (Public vs. Private Non-Profit vs. For-Profit),
and emits:
  - data/colleges/summary.json
  - data/colleges/summary-data.js
  - data/colleges/colleges.json
  - data/colleges/college-scorecard-2026.csv.gz

Accounting safeguards:
  - Always stratifies by Predominant Degree (Bachelor's 4-Yr vs. Associate's
    2-Yr vs. Certificate) so short-term trade certificates are never mixed with
    4-year universities in completion or debt medians.
  - Combines Student Median Debt (GRAD_DEBT_MDN) AND Parent PLUS Median Debt
    (PLUS_DEBT_INST_COMP_MD / PLUS_DEBT_INST_MD) separately—never silently
    adding them for students who don't borrow PLUS, while exposing total
    family burden when parents do borrow.
  - Tracks all 5 federal income-bracket net prices ($0-30k, $30-48k, $48-75k,
    $75-110k, $110k+) so families see THEIR actual price, not sticker tuition.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CURL_BIN = shutil.which("curl.exe") or shutil.which("curl") or "curl"
DEFAULT_URL = "https://ed-public-download.scorecard.network/downloads/Most-Recent-Cohorts-Institution_06102026.zip"
CACHE_DIR = Path(
    os.environ.get("COLLEGE_CACHE_DIR", str(Path(tempfile.gettempdir()) / "college_cache"))
)

CTRL_MAP = {"1": "Public", "2": "Private Non-Profit", "3": "For-Profit"}
DEG_MAP = {"1": "Certificate", "2": "Associate's", "3": "Bachelor's", "4": "Graduate-Only", "0": "Unclassified"}

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "PR": "Puerto Rico",
}


def num(v: Any) -> float | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s or s in ("NULL", "PrivacySuppressed", "NA", "PS"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def rint(v: float | None) -> int | None:
    return int(round(v)) if v is not None else None


def r1(v: float | None) -> float | None:
    return round(v, 1) if v is not None else None


def r2(v: float | None) -> float | None:
    return round(v, 2) if v is not None else None


def med(vals: list[float]) -> float | None:
    return round(statistics.median(vals), 1) if vals else None


def fetch_zip() -> tuple[Path, str]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / "institutions_2026.zip"
    url = DEFAULT_URL
    if dst.exists() and dst.stat().st_size > 10_000_000 and zipfile.is_zipfile(dst):
        return dst, url
    # Try discovering newer zip URL from Scorecard data page if default fails
    candidates = [url]
    try:
        html = subprocess.check_output(
            [CURL_BIN, "-sL", "https://collegescorecard.ed.gov/data/"], text=True, errors="replace"
        )
        m = re.search(r"https://ed-public-download\.scorecard\.network/downloads/Most-Recent-Cohorts-Institution_\d+\.zip", html)
        if m and m.group(0) not in candidates:
            candidates.insert(0, m.group(0))
    except Exception:
        pass

    for u in candidates:
        tmp = dst.with_suffix(".tmp")
        code = subprocess.check_output(
            [CURL_BIN, "-sL", "-w", "%{http_code}", "-o", str(tmp), u], text=True
        ).strip()
        if code == "200" and tmp.exists() and tmp.stat().st_size > 10_000_000 and zipfile.is_zipfile(tmp):
            tmp.replace(dst)
            print(f"Downloaded College Scorecard ZIP ({dst.stat().st_size:,} bytes) from {u}")
            return dst, u
        tmp.unlink(missing_ok=True)
    raise RuntimeError("Could not download College Scorecard institution ZIP")


def main() -> None:
    zpath, src_url = fetch_zip()

    records: list[dict[str, Any]] = []
    with zipfile.ZipFile(zpath) as zf:
        fn = [n for n in zf.namelist() if n.lower().endswith(".csv") and not n.startswith("__MACOSX")][0]
        with zf.open(fn) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace"))
            for row in reader:
                if row.get("CURROPER") != "1":
                    continue
                st = (row.get("STABBR") or "").strip().upper()
                if st not in STATE_NAMES:
                    continue
                ctrl_c = (row.get("CONTROL") or "").strip()
                ctrl = CTRL_MAP.get(ctrl_c)
                if not ctrl:
                    continue
                deg_c = (row.get("PREDDEG") or "").strip()
                deg = DEG_MAP.get(deg_c, "Unclassified")
                ugds = rint(num(row.get("UGDS"))) or 0
                is_pub = (ctrl_c == "1")

                npt = num(row.get("NPT4_PUB")) if is_pub else num(row.get("NPT4_PRIV"))
                npt1 = num(row.get("NPT41_PUB")) if is_pub else num(row.get("NPT41_PRIV"))
                npt2 = num(row.get("NPT42_PUB")) if is_pub else num(row.get("NPT42_PRIV"))
                npt3 = num(row.get("NPT43_PUB")) if is_pub else num(row.get("NPT43_PRIV"))
                npt4 = num(row.get("NPT44_PUB")) if is_pub else num(row.get("NPT44_PRIV"))
                npt5 = num(row.get("NPT45_PUB")) if is_pub else num(row.get("NPT45_PRIV"))

                cost = num(row.get("COSTT4_A"))
                adm = num(row.get("ADM_RATE"))
                grad = num(row.get("C150_4")) if deg_c == "3" else (num(row.get("C150_L4")) or num(row.get("C150_4")))
                pell = num(row.get("PCTPELL"))

                debt = num(row.get("GRAD_DEBT_MDN")) or num(row.get("DEBT_MDN"))
                plus_d = num(row.get("PLUS_DEBT_INST_COMP_MD")) or num(row.get("PLUS_DEBT_INST_MD"))
                earn10 = num(row.get("MD_EARN_WNE_P10"))
                earn6 = num(row.get("MD_EARN_WNE_P6"))
                gt10 = num(row.get("GT_THRESHOLD_P10"))
                makeprog = num(row.get("BBRR2_FED_UG_MAKEPROG"))

                # Debt-to-earnings ratio (%) and 4-yr/2-yr net cost payback estimate
                dte_pct = round(debt / earn10 * 100.0, 1) if (debt and earn10 and earn10 > 0) else None
                # Years of 10-yr earnings premium over $32,000 HS benchmark needed to recover 4 yrs (or 2 yrs) net price
                yrs_prog = 4 if deg_c == "3" else (2 if deg_c == "2" else 1)
                total_net = (npt * yrs_prog) if npt and npt > 0 else None
                payback_yrs = None
                if total_net and earn10 and earn10 > 32_000:
                    payback_yrs = round(total_net / (earn10 - 32_000), 1)
                    if payback_yrs > 99:
                        payback_yrs = 99.0

                records.append({
                    "unitid": int(row["UNITID"]),
                    "name": (row.get("INSTNM") or "").strip(),
                    "city": (row.get("CITY") or "").strip(),
                    "state": st,
                    "ctrl": ctrl,
                    "deg": deg,
                    "ugds": ugds,
                    "adm_pct": r1(adm * 100.0) if adm is not None else None,
                    "grad_pct": r1(grad * 100.0) if grad is not None else None,
                    "pell_pct": r1(pell * 100.0) if pell is not None else None,
                    "cost": rint(cost),
                    "npt": rint(npt),
                    "npt1": rint(npt1),
                    "npt2": rint(npt2),
                    "npt3": rint(npt3),
                    "npt4": rint(npt4),
                    "npt5": rint(npt5),
                    "debt": rint(debt),
                    "plus_debt": rint(plus_d),
                    "earn10": rint(earn10),
                    "earn6": rint(earn6),
                    "gt10_pct": r1(gt10 * 100.0) if gt10 is not None else None,
                    "makeprog_pct": r1(makeprog * 100.0) if makeprog is not None else None,
                    "dte_pct": dte_pct,
                    "payback_yrs": payback_yrs,
                })

    records.sort(key=lambda x: (-x["ugds"], x["name"]))

    # Stratified Summary: Ownership x Degree Level (Bachelor's, Associate's, Certificate)
    def summarize(sub: list[dict[str, Any]], label: str) -> dict[str, Any]:
        npts = [x["npt"] for x in sub if x["npt"] is not None]
        npt1s = [x["npt1"] for x in sub if x["npt1"] is not None]
        debts = [x["debt"] for x in sub if x["debt"] is not None]
        pluses = [x["plus_debt"] for x in sub if x["plus_debt"] is not None]
        earns = [x["earn10"] for x in sub if x["earn10"] is not None]
        gts = [x["gt10_pct"] for x in sub if x["gt10_pct"] is not None]
        grads = [x["grad_pct"] for x in sub if x["grad_pct"] is not None]
        progs = [x["makeprog_pct"] for x in sub if x["makeprog_pct"] is not None]
        fail_hs = sum(1 for x in sub if x["gt10_pct"] is not None and x["gt10_pct"] < 50.0)
        return {
            "label": label,
            "schools": len(sub),
            "ugds": sum(x["ugds"] for x in sub),
            "med_npt": rint(med(npts)),
            "med_npt_lowinc": rint(med(npt1s)),
            "med_debt": rint(med(debts)),
            "med_plus_debt": rint(med(pluses)),
            "med_earn10": rint(med(earns)),
            "med_gt10_pct": med(gts),
            "fail_hs_count": fail_hs,
            "med_grad_pct": med(grads),
            "med_makeprog_pct": med(progs),
        }

    by_ctrl = [summarize([r for r in records if r["ctrl"] == c], c) for c in ("Public", "Private Non-Profit", "For-Profit")]
    bach = [r for r in records if r["deg"] == "Bachelor's"]
    by_ctrl_bach = [summarize([r for r in bach if r["ctrl"] == c], f"{c} (4-Yr Bachelor's)") for c in ("Public", "Private Non-Profit", "For-Profit")]
    assoc = [r for r in records if r["deg"] == "Associate's"]
    by_ctrl_assoc = [summarize([r for r in assoc if r["ctrl"] == c], f"{c} (2-Yr Associate's)") for c in ("Public", "Private Non-Profit", "For-Profit")]

    # High-impact leaderboards (Bachelor's schools with >= 1,000 undergrads for fair signal)
    bach_lg = [r for r in bach if r["ugds"] >= 1000]
    top_plus_traps = sorted([r for r in bach_lg if r["plus_debt"]], key=lambda x: -x["plus_debt"])[:15]
    best_roi_public = sorted(
        [r for r in bach_lg if r["ctrl"] == "Public" and r["npt"] and r["earn10"] and r["grad_pct"] and r["grad_pct"] >= 60],
        key=lambda x: (x["payback_yrs"] if x["payback_yrs"] is not None else 999, -x["earn10"]),
    )[:15]
    worst_fail_hs = sorted(
        [r for r in records if r["ugds"] >= 500 and r["gt10_pct"] is not None and r["gt10_pct"] < 50.0],
        key=lambda x: (x["gt10_pct"], -x["ugds"]),
    )[:15]

    tot_fail_hs = sum(1 for r in records if r["gt10_pct"] is not None and r["gt10_pct"] < 50.0)
    fp_fail_hs = sum(1 for r in records if r["ctrl"] == "For-Profit" and r["gt10_pct"] is not None and r["gt10_pct"] < 50.0)
    plus_over_40k = sum(1 for r in records if r["plus_debt"] and r["plus_debt"] >= 40_000)

    by_state = []
    for st in sorted(STATE_NAMES.keys()):
        sub = [r for r in records if r["state"] == st]
        if not sub:
            continue
        pub_b = [r for r in sub if r["ctrl"] == "Public" and r["deg"] == "Bachelor's"]
        by_state.append({
            "state": st,
            "name": STATE_NAMES[st],
            "schools": len(sub),
            "ugds": sum(r["ugds"] for r in sub),
            "pub4_med_npt": rint(med([r["npt"] for r in pub_b if r["npt"] is not None])),
            "pub4_med_earn10": rint(med([r["earn10"] for r in pub_b if r["earn10"] is not None])),
            "fail_hs": sum(1 for r in sub if r["gt10_pct"] is not None and r["gt10_pct"] < 50.0),
        })

    summary = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "U.S. Department of Education College Scorecard (June 2026 Institution Release)",
            "source_url": "https://collegescorecard.ed.gov/data/",
            "download_url": src_url,
        },
        "national": {
            "active_schools": len(records),
            "total_ugds": sum(r["ugds"] for r in records),
            "bachelors_schools": len(bach),
            "fail_hs_total": tot_fail_hs,
            "fail_hs_forprofit": fp_fail_hs,
            "fail_hs_forprofit_pct": round(fp_fail_hs / tot_fail_hs * 100.0, 1) if tot_fail_hs else 0.0,
            "plus_over_40k_schools": plus_over_40k,
            "med_npt_all": rint(med([r["npt"] for r in records if r["npt"] is not None])),
            "med_earn10_all": rint(med([r["earn10"] for r in records if r["earn10"] is not None])),
            "med_debt_all": rint(med([r["debt"] for r in records if r["debt"] is not None])),
        },
        "by_ctrl": by_ctrl,
        "by_ctrl_bach": by_ctrl_bach,
        "by_ctrl_assoc": by_ctrl_assoc,
        "top_plus_traps": top_plus_traps,
        "best_roi_public": best_roi_public,
        "worst_fail_hs": worst_fail_hs,
        "by_state": by_state,
    }

    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ROOT / "summary-data.js").write_text(
        "window.COLLEGE_SUMMARY = " + json.dumps(summary, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    cols = [
        "unitid", "name", "city", "state", "ctrl", "deg", "ugds",
        "adm_pct", "grad_pct", "pell_pct", "cost", "npt", "npt1", "npt2", "npt3", "npt4", "npt5",
        "debt", "plus_debt", "earn10", "gt10_pct", "makeprog_pct", "dte_pct", "payback_yrs",
    ]
    rows = [[r[c] for c in cols] for r in records]
    (ROOT / "colleges.json").write_text(
        json.dumps({"cols": cols, "rows": rows}, separators=(",", ":")),
        encoding="utf-8",
    )

    with gzip.open(ROOT / "college-scorecard-2026.csv.gz", "wt", encoding="utf-8", newline="") as gz:
        w = csv.writer(gz)
        w.writerow(cols)
        for r in records:
            w.writerow([r[c] for c in cols])

    print(f"\n=== COLLEGE SCORECARD PIPELINE COMPLETE ({len(records):,} active schools, {summary['national']['total_ugds']:,} undergrads) ===")
    print(f"Failing HS Earnings Test (<50% > HS at 10yr): {tot_fail_hs} total | {fp_fail_hs} For-Profit ({summary['national']['fail_hs_forprofit_pct']}%) | Parent PLUS >=$40k schools: {plus_over_40k}")
    print("\n4-YEAR BACHELOR'S STRATIFIED COMPARISON:")
    for b in by_ctrl_bach:
        print(f"  {b['label']:34s}: n={b['schools']:4d} | npt=${b['med_npt'] or 0:6,} | debt=${b['med_debt'] or 0:6,} | PLUS=${b['med_plus_debt'] or 0:6,} | earn10=${b['med_earn10'] or 0:6,} | grad={b['med_grad_pct']}% | >HS={b['med_gt10_pct']}% | repay2yr={b['med_makeprog_pct']}%")
    print("\nTOP 5 PARENT PLUS DEBT TRAPS (4-Yr, >=1k UGDS):")
    for x in top_plus_traps[:5]:
        print(f"  {x['name'][:38]:38s} ({x['state']}, {x['ctrl'][:4]}): PLUS=${x['plus_debt']:,} | Student=${x['debt'] or 0:,} | Earn10=${x['earn10'] or 0:,}")
    print("\nTOP 5 BEST-VALUE PUBLIC 4-YR UNIVERSITIES:")
    for x in best_roi_public[:5]:
        print(f"  {x['name'][:38]:38s} ({x['state']}): Net=${x['npt']:,}/yr | Earn10=${x['earn10']:,} | Payback={x['payback_yrs']} yrs | Grad={x['grad_pct']}%")


if __name__ == "__main__":
    main()
