"""
Reproducible 4-Dataset Analysis: U.S. Hospital Charity Care, Chargemaster Markups & Financial Reality
Primary Sources (live CMS APIs, joined by normalized 6-char CCN & PECOS Enrollment ID):
  1. CMS Hospital General Information (xubh-q36u) — all ~5,435 U.S. hospitals (stars, ownership, type, ER)
  2. CMS Hospital Provider Cost Report FY2024 Form 2552-10 (data-api/v1, dynamically resolved)
     — Worksheet S-10 Cost of Charity Care, Bad Debt, Uncompensated Care, Cost-to-Charge Ratio,
       Less Total Operating Expense, Net Patient Revenue, Operating & Total Net Margins
  3. CMS Hospital Enrollments (data-api/v1, dynamically resolved)
  4. CMS Hospital All Owners / PECOS (data-api/v1, dynamically resolved) — Chain Home Office, PE/REIT flags

Run:
  python analyze_cms_hospitals.py
  python analyze_cms_hospitals.py --export-csv cms-hospitals-linked.csv.gz

Outputs:
  - summary.json
  - summary-data.js
  - hospitals.json (compact lookup index for all ~5,435 hospitals)
  - (optional) cms-hospitals-linked.csv.gz
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
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).resolve().parent
CURL_BIN = shutil.which("curl.exe") or shutil.which("curl") or "curl"

HOSP_INFO_BASE = "https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0"
CMS_CATALOG_URL = "https://data.cms.gov/data.json"

FALLBACK_DATASETS = {
    "cost_report": {
        "title_prefix": "Hospital Provider Cost Report",
        "uuid": "44060663-47d8-4ced-a115-b53b4c270acb",
        "title": "Hospital Provider Cost Report (fallback FY2024)",
    },
    "enrollments": {
        "title_prefix": "Hospital Enrollments",
        "uuid": "f6f6505c-e8b0-4d57-b258-e2b94133aaf2",
        "title": "Hospital Enrollments (fallback)",
    },
    "owners": {
        "title_prefix": "Hospital All Owners",
        "uuid": "029c119f-f79c-49be-9100-344d31d10344",
        "title": "Hospital All Owners (fallback)",
    },
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
            raw = subprocess.check_output([CURL_BIN, "-sS", "--fail", url], timeout=timeout)
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def norm_ccn(v: Any) -> str:
    s = str(v or "").strip().upper()
    if s.isdigit():
        return s.zfill(6)
    return s


def to_float(v: Any) -> float | None:
    if v in (None, "", "Not Available", "N/A"):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def parse_iso_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def classify_ownership(raw: str | None) -> str:
    s = (raw or "").lower()
    if "non-profit" in s or "nonprofit" in s or "voluntary" in s:
        return "Non-Profit"
    if "proprietary" in s or "for-profit" in s or "physician" in s:
        return "For-Profit"
    if "government" in s or "tribal" in s or "department of defense" in s or "veterans" in s:
        return "Government"
    return "Other"


def resolve_endpoints() -> dict[str, dict[str, str]]:
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
        cat = curl_json(CMS_CATALOG_URL, timeout=90, retries=2)
        for key, spec in FALLBACK_DATASETS.items():
            prefix = spec["title_prefix"]
            for ds in cat.get("dataset", []):
                title = ds.get("title", "")
                if not title.startswith(prefix):
                    continue
                for dist in ds.get("distribution", []):
                    if dist.get("description") == "latest" and dist.get("accessURL"):
                        u = dist["accessURL"]
                        parts = u.split("/dataset/")
                        uid = parts[1].split("/")[0] if len(parts) > 1 else spec["uuid"]
                        resolved[key] = {
                            "title": title,
                            "uuid": uid,
                            "url": u,
                            "resolved_dynamically": "true",
                        }
    except Exception:
        pass
    return resolved


def fetch_pdc_all(base_url: str, page_size: int = 500) -> list[dict[str, Any]]:
    first = curl_json(f"{base_url}?limit={page_size}&offset=0")
    total = int(first["count"])
    rows = list(first["results"])
    offsets = list(range(page_size, total, page_size))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for res in ex.map(lambda o: curl_json(f"{base_url}?limit={page_size}&offset={o}"), offsets):
            rows.extend(res.get("results", []))
    return rows


def fetch_data_api_all(url: str, page_size: int = 5000) -> list[dict[str, Any]]:
    stats = curl_json(f"{url}/stats")
    total = int(stats["total_rows"])
    offsets = list(range(0, total, page_size))
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for batch in ex.map(lambda o: curl_json(f"{url}?size={page_size}&offset={o}"), offsets):
            rows.extend(batch)
    return rows


def med(arr: list[float], digits: int = 2) -> float | None:
    return round(statistics.median(arr), digits) if arr else None


def avg(arr: list[float], digits: int = 2) -> float | None:
    return round(statistics.mean(arr), digits) if arr else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-csv", default="", help="Optional output filename (.csv or .csv.gz) in data/hospitals/")
    args = parser.parse_args()

    t0 = time.time()
    endpoints = resolve_endpoints()

    # Fetch all 4 datasets
    hospitals_raw = fetch_pdc_all(HOSP_INFO_BASE)
    cr_raw = fetch_data_api_all(endpoints["cost_report"]["url"])
    enr_raw = fetch_data_api_all(endpoints["enrollments"]["url"])
    own_raw = fetch_data_api_all(endpoints["owners"]["url"])

    # 1. Deduplicate Cost Reports per CCN: prefer longest fiscal year (>=300d full-year flag)
    cr_by_ccn: dict[str, dict[str, Any]] = {}
    cr_days_by_ccn: dict[str, int] = {}
    for r in cr_raw:
        ccn = norm_ccn(r.get("Provider CCN"))
        if not ccn:
            continue
        d1 = parse_iso_date(r.get("Fiscal Year Begin Date"))
        d2 = parse_iso_date(r.get("Fiscal Year End Date"))
        days = (d2 - d1).days + 1 if d1 and d2 else 0
        prev_days = cr_days_by_ccn.get(ccn, -1)
        if days > prev_days:
            cr_by_ccn[ccn] = r
            cr_days_by_ccn[ccn] = days

    # 2. Index Enrollments (CCN -> list of Enrollment IDs) and Owners (Enrollment ID -> owner metadata)
    eids_by_ccn: dict[str, set[str]] = defaultdict(set)
    for r in enr_raw:
        ccn = norm_ccn(r.get("CCN"))
        eid = (r.get("ENROLLMENT ID") or "").strip()
        if ccn and eid:
            eids_by_ccn[ccn].add(eid)

    own_by_eid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pe_rows_total = 0
    pe_rows_blank_org = 0
    reit_rows_total = 0
    reit_rows_blank_org = 0
    for r in own_raw:
        eid = (r.get("ENROLLMENT ID") or "").strip()
        if not eid:
            continue
        own_by_eid[eid].append(r)
        is_org = (r.get("TYPE - OWNER") or "").strip().upper() == "O"
        org_name = (r.get("ORGANIZATION NAME - OWNER") or "").strip()
        if r.get("PRIVATE EQUITY COMPANY - OWNER") == "Y":
            pe_rows_total += 1
            if is_org and not org_name:
                pe_rows_blank_org += 1
        if r.get("REIT - OWNER") == "Y":
            reit_rows_total += 1
            if is_org and not org_name:
                reit_rows_blank_org += 1

    # 3. Join all 4 datasets onto CMS Hospital General Information base universe
    linked = []
    matched_cr = 0
    full_year_cr = 0
    matched_enr = 0

    for h in hospitals_raw:
        ccn = norm_ccn(h.get("facility_id"))
        if not ccn:
            continue
        name = (h.get("facility_name") or "").strip()
        city = (h.get("citytown") or "").strip()
        state = (h.get("state") or "").strip().upper()
        zip5 = str(h.get("zip_code") or "").strip()[:5]
        htype = (h.get("hospital_type") or "").strip()
        own_raw_str = (h.get("hospital_ownership") or "").strip()
        own_grp = classify_ownership(own_raw_str)
        er = (h.get("emergency_services") or "").strip().lower() == "yes"
        stars = to_float(h.get("hospital_overall_rating"))
        stars_int = int(stars) if stars is not None else None

        # Ownership / System from PECOS
        eids = eids_by_ccn.get(ccn, set())
        pe_flag = False
        reit_flag = False
        holding_flag = False
        mgmt_flag = False
        system_names: list[str] = []
        if eids:
            matched_enr += 1
            for eid in eids:
                for ow in own_by_eid.get(eid, []):
                    if ow.get("PRIVATE EQUITY COMPANY - OWNER") == "Y":
                        pe_flag = True
                    if ow.get("REIT - OWNER") == "Y":
                        reit_flag = True
                    if ow.get("HOLDING COMPANY - OWNER") == "Y":
                        holding_flag = True
                    if ow.get("MANAGEMENT SERVICES COMPANY - OWNER") == "Y":
                        mgmt_flag = True
                    if ow.get("CHAIN HOME OFFICE - OWNER") == "Y":
                        oname = (ow.get("ORGANIZATION NAME - OWNER") or "").strip()
                        if oname and oname not in system_names:
                            system_names.append(oname)
        system_name = system_names[0] if system_names else None

        # Cost Report FY2024 metrics
        cr = cr_by_ccn.get(ccn)
        fy_days = cr_days_by_ccn.get(ccn, 0)
        is_fy = False
        op_exp = npr = op_inc = other_inc = net_inc = charity_cost = bad_debt = bad_debt_cost = uncomp_cost = ccr = markup = None
        charity_pct = uncomp_pct = bad_debt_pct = op_mgn = net_mgn = bad_to_charity = None
        cash_assets = total_assets = beds = None
        fy_end = None

        if cr is not None:
            matched_cr += 1
            fy_end = cr.get("Fiscal Year End Date")
            if fy_days >= 300:
                is_fy = True
                full_year_cr += 1
                op_exp = to_float(cr.get("Less Total Operating Expense"))
                npr = to_float(cr.get("Net Patient Revenue"))
                op_inc = to_float(cr.get("Net Income from Service to Patients"))
                other_inc = to_float(cr.get("Total Other Income"))
                net_inc = to_float(cr.get("Net Income"))
                charity_cost = to_float(cr.get("Cost of Charity Care"))
                bad_debt = to_float(cr.get("Total Bad Debt Expense"))
                uncomp_cost = to_float(cr.get("Cost of Uncompensated Care"))
                ccr = to_float(cr.get("Cost To Charge Ratio"))
                cash_assets = to_float(cr.get("Cash on Hand and in Banks"))
                total_assets = to_float(cr.get("Total Assets"))
                beds = to_float(cr.get("Number of Beds"))

                if ccr is not None and 0.02 <= ccr <= 5.0:
                    markup = round(1.0 / ccr, 2)
                # Apples-to-apples cost of non-Medicare bad debt (Worksheet S-10 line 29 = Uncomp Cost - Charity Cost).
                # Note: raw "Total Bad Debt Expense" is reported at billed chargemaster charges, NOT cost!
                bad_debt_cost = None
                if uncomp_cost is not None and charity_cost is not None and uncomp_cost >= charity_cost:
                    bad_debt_cost = uncomp_cost - charity_cost
                elif bad_debt is not None and ccr is not None and bad_debt >= 0 and 0.02 <= ccr <= 5.0:
                    bad_debt_cost = bad_debt * ccr

                if op_exp is not None and op_exp > 100_000:
                    if charity_cost is not None and charity_cost >= 0:
                        charity_pct = round(charity_cost / op_exp * 100, 2)
                    if uncomp_cost is not None and uncomp_cost >= 0:
                        uncomp_pct = round(uncomp_cost / op_exp * 100, 2)
                    if bad_debt_cost is not None and bad_debt_cost >= 0:
                        bad_debt_pct = round(bad_debt_cost / op_exp * 100, 2)
                if npr is not None and npr > 100_000:
                    if op_inc is not None:
                        op_mgn = round(op_inc / npr * 100, 1)
                    tot_rev = npr + (other_inc or 0.0)
                    if net_inc is not None and tot_rev > 100_000:
                        net_mgn = round(net_inc / tot_rev * 100, 1)
                if bad_debt_cost is not None and charity_cost is not None and charity_cost > 10_000 and bad_debt_cost >= 0:
                    bad_to_charity = round(bad_debt_cost / charity_cost, 2)

        # Flags for quick filtering
        flags = []
        if own_grp == "Non-Profit" and charity_pct is not None and charity_pct < 1.0 and op_exp and op_exp >= 50_000_000:
            flags.append("LOW_CHARITY_NP")
        if own_grp == "Non-Profit" and charity_pct is not None and charity_pct < 1.0 and net_mgn is not None and net_mgn >= 5.0:
            flags.append("HIGH_MARGIN_LOW_CHARITY")
        if markup is not None and markup >= 5.0:
            flags.append("HIGH_MARKUP_5X")
        if pe_flag:
            flags.append("PE")
        if reit_flag:
            flags.append("REIT")
        if bad_debt_cost is not None and charity_cost is not None and charity_cost >= 0 and bad_debt_cost > charity_cost * 2 and op_exp and op_exp >= 25_000_000:
            flags.append("BAD_DEBT_HEAVY")

        linked.append({
            "ccn": ccn,
            "name": name,
            "city": city,
            "state": state,
            "zip": zip5,
            "type": htype,
            "own_raw": own_raw_str,
            "own": own_grp,
            "er": er,
            "stars": stars_int,
            "system": system_name,
            "pe": pe_flag,
            "reit": reit_flag,
            "holding": holding_flag,
            "mgmt": mgmt_flag,
            "fy_end": fy_end,
            "fy_days": fy_days if cr else None,
            "is_fy": is_fy,
            "beds": int(beds) if beds is not None else None,
            "op_exp": round(op_exp) if op_exp is not None else None,
            "npr": round(npr) if npr is not None else None,
            "net_inc": round(net_inc) if net_inc is not None else None,
            "charity_cost": round(charity_cost) if charity_cost is not None else None,
            "bad_debt": round(bad_debt_cost) if bad_debt_cost is not None else None,
            "bad_debt_raw_charges": round(bad_debt) if bad_debt is not None else None,
            "uncomp_cost": round(uncomp_cost) if uncomp_cost is not None else None,
            "charity_pct": charity_pct,
            "bad_debt_pct": bad_debt_pct,
            "uncomp_pct": uncomp_pct,
            "markup": markup,
            "op_mgn": op_mgn,
            "net_mgn": net_mgn,
            "bad_to_charity": bad_to_charity,
            "flags": flags,
        })

    # 4. Compute Summary Analytics (focusing on Acute Care + Critical Access full-year S-10 reporters for clean comparisons)
    s10_full = [x for x in linked if x["is_fy"] and x["charity_pct"] is not None]
    acute_s10 = [x for x in s10_full if x["type"] in ("Acute Care Hospitals", "Critical Access Hospitals")]

    by_owner = []
    for own in ("Non-Profit", "For-Profit", "Government"):
        grp_all = [x for x in linked if x["own"] == own]
        grp_fy = [x for x in linked if x["own"] == own and x["is_fy"]]
        grp_s10 = [x for x in acute_s10 if x["own"] == own]
        stars_l = [x["stars"] for x in grp_all if x["stars"] is not None]
        ch_l = [x["charity_pct"] for x in grp_s10 if x["charity_pct"] is not None]
        bd_l = [x["bad_debt_pct"] for x in grp_s10 if x["bad_debt_pct"] is not None]
        uc_l = [x["uncomp_pct"] for x in grp_s10 if x["uncomp_pct"] is not None]
        mk_l = [x["markup"] for x in grp_fy if x["markup"] is not None and x["type"] in ("Acute Care Hospitals", "Critical Access Hospitals")]
        om_l = [x["op_mgn"] for x in grp_fy if x["op_mgn"] is not None and -100 <= x["op_mgn"] <= 100 and x["type"] in ("Acute Care Hospitals", "Critical Access Hospitals")]
        nm_l = [x["net_mgn"] for x in grp_fy if x["net_mgn"] is not None and -100 <= x["net_mgn"] <= 100 and x["type"] in ("Acute Care Hospitals", "Critical Access Hospitals")]
        tot_ch_b = round(sum(x["charity_cost"] for x in grp_s10 if x["charity_cost"] and x["charity_cost"] > 0) / 1e9, 2)
        tot_bd_b = round(sum(x["bad_debt"] for x in grp_s10 if x["bad_debt"] and x["bad_debt"] > 0) / 1e9, 2)
        tot_op_b = round(sum(x["op_exp"] for x in grp_s10 if x["op_exp"] and x["op_exp"] > 0) / 1e9, 2)
        under_1 = sum(1 for v in ch_l if v < 1.0)
        under_2 = sum(1 for v in ch_l if v < 2.0)
        by_owner.append({
            "ownership": own,
            "total_hospitals": len(grp_all),
            "s10_acute_count": len(grp_s10),
            "avg_stars": avg(stars_l, 2),
            "median_charity_pct": med(ch_l, 2),
            "weighted_charity_pct": round(tot_ch_b / tot_op_b * 100, 2) if tot_op_b > 0 else None,
            "median_bad_debt_pct": med(bd_l, 2),
            "median_uncomp_pct": med(uc_l, 2),
            "median_markup": med(mk_l, 2),
            "median_op_mgn": med(om_l, 1),
            "median_net_mgn": med(nm_l, 1),
            "pct_charity_under_1": round(under_1 / len(ch_l) * 100, 1) if ch_l else None,
            "pct_charity_under_2": round(under_2 / len(ch_l) * 100, 1) if ch_l else None,
            "total_charity_billions": tot_ch_b,
            "total_bad_debt_billions": tot_bd_b,
        })

    # Nonprofit charity distribution tiers (Acute + CAH)
    np_s10 = [x for x in acute_s10 if x["own"] == "Non-Profit"]
    np_tiers = {
        "total_np_s10": len(np_s10),
        "under_1pct": sum(1 for x in np_s10 if x["charity_pct"] < 1.0),
        "1_to_2pct": sum(1 for x in np_s10 if 1.0 <= x["charity_pct"] < 2.0),
        "2_to_4pct": sum(1 for x in np_s10 if 2.0 <= x["charity_pct"] < 4.0),
        "4pct_plus": sum(1 for x in np_s10 if x["charity_pct"] >= 4.0),
        "high_margin_low_charity_count": sum(1 for x in np_s10 if x["charity_pct"] < 1.0 and x["net_mgn"] is not None and x["net_mgn"] >= 5.0),
    }

    # Markup distribution across Acute + CAH
    acute_mk = [x for x in linked if x["is_fy"] and x["markup"] is not None and x["type"] in ("Acute Care Hospitals", "Critical Access Hospitals")]
    markup_stats = {
        "count": len(acute_mk),
        "median_markup": med([x["markup"] for x in acute_mk], 2),
        "over_5x_count": sum(1 for x in acute_mk if x["markup"] >= 5.0),
        "over_5x_pct": round(sum(1 for x in acute_mk if x["markup"] >= 5.0) / len(acute_mk) * 100, 1) if acute_mk else 0,
        "over_10x_count": sum(1 for x in acute_mk if x["markup"] >= 10.0),
        "fp_median_markup": med([x["markup"] for x in acute_mk if x["own"] == "For-Profit"], 2),
        "np_median_markup": med([x["markup"] for x in acute_mk if x["own"] == "Non-Profit"], 2),
        "gov_median_markup": med([x["markup"] for x in acute_mk if x["own"] == "Government"], 2),
    }

    # State summary (50 states + DC)
    by_state = []
    for st in sorted(US_STATES_DC):
        st_all = [x for x in linked if x["state"] == st]
        st_np = [x for x in np_s10 if x["state"] == st]
        st_mk = [x for x in acute_mk if x["state"] == st]
        if not st_all:
            continue
        by_state.append({
            "state": st,
            "total_hospitals": len(st_all),
            "np_s10_count": len(st_np),
            "np_median_charity_pct": med([x["charity_pct"] for x in st_np], 2),
            "np_pct_under_1": round(sum(1 for x in st_np if x["charity_pct"] < 1.0) / len(st_np) * 100, 1) if st_np else None,
            "median_markup": med([x["markup"] for x in st_mk], 2),
            "median_net_mgn": med([x["net_mgn"] for x in st_all if x["is_fy"] and x["net_mgn"] is not None and -100 <= x["net_mgn"] <= 100], 1),
        })
    by_state.sort(key=lambda x: x["np_median_charity_pct"] if x["np_median_charity_pct"] is not None else 999)

    # Top Large Nonprofit Hospitals with Lowest Charity Care (<1%) & Strong Net Margins (op_exp >= $250M, net_mgn >= 5%)
    spotlight_low_charity = sorted(
        [x for x in np_s10 if (x["op_exp"] or 0) >= 250_000_000 and x["charity_pct"] < 1.0 and (x["net_mgn"] or -999) >= 5.0],
        key=lambda x: (x["charity_pct"], -(x["net_inc"] or 0)),
    )[:15]

    # Top High-Markup Acute Hospitals (op_exp >= $100M)
    spotlight_markup = sorted(
        [x for x in acute_mk if (x["op_exp"] or 0) >= 100_000_000],
        key=lambda x: -(x["markup"] or 0),
    )[:15]

    # PECOS Hospital Ownership Audit
    pe_hosp = [x for x in linked if x["pe"]]
    reit_hosp = [x for x in linked if x["reit"]]
    pecos_audit = {
        "matched_hospitals": matched_enr,
        "match_pct": round(matched_enr / len(linked) * 100, 1) if linked else 0,
        "total_owner_rows": len(own_raw),
        "pe_hospitals": len(pe_hosp),
        "reit_hospitals": len(reit_hosp),
        "pe_rows_total": pe_rows_total,
        "pe_rows_blank_org": pe_rows_blank_org,
        "reit_rows_total": reit_rows_total,
        "reit_rows_blank_org": reit_rows_blank_org,
        "chain_home_office_hospitals": sum(1 for x in linked if x["system"]),
    }

    summary = {
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "runtime_sec": round(time.time() - t0, 1),
            "endpoints": endpoints,
            "total_hospitals": len(linked),
            "matched_cost_reports": matched_cr,
            "full_year_cost_reports": full_year_cr,
            "acute_cah_s10_count": len(acute_s10),
        },
        "by_ownership": by_owner,
        "nonprofit_charity_tiers": np_tiers,
        "markup_stats": markup_stats,
        "pecos_audit": pecos_audit,
        "by_state": by_state,
        "spotlight_low_charity_high_margin_np": [
            {k: x[k] for k in ("ccn", "name", "city", "state", "stars", "op_exp", "charity_cost", "charity_pct", "bad_debt", "net_inc", "net_mgn", "markup")}
            for x in spotlight_low_charity
        ],
        "spotlight_highest_markup": [
            {k: x[k] for k in ("ccn", "name", "city", "state", "own", "stars", "op_exp", "markup", "charity_pct", "net_mgn")}
            for x in spotlight_markup
        ],
    }

    # Compact array-of-arrays for fast browser lookup across ALL 5,435 hospitals
    cols = [
        "ccn", "name", "city", "state", "zip", "type", "own", "er", "stars", "system",
        "beds", "op_exp", "charity_cost", "charity_pct", "bad_debt", "bad_debt_pct",
        "uncomp_pct", "markup", "op_mgn", "net_mgn", "net_inc", "flags",
    ]
    rows_compact = [
        [
            x["ccn"], x["name"], x["city"], x["state"], x["zip"], x["type"], x["own"],
            1 if x["er"] else 0, x["stars"], x["system"], x["beds"], x["op_exp"],
            x["charity_cost"], x["charity_pct"], x["bad_debt"], x["bad_debt_pct"],
            x["uncomp_pct"], x["markup"], x["op_mgn"], x["net_mgn"], x["net_inc"],
            "|".join(x["flags"]),
        ]
        for x in linked
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "summary-data.js").write_text(
        "window.CMS_HOSPITAL_DATA = " + json.dumps(summary, indent=2) + ";\n",
        encoding="utf-8",
    )
    (OUT_DIR / "hospitals.json").write_text(
        json.dumps({"cols": cols, "rows": rows_compact}, separators=(",", ":")),
        encoding="utf-8",
    )

    if args.export_csv:
        csv_path = OUT_DIR / args.export_csv
        csv_fields = [
            "ccn", "name", "city", "state", "zip", "type", "own_raw", "own", "er", "stars",
            "system", "pe", "reit", "holding", "mgmt", "fy_end", "fy_days", "beds",
            "op_exp", "npr", "net_inc", "charity_cost", "charity_pct", "bad_debt",
            "bad_debt_pct", "uncomp_cost", "uncomp_pct", "markup", "op_mgn", "net_mgn",
            "bad_to_charity", "flags",
        ]
        opener = gzip.open if str(csv_path).endswith(".gz") else open
        with opener(csv_path, "wt", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(csv_fields)
            for x in linked:
                w.writerow([
                    "|".join(x[k]) if k == "flags" else x[k]
                    for k in csv_fields
                ])

    print(f"Hospitals analyzed: {len(linked):,} | CR matched: {matched_cr:,} | Full-year CR: {full_year_cr:,} | Acute/CAH S-10: {len(acute_s10):,} ({round(time.time()-t0,1)}s)")
    print("\nBy Ownership (Acute + Critical Access S-10):")
    for o in by_owner:
        print(
            f"  {o['ownership']:10s} | all={o['total_hospitals']:4d} s10={o['s10_acute_count']:4d} | med charity={o['median_charity_pct']}% (<1%: {o['pct_charity_under_1']}%, <2%: {o['pct_charity_under_2']}%) | badDebt={o['median_bad_debt_pct']}% | markup={o['median_markup']}x | opMgn={o['median_op_mgn']}% netMgn={o['median_net_mgn']}% | $charity=${o['total_charity_billions']}B $badDebt=${o['total_bad_debt_billions']}B"
        )
    print("\nNonprofit Charity Tiers:", np_tiers)
    print("Markup Stats:", markup_stats)
    print("PECOS Hospital Audit:", pecos_audit)
    print("\nTop 8 Large Non-Profits (>= $250M op_exp, >= 5% net margin, <1% charity care):")
    for x in spotlight_low_charity[:8]:
        print(f"  {x['ccn']} {x['name'][:36]:36s} ({x['state']}) | opExp=${x['op_exp']/1e6:6.0f}M | charity={x['charity_pct']:4.2f}% (${x['charity_cost']/1e6:4.1f}M) | netMgn={x['net_mgn']:5.1f}% (${x['net_inc']/1e6:5.1f}M) | markup={x['markup']}x")
    print("\nTop 8 Highest Chargemaster Markup Hospitals (>= $100M op_exp):")
    for x in spotlight_markup[:8]:
        print(f"  {x['ccn']} {x['name'][:36]:36s} ({x['state']}, {x['own']:10s}) | markup={x['markup']:5.2f}x | charity={x['charity_pct']}% | netMgn={x['net_mgn']}%")


if __name__ == "__main__":
    main()
