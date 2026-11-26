"""
Reproducible Analysis: Global Road Traffic Mortality (2010–2021 Finalized WHO Data)
Primary Source: World Health Organization (WHO) Global Health Observatory (GHO) API
  - Indicator RS_198: Estimated road traffic death rate (per 100,000 population)
Metadata & Population: World Bank Open Data API (SP.POP.TOTL)

Why 2010 -> 2021 (and not 2022–2023)?
  - WHO's Global Status Report on Road Safety 2023 finalized empirical country estimates through 2021.
  - WHO GHO rows for 2022–2023 are forward model extrapolations with dramatically wider
    uncertainty intervals (for example, extrapolating the 2020–2021 U.S. pandemic spike up to
    18.4/100k in 2023, whereas actual NHTSA FARS deaths declined slightly to 40,901, or ~12.2/100k).
  - Using finalized 2010 -> 2021 WHO data (supplemented by IRTAD/NHTSA 2023–2024 actuals in prose)
    prevents misleading projection artifacts.

Run: python analyze_who_road_deaths.py
Outputs: summary.json
"""

import json
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
BASELINE_YEAR = 2010
FINALIZED_YEAR = 2021
MIN_POPULATION = 1_000_000


def fetch_json(url: str):
    with urllib.request.urlopen(url, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    # 1. Fetch WHO GHO RS_198 (both sexes aggregate: Dim1 == 'SEX_BTSX')
    gho_rows = fetch_json("https://ghoapi.azureedge.net/api/RS_198")["value"]

    by_country = {}
    ci_width_check = {}
    agg_regions = {}

    for r in gho_rows:
        if r.get("Dim1") != "SEX_BTSX":
            continue
        val = r.get("NumericValue")
        yr = r.get("TimeDim")
        dim_type = r.get("SpatialDimType")
        code = r.get("SpatialDim")
        if val is None or yr is None or not code:
            continue
        yr = int(yr)
        val = round(float(val), 2)
        if dim_type == "COUNTRY":
            by_country.setdefault(code, {})[yr] = val
            if code == "USA" and yr in (2021, 2022, 2023):
                ci_width_check[yr] = {
                    "val": val,
                    "low": r.get("Low"),
                    "high": r.get("High"),
                }
        elif dim_type in ("GLOBAL", "REGION", "WORLDBANKINCOMEGROUP"):
            agg_regions.setdefault(code, {})[yr] = val

    # 2. Fetch World Bank country metadata + 2021 population
    countries_raw = fetch_json(
        "https://api.worldbank.org/v2/country?format=json&per_page=400"
    )[1]
    meta = {
        c["id"]: {
            "name": c["name"],
            "region": c["region"]["value"],
            "income": c["incomeLevel"]["value"],
        }
        for c in countries_raw
        if c["region"]["id"] != "NA"
    }

    pop_raw = fetch_json(
        f"https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?date={FINALIZED_YEAR}&format=json&per_page=400"
    )[1]
    pop = {
        r["countryiso3code"]: int(r["value"])
        for r in pop_raw
        if r.get("countryiso3code") and r.get("value") is not None
    }

    # 3. Build eligible country dataset (pop >= 1M, finalized 2010 -> 2021)
    eligible = []
    for cid, series in by_country.items():
        if cid not in meta:
            continue
        if BASELINE_YEAR in series and FINALIZED_YEAR in series and pop.get(cid, 0) >= MIN_POPULATION:
            b = series[BASELINE_YEAR]
            l = series[FINALIZED_YEAR]
            if b > 0:
                pct = round((l - b) / b * 100, 1)
                abs_diff = round(l - b, 2)
                eligible.append(
                    {
                        "code": cid,
                        "name": meta[cid]["name"],
                        "region": meta[cid]["region"],
                        "income": meta[cid]["income"],
                        "population": pop[cid],
                        "baseline_rate": b,
                        "latest_rate": l,
                        "pct_change": pct,
                        "abs_change": abs_diff,
                        "series": {
                            str(y): series[y]
                            for y in range(BASELINE_YEAR, FINALIZED_YEAR + 1)
                            if y in series
                        },
                    }
                )

    eligible.sort(key=lambda x: x["pct_change"])
    by_code = {r["code"]: r for r in eligible}

    benchmark_codes = [
        "NOR", "SGP", "JPN", "SWE", "DNK", "GBR", "DEU", "ESP", "FRA",
        "LTU", "POL", "KOR", "AUS", "CAN", "OMN", "SAU", "USA", "BRA", "CHN", "IND", "VNM"
    ]
    benchmarks = [by_code[c] for c in benchmark_codes if c in by_code]

    # Regional/income aggregates trimmed to 2010..2021
    agg_clean = {}
    for code, s in agg_regions.items():
        if BASELINE_YEAR in s and FINALIZED_YEAR in s:
            agg_clean[code] = {
                "baseline_rate": s[BASELINE_YEAR],
                "latest_rate": s[FINALIZED_YEAR],
                "pct_change": round((s[FINALIZED_YEAR] - s[BASELINE_YEAR]) / s[BASELINE_YEAR] * 100, 1),
                "series": {str(y): s[y] for y in range(BASELINE_YEAR, FINALIZED_YEAR + 1) if y in s},
            }

    summary = {
        "source": "World Health Organization (WHO) Global Health Observatory — Indicator RS_198 (Estimated road traffic death rate per 100,000 population, finalized 2010–2021)",
        "baseline_year": BASELINE_YEAR,
        "latest_year": FINALIZED_YEAR,
        "eligible_country_count": len(eligible),
        "population_threshold": MIN_POPULATION,
        "usa_extrapolation_check": ci_width_check,
        "aggregates": agg_clean,
        "top_15_fastest_drops": eligible[:15],
        "safest_10_latest": sorted(eligible, key=lambda x: x["latest_rate"])[:10],
        "benchmarks": benchmarks,
        "all_countries": eligible,
    }

    out_path = OUT_DIR / "summary.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Also write browser-friendly JS module so Guide #02 works locally via file:// AND on Vercel!
    js_path = OUT_DIR / "summary-data.js"
    js_path.write_text(
        "window.TRAFFIC_SAFETY_DATA = " + json.dumps(summary, indent=2) + ";\n",
        encoding="utf-8",
    )

    print(f"Finalized WHO window: {BASELINE_YEAR} -> {FINALIZED_YEAR} | Eligible countries (pop >= 1M): {len(eligible)}")
    print("USA WHO GHO CI check (proving 2022-2023 extrapolation jump):", ci_width_check)

    print("\nGlobal, Regional & Income Aggregates (2010 -> 2021, per 100k):")
    for code in ["GLOBAL", "EUR", "WPR", "EMR", "AMR", "SEAR", "AFR", "WB_HI", "WB_UMI", "WB_LMI", "WB_LI"]:
        if code in agg_clean:
            a = agg_clean[code]
            print(f"  {code:8s}: {a['baseline_rate']:5.1f} -> {a['latest_rate']:5.1f} ({a['pct_change']:+5.1f}%)")

    print("\nTop 15 Fastest % Reductions (2010 -> 2021, pop >= 1M):")
    for r in eligible[:15]:
        print(
            f"  {r['name']:28s} ({r['code']}) | {r['baseline_rate']:5.1f} -> {r['latest_rate']:5.1f} | {r['pct_change']:+6.1f}% | {r['income']}"
        )

    print("\nSafest 10 Countries in 2021 (per 100k, pop >= 1M):")
    for r in summary["safest_10_latest"]:
        print(
            f"  {r['name']:28s} ({r['code']}) | {r['baseline_rate']:5.1f} -> {r['latest_rate']:5.1f} | {r['pct_change']:+6.1f}%"
        )

    print("\nKey Benchmarks (2010 -> 2021, sorted by 2021 rate):")
    for r in sorted(benchmarks, key=lambda x: x["latest_rate"]):
        print(
            f"  {r['name']:28s} ({r['code']}) | {r['baseline_rate']:5.1f} -> {r['latest_rate']:5.1f} | {r['pct_change']:+6.1f}%"
        )


if __name__ == "__main__":
    main()
