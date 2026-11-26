#!/usr/bin/env python3
"""
NCUA 5300 Call Reports U.S. Credit Union Accountability Pipeline (FY2021 & FY2025).

Downloads official NCUA Quarterly Call Report ZIP archives directly from ncua.gov:
  - FY2025 (Q4): https://ncua.gov/files/publications/analysis/call-report-data-2025-12.zip
  - FY2021 (Q4): https://ncua.gov/files/publications/analysis/call-report-data-2021-12.zip

Joins FOICU, FS220, FS220A, and FS220B across all ~4,374 federally insured U.S.
credit unions (~144M members), computing:
  - Effective deposit/dividend rate paid: (ACCT_380 + ACCT_381) / ACCT_018
  - Asset yield: ACCT_115 / ACCT_010
  - 2021->2025 Rate Pass-Through ("Deposit Beta"): delta_dep_rate / delta_asset_yield
  - Fee Income & Fee Income per Member: ACCT_131 / ACCT_083
  - Uninsured Shares %: ACCT_068A / ACCT_018
  - Net Worth Ratio: ACCT_998 / 100
  - Actual Credit Card (ACCT_521), New Auto (ACCT_523), and Used Auto (ACCT_524) APRs

Direct apples-to-apples comparison against our FDIC Bank pipeline (Guide #10):
  FDIC All 4,204 Banks (1.99% wavg deposit rate; Big 4 1.71%; 45.2% megabank uninsured)
  vs. NCUA All 4,374 Credit Unions!
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import os
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
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

URL_2025 = "https://ncua.gov/files/publications/analysis/call-report-data-2025-12.zip"
URL_2021 = "https://ncua.gov/files/publications/analysis/call-report-data-2021-12.zip"

CACHE_DIR = Path(
    os.environ.get("NCUA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "ncua_cache"))
)

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


def flt(v: Any) -> float:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return 0.0


def rate_bps(v: Any) -> float | None:
    x = flt(v)
    if x <= 0 or x > 3600:
        return None
    return round(x / 100.0, 2)


def med(vals: list[float]) -> float | None:
    return round(statistics.median(vals), 2) if vals else None


def tier_of(assets: float) -> str:
    if assets >= 10e9:
        return "Mega CU ($10B+)"
    if assets >= 1e9:
        return "Large CU ($1B–$10B)"
    if assets >= 100e6:
        return "Mid-Size CU ($100M–$1B)"
    return "Small Community CU (<$100M)"


def fetch_zip(filename: str, url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / filename
    if dst.exists() and dst.stat().st_size > 2_000_000 and zipfile.is_zipfile(dst):
        return dst
    tmp = dst.with_suffix(".tmp")
    code = subprocess.check_output(
        [CURL_BIN, "-sL", "-A", UA, "-w", "%{http_code}", "-o", str(tmp), url],
        text=True,
    ).strip()
    if code != "200" or not tmp.exists() or not zipfile.is_zipfile(tmp):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed downloading {url}: HTTP {code}")
    tmp.replace(dst)
    print(f"Downloaded {filename} ({dst.stat().st_size:,} bytes)")
    return dst


def load_ncua_year(zpath: Path) -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(zpath) as zf:
        with zf.open("FOICU.txt") as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", errors="replace")):
                cid = str(row.get("CU_NUMBER") or "").strip()
                if not cid:
                    continue
                data[cid] = {
                    "cu_num": cid,
                    "name": (row.get("CU_NAME") or "").strip().title(),
                    "city": (row.get("CITY") or "").strip().title(),
                    "state": (row.get("STATE") or "").strip().upper(),
                    "charter_yr": int(flt(row.get("YEAR_OPENED"))) if flt(row.get("YEAR_OPENED")) > 1850 else None,
                }

        def merge_table(tname: str, fields: list[str]) -> None:
            if tname not in zf.namelist():
                return
            with zf.open(tname) as raw:
                r = csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", errors="replace"))
                cmap = {c.upper(): c for c in (r.fieldnames or [])}
                for row in r:
                    cid = str(row.get(cmap.get("CU_NUMBER", "CU_NUMBER")) or "").strip()
                    if cid not in data:
                        continue
                    d = data[cid]
                    for f in fields:
                        col = cmap.get(f)
                        if col:
                            d[f] = flt(row.get(col))

        merge_table("FS220.txt", ["ACCT_010", "ACCT_018", "ACCT_025B", "ACCT_083", "ACCT_380", "ACCT_521", "ACCT_523", "ACCT_524"])
        merge_table("FS220A.txt", ["ACCT_110", "ACCT_115", "ACCT_131", "ACCT_350", "ACCT_381", "ACCT_661A", "ACCT_998"])
        merge_table("FS220B.txt", ["ACCT_068A"])
    return data


def main() -> None:
    try:
        z25 = fetch_zip("ncua_2025_12.zip", URL_2025)
        z21 = fetch_zip("ncua_2021_12.zip", URL_2021)
    except RuntimeError as exc:
        if os.environ.get("CI") and (ROOT / "summary.json").exists() and (ROOT / "credit-unions.json").exists():
            print(f"Skipping NCUA refresh in CI ({exc}); keeping verified artifacts.")
            return
        raise

    d25 = load_ncua_year(z25)
    d21 = load_ncua_year(z21)

    records: list[dict[str, Any]] = []
    tot_assets = 0.0
    tot_shares = 0.0
    tot_members = 0.0
    tot_div = 0.0
    tot_fees = 0.0
    tot_netinc = 0.0
    tot_unins = 0.0
    tot_intinc = 0.0

    for cid, r in d25.items():
        if r["state"] not in STATE_NAMES:
            continue
        assets = r.get("ACCT_010", 0.0)
        shares = r.get("ACCT_018", 0.0)
        members = r.get("ACCT_083", 0.0)
        if assets <= 0 or shares <= 0 or members <= 0:
            continue

        div_paid = r.get("ACCT_380", 0.0) + r.get("ACCT_381", 0.0)
        int_inc = r.get("ACCT_115", 0.0)
        fees = r.get("ACCT_131", 0.0)
        netinc = r.get("ACCT_661A", 0.0)
        unins = r.get("ACCT_068A", 0.0)
        nwr = r.get("ACCT_998", 0.0) / 100.0 if r.get("ACCT_998", 0.0) > 0 else None

        dep_rate = (div_paid / shares * 100.0) if shares > 0 else 0.0
        asset_yld = (int_inc / assets * 100.0) if assets > 0 else 0.0
        if dep_rate > 12.0 or dep_rate < 0:
            continue
        unins_pct = min(100.0, max(0.0, unins / shares * 100.0)) if shares > 0 else 0.0
        fee_per_mem = fees / members if members > 0 else 0.0

        # Match FY2021 for pass-through ("Deposit Beta")
        p = d21.get(cid)
        dep21 = None
        beta = None
        if p and p.get("ACCT_018", 0.0) > 0 and p.get("ACCT_010", 0.0) > 0:
            div21 = p.get("ACCT_380", 0.0) + p.get("ACCT_381", 0.0)
            dep21 = div21 / p["ACCT_018"] * 100.0
            yld21 = p.get("ACCT_115", 0.0) / p["ACCT_010"] * 100.0
            dy = asset_yld - yld21
            if dy >= 0.5:
                b_raw = (dep_rate - dep21) / dy * 100.0
                if -50 <= b_raw <= 250:
                    beta = round(b_raw, 1)

        tot_assets += assets; tot_shares += shares; tot_members += members
        tot_div += div_paid; tot_fees += fees; tot_netinc += netinc
        tot_unins += unins; tot_intinc += int_inc

        records.append({
            "cu_num": int(cid) if cid.isdigit() else cid,
            "name": r["name"][:55],
            "city": r["city"][:25],
            "state": r["state"],
            "tier": tier_of(assets),
            "assets_m": round(assets / 1e6, 1),
            "shares_m": round(shares / 1e6, 1),
            "members": int(round(members)),
            "dep_rate": round(dep_rate, 2),
            "dep_rate21": round(dep21, 2) if dep21 is not None else None,
            "asset_yld": round(asset_yld, 2),
            "beta": beta,
            "fees_m": round(fees / 1e6, 2),
            "fee_per_mem": round(fee_per_mem, 1),
            "unins_pct": round(unins_pct, 1),
            "net_worth": round(nwr, 2) if nwr is not None else None,
            "cc_apr": rate_bps(r.get("ACCT_521")),
            "new_auto": rate_bps(r.get("ACCT_523")),
            "used_auto": rate_bps(r.get("ACCT_524")),
        })

    records.sort(key=lambda x: -x["assets_m"])

    # Tier breakdown
    tier_order = ["Mega CU ($10B+)", "Large CU ($1B–$10B)", "Mid-Size CU ($100M–$1B)", "Small Community CU (<$100M)"]
    by_tier = []
    for t in tier_order:
        sub = [x for x in records if x["tier"] == t]
        if not sub:
            continue
        sh_m = sum(x["shares_m"] for x in sub)
        mem_t = sum(x["members"] for x in sub)
        fee_t = sum(x["fees_m"] for x in sub)
        wdep = sum(x["dep_rate"] * x["shares_m"] for x in sub) / sh_m if sh_m else 0.0
        by_tier.append({
            "tier": t,
            "count": len(sub),
            "shares_b": round(sh_m / 1000.0, 1),
            "share_of_us_pct": round(sh_m / (tot_shares / 1e6) * 100.0, 1),
            "members_m": round(mem_t / 1e6, 2),
            "wavg_dep_rate": round(wdep, 2),
            "med_dep_rate": med([x["dep_rate"] for x in sub]),
            "med_beta": med([x["beta"] for x in sub if x["beta"] is not None]),
            "fees_b": round(fee_t / 1000.0, 2),
            "wavg_fee_per_mem": round(fee_t * 1e6 / mem_t, 1) if mem_t else 0.0,
            "med_unins_pct": med([x["unins_pct"] for x in sub]),
            "med_new_auto": med([x["new_auto"] for x in sub if x["new_auto"] is not None]),
            "med_cc_apr": med([x["cc_apr"] for x in sub if x["cc_apr"] is not None]),
        })

    wavg_dep = round(tot_div / tot_shares * 100.0, 2)
    wavg_yld = round(tot_intinc / tot_assets * 100.0, 2)
    dep_rates_sorted = sorted(x["dep_rate"] for x in records)
    p75_dep = round(dep_rates_sorted[(3 * len(dep_rates_sorted)) // 4], 2)

    by_state = []
    for st in sorted(STATE_NAMES.keys()):
        sub = [x for x in records if x["state"] == st]
        if not sub:
            continue
        by_state.append({
            "state": st, "name": STATE_NAMES[st], "count": len(sub),
            "members": sum(x["members"] for x in sub),
            "med_dep_rate": med([x["dep_rate"] for x in sub]),
            "med_new_auto": med([x["new_auto"] for x in sub if x["new_auto"] is not None]),
        })

    summary = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "National Credit Union Administration (NCUA) 5300 Call Reports (Q4 2021 & Q4 2025)",
            "source_url": "https://ncua.gov/analysis/credit-union-corporate-call-report-data/quarterly-data",
        },
        "national": {
            "credit_unions": len(records),
            "members_m": round(tot_members / 1e6, 2),
            "assets_t": round(tot_assets / 1e12, 2),
            "shares_t": round(tot_shares / 1e12, 2),
            "dividends_paid_b": round(tot_div / 1e9, 2),
            "fees_b": round(tot_fees / 1e9, 2),
            "fee_per_member": round(tot_fees / tot_members, 1) if tot_members else 0.0,
            "net_income_b": round(tot_netinc / 1e9, 2),
            "wavg_dep_rate": wavg_dep,
            "med_dep_rate": med([x["dep_rate"] for x in records]),
            "p75_dep_rate": p75_dep,
            "wavg_asset_yld": wavg_yld,
            "med_beta": med([x["beta"] for x in records if x["beta"] is not None]),
            "wavg_unins_pct": round(tot_unins / tot_shares * 100.0, 1),
            "med_unins_pct": med([x["unins_pct"] for x in records]),
            "med_new_auto": med([x["new_auto"] for x in records if x["new_auto"] is not None]),
            "med_used_auto": med([x["used_auto"] for x in records if x["used_auto"] is not None]),
            "med_cc_apr": med([x["cc_apr"] for x in records if x["cc_apr"] is not None]),
        },
        "by_tier": by_tier,
        "top_15_largest": records[:15],
        "top_15_savers": sorted([x for x in records if x["assets_m"] >= 1000], key=lambda z: -z["dep_rate"])[:15],
        "by_state": by_state,
    }

    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ROOT / "summary-data.js").write_text(
        "window.NCUA_SUMMARY = " + json.dumps(summary, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    cols = ["cu_num", "name", "city", "state", "tier", "assets_m", "shares_m", "members", "dep_rate", "dep_rate21", "asset_yld", "beta", "fees_m", "fee_per_mem", "unins_pct", "net_worth", "cc_apr", "new_auto", "used_auto"]
    rows = [[r[c] for c in cols] for r in records]
    (ROOT / "credit-unions.json").write_text(
        json.dumps({"cols": cols, "rows": rows}, separators=(",", ":")),
        encoding="utf-8",
    )

    with gzip.open(ROOT / "ncua-credit-unions-2021-2025.csv.gz", "wt", encoding="utf-8", newline="") as gz:
        w = csv.writer(gz)
        w.writerow(cols)
        for r in records:
            w.writerow([r[c] for c in cols])

    print(f"\n=== NCUA CREDIT UNIONS PIPELINE COMPLETE ({len(records):,} CUs, {tot_members/1e6:.2f}M members) ===")
    print(f"Assets=${tot_assets/1e12:.2f}T | Shares=${tot_shares/1e12:.2f}T | Wtd Dep Rate={wavg_dep}% (med={summary['national']['med_dep_rate']}%, p75={p75_dep}%) | Beta={summary['national']['med_beta']}%")
    print(f"Fees=${tot_fees/1e9:.2f}B (${summary['national']['fee_per_member']}/member) | Uninsured={summary['national']['wavg_unins_pct']}% wavg ({summary['national']['med_unins_pct']}% med)")
    print(f"Loan APR Medians: New Auto={summary['national']['med_new_auto']}% | Used Auto={summary['national']['med_used_auto']}% | Credit Card={summary['national']['med_cc_apr']}%")
    print("\nBY TIER:")
    for t in by_tier:
        print(f"  {t['tier']:28s}: n={t['count']:4d} | wdep={t['wavg_dep_rate']}% | beta={t['med_beta']}% | fees=${t['fees_b']}B (${t['wavg_fee_per_mem']}/mem) | unins={t['med_unins_pct']}% | auto={t['med_new_auto']}%")
    print("\nTOP 5 LARGEST CREDIT UNIONS:")
    for x in records[:5]:
        print(f"  {x['name'][:36]:36s} ({x['state']}): ${x['assets_m']/1000:.1f}B | {x['members']/1e6:.2f}M mem | dep={x['dep_rate']}% (beta={x['beta']}%) | fee=${x['fee_per_mem']}/mem | auto={x['new_auto']}% | cc={x['cc_apr']}%")


if __name__ == "__main__":
    main()
