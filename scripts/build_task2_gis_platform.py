#!/usr/bin/env python3
"""
Builds the Task 2 Interactive Geographic Visualization, Construction Activity & Traffic Impact Intelligence
Platform (web/task2_gis_intelligence.html) and updates the main portal (web/index.html) with a prominent
top banner linking Task 1 and Task 2 seamlessly.
"""
import html
import json
import re
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DATASETS_DIR = BASE_DIR / "datasets"
WEB_DIR = BASE_DIR / "web" if (BASE_DIR / "web").is_dir() else BASE_DIR
ARTIFACT_DIR = Path(os.environ["AGY_ARTIFACT_DIR"]) if "AGY_ARTIFACT_DIR" in os.environ else None


def render_table_html(rows: list, cols: list) -> str:
    if not rows:
        return "<p>No records.</p>"
    out = ['<div class="t2-table-wrap"><table class="t2-table"><thead><tr>']
    for _, hdr in cols:
        out.append(f"<th>{html.escape(hdr)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for k, hdr in cols:
            v = r.get(k, "")
            s = json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else str(v)
            esc = html.escape(s)
            if s.startswith("http://") or s.startswith("https://"):
                lbl = re.sub(r"^https?://(www\.)?", "", s)[:38]
                cell = f'<a href="{esc}" target="_blank" rel="noopener">{html.escape(lbl)} ↗</a>'
            elif "Tier 4" in s or "CONFIRMED" in s:
                cell = f'<span class="ep-badge ep-t4">{esc}</span>'
            elif "Tier 3" in s or "MODELLED" in s:
                cell = f'<span class="ep-badge ep-t3">{esc}</span>'
            elif "Tier 2" in s or "SPATIAL" in s:
                cell = f'<span class="ep-badge ep-t2">{esc}</span>'
            elif "Tier 1" in s or "Observed" in s:
                cell = f'<span class="ep-badge ep-t1">{esc}</span>'
            elif s in ("Verified", "Corroborated", "Estimated"):
                cls = "b-ver" if s == "Verified" else ("b-cor" if s == "Corroborated" else "b-est")
                cell = f'<span class="conf-pill {cls}">{esc}</span>'
            else:
                cell = esc
            out.append(f'<td data-label="{html.escape(hdr)}">{cell}</td>')
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def load_ds(stem: str):
    return json.loads((DATASETS_DIR / f"{stem}.json").read_text(encoding="utf-8"))


def build_data_payload():
    projs_all = load_ds("04_project_inventory")
    projs_dxb_shj = [p for p in projs_all if p["emirate"] in ("Dubai", "Sharjah")]
    docs_all = load_ds("05_project_documents")
    facs_all = [f for f in load_ds("09b_nearby_facilities_dataset") if f["emirate"] in ("Dubai", "Sharjah")]
    sources_all = load_ds("11_provenance_source_register")

    tds = load_ds("15_transport_open_data_register")
    roads = load_ds("16_road_network_dataset")
    obs = load_ds("17_traffic_congestion_observations")
    providers = load_ds("18_tomtom_and_provider_assessment")
    tis = load_ds("19_traffic_impact_studies_and_logistics")
    parking = load_ds("20_parking_and_mobility_facilities")
    communities = load_ds("21a_communities_and_hotspots")
    intersections = load_ds("21b_intersections_and_nodes")
    incidents = load_ds("21c_traffic_incidents_and_roadworks")
    subdevs = load_ds("21d_jvc_and_community_subdevelopments")
    impact_links = load_ds("22_project_road_impact_links")

    # Transit lines & stations for Layer 8 (Transport Infrastructure)
    transit_lines = [
        {
            "transit_id": "TRN-RED",
            "line_name": "Dubai Metro Red Line & Route 2020 (Operational)",
            "emirate": "Dubai",
            "status": "Operational (35 Stations — Centrepoint to Expo 2020 / JAE)",
            "daily_ridership": "485,000+ daily riders [Observed RTA Rail Agency]",
            "color": "#ef4444",
            "coords": [[55.3910, 25.2300], [55.3350, 25.2520], [55.2798, 25.2215], [55.2620, 25.1970], [55.2285, 25.1585], [55.1405, 25.0765], [55.1508, 24.9602]],
            "stations": [
                {"name": "Centrepoint (Rashidiya) Park & Ride", "lat": 25.2300, "lon": 55.3910},
                {"name": "Burj Khalifa / Dubai Mall Station", "lat": 25.2014, "lon": 55.2695},
                {"name": "Business Bay Metro Station", "lat": 25.1913, "lon": 55.2602},
                {"name": "Mall of the Emirates Station (Hessa Feeder Bus)", "lat": 25.1180, "lon": 55.1995},
                {"name": "Sobha Realty (Dubai Marina) Station", "lat": 25.0802, "lon": 55.1402},
                {"name": "Expo 2020 Metro Station", "lat": 24.9602, "lon": 55.1508}
            ]
        },
        {
            "transit_id": "TRN-BLUE",
            "line_name": "Dubai Metro Blue Line (PRJ-D8 — AED 18B Under Construction, 2029 Completion)",
            "emirate": "Dubai",
            "status": "Under Construction (30 km, 14 Stations — Creek Harbour, Festival City, Ras Al Khor, Silicon Oasis, Academic City)",
            "daily_ridership": "320,000 forecast daily riders by 2040 [Published RTA Design Capacity]",
            "color": "#3b82f6",
            "coords": [[55.3910, 25.2300], [55.3520, 25.2220], [55.3460, 25.2048], [55.3480, 25.1895], [55.3920, 25.1680], [55.3850, 25.1250], [55.4120, 25.1150]],
            "stations": [
                {"name": "Dubai Creek Harbour Iconic Station (Emaar Creek Tower)", "lat": 25.2048, "lon": 55.3460},
                {"name": "Ras Al Khor Industrial / Nad Al Hamar Station", "lat": 25.1895, "lon": 55.3480},
                {"name": "International City Underground Interchange", "lat": 25.1680, "lon": 55.3920},
                {"name": "Dubai Silicon Oasis Station", "lat": 25.1250, "lon": 55.3850}
            ]
        },
        {
            "transit_id": "TRN-ETIHAD",
            "line_name": "Etihad Rail National Freight & Passenger Corridor (Dubai South – Sharjah AlBadiyah)",
            "emirate": "Dubai / Sharjah",
            "status": "Freight Operational; Passenger Stations at Jumeirah Golf Estates & Sharjah University City in Development",
            "daily_ridership": "60M tonnes/yr freight capacity + 36.5M annual passenger target by 2030",
            "color": "#f59e0b",
            "coords": [[55.1350, 24.8850], [55.2050, 24.9850], [55.2650, 25.0450], [55.4850, 25.2850], [55.5580, 25.3180]],
            "stations": [
                {"name": "Dubai South / DWC Freight & Logistics Rail Terminal", "lat": 24.8850, "lon": 55.1350},
                {"name": "Sharjah University City / Aljada Etihad Rail Passenger Station", "lat": 25.3180, "lon": 55.4850}
            ]
        }
    ]

    return {
        "projects": projs_dxb_shj,
        "documents": docs_all,
        "facilities": facs_all,
        "sources": {s["source_id"]: s for s in sources_all},
        "tds": tds,
        "roads": roads,
        "observations": obs,
        "providers": providers,
        "tis": tis,
        "parking": parking,
        "communities": communities,
        "intersections": intersections,
        "incidents": incidents,
        "subdevs": subdevs,
        "impact_links": impact_links,
        "transit_lines": transit_lines,
    }


def main():
    payload = build_data_payload()
    payload_json = json.dumps(payload, ensure_ascii=False)

    # Render complete Milestone 1–6 HTML Evidence Tables for bottom tabs
    tbl_tds = render_table_html(payload["tds"], [
        ("dataset_id", "ID"), ("dataset_name", "Dataset Name"), ("publishing_authority", "Publishing Authority"),
        ("geographic_coverage", "Coverage"), ("data_format", "Format"), ("update_frequency", "Update Freq"),
        ("api_availability", "API Availability"), ("access_restrictions", "Access Restrictions"),
        ("licensing_conditions", "Licensing"), ("coordinate_reference_system", "CRS"),
        ("historical_data_availability", "Historical Availability"), ("suitability_for_prototype", "Prototype Suitability"),
        ("original_url", "Verified URL"), ("confidence", "Confidence")
    ])
    tbl_roads = render_table_html(payload["roads"], [
        ("road_id", "Road ID"), ("road_code", "Code"), ("road_name", "Road Name"), ("emirate", "Emirate"),
        ("road_type", "Road Class"), ("authority", "Authority"), ("speed_limit_kmh", "Published Speed Limit"),
        ("lanes_per_direction", "Lanes/Dir"), ("capacity_vph_per_dir", "Capacity (vph/dir)"),
        ("capacity_basis", "Published vs. HCM Basis"), ("hgv_truck_ban_window", "HGV Truck Ban Schedule"),
        ("salik_toll_status", "Salik Dynamic Toll Status"), ("geometry_source_and_validation", "Polyline Geometry Source & Validation"),
        ("served_communities", "Served Communities"), ("source_id", "Source ID"), ("confidence", "Confidence")
    ])
    tbl_obs = render_table_html(payload["observations"], [
        ("observation_id", "Obs ID"), ("road_id", "Road / City Scope"), ("road_name", "Corridor / Benchmark Scope"), ("community", "Community"),
        ("location", "Geographic Coverage / Coordinates"), ("measurement_period", "Measurement / Scenario Period"),
        ("time_period", "Time Period"), ("average_speed_kmh", "Corridor Speed (km/h)"), ("travel_time_min_per_10km", "Total Time (min/10km)"),
        ("free_flow_speed_kmh", "Free-Flow v0 (km/h)"), ("free_flow_time_min_per_10km", "t0 (min/10km)"),
        ("modelled_demand_vph_dir", "Demand V (vph/dir)"), ("reference_capacity_vph_dir", "Ref Cap C (vph/dir)"), ("vc_ratio", "V/C Ratio"),
        ("bpr_uninterrupted_time_min_per_10km", "t_BPR (min/10km)"), ("bpr_uninterrupted_speed_kmh", "v_BPR (km/h)"),
        ("bottleneck_and_control_delay_min_per_10km", "+d_adj (min/10km)"), ("bottleneck_delay_parameters", "Bottleneck / Control Delay Model"),
        ("congestion_level", "Congestion Level"), ("evidence_level", "Evidence Classification"),
        ("officially_published_corridor_benchmark", "Officially Published RTA/SRTA/TomTom Benchmark"),
        ("modelled_assumptions_and_derivation", "Complete Two-Term BPR + Bottleneck Delay Derivation"),
        ("comparison_period", "2024 vs. 2026 Comparison"),
        ("source_report_title", "Substantiating Report Title"), ("source_url", "Report URL"),
        ("publication_date", "Pub Date"), ("source_id", "Source ID"), ("confidence", "Confidence")
    ])
    tbl_intersections = render_table_html(payload["intersections"], [
        ("intersection_id", "ID"), ("intersection_name", "Intersection / Interchange"), ("emirate", "Emirate"),
        ("community", "Community"), ("intersection_type", "Type"), ("connected_road_ids", "Connected Roads"),
        ("peak_level_of_service", "Modelled Peak LOS"), ("rta_upgrade_and_mitigation", "Officially Published RTA/SRTA Upgrade"),
        ("served_project_ids", "Served Projects"), ("source_id", "Source ID"), ("confidence", "Confidence")
    ])
    tbl_incidents = render_table_html(payload["incidents"], [
        ("incident_id", "ID"), ("road_id", "Road ID"), ("road_name", "Road Corridor"), ("emirate", "Emirate"),
        ("community", "Community"), ("incident_category", "Category"), ("active_period", "Active Window"),
        ("speed_and_capacity_impact", "Speed & Capacity Impact"), ("epistemic_tier", "Epistemic Tier"),
        ("source_id", "Source ID"), ("confidence", "Confidence")
    ])
    tbl_subdevs = render_table_html(payload["subdevs"], [
        ("subdev_id", "Cluster ID"), ("development_name", "Sub-Development Cluster"), ("developer", "Developer"),
        ("community_district", "District"), ("linked_task1_ref", "Task 1 Link"), ("building_count", "Towers"),
        ("floors_range", "Floors"), ("total_units", "Total Units"), ("active_gfa_sqm", "Active GFA (m²)"),
        ("primary_access_road_id", "Access Road"), ("nearest_road_vertex_wgs84", "Nearest Road Vertex (WGS84)"),
        ("distance_to_road_km", "Haversine Dist (km)"),
        ("estimated_midday_hgv_trips_per_day", "Scenario-Based Modelled HGV Trips/Day"),
        ("hgv_modelling_assumptions_and_sensitivity", "HGV Scenario Assumptions & Sensitivity"),
        ("epistemic_impact_tier", "Epistemic Tier"),
        ("source_id", "Source ID"), ("confidence", "Confidence")
    ])
    tbl_providers = render_table_html(payload["providers"], [
        ("provider_id", "ID"), ("provider_name", "Provider / API"), ("service_tier_evaluated", "Service Tier"),
        ("dubai_and_uae_coverage", "Dubai & UAE Coverage"), ("live_vs_historical_capability", "Live vs. Historical"),
        ("update_frequency", "Update Freq"), ("api_rate_limits", "API Limits"), ("pricing_structure", "Pricing"),
        ("commercial_usage_and_retention_terms", "Caching & Retention Terms"), ("prototype_recommendation", "Assessment Verdict"),
        ("official_url", "URL"), ("confidence", "Confidence")
    ])
    tbl_impacts = render_table_html(payload["impact_links"], [
        ("link_id", "Link ID"), ("project_id", "Project ID"), ("project_name", "Project / Development"),
        ("emirate", "Emirate"), ("community", "Community"), ("project_coordinates", "Project Coords (WGS84)"),
        ("primary_road_id", "Road ID"), ("primary_road_name", "Connected Road"),
        ("nearest_road_vertex_wgs84", "Nearest Road Vertex (WGS84)"),
        ("distance_to_primary_road_km", "Haversine Dist (km)"),
        ("geometry_validation_method", "Geometry Validation Method"),
        ("published_road_capacity_and_upgrade_fact", "Officially Published Road Capacity Benchmark"),
        ("observed_road_traffic_condition", "Modelled Corridor Traffic Estimate"),
        ("concrete_mixer_loads_day", "Mixers/d"), ("rebar_trailer_loads_day", "Rebar/d"),
        ("earthworks_tipper_loads_day", "Tippers/d"), ("mep_fitout_truck_loads_day", "MEP/d"),
        ("total_hgv_round_trips_day", "Est. HGV Round-Trips/d"),
        ("modelled_daily_hgv_concrete_rebar_trips", "Scenario-Based 4-Component HGV Equation"),
        ("hgv_modelling_assumptions_and_sensitivity", "HGV Modelling Assumptions & Peak Multiplier"),
        ("evidence_level", "Evidence Level"),
        ("epistemic_impact_classification", "Epistemic Classification"),
        ("source_id", "Source IDs"), ("corridor_source_url", "Corridor Source URL"), ("confidence", "Confidence")
    ])
    tbl_tis = render_table_html(payload["tis"], [
        ("tis_id", "TIS ID"), ("project_or_corridor", "Project / Corridor Assessed"), ("emirate", "Emirate"),
        ("study_publisher", "Publisher"), ("study_date", "Date"), ("study_type_and_availability", "Availability Status"),
        ("traffic_assumptions_and_trip_rates", "Trip Generation Rates & Assumptions"), ("road_network_assessed", "Road Network Assessed"),
        ("forecast_traffic_volumes", "Forecast Volumes & Capacity"), ("proposed_mitigation_and_logistics", "Mitigation & Construction Logistics"),
        ("supporting_document_url", "URL"), ("confidence", "Confidence")
    ])
    tbl_parking = render_table_html(payload["parking"], [
        ("parking_id", "ID"), ("facility_name", "Parking / Mobility Facility"), ("emirate", "Emirate"),
        ("community", "Community"), ("facility_category", "Category"), ("capacity_bays", "Capacity & Bays"),
        ("statutory_requirement_or_tariff", "Statutory Rule / Tariff"), ("occupancy_and_congestion_impact", "Occupancy & Congestion Impact"),
        ("operator_and_source", "Operator"), ("source_url", "URL"), ("confidence", "Confidence")
    ])
    tbl_communities = render_table_html(payload["communities"], [
        ("community_id", "ID"), ("community_name", "Community / Hotspot"), ("emirate", "Emirate"),
        ("active_developments_count", "Active Devs"), ("active_towers_and_buildings", "Active Towers"),
        ("scheduled_units_2025_2029", "Scheduled Units"), ("active_structural_gfa_sqm", "Active GFA (m²)"),
        ("primary_road_corridors", "Connected Roads"), ("observed_congestion_severity", "Observed Congestion"),
        ("construction_activity_index_score", "Hotspot Index"), ("activity_index_formula_and_limitations", "Formula & Limitations"), ("confidence", "Confidence")
    ])

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"/>
  <meta http-equiv="Pragma" content="no-cache"/>
  <meta http-equiv="Expires" content="0"/>
  <title>UAE Construction &amp; Traffic Intelligence — Executive GIS Platform</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🗺️</text></svg>"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
  <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" crossorigin=""/>
  <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js" crossorigin=""></script>
  <script src="https://unpkg.com/three@0.160.0/build/three.min.js" crossorigin=""></script>
  <style>
    :root {{
      --bg-dark: #f8fafc;
      --panel-dark: #ffffff;
      --panel-card: #ffffff;
      --border: #e2e8f0;
      --text: #0f172a;
      --muted: #64748b;
      --cyan: #2563eb;
      --emerald: #10b981;
      --amber: #f59e0b;
      --orange: #f97316;
      --rose: #ef4444;
      --purple: #7c3aed;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Inter", "Plus Jakarta Sans", "Segoe UI", Roboto, sans-serif;
      background: #f1f5f9;
      color: #0f172a;
      line-height: 1.45;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }}
    a {{ color: #2563eb; text-decoration: none; font-weight: 600; }}
    a:hover {{ text-decoration: underline; }}

    /* 1. HAIO-STYLE ULTRA-CLEAN WHITE TOP NAVBAR (60px) */
    .exec-header {{
      background: #ffffff;
      border-bottom: 1px solid #e2e8f0;
      padding: 0 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      position: relative;
      z-index: 2500;
      min-height: 58px;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }}
    .brand-cluster {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: nowrap;
      min-width: 0;
    }}
    .brand-title {{
      font-weight: 800;
      font-size: 1.12rem;
      letter-spacing: -0.025em;
      color: #0f172a;
      display: flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
      cursor: pointer;
    }}
    .haio-logo-pin {{
      width: 28px;
      height: 28px;
      border-radius: 9px;
      background: #2563eb;
      color: #ffffff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 0.90rem;
      box-shadow: 0 4px 10px rgba(37, 99, 235, 0.30);
    }}
    .brand-badge {{
      background: #eff6ff;
      color: #2563eb;
      border: 1px solid #bfdbfe;
      font-size: 0.66rem;
      padding: 2px 8px;
      border-radius: 999px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .kpi-strip {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .kpi-chip {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 0.72rem;
      color: #64748b;
      white-space: nowrap;
    }}
    .kpi-chip strong {{
      color: #0f172a;
      font-weight: 700;
      margin-left: 3px;
    }}

    /* 5 Main Executive Product Areas (haio.sg Soft Pill Mode Switcher) */
    .mode-switcher {{
      display: flex;
      background: transparent;
      padding: 2px;
      gap: 4px;
      flex-wrap: nowrap;
      overflow-x: auto;
      scrollbar-width: none;
      align-items: center;
    }}
    .mode-switcher::-webkit-scrollbar {{ display: none; }}
    .mode-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: #475569;
      padding: 7px 14px;
      border-radius: 999px;
      font-size: 0.80rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.18s ease;
      white-space: nowrap;
      flex-shrink: 0;
    }}
    .mode-btn:hover {{
      color: #0f172a;
      background: #f1f5f9;
    }}
    .mode-btn.active {{
      background: #eff6ff;
      color: #2563eb;
      font-weight: 700;
      border-color: #dbeafe;
    }}

    /* Right Header Actions & Pill Toggle */
    .header-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
      position: relative;
      flex-shrink: 0;
    }}
    .emirate-pill-select {{
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      color: #0f172a;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 0.76rem;
      font-weight: 700;
      cursor: pointer;
      outline: none;
    }}
    .export-dropdown {{
      position: relative;
    }}
    .export-dropdown summary {{
      list-style: none;
      background: #2563eb;
      border: 1px solid #1d4ed8;
      color: #ffffff;
      padding: 6px 13px;
      border-radius: 999px;
      font-size: 0.76rem;
      font-weight: 700;
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
      box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
    }}
    .export-dropdown summary::-webkit-details-marker {{ display: none; }}
    .export-menu {{
      position: absolute;
      right: 0;
      top: calc(100% + 8px);
      width: 260px;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 8px;
      box-shadow: 0 16px 36px rgba(15, 23, 42, 0.16);
      display: flex;
      flex-direction: column;
      gap: 3px;
      z-index: 3000;
    }}
    .export-menu a {{
      padding: 8px 10px;
      border-radius: 10px;
      font-size: 0.78rem;
      color: #1e293b;
      display: flex;
      justify-content: space-between;
      font-weight: 600;
    }}
    .export-menu a:hover {{
      background: #eff6ff;
      color: #2563eb;
      text-decoration: none;
    }}

    /* 2. FULL-BLEED 3D STAGE WITH FLOATING ROUNDED CARD INSPECTOR (HAIO.SG LAYOUT) */
    .workbench {{
      position: relative;
      width: 100%;
      height: calc(100vh - 58px);
      min-height: 620px;
      overflow: hidden;
      background: #0b1320;
    }}
    .workbench.panel-collapsed .sidebar-right {{
      transform: translateX(calc(100% + 24px));
      opacity: 0;
      pointer-events: none;
    }}
    @media (max-width: 1440px) {{
      .kpi-strip {{ display: none; }}
    }}
    @media (max-width: 1024px) {{
      .workbench {{
        display: flex !important;
        flex-direction: column;
        height: auto !important;
        min-height: 0 !important;
      }}
    }}
    @media (max-width: 768px) {{
      .exec-header {{ padding: 6px 12px; }}
      .mode-switcher {{ width: 100%; overflow-x: auto; flex-wrap: nowrap; }}
    }}

    /* 3. Full-Bleed 3D + 2D Map Stage */
    .map-stage {{
      position: relative;
      width: 100%;
      height: 100%;
      background: #0b1320;
      overflow: hidden;
    }}
    /* Primary WebGL 3D MapLibre Canvas (Full-Bleed) */
    #map3dCanvas {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      z-index: 2;
    }}
    /* Backing Synchronized 2D Leaflet Canvas */
    #mapCanvas {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
      opacity: 0;
      pointer-events: none;
    }}
    .map-stage.mode-2d-leaflet #mapCanvas {{
      opacity: 1;
      pointer-events: auto;
      z-index: 3;
    }}
    .map-stage.mode-2d-leaflet #map3dCanvas {{
      opacity: 0;
      pointer-events: none;
    }}

    /* HAIO.SG FLOATING PILL CONTROLS ON THE MAP CANVAS */
    .haio-floating-top-left {{
      position: absolute;
      top: 16px;
      left: 16px;
      z-index: 800;
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      pointer-events: none;
    }}
    .haio-floating-top-left > * {{
      pointer-events: auto;
    }}
    .haio-pill-btn {{
      background: #ffffff;
      border: 1px solid rgba(226, 232, 240, 0.95);
      color: #0f172a;
      padding: 8px 16px;
      border-radius: 999px;
      font-size: 0.84rem;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.14);
      transition: all 0.18s ease;
      white-space: nowrap;
      user-select: none;
    }}
    .haio-pill-btn:hover {{
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.20);
    }}
    .haio-switch-track {{
      width: 38px;
      height: 22px;
      border-radius: 999px;
      background: #cbd5e1;
      position: relative;
      display: inline-block;
      transition: background 0.2s ease;
    }}
    .haio-switch-track.on {{
      background: #2563eb;
    }}
    .haio-switch-thumb {{
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #ffffff;
      position: absolute;
      top: 2px;
      left: 2px;
      transition: transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
      box-shadow: 0 1px 3px rgba(0,0,0,0.25);
    }}
    .haio-switch-track.on .haio-switch-thumb {{
      transform: translateX(16px);
    }}

    /* 2D / 3D Segmented Pill */
    .haio-2d3d-pill {{
      background: #ffffff;
      border-radius: 999px;
      padding: 3px;
      display: inline-flex;
      align-items: center;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.14);
      border: 1px solid #e2e8f0;
    }}
    .haio-dim-btn {{
      border: none;
      background: transparent;
      color: #475569;
      font-size: 0.78rem;
      font-weight: 800;
      padding: 5px 12px;
      border-radius: 999px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .haio-dim-btn.active {{
      background: #2563eb;
      color: #ffffff;
      box-shadow: 0 2px 6px rgba(37, 99, 235, 0.30);
    }}

    /* Center-Top Lens Dock (Discover, 3D Towers, Commute, Peak, Supply, Master Plan) */
    .haio-lens-dock {{
      position: absolute;
      top: 16px;
      left: 50%;
      transform: translateX(-62%);
      z-index: 790;
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(226, 232, 240, 0.9);
      border-radius: 18px;
      padding: 5px;
      display: flex;
      align-items: center;
      gap: 3px;
      box-shadow: 0 8px 26px rgba(15, 23, 42, 0.14);
    }}
    .haio-lens-btn {{
      border: none;
      background: transparent;
      color: #475569;
      padding: 6px 12px;
      border-radius: 13px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      cursor: pointer;
      font-size: 0.69rem;
      font-weight: 700;
      transition: all 0.16s ease;
      white-space: nowrap;
    }}
    .haio-lens-btn .lens-ico {{
      font-size: 0.95rem;
      line-height: 1;
    }}
    .haio-lens-btn:hover {{
      background: #f1f5f9;
      color: #0f172a;
    }}
    .haio-lens-btn.active {{
      background: #2563eb;
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
    }}

    /* Bottom-Left Compass Pill (🧭 NE 45°) & Sun/Time Window Pill */
    .haio-floating-bottom-left {{
      position: absolute;
      bottom: 18px;
      left: 16px;
      z-index: 800;
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      max-width: calc(100% - 440px);
      pointer-events: none;
    }}
    .haio-floating-bottom-left > * {{
      pointer-events: auto;
    }}
    .haio-compass-pill {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 999px;
      padding: 8px 16px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 0.84rem;
      font-weight: 800;
      color: #0f172a;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.16);
      transition: transform 0.15s ease;
      user-select: none;
    }}
    .haio-compass-pill:hover {{
      transform: scale(1.03);
    }}
    .compass-needle-svg {{
      width: 18px;
      height: 18px;
      transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
    }}

    /* Sun & Diurnal Time Window Pill Bar */
    .time-group {{
      display: inline-flex;
      gap: 3px;
      flex-wrap: nowrap;
      align-items: center;
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(10px);
      padding: 4px;
      border-radius: 999px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.14);
    }}
    .time-btn {{
      background: transparent;
      border: none;
      color: #475569;
      padding: 6px 11px;
      border-radius: 999px;
      font-size: 0.74rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
    }}
    .time-btn:hover {{
      color: #0f172a;
      background: #f1f5f9;
    }}
    .time-btn.active {{
      background: #0f172a;
      color: #ffffff;
      box-shadow: 0 2px 6px rgba(15, 23, 42, 0.25);
    }}

    .basemap-switcher {{
      background: rgba(255, 255, 255, 0.96);
      border: 1px solid #e2e8f0;
      padding: 3px;
      border-radius: 999px;
      display: inline-flex;
      gap: 2px;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.14);
    }}
    .bm-btn {{
      background: transparent;
      border: none;
      color: #475569;
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 0.73rem;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
    }}
    .bm-btn.active {{
      background: #eff6ff;
      color: #2563eb;
    }}

    /* Dark Floating 3D Tower Callout Pill (Exact haio.sg "Block 1 · 2 stacks" style) */
    .haio-3d-block-callout {{
      background: #0f172a;
      color: #ffffff;
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 700;
      white-space: nowrap;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.40);
      border: 1.5px solid rgba(255, 255, 255, 0.22);
      cursor: pointer;
      pointer-events: auto;
      transition: transform 0.15s ease, background 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .haio-3d-block-callout:hover {{
      transform: translateY(-2px) scale(1.04);
      background: #2563eb;
    }}
    .haio-3d-block-callout.hero {{
      background: #0f172a;
      border-color: #fbbf24;
      font-size: 0.82rem;
      padding: 7px 16px;
    }}

    .road-speed-pill {{
      background: rgba(15, 23, 42, 0.92);
      border: 1.5px solid #38bdf8;
      color: #fff;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 0.69rem;
      font-weight: 800;
      white-space: nowrap;
      box-shadow: 0 3px 10px rgba(0,0,0,0.45);
      pointer-events: auto;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}

    .story-bar {{
      display: flex;
      align-items: center;
      gap: 4px;
      flex-wrap: wrap;
    }}
    .story-step {{
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      color: #334155;
      padding: 4px 9px;
      border-radius: 999px;
      font-size: 0.70rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .story-step:hover {{ color: #2563eb; border-color: #2563eb; }}
    .story-step.active {{
      background: #2563eb;
      color: #fff;
      border-color: #2563eb;
    }}
    .story-arrow {{ color: #94a3b8; font-size: 0.68rem; }}

    .quick-layer-pill {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      color: #475569;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 0.74rem;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      white-space: nowrap;
      box-shadow: 0 2px 8px rgba(15,23,42,0.08);
    }}
    .quick-layer-pill.on, .quick-layer-pill.active {{
      background: #eff6ff;
      border-color: #93c5fd;
      color: #2563eb;
    }}
    .uc-btn {{
      background: #f1f5f9;
      border: 1px solid transparent;
      color: #475569;
      padding: 7px 8px;
      border-radius: 999px;
      font-size: 0.73rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .uc-btn:hover {{ color: #0f172a; background: #e2e8f0; }}
    .uc-btn.active {{
      background: #0f172a;
      color: #ffffff;
    }}
    .live-window-banner {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-left: 4px solid #2563eb;
      border-radius: 12px;
      padding: 10px 12px;
      margin-bottom: 12px;
      font-size: 0.75rem;
      color: #1e293b;
    }}

    /* Compact Popover for All 11 Layers & Advanced Filters */
    .layers-drawer-popover {{
      position: absolute;
      top: 66px;
      left: 16px;
      width: 348px;
      max-height: 76vh;
      overflow-y: auto;
      background: rgba(255, 255, 255, 0.98);
      backdrop-filter: blur(16px);
      border: 1px solid #cbd5e1;
      border-radius: 18px;
      padding: 14px;
      z-index: 1200;
      box-shadow: 0 18px 42px rgba(15, 23, 42, 0.22);
      display: none;
      color: #0f172a;
    }}
    .layers-drawer-popover.open {{ display: block; }}

    /* Compact Map Legend Pill */
    .map-legend {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.70rem;
      flex-wrap: wrap;
      background: rgba(255, 255, 255, 0.95);
      border: 1px solid #e2e8f0;
      padding: 6px 12px;
      border-radius: 999px;
      color: #1e293b;
      font-weight: 600;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.12);
    }}
    .legend-inline {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .leg-row {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      white-space: nowrap;
    }}
    .leg-line {{
      width: 14px;
      height: 3px;
      border-radius: 2px;
      display: inline-block;
    }}
    .layer-dot {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
      display: inline-block;
      flex-shrink: 0;
    }}

    /* Form Controls inside Filter Popover & Q&A */
    .ctrl-label {{
      display: block;
      font-size: 0.68rem;
      color: #64748b;
      font-weight: 700;
      margin: 8px 0 3px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .ctrl-select, .ctrl-input {{
      width: 100%;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      color: #0f172a;
      padding: 8px 11px;
      border-radius: 10px;
      font-size: 0.80rem;
      font-weight: 500;
      outline: none;
    }}
    .ctrl-select:focus, .ctrl-input:focus {{
      border-color: #2563eb;
      background: #ffffff;
    }}
    .layer-list {{
      display: flex;
      flex-direction: column;
      gap: 5px;
      margin-top: 8px;
    }}
    .layer-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.75rem;
      padding: 6px 8px;
      border-radius: 10px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      color: #1e293b;
      font-weight: 600;
    }}
    .layer-item label {{
      display: flex;
      align-items: center;
      gap: 7px;
      cursor: pointer;
      flex: 1;
    }}
    .prov-tag {{
      font-size: 0.62rem;
      padding: 2px 6px;
      border-radius: 999px;
      font-weight: 700;
    }}
    .prov-ver {{ background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }}
    .prov-mod {{ background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }}

    /* 4. HAIO.SG FLOATING RIGHT ROUNDED CARD INSPECTOR */
    .sidebar-right {{
      position: absolute;
      top: 16px;
      right: 16px;
      bottom: 16px;
      width: 400px;
      background: #ffffff;
      border: 1px solid rgba(226, 232, 240, 0.95);
      border-radius: 22px;
      box-shadow: 0 16px 48px rgba(15, 23, 42, 0.22);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      z-index: 900;
      transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.22s ease;
    }}
    .drawer-tabs {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      background: #f8fafc;
      border-bottom: 1px solid #e2e8f0;
      padding: 6px 8px;
      gap: 4px;
    }}
    .dtab-btn {{
      background: transparent;
      border: none;
      border-radius: 999px;
      color: #64748b;
      padding: 7px 6px;
      font-size: 0.74rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.16s ease;
    }}
    .dtab-btn:hover {{
      color: #0f172a;
      background: #e2e8f0;
    }}
    .dtab-btn.active {{
      color: #2563eb;
      background: #eff6ff;
      box-shadow: 0 1px 3px rgba(37, 99, 235, 0.12);
    }}
    .drawer-body {{
      padding: 18px;
      overflow-y: auto;
      flex: 1;
      scrollbar-width: thin;
    }}

    /* HAIO.SG 3D BLOCK / FLOOR / STACK CARD COMPONENTS */
    .haio-card-title {{
      font-size: 1.24rem;
      font-weight: 800;
      color: #0f172a;
      margin: 0 0 4px 0;
      letter-spacing: -0.02em;
      line-height: 1.25;
    }}
    .haio-card-sub {{
      font-size: 0.84rem;
      color: #64748b;
      font-weight: 500;
      margin-bottom: 14px;
    }}
    .haio-divider {{
      height: 1px;
      background: #f1f5f9;
      margin: 14px 0;
    }}
    .haio-field-lbl {{
      display: block;
      font-size: 0.69rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #64748b;
      margin-bottom: 6px;
    }}
    .haio-select {{
      width: 100%;
      background: #ffffff;
      border: 1.5px solid #e2e8f0;
      border-radius: 12px;
      padding: 10px 12px;
      font-size: 0.86rem;
      font-weight: 600;
      color: #0f172a;
      cursor: pointer;
      outline: none;
      transition: border-color 0.15s ease;
    }}
    .haio-select:hover, .haio-select:focus {{
      border-color: #2563eb;
    }}
    .haio-showme-row {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }}
    .haio-showme-pill {{
      background: #f1f5f9;
      border: 1px solid transparent;
      color: #334155;
      padding: 8px 14px;
      border-radius: 999px;
      font-size: 0.80rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .haio-showme-pill:hover {{
      background: #e2e8f0;
      color: #0f172a;
    }}
    .haio-showme-pill.active {{
      background: #0f172a;
      color: #ffffff;
      box-shadow: 0 3px 10px rgba(15, 23, 42, 0.22);
    }}
    .haio-unit-bar {{
      background: #f8fafc;
      border: 1px solid #f1f5f9;
      border-radius: 12px;
      padding: 10px 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 0.80rem;
      font-weight: 700;
      color: #1e293b;
      margin-bottom: 10px;
    }}
    .haio-block-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 8px;
      margin-top: 6px;
      margin-bottom: 10px;
    }}
    .haio-block-card {{
      background: #ffffff;
      border: 1.5px solid #e2e8f0;
      border-radius: 14px;
      padding: 11px 13px;
      cursor: pointer;
      transition: all 0.16s ease;
    }}
    .haio-block-card:hover {{
      border-color: #2563eb;
      background: #f8fafc;
      transform: translateY(-1px);
    }}
    .haio-block-card.active {{
      border-color: #2563eb;
      background: #eff6ff;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.14);
    }}
    .haio-block-card strong {{
      display: block;
      font-size: 0.86rem;
      color: #0f172a;
      margin-bottom: 2px;
    }}
    .haio-block-card span {{
      display: block;
      font-size: 0.74rem;
      color: #64748b;
      line-height: 1.35;
    }}
    /* HAIO Discovery List Row ("5 new launches in 3D" style) */
    .haio-launch-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 12px;
      border-bottom: 1px solid #f1f5f9;
      cursor: pointer;
      border-radius: 10px;
      transition: background 0.15s ease;
    }}
    .haio-launch-row:hover {{
      background: #f8fafc;
    }}
    .haio-launch-left {{
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }}
    .haio-launch-bar {{
      width: 4px;
      height: 34px;
      border-radius: 4px;
      background: #f59e0b;
      flex-shrink: 0;
    }}
    .haio-launch-3d-tag {{
      text-align: right;
      flex-shrink: 0;
      font-size: 0.72rem;
      color: #64748b;
      line-height: 1.25;
    }}
    .haio-launch-3d-tag strong {{
      display: block;
      color: #2563eb;
      font-size: 0.78rem;
      font-weight: 800;
    }}

    .detail-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 14px;
      margin-bottom: 10px;
      color: #0f172a;
    }}
    .detail-card h4 {{
      margin: 0 0 6px 0;
      font-size: 1.02rem;
      color: #0f172a;
      font-weight: 800;
    }}

    /* Executive KPI Grid inside Cards */
    .exec-metric-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      margin: 10px 0;
    }}
    .exec-metric-tile, .exec-metric-box {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 9px 11px;
    }}
    .exec-metric-tile .m-lbl, .exec-metric-box .em-lbl {{
      font-size: 0.65rem;
      text-transform: uppercase;
      color: #64748b;
      font-weight: 700;
      letter-spacing: 0.04em;
    }}
    .exec-metric-tile .m-val, .exec-metric-box .em-val {{
      font-size: 0.88rem;
      font-weight: 800;
      color: #0f172a;
      margin-top: 2px;
    }}
    .exec-metric-box .em-sub {{
      font-size: 0.69rem;
      color: #64748b;
      margin-top: 2px;
    }}
    .ep-pill-pub {{
      display: inline-block;
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      color: #059669;
      font-size: 0.65rem;
      font-weight: 800;
      padding: 1px 6px;
      border-radius: 4px;
      margin-right: 4px;
    }}
    .ep-pill-mod {{
      display: inline-block;
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #d97706;
      font-size: 0.65rem;
      font-weight: 800;
      padding: 1px 6px;
      border-radius: 4px;
      margin-right: 4px;
    }}

    /* Progressive Disclosure Technical Accordion (<details>) */
    details.tech-accordion {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      margin-top: 10px;
      overflow: hidden;
    }}
    details.tech-accordion summary {{
      padding: 10px 12px;
      font-size: 0.76rem;
      font-weight: 700;
      color: #2563eb;
      cursor: pointer;
      user-select: none;
      background: #f8fafc;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    details.tech-accordion summary:hover {{
      background: #eff6ff;
    }}
    details.tech-accordion .acc-body, details.tech-accordion .tech-body {{
      padding: 10px 12px;
      font-size: 0.75rem;
      border-top: 1px solid #e2e8f0;
      color: #334155;
      background: #ffffff;
      line-height: 1.55;
    }}

    .kv-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 7px;
      font-size: 0.76rem;
      margin-top: 8px;
    }}
    .kv-row {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 8px 10px;
      border-radius: 10px;
    }}
    .kv-lbl {{
      font-size: 0.66rem;
      text-transform: uppercase;
      color: #64748b;
      font-weight: 700;
    }}
    .kv-val {{
      color: #1e293b;
      margin-top: 3px;
      word-break: break-word;
    }}

    /* Epistemic Tier Badges */
    .ep-badge {{
      display: inline-block;
      padding: 3px 9px;
      border-radius: 999px;
      font-size: 0.69rem;
      font-weight: 700;
    }}
    .ep-t1 {{ background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }}
    .ep-t2 {{ background: #f5f3ff; color: #7c3aed; border: 1px solid #ddd6fe; }}
    .ep-t3 {{ background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }}
    .ep-t4 {{ background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }}

    .conf-pill {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 0.68rem;
      font-weight: 700;
    }}
    .b-ver {{ background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }}
    .b-cor {{ background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }}
    .b-est {{ background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }}

    /* Q&A Interface */
    .qa-box {{
      display: flex;
      gap: 6px;
      margin-bottom: 10px;
    }}
    .qa-preset-list {{
      display: flex;
      flex-direction: column;
      gap: 5px;
      margin-bottom: 10px;
    }}
    .qa-preset-btn {{
      text-align: left;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      color: #1e293b;
      padding: 8px 10px;
      border-radius: 10px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .qa-preset-btn:hover {{
      border-color: #2563eb;
      color: #2563eb;
      background: #eff6ff;
    }}

    /* Bottom Expandable Evidence & Datasets Section */
    .evidence-section {{
      padding: 20px 20px 48px;
      max-width: 1600px;
      margin: 0 auto;
    }}
    .ev-tabs {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 12px;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 8px;
    }}
    .ev-tab-btn {{
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      color: #334155;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
    }}
    .ev-tab-btn.active {{
      background: #2563eb;
      color: #fff;
      border-color: #2563eb;
    }}
    .ev-panel {{ display: none; }}
    .ev-panel.active {{ display: block; }}

    .t2-table-wrap {{
      overflow-x: auto;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
      margin-top: 8px;
      max-height: 520px;
    }}
    .t2-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.75rem;
      color: #1e293b;
    }}
    .t2-table th, .t2-table td {{
      padding: 8px 10px;
      border-bottom: 1px solid #f1f5f9;
      text-align: left;
      vertical-align: top;
    }}
    .t2-table th {{
      background: #f8fafc;
      color: #0f172a;
      font-weight: 700;
      position: sticky;
      top: 0;
      border-bottom: 2px solid #e2e8f0;
    }}
    .t2-table tr:hover td {{
      background: #f8fafc;
    }}
    .dl-bar {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin: 8px 0;
      align-items: center;
      font-size: 0.76rem;
    }}
    .dl-chip {{
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #2563eb;
      padding: 3px 10px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 0.72rem;
    }}
    .mobile-back-map-btn {{
      display: none;
    }}

    /* =========================================================================
       MOBILE & TABLET RESPONSIVE ARCHITECTURE (HAIO.SG BOTTOM SHEET LAYOUT)
       ========================================================================= */
    @media (max-width: 1280px) {{
      .haio-lens-dock {{
        display: none;
      }}
    }}
    @media (max-width: 1024px) {{
      html, body {{
        max-width: 100vw;
        overflow-x: hidden;
      }}
      .exec-header {{
        flex-wrap: wrap;
        padding: 8px 12px;
        gap: 6px;
        min-height: auto;
      }}
      .brand-cluster {{
        flex: 1 1 auto;
        min-width: 0;
      }}
      .header-actions {{
        margin-left: auto;
        gap: 6px;
      }}
      .mode-switcher {{
        order: 3;
        width: 100%;
        overflow-x: auto;
        flex-wrap: nowrap;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        padding: 2px 0;
        gap: 4px;
      }}
      .mode-switcher::-webkit-scrollbar {{ display: none; }}
      .mode-btn {{
        flex-shrink: 0;
        padding: 5px 11px;
        font-size: 0.74rem;
      }}
      .workbench {{
        display: flex !important;
        flex-direction: column;
        height: auto !important;
        min-height: 0 !important;
        background: #f1f5f9;
      }}
      .map-stage {{
        position: relative;
        width: 100%;
        height: 54vh !important;
        min-height: 360px;
        max-height: 480px;
        flex: none;
      }}
      .haio-floating-top-left {{
        top: 10px;
        left: 10px;
        right: 10px;
        gap: 6px;
      }}
      .haio-pill-btn {{
        padding: 6px 12px;
        font-size: 0.76rem;
      }}
      .haio-floating-bottom-left {{
        bottom: 10px;
        left: 10px;
        right: 10px;
        max-width: none;
        gap: 6px;
        overflow-x: auto;
        flex-wrap: nowrap;
        scrollbar-width: none;
      }}
      .haio-floating-bottom-left::-webkit-scrollbar {{ display: none; }}
      .haio-compass-pill {{
        padding: 6px 12px;
        font-size: 0.76rem;
        flex-shrink: 0;
      }}
      .time-group {{
        flex-shrink: 0;
      }}
      .time-btn {{
        padding: 5px 9px;
        font-size: 0.70rem;
      }}
      .layers-drawer-popover {{
        position: fixed !important;
        left: 10px !important;
        right: 10px !important;
        bottom: 10px !important;
        top: auto !important;
        width: auto !important;
        max-height: 78vh !important;
        z-index: 4500 !important;
        box-shadow: 0 -10px 40px rgba(15,23,42,0.35) !important;
      }}
      .sidebar-right {{
        position: relative !important;
        top: auto !important;
        right: auto !important;
        bottom: auto !important;
        width: 100% !important;
        border-radius: 22px 22px 0 0 !important;
        margin-top: -14px;
        box-shadow: 0 -8px 28px rgba(15, 23, 42, 0.14) !important;
        overflow: visible;
      }}
      .drawer-body {{
        max-height: none;
        overflow-y: visible;
        padding: 14px;
      }}
      .mobile-back-map-btn {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #2563eb;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.70rem;
        font-weight: 700;
        cursor: pointer;
      }}
    }}

    @media (max-width: 768px) {{
      .brand-title {{
        font-size: 0.92rem;
        gap: 6px;
      }}
      .emirate-pill-select {{
        font-size: 0.70rem;
        padding: 5px 8px;
        max-width: 132px;
      }}
      .export-dropdown summary {{
        font-size: 0.70rem;
        padding: 5px 9px;
      }}
      .export-menu {{
        position: fixed;
        top: 52px;
        right: 10px;
        left: 10px;
        width: auto;
        max-width: 340px;
        margin-left: auto;
        z-index: 4500;
      }}
      .dtab-btn {{
        padding: 7px 4px;
        font-size: 0.70rem;
      }}
      .evidence-section {{
        padding: 12px 10px 36px;
      }}
      .ev-tabs {{
        flex-wrap: nowrap;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        padding-bottom: 6px;
      }}
      .ev-tabs::-webkit-scrollbar {{ display: none; }}
      .ev-tab-btn {{
        flex-shrink: 0;
        white-space: nowrap;
        font-size: 0.70rem;
        padding: 5px 9px;
      }}
    }}
  </style>
