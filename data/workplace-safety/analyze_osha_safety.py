#!/usr/bin/env python3
"""
OSHA U.S. Workplace Injury & Severe Amputation Accountability Pipeline
(2025 Form 300A ITA Summary + 2015-2025 Federal Severe Injury Reports).

Downloads directly from official osha.gov bulk endpoints:
  1. 2025 ITA Form 300A Establishment Summary Data (~400,288 raw filings)
  2. 2015-2025 Federal OSHA Severe Injury Reports (~105,996 events)

Critical data-hygiene & accounting safeguards built in:
  - Deduplicates ~6,700+ duplicate establishment submissions (e.g., identical
    normalized street address + ZIP5 + state + employees + hours submitted under
    multiple establishment_IDs on consecutive days, keeping the latest filing).
  - Filters clerical hours/headcount errors (hours/employee outside [400, 4000],
    headcount vs. OSHA size-bucket extreme mismatches, or impossible TCR > 150).
  - Normalizes fragmented corporate subsidiaries into unified parent companies
    (e.g., Walmart + Sam's Club, JBS + Swift + Pilgrim's Pride, FedEx Express +
    Ground + Freight, USPS spelling variants, United Continental Holdings).
  - Computes NAICS-weighted peer industry benchmark TCR/DART for each corporate
    parent so employers are compared fairly against their exact industry mix.
  - Explicitly documents Federal OSHA (29 jurisdictions) vs. 21 State-Plan
    states for Severe Injury Reports (SIR) while Form 300A covers all 50 states.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CURL_BIN = shutil.which("curl.exe") or shutil.which("curl") or "curl"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

ITA_PAGE = "https://www.osha.gov/Establishment-Specific-Injury-and-Illness-Data"
SIR_PAGE = "https://www.osha.gov/severe-injury-reports"

DEFAULT_ITA_URL = "https://www.osha.gov/sites/default/largefiles/ITA_300A_Summary_Data_2025_through_08-31-2026.csv"
DEFAULT_SIR_URL = "https://www.osha.gov/sites/default/files/January2015toNovember2025.zip"

CACHE_DIR = Path(
    os.environ.get("OSHA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "osha_cache"))
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
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

# 21 states with private-sector OSHA State Plans (SIR reports go to state agencies, not Fed SIR)
STATE_PLAN_PRIVATE = {
    "AK", "AZ", "CA", "HI", "IN", "IA", "KY", "MD", "MI", "MN",
    "NV", "NM", "NC", "OR", "SC", "TN", "UT", "VT", "VA", "WA", "WY",
}

# Normalized major corporate parents across 300A & SIR
MAJOR_PARENTS = [
    ("Walmart (incl. Sam's Club)", r"\bWAL[\s-]*MART\b|\bSAM'?S\s+(?:CLUB|EAST|WEST)\b"),
    ("Amazon", r"\bAMAZON(?:\.COM)?\b"),
    ("Target", r"^TARGET\b|\bTARGET\s+CORP"),
    ("UPS", r"^UPS\b|\bUNITED\s+PARCEL\s+SERVICE\b"),
    ("FedEx", r"\bFEDEX\b|\bFEDERAL\s+EXPRESS\b"),
    ("Costco Wholesale", r"\bCOSTCO\b"),
    ("Lowe's", r"\bLOWE'?S\s+(?:HOME|COMPAN|COS)"),
    ("Publix Super Markets", r"\bPUBLIX\b"),
    ("Kroger", r"\bKROGER\b"),
    ("H-E-B", r"\bH-?E-?B\b"),
    ("Menards", r"\bMENARDS?\b"),
    ("American Airlines", r"\bAMERICAN\s+AIRLINES\b"),
    ("Delta Air Lines", r"\bDELTA\s+AIR\s+LINES\b"),
    ("Southwest Airlines", r"\bSOUTHWEST\s+AIRLINES\b"),
    ("United Airlines", r"\bUNITED\s+(?:AIRLINES|CONTINENTAL\s+HOLDINGS)\b"),
    ("Alaska Airlines", r"\bALASKA\s+AIRLINES\b"),
    ("Boeing", r"\bBOEING\b"),
    ("Ford Motor", r"\bFORD\s+MOTOR\b"),
    ("General Motors", r"\bGENERAL\s+MOTORS\b"),
    ("Tesla", r"\bTESLA\b"),
    ("Tyson Foods", r"\bTYSON\s+(?:FOODS|FRESH|POULTRY|PREPARED|FARMS)|\bTYSON\s+INC"),
    ("JBS / Pilgrim's Pride", r"\bJBS\b|\bSWIFT\s+(?:BEEF|PORK|PREPARED)|\bPILGRIM'?S\s+PRIDE\b"),
    ("Smithfield Foods", r"\bSMITHFIELD\b"),
    ("PepsiCo / Frito-Lay", r"\bPEPSICO\b|\bFRITO[\s-]*LAY\b|\bPEPSI\s+BEVERAGES\b"),
    ("Coca-Cola Bottlers", r"\bCOCA[\s-]*COLA\b"),
    ("Sysco", r"\bSYSCO\b"),
    ("US Foods", r"\bUS\s+FOODS\b|\bU\.S\.\s+FOODS\b"),
    ("Waste Management (WM)", r"\bWASTE\s+MANAGEMENT\b|\bWM\s+OF\b"),
    ("Republic Services", r"\bREPUBLIC\s+SERVICES\b"),
    ("Compass Group", r"\bCOMPASS\s+GROUP\b"),
    ("USPS (Federal)", r"\bU\.?S\.?\s*POSTAL\s+SERVICE\b|\bUNITED\s+STATES\s+POSTAL\b|\bUSPS\b"),
    ("Dollar Tree / Family Dollar", r"\bDOLLAR\s+TREE\b|\bFAMILY\s+DOLLAR\b"),
]
COMPILED_PARENTS = [(lbl, re.compile(pat, re.I)) for lbl, pat in MAJOR_PARENTS]

NAICS2_LABELS = {
    "11": "Agriculture, Forestry & Fishing",
    "21": "Mining, Quarrying & Oil/Gas",
    "22": "Utilities",
    "23": "Construction",
    "31": "Manufacturing (Food, Beverage, Textiles)",
    "32": "Manufacturing (Wood, Paper, Chemical, Plastics)",
    "33": "Manufacturing (Metals, Machinery, Auto, Aerospace)",
    "42": "Wholesale Trade",
    "44": "Retail Trade (Stores, Grocery, Home Centers)",
    "45": "Retail Trade (General Merchandise & E-Commerce)",
    "48": "Transportation (Airlines, Trucking, Couriers)",
    "49": "Warehousing, Storage & Postal",
    "51": "Information",
    "52": "Finance & Insurance",
    "53": "Real Estate & Rental",
    "54": "Professional & Technical Services",
    "56": "Waste Management & Admin Support",
    "61": "Educational Services",
    "62": "Healthcare & Social Assistance",
    "71": "Arts, Entertainment & Recreation",
    "72": "Accommodation & Food Services",
    "81": "Other Services (Repair, Laundry)",
    "92": "Public Administration",
}


def flt(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def norm_text(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"[^A-Z0-9]+", " ", s.upper()).strip()


def match_parent(company: str | None, est: str | None = None) -> str | None:
    for txt in (company, est):
        if not txt:
            continue
        for lbl, rx in COMPILED_PARENTS:
            if rx.search(txt):
                return lbl
    return None


def norm_company_key(company: str | None) -> str:
    s = norm_text(company)
    # Strip common legal suffixes for grouping non-spotlight employers
    s = re.sub(r"\b(?:INC|INCORPORATED|LLC|L L C|LP|L P|LLP|CORP|CORPORATION|CO|COMPANY|LTD|HOLDINGS|GROUP)\b", "", s)
    return " ".join(s.split())


def discover_latest_urls() -> tuple[str, str]:
    ita_url, sir_url = DEFAULT_ITA_URL, DEFAULT_SIR_URL
    try:
        html = subprocess.check_output(
            [CURL_BIN, "-sL", "-A", UA, ITA_PAGE], text=True, errors="replace"
        )
        m = re.search(r'href=["\']([^"\']*ITA_300A_Summary_Data_202[5-9][^"\']*\.(?:csv|zip))["\']', html, re.I)
        if m:
            href = m.group(1)
            ita_url = href if href.startswith("http") else "https://www.osha.gov" + href
    except Exception:
        pass
    try:
        html = subprocess.check_output(
            [CURL_BIN, "-sL", "-A", UA, SIR_PAGE], text=True, errors="replace"
        )
        m = re.search(r'href=["\']([^"\']*January2015to[^"\']*\.zip)["\']', html, re.I)
        if m:
            href = m.group(1)
            sir_url = href if href.startswith("http") else "https://www.osha.gov" + href
    except Exception:
        pass
    return ita_url, sir_url


def fetch_file(url: str, filename: str, referer: str, min_bytes: int = 1_000_000) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / filename
    if dst.exists() and dst.stat().st_size >= min_bytes:
        return dst
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    code = subprocess.check_output(
        [CURL_BIN, "-sL", "-A", UA, "-H", f"Referer: {referer}", "-w", "%{http_code}", "-o", str(tmp), url],
        text=True,
    ).strip()
    if code != "200" or not tmp.exists() or tmp.stat().st_size < min_bytes:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed downloading {url}: HTTP {code}")
    tmp.replace(dst)
    print(f"Downloaded {filename} ({dst.stat().st_size:,} bytes) from {url}")
    return dst


def main() -> None:
    ita_url, sir_url = discover_latest_urls()
    ita_path = fetch_file(ita_url, "ita_2025.csv", ITA_PAGE, min_bytes=10_000_000)
    sir_path = fetch_file(sir_url, "sir_2015_2025.zip", SIR_PAGE, min_bytes=5_000_000)

    # 1. Stream & clean ITA 2025 Form 300A filings with duplicate detection
    raw_count = 0
    dropped_bad_hrs = 0
    dropped_size_outlier = 0
    dropped_rate_outlier = 0
    dup_count = 0

    # Deduplicate by (norm_street, zip5, state, emp_int, hrs_int, inj_int) keeping latest date_submitted
    # Also catch same establishment submitted twice with slightly different punctuation in name
    dedup_map: dict[tuple, dict[str, Any]] = {}

    open_fn = None
    if ita_path.suffix.lower() == ".zip":
        zf_ita = zipfile.ZipFile(ita_path)
        csv_member = [n for n in zf_ita.namelist() if n.lower().endswith(".csv")][0]
        raw_stream = io.TextIOWrapper(zf_ita.open(csv_member), encoding="utf-8-sig", errors="replace")
    else:
        zf_ita = None
        raw_stream = open(ita_path, "r", encoding="utf-8-sig", errors="replace")

    try:
        reader = csv.DictReader(raw_stream)
        for row in reader:
            raw_count += 1
            emp = flt(row.get("annual_average_employees"))
            hrs = flt(row.get("total_hours_worked"))
            if emp < 1 or hrs <= 0:
                dropped_bad_hrs += 1
                continue
            hpe = hrs / emp
            if hpe < 400 or hpe > 4000:
                dropped_bad_hrs += 1
                continue

            sz = str(row.get("size") or "").strip()
            if emp > 30_000 or (sz == "1" and emp >= 100) or (sz == "2" and emp >= 1000):
                dropped_size_outlier += 1
                continue

            deaths = flt(row.get("total_deaths"))
            dafw = flt(row.get("total_dafw_cases"))
            djtr = flt(row.get("total_djtr_cases"))
            other = flt(row.get("total_other_cases"))
            inj = deaths + dafw + djtr + other
            dart = dafw + djtr
            tcr = inj * 200_000.0 / hrs
            if tcr > 150.0:
                dropped_rate_outlier += 1
                continue

            st = (row.get("state") or "").strip().upper()
            zp = (row.get("zip_code") or "").strip()[:5]
            addr_n = norm_text(row.get("street_address"))
            est_n = norm_text(row.get("establishment_name"))
            # Strong duplicate key: exact same street+zip+state+employees+hours+injuries
            # (catches Costco/H-E-B double submissions while preserving distinct departments at same address!)
            dkey = (addr_n or est_n, zp, st, int(round(emp)), int(round(hrs)), int(round(inj)))
            rec = {
                "eid": row.get("establishment_ID") or row.get("ID"),
                "est": (row.get("establishment_name") or "").strip(),
                "co": (row.get("company_name") or "").strip(),
                "city": (row.get("city") or "").strip(),
                "state": st,
                "zip": zp,
                "naics": (row.get("naics_code") or "").strip(),
                "ind_desc": (row.get("industry_description") or "").strip(),
                "emp": emp,
                "hrs": hrs,
                "inj": inj,
                "dart": dart,
                "dafw": dafw,
                "djtr": djtr,
                "deaths": deaths,
                "dafw_days": flt(row.get("total_dafw_days")),
                "djtr_days": flt(row.get("total_djtr_days")),
                "sub_date": (row.get("date_submitted") or "").strip(),
            }
            if dkey in dedup_map:
                dup_count += 1
                # Keep the later submission date (MM/DD/YYYY or ISO)
                if rec["sub_date"] >= dedup_map[dkey]["sub_date"]:
                    dedup_map[dkey] = rec
            else:
                dedup_map[dkey] = rec
    finally:
        raw_stream.close()
        if zf_ita:
            zf_ita.close()

    clean = list(dedup_map.values())

    # 2. Compute National, NAICS-4, NAICS-2, and State 2025 ITA Totals
    tot_emp = sum(r["emp"] for r in clean)
    tot_hrs = sum(r["hrs"] for r in clean)
    tot_inj = sum(r["inj"] for r in clean)
    tot_dart = sum(r["dart"] for r in clean)
    tot_deaths = sum(r["deaths"] for r in clean)
    tot_dafw_days = sum(r["dafw_days"] for r in clean)
    nat_tcr = tot_inj * 200_000.0 / tot_hrs
    nat_dart = tot_dart * 200_000.0 / tot_hrs

    # NAICS-4 industry stats (and NAICS-6 descriptions)
    naics4_acc: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"sites": 0, "emp": 0.0, "hrs": 0.0, "inj": 0.0, "dart": 0.0, "deaths": 0.0, "dafw_days": 0.0, "descs": Counter()}
    )
    naics2_acc: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"sites": 0, "emp": 0.0, "hrs": 0.0, "inj": 0.0, "dart": 0.0, "deaths": 0.0}
    )
    state_ita: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"sites": 0, "emp": 0.0, "hrs": 0.0, "inj": 0.0, "dart": 0.0, "deaths": 0.0}
    )

    for r in clean:
        n4 = r["naics"][:4] if len(r["naics"]) >= 4 else ""
        n2 = r["naics"][:2] if len(r["naics"]) >= 2 else ""
        if n4:
            a = naics4_acc[n4]
            a["sites"] += 1; a["emp"] += r["emp"]; a["hrs"] += r["hrs"]
            a["inj"] += r["inj"]; a["dart"] += r["dart"]; a["deaths"] += r["deaths"]; a["dafw_days"] += r["dafw_days"]
            if r["ind_desc"]:
                a["descs"][r["ind_desc"]] += 1
        if n2 in NAICS2_LABELS:
            b = naics2_acc[n2]
            b["sites"] += 1; b["emp"] += r["emp"]; b["hrs"] += r["hrs"]
            b["inj"] += r["inj"]; b["dart"] += r["dart"]; b["deaths"] += r["deaths"]
        if r["state"] in STATE_NAMES:
            s = state_ita[r["state"]]
            s["sites"] += 1; s["emp"] += r["emp"]; s["hrs"] += r["hrs"]
            s["inj"] += r["inj"]; s["dart"] += r["dart"]; s["deaths"] += r["deaths"]

    naics4_tcr = {k: (v["inj"] * 200_000.0 / v["hrs"]) for k, v in naics4_acc.items() if v["hrs"] > 0}
    naics4_dart = {k: (v["dart"] * 200_000.0 / v["hrs"]) for k, v in naics4_acc.items() if v["hrs"] > 0}

    # 3. Stream & aggregate 2015-2025 Severe Injury Reports (SIR)
    sir_total = 0
    sir_hosp = 0
    sir_amp = 0
    sir_eye = 0
    sir_by_year: dict[str, dict[str, int]] = defaultdict(lambda: {"events": 0, "hosp": 0, "amp": 0})
    sir_by_parent: dict[str, dict[str, int]] = defaultdict(lambda: {"events": 0, "hosp": 0, "amp": 0, "eye": 0, "events_24_25": 0})
    sir_by_co_norm: dict[str, dict[str, int]] = defaultdict(lambda: {"events": 0, "hosp": 0, "amp": 0})
    sir_by_naics4: dict[str, dict[str, int]] = defaultdict(lambda: {"events": 0, "hosp": 0, "amp": 0})
    sir_by_state: dict[str, dict[str, int]] = defaultdict(lambda: {"events": 0, "hosp": 0, "amp": 0})
    sir_amp_sources: Counter = Counter()
    sir_events_types: Counter = Counter()

    with zipfile.ZipFile(sir_path) as zf:
        csv_name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
        with zf.open(csv_name) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", errors="replace"))
            for row in reader:
                sir_total += 1
                h = int(flt(row.get("Hospitalized")))
                a = int(flt(row.get("Amputation")))
                e = int(flt(row.get("Loss of Eye")))
                sir_hosp += h
                sir_amp += a
                sir_eye += e

                ed = (row.get("EventDate") or "").strip()
                yr = ed.split("/")[-1][:4] if "/" in ed else ed[:4]
                if yr.isdigit():
                    sir_by_year[yr]["events"] += 1
                    sir_by_year[yr]["hosp"] += h
                    sir_by_year[yr]["amp"] += a

                st_raw = (row.get("State") or "").strip().upper()
                # Map full state name to 2-letter code if needed
                st_code = st_raw if len(st_raw) == 2 else next((k for k, v in STATE_NAMES.items() if v.upper() == st_raw), "")
                if st_code:
                    sir_by_state[st_code]["events"] += 1
                    sir_by_state[st_code]["hosp"] += h
                    sir_by_state[st_code]["amp"] += a

                n4 = (row.get("Primary NAICS") or "").strip()[:4]
                if len(n4) == 4 and n4.isdigit():
                    sir_by_naics4[n4]["events"] += 1
                    sir_by_naics4[n4]["hosp"] += h
                    sir_by_naics4[n4]["amp"] += a

                if a > 0:
                    src = (row.get("SourceTitle") or "").strip()
                    if src:
                        sir_amp_sources[src] += a
                ev_t = (row.get("EventTitle") or "").strip()
                if ev_t:
                    sir_events_types[ev_t] += 1

                emp_name = (row.get("Employer") or "").strip()
                p = match_parent(emp_name)
                if p:
                    sir_by_parent[p]["events"] += 1
                    sir_by_parent[p]["hosp"] += h
                    sir_by_parent[p]["amp"] += a
                    sir_by_parent[p]["eye"] += e
                    if yr in ("2024", "2025"):
                        sir_by_parent[p]["events_24_25"] += 1
                nk = norm_company_key(emp_name)
                if nk:
                    sir_by_co_norm[nk]["events"] += 1
                    sir_by_co_norm[nk]["hosp"] += h
                    sir_by_co_norm[nk]["amp"] += a

    # 4. Aggregate Corporate Employers (Major normalized parents + general normalized company names)
    emp_groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "is_major": False, "display": "", "raw_names": Counter(), "states": Counter(),
            "naics4": Counter(), "sites": 0, "emp": 0.0, "hrs": 0.0, "inj": 0.0,
            "dart": 0.0, "deaths": 0.0, "dafw_days": 0.0,
            "exp_inj": 0.0, "exp_dart": 0.0,
        }
    )

    for r in clean:
        p = match_parent(r["co"], r["est"])
        if p:
            gkey = "MAJOR::" + p
            g = emp_groups[gkey]
            g["is_major"] = True
            g["display"] = p
        else:
            nk = norm_company_key(r["co"] or r["est"])
            if not nk or len(nk) < 3:
                continue
            gkey = "CO::" + nk
            g = emp_groups[gkey]
            g["raw_names"][r["co"] or r["est"]] += 1

        g["sites"] += 1
        g["emp"] += r["emp"]
        g["hrs"] += r["hrs"]
        g["inj"] += r["inj"]
        g["dart"] += r["dart"]
        g["deaths"] += r["deaths"]
        g["dafw_days"] += r["dafw_days"]
        if r["state"] in STATE_NAMES:
            g["states"][r["state"]] += 1
        n4 = r["naics"][:4] if len(r["naics"]) >= 4 else ""
        if n4:
            g["naics4"][n4] += r["hrs"]
            if n4 in naics4_tcr:
                g["exp_inj"] += naics4_tcr[n4] * (r["hrs"] / 200_000.0)
                g["exp_dart"] += naics4_dart[n4] * (r["hrs"] / 200_000.0)

    employers_list: list[dict[str, Any]] = []
    major_scorecard: list[dict[str, Any]] = []

    for gkey, g in emp_groups.items():
        if not g["is_major"] and g["emp"] < 1000:
            continue
        if g["is_major"] and g["emp"] < 2000 and g["display"] != "USPS (Federal)":
            continue
        name = g["display"] if g["is_major"] else g["raw_names"].most_common(1)[0][0]
        tcr = g["inj"] * 200_000.0 / g["hrs"]
        dart = g["dart"] * 200_000.0 / g["hrs"]
        dart_share = (g["dart"] / g["inj"] * 100.0) if g["inj"] > 0 else 0.0
        peer_tcr = (g["exp_inj"] * 200_000.0 / g["hrs"]) if g["exp_inj"] > 0 else nat_tcr
        peer_dart = (g["exp_dart"] * 200_000.0 / g["hrs"]) if g["exp_dart"] > 0 else nat_dart
        dart_ratio = (dart / peer_dart) if peer_dart > 0 else None

        top_n4 = g["naics4"].most_common(1)[0][0] if g["naics4"] else ""
        top_ind = naics4_acc[top_n4]["descs"].most_common(1)[0][0] if top_n4 and naics4_acc[top_n4]["descs"] else ""
        top_st = g["states"].most_common(1)[0][0] if g["states"] else ""

        if g["is_major"]:
            sir = sir_by_parent.get(name, {"events": 0, "hosp": 0, "amp": 0, "events_24_25": 0})
        else:
            nk = gkey.split("::", 1)[1]
            sir = sir_by_co_norm.get(nk, {"events": 0, "hosp": 0, "amp": 0})

        rec = {
            "name": name,
            "is_major": g["is_major"],
            "state": top_st,
            "n_states": len(g["states"]),
            "naics4": top_n4,
            "industry": top_ind[:60],
            "sites": g["sites"],
            "emp": int(round(g["emp"])),
            "inj": int(round(g["inj"])),
            "dart_cases": int(round(g["dart"])),
            "deaths": int(round(g["deaths"])),
            "dafw_days": int(round(g["dafw_days"])),
            "tcr": round(tcr, 2),
            "dart": round(dart, 2),
            "dart_share": round(dart_share, 1),
            "peer_dart": round(peer_dart, 2),
            "dart_vs_peer": round(dart_ratio, 2) if dart_ratio is not None else None,
            "sir_events": sir.get("events", 0),
            "sir_hosp": sir.get("hosp", 0),
            "sir_amp": sir.get("amp", 0),
        }
        employers_list.append(rec)
        if g["is_major"]:
            major_scorecard.append(rec)

    employers_list.sort(key=lambda x: -x["emp"])
    major_scorecard.sort(key=lambda x: -x["emp"])

    # 5. Build Industry (4-digit NAICS) table (industries with >= 5,000 workers)
    industries_list = []
    for n4, a in naics4_acc.items():
        if a["emp"] < 5000 or a["hrs"] <= 0:
            continue
        tcr = a["inj"] * 200_000.0 / a["hrs"]
        dart = a["dart"] * 200_000.0 / a["hrs"]
        sir = sir_by_naics4.get(n4, {"events": 0, "hosp": 0, "amp": 0})
        desc = a["descs"].most_common(1)[0][0] if a["descs"] else f"NAICS {n4}"
        industries_list.append({
            "naics4": n4,
            "sector": NAICS2_LABELS.get(n4[:2], "Other"),
            "desc": desc,
            "sites": a["sites"],
            "emp": int(round(a["emp"])),
            "inj": int(round(a["inj"])),
            "dart_cases": int(round(a["dart"])),
            "deaths": int(round(a["deaths"])),
            "tcr": round(tcr, 2),
            "dart": round(dart, 2),
            "sir_events": sir["events"],
            "sir_hosp": sir["hosp"],
            "sir_amp": sir["amp"],
        })
    industries_list.sort(key=lambda x: -x["dart"])

    # 6. Build Top 1,000 Highest-Injury Large Individual Workplaces (>= 150 employees & >= 10 DART cases)
    hotspots_raw = []
    for r in clean:
        if r["emp"] < 150 or r["dart"] < 10 or r["state"] not in STATE_NAMES:
            continue
        tcr = r["inj"] * 200_000.0 / r["hrs"]
        dart = r["dart"] * 200_000.0 / r["hrs"]
        n4 = r["naics"][:4]
        p_dart = naics4_dart.get(n4, nat_dart)
        hotspots_raw.append({
            "est": r["est"][:60],
            "co": (match_parent(r["co"], r["est"]) or r["co"] or r["est"])[:50],
            "city": r["city"][:30],
            "state": r["state"],
            "ind": r["ind_desc"][:45],
            "emp": int(round(r["emp"])),
            "inj": int(round(r["inj"])),
            "dart_cases": int(round(r["dart"])),
            "tcr": round(tcr, 2),
            "dart": round(dart, 2),
            "vs_peer": round(dart / p_dart, 2) if p_dart > 0 else None,
            "dafw_days": int(round(r["dafw_days"])),
        })
    hotspots_raw.sort(key=lambda x: (-x["dart"], -x["dart_cases"]))
    hotspots = hotspots_raw[:1000]

    # 7. Sector (2-digit NAICS) summary
    sectors = []
    for n2, b in naics2_acc.items():
        if b["emp"] < 20_000:
            continue
        sectors.append({
            "naics2": n2,
            "label": NAICS2_LABELS[n2],
            "sites": b["sites"],
            "emp": int(round(b["emp"])),
            "inj": int(round(b["inj"])),
            "tcr": round(b["inj"] * 200_000.0 / b["hrs"], 2),
            "dart": round(b["dart"] * 200_000.0 / b["hrs"], 2),
            "deaths": int(round(b["deaths"])),
        })
    sectors.sort(key=lambda x: -x["dart"])

    # 8. State summary
    by_state = []
    for st in sorted(STATE_NAMES.keys()):
        s = state_ita[st]
        sir_s = sir_by_state[st]
        by_state.append({
            "state": st,
            "name": STATE_NAMES[st],
            "state_plan": st in STATE_PLAN_PRIVATE,
            "sites": s["sites"],
            "emp": int(round(s["emp"])),
            "inj": int(round(s["inj"])),
            "tcr": round(s["inj"] * 200_000.0 / s["hrs"], 2) if s["hrs"] else None,
            "dart": round(s["dart"] * 200_000.0 / s["hrs"], 2) if s["hrs"] else None,
            "deaths": int(round(s["deaths"])),
            "sir_events": sir_s["events"],
            "sir_hosp": sir_s["hosp"],
            "sir_amp": sir_s["amp"],
        })

    # Top amputation employers from SIR (normalized major parents)
    top_amp_employers = sorted(
        [
            {"name": k, **v}
            for k, v in sir_by_parent.items()
            if v["amp"] > 0
        ],
        key=lambda x: -x["amp"],
    )[:15]

    summary = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ita_source": "OSHA Injury Tracking Application (ITA) 2025 Form 300A Summary Data",
            "ita_url": ita_url,
            "sir_source": "Federal OSHA Severe Injury Reports (Jan 2015 – Nov 2025, 29 Federal Jurisdictions)",
            "sir_url": sir_url,
        },
        "data_hygiene": {
            "raw_300a_rows": raw_count,
            "exact_duplicates_removed": dup_count,
            "bad_hours_dropped": dropped_bad_hrs,
            "size_outliers_dropped": dropped_size_outlier,
            "rate_outliers_dropped": dropped_rate_outlier,
            "clean_establishments": len(clean),
        },
        "national": {
            "establishments": len(clean),
            "workers": int(round(tot_emp)),
            "hours_b": round(tot_hrs / 1e9, 2),
            "total_injuries": int(round(tot_inj)),
            "dart_cases": int(round(tot_dart)),
            "deaths": int(round(tot_deaths)),
            "dafw_days_m": round(tot_dafw_days / 1e6, 2),
            "tcr": round(nat_tcr, 2),
            "dart": round(nat_dart, 2),
            "employers_tracked": len(employers_list),
            "industries_tracked": len(industries_list),
            "sir_events": sir_total,
            "sir_hosp": sir_hosp,
            "sir_amp": sir_amp,
            "sir_eye": sir_eye,
        },
        "major_scorecard": major_scorecard,
        "top_amp_employers": top_amp_employers,
        "top_amp_sources": [{"source": k, "amputations": v} for k, v in sir_amp_sources.most_common(10)],
        "top_dangerous_industries": industries_list[:20],
        "sectors": sectors,
        "sir_by_year": [{"year": yr, **d} for yr, d in sorted(sir_by_year.items()) if yr.isdigit() and int(yr) >= 2015],
        "by_state": by_state,
    }

    # Emit JSON & JS files
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ROOT / "summary-data.js").write_text(
        "window.OSHA_SUMMARY = " + json.dumps(summary, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    # Compact columnar employers.json (all employers >= 1,000 workers + major parents)
    e_cols = ["name", "is_major", "state", "n_states", "industry", "sites", "emp", "inj", "dart_cases", "deaths", "tcr", "dart", "dart_share", "peer_dart", "dart_vs_peer", "sir_events", "sir_hosp", "sir_amp"]
    e_rows = [[r[c] for c in e_cols] for r in employers_list]
    (ROOT / "employers.json").write_text(
        json.dumps({"cols": e_cols, "rows": e_rows}, separators=(",", ":")),
        encoding="utf-8",
    )

    # Compact industries.json
    i_cols = ["naics4", "sector", "desc", "sites", "emp", "inj", "tcr", "dart", "deaths", "sir_events", "sir_hosp", "sir_amp"]
    i_rows = [[r[c] for c in i_cols] for r in industries_list]
    (ROOT / "industries.json").write_text(
        json.dumps({"cols": i_cols, "rows": i_rows}, separators=(",", ":")),
        encoding="utf-8",
    )

    # Compact hotspots.json (top 1,000 highest-DART large individual sites)
    h_cols = ["est", "co", "city", "state", "ind", "emp", "inj", "dart_cases", "tcr", "dart", "vs_peer", "dafw_days"]
    h_rows = [[r[c] for c in h_cols] for r in hotspots]
    (ROOT / "hotspots.json").write_text(
        json.dumps({"cols": h_cols, "rows": h_rows}, separators=(",", ":")),
        encoding="utf-8",
    )

    # Emit open bulk CSV.gz (employers + industries)
    with gzip.open(ROOT / "osha-employers-2025.csv.gz", "wt", encoding="utf-8", newline="") as gz:
        w = csv.writer(gz)
        w.writerow(e_cols)
        for r in employers_list:
            w.writerow([r[c] for c in e_cols])

    with gzip.open(ROOT / "osha-industries-2025.csv.gz", "wt", encoding="utf-8", newline="") as gz:
        w = csv.writer(gz)
        w.writerow(i_cols)
        for r in industries_list:
            w.writerow([r[c] for c in i_cols])

    print(f"\n=== OSHA PIPELINE COMPLETE ===")
    print(f"Raw 300A: {raw_count:,} | Exact dups removed: {dup_count:,} | Clean establishments: {len(clean):,}")
    print(f"Workers: {tot_emp:,.0f} | Injuries: {tot_inj:,.0f} | DART: {tot_dart:,.0f} | Deaths: {tot_deaths:,.0f} | TCR={nat_tcr:.2f} | DART={nat_dart:.2f}")
    print(f"SIR 2015-2025: {sir_total:,} events | Hosp={sir_hosp:,} | Amp={sir_amp:,}")
    print(f"Employers (>=1k workers): {len(employers_list):,} | Industries (NAICS-4): {len(industries_list):,} | Hotspots: {len(hotspots):,}")
    print("\nTop 15 Major Employers (DEDUPLICATED!):")
    for r in major_scorecard[:15]:
        print(f"  {r['name']:28s} | sites={r['sites']:5d} | emp={r['emp']:9,} | TCR={r['tcr']:5.2f} | DART={r['dart']:5.2f} ({r['dart_vs_peer']}x peer) | SIR amp={r['sir_amp']:3d} hosp={r['sir_hosp']:4d}")


if __name__ == "__main__":
    main()
