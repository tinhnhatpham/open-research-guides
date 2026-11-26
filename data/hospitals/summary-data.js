window.CMS_HOSPITAL_DATA = {
  "metadata": {
    "generated_at_utc": "2026-11-26T20:06:13Z",
    "runtime_sec": 6.1,
    "endpoints": {
      "cost_report": {
        "title": "Hospital Provider Cost Report : 2024-01-02",
        "uuid": "44060663-47d8-4ced-a115-b53b4c270acb",
        "url": "https://data.cms.gov/data-api/v1/dataset/44060663-47d8-4ced-a115-b53b4c270acb/data",
        "resolved_dynamically": "true"
      },
      "enrollments": {
        "title": "Hospital Enrollments : 2026-11-01",
        "uuid": "f6f6505c-e8b0-4d57-b258-e2b94133aaf2",
        "url": "https://data.cms.gov/data-api/v1/dataset/f6f6505c-e8b0-4d57-b258-e2b94133aaf2/data",
        "resolved_dynamically": "true"
      },
      "owners": {
        "title": "Hospital All Owners : 2026-11-01",
        "uuid": "029c119f-f79c-49be-9100-344d31d10344",
        "url": "https://data.cms.gov/data-api/v1/dataset/029c119f-f79c-49be-9100-344d31d10344/data",
        "resolved_dynamically": "true"
      }
    },
    "total_hospitals": 5435,
    "matched_cost_reports": 5171,
    "full_year_cost_reports": 5078,
    "acute_cah_s10_count": 4040
  },
  "by_ownership": [
    {
      "ownership": "Non-Profit",
      "total_hospitals": 2952,
      "s10_acute_count": 2579,
      "avg_stars": 3.32,
      "median_charity_pct": 1.53,
      "weighted_charity_pct": 2.1,
      "median_bad_debt_pct": 0.98,
      "median_uncomp_pct": 2.79,
      "median_markup": 3.84,
      "median_op_mgn": -1.0,
      "median_net_mgn": 6.1,
      "pct_charity_under_1": 31.7,
      "pct_charity_under_2": 60.3,
      "total_charity_billions": 21.48,
      "total_bad_debt_billions": 7.68
    },
    {
      "ownership": "For-Profit",
      "total_hospitals": 1144,
      "s10_acute_count": 618,
      "avg_stars": 2.81,
      "median_charity_pct": 2.16,
      "weighted_charity_pct": 4.21,
      "median_bad_debt_pct": 0.82,
      "median_uncomp_pct": 3.73,
      "median_markup": 6.4,
      "median_op_mgn": 6.4,
      "median_net_mgn": 9.6,
      "pct_charity_under_1": 30.9,
      "pct_charity_under_2": 47.9,
      "total_charity_billions": 5.06,
      "total_bad_debt_billions": 1.03
    },
    {
      "ownership": "Government",
      "total_hospitals": 1339,
      "s10_acute_count": 843,
      "avg_stars": 3.17,
      "median_charity_pct": 0.98,
      "weighted_charity_pct": 3.74,
      "median_bad_debt_pct": 1.92,
      "median_uncomp_pct": 3.55,
      "median_markup": 2.12,
      "median_op_mgn": -8.7,
      "median_net_mgn": 3.8,
      "pct_charity_under_1": 50.3,
      "pct_charity_under_2": 67.3,
      "total_charity_billions": 8.72,
      "total_bad_debt_billions": 3.29
    }
  ],
  "nonprofit_charity_tiers": {
    "total_np_s10": 2579,
    "under_1pct": 818,
    "1_to_2pct": 736,
    "2_to_4pct": 581,
    "4pct_plus": 444,
    "high_margin_low_charity_count": 408
  },
  "markup_stats": {
    "count": 4299,
    "median_markup": 3.74,
    "over_5x_count": 1324,
    "over_5x_pct": 30.8,
    "over_10x_count": 266,
    "fp_median_markup": 6.4,
    "np_median_markup": 3.84,
    "gov_median_markup": 2.12
  },
  "pecos_audit": {
    "matched_hospitals": 5154,
    "match_pct": 94.8,
    "total_owner_rows": 147029,
    "pe_hospitals": 5,
    "reit_hospitals": 1,
    "pe_rows_total": 176,
    "pe_rows_blank_org": 0,
    "reit_rows_total": 6,
    "reit_rows_blank_org": 0,
    "chain_home_office_hospitals": 988
  },
  "by_state": [
    {
      "state": "HI",
      "total_hospitals": 23,
      "np_s10_count": 8,
      "np_median_charity_pct": 0.29,
      "np_pct_under_1": 62.5,
      "median_markup": 2.44,
      "median_net_mgn": 9.8
    },
    {
      "state": "ME",
      "total_hospitals": 36,
      "np_s10_count": 25,
      "np_median_charity_pct": 0.48,
      "np_pct_under_1": 84.0,
      "median_markup": 2.53,
      "median_net_mgn": 3.6
    },
    {
      "state": "VT",
      "total_hospitals": 17,
      "np_s10_count": 13,
      "np_median_charity_pct": 0.63,
      "np_pct_under_1": 61.5,
      "median_markup": 2.47,
      "median_net_mgn": 3.2
    },
    {
      "state": "ND",
      "total_hospitals": 47,
      "np_s10_count": 38,
      "np_median_charity_pct": 0.64,
      "np_pct_under_1": 57.9,
      "median_markup": 1.41,
      "median_net_mgn": 1.1
    },
    {
      "state": "MA",
      "total_hospitals": 85,
      "np_s10_count": 45,
      "np_median_charity_pct": 0.67,
      "np_pct_under_1": 73.3,
      "median_markup": 2.68,
      "median_net_mgn": 2.5
    },
    {
      "state": "SD",
      "total_hospitals": 61,
      "np_s10_count": 43,
      "np_median_charity_pct": 0.7,
      "np_pct_under_1": 74.4,
      "median_markup": 2.45,
      "median_net_mgn": 8.7
    },
    {
      "state": "WV",
      "total_hospitals": 55,
      "np_s10_count": 31,
      "np_median_charity_pct": 0.7,
      "np_pct_under_1": 71.0,
      "median_markup": 3.02,
      "median_net_mgn": 5.0
    },
    {
      "state": "IA",
      "total_hospitals": 118,
      "np_s10_count": 64,
      "np_median_charity_pct": 0.81,
      "np_pct_under_1": 62.5,
      "median_markup": 1.98,
      "median_net_mgn": 9.9
    },
    {
      "state": "NY",
      "total_hospitals": 193,
      "np_s10_count": 129,
      "np_median_charity_pct": 0.92,
      "np_pct_under_1": 54.3,
      "median_markup": 3.03,
      "median_net_mgn": 2.8
    },
    {
      "state": "WI",
      "total_hospitals": 143,
      "np_s10_count": 111,
      "np_median_charity_pct": 0.95,
      "np_pct_under_1": 50.5,
      "median_markup": 3.04,
      "median_net_mgn": 9.1
    },
    {
      "state": "MI",
      "total_hospitals": 150,
      "np_s10_count": 93,
      "np_median_charity_pct": 1.01,
      "np_pct_under_1": 49.5,
      "median_markup": 3.4,
      "median_net_mgn": 6.9
    },
    {
      "state": "ID",
      "total_hospitals": 49,
      "np_s10_count": 20,
      "np_median_charity_pct": 1.04,
      "np_pct_under_1": 50.0,
      "median_markup": 1.92,
      "median_net_mgn": 3.1
    },
    {
      "state": "MT",
      "total_hospitals": 63,
      "np_s10_count": 45,
      "np_median_charity_pct": 1.07,
      "np_pct_under_1": 44.4,
      "median_markup": 1.43,
      "median_net_mgn": 2.1
    },
    {
      "state": "PA",
      "total_hospitals": 188,
      "np_s10_count": 124,
      "np_median_charity_pct": 1.1,
      "np_pct_under_1": 43.5,
      "median_markup": 5.1,
      "median_net_mgn": 7.2
    },
    {
      "state": "RI",
      "total_hospitals": 13,
      "np_s10_count": 7,
      "np_median_charity_pct": 1.1,
      "np_pct_under_1": 42.9,
      "median_markup": 3.58,
      "median_net_mgn": 3.8
    },
    {
      "state": "MN",
      "total_hospitals": 136,
      "np_s10_count": 88,
      "np_median_charity_pct": 1.16,
      "np_pct_under_1": 46.6,
      "median_markup": 2.1,
      "median_net_mgn": 4.9
    },
    {
      "state": "NE",
      "total_hospitals": 93,
      "np_s10_count": 44,
      "np_median_charity_pct": 1.18,
      "np_pct_under_1": 47.7,
      "median_markup": 1.55,
      "median_net_mgn": 6.2
    },
    {
      "state": "CA",
      "total_hospitals": 378,
      "np_s10_count": 174,
      "np_median_charity_pct": 1.19,
      "np_pct_under_1": 32.8,
      "median_markup": 4.8,
      "median_net_mgn": 3.8
    },
    {
      "state": "CT",
      "total_hospitals": 36,
      "np_s10_count": 21,
      "np_median_charity_pct": 1.19,
      "np_pct_under_1": 38.1,
      "median_markup": 3.8,
      "median_net_mgn": 2.2
    },
    {
      "state": "KY",
      "total_hospitals": 103,
      "np_s10_count": 59,
      "np_median_charity_pct": 1.23,
      "np_pct_under_1": 33.9,
      "median_markup": 3.95,
      "median_net_mgn": 14.0
    },
    {
      "state": "NH",
      "total_hospitals": 27,
      "np_s10_count": 23,
      "np_median_charity_pct": 1.25,
      "np_pct_under_1": 30.4,
      "median_markup": 3.2,
      "median_net_mgn": 11.9
    },
    {
      "state": "KS",
      "total_hospitals": 139,
      "np_s10_count": 47,
      "np_median_charity_pct": 1.29,
      "np_pct_under_1": 42.6,
      "median_markup": 1.77,
      "median_net_mgn": -0.2
    },
    {
      "state": "DC",
      "total_hospitals": 11,
      "np_s10_count": 3,
      "np_median_charity_pct": 1.3,
      "np_pct_under_1": 0.0,
      "median_markup": 3.94,
      "median_net_mgn": 6.8
    },
    {
      "state": "IL",
      "total_hospitals": 193,
      "np_s10_count": 122,
      "np_median_charity_pct": 1.49,
      "np_pct_under_1": 25.4,
      "median_markup": 4.12,
      "median_net_mgn": 6.3
    },
    {
      "state": "IN",
      "total_hospitals": 145,
      "np_s10_count": 70,
      "np_median_charity_pct": 1.5,
      "np_pct_under_1": 25.7,
      "median_markup": 4.56,
      "median_net_mgn": 7.0
    },
    {
      "state": "OH",
      "total_hospitals": 193,
      "np_s10_count": 125,
      "np_median_charity_pct": 1.53,
      "np_pct_under_1": 28.8,
      "median_markup": 4.4,
      "median_net_mgn": 6.6
    },
    {
      "state": "AZ",
      "total_hospitals": 108,
      "np_s10_count": 42,
      "np_median_charity_pct": 1.59,
      "np_pct_under_1": 31.0,
      "median_markup": 5.55,
      "median_net_mgn": 10.4
    },
    {
      "state": "AK",
      "total_hospitals": 25,
      "np_s10_count": 7,
      "np_median_charity_pct": 1.6,
      "np_pct_under_1": 28.6,
      "median_markup": 1.88,
      "median_net_mgn": 7.8
    },
    {
      "state": "DE",
      "total_hospitals": 13,
      "np_s10_count": 6,
      "np_median_charity_pct": 1.84,
      "np_pct_under_1": 16.7,
      "median_markup": 3.73,
      "median_net_mgn": 7.3
    },
    {
      "state": "MD",
      "total_hospitals": 56,
      "np_s10_count": 28,
      "np_median_charity_pct": 1.84,
      "np_pct_under_1": 28.6,
      "median_markup": 1.44,
      "median_net_mgn": 3.6
    },
    {
      "state": "LA",
      "total_hospitals": 162,
      "np_s10_count": 39,
      "np_median_charity_pct": 1.86,
      "np_pct_under_1": 17.9,
      "median_markup": 3.79,
      "median_net_mgn": 6.5
    },
    {
      "state": "MO",
      "total_hospitals": 119,
      "np_s10_count": 58,
      "np_median_charity_pct": 1.99,
      "np_pct_under_1": 20.7,
      "median_markup": 3.84,
      "median_net_mgn": 3.4
    },
    {
      "state": "WY",
      "total_hospitals": 31,
      "np_s10_count": 2,
      "np_median_charity_pct": 2.06,
      "np_pct_under_1": 0.0,
      "median_markup": 1.73,
      "median_net_mgn": -0.3
    },
    {
      "state": "CO",
      "total_hospitals": 96,
      "np_s10_count": 49,
      "np_median_charity_pct": 2.07,
      "np_pct_under_1": 12.2,
      "median_markup": 3.76,
      "median_net_mgn": 3.5
    },
    {
      "state": "VA",
      "total_hospitals": 98,
      "np_s10_count": 52,
      "np_median_charity_pct": 2.1,
      "np_pct_under_1": 21.2,
      "median_markup": 4.48,
      "median_net_mgn": 9.9
    },
    {
      "state": "NM",
      "total_hospitals": 45,
      "np_s10_count": 17,
      "np_median_charity_pct": 2.13,
      "np_pct_under_1": 29.4,
      "median_markup": 3.42,
      "median_net_mgn": 17.0
    },
    {
      "state": "WA",
      "total_hospitals": 101,
      "np_s10_count": 41,
      "np_median_charity_pct": 2.17,
      "np_pct_under_1": 2.4,
      "median_markup": 3.15,
      "median_net_mgn": 3.3
    },
    {
      "state": "NV",
      "total_hospitals": 46,
      "np_s10_count": 14,
      "np_median_charity_pct": 2.29,
      "np_pct_under_1": 14.3,
      "median_markup": 5.47,
      "median_net_mgn": 11.7
    },
    {
      "state": "OR",
      "total_hospitals": 62,
      "np_s10_count": 42,
      "np_median_charity_pct": 2.39,
      "np_pct_under_1": 9.5,
      "median_markup": 2.65,
      "median_net_mgn": 0.9
    },
    {
      "state": "AR",
      "total_hospitals": 90,
      "np_s10_count": 48,
      "np_median_charity_pct": 2.54,
      "np_pct_under_1": 20.8,
      "median_markup": 3.49,
      "median_net_mgn": 1.5
    },
    {
      "state": "NC",
      "total_hospitals": 121,
      "np_s10_count": 59,
      "np_median_charity_pct": 2.59,
      "np_pct_under_1": 6.8,
      "median_markup": 4.19,
      "median_net_mgn": 9.6
    },
    {
      "state": "NJ",
      "total_hospitals": 79,
      "np_s10_count": 53,
      "np_median_charity_pct": 2.76,
      "np_pct_under_1": 3.8,
      "median_markup": 5.72,
      "median_net_mgn": 3.0
    },
    {
      "state": "UT",
      "total_hospitals": 52,
      "np_s10_count": 29,
      "np_median_charity_pct": 2.93,
      "np_pct_under_1": 13.8,
      "median_markup": 3.73,
      "median_net_mgn": 14.2
    },
    {
      "state": "SC",
      "total_hospitals": 66,
      "np_s10_count": 33,
      "np_median_charity_pct": 3.23,
      "np_pct_under_1": 3.0,
      "median_markup": 5.23,
      "median_net_mgn": 10.4
    },
    {
      "state": "MS",
      "total_hospitals": 109,
      "np_s10_count": 32,
      "np_median_charity_pct": 3.27,
      "np_pct_under_1": 15.6,
      "median_markup": 2.91,
      "median_net_mgn": 3.2
    },
    {
      "state": "OK",
      "total_hospitals": 135,
      "np_s10_count": 40,
      "np_median_charity_pct": 3.38,
      "np_pct_under_1": 15.0,
      "median_markup": 3.8,
      "median_net_mgn": 2.9
    },
    {
      "state": "TN",
      "total_hospitals": 121,
      "np_s10_count": 39,
      "np_median_charity_pct": 3.92,
      "np_pct_under_1": 7.7,
      "median_markup": 5.16,
      "median_net_mgn": 5.0
    },
    {
      "state": "FL",
      "total_hospitals": 223,
      "np_s10_count": 79,
      "np_median_charity_pct": 4.23,
      "np_pct_under_1": 5.1,
      "median_markup": 7.05,
      "median_net_mgn": 11.0
    },
    {
      "state": "AL",
      "total_hospitals": 99,
      "np_s10_count": 19,
      "np_median_charity_pct": 5.13,
      "np_pct_under_1": 10.5,
      "median_markup": 4.12,
      "median_net_mgn": 1.2
    },
    {
      "state": "GA",
      "total_hospitals": 148,
      "np_s10_count": 52,
      "np_median_charity_pct": 6.28,
      "np_pct_under_1": 3.8,
      "median_markup": 4.83,
      "median_net_mgn": 9.2
    },
    {
      "state": "TX",
      "total_hospitals": 470,
      "np_s10_count": 127,
      "np_median_charity_pct": 7.74,
      "np_pct_under_1": 1.6,
      "median_markup": 4.99,
      "median_net_mgn": 9.0
    }
  ],
  "spotlight_low_charity_high_margin_np": [
    {
      "ccn": "050424",
      "name": "SCRIPPS GREEN HOSPITAL",
      "city": "LA JOLLA",
      "state": "CA",
      "stars": 5,
      "op_exp": 389395981,
      "charity_cost": 350780,
      "charity_pct": 0.09,
      "bad_debt": 274964,
      "net_inc": 98618084,
      "net_mgn": 20.2,
      "markup": 6.72
    },
    {
      "ccn": "050394",
      "name": "COMMUNITY MEMORIAL HOSPITAL - VENTURA",
      "city": "VENTURA",
      "state": "CA",
      "stars": 4,
      "op_exp": 593437320,
      "charity_cost": 517331,
      "charity_pct": 0.09,
      "bad_debt": 625379,
      "net_inc": 35210240,
      "net_mgn": 5.6,
      "markup": 3.64
    },
    {
      "ccn": "470001",
      "name": "CENTRAL VERMONT MEDICAL CENTER",
      "city": "BARRE",
      "state": "VT",
      "stars": 3,
      "op_exp": 311060188,
      "charity_cost": 516907,
      "charity_pct": 0.17,
      "bad_debt": 1741814,
      "net_inc": 59592094,
      "net_mgn": 16.1,
      "markup": 2.57
    },
    {
      "ccn": "520008",
      "name": "WAUKESHA MEMORIAL HOSPITAL",
      "city": "WAUKESHA",
      "state": "WI",
      "stars": 4,
      "op_exp": 551101304,
      "charity_cost": 1243468,
      "charity_pct": 0.23,
      "bad_debt": 3619985,
      "net_inc": 88182087,
      "net_mgn": 13.8,
      "markup": 4.63
    },
    {
      "ccn": "050441",
      "name": "STANFORD HEALTH CARE",
      "city": "STANFORD",
      "state": "CA",
      "stars": 5,
      "op_exp": 7919137656,
      "charity_cost": 19595987,
      "charity_pct": 0.25,
      "bad_debt": 6219969,
      "net_inc": 1212361140,
      "net_mgn": 13.3,
      "markup": 7.25
    },
    {
      "ccn": "330162",
      "name": "NORTHERN WESTCHESTER HOSPITAL",
      "city": "MOUNT KISCO",
      "state": "NY",
      "stars": 5,
      "op_exp": 512457328,
      "charity_cost": 1259752,
      "charity_pct": 0.25,
      "bad_debt": 189406,
      "net_inc": 77745121,
      "net_mgn": 13.2,
      "markup": 3.94
    },
    {
      "ccn": "190004",
      "name": "THIBODAUX REGIONAL MEDICAL CENTER",
      "city": "THIBODAUX",
      "state": "LA",
      "stars": 3,
      "op_exp": 278787625,
      "charity_cost": 701371,
      "charity_pct": 0.25,
      "bad_debt": 2240435,
      "net_inc": 51271857,
      "net_mgn": 15.1,
      "markup": 6.71
    },
    {
      "ccn": "150023",
      "name": "UNION HOSPITAL INC",
      "city": "TERRE HAUTE",
      "state": "IN",
      "stars": 3,
      "op_exp": 628885246,
      "charity_cost": 1672653,
      "charity_pct": 0.27,
      "bad_debt": 6180965,
      "net_inc": 99144342,
      "net_mgn": 13.6,
      "markup": 4.73
    },
    {
      "ccn": "390145",
      "name": "EXCELA HEALTH WESTMORELAND REGIONAL HOSPITAL",
      "city": "GREENSBURG",
      "state": "PA",
      "stars": 3,
      "op_exp": 295426848,
      "charity_cost": 819531,
      "charity_pct": 0.28,
      "bad_debt": 3848147,
      "net_inc": 32053042,
      "net_mgn": 9.8,
      "markup": 3.24
    },
    {
      "ccn": "120001",
      "name": "THE QUEENS MEDICAL CENTER",
      "city": "HONOLULU",
      "state": "HI",
      "stars": 3,
      "op_exp": 1641814774,
      "charity_cost": 4712725,
      "charity_pct": 0.29,
      "bad_debt": 7862442,
      "net_inc": 246105389,
      "net_mgn": 13.0,
      "markup": 4.47
    },
    {
      "ccn": "030062",
      "name": "SUMMIT HEALTHCARE REGIONAL MEDICAL CENTER",
      "city": "SHOW LOW",
      "state": "AZ",
      "stars": 4,
      "op_exp": 283861957,
      "charity_cost": 860583,
      "charity_pct": 0.3,
      "bad_debt": 2096834,
      "net_inc": 18905605,
      "net_mgn": 6.2,
      "markup": 5.61
    },
    {
      "ccn": "340039",
      "name": "IREDELL MEMORIAL HOSPITAL INC",
      "city": "STATESVILLE",
      "state": "NC",
      "stars": 3,
      "op_exp": 253828836,
      "charity_cost": 798146,
      "charity_pct": 0.31,
      "bad_debt": 4112871,
      "net_inc": 31395939,
      "net_mgn": 11.0,
      "markup": 5.6
    },
    {
      "ccn": "430077",
      "name": "MONUMENT HEALTH RAPID CITY HOSPITAL",
      "city": "RAPID CITY",
      "state": "SD",
      "stars": 3,
      "op_exp": 959218702,
      "charity_cost": 3112272,
      "charity_pct": 0.32,
      "bad_debt": 17805102,
      "net_inc": 83952169,
      "net_mgn": 8.0,
      "markup": 3.98
    },
    {
      "ccn": "390090",
      "name": "WEST PENN HOSPITAL",
      "city": "PITTSBURGH",
      "state": "PA",
      "stars": 3,
      "op_exp": 798068373,
      "charity_cost": 2622233,
      "charity_pct": 0.33,
      "bad_debt": 1864746,
      "net_inc": 223383185,
      "net_mgn": 21.9,
      "markup": 4.84
    },
    {
      "ccn": "200024",
      "name": "CENTRAL MAINE MEDICAL CENTER",
      "city": "LEWISTON",
      "state": "ME",
      "stars": 4,
      "op_exp": 517339534,
      "charity_cost": 1722877,
      "charity_pct": 0.33,
      "bad_debt": 7377630,
      "net_inc": 40017737,
      "net_mgn": 7.2,
      "markup": 3.25
    }
  ],
  "spotlight_highest_markup": [
    {
      "ccn": "010040",
      "name": "GADSDEN REGIONAL MEDICAL CENTER",
      "city": "GADSDEN",
      "state": "AL",
      "own": "For-Profit",
      "stars": 2,
      "op_exp": 163681071,
      "markup": 22.69,
      "charity_pct": 4.27,
      "net_mgn": 10.0
    },
    {
      "ccn": "310044",
      "name": "CAPITAL HEALTH MEDICAL CENTER - HOPEWELL",
      "city": "PENNINGTON",
      "state": "NJ",
      "own": "Non-Profit",
      "stars": 2,
      "op_exp": 802669090,
      "markup": 22.02,
      "charity_pct": 2.84,
      "net_mgn": 0.3
    },
    {
      "ccn": "310092",
      "name": "CAPITAL HEALTH REGIONAL MEDICAL CENTER",
      "city": "TRENTON",
      "state": "NJ",
      "own": "Non-Profit",
      "stars": 2,
      "op_exp": 446764306,
      "markup": 21.94,
      "charity_pct": 11.51,
      "net_mgn": 0.5
    },
    {
      "ccn": "450119",
      "name": "SOUTH TEXAS HEALTH SYSTEM",
      "city": "EDINBURG",
      "state": "TX",
      "own": "For-Profit",
      "stars": 4,
      "op_exp": 667860910,
      "markup": 21.61,
      "charity_pct": 6.67,
      "net_mgn": 15.0
    },
    {
      "ccn": "670078",
      "name": "BAPTIST NEIGHBORHOOD HOSPITAL THOUSAND OAKS",
      "city": "SAN ANTONIO",
      "state": "TX",
      "own": "For-Profit",
      "stars": 5,
      "op_exp": 105394872,
      "markup": 21.26,
      "charity_pct": null,
      "net_mgn": 36.6
    },
    {
      "ccn": "100264",
      "name": "HCA FLORIDA OAK HILL HOSPITAL",
      "city": "BROOKSVILLE",
      "state": "FL",
      "own": "For-Profit",
      "stars": 1,
      "op_exp": 234678065,
      "markup": 19.94,
      "charity_pct": 6.4,
      "net_mgn": 40.8
    },
    {
      "ccn": "450033",
      "name": "VHS HARLINGEN HOSPITAL COMPANY LLC",
      "city": "HARLINGEN",
      "state": "TX",
      "own": "For-Profit",
      "stars": 2,
      "op_exp": 386853685,
      "markup": 19.92,
      "charity_pct": 7.23,
      "net_mgn": 19.4
    },
    {
      "ccn": "290057",
      "name": "HENDERSON HOSPITAL",
      "city": "HENDERSON",
      "state": "NV",
      "own": "For-Profit",
      "stars": 2,
      "op_exp": 323039728,
      "markup": 19.69,
      "charity_pct": 2.74,
      "net_mgn": 27.3
    },
    {
      "ccn": "100226",
      "name": "HCA FLORIDA ORANGE PARK HOSPITAL",
      "city": "ORANGE PARK",
      "state": "FL",
      "own": "Non-Profit",
      "stars": 3,
      "op_exp": 361849451,
      "markup": 19.66,
      "charity_pct": 8.31,
      "net_mgn": 28.9
    },
    {
      "ccn": "100191",
      "name": "HCA FLORIDA TRINITY HOSPITAL",
      "city": "TRINITY",
      "state": "FL",
      "own": "For-Profit",
      "stars": 2,
      "op_exp": 300555220,
      "markup": 19.54,
      "charity_pct": 6.44,
      "net_mgn": 22.4
    },
    {
      "ccn": "100023",
      "name": "HCA FLORIDA CITRUS HOSPITAL",
      "city": "INVERNESS",
      "state": "FL",
      "own": "Government",
      "stars": 2,
      "op_exp": 242247034,
      "markup": 19.14,
      "charity_pct": 3.77,
      "net_mgn": 9.8
    },
    {
      "ccn": "450662",
      "name": "VALLEY REGIONAL MEDICAL CENTER",
      "city": "BROWNSVILLE",
      "state": "TX",
      "own": "For-Profit",
      "stars": 2,
      "op_exp": 133176731,
      "markup": 18.88,
      "charity_pct": 13.94,
      "net_mgn": 45.4
    },
    {
      "ccn": "060065",
      "name": "HCA HEALTHONE MOUNTAIN RIDGE",
      "city": "THORNTON",
      "state": "CO",
      "own": "Non-Profit",
      "stars": 3,
      "op_exp": 193021759,
      "markup": 18.76,
      "charity_pct": 13.39,
      "net_mgn": 13.5
    },
    {
      "ccn": "010104",
      "name": "GRANDVIEW MEDICAL CENTER",
      "city": "BIRMINGHAM",
      "state": "AL",
      "own": "For-Profit",
      "stars": 3,
      "op_exp": 611091623,
      "markup": 18.6,
      "charity_pct": 1.63,
      "net_mgn": 13.2
    },
    {
      "ccn": "100223",
      "name": "HCA FLORIDA FORT WALTON-DESTIN HOSPITAL",
      "city": "FORT WALTON BEACH",
      "state": "FL",
      "own": "For-Profit",
      "stars": 3,
      "op_exp": 227172115,
      "markup": 18.53,
      "charity_pct": 10.96,
      "net_mgn": 42.2
    }
  ]
};
