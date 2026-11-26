"""
Reproducible 5-Dataset Analysis: U.S. Nursing Home Accountability Platform
Primary Sources (live CMS APIs, joined by normalized CCN & PECOS Enrollment ID):
  1. CMS Provider Information (4pq5-n9py) — PBJ staffing, ratings, surveys, fines, footnotes
  2. CMS Nursing Home Chain Performance Measures (data-api/v1, dynamically resolved)
  3. CMS Skilled Nursing Facility Enrollments (data-api/v1, dynamically resolved)
  4. CMS Skilled Nursing Facility All Owners / PECOS (data-api/v1, dynamically resolved)
  5. CMS Skilled Nursing Facility Cost Report FY2024 Form 2540-10 (data-api/v1, dynamically resolved)

Run:
  python analyze_cms_nursing_homes.py
  python analyze_cms_nursing_homes.py --export-csv cms-nursing-homes-linked.csv.gz

Outputs:
  - summary.json
  - summary-data.js
  - chains.json
  - facilities.json
  - (optional) linked CSV / CSV.GZ via --export-csv
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import gzip
import json
import math
import statistics
import subprocess
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).resolve().parent

PROVIDER_BASE = "https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0"
PROVIDER_PAGE_SIZE = 500
DATA_API_PAGE_SIZE = 5000
CMS_CATALOG_URL = "https://data.cms.gov/data.json"

# Fallback verified UUIDs (resolved dynamically from data.cms.gov/data.json where description == "latest")
FALLBACK_DATASETS = {
    "chains": {
        "title_prefix": "Nursing Home Chain Performance Measures",
        "uuid": "97ecfad1-d3f1-4d42-b774-d74661d830bc",
        "title": "Nursing Home Chain Performance Measures (fallback)",
    },
    "enrollments": {
        "title_prefix": "Skilled Nursing Facility Enrollments",
        "uuid": "5f2c306f-3b1c-42cd-b037-187b2ce22126",
        "title": "Skilled Nursing Facility Enrollments (fallback)",
    },
    "owners": {
        "title_prefix": "Skilled Nursing Facility All Owners",
        "uuid": "afe44b85-cc6d-40d7-b5df-00ae8910d1d2",
        "title": "Skilled Nursing Facility All Owners (fallback)",
    },
    "cost_report": {
        "title_prefix": "Skilled Nursing Facility Cost Report",
        "uuid": "a69d3df7-3f66-4a0d-b5b8-0d66049bd565",
        "title": "Skilled Nursing Facility Cost Report (fallback)",
    },
}

CMS_FOOTNOTES = {
    "1": "Data are not available because the facility is too new to have enough data to rate.",
    "2": "Data are not available or insufficient to calculate a staffing rating.",
    "6": "Submitted staffing data did not meet CMS criteria for calculation.",
    "18": "Facility is in the Special Focus Facility (SFF) program; star ratings are not displayed.",
    "23": "Facility did not submit Payroll-Based Journal (PBJ) staffing data (automatic 1-star staffing rating).",
    "24": "Facility reported a high number of days without a Registered Nurse (RN) onsite (automatic 1-star staffing rating).",
    "25": "CMS could not validate the accuracy of submitted PBJ staffing data (automatic 1-star staffing rating).",
    "26": "Turnover not reported because the facility did not submit sufficient PBJ staffing data.",
    "27": "Turnover not reported because submitted PBJ data did not meet calculation criteria.",
}

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
            raw = subprocess.check_output(["curl.exe", "-sS", "--fail", url], timeout=timeout)
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def resolve_cms_endpoints() -> dict[str, dict[str, str]]:
    """Dynamically resolve latest data-api/v1 UUIDs from data.cms.gov/data.json."""
    resolved = {
        k: {
            "title": v["title"],
            "uuid": v["uuid"],
            "url": f"https://data.cms.gov/data-api/v1/dataset/{v['uuid']}/data",
            "resolved_dynamically": "false",
        }
        for k, v in FALLBACK_DATASETS.items()
    }
    try:
        catalog = curl_json(CMS_CATALOG_URL, timeout=90, retries=2)
        for key, spec in FALLBACK_DATASETS.items():
            prefix = spec["title_prefix"]
            for ds in catalog.get("dataset", []):
                title = ds.get("title", "")
                if not title.startswith(prefix):
                    continue
                for dist in ds.get("distribution", []):
                    if dist.get("description") == "latest" and dist.get("format") == "API":
                        access_url = dist.get("accessURL", "")
                        if "/data-api/v1/dataset/" in access_url and access_url.endswith("/data"):
                            uuid = access_url.split("/data-api/v1/dataset/")[1].split("/data")[0]
                            resolved[key] = {
                                "title": title,
                                "uuid": uuid,
                                "url": access_url,
                                "resolved_dynamically": "true",
                            }
                            break
    except Exception as exc:
        print(f"[warn] Could not dynamically resolve data.json ({exc}); using verified fallback UUIDs.")
    return resolved


def fetch_provider_info(cache_dir: Path | None) -> list[dict[str, Any]]:
    if cache_dir:
        cf = cache_dir / "provider_info.json"
        if cf.exists():
            return json.loads(cf.read_text(encoding="utf-8"))

    first = curl_json(f"{PROVIDER_BASE}?limit={PROVIDER_PAGE_SIZE}&offset=0")
    total_count = int(first["count"])
    rows = list(first["results"])
    offsets = list(range(PROVIDER_PAGE_SIZE, total_count, PROVIDER_PAGE_SIZE))

    def _get(off: int) -> list[dict[str, Any]]:
        return curl_json(f"{PROVIDER_BASE}?limit={PROVIDER_PAGE_SIZE}&offset={off}").get("results", [])

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        for batch in ex.map(_get, offsets):
            rows.extend(batch)

    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "provider_info.json").write_text(json.dumps(rows), encoding="utf-8")
    return rows


def fetch_data_api(name: str, data_url: str, cache_dir: Path | None) -> list[dict[str, Any]]:
    if cache_dir:
        cf = cache_dir / f"{name}.json"
        if cf.exists():
            return json.loads(cf.read_text(encoding="utf-8"))

    stats = curl_json(f"{data_url}/stats")
    total_rows = int(stats["total_rows"])
    offsets = list(range(0, total_rows, DATA_API_PAGE_SIZE))

    def _get(off: int) -> list[dict[str, Any]]:
        return curl_json(f"{data_url}?size={DATA_API_PAGE_SIZE}&offset={off}", timeout=90)

    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        for batch in ex.map(_get, offsets):
            rows.extend(batch)

    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"{name}.json").write_text(json.dumps(rows), encoding="utf-8")
    return rows


def normalize_ccn(raw: Any) -> str:
    s = str(raw or "").strip().upper()
    if not s:
        return ""
    if s.isdigit():
        return s.zfill(6)
    return s


def to_float(v: Any) -> float | None:
    if v in (None, "", "N/A", "NA", "null"):
        return None
    try:
        s = str(v).replace(",", "").replace("$", "").strip()
        if not s:
            return None
        val = float(s)
        return val if math.isfinite(val) else None
    except ValueError:
        return None


def to_int(v: Any) -> int | None:
    f = to_float(v)
    return int(round(f)) if f is not None else None


def parse_date(v: Any) -> date | None:
    s = str(v or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None


def classify_owner(o: str | None) -> str:
    ol = (o or "").lower()
    if "for profit" in ol:
        return "For-Profit"
    if "non profit" in ol:
        return "Non-Profit"
    if "government" in ol:
        return "Government"
    return "Other"


def mean_or_none(arr: list[float], digits: int = 2) -> float | None:
    return round(statistics.mean(arr), digits) if arr else None


def med_or_none(arr: list[float], digits: int = 2) -> float | None:
    return round(statistics.median(arr), digits) if arr else None


def ratio_drop_pct(avg_7d: float | None, avg_wknd: float | None) -> float | None:
    if avg_7d is None or avg_wknd is None or avg_7d <= 0:
        return None
    return round((avg_7d - avg_wknd) / avg_7d * 100.0, 1)


def implied_wkday_raw(avg_7d: float | None, avg_wknd: float | None) -> float | None:
    if avg_7d is None or avg_wknd is None:
        return None
    val = (7.0 * avg_7d - 2.0 * avg_wknd) / 5.0
    return val if val > 0 else None


def clean_str(v: Any) -> str:
    return " ".join(str(v or "").strip().split())


def medicaid_tier(pct: float | None) -> str | None:
    if pct is None:
        return None
    if pct < 40.0:
        return "<40%"
    if pct < 60.0:
        return "40-60%"
    if pct < 80.0:
        return "60-80%"
    return "80%+"


def main() -> None:
    parser = argparse.ArgumentParser(description="5-Dataset CMS Nursing Home Accountability Analyzer")
    parser.add_argument("--cache-dir", type=Path, default=None, help="Optional directory to cache raw API responses")
    parser.add_argument("--export-csv", type=Path, default=None, help="Optional output path for linked CSV or .csv.gz")
    args = parser.parse_args()

    t0 = time.time()
    print("[1/6] Resolving live CMS endpoints via data.cms.gov/data.json...")
    endpoints = resolve_cms_endpoints()
    for k, v in endpoints.items():
        print(f"  {k:12s} -> {v['uuid']} ({v['title']})")

    print("[2/6] Fetching all 5 live CMS datasets...")
    provider_rows = fetch_provider_info(args.cache_dir)
    chain_rows = fetch_data_api("chains", endpoints["chains"]["url"], args.cache_dir)
    enrollment_rows = fetch_data_api("enrollments", endpoints["enrollments"]["url"], args.cache_dir)
    owner_rows = fetch_data_api("owners", endpoints["owners"]["url"], args.cache_dir)
    cost_rows = fetch_data_api("cost_report", endpoints["cost_report"]["url"], args.cache_dir)
    print(
        f"  Loaded: providers={len(provider_rows):,}, chains={len(chain_rows):,}, "
        f"enrollments={len(enrollment_rows):,}, owners={len(owner_rows):,}, cost_reports={len(cost_rows):,}"
    )

    # ------------------------------------------------------------------
    # Index Provider Info by normalized CCN
    # ------------------------------------------------------------------
    providers_by_ccn: dict[str, dict[str, Any]] = {}
    alphanumeric_ccns = 0
    processing_dates: Counter[str] = Counter()
    for r in provider_rows:
        ccn = normalize_ccn(r.get("cms_certification_number_ccn"))
        if not ccn:
            continue
        if not ccn.isdigit():
            alphanumeric_ccns += 1
        providers_by_ccn[ccn] = r
        pd = clean_str(r.get("processing_date"))
        if pd:
            processing_dates[pd] += 1

    processing_date = processing_dates.most_common(1)[0][0] if processing_dates else ""
    total_facilities = len(providers_by_ccn)

    # ------------------------------------------------------------------
    # Step 3: Join PECOS Enrollments -> All Owners
    # ------------------------------------------------------------------
    print("[3/6] Joining PECOS SNF Enrollments & All Owners (302k rows)...")
    enr_to_ccn: dict[str, str] = {}
    ccn_to_enrs: dict[str, set[str]] = defaultdict(set)
    for er in enrollment_rows:
        eid = clean_str(er.get("ENROLLMENT ID"))
        ccn = normalize_ccn(er.get("CCN"))
        if eid and ccn:
            enr_to_ccn[eid] = ccn
            ccn_to_enrs[ccn].add(eid)

    matched_enrollment_ccns = {ccn for ccn in ccn_to_enrs if ccn in providers_by_ccn}

    FLAG_COLS = {
        "pe": "PRIVATE EQUITY COMPANY - OWNER",
        "reit": "REIT - OWNER",
        "holding": "HOLDING COMPANY - OWNER",
        "mgmt": "MANAGEMENT SERVICES COMPANY - OWNER",
        "investment": "INVESTMENT FIRM - OWNER",
        "financial": "FINANCIAL INSTITUTION - OWNER",
        "consulting": "CONSULTING FIRM - OWNER",
        "staffing": "MEDICAL STAFFING COMPANY - OWNER",
        "acq": "CREATED FOR ACQUISITION - OWNER",
        "parent": "PARENT COMPANY - OWNER",
        "chain_ho": "CHAIN HOME OFFICE - OWNER",
    }

    pecos_row_stats = {
        "total_rows": len(owner_rows),
        "org_rows": 0,
        "ind_rows": 0,
        "nameless_org_rows": 0,
        "nameless_org_no_dba_rows": 0,
        "matched_provider_rows": 0,
        "flag_row_counts": {k: 0 for k in list(FLAG_COLS.keys()) + ["adp"]},
    }

    pecos_by_ccn: dict[str, dict[str, Any]] = {}

    def _init_pecos() -> dict[str, Any]:
        return {
            "owner_rows": 0,
            "org_rows": 0,
            "nameless_org_rows": 0,
            "flags": {k: False for k in list(FLAG_COLS.keys()) + ["adp"]},
            "pe_names": [],
            "reit_names": [],
            "notable_orgs": [],
            "_seen_orgs": set(),
        }

    pe_org_counter: Counter[str] = Counter()
    reit_org_counter: Counter[str] = Counter()
    nameless_roles: Counter[str] = Counter()

    for ow in owner_rows:
        eid = clean_str(ow.get("ENROLLMENT ID"))
        ccn = enr_to_ccn.get(eid)
        otype = clean_str(ow.get("TYPE - OWNER")).upper()
        org_name = clean_str(ow.get("ORGANIZATION NAME - OWNER"))
        dba_name = clean_str(ow.get("DOING BUSINESS AS NAME - OWNER"))
        role_code = clean_str(ow.get("ROLE CODE - OWNER"))
        role_text = clean_str(ow.get("ROLE TEXT - OWNER")).upper()

        is_org = otype == "O"
        is_nameless_org = is_org and not org_name
        if is_org:
            pecos_row_stats["org_rows"] += 1
        elif otype == "I":
            pecos_row_stats["ind_rows"] += 1
        if is_nameless_org:
            pecos_row_stats["nameless_org_rows"] += 1
            nameless_roles[role_text or "(blank role)"] += 1
            if not dba_name:
                pecos_row_stats["nameless_org_no_dba_rows"] += 1

        is_adp = ("ADP" in role_text) or (role_code in {"72", "73", "74", "75", "76"})
        row_flags = {k: (clean_str(ow.get(col)).upper() == "Y") for k, col in FLAG_COLS.items()}
        row_flags["adp"] = is_adp

        for fk, fv in row_flags.items():
            if fv:
                pecos_row_stats["flag_row_counts"][fk] += 1

        if not ccn or ccn not in providers_by_ccn:
            continue

        pecos_row_stats["matched_provider_rows"] += 1
        rec = pecos_by_ccn.get(ccn)
        if rec is None:
            rec = _init_pecos()
            pecos_by_ccn[ccn] = rec

        rec["owner_rows"] += 1
        if is_org:
            rec["org_rows"] += 1
        if is_nameless_org:
            rec["nameless_org_rows"] += 1

        for fk, fv in row_flags.items():
            if fv:
                rec["flags"][fk] = True

        display_org = org_name or (f"(DBA) {dba_name}" if dba_name else "")
        if display_org:
            if row_flags["pe"] and display_org not in rec["pe_names"]:
                rec["pe_names"].append(display_org)
                pe_org_counter[display_org] += 1
            if row_flags["reit"] and display_org not in rec["reit_names"]:
                rec["reit_names"].append(display_org)
                reit_org_counter[display_org] += 1
            if (
                any(row_flags[k] for k in ("pe", "reit", "holding", "mgmt", "investment", "financial"))
                and display_org not in rec["_seen_orgs"]
                and len(rec["notable_orgs"]) < 6
            ):
                rec["_seen_orgs"].add(display_org)
                tags = []
                if row_flags["pe"]:
                    tags.append("PE")
                if row_flags["reit"]:
                    tags.append("REIT")
                if row_flags["holding"]:
                    tags.append("Holding")
                if row_flags["mgmt"]:
                    tags.append("Mgmt")
                if row_flags["investment"]:
                    tags.append("Invest")
                if row_flags["financial"]:
                    tags.append("Fin")
                rec["notable_orgs"].append(f"{display_org} [{','.join(tags)}]")

    # ------------------------------------------------------------------
    # Step 4: Deduplicate & Process SNF Cost Report FY2024 (Form 2540-10)
    # ------------------------------------------------------------------
    print("[4/6] Processing SNF Cost Report FY2024 (Form 2540-10)...")
    cost_grouped: dict[str, list[tuple[int, int, date, float, dict[str, Any]]]] = defaultdict(list)
    for cr in cost_rows:
        ccn = normalize_ccn(cr.get("Provider CCN"))
        if not ccn:
            continue
        bdt = parse_date(cr.get("Fiscal Year Begin Date"))
        edt = parse_date(cr.get("Fiscal Year End Date"))
        days = (edt - bdt).days + 1 if (bdt and edt and edt >= bdt) else 0
        is_full_year = 1 if days >= 300 else 0
        tot_days = to_float(cr.get("Total Days Total")) or 0.0
        cost_grouped[ccn].append((is_full_year, days, edt or date(1900, 1, 1), tot_days, cr))

    multi_period_ccns = sum(1 for v in cost_grouped.values() if len(v) > 1)
    cost_by_ccn: dict[str, dict[str, Any]] = {}

    for ccn, entries in cost_grouped.items():
        # Prefer full-year (>=300d), then longest period, then latest FY end, then highest patient days
        entries.sort(key=lambda x: (x[0], x[1], x[2], x[3]), reverse=True)
        is_fy, period_days, edt, _, cr = entries[0]

        tot_days = to_float(cr.get("Total Days Total"))
        # Blank Total Days Title XIX treated as 0 so zero-Medicaid SNFs remain in <40% tier
        raw_xix = cr.get("Total Days Title XIX")
        xix_days = to_float(raw_xix)
        if xix_days is None and tot_days is not None and tot_days > 0:
            xix_days = 0.0
        xviii_days = to_float(cr.get("Total Days Title XVIII"))
        if xviii_days is None and tot_days is not None and tot_days > 0:
            xviii_days = 0.0

        mcaid_pct = None
        mcare_pct = None
        if tot_days and tot_days > 0 and xix_days is not None and xix_days >= 0:
            if xix_days <= tot_days * 1.02:
                mcaid_pct = round(min(100.0, xix_days / tot_days * 100.0), 1)
        if tot_days and tot_days > 0 and xviii_days is not None and xviii_days >= 0:
            if xviii_days <= tot_days * 1.02:
                mcare_pct = round(min(100.0, xviii_days / tot_days * 100.0), 1)

        net_pat_rev = to_float(cr.get("Net Patient Revenue"))
        other_inc = to_float(cr.get("Total Other Income"))
        op_exp = to_float(cr.get("Less Total Operating Expense"))
        pat_net_inc = to_float(cr.get("Net Income from service to patients"))
        net_inc = to_float(cr.get("Net Income"))

        adj_sal = to_float(cr.get("Total Salaries (adjusted)"))
        wage_core = to_float(cr.get("Wage-related Costs (core)"))
        contract_lab = to_float(cr.get("Contract Labor"))

        op_margin = None
        if net_pat_rev is not None and net_pat_rev > 0 and pat_net_inc is not None:
            op_margin = round(pat_net_inc / net_pat_rev * 100.0, 2)

        tot_rev = None
        tot_margin = None
        if net_pat_rev is not None:
            tot_rev = net_pat_rev + (other_inc or 0.0)
            if tot_rev > 0 and net_inc is not None:
                tot_margin = round(net_inc / tot_rev * 100.0, 2)

        w2_day = None
        contract_day = None
        direct_labor_day = None
        direct_labor_total = None
        if tot_days and tot_days > 0 and adj_sal is not None and adj_sal >= 0:
            w2_day = round(adj_sal / tot_days, 2)
            c_val = max(0.0, contract_lab or 0.0)
            w_val = max(0.0, wage_core or 0.0)
            direct_labor_total = adj_sal + w_val + c_val
            contract_day = round(c_val / tot_days, 2)
            direct_labor_day = round(direct_labor_total / tot_days, 2)

        rev_day = round(net_pat_rev / tot_days, 2) if (tot_days and tot_days > 0 and net_pat_rev is not None and net_pat_rev > 0) else None
        opex_day = round(op_exp / tot_days, 2) if (tot_days and tot_days > 0 and op_exp is not None and op_exp > 0) else None

        cost_by_ccn[ccn] = {
            "fy_begin": clean_str(cr.get("Fiscal Year Begin Date")),
            "fy_end": clean_str(cr.get("Fiscal Year End Date")),
            "period_days": period_days,
            "is_full_year": bool(is_fy),
            "total_days": tot_days,
            "medicaid_days": xix_days,
            "medicaid_pct": mcaid_pct,
            "medicare_pct": mcare_pct,
            "medicaid_tier": medicaid_tier(mcaid_pct),
            "net_patient_rev": net_pat_rev,
            "other_income": other_inc or 0.0,
            "total_rev": tot_rev,
            "op_expense": op_exp,
            "pat_net_income": pat_net_inc,
            "net_income": net_inc,
            "op_margin_pct": op_margin,
            "tot_margin_pct": tot_margin,
            "adj_salaries": adj_sal,
            "wage_core": wage_core or 0.0,
            "contract_labor": contract_lab or 0.0,
            "direct_labor_total": direct_labor_total,
            "w2_day": w2_day,
            "contract_day": contract_day,
            "direct_labor_day": direct_labor_day,
            "rev_day": rev_day,
            "opex_day": opex_day,
        }

    # Hospital-based SNF exclusion check
    hosp_snf_total = 0
    hosp_snf_missing_cost = 0
    freestanding_total = 0
    freestanding_matched_cost = 0
    for ccn, pr in providers_by_ccn.items():
        in_hosp = clean_str(pr.get("provider_resides_in_hospital")).upper() == "Y"
        has_cost = ccn in cost_by_ccn
        if in_hosp:
            hosp_snf_total += 1
            if not has_cost:
                hosp_snf_missing_cost += 1
        else:
            freestanding_total += 1
            if has_cost:
                freestanding_matched_cost += 1

    # ------------------------------------------------------------------
    # Step 5: Main Facility Aggregation across all 14,686 homes
    # ------------------------------------------------------------------
    print("[5/6] Aggregating national, ownership, state, chain, inspection & financial tables...")
    by_owner: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "n": 0, "stars": [], "tot_h": [], "wknd_h": [], "rn_h": [], "rn_wknd_h": [],
            "turn": [], "rn_turn": [], "fines_amt": [], "fined_n": 0, "abuse_n": 0,
            "overdue_n": 0, "pe_reit_n": 0,
        }
    )
    by_state: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "n": 0, "stars": [], "tot_h": [], "wknd_h": [], "rn_h": [], "rn_wknd_h": [],
            "turn": [], "rn_turn": [], "fines_amt": [], "fined_n": 0, "abuse_n": 0,
            "overdue_n": 0, "pe_reit_n": 0, "for_profit_n": 0, "gov_chain_n": 0,
        }
    )

    # Medicaid-controlled financial matrix: tier -> ownership -> accumulators
    tier_owner: dict[str, dict[str, dict[str, Any]]] = {
        t: defaultdict(
            lambda: {
                "n": 0, "op_margins": [], "tot_margins": [], "direct_labor_days": [],
                "w2_days": [], "contract_days": [], "rev_days": [], "opex_days": [],
                "tot_h": [], "stars": [], "sum_pat_inc": 0.0, "sum_net_pat_rev": 0.0,
                "sum_net_inc": 0.0, "sum_tot_rev": 0.0, "sum_direct_labor": 0.0, "sum_days": 0.0,
            }
        )
        for t in ("<40%", "40-60%", "60-80%", "80%+")
    }

    # Chain enrichment buckets (keyed by chain_id)
    chain_enrich: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "n": 0, "tot_h": [], "wknd_h": [], "rn_h": [], "rn_wknd_h": [],
            "overdue_n": 0, "pe_reit_n": 0, "pe_n": 0, "reit_n": 0,
            "fn23_n": 0, "fn24_n": 0, "fn25_n": 0,
            "op_margins": [], "tot_margins": [], "direct_labor_days": [],
            "gov_tx_in_n": 0,
        }
    )

    # Global accumulators
    all_tot_h, all_wknd_h, all_rn_h, all_rn_wknd = [], [], [], []
    all_turn, all_rn_turn, all_fines = [], [], []
    fined_total_n = 0
    abuse_total_n = 0
    sff_total_n = 0
    sff_cand_total_n = 0
    overdue_total_n = 0
    changed_own_12m_n = 0

    # 5-star reality & 4-star abuse icon
    five_star_n = 0
    five_star_high_turn = 0
    five_star_fined = 0
    five_star_big_wknd = 0
    five_star_overdue = 0
    five_star_any_3 = 0  # turnover>=50 OR fined>0 OR wknd_drop>=15%
    five_star_any_4 = 0  # any_3 OR overdue>2yrs
    four_star_abuse_homes: list[dict[str, Any]] = []
    five_star_uninspected_2020: list[dict[str, Any]] = []

    # Government-chain distortion
    gov_total_n = 0
    gov_in_chain_n = 0
    gov_chain_by_state: Counter[str] = Counter()
    gov_chain_tx_in_chains: Counter[str] = Counter()
    gov_chain_other_chains: Counter[str] = Counter()

    # Footnote counters
    fn_staffing: Counter[str] = Counter()
    fn_reported_staffing: Counter[str] = Counter()
    fn_turnover: Counter[str] = Counter()
    fn_overall: Counter[str] = Counter()

    # Inspection year distribution
    insp_year_dist: Counter[str] = Counter()

    # PECOS cohort comparisons
    pecos_flag_facility_counts = {k: 0 for k in list(FLAG_COLS.keys()) + ["adp", "pe_or_reit", "nameless_org"]}
    pecos_cohorts: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"n": 0, "stars": [], "tot_h": [], "wknd_h": [], "rn_h": [], "rn_wknd_h": [], "turn": [], "fined_n": 0, "fines": [], "abuse_n": 0, "op_margins": [], "direct_labor_days": []}
    )

    # Compact facilities array for frontend lookup + CSV rows
    FACILITY_COLS = [
        "ccn", "name", "city", "st", "zip", "own", "own_idx", "beds", "res",
        "chain_id", "stars", "h_stars", "s_stars", "q_stars",
        "tot_h", "wknd_h", "rn_h", "rn_wknd_h", "turn", "rn_turn", "adm_left",
        "fines_n", "fines_amt", "defic", "abuse", "sff", "overdue", "insp_dt", "hosp",
        "fn_st", "fn_rep", "fn_turn",
        "pecos_flags", "nameless_n", "owner_orgs",
        "mcaid_pct", "op_mgn", "tot_mgn", "labor_d", "w2_d", "rev_d",
        "rf_mask", "chg_own",
    ]
    own_type_list: list[str] = []
    own_type_idx_map: dict[str, int] = {}
    chain_id_name_map: dict[str, str] = {}
    facility_rows_compact: list[list[Any]] = []
    csv_export_rows: list[dict[str, Any]] = []

    for ccn, r in sorted(providers_by_ccn.items()):
        name = clean_str(r.get("provider_name"))
        city = clean_str(r.get("citytown"))
        st = clean_str(r.get("state")).upper() or "UNK"
        zcode = clean_str(r.get("zip_code"))[:5]
        own_raw = clean_str(r.get("ownership_type"))
        own = classify_owner(own_raw)
        beds = to_int(r.get("number_of_certified_beds"))
        res = to_float(r.get("average_number_of_residents_per_day"))
        chain_id = clean_str(r.get("chain_id"))
        chain_name = clean_str(r.get("chain_name"))
        in_hosp = clean_str(r.get("provider_resides_in_hospital")).upper() == "Y"
        chg_own = clean_str(r.get("provider_changed_ownership_in_last_12_months")).upper() == "Y"

        stars = to_int(r.get("overall_rating"))
        h_stars = to_int(r.get("health_inspection_rating"))
        s_stars = to_int(r.get("staffing_rating"))
        q_stars = to_int(r.get("qm_rating"))

        tot_h = to_float(r.get("reported_total_nurse_staffing_hours_per_resident_per_day"))
        wknd_h = to_float(r.get("total_number_of_nurse_staff_hours_per_resident_per_day_on_t_4a14"))
        rn_h = to_float(r.get("reported_rn_staffing_hours_per_resident_per_day"))
        rn_wknd = to_float(r.get("registered_nurse_hours_per_resident_per_day_on_the_weekend"))
        turn = to_float(r.get("total_nursing_staff_turnover"))
        rn_turn = to_float(r.get("registered_nurse_turnover"))
        adm_left = to_int(r.get("number_of_administrators_who_have_left_the_nursing_home"))

        fines_n = to_int(r.get("number_of_fines")) or 0
        fines_amt = to_float(r.get("total_amount_of_fines_in_dollars")) or 0.0
        defic = to_int(r.get("rating_cycle_1_total_number_of_health_deficiencies"))
        abuse = clean_str(r.get("abuse_icon")).upper() == "Y"
        sff_raw = clean_str(r.get("special_focus_status"))
        sff_code = "SFF" if sff_raw == "SFF" else ("Cand" if "Candidate" in sff_raw else "")
        overdue = clean_str(r.get("most_recent_health_inspection_more_than_2_years_ago")).upper() == "Y"
        insp_dt = clean_str(r.get("rating_cycle_1_standard_survey_health_date"))

        fn_st = clean_str(r.get("staffing_rating_footnote"))
        fn_rep = clean_str(r.get("reported_staffing_footnote"))
        fn_trn = clean_str(r.get("total_nursing_staff_turnover_footnote"))
        fn_ov = clean_str(r.get("overall_rating_footnote"))

        if fn_st:
            fn_staffing[fn_st] += 1
        if fn_rep:
            fn_reported_staffing[fn_rep] += 1
        if fn_trn:
            fn_turnover[fn_trn] += 1
        if fn_ov:
            fn_overall[fn_ov] += 1

        if insp_dt and len(insp_dt) >= 4:
            yr = insp_dt[:4]
            if yr.isdigit():
                insp_year_dist[yr] += 1
        else:
            insp_year_dist["Missing"] += 1

        if tot_h is not None:
            all_tot_h.append(tot_h)
        if wknd_h is not None:
            all_wknd_h.append(wknd_h)
        if rn_h is not None:
            all_rn_h.append(rn_h)
        if rn_wknd is not None:
            all_rn_wknd.append(rn_wknd)
        if turn is not None:
            all_turn.append(turn)
        if rn_turn is not None:
            all_rn_turn.append(rn_turn)
        all_fines.append(fines_amt)
        if fines_n > 0:
            fined_total_n += 1
        if abuse:
            abuse_total_n += 1
        if sff_code == "SFF":
            sff_total_n += 1
        elif sff_code == "Cand":
            sff_cand_total_n += 1
        if overdue:
            overdue_total_n += 1
        if chg_own:
            changed_own_12m_n += 1

        # PECOS record
        prec = pecos_by_ccn.get(ccn)
        pflags_list = []
        nameless_n = 0
        owner_orgs_str = ""
        is_pe_reit = False
        if prec:
            fmap = prec["flags"]
            for fk in list(FLAG_COLS.keys()) + ["adp"]:
                if fmap[fk]:
                    pecos_flag_facility_counts[fk] += 1
            if fmap["pe"] or fmap["reit"]:
                is_pe_reit = True
                pecos_flag_facility_counts["pe_or_reit"] += 1
            if prec["nameless_org_rows"] > 0:
                nameless_n = prec["nameless_org_rows"]
                pecos_flag_facility_counts["nameless_org"] += 1
            for code, key in [
                ("PE", "pe"), ("REIT", "reit"), ("ADP", "adp"), ("HOLD", "holding"),
                ("MGMT", "mgmt"), ("INV", "investment"), ("FIN", "financial"),
                ("CONS", "consulting"), ("STF", "staffing"), ("ACQ", "acq"),
            ]:
                if fmap[key]:
                    pflags_list.append(code)
            # Prioritize PE/REIT orgs first, keep concise top 2 for compact JSON
            sorted_orgs = sorted(
                prec["notable_orgs"],
                key=lambda s: (0 if ("[PE" in s or "REIT" in s) else 1, s),
            )
            owner_orgs_str = " | ".join(s[:58] for s in sorted_orgs[:2])

        # Cost report record
        crec = cost_by_ccn.get(ccn)

        # Red-flag count for 5-star & lookup filter
        fac_wknd_drop = ((tot_h - wknd_h) / tot_h) if (tot_h and wknd_h is not None and tot_h > 0) else None
        rf_turn = (turn is not None and turn >= 50.0)
        rf_fine = fines_n > 0
        rf_wknd = (fac_wknd_drop is not None and fac_wknd_drop >= 0.15)
        rf_over = overdue
        red_flags_3 = int(rf_turn) + int(rf_fine) + int(rf_wknd)
        red_flags_4 = red_flags_3 + int(rf_over)

        if stars == 5:
            five_star_n += 1
            if rf_turn:
                five_star_high_turn += 1
            if rf_fine:
                five_star_fined += 1
            if rf_wknd:
                five_star_big_wknd += 1
            if rf_over:
                five_star_overdue += 1
            if red_flags_3 > 0:
                five_star_any_3 += 1
            if red_flags_4 > 0:
                five_star_any_4 += 1
            if insp_dt and insp_dt[:4].isdigit() and int(insp_dt[:4]) <= 2020:
                five_star_uninspected_2020.append({
                    "ccn": ccn,
                    "name": name,
                    "city": city,
                    "state": st,
                    "last_inspection_date": insp_dt,
                    "ownership": own,
                    "chain": chain_name or None,
                    "total_hprd": tot_h,
                    "turnover_pct": turn,
                    "fines_dollars": round(fines_amt),
                })

        if stars == 4 and abuse:
            four_star_abuse_homes.append({
                "ccn": ccn,
                "name": name,
                "city": city,
                "state": st,
                "ownership": own,
                "chain": chain_name or None,
                "health_stars": h_stars,
                "staffing_stars": s_stars,
                "qm_stars": q_stars,
                "total_hprd": tot_h,
                "fines_dollars": round(fines_amt),
            })

        # Government-chain distortion tracking
        is_gov_chain = (own == "Government" and bool(chain_id))
        is_tx_in_gov_chain = is_gov_chain and st in ("TX", "IN")
        if own == "Government":
            gov_total_n += 1
            if chain_id:
                gov_in_chain_n += 1
                gov_chain_by_state[st] += 1
                if st in ("TX", "IN"):
                    gov_chain_tx_in_chains[f"{chain_name} ({st})"] += 1
                else:
                    gov_chain_other_chains[f"{chain_name} ({st})"] += 1

        # Ownership & State buckets
        own_buckets = [by_owner[own]]
        if own == "Government":
            own_buckets.append(by_owner["Government (TX/IN Chain Leases)" if is_tx_in_gov_chain else "Government (Excl. TX/IN Chains)"])

        for b in own_buckets + [by_state[st]]:
            b["n"] += 1
            if stars is not None:
                b["stars"].append(float(stars))
            if tot_h is not None:
                b["tot_h"].append(tot_h)
            if wknd_h is not None:
                b["wknd_h"].append(wknd_h)
            if rn_h is not None:
                b["rn_h"].append(rn_h)
            if rn_wknd is not None:
                b["rn_wknd_h"].append(rn_wknd)
            if turn is not None:
                b["turn"].append(turn)
            if rn_turn is not None:
                b["rn_turn"].append(rn_turn)
            b["fines_amt"].append(fines_amt)
            if fines_n > 0:
                b["fined_n"] += 1
            if abuse:
                b["abuse_n"] += 1
            if overdue:
                b["overdue_n"] += 1
            if is_pe_reit:
                b["pe_reit_n"] += 1

        if own == "For-Profit":
            by_state[st]["for_profit_n"] += 1
        if is_gov_chain:
            by_state[st]["gov_chain_n"] += 1

        # PECOS cohort comparison (For-Profit PE/REIT vs For-Profit Holding/Mgmt vs For-Profit Other vs Non-Profit)
        if own == "Non-Profit":
            p_coh = "Non-Profit"
        elif own == "For-Profit" and is_pe_reit:
            p_coh = "For-Profit (PE/REIT Disclosed)"
        elif own == "For-Profit" and prec and (prec["flags"]["holding"] or prec["flags"]["mgmt"] or prec["flags"]["investment"]):
            p_coh = "For-Profit (Holding/Mgmt/Invest Only)"
        elif own == "For-Profit":
            p_coh = "For-Profit (No PE/REIT/Holding Flag)"
        else:
            p_coh = "Government"

        cb = pecos_cohorts[p_coh]
        cb["n"] += 1
        if stars is not None:
            cb["stars"].append(float(stars))
        if tot_h is not None:
            cb["tot_h"].append(tot_h)
        if wknd_h is not None:
            cb["wknd_h"].append(wknd_h)
        if rn_h is not None:
            cb["rn_h"].append(rn_h)
        if rn_wknd is not None:
            cb["rn_wknd_h"].append(rn_wknd)
        if turn is not None:
            cb["turn"].append(turn)
        if fines_n > 0:
            cb["fined_n"] += 1
        cb["fines"].append(fines_amt)
        if abuse:
            cb["abuse_n"] += 1
        if crec and crec["op_margin_pct"] is not None:
            cb["op_margins"].append(crec["op_margin_pct"])
        if crec and crec["direct_labor_day"] is not None:
            cb["direct_labor_days"].append(crec["direct_labor_day"])

        # Medicaid-controlled cost report matrix
        if crec and crec["medicaid_tier"] and own in ("For-Profit", "Non-Profit", "Government"):
            tb = tier_owner[crec["medicaid_tier"]][own]
            tb["n"] += 1
            if crec["op_margin_pct"] is not None:
                tb["op_margins"].append(crec["op_margin_pct"])
            if crec["tot_margin_pct"] is not None:
                tb["tot_margins"].append(crec["tot_margin_pct"])
            if crec["direct_labor_day"] is not None:
                tb["direct_labor_days"].append(crec["direct_labor_day"])
            if crec["w2_day"] is not None:
                tb["w2_days"].append(crec["w2_day"])
            if crec["contract_day"] is not None:
                tb["contract_days"].append(crec["contract_day"])
            if crec["rev_day"] is not None:
                tb["rev_days"].append(crec["rev_day"])
            if crec["opex_day"] is not None:
                tb["opex_days"].append(crec["opex_day"])
            if tot_h is not None:
                tb["tot_h"].append(tot_h)
            if stars is not None:
                tb["stars"].append(float(stars))
            if crec["net_patient_rev"] is not None and crec["net_patient_rev"] > 0 and crec["pat_net_income"] is not None:
                tb["sum_pat_inc"] += crec["pat_net_income"]
                tb["sum_net_pat_rev"] += crec["net_patient_rev"]
            if crec["total_rev"] is not None and crec["total_rev"] > 0 and crec["net_income"] is not None:
                tb["sum_net_inc"] += crec["net_income"]
                tb["sum_tot_rev"] += crec["total_rev"]
            if crec["direct_labor_total"] is not None and crec["total_days"]:
                tb["sum_direct_labor"] += crec["direct_labor_total"]
                tb["sum_days"] += crec["total_days"]

        # Chain enrichment
        if chain_id:
            ce = chain_enrich[chain_id]
            ce["n"] += 1
            if tot_h is not None:
                ce["tot_h"].append(tot_h)
            if wknd_h is not None:
                ce["wknd_h"].append(wknd_h)
            if rn_h is not None:
                ce["rn_h"].append(rn_h)
            if rn_wknd is not None:
                ce["rn_wknd_h"].append(rn_wknd)
            if overdue:
                ce["overdue_n"] += 1
            if is_pe_reit:
                ce["pe_reit_n"] += 1
            if prec and prec["flags"]["pe"]:
                ce["pe_n"] += 1
            if prec and prec["flags"]["reit"]:
                ce["reit_n"] += 1
            if fn_rep == "23" or fn_st == "23":
                ce["fn23_n"] += 1
            if fn_st == "24" or fn_rep == "24":
                ce["fn24_n"] += 1
            if fn_rep == "25" or fn_st == "25":
                ce["fn25_n"] += 1
            if crec and crec["op_margin_pct"] is not None:
                ce["op_margins"].append(crec["op_margin_pct"])
            if crec and crec["tot_margin_pct"] is not None:
                ce["tot_margins"].append(crec["tot_margin_pct"])
            if crec and crec["direct_labor_day"] is not None:
                ce["direct_labor_days"].append(crec["direct_labor_day"])
            if is_tx_in_gov_chain:
                ce["gov_tx_in_n"] += 1

        # Compact facility row
        own_code = "FP" if own == "For-Profit" else ("NP" if own == "Non-Profit" else ("GV" if own == "Government" else "OT"))
        if own_raw not in own_type_idx_map:
            own_type_idx_map[own_raw] = len(own_type_list)
            own_type_list.append(own_raw)
        if chain_id and chain_name and chain_id not in chain_id_name_map:
            chain_id_name_map[chain_id] = chain_name
        rf_mask = (1 if rf_turn else 0) | (2 if rf_fine else 0) | (4 if rf_wknd else 0) | (8 if rf_over else 0)
        facility_rows_compact.append([
            ccn,
            name,
            city,
            st,
            zcode,
            own_code,
            own_type_idx_map[own_raw],
            beds,
            round(res, 1) if res is not None else None,
            chain_id or None,
            stars,
            h_stars,
            s_stars,
            q_stars,
            round(tot_h, 2) if tot_h is not None else None,
            round(wknd_h, 2) if wknd_h is not None else None,
            round(rn_h, 2) if rn_h is not None else None,
            round(rn_wknd, 2) if rn_wknd is not None else None,
            round(turn, 1) if turn is not None else None,
            round(rn_turn, 1) if rn_turn is not None else None,
            adm_left,
            fines_n,
            round(fines_amt),
            defic,
            1 if abuse else 0,
            sff_code or None,
            1 if overdue else 0,
            insp_dt or None,
            1 if in_hosp else 0,
            fn_st or None,
            fn_rep or None,
            fn_trn or None,
            ",".join(pflags_list) if pflags_list else None,
            nameless_n if nameless_n else None,
            owner_orgs_str or None,
            crec["medicaid_pct"] if crec else None,
            crec["op_margin_pct"] if crec else None,
            crec["tot_margin_pct"] if crec else None,
            crec["direct_labor_day"] if crec else None,
            crec["w2_day"] if crec else None,
            crec["rev_day"] if crec else None,
            rf_mask,
            1 if chg_own else 0,
        ])

        if args.export_csv:
            csv_export_rows.append({
                "ccn": ccn,
                "provider_name": name,
                "city": city,
                "state": st,
                "zip": zcode,
                "ownership_group": own,
                "ownership_type": own_raw,
                "hospital_based": "Y" if in_hosp else "N",
                "certified_beds": beds,
                "avg_residents_per_day": res,
                "chain_id": chain_id,
                "chain_name": chain_name,
                "overall_rating": stars,
                "health_inspection_rating": h_stars,
                "staffing_rating": s_stars,
                "qm_rating": q_stars,
                "total_nurse_hprd_7day": tot_h,
                "weekend_nurse_hprd": wknd_h,
                "rn_hprd_7day": rn_h,
                "weekend_rn_hprd": rn_wknd,
                "total_nursing_turnover_pct": turn,
                "rn_turnover_pct": rn_turn,
                "administrators_left": adm_left,
                "fines_count": fines_n,
                "fines_dollars": round(fines_amt, 2),
                "cycle1_health_deficiencies": defic,
                "abuse_icon": "Y" if abuse else "N",
                "special_focus_status": sff_raw,
                "inspection_overdue_2yr": "Y" if overdue else "N",
                "last_standard_survey_date": insp_dt,
                "changed_ownership_12m": "Y" if chg_own else "N",
                "staffing_rating_footnote": fn_st,
                "reported_staffing_footnote": fn_rep,
                "turnover_footnote": fn_trn,
                "pecos_flags": ",".join(pflags_list),
                "pecos_nameless_org_rows": nameless_n,
                "pecos_notable_owners": owner_orgs_str,
                "fy2024_cost_report_matched": "Y" if crec else "N",
                "fy2024_period_days": crec["period_days"] if crec else "",
                "fy2024_medicaid_pct": crec["medicaid_pct"] if crec else "",
                "fy2024_medicare_pct": crec["medicare_pct"] if crec else "",
                "fy2024_net_patient_revenue": crec["net_patient_rev"] if crec else "",
                "fy2024_operating_expense": crec["op_expense"] if crec else "",
                "fy2024_patient_operating_margin_pct": crec["op_margin_pct"] if crec else "",
                "fy2024_total_net_margin_pct": crec["tot_margin_pct"] if crec else "",
                "fy2024_direct_labor_per_day": crec["direct_labor_day"] if crec else "",
                "fy2024_w2_salaries_per_day": crec["w2_day"] if crec else "",
                "fy2024_contract_labor_per_day": crec["contract_day"] if crec else "",
                "fy2024_net_patient_rev_per_day": crec["rev_day"] if crec else "",
            })

    # ------------------------------------------------------------------
    # Step 6: Process 612 Chains (filtering out blank-ID National row)
    # ------------------------------------------------------------------
    national_chain_row = None
    chains_out: list[dict[str, Any]] = []
    for ch in chain_rows:
        cid = clean_str(ch.get("Chain ID"))
        cname = clean_str(ch.get("Chain"))
        if not cid and cname.lower() == "national":
            national_chain_row = {
                "facilities": to_int(ch.get("Number of facilities")),
                "avg_stars": to_float(ch.get("Average overall 5-star rating")),
                "avg_total_hprd": to_float(ch.get("Average total nurse hours per resident day")),
                "avg_wknd_hprd": to_float(ch.get("Average total weekend nurse hours per resident day")),
                "avg_rn_hprd": to_float(ch.get("Average total Registered Nurse hours per resident day")),
                "avg_turnover_pct": to_float(ch.get("Average total nursing staff turnover percentage")),
                "abuse_pct": to_float(ch.get("Percentage of facilities with an abuse icon")),
                "long_stay_antipsychotic_pct": to_float(ch.get("Average percentage of long-stay residents who received an antipsychotic medication")),
            }
            continue
        if not cid:
            continue

        ce = chain_enrich.get(cid)
        n_fac = to_int(ch.get("Number of facilities")) or (ce["n"] if ce else 0)
        tot_h = to_float(ch.get("Average total nurse hours per resident day"))
        wknd_h = to_float(ch.get("Average total weekend nurse hours per resident day"))
        rn_h = to_float(ch.get("Average total Registered Nurse hours per resident day"))

        # Compute exact ratio-of-means drops from joined provider rows (more precise than rounded chain means)
        ce_tot = statistics.mean(ce["tot_h"]) if (ce and ce["tot_h"]) else tot_h
        ce_wknd = statistics.mean(ce["wknd_h"]) if (ce and ce["wknd_h"]) else wknd_h
        ce_rn = statistics.mean(ce["rn_h"]) if (ce and ce["rn_h"]) else rn_h
        ce_rn_wknd = statistics.mean(ce["rn_wknd_h"]) if (ce and ce["rn_wknd_h"]) else None

        wknd_drop = ratio_drop_pct(ce_tot, ce_wknd)
        rn_wknd_drop = ratio_drop_pct(ce_rn, ce_rn_wknd)

        fn23 = ce["fn23_n"] if ce else 0
        fn24 = ce["fn24_n"] if ce else 0
        fn25 = ce["fn25_n"] if ce else 0
        ap_pct = to_float(ch.get("Average percentage of long-stay residents who received an antipsychotic medication"))

        # Data-driven caveats
        caveats = []
        if ce and ce["n"] > 0 and fn23 >= max(3, int(0.4 * ce["n"])):
            caveats.append(f"PBJ non-submission (Footnote 23) at {fn23}/{ce['n']} homes")
        if ce and ce["n"] > 0 and fn25 >= max(3, int(0.4 * ce["n"])):
            caveats.append(f"CMS could not validate PBJ (Footnote 25) at {fn25}/{ce['n']} homes")
        if ap_pct is not None and ap_pct >= 35.0:
            caveats.append(f"High antipsychotic rate ({ap_pct}%) — verify behavioral/psychiatric case-mix")
        if ce and ce["gov_tx_in_n"] >= 3:
            caveats.append(f"Operates {ce['gov_tx_in_n']} TX/IN county or hospital-district leased homes")

        chains_out.append({
            "id": cid,
            "name": cname,
            "n": n_fac,
            "states": to_int(ch.get("Number of states and territories with operations")),
            "sff": to_int(ch.get("Number of Special Focus Facilities (SFF)")) or 0,
            "sff_cand": to_int(ch.get("Number of SFF candidates")) or 0,
            "abuse_n": to_int(ch.get("Number of facilities with an abuse icon")) or 0,
            "abuse_pct": to_float(ch.get("Percentage of facilities with an abuse icon")),
            "fp_pct": to_float(ch.get("Percent of facilities classified as for-profit")),
            "np_pct": to_float(ch.get("Percent of facilities classified as non-profit")),
            "gov_pct": to_float(ch.get("Percent of facilities classified as government-owned")),
            "stars": to_float(ch.get("Average overall 5-star rating")),
            "h_stars": to_float(ch.get("Average health inspection rating")),
            "s_stars": to_float(ch.get("Average staffing rating")),
            "q_stars": to_float(ch.get("Average quality rating")),
            "tot_h": round(tot_h, 2) if tot_h is not None else None,
            "wknd_h": round(wknd_h, 2) if wknd_h is not None else None,
            "wknd_drop": wknd_drop,
            "rn_h": round(rn_h, 2) if rn_h is not None else None,
            "rn_wknd_h": round(ce_rn_wknd, 2) if ce_rn_wknd is not None else None,
            "rn_wknd_drop": rn_wknd_drop,
            "turn": to_float(ch.get("Average total nursing staff turnover percentage")),
            "rn_turn": to_float(ch.get("Average Registered Nurse turnover percentage")),
            "adm_left": to_float(ch.get("Average number of administrators who have left the nursing home")),
            "fines_n": to_int(ch.get("Total number of fines")) or 0,
            "fines_tot": round(to_float(ch.get("Total amount of fines in dollars")) or 0.0),
            "avg_fine": round(to_float(ch.get("Average amount of fines in dollars")) or 0.0),
            "ap_pct": ap_pct,
            "rehos_pct": to_float(ch.get("Average percentage of short-stay residents who were re-hospitalized after a nursing home admission")),
            "overdue_pct": round(ce["overdue_n"] / ce["n"] * 100.0, 1) if (ce and ce["n"] > 0) else None,
            "pe_reit_n": ce["pe_reit_n"] if ce else 0,
            "fn23_n": fn23,
            "fn24_n": fn24,
            "fn25_n": fn25,
            "med_op_mgn": med_or_none(ce["op_margins"], 1) if ce else None,
            "med_labor_d": med_or_none(ce["direct_labor_days"], 0) if ce else None,
            "gov_tx_in_n": ce["gov_tx_in_n"] if ce else 0,
            "caveat": "; ".join(caveats) if caveats else None,
        })

    chains_out.sort(key=lambda x: (-x["n"], x["name"]))

    # ------------------------------------------------------------------
    # Build summary structures
    # ------------------------------------------------------------------
    nat_tot_raw = statistics.mean(all_tot_h) if all_tot_h else None
    nat_wknd_raw = statistics.mean(all_wknd_h) if all_wknd_h else None
    nat_rn_raw = statistics.mean(all_rn_h) if all_rn_h else None
    nat_rn_wknd_raw = statistics.mean(all_rn_wknd) if all_rn_wknd else None

    nat_imp_wkday_raw = implied_wkday_raw(nat_tot_raw, nat_wknd_raw)
    nat_imp_rn_wkday_raw = implied_wkday_raw(nat_rn_raw, nat_rn_wknd_raw)

    def _build_owner_row(label: str, b: dict[str, Any]) -> dict[str, Any]:
        th_raw = statistics.mean(b["tot_h"]) if b["tot_h"] else None
        wh_raw = statistics.mean(b["wknd_h"]) if b["wknd_h"] else None
        rh_raw = statistics.mean(b["rn_h"]) if b["rn_h"] else None
        rwh_raw = statistics.mean(b["rn_wknd_h"]) if b["rn_wknd_h"] else None
        imp_w = implied_wkday_raw(th_raw, wh_raw)
        imp_rw = implied_wkday_raw(rh_raw, rwh_raw)
        return {
            "ownership": label,
            "facilities": b["n"],
            "share_pct": round(b["n"] / total_facilities * 100.0, 1),
            "avg_stars": mean_or_none(b["stars"]),
            "avg_total_hprd": round(th_raw, 2) if th_raw is not None else None,
            "avg_weekend_hprd": round(wh_raw, 2) if wh_raw is not None else None,
            "weekend_drop_pct": ratio_drop_pct(th_raw, wh_raw),
            "implied_weekday_hprd": round(imp_w, 2) if imp_w is not None else None,
            "implied_weekday_drop_pct": ratio_drop_pct(imp_w, wh_raw),
            "avg_rn_hprd": round(rh_raw, 2) if rh_raw is not None else None,
            "avg_rn_weekend_hprd": round(rwh_raw, 2) if rwh_raw is not None else None,
            "rn_weekend_drop_pct": ratio_drop_pct(rh_raw, rwh_raw),
            "implied_rn_weekday_drop_pct": ratio_drop_pct(imp_rw, rwh_raw),
            "avg_turnover_pct": mean_or_none(b["turn"], 1),
            "avg_rn_turnover_pct": mean_or_none(b["rn_turn"], 1),
            "pct_fined": round(b["fined_n"] / b["n"] * 100.0, 1) if b["n"] else 0.0,
            "avg_fine_dollars": round(statistics.mean(b["fines_amt"])) if b["fines_amt"] else 0,
            "pct_abuse_icon": round(b["abuse_n"] / b["n"] * 100.0, 1) if b["n"] else 0.0,
            "pct_overdue_2yr": round(b["overdue_n"] / b["n"] * 100.0, 1) if b["n"] else 0.0,
            "pct_pe_reit": round(b["pe_reit_n"] / b["n"] * 100.0, 1) if b["n"] else 0.0,
        }

    owner_summary = [_build_owner_row(k, by_owner[k]) for k in ("Non-Profit", "Government", "For-Profit") if by_owner[k]["n"] > 0]
    gov_split = [
        _build_owner_row(k, by_owner[k])
        for k in ("Government (Excl. TX/IN Chains)", "Government (TX/IN Chain Leases)")
        if by_owner[k]["n"] > 0
    ]

    # State summary (all 50 states + DC)
    state_summary = []
    for st in sorted(US_STATES_DC):
        b = by_state.get(st)
        if not b or b["n"] == 0:
            continue
        th_raw = statistics.mean(b["tot_h"]) if b["tot_h"] else None
        wh_raw = statistics.mean(b["wknd_h"]) if b["wknd_h"] else None
        rh_raw = statistics.mean(b["rn_h"]) if b["rn_h"] else None
        rwh_raw = statistics.mean(b["rn_wknd_h"]) if b["rn_wknd_h"] else None
        state_summary.append({
            "state": st,
            "facilities": b["n"],
            "avg_stars": mean_or_none(b["stars"]),
            "avg_total_hprd": round(th_raw, 2) if th_raw is not None else None,
            "avg_weekend_hprd": round(wh_raw, 2) if wh_raw is not None else None,
            "weekend_drop_pct": ratio_drop_pct(th_raw, wh_raw),
            "avg_rn_hprd": round(rh_raw, 2) if rh_raw is not None else None,
            "avg_rn_weekend_hprd": round(rwh_raw, 2) if rwh_raw is not None else None,
            "rn_weekend_drop_pct": ratio_drop_pct(rh_raw, rwh_raw),
            "avg_turnover_pct": mean_or_none(b["turn"], 1),
            "avg_rn_turnover_pct": mean_or_none(b["rn_turn"], 1),
            "pct_fined": round(b["fined_n"] / b["n"] * 100.0, 1),
            "avg_fine_dollars": round(statistics.mean(b["fines_amt"])) if b["fines_amt"] else 0,
            "pct_abuse_icon": round(b["abuse_n"] / b["n"] * 100.0, 1),
            "overdue_2yr_n": b["overdue_n"],
            "pct_overdue_2yr": round(b["overdue_n"] / b["n"] * 100.0, 1),
            "pct_for_profit": round(b["for_profit_n"] / b["n"] * 100.0, 1),
            "pct_pe_reit": round(b["pe_reit_n"] / b["n"] * 100.0, 1),
            "gov_chain_n": b["gov_chain_n"],
        })
    state_summary.sort(key=lambda x: x["avg_total_hprd"] or 0, reverse=True)

    # Medicaid-controlled cost report matrix
    cost_matrix = []
    for tier in ("<40%", "40-60%", "60-80%", "80%+"):
        row_entry: dict[str, Any] = {"medicaid_tier": tier, "by_ownership": {}}
        for own in ("For-Profit", "Non-Profit", "Government"):
            tb = tier_owner[tier][own]
            row_entry["by_ownership"][own] = {
                "facilities": tb["n"],
                "median_op_margin_pct": med_or_none(tb["op_margins"], 2),
                "agg_op_margin_pct": round(tb["sum_pat_inc"] / tb["sum_net_pat_rev"] * 100.0, 2) if tb["sum_net_pat_rev"] > 0 else None,
                "median_tot_margin_pct": med_or_none(tb["tot_margins"], 2),
                "agg_tot_margin_pct": round(tb["sum_net_inc"] / tb["sum_tot_rev"] * 100.0, 2) if tb["sum_tot_rev"] > 0 else None,
                "median_direct_labor_day": med_or_none(tb["direct_labor_days"], 2),
                "agg_direct_labor_day": round(tb["sum_direct_labor"] / tb["sum_days"], 2) if tb["sum_days"] > 0 else None,
                "median_w2_day": med_or_none(tb["w2_days"], 2),
                "median_contract_day": med_or_none(tb["contract_days"], 2),
                "median_rev_day": med_or_none(tb["rev_days"], 2),
                "median_opex_day": med_or_none(tb["opex_days"], 2),
                "avg_total_hprd": mean_or_none(tb["tot_h"], 2),
                "avg_stars": mean_or_none(tb["stars"], 2),
            }
        cost_matrix.append(row_entry)

    # Overall Cost Report Cohort Stats
    all_matched_costs = [cost_by_ccn[c] for c in providers_by_ccn if c in cost_by_ccn]
    all_op_m = [x["op_margin_pct"] for x in all_matched_costs if x["op_margin_pct"] is not None]
    all_tot_m = [x["tot_margin_pct"] for x in all_matched_costs if x["tot_margin_pct"] is not None]
    all_dl_d = [x["direct_labor_day"] for x in all_matched_costs if x["direct_labor_day"] is not None]
    all_w2_d = [x["w2_day"] for x in all_matched_costs if x["w2_day"] is not None]
    all_ctr_d = [x["contract_day"] for x in all_matched_costs if x["contract_day"] is not None]

    # PECOS cohort table
    pecos_cohort_rows = []
    for label in (
        "Non-Profit",
        "For-Profit (PE/REIT Disclosed)",
        "For-Profit (Holding/Mgmt/Invest Only)",
        "For-Profit (No PE/REIT/Holding Flag)",
        "Government",
    ):
        cb = pecos_cohorts[label]
        if cb["n"] == 0:
            continue
        th = statistics.mean(cb["tot_h"]) if cb["tot_h"] else None
        wh = statistics.mean(cb["wknd_h"]) if cb["wknd_h"] else None
        rh = statistics.mean(cb["rn_h"]) if cb["rn_h"] else None
        rwh = statistics.mean(cb["rn_wknd_h"]) if cb["rn_wknd_h"] else None
        pecos_cohort_rows.append({
            "cohort": label,
            "facilities": cb["n"],
            "avg_stars": mean_or_none(cb["stars"]),
            "avg_total_hprd": round(th, 2) if th is not None else None,
            "weekend_drop_pct": ratio_drop_pct(th, wh),
            "rn_weekend_drop_pct": ratio_drop_pct(rh, rwh),
            "avg_turnover_pct": mean_or_none(cb["turn"], 1),
            "pct_fined": round(cb["fined_n"] / cb["n"] * 100.0, 1),
            "avg_fine_dollars": round(statistics.mean(cb["fines"])) if cb["fines"] else 0,
            "pct_abuse_icon": round(cb["abuse_n"] / cb["n"] * 100.0, 1),
            "median_op_margin_pct": med_or_none(cb["op_margins"], 2),
            "median_direct_labor_day": med_or_none(cb["direct_labor_days"], 2),
        })

    # Top overdue states
    top_overdue_states = sorted(state_summary, key=lambda x: (-x["pct_overdue_2yr"], -x["overdue_2yr_n"]))[:12]

    # Chain highlights
    chains_20plus = [c for c in chains_out if c["n"] >= 20]
    chains_50plus = [c for c in chains_out if c["n"] >= 50]
    total_chain_homes = sum(1 for r in providers_by_ccn.values() if clean_str(r.get("chain_id")))

    summary = {
        "metadata": {
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "provider_processing_date": processing_date,
            "total_facilities": total_facilities,
            "alphanumeric_ccn_count": alphanumeric_ccns,
            "endpoints": {
                "provider_info": {
                    "id": "4pq5-n9py",
                    "rows": len(provider_rows),
                    "url": PROVIDER_BASE,
                },
                "chains": {**endpoints["chains"], "rows": len(chain_rows), "chains_excluding_national": len(chains_out)},
                "enrollments": {**endpoints["enrollments"], "rows": len(enrollment_rows), "matched_ccns": len(matched_enrollment_ccns)},
                "owners": {**endpoints["owners"], "rows": len(owner_rows), "matched_ccns": len(pecos_by_ccn)},
                "cost_report": {**endpoints["cost_report"], "rows": len(cost_rows), "unique_ccns": len(cost_by_ccn), "matched_ccns": len(all_matched_costs)},
            },
        },
        "national": {
            "avg_total_hprd": round(nat_tot_raw, 2) if nat_tot_raw is not None else None,
            "avg_weekend_hprd": round(nat_wknd_raw, 2) if nat_wknd_raw is not None else None,
            "weekend_drop_pct": ratio_drop_pct(nat_tot_raw, nat_wknd_raw),
            "implied_weekday_hprd": round(nat_imp_wkday_raw, 2) if nat_imp_wkday_raw is not None else None,
            "implied_weekday_drop_pct": ratio_drop_pct(nat_imp_wkday_raw, nat_wknd_raw),
            "avg_rn_hprd": round(nat_rn_raw, 2) if nat_rn_raw is not None else None,
            "avg_rn_weekend_hprd": round(nat_rn_wknd_raw, 2) if nat_rn_wknd_raw is not None else None,
            "rn_weekend_drop_pct": ratio_drop_pct(nat_rn_raw, nat_rn_wknd_raw),
            "implied_rn_weekday_hprd": round(nat_imp_rn_wkday_raw, 2) if nat_imp_rn_wkday_raw is not None else None,
            "implied_rn_weekday_drop_pct": ratio_drop_pct(nat_imp_rn_wkday_raw, nat_rn_wknd_raw),
            "avg_turnover_pct": mean_or_none(all_turn, 1),
            "median_turnover_pct": med_or_none(all_turn, 1),
            "avg_rn_turnover_pct": mean_or_none(all_rn_turn, 1),
            "pct_fined": round(fined_total_n / total_facilities * 100.0, 1),
            "fined_count": fined_total_n,
            "total_fines_millions": round(sum(all_fines) / 1_000_000.0, 1),
            "pct_abuse_icon": round(abuse_total_n / total_facilities * 100.0, 1),
            "abuse_count": abuse_total_n,
            "sff_count": sff_total_n,
            "sff_candidate_count": sff_cand_total_n,
            "overdue_2yr_count": overdue_total_n,
            "pct_overdue_2yr": round(overdue_total_n / total_facilities * 100.0, 1),
            "changed_ownership_12m_count": changed_own_12m_n,
            "chain_affiliated_count": total_chain_homes,
            "chain_affiliated_pct": round(total_chain_homes / total_facilities * 100.0, 1),
            "national_chain_benchmark": national_chain_row,
        },
        "five_star_reality": {
            "five_star_count": five_star_n,
            "share_of_all_pct": round(five_star_n / total_facilities * 100.0, 1),
            "pct_high_turnover_50plus": round(five_star_high_turn / five_star_n * 100.0, 1) if five_star_n else 0.0,
            "pct_with_fines": round(five_star_fined / five_star_n * 100.0, 1) if five_star_n else 0.0,
            "pct_big_weekend_drop_15plus": round(five_star_big_wknd / five_star_n * 100.0, 1) if five_star_n else 0.0,
            "pct_overdue_2yr": round(five_star_overdue / five_star_n * 100.0, 1) if five_star_n else 0.0,
            "pct_any_red_flag_3": round(five_star_any_3 / five_star_n * 100.0, 1) if five_star_n else 0.0,
            "count_any_red_flag_3": five_star_any_3,
            "pct_any_red_flag_4": round(five_star_any_4 / five_star_n * 100.0, 1) if five_star_n else 0.0,
            "count_any_red_flag_4": five_star_any_4,
            "four_star_abuse_count": len(four_star_abuse_homes),
            "four_star_abuse_homes": sorted(four_star_abuse_homes, key=lambda x: (-x["fines_dollars"], x["state"], x["name"])),
        },
        "by_ownership": owner_summary,
        "gov_chain_distortion": {
            "gov_total": gov_total_n,
            "gov_in_chain": gov_in_chain_n,
            "gov_in_chain_pct": round(gov_in_chain_n / gov_total_n * 100.0, 1) if gov_total_n else 0.0,
            "tx_gov_chain_count": gov_chain_by_state.get("TX", 0),
            "in_gov_chain_count": gov_chain_by_state.get("IN", 0),
            "tx_in_share_of_gov_chains_pct": round((gov_chain_by_state.get("TX", 0) + gov_chain_by_state.get("IN", 0)) / gov_in_chain_n * 100.0, 1) if gov_in_chain_n else 0.0,
            "by_state_top10": [{"state": st, "count": cnt} for st, cnt in gov_chain_by_state.most_common(10)],
            "top_tx_in_chains": [{"chain": ch, "count": cnt} for ch, cnt in gov_chain_tx_in_chains.most_common(10)],
            "top_other_public_chains": [{"chain": ch, "count": cnt} for ch, cnt in gov_chain_other_chains.most_common(8)],
            "ownership_split": gov_split,
        },
        "pecos_audit": {
            "total_owner_rows": pecos_row_stats["total_rows"],
            "org_owner_rows": pecos_row_stats["org_rows"],
            "ind_owner_rows": pecos_row_stats["ind_rows"],
            "matched_enrollment_ccns": len(matched_enrollment_ccns),
            "matched_owner_ccns": len(pecos_by_ccn),
            "nameless_org_rows": pecos_row_stats["nameless_org_rows"],
            "nameless_org_no_dba_rows": pecos_row_stats["nameless_org_no_dba_rows"],
            "nameless_org_pct_of_org_rows": round(pecos_row_stats["nameless_org_rows"] / pecos_row_stats["org_rows"] * 100.0, 1) if pecos_row_stats["org_rows"] else 0.0,
            "nameless_org_facilities": pecos_flag_facility_counts["nameless_org"],
            "nameless_top_roles": [{"role": r, "rows": c} for r, c in nameless_roles.most_common(6)],
            "flag_rows": pecos_row_stats["flag_row_counts"],
            "flag_facilities": pecos_flag_facility_counts,
            "flag_pct_matched": {
                k: round(v / len(pecos_by_ccn) * 100.0, 1) if pecos_by_ccn else 0.0
                for k, v in pecos_flag_facility_counts.items()
            },
            "top_pe_orgs": [{"name": nm, "facilities": cnt} for nm, cnt in pe_org_counter.most_common(8)],
            "top_reit_orgs": [{"name": nm, "facilities": cnt} for nm, cnt in reit_org_counter.most_common(8)],
            "cohorts": pecos_cohort_rows,
        },
        "cost_report_analysis": {
            "total_raw_rows": len(cost_rows),
            "unique_ccns_in_file": len(cost_by_ccn),
            "multi_period_ccns_deduplicated": multi_period_ccns,
            "matched_to_provider_info": len(all_matched_costs),
            "match_rate_pct": round(len(all_matched_costs) / total_facilities * 100.0, 1),
            "hospital_based_total": hosp_snf_total,
            "hospital_based_missing_2540_10": hosp_snf_missing_cost,
            "hospital_based_exclusion_pct": round(hosp_snf_missing_cost / hosp_snf_total * 100.0, 1) if hosp_snf_total else 0.0,
            "freestanding_match_pct": round(freestanding_matched_cost / freestanding_total * 100.0, 1) if freestanding_total else 0.0,
            "overall_median_op_margin_pct": med_or_none(all_op_m, 2),
            "overall_median_tot_margin_pct": med_or_none(all_tot_m, 2),
            "overall_median_direct_labor_day": med_or_none(all_dl_d, 2),
            "overall_median_w2_day": med_or_none(all_w2_d, 2),
            "overall_median_contract_day": med_or_none(all_ctr_d, 2),
            "medicaid_matrix": cost_matrix,
        },
        "inspection_backlog": {
            "national_overdue_2yr_count": overdue_total_n,
            "national_overdue_2yr_pct": round(overdue_total_n / total_facilities * 100.0, 1),
            "top_overdue_states": [
                {
                    "state": s["state"],
                    "facilities": s["facilities"],
                    "overdue_n": s["overdue_2yr_n"],
                    "overdue_pct": s["pct_overdue_2yr"],
                }
                for s in top_overdue_states
            ],
            "last_inspection_year_distribution": dict(sorted(insp_year_dist.items())),
            "five_star_uninspected_since_2020": sorted(five_star_uninspected_2020, key=lambda x: (x["last_inspection_date"], x["ccn"])),
        },
        "footnote_audit": {
            "definitions": CMS_FOOTNOTES,
            "staffing_rating_footnotes": dict(fn_staffing.most_common()),
            "reported_staffing_footnotes": dict(fn_reported_staffing.most_common()),
            "turnover_footnotes": dict(fn_turnover.most_common()),
            "overall_rating_footnotes": dict(fn_overall.most_common()),
        },
        "chain_highlights": {
            "total_chains": len(chains_out),
            "chains_20plus": len(chains_20plus),
            "chains_50plus": len(chains_50plus),
            "top_stars_20plus": sorted([c for c in chains_20plus if c["stars"] is not None], key=lambda x: (-x["stars"], -x["n"]))[:8],
            "bottom_stars_20plus": sorted([c for c in chains_20plus if c["stars"] is not None], key=lambda x: (x["stars"], -x["n"]))[:8],
            "top_fines_chains": sorted(chains_out, key=lambda x: -x["fines_tot"])[:8],
            "highest_abuse_20plus": sorted([c for c in chains_20plus if c["abuse_pct"] is not None], key=lambda x: (-x["abuse_pct"], -x["n"]))[:8],
        },
        "by_state": state_summary,
    }

    print("[6/6] Writing outputs...")
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "summary-data.js").write_text(
        "window.CMS_NURSING_HOME_DATA = " + json.dumps(summary, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    (OUT_DIR / "chains.json").write_text(
        json.dumps({"generated_utc": summary["metadata"]["generated_utc"], "national": national_chain_row, "chains": chains_out}, separators=(",", ":")),
        encoding="utf-8",
    )
    (OUT_DIR / "facilities.json").write_text(
        json.dumps(
            {
                "cols": FACILITY_COLS,
                "own_types": own_type_list,
                "chains": chain_id_name_map,
                "rows": facility_rows_compact,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    if args.export_csv:
        out_csv = args.export_csv
        if not out_csv.is_absolute():
            out_csv = OUT_DIR / out_csv
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(csv_export_rows[0].keys()) if csv_export_rows else []
        if str(out_csv).endswith(".gz"):
            with gzip.open(out_csv, "wt", encoding="utf-8", newline="") as gz:
                w = csv.DictWriter(gz, fieldnames=fieldnames)
                w.writeheader()
                w.writerows(csv_export_rows)
        else:
            with out_csv.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                w.writerows(csv_export_rows)
        print(f"  Exported linked CSV: {out_csv} ({out_csv.stat().st_size / 1024:.1f} KB)")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s! Key Verification Summary:")
    print(f"  Facilities: {total_facilities:,} (alphanumeric CCNs: {alphanumeric_ccns})")
    print(f"  National 7d->Wknd: Total {summary['national']['avg_total_hprd']}h -> {summary['national']['avg_weekend_hprd']}h (-{summary['national']['weekend_drop_pct']}%) | Implied Wkday->Wknd: -{summary['national']['implied_weekday_drop_pct']}%")
    print(f"  National RN 7d->Wknd: {summary['national']['avg_rn_hprd']}h -> {summary['national']['avg_rn_weekend_hprd']}h (-{summary['national']['rn_weekend_drop_pct']}%) | Implied Wkday->Wknd: -{summary['national']['implied_rn_weekday_drop_pct']}%")
    print(f"  5-Star Reality: n={five_star_n:,}, any 3 red flags={summary['five_star_reality']['pct_any_red_flag_3']}% ({five_star_any_3:,}), any 4={summary['five_star_reality']['pct_any_red_flag_4']}% | 4★ w/ Abuse Icon: {len(four_star_abuse_homes)}")
    print(f"  Overdue >2yr: {overdue_total_n:,} ({summary['national']['pct_overdue_2yr']}%) | Top 5 states: {[(x['state'], x['overdue_pct']) for x in summary['inspection_backlog']['top_overdue_states'][:5]]}")
    print(f"  5★ Uninspected <=2020: {[(x['ccn'], x['state'], x['last_inspection_date']) for x in summary['inspection_backlog']['five_star_uninspected_since_2020']]}")
    print(f"  Gov-Chain Distortion: {gov_in_chain_n}/{gov_total_n} ({summary['gov_chain_distortion']['gov_in_chain_pct']}%) | TX={gov_chain_by_state.get('TX',0)}, IN={gov_chain_by_state.get('IN',0)}")
    print(f"  PECOS Audit: {len(owner_rows):,} rows, {len(pecos_by_ccn):,} CCNs | Nameless org rows={pecos_row_stats['nameless_org_rows']:,} ({summary['pecos_audit']['nameless_org_pct_of_org_rows']}% of org rows) | PE={pecos_flag_facility_counts['pe']}, REIT={pecos_flag_facility_counts['reit']}, ADP={pecos_flag_facility_counts['adp']}, Holding={pecos_flag_facility_counts['holding']}")
    print(f"  Cost Report FY2024: {len(all_matched_costs):,} matched ({summary['cost_report_analysis']['match_rate_pct']}%) | Hosp-based excluded={hosp_snf_missing_cost}/{hosp_snf_total} ({summary['cost_report_analysis']['hospital_based_exclusion_pct']}%)")
    for row in cost_matrix:
        fp = row["by_ownership"]["For-Profit"]
        np_ = row["by_ownership"]["Non-Profit"]
        print(f"    Medicaid {row['medicaid_tier']:6s} | FP(n={fp['facilities']:4d}): opMgn={fp['median_op_margin_pct']}% totMgn={fp['median_tot_margin_pct']}% labor=${fp['median_direct_labor_day']}/d | NP(n={np_['facilities']:4d}): opMgn={np_['median_op_margin_pct']}% totMgn={np_['median_tot_margin_pct']}% labor=${np_['median_direct_labor_day']}/d")
    for fn in ("summary.json", "summary-data.js", "chains.json", "facilities.json"):
        p = OUT_DIR / fn
        print(f"  File size {fn:18s}: {p.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
