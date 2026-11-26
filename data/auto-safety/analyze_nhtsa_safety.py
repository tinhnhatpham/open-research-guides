#!/usr/bin/env python3
"""
NHTSA U.S. Vehicle Safety Recalls, Fire/Crash Complaints & Automaker
Accountability Pipeline (Post-2010 Recalls + 2020-2026 Owner Complaints).

Downloads directly from official static.nhtsa.gov/odi/ffdd/ flat files:
  1. FLAT_RCL_POST_2010.zip (all NHTSA safety recalls 2010-present)
  2. COMPLAINTS_RECEIVED_2020-2024.zip + COMPLAINTS_RECEIVED_2025-2026.zip

Critical accounting & data-hygiene safeguards built in:
  - Deduplicates Complaints by ODINO before summing crashes, fires, injuries,
    and deaths (NHTSA repeats ODINO rows whenever a single complaint cites
    multiple vehicle components—preventing 1.5x-3x double counting).
  - Deduplicates Recalls by CAMPNO before summing Potential Units Affected
    (POTAFF), Do-Not-Drive, Park-Outside, and ODI-forced counts (NHTSA repeats
    POTAFF on every model-year row within a multi-model campaign).
  - Filters vehicle recalls (RCLTYPECD == 'V') for automaker & used-car model
    scorecards while tracking major passenger vehicle brands cleanly.
  - Emits model-year dossiers (MY 2010-2026), Do-Not-Drive / Park-Outside
    critical advisory catalog, automaker accountability scorecard, and open
    .csv.gz downloads.
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

RCL_URL = "https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip"
CMPL_URLS = [
    ("COMPLAINTS_2020_2024.zip", "https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2020-2024.zip"),
    ("COMPLAINTS_2025_2026.zip", "https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2025-2026.zip"),
]

CACHE_DIR = Path(
    os.environ.get("NHTSA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "nhtsa_cache"))
)

MAJOR_BRANDS = {
    "FORD", "TOYOTA", "CHEVROLET", "HONDA", "NISSAN", "HYUNDAI", "KIA", "JEEP",
    "SUBARU", "RAM", "GMC", "DODGE", "BMW", "MERCEDES-BENZ", "VOLKSWAGEN",
    "TESLA", "MAZDA", "LEXUS", "AUDI", "CHRYSLER", "BUICK", "CADILLAC",
    "VOLVO", "ACURA", "MITSUBISHI", "LINCOLN", "INFINITI", "MINI", "PORSCHE",
    "LAND ROVER", "GENESIS", "RIVIAN", "LUCID", "ALFA ROMEO", "FIAT", "JAGUAR",
}

BRAND_ALIAS = {
    "MERCEDES BENZ": "MERCEDES-BENZ",
    "MERCEDES": "MERCEDES-BENZ",
    "VW": "VOLKSWAGEN",
    "CHEVY": "CHEVROLET",
    "LANDROVER": "LAND ROVER",
    "ALFA": "ALFA ROMEO",
}


def norm_make(m: str) -> str:
    s = " ".join((m or "").strip().upper().split())
    return BRAND_ALIAS.get(s, s)


def norm_model(m: str) -> str:
    s = " ".join((m or "").strip().upper().split())
    return s


def safe_int(v: str) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def fetch_zip(filename: str, url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / filename
    if dst.exists() and dst.stat().st_size > 1_000_000 and zipfile.is_zipfile(dst):
        return dst
    tmp = dst.with_suffix(".tmp")
    code = subprocess.check_output(
        [CURL_BIN, "-sL", "-w", "%{http_code}", "-o", str(tmp), url],
        text=True,
    ).strip()
    if code != "200" or not tmp.exists() or not zipfile.is_zipfile(tmp):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed downloading {url}: HTTP {code}")
    tmp.replace(dst)
    print(f"Downloaded {filename} ({dst.stat().st_size:,} bytes)")
    return dst


def main() -> None:
    rcl_zip = fetch_zip("FLAT_RCL_POST_2010.zip", RCL_URL)
    cmpl_zips = [fetch_zip(fn, url) for fn, url in CMPL_URLS]

    # ------------------------------------------------------------------
    # 1. Parse Recalls (FLAT_RCL_POST_2010.zip) — deduplicated by CAMPNO
    # ------------------------------------------------------------------
    # 0-based indices per RCL.txt:
    # 1:CAMPNO, 2:MAKETXT, 3:MODELTXT, 4:YEARTXT, 6:COMPNAME, 7:MFGNAME,
    # 10:RCLTYPECD, 11:POTAFF, 13:INFLUENCED_BY, 15:RCDATE, 19:DESC_DEFECT,
    # 20:CONSEQUENCE, 27:DO_NOT_DRIVE, 28:PARK_OUTSIDE
    campaigns: dict[str, dict[str, Any]] = {}
    mmy_recalls: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    mmy_odi: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    mmy_dnd: dict[tuple[str, str, int], bool] = defaultdict(bool)
    mmy_po: dict[tuple[str, str, int], bool] = defaultdict(bool)
    mmy_rcl_comps: dict[tuple[str, str, int], Counter] = defaultdict(Counter)

    rcl_raw_rows = 0
    with zipfile.ZipFile(rcl_zip) as zf:
        fn = zf.namelist()[0]
        with zf.open(fn) as raw:
            for line in io.TextIOWrapper(raw, encoding="latin-1", errors="replace"):
                parts = line.rstrip("\r\n").split("\t")
                if len(parts) < 22:
                    continue
                rcl_raw_rows += 1
                rtype = parts[10].strip().upper()
                if rtype != "V":
                    continue
                camp = parts[1].strip().upper()
                if not camp:
                    continue
                make = norm_make(parts[2])
                model = norm_model(parts[3])
                yr = safe_int(parts[4])
                comp = parts[6].strip().upper()
                potaff = safe_int(parts[11])
                infl = parts[13].strip().upper()
                rcdate = parts[15].strip()
                rc_yr = safe_int(rcdate[:4])
                desc = parts[19].strip()
                conseq = parts[20].strip()
                dnd = len(parts) > 27 and parts[27].strip().upper() in ("YES", "Y")
                po = len(parts) > 28 and parts[28].strip().upper() in ("YES", "Y")
                fire_risk = po or ("FIRE" in conseq.upper()) or ("THERMAL" in conseq.upper())

                if camp not in campaigns:
                    campaigns[camp] = {
                        "camp": camp,
                        "rcdate": rcdate,
                        "rc_yr": rc_yr,
                        "potaff": potaff,
                        "infl": infl,
                        "dnd": dnd,
                        "po": po,
                        "fire_risk": fire_risk,
                        "comp": comp[:80],
                        "makes": set(),
                        "models": set(),
                        "years": set(),
                        "conseq": conseq[:220],
                        "desc": desc[:260],
                    }
                c = campaigns[camp]
                if potaff > c["potaff"]:
                    c["potaff"] = potaff
                if dnd:
                    c["dnd"] = True
                if po:
                    c["po"] = True
                if fire_risk:
                    c["fire_risk"] = True
                if make:
                    c["makes"].add(make)
                if model:
                    c["models"].add(model)
                if 1990 <= yr <= 2027:
                    c["years"].add(yr)

                if make in MAJOR_BRANDS and model and 2010 <= yr <= 2026:
                    key = (make, model, yr)
                    mmy_recalls[key].add(camp)
                    if infl == "ODI":
                        mmy_odi[key].add(camp)
                    if dnd:
                        mmy_dnd[key] = True
                    if po:
                        mmy_po[key] = True
                    if comp:
                        mmy_rcl_comps[key][comp.split(":")[0].strip()[:40]] += 1

    # ------------------------------------------------------------------
    # 2. Parse Complaints (2020-2026) — DEDUPLICATED by ODINO!
    # ------------------------------------------------------------------
    # 0-based indices per CMPL.txt:
    # 1:ODINO, 3:MAKETXT, 4:MODELTXT, 5:YEARTXT, 6:CRASH, 8:FIRE,
    # 9:INJURED, 10:DEATHS, 11:COMPDESC, 16:LDATE
    cmpl_raw_rows = 0
    seen_odino: set[str] = set()
    dup_odino = 0

    tot_cmpl = 0
    tot_crash = 0
    tot_fire = 0
    tot_inj = 0
    tot_death = 0
    cmpl_by_year: dict[str, dict[str, int]] = defaultdict(lambda: {"cmpl": 0, "crash": 0, "fire": 0, "inj": 0, "death": 0})
    brand_cmpl: dict[str, dict[str, int]] = defaultdict(lambda: {"cmpl": 0, "crash": 0, "fire": 0, "inj": 0, "death": 0})
    mmy_cmpl: dict[tuple[str, str, int], dict[str, Any]] = defaultdict(
        lambda: {"cmpl": 0, "crash": 0, "fire": 0, "inj": 0, "death": 0, "comps": Counter()}
    )
    comp_counts: Counter = Counter()

    for zp in cmpl_zips:
        with zipfile.ZipFile(zp) as zf:
            fn = zf.namelist()[0]
            with zf.open(fn) as raw:
                for line in io.TextIOWrapper(raw, encoding="latin-1", errors="replace"):
                    parts = line.rstrip("\r\n").split("\t")
                    if len(parts) < 18:
                        continue
                    cmpl_raw_rows += 1
                    odino = parts[1].strip()
                    if not odino:
                        continue
                    comp = parts[11].strip().upper().split(":")[0].strip()[:40]
                    make = norm_make(parts[3])
                    model = norm_model(parts[4])
                    yr = safe_int(parts[5])
                    if odino in seen_odino:
                        dup_odino += 1
                        # Still record secondary component for model-year profile without double counting incident
                        if make in MAJOR_BRANDS and model and 2010 <= yr <= 2026 and comp:
                            mmy_cmpl[(make, model, yr)]["comps"][comp] += 1
                        continue
                    seen_odino.add(odino)

                    crash = 1 if parts[6].strip().upper() == "Y" else 0
                    fire = 1 if parts[8].strip().upper() == "Y" else 0
                    inj = safe_int(parts[9])
                    death = safe_int(parts[10])
                    ldate = parts[16].strip() or parts[15].strip()
                    cyr = ldate[:4]

                    tot_cmpl += 1
                    tot_crash += crash
                    tot_fire += fire
                    tot_inj += inj
                    tot_death += death

                    if cyr.isdigit() and 2020 <= int(cyr) <= 2026:
                        d = cmpl_by_year[cyr]
                        d["cmpl"] += 1; d["crash"] += crash; d["fire"] += fire; d["inj"] += inj; d["death"] += death
                    if comp and comp != "UNKNOWN OR OTHER":
                        comp_counts[comp] += 1

                    if make in MAJOR_BRANDS:
                        b = brand_cmpl[make]
                        b["cmpl"] += 1; b["crash"] += crash; b["fire"] += fire; b["inj"] += inj; b["death"] += death
                        if model and 2010 <= yr <= 2026:
                            m = mmy_cmpl[(make, model, yr)]
                            m["cmpl"] += 1; m["crash"] += crash; m["fire"] += fire; m["inj"] += inj; m["death"] += death
                            if comp:
                                m["comps"][comp] += 1

    # ------------------------------------------------------------------
    # 3. Brand Scorecard (2016-2026 Vehicle Recalls + 2020-2026 Complaints)
    # ------------------------------------------------------------------
    brand_rcl: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"camps": 0, "units": 0, "odi": 0, "dnd": 0, "po": 0, "fire_camps": 0}
    )
    rcl_by_year: dict[int, dict[str, int]] = defaultdict(lambda: {"camps": 0, "units": 0, "odi": 0, "po_dnd": 0})
    critical_list: list[dict[str, Any]] = []

    tot_v_camps = 0
    tot_v_units = 0
    tot_odi = 0
    tot_dnd = 0
    tot_po = 0
    tot_fire_camps = 0

    for c in campaigns.values():
        tot_v_camps += 1
        tot_v_units += c["potaff"]
        if c["infl"] == "ODI":
            tot_odi += 1
        if c["dnd"]:
            tot_dnd += 1
        if c["po"]:
            tot_po += 1
        if c["fire_risk"]:
            tot_fire_camps += 1

        if 2010 <= c["rc_yr"] <= 2026:
            ry = rcl_by_year[c["rc_yr"]]
            ry["camps"] += 1
            ry["units"] += c["potaff"]
            if c["infl"] == "ODI":
                ry["odi"] += 1
            if c["dnd"] or c["po"]:
                ry["po_dnd"] += 1

        # Critical Do-Not-Drive / Park-Outside advisories (major brands or >=1,000 units)
        if c["dnd"] or c["po"]:
            major_makes = sorted(c["makes"] & MAJOR_BRANDS)
            all_makes = major_makes or sorted(c["makes"])[:3]
            yrs_sorted = sorted(c["years"])
            yr_span = f"{yrs_sorted[0]}–{yrs_sorted[-1]}" if len(yrs_sorted) > 1 else (str(yrs_sorted[0]) if yrs_sorted else "Various")
            critical_list.append({
                "camp": c["camp"],
                "rcdate": c["rcdate"],
                "brand": ", ".join(all_makes[:3]),
                "models": ", ".join(sorted(c["models"])[:5]) + (f" (+{len(c['models'])-5})" if len(c["models"]) > 5 else ""),
                "years": yr_span,
                "units": c["potaff"],
                "dnd": c["dnd"],
                "po": c["po"],
                "infl": c["infl"],
                "comp": c["comp"],
                "conseq": c["conseq"],
            })

        # Assign campaign to each major brand present (note: multi-brand campaigns like Takata appear under each affected brand; documented clearly)
        if 2016 <= c["rc_yr"] <= 2026:
            for mk in (c["makes"] & MAJOR_BRANDS):
                br = brand_rcl[mk]
                br["camps"] += 1
                br["units"] += c["potaff"]
                if c["infl"] == "ODI":
                    br["odi"] += 1
                if c["dnd"]:
                    br["dnd"] += 1
                if c["po"]:
                    br["po"] += 1
                if c["fire_risk"]:
                    br["fire_camps"] += 1

    critical_list.sort(key=lambda x: (-x["units"], x["rcdate"]), reverse=False)

    brand_scorecard = []
    for mk in sorted(MAJOR_BRANDS):
        br = brand_rcl[mk]
        bc = brand_cmpl[mk]
        if br["camps"] < 5 and bc["cmpl"] < 50:
            continue
        odi_pct = round(br["odi"] / br["camps"] * 100.0, 1) if br["camps"] else 0.0
        fire_per_1k = round(bc["fire"] / bc["cmpl"] * 1000.0, 1) if bc["cmpl"] else 0.0
        crash_per_1k = round(bc["crash"] / bc["cmpl"] * 1000.0, 1) if bc["cmpl"] else 0.0
        brand_scorecard.append({
            "brand": mk,
            "camps_16_26": br["camps"],
            "units_16_26": br["units"],
            "odi_camps": br["odi"],
            "odi_pct": odi_pct,
            "dnd_camps": br["dnd"],
            "po_camps": br["po"],
            "fire_camps": br["fire_camps"],
            "cmpl_20_26": bc["cmpl"],
            "crashes": bc["crash"],
            "fires": bc["fire"],
            "injured": bc["inj"],
            "deaths": bc["death"],
            "fire_per_1k": fire_per_1k,
            "crash_per_1k": crash_per_1k,
        })
    brand_scorecard.sort(key=lambda x: -x["cmpl_20_26"])

    # ------------------------------------------------------------------
    # 4. Model-Year Dossiers (MY 2010-2026) joining Recalls + Complaints
    # ------------------------------------------------------------------
    all_keys = set(mmy_recalls.keys()) | set(mmy_cmpl.keys())
    model_rows = []
    for key in all_keys:
        mk, mdl, yr = key
        r_set = mmy_recalls.get(key, set())
        o_set = mmy_odi.get(key, set())
        c_d = mmy_cmpl.get(key)
        cmpl_n = c_d["cmpl"] if c_d else 0
        # Keep every MY 2010-2026 vehicle with >= 15 complaints OR >= 4 recalls OR DND/PO flag
        if cmpl_n < 15 and len(r_set) < 4 and not mmy_dnd[key] and not mmy_po[key]:
            continue
        top_comp = ""
        if c_d and c_d["comps"]:
            top_comp = c_d["comps"].most_common(1)[0][0]
        elif mmy_rcl_comps[key]:
            top_comp = mmy_rcl_comps[key].most_common(1)[0][0]
        model_rows.append({
            "brand": mk,
            "model": mdl,
            "year": yr,
            "recalls": len(r_set),
            "odi_recalls": len(o_set),
            "dnd": 1 if mmy_dnd[key] else 0,
            "po": 1 if mmy_po[key] else 0,
            "cmpl": cmpl_n,
            "crashes": c_d["crash"] if c_d else 0,
            "fires": c_d["fire"] if c_d else 0,
            "injured": c_d["inj"] if c_d else 0,
            "deaths": c_d["death"] if c_d else 0,
            "top_comp": top_comp,
        })

    model_rows.sort(key=lambda x: (-x["cmpl"], -x["recalls"]))

    top_fire_models = sorted(model_rows, key=lambda x: (-x["fires"], -x["cmpl"]))[:15]
    top_cmpl_models = model_rows[:15]
    top_recall_models = sorted(model_rows, key=lambda x: (-x["recalls"], -x["cmpl"]))[:15]

    summary = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "recall_source": "NHTSA Office of Defects Investigation (ODI) Vehicle Recalls (2010–Nov 2026)",
            "complaint_source": "NHTSA Consumer Safety Complaints Received (2020–Nov 2026)",
            "source_url": "https://www.nhtsa.gov/nhtsa-datasets-and-apis",
        },
        "data_hygiene": {
            "raw_recall_rows": rcl_raw_rows,
            "unique_vehicle_campaigns": tot_v_camps,
            "raw_complaint_rows": cmpl_raw_rows,
            "duplicate_odino_rows_deduped": dup_odino,
            "unique_complaints": tot_cmpl,
        },
        "national": {
            "vehicle_campaigns_post2010": tot_v_camps,
            "total_units_recalled_m": round(tot_v_units / 1e6, 1),
            "odi_forced_campaigns": tot_odi,
            "odi_forced_pct": round(tot_odi / tot_v_camps * 100.0, 1) if tot_v_camps else 0.0,
            "dnd_campaigns": tot_dnd,
            "po_campaigns": tot_po,
            "fire_risk_campaigns": tot_fire_camps,
            "unique_complaints_20_26": tot_cmpl,
            "crashes_20_26": tot_crash,
            "fires_20_26": tot_fire,
            "injured_20_26": tot_inj,
            "deaths_20_26": tot_death,
            "models_indexed": len(model_rows),
            "brands_scored": len(brand_scorecard),
        },
        "brand_scorecard": brand_scorecard,
        "top_fire_models": top_fire_models,
        "top_cmpl_models": top_cmpl_models,
        "top_recall_models": top_recall_models,
        "top_components": [{"comp": k, "count": v} for k, v in comp_counts.most_common(12)],
        "critical_advisories_top25": critical_list[:25],
        "critical_advisories_total": len(critical_list),
        "cmpl_by_year": [{"year": yr, **d} for yr, d in sorted(cmpl_by_year.items())],
        "rcl_by_year": [{"year": str(yr), **d} for yr, d in sorted(rcl_by_year.items())],
    }

    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ROOT / "summary-data.js").write_text(
        "window.NHTSA_SUMMARY = " + json.dumps(summary, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    m_cols = ["brand", "model", "year", "recalls", "odi_recalls", "dnd", "po", "cmpl", "crashes", "fires", "injured", "deaths", "top_comp"]
    m_rows = [[r[c] for c in m_cols] for r in model_rows]
    (ROOT / "models.json").write_text(
        json.dumps({"cols": m_cols, "rows": m_rows}, separators=(",", ":")),
        encoding="utf-8",
    )

    (ROOT / "critical-advisories.json").write_text(
        json.dumps(critical_list, separators=(",", ":")),
        encoding="utf-8",
    )

    with gzip.open(ROOT / "nhtsa-models-2010-2026.csv.gz", "wt", encoding="utf-8", newline="") as gz:
        w = csv.writer(gz)
        w.writerow(m_cols)
        for r in model_rows:
            w.writerow([r[c] for c in m_cols])

    b_cols = list(brand_scorecard[0].keys()) if brand_scorecard else []
    with gzip.open(ROOT / "nhtsa-brands-2016-2026.csv.gz", "wt", encoding="utf-8", newline="") as gz:
        w = csv.writer(gz)
        w.writerow(b_cols)
        for r in brand_scorecard:
            w.writerow([r[c] for c in b_cols])

    print(f"\n=== NHTSA PIPELINE COMPLETE ===")
    print(f"Vehicle Campaigns (2010-2026): {tot_v_camps:,} | Units={tot_v_units/1e6:.1f}M | ODI-forced={tot_odi:,} ({summary['national']['odi_forced_pct']}%) | DND={tot_dnd} | Park-Outside={tot_po}")
    print(f"Complaints (2020-2026): {tot_cmpl:,} unique ({dup_odino:,} dup component rows deduped!) | Crashes={tot_crash:,} | Fires={tot_fire:,} | Injured={tot_inj:,} | Deaths={tot_death:,}")
    print(f"Models indexed (MY 2010-2026): {len(model_rows):,} | Brands scored: {len(brand_scorecard)} | Critical DND/PO advisories: {len(critical_list)}")
    print("\nTop 12 Brands by 2020-2026 Complaints:")
    for b in brand_scorecard[:12]:
        print(f"  {b['brand']:15s} | camps16-26={b['camps_16_26']:3d} (ODI={b['odi_camps']:2d}, PO={b['po_camps']:2d}, DND={b['dnd_camps']:2d}) | cmpl={b['cmpl_20_26']:6,} | crashes={b['crashes']:4,} | fires={b['fires']:4,} ({b['fire_per_1k']}/1k)")
    print("\nTop 10 Fire-Complaint Model-Years:")
    for m in top_fire_models[:10]:
        print(f"  {m['year']} {m['brand']} {m['model']:20s} | fires={m['fires']:3d} | crashes={m['crashes']:3d} | cmpl={m['cmpl']:4d} | recalls={m['recalls']:2d} | PO={m['po']} DND={m['dnd']}")


if __name__ == "__main__":
    main()