</head>
<body>

  <!-- 1. HAIO-STYLE ULTRA-CLEAN WHITE TOP NAVBAR -->
  <header class="exec-header">
    <div class="brand-cluster">
      <div class="brand-title" onclick="backToCityMapOverview()">
        <span class="haio-logo-pin">🗺️</span>
        <span>UAE Construction &amp; Traffic Intelligence</span>
      </div>
      <div class="kpi-strip">
        <span class="kpi-chip">Scope <strong id="hudScope">Dubai Corridors</strong></span>
        <span class="kpi-chip">Sites <strong id="hudProjects">25 Active Sites</strong></span>
        <span class="kpi-chip">Avg Speed <strong id="hudAvgSpeed" style="color:#059669;">43.9 km/h</strong></span>
      </div>
    </div>

    <!-- 5 MAIN EXECUTIVE AREAS (GOAL-ALIGNED NAVIGATION) -->
    <nav class="mode-switcher" aria-label="Primary Platform Modes">
      <button class="mode-btn active" id="mode-overview" onclick="setPlatformMode('overview', this)">1. Overview</button>
      <button class="mode-btn" id="mode-construction" onclick="setPlatformMode('construction', this)">2. Construction Map</button>
      <button class="mode-btn" id="mode-traffic" onclick="setPlatformMode('traffic', this)">3. Traffic Intelligence</button>
      <button class="mode-btn" id="mode-project" onclick="setPlatformMode('project', this)">4. Project Explorer</button>
      <button class="mode-btn" id="mode-evidence" onclick="setPlatformMode('evidence', this)">5. Evidence &amp; Data ↓</button>
    </nav>

    <div class="header-actions">
      <select id="emirateSelect" class="emirate-pill-select" onchange="onEmirateChange()" aria-label="Select Emirate">
        <option value="Dubai" selected>Dubai (25 Sites)</option>
        <option value="Sharjah">Sharjah (12 Sites)</option>
        <option value="ALL">All UAE (37 Sites)</option>
      </select>

      <details class="export-dropdown">
        <summary>Data &amp; Exports ▾</summary>
        <div class="export-menu">
          <a href="#evidence-tables" onclick="document.getElementById('evidenceAccordion').open=true"><span>📊 All 11 Task 2 Datasets</span><span>↓</span></a>
          <a href="datasets/task2_verification_receipt.json" target="_blank"><span>✅ Verification Receipt</span><span>JSON</span></a>
          <a href="datasets/dubai_sharjah_gis_bundle.geojson" target="_blank"><span>📦 Spatial Bundle (123)</span><span>GeoJSON</span></a>
          <a href="datasets/21_task2_spatial_database.sqlite"><span>🗄️ Task 2 Spatial DB</span><span>SQLite</span></a>
          <a href="task2_gis_and_traffic_intelligence_report.md" target="_blank"><span>📄 Full Task 2 Report</span><span>MD</span></a>
          <a href="index.html"><span>🏛️ Switch to Task 1 (85 Projects)</span><span>→</span></a>
        </div>
      </details>
    </div>
  </header>

  <!-- 2. FULL-BLEED REALISTIC 3D GIS STAGE + FLOATING INTELLIGENCE INSPECTOR -->
  <main class="workbench" id="mainWorkbench">

    <section class="map-stage" id="mapStage">
      <!-- Top-Left Floating Map Controls (Exact haio.sg < Map + Blocks [ON] + 2D/3D + Layers) -->
      <div class="haio-floating-top-left">
        <button class="haio-pill-btn" onclick="backToCityMapOverview()" title="Switch to Dubai &amp; UAE Corridor Overview">
          <span>‹ Map</span>
        </button>

        <button class="haio-pill-btn" id="blocksTogglePill" onclick="toggle3DBlocksMassing()" title="Toggle Photorealistic 3D Buildings &amp; Blocks">
          <span>Blocks</span>
          <span class="haio-switch-track on" id="blocksSwitchTrack">
            <span class="haio-switch-thumb"></span>
          </span>
        </button>

        <div class="haio-2d3d-pill" role="group" aria-label="2D or 3D Camera Pitch">
          <button class="haio-dim-btn" id="btnDim2D" onclick="setCameraDimension('2D')">2D</button>
          <button class="haio-dim-btn active" id="btnDim3D" onclick="setCameraDimension('3D')">3D</button>
        </div>

        <button class="haio-pill-btn" onclick="toggleLayersPopover()" style="padding:8px 13px; font-size:0.78rem;">
          <span>⚙ Layers (11)</span>
        </button>
      </div>

      <!-- 3D Projected Hero Tower Roof Callout ("Block 1 · 2 stacks") -->
      <div id="hero3DRoofCallout" class="haio-3d-block-callout" style="position:absolute; top:0; left:0; z-index:785; display:none; background:rgba(15,23,42,0.94); color:#ffffff; border:1px solid rgba(255,255,255,0.22); padding:6px 14px; font-size:0.78rem; font-weight:700; border-radius:999px; box-shadow:0 8px 24px rgba(0,0,0,0.45); pointer-events:auto;" onclick="select3DBlockCard('B1')">
        <span id="hero3DRoofCalloutText">Block 1 · 2 stacks</span>
      </div>

      <!-- Photorealistic 3D Attribution Badge (Bottom-Right beside Inspector Card) -->
      <div id="photoreal3DAttribution" style="position:absolute; right:430px; bottom:14px; z-index:780; display:flex; align-items:center; gap:8px; pointer-events:none;">
        <div style="background:rgba(15,23,42,0.62); backdrop-filter:blur(6px); color:#f8fafc; padding:3px 9px; border-radius:6px; font-size:0.66rem; font-weight:600; line-height:1.2; text-align:right;">
          <strong style="font-size:0.74rem; display:block; letter-spacing:0.01em;">3D Earth &amp; RTA GIS</strong>
          <span>Airbus · Maxar · OSM 3D</span>
        </div>
        <div style="width:22px; height:22px; border-radius:50%; background:#ffffff; color:#0f172a; display:inline-flex; align-items:center; justify-content:center; font-size:0.74rem; font-weight:800; box-shadow:0 2px 8px rgba(0,0,0,0.3);">i</div>
      </div>

      <!-- Center-Top Floating Scenario Dock (Hidden to avoid duplicate toolbar clutter) -->
      <div class="haio-lens-dock" id="haioLensDock" style="display:none;">
        <button class="haio-lens-btn active" id="lens-1" onclick="selectLensDock(1)">
          <span class="lens-ico">🔥</span>
          <span>Hotspots</span>
        </button>
        <button class="haio-lens-btn" id="lens-2" onclick="selectLensDock(2)">
          <span class="lens-ico">🚧</span>
          <span>JVC Traffic</span>
        </button>
        <button class="haio-lens-btn" id="lens-3" onclick="selectLensDock(3)">
          <span class="lens-ico">⏱️</span>
          <span>AM vs PM</span>
        </button>
        <button class="haio-lens-btn" id="lens-4" onclick="selectLensDock(4)">
          <span class="lens-ico">🏗️</span>
          <span>Projects</span>
        </button>
        <button class="haio-lens-btn" id="lens-5" onclick="selectLensDock(5)">
          <span class="lens-ico">🏢</span>
          <span>Downtown 3D</span>
        </button>
        <button class="haio-lens-btn" id="lens-6" onclick="selectLensDock(6)">
          <span class="lens-ico">🗺️</span>
          <span>Sharjah</span>
        </button>
      </div>

      <!-- Primary WebGL 3D MapLibre GL JS Canvas (Real OSM 3D Buildings + Satellite + Road Corridors) -->
      <div id="map3dCanvas"></div>
      <!-- Synchronized Backing 2D Leaflet Canvas -->
      <div id="mapCanvas" class="basemap-dark"></div>

      <!-- Collapsible Advanced Layers & Filters Popover (All 11 Layers Preserved) -->
      <div class="layers-drawer-popover" id="layersPopover">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <strong style="font-size:0.84rem; color:#0f172a;">Map Layers (11) &amp; Spatial Filters</strong>
          <div style="display:flex; gap:6px;">
            <button onclick="resetAllFilters()" style="background:#eff6ff;border:1px solid #bfdbfe;color:#2563eb;font-size:0.70rem;font-weight:700;padding:3px 9px;border-radius:999px;cursor:pointer;">Reset</button>
            <button onclick="toggleLayersPopover()" style="background:transparent;border:none;color:#64748b;font-size:0.95rem;cursor:pointer;">✕</button>
          </div>
        </div>

        <input type="text" id="searchInput" class="ctrl-input" placeholder="Search project, road, community (e.g. JVC, Hessa)..." oninput="applyMapFilters()"/>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:4px;">
          <div>
            <label class="ctrl-label">Community Jump</label>
            <select id="communitySelect" class="ctrl-select" onchange="zoomToSelectedCommunity()">
              <option value="ALL">-- All Communities --</option>
            </select>
          </div>
          <div>
            <label class="ctrl-label">Congestion Filter</label>
            <select id="congestionFilter" class="ctrl-select" onchange="applyMapFilters()">
              <option value="ALL">All Levels</option>
              <option value="Severe">Severe Only</option>
              <option value="High">High &amp; Severe</option>
              <option value="Moderate">Moderate</option>
              <option value="Low">Low / Free-Flow</option>
              <option value="Unavailable">Data Unavailable</option>
            </select>
          </div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:4px;">
          <div>
            <label class="ctrl-label">Impact Buffer</label>
            <select id="radiusSelect" class="ctrl-select" onchange="updateImpactBuffers()">
              <option value="500">500m Access</option>
              <option value="1500" selected>1.5 km Collector</option>
              <option value="3000">3.0 km Arterial</option>
            </select>
          </div>
          <div>
            <label class="ctrl-label">Epistemic Tier</label>
            <select id="epistemicFilter" class="ctrl-select" onchange="applyMapFilters()">
              <option value="ALL">All 4 Tiers</option>
              <option value="Tier 4">Tier 4: Confirmed ROW</option>
              <option value="Tier 2">Tier 2: Spatial Assoc.</option>
              <option value="Tier 3">Tier 3: Modelled HGV</option>
            </select>
          </div>
        </div>

        <div class="layer-list">
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L1" checked onchange="toggleLayerGroup('projects', this.checked)"/><span class="layer-dot" style="background:#2563eb;"></span> 1. Active Construction Projects (32 + 5)</label>
            <span class="prov-tag prov-ver">Default ON</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L3" checked onchange="toggleLayerGroup('communities', this.checked)"/><span class="layer-dot" style="background:#7c3aed;"></span> 2. Community Hotspots (10)</label>
            <span class="prov-tag prov-ver">Default ON</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L6" checked onchange="toggleLayerGroup('traffic', this.checked)"/><span class="layer-dot" style="background:#ef4444;"></span> 3. Modelled Corridor Speeds</label>
            <span class="prov-tag prov-mod">Modelled</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L4" checked onchange="toggleLayerGroup('roads', this.checked)"/><span class="layer-dot" style="background:#64748b;"></span> 4. Base Road Network (23)</label>
            <span class="prov-tag prov-ver">RTA Cap</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L2" onchange="toggleLayerGroup('devbounds', this.checked)"/><span class="layer-dot" style="background:#8b5cf6;"></span> 5. JVC Sub-Clusters &amp; Radii</label>
            <span class="prov-tag prov-ver">Zoom/Toggle</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L5" onchange="toggleLayerGroup('intersections', this.checked)"/><span class="layer-dot" style="background:#f43f5e;"></span> 6. Bottleneck Intersections (16)</label>
            <span class="prov-tag prov-ver">Corrob.</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L7" onchange="toggleLayerGroup('incidents', this.checked)"/><span class="layer-dot" style="background:#f97316;"></span> 7. Active RTA/SRTA Roadworks (5)</label>
            <span class="prov-tag prov-ver">Verified</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L8" onchange="toggleLayerGroup('transit', this.checked)"/><span class="layer-dot" style="background:#3b82f6;"></span> 8. Metro Red/Blue &amp; Etihad Rail</label>
            <span class="prov-tag prov-ver">Verified</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L9" onchange="toggleLayerGroup('facilities', this.checked)"/><span class="layer-dot" style="background:#10b981;"></span> 9. Logistics &amp; Batching Plants</label>
            <span class="prov-tag prov-ver">Verified</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L10" onchange="toggleLayerGroup('parking', this.checked)"/><span class="layer-dot" style="background:#14b8a6;"></span> 10. Parking &amp; Mobility Hubs</label>
            <span class="prov-tag prov-ver">Verified</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L11" onchange="toggleLayerGroup('impacts', this.checked)"/><span class="layer-dot" style="background:#f59e0b;"></span> 11. Project-to-Road Impact Vectors</label>
            <span class="prov-tag prov-mod">Modelled</span>
          </div>
        </div>
      </div>

      <!-- Bottom-Left Floating Pills: Compass Orbit + 4 Diurnal Time Windows + Basemap -->
      <div class="haio-floating-bottom-left">
        <button class="haio-compass-pill" onclick="orbitCameraStep()" title="Click to orbit 3D camera by 45°">
          <svg class="compass-needle-svg" id="compassSvg" viewBox="0 0 24 24" style="transform: rotate(-60deg);">
            <polygon points="12,2 16,12 12,10 8,12" fill="#ef4444"/>
            <polygon points="12,22 16,12 12,14 8,12" fill="#94a3b8"/>
          </svg>
          <span id="compassLabel">NE 60°</span>
        </button>

        <div class="time-group" aria-label="Traffic Time Window Selector">
          <button class="time-btn" data-tp="Morning Peak (07:30–09:30)" onclick="setTimeWindow('Morning Peak (07:30–09:30)', this)">☀ AM</button>
          <button class="time-btn" data-tp="Midday (12:00–14:00)" onclick="setTimeWindow('Midday (12:00–14:00)', this)">🚛 Midday</button>
          <button class="time-btn active" data-tp="Evening Peak (17:00–20:00)" onclick="setTimeWindow('Evening Peak (17:00–20:00)', this)">🌇 PM</button>
          <button class="time-btn" data-tp="Night (22:00–05:00)" onclick="setTimeWindow('Night (22:00–05:00)', this)">🌙 Night</button>
        </div>

        <div class="basemap-switcher">
          <button class="bm-btn active" onclick="setBasemap('sat', this)">3D Earth</button>
          <button class="bm-btn" onclick="setBasemap('light', this)">Street</button>
          <button class="bm-btn" onclick="setBasemap('dark', this)">Dark</button>
        </div>

        <span id="hudTime" style="display:none;">Evening Peak (17:00–20:00)</span>
        <span id="hudHgvStatus" style="display:none;">🚫 HGV Ban 17:00–20:00 (E11/E44/D61)</span>
        <div style="display:none;">
          <button id="qpill-projects" onclick="quickToggle('projects', 'chk-L1', this)"></button>
          <button id="qpill-communities" onclick="quickToggle('communities', 'chk-L3', this)"></button>
          <button id="qpill-traffic" onclick="quickToggle('traffic', 'chk-L6', this)"></button>
          <button id="qpill-impacts" onclick="quickToggle('impacts', 'chk-L11', this)"></button>
        </div>
      </div>
    </section>

    <!-- FLOATING RIGHT INTELLIGENCE INSPECTOR -->
    <aside class="sidebar-right">
      <div class="drawer-tabs">
        <button class="dtab-btn active" id="dtab-insp" onclick="switchDrawerTab('insp')">🏢 3D Block &amp; Road</button>
        <button class="dtab-btn" id="dtab-uc" onclick="switchDrawerTab('uc')">📌 Hotspots &amp; Traffic</button>
        <button class="dtab-btn" id="dtab-qa" onclick="switchDrawerTab('qa')">💬 Ask Data</button>
      </div>

      <!-- TAB 1: GUIDED CONSTRUCTION & TRAFFIC SCENARIOS -->
      <div class="drawer-body" id="dpanel-uc" style="display:none;">
        <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:4px; margin-bottom:10px;">
          <button class="uc-btn active" id="btn-uc1" onclick="runUseCase(1)">1. Hotspots</button>
          <button class="uc-btn" id="btn-uc2" onclick="runUseCase(2)">2. JVC</button>
          <button class="uc-btn" id="btn-uc3" onclick="runUseCase(3)">3. AM/PM</button>
          <button class="uc-btn" id="btn-uc4" onclick="runUseCase(4)">4. Sharjah</button>
        </div>

        <details class="tech-accordion" style="margin-bottom:10px;">
          <summary style="font-size:0.73rem; padding:8px 12px;">🧭 Guided 5-Step Story Tour (UAE → Dubai → JVC → Project → Road)</summary>
          <div class="tech-body" style="padding:8px 10px;">
            <div class="story-bar" role="region" aria-label="Guided Visual Storytelling Sequence">
              <button class="story-step" id="story-1" onclick="runStoryStep(1)">1. UAE Overview</button>
              <span class="story-arrow">→</span>
              <button class="story-step active" id="story-2" onclick="runStoryStep(2)">2. Dubai</button>
              <span class="story-arrow">→</span>
              <button class="story-step" id="story-3" onclick="runStoryStep(3)">3. Community (JVC)</button>
              <span class="story-arrow">→</span>
              <button class="story-step" id="story-4" onclick="runStoryStep(4)">4. Project</button>
              <span class="story-arrow">→</span>
              <button class="story-step" id="story-5" onclick="runStoryStep(5)">5. Road Impact</button>
            </div>
          </div>
        </details>

        <div id="useCaseContainer"></div>
      </div>

      <!-- TAB 2: CONSTRUCTION PROJECT & ROAD CORRIDOR INSPECTOR -->
      <div class="drawer-body" id="dpanel-insp" style="display:block;">
        <div id="inspectorContainer"></div>
      </div>

      <!-- TAB 3: EVIDENCE, METHODOLOGY & DETERMINISTIC Q&A -->
      <div class="drawer-body" id="dpanel-qa" style="display:none;">
        <div class="detail-card">
          <h4>Deterministic Database Q&amp;A &amp; Methodology</h4>
          <p style="font-size:0.75rem; color:#64748b; margin:0 0 8px;">Ask a question or select a preset to query the normalized Task 1 + Task 2 tables and fly the 3D camera to the matched sites.</p>
          <div class="qa-box">
            <input type="text" id="qaInput" class="ctrl-input" placeholder="Ask about JVC, Hessa St, Dubai South, TIS, Morning vs Evening..." onkeydown="if(event.key==='Enter') runDeterministicQA()"/>
            <button onclick="runDeterministicQA()" style="background:#2563eb;border:none;color:#fff;padding:0 14px;border-radius:10px;font-weight:700;cursor:pointer;">Ask</button>
          </div>
          <div class="qa-preset-list">
            <button class="qa-preset-btn" onclick="askPreset(0)">1. Which areas in Dubai currently have the highest construction activity?</button>
            <button class="qa-preset-btn" onclick="askPreset(1)">2. Show construction activity in JVC and the surrounding traffic conditions.</button>
            <button class="qa-preset-btn" onclick="askPreset(2)">3. Compare traffic conditions around Hessa St &amp; JVC during morning and evening periods.</button>
            <button class="qa-preset-btn" onclick="askPreset(3)">4. Which projects are near major road intersections and bottlenecks?</button>
            <button class="qa-preset-btn" onclick="askPreset(4)">5. What traffic data and freight capacity are available around Dubai South &amp; DWC?</button>
            <button class="qa-preset-btn" onclick="askPreset(5)">6. Which communities have both active construction and observed severe congestion?</button>
            <button class="qa-preset-btn" onclick="askPreset(6)">7. Which projects and corridors have published Traffic Impact Studies (TIS) vs. restricted files?</button>
            <button class="qa-preset-btn" onclick="askPreset(7)">8. How does TomTom compare against Dubai Pulse / RTA Open Data, HERE, and Google Maps?</button>
          </div>
        </div>
        <div id="qaResultContainer"></div>
      </div>
    </aside>
  </main>

  <!-- BOTTOM SECTION: EXPANDABLE EVIDENCE REPOSITORY & ALL 11 TASK 2 DATASETS -->
  <section class="evidence-section" id="evidence-tables">
    <details id="evidenceAccordion" class="tech-accordion" style="border-color:#3b82f6;">
      <summary style="font-size:0.95rem; padding:12px 16px;">
        <span>📊 Evidence &amp; Methodology Repository — Inspect All 11 Task 2 Datasets (157 Rows), BPR Math &amp; Spatial SQLite</span>
        <span style="font-size:0.75rem; color:#94a3b8;">Click to Expand / Collapse ▾</span>
      </summary>
      <div class="acc-body" style="padding:16px;">
        <p style="margin:0 0 12px; font-size:0.80rem; color:var(--muted);">Every table below is directly inspectable in-browser and downloadable as <strong>GitHub Raw CSV</strong>, <strong>Plain Text (<code>.csv.txt</code>)</strong>, <strong>Browser Table (<code>.html</code>)</strong>, <strong>JSON</strong>, <strong>GeoJSON</strong>, and <strong>Spatial SQLite Database (<code>21_task2_spatial_database.sqlite</code>)</strong>.</p>

    <div class="ev-tabs">
      <button class="ev-tab-btn active" onclick="openEvTab('ev-impacts', this)">1. #22 Project-to-Road Links (37)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-obs', this)">2. #17 Traffic Benchmarks &amp; Estimates (22)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-roads', this)">3. #16 Road Network (23)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-comm', this)">4. #21A Communities (10)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-ints', this)">5. #21B Intersections (16)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-incs', this)">6. #21C Roadworks &amp; Incidents (5)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-subdevs', this)">7. #21D JVC Sub-Clusters (5)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-tds', this)">8. #15 Open-Data Sources (18)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-tomtom', this)">9. #18 TomTom &amp; Providers (6)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-tis', this)">10. #19 TIS &amp; HGV Rules (8)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-park', this)">11. #20 Parking, EV &amp; Delivery (7)</button>
      <button class="ev-tab-btn" onclick="openEvTab('ev-arch', this)">12. Manifest Reconciliation (15–22) &amp; Architecture</button>
    </div>

    <div id="ev-impacts" class="ev-panel active">
      <div class="dl-bar">
        <strong>Dataset #22 — Project-to-Road Nearest-Vertex Geometry &amp; Scenario-Based HGV Impact Matrix (37 Links, All &lt; 3.0 km):</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/22_project_road_impact_links.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/22_project_road_impact_links.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/22_project_road_impact_links.html">Browser Table</a>
        <a class="dl-chip" href="datasets/22_project_road_impact_links.json">JSON</a>
        <a class="dl-chip" href="datasets/21d_jvc_and_community_subdevelopments.json">JVC Sub-Clusters JSON</a>
      </div>
      {tbl_impacts}
    </div>

    <div id="ev-obs" class="ev-panel">
      <div class="dl-bar">
        <strong>Dataset #17 — 1 Published TomTom City-Wide Benchmark (<code>OBS-DXB-CITY-00</code>) + 21 Modelled Corridor Estimates Calibrated to Official RTA/SRTA Capacity Benchmarks:</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/17_traffic_congestion_observations.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/17_traffic_congestion_observations.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/17_traffic_congestion_observations.html">Browser Table</a>
        <a class="dl-chip" href="datasets/17_traffic_congestion_observations.json">JSON</a>
      </div>
      {tbl_obs}
    </div>

    <div id="ev-roads" class="ev-panel">
      <div class="dl-bar">
        <strong>Dataset #16 — Dubai &amp; Sharjah Road Network, Speed Limits, Published RTA vs. HCM Capacities &amp; HGV Bans (23 Corridors):</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/16_road_network_dataset.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/16_road_network_dataset.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/16_road_network_dataset.html">Browser Table</a>
        <a class="dl-chip" href="datasets/16_road_network_dataset.json">JSON</a>
        <a class="dl-chip" href="datasets/dubai_sharjah_gis_bundle.geojson">GeoJSON</a>
      </div>
      {tbl_roads}
    </div>

    <div id="ev-comm" class="ev-panel">
      <div class="dl-bar">
        <strong>Dataset #21A — Community Boundaries, Construction Hotspot Counts &amp; Transparent Activity Index Formula (10 Zones):</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/21a_communities_and_hotspots.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/21a_communities_and_hotspots.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/21a_communities_and_hotspots.html">Browser Table</a>
        <a class="dl-chip" href="datasets/21a_communities_and_hotspots.json">JSON</a>
      </div>
      {tbl_communities}
    </div>

    <div id="ev-ints" class="ev-panel">
      <div class="dl-bar">
        <strong>Dataset #21B — Critical Intersections, Grade-Separated Flyovers &amp; Access Bottleneck Nodes (16 Nodes):</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/21b_intersections_and_nodes.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/21b_intersections_and_nodes.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/21b_intersections_and_nodes.html">Browser Table</a>
        <a class="dl-chip" href="datasets/21b_intersections_and_nodes.json">JSON</a>
      </div>
      {tbl_intersections}
    </div>

    <div id="ev-incs" class="ev-panel">
      <div class="dl-bar">
        <strong>Dataset #21C — Active RTA &amp; SRTA Capital Roadworks, diversions &amp; Work-Zone Constrictions (5 Active Zones):</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/21c_traffic_incidents_and_roadworks.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/21c_traffic_incidents_and_roadworks.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/21c_traffic_incidents_and_roadworks.html">Browser Table</a>
        <a class="dl-chip" href="datasets/21c_traffic_incidents_and_roadworks.json">JSON</a>
      </div>
      {tbl_incidents}
    </div>

    <div id="ev-subdevs" class="ev-panel">
      <div class="dl-bar">
        <strong>Dataset #21D — JVC High-Rise Sub-Development Clusters Linked to Task 1 Developer Inventory (5 Clusters / 25 Towers):</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/21d_jvc_and_community_subdevelopments.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/21d_jvc_and_community_subdevelopments.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/21d_jvc_and_community_subdevelopments.html">Browser Table</a>
        <a class="dl-chip" href="datasets/21d_jvc_and_community_subdevelopments.json">JSON</a>
      </div>
      {tbl_subdevs}
    </div>

    <div id="ev-tds" class="ev-panel">
      <div class="dl-bar">
        <strong>Dataset #15 — Dubai, Sharjah &amp; UAE Open-Data and Transport Source Register (18 Datasets × 16 Required Fields):</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/15_transport_open_data_register.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/15_transport_open_data_register.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/15_transport_open_data_register.html">Browser Table</a>
        <a class="dl-chip" href="datasets/15_transport_open_data_register.json">JSON</a>
      </div>
      {tbl_tds}
    </div>

    <div id="ev-tomtom" class="ev-panel">
      <div class="dl-bar">
        <strong>Dataset #18 — TomTom API, Licensing, Rate-Limit &amp; Commercial Provider Comparison Matrix (6 Providers):</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/18_tomtom_and_provider_assessment.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/18_tomtom_and_provider_assessment.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/18_tomtom_and_provider_assessment.html">Browser Table</a>
        <a class="dl-chip" href="datasets/18_tomtom_and_provider_assessment.json">JSON</a>
      </div>
      {tbl_providers}
    </div>

    <div id="ev-tis" class="ev-panel">
      <div class="dl-bar">
        <strong>Dataset #19 — Traffic Impact Studies (TIS), RTA DTGPRM Trip Generation Rates &amp; HGV Construction Logistics (8 Records):</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/19_traffic_impact_studies_and_logistics.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/19_traffic_impact_studies_and_logistics.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/19_traffic_impact_studies_and_logistics.html">Browser Table</a>
        <a class="dl-chip" href="datasets/19_traffic_impact_studies_and_logistics.json">JSON</a>
      </div>
      {tbl_tis}
    </div>

    <div id="ev-park" class="ev-panel">
      <div class="dl-bar">
        <strong>Dataset #20 — Parking Facilities (Parkin PJSC, Metro Park-and-Ride), DEWA EV Chargers &amp; Delivery-Bike Mobility (7 Records):</strong>
        <a class="dl-chip" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/20_parking_and_mobility_facilities.csv">GitHub Raw CSV</a>
        <a class="dl-chip" href="csv_raw/20_parking_and_mobility_facilities.csv.txt">Plain-Text (.csv.txt)</a>
        <a class="dl-chip" href="csv_view/20_parking_and_mobility_facilities.html">Browser Table</a>
        <a class="dl-chip" href="datasets/20_parking_and_mobility_facilities.json">JSON</a>
      </div>
      {tbl_parking}
    </div>

    <div id="ev-arch" class="ev-panel">
      <div class="detail-card" style="line-height:1.6;">
        <h4>1. Dataset Identifier Range Reconciliation (`15` through `22` = 11 Distinct Datasets + 18-Table Spatial SQLite DB)</h4>
        <p>Why do identifiers <code>15</code> through <code>22</code> (8 root numbers) yield <strong>11 new CSV/JSON datasets</strong>? Because identifier <code>21</code> (the Spatial Database package) is normalized into <strong>4 distinct spatial entity datasets (<code>21a</code>, <code>21b</code>, <code>21c</code>, <code>21d</code>)</strong> plus the 7 single-numbered datasets (<code>15</code>, <code>16</code>, <code>17</code>, <code>18</code>, <code>19</code>, <code>20</code>, <code>22</code>) = <strong>11 datasets (157 rows)</strong>, all compiled into <code>21_task2_spatial_database.sqlite</code> (18 tables) and <code>11_consolidated_database.sqlite</code> (29 tables, 1,498 total rows).</p>
        <h4>2. Technical Architecture, Epistemic Methodology &amp; Community Digital Twin Roadmap (Sections 11, 16 &amp; 17)</h4>
        <p><strong>Data Pipeline &amp; Spatial Reference Architecture:</strong> Task 1 + Task 2 Validated Repository (85 projects, 205 documents, 452 sources) → Normalized Relational &amp; Spatial Store (<code>21_task2_spatial_database.sqlite</code> / PostGIS-ready schema + <code>dubai_sharjah_gis_bundle.geojson</code> with 123 WGS84 <code>EPSG:4326</code> features and exact nearest-vertex Haversine distance math) → Deterministic Spatial &amp; Temporal Query Engine → Interactive 11-Layer Geospatial Map + Map-Linked Q&amp;A Layer.</p>
        <p><strong>Strict Epistemic Guardrails (Zero Fabricated Telemetry &amp; Two-Term BPR + Modelled Bottleneck-Delay Assumption Reproducibility):</strong> Every road capacity separates <code>PUBLISHED_OFFICIAL</code> (RTA/SRTA statutory corridor capacities and upgrade travel-time reduction targets) from <code>HCM_7TH_EDITION_ESTIMATE</code>. TomTom Dubai Traffic Index (<code>SRC-436</code>, <code>https://www.tomtom.com/traffic-index/city/dubai/</code>) is used strictly at the city-wide level (<code>OBS-DXB-CITY-00</code>: 31.3 km/h average speed, 19 min 10 sec per 10 km, 42.7% annual congestion, 26.3 km/h rush-hour average, 32.1 km/h AM rush [18 min 41 sec, 42.3% congestion], 22.6 km/h PM rush [26 min 33 sec, 94.4% congestion]). All 21 corridor-level speed, volume, and congestion records (<code>OBS-DXB-001..015</code>, <code>OBS-SHJ-001..006</code>) are classified as <strong>Modelled Corridor Estimates</strong> derived via a formula-based <strong>Uninterrupted BPR Link Term (<code>t_BPR, v_BPR</code>) + Modelled, HCM-Informed Bottleneck-Delay Assumption (<code>+d_adj</code>)</strong>, and all daily HGV figures are classified as <strong>Scenario-Based Estimated Daily HGV Movements</strong> with 5 explicit modelling assumptions.</p>
      </div>
    </div>
    </details>
  </section>
"""
    # Append client-side JavaScript engine
    js_code = r"""
  <script id="task2Payload" type="application/json">__PAYLOAD_JSON__</script>
  <script>
    const DATA = JSON.parse(document.getElementById("task2Payload").textContent);
    let map;
    let baseTileLayer;
    let currentTimeWindow = "Evening Peak (17:00–20:00)";
    let currentRadiusMeters = 1500;
    let is3DPerspective = false;
    let currentUseCase = 1;
    let currentDrawerTab = "uc";
    let currentInspState = { type: "project", id: "PRJ-D6" };

    const ALL_TIME_WINDOWS = [
      "Morning Peak (07:30–09:30)",
      "Midday (12:00–14:00)",
      "Evening Peak (17:00–20:00)",
      "Night (22:00–05:00)"
    ];

    const layerGroups = {
      communities: L.layerGroup(),
      devbounds: L.layerGroup(),
      roads: L.layerGroup(),
      traffic: L.layerGroup(),
      intersections: L.layerGroup(),
      incidents: L.layerGroup(),
      transit: L.layerGroup(),
      facilities: L.layerGroup(),
      parking: L.layerGroup(),
      impacts: L.layerGroup(),
      projects: L.layerGroup()
    };

    function parseCoord(str) {
      const m = String(str).match(/[-+]?\d+\.\d+/g);
      return m && m.length >= 2 ? [parseFloat(m[0]), parseFloat(m[1])] : [25.1972, 55.2744];
    }

    function congestionColor(levelStr) {
      const s = String(levelStr || "");
      if (s.includes("Unavailable")) return "#64748b";
      if (s.includes("Severe")) return "#ef4444";
      if (s.includes("High")) return "#f97316";
      if (s.includes("Moderate")) return "#eab308";
      return "#10b981";
    }

    function parseSpeedLimit(str) {
      const m = String(str || "80").match(/\d+/);
      return m ? parseFloat(m[0]) : 80.0;
    }

    function parseCapacity(str, lanes) {
      const m = String(str || "").replace(/,/g, "").match(/\d{3,5}/);
      return m ? parseFloat(m[0]) : (parseFloat(lanes || 3) * 1800.0);
    }

    // Deterministic 4-Window BPR + Bottleneck Corridor Profile Engine
    // Uses exact Dataset #17 observation when available, or computes a diurnal BPR profile calibrated to the road's baseline
    function getCorridorProfileForWindow(road, tp) {
      const roadObs = DATA.observations.filter(o => o.road_id === road.road_id);
      const exact = roadObs.find(o => o.time_period === tp);
      if (exact) {
        return { obs: exact, exactMatch: true };
      }

      const v0 = roadObs.length > 0 ? parseFloat(roadObs[0].free_flow_speed_kmh) : parseSpeedLimit(road.speed_limit_kmh);
      const cRef = roadObs.length > 0 ? parseFloat(roadObs[0].reference_capacity_vph_dir) : parseCapacity(road.capacity_vph_per_dir, road.lanes_per_direction);
      const baseVc = roadObs.length > 0 ? parseFloat(roadObs[0].vc_ratio) : (road.road_type.includes("Freeway") ? 0.82 : 0.88);
      const baseDadj = roadObs.length > 0 ? parseFloat(roadObs[0].bottleneck_and_control_delay_min_per_10km) : (road.road_type.includes("Freeway") ? 3.2 : 6.8);

      let vcFactor = 1.0;
      let dFactor = 1.0;
      if (tp.includes("Morning")) {
        vcFactor = 0.94;
        dFactor = 0.82;
      } else if (tp.includes("Midday")) {
        vcFactor = 0.72;
        dFactor = 0.42;
      } else if (tp.includes("Evening")) {
        vcFactor = 1.02;
        dFactor = 1.05;
      } else if (tp.includes("Night")) {
        vcFactor = 0.34;
        dFactor = 0.14;
      }

      const vc = Math.round(Math.min(1.14, Math.max(0.22, baseVc * vcFactor)) * 100) / 100;
      const vDem = Math.round(cRef * vc);
      const t0 = Math.round((600.0 / v0) * 100) / 100;
      const tBpr = Math.round(t0 * (1.0 + 0.15 * Math.pow(vc, 4)) * 100) / 100;
      const vBpr = Math.round((v0 / (1.0 + 0.15 * Math.pow(vc, 4))) * 10) / 10;
      const dAdj = Math.round(baseDadj * dFactor * 100) / 100;
      const tTot = Math.round((tBpr + dAdj) * 100) / 100;
      const vCorr = Math.round((600.0 / tTot) * 10) / 10;
      const ratio = vCorr / v0;

      let congTier = "Low";
      if (ratio < 0.42) congTier = "Severe";
      else if (ratio < 0.59) congTier = "High";
      else if (ratio < 0.76) congTier = "Moderate";

      const synthObs = {
        observation_id: roadObs.length > 0 ? `${roadObs[0].observation_id} (${tp.split(' ')[0]} Diurnal BPR)` : `BPR-${road.road_id}`,
        road_id: road.road_id,
        time_period: tp,
        free_flow_speed_kmh: v0,
        free_flow_time_min_per_10km: t0,
        modelled_demand_vph_dir: vDem,
        reference_capacity_vph_dir: cRef,
        vc_ratio: vc,
        bpr_uninterrupted_time_min_per_10km: tBpr,
        bpr_uninterrupted_speed_kmh: vBpr,
        bottleneck_and_control_delay_min_per_10km: dAdj,
        travel_time_min_per_10km: tTot,
        average_speed_kmh: vCorr,
        congestion_level: `${congTier} (Modelled Diurnal Estimate: v/v0 = ${ratio.toFixed(2)}; v_BPR = ${vBpr} km/h -> ${vCorr} km/h after +${dAdj} min/10km bottleneck assumption)`,
        traffic_volume_vph: `Modelled ~${vDem.toLocaleString()} vph/dir (${tp.includes('Midday') || tp.includes('Night') ? 'Active HGV Haulage Permitted' : 'HGV Peak Restriction Window'})`,
        officially_published_corridor_benchmark: roadObs.length > 0 ? roadObs[0].officially_published_corridor_benchmark : `Published statutory speed limit ${road.speed_limit_kmh} & capacity ${road.capacity_vph_per_dir}`,
        modelled_assumptions_and_derivation: `Diurnal BPR scaling for ${tp}: V/C=${vc} (${vDem}/${cRef} vph/dir) -> t_BPR=${tBpr} min/10km + d_adj=+${dAdj} min/10km = ${tTot} min/10km (${vCorr} km/h).`,
        comparison_period: roadObs.length > 0 ? roadObs[0].comparison_period : "2024–2026 Corridor Capacity & Phased Upgrade Baseline",
        source_id: road.source_id,
        source_url: "",
        publication_date: "2026-11-09"
      };
      return { obs: synthObs, exactMatch: false };
    }

    function getRoadObsForWindow(roadId, tp) {
      const road = DATA.roads.find(r => r.road_id === roadId);
      if (!road) return null;
      return getCorridorProfileForWindow(road, tp).obs;
    }

    function getWindowHgvBannerInfo(tp) {
      if (tp.includes("Morning")) {
        return {
          shortTp: "AM Peak (07:30–09:30)",
          hgvBadge: "🚫 HGV Ban 06:30–08:30 (E11/E44/D61)",
          text: "🚫 HGVs Banned on E11/E44/D61 (06:30–08:30 AM Rush) — Commuter Queue Window",
          color: "#fca5a5",
          hgvStyle: "background:rgba(239,68,68,0.22); color:#fca5a5; border:1px solid #ef4444; padding:1px 6px; border-radius:4px; font-weight:700; font-size:0.68rem;",
          narrative: "Morning commuter wave toward Business Bay, DIFC & Dubai/Sharjah employment hubs. Heavy construction trucks are restricted on primary passenger arterials; commuter queues dominate Hessa St (29 km/h) and E311 Southbound (28 km/h)."
        };
      }
      if (tp.includes("Midday")) {
        return {
          shortTp: "Midday HGV (12:00–14:00)",
          hgvBadge: "🚛 HGV Haulage Active (08:30–16:30)",
          text: "🚛 ACTIVE HGV CONCRETE & REBAR HAULAGE WINDOW (08:30–16:30 Permitted)",
          color: "#fde68a",
          hgvStyle: "background:rgba(245,158,11,0.24); color:#fde68a; border:1px solid #f59e0b; padding:1px 6px; border-radius:4px; font-weight:700; font-size:0.68rem;",
          narrative: "Passenger commuter peaks subside (Hessa St rises to 48 km/h; Al Khail Rd rises to 78 km/h), while active daytime HGV concrete mixers, rebar trailers, and earthworks tippers operate across JVC, Business Bay, Creek Harbour & Dubai South."
        };
      }
      if (tp.includes("Night")) {
        return {
          shortTp: "Night Pour Window (22:00–05:00)",
          hgvBadge: "🌙 Night Concrete Pours (22:00–05:00)",
          text: "🌙 NIGHT MASS CONCRETE POUR & HEAVY FREIGHT WINDOW (22:00–05:00 Free-Flow)",
          color: "#6ee7b7",
          hgvStyle: "background:rgba(16,185,129,0.22); color:#6ee7b7; border:1px solid #10b981; padding:1px 6px; border-radius:4px; font-weight:700; font-size:0.68rem;",
          narrative: "Free-flow passenger conditions across all corridors (Hessa St 68 km/h; SZR 88 km/h; Al Khail 92 km/h). Continuous nocturnal raft-foundation concrete pours and oversized structural steel deliveries operate unimpeded."
        };
      }
      return {
        shortTp: "PM Peak (17:00–20:00)",
        hgvBadge: "🚫 HGV Ban 17:00–20:00 (E11/E44/D61)",
        text: "🚫 HGVs Banned on E11/E44/D61 (17:00–20:00 PM Rush) — Peak Commuter Bottlenecks",
        color: "#fca5a5",
        hgvStyle: "background:rgba(239,68,68,0.22); color:#fca5a5; border:1px solid #ef4444; padding:1px 6px; border-radius:4px; font-weight:700; font-size:0.68rem;",
        narrative: "Highest diurnal congestion across the network. Return commuter flows create severe bottlenecks on Hessa St West (25 km/h), JVC Circle Blvd (21 km/h), Financial Centre Rd (22 km/h), and SZR (44 km/h)."
      };
    }

    // =========================================================================
    // HAIO.SG-GRADE 3D ARCHITECTURAL MASSING, STACK & FLOOR ENGINE (MAPLIBRE GL)
    // =========================================================================
    let map3d = null;
    let map3dLoaded = false;
    let map3dMarkers = [];
    let is3DBlocksEnabled = true;
    let currentCameraDim = "3D";
    let currentBasemapMode = "sat";
    let selected3DProjectId = "PRJ-D11";
    let active3DBlock = "ALL";
    let active3DFloor = "ALL";
    let active3DStack = "ALL";
    let active3DShowMe = "all";

    function projectScaleStyle(p) {
      const v = String(p.published_investment_value || "");
      if (v.includes("55B") || v.includes("50B") || v.includes("35B") || v.includes("30B") || v.includes("25B") || v.includes("128B")) {
        return { radius: 11, fillColor: "#fbbf24", color: "#fff", weight: 2.5, tier: "Mega-Project (≥ AED 25B)" };
      }
      if (v.includes("18B") || v.includes("15B") || v.includes("13B") || v.includes("12B") || v.includes("10B") || v.includes("8B") || v.includes("7B") || v.includes("6B") || v.includes("5B")) {
        return { radius: 8, fillColor: "#38bdf8", color: "#0f172a", weight: 2, tier: "Major Masterplan (AED 5B–25B)" };
      }
      return { radius: 5.5, fillColor: "#22d3ee", color: "#0f172a", weight: 1.5, tier: "Active Development (< AED 5B)" };
    }

    function getProject3DSpec(p) {
      const fh = String(p.floors_and_height || "");
      const tb = String(p.towers_and_buildings_count || "");
      const uv = String(p.apartments_and_villas_count || "");
      let storeys = 52;
      const fm = fh.match(/(\d{2,3})\s*(?:floors|storeys|levels|F|G\+)/i) || fh.match(/G\+\d+P\+(\d{2,3})/i) || fh.match(/(\d{2,3})/);
      if (fm) {
        const parsed = parseInt(fm[1], 10);
        if (parsed >= 12 && parsed <= 160) storeys = parsed;
      }
      if (p.project_id === "PRJ-D10") storeys = 131;
      else if (p.project_id === "PRJ-D11") storeys = 104;
      else if (p.project_id === "PRJ-D12") storeys = 122;
      else if (p.project_id === "PRJ-D13") storeys = 106;
      else if (p.project_id === "PRJ-D3") storeys = 131;
      else if (p.project_id === "PRJ-D14") storeys = 71;
      else if (p.project_id === "PRJ-D20") storeys = 65;

      let homes = 420;
      const um = uv.replace(/,/g, "").match(/(\d{2,6})/);
      if (um) homes = parseInt(um[1], 10);

      let blocksCount = 2;
      if (tb.includes("Single Supertall") && p.project_id !== "PRJ-D11" && p.project_id !== "PRJ-D12") blocksCount = 1;

      const heightM = Math.min(340, Math.max(115, Math.round(storeys * 2.85)));
      const stacksPerBlock = 4;
      const blocks = [];
      for (let b = 1; b <= blocksCount; b++) {
        const bStoreys = b === 1 ? storeys : Math.max(24, Math.round(storeys * 0.68));
        const bHeight = b === 1 ? heightM : Math.round(heightM * 0.68);
        blocks.push({
          blockNum: b,
          id: `B${b}`,
          label: `Block ${b}`,
          stacksLabel: b === 1 ? "Stacks 01 to 04" : "Stacks 05 to 08",
          storeys: bStoreys,
          heightM: bHeight,
          dLon: b === 1 ? -0.00038 : 0.00058,
          dLat: b === 1 ? 0.00028 : -0.00036
        });
      }
      return { storeys, homes, blocksCount, stacksPerBlock, heightM, blocks };
    }

    // Build smooth circular/octagonal active construction site ground perimeter (zero fake rectangular boxes)
    function makeSiteCircleRing(cLon, cLat, radiusMeters, steps = 28) {
      const coords = [];
      const dLat = radiusMeters / 111320.0;
      const dLon = radiusMeters / (111320.0 * Math.cos((cLat * Math.PI) / 180.0));
      for (let i = 0; i <= steps; i++) {
        const ang = (i / steps) * 2.0 * Math.PI;
        coords.push([
          +(cLon + Math.cos(ang) * dLon).toFixed(6),
          +(cLat + Math.sin(ang) * dLat).toFixed(6)
        ]);
      }
      return coords;
    }

    function buildProjectSiteZonesGeoJSON() {
      const features = [];
      const emFilter = document.getElementById("emirateSelect") ? document.getElementById("emirateSelect").value : "ALL";
      const q = (document.getElementById("searchInput")?.value || "").toLowerCase().trim();

      DATA.projects.forEach(p => {
        if (emFilter !== "ALL" && p.emirate !== emFilter) return;
        if (q && !JSON.stringify(p).toLowerCase().includes(q)) return;
        const [lat, lon] = parseCoord(p.coordinates);
        const st = projectScaleStyle(p);
        const isSel = (p.project_id === selected3DProjectId);
        const radM = st.radius >= 11 ? 320 : (st.radius >= 8 ? 220 : 150);

        features.push({
          type: "Feature",
          properties: {
            project_id: p.project_id,
            color: isSel ? "#2563eb" : st.fillColor,
            fillOpacity: isSel ? 0.28 : 0.16,
            lineWidth: isSel ? 3.0 : 1.8
          },
          geometry: { type: "Polygon", coordinates: [makeSiteCircleRing(lon, lat, radM)] }
        });
      });

      DATA.subdevs.forEach(sd => {
        if (emFilter !== "ALL" && sd.emirate !== emFilter) return;
        if (q && !JSON.stringify(sd).toLowerCase().includes(q)) return;
        features.push({
          type: "Feature",
          properties: {
            project_id: sd.subdev_id,
            color: "#a855f7",
            fillOpacity: 0.18,
            lineWidth: 1.8
          },
          geometry: { type: "Polygon", coordinates: [makeSiteCircleRing(sd.longitude, sd.latitude, 160)] }
        });
      });

      return { type: "FeatureCollection", features };
    }

    function formatBearingCompass(b) {
      const deg = ((Math.round(b) % 360) + 360) % 360;
      const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
      const dir = dirs[Math.round(deg / 45) % 8];
      return { deg, label: `${dir} ${deg}°` };
    }

    function updateCompassUI() {
      if (!map3d) return;
      const { deg, label } = formatBearingCompass(map3d.getBearing());
      const lblEl = document.getElementById("compassLabel");
      if (lblEl) lblEl.textContent = label;
      const svgEl = document.getElementById("compassSvg");
      if (svgEl) svgEl.style.transform = `rotate(${-deg}deg)`;
    }

    function orbitCameraStep() {
      if (!map3d) return;
      const nextBearing = (Math.round(map3d.getBearing() / 45) * 45 + 45) % 360;
      map3d.easeTo({ bearing: nextBearing, pitch: currentCameraDim === "3D" ? 60 : 0, duration: 650 });
    }

    function setCameraDimension(dim) {
      currentCameraDim = dim;
      document.getElementById("btnDim2D").classList.toggle("active", dim === "2D");
      document.getElementById("btnDim3D").classList.toggle("active", dim === "3D");
      if (map3d) {
        map3d.easeTo({
          pitch: dim === "3D" ? 60 : 0,
          bearing: dim === "3D" ? 60 : 0,
          duration: 800
        });
      }
    }

    function toggle3DBlocksMassing() {
      is3DBlocksEnabled = !is3DBlocksEnabled;
      const trk = document.getElementById("blocksSwitchTrack");
      if (trk) trk.classList.toggle("on", is3DBlocksEnabled);
      if (map3d && map3dLoaded) {
        if (map3d.getLayer("osm-3d-buildings")) {
          map3d.setLayoutProperty("osm-3d-buildings", "visibility", is3DBlocksEnabled ? "visible" : "none");
        }
        if (map3d.getLayer("haio-photoreal-3d-layer")) {
          map3d.setLayoutProperty("haio-photoreal-3d-layer", "visibility", is3DBlocksEnabled ? "visible" : "none");
        }
        map3d.triggerRepaint();
      }
      sync3DMapLayers();
    }

    function backToCityMapOverview() {
      const zNow = map3d ? map3d.getZoom() : 16;
      if (zNow > 13.8) {
        switchDrawerTab("uc");
        flyBothMaps(25.125, 55.235, 11.4, 48, 28);
        document.getElementById("hudScope").textContent = "Dubai Corridors Overview";
        runUseCase(1, false);
      } else {
        showProjectInspector(selected3DProjectId || "PRJ-D11", true);
      }
    }

    function selectLensDock(idx) {
      document.querySelectorAll(".haio-lens-btn").forEach((b, i) => b.classList.toggle("active", (i + 1) === idx));
      if (idx === 1) {
        backToCityMapOverview();
      } else if (idx === 2) {
        runUseCase(2, true);
      } else if (idx === 3) {
        runUseCase(3, true);
      } else if (idx === 4) {
        showProjectInspector(selected3DProjectId || "PRJ-D11", true);
      } else if (idx === 5) {
        switchDrawerTab("insp");
        showProjectInspector("PRJ-D11", true);
      } else if (idx === 6) {
        runUseCase(4, true);
      }
    }

    function flyBothMaps(lat, lon, zoom, pitch = 60, bearing = 60) {
      const clampedZoom = Math.min(17.4, Math.max(9.0, zoom));
      if (map) {
        map.flyTo([lat, lon], Math.min(18, Math.max(9, Math.round(clampedZoom))), { duration: 0.8 });
      }
      if (map3d) {
        map3d.flyTo({
          center: [lon, lat],
          zoom: clampedZoom,
          pitch: currentCameraDim === "3D" ? pitch : 0,
          bearing: currentCameraDim === "3D" ? bearing : 0,
          duration: 1050,
          essential: true
        });
      }
    }

    // =========================================================================
    // THREE.JS PHOTOREALISTIC 3D ARCHITECTURAL ENSEMBLE & TEXTURE ENGINE
    // =========================================================================
    let three3DLayer = null;
    let threeTextureCache = {};

    function getAxaRibbedTowerTexture() {
      if (threeTextureCache.axa) return threeTextureCache.axa;
      const cv = document.createElement("canvas");
      cv.width = 1024;
      cv.height = 2048;
      const ctx = cv.getContext("2d");
      ctx.fillStyle = "#e8e3d9";
      ctx.fillRect(0, 0, cv.width, cv.height);

      const bands = 48;
      const bandH = cv.height / bands;
      for (let i = 0; i < bands; i++) {
        const y = i * bandH;
        // Sunlit warm cream-white limestone spandrel ring (top 54% of floor)
        const spH = bandH * 0.54;
        const gradSp = ctx.createLinearGradient(0, y, 0, y + spH);
        gradSp.addColorStop(0, "#f4f1ea");
        gradSp.addColorStop(0.75, "#e6e0d5");
        gradSp.addColorStop(1, "#c2bbb0");
        ctx.fillStyle = gradSp;
        ctx.fillRect(0, y, cv.width, spH);

        // Subtle vertical stone panel joints
        ctx.strokeStyle = "rgba(140, 132, 120, 0.28)";
        ctx.lineWidth = 1.5;
        for (let x = 0; x < cv.width; x += 32) {
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(x, y + spH);
          ctx.stroke();
        }

        // Recessed dark bronze-charcoal ribbon window band (bottom 46% of floor)
        const winY = y + spH;
        const winH = bandH - spH;
        const gradWin = ctx.createLinearGradient(0, winY, 0, winY + winH);
        gradWin.addColorStop(0, "#14181f");
        gradWin.addColorStop(0.35, "#26303d");
        gradWin.addColorStop(1, "#1c222b");
        ctx.fillStyle = gradWin;
        ctx.fillRect(0, winY, cv.width, winH);

        // Window mullions & subtle interior warm/cool reflections
        for (let x = 0; x < cv.width; x += 16) {
          if (((i * 13 + (x / 16) * 7) % 11) === 0) {
            ctx.fillStyle = "rgba(219, 234, 254, 0.22)";
            ctx.fillRect(x + 2, winY + 2, 12, winH - 3);
          } else if (((i * 17 + (x / 16) * 5) % 19) === 0) {
            ctx.fillStyle = "rgba(254, 243, 199, 0.20)";
            ctx.fillRect(x + 2, winY + 2, 12, winH - 3);
          }
          ctx.fillStyle = "#11151c";
          ctx.fillRect(x, winY, 2, winH);
        }
      }

      // Iconic Royal-Blue Corporate Sky-Sign Badges around the top of the cylindrical tower
      [140, 480, 790].forEach(bx => {
        const by = bandH * 3.1;
        const bw = 96;
        const bh = bandH * 3.0;
        ctx.fillStyle = "#1e3a8a";
        ctx.fillRect(bx, by, bw, bh);
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 3;
        ctx.strokeRect(bx + 3, by + 3, bw - 6, bh - 6);
        ctx.strokeStyle = "#ef4444";
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(bx + bw - 26, by + 6);
        ctx.lineTo(bx + bw - 6, by + 32);
        ctx.stroke();
        ctx.fillStyle = "#ffffff";
        ctx.font = "900 34px Inter, Arial, sans-serif";
        ctx.fillText("AXA", bx + 12, by + bh * 0.66);
      });

      const tex = new THREE.CanvasTexture(cv);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.ClampToEdgeWrapping;
      tex.anisotropy = 8;
      threeTextureCache.axa = tex;
      return tex;
    }

    function getBronzeSetbackTowerTexture() {
      if (threeTextureCache.bronze) return threeTextureCache.bronze;
      const cv = document.createElement("canvas");
      cv.width = 512;
      cv.height = 1024;
      const ctx = cv.getContext("2d");
      ctx.fillStyle = "#8a5643";
      ctx.fillRect(0, 0, cv.width, cv.height);

      const floors = 32;
      const fh = cv.height / floors;
      const cols = 10;
      const cw = cv.width / cols;

      for (let f = 0; f < floors; f++) {
        const y = f * fh;
        // Warm metallic bronze/terracotta spandrel beam
        const grad = ctx.createLinearGradient(0, y, 0, y + fh);
        grad.addColorStop(0, "#9c6652");
        grad.addColorStop(0.4, "#85523f");
        grad.addColorStop(1, "#6b3e2e");
        ctx.fillStyle = grad;
        ctx.fillRect(0, y, cv.width, fh);

        // Recessed dark bronze-tinted windows
        for (let c = 0; c < cols; c++) {
          const x = c * cw;
          ctx.fillStyle = "#22252a";
          ctx.fillRect(x + 7, y + fh * 0.28, cw - 14, fh * 0.62);
          if (((f * 7 + c * 13) % 9) === 0) {
            ctx.fillStyle = "rgba(253, 230, 138, 0.25)";
            ctx.fillRect(x + 9, y + fh * 0.32, cw - 18, fh * 0.54);
          } else {
            ctx.fillStyle = "rgba(148, 163, 184, 0.16)";
            ctx.fillRect(x + 9, y + fh * 0.32, (cw - 18) * 0.5, fh * 0.54);
          }
        }
      }

      const tex = new THREE.CanvasTexture(cv);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      tex.anisotropy = 8;
      threeTextureCache.bronze = tex;
      return tex;
    }

    function getDarkCurtainWallTexture() {
      if (threeTextureCache.darkCurtain) return threeTextureCache.darkCurtain;
      const cv = document.createElement("canvas");
      cv.width = 512;
      cv.height = 1024;
      const ctx = cv.getContext("2d");

      const bgGrad = ctx.createLinearGradient(0, 0, cv.width, cv.height);
      bgGrad.addColorStop(0, "#2b3038");
      bgGrad.addColorStop(0.5, "#1f242b");
      bgGrad.addColorStop(1, "#161a20");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, cv.width, cv.height);

      const floors = 44;
      const fh = cv.height / floors;
      const cols = 16;
      const cw = cv.width / cols;

      for (let f = 0; f < floors; f++) {
        const y = f * fh;
        // Horizontal bronze-grey spandrel line
        ctx.fillStyle = (f % 8 === 0) ? "#574c43" : "#383d45";
        ctx.fillRect(0, y, cv.width, (f % 8 === 0) ? 4 : 2.2);

        for (let c = 0; c < cols; c++) {
          const x = c * cw;
          if (((f * 11 + c * 5) % 7) === 0) {
            ctx.fillStyle = "rgba(254, 240, 138, 0.18)";
            ctx.fillRect(x + 3, y + 3, cw - 6, fh - 5);
          } else if (((f + c) % 5) === 0) {
            ctx.fillStyle = "rgba(147, 197, 253, 0.14)";
            ctx.fillRect(x + 3, y + 3, cw - 6, fh - 5);
          }
          // Vertical bronze/champagne mullion fin
          ctx.fillStyle = (c % 4 === 0) ? "#786657" : "#3f4650";
          ctx.fillRect(x, y, (c % 4 === 0) ? 3 : 1.5, fh);
        }
      }

      const tex = new THREE.CanvasTexture(cv);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      tex.anisotropy = 8;
      threeTextureCache.darkCurtain = tex;
      return tex;
    }

    function getBlueGlassCurtainTexture() {
      if (threeTextureCache.blueCurtain) return threeTextureCache.blueCurtain;
      const cv = document.createElement("canvas");
      cv.width = 512;
      cv.height = 1024;
      const ctx = cv.getContext("2d");

      const g = ctx.createLinearGradient(0, 0, cv.width, cv.height);
      g.addColorStop(0, "#4b6b88");
      g.addColorStop(0.45, "#2d4860");
      g.addColorStop(1, "#1e3246");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, cv.width, cv.height);

      const floors = 40;
      const fh = cv.height / floors;
      for (let f = 0; f < floors; f++) {
        const y = f * fh;
        ctx.fillStyle = "#cbd5e1";
        ctx.fillRect(0, y, cv.width, 2.5);
        for (let x = 0; x < cv.width; x += 24) {
          ctx.fillStyle = "rgba(226, 232, 240, 0.35)";
          ctx.fillRect(x, y, 1.8, fh);
          if (((f * 5 + (x / 24)) % 6) === 0) {
            ctx.fillStyle = "rgba(186, 230, 253, 0.22)";
            ctx.fillRect(x + 3, y + 3, 18, fh - 5);
          }
        }
      }

      const tex = new THREE.CanvasTexture(cv);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      tex.anisotropy = 8;
      threeTextureCache.blueCurtain = tex;
      return tex;
    }

    function getRibbedLimestoneTowerTexture() {
      if (threeTextureCache.ribbedLimestone) return threeTextureCache.ribbedLimestone;
      const cv = document.createElement("canvas");
      cv.width = 512;
      cv.height = 1024;
      const ctx = cv.getContext("2d");
      ctx.fillStyle = "#e5e0d5";
      ctx.fillRect(0, 0, 512, 1024);
      const floors = 16;
      const bh = 1024 / floors;
      for (let i = 0; i < floors; i++) {
        const y = i * bh;
        ctx.fillStyle = "#f1ede4";
        ctx.fillRect(0, y, 512, bh * 0.46);
        ctx.fillStyle = "#cfc8b8";
        ctx.fillRect(0, y + bh * 0.42, 512, bh * 0.06);
        ctx.fillStyle = "#1e293b";
        ctx.fillRect(0, y + bh * 0.48, 512, bh * 0.52);
        for (let x = 0; x < 512; x += 24) {
          ctx.fillStyle = "#cbd5e1";
          ctx.fillRect(x, y + bh * 0.48, 3, bh * 0.52);
          if ((i * 7 + x) % 5 === 0) {
            ctx.fillStyle = "rgba(186, 230, 253, 0.28)";
            ctx.fillRect(x + 4, y + bh * 0.52, 16, bh * 0.42);
          }
        }
      }
      const tex = new THREE.CanvasTexture(cv);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      tex.anisotropy = 8;
      threeTextureCache.ribbedLimestone = tex;
      return tex;
    }

    function getPodiumTerracottaTexture() {
      if (threeTextureCache.podiumBase) return threeTextureCache.podiumBase;
      const cv = document.createElement("canvas");
      cv.width = 1024;
      cv.height = 512;
      const ctx = cv.getContext("2d");

      // Rich terracotta/burgundy architectural stone facade (matching W Residences podium base)
      const g = ctx.createLinearGradient(0, 0, 0, cv.height);
      g.addColorStop(0, "#6b2d29");
      g.addColorStop(0.65, "#54201d");
      g.addColorStop(1, "#3b1513");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, cv.width, cv.height);

      // Top white architectural slab cornice
      ctx.fillStyle = "#f1f5f9";
      ctx.fillRect(0, 0, cv.width, 24);
      // Mid-level horizontal stone trim
      ctx.fillStyle = "#7f3934";
      ctx.fillRect(0, cv.height * 0.48, cv.width, 10);

      // Vertical architectural fins & dark recessed storefront glazing at street level
      for (let x = 24; x < cv.width - 24; x += 48) {
        ctx.fillStyle = "#451815";
        ctx.fillRect(x, 28, 6, cv.height - 28);
        // Ground-floor double-height retail/lobby glass
        ctx.fillStyle = "#18222d";
        ctx.fillRect(x + 10, cv.height * 0.56, 32, cv.height * 0.38);
        ctx.fillStyle = "rgba(253, 230, 138, 0.22)";
        ctx.fillRect(x + 14, cv.height * 0.60, 24, cv.height * 0.28);
      }

      // Signature Circular Architectural Window Portal on left-center of podium
      ctx.save();
      ctx.beginPath();
      ctx.arc(260, cv.height * 0.46, 56, 0, Math.PI * 2);
      ctx.fillStyle = "#1e293b";
      ctx.fill();
      ctx.lineWidth = 8;
      ctx.strokeStyle = "#8c423c";
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(260, cv.height * 0.46, 40, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(125, 211, 252, 0.25)";
      ctx.fill();
      ctx.restore();

      const tex = new THREE.CanvasTexture(cv);
      tex.anisotropy = 8;
      threeTextureCache.podiumBase = tex;
      return tex;
    }

    function getPodiumSmokedGlassTexture() {
      if (threeTextureCache.podiumGlass) return threeTextureCache.podiumGlass;
      const cv = document.createElement("canvas");
      cv.width = 1024;
      cv.height = 512;
      const ctx = cv.getContext("2d");

      // Sleek dark obsidian smoked-glass curtain wall
      const g = ctx.createLinearGradient(0, 0, cv.width, cv.height);
      g.addColorStop(0, "#1e2936");
      g.addColorStop(0.45, "#111821");
      g.addColorStop(0.55, "#263545");
      g.addColorStop(1, "#0f151d");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, cv.width, cv.height);

      // Diagonal sky-reflection sheen across the glass box
      ctx.fillStyle = "rgba(186, 230, 253, 0.12)";
      ctx.beginPath();
      ctx.moveTo(cv.width * 0.18, 0);
      ctx.lineTo(cv.width * 0.46, 0);
      ctx.lineTo(cv.width * 0.28, cv.height);
      ctx.lineTo(cv.width * 0.02, cv.height);
      ctx.closePath();
      ctx.fill();

      // 6 internal podium floors visible through smoked glass
      for (let f = 1; f < 6; f++) {
        const y = (f / 6) * cv.height;
        ctx.fillStyle = "rgba(148, 163, 184, 0.28)";
        ctx.fillRect(0, y, cv.width, 4);
      }

      // Crisp vertical aluminum curtain-wall mullions
      for (let x = 0; x < cv.width; x += 28) {
        ctx.fillStyle = (x % 112 === 0) ? "rgba(226, 232, 240, 0.55)" : "rgba(148, 163, 184, 0.25)";
        ctx.fillRect(x, 0, (x % 112 === 0) ? 3.5 : 1.5, cv.height);
      }

      const tex = new THREE.CanvasTexture(cv);
      tex.anisotropy = 8;
      threeTextureCache.podiumGlass = tex;
      return tex;
    }

    function getRooftopGardenTexture() {
      if (threeTextureCache.roofGarden) return threeTextureCache.roofGarden;
      const cv = document.createElement("canvas");
      cv.width = 512;
      cv.height = 512;
      const ctx = cv.getContext("2d");

      // Travertine stone deck base
      ctx.fillStyle = "#d6d3cd";
      ctx.fillRect(0, 0, 512, 512);

      // Outer lush green landscaped lawn beds
      ctx.fillStyle = "#276738";
      ctx.fillRect(22, 22, 468, 468);

      // Stone garden walkways & central amenity terrace
      ctx.strokeStyle = "#e2e8f0";
      ctx.lineWidth = 18;
      ctx.strokeRect(64, 64, 384, 384);

      // Central wooden pergola & sky-pool deck
      ctx.fillStyle = "#78553a";
      ctx.fillRect(140, 110, 232, 160);
      ctx.fillStyle = "#0ea5e9";
      ctx.fillRect(164, 130, 184, 85);

      // Varied botanical foliage patches
      const greens = ["#15803d", "#166534", "#22c55e", "#14532d", "#4ade80"];
      for (let i = 0; i < 90; i++) {
        const gx = 32 + ((i * 73) % 448);
        const gy = 32 + ((i * 137) % 448);
        if (gx > 135 && gx < 375 && gy > 105 && gy < 275) continue;
        ctx.fillStyle = greens[i % greens.length];
        ctx.beginPath();
        ctx.arc(gx, gy, 10 + (i % 12), 0, Math.PI * 2);
        ctx.fill();
      }

      const tex = new THREE.CanvasTexture(cv);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      tex.anisotropy = 8;
      threeTextureCache.roofGarden = tex;
      return tex;
    }

    function getHeroWhiteTowerTexture(storeys, showMode, flrZone, stkFilter, wingIndex) {
      const key = `hero_${storeys}_${showMode}_${flrZone}_${stkFilter}_${wingIndex}`;
      if (threeTextureCache[key]) return threeTextureCache[key];

      const cv = document.createElement("canvas");
      cv.width = 512;
      cv.height = 2048;
      const ctx = cv.getContext("2d");

      // Crisp sunlit architectural white facade (exact W Residences Marina View white massing)
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, cv.width, cv.height);

      const fCount = Math.min(85, Math.max(36, storeys || 51));
      const fh = cv.height / fCount;

      for (let f = 0; f < fCount; f++) {
        // Floor index from bottom (1 = lowest floor, fCount = top penthouse)
        const floorNum = fCount - f;
        const y = f * fh;

        // Check if this floor/wing is highlighted by the user's BLOCK / FLOOR / STACK / SHOW ME filter
        let highlightCol = null;
        const is4BRWing = (wingIndex % 2 === 0);
        if (showMode === "4br" && is4BRWing) highlightCol = "#fbbf24";
        else if (showMode === "5br" && !is4BRWing) highlightCol = "#34d399";
        else if (showMode === "4br_5br_mix") highlightCol = is4BRWing ? "#fbbf24" : "#34d399";
        else if (showMode === "hgv") highlightCol = (floorNum <= fCount * 0.45) ? "#f97316" : "#60a5fa";

        if (flrZone === "LOW" && floorNum <= Math.round(fCount * 0.35)) highlightCol = "#3b82f6";
        else if (flrZone === "MID" && floorNum > Math.round(fCount * 0.35) && floorNum <= Math.round(fCount * 0.72)) highlightCol = "#f59e0b";
        else if (flrZone === "HIGH" && floorNum > Math.round(fCount * 0.72)) highlightCol = "#10b981";

        if (stkFilter === "S1" && (wingIndex === 0 || wingIndex === 1 || wingIndex === 2)) highlightCol = "#fbbf24";
        else if (stkFilter === "S2" && (wingIndex === 3 || wingIndex === 4 || wingIndex === 5)) highlightCol = "#34d399";

        if (highlightCol) {
          ctx.fillStyle = highlightCol;
          ctx.fillRect(0, y + 2, cv.width, fh - 3);
        } else {
          // Subtle sunlit slab gradient on pure white
          const sg = ctx.createLinearGradient(0, y, 0, y + fh);
          sg.addColorStop(0, "#ffffff");
          sg.addColorStop(0.82, "#f8fafc");
          sg.addColorStop(1, "#e2e8f0");
          ctx.fillStyle = sg;
          ctx.fillRect(0, y, cv.width, fh);
        }

        // Crisp horizontal floor slab shadow line
        ctx.fillStyle = "#cbd5e1";
        ctx.fillRect(0, y, cv.width, 2.4);

        // Neat architectural window / balcony openings across each stack floor
        const winCols = [44, 118, 220, 310, 396, 448];
        winCols.forEach((wx, idx) => {
          const ww = (idx % 2 === 0) ? 28 : 42;
          ctx.fillStyle = highlightCol ? "rgba(15, 23, 42, 0.45)" : "#94a3b8";
          ctx.fillRect(wx, y + fh * 0.24, ww, fh * 0.56);
          ctx.fillStyle = highlightCol ? "rgba(255, 255, 255, 0.35)" : "#cbd5e1";
          ctx.fillRect(wx + 2, y + fh * 0.28, ww - 4, fh * 0.48);
        });
      }

      // Vertical stack recess shadow channels
      ctx.fillStyle = "rgba(148, 163, 184, 0.42)";
      ctx.fillRect(188, 0, 5, cv.height);
      ctx.fillRect(368, 0, 5, cv.height);

      const tex = new THREE.CanvasTexture(cv);
      tex.anisotropy = 8;
      threeTextureCache[key] = tex;
      return tex;
    }

    function addBoxWithEdges(parent, w, h, d, x, yBottom, z, mat, edgeColor = null, rotY = 0) {
      const geo = new THREE.BoxGeometry(w, h, d);
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(x, yBottom + h / 2, z);
      if (rotY) mesh.rotation.y = rotY;
      parent.add(mesh);

      if (edgeColor !== null) {
        const edges = new THREE.EdgesGeometry(geo);
        const line = new THREE.LineSegments(
          edges,
          new THREE.LineBasicMaterial({ color: edgeColor, transparent: true, opacity: 0.55 })
        );
        line.position.copy(mesh.position);
        line.rotation.copy(mesh.rotation);
        parent.add(line);
      }
      return mesh;
    }

    function addTreeCanopyCluster(parent, x, yBase, z, scale = 1.0) {
      const trunkGeo = new THREE.CylinderGeometry(0.6 * scale, 0.9 * scale, 3.5 * scale, 6);
      const trunkMat = new THREE.MeshLambertMaterial({ color: 0x4a3525 });
      const trunk = new THREE.Mesh(trunkGeo, trunkMat);
      trunk.position.set(x, yBase + 1.75 * scale, z);
      parent.add(trunk);

      const colors = [0x1e5631, 0x2d6a3e, 0x166534, 0x15803d, 0x14532d];
      const col = colors[Math.abs(Math.round(x * 7 + z * 13)) % colors.length];
      const crownGeo = new THREE.DodecahedronGeometry(4.6 * scale, 1);
      const crownMat = new THREE.MeshLambertMaterial({ color: col });
      const crown = new THREE.Mesh(crownGeo, crownMat);
      crown.position.set(x, yBase + 5.4 * scale, z);
      crown.scale.set(1.22, 0.85, 1.22);
      parent.add(crown);
    }

    function getCreamLowRiseTexture() {
      if (threeTextureCache.creamLow) return threeTextureCache.creamLow;
      const cv = document.createElement("canvas");
      cv.width = 512;
      cv.height = 256;
      const ctx = cv.getContext("2d");
      ctx.fillStyle = "#e5dfd3";
      ctx.fillRect(0, 0, cv.width, cv.height);

      const floors = 5;
      const fh = cv.height / floors;
      for (let f = 0; f < floors; f++) {
        const y = f * fh;
        ctx.fillStyle = "#cfc8b8";
        ctx.fillRect(0, y, cv.width, 4);
        for (let x = 16; x < cv.width - 16; x += 36) {
          ctx.fillStyle = "#334155";
          ctx.fillRect(x, y + 10, 22, fh - 16);
          ctx.fillStyle = "rgba(148, 163, 184, 0.35)";
          ctx.fillRect(x + 2, y + 12, 18, fh - 20);
        }
      }
      const tex = new THREE.CanvasTexture(cv);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      tex.anisotropy = 8;
      threeTextureCache.creamLow = tex;
      return tex;
    }

    function getUrbanGroundContextTexture() {
      if (threeTextureCache.urbanGround) return threeTextureCache.urbanGround;
      const cv = document.createElement("canvas");
      cv.width = 1024;
      cv.height = 1024;
      const ctx = cv.getContext("2d");

      // Warm realistic earth & urban park ground base
      ctx.fillStyle = "#8c7a5b";
      ctx.fillRect(0, 0, 1024, 1024);

      // Textured open development parcels (right half — sandy-ochre earth & grass patches like haio.sg)
      for (let i = 0; i < 400; i++) {
        const px = 480 + ((i * 97) % 520);
        const py = 60 + ((i * 151) % 880);
        ctx.fillStyle = (i % 3 === 0) ? "rgba(180, 158, 118, 0.38)" : ((i % 3 === 1) ? "rgba(74, 107, 62, 0.32)" : "rgba(122, 104, 76, 0.35)");
        ctx.beginPath();
        ctx.arc(px, py, 14 + (i % 28), 0, Math.PI * 2);
        ctx.fill();
      }

      // Urban asphalt avenues & white lane markings
      ctx.strokeStyle = "#334155";
      ctx.lineWidth = 28;
      ctx.beginPath();
      ctx.moveTo(460, 0);
      ctx.lineTo(680, 1024);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(180, 620);
      ctx.lineTo(980, 380);
      ctx.stroke();

      // Lush green park belt along the podium right edge
      ctx.save();
      ctx.translate(545, 520);
      ctx.rotate(-0.18);
      ctx.fillStyle = "#2d6a32";
      ctx.fillRect(-45, -180, 88, 340);
      ctx.restore();

      // Paved architectural plaza around the Hero White Tower & Podium
      ctx.fillStyle = "#cbd5e1";
      ctx.fillRect(340, 440, 190, 150);

      const tex = new THREE.CanvasTexture(cv);
      tex.anisotropy = 8;
      threeTextureCache.urbanGround = tex;
      return tex;
    }

    function rebuildThreeHeroScene() {
      if (!three3DLayer || !three3DLayer.scene) return;
      const scene = three3DLayer.scene;
      if (three3DLayer.cityGroup) {
        scene.remove(three3DLayer.cityGroup);
      }

      const p = DATA.projects.find(x => x.project_id === selected3DProjectId) || DATA.projects[0];
      const [lat, lon] = parseCoord(p.coordinates);
      three3DLayer.originLonLat = [lon, lat];
      const spec = getProject3DSpec(p);

      // Update the 3D floating roof callout text ("Block 1 · 2 stacks")
      const calloutTxtEl = document.getElementById("hero3DRoofCalloutText");
      if (calloutTxtEl) {
        calloutTxtEl.textContent = `Block 1 · 2 stacks`;
      }

      const cityGroup = new THREE.Group();
      // Align local axes with NE 60° camera view so (-x = Left, +x = Right, -z = Background, +z = Foreground)
      cityGroup.rotation.y = -THREE.MathUtils.degToRad(60);

      // Subtle landscaped green park belt & architectural plaza apron under the Hero Tower & Podium
      // (Lets real high-res Esri World Imagery satellite earth, roads, and parcels show cleanly around the site)
      const parkBeltGeo = new THREE.PlaneGeometry(54, 155);
      const parkBeltMat = new THREE.MeshLambertMaterial({ color: 0x2d6a32, transparent: true, opacity: 0.78 });
      const parkBeltMesh = new THREE.Mesh(parkBeltGeo, parkBeltMat);
      parkBeltMesh.rotation.x = -Math.PI / 2;
      parkBeltMesh.rotation.z = 0.16;
      parkBeltMesh.position.set(28, 0.18, -8);
      cityGroup.add(parkBeltMesh);

      const siteApronGeo = new THREE.PlaneGeometry(118, 92);
      const siteApronMat = new THREE.MeshLambertMaterial({ color: 0xe2e8f0, transparent: true, opacity: 0.72 });
      const siteApronMesh = new THREE.Mesh(siteApronGeo, siteApronMat);
      siteApronMesh.rotation.x = -Math.PI / 2;
      siteApronMesh.position.set(-14, 0.22, 18);
      cityGroup.add(siteApronMesh);

      // -----------------------------------------------------------------------
      // 1. HERO ACTIVE PROJECT: ARTICULATED STARK-WHITE RESIDENTIAL TOWER (Block 1)
      //    Unobstructed in the center-left of the plot, right beside the Podium
      // -----------------------------------------------------------------------
      const heroBaseH = 74;
      three3DLayer.heroRoofLocalVec = new THREE.Vector3(-36, heroBaseH + 5, 4);

      // White architectural plaza plinth under Block 1
      const whiteRoofMat = new THREE.MeshLambertMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 0.32 });
      addBoxWithEdges(cityGroup, 50, 3.0, 38, -36, 0, 6, whiteRoofMat, 0xcbd5e1);

      // 6 Interlocking Articulated White Residential Stack Wings (Exact W Residences Marina View massing)
      const wingSpecs = [
        { w: 15, d: 15, h: heroBaseH * 1.00, x: -49, z: 0 },
        { w: 17, d: 14, h: heroBaseH * 0.98, x: -37, z: -3 },
        { w: 15, d: 16, h: heroBaseH * 0.95, x: -40, z: 12 },
        { w: 16, d: 15, h: heroBaseH * 1.02, x: -23, z: -2 },
        { w: 15, d: 16, h: heroBaseH * 0.96, x: -22, z: 11 },
        { w: 13, d: 14, h: heroBaseH * 0.90, x: -52, z: 13 }
      ];

      wingSpecs.forEach((ws, idx) => {
        const wallTex = getHeroWhiteTowerTexture(spec.storeys, active3DShowMe, active3DFloor, active3DStack, idx);
        const isDefaultWhite = (active3DShowMe === "all" && active3DFloor === "ALL" && active3DStack === "ALL");
        const wallMat = new THREE.MeshLambertMaterial({
          map: wallTex,
          emissive: isDefaultWhite ? 0xffffff : 0x000000,
          emissiveIntensity: isDefaultWhite ? 0.28 : 0.0
        });
        const mats = [wallMat, wallMat, whiteRoofMat, whiteRoofMat, wallMat, wallMat];
        addBoxWithEdges(cityGroup, ws.w, ws.h, ws.d, ws.x, 3.0, ws.z, mats, 0xcbd5e1);
        addBoxWithEdges(cityGroup, ws.w * 0.74, 2.6, ws.d * 0.74, ws.x, 3.0 + ws.h, ws.z, whiteRoofMat, 0x94a3b8);
      });

      // -----------------------------------------------------------------------
      // 2. HERO ACTIVE PROJECT: TERRACOTTA & DARK SMOKED-GLASS PODIUM + ROOFTOP SKY-GARDEN
      //    Positioned immediately to the right of the White Tower (x = +16, z = +18)
      // -----------------------------------------------------------------------
      const podGroup = new THREE.Group();
      podGroup.position.set(16, 0, 18);
      podGroup.rotation.y = -0.16;

      const podBaseTex = getPodiumTerracottaTexture();
      const podBaseWallMat = new THREE.MeshLambertMaterial({ map: podBaseTex });
      const podBaseRoofMat = new THREE.MeshLambertMaterial({ color: 0xf1f5f9 });
      const podBaseMats = [podBaseWallMat, podBaseWallMat, podBaseRoofMat, podBaseRoofMat, podBaseWallMat, podBaseWallMat];

      // Level 1: Terracotta / Burgundy Architectural Podium Base (0..18m)
      addBoxWithEdges(podGroup, 44, 18, 54, 0, 0, 0, podBaseMats, 0x451a03);

      // Level 2: Mid-Level Lush Planted Green Terrace Ledge (18..21.5m)
      const midGreenMat = new THREE.MeshLambertMaterial({ color: 0x276738 });
      addBoxWithEdges(podGroup, 45.2, 3.5, 55.2, 0, 18, 0, midGreenMat, null);

      // Level 3: Sleek Dark Smoked-Glass Upper Podium Box (21.5..46m)
      const podGlassTex = getPodiumSmokedGlassTexture();
      const podGlassWallMat = new THREE.MeshLambertMaterial({ map: podGlassTex });
      const roofGardenTex = getRooftopGardenTexture();
      const roofGardenMat = new THREE.MeshLambertMaterial({ map: roofGardenTex });
      const darkRimMat = new THREE.MeshLambertMaterial({ color: 0x1e293b });
      const podGlassMats = [podGlassWallMat, podGlassWallMat, roofGardenMat, darkRimMat, podGlassWallMat, podGlassWallMat];
      addBoxWithEdges(podGroup, 37, 24.5, 48, 2.5, 21.5, -1.0, podGlassMats, 0x334155);

      // Level 4: Rooftop Sky-Garden Perimeter Parapet Walls & 3D Botanical Tree Canopies (at y = 46m)
      addBoxWithEdges(podGroup, 37.4, 2.2, 1.2, 2.5, 46, -24.4, darkRimMat, null);
      addBoxWithEdges(podGroup, 37.4, 2.2, 1.2, 2.5, 46, 22.4, darkRimMat, null);
      addBoxWithEdges(podGroup, 1.2, 2.2, 48.0, -15.4, 46, -1.0, darkRimMat, null);
      addBoxWithEdges(podGroup, 1.2, 2.2, 48.0, 20.4, 46, -1.0, darkRimMat, null);

      const roofTreeCoords = [
        [-9, -17], [0, -18], [10, -17], [14, -9], [14, 2], [13, 12],
        [-9, 13], [2, 14], [-10, 0], [-4, -7], [7, 6], [0, 3]
      ];
      roofTreeCoords.forEach(([tx, tz]) => {
        addTreeCanopyCluster(podGroup, tx, 45.8, tz, 0.65);
      });

      cityGroup.add(podGroup);

      // -----------------------------------------------------------------------
      // 3. ICONIC CYLINDRICAL RIBBED WHITE TOWER (AXA Tower Style on the Left)
      //    Positioned at x = -112, z = +38 so it frames the left side without blocking Block 1
      // -----------------------------------------------------------------------
      const axaX = -112;
      const axaZ = 38;
      const axaH = 212;
      const axaTex = getAxaRibbedTowerTexture();
      const axaWallMat = new THREE.MeshLambertMaterial({ map: axaTex });
      const axaCapMat = new THREE.MeshLambertMaterial({ color: 0xd6d1c7 });
      const axaCylGeo = new THREE.CylinderGeometry(27.5, 27.5, axaH, 44, 1, false);
      const axaMesh = new THREE.Mesh(axaCylGeo, [axaWallMat, axaCapMat, axaCapMat]);
      axaMesh.position.set(axaX, axaH / 2, axaZ);
      axaMesh.rotation.y = THREE.MathUtils.degToRad(48);
      cityGroup.add(axaMesh);

      // Recessed Circular Mechanical Crown on top of the Cylindrical Tower
      const axaCrownGeo = new THREE.CylinderGeometry(19.0, 19.0, 12, 36);
      const axaCrownMat = new THREE.MeshLambertMaterial({ color: 0xb8b2a6 });
      const axaCrown = new THREE.Mesh(axaCrownGeo, axaCrownMat);
      axaCrown.position.set(axaX, axaH + 6.0, axaZ);
      cityGroup.add(axaCrown);

      // -----------------------------------------------------------------------
      // 4. FOREGROUND SCULPTED BRONZE/TERRACOTTA SETBACK TOWER (Bottom-Center Edge)
      //    Positioned at x = -54, z = +188 with height = 74m so its detailed roof sits
      //    in the bottom foreground BELOW the White Tower & Podium (zero occlusion!)
      // -----------------------------------------------------------------------
      const brzX = -54;
      const brzZ = 188;
      const brzH = 74;
      const brzTex = getBronzeSetbackTowerTexture();
      const brzWallMat = new THREE.MeshLambertMaterial({ map: brzTex });
      const brzCapMat = new THREE.MeshLambertMaterial({ color: 0x8c5845 });
      const brzMats = [brzWallMat, brzWallMat, brzCapMat, brzCapMat, brzWallMat, brzWallMat];

      addBoxWithEdges(cityGroup, 42, brzH, 34, brzX, 0, brzZ, brzMats, 0x5c3426, 0.14);
      addBoxWithEdges(cityGroup, 32, brzH, 42, brzX, 0, brzZ, brzMats, 0x5c3426, 0.14);

      // Projecting Bronze Crown Cornice & Recessed Grey Mechanical Roof Well with Red HVAC Units
      const brzCorniceMat = new THREE.MeshLambertMaterial({ color: 0x9e6854 });
      addBoxWithEdges(cityGroup, 45, 5.0, 37, brzX, brzH, brzZ, brzCorniceMat, 0x5c3426, 0.14);
      const mechDeckMat = new THREE.MeshLambertMaterial({ color: 0x64748b });
      addBoxWithEdges(cityGroup, 33, 1.8, 26, brzX, brzH + 4.2, brzZ, mechDeckMat, 0x334155, 0.14);
      const redHvacMat = new THREE.MeshLambertMaterial({ color: 0xb91c1c });
      const silHvacMat = new THREE.MeshLambertMaterial({ color: 0xcbd5e1 });
      addBoxWithEdges(cityGroup, 8.0, 4.5, 6.5, brzX - 5, brzH + 5.5, brzZ - 2, redHvacMat, null, 0.14);
      addBoxWithEdges(cityGroup, 9.0, 4.0, 7.0, brzX + 6, brzH + 5.5, brzZ + 3, silHvacMat, null, 0.14);

      // Stepped Blue-Silver Glass Fin Annex in front of the Bronze Tower at bottom edge
      const blueCurtainMat = new THREE.MeshLambertMaterial({ map: getBlueGlassCurtainTexture() });
      const annexMats = [blueCurtainMat, blueCurtainMat, silHvacMat, silHvacMat, blueCurtainMat, blueCurtainMat];
      addBoxWithEdges(cityGroup, 20, 56, 18, brzX - 5, 0, brzZ + 28, annexMats, 0x94a3b8, 0.18);
      addBoxWithEdges(cityGroup, 18, 50, 17, brzX + 13, 0, brzZ + 26, annexMats, 0x94a3b8, -0.10);

      // -----------------------------------------------------------------------
      // 5. BACKGROUND TWIN DARK CHARCOAL/BRONZE CURTAIN-WALL SKYSCRAPERS (Upper-Center)
      // -----------------------------------------------------------------------
      const darkTex = getDarkCurtainWallTexture();
      const darkWallMat = new THREE.MeshLambertMaterial({ map: darkTex });
      const darkCapMat = new THREE.MeshLambertMaterial({ color: 0x334155 });
      const darkMats = [darkWallMat, darkWallMat, darkCapMat, darkCapMat, darkWallMat, darkWallMat];

      // Twin Tower 1 (Center-Background Left)
      addBoxWithEdges(cityGroup, 38, 172, 26, -34, 0, -96, darkMats, 0x475569, -0.18);
      addBoxWithEdges(cityGroup, 28, 180, 24, -22, 0, -104, darkMats, 0x475569, -0.18);
      addBoxWithEdges(cityGroup, 24, 9, 16, -28, 180, -100, darkCapMat, 0x64748b, -0.18);

      // Twin Tower 2 (Center-Background Right)
      addBoxWithEdges(cityGroup, 36, 168, 26, 22, 0, -100, darkMats, 0x475569, -0.22);
      addBoxWithEdges(cityGroup, 26, 176, 24, 34, 0, -108, darkMats, 0x475569, -0.22);
      addBoxWithEdges(cityGroup, 22, 8, 15, 28, 176, -104, darkCapMat, 0x64748b, -0.22);

      // -----------------------------------------------------------------------
      // 6. LEFT-SIDE SKYLINE: SLANTED BLUE-GLASS TOWER, TALL RESIDENTIAL & PYRAMID CROWN TOWER
      // -----------------------------------------------------------------------
      addBoxWithEdges(cityGroup, 32, 182, 28, -138, 0, -42, annexMats, 0xcbd5e1, 0.22);
      addBoxWithEdges(cityGroup, 28, 192, 24, -84, 0, -54, annexMats, 0x94a3b8, 0.08);

      const stoneWallMat = new THREE.MeshLambertMaterial({ map: getCreamLowRiseTexture() });
      const stoneMats = [stoneWallMat, stoneWallMat, axaCapMat, axaCapMat, stoneWallMat, stoneWallMat];
      addBoxWithEdges(cityGroup, 28, 142, 28, -172, 0, -4, stoneMats, 0x94a3b8, 0.15);
      const goldPyrGeo = new THREE.ConeGeometry(19, 24, 4);
      const goldPyrMat = new THREE.MeshLambertMaterial({ color: 0xd97706 });
      const goldPyr = new THREE.Mesh(goldPyrGeo, goldPyrMat);
      goldPyr.position.set(-172, 142 + 12, -4);
      goldPyr.rotation.y = Math.PI / 4 + 0.15;
      cityGroup.add(goldPyr);

      // Mid-rise building to the left of AXA tower
      const creamLowMat = new THREE.MeshLambertMaterial({ map: getCreamLowRiseTexture() });
      const greyRoofMat = new THREE.MeshLambertMaterial({ color: 0x94a3b8 });
      const creamMats = [creamLowMat, creamLowMat, greyRoofMat, greyRoofMat, creamLowMat, creamLowMat];
      addBoxWithEdges(cityGroup, 32, 72, 28, -164, 0, 56, stoneMats, 0x94a3b8, 0.12);

      // Bottom-left fluted stone tower
      const octGeo = new THREE.CylinderGeometry(19, 19, 108, 16);
      const octMat = new THREE.MeshLambertMaterial({ map: brzTex });
      const octMesh = new THREE.Mesh(octGeo, [octMat, greyRoofMat, greyRoofMat]);
      octMesh.position.set(-168, 54, 128);
      cityGroup.add(octMesh);

      // Far-left skyline continuation & Business Bay Canal-Front Towers
      const farLeftRoofGreen = new THREE.MeshLambertMaterial({ map: roofGardenTex });
      const limWallMat = new THREE.MeshLambertMaterial({ map: getRibbedLimestoneTowerTexture(), emissive: 0x334155, emissiveIntensity: 0.18 });
      const farLeftGreenMats = [stoneWallMat, stoneWallMat, farLeftRoofGreen, greyRoofMat, stoneWallMat, stoneWallMat];
      addBoxWithEdges(cityGroup, 44, 118, 36, -245, 0, 178, farLeftGreenMats, 0xcbd5e1, 0.24);
      addBoxWithEdges(cityGroup, 36, 164, 30, -228, 0, 62, annexMats, 0x94a3b8, 0.16);
      addBoxWithEdges(cityGroup, 34, 188, 28, -224, 0, -36, darkMats, 0x475569, -0.12);
      addBoxWithEdges(cityGroup, 38, 146, 32, -286, 0, 16, stoneMats, 0x94a3b8, 0.18);
      addBoxWithEdges(cityGroup, 32, 134, 28, -295, 0, 108, brzMats, 0x5c3426, 0.10);
      addBoxWithEdges(cityGroup, 36, 172, 30, -198, 0, -88, annexMats, 0x94a3b8, 0.08);

      // Additional canal-front and waterfront high-rise towers around the bridge
      const extraCanalTowers = [
        { w: 38, h: 145, d: 32, x: -165, z: 215, mat: blueCurtainMat, rMat: greyRoofMat, rot: 0.22 },
        { w: 42, h: 162, d: 34, x: -215, z: 265, mat: limWallMat, rMat: farLeftRoofGreen, rot: 0.18 },
        { w: 36, h: 138, d: 30, x: -125, z: 275, mat: darkWallMat, rMat: greyRoofMat, rot: -0.15 },
        { w: 40, h: 154, d: 32, x: -185, z: 335, mat: brzWallMat, rMat: greyRoofMat, rot: 0.12 },
        { w: 36, h: 128, d: 30, x: -265, z: 195, mat: darkWallMat, rMat: farLeftRoofGreen, rot: 0.25 },
        { w: 38, h: 148, d: 32, x: -315, z: 255, mat: blueCurtainMat, rMat: greyRoofMat, rot: 0.15 },
        { w: 34, h: 118, d: 28, x: 95, z: 45, mat: limWallMat, rMat: greyRoofMat, rot: -0.20 },
        { w: 38, h: 132, d: 30, x: 135, z: -25, mat: blueCurtainMat, rMat: farLeftRoofGreen, rot: -0.18 },
        { w: 36, h: 142, d: 30, x: 115, z: -95, mat: darkWallMat, rMat: greyRoofMat, rot: -0.12 }
      ];
      extraCanalTowers.forEach(t => {
        const mats = [t.mat, t.mat, t.rMat, greyRoofMat, t.mat, t.mat];
        addBoxWithEdges(cityGroup, t.w, t.h, t.d, t.x, 0, t.z, mats, 0xcbd5e1, t.rot);
      });

      // -----------------------------------------------------------------------
      // 7. LOW-RISE URBAN PAVILIONS & 80+ 3D BOTANICAL TREES AROUND THE PLOT
      // -----------------------------------------------------------------------
      addBoxWithEdges(cityGroup, 28, 17, 24, -68, 0, 58, creamMats, 0x94a3b8, -0.14);
      addBoxWithEdges(cityGroup, 18, 22, 16, -66, 0, 56, creamMats, 0x94a3b8, -0.14);

      addBoxWithEdges(cityGroup, 34, 16, 26, 14, 0, 88, creamMats, 0x94a3b8, -0.18);
      addBoxWithEdges(cityGroup, 16, 21, 20, 26, 0, 94, creamMats, 0x94a3b8, -0.18);
      addBoxWithEdges(cityGroup, 5.5, 18, 5.5, 20, 0, 99, redHvacMat, null, -0.18);

      addBoxWithEdges(cityGroup, 42, 18, 30, 74, 0, 126, creamMats, 0x94a3b8, -0.22);
      addBoxWithEdges(cityGroup, 26, 23, 20, 92, 0, 118, creamMats, 0x94a3b8, -0.22);

      const streetTrees = [
        [-82, 74], [-74, 82], [-58, 78], [-44, 86], [-18, 68], [-8, 74],
        [36, 58], [44, 48], [50, 34], [56, 20], [60, 4], [64, -12],
        [48, -24], [40, -36], [54, -44], [72, 26], [80, 42], [90, 58],
        [104, 72], [52, 88], [42, 102], [28, 116], [12, 124], [-78, 128],
        [-92, 86], [-72, -18], [-58, -32], [-14, -42], [8, -38], [24, -46],
        [88, -10], [96, 4], [108, -18], [116, 12], [68, 78], [58, 92]
      ];
      streetTrees.forEach(([tx, tz], idx) => {
        const sc = 0.90 + (idx % 4) * 0.22;
        addTreeCanopyCluster(cityGroup, tx, 0, tz, sc);
      });

      three3DLayer.cityGroup = cityGroup;
      scene.add(cityGroup);

      // Also build 3D clusters at all other active UAE projects + extrude all OSM buildings across the entire map!
      rebuildAllProjectsAndOsmCity3D();
      if (map3d) map3d.triggerRepaint();
    }

    let osmRebuildTimer = null;
    function scheduleOsmCityRebuild() {
      if (osmRebuildTimer) clearTimeout(osmRebuildTimer);
      osmRebuildTimer = setTimeout(() => {
        rebuildAllProjectsAndOsmCity3D();
      }, 140);
    }

    // Extrudes ALL real OpenStreetMap building footprints across the entire visible map into textured 3D Three.js buildings
    // PLUS generates 3D textured tower clusters at all 37 active UAE Construction Projects & Sub-Clusters
    function rebuildAllProjectsAndOsmCity3D() {
      if (!three3DLayer || !three3DLayer.scene || !map3d || !map3dLoaded) return;
      if (typeof THREE.ShapeUtils === "undefined") return;

      const darkTex = getDarkCurtainWallTexture();
      const blueTex = getBlueGlassCurtainTexture();
      const limTex = getRibbedLimestoneTowerTexture();
      const brzTex = getBronzeSetbackTowerTexture();
      const creamTex = getCreamLowRiseTexture();
      const roofGardenTex = getRooftopGardenTexture();

      const wallMats = [
        new THREE.MeshLambertMaterial({ map: darkTex, emissive: 0x1e293b, emissiveIntensity: 0.22, side: THREE.DoubleSide }),
        new THREE.MeshLambertMaterial({ map: blueTex, emissive: 0x1e3a5f, emissiveIntensity: 0.20, side: THREE.DoubleSide }),
        new THREE.MeshLambertMaterial({ map: limTex, emissive: 0x334155, emissiveIntensity: 0.18, side: THREE.DoubleSide }),
        new THREE.MeshLambertMaterial({ map: brzTex, emissive: 0x451a03, emissiveIntensity: 0.18, side: THREE.DoubleSide }),
        new THREE.MeshLambertMaterial({ map: creamTex, emissive: 0x334155, emissiveIntensity: 0.18, side: THREE.DoubleSide })
      ];

      const roofMats = [
        new THREE.MeshLambertMaterial({ color: 0x94a3b8, side: THREE.DoubleSide }),
        new THREE.MeshLambertMaterial({ color: 0xcbd5e1, side: THREE.DoubleSide }),
        new THREE.MeshLambertMaterial({ color: 0xd6d3cd, side: THREE.DoubleSide }),
        new THREE.MeshLambertMaterial({ color: 0x8c5845, side: THREE.DoubleSide }),
        new THREE.MeshLambertMaterial({ map: roofGardenTex, side: THREE.DoubleSide })
      ];

      const originLonLat = three3DLayer.originLonLat;
      const originMerc = maplibregl.MercatorCoordinate.fromLngLat(originLonLat, 0);
      const scale = originMerc.meterInMercatorCoordinateUnits();

      let feats = [];
      try {
        feats = map3d.querySourceFeatures("openmaptiles", { sourceLayer: "building" }) || [];
      } catch (err) {
        feats = [];
      }

      const buckets = wallMats.map(() => ({ pos: [], norm: [], uv: [] }));
      const roofBuckets = roofMats.map(() => ({ pos: [], norm: [], uv: [] }));
      const edgePos = [];
      const seen = new Set();

      for (const f of feats) {
        if (!f.geometry) continue;
        const rawH = Number(f.properties?.render_height) || 20;
        const minH = Math.max(0, Number(f.properties?.render_min_height) || 0);
        if (rawH <= minH + 1) continue;

        const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] :
                      (f.geometry.type === "MultiPolygon" ? f.geometry.coordinates : []);

        for (const poly of polys) {
          const ring = poly[0];
          if (!ring || ring.length < 4) continue;

          const pts = [];
          let cx = 0, cz = 0;
          let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
          for (let i = 0; i < ring.length - 1; i++) {
            const m = maplibregl.MercatorCoordinate.fromLngLat(ring[i], 0);
            const vx = (m.x - originMerc.x) / scale;
            const vz = (m.y - originMerc.y) / scale;
            pts.push({ x: vx, z: vz });
            cx += vx;
            cz += vz;
            if (vx < minX) minX = vx;
            if (vx > maxX) maxX = vx;
            if (vz < minZ) minZ = vz;
            if (vz > maxZ) maxZ = vz;
          }
          if (pts.length < 3) continue;
          cx /= pts.length;
          cz /= pts.length;

          // Clear 215m radius around active Hero Site so Hero White Tower, Podium, AXA, and Foreground Bronze Tower stand cleanly
          if (Math.hypot(cx, cz) < 215) continue;

          const key = `${Math.round(cx * 0.25)}_${Math.round(cz * 0.25)}_${Math.round(rawH)}_${Math.round(minH)}`;
          if (seen.has(key)) continue;
          seen.add(key);

          const spanX = maxX - minX;
          const spanZ = maxZ - minZ;
          if ((spanX > 220 || spanZ > 220) && rawH < 14) continue;

          const hash = Math.abs(Math.round(cx * 1.37 + cz * 2.19));
          let h = rawH;
          if (h <= 12 && minH === 0 && spanX > 12 && spanZ > 12 && spanX < 95 && spanZ < 95) {
            h = 32 + (hash % 75);
          } else if (h < 28 && minH === 0 && spanX > 18 && spanZ > 18 && (hash % 3 !== 0)) {
            h = h * 1.65;
          }

          const styleIdx = (h < 22) ? 4 : (hash % 4);
          const roofIdx = (h >= 28 && hash % 5 === 0) ? 4 : (hash % 4);
          const b = buckets[styleIdx];
          const rb = roofBuckets[roofIdx];

          let uDist = 0;
          const uScale = 34.0;
          const vScale = 52.0;
          const v0 = minH / vScale;
          const v1 = h / vScale;

          for (let i = 0; i < pts.length; i++) {
            const p0 = pts[i];
            const p1 = pts[(i + 1) % pts.length];
            const dx = p1.x - p0.x;
            const dz = p1.z - p0.z;
            const segLen = Math.hypot(dx, dz);
            if (segLen < 0.3) continue;

            let nx = dz / segLen;
            let nz = -dx / segLen;
            const midX = (p0.x + p1.x) * 0.5 - cx;
            const midZ = (p0.z + p1.z) * 0.5 - cz;
            if (nx * midX + nz * midZ < 0) {
              nx = -nx;
              nz = -nz;
            }

            const u0 = uDist / uScale;
            const u1 = (uDist + segLen) / uScale;
            uDist += segLen;

            b.pos.push(p0.x, minH, p0.z,  p1.x, minH, p1.z,  p1.x, h, p1.z);
            b.norm.push(nx, 0, nz,  nx, 0, nz,  nx, 0, nz);
            b.uv.push(u0, v0,  u1, v0,  u1, v1);

            b.pos.push(p0.x, minH, p0.z,  p1.x, h, p1.z,  p0.x, h, p0.z);
            b.norm.push(nx, 0, nz,  nx, 0, nz,  nx, 0, nz);
            b.uv.push(u0, v0,  u1, v1,  u0, v1);

            edgePos.push(p0.x, h, p0.z,  p1.x, h, p1.z);
          }

          const contour = pts.map(p => new THREE.Vector2(p.x, p.z));
          const tris = THREE.ShapeUtils.triangulateShape(contour, []);
          for (const t of tris) {
            const a = pts[t[0]], bPt = pts[t[1]], c = pts[t[2]];
            rb.pos.push(a.x, h, a.z,  bPt.x, h, bPt.z,  c.x, h, c.z);
            rb.norm.push(0, 1, 0,  0, 1, 0,  0, 1, 0);
            rb.uv.push(
              (a.x - minX) / Math.max(10, spanX), (a.z - minZ) / Math.max(10, spanZ),
              (bPt.x - minX) / Math.max(10, spanX), (bPt.z - minZ) / Math.max(10, spanZ),
              (c.x - minX) / Math.max(10, spanX), (c.z - minZ) / Math.max(10, spanZ)
            );
          }
        }
      }

      if (three3DLayer.osmCityGroup) {
        three3DLayer.scene.remove(three3DLayer.osmCityGroup);
      }
      const osmGroup = new THREE.Group();

      buckets.forEach((b, idx) => {
        if (!b.pos.length) return;
        const geo = new THREE.BufferGeometry();
        geo.setAttribute("position", new THREE.Float32BufferAttribute(b.pos, 3));
        geo.setAttribute("normal", new THREE.Float32BufferAttribute(b.norm, 3));
        geo.setAttribute("uv", new THREE.Float32BufferAttribute(b.uv, 2));
        osmGroup.add(new THREE.Mesh(geo, wallMats[idx]));
      });

      roofBuckets.forEach((rb, idx) => {
        if (!rb.pos.length) return;
        const geo = new THREE.BufferGeometry();
        geo.setAttribute("position", new THREE.Float32BufferAttribute(rb.pos, 3));
        geo.setAttribute("normal", new THREE.Float32BufferAttribute(rb.norm, 3));
        geo.setAttribute("uv", new THREE.Float32BufferAttribute(rb.uv, 2));
        osmGroup.add(new THREE.Mesh(geo, roofMats[idx]));
      });

      if (edgePos.length) {
        const edgeGeo = new THREE.BufferGeometry();
        edgeGeo.setAttribute("position", new THREE.Float32BufferAttribute(edgePos, 3));
        osmGroup.add(new THREE.LineSegments(edgeGeo, new THREE.LineBasicMaterial({ color: 0xcbd5e1, transparent: true, opacity: 0.45 })));
      }

      // Also place 3D textured tower clusters at all other 36 active UAE Construction Projects & Sub-Clusters
      const whiteWallMat = new THREE.MeshLambertMaterial({ map: getHeroWhiteTowerTexture(48, "all", "ALL", "ALL", 0), emissive: 0xffffff, emissiveIntensity: 0.25 });
      const whiteRoof = new THREE.MeshLambertMaterial({ color: 0xffffff });
      const podMat = new THREE.MeshLambertMaterial({ map: getPodiumSmokedGlassTexture() });
      const allSites = [
        ...DATA.projects.map(p => ({ id: p.project_id, coords: parseCoord(p.coordinates), h: 85 })),
        ...DATA.subdevs.map(s => ({ id: s.subdev_id, coords: [s.latitude, s.longitude], h: 72 }))
      ];
      allSites.forEach((site, sIdx) => {
        if (site.id === selected3DProjectId) return;
        const [sLat, sLon] = site.coords;
        const sm = maplibregl.MercatorCoordinate.fromLngLat([sLon, sLat], 0);
        const sx = (sm.x - originMerc.x) / scale;
        const sz = (sm.y - originMerc.y) / scale;
        if (Math.hypot(sx, sz) > 35000 || Math.hypot(sx, sz) < 220) return;

        // Main white project tower + podium + 3 context towers at each project site
        const wMats = [whiteWallMat, whiteWallMat, whiteRoof, whiteRoof, whiteWallMat, whiteWallMat];
        addBoxWithEdges(osmGroup, 26, site.h, 22, sx - 14, 0, sz, wMats, 0xcbd5e1, 0.15);
        addBoxWithEdges(osmGroup, 22, site.h * 0.92, 20, sx + 4, 0, sz - 8, wMats, 0xcbd5e1, 0.15);
        const pMats = [podMat, podMat, roofMats[4], roofMats[0], podMat, podMat];
        addBoxWithEdges(osmGroup, 36, 28, 42, sx + 28, 0, sz + 12, pMats, 0x334155, -0.12);
        const cMat1 = wallMats[sIdx % 4];
        const cMat2 = wallMats[(sIdx + 1) % 4];
        addBoxWithEdges(osmGroup, 32, site.h * 1.35, 28, sx - 58, 0, sz - 42, [cMat1, cMat1, roofMats[0], roofMats[0], cMat1, cMat1], 0x94a3b8, 0.22);
        addBoxWithEdges(osmGroup, 34, site.h * 1.20, 28, sx + 64, 0, sz - 48, [cMat2, cMat2, roofMats[1], roofMats[1], cMat2, cMat2], 0x94a3b8, -0.18);
      });

      three3DLayer.osmCityGroup = osmGroup;
      three3DLayer.scene.add(osmGroup);
      map3d.triggerRepaint();
    }

    function createPhotorealistic3DCustomLayer() {
      const layer = {
        id: "haio-photoreal-3d-layer",
        type: "custom",
        renderingMode: "3d",
        originLonLat: [55.2798, 25.1844],
        heroRoofLocalVec: new THREE.Vector3(-30, 120, 4),
        onAdd: function (mapInstance, gl) {
          this.map = mapInstance;
          this.camera = new THREE.Camera();
          this.scene = new THREE.Scene();

          // Realistic Sun + Sky Hemisphere Lighting
          const hemiLight = new THREE.HemisphereLight(0xffffff, 0x64748b, 0.82);
          hemiLight.position.set(0, 300, 0);
          this.scene.add(hemiLight);

          const sunLight = new THREE.DirectionalLight(0xfffbeb, 0.92);
          sunLight.position.set(-180, 320, 220);
          this.scene.add(sunLight);

          const fillLight = new THREE.DirectionalLight(0xbae6fd, 0.38);
          fillLight.position.set(200, 180, -160);
          this.scene.add(fillLight);

          this.renderer = new THREE.WebGLRenderer({
            canvas: mapInstance.getCanvas(),
            context: gl,
            antialias: true
          });
          this.renderer.autoClear = false;
          rebuildThreeHeroScene();
        },
        render: function (gl, matrix) {
          if (!is3DBlocksEnabled || !this.scene || !this.renderer) return;
          const zNow = this.map.getZoom();
          const calloutEl = document.getElementById("hero3DRoofCallout");
          if (zNow < 11.2) {
            if (calloutEl) calloutEl.style.display = "none";
            return;
          }

          const merc = maplibregl.MercatorCoordinate.fromLngLat(this.originLonLat, 0);
          const scale = merc.meterInMercatorCoordinateUnits();

          const rotX = new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(1, 0, 0), Math.PI / 2);
          const m = new THREE.Matrix4().fromArray(matrix);
          const l = new THREE.Matrix4()
            .makeTranslation(merc.x, merc.y, merc.z)
            .scale(new THREE.Vector3(scale, -scale, scale))
            .multiply(rotX);

          this.camera.projectionMatrix = m.multiply(l);

          // Clear depth buffer so Three.js photorealistic 3D buildings cleanly occlude underlying flat layers
          gl.clear(gl.DEPTH_BUFFER_BIT);
          this.renderer.resetState();
          this.renderer.render(this.scene, this.camera);

          // Project the exact 3D roof coordinate of the white tower ("Block 1 · 2 stacks") onto screen pixels
          if (calloutEl && this.cityGroup && zNow >= 14.5) {
            const worldRoof = this.heroRoofLocalVec.clone().applyMatrix4(this.cityGroup.matrixWorld);
            const ndc = worldRoof.applyMatrix4(this.camera.projectionMatrix);
            if (ndc.z >= -1 && ndc.z <= 1) {
              const canvas = this.map.getCanvas();
              const px = (ndc.x * 0.5 + 0.5) * canvas.clientWidth;
              const py = (-ndc.y * 0.5 + 0.5) * canvas.clientHeight;
              calloutEl.style.transform = `translate3d(${Math.round(px)}px, ${Math.round(py)}px, 0) translate(-50%, -100%)`;
              calloutEl.style.display = "inline-flex";
            } else {
              calloutEl.style.display = "none";
            }
          } else if (calloutEl) {
            calloutEl.style.display = "none";
          }
        }
      };
      three3DLayer = layer;
      return layer;
    }

    function init3DMap() {
      if (typeof maplibregl === "undefined") return;

      const defaultProj = DATA.projects.find(x => x.project_id === selected3DProjectId) || DATA.projects[0];
      const [initLat, initLon] = parseCoord(defaultProj.coordinates);

      map3d = new maplibregl.Map({
        container: "map3dCanvas",
        center: [initLon, initLat],
        zoom: window.innerWidth <= 768 ? 15.6 : 16.25,
        pitch: 58,
        bearing: 60,
        minZoom: 8.5,
        maxZoom: 17.6,
        maxBounds: [[51.0, 22.4], [56.8, 26.5]],
        antialias: true,
        attributionControl: false,
        style: {
          version: 8,
          glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
          light: {
            anchor: "viewport",
            color: "#fffbeb",
            intensity: 0.62,
            position: [1.45, 215, 48]
          },
          sources: {
            "sat-tiles": {
              type: "raster",
              tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
              tileSize: 256,
              maxzoom: 17
            },
            "light-tiles": {
              type: "raster",
              tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
              tileSize: 256,
              maxzoom: 18
            },
            "openmaptiles": {
              type: "vector",
              url: "https://tiles.openfreemap.org/planet"
            },
            "communities-3d": {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] }
            },
            "roads-3d": {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] }
            },
            "impacts-3d": {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] }
            },
            "projects-zones-3d": {
              type: "geojson",
              data: buildProjectSiteZonesGeoJSON()
            }
          },
          layers: [
            {
              id: "bg-dark-layer",
              type: "background",
              paint: { "background-color": "#0b1320" }
            },
            {
              id: "sat-raster-layer",
              type: "raster",
              source: "sat-tiles",
              layout: { visibility: "visible" },
              paint: { "raster-opacity": 1.0, "raster-contrast": 0.14, "raster-saturation": 0.16 }
            },
            {
              id: "light-raster-layer",
              type: "raster",
              source: "light-tiles",
              layout: { visibility: "none" },
              paint: { "raster-opacity": 0.96 }
            },
            {
              id: "communities-fill-3d",
              type: "fill",
              source: "communities-3d",
              paint: {
                "fill-color": ["get", "color"],
                "fill-opacity": 0.0
              }
            },
            {
              id: "communities-line-3d",
              type: "line",
              source: "communities-3d",
              paint: {
                "line-color": ["get", "color"],
                "line-width": 1.2,
                "line-opacity": 0.0
              }
            },
            {
              id: "projects-zone-fill-3d",
              type: "fill",
              source: "projects-zones-3d",
              maxzoom: 14.5,
              paint: {
                "fill-color": ["get", "color"],
                "fill-opacity": ["get", "fillOpacity"]
              }
            },
            {
              id: "projects-zone-line-3d",
              type: "line",
              source: "projects-zones-3d",
              maxzoom: 14.5,
              paint: {
                "line-color": ["get", "color"],
                "line-width": ["get", "lineWidth"],
                "line-opacity": 0.92
              }
            },
            {
              id: "roads-casing-3d",
              type: "line",
              source: "roads-3d",
              layout: {
                "line-cap": "round",
                "line-join": "round"
              },
              paint: {
                "line-color": "#0f172a",
                "line-width": [
                  "interpolate", ["exponential", 1.35], ["zoom"],
                  9, ["*", ["get", "casingWidth"], 0.75],
                  13, ["*", ["get", "casingWidth"], 1.15],
                  16.5, ["*", ["get", "casingWidth"], 1.85]
                ],
                "line-opacity": 0.86
              }
            },
            {
              id: "roads-traffic-3d",
              type: "line",
              source: "roads-3d",
              layout: {
                "line-cap": "round",
                "line-join": "round"
              },
              paint: {
                "line-color": ["get", "color"],
                "line-width": [
                  "interpolate", ["exponential", 1.35], ["zoom"],
                  9, ["*", ["get", "trafficWidth"], 0.75],
                  13, ["*", ["get", "trafficWidth"], 1.15],
                  16.5, ["*", ["get", "trafficWidth"], 1.85]
                ],
                "line-opacity": 0.94
              }
            },
            {
              id: "impacts-line-3d",
              type: "line",
              source: "impacts-3d",
              maxzoom: 14.8,
              paint: {
                "line-color": "#fbbf24",
                "line-width": 2.2,
                "line-dasharray": [2, 2],
                "line-opacity": 0.88
              }
            },
            {
              id: "osm-3d-buildings",
              type: "fill-extrusion",
              source: "openmaptiles",
              "source-layer": "building",
              minzoom: 12.0,
              filter: ["!", ["has", "hide_3d"]],
              paint: {
                "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
                "fill-extrusion-height": ["coalesce", ["get", "render_height"], 16],
                "fill-extrusion-color": [
                  "step",
                  ["coalesce", ["get", "render_height"], 16],
                  "#dcd6cc",
                  22, "#c8bfb2",
                  48, "#8c624c",
                  95, "#475569",
                  160, "#334155",
                  240, "#cfc8bc"
                ],
                "fill-extrusion-vertical-gradient": true,
                "fill-extrusion-opacity": [
                  "interpolate", ["linear"], ["zoom"],
                  12.0, 0.88,
                  13.5, 0.005
                ]
              }
            },
            {
              id: "osm-road-labels",
              type: "symbol",
              source: "openmaptiles",
              "source-layer": "transportation_name",
              minzoom: 12,
              maxzoom: 15.2,
              layout: {
                "symbol-placement": "line",
                "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]],
                "text-font": ["Noto Sans Regular"],
                "text-size": ["interpolate", ["linear"], ["zoom"], 12, 10, 15, 12]
              },
              paint: {
                "text-color": "#f8fafc",
                "text-halo-color": "#0f172a",
                "text-halo-width": 1.6
              }
            },
            {
              id: "osm-place-labels",
              type: "symbol",
              source: "openmaptiles",
              "source-layer": "place",
              minzoom: 10,
              maxzoom: 14.8,
              layout: {
                "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]],
                "text-font": ["Noto Sans Bold"],
                "text-size": ["interpolate", ["linear"], ["zoom"], 10, 11, 14, 14]
              },
              paint: {
                "text-color": "#ffffff",
                "text-halo-color": "rgba(15, 23, 42, 0.9)",
                "text-halo-width": 2.0
              }
            }
          ]
        }
      });

      map3d.on("rotate", updateCompassUI);
      map3d.on("move", () => {
        updateCompassUI();
        if (map3d) map3d.triggerRepaint();
      });
      map3d.on("moveend", scheduleOsmCityRebuild);
      map3d.on("idle", scheduleOsmCityRebuild);
      map3d.on("sourcedata", (e) => {
        if (e.sourceId === "openmaptiles" && e.isSourceLoaded) {
          scheduleOsmCityRebuild();
        }
      });
      map3d.on("zoomend", sync3DMapLayers);

      map3d.on("load", () => {
        map3dLoaded = true;
        if (typeof THREE !== "undefined") {
          map3d.addLayer(createPhotorealistic3DCustomLayer(), "osm-road-labels");
        }
        sync3DMapLayers();
        scheduleOsmCityRebuild();
        setTimeout(scheduleOsmCityRebuild, 900);
        setTimeout(scheduleOsmCityRebuild, 2200);
        updateCompassUI();
      });

      map3d.on("click", "projects-zone-fill-3d", (e) => {
        if (e.features && e.features.length > 0) {
          const pid = e.features[0].properties.project_id;
          if (pid && String(pid).startsWith("PRJ-")) {
            showProjectInspector(pid, true);
          } else if (pid && String(pid).startsWith("SUB-")) {
            const sd = DATA.subdevs.find(x => x.subdev_id === pid);
            if (sd) showSubdevInspector(sd, true);
          }
        }
      });

      map3d.on("click", "roads-traffic-3d", (e) => {
        if (e.features && e.features.length > 0) {
          const rId = e.features[0].properties.road_id;
          if (rId) showRoadInspector(rId, true);
        }
      });
    }

    function sync3DMapLayers() {
      if (!map3d || !map3dLoaded) return;

      rebuildThreeHeroScene();

      const emFilter = document.getElementById("emirateSelect") ? document.getElementById("emirateSelect").value : "ALL";
      const q = (document.getElementById("searchInput")?.value || "").toLowerCase().trim();
      const showComm = document.getElementById("chk-L3")?.checked ?? true;
      const showRoads = document.getElementById("chk-L4")?.checked ?? true;
      const showTraffic = document.getElementById("chk-L6")?.checked ?? true;
      const showImpacts = document.getElementById("chk-L11")?.checked ?? false;
      const showProjs = document.getElementById("chk-L1")?.checked ?? true;

      // 1. Communities GeoJSON
      const commFeats = [];
      if (showComm) {
        DATA.communities.forEach(c => {
          if (emFilter !== "ALL" && c.emirate !== emFilter) return;
          const col = c.observed_congestion_severity.includes("Severe") ? "#ef4444" :
                      (c.observed_congestion_severity.includes("High") ? "#f97316" : "#8b5cf6");
          commFeats.push({
            type: "Feature",
            properties: { community_id: c.community_id, color: col },
            geometry: { type: "Polygon", coordinates: [c.polygon_wgs84] }
          });
        });
      }
      map3d.getSource("communities-3d")?.setData({ type: "FeatureCollection", features: commFeats });

      // 2. Roads & Traffic GeoJSON (All 23 Real OpenStreetMap Highway Geometries)
      const roadFeats = [];
      if (showRoads || showTraffic) {
        DATA.roads.forEach(r => {
          if (emFilter !== "ALL" && r.emirate !== emFilter) return;
          const { obs } = getCorridorProfileForWindow(r, currentTimeWindow);
          const congLvl = obs ? obs.congestion_level : "Unavailable";
          const tCol = showTraffic ? congestionColor(congLvl) : "#64748b";
          const isFwy = r.road_type.includes("Freeway") || r.road_type.includes("Express");
          roadFeats.push({
            type: "Feature",
            properties: {
              road_id: r.road_id,
              color: tCol,
              casingWidth: isFwy ? 6.0 : 4.2,
              trafficWidth: isFwy ? 3.8 : 2.6
            },
            geometry: { type: "LineString", coordinates: r.geometry_wgs84 }
          });
        });
      }
      map3d.getSource("roads-3d")?.setData({ type: "FeatureCollection", features: roadFeats });

      // 3. Impact Vectors GeoJSON
      const impFeats = [];
      DATA.impact_links.forEach(l => {
        if (!showImpacts && l.project_id !== selected3DProjectId) return;
        if (l.nearest_road_vertex_lat !== undefined && l.nearest_road_vertex_lon !== undefined) {
          const p = DATA.projects.find(x => x.project_id === l.project_id);
          if (p) {
            const [lat, lon] = parseCoord(p.coordinates);
            impFeats.push({
              type: "Feature",
              properties: { project_id: l.project_id },
              geometry: { type: "LineString", coordinates: [[lon, lat], [l.nearest_road_vertex_lon, l.nearest_road_vertex_lat]] }
            });
          }
        }
      });
      map3d.getSource("impacts-3d")?.setData({ type: "FeatureCollection", features: impFeats });

      // 4. Active Construction Site Perimeter Zones
      map3d.getSource("projects-zones-3d")?.setData(showProjs ? buildProjectSiteZonesGeoJSON() : { type: "FeatureCollection", features: [] });

      // 5. Update 3D Sun Lighting based on active diurnal window
      if (currentTimeWindow.includes("Morning")) {
        map3d.setLight({ anchor: "viewport", color: "#fef3c7", intensity: 0.62, position: [1.4, 95, 38] });
      } else if (currentTimeWindow.includes("Midday")) {
        map3d.setLight({ anchor: "viewport", color: "#ffffff", intensity: 0.58, position: [1.15, 180, 22] });
      } else if (currentTimeWindow.includes("Night")) {
        map3d.setLight({ anchor: "viewport", color: "#93c5fd", intensity: 0.65, position: [1.3, 240, 50] });
      } else {
        map3d.setLight({ anchor: "viewport", color: "#fffbeb", intensity: 0.62, position: [1.45, 215, 48] });
      }

      // 6. Clean Map Callout Pills (When zoomed in >= 14.5, keep viewport ultra-clean like haio.sg with only #hero3DRoofCallout!)
      map3dMarkers.forEach(m => m.remove());
      map3dMarkers = [];

      const zNow = map3d.getZoom();

      if (showProjs && zNow < 14.5) {
        DATA.projects.forEach(p => {
          if (emFilter !== "ALL" && p.emirate !== emFilter) return;
          if (q && !JSON.stringify(p).toLowerCase().includes(q)) return;
          const [lat, lon] = parseCoord(p.coordinates);
          const st = projectScaleStyle(p);
          const isSel = (p.project_id === selected3DProjectId);
          const shortName = p.project_name.split("(")[0].trim().slice(0, 20);

          const el = document.createElement("div");
          el.className = isSel ? "haio-3d-block-callout hero" : "haio-3d-block-callout";
          el.style.padding = isSel ? "6px 12px" : "4px 9px";
          el.style.fontSize = isSel ? "0.75rem" : "0.69rem";
          el.style.borderLeft = `4px solid ${st.fillColor}`;
          el.innerHTML = `<span style="width:7px;height:7px;border-radius:50%;background:${st.fillColor};display:inline-block;"></span><span><strong>${p.project_id}</strong>: ${shortName}</span>`;
          el.onclick = (ev) => {
            ev.stopPropagation();
            showProjectInspector(p.project_id, true);
          };
          const mk = new maplibregl.Marker({ element: el, anchor: "bottom", offset: [0, -6] })
            .setLngLat([lon, lat])
            .addTo(map3d);
          map3dMarkers.push(mk);
        });
      }

      if (showTraffic && zNow < 14.8) {
        const roadPillSpecs = [
          { id: "RD-DXB-01", code: "E11 SZR" },
          { id: "RD-DXB-03", code: "E44 Khail" },
          { id: "RD-DXB-05", code: "D61 Hessa" },
          { id: "RD-DXB-09", code: "E611 Freight" },
          { id: "RD-DXB-12", code: "D71 FinCtr" },
          { id: "RD-SHJ-01", code: "E311 Shj" }
        ];

        roadPillSpecs.forEach(ra => {
          const rObj = DATA.roads.find(x => x.road_id === ra.id);
          const obs = getRoadObsForWindow(ra.id, currentTimeWindow);
          if (!rObj || !obs || !rObj.geometry_wgs84.length) return;
          if (emFilter !== "ALL" && rObj.emirate !== emFilter) return;
          const midPt = rObj.geometry_wgs84[Math.floor(rObj.geometry_wgs84.length / 2)];
          const tCol = congestionColor(obs.congestion_level);
          const el = document.createElement("div");
          el.className = "road-speed-pill";
          el.style.borderColor = tCol;
          el.innerHTML = `<span style="width:7px;height:7px;border-radius:50%;background:${tCol};display:inline-block;"></span><span>${ra.code}: <strong>${obs.average_speed_kmh} km/h</strong></span>`;
          el.onclick = (ev) => {
            ev.stopPropagation();
            showRoadInspector(ra.id, true);
          };
          const mk = new maplibregl.Marker({ element: el, anchor: "center" })
            .setLngLat([midPt[0], midPt[1]])
            .addTo(map3d);
          map3dMarkers.push(mk);
        });
      }
    }

    function initMap() {
      map = L.map("mapCanvas", {
        center: [25.1844, 55.2798],
        zoom: window.innerWidth <= 768 ? 14 : 15,
        minZoom: 9,
        maxZoom: 18,
        maxBounds: [[22.4, 51.0], [26.5, 56.8]],
        maxBoundsViscosity: 0.9,
        zoomControl: false
      });

      // Enable only the 4 core executive layers by default (Clean Initial View)
      ["communities", "roads", "traffic", "projects"].forEach(k => {
        layerGroups[k].addTo(map);
      });

      init3DMap();
      setBasemap("sat", document.querySelector(".bm-btn.active"));

      populateCommunityDropdown();
      renderAllMapLayers();
      runUseCase(1, false);
      showProjectInspector("PRJ-D11", false);
    }

    function setPlatformMode(mode, btnEl) {
      if (btnEl) {
        document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
        btnEl.classList.add("active");
      }
      const wb = document.getElementById("mainWorkbench");
      if (wb.classList.contains("panel-collapsed")) toggleRightPanel();

      if (mode === "overview") {
        switchDrawerTab("uc");
        setLayerSet(["communities", "roads", "traffic", "projects"]);
        backToCityMapOverview();
      } else if (mode === "construction") {
        switchDrawerTab("uc");
        setLayerSet(["communities", "devbounds", "projects", "roads", "traffic"]);
        flyBothMaps(25.0585, 55.2090, 13.8, 56, 32);
        runUseCase(2, false);
      } else if (mode === "traffic") {
        switchDrawerTab("uc");
        setLayerSet(["roads", "traffic", "intersections", "impacts", "projects"]);
        runUseCase(3, true);
      } else if (mode === "project") {
        switchDrawerTab("insp");
        setLayerSet(["communities", "roads", "traffic", "impacts", "projects", "devbounds"]);
        showProjectInspector("PRJ-D11", true);
      } else if (mode === "evidence") {
        const det = document.getElementById("evidenceAccordion");
        if (det) det.open = true;
        const evSec = document.getElementById("evidence-tables") || document.getElementById("evidenceSection");
        if (evSec) evSec.scrollIntoView({ behavior: "smooth" });
      }
    }

    function setLayerSet(activeKeys) {
      const keyToChk = {
        projects: "chk-L1", devbounds: "chk-L2", communities: "chk-L3",
        roads: "chk-L4", intersections: "chk-L5", traffic: "chk-L6",
        incidents: "chk-L7", transit: "chk-L8", facilities: "chk-L9",
        parking: "chk-L10", impacts: "chk-L11"
      };
      const keyToQ = {
        projects: "qpill-projects", communities: "qpill-communities",
        traffic: "qpill-traffic", impacts: "qpill-impacts"
      };
      Object.keys(layerGroups).forEach(k => {
        const on = activeKeys.includes(k);
        toggleLayerGroup(k, on);
        const chk = document.getElementById(keyToChk[k]);
        if (chk) chk.checked = on;
        const qp = document.getElementById(keyToQ[k]);
        if (qp) {
          qp.classList.toggle("on", on);
          qp.classList.toggle("active", on);
        }
      });
      sync3DMapLayers();
    }

    function quickToggle(key, chkId, btnEl) {
      const chk = document.getElementById(chkId);
      const nextState = chk ? !chk.checked : !map.hasLayer(layerGroups[key]);
      if (chk) chk.checked = nextState;
      if (btnEl) {
        btnEl.classList.toggle("on", nextState);
        btnEl.classList.toggle("active", nextState);
      }
      toggleLayerGroup(key, nextState);
    }

    function toggleLayersPopover() {
      const pop = document.getElementById("layersPopover");
      if (pop) pop.classList.toggle("open");
    }

    function toggleRightPanel() {
      const wb = document.getElementById("mainWorkbench");
      const btn = document.getElementById("collapseRightBtn");
      wb.classList.toggle("panel-collapsed");
      if (btn) btn.textContent = wb.classList.contains("panel-collapsed") ? "◂ Open Panel" : "▸ Collapse";
      setTimeout(() => {
        if (map) map.invalidateSize();
        if (map3d) map3d.resize();
      }, 260);
    }

    function toggle3DPerspective(btnEl) {
      setCameraDimension(currentCameraDim === "3D" ? "2D" : "3D");
    }

    function runStoryStep(step) {
      document.querySelectorAll(".story-bar .story-step").forEach((el, idx) => {
        el.classList.toggle("active", (idx + 1) === step);
      });
      if (step === 1) {
        document.getElementById("emirateSelect").value = "ALL";
        populateCommunityDropdown();
        setLayerSet(["communities", "roads", "traffic", "projects"]);
        flyBothMaps(25.195, 55.355, 10.4, 48, 20);
        document.getElementById("hudScope").textContent = "Step 1: UAE Overview";
        runUseCase(1, false);
      } else if (step === 2) {
        document.getElementById("emirateSelect").value = "Dubai";
        populateCommunityDropdown();
        setLayerSet(["communities", "roads", "traffic", "projects"]);
        flyBothMaps(25.155, 55.265, 11.8, 54, 35);
        document.getElementById("hudScope").textContent = "Step 2: Dubai Core Corridors";
        runUseCase(1, false);
      } else if (step === 3) {
        document.getElementById("emirateSelect").value = "Dubai";
        populateCommunityDropdown();
        setLayerSet(["communities", "devbounds", "roads", "traffic", "impacts", "projects"]);
        flyBothMaps(25.0585, 55.2090, 14.2, 58, 40);
        document.getElementById("hudScope").textContent = "Step 3: JVC High-Density Hotspot";
        runUseCase(2, false);
      } else if (step === 4) {
        setLayerSet(["communities", "devbounds", "roads", "traffic", "impacts", "projects"]);
        document.getElementById("hudScope").textContent = "Step 4: 3D Tower (PRJ-D6)";
        showProjectInspector("PRJ-D6", true);
      } else if (step === 5) {
        setLayerSet(["roads", "traffic", "intersections", "impacts", "projects"]);
        flyBothMaps(25.0695, 55.1950, 13.8, 55, 25);
        document.getElementById("hudScope").textContent = "Step 5: Hessa St (D61) Impact";
        showRoadInspector("RD-DXB-05", false);
      }
    }

    function setBasemap(mode, btnEl) {
      currentBasemapMode = mode || "sat";
      if (btnEl) {
        document.querySelectorAll(".bm-btn").forEach(b => {
          if (b.id !== "btn3dTilt" && b.id !== "collapseRightBtn") b.classList.remove("active");
        });
        btnEl.classList.add("active");
      }
      if (map3d && map3dLoaded) {
        map3d.setLayoutProperty("sat-raster-layer", "visibility", mode === "sat" ? "visible" : "none");
        map3d.setLayoutProperty("light-raster-layer", "visibility", mode === "light" ? "visible" : "none");
      }
      const mc = document.getElementById("mapCanvas");
      if (mc) mc.classList.toggle("basemap-dark", mode === "dark" || !mode);
      if (baseTileLayer && map) map.removeLayer(baseTileLayer);
      if (map) {
        if (mode === "sat") {
          baseTileLayer = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
            minZoom: 9, maxZoom: 18, noWrap: true
          });
        } else {
          baseTileLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            minZoom: 9, maxZoom: 18, noWrap: true, className: mode === "dark" ? "gis-dark-tiles" : ""
          });
        }
        baseTileLayer.addTo(map);
        baseTileLayer.bringToBack();
      }
    }

    function populateCommunityDropdown() {
      const em = document.getElementById("emirateSelect").value;
      const sel = document.getElementById("communitySelect");
      const comms = DATA.communities.filter(c => em === "ALL" || c.emirate === em);
      sel.innerHTML = `<option value="ALL">-- All ${em === 'ALL' ? 'Dubai & Sharjah' : em} Communities (${comms.length}) --</option>` +
        comms.map(c => `<option value="${c.community_id}">${c.emirate}: ${c.community_name} (${c.active_developments_count} Active Devs)</option>`).join("");
    }

    function onEmirateChange() {
      const em = document.getElementById("emirateSelect").value;
      populateCommunityDropdown();
      if (em === "Dubai") {
        flyBothMaps(25.175, 55.272, 12.2, 56, 40);
        document.getElementById("hudScope").textContent = "Dubai 3D";
      } else if (em === "Sharjah") {
        flyBothMaps(25.318, 55.475, 13.0, 56, 35);
        document.getElementById("hudScope").textContent = "Sharjah 3D";
      } else {
        flyBothMaps(25.195, 55.345, 10.6, 50, 25);
        document.getElementById("hudScope").textContent = "All UAE 3D";
      }
      applyMapFilters();
    }

    function zoomToSelectedCommunity() {
      const cid = document.getElementById("communitySelect").value;
      if (cid === "ALL") {
        onEmirateChange();
        return;
      }
      const c = DATA.communities.find(x => x.community_id === cid);
      if (c) {
        flyBothMaps(c.center_lat, c.center_lon, (c.recommended_zoom || 13) + 0.8, 58, 40);
        document.getElementById("hudScope").textContent = c.community_name;
        showCommunityInspector(c);
      }
    }

    function toggleLayerGroup(key, show) {
      if (show) {
        if (!map.hasLayer(layerGroups[key])) map.addLayer(layerGroups[key]);
      } else {
        if (map.hasLayer(layerGroups[key])) map.removeLayer(layerGroups[key]);
      }
      const keyToQ = {
        projects: "qpill-projects", communities: "qpill-communities",
        traffic: "qpill-traffic", impacts: "qpill-impacts"
      };
      if (keyToQ[key]) {
        const qp = document.getElementById(keyToQ[key]);
        if (qp) {
          qp.classList.toggle("on", show);
          qp.classList.toggle("active", show);
        }
      }
      sync3DMapLayers();
    }

    function setTimeWindow(tp, btnEl) {
      currentTimeWindow = tp;
      document.getElementById("hudTime").textContent = tp;

      document.querySelectorAll(".time-btn").forEach(b => {
        const bTp = b.getAttribute("data-tp");
        b.classList.toggle("active", bTp === tp);
      });

      const info = getWindowHgvBannerInfo(tp);
      const hgvEl = document.getElementById("hudHgvStatus");
      if (hgvEl) {
        hgvEl.textContent = info.hgvBadge;
        hgvEl.style.cssText = info.hgvStyle;
      }

      renderAllMapLayers();

      if (currentDrawerTab === "uc") {
        runUseCase(currentUseCase, false);
      } else if (currentDrawerTab === "insp") {
        if (currentInspState.type === "road") showRoadInspector(currentInspState.id, false);
        else if (currentInspState.type === "project") showProjectInspector(currentInspState.id, false);
        else if (currentInspState.type === "subdev") showSubdevInspector(currentInspState.obj, false);
        else if (currentInspState.type === "community") showCommunityInspector(currentInspState.obj);
      } else if (currentDrawerTab === "qa") {
        const qVal = (document.getElementById("qaInput").value || "").trim();
        if (qVal) runDeterministicQA();
      }
    }

    function updateImpactBuffers() {
      currentRadiusMeters = parseInt(document.getElementById("radiusSelect").value || "1500", 10);
      renderAllMapLayers();
    }

    function applyMapFilters() {
      renderAllMapLayers();
    }

    function resetAllFilters() {
      document.getElementById("searchInput").value = "";
      document.getElementById("emirateSelect").value = "Dubai";
      document.getElementById("congestionFilter").value = "ALL";
      document.getElementById("epistemicFilter").value = "ALL";
      document.getElementById("radiusSelect").value = "1500";
      currentRadiusMeters = 1500;
      populateCommunityDropdown();
      setLayerSet(["communities", "roads", "traffic", "projects"]);
      flyBothMaps(25.1844, 55.2798, 15.6, 60, 45);
      renderAllMapLayers();
    }


    function renderAllMapLayers() {
      Object.values(layerGroups).forEach(lg => lg.clearLayers());

      const emFilter = document.getElementById("emirateSelect").value;
      const q = (document.getElementById("searchInput").value || "").toLowerCase().trim();
      const congFilter = document.getElementById("congestionFilter").value;
      const epFilter = document.getElementById("epistemicFilter").value;

      // 1. Layer 3: Community Boundaries & Hotspots
      DATA.communities.forEach(c => {
        if (emFilter !== "ALL" && c.emirate !== emFilter) return;
        if (q && !JSON.stringify(c).toLowerCase().includes(q)) return;
        const latlngs = c.polygon_wgs84.map(pt => [pt[1], pt[0]]);
        const col = c.observed_congestion_severity.includes("Severe") ? "#ef4444" :
                    (c.observed_congestion_severity.includes("High") ? "#f97316" : "#a855f7");
        const poly = L.polygon(latlngs, {
          color: col,
          weight: 0,
          opacity: 0,
          fillColor: col,
          fillOpacity: 0
        });
        poly.bindTooltip(`<strong>${c.community_name}</strong><br/>Active Devs: ${c.active_developments_count} | Active Towers: ${c.active_towers_and_buildings}<br/>Hotspot Score: ${c.construction_activity_index_score}`, { sticky: true });
        poly.on("click", () => showCommunityInspector(c));
        poly.addTo(layerGroups.communities);
      });

      let speedSum = 0;
      let speedCount = 0;
      const badgeRoadIds = new Set(["RD-DXB-01", "RD-DXB-03", "RD-DXB-05", "RD-DXB-07", "RD-DXB-09", "RD-DXB-11", "RD-DXB-12", "RD-DXB-15", "RD-SHJ-01", "RD-SHJ-02"]);
      const overviewCorePills = new Set(["RD-DXB-01", "RD-DXB-05", "RD-DXB-09", "RD-SHJ-01"]);
      const shortRoadLabels = {
        "RD-DXB-01": "E11 SZR",
        "RD-DXB-03": "E44 Khail",
        "RD-DXB-05": "D61 Hessa",
        "RD-DXB-07": "JVC Blvd",
        "RD-DXB-09": "E611 Freight",
        "RD-DXB-11": "D62 Khor",
        "RD-DXB-12": "D71 FinCtr",
        "RD-DXB-15": "E77 DWC",
        "RD-SHJ-01": "E311 Shj",
        "RD-SHJ-02": "E611 Shj"
      };
      const pillCoords = {
        "RD-DXB-01": [25.175, 55.242],
        "RD-DXB-03": [25.095, 55.228],
        "RD-DXB-05": [25.092, 55.162],
        "RD-DXB-07": [25.049, 55.215],
        "RD-DXB-09": [25.012, 55.288],
        "RD-DXB-11": [25.189, 55.348],
        "RD-DXB-12": [25.204, 55.272],
        "RD-DXB-15": [24.915, 55.161],
        "RD-SHJ-01": [25.318, 55.465],
        "RD-SHJ-02": [25.298, 55.588]
      };
      const isOverviewZoom = map && (map.getZoom() < 12);

      // 2. Layer 4 & Layer 6: Road Network & Dynamic 4-Window Traffic Speed/Congestion Overlay + Floating Speed Pills
      DATA.roads.forEach(r => {
        if (emFilter !== "ALL" && r.emirate !== emFilter) return;
        const { obs, exactMatch } = getCorridorProfileForWindow(r, currentTimeWindow);
        const congLvl = obs ? obs.congestion_level : "Unavailable";

        if (congFilter !== "ALL") {
          if (congFilter === "High" && !(congLvl.includes("High") || congLvl.includes("Severe"))) return;
          if (congFilter !== "High" && !congLvl.includes(congFilter)) return;
        }
        if (q && !JSON.stringify(r).toLowerCase().includes(q) && !(obs && JSON.stringify(obs).toLowerCase().includes(q))) return;

        if (obs && obs.average_speed_kmh) {
          speedSum += parseFloat(obs.average_speed_kmh);
          speedCount++;
        }

        const latlngs = r.geometry_wgs84.map(pt => [pt[1], pt[0]]);

        // Base casing line (Layer 4 — Reduced weight for visual clarity)
        const baseLine = L.polyline(latlngs, {
          color: "#1e293b",
          weight: r.road_type.includes("Freeway") || r.road_type.includes("Express") ? 4.5 : 3.2,
          opacity: 0.82
        });
        baseLine.on("click", () => showRoadInspector(r.road_id));
        baseLine.addTo(layerGroups.roads);

        // Traffic color overlay line (Layer 6 — Clean 3.0px / 2.2px stroke)
        const tCol = congestionColor(congLvl);
        const speedTxt = obs ? `${obs.average_speed_kmh} km/h (${obs.travel_time_min_per_10km} min/10km | V/C=${obs.vc_ratio})` : "Data Unavailable";
        const matchNote = exactMatch
          ? `[Primary Dataset #17 Record: ${obs.observation_id}] Source: ${obs.source_id}`
          : `[Diurnal BPR Profile for ${currentTimeWindow}] Source: ${r.source_id}`;
        const trafLine = L.polyline(latlngs, {
          color: tCol,
          weight: r.road_type.includes("Freeway") || r.road_type.includes("Express") ? 3.2 : 2.4,
          lineCap: "round",
          lineJoin: "round",
          opacity: 0.95
        });
        trafLine.bindTooltip(
          `<strong>${r.road_name} (${r.road_code})</strong><br/>` +
          `Active Window: <strong>${currentTimeWindow}</strong><br/>` +
          `Modelled Speed: <strong style="color:${tCol};">${speedTxt}</strong><br/>` +
          `Congestion Status: <strong>${congLvl.split('(')[0]}</strong><br/>` +
          `Published Capacity: ${r.capacity_vph_per_dir}<br/>` +
          `<em>${matchNote}</em>`,
          { sticky: true }
        );
        trafLine.on("click", () => showRoadInspector(r.road_id));
        trafLine.addTo(layerGroups.traffic);

        // Floating On-Map Speed Pill for Key Corridors (Instantly updates when AM/Midday/PM/Night is clicked)
        const showPill = obs && (isOverviewZoom ? overviewCorePills.has(r.road_id) : badgeRoadIds.has(r.road_id));
        if (showPill) {
          const midPt = r.geometry_wgs84[Math.floor(r.geometry_wgs84.length / 2)];
          const anchorLatLng = [midPt[1], midPt[0]];
          const shortCode = shortRoadLabels[r.road_id] || r.road_code.split("/")[0].trim();
          const pillIcon = L.divIcon({
            className: "",
            html: `<div class="road-speed-pill" style="border-color:${tCol};" onclick="showRoadInspector('${r.road_id}')"><span style="width:6px;height:6px;border-radius:50%;background:${tCol};display:inline-block;"></span><span>${shortCode}: <strong>${obs.average_speed_kmh} km/h</strong></span></div>`,
            iconSize: [86, 20],
            iconAnchor: [43, 10]
          });
          const pillMarker = L.marker(anchorLatLng, { icon: pillIcon });
          pillMarker.on("click", () => showRoadInspector(r.road_id));
          pillMarker.addTo(layerGroups.traffic);
        }
      });

      const avgSpd = speedCount > 0 ? (speedSum / speedCount).toFixed(1) : "45.0";
      const hudAvgEl = document.getElementById("hudAvgSpeed");
      if (hudAvgEl) hudAvgEl.textContent = `${avgSpd} km/h`;
      const panelSumEl = document.getElementById("panelWindowSpeedSummary");
      if (panelSumEl) {
        const shortW = currentTimeWindow.split("(")[0].trim();
        panelSumEl.textContent = `${shortW} • Avg ${avgSpd} km/h`;
      }

      // 3. Layer 5: Intersections & Bottlenecks
      DATA.intersections.forEach(i => {
        if (emFilter !== "ALL" && i.emirate !== emFilter) return;
        if (q && !JSON.stringify(i).toLowerCase().includes(q)) return;
        const marker = L.circleMarker([i.latitude, i.longitude], {
          radius: 5.5,
          color: "#fff",
          weight: 1.5,
          fillColor: "#f43f5e",
          fillOpacity: 0.95
        });
        marker.bindTooltip(`<strong>Junction: ${i.intersection_name}</strong><br/>Peak LOS: ${i.peak_level_of_service}<br/>Upgrade: ${i.rta_upgrade_and_mitigation}`, { direction: "top" });
        marker.on("click", () => showIntersectionInspector(i));
        marker.addTo(layerGroups.intersections);
      });

      // 4. Layer 7: Active Roadworks & Traffic Incidents
      DATA.incidents.forEach(inc => {
        if (emFilter !== "ALL" && inc.emirate !== emFilter) return;
        const m = L.circleMarker([inc.latitude, inc.longitude], {
          radius: 7,
          color: "#fb923c",
          weight: 1.5,
          dashArray: "3,3",
          fillColor: "#ea580c",
          fillOpacity: 0.85
        });
        m.bindTooltip(`<strong>🚧 ${inc.incident_category}</strong><br/>${inc.road_name}<br/><strong>${inc.epistemic_tier}</strong><br/>${inc.speed_and_capacity_impact}`, { direction: "top" });
        m.on("click", () => showRoadInspector(inc.road_id));
        m.addTo(layerGroups.incidents);
      });

      // 5. Layer 8: Public Transport Infrastructure (Metro Red/Blue Lines & Etihad Rail)
      DATA.transit_lines.forEach(t => {
        const latlngs = t.coords.map(pt => [pt[1], pt[0]]);
        const line = L.polyline(latlngs, {
          color: t.color,
          weight: 2.5,
          dashArray: t.transit_id === "TRN-BLUE" ? "7,5" : null,
          opacity: 0.85
        });
        line.bindTooltip(`<strong>🚇 ${t.line_name}</strong><br/>${t.status}<br/>Ridership: ${t.daily_ridership}`, { sticky: true });
        line.addTo(layerGroups.transit);

        t.stations.forEach(st => {
          const sm = L.circleMarker([st.lat, st.lon], {
            radius: 4.5,
            color: "#fff",
            weight: 1.2,
            fillColor: t.color,
            fillOpacity: 1.0
          });
          sm.bindTooltip(`<strong>🚉 ${st.name}</strong><br/>${t.line_name}`);
          sm.addTo(layerGroups.transit);
        });
      });

      // 6. Layer 9: Nearby Schools, Hospitals, Malls (Task 1 09b)
      DATA.facilities.forEach(f => {
        if (emFilter !== "ALL" && f.emirate !== emFilter) return;
        const [lat, lon] = parseCoord(f.coordinates);
        const fm = L.circleMarker([lat, lon], {
          radius: 4.5,
          color: "#065f46",
          weight: 1.2,
          fillColor: "#10b981",
          fillOpacity: 0.9
        });
        fm.bindTooltip(`<strong>🏥/🏫 ${f.feature_name}</strong><br/>${f.facility_category}<br/>Dist to projects: ${f.distance_to_projects_km} km`);
        fm.addTo(layerGroups.facilities);
      });

      // 7. Layer 10: Parking, EV Chargers & Delivery Hubs
      DATA.parking.forEach(pk => {
        if (emFilter !== "ALL" && pk.emirate !== emFilter) return;
        const pm = L.circleMarker([pk.latitude, pk.longitude], {
          radius: 5,
          color: "#fff",
          weight: 1.2,
          fillColor: "#14b8a6",
          fillOpacity: 0.95
        });
        pm.bindTooltip(`<strong>🅿️ ${pk.facility_name}</strong><br/>${pk.capacity_bays}<br/>${pk.occupancy_and_congestion_impact}`);
        pm.addTo(layerGroups.parking);
      });

      // Build lookup for impact links
      const linkByProj = {};
      DATA.impact_links.forEach(l => { linkByProj[l.project_id] = l; });

      let visibleProjectsCount = 0;

      // 8. Layer 1, Layer 2 & Layer 11: Flagship Projects (Proportional Scale Hierarchy) + Impact Buffers + Road Vectors
      DATA.projects.forEach(p => {
        if (emFilter !== "ALL" && p.emirate !== emFilter) return;
        const link = linkByProj[p.project_id];
        if (epFilter !== "ALL" && link && !link.epistemic_impact_classification.includes(epFilter)) return;
        if (q && !JSON.stringify(p).toLowerCase().includes(q) && !(link && JSON.stringify(link).toLowerCase().includes(q))) return;

        visibleProjectsCount++;
        const [lat, lon] = parseCoord(p.coordinates);

        // Impact radius circle (Layer 11)
        const bufCircle = L.circle([lat, lon], {
          radius: currentRadiusMeters,
          color: "#f59e0b",
          weight: 1,
          dashArray: "4,4",
          fillColor: "#f59e0b",
          fillOpacity: 0.04
        });
        bufCircle.addTo(layerGroups.impacts);

        // Project-to-Road Nearest-Vertex Vector Line (Layer 11)
        if (link && link.nearest_road_vertex_lat !== undefined && link.nearest_road_vertex_lon !== undefined) {
          const vecLine = L.polyline([[lat, lon], [link.nearest_road_vertex_lat, link.nearest_road_vertex_lon]], {
            color: "#fbbf24",
            weight: 1.5,
            dashArray: "4,4",
            opacity: 0.85
          });
          vecLine.bindTooltip(
            `<strong>${p.project_id} → ${link.primary_road_id}</strong> (${link.distance_to_primary_road_km} km Haversine)<br/>` +
            `Project: [${lat.toFixed(4)}, ${lon.toFixed(4)}] → Nearest Vertex: [${link.nearest_road_vertex_lat.toFixed(4)}, ${link.nearest_road_vertex_lon.toFixed(4)}]<br/>` +
            `${link.epistemic_impact_classification}`
          );
          vecLine.addTo(layerGroups.impacts);
        }

        // Project Marker (Layer 1 — Scaled by Investment Tier)
        const st = projectScaleStyle(p);
        if (st.radius >= 10) {
          L.circleMarker([lat, lon], {
            radius: st.radius + 4,
            color: st.fillColor,
            weight: 1,
            fillColor: st.fillColor,
            fillOpacity: 0.18,
            interactive: false
          }).addTo(layerGroups.projects);
        }
        const marker = L.circleMarker([lat, lon], {
          radius: st.radius,
          color: st.color,
          weight: st.weight,
          fillColor: st.fillColor,
          fillOpacity: 0.96
        });
        marker.bindTooltip(
          `<strong>${p.project_id}: ${p.project_name}</strong><br/>` +
          `Scale Tier: <strong>${st.tier}</strong> (${p.published_investment_value})<br/>` +
          `Developer: ${p.developer} | ${p.city_district_community}<br/>` +
          `Status: ${p.lifecycle_status}<br/>` +
          (link ? `Primary Corridor: <strong>${link.primary_road_name} (${link.distance_to_primary_road_km} km)</strong>` : ""),
          { direction: "top" }
        );
        marker.on("click", () => showProjectInspector(p.project_id));
        marker.addTo(layerGroups.projects);
      });

      // 9. JVC Sub-Developments (Layer 2 — Development Clusters for Deep Community Zoom)
      DATA.subdevs.forEach(sd => {
        if (emFilter !== "ALL" && sd.emirate !== emFilter) return;
        const link = linkByProj[sd.subdev_id];
        if (epFilter !== "ALL" && link && !link.epistemic_impact_classification.includes(epFilter)) return;
        if (q && !JSON.stringify(sd).toLowerCase().includes(q)) return;

        visibleProjectsCount++;
        if (link && link.nearest_road_vertex_lat !== undefined && link.nearest_road_vertex_lon !== undefined) {
          const sdVec = L.polyline([[sd.latitude, sd.longitude], [link.nearest_road_vertex_lat, link.nearest_road_vertex_lon]], {
            color: "#c084fc",
            weight: 1.5,
            dashArray: "4,4",
            opacity: 0.8
          });
          sdVec.bindTooltip(`<strong>${sd.subdev_id} → ${link.primary_road_id}</strong> (${link.distance_to_primary_road_km} km Haversine to nearest vertex [${link.nearest_road_vertex_wgs84}])`);
          sdVec.addTo(layerGroups.impacts);
        }
        const sm = L.circleMarker([sd.latitude, sd.longitude], {
          radius: 6,
          color: "#fff",
          weight: 1.2,
          fillColor: "#a855f7",
          fillOpacity: 0.95
        });
        sm.bindTooltip(
          `<strong>🏢 ${sd.subdev_id}: ${sd.development_name}</strong><br/>` +
          `Developer: ${sd.developer}<br/>` +
          `Scale: ${sd.building_count} Towers (${sd.total_units.toLocaleString()} Units | ${sd.active_gfa_sqm.toLocaleString()} m² GFA)<br/>` +
          `Nearest Vertex Dist: ${sd.distance_to_road_km} km to ${sd.primary_access_road_id}<br/>` +
          `Scenario HGV Load: ${sd.estimated_midday_hgv_trips_per_day}<br/>` +
          `<strong>${sd.epistemic_impact_tier}</strong>`,
          { direction: "top" }
        );
        sm.on("click", () => showSubdevInspector(sd));
        sm.addTo(layerGroups.devbounds);
      });

      document.getElementById("hudProjects").textContent = `${visibleProjectsCount} Active Sites`;
      sync3DMapLayers();
    }

    function switchDrawerTab(tab) {
      currentDrawerTab = tab;
      ["uc", "insp", "qa"].forEach(k => {
        document.getElementById(`dtab-${k}`).classList.toggle("active", k === tab);
        document.getElementById(`dpanel-${k}`).style.display = (k === tab) ? "block" : "none";
      });
    }

    // Interactive 3D Block, Floor Zone, Stack & Unit-Type Handlers (100% Unlocked — No Login Wall)
    function update3DBlockControls(blkVal, flrVal, stkVal, showVal) {
      if (blkVal !== undefined) active3DBlock = blkVal;
      if (flrVal !== undefined) active3DFloor = flrVal;
      if (stkVal !== undefined) active3DStack = stkVal;
      if (showVal !== undefined) active3DShowMe = showVal;

      sync3DMapLayers();
      showProjectInspector(selected3DProjectId, false);
    }

    function select3DBlockCard(blockId) {
      active3DBlock = (active3DBlock === blockId) ? "ALL" : blockId;
      if (active3DBlock !== "ALL" && active3DShowMe === "all") {
        active3DShowMe = "4br_5br_mix";
      } else if (active3DBlock === "ALL" && active3DShowMe === "4br_5br_mix") {
        active3DShowMe = "all";
      }
      const p = DATA.projects.find(x => x.project_id === selected3DProjectId);
      if (p && map3d) {
        const [lat, lon] = parseCoord(p.coordinates);
        map3d.flyTo({
          center: [lon, lat],
          zoom: active3DBlock === "ALL" ? 16.25 : 16.85,
          pitch: 60,
          bearing: active3DBlock === "ALL" ? 60 : 48,
          duration: 900
        });
      }
      sync3DMapLayers();
      showProjectInspector(selected3DProjectId, false);
    }

    // =========================================================================
    // SECTION C3: HAIO.SG 3D BLOCK EXPLORER + UAE CONSTRUCTION & TRAFFIC INSPECTOR
    // =========================================================================
    function showProjectInspector(pid, fly = true) {
      selected3DProjectId = pid;
      currentInspState = { type: "project", id: pid };
      switchDrawerTab("insp");
      const p = DATA.projects.find(x => x.project_id === pid);
      if (!p) return;
      const link = DATA.impact_links.find(x => x.project_id === pid);
      const docs = DATA.documents.filter(d => d.project_id === pid);
      const [lat, lon] = parseCoord(p.coordinates);
      const spec = getProject3DSpec(p);

      sync3DMapLayers();
      if (fly) {
        flyBothMaps(lat, lon, window.innerWidth <= 768 ? 15.6 : 16.25, 58, 60);
        document.getElementById("hudScope").textContent = `${p.project_id}: ${p.project_name.split('(')[0].trim()}`;
      }

      const primRoadObs = link ? getRoadObsForWindow(link.primary_road_id, currentTimeWindow) : null;
      const st = projectScaleStyle(p);
      const cleanTitle = p.project_name.split("(")[0].trim();
      const u4br = Math.max(16, Math.round(spec.homes * 0.50));
      const u5br = Math.max(16, spec.homes - u4br);

      const docsHtml = docs.map(d =>
        `<div style="margin-bottom:4px;">• <a href="${d.document_url}" target="_blank" rel="noopener">${d.document_title} ↗</a> <span style="color:#64748b;">(${d.document_type} | ${d.availability_status})</span></div>`
      ).join("") || "Linked in Task 1 Document Archive";

      const projOptionsHtml = DATA.projects.map(pr => {
        return `<option value="${pr.project_id}" ${pr.project_id === pid ? 'selected' : ''}>${pr.project_id}: ${pr.project_name.split('(')[0].trim()} (${pr.emirate} · ${pr.city_district_community.split('/')[0].trim()})</option>`;
      }).join("");

      document.getElementById("inspectorContainer").innerHTML = `
        <div style="padding:2px 2px 10px;">
          <!-- Compact Project Switcher at Top -->
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px; margin-bottom:10px;">
            <select class="haio-select" style="padding:6px 10px; font-size:0.75rem; background:#f8fafc; border-color:#e2e8f0;" onchange="showProjectInspector(this.value, true)" aria-label="Select Active Construction Project">
              ${projOptionsHtml}
            </select>
            <button class="mobile-back-map-btn" onclick="document.getElementById('mapStage').scrollIntoView({behavior:'smooth',block:'center'})">🗺️ ↑ Map</button>
          </div>

          <!-- HAIO.SG EXACT CLEAN HEADER & SUBTITLE -->
          <h3 class="haio-card-title">${cleanTitle}</h3>
          <div class="haio-card-sub">${spec.homes.toLocaleString()} homes · 2 stacks · 1 blocks · ${p.project_id}</div>

          <!-- BLOCK SELECTOR -->
          <label class="haio-field-lbl">BLOCK</label>
          <select class="haio-select" style="margin-bottom:12px;" onchange="update3DBlockControls(this.value, undefined, undefined, undefined)" aria-label="Select 3D Building Block">
            <option value="ALL" ${active3DBlock === 'ALL' ? 'selected' : ''}>All blocks</option>
            <option value="B1" ${active3DBlock === 'B1' ? 'selected' : ''}>Block 1 (Tower · ${spec.storeys} storeys)</option>
            <option value="B2" ${active3DBlock === 'B2' ? 'selected' : ''}>Podium &amp; Sky-Garden (12 storeys)</option>
          </select>

          <!-- FLOOR & STACK 2-COLUMN SELECTORS (100% UNLOCKED) -->
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:14px;">
            <div>
              <label class="haio-field-lbl">FLOOR</label>
              <select class="haio-select" onchange="update3DBlockControls(undefined, this.value, undefined, undefined)" aria-label="Select Floor Zone">
                <option value="ALL" ${active3DFloor === 'ALL' ? 'selected' : ''}>Select a block / All</option>
                <option value="LOW" ${active3DFloor === 'LOW' ? 'selected' : ''}>Low-Rise (F01–F${Math.round(spec.storeys*0.35)})</option>
                <option value="MID" ${active3DFloor === 'MID' ? 'selected' : ''}>Mid-Rise (F${Math.round(spec.storeys*0.35)+1}–F${Math.round(spec.storeys*0.72)})</option>
                <option value="HIGH" ${active3DFloor === 'HIGH' ? 'selected' : ''}>Sky Suites (F${Math.round(spec.storeys*0.72)+1}–F${spec.storeys})</option>
              </select>
            </div>
            <div>
              <label class="haio-field-lbl">STACK</label>
              <select class="haio-select" onchange="update3DBlockControls(undefined, undefined, this.value, undefined)" aria-label="Select Stack">
                <option value="ALL" ${active3DStack === 'ALL' ? 'selected' : ''}>Select floor first / All</option>
                <option value="S1" ${active3DStack === 'S1' ? 'selected' : ''}>Stack 01 (North Wing)</option>
                <option value="S2" ${active3DStack === 'S2' ? 'selected' : ''}>Stack 02 (South Wing)</option>
              </select>
            </div>
          </div>

          <!-- SHOW ME PILLS -->
          <label class="haio-field-lbl">SHOW ME</label>
          <div class="haio-showme-row">
            <button class="haio-showme-pill ${active3DShowMe === 'all' ? 'active' : ''}" onclick="update3DBlockControls(undefined, undefined, undefined, 'all')">All homes</button>
            <button class="haio-showme-pill ${active3DShowMe === '4br' ? 'active' : ''}" onclick="update3DBlockControls(undefined, undefined, undefined, '4br')">4 bedrooms</button>
            <button class="haio-showme-pill ${active3DShowMe === '5br' ? 'active' : ''}" onclick="update3DBlockControls(undefined, undefined, undefined, '5br')">5 bedrooms</button>
          </div>

          <!-- UNIT TYPES · HOMES SUMMARY BAR -->
          <label class="haio-field-lbl">UNIT TYPES · HOMES</label>
          <div class="haio-unit-bar">
            <span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:9px;height:9px;border-radius:50%;background:#fbbf24;display:inline-block;"></span> 4BR</span>
            <strong>${u4br}</strong>
            <span style="display:inline-flex; align-items:center; gap:6px; margin-left:8px;"><span style="width:9px;height:9px;border-radius:50%;background:#34d399;display:inline-block;"></span> 5BR</span>
            <strong>${u5br}</strong>
          </div>

          <p style="font-size:0.75rem; color:#64748b; line-height:1.45; margin:8px 0 12px;">
            Exterior shown plain: the developer's façade is not on file, so glass and slab edges are neutral and illustrative. Pick a block to colour homes by unit type.
          </p>

          <!-- OR PICK A BLOCK -->
          <label class="haio-field-lbl">OR PICK A BLOCK</label>
          <div class="haio-block-grid">
            <div class="haio-block-card ${active3DBlock === 'B1' ? 'active' : ''}" onclick="select3DBlockCard('B1')">
              <strong>Block 1</strong>
              <span>Stacks 01 to 32<br/>${spec.storeys} storeys</span>
            </div>
          </div>
          <div style="font-size:0.73rem; color:#64748b; margin-bottom:12px;">Tap a block to look closer · Ctrl or ⌘ + drag to turn</div>

          <div class="haio-divider"></div>

          <!-- UAE CONSTRUCTION & SURROUNDING ROAD TRAFFIC INTELLIGENCE -->
          <label class="haio-field-lbl" style="color:#2563eb;">UAE CONSTRUCTION &amp; SURROUNDING ROAD TRAFFIC IMPACT</label>

          ${primRoadObs && link ? `
          <div class="live-window-banner" style="margin-top:6px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:4px;">
              <strong style="color:#2563eb;">⏱️ ${currentTimeWindow.split('(')[0].trim()} Speed</strong>
              <span style="color:${congestionColor(primRoadObs.congestion_level)}; font-weight:800;">~${primRoadObs.average_speed_kmh} km/h (${primRoadObs.travel_time_min_per_10km} min/10km)</span>
            </div>
            <div style="margin-top:4px; color:#334155; font-size:0.74rem;">
              Access Road: <a href="javascript:void(0)" onclick="showRoadInspector('${link.primary_road_id}')"><strong>${link.primary_road_name} (${link.primary_road_id})</strong></a> · <strong>${link.distance_to_primary_road_km} km</strong> Haversine<br/>
              Status: <strong>${primRoadObs.congestion_level.split('(')[0].trim()} Congestion</strong> · V/C = ${primRoadObs.vc_ratio} (${primRoadObs.modelled_demand_vph_dir}/${primRoadObs.reference_capacity_vph_dir} vph/dir)
            </div>
          </div>` : ""}

          <div class="exec-metric-grid">
            <div class="exec-metric-box">
              <div class="em-lbl">Published Investment</div>
              <div class="em-val" style="color:#2563eb;">${(p.published_investment_value || '').split('[')[0].trim()}</div>
              <div class="em-sub">GFA: ${(p.gross_floor_area || '').split('[')[0].trim()}</div>
            </div>
            <div class="exec-metric-box">
              <div class="em-lbl">Developer &amp; Status</div>
              <div class="em-val" style="font-size:0.78rem; color:#059669;">${p.developer.split('(')[0].trim()}</div>
              <div class="em-sub">${p.lifecycle_status.split('(')[0].trim()}</div>
            </div>
            <div class="exec-metric-box">
              <div class="em-lbl">Scenario HGV Load</div>
              <div class="em-val" style="color:#d97706;">${link ? `${link.total_hgv_round_trips_day} trips/day` : "N/A"}</div>
              <div class="em-sub">${link ? `${link.total_hgv_one_way_movements_day} one-way/day` : ""}</div>
            </div>
            <div class="exec-metric-box">
              <div class="em-lbl">Epistemic Tier</div>
              <div class="em-val" style="font-size:0.75rem;">${link ? link.epistemic_impact_classification.split(':')[0] : "Tier 2"}</div>
              <div class="em-sub">${p.city_district_community.split('/')[0].trim()}</div>
            </div>
          </div>

          <details class="tech-accordion">
            <summary>4-Component HGV Logistics &amp; Corridor Connections</summary>
            <div class="tech-body">
              ${link ? `
              <div style="margin-bottom:6px;"><strong>Epistemic Classification:</strong> ${link.epistemic_impact_classification}</div>
              <div style="margin-bottom:6px;"><strong>Published RTA/SRTA Benchmark:</strong> ${link.published_road_capacity_and_upgrade_fact}</div>
              <div style="margin-bottom:6px;"><strong>Connected Corridors:</strong> Primary: <a href="javascript:void(0)" onclick="showRoadInspector('${link.primary_road_id}')">${link.primary_road_name}</a> (${link.distance_to_primary_road_km} km to <code>[${link.nearest_road_vertex_wgs84}]</code>) | Secondary: <a href="javascript:void(0)" onclick="showRoadInspector('${link.secondary_road_id}')">${link.secondary_road_name}</a> (${link.distance_to_secondary_road_km} km)</div>
              <div><strong>4-Component Daily HGV Breakdown (${link.total_hgv_round_trips_day} round-trips/d):</strong> Mixers: ${link.concrete_mixer_loads_day}/d | Rebar: ${link.rebar_trailer_loads_day}/d | Tippers: ${link.earthworks_tipper_loads_day}/d | MEP: ${link.mep_fitout_truck_loads_day}/d</div>
              ` : ""}
            </div>
          </details>

          <details class="tech-accordion">
            <summary>Official Documents (${docs.length}), Contractors &amp; Provenance</summary>
            <div class="tech-body">
              <div style="margin-bottom:6px;"><strong>Contractors &amp; Consultants:</strong> ${p.main_contractor_and_consultants}</div>
              <div style="margin-bottom:6px;"><strong>Official Documents (${docs.length}):</strong> ${docsHtml}</div>
              <div><strong>Provenance:</strong> <a href="${p.source_url}" target="_blank" rel="noopener">${p.publisher} ↗</a> ${link ? `| <a href="${link.corridor_source_url}" target="_blank" rel="noopener">${link.corridor_source_title} ↗</a>` : ""}</div>
            </div>
          </details>
        </div>
      `;
    }

    function showSubdevInspector(sd, fly = true) {
      currentInspState = { type: "subdev", obj: sd };
      switchDrawerTab("insp");
      if (fly) flyBothMaps(sd.latitude, sd.longitude, 15.4, 60, 45);
      const primObs = getRoadObsForWindow(sd.primary_access_road_id, currentTimeWindow);
      document.getElementById("inspectorContainer").innerHTML = `
        <div class="detail-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span class="brand-badge">${sd.subdev_id} • JVC 3D Sub-Cluster</span>
            <span class="conf-pill b-est">${sd.confidence}</span>
          </div>
          <h4>${sd.development_name}</h4>
          <div style="font-size:0.78rem; color:#2563eb; font-weight:700; margin-bottom:10px;">${sd.developer} • ${sd.community_district}</div>
          ${primObs ? `
          <div class="live-window-banner">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color:#2563eb;">⏱️ ${currentTimeWindow}</strong>
              <span style="color:${congestionColor(primObs.congestion_level)}; font-weight:800;">~${primObs.average_speed_kmh} km/h on ${sd.primary_access_road_id}</span>
            </div>
            <div style="margin-top:2px; color:#334155;">${primObs.congestion_level} (${primObs.travel_time_min_per_10km} min/10km)</div>
          </div>` : ""}
          <div class="exec-metric-grid">
            <div class="exec-metric-box"><div class="em-lbl">Active Towers</div><div class="em-val">${sd.building_count} Towers</div><div class="em-sub">${sd.floors_range}</div></div>
            <div class="exec-metric-box"><div class="em-lbl">Total Units</div><div class="em-val" style="color:#2563eb;">${sd.total_units.toLocaleString()}</div><div class="em-sub">${sd.active_gfa_sqm.toLocaleString()} m² GFA</div></div>
          </div>
          <div style="margin-bottom:8px;"><span class="ep-badge ep-t3">${sd.epistemic_impact_tier}</span></div>
          <div class="kv-grid">
            <div class="kv-row"><div class="kv-lbl">Construction Status &amp; Primary Corridor</div><div class="kv-val">${sd.construction_status}<br/>Corridor: <a href="javascript:void(0)" onclick="showRoadInspector('${sd.primary_access_road_id}')">${sd.primary_access_road_id}</a> (<strong>${sd.distance_to_road_km} km</strong> to vertex)</div></div>
          </div>
          <details class="tech-accordion">
            <summary>Technical Details: Vertex Coordinates &amp; HGV Modelling Assumptions</summary>
            <div class="tech-body">
              <div style="margin-bottom:5px;"><strong>Task 1 Cross-Reference:</strong> ${sd.linked_task1_ref}</div>
              <div style="margin-bottom:5px;"><strong>Nearest-Vertex Geometry:</strong> Centroid [${sd.latitude.toFixed(4)}, ${sd.longitude.toFixed(4)}] → Vertex [${sd.nearest_road_vertex_wgs84}] (${sd.distance_to_road_km} km Haversine).</div>
              <div><strong>Scenario HGV Movements:</strong> ${sd.estimated_midday_hgv_trips_per_day}<br/><span style="color:#b45309;">${sd.hgv_modelling_assumptions_and_sensitivity}</span></div>
            </div>
          </details>
        </div>
      `;
    }

    // =========================================================================
    // SECTION C4: ROAD-LEVEL DETAIL PANEL (Executive Summary + Progressive Disclosure)
    // =========================================================================
    function showRoadInspector(roadId, fly = true) {
      currentInspState = { type: "road", id: roadId };
      switchDrawerTab("insp");
      const r = DATA.roads.find(x => x.road_id === roadId);
      if (!r) return;
      const allWindowObs = ALL_TIME_WINDOWS.map(tp => getCorridorProfileForWindow(r, tp).obs).filter(Boolean);
      const activeObs = getCorridorProfileForWindow(r, currentTimeWindow).obs;
      const cityObs = DATA.observations.find(o => o.observation_id === "OBS-DXB-CITY-00");
      const connectedLinks = DATA.impact_links.filter(l => l.primary_road_id === roadId || l.secondary_road_id === roadId);
      const midPt = r.geometry_wgs84[Math.floor(r.geometry_wgs84.length / 2)];
      if (fly) flyBothMaps(midPt[1], midPt[0], 13.6, 55, 35);

      const obsHtml = allWindowObs.map(o => {
        const isCurrent = o.time_period === currentTimeWindow;
        const srcHtml = o.source_url
          ? `<a href="${o.source_url}" target="_blank" rel="noopener">${o.source_id}: ${o.source_report_title || 'Official Source'} (${o.publication_date || ''}) ↗</a>`
          : o.source_id;
        return `
        <div onclick="setTimeWindow('${o.time_period}')" style="cursor:pointer; background:${isCurrent ? '#eff6ff' : '#ffffff'}; border:${isCurrent ? '1.5px solid #2563eb' : '1px solid #e2e8f0'}; padding:9px; border-radius:10px; margin-bottom:7px; transition:all 0.15s;">
          <div style="display:flex; justify-content:space-between; align-items:center; font-weight:700; color:#0f172a; gap:4px; flex-wrap:wrap;">
            <span>${isCurrent ? '🔵 ' : ''}${o.time_period} ${isCurrent ? '<span style="font-size:0.62rem; background:#2563eb; color:#fff; padding:1px 6px; border-radius:999px; margin-left:4px;">ACTIVE</span>' : ''}</span>
            <span style="color:${congestionColor(o.congestion_level)};">~${o.average_speed_kmh} km/h (${o.travel_time_min_per_10km} min/10km)</span>
          </div>
          <div style="font-size:0.72rem; color:#059669; margin-top:4px;"><span class="ep-pill-pub">PUBLISHED</span> ${o.officially_published_corridor_benchmark}</div>
          <div style="font-size:0.72rem; color:#334155; margin-top:4px;"><span class="ep-pill-mod">MODELLED</span> <strong>${o.congestion_level.split('(')[0].trim()} Congestion (V/C=${o.vc_ratio})</strong> | Volume: ${o.traffic_volume_vph}</div>
          <details class="tech-accordion" style="margin-top:6px;" onclick="event.stopPropagation()">
            <summary>BPR Equation Breakdown &amp; Source (${o.observation_id})</summary>
            <div class="tech-body">
              <div><strong>Two-Term BPR + Bottleneck Formula:</strong> v₀=${o.free_flow_speed_kmh} km/h (t₀=${o.free_flow_time_min_per_10km} min/10km) | V/C=${o.vc_ratio} (${o.modelled_demand_vph_dir}/${o.reference_capacity_vph_dir} vph/dir) → <strong>Uninterrupted BPR Link: ${o.bpr_uninterrupted_speed_kmh} km/h (${o.bpr_uninterrupted_time_min_per_10km} min/10km)</strong> + <strong>Bottleneck Assumption (+d_adj): +${o.bottleneck_and_control_delay_min_per_10km} min/10km</strong> = <strong>${o.travel_time_min_per_10km} min/10km → ${o.average_speed_kmh} km/h</strong></div>
              <div style="margin-top:4px;"><strong>Derivation:</strong> ${o.modelled_assumptions_and_derivation}</div>
              <div style="margin-top:4px;"><strong>2024 vs 2026 Comparison:</strong> ${o.comparison_period}</div>
              <div style="margin-top:4px;"><strong>Source:</strong> ${srcHtml}</div>
            </div>
          </details>
        </div>`;
      }).join("");

      const projHtml = connectedLinks.map(l =>
        `<div style="margin-bottom:3px;">• <a href="javascript:void(0)" onclick="showProjectInspector('${l.project_id}')"><strong>${l.project_id}</strong>: ${l.project_name}</a> (${l.distance_to_primary_road_km} km — ${l.epistemic_impact_classification.split('(')[0]})</div>`
      ).join("") || "Serves general corridor traffic";

      document.getElementById("inspectorContainer").innerHTML = `
        <div class="detail-card">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px; flex-wrap:wrap; margin-bottom:6px;">
            <span class="brand-badge">${r.road_id} • ${r.road_code}</span>
            <div style="display:flex; gap:6px; align-items:center;">
              <button class="mobile-back-map-btn" onclick="document.getElementById('mapStage').scrollIntoView({behavior:'smooth',block:'center'})">🗺️ ↑ Map</button>
              <span class="conf-pill ${r.confidence === 'Verified' ? 'b-ver' : 'b-est'}">${r.confidence}</span>
            </div>
          </div>
          <h4>${r.road_name}</h4>
          <div style="font-size:0.78rem; color:#2563eb; font-weight:700; margin-bottom:10px;">${r.authority} • ${r.road_type}</div>

          ${activeObs ? `
          <div class="live-window-banner">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color:#2563eb;">⏱️ ${currentTimeWindow}</strong>
              <span style="color:${congestionColor(activeObs.congestion_level)}; font-weight:800;">~${activeObs.average_speed_kmh} km/h (${activeObs.travel_time_min_per_10km} min/10km)</span>
            </div>
            <div style="margin-top:3px; color:#334155;"><strong>${activeObs.congestion_level.split('(')[0].trim()} Congestion</strong> | V/C = ${activeObs.vc_ratio} (${activeObs.modelled_demand_vph_dir}/${activeObs.reference_capacity_vph_dir} vph/dir)</div>
          </div>` : ""}

          <div class="exec-metric-grid">
            <div class="exec-metric-box">
              <div class="em-lbl">Speed Limit &amp; Lanes</div>
              <div class="em-val">${r.speed_limit_kmh}</div>
              <div class="em-sub">${r.lanes_per_direction} lanes/dir (${r.direction})</div>
            </div>
            <div class="exec-metric-box">
              <div class="em-lbl">Published Capacity</div>
              <div class="em-val" style="color:#059669; font-size:0.78rem;">${r.capacity_vph_per_dir}</div>
              <div class="em-sub">Connected Sites: ${connectedLinks.length}</div>
            </div>
          </div>

          <div class="kv-grid">
            <div class="kv-row"><div class="kv-lbl">HGV Truck Ban &amp; Salik Toll Policy</div><div class="kv-val"><strong>HGV Rule:</strong> ${r.hgv_truck_ban_window}<br/><strong>Salik:</strong> ${r.salik_toll_status}</div></div>
            <div class="kv-row"><div class="kv-lbl">Corridor Traffic Across All 4 Time Windows (Click Any Window to Sync Map)</div><div class="kv-val">${obsHtml}</div></div>
            <div class="kv-row"><div class="kv-lbl">Connected Construction Projects (${connectedLinks.length})</div><div class="kv-val">${projHtml}</div></div>
          </div>

          <details class="tech-accordion">
            <summary>Technical Details: Capacity Basis, Polyline Geometry &amp; City Baseline</summary>
            <div class="tech-body">
              <div style="margin-bottom:5px;"><strong>Capacity Basis:</strong> ${r.capacity_basis}</div>
              <div style="margin-bottom:5px;"><strong>Geometry Validation:</strong> ${r.geometry_source_and_validation}</div>
              ${cityObs && r.emirate === 'Dubai' ? `<div style="margin-bottom:5px;"><strong>Published City-Wide Reference (${cityObs.observation_id}):</strong> ${cityObs.officially_published_corridor_benchmark} (<a href="${cityObs.source_url}" target="_blank" rel="noopener">TomTom Dubai Index ↗</a>)</div>` : ""}
              <div><strong>Served Communities:</strong> ${r.served_communities} (Source: ${r.source_id})</div>
            </div>
          </details>
        </div>
      `;
    }

    function showIntersectionInspector(i, fly = true) {
      currentInspState = { type: "intersection", obj: i };
      switchDrawerTab("insp");
      if (fly) flyBothMaps(i.latitude, i.longitude, 15.2, 58, 40);
      document.getElementById("inspectorContainer").innerHTML = `
        <div class="detail-card">
          <span class="brand-badge">${i.intersection_id} • Critical Junction</span>
          <h4 style="margin-top:6px;">${i.intersection_name}</h4>
          <div class="kv-grid">
            <div class="kv-row"><div class="kv-lbl">Community &amp; Type</div><div class="kv-val">${i.community} — ${i.intersection_type}</div></div>
            <div class="kv-row"><div class="kv-lbl">Peak Level of Service (LOS)</div><div class="kv-val"><strong>${i.peak_level_of_service}</strong></div></div>
            <div class="kv-row"><div class="kv-lbl">RTA / SRTA Capital Upgrade &amp; Mitigation</div><div class="kv-val">${i.rta_upgrade_and_mitigation}</div></div>
            <div class="kv-row"><div class="kv-lbl">Connected Roads &amp; Projects</div><div class="kv-val">Roads: ${i.connected_road_ids}<br/>Projects: ${i.served_project_ids}</div></div>
          </div>
        </div>
      `;
    }

    function showCommunityInspector(c) {
      currentInspState = { type: "community", obj: c };
      switchDrawerTab("insp");
      document.getElementById("inspectorContainer").innerHTML = `
        <div class="detail-card">
          <span class="brand-badge">${c.community_id} • Community Hotspot</span>
          <h4 style="margin-top:6px;">${c.community_name}</h4>
          <div class="kv-grid">
            <div class="kv-row"><div class="kv-lbl">Construction Activity Index &amp; Rank</div><div class="kv-val"><strong style="color:#2563eb;">${c.construction_activity_index_score}</strong></div></div>
            <div class="kv-row"><div class="kv-lbl">Published Formula &amp; Analytical Limitations (Section D1)</div><div class="kv-val">${c.activity_index_formula_and_limitations}</div></div>
            <div class="kv-row"><div class="kv-lbl">Active Scale (2025–2029)</div><div class="kv-val"><strong>${c.active_developments_count} Active Developments</strong> | <strong>${c.active_towers_and_buildings} Towers/Clusters</strong> | <strong>${c.scheduled_units_2025_2029.toLocaleString()} Scheduled Units</strong> | <strong>${c.active_structural_gfa_sqm.toLocaleString()} m² Active GFA</strong></div></div>
            <div class="kv-row"><div class="kv-lbl">Flagship Projects &amp; Clusters</div><div class="kv-val">${c.flagship_project_ids}</div></div>
            <div class="kv-row"><div class="kv-lbl">Connected Road Corridors &amp; Observed Congestion</div><div class="kv-val"><strong>Roads:</strong> ${c.primary_road_corridors}<br/><strong>Observed Severity:</strong> ${c.observed_congestion_severity}</div></div>
          </div>
        </div>
      `;
    }

    // =========================================================================
    // WORK PACKAGE E: 3 INTERACTIVE USE CASES + SHARJAH EXPANSION
    // =========================================================================
    function runUseCase(num, fly = true) {
      currentUseCase = num;
      switchDrawerTab("uc");
      document.querySelectorAll(".uc-btn").forEach((b, idx) => b.classList.toggle("active", idx === num - 1));
      const hgvInfo = getWindowHgvBannerInfo(currentTimeWindow);
      const d61Obs = getRoadObsForWindow("RD-DXB-05", currentTimeWindow);
      const e44Obs = getRoadObsForWindow("RD-DXB-03", currentTimeWindow);
      const e11Obs = getRoadObsForWindow("RD-DXB-01", currentTimeWindow);
      const jvcObs = getRoadObsForWindow("RD-DXB-07", currentTimeWindow);
      const shjObs = getRoadObsForWindow("RD-SHJ-01", currentTimeWindow);
      const e611ShjObs = getRoadObsForWindow("RD-SHJ-02", currentTimeWindow);

      const commRoadMap = {
        "COM-DXB-01": "RD-DXB-05",
        "COM-DXB-02": "RD-DXB-12",
        "COM-DXB-03": "RD-DXB-11",
        "COM-DXB-04": "RD-DXB-09",
        "COM-DXB-05": "RD-DXB-06",
        "COM-DXB-06": "RD-DXB-16",
        "COM-DXB-07": "RD-DXB-14"
      };

      if (num === 1) {
        if (fly) {
          document.getElementById("emirateSelect").value = "Dubai";
          populateCommunityDropdown();
          flyBothMaps(25.105, 55.245, 11.2, 48, 30);
          document.getElementById("hudScope").textContent = "Use Case 1: Dubai Construction Hotspots";
          renderAllMapLayers();
        }

        const dxbComms = DATA.communities.filter(c => c.emirate === "Dubai");
        const flagshipQuickJump = [
          { id: "PRJ-D6", name: "PRJ-D6: Binghatti Mercedes-Benz Places", area: "Downtown Dubai · AED 3.7B · D71 Financial Ctr Rd", tag: "Inspect Site →" },
          { id: "PRJ-D11", name: "PRJ-D11: Burj Binghatti Jacob & Co", area: "Business Bay · AED 3.0B · E44 Al Khail Rd", tag: "Inspect Site →" },
          { id: "PRJ-D3", name: "PRJ-D3: Dubai Creek Harbour Masterplan", area: "Creek Harbour · AED 55B · D62 Ras Al Khor Rd", tag: "Inspect Site →" },
          { id: "PRJ-D16", name: "PRJ-D16: DAMAC Lagoons Master Community", area: "Hessa St Corridor · AED 28B · D61 Hessa St", tag: "Inspect Site →" },
          { id: "PRJ-D1", name: "PRJ-D1: Al Maktoum Int'l Airport (DWC)", area: "Dubai South · AED 128B · E611 & E77 Freight", tag: "Inspect Site →" },
          { id: "PRJ-D2", name: "PRJ-D2: Palm Jebel Ali Mega-Island", area: "Jebel Ali Coast · AED 35B · E11 Sheikh Zayed Rd", tag: "Inspect Site →" }
        ];
        document.getElementById("useCaseContainer").innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Use Case 1 — City-Wide Hotspot Intelligence</span>
            <h4 style="margin-top:6px;">"Which areas in Dubai currently have the highest construction activity?"</h4>
            <div class="live-window-banner">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#1d4ed8;">⏱️ Active Window: ${currentTimeWindow}</strong>
                <span style="color:#0f172a; font-weight:800;">D61: ${d61Obs ? d61Obs.average_speed_kmh : 29} km/h • E44: ${e44Obs ? e44Obs.average_speed_kmh : 64} km/h • E11: ${e11Obs ? e11Obs.average_speed_kmh : 52} km/h</span>
              </div>
              <div style="margin-top:2px; font-size:0.68rem; color:#475569;">${hgvInfo.text}</div>
            </div>
            <p style="font-size:0.76rem; color:#334155;">Grounded in Task 1's 20 Dubai Flagship Projects (<code>PRJ-D1..D20</code>), DLD <code>dld_projects-open</code> active escrow registries, and DM GIS community boundaries, construction activity in Dubai is concentrated across <strong>6 primary clusters</strong>:</p>
            ${dxbComms.map(c => {
              const rId = commRoadMap[c.community_id] || "RD-DXB-05";
              const rObs = getRoadObsForWindow(rId, currentTimeWindow);
              const shortTier = rObs ? rObs.congestion_level.split('(')[0].trim() : c.observed_congestion_severity.split('(')[0].trim();
              return `
              <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:9px 11px; border-radius:11px; margin-bottom:7px; cursor:pointer; transition:all 0.15s;" onclick="flyBothMaps(${c.center_lat}, ${c.center_lon}, ${c.recommended_zoom}, 55, 35); showCommunityInspector(DATA.communities.find(x=>x.community_id==='${c.community_id}'))">
                <div style="display:flex; justify-content:space-between; font-size:0.79rem; font-weight:800; color:#0f172a;">
                  <span>${c.community_name}</span>
                  <span style="color:#2563eb;">${c.construction_activity_index_score.split(' ')[0]}</span>
                </div>
                <div style="font-size:0.72rem; color:#475569; margin-top:3px;">
                  <strong>${c.active_developments_count} Devs</strong> • <strong>${c.active_towers_and_buildings} Towers/Clusters</strong> • <strong>${c.scheduled_units_2025_2029.toLocaleString()} Units</strong> • <strong>${(c.active_structural_gfa_sqm/1e6).toFixed(2)}M m² GFA</strong>
                </div>
                ${rObs ? `<div style="font-size:0.71rem; color:${congestionColor(rObs.congestion_level)}; margin-top:3px; font-weight:700;">⏱️ ${currentTimeWindow.split(' ')[0]} (${rId}): ~${rObs.average_speed_kmh} km/h (${rObs.travel_time_min_per_10km} min/10km) • ${shortTier} Congestion (V/C=${rObs.vc_ratio})</div>` : `<div style="font-size:0.71rem; color:${congestionColor(c.observed_congestion_severity)}; margin-top:2px;">Traffic: ${shortTier}</div>`}
              </div>
            `;
            }).join("")}
            <div style="font-size:0.71rem; color:#64748b; border-top:1px solid #e2e8f0; padding-top:6px;">
              <strong>Key Analytical Insight:</strong> High construction GFA does <em>not</em> automatically produce severe congestion. <strong>Dubai South / DWC (7.85M m² GFA)</strong> experiences <em>Low–Moderate</em> congestion because it is served by 12-lane 24/7 HGV-exempt freeways (<code>E611</code> &amp; <code>E77</code>), whereas <strong>JVC (3.42M m² GFA)</strong> and <strong>Business Bay (3.85M m² GFA)</strong> experience <em>Severe</em> peak congestion due to arterial/collector access funnels.
            </div>
          </div>

          <div class="detail-card" style="margin-top:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <span style="font-size:0.72rem; font-weight:800; color:#0f172a; text-transform:uppercase; letter-spacing:0.05em;">🏗️ Flagship Construction Sites &amp; Corridors</span>
              <span style="font-size:0.68rem; color:#2563eb; font-weight:700;">Click to fly to site →</span>
            </div>
            ${flagshipQuickJump.map(l => `
              <div class="haio-launch-row" onclick="showProjectInspector('${l.id}')">
                <div>
                  <div class="haio-launch-name">${l.name}</div>
                  <div class="haio-launch-meta">${l.area}</div>
                </div>
                <span class="haio-launch-3d-tag">${l.tag}</span>
              </div>
            `).join("")}
          </div>
        `;
      } else if (num === 2) {
        if (fly) {
          document.getElementById("emirateSelect").value = "Dubai";
          populateCommunityDropdown();
          document.getElementById("communitySelect").value = "COM-DXB-01";
          flyBothMaps(25.0565, 55.2090, 14, 58, 35);
          document.getElementById("hudScope").textContent = "Use Case 2: JVC Construction & Traffic Impact";
          renderAllMapLayers();
        }

        document.getElementById("useCaseContainer").innerHTML = `
          <div class="detail-card">
            <span class="brand-badge" style="background:#ffe4e6; color:#be123c;">Use Case 2 — JVC Community Deep-Dive</span>
            <h4 style="margin-top:6px;">"Show construction activity in JVC and the surrounding traffic conditions."</h4>
            <div class="live-window-banner">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#1d4ed8;">⏱️ JVC Live Window: ${currentTimeWindow}</strong>
                <span style="color:${d61Obs ? congestionColor(d61Obs.congestion_level) : '#ef4444'}; font-weight:800;">D61: ~${d61Obs ? d61Obs.average_speed_kmh : 29} km/h</span>
              </div>
              <div style="margin-top:3px; color:#334155;">
                • <strong>Hessa St (D61):</strong> ~${d61Obs ? d61Obs.average_speed_kmh : 29} km/h (${d61Obs ? d61Obs.travel_time_min_per_10km : 20.68} min/10km | V/C=${d61Obs ? d61Obs.vc_ratio : 1.04})<br/>
                • <strong>Al Khail Rd (E44):</strong> ~${e44Obs ? e44Obs.average_speed_kmh : 64} km/h (${e44Obs ? e44Obs.travel_time_min_per_10km : 9.38} min/10km | V/C=${e44Obs ? e44Obs.vc_ratio : 0.82})<br/>
                • <strong>JVC Circle Blvd:</strong> ~${jvcObs ? jvcObs.average_speed_kmh : 28} km/h (${jvcObs ? jvcObs.travel_time_min_per_10km : 21.43} min/10km | V/C=${jvcObs ? jvcObs.vc_ratio : 0.89})
              </div>
              <div style="margin-top:2px; font-size:0.68rem; color:#475569;">${hgvInfo.text}</div>
            </div>
            <p style="font-size:0.76rem; color:#334155;"><strong>Jumeirah Village Circle (JVC)</strong> has <strong>38 active developments (64 towers, ~28,500 scheduled units, 3.42M m² active GFA)</strong> plus major Hessa St East masterplans (<a href="javascript:void(0)" onclick="showProjectInspector('PRJ-D16')">PRJ-D16 DAMAC Lagoons</a> &amp; <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-D19')">PRJ-D19 Tilal Al Ghaf</a>), all funneling into 3 primary corridors:</p>

            <div class="kv-grid">
              <div class="kv-row">
                <div class="kv-lbl">1. Officially Published RTA Capacity Benchmarks vs. Modelled Corridor Estimates</div>
                <div class="kv-val">
                  • <a href="javascript:void(0)" onclick="showRoadInspector('RD-DXB-05')"><strong>Hessa St (D61 West)</strong></a>: <strong>Officially Published RTA Fact (<code>SRC-433</code>):</strong> AED 689M upgrade widens D61 from 2 to 4 lanes/dir, doubling capacity from <strong>4,000 to 8,000 vph/dir</strong>. <strong>Modelled Corridor Estimate (Formula BPR + Modelled Bottleneck-Delay Assumption):</strong> AM Peak V/C=1.04 (4,160/4,000) → <code>v_BPR = 68.1 km/h</code> (8.81 min/10km) + <code>d_adj = +11.87 min/10km</code> (modelled queue/signal delay assumption) = <strong>20.68 min/10km → 29.0 km/h</strong>; PM Peak V/C=1.10 (4,400/4,000) → <code>v_BPR = 65.6 km/h</code> (9.15 min/10km) + <code>d_adj = +14.85 min/10km</code> = <strong>24.00 min/10km → 25.0 km/h</strong>.<br/>
                  • <a href="javascript:void(0)" onclick="showRoadInspector('RD-DXB-03')"><strong>Al Khail Rd (E44 JVC Segment)</strong></a>: <strong>Officially Published RTA Fact (<code>SRC-434</code>):</strong> AED 700M upgrade adds +15,000–19,600 vph capacity and cuts corridor travel time by <strong>30%</strong>. <strong>Modelled Corridor Estimate:</strong> AM Peak V/C=0.82 (9,348/11,400) → <code>v_BPR = 93.6 km/h</code> (6.41 min/10km) + <code>d_adj = +2.97 min/10km</code> (modelled weaving delay assumption) = <strong>9.38 min/10km → 64.0 km/h</strong> (vs. modelled 58.0 km/h PM Peak at V/C=0.86).
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">2. Tier 2 — Spatial Association &amp; Nearest-Vertex Geometry Validation</div>
                <div class="kv-val">
                  5 multi-tower JVC clusters (<a href="javascript:void(0)" onclick="showSubdevInspector(DATA.subdevs[0])">SUB-JVC-01 Binghatti [6 towers]</a>, <a href="javascript:void(0)" onclick="showSubdevInspector(DATA.subdevs[1])">SUB-JVC-02 Ellington</a>, <a href="javascript:void(0)" onclick="showSubdevInspector(DATA.subdevs[2])">SUB-JVC-03 Samana</a>, <a href="javascript:void(0)" onclick="showSubdevInspector(DATA.subdevs[3])">SUB-JVC-04 Tiger Sky 122F</a>, <a href="javascript:void(0)" onclick="showSubdevInspector(DATA.subdevs[4])">SUB-JVC-05 Nakheel</a>) sit <strong>0.50–1.19 km (WGS84 Haversine to nearest road polyline vertex)</strong> from JVC's Hessa St, Al Khail Rd, and Circle Blvd corridors.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">3. Tier 3 — Scenario-Based Estimated Daily HGV Movements (Not Observed Construction Traffic)</div>
                <div class="kv-val">
                  Because RTA bans HGVs on D61/E44 during <strong>06:30–08:30 &amp; 17:30–20:00</strong>, construction trucks are <em>not</em> the primary driver of AM/PM rush-hour queues. Using our 4-component scenario formula (8.5 m³ mixers, 25 t rebar trailers, 0.35 m³/m² earthworks in 18 m³ tippers, 0.18 t/m² MEP in 12 t trucks over 1,825 days; peak-phase multiplier 1.8x–2.5x), active JVC sites generate an estimated <strong>~168–280 HGV movements/hr during Midday (08:30–13:00) &amp; Night (20:30–05:00)</strong> on <a href="javascript:void(0)" onclick="showRoadInspector('RD-DXB-07')">JVC Circle Blvd</a>.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">4. Tier 4 — Confirmed Causal Impact &amp; RTA Mitigation</div>
                <div class="kv-val">
                  RTA's active <strong>AED 689M Hessa Street Improvement Project</strong> (widening D61 from 2 to 4 lanes/dir, doubling capacity from <strong>4,000 to 8,000 vph/dir</strong> + 4 grade-separated intersections) is the verified work zone &amp; long-term capacity solution.
                </div>
              </div>
            </div>
          </div>
        `;
      } else if (num === 3) {
        if (fly) {
          document.getElementById("emirateSelect").value = "Dubai";
          populateCommunityDropdown();
          flyBothMaps(25.125, 55.255, 12, 52, 30);
          document.getElementById("hudScope").textContent = "Use Case 3: Temporal & Historical Comparison";
          renderAllMapLayers();
        }

        document.getElementById("useCaseContainer").innerHTML = `
          <div class="detail-card">
            <span class="brand-badge" style="background:#ccfbf1; color:#0f766e;">Use Case 3 — Temporal &amp; Historical Analysis</span>
            <h4 style="margin-top:6px;">"Compare traffic conditions around construction hotspots across Morning, Midday, Evening &amp; 2024–2026."</h4>
            <div class="live-window-banner">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#1d4ed8;">⏱️ Selected Window: ${currentTimeWindow}</strong>
                <span style="color:#0f172a; font-weight:800;">D61: ${d61Obs ? d61Obs.average_speed_kmh : 29} km/h • E44: ${e44Obs ? e44Obs.average_speed_kmh : 64} km/h • E11: ${e11Obs ? e11Obs.average_speed_kmh : 52} km/h</span>
              </div>
              <div style="margin-top:2px; font-size:0.68rem; color:#475569;">${hgvInfo.text}</div>
            </div>
            <p style="font-size:0.75rem; color:#334155;">Use the <strong>Sun &amp; Time Window buttons</strong> on the bottom-left or inside the inspector to watch corridor speeds, colors, and BPR metrics update dynamically:</p>

            <div class="kv-grid">
              <div class="kv-row">
                <div class="kv-lbl">0. Published City-Wide Reference Only (TomTom Dubai Traffic Index — OBS-DXB-CITY-00)</div>
                <div class="kv-val">
                  • <strong>TomTom 2025 Dubai Traffic Index (<a href="https://www.tomtom.com/traffic-index/city/dubai/" target="_blank" rel="noopener">SRC-436 ↗</a>):</strong> <strong>31.3 km/h</strong> city-wide average speed (<strong>19 min 10 sec</strong> / 19.17 min per 10 km); <strong>42.7%</strong> annual congestion level; <strong>26.3 km/h</strong> overall rush-hour average speed; <strong>32.1 km/h</strong> morning rush-hour speed (<strong>18 min 41 sec</strong> per 10 km; <strong>42.3%</strong> congestion); <strong>22.6 km/h</strong> evening rush-hour speed (<strong>26 min 33 sec</strong> per 10 km; <strong>94.4%</strong> congestion). <em>Used strictly at city level; never disaggregated to individual road segments.</em>
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">1. Hessa Street (D61 — JVC North Gate • Published RTA Capacity: 4,000 → 8,000 vph/dir)</div>
                <div class="kv-val">
                  • <strong style="${currentTimeWindow.includes('Morning') ? 'color:#2563eb;' : ''}">Morning Peak (07:30–09:30):</strong> Formula BPR <code>v_BPR = 68.1 km/h</code> (8.81 min/10km at V/C=1.04) + modelled bottleneck-delay assumption <code>d_adj = +11.87 min/10km</code> = <strong>20.68 min/10km → 29.0 km/h</strong> (HGVs banned).<br/>
                  • <strong style="${currentTimeWindow.includes('Midday') ? 'color:#2563eb;' : ''}">Midday (12:00–14:00):</strong> Formula BPR <code>v_BPR = 75.8 km/h</code> (7.92 min/10km at V/C=0.78) + modelled bottleneck-delay assumption <code>d_adj = +4.58 min/10km</code> = <strong>12.50 min/10km → 48.0 km/h</strong>.<br/>
                  • <strong style="${currentTimeWindow.includes('Evening') ? 'color:#2563eb;' : ''}">Evening Peak (17:00–20:00):</strong> Formula BPR <code>v_BPR = 65.6 km/h</code> (9.15 min/10km at V/C=1.10) + modelled bottleneck-delay assumption <code>d_adj = +14.85 min/10km</code> = <strong>24.00 min/10km → 25.0 km/h</strong>.<br/>
                  • <strong style="${currentTimeWindow.includes('Night') ? 'color:#2563eb;' : ''}">Night (22:00–05:00):</strong> Formula BPR <code>v_BPR = 79.9 km/h</code> (7.51 min/10km at V/C=0.29) + modelled bottleneck-delay assumption <code>d_adj = +1.31 min/10km</code> = <strong>8.82 min/10km → 68.0 km/h</strong>.<br/>
                  • <strong>Modelled 2024 vs 2026 Delta:</strong> Modelled improvement from ~19–22 km/h (2024) to ~25–29 km/h as phased AED 689M flyovers open.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">2. Al Khail Road (E44 — Published RTA Benchmark: +15,000–19,600 vph &amp; 30% Travel-Time Reduction)</div>
                <div class="kv-val">
                  • <strong>Morning Peak:</strong> Formula BPR <code>v_BPR = 93.6 km/h</code> (6.41 min/10km at V/C=0.82 [9,348/11,400]) + modelled ramp-weave delay assumption <code>d_adj = +2.97 min/10km</code> = <strong>9.38 min/10km → 64.0 km/h</strong> (calibrated to <strong>RTA's published 30% travel-time reduction</strong> post-AED 700M bridges).<br/>
                  • <strong>Evening Peak:</strong> Formula BPR <code>v_BPR = 92.4 km/h</code> (6.49 min/10km at V/C=0.86 [9,804/11,400]) + modelled weave delay assumption <code>d_adj = +3.85 min/10km</code> = <strong>10.34 min/10km → 58.0 km/h</strong>.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">3. Sheikh Zayed Road (E11 — Published Salik Benchmark: AED 6 Peak / AED 4 Off-Peak)</div>
                <div class="kv-val">
                  • <strong>Morning Peak:</strong> Modelled ~52 km/h | <strong>Evening Peak:</strong> Modelled ~44 km/h.<br/>
                  • <strong>Published Salik Effect (<code>SRC-435</code>):</strong> Dynamic Salik pricing (Jan 31, 2025) + Al Safa South gate redistributes ~9–12% peak traffic. Zero daytime HGV impact due to 06:00–22:00 truck ban.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">Explicit Epistemic Guardrail (Section D5 &amp; E3)</div>
                <div class="kv-val" style="color:#b45309;">
                  Official RTA, SRTA, and Salik releases substantiate corridor capacities, bridge upgrades, travel-time reduction percentages, and HGV ban windows. TomTom's public Dubai Traffic Index is cited strictly at the city-wide level (<code>OBS-DXB-CITY-00</code>). All 21 corridor-level speed, volume, and congestion values (<code>OBS-DXB-001..015</code>, <code>OBS-SHJ-001..006</code>) are explicitly classified as <strong>Modelled Corridor Estimates</strong> (<code>confidence = "Estimated"</code>).
                </div>
              </div>
            </div>
          </div>
        `;
      } else if (num === 4) {
        if (fly) {
          document.getElementById("emirateSelect").value = "Sharjah";
          populateCommunityDropdown();
          flyBothMaps(25.312, 55.505, 12, 52, 30);
          document.getElementById("hudScope").textContent = "Priority 2: Sharjah Expansion (12 Projects)";
          renderAllMapLayers();
        }

        document.getElementById("useCaseContainer").innerHTML = `
          <div class="detail-card">
            <span class="brand-badge" style="background:#fef3c7; color:#b45309;">Priority 2 — Sharjah Expansion</span>
            <h4 style="margin-top:6px;">Sharjah Construction &amp; Corridor Intelligence (12 Flagships on Unified Architecture)</h4>
            <div class="live-window-banner">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#1d4ed8;">⏱️ Sharjah Active Window: ${currentTimeWindow}</strong>
                <span style="color:${shjObs ? congestionColor(shjObs.congestion_level) : '#ef4444'}; font-weight:800;">E311: ~${shjObs ? shjObs.average_speed_kmh : 28} km/h • E611: ~${e611ShjObs ? e611ShjObs.average_speed_kmh : 62} km/h</span>
              </div>
              <div style="margin-top:2px; font-size:0.68rem; color:#475569;">${hgvInfo.text}</div>
            </div>
            <p style="font-size:0.76rem; color:#334155;">Reusing the exact Dubai spatial schema, all 12 Sharjah Flagship Projects (<code>PRJ-SH1..SH12</code>) are mapped across Sharjah's 3 primary commuter &amp; megaproject corridors:</p>
            <div class="kv-grid">
              <div class="kv-row">
                <div class="kv-lbl">1. Muwaileh, Aljada &amp; Al Zahia Nexus (E311 × E88)</div>
                <div class="kv-val">
                  • <strong>Projects:</strong> <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH2')">PRJ-SH2 Aljada (25,000 units)</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH9')">PRJ-SH9 Al Zahia</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH8')">PRJ-SH8 Olfah</a>.<br/>
                  • <strong>Traffic (${currentTimeWindow}):</strong> <a href="javascript:void(0)" onclick="showRoadInspector('RD-SHJ-01')">E311 Industrial / National Paints</a> operates at <strong>~${shjObs ? shjObs.average_speed_kmh : 28} km/h (${shjObs ? shjObs.congestion_level.split('(')[0].trim() : 'Severe'})</strong>. SRTA &amp; Arada built dedicated Aljada/Airport Rd (E88) grade-separated bridges to bypass E311 queues.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">2. Emirates Road (E611) Forest &amp; Eco-City Belt</div>
                <div class="kv-val">
                  • <strong>Projects:</strong> <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH3')">PRJ-SH3 Masaar 1–3</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH5')">PRJ-SH5 Khalid Bin Sultan City (Zaha Hadid)</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH6')">PRJ-SH6 Hayyan</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH7')">PRJ-SH7 Tilal City</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH10')">PRJ-SH10 Sharjah Sustainable City</a>.<br/>
                  • <strong>Traffic (${currentTimeWindow}):</strong> <a href="javascript:void(0)" onclick="showRoadInspector('RD-SHJ-02')">Emirates Rd (E611)</a> operates at <strong>~${e611ShjObs ? e611ShjObs.average_speed_kmh : 62} km/h (${e611ShjObs ? e611ShjObs.congestion_level.split('(')[0].trim() : 'Moderate'})</strong>; SRTA's 320m Al Dhaid Bridge (E88) opens November 15, 2026.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">3. Al Khan Waterfront, Al Hamriyah North &amp; Khorfakkan East Coast (E11 / S142)</div>
                <div class="kv-val">
                  • <strong>Waterfront &amp; Coastal Corridors:</strong> <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH4')">PRJ-SH4 Maryam Island</a> (0.28 km to <a href="javascript:void(0)" onclick="showRoadInspector('RD-SHJ-04')">RD-SHJ-04 Al Ittihad Rd E11</a>); <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH1')">PRJ-SH1 Sharjah Waterfront City</a> (0.37 km to <a href="javascript:void(0)" onclick="showRoadInspector('RD-SHJ-07')">RD-SHJ-07 Al Ittihad Rd North E11 Al Hamriyah</a>); and <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH11')">PRJ-SH11 Khorfakkan Beach Resort</a> (0.30 km to <a href="javascript:void(0)" onclick="showRoadInspector('RD-SHJ-06')">RD-SHJ-06 Sharjah–Khorfakkan Highway S142 East Coast</a>).
                </div>
              </div>
            </div>
          </div>
        `;
      }
    }

    // =========================================================================
    // WORK PACKAGE F: DETERMINISTIC DATABASE Q&A ENGINE WITH MAP AUTO-ZOOM
    // =========================================================================
    const PRESET_QUESTIONS = [
      "Which areas in Dubai currently have the highest construction activity?",
      "Show construction activity in JVC and the surrounding traffic conditions.",
      "Compare traffic conditions around Hessa St & JVC during morning and evening periods.",
      "Which projects are near major road intersections and bottlenecks?",
      "What traffic data and freight capacity are available around Dubai South & DWC?",
      "Which communities have both active construction and observed severe congestion?",
      "Which projects and corridors have published Traffic Impact Studies (TIS) vs. restricted files?",
      "How does TomTom compare against Dubai Pulse / RTA Open Data, HERE, and Google Maps?"
    ];

    function askPreset(idx) {
      document.getElementById("qaInput").value = PRESET_QUESTIONS[idx];
      runDeterministicQA();
    }

    function runDeterministicQA() {
      switchDrawerTab("qa");
      const rawQ = (document.getElementById("qaInput").value || "").trim();
      const q = rawQ.toLowerCase();
      const out = document.getElementById("qaResultContainer");

      if (!q) {
        out.innerHTML = `<div class="detail-card">Please enter a question or click one of the 8 verified preset queries above.</div>`;
        return;
      }

      // Deterministic query routing over DATA tables
      if (q.includes("jvc") || q.includes("jumeirah village") || (q.includes("hessa") && !q.includes("compare") && !q.includes("morning"))) {
        runUseCase(2);
        switchDrawerTab("qa");
        const jvcLinks = DATA.impact_links.filter(l => l.community.toLowerCase().includes("jvc") || l.primary_road_id.includes("RD-DXB-05") || l.primary_road_id.includes("RD-DXB-06"));
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic SQL/JSON Query Result • Auto-Zoomed to JVC [25.0565, 55.2090]</span>
            <h4 style="margin-top:6px;">JVC &amp; Hessa Street Construction-to-Traffic Query (${jvcLinks.length} Linked Records)</h4>
            <p style="font-size:0.76rem; color:#334155;"><strong>Database Findings:</strong> JVC (<code>COM-DXB-01</code>) records <strong>38 active developments, 64 active towers, 28,500 scheduled units, and 3,420,000 m² active structural GFA</strong>. Officially published RTA capacity on <code>RD-DXB-05</code> (Hessa St D61) doubles from <strong>4,000 to 8,000 vph/dir</strong> under the AED 689M upgrade, while modelled corridor speeds are <strong>~29 km/h (AM Peak)</strong> and <strong>~25 km/h (PM Peak — Severe)</strong>, and <code>RD-DXB-03</code> (Al Khail Rd E44) is modelled at <strong>~58–64 km/h</strong> calibrated to RTA's published 30% travel-time reduction.</p>
            <div class="kv-grid">
              ${jvcLinks.map(l => `
                <div class="kv-row" style="cursor:pointer;" onclick="showProjectInspector('${l.project_id}')">
                  <div class="kv-lbl">${l.project_id} → ${l.primary_road_id} (${l.distance_to_primary_road_km} km Haversine to [${l.nearest_road_vertex_wgs84}])</div>
                  <div class="kv-val"><strong>${l.project_name}</strong><br/><span style="color:#059669; font-weight:700;">${l.published_road_capacity_and_upgrade_fact}</span><br/>${l.observed_road_traffic_condition}<br/><em>${l.modelled_daily_hgv_concrete_rebar_trips}</em><br/><span style="color:#2563eb; font-weight:700;">${l.epistemic_impact_classification}</span></div>
                </div>
              `).join("")}
            </div>
            <div style="margin-top:8px; font-size:0.70rem; color:#64748b;"><strong>Sources:</strong> DLD <code>dld_projects-open</code> (<code>SRC-020</code> JVC Master Community), RTA AED 689M Hessa St D61 Capacity Release (<code>SRC-433</code>), and RTA AED 700M Al Khail Rd E44 Capacity Release (<code>SRC-434</code>).</div>
          </div>
        `;
      } else if (q.includes("morning") || q.includes("evening") || q.includes("compare") || q.includes("vary") || q.includes("time")) {
        flyBothMaps(25.0645, 55.2095, 13, 55, 35);
        const d61Obs = DATA.observations.filter(o => o.road_id === "RD-DXB-05" || o.road_id === "RD-DXB-03");
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic Temporal Comparison Query • Hessa St (D61) &amp; Al Khail Rd (E44)</span>
            <h4 style="margin-top:6px;">Morning vs. Midday vs. Evening vs. Night Traffic Comparison (${d61Obs.length} Modelled Corridor Scenarios)</h4>
            <div class="kv-grid">
              ${d61Obs.map(o => `
                <div class="kv-row" style="cursor:pointer;" onclick="showRoadInspector('${o.road_id}')">
                  <div class="kv-lbl">${o.road_id} • ${o.time_period} (${o.evidence_level})</div>
                  <div class="kv-val"><strong>Corridor Speed: ~${o.average_speed_kmh} km/h</strong> (${o.travel_time_min_per_10km} min/10km) | <strong>Uninterrupted BPR: ${o.bpr_uninterrupted_speed_kmh} km/h</strong> (${o.bpr_uninterrupted_time_min_per_10km} min/10km at V/C=${o.vc_ratio}) + <strong>Bottleneck Delay (+d_adj): +${o.bottleneck_and_control_delay_min_per_10km} min/10km</strong><br/><strong>Published Benchmark:</strong> <span style="color:#059669; font-weight:700;">${o.officially_published_corridor_benchmark}</span><br/><strong>Modelled Derivation:</strong> ${o.modelled_assumptions_and_derivation}<br/><strong>Modelled Volume:</strong> ${o.traffic_volume_vph}</div>
                </div>
              `).join("")}
            </div>
            <div style="margin-top:8px; font-size:0.71rem; color:#b45309;"><strong>Epistemic Notice:</strong> Corridor capacities and upgrade travel-time reduction targets are officially published by RTA (<code>SRC-433</code>, <code>SRC-434</code>). Segment-specific hourly speeds and volumes are Modelled Corridor Estimates derived via the BPR volume-delay function.</div>
          </div>
        `;
      } else if (q.includes("dubai south") || q.includes("dwc") || q.includes("maktoum") || q.includes("expo") || q.includes("e611")) {
        flyBothMaps(24.9120, 55.1580, 12, 52, 35);
        const dsLinks = DATA.impact_links.filter(l => ["PRJ-D1", "PRJ-D15", "PRJ-D18", "PRJ-D6"].includes(l.project_id));
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic Spatial Query • Auto-Zoomed to Dubai South &amp; DWC [24.912, 55.158]</span>
            <h4 style="margin-top:6px;">Dubai South, Expo City &amp; DWC Airport Traffic &amp; Freight Intelligence</h4>
            <p style="font-size:0.76rem; color:#334155;"><strong>Database Findings:</strong> Dubai South (<code>COM-DXB-04</code>) has the largest active construction GFA in the UAE (<strong>7.85M m²</strong> across <code>PRJ-D1</code> DWC AED 128B Airport, <code>PRJ-D15</code> Azizi Venice &amp; <code>PRJ-D18</code> Expo City), yet modelled congestion is <strong>Low (~86 km/h modelled speed on E611, LOS B)</strong> because <strong>Emirates Road (E611)</strong> provides a published 11,400 vph/dir 6-lane capacity and is <strong>100% exempt from Dubai's daytime HGV truck bans</strong>.</p>
            <div class="kv-grid">
              ${dsLinks.map(l => `
                <div class="kv-row" style="cursor:pointer;" onclick="showProjectInspector('${l.project_id}')">
                  <div class="kv-lbl">${l.project_id}: ${l.project_name}</div>
                  <div class="kv-val">Connected Road: <strong>${l.primary_road_name} (${l.distance_to_primary_road_km} km)</strong><br/>Modelled Freight: ${l.modelled_daily_hgv_concrete_rebar_trips}<br/>HGV Policy: ${l.hgv_routing_and_ban_compliance}</div>
                </div>
              `).join("")}
            </div>
          </div>
        `;
      } else if (q.includes("intersection") || q.includes("junction") || q.includes("bottleneck")) {
        flyBothMaps(25.155, 55.275, 11, 50, 30);
        const nearInts = [...DATA.impact_links].sort((a, b) => a.distance_to_intersection_km - b.distance_to_intersection_km).slice(0, 8);
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic Spatial Proximity Query • Top 8 Projects Nearest Major Intersections</span>
            <h4 style="margin-top:6px;">Projects Ranked by Geodesic Proximity to Major Interchanges</h4>
            <div class="kv-grid">
              ${nearInts.map(l => `
                <div class="kv-row" style="cursor:pointer;" onclick="showProjectInspector('${l.project_id}')">
                  <div class="kv-lbl">${l.project_id} (${l.distance_to_intersection_km} km to ${l.nearest_intersection_id})</div>
                  <div class="kv-val"><strong>${l.project_name}</strong><br/>Junction: ${l.nearest_intersection_name}<br/>Road: ${l.primary_road_name} (${l.distance_to_primary_road_km} km)</div>
                </div>
              `).join("")}
            </div>
          </div>
        `;
      } else if (q.includes("tis") || q.includes("traffic impact") || q.includes("study") || q.includes("studies")) {
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic TIS Registry Query • 8 Corridor &amp; Masterplan Studies</span>
            <h4 style="margin-top:6px;">Published RTA/SRTA Corridor Studies vs. Restricted Developer TIS Submissions</h4>
            <p style="font-size:0.75rem; color:#334155;">Individual plot-level consultant TIS reports submitted via the <strong>RTA Traffic Engineering System (TES)</strong> are confidential commercial records. However, <strong>RTA and SRTA publish official corridor-level engineering studies and capacity upgrades</strong> for all major hotspots:</p>
            <div class="kv-grid">
              ${DATA.tis.map(t => `
                <div class="kv-row">
                  <div class="kv-lbl">${t.tis_id} • ${t.location_community}</div>
                  <div class="kv-val"><strong>${t.project_or_corridor}</strong><br/><strong>Status:</strong> ${t.study_type_and_availability}<br/><strong>Forecast &amp; Mitigation:</strong> ${t.forecast_traffic_volumes} — ${t.proposed_mitigation_and_logistics}</div>
                </div>
              `).join("")}
            </div>
          </div>
        `;
      } else if (q.includes("tomtom") || q.includes("provider") || q.includes("here") || q.includes("google")) {
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic Provider Evaluation Query (Work Package A4)</span>
            <h4 style="margin-top:6px;">TomTom vs. Dubai Pulse/RTA vs. HERE vs. Google Maps vs. Mapbox</h4>
            <div class="kv-grid">
              ${DATA.providers.map(p => `
                <div class="kv-row">
                  <div class="kv-lbl">${p.provider_id}: ${p.provider_name}</div>
                  <div class="kv-val"><strong>Coverage &amp; Freq:</strong> ${p.dubai_and_uae_coverage} (${p.update_frequency})<br/><strong>Limits &amp; Pricing:</strong> ${p.api_rate_limits} | ${p.pricing_structure}<br/><strong>Retention Rule:</strong> ${p.commercial_usage_and_retention_terms}<br/><span style="color:#2563eb; font-weight:700;"><strong>Verdict:</strong> ${p.prototype_recommendation}</span></div>
                </div>
              `).join("")}
            </div>
          </div>
        `;
      } else if (q.includes("both") || q.includes("severe") || q.includes("hotspot") || q.includes("highest") || q.includes("concentrated")) {
        const ranked = [...DATA.communities].sort((a, b) => parseFloat(b.construction_activity_index_score) - parseFloat(a.construction_activity_index_score));
        flyBothMaps(25.155, 55.305, 11, 50, 30);
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic Hotspot &amp; Congestion Cross-Query (${ranked.length} Communities)</span>
            <h4 style="margin-top:6px;">Communities Ranked by Construction Activity Index &amp; Observed Congestion</h4>
            <div class="kv-grid">
              ${ranked.map(c => `
                <div class="kv-row" style="cursor:pointer;" onclick="flyBothMaps(${c.center_lat}, ${c.center_lon}, ${c.recommended_zoom}, 55, 35); showCommunityInspector(DATA.communities.find(x=>x.community_id==='${c.community_id}'))">
                  <div class="kv-lbl">${c.emirate} • Score: ${c.construction_activity_index_score}</div>
                  <div class="kv-val"><strong>${c.community_name}</strong><br/>Active Devs: ${c.active_developments_count} | Towers: ${c.active_towers_and_buildings} | Units: ${c.scheduled_units_2025_2029.toLocaleString()} | Active GFA: ${c.active_structural_gfa_sqm.toLocaleString()} m²<br/><strong style="color:${congestionColor(c.observed_congestion_severity)};">Congestion: ${c.observed_congestion_severity}</strong></div>
                </div>
              `).join("")}
            </div>
          </div>
        `;
      } else {
        // Generic keyword search across projects, roads, and communities
        const mProjs = DATA.projects.filter(p => JSON.stringify(p).toLowerCase().includes(q));
        const mRoads = DATA.roads.filter(r => JSON.stringify(r).toLowerCase().includes(q));
        if (mProjs.length > 0) {
          const [lat, lon] = parseCoord(mProjs[0].coordinates);
          flyBothMaps(lat, lon, 15.8, 60, 45);
        }
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic Keyword Search Result</span>
            <h4 style="margin-top:6px;">Matched ${mProjs.length} Projects &amp; ${mRoads.length} Road Corridors for "${rawQ}"</h4>
            <div class="kv-grid">
              ${mProjs.slice(0, 6).map(p => `
                <div class="kv-row" style="cursor:pointer;" onclick="showProjectInspector('${p.project_id}')">
                  <div class="kv-lbl">${p.project_id} • ${p.emirate}</div>
                  <div class="kv-val"><strong>${p.project_name}</strong> (${p.developer}) — ${p.city_district_community}</div>
                </div>
              `).join("")}
              ${mRoads.slice(0, 6).map(r => `
                <div class="kv-row" style="cursor:pointer;" onclick="showRoadInspector('${r.road_id}')">
                  <div class="kv-lbl">${r.road_id} • ${r.road_code}</div>
                  <div class="kv-val"><strong>${r.road_name}</strong> — ${r.capacity_vph_per_dir}</div>
                </div>
              `).join("")}
            </div>
          </div>
        `;
      }
    }

    function openEvTab(panelId, btnEl) {
      document.querySelectorAll(".ev-panel").forEach(p => p.classList.remove("active"));
      document.querySelectorAll(".ev-tab-btn").forEach(b => b.classList.remove("active"));
      document.getElementById(panelId).classList.add("active");
      if (btnEl) btnEl.classList.add("active");
    }

    window.addEventListener("DOMContentLoaded", initMap);
  </script>
</body>
</html>
""".replace("__PAYLOAD_JSON__", payload_json)

    full_html = html_doc + js_code
    out_path = WEB_DIR / "task2_gis_intelligence.html"
    out_path.write_text(full_html, encoding="utf-8")
    if ARTIFACT_DIR and ARTIFACT_DIR.exists():
        (ARTIFACT_DIR / "uae_construction_portal.html").write_text(full_html, encoding="utf-8")
    print(f"Built Task 2 Interactive GIS & Traffic Platform: {out_path} ({out_path.stat().st_size // 1024} KB)")

    # Inject a prominent, mobile-responsive Task 2 banner at the very top of web/index.html & web/validation_report.html
    banner_html = """<!-- TASK 2 GLOBAL SWITCHER BANNER -->
  <style>
    #task2-global-banner { background:linear-gradient(90deg,#090d16 0%,#0f172a 50%,#1e1b4b 100%); color:#fff; padding:9px 16px; border-bottom:2px solid #38bdf8; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; font-family:system-ui,sans-serif; z-index:9999; }
    #task2-global-banner .t2-links { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
    @media (max-width: 768px) {
      #task2-global-banner { padding:7px 10px; gap:5px; }
      #task2-global-banner .t2-title { font-size:0.78rem !important; line-height:1.25; }
      #task2-global-banner .t2-links { width:100%; overflow-x:auto; flex-wrap:nowrap; -webkit-overflow-scrolling:touch; scrollbar-width:none; padding-bottom:2px; }
      #task2-global-banner .t2-links::-webkit-scrollbar { display:none; }
      #task2-global-banner .t2-links a { flex-shrink:0; white-space:nowrap; font-size:0.72rem !important; padding:4px 9px !important; }
    }
  </style>
  <div id="task2-global-banner">
    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
      <span style="background:#0284c7; color:#fff; font-weight:800; font-size:0.68rem; padding:2px 8px; border-radius:999px; text-transform:uppercase;">Task 2 Live</span>
      <strong class="t2-title" style="font-size:0.88rem;">Geographic Visualization &amp; Traffic Impact Intelligence (Dubai &amp; Sharjah)</strong>
    </div>
    <div class="t2-links">
      <a href="task2_gis_intelligence.html" style="background:#0284c7; border:1px solid #38bdf8; color:#fff; padding:5px 12px; border-radius:7px; font-weight:700; font-size:0.78rem; text-decoration:none;">🗺️ Launch Task 2 GIS Map →</a>
      <a href="datasets/dubai_sharjah_gis_bundle.geojson" style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.25); color:#bae6fd; padding:5px 10px; border-radius:7px; font-weight:600; font-size:0.74rem; text-decoration:none;">GeoJSON Bundle</a>
      <a href="datasets/21_task2_spatial_database.sqlite" style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.25); color:#bae6fd; padding:5px 10px; border-radius:7px; font-weight:600; font-size:0.74rem; text-decoration:none;">Spatial SQLite</a>
      <a href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/22_project_road_impact_links.csv" style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.25); color:#bae6fd; padding:5px 10px; border-radius:7px; font-weight:600; font-size:0.74rem; text-decoration:none;">Impact Links CSV</a>
    </div>
  </div>"""

    import re as _re
    for page_fn in ("index.html", "validation_report.html"):
        p_file = WEB_DIR / page_fn
        if p_file.exists():
            txt = p_file.read_text(encoding="utf-8")
            if "<!-- TASK 2 GLOBAL SWITCHER BANNER -->" in txt:
                txt = _re.sub(
                    r"<!-- TASK 2 GLOBAL SWITCHER BANNER -->.*?</div>\s*</div>",
                    banner_html,
                    txt,
                    count=1,
                    flags=_re.S,
                )
                p_file.write_text(txt, encoding="utf-8")
                print(f"Updated mobile-responsive Task 2 Navigation Banner in {page_fn}")
            elif "id=\"task2-global-banner\"" not in txt:
                txt = txt.replace("<body>", "<body>\n" + banner_html, 1)
                p_file.write_text(txt, encoding="utf-8")
                print(f"Injected Task 2 Navigation Banner into {page_fn}")


if __name__ == "__main__":
    main()
