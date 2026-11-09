#!/usr/bin/env python3
"""
Standalone Mathematical, Spatial, and Provenance Verification Script for Task 2.
Recomputes and verifies:
  1. TomTom 2025 Dubai Traffic Index city-wide baseline (OBS-DXB-CITY-00 / SRC-436).
  2. Two-Term BPR Uninterrupted Link + HCM Bottleneck/Control Delay reproducibility across all 21 corridor observations.
  3. Official RTA source separation and wording precision (SRC-439 vs SRC-451; SRC-440 vs SRC-452).
  4. 37/37 nearest-vertex WGS84 Haversine distances (< 3.0 km), 37/37 GeoJSON LineString endpoints, and 37/37 4-component HGV sums.
  5. SQLite schema manifest (11_sqlite_schema_inspector) and master repository sync.
"""

import csv
import json
import math
import shutil
import sqlite3
from pathlib import Path

BASE_DIR = Path("/Users/siddiqahmed26/.gemini/antigravity/scratch/uae-construction-research")
DATASETS_DIR = BASE_DIR / "datasets"
CSV_DIR = BASE_DIR / "csv"
WEB_DIR = BASE_DIR / "web"
WEB_DATASETS_DIR = WEB_DIR / "datasets"
WEB_CSV_DIR = WEB_DIR / "csv"
WEB_CSV_RAW_DIR = WEB_DIR / "csv_raw"
WEB_CSV_VIEW_DIR = WEB_DIR / "csv_view"
WEB_SCRIPTS_DIR = WEB_DIR / "scripts"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def sync_schema_manifest():
    """Synchronize 11_sqlite_schema_inspector and 11_master_repository with the rebuilt SQLite databases."""
    schema_path = DATASETS_DIR / "11_sqlite_schema_inspector.json"
    rows = json.loads(schema_path.read_text(encoding="utf-8"))

    conn_main = sqlite3.connect(DATASETS_DIR / "11_consolidated_database.sqlite")
    conn_t2 = sqlite3.connect(DATASETS_DIR / "21_task2_spatial_database.sqlite")

    for r in rows:
        tname = r["table_name"]
        try:
            cnt = conn_main.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
            cols = conn_main.execute(f'PRAGMA table_info("{tname}")').fetchall()
        except Exception:
            cnt = conn_t2.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
            cols = conn_t2.execute(f'PRAGMA table_info("{tname}")').fetchall()
        r["row_count"] = cnt
        r["column_count"] = len(cols)
        r["columns_list"] = ", ".join(c[1] for c in cols)

    conn_main.close()
    conn_t2.close()

    for p in (DATASETS_DIR / "11_sqlite_schema_inspector.json", WEB_DATASETS_DIR / "11_sqlite_schema_inspector.json"):
        p.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    headers = list(rows[0].keys())
    for cp in (
        CSV_DIR / "11_sqlite_schema_inspector.csv",
        WEB_CSV_DIR / "11_sqlite_schema_inspector.csv",
        WEB_CSV_RAW_DIR / "11_sqlite_schema_inspector.csv.txt",
    ):
        with open(cp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            w.writerows(rows)

    # Update 11_master_repository.json provenance source register entry if present
    prov_rows = json.loads((DATASETS_DIR / "11_provenance_source_register.json").read_text(encoding="utf-8"))
    for mp in (DATASETS_DIR / "11_master_repository.json", WEB_DATASETS_DIR / "11_master_repository.json"):
        if mp.exists():
            mdata = json.loads(mp.read_text(encoding="utf-8"))
            if isinstance(mdata, dict):
                if "provenance_source_register" in mdata:
                    mdata["provenance_source_register"] = prov_rows
                if "sqlite_schema_inspector" in mdata:
                    mdata["sqlite_schema_inspector"] = rows
                mp.write_text(json.dumps(mdata, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    sync_schema_manifest()

    obs_rows = json.loads((DATASETS_DIR / "17_traffic_congestion_observations.json").read_text(encoding="utf-8"))
    roads_rows = json.loads((DATASETS_DIR / "16_road_network_dataset.json").read_text(encoding="utf-8"))
    links_rows = json.loads((DATASETS_DIR / "22_project_road_impact_links.json").read_text(encoding="utf-8"))
    prov_rows = json.loads((DATASETS_DIR / "11_provenance_source_register.json").read_text(encoding="utf-8"))
    geojson_data = json.loads((DATASETS_DIR / "dubai_sharjah_gis_bundle.geojson").read_text(encoding="utf-8"))

    prov_by_id = {r["source_id"]: r for r in prov_rows}
    roads_by_id = {r["road_id"]: r for r in roads_rows}

    # 1. Verify TomTom City-Wide Baseline (OBS-DXB-CITY-00)
    city_row = next(r for r in obs_rows if r["observation_id"] == "OBS-DXB-CITY-00")
    assert city_row["average_speed_kmh"] == 31.3, f"Expected 31.3, got {city_row['average_speed_kmh']}"
    assert city_row["travel_time_min_per_10km"] == 19.17, f"Expected 19.17, got {city_row['travel_time_min_per_10km']}"
    assert "19 min 10 sec" in city_row["travel_time_formatted"], "Missing 19 min 10 sec"
    assert city_row["tomtom_annual_congestion_pct"] == "42.7%", "Missing 42.7% annual congestion"
    assert city_row["tomtom_rush_hour_avg_speed_kmh"] == "26.3 km/h", "Missing 26.3 km/h rush-hour average"
    assert city_row["tomtom_morning_rush_speed_kmh"].startswith("32.1 km/h"), "Missing 32.1 km/h AM rush speed"
    assert city_row["tomtom_evening_rush_speed_kmh"].startswith("22.6 km/h"), "Missing 22.6 km/h PM rush speed"
    assert "65" not in str(city_row["free_flow_speed_kmh"]), "Unsupported 65 km/h free-flow speed retained"

    # 2. Verify Two-Term BPR + Bottleneck Delay Reproducibility on All 21 Corridor Rows
    corridor_rows = [r for r in obs_rows if r["observation_id"] != "OBS-DXB-CITY-00"]
    assert len(corridor_rows) == 21, f"Expected 21 corridor rows, got {len(corridor_rows)}"

    bpr_audit_table = []
    for r in corridor_rows:
        oid = r["observation_id"]
        v0 = float(r["free_flow_speed_kmh"])
        v_dem = float(r["modelled_demand_vph_dir"])
        c_ref = float(r["reference_capacity_vph_dir"])
        alpha = float(r["bpr_alpha"])
        beta = float(r["bpr_beta"])
        d_adj = float(r["bottleneck_and_control_delay_min_per_10km"])

        t0_calc = round(600.0 / v0, 2)
        vc_calc = round(v_dem / c_ref, 2)
        t_bpr_calc = round((600.0 / v0) * (1.0 + alpha * ((v_dem / c_ref) ** beta)), 2)
        v_bpr_calc = round(v0 / (1.0 + alpha * ((v_dem / c_ref) ** beta)), 1)
        t_tot_calc = round(t_bpr_calc + d_adj, 2)
        v_corr_calc = round(600.0 / t_tot_calc, 1)

        assert t0_calc == r["free_flow_time_min_per_10km"], f"{oid}: t0 mismatch {t0_calc} != {r['free_flow_time_min_per_10km']}"
        assert vc_calc == r["vc_ratio"], f"{oid}: vc mismatch {vc_calc} != {r['vc_ratio']}"
        assert t_bpr_calc == r["bpr_uninterrupted_time_min_per_10km"], f"{oid}: t_bpr mismatch {t_bpr_calc} != {r['bpr_uninterrupted_time_min_per_10km']}"
        assert v_bpr_calc == r["bpr_uninterrupted_speed_kmh"], f"{oid}: v_bpr mismatch {v_bpr_calc} != {r['bpr_uninterrupted_speed_kmh']}"
        assert t_tot_calc == r["travel_time_min_per_10km"], f"{oid}: t_tot mismatch {t_tot_calc} != {r['travel_time_min_per_10km']}"
        assert v_corr_calc == r["average_speed_kmh"], f"{oid}: v_corr mismatch {v_corr_calc} != {r['average_speed_kmh']}"

        bpr_audit_table.append({
            "observation_id": oid,
            "road_id": r["road_id"],
            "v0_kmh": v0,
            "V_vph_dir": v_dem,
            "C_vph_dir": c_ref,
            "vc_ratio": vc_calc,
            "t_bpr_min_10km": t_bpr_calc,
            "v_bpr_kmh": v_bpr_calc,
            "d_adj_min_10km": d_adj,
            "t_total_min_10km": t_tot_calc,
            "v_corridor_kmh": v_corr_calc,
        })

    # 3. Verify SRC-439 / SRC-451 and SRC-440 / SRC-452 Provenance Separation
    assert prov_by_id["SRC-439"]["original_url"] == "https://www.rta.ae/wps/portal/rta/ae/home/news-and-media/all-news/NewsDetails/opening-of-phase-i-of-sheikh-rashid-bin-saeed-corridor-project"
    assert prov_by_id["SRC-451"]["original_url"] == "https://www.rta.ae/wps/portal/rta/ae/home/news-and-media/all-news/NewsDetails/rta-awards-aed-20-5-billion-contract-for-dubai-metro-blue-line-project"
    assert prov_by_id["SRC-440"]["original_url"] == "https://www.rta.ae/wps/portal/rta/ae/home/news-and-media/AllProjects/ongoing-project-details/70+of+umm+suqeim+street+improvement+project"
    assert prov_by_id["SRC-452"]["original_url"] == "https://www.rta.ae/wps/portal/rta/ae/home/news-and-media/all-news/NewsDetails/hamdan-bin-mohammed-reviews-progress-of-key-strategic-road-corridors"

    # Check that no Ras Al Khor / SRC-439 record has "10,000 vph/dir"
    rak_records = (
        [r for r in roads_rows if r["road_id"] == "RD-DXB-11"]
        + [r for r in obs_rows if r["road_id"] == "RD-DXB-11"]
        + [r for r in links_rows if r["primary_road_id"] == "RD-DXB-11"]
        + [prov_by_id["SRC-439"], prov_by_id["SRC-451"]]
    )
    rak_text = json.dumps(rak_records)
    assert "10,000 vph/dir" not in rak_text, "Found '10,000 vph/dir' in Ras Al Khor / SRC-439 records!"

    # 4. Verify 37/37 Nearest-Vertex Haversine Distances, GeoJSON Endpoints & HGV Sums
    impact_features = {
        f["properties"]["link_id"]: f
        for f in geojson_data["features"]
        if "link_id" in f.get("properties", {})
    }
    assert len(links_rows) == 37 and len(impact_features) == 37

    for l in links_rows:
        lid = l["link_id"]
        plat_str, plon_str = [x.strip() for x in l["project_coordinates"].split(",")]
        plat, plon = float(plat_str), float(plon_str)
        road = roads_by_id[l["primary_road_id"]]
        best_d = min(haversine_km(plat, plon, float(v[1]), float(v[0])) for v in road["geometry_wgs84"])
        assert round(best_d, 2) == l["distance_to_primary_road_km"], f"{lid}: distance mismatch"
        assert l["distance_to_primary_road_km"] < 3.0, f"{lid}: distance >= 3.0 km"

        # GeoJSON LineString endpoint match
        coords = impact_features[lid]["geometry"]["coordinates"]
        assert round(coords[0][1], 4) == round(plat, 4) and round(coords[0][0], 4) == round(plon, 4)
        assert round(coords[1][1], 4) == round(float(l["nearest_road_vertex_lat"]), 4)
        assert round(coords[1][0], 4) == round(float(l["nearest_road_vertex_lon"]), 4)

        # HGV 4-component sum
        comp_sum = round(
            float(l["concrete_mixer_loads_day"])
            + float(l["rebar_trailer_loads_day"])
            + float(l["earthworks_tipper_loads_day"])
            + float(l["mep_fitout_truck_loads_day"]),
            2,
        )
        assert abs(comp_sum - float(l["total_hgv_round_trips_day"])) <= 0.02, f"{lid}: HGV sum mismatch"

    # Copy scripts to web/scripts/
    WEB_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    for sname in (
        "build_task2_spatial_and_traffic_datasets.py",
        "build_task2_gis_platform.py",
        "verify_task2_math_and_provenance.py",
    ):
        src_p = BASE_DIR / "scripts" / sname
        if src_p.exists():
            shutil.copy2(src_p, WEB_SCRIPTS_DIR / sname)

    receipt = {
        "verification_timestamp": "2026-11-09T13:12:00+05:30",
        "status": "ALL_CHECKS_PASSED",
        "tomtom_city_baseline_check": {
            "observation_id": "OBS-DXB-CITY-00",
            "source_id": "SRC-436",
            "average_speed_kmh": city_row["average_speed_kmh"],
            "travel_time_min_per_10km": city_row["travel_time_min_per_10km"],
            "travel_time_formatted": city_row["travel_time_formatted"],
            "annual_congestion_pct": city_row["tomtom_annual_congestion_pct"],
            "rush_hour_avg_speed_kmh": city_row["tomtom_rush_hour_avg_speed_kmh"],
            "morning_rush_speed_kmh": city_row["tomtom_morning_rush_speed_kmh"],
            "evening_rush_speed_kmh": city_row["tomtom_evening_rush_speed_kmh"],
            "free_flow_speed_kmh": city_row["free_flow_speed_kmh"],
        },
        "two_term_bpr_and_bottleneck_delay_check": {
            "corridor_rows_verified": "21/21",
            "max_speed_discrepancy_kmh": 0.0,
            "max_time_discrepancy_min_per_10km": 0.0,
            "rows": bpr_audit_table,
        },
        "official_source_separation_check": {
            "SRC-439": prov_by_id["SRC-439"]["original_url"],
            "SRC-451": prov_by_id["SRC-451"]["original_url"],
            "SRC-440": prov_by_id["SRC-440"]["original_url"],
            "SRC-452": prov_by_id["SRC-452"]["original_url"],
            "zero_occurrence_of_10000_vph_per_dir": True,
        },
        "spatial_and_hgv_checks": {
            "nearest_vertex_haversine_37_of_37": True,
            "geojson_linestring_endpoints_37_of_37": True,
            "hgv_four_component_sum_37_of_37": True,
        },
        "provenance_sources_total": len(prov_rows),
    }

    for rp in (DATASETS_DIR / "task2_verification_receipt.json", WEB_DATASETS_DIR / "task2_verification_receipt.json"):
        rp.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    print("ALL MATHEMATICAL, SPATIAL & PROVENANCE CHECKS PASSED!")
    print(f"TomTom City Baseline: {city_row['average_speed_kmh']} km/h | {city_row['travel_time_formatted']} | {city_row['tomtom_annual_congestion_pct']} congestion")
    print(f"Two-Term BPR + Bottleneck Delay Reproducibility: {len(bpr_audit_table)}/21 rows passed with 0.00 discrepancy")
    print(f"Provenance Sources: {len(prov_rows)} (SRC-439/451 & SRC-440/452 verified)")
    print("Spatial & HGV Checks: 37/37 Haversine, 37/37 GeoJSON endpoints, 37/37 HGV sums passed")


if __name__ == "__main__":
    main()
