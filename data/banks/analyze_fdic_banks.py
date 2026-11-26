"""
Reproducible Multi-Year Analysis: U.S. Banking Reality — Deposit Rate Pass-Through ("The Deposit Skim"),
Deposit Fee Extraction & Uninsured Deposit Risk across ALL Active FDIC-Insured U.S. Banks (2021 -> 2025)

Primary Sources (Live FDIC BankFind API v2 — zero API keys):
  1. FDIC Institutions API (ACTIVE:1) — all ~4,204 active U.S. banks (location, branches, asset tier, charter)
  2. FDIC Financials API (REPDTE:20251231) — full-year FY2025 Call Reports (interest paid on domestic
     deposits EDEPDOM, yield on earning assets INTINCY, NIMY, deposit service charges ISC,
     uninsured deposits DEPUNINS, net income NETINC, ROA)
  3. FDIC Financials API (REPDTE:20211231) — full-year FY2021 pre-hike baseline Call Reports
     to compute each bank's exact 2021 -> 2025 rate-hike pass-through ratio ("Deposit Beta").

Note on units: FDIC dollar figures (ASSET, DEP, DEPDOM, EDEPDOM, INTINC, ISC, NETINC, DEPUNINS)
are reported in thousands of dollars ($K). Ratios (INTINCY, NIMY, ROA) are percentages.

Run:
  python analyze_fdic_banks.py
  python analyze_fdic_banks.py --export-csv fdic-banks-2021-2025.csv.gz

Outputs:
  - summary.json
  - summary-data.js
  - banks.json (compact lookup for all ~4,204 active U.S. banks)
  - (optional) fdic-banks-2021-2025.csv.gz
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
import statistics
import subprocess
import time
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).resolve().parent
CURL_BIN = shutil.which("curl.exe") or shutil.which("curl") or "curl"
FDIC_BASE = "https://api.fdic.gov/banks"

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


def fetch_fdic_all(endpoint: str, filters: str, fields: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    limit = 10000
    while True:
        qs = urllib.parse.urlencode({
            "filters": filters,
            "fields": fields,
            "limit": str(limit),
            "offset": str(offset),
        })
        resp = curl_json(f"{FDIC_BASE}/{endpoint}?{qs}")
        batch = [x["data"] for x in resp.get("data", []) if "data" in x]
        rows.extend(batch)
        total = int(resp.get("meta", {}).get("total", len(rows)))
        offset += len(batch)
        if not batch or offset >= total:
            break
    return rows


def to_f(v: Any) -> float | None:
    if v in (None, "", "NA"):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def asset_tier(asset_k: float | None) -> str:
    if asset_k is None:
        return "Unknown"
    # asset_k is in $thousands
    if asset_k >= 250_000_000:  # >= $250B
        return "Megabank ($250B+)"
    if asset_k >= 10_000_000:   # $10B - $250B
        return "Regional ($10B–$250B)"
    if asset_k >= 1_000_000:    # $1B - $10B
        return "Mid-Size ($1B–$10B)"
    return "Community (<$1B)"


def med(arr: list[float], d: int = 2) -> float | None:
    return round(statistics.median(arr), d) if arr else None


def avg(arr: list[float], d: int = 2) -> float | None:
    return round(statistics.mean(arr), d) if arr else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-csv", default="", help="Optional CSV/CSV.GZ filename in data/banks/")
    args = parser.parse_args()

    t0 = time.time()

    # 1. Fetch active FDIC institutions + FY2025 & FY2021 year-end Call Reports
    inst_fields = "CERT,NAME,CITY,STALP,ZIP,OFFDOM,ASSET,DEP,BKCLASS,SPECGRPN,WEBADDR"
    fin_fields = "CERT,NAME,REPDTE,ASSET,DEP,DEPDOM,DEPIDOM,DEPNIDOM,EDEPDOM,INTINC,INTINCY,EINTEXP,NIMY,ISERCHG,NETINC,ROA,DEPUNINS,EQTOT"

    inst_raw = fetch_fdic_all("institutions", "ACTIVE:1", inst_fields)
    fin25_raw = fetch_fdic_all("financials", "REPDTE:20251231", fin_fields)
    fin21_raw = fetch_fdic_all("financials", "REPDTE:20211231", fin_fields)

    fin25 = {int(r["CERT"]): r for r in fin25_raw if r.get("CERT") is not None}
    fin21 = {int(r["CERT"]): r for r in fin21_raw if r.get("CERT") is not None}

    banks = []
    for ins in inst_raw:
        cert = int(ins["CERT"])
        f25 = fin25.get(cert)
        f21 = fin21.get(cert)

        name = (ins.get("NAME") or "").strip()
        city = (ins.get("CITY") or "").strip()
        state = (ins.get("STALP") or "").strip().upper()
        zip5 = str(ins.get("ZIP") or "").strip()[:5]
        branches = int(to_f(ins.get("OFFDOM")) or 0)
        spec = (ins.get("SPECGRPN") or "").strip()
        web = (ins.get("WEBADDR") or "").strip()

        asset_k = to_f(f25.get("ASSET")) if f25 else to_f(ins.get("ASSET"))
        tier = asset_tier(asset_k)

        dep_k = to_f(f25.get("DEP")) if f25 else to_f(ins.get("DEP"))
        depdom_k = to_f(f25.get("DEPDOM")) if f25 else None
        depidom_k = to_f(f25.get("DEPIDOM")) if f25 else None
        depnidom_k = to_f(f25.get("DEPNIDOM")) if f25 else None
        edepdom_k = to_f(f25.get("EDEPDOM")) if f25 else None
        intinc_k = to_f(f25.get("INTINC")) if f25 else None
        yield25 = to_f(f25.get("INTINCY")) if f25 else None
        nim25 = to_f(f25.get("NIMY")) if f25 else None
        isc_k = to_f(f25.get("ISERCHG")) if f25 else None
        netinc_k = to_f(f25.get("NETINC")) if f25 else None
        roa25 = to_f(f25.get("ROA")) if f25 else None
        unins_k = to_f(f25.get("DEPUNINS")) if f25 else None

        # Effective FY2025 domestic deposit interest rate paid (%) — blended AND interest-bearing only
        dep_rate25 = None
        if depdom_k and depdom_k > 1000 and edepdom_k is not None and edepdom_k >= 0:
            r25 = edepdom_k / depdom_k * 100.0
            if 0.0 <= r25 <= 12.0:
                dep_rate25 = round(r25, 2)

        ib_rate25 = None
        if depidom_k and depidom_k > 1000 and edepdom_k is not None and edepdom_k >= 0:
            ibr = edepdom_k / depidom_k * 100.0
            if 0.0 <= ibr <= 12.0:
                ib_rate25 = round(ibr, 2)

        nonint_pct = None
        if depdom_k and depdom_k > 1000 and depnidom_k is not None and depnidom_k >= 0:
            nonint_pct = round(min(100.0, depnidom_k / depdom_k * 100.0), 1)

        # Spread kept by bank: Yield on Earning Assets minus Effective Deposit Rate Paid
        spread25 = None
        if yield25 is not None and dep_rate25 is not None and 0 <= yield25 <= 25:
            spread25 = round(yield25 - dep_rate25, 2)

        # Deposit service charge fee rate (% of domestic deposits — e.g., 0.25% = $25 per $10k)
        fee_rate25 = None
        if depdom_k and depdom_k > 1000 and isc_k is not None and isc_k >= 0:
            fr = isc_k / depdom_k * 100.0
            if 0.0 <= fr <= 5.0:
                fee_rate25 = round(fr, 3)

        # Uninsured deposit share (% of domestic deposits)
        unins_pct = None
        if depdom_k and depdom_k > 1000 and unins_k is not None and unins_k >= 0:
            up = min(100.0, unins_k / depdom_k * 100.0)
            unins_pct = round(up, 1)

        # 2021 -> 2025 Rate-Hike Pass-Through ("Deposit Beta")
        dep_rate21 = None
        yield21 = None
        delta_dep = None
        delta_yield = None
        pass_through = None
        if f21:
            d21 = to_f(f21.get("DEPDOM"))
            e21 = to_f(f21.get("EDEPDOM"))
            y21 = to_f(f21.get("INTINCY"))
            if d21 and d21 > 1000 and e21 is not None and e21 >= 0:
                r21 = e21 / d21 * 100.0
                if 0.0 <= r21 <= 10.0:
                    dep_rate21 = round(r21, 2)
            if y21 is not None and 0 <= y21 <= 25:
                yield21 = round(y21, 2)
            if dep_rate25 is not None and dep_rate21 is not None:
                delta_dep = round(dep_rate25 - dep_rate21, 2)
            if yield25 is not None and yield21 is not None:
                delta_yield = round(yield25 - yield21, 2)
            if delta_dep is not None and delta_yield is not None and delta_yield >= 0.5:
                pt = delta_dep / delta_yield * 100.0
                if -50.0 <= pt <= 250.0:
                    pass_through = round(pt, 1)

        flags = []
        if tier == "Megabank ($250B+)":
            flags.append("MEGABANK")
        if dep_rate25 is not None and dep_rate25 < 1.50 and (depdom_k or 0) >= 1_000_000:
            flags.append("LOW_YIELD_LARGE")
        if dep_rate25 is not None and dep_rate25 >= 3.25:
            flags.append("HIGH_YIELD")
        if fee_rate25 is not None and fee_rate25 >= 0.30 and (isc_k or 0) >= 1000:
            flags.append("HIGH_FEES")
        if unins_pct is not None and unins_pct >= 50.0:
            flags.append("HIGH_UNINSURED")
        if pass_through is not None and pass_through < 50.0 and (depdom_k or 0) >= 1_000_000:
            flags.append("LOW_PASSTHROUGH")

        banks.append({
            "cert": cert,
            "name": name,
            "city": city,
            "state": state,
            "zip": zip5,
            "tier": tier,
            "spec": spec,
            "branches": branches,
            "web": web,
            "asset_m": round(asset_k / 1000.0, 1) if asset_k is not None else None,
            "depdom_m": round(depdom_k / 1000.0, 1) if depdom_k is not None else None,
            "edepdom_m": round(edepdom_k / 1000.0, 2) if edepdom_k is not None else None,
            "isc_m": round(isc_k / 1000.0, 2) if isc_k is not None else None,
            "netinc_m": round(netinc_k / 1000.0, 2) if netinc_k is not None else None,
            "dep_rate25": dep_rate25,
            "ib_rate25": ib_rate25,
            "nonint_pct": nonint_pct,
            "dep_rate21": dep_rate21,
            "delta_dep": delta_dep,
            "yield25": round(yield25, 2) if yield25 is not None else None,
            "delta_yield": delta_yield,
            "spread25": spread25,
            "nim25": round(nim25, 2) if nim25 is not None else None,
            "pass_through": pass_through,
            "fee_rate25": fee_rate25,
            "unins_pct": unins_pct,
            "roa25": round(roa25, 2) if roa25 is not None else None,
            "flags": flags,
        })

    # National & Tier Aggregations
    with_fin = [b for b in banks if b["dep_rate25"] is not None]
    total_dom_dep_t = sum((b["depdom_m"] or 0) for b in with_fin) / 1e6  # trillions
    total_dep_int_b = sum((b["edepdom_m"] or 0) for b in with_fin) / 1e3  # billions
    total_isc_b = sum((b["isc_m"] or 0) for b in with_fin) / 1e3          # billions
    total_netinc_b = sum((b["netinc_m"] or 0) for b in with_fin) / 1e3    # billions

    weighted_dep_rate_nat = round(total_dep_int_b / (total_dom_dep_t * 1000) * 100, 2) if total_dom_dep_t else None

    # Compute top-quartile (75th percentile) FY2025 effective deposit rate across all banks
    all_rates = sorted(b["dep_rate25"] for b in with_fin)
    p75_rate = round(all_rates[int(len(all_rates) * 0.75)], 2) if all_rates else None
    p50_rate = med(all_rates, 2)
    p25_rate = round(all_rates[int(len(all_rates) * 0.25)], 2) if all_rates else None

    tier_order = ["Megabank ($250B+)", "Regional ($10B–$250B)", "Mid-Size ($1B–$10B)", "Community (<$1B)"]
    by_tier = []
    for tname in tier_order:
        grp = [b for b in with_fin if b["tier"] == tname]
        if not grp:
            continue
        dep_sum_b = sum((b["depdom_m"] or 0) for b in grp) / 1e3
        int_sum_b = sum((b["edepdom_m"] or 0) for b in grp) / 1e3
        isc_sum_b = sum((b["isc_m"] or 0) for b in grp) / 1e3
        net_sum_b = sum((b["netinc_m"] or 0) for b in grp) / 1e3
        w_rate = round(int_sum_b / dep_sum_b * 100, 2) if dep_sum_b > 0 else None
        # Estimated annual "interest gap" vs p75_rate for this tier
        gap_vs_p75_b = round(max(0.0, (p75_rate - w_rate) / 100.0 * dep_sum_b), 1) if (p75_rate and w_rate is not None) else 0.0
        by_tier.append({
            "tier": tname,
            "banks": len(grp),
            "dom_deposits_billions": round(dep_sum_b, 1),
            "deposit_share_pct": round(dep_sum_b / (total_dom_dep_t * 1000) * 100, 1) if total_dom_dep_t else 0,
            "weighted_dep_rate": w_rate,
            "median_dep_rate": med([b["dep_rate25"] for b in grp], 2),
            "median_yield25": med([b["yield25"] for b in grp if b["yield25"] is not None], 2),
            "median_spread25": med([b["spread25"] for b in grp if b["spread25"] is not None], 2),
            "median_pass_through": med([b["pass_through"] for b in grp if b["pass_through"] is not None], 1),
            "total_dep_fees_billions": round(isc_sum_b, 2),
            "median_unins_pct": med([b["unins_pct"] for b in grp if b["unins_pct"] is not None], 1),
            "total_net_income_billions": round(net_sum_b, 1),
            "annual_gap_vs_p75_billions": gap_vs_p75_b,
        })

    # Top 15 Largest U.S. Banks by Domestic Deposits
    top_15_banks = sorted(with_fin, key=lambda b: -(b["depdom_m"] or 0))[:15]

    # Top 15 Deposit Fee Extractors (Total $M ISC)
    top_15_fees = sorted(with_fin, key=lambda b: -(b["isc_m"] or 0))[:15]

    # Top 15 Highest-Yield Large Banks (Dom Deposits >= $5B)
    top_15_savers = sorted(
        [b for b in with_fin if (b["depdom_m"] or 0) >= 5000],
        key=lambda b: -(b["dep_rate25"] or 0),
    )[:15]

    # 50-State + DC Summary
    by_state = []
    for st in sorted(US_STATES_DC):
        grp = [b for b in with_fin if b["state"] == st]
        if not grp:
            continue
        dep_b = sum((b["depdom_m"] or 0) for b in grp) / 1e3
        isc_m = sum((b["isc_m"] or 0) for b in grp)
        by_state.append({
            "state": st,
            "banks": len(grp),
            "dom_deposits_billions": round(dep_b, 1),
            "median_dep_rate": med([b["dep_rate25"] for b in grp], 2),
            "median_pass_through": med([b["pass_through"] for b in grp if b["pass_through"] is not None], 1),
            "total_dep_fees_millions": round(isc_m, 1),
            "median_unins_pct": med([b["unins_pct"] for b in grp if b["unins_pct"] is not None], 1),
        })
    by_state.sort(key=lambda x: x["median_dep_rate"] or 0, reverse=True)

    # Big 4 Megabanks exact combined skim vs p75
    big4 = sorted(with_fin, key=lambda b: -(b["depdom_m"] or 0))[:4]
    big4_dep_b = sum((b["depdom_m"] or 0) for b in big4) / 1e3
    big4_int_b = sum((b["edepdom_m"] or 0) for b in big4) / 1e3
    big4_isc_b = sum((b["isc_m"] or 0) for b in big4) / 1e3
    big4_rate = round(big4_int_b / big4_dep_b * 100, 2) if big4_dep_b else None
    big4_gap_vs_p75_b = round(max(0.0, (p75_rate - big4_rate) / 100.0 * big4_dep_b), 1) if (p75_rate and big4_rate is not None) else 0.0

    counts = {
        "megabanks": sum(1 for b in banks if "MEGABANK" in b["flags"]),
        "low_yield_large": sum(1 for b in banks if "LOW_YIELD_LARGE" in b["flags"]),
        "high_yield": sum(1 for b in banks if "HIGH_YIELD" in b["flags"]),
        "high_fees": sum(1 for b in banks if "HIGH_FEES" in b["flags"]),
        "high_uninsured": sum(1 for b in banks if "HIGH_UNINSURED" in b["flags"]),
        "low_passthrough": sum(1 for b in banks if "LOW_PASSTHROUGH" in b["flags"]),
    }

    summary = {
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "runtime_sec": round(time.time() - t0, 1),
            "source": "FDIC BankFind API v2 (Active Institutions + FY2021 & FY2025 Year-End Call Reports)",
            "total_active_banks": len(banks),
            "banks_with_fy25_call_report": len(with_fin),
        },
        "national": {
            "total_dom_deposits_trillions": round(total_dom_dep_t, 2),
            "total_dep_interest_paid_billions": round(total_dep_int_b, 1),
            "total_dep_service_fees_billions": round(total_isc_b, 2),
            "total_net_income_billions": round(total_netinc_b, 1),
            "weighted_avg_dep_rate": weighted_dep_rate_nat,
            "p25_dep_rate": p25_rate,
            "median_dep_rate": p50_rate,
            "p75_dep_rate": p75_rate,
            "median_pass_through_21_25": med([b["pass_through"] for b in with_fin if b["pass_through"] is not None], 1),
            "median_unins_pct": med([b["unins_pct"] for b in with_fin if b["unins_pct"] is not None], 1),
        },
        "big4_spotlight": {
            "names": [b["name"] for b in big4],
            "dom_deposits_trillions": round(big4_dep_b / 1000.0, 2),
            "share_of_us_deposits_pct": round(big4_dep_b / (total_dom_dep_t * 1000) * 100, 1) if total_dom_dep_t else 0,
            "weighted_dep_rate": big4_rate,
            "dep_service_fees_billions": round(big4_isc_b, 2),
            "annual_gap_vs_p75_billions": big4_gap_vs_p75_b,
        },
        "counts": counts,
        "by_tier": by_tier,
        "top_15_banks": [
            {k: b[k] for k in ("cert", "name", "city", "state", "depdom_m", "dep_rate25", "ib_rate25", "nonint_pct", "dep_rate21", "yield25", "spread25", "pass_through", "isc_m", "unins_pct", "netinc_m", "branches")}
            for b in top_15_banks
        ],
        "top_15_savers": [
            {k: b[k] for k in ("cert", "name", "city", "state", "depdom_m", "dep_rate25", "yield25", "pass_through", "isc_m", "unins_pct")}
            for b in top_15_savers
        ],
        "by_state": by_state,
    }

    cols = [
        "cert", "name", "city", "state", "zip", "tier", "branches", "asset_m", "depdom_m",
        "dep_rate25", "ib_rate25", "nonint_pct", "dep_rate21", "yield25", "spread25",
        "pass_through", "isc_m", "fee_rate25", "unins_pct", "netinc_m", "roa25", "flags",
    ]
    rows_compact = [
        [
            b["cert"], b["name"], b["city"], b["state"], b["zip"], b["tier"], b["branches"],
            b["asset_m"], b["depdom_m"], b["dep_rate25"], b["ib_rate25"], b["nonint_pct"],
            b["dep_rate21"], b["yield25"], b["spread25"], b["pass_through"], b["isc_m"],
            b["fee_rate25"], b["unins_pct"], b["netinc_m"], b["roa25"], "|".join(b["flags"]),
        ]
        for b in banks
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "summary-data.js").write_text(
        "window.FDIC_BANK_DATA = " + json.dumps(summary, indent=2) + ";\n",
        encoding="utf-8",
    )
    (OUT_DIR / "banks.json").write_text(
        json.dumps({"cols": cols, "rows": rows_compact}, separators=(",", ":")),
        encoding="utf-8",
    )

    if args.export_csv:
        csv_path = OUT_DIR / args.export_csv
        fields = [
            "cert", "name", "city", "state", "zip", "tier", "spec", "branches", "asset_m",
            "depdom_m", "edepdom_m", "dep_rate25", "ib_rate25", "nonint_pct", "dep_rate21",
            "delta_dep", "yield25", "delta_yield", "spread25", "nim25", "pass_through",
            "isc_m", "fee_rate25", "unins_pct", "netinc_m", "roa25", "flags",
        ]
        opener = gzip.open if str(csv_path).endswith(".gz") else open
        with opener(csv_path, "wt", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(fields)
            for b in banks:
                w.writerow(["|".join(b[k]) if k == "flags" else b[k] for k in fields])

    print(f"FDIC active banks: {len(banks):,} | FY25 Call Reports: {len(with_fin):,} ({round(time.time()-t0, 1)}s)")
    print("National:", summary["national"])
    print("Big 4 Spotlight:", summary["big4_spotlight"])
    print("\nBy Asset Tier:")
    for t in by_tier:
        print(f"  {t['tier']:22s} | n={t['banks']:4d} | dep=${t['dom_deposits_billions']:7.1f}B ({t['deposit_share_pct']:4.1f}%) | wRate={t['weighted_dep_rate']}% med={t['median_dep_rate']}% | spread={t['median_spread25']}% | passThru={t['median_pass_through']}% | fees=${t['total_dep_fees_billions']}B | unins={t['median_unins_pct']}% | gapVsP75=${t['annual_gap_vs_p75_billions']}B")
    print("\nTop 10 Largest U.S. Banks (FY2025):")
    for b in top_15_banks[:10]:
        print(f"  {b['cert']:5d} {b['name'][:30]:30s} ({b['state']}) | dep=${b['depdom_m']/1e3:6.0f}B | paid={b['dep_rate25']}% (2021:{b['dep_rate21']}%) | yld={b['yield25']}% | pass={b['pass_through']}% | fees=${b['isc_m']:,.0f}M | unins={b['unins_pct']}%")
    print("\nTop 8 Highest Effective Deposit Rate Large Banks (>=$5B deposits):")
    for b in top_15_savers[:8]:
        print(f"  {b['cert']:5d} {b['name'][:30]:30s} ({b['state']}) | dep=${b['depdom_m']/1e3:5.1f}B | paid={b['dep_rate25']}% | pass={b['pass_through']}% | fees=${b['isc_m']:,.1f}M | unins={b['unins_pct']}%")


if __name__ == "__main__":
    main()
