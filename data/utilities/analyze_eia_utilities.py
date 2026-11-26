#!/usr/bin/env python3
"""
EIA Form 861 U.S. Electric Utility Accountability Pipeline (2020-2025).

Downloads official U.S. Energy Information Administration (EIA) Form 861 annual
ZIP archives (Sales to Ultimate Customers, Reliability SAIDI/SAIFI, and County
Service Territories) for 2020, 2024, and 2025, joins them cleanly across all
full-form residential utilities serving ~140.8M U.S. households, and emits:

  - data/utilities/summary.json
  - data/utilities/summary-data.js
  - data/utilities/utilities.json
  - data/utilities/eia-861-utilities-2020-2025.csv.gz

Accounting safeguards:
  1. Uses Bundled (Part A & Part D) residential revenue/sales for full retail
     rate calculations (never mixes Delivery-only wires charges into full rates).
  2. Sums Bundled + Delivery residential customer counts per (utility, state)
     so deregulated/CCA distribution utilities (e.g., PG&E, SDG&E, ComEd,
     Eversource) reflect their true residential household footprint.
  3. Excludes 'Behind the Meter' third-party solar lessors (Sunrun, Tesla, etc.)
     and EIA state 'Adjustment' placeholder rows (uid=99999) from individual
     utility rankings while preserving exact national all-sector totals.
  4. Reads both IEEE Standard and Other Standard SAIDI/SAIFI (with and without
     Major Event Days) across 2024 and 2025 to separate routine grid quality
     from single-year hurricane/storm spikes.
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
import sys
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import openpyxl

ROOT = Path(__file__).resolve().parent
CURL_BIN = shutil.which("curl.exe") or shutil.which("curl") or "curl"

BASE_URL = "https://www.eia.gov/electricity/data/eia861"
LATEST_YEAR = 2025
PRIOR_REL_YEAR = 2024
BASE_YEAR = 2020

# Optional local cache dir for fast local reruns (ignored in CI)
CACHE_DIR = Path(
    os.environ.get(
        "EIA861_CACHE_DIR",
        str(Path(tempfile.gettempdir()) / "eia861_cache"),
    )
)

OWNERSHIP_BUCKET = {
    "Investor Owned": "Investor-Owned (For-Profit)",
    "Municipal": "Municipal (City-Owned)",
    "Political Subdivision": "Public Utility District",
    "Cooperative": "Rural Electric Cooperative",
    "State": "State / Federal Public",
    "Federal": "State / Federal Public",
    "Retail Power Marketer": "Retail Power Marketer (Deregulated)",
}

PUBLIC_POWER_TYPES = {"Municipal", "Political Subdivision"}
TRADITIONAL_OWNERSHIPS = {
    "Investor Owned",
    "Municipal",
    "Political Subdivision",
    "Cooperative",
    "State",
    "Federal",
}

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
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


def num(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if not s or s in (".", "NA", "N/A", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def r2(v: float | None) -> float | None:
    return round(v, 2) if v is not None else None


def r1(v: float | None) -> float | None:
    return round(v, 1) if v is not None else None


def med(vals: list[float]) -> float | None:
    return round(statistics.median(vals), 2) if vals else None


def fetch_eia_zip(year: int) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / f"f861{year}.zip"
    if dst.exists() and dst.stat().st_size > 100_000 and zipfile.is_zipfile(dst):
        return dst

    candidates = [
        f"{BASE_URL}/zip/f861{year}.zip",
        f"{BASE_URL}/archive/zip/f861{year}.zip",
    ]
    for url in candidates:
        tmp = dst.with_suffix(".tmp")
        code = subprocess.check_output(
            [CURL_BIN, "-sL", "-w", "%{http_code}", "-o", str(tmp), url],
            text=True,
        ).strip()
        if code == "200" and tmp.exists() and tmp.stat().st_size > 100_000 and zipfile.is_zipfile(tmp):
            tmp.replace(dst)
            print(f"Downloaded f861{year}.zip ({dst.stat().st_size:,} bytes) from {url}")
            return dst
        tmp.unlink(missing_ok=True)
    raise RuntimeError(f"Could not download EIA-861 ZIP for year {year}")


def find_member(zf: zipfile.ZipFile, prefix: str) -> str:
    prefix_l = prefix.lower()
    for n in zf.namelist():
        base = n.rsplit("/", 1)[-1].lower()
        if base.startswith(prefix_l) and base.endswith(".xlsx") and not base.startswith("~$"):
            return n
    raise KeyError(f"Could not find {prefix}*.xlsx in {zf.filename}")


def load_sales(zip_path: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as zf:
        member = find_member(zf, "Sales_Ult_Cust_")
        wb = openpyxl.load_workbook(io.BytesIO(zf.read(member)), read_only=True, data_only=True)
    ws = wb["States"]
    rows = []
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i < 3 or not r or r[0] is None:
            continue
        yr_s = str(r[0]).strip()
        if not yr_s.isdigit():
            continue
        uid = num(r[1])
        rows.append({
            "year": int(yr_s),
            "uid": int(uid) if uid is not None else None,
            "name": str(r[2] or "").strip(),
            "part": str(r[3] or "").strip(),
            "stype": str(r[4] or "").strip(),
            "dtype": str(r[5] or "").strip(),
            "state": str(r[6] or "").strip().upper(),
            "own": str(r[7] or "").strip(),
            "ba": str(r[8] or "").strip(),
            "res_rev": num(r[9]) or 0.0,    # thousand $
            "res_mwh": num(r[10]) or 0.0,   # MWh
            "res_cust": num(r[11]) or 0.0,  # count
            "com_rev": num(r[12]) or 0.0,
            "com_mwh": num(r[13]) or 0.0,
            "ind_rev": num(r[15]) or 0.0,
            "ind_mwh": num(r[16]) or 0.0,
        })
    wb.close()
    return rows


def load_reliability(zip_path: Path, header_rows: int = 3) -> dict[tuple[int, str], dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as zf:
        member = find_member(zf, "Reliability_")
        wb = openpyxl.load_workbook(io.BytesIO(zf.read(member)), read_only=True, data_only=True)
    ws = wb["Reliability_States"]
    out: dict[tuple[int, str], dict[str, Any]] = {}
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i < header_rows or not r or r[0] is None:
            continue
        if not str(r[0]).strip().isdigit():
            continue
        uid = num(r[1])
        if uid is None:
            continue
        st = str(r[3] or "").strip().upper()
        s_ieee_w = num(r[5])
        f_ieee_w = num(r[6])
        s_ieee_wo = num(r[8])
        f_ieee_wo = num(r[9])
        s_oth_w = num(r[17]) if len(r) > 17 else None
        f_oth_w = num(r[18]) if len(r) > 18 else None
        s_oth_wo = num(r[20]) if len(r) > 20 else None
        f_oth_wo = num(r[21]) if len(r) > 21 else None

        if s_ieee_w is not None or s_ieee_wo is not None:
            std = "IEEE"
            sw, fw, swo, fwo = s_ieee_w, f_ieee_w, s_ieee_wo, f_ieee_wo
        elif s_oth_w is not None or s_oth_wo is not None:
            std = "Other"
            sw, fw, swo, fwo = s_oth_w, f_oth_w, s_oth_wo, f_oth_wo
        else:
            continue

        out[(int(uid), st)] = {
            "std": std,
            "saidi_w": sw,
            "saifi_w": fw,
            "saidi_wo": swo,
            "saifi_wo": fwo,
        }
    wb.close()
    return out


def load_counties(zip_path: Path) -> dict[tuple[int, str], list[str]]:
    with zipfile.ZipFile(zip_path) as zf:
        member = find_member(zf, "Service_Territory_")
        wb = openpyxl.load_workbook(io.BytesIO(zf.read(member)), read_only=True, data_only=True)
    ws = wb["Counties_States"]
    cmap: dict[tuple[int, str], set[str]] = defaultdict(set)
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i < 1 or not r or r[0] is None or not str(r[0]).strip().isdigit():
            continue
        uid = num(r[1])
        st = str(r[4] or "").strip().upper()
        county = str(r[5] or "").strip()
        if uid is not None and st and county:
            cmap[(int(uid), st)].add(county)
    wb.close()
    return {k: sorted(v) for k, v in cmap.items()}


def compute_national_sector_totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Include all states (including Adjustment rows) for official national EIA totals
    res_rev = sum(r["res_rev"] for r in rows if r["stype"] in ("Bundled", "Energy", "Delivery"))
    res_mwh = sum(r["res_mwh"] for r in rows if r["stype"] in ("Bundled", "Delivery"))
    res_cust = sum(r["res_cust"] for r in rows if r["stype"] in ("Bundled", "Delivery"))
    com_rev = sum(r["com_rev"] for r in rows if r["stype"] in ("Bundled", "Energy", "Delivery"))
    com_mwh = sum(r["com_mwh"] for r in rows if r["stype"] in ("Bundled", "Delivery"))
    ind_rev = sum(r["ind_rev"] for r in rows if r["stype"] in ("Bundled", "Energy", "Delivery"))
    ind_mwh = sum(r["ind_mwh"] for r in rows if r["stype"] in ("Bundled", "Delivery"))
    return {
        "res_cust": int(round(res_cust)),
        "res_rev_b": round(res_rev / 1e6, 2),
        "res_mwh_m": round(res_mwh / 1e6, 2),
        "res_rate": round(res_rev / res_mwh * 100, 2) if res_mwh else None,
        "com_rate": round(com_rev / com_mwh * 100, 2) if com_mwh else None,
        "ind_rate": round(ind_rev / ind_mwh * 100, 2) if ind_mwh else None,
        "avg_monthly_kwh": round((res_mwh * 1000.0) / res_cust / 12.0, 0) if res_cust else None,
        "avg_monthly_bill": round((res_rev * 1000.0) / res_cust / 12.0, 2) if res_cust else None,
    }


def main() -> None:
    z25 = fetch_eia_zip(LATEST_YEAR)
    z24 = fetch_eia_zip(PRIOR_REL_YEAR)
    z20 = fetch_eia_zip(BASE_YEAR)

    s25 = load_sales(z25)
    s24 = load_sales(z24)
    s20 = load_sales(z20)

    rel25 = load_reliability(z25, header_rows=3)
    rel24 = load_reliability(z24, header_rows=3)
    rel20 = load_reliability(z20, header_rows=2)
    counties25 = load_counties(z25)

    nat25 = compute_national_sector_totals(s25)
    nat24 = compute_national_sector_totals(s24)
    nat20 = compute_national_sector_totals(s20)

    # Index Delivery residential customers/mwh per (uid, state) in 2025
    deliv25: dict[tuple[int, str], dict[str, float]] = defaultdict(lambda: {"cust": 0.0, "mwh": 0.0, "rev": 0.0})
    for r in s25:
        if r["uid"] and r["uid"] != 99999 and r["stype"] == "Delivery":
            d = deliv25[(r["uid"], r["state"])]
            d["cust"] += r["res_cust"]
            d["mwh"] += r["res_mwh"]
            d["rev"] += r["res_rev"]

    # Index 2020 Bundled residential rates per (uid, state)
    b20_map: dict[tuple[int, str], dict[str, float]] = {}
    for r in s20:
        if r["uid"] and r["uid"] != 99999 and r["stype"] == "Bundled" and r["res_mwh"] > 0 and r["res_cust"] > 0:
            key = (r["uid"], r["state"])
            if key not in b20_map:
                b20_map[key] = {"rev": 0.0, "mwh": 0.0, "cust": 0.0}
            b20_map[key]["rev"] += r["res_rev"]
            b20_map[key]["mwh"] += r["res_mwh"]
            b20_map[key]["cust"] += r["res_cust"]

    # Aggregate 2025 Bundled records per (uid, state), excluding Adjustment & Behind the Meter
    b25_agg: dict[tuple[int, str], dict[str, Any]] = {}
    for r in s25:
        if not r["uid"] or r["uid"] == 99999:
            continue
        if r["stype"] != "Bundled":
            continue
        if r["own"] == "Behind the Meter":
            continue
        if r["res_cust"] <= 0 or r["res_mwh"] <= 0:
            continue
        if r["state"] not in STATE_NAMES:
            continue
        key = (r["uid"], r["state"])
        if key not in b25_agg:
            b25_agg[key] = {
                "uid": r["uid"],
                "name": r["name"],
                "state": r["state"],
                "own": r["own"],
                "part": r["part"],
                "ba": r["ba"],
                "res_rev": 0.0,
                "res_mwh": 0.0,
                "res_cust": 0.0,
                "com_rev": 0.0,
                "com_mwh": 0.0,
                "ind_rev": 0.0,
                "ind_mwh": 0.0,
            }
        agg = b25_agg[key]
        agg["res_rev"] += r["res_rev"]
        agg["res_mwh"] += r["res_mwh"]
        agg["res_cust"] += r["res_cust"]
        agg["com_rev"] += r["com_rev"]
        agg["com_mwh"] += r["com_mwh"]
        agg["ind_rev"] += r["ind_rev"]
        agg["ind_mwh"] += r["ind_mwh"]

    # Pre-compute state-level Public Power (Municipal + Political Subdivision) & Overall benchmarks
    state_pub_acc: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])  # rev, mwh, cust
    state_iou_acc: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    state_coop_acc: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    state_all_acc: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])

    for u in b25_agg.values():
        st = u["state"]
        state_all_acc[st][0] += u["res_rev"]
        state_all_acc[st][1] += u["res_mwh"]
        state_all_acc[st][2] += u["res_cust"]
        if u["own"] in PUBLIC_POWER_TYPES:
            state_pub_acc[st][0] += u["res_rev"]
            state_pub_acc[st][1] += u["res_mwh"]
            state_pub_acc[st][2] += u["res_cust"]
        elif u["own"] == "Investor Owned":
            state_iou_acc[st][0] += u["res_rev"]
            state_iou_acc[st][1] += u["res_mwh"]
            state_iou_acc[st][2] += u["res_cust"]
        elif u["own"] == "Cooperative":
            state_coop_acc[st][0] += u["res_rev"]
            state_coop_acc[st][1] += u["res_mwh"]
            state_coop_acc[st][2] += u["res_cust"]

    state_pub_rate = {
        st: (v[0] / v[1] * 100.0) for st, v in state_pub_acc.items() if v[1] > 0 and v[2] >= 1000
    }
    state_all_rate = {
        st: (v[0] / v[1] * 100.0) for st, v in state_all_acc.items() if v[1] > 0
    }

    # Build unified utility records
    records: list[dict[str, Any]] = []
    for key, u in b25_agg.items():
        uid, st = key
        rate25 = u["res_rev"] / u["res_mwh"] * 100.0  # cents / kWh
        avg_kwh_mo = (u["res_mwh"] * 1000.0) / u["res_cust"] / 12.0
        avg_bill_mo = (u["res_rev"] * 1000.0) / u["res_cust"] / 12.0

        d25 = deliv25.get(key)
        deliv_cust = int(round(d25["cust"])) if d25 else 0
        total_cust = int(round(u["res_cust"])) + deliv_cust

        prev = b20_map.get(key)
        rate20 = (prev["rev"] / prev["mwh"] * 100.0) if prev and prev["mwh"] > 0 else None
        hike_cents = (rate25 - rate20) if rate20 is not None else None
        hike_pct = ((rate25 / rate20 - 1.0) * 100.0) if rate20 and rate20 > 0 else None
        # Extra $/yr at 2025 household usage compared to 2020 rate
        hike_yr_dollars = (hike_cents / 100.0 * avg_kwh_mo * 12.0) if hike_cents is not None else None

        ind_rate = (u["ind_rev"] / u["ind_mwh"] * 100.0) if u["ind_mwh"] >= 100 else None
        com_rate = (u["com_rev"] / u["com_mwh"] * 100.0) if u["com_mwh"] >= 100 else None

        r25_rel = rel25.get(key) or {}
        r24_rel = rel24.get(key) or {}
        r20_rel = rel20.get(key) or {}

        sw25 = r25_rel.get("saidi_w")
        swo25 = r25_rel.get("saidi_wo")
        fw25 = r25_rel.get("saifi_w")
        fwo25 = r25_rel.get("saifi_wo")
        sw24 = r24_rel.get("saidi_w")
        swo24 = r24_rel.get("saidi_wo")
        rel_std = r25_rel.get("std") or r24_rel.get("std") or ""

        # 2-year storm-smoothed SAIDI (average of 2024 & 2025 when both present)
        sw_vals = [x for x in (sw25, sw24) if x is not None]
        saidi_2yr = sum(sw_vals) / len(sw_vals) if sw_vals else None

        pub_bench = state_pub_rate.get(st)
        vs_pub_cents = (rate25 - pub_bench) if pub_bench is not None else None
        vs_pub_yr = (vs_pub_cents / 100.0 * avg_kwh_mo * 12.0) if vs_pub_cents is not None else None

        cty_list = counties25.get(key, [])
        # Keep top 8 counties in compact JSON for searchability; full list in CSV
        cty_full = ", ".join(cty_list)
        cty_short = ", ".join(cty_list[:10]) + (f" (+{len(cty_list)-10})" if len(cty_list) > 10 else "")

        records.append({
            "uid": uid,
            "name": u["name"],
            "state": st,
            "own": u["own"],
            "own_bucket": OWNERSHIP_BUCKET.get(u["own"], u["own"]),
            "part": u["part"],
            "ba": u["ba"],
            "bundled_cust": int(round(u["res_cust"])),
            "deliv_cust": deliv_cust,
            "total_cust": total_cust,
            "res_mwh": round(u["res_mwh"], 1),
            "res_rev_k": round(u["res_rev"], 1),
            "rate25": round(rate25, 2),
            "rate20": r2(rate20),
            "hike_cents": r2(hike_cents),
            "hike_pct": r1(hike_pct),
            "hike_yr_dollars": round(hike_yr_dollars) if hike_yr_dollars is not None else None,
            "avg_kwh_mo": round(avg_kwh_mo),
            "avg_bill_mo": round(avg_bill_mo, 2),
            "com_rate": r2(com_rate),
            "ind_rate": r2(ind_rate),
            "state_pub_rate": r2(pub_bench),
            "vs_pub_cents": r2(vs_pub_cents),
            "vs_pub_yr": round(vs_pub_yr) if vs_pub_yr is not None else None,
            "saidi_w25": r1(sw25),
            "saidi_wo25": r1(swo25),
            "saifi_w25": r2(fw25),
            "saifi_wo25": r2(fwo25),
            "saidi_w24": r1(sw24),
            "saidi_wo24": r1(swo24),
            "saidi_2yr": r1(saidi_2yr),
            "saidi_w20": r1(r20_rel.get("saidi_w")),
            "rel_std": rel_std,
            "counties_short": cty_short,
            "counties_full": cty_full,
        })

    records.sort(key=lambda x: (-x["total_cust"], -x["bundled_cust"]))

    # Ownership tier summary (Bundled 2025 + matched 2020 + Reliability)
    by_own_groups = [
        ("Investor Owned", "Investor-Owned (For-Profit)"),
        ("Municipal", "Municipal (City-Owned)"),
        ("Political Subdivision", "Public Utility District"),
        ("Cooperative", "Rural Electric Cooperative"),
        ("Retail Power Marketer", "Retail Power Marketer (TX/Deregulated)"),
        ("State/Federal", "State & Federal Public"),
    ]
    by_ownership = []
    for raw_key, label in by_own_groups:
        if raw_key == "State/Federal":
            sub = [r for r in records if r["own"] in ("State", "Federal")]
        else:
            sub = [r for r in records if r["own"] == raw_key]
        if not sub:
            continue
        tot_bcust = sum(r["bundled_cust"] for r in sub)
        tot_tcust = sum(r["total_cust"] for r in sub)
        tot_rev = sum(r["res_rev_k"] for r in sub)
        tot_mwh = sum(r["res_mwh"] for r in sub)
        wavg25 = tot_rev / tot_mwh * 100.0 if tot_mwh else None

        # Weighted 2020 rate across matched utilities in this tier
        m20_rev = 0.0
        m20_mwh = 0.0
        m25_rev = 0.0
        m25_mwh = 0.0
        hike_pcts = []
        for r in sub:
            prev = b20_map.get((r["uid"], r["state"]))
            if prev and prev["mwh"] > 0:
                m20_rev += prev["rev"]
                m20_mwh += prev["mwh"]
                m25_rev += r["res_rev_k"]
                m25_mwh += r["res_mwh"]
                if r["hike_pct"] is not None:
                    hike_pcts.append(r["hike_pct"])
        wavg20 = (m20_rev / m20_mwh * 100.0) if m20_mwh else None
        wavg_matched25 = (m25_rev / m25_mwh * 100.0) if m25_mwh else None
        wavg_hike_pct = ((wavg_matched25 / wavg20 - 1.0) * 100.0) if (wavg20 and wavg_matched25) else None

        sw25s = [r["saidi_w25"] for r in sub if r["saidi_w25"] is not None]
        swo25s = [r["saidi_wo25"] for r in sub if r["saidi_wo25"] is not None]
        sw2yr = [r["saidi_2yr"] for r in sub if r["saidi_2yr"] is not None]

        by_ownership.append({
            "key": raw_key,
            "label": label,
            "utilities": len(sub),
            "bundled_cust": tot_bcust,
            "total_cust": tot_tcust,
            "wavg_rate25": r2(wavg25),
            "wavg_rate20": r2(wavg20),
            "wavg_hike_pct": r1(wavg_hike_pct),
            "med_rate25": med([r["rate25"] for r in sub]),
            "med_hike_pct": r1(statistics.median(hike_pcts)) if hike_pcts else None,
            "avg_bill_mo": round(tot_rev * 1000.0 / tot_bcust / 12.0, 2) if tot_bcust else None,
            "rel_count": len(sw25s),
            "med_saidi_w25": r1(statistics.median(sw25s)) if sw25s else None,
            "med_saidi_wo25": r1(statistics.median(swo25s)) if swo25s else None,
            "med_saidi_2yr": r1(statistics.median(sw2yr)) if sw2yr else None,
        })

    # Same-State IOU vs Public Power comparison
    same_state = []
    iou_higher_count = 0
    total_same_state_excess = 0.0
    for st in sorted(STATE_NAMES.keys()):
        iou = state_iou_acc.get(st, [0.0, 0.0, 0.0])
        pub = state_pub_acc.get(st, [0.0, 0.0, 0.0])
        coop = state_coop_acc.get(st, [0.0, 0.0, 0.0])
        all_st = state_all_acc.get(st, [0.0, 0.0, 0.0])
        iou_r = (iou[0] / iou[1] * 100.0) if iou[1] > 0 else None
        pub_r = (pub[0] / pub[1] * 100.0) if pub[1] > 0 else None
        coop_r = (coop[0] / coop[1] * 100.0) if coop[1] > 0 else None
        all_r = (all_st[0] / all_st[1] * 100.0) if all_st[1] > 0 else None

        both_major = (iou[2] >= 10_000 and pub[2] >= 5_000 and iou_r is not None and pub_r is not None)
        diff = (iou_r - pub_r) if both_major else None
        excess_m = None
        if both_major and diff is not None:
            if diff > 0:
                iou_higher_count += 1
            ex_dollars = max(0.0, (diff / 100.0) * (iou[1] * 1000.0))
            total_same_state_excess += ex_dollars
            excess_m = round(ex_dollars / 1e6, 1)

        # State 2025 SAIDI medians by IOU vs Municipal
        st_iou_saidi = [r["saidi_w25"] for r in records if r["state"] == st and r["own"] == "Investor Owned" and r["saidi_w25"] is not None]
        st_pub_saidi = [r["saidi_w25"] for r in records if r["state"] == st and r["own"] in PUBLIC_POWER_TYPES and r["saidi_w25"] is not None]

        same_state.append({
            "state": st,
            "state_name": STATE_NAMES[st],
            "all_rate25": r2(all_r),
            "iou_rate25": r2(iou_r),
            "pub_rate25": r2(pub_r),
            "coop_rate25": r2(coop_r),
            "iou_cust": int(round(iou[2])),
            "pub_cust": int(round(pub[2])),
            "both_major": both_major,
            "iou_vs_pub_cents": r2(diff),
            "excess_m": excess_m,
            "iou_med_saidi": r1(statistics.median(st_iou_saidi)) if st_iou_saidi else None,
            "pub_med_saidi": r1(statistics.median(st_pub_saidi)) if st_pub_saidi else None,
        })

    major_states = [s for s in same_state if s["both_major"]]
    top_state_gaps = sorted(major_states, key=lambda x: -(x["iou_vs_pub_cents"] or -999))[:14]

    # Largest 15 utilities & Worst 15 large utility rate hikes (>=100k total customers)
    top_15_largest = [
        {
            "uid": r["uid"], "name": r["name"], "state": r["state"], "own": r["own"],
            "total_cust": r["total_cust"], "bundled_cust": r["bundled_cust"],
            "rate20": r["rate20"], "rate25": r["rate25"], "hike_pct": r["hike_pct"],
            "avg_bill_mo": r["avg_bill_mo"], "saidi_w25": r["saidi_w25"],
            "saidi_wo25": r["saidi_wo25"], "vs_pub_cents": r["vs_pub_cents"],
        }
        for r in records[:15]
    ]

    large_with_hike = [r for r in records if r["total_cust"] >= 100_000 and r["hike_pct"] is not None and r["own"] in TRADITIONAL_OWNERSHIPS]
    worst_15_hikes = [
        {
            "uid": r["uid"], "name": r["name"], "state": r["state"], "own": r["own"],
            "total_cust": r["total_cust"], "rate20": r["rate20"], "rate25": r["rate25"],
            "hike_pct": r["hike_pct"], "hike_yr_dollars": r["hike_yr_dollars"],
            "saidi_w25": r["saidi_w25"], "vs_pub_cents": r["vs_pub_cents"],
        }
        for r in sorted(large_with_hike, key=lambda x: -(x["hike_pct"] or -999))[:15]
    ]

    # Spotlight neighbor pairs (same state / metro, IOU vs Public Power)
    by_uid_st = {(r["uid"], r["state"]): r for r in records}
    neighbor_pairs_spec = [
        ("California (Bay Area / NorCal)", (14328, "CA"), (16534, "CA")),   # PG&E vs SMUD
        ("California (SoCal)", (17609, "CA"), (11208, "CA")),               # SCE vs LADWP
        ("California (San Diego vs Sacramento)", (16609, "CA"), (16534, "CA")), # SDG&E vs SMUD
        ("Florida (Duke FL vs JEA Jacksonville)", (6455, "FL"), (9617, "FL")),
        ("Texas (TXU Retail vs San Antonio CPS Energy)", (19327, "TX"), (16604, "TX")),
        ("Washington (Puget Sound Energy vs Seattle City Light)", (15500, "WA"), (16868, "WA")),
    ]
    neighbor_pairs = []
    for region, k_a, k_b in neighbor_pairs_spec:
        a = by_uid_st.get(k_a)
        b = by_uid_st.get(k_b)
        if a and b:
            neighbor_pairs.append({
                "region": region,
                "iou_name": a["name"], "iou_own": a["own"], "iou_rate25": a["rate25"],
                "iou_hike_pct": a["hike_pct"], "iou_saidi_w25": a["saidi_w25"], "iou_cust": a["total_cust"],
                "pub_name": b["name"], "pub_own": b["own"], "pub_rate25": b["rate25"],
                "pub_hike_pct": b["hike_pct"], "pub_saidi_w25": b["saidi_w25"], "pub_cust": b["total_cust"],
                "rate_diff_cents": round(a["rate25"] - b["rate25"], 2),
                "annual_diff_at_900kwh": round((a["rate25"] - b["rate25"]) / 100.0 * 900 * 12),
            })

    # National reliability medians across traditional utilities
    trad_recs = [r for r in records if r["own"] in TRADITIONAL_OWNERSHIPS]
    all_sw25 = [r["saidi_w25"] for r in trad_recs if r["saidi_w25"] is not None]
    all_swo25 = [r["saidi_wo25"] for r in trad_recs if r["saidi_wo25"] is not None]
    all_rates25 = [r["rate25"] for r in records]
    all_hikes = [r["hike_pct"] for r in records if r["hike_pct"] is not None]

    # Headline numbers
    res_hike_pct_nat = round((nat25["res_rate"] / nat20["res_rate"] - 1.0) * 100.0, 1)
    res_rev_diff_b = round(nat25["res_rev_b"] - nat20["res_rev_b"], 2)
    ind_ratio = round(nat25["res_rate"] / nat25["ind_rate"], 2) if nat25["ind_rate"] else None

    summary = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "U.S. Energy Information Administration (EIA) Form EIA-861 (Annual Electric Power Industry Report)",
            "source_url": "https://www.eia.gov/electricity/data/eia861/",
            "latest_year": LATEST_YEAR,
            "prior_rel_year": PRIOR_REL_YEAR,
            "base_year": BASE_YEAR,
        },
        "national": {
            "y2025": nat25,
            "y2024": nat24,
            "y2020": nat20,
            "res_hike_pct_20_25": res_hike_pct_nat,
            "res_rev_increase_b_20_25": res_rev_diff_b,
            "res_vs_ind_ratio": ind_ratio,
            "utilities_analyzed": len(records),
            "traditional_utilities": len(trad_recs),
            "bundled_cust_covered": sum(r["bundled_cust"] for r in records),
            "total_footprint_cust": sum(r["total_cust"] for r in records),
            "rel_utilities_2025": len(all_sw25),
            "rel_cust_pct": round(
                sum(r["bundled_cust"] for r in trad_recs if r["saidi_w25"] is not None)
                / sum(r["bundled_cust"] for r in trad_recs)
                * 100.0,
                1,
            ),
            "med_rate25": med(all_rates25),
            "p25_rate25": round(sorted(all_rates25)[len(all_rates25) // 4], 2),
            "p75_rate25": round(sorted(all_rates25)[(3 * len(all_rates25)) // 4], 2),
            "med_hike_pct": r1(statistics.median(all_hikes)) if all_hikes else None,
            "med_saidi_w25": r1(statistics.median(all_sw25)) if all_sw25 else None,
            "med_saidi_wo25": r1(statistics.median(all_swo25)) if all_swo25 else None,
        },
        "same_state_iou_vs_public": {
            "states_compared": len(major_states),
            "states_iou_higher": iou_higher_count,
            "pct_states_iou_higher": round(iou_higher_count / len(major_states) * 100.0, 1) if major_states else None,
            "annual_excess_b": round(total_same_state_excess / 1e9, 2),
            "top_state_gaps": top_state_gaps,
        },
        "by_ownership": by_ownership,
        "neighbor_pairs": neighbor_pairs,
        "top_15_largest": top_15_largest,
        "worst_15_hikes": worst_15_hikes,
        "by_state": same_state,
    }

    # Write summary.json and summary-data.js
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ROOT / "summary-data.js").write_text(
        "window.UTILITY_SUMMARY = " + json.dumps(summary, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    # Write compact columnar utilities.json for instant client-side search (name, county, state)
    cols = [
        "uid", "name", "state", "own", "total_cust", "bundled_cust", "deliv_cust",
        "rate25", "rate20", "hike_pct", "hike_yr_dollars", "avg_kwh_mo", "avg_bill_mo",
        "ind_rate", "state_pub_rate", "vs_pub_cents", "vs_pub_yr",
        "saidi_w25", "saidi_wo25", "saifi_w25", "saidi_w24", "saidi_2yr", "rel_std", "counties",
    ]
    compact_rows = [
        [
            r["uid"], r["name"], r["state"], r["own"], r["total_cust"], r["bundled_cust"], r["deliv_cust"],
            r["rate25"], r["rate20"], r["hike_pct"], r["hike_yr_dollars"], r["avg_kwh_mo"], r["avg_bill_mo"],
            r["ind_rate"], r["state_pub_rate"], r["vs_pub_cents"], r["vs_pub_yr"],
            r["saidi_w25"], r["saidi_wo25"], r["saifi_w25"], r["saidi_w24"], r["saidi_2yr"],
            r["rel_std"], r["counties_short"],
        ]
        for r in records
    ]
    (ROOT / "utilities.json").write_text(
        json.dumps({"cols": cols, "rows": compact_rows}, separators=(",", ":")),
        encoding="utf-8",
    )

    # Write full open CSV.gz dataset
    csv_cols = [
        "eia_utility_id", "utility_name", "state", "ownership", "part", "balancing_authority",
        "total_res_customers_2025", "bundled_res_customers_2025", "delivery_only_res_customers_2025",
        "bundled_res_mwh_2025", "bundled_res_revenue_k_2025",
        "res_rate_cents_kwh_2025", "res_rate_cents_kwh_2020", "rate_hike_cents_20_25", "rate_hike_pct_20_25",
        "est_annual_hike_dollars_per_hh", "avg_monthly_kwh_2025", "avg_monthly_bill_2025",
        "commercial_rate_cents_kwh_2025", "industrial_rate_cents_kwh_2025",
        "in_state_public_power_rate_2025", "vs_in_state_public_cents", "vs_in_state_public_annual_dollars",
        "saidi_with_med_min_2025", "saidi_without_med_min_2025", "saifi_with_med_2025", "saifi_without_med_2025",
        "saidi_with_med_min_2024", "saidi_without_med_min_2024", "saidi_2yr_avg_min", "saidi_with_med_min_2020",
        "reliability_standard", "counties_served",
    ]
    csv_path = ROOT / "eia-861-utilities-2020-2025.csv.gz"
    with gzip.open(csv_path, "wt", encoding="utf-8", newline="") as gz:
        w = csv.writer(gz)
        w.writerow(csv_cols)
        for r in records:
            w.writerow([
                r["uid"], r["name"], r["state"], r["own"], r["part"], r["ba"],
                r["total_cust"], r["bundled_cust"], r["deliv_cust"],
                r["res_mwh"], r["res_rev_k"],
                r["rate25"], r["rate20"], r["hike_cents"], r["hike_pct"],
                r["hike_yr_dollars"], r["avg_kwh_mo"], r["avg_bill_mo"],
                r["com_rate"], r["ind_rate"],
                r["state_pub_rate"], r["vs_pub_cents"], r["vs_pub_yr"],
                r["saidi_w25"], r["saidi_wo25"], r["saifi_w25"], r["saifi_wo25"],
                r["saidi_w24"], r["saidi_wo24"], r["saidi_2yr"], r["saidi_w20"],
                r["rel_std"], r["counties_full"],
            ])

    print(f"\n=== EIA-861 PIPELINE COMPLETE ({len(records)} utilities) ===")
    print(f"National 2020->2025 Res Rate: {nat20['res_rate']}c -> {nat25['res_rate']}c ({res_hike_pct_nat:+.1f}%), Rev +${res_rev_diff_b}B/yr")
    print(f"Same-State IOU > Public Power: {iou_higher_count}/{len(major_states)} states ({summary['same_state_iou_vs_public']['pct_states_iou_higher']}%), Excess = ${summary['same_state_iou_vs_public']['annual_excess_b']}B/yr")
    for o in by_ownership:
        print(f"  {o['label']:38s}: n={o['utilities']:4d} | wavg25={o['wavg_rate25']}c (hike {o['wavg_hike_pct']}%) | SAIDI w/MED={o['med_saidi_w25']}m w/o={o['med_saidi_wo25']}m")
    print(f"Neighbor pairs matched: {len(neighbor_pairs)}/{len(neighbor_pairs_spec)}")
    for p in neighbor_pairs:
        print(f"  {p['region']}: {p['iou_name']} ({p['iou_rate25']}c, SAIDI {p['iou_saidi_w25']}m) vs {p['pub_name']} ({p['pub_rate25']}c, SAIDI {p['pub_saidi_w25']}m) -> +${p['annual_diff_at_900kwh']}/yr")


if __name__ == "__main__":
    main()
