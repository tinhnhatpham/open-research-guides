#!/usr/bin/env python3
"""
NOAA NCEI Storm Events 11-Year U.S. County & Hazard Risk Pipeline (2016-2026).

Downloads the latest creation-date StormEvents_details CSV.GZ for each year
2016 through 2026 directly from NOAA's public archive:
  https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/

Critical accounting & mapping safeguards built in:
  1. Picks ONLY the latest cYYYYMMDD creation file per year (never double-counts
     multiple revisions of the same year in NOAA's directory).
  2. Correctly parses NOAA's K/M/B/T damage suffix strings (e.g. '12.50K',
     '1.4B') for both DAMAGE_PROPERTY and DAMAGE_CROPS.
  3. Handles NOAA's CZ_TYPE='C' (County FIPS) vs CZ_TYPE='Z' (NWS Forecast
     Zone, used for hurricanes, wildfires, heat waves, and winter storms)
     explicitly: national, state, hazard, and year totals include ALL events
     (C + Z), while county-level lookup aggregates all County-FIPS rows plus
     exact-name 1:1 zone-to-county matches, transparently flagging zone-level
     hazards so wildfires/hurricanes are never silently dropped.
  4. Compares 2021-2025 vs 2016-2020 (two complete 5-year windows) for honest
     trend acceleration without partial-year 2026 distortion.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CURL_BIN = shutil.which("curl.exe") or shutil.which("curl") or "curl"
BASE_URL = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
CACHE_DIR = Path(
    os.environ.get("NOAA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "noaa_storms_cache"))
)

YEARS = list(range(2016, 2027))

STATE_ABBR = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
    "DISTRICT OF COLUMBIA": "DC", "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI",
    "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA",
    "KANSAS": "KS", "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME",
    "MARYLAND": "MD", "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN",
    "MISSISSIPPI": "MS", "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE",
    "NEVADA": "NV", "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM",
    "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH",
    "OKLAHOMA": "OK", "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX",
    "UTAH": "UT", "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY", "PUERTO RICO": "PR",
}


def bucket_hazard(ev: str) -> str:
    e = (ev or "").strip().lower()
    if "tornado" in e or "funnel" in e or "waterspout" in e:
        return "Tornado"
    if "hurricane" in e or "tropical" in e or "storm surge" in e:
        return "Hurricane & Tropical Storm"
    if "wildfire" in e:
        return "Wildfire"
    if "flood" in e or "debris flow" in e:
        return "Flood & Flash Flood"
    if "hail" in e:
        return "Hail"
    if "heat" in e:
        return "Extreme Heat"
    if any(k in e for k in ("winter", "blizzard", "ice storm", "heavy snow", "cold", "frost", "freeze", "sleet", "lake-effect", "avalanche")):
        return "Winter Storm & Extreme Cold"
    if any(k in e for k in ("wind", "dust", "lightning")):
        return "Severe Wind & Lightning"
    if "drought" in e:
        return "Drought"
    if any(k in e for k in ("rip current", "surf", "sneakerwave", "coastal", "tsunami", "marine")):
        return "Coastal & Rip Current"
    return "Other Weather"


def parse_dmg(v: str | None) -> float:
    if not v:
        return 0.0
    s = v.strip().upper().replace(",", "")
    if not s:
        return 0.0
    mult = 1.0
    if s.endswith("K"):
        mult = 1e3; s = s[:-1]
    elif s.endswith("M"):
        mult = 1e6; s = s[:-1]
    elif s.endswith("B"):
        mult = 1e9; s = s[:-1]
    elif s.endswith("T"):
        mult = 1e12; s = s[:-1]
    elif s.endswith("H"):
        mult = 1e2; s = s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return 0.0


def safe_int(v: str | None) -> int:
    try:
        return int(float(v or 0))
    except ValueError:
        return 0


def discover_latest_files() -> dict[int, str]:
    html = subprocess.check_output([CURL_BIN, "-sL", BASE_URL], text=True, errors="replace")
    found = re.findall(r'href="(StormEvents_details-ftp_v1\.0_d(\d{4})_c(\d{8})\.csv\.gz)"', html)
    latest: dict[int, tuple[str, str]] = {}
    for fname, yr_s, created in found:
        yr = int(yr_s)
        if yr in YEARS:
            if yr not in latest or created > latest[yr][0]:
                latest[yr] = (created, fname)
    return {yr: fn for yr, (_, fn) in sorted(latest.items())}


def fetch_gz(fname: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / fname
    if dst.exists() and dst.stat().st_size > 100_000:
        return dst
    tmp = dst.with_suffix(".tmp")
    code = subprocess.check_output(
        [CURL_BIN, "-sL", "-w", "%{http_code}", "-o", str(tmp), BASE_URL + fname], text=True
    ).strip()
    if code != "200" or not tmp.exists() or tmp.stat().st_size < 100_000:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed downloading {fname}: HTTP {code}")
    tmp.replace(dst)
    print(f"Downloaded {fname} ({dst.stat().st_size:,} bytes)")
    return dst


def main() -> None:
    files = discover_latest_files()
    print(f"Discovered {len(files)} latest annual NOAA files ({min(files)}–{max(files)})")

    tot_events = 0
    tot_prop = 0.0
    tot_crop = 0.0
    tot_deaths = 0
    tot_inj = 0

    by_year: dict[int, dict[str, Any]] = defaultdict(lambda: {"events": 0, "prop": 0.0, "crop": 0.0, "deaths": 0, "inj": 0})
    by_hazard: dict[str, dict[str, Any]] = defaultdict(lambda: {"events": 0, "prop": 0.0, "crop": 0.0, "deaths": 0, "inj": 0, "ev_16_20": 0, "ev_21_25": 0, "prop_16_20": 0.0, "prop_21_25": 0.0})
    by_state: dict[str, dict[str, Any]] = defaultdict(lambda: {"name": "", "events": 0, "prop": 0.0, "crop": 0.0, "deaths": 0, "inj": 0, "haz_prop": defaultdict(float), "haz_ev": Counter(), "prop_16_20": 0.0, "prop_21_25": 0.0})

    # Track county-level (CZ_TYPE == 'C') plus exact-name zone-to-county matching
    county_names_by_st: dict[tuple[str, str], str] = {}  # (st, NORM_NAME) -> fips5
    raw_county_rows: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "fips": "", "name": "", "state": "", "events": 0, "prop": 0.0, "crop": 0.0,
        "deaths": 0, "inj": 0, "hail_ev": 0, "tornado_ev": 0, "flood_ev": 0, "wind_ev": 0,
        "ev_16_20": 0, "ev_21_25": 0, "prop_16_20": 0.0, "prop_21_25": 0.0,
        "haz_prop": defaultdict(float), "haz_ev": Counter(),
    })
    zone_events_buffer: list[tuple[str, str, int, str, float, float, int, int]] = []

    for yr, fname in sorted(files.items()):
        gz_path = fetch_gz(fname)
        with gzip.open(gz_path, "rt", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                st_name = (row.get("STATE") or "").strip().upper()
                st = STATE_ABBR.get(st_name)
                if not st:
                    continue
                ev_type = (row.get("EVENT_TYPE") or "").strip()
                haz = bucket_hazard(ev_type)
                prop = parse_dmg(row.get("DAMAGE_PROPERTY"))
                crop = parse_dmg(row.get("DAMAGE_CROPS"))
                deaths = safe_int(row.get("DEATHS_DIRECT")) + safe_int(row.get("DEATHS_INDIRECT"))
                inj = safe_int(row.get("INJURIES_DIRECT")) + safe_int(row.get("INJURIES_INDIRECT"))

                tot_events += 1
                tot_prop += prop
                tot_crop += crop
                tot_deaths += deaths
                tot_inj += inj

                y = by_year[yr]
                y["events"] += 1; y["prop"] += prop; y["crop"] += crop; y["deaths"] += deaths; y["inj"] += inj

                h = by_hazard[haz]
                h["events"] += 1; h["prop"] += prop; h["crop"] += crop; h["deaths"] += deaths; h["inj"] += inj
                if 2016 <= yr <= 2020:
                    h["ev_16_20"] += 1; h["prop_16_20"] += prop
                elif 2021 <= yr <= 2025:
                    h["ev_21_25"] += 1; h["prop_21_25"] += prop

                s = by_state[st]
                s["name"] = st_name.title()
                s["events"] += 1; s["prop"] += prop; s["crop"] += crop; s["deaths"] += deaths; s["inj"] += inj
                s["haz_prop"][haz] += prop
                s["haz_ev"][haz] += 1
                if 2016 <= yr <= 2020:
                    s["prop_16_20"] += prop
                elif 2021 <= yr <= 2025:
                    s["prop_21_25"] += prop

                cz_type = (row.get("CZ_TYPE") or "").strip().upper()
                cz_name = (row.get("CZ_NAME") or "").strip()
                st_fips = (row.get("STATE_FIPS") or "").strip().zfill(2)
                cz_fips = (row.get("CZ_FIPS") or "").strip().zfill(3)

                if cz_type == "C" and st_fips.isdigit() and cz_fips.isdigit() and cz_fips != "000":
                    fips5 = st_fips + cz_fips
                    c = raw_county_rows[fips5]
                    c["fips"] = fips5
                    if not c["name"]:
                        c["name"] = cz_name.title()
                    c["state"] = st
                    c["events"] += 1; c["prop"] += prop; c["crop"] += crop; c["deaths"] += deaths; c["inj"] += inj
                    c["haz_prop"][haz] += prop
                    c["haz_ev"][haz] += 1
                    if haz == "Hail": c["hail_ev"] += 1
                    elif haz == "Tornado": c["tornado_ev"] += 1
                    elif haz == "Flood & Flash Flood": c["flood_ev"] += 1
                    elif haz == "Severe Wind & Lightning": c["wind_ev"] += 1
                    if 2016 <= yr <= 2020:
                        c["ev_16_20"] += 1; c["prop_16_20"] += prop
                    elif 2021 <= yr <= 2025:
                        c["ev_21_25"] += 1; c["prop_21_25"] += prop
                    norm_c = re.sub(r"\s+(?:COUNTY|PARISH|BOROUGH|CITY)$", "", cz_name.upper()).strip()
                    county_names_by_st[(st, norm_c)] = fips5
                elif cz_type == "Z" and cz_name:
                    zone_events_buffer.append((st, cz_name.upper(), yr, haz, prop, crop, deaths, inj))

    # Map 1:1 exact-name NWS Forecast Zones onto their matching County FIPS (captures many county-aligned Hurricane, Wildfire & Heat zones!)
    zone_matched = 0
    for st, zn, yr, haz, prop, crop, deaths, inj in zone_events_buffer:
        zn_clean = re.sub(r"\s+(?:COUNTY|PARISH|BOROUGH|INLAND|COASTAL|NORTHERN|SOUTHERN|EASTERN|WESTERN)$", "", zn).strip()
        fips5 = county_names_by_st.get((st, zn)) or county_names_by_st.get((st, zn_clean))
        if fips5 and fips5 in raw_county_rows:
            zone_matched += 1
            c = raw_county_rows[fips5]
            c["events"] += 1; c["prop"] += prop; c["crop"] += crop; c["deaths"] += deaths; c["inj"] += inj
            c["haz_prop"][haz] += prop
            c["haz_ev"][haz] += 1
            if 2016 <= yr <= 2020:
                c["ev_16_20"] += 1; c["prop_16_20"] += prop
            elif 2021 <= yr <= 2025:
                c["ev_21_25"] += 1; c["prop_21_25"] += prop

    # Build final county records + national property-damage percentiles
    counties = []
    for c in raw_county_rows.values():
        top_haz = ""
        if c["haz_prop"]:
            top_p = max(c["haz_prop"].items(), key=lambda kv: kv[1])
            top_haz = top_p[0] if top_p[1] > 0 else c["haz_ev"].most_common(1)[0][0]
        elif c["haz_ev"]:
            top_haz = c["haz_ev"].most_common(1)[0][0]
        ev_chg = round((c["ev_21_25"] / c["ev_16_20"] - 1.0) * 100.0, 1) if c["ev_16_20"] >= 10 else None
        counties.append({
            "fips": c["fips"],
            "county": c["name"],
            "state": c["state"],
            "events": c["events"],
            "prop_m": round(c["prop"] / 1e6, 2),
            "crop_m": round(c["crop"] / 1e6, 2),
            "deaths": c["deaths"],
            "inj": c["inj"],
            "hail": c["hail_ev"],
            "tornado": c["tornado_ev"],
            "flood": c["flood_ev"],
            "wind": c["wind_ev"],
            "ev_16_20": c["ev_16_20"],
            "ev_21_25": c["ev_21_25"],
            "ev_chg_pct": ev_chg,
            "top_haz": top_haz,
        })

    # Compute percentile rank on property damage
    by_prop = sorted(range(len(counties)), key=lambda i: counties[i]["prop_m"])
    n_c = max(1, len(counties) - 1)
    for rank, idx in enumerate(by_prop):
        counties[idx]["dmg_pctl"] = round(rank / n_c * 100.0, 1)

    counties.sort(key=lambda x: (-x["prop_m"], -x["events"]))

    # Hazard table
    hazards = []
    for hname, d in by_hazard.items():
        hazards.append({
            "hazard": hname,
            "events": d["events"],
            "prop_b": round(d["prop"] / 1e9, 2),
            "crop_b": round(d["crop"] / 1e9, 2),
            "deaths": d["deaths"],
            "inj": d["inj"],
            "ev_16_20": d["ev_16_20"],
            "ev_21_25": d["ev_21_25"],
            "prop_16_20_b": round(d["prop_16_20"] / 1e9, 2),
            "prop_21_25_b": round(d["prop_21_25"] / 1e9, 2),
        })
    hazards.sort(key=lambda x: -x["prop_b"])

    # State table
    states = []
    for st, d in sorted(by_state.items()):
        top_h = max(d["haz_prop"].items(), key=lambda kv: kv[1])[0] if d["haz_prop"] else ""
        states.append({
            "state": st,
            "name": d["name"],
            "events": d["events"],
            "prop_b": round(d["prop"] / 1e9, 2),
            "crop_b": round(d["crop"] / 1e9, 2),
            "deaths": d["deaths"],
            "inj": d["inj"],
            "prop_16_20_b": round(d["prop_16_20"] / 1e9, 2),
            "prop_21_25_b": round(d["prop_21_25"] / 1e9, 2),
            "top_haz": top_h,
        })
    states.sort(key=lambda x: -x["prop_b"])

    years_out = [
        {"year": yr, "events": d["events"], "prop_b": round(d["prop"] / 1e9, 2), "crop_b": round(d["crop"] / 1e9, 2), "deaths": d["deaths"], "inj": d["inj"]}
        for yr, d in sorted(by_year.items())
    ]

    ev_16_20_tot = sum(by_year[y]["events"] for y in range(2016, 2021))
    ev_21_25_tot = sum(by_year[y]["events"] for y in range(2021, 2026))
    prop_16_20_tot = sum(by_year[y]["prop"] for y in range(2016, 2021))
    prop_21_25_tot = sum(by_year[y]["prop"] for y in range(2021, 2026))

    summary = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "NOAA National Centers for Environmental Information (NCEI) Storm Events Database (2016–2026)",
            "source_url": BASE_URL,
            "years_covered": f"{min(files)}–{max(files)}",
        },
        "national": {
            "events": tot_events,
            "prop_b": round(tot_prop / 1e9, 2),
            "crop_b": round(tot_crop / 1e9, 2),
            "deaths": tot_deaths,
            "inj": tot_inj,
            "counties_mapped": len(counties),
            "zone_events_total": len(zone_events_buffer),
            "zone_events_matched_to_county": zone_matched,
            "ev_16_20": ev_16_20_tot,
            "ev_21_25": ev_21_25_tot,
            "ev_5yr_chg_pct": round((ev_21_25_tot / ev_16_20_tot - 1.0) * 100.0, 1) if ev_16_20_tot else 0.0,
            "prop_16_20_b": round(prop_16_20_tot / 1e9, 2),
            "prop_21_25_b": round(prop_21_25_tot / 1e9, 2),
        },
        "by_hazard": hazards,
        "by_state": states,
        "by_year": years_out,
        "top_15_counties": counties[:15],
        "deadliest_hazards": sorted(hazards, key=lambda x: -x["deaths"])[:8],
    }

    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ROOT / "summary-data.js").write_text(
        "window.NOAA_SUMMARY = " + json.dumps(summary, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    cols = ["fips", "county", "state", "events", "prop_m", "crop_m", "deaths", "inj", "hail", "tornado", "flood", "wind", "ev_16_20", "ev_21_25", "ev_chg_pct", "top_haz", "dmg_pctl"]
    rows = [[c[k] for k in cols] for c in counties]
    (ROOT / "counties.json").write_text(
        json.dumps({"cols": cols, "rows": rows}, separators=(",", ":")),
        encoding="utf-8",
    )

    with gzip.open(ROOT / "noaa-counties-2016-2026.csv.gz", "wt", encoding="utf-8", newline="") as gz:
        w = csv.writer(gz)
        w.writerow(cols)
        for c in counties:
            w.writerow([c[k] for k in cols])

    print(f"\n=== NOAA STORM EVENTS PIPELINE COMPLETE (2016-2026) ===")
    print(f"Total Events: {tot_events:,} | Property Damage: ${tot_prop/1e9:.2f}B | Crop: ${tot_crop/1e9:.2f}B | Deaths: {tot_deaths:,} | Injuries: {tot_inj:,}")
    print(f"5-Year Trend (2016-20 -> 2021-25): Events {ev_16_20_tot:,} -> {ev_21_25_tot:,} ({summary['national']['ev_5yr_chg_pct']:+.1f}%) | Prop ${prop_16_20_tot/1e9:.1f}B -> ${prop_21_25_tot/1e9:.1f}B")
    print(f"Counties mapped: {len(counties):,} (Zone events matched to exact county: {zone_matched:,}/{len(zone_events_buffer):,})")
    print("\nTOP HAZARDS BY PROPERTY DAMAGE:")
    for h in hazards[:8]:
        print(f"  {h['hazard']:28s}: ${h['prop_b']:6.2f}B prop | ${h['crop_b']:5.2f}B crop | deaths={h['deaths']:5,} | events={h['events']:7,}")
    print("\nTOP 10 STATES BY OBSERVED PROPERTY DAMAGE:")
    for s in states[:10]:
        print(f"  {s['name']:16s} ({s['state']}): ${s['prop_b']:6.2f}B | deaths={s['deaths']:4,} | #1={s['top_haz']}")


if __name__ == "__main__":
    main()
