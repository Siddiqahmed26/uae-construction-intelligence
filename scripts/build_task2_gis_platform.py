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
  <title>UAE Construction &amp; Traffic Intelligence — Executive GIS Platform</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🗺️</text></svg>"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
  <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" crossorigin=""/>
  <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js" crossorigin=""></script>
  <style>
    :root {{
      --bg-dark: #070b14;
      --panel-dark: #0d1424;
      --panel-card: #152036;
      --border: #263552;
      --text: #f8fafc;
      --muted: #94a3b8;
      --cyan: #38bdf8;
      --emerald: #10b981;
      --amber: #f59e0b;
      --orange: #f97316;
      --rose: #ef4444;
      --purple: #a855f7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
      background: var(--bg-dark);
      color: var(--text);
      line-height: 1.45;
      overflow-x: hidden;
    }}
    a {{ color: var(--cyan); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    /* 1. Clean Single-Row Executive Header */
    .exec-header {{
      background: rgba(9, 13, 22, 0.96);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 8px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      position: sticky;
      top: 0;
      z-index: 2500;
      min-height: 54px;
    }}
    .brand-cluster {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .brand-title {{
      font-weight: 800;
      font-size: 0.96rem;
      letter-spacing: -0.01em;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .brand-badge {{
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #fff;
      font-size: 0.68rem;
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
      background: rgba(30, 41, 59, 0.8);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 3px 8px;
      font-size: 0.72rem;
      color: var(--muted);
      white-space: nowrap;
    }}
    .kpi-chip strong {{
      color: #fff;
      font-weight: 700;
      margin-left: 3px;
    }}

    /* 5 Main Executive Product Areas (Mode Switcher) */
    .mode-switcher {{
      display: flex;
      background: #090e1a;
      border: 1px solid var(--border);
      border-radius: 9px;
      padding: 3px;
      gap: 3px;
      flex-wrap: wrap;
    }}
    .mode-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: #cbd5e1;
      padding: 6px 11px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
    }}
    .mode-btn:hover {{
      color: #fff;
      background: rgba(56, 189, 248, 0.08);
    }}
    .mode-btn.active {{
      background: linear-gradient(135deg, #0284c7, #1d4ed8);
      color: #fff;
      border-color: rgba(56, 189, 248, 0.45);
      box-shadow: 0 2px 8px rgba(2, 132, 199, 0.35);
    }}

    /* Compact Right Header Actions & Dropdown */
    .header-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
      position: relative;
    }}
    .emirate-pill-select {{
      background: #152036;
      border: 1px solid #3b82f6;
      color: #fff;
      padding: 5px 10px;
      border-radius: 7px;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
    }}
    .export-dropdown {{
      position: relative;
    }}
    .export-dropdown summary {{
      list-style: none;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border);
      color: #e2e8f0;
      padding: 5px 10px;
      border-radius: 7px;
      font-size: 0.74rem;
      font-weight: 600;
      cursor: pointer;
      user-select: none;
    }}
    .export-dropdown summary::-webkit-details-marker {{ display: none; }}
    .export-menu {{
      position: absolute;
      right: 0;
      top: calc(100% + 6px);
      width: 250px;
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 8px;
      box-shadow: 0 12px 28px rgba(0,0,0,0.6);
      display: flex;
      flex-direction: column;
      gap: 4px;
      z-index: 3000;
    }}
    .export-menu a {{
      padding: 6px 8px;
      border-radius: 6px;
      font-size: 0.75rem;
      color: #e2e8f0;
      display: flex;
      justify-content: space-between;
    }}
    .export-menu a:hover {{
      background: rgba(56, 189, 248, 0.14);
      color: var(--cyan);
      text-decoration: none;
    }}

    /* 2. Map-Centric Two-Column Executive Workbench with Multi-Stage Breakpoints */
    .workbench {{
      display: grid;
      grid-template-columns: 1fr 420px;
      height: calc(100vh - 55px);
      min-height: 620px;
      position: relative;
      border-bottom: 1px solid var(--border);
      transition: grid-template-columns 0.22s ease;
    }}
    .workbench.panel-collapsed {{
      grid-template-columns: 1fr 0px;
    }}
    @media (max-width: 1440px) {{
      .workbench {{ grid-template-columns: 1fr 375px; }}
      .kpi-strip {{ display: none; }}
    }}
    @media (max-width: 1024px) {{
      .workbench {{
        grid-template-columns: 1fr;
        grid-template-rows: 62vh 1fr;
        height: auto;
      }}
      .sidebar-right {{
        border-left: none !important;
        border-top: 1px solid var(--border);
      }}
    }}
    @media (max-width: 768px) {{
      .exec-header {{ padding: 8px 10px; }}
      .mode-switcher {{ width: 100%; overflow-x: auto; flex-wrap: nowrap; }}
      .workbench {{ grid-template-rows: 54vh 1fr; }}
    }}

    /* 3. Center Map Stage & Floating HUD Controls */
    .map-stage {{
      position: relative;
      display: flex;
      flex-direction: column;
      background: #060a12;
      overflow: hidden;
    }}
    #mapCanvas {{
      flex: 1;
      width: 100%;
      height: 100%;
      z-index: 1;
      background: #080d18;
      transition: transform 0.35s ease;
    }}
    #mapCanvas.tilt-3d {{
      transform: perspective(1400px) rotateX(22deg) scale(1.06);
      transform-origin: center 60%;
    }}
    .leaflet-tile.gis-dark-tiles {{
      filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
    }}

    /* Top Floating Bar: Guided 5-Step Storytelling Sequence + Basemap/Engine Switcher */
    .map-hud-top {{
      position: absolute;
      top: 10px;
      left: 50px;
      right: 12px;
      z-index: 900;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      pointer-events: none;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .story-bar {{
      pointer-events: auto;
      background: rgba(13, 20, 36, 0.92);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border);
      border-radius: 9px;
      padding: 4px 6px;
      display: flex;
      align-items: center;
      gap: 4px;
      flex-wrap: wrap;
      box-shadow: 0 4px 16px rgba(0,0,0,0.45);
    }}
    .story-lbl {{
      font-size: 0.68rem;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--cyan);
      padding: 0 6px;
      letter-spacing: 0.04em;
    }}
    .story-step {{
      background: rgba(30, 41, 59, 0.75);
      border: 1px solid transparent;
      color: #cbd5e1;
      padding: 4px 9px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .story-step:hover {{ color: #fff; border-color: #475569; }}
    .story-step.active {{
      background: #0284c7;
      color: #fff;
      border-color: #38bdf8;
    }}
    .story-arrow {{ color: #475569; font-size: 0.70rem; }}

    .hud-right-stack {{
      display: flex;
      gap: 6px;
      align-items: center;
      pointer-events: auto;
      flex-wrap: wrap;
    }}
    .basemap-switcher {{
      background: rgba(13, 20, 36, 0.92);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border);
      padding: 3px;
      border-radius: 8px;
      display: flex;
      gap: 3px;
    }}
    .bm-btn {{
      background: transparent;
      border: none;
      color: var(--muted);
      padding: 4px 8px;
      border-radius: 5px;
      font-size: 0.71rem;
      font-weight: 700;
      cursor: pointer;
    }}
    .bm-btn.active {{
      background: #0284c7;
      color: #fff;
    }}

    /* Prominent Epistemic Traffic Banner on Map */
    .epistemic-banner {{
      position: absolute;
      top: 52px;
      left: 50px;
      z-index: 890;
      pointer-events: auto;
      background: rgba(13, 20, 36, 0.90);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(245, 158, 11, 0.45);
      border-radius: 8px;
      padding: 4px 10px;
      font-size: 0.70rem;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}

    /* Bottom Floating Dock: Compact Layer Pills, Time Window Switcher & Collapsible Filter/Layer Popover */
    .map-hud-bottom {{
      position: absolute;
      bottom: 14px;
      left: 14px;
      right: 14px;
      z-index: 900;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      pointer-events: none;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .layer-pill-bar {{
      pointer-events: auto;
      background: rgba(13, 20, 36, 0.94);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border);
      border-radius: 9px;
      padding: 5px 8px;
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      box-shadow: 0 6px 20px rgba(0,0,0,0.5);
    }}
    .quick-layer-pill {{
      background: rgba(30, 41, 59, 0.8);
      border: 1px solid #334155;
      color: #94a3b8;
      padding: 4px 9px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}
    .quick-layer-pill.on {{
      background: rgba(2, 132, 199, 0.22);
      border-color: #38bdf8;
      color: #f8fafc;
    }}
    .time-group {{
      pointer-events: auto;
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
      align-items: center;
      background: rgba(13, 20, 36, 0.94);
      backdrop-filter: blur(10px);
      padding: 4px 6px;
      border-radius: 9px;
      border: 1px solid var(--border);
      box-shadow: 0 6px 20px rgba(0,0,0,0.5);
    }}
    .time-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--muted);
      padding: 4px 9px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 700;
      cursor: pointer;
    }}
    .time-btn.active {{
      background: #0f766e;
      color: #fff;
      border-color: #14b8a6;
    }}

    /* Compact Popover for All 11 Layers & Advanced Filters */
    .layers-drawer-popover {{
      position: absolute;
      bottom: 56px;
      left: 14px;
      width: 340px;
      max-height: 72vh;
      overflow-y: auto;
      background: rgba(13, 20, 36, 0.97);
      backdrop-filter: blur(14px);
      border: 1px solid #3b82f6;
      border-radius: 12px;
      padding: 12px;
      z-index: 1200;
      box-shadow: 0 14px 34px rgba(0,0,0,0.65);
      display: none;
    }}
    .layers-drawer-popover.open {{ display: block; }}

    /* Compact Map Legend Pill */
    .map-legend {{
      pointer-events: auto;
      background: rgba(13, 20, 36, 0.94);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border);
      border-radius: 9px;
      padding: 6px 10px;
      font-size: 0.70rem;
      max-width: 440px;
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
      font-size: 0.70rem;
      color: var(--muted);
      font-weight: 700;
      margin: 6px 0 2px;
      text-transform: uppercase;
    }}
    .ctrl-select, .ctrl-input {{
      width: 100%;
      background: #070b14;
      border: 1px solid #334155;
      color: #fff;
      padding: 6px 8px;
      border-radius: 6px;
      font-size: 0.76rem;
    }}
    .layer-list {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-top: 6px;
    }}
    .layer-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.73rem;
      padding: 4px 6px;
      border-radius: 6px;
      background: rgba(21, 32, 54, 0.75);
      border: 1px solid rgba(51, 65, 85, 0.5);
    }}
    .layer-item label {{
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      flex: 1;
    }}
    .prov-tag {{
      font-size: 0.62rem;
      padding: 1px 5px;
      border-radius: 4px;
      font-weight: 700;
    }}
    .prov-ver {{ background: rgba(16,185,129,0.18); color: #34d399; border: 1px solid rgba(16,185,129,0.35); }}
    .prov-mod {{ background: rgba(245,158,11,0.18); color: #fbbf24; border: 1px solid rgba(245,158,11,0.35); }}

    /* 4. Right Contextual Executive Panel + Progressive Disclosure Accordions */
    .sidebar-right {{
      background: var(--panel-dark);
      border-left: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    .drawer-tabs {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      background: #080d18;
      border-bottom: 1px solid var(--border);
    }}
    .dtab-btn {{
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--muted);
      padding: 9px 6px;
      font-size: 0.74rem;
      font-weight: 700;
      cursor: pointer;
    }}
    .dtab-btn.active {{
      color: var(--cyan);
      border-bottom-color: var(--cyan);
      background: rgba(56,189,248,0.08);
    }}
    .drawer-body {{
      padding: 12px;
      overflow-y: auto;
      flex: 1;
    }}
    .detail-card {{
      background: var(--panel-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      margin-bottom: 10px;
    }}
    .detail-card h4 {{
      margin: 0 0 6px 0;
      font-size: 0.94rem;
      color: #fff;
    }}

    /* Executive KPI Grid inside Cards */
    .exec-metric-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 7px;
      margin: 8px 0;
    }}
    .exec-metric-tile {{
      background: rgba(9, 14, 26, 0.75);
      border: 1px solid rgba(51, 65, 85, 0.7);
      border-radius: 8px;
      padding: 7px 9px;
    }}
    .exec-metric-tile .m-lbl {{
      font-size: 0.65rem;
      text-transform: uppercase;
      color: var(--muted);
      font-weight: 700;
    }}
    .exec-metric-tile .m-val {{
      font-size: 0.84rem;
      font-weight: 800;
      color: #fff;
      margin-top: 2px;
    }}

    /* Progressive Disclosure Technical Accordion (<details>) */
    details.tech-accordion {{
      background: rgba(9, 14, 26, 0.65);
      border: 1px solid rgba(51, 65, 85, 0.75);
      border-radius: 8px;
      margin-top: 8px;
      overflow: hidden;
    }}
    details.tech-accordion summary {{
      padding: 8px 10px;
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--cyan);
      cursor: pointer;
      user-select: none;
      background: rgba(15, 23, 42, 0.85);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    details.tech-accordion summary:hover {{
      background: rgba(30, 41, 59, 0.9);
    }}
    details.tech-accordion .acc-body {{
      padding: 9px 10px;
      font-size: 0.74rem;
      border-top: 1px solid rgba(51, 65, 85, 0.6);
      color: #cbd5e1;
    }}

    .kv-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 6px;
      font-size: 0.75rem;
      margin-top: 6px;
    }}
    .kv-row {{
      background: rgba(9, 14, 26, 0.65);
      border: 1px solid rgba(51, 65, 85, 0.65);
      padding: 6px 8px;
      border-radius: 6px;
    }}
    .kv-lbl {{
      font-size: 0.66rem;
      text-transform: uppercase;
      color: var(--muted);
      font-weight: 700;
    }}
    .kv-val {{
      color: #f1f5f9;
      margin-top: 2px;
      word-break: break-word;
    }}

    /* Epistemic Tier Badges */
    .ep-badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 0.69rem;
      font-weight: 700;
    }}
    .ep-t1 {{ background: rgba(56,189,248,0.18); color: #7dd3fc; border: 1px solid #0284c7; }}
    .ep-t2 {{ background: rgba(168,85,247,0.18); color: #d8b4fe; border: 1px solid #9333ea; }}
    .ep-t3 {{ background: rgba(245,158,11,0.18); color: #fcd34d; border: 1px solid #d97706; }}
    .ep-t4 {{ background: rgba(239,68,68,0.20); color: #fca5a5; border: 1px solid #dc2626; }}

    .conf-pill {{
      display: inline-block;
      padding: 2px 7px;
      border-radius: 999px;
      font-size: 0.68rem;
      font-weight: 700;
    }}
    .b-ver {{ background: rgba(16,185,129,0.2); color: #34d399; }}
    .b-cor {{ background: rgba(56,189,248,0.2); color: #38bdf8; }}
    .b-est {{ background: rgba(245,158,11,0.2); color: #fbbf24; }}

    /* Q&A Interface */
    .qa-box {{
      display: flex;
      gap: 6px;
      margin-bottom: 8px;
    }}
    .qa-preset-list {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-bottom: 10px;
    }}
    .qa-preset-btn {{
      text-align: left;
      background: rgba(15,23,42,0.85);
      border: 1px solid #334155;
      color: #cbd5e1;
      padding: 6px 8px;
      border-radius: 6px;
      font-size: 0.73rem;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .qa-preset-btn:hover {{
      border-color: var(--cyan);
      color: #fff;
      background: rgba(2,132,199,0.2);
    }}

    /* Bottom Expandable Evidence & Datasets Section */
    .evidence-section {{
      padding: 18px 20px 48px;
      max-width: 1600px;
      margin: 0 auto;
    }}
    .ev-tabs {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 12px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
    }}
    .ev-tab-btn {{
      background: #152036;
      border: 1px solid #334155;
      color: #cbd5e1;
      padding: 6px 11px;
      border-radius: 7px;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
    }}
    .ev-tab-btn.active {{
      background: #0284c7;
      color: #fff;
      border-color: #38bdf8;
    }}
    .ev-panel {{ display: none; }}
    .ev-panel.active {{ display: block; }}

    .t2-table-wrap {{
      overflow-x: auto;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: var(--panel-dark);
      margin-top: 8px;
      max-height: 520px;
    }}
    .t2-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.75rem;
    }}
    .t2-table th, .t2-table td {{
      padding: 7px 9px;
      border-bottom: 1px solid #1e293b;
      text-align: left;
      vertical-align: top;
    }}
    .t2-table th {{
      background: #080d18;
      color: var(--cyan);
      font-weight: 700;
      position: sticky;
      top: 0;
    }}
    .t2-table tr:hover td {{
      background: rgba(56,189,248,0.05);
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
      background: #152036;
      border: 1px solid #475569;
      color: #38bdf8;
      padding: 3px 9px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.72rem;
    }}
  </style>
</head>
<body>

  <!-- 1. EXECUTIVE SINGLE-ROW HEADER WITH 5 MAIN PRODUCT MODES -->
  <header class="exec-header">
    <div class="brand-cluster">
      <div class="brand-title">
        <span class="brand-badge">UAE Intelligence</span>
        <span>Construction &amp; Traffic Platform</span>
      </div>
      <div class="kpi-strip">
        <span class="kpi-chip">Scope <strong id="hudScope">Dubai</strong></span>
        <span class="kpi-chip">Active Sites <strong id="hudProjects">25</strong></span>
        <span class="kpi-chip">Corridors <strong id="hudRoads">23</strong></span>
        <span class="kpi-chip">Communities <strong id="hudComms">10</strong></span>
      </div>
    </div>

    <!-- 5 MAIN AREAS (SECTION 4 REDESIGN) -->
    <nav class="mode-switcher" aria-label="Primary Platform Modes">
      <button class="mode-btn active" id="mode-overview" onclick="setPlatformMode('overview', this)">1. Overview</button>
      <button class="mode-btn" id="mode-construction" onclick="setPlatformMode('construction', this)">2. Construction Map</button>
      <button class="mode-btn" id="mode-traffic" onclick="setPlatformMode('traffic', this)">3. Traffic Intelligence</button>
      <button class="mode-btn" id="mode-project" onclick="setPlatformMode('project', this)">4. Project Explorer</button>
      <button class="mode-btn" id="mode-evidence" onclick="setPlatformMode('evidence', this)">5. Evidence &amp; Methodology</button>
    </nav>

    <div class="header-actions">
      <select id="emirateSelect" class="emirate-pill-select" onchange="onEmirateChange()" aria-label="Select Emirate">
        <option value="Dubai" selected>Dubai (25 Sites)</option>
        <option value="Sharjah">Sharjah (12 Sites)</option>
        <option value="ALL">Dubai + Sharjah (37 Sites)</option>
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

  <!-- 2. TWO-COLUMN MAP-CENTRIC WORKBENCH -->
  <main class="workbench" id="mainWorkbench">

    <!-- FULL-BLEED INTERACTIVE MAP STAGE -->
    <section class="map-stage">
      <!-- Top Floating Guided Storytelling Bar & Basemap Switcher -->
      <div class="map-hud-top">
        <div class="story-bar" role="region" aria-label="Guided Visual Storytelling Sequence">
          <span class="story-lbl">Story Tour:</span>
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

        <div class="hud-right-stack">
          <div class="basemap-switcher">
            <button class="bm-btn active" onclick="setBasemap('dark', this)">Dark GIS</button>
            <button class="bm-btn" onclick="setBasemap('light', this)">Street</button>
            <button class="bm-btn" onclick="setBasemap('sat', this)">Satellite</button>
            <button class="bm-btn" id="btn3dTilt" onclick="toggle3DPerspective(this)" title="Toggle WebGL / 3D Perspective Pitch">3D Pitch</button>
          </div>
          <button class="bm-btn" style="background:rgba(13,20,36,0.92);border:1px solid var(--border);color:#e2e8f0;padding:5px 9px;border-radius:7px;" onclick="toggleRightPanel()" title="Expand / Collapse Side Panel">⇤ Panel</button>
        </div>
      </div>

      <!-- Prominent Epistemic Differentiation Banner (Fixes 3.E & 5.5) -->
      <div class="epistemic-banner">
        <span class="conf-pill b-ver">PUBLISHED: RTA/SRTA Capacities &amp; TomTom City Index (31.3 km/h)</span>
        <span class="conf-pill b-est">MODELLED ESTIMATES: Segment Speeds (BPR + Delay) &amp; Daily HGV Loads (Not Live Telemetry)</span>
        <span style="color:#cbd5e1;">Window: <strong id="hudTime" style="color:#fff;">Evening Peak (17:00–20:00)</strong></span>
      </div>

      <!-- Primary Map Canvas -->
      <div id="mapCanvas"></div>

      <!-- Hidden/Collapsible Advanced Layers & Filters Popover (All 11 Layers Preserved without Clutter) -->
      <div class="layers-drawer-popover" id="layersPopover">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <strong style="font-size:0.80rem; color:var(--cyan);">Map Layers (11) &amp; Filters</strong>
          <div style="display:flex; gap:6px;">
            <button onclick="resetAllFilters()" style="background:#334155;border:none;color:#fff;font-size:0.68rem;padding:2px 7px;border-radius:4px;cursor:pointer;">Reset</button>
            <button onclick="toggleLayersPopover()" style="background:transparent;border:none;color:#94a3b8;font-size:0.85rem;cursor:pointer;">✕</button>
          </div>
        </div>

        <input type="text" id="searchInput" class="ctrl-input" placeholder="Search project, road, community (e.g. JVC, Hessa)..." oninput="applyMapFilters()"/>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:4px;">
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

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:4px;">
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
            <label><input type="checkbox" id="chk-L1" checked onchange="toggleLayerGroup('projects', this.checked)"/><span class="layer-dot" style="background:#38bdf8;"></span> 1. Construction Projects (Scaled)</label>
            <span class="prov-tag prov-ver">Default ON</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L3" checked onchange="toggleLayerGroup('communities', this.checked)"/><span class="layer-dot" style="background:#c084fc;"></span> 2. Community Hotspots (10)</label>
            <span class="prov-tag prov-ver">Default ON</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L6" checked onchange="toggleLayerGroup('traffic', this.checked)"/><span class="layer-dot" style="background:#ef4444;"></span> 3. Modelled Corridor Speeds</label>
            <span class="prov-tag prov-mod">Modelled</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L4" checked onchange="toggleLayerGroup('roads', this.checked)"/><span class="layer-dot" style="background:#94a3b8;"></span> 4. Base Road Network (23)</label>
            <span class="prov-tag prov-ver">RTA Cap</span>
          </div>
          <div class="layer-item">
            <label><input type="checkbox" id="chk-L2" onchange="toggleLayerGroup('devbounds', this.checked)"/><span class="layer-dot" style="background:#818cf8;"></span> 5. JVC Sub-Clusters &amp; Radii</label>
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

      <!-- Bottom Floating Bar: Compact Quick Layer Pills, Time Window Selector & Compact Legend -->
      <div class="map-hud-bottom">
        <div class="layer-pill-bar">
          <button class="quick-layer-pill on" id="qpill-projects" onclick="quickToggle('projects', 'chk-L1', this)"><span class="layer-dot" style="background:#38bdf8;"></span> Projects</button>
          <button class="quick-layer-pill on" id="qpill-communities" onclick="quickToggle('communities', 'chk-L3', this)"><span class="layer-dot" style="background:#c084fc;"></span> Communities</button>
          <button class="quick-layer-pill on" id="qpill-traffic" onclick="quickToggle('traffic', 'chk-L6', this)"><span class="layer-dot" style="background:#ef4444;"></span> Modelled Traffic</button>
          <button class="quick-layer-pill" id="qpill-impacts" onclick="quickToggle('impacts', 'chk-L11', this)"><span class="layer-dot" style="background:#f59e0b;"></span> Impact Links</button>
          <button class="quick-layer-pill" style="color:var(--cyan); border-color:#0284c7;" onclick="toggleLayersPopover()">⚙ Filters &amp; All 11 Layers</button>
        </div>

        <div class="time-group" aria-label="Traffic Time Window Selector">
          <button class="time-btn" data-tp="Morning Peak (07:30–09:30)" onclick="setTimeWindow('Morning Peak (07:30–09:30)', this)">🌅 AM Peak</button>
          <button class="time-btn" data-tp="Midday (12:00–14:00)" onclick="setTimeWindow('Midday (12:00–14:00)', this)">🚛 Midday HGV</button>
          <button class="time-btn active" data-tp="Evening Peak (17:00–20:00)" onclick="setTimeWindow('Evening Peak (17:00–20:00)', this)">🌇 PM Peak</button>
          <button class="time-btn" data-tp="Night (22:00–05:00)" onclick="setTimeWindow('Night (22:00–05:00)', this)">🌙 Night</button>
        </div>

        <div class="map-legend">
          <div class="legend-inline">
            <span class="leg-row"><span class="layer-dot" style="width:12px;height:12px;background:#0ea5e9;border:2px solid #fff;"></span> Mega ≥AED 25B</span>
            <span class="leg-row"><span class="layer-dot" style="width:9px;height:9px;background:#38bdf8;"></span> Major 5–25B</span>
            <span class="leg-row"><span class="layer-dot" style="width:6px;height:6px;background:#93c5fd;"></span> Tower &lt;5B</span>
            <span class="leg-row"><span class="leg-line" style="background:#ef4444;"></span> Severe</span>
            <span class="leg-row"><span class="leg-line" style="background:#f97316;"></span> High</span>
            <span class="leg-row"><span class="leg-line" style="background:#eab308;"></span> Mod</span>
            <span class="leg-row"><span class="leg-line" style="background:#10b981;"></span> Low</span>
          </div>
        </div>
      </div>
    </section>

    <!-- RIGHT CONTEXTUAL EXECUTIVE PANEL (ADAPTS TO 5 MODES + PROGRESSIVE DISCLOSURE) -->
    <aside class="sidebar-right">
      <div class="drawer-tabs">
        <button class="dtab-btn active" id="dtab-uc" onclick="switchDrawerTab('uc')">📌 Overview &amp; Scenarios</button>
        <button class="dtab-btn" id="dtab-insp" onclick="switchDrawerTab('insp')">🔍 Project / Road Explorer</button>
        <button class="dtab-btn" id="dtab-qa" onclick="switchDrawerTab('qa')">💬 Evidence &amp; Q&amp;A</button>
      </div>

      <!-- TAB 1: OVERVIEW, HOTSPOTS & GUIDED SCENARIOS -->
      <div class="drawer-body" id="dpanel-uc">
        <div style="display:flex; gap:5px; flex-wrap:wrap; margin-bottom:10px;">
          <button class="story-step active" id="btn-uc1" onclick="runUseCase(1)">1. Dubai Hotspots</button>
          <button class="story-step" id="btn-uc2" onclick="runUseCase(2)">2. JVC Traffic</button>
          <button class="story-step" id="btn-uc3" onclick="runUseCase(3)">3. AM vs PM &amp; 2024–26</button>
          <button class="story-step" id="btn-uc4" onclick="runUseCase(4)">4. Sharjah</button>
        </div>
        <div id="useCaseContainer"></div>
      </div>

      <!-- TAB 2: EXECUTIVE PROJECT / ROAD EXPLORER (WITH PROGRESSIVE DISCLOSURE <details>) -->
      <div class="drawer-body" id="dpanel-insp" style="display:none;">
        <div id="inspectorContainer">
          <div class="detail-card">
            <h4>Select Any Project Marker or Road Corridor</h4>
            <p style="font-size:0.77rem; color:var(--muted);">Click a scaled project marker or road corridor on the map to view its executive summary card. Detailed engineering derivations (BPR formulas, 4-component HGV math, WGS84 vertex distances, and source registers) open cleanly inside expandable sections.</p>
          </div>
        </div>
      </div>

      <!-- TAB 3: EVIDENCE, METHODOLOGY & DETERMINISTIC Q&A -->
      <div class="drawer-body" id="dpanel-qa" style="display:none;">
        <div class="detail-card">
          <h4>Deterministic Database Q&amp;A &amp; Methodology</h4>
          <p style="font-size:0.73rem; color:var(--muted); margin:0 0 8px;">Ask a question or select a preset to query the normalized Task 1 + Task 2 tables and fly the map to the matched sites.</p>
          <div class="qa-box">
            <input type="text" id="qaInput" class="ctrl-input" placeholder="Ask about JVC, Hessa St, Dubai South, TIS, Morning vs Evening..." onkeydown="if(event.key==='Enter') runDeterministicQA()"/>
            <button onclick="runDeterministicQA()" style="background:#0284c7;border:none;color:#fff;padding:0 12px;border-radius:6px;font-weight:700;cursor:pointer;">Ask</button>
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

    function initMap() {
      map = L.map("mapCanvas", {
        center: [25.115, 55.245],
        zoom: 11,
        zoomControl: true
      });

      setBasemap("dark", document.querySelector(".bm-btn.active"));

      // Enable only the 4 core executive layers by default (Clean Initial View)
      ["communities", "roads", "traffic", "projects"].forEach(k => {
        layerGroups[k].addTo(map);
      });

      populateCommunityDropdown();
      renderAllMapLayers();
      runUseCase(1);
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
        runUseCase(1);
      } else if (mode === "construction") {
        switchDrawerTab("uc");
        setLayerSet(["communities", "devbounds", "projects", "roads"]);
        runUseCase(1);
      } else if (mode === "traffic") {
        switchDrawerTab("uc");
        setLayerSet(["roads", "traffic", "intersections", "impacts", "projects"]);
        runUseCase(3);
      } else if (mode === "project") {
        switchDrawerTab("insp");
        setLayerSet(["communities", "roads", "traffic", "impacts", "projects", "devbounds"]);
        showProjectInspector("PRJ-D6");
      } else if (mode === "evidence") {
        const det = document.getElementById("evidenceAccordion");
        if (det) det.open = true;
        document.getElementById("evidenceSection").scrollIntoView({ behavior: "smooth" });
      }
    }

    function setLayerSet(activeKeys) {
      const keyToChk = {
        projects: "lyr_projects", devbounds: "lyr_devbounds", communities: "lyr_communities",
        roads: "lyr_roads", intersections: "lyr_intersections", traffic: "lyr_traffic",
        incidents: "lyr_incidents", transit: "lyr_transit", facilities: "lyr_facilities",
        parking: "lyr_parking", impacts: "lyr_impacts"
      };
      const keyToQ = {
        projects: "qpill-projects", communities: "qpill-communities",
        traffic: "qpill-traffic", impacts: "qpill-impacts",
        intersections: "qpill-intersections", transit: "qpill-transit"
      };
      Object.keys(layerGroups).forEach(k => {
        const on = activeKeys.includes(k);
        toggleLayerGroup(k, on);
        const chk = document.getElementById(keyToChk[k]);
        if (chk) chk.checked = on;
        const qp = document.getElementById(keyToQ[k]);
        if (qp) qp.classList.toggle("active", on);
      });
    }

    function quickToggle(key, chkId, btnEl) {
      const chk = document.getElementById(chkId);
      const nextState = chk ? !chk.checked : !map.hasLayer(layerGroups[key]);
      if (chk) chk.checked = nextState;
      if (btnEl) btnEl.classList.toggle("active", nextState);
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
      setTimeout(() => { if (map) map.invalidateSize(); }, 260);
    }

    function toggle3DPerspective(btnEl) {
      is3DPerspective = !is3DPerspective;
      const mc = document.getElementById("mapCanvas");
      if (btnEl) btnEl.classList.toggle("active", is3DPerspective);
      if (is3DPerspective) {
        mc.style.transform = "perspective(1400px) rotateX(24deg) scale(1.06)";
        mc.style.transformOrigin = "center 65%";
        mc.style.transition = "transform 0.45s cubic-bezier(0.22, 1, 0.36, 1)";
      } else {
        mc.style.transform = "none";
      }
    }

    function runStoryStep(step) {
      document.querySelectorAll(".story-step").forEach((el, idx) => {
        el.classList.toggle("active", (idx + 1) === step);
      });
      if (step === 1) {
        document.getElementById("emirateSelect").value = "ALL";
        populateCommunityDropdown();
        setLayerSet(["communities", "roads", "traffic", "projects"]);
        map.flyTo([25.195, 55.355], 10, { duration: 0.9 });
        document.getElementById("hudScope").textContent = "Step 1: UAE Overview (Dubai + Sharjah)";
        runUseCase(1);
      } else if (step === 2) {
        document.getElementById("emirateSelect").value = "Dubai";
        populateCommunityDropdown();
        setLayerSet(["communities", "roads", "traffic", "projects"]);
        map.flyTo([25.115, 55.245], 11, { duration: 0.9 });
        document.getElementById("hudScope").textContent = "Step 2: Dubai Core Corridors";
        runUseCase(1);
      } else if (step === 3) {
        document.getElementById("emirateSelect").value = "Dubai";
        populateCommunityDropdown();
        setLayerSet(["communities", "devbounds", "roads", "traffic", "impacts", "projects"]);
        map.flyTo([25.0585, 55.2090], 13, { duration: 0.9 });
        document.getElementById("hudScope").textContent = "Step 3: JVC High-Density Hotspot";
        runUseCase(2);
      } else if (step === 4) {
        setLayerSet(["communities", "devbounds", "roads", "traffic", "impacts", "projects"]);
        map.flyTo([25.0552, 55.2078], 14, { duration: 0.9 });
        document.getElementById("hudScope").textContent = "Step 4: Project Inspection (PRJ-D6)";
        showProjectInspector("PRJ-D6");
      } else if (step === 5) {
        setLayerSet(["roads", "traffic", "intersections", "impacts", "projects"]);
        map.flyTo([25.0695, 55.1950], 13, { duration: 0.9 });
        document.getElementById("hudScope").textContent = "Step 5: Hessa St (D61) Impact Analysis";
        showRoadInspector("RD-DXB-04");
      }
    }

    function setBasemap(mode, btnEl) {
      if (btnEl) {
        document.querySelectorAll(".bm-btn").forEach(b => b.classList.remove("active"));
        btnEl.classList.add("active");
      }
      if (baseTileLayer) map.removeLayer(baseTileLayer);
      if (mode === "sat") {
        baseTileLayer = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
          maxZoom: 19,
          attribution: "Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics"
        });
      } else if (mode === "light") {
        baseTileLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 19,
          attribution: "&copy; OpenStreetMap contributors (ODbL — No API Key Required)"
        });
      } else {
        baseTileLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 19,
          className: "gis-dark-tiles",
          attribution: "&copy; OpenStreetMap contributors (ODbL Dark GIS — No API Key Required)"
        });
      }
      baseTileLayer.addTo(map);
      baseTileLayer.bringToBack();
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
        map.flyTo([25.115, 55.245], 11, { duration: 0.8 });
        document.getElementById("hudScope").textContent = "Dubai (Priority 1)";
      } else if (em === "Sharjah") {
        map.flyTo([25.315, 55.505], 12, { duration: 0.8 });
        document.getElementById("hudScope").textContent = "Sharjah (Priority 2)";
      } else {
        map.flyTo([25.185, 55.345], 10, { duration: 0.8 });
        document.getElementById("hudScope").textContent = "Dubai + Sharjah";
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
        map.flyTo([c.center_lat, c.center_lon], c.recommended_zoom || 13, { duration: 0.9 });
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
    }

    function setTimeWindow(tp, btnEl) {
      currentTimeWindow = tp;
      document.getElementById("hudTime").textContent = tp;
      if (btnEl) {
        document.querySelectorAll(".time-btn").forEach(b => b.classList.remove("active"));
        btnEl.classList.add("active");
      }
      renderAllMapLayers();
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
      map.flyTo([25.115, 55.245], 11, { duration: 0.8 });
      renderAllMapLayers();
    }

    function getRoadObsForWindow(roadId, tp) {
      const roadObs = DATA.observations.filter(o => o.road_id === roadId);
      const exact = roadObs.find(o => o.time_period === tp);
      if (exact) return { obs: exact, exactMatch: true };
      if (roadObs.length > 0) return { obs: roadObs[0], exactMatch: false };
      return { obs: null, exactMatch: false };
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
          weight: 1.5,
          dashArray: "5,4",
          fillColor: col,
          fillOpacity: 0.08
        });
        poly.bindTooltip(`<strong>${c.community_name}</strong><br/>Active Devs: ${c.active_developments_count} | Active Towers: ${c.active_towers_and_buildings}<br/>Hotspot Score: ${c.construction_activity_index_score}`, { sticky: true });
        poly.on("click", () => showCommunityInspector(c));
        poly.addTo(layerGroups.communities);
      });

      // 2. Layer 4 & Layer 6: Road Network & Dynamic Traffic Speed/Congestion Overlay (Crisp Cartographic Weights)
      DATA.roads.forEach(r => {
        if (emFilter !== "ALL" && r.emirate !== emFilter) return;
        const { obs, exactMatch } = getRoadObsForWindow(r.road_id, currentTimeWindow);
        const congLvl = exactMatch && obs ? obs.congestion_level : "Unavailable for Selected Window (Not Zero Congestion)";

        if (congFilter !== "ALL") {
          if (congFilter === "High" && !(congLvl.includes("High") || congLvl.includes("Severe"))) return;
          if (congFilter !== "High" && !congLvl.includes(congFilter)) return;
        }
        if (q && !JSON.stringify(r).toLowerCase().includes(q) && !(obs && JSON.stringify(obs).toLowerCase().includes(q))) return;

        const latlngs = r.geometry_wgs84.map(pt => [pt[1], pt[0]]);

        // Base casing line (Layer 4 — Reduced weight for visual clarity)
        const baseLine = L.polyline(latlngs, {
          color: "#1e293b",
          weight: r.road_type.includes("Freeway") || r.road_type.includes("Express") ? 3.5 : 2.5,
          opacity: 0.75
        });
        baseLine.on("click", () => showRoadInspector(r.road_id));
        baseLine.addTo(layerGroups.roads);

        // Traffic color overlay line (Layer 6 — Clean 2.5px / 2.0px stroke)
        const tCol = congestionColor(congLvl);
        const speedTxt = exactMatch && obs ? `${obs.average_speed_kmh} km/h (${obs.travel_time_min_per_10km} min/10km)` : `Data Unavailable for ${currentTimeWindow}`;
        const matchNote = exactMatch && obs
          ? `[MODELLED CORRIDOR ESTIMATE — BPR + Bottleneck Delay] Source: ${obs.source_id}`
          : `[Window Not Modelled — Click to inspect recorded peak periods]`;
        const trafLine = L.polyline(latlngs, {
          color: tCol,
          weight: r.road_type.includes("Freeway") || r.road_type.includes("Express") ? 2.5 : 2.0,
          dashArray: exactMatch ? null : "5,5",
          opacity: 0.92
        });
        trafLine.bindTooltip(
          `<strong>${r.road_name}</strong><br/>` +
          `Window: <strong>${currentTimeWindow}</strong> → <strong>${speedTxt}</strong><br/>` +
          `Status: <strong>${congLvl}</strong><br/>` +
          `Published Capacity: ${r.capacity_vph_per_dir}<br/>` +
          `<em>${matchNote}</em>`,
          { sticky: true }
        );
        trafLine.on("click", () => showRoadInspector(r.road_id));
        trafLine.addTo(layerGroups.traffic);
      });

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
    }

    function switchDrawerTab(tab) {
      ["uc", "insp", "qa"].forEach(k => {
        document.getElementById(`dtab-${k}`).classList.toggle("active", k === tab);
        document.getElementById(`dpanel-${k}`).style.display = (k === tab) ? "block" : "none";
      });
    }

    // =========================================================================
    // SECTION C3: PROJECT-LEVEL DETAIL PANEL (Executive Summary + Progressive Disclosure)
    // =========================================================================
    function showProjectInspector(pid) {
      switchDrawerTab("insp");
      const p = DATA.projects.find(x => x.project_id === pid);
      if (!p) return;
      const link = DATA.impact_links.find(x => x.project_id === pid);
      const docs = DATA.documents.filter(d => d.project_id === pid);
      const [lat, lon] = parseCoord(p.coordinates);
      map.flyTo([lat, lon], 14, { duration: 0.7 });

      const docsHtml = docs.map(d =>
        `<div style="margin-bottom:4px;">• <a href="${d.document_url}" target="_blank" rel="noopener">${d.document_title} ↗</a> <span style="color:var(--muted);">(${d.document_type} | ${d.availability_status})</span></div>`
      ).join("") || "Linked in Task 1 Document Archive";

      document.getElementById("inspectorContainer").innerHTML = `
        <div class="detail-card">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px; flex-wrap:wrap; margin-bottom:6px;">
            <span class="brand-badge">${p.project_id} • ${p.emirate}</span>
            <span class="conf-pill b-ver">${p.confidence_classification}</span>
          </div>
          <h4>${p.project_name}</h4>
          <div style="font-size:0.78rem; color:var(--cyan); font-weight:700; margin-bottom:10px;">${p.developer} • ${p.city_district_community}</div>

          <!-- Executive KPI Summary Grid -->
          <div class="exec-metric-grid">
            <div class="exec-metric-box">
              <div class="em-lbl">Lifecycle Status</div>
              <div class="em-val">${p.lifecycle_status}</div>
              <div class="em-sub">${p.project_category}</div>
            </div>
            <div class="exec-metric-box">
              <div class="em-lbl">Published Value</div>
              <div class="em-val" style="color:#38bdf8;">${p.published_investment_value}</div>
              <div class="em-sub">Plot: ${p.land_plot_area}</div>
            </div>
            <div class="exec-metric-box">
              <div class="em-lbl">Primary Corridor</div>
              <div class="em-val" style="font-size:0.78rem;">${link ? `<a href="javascript:void(0)" onclick="showRoadInspector('${link.primary_road_id}')">${link.primary_road_name}</a>` : "Arterial Grid"}</div>
              <div class="em-sub">${link ? `${link.distance_to_primary_road_km} km to nearest vertex` : ""}</div>
            </div>
            <div class="exec-metric-box">
              <div class="em-lbl">Scenario HGV Load</div>
              <div class="em-val" style="color:#fbbf24;">${link ? `${link.total_hgv_round_trips_day} trips/day` : "N/A"}</div>
              <div class="em-sub">${link ? `${link.total_hgv_one_way_movements_day} one-way/day (Est.)` : ""}</div>
            </div>
          </div>

          ${link ? `<div style="margin-bottom:8px;"><span class="ep-badge ${link.epistemic_impact_classification.includes('Tier 4') ? 'ep-t4' : (link.epistemic_impact_classification.includes('Tier 2') ? 'ep-t2' : 'ep-t3')}">${link.epistemic_impact_classification}</span></div>` : ""}

          <div class="kv-grid">
            <div class="kv-row"><div class="kv-lbl">Scale &amp; Timeline</div><div class="kv-val"><strong>GFA:</strong> ${p.gross_floor_area} | <strong>Buildings:</strong> ${p.towers_and_buildings_count} (${p.floors_and_height}) | <strong>Units:</strong> ${p.apartments_and_villas_count}<br/><span style="color:var(--muted);">${p.timeline_milestones}</span></div></div>
            <div class="kv-row"><div class="kv-lbl">Corridor Capacity vs. Modelled Traffic</div><div class="kv-val">${link ? `<span class="ep-pill-pub">PUBLISHED BENCHMARK</span> <span style="color:#34d399;">${link.published_road_capacity_and_upgrade_fact}</span><br/><span class="ep-pill-mod" style="margin-top:4px; display:inline-block;">MODELLED CORRIDOR ESTIMATE</span> ${link.observed_road_traffic_condition}` : ""}</div></div>
          </div>

          <details class="tech-accordion">
            <summary>Technical Details: Geometry Math, 4-Component HGV Model &amp; Provenance (${docs.length} Docs)</summary>
            <div class="tech-body">
              <div style="margin-bottom:6px;"><strong>1. Nearest-Vertex Geometry Validation:</strong> ${link ? `Project Centroid <code>${link.project_coordinates}</code> → Nearest Road Vertex <code>${link.nearest_road_vertex_wgs84}</code> (<strong>${link.distance_to_primary_road_km} km</strong> via ${link.geometry_validation_method}). Nearest Junction: ${link.nearest_intersection_name} (${link.distance_to_intersection_km} km).` : p.coordinates}</div>
              ${link ? `<div style="margin-bottom:6px;"><strong>2. Scenario-Based 4-Component HGV Breakdown:</strong> <strong>${link.total_hgv_round_trips_day} round-trips/day (${link.total_hgv_one_way_movements_day} one-way/day)</strong> = ${link.concrete_mixer_loads_day} concrete mixers + ${link.rebar_trailer_loads_day} rebar trailers + ${link.earthworks_tipper_loads_day} earthworks tippers + ${link.mep_fitout_truck_loads_day} MEP/fit-out trucks.<br/><span style="color:#fcd34d;">Assumptions: ${link.hgv_modelling_assumptions_and_sensitivity}</span><br/><strong>HGV Ban Compliance:</strong> ${link.hgv_routing_and_ban_compliance}</div>` : ""}
              <div style="margin-bottom:6px;"><strong>3. Contractors &amp; Consultants:</strong> ${p.main_contractor_and_consultants}</div>
              <div style="margin-bottom:6px;"><strong>4. Supporting Documents (${docs.length}):</strong> ${docsHtml}</div>
              <div><strong>5. Dual Provenance Trail:</strong> Project (${link ? link.project_source_id : p.project_id}): <a href="${p.source_url}" target="_blank" rel="noopener">${p.publisher} ↗</a> | Corridor (${link ? link.corridor_traffic_source_id : ""}): ${link ? `<a href="${link.corridor_source_url}" target="_blank" rel="noopener">${link.corridor_source_title} ↗</a>` : ""}</div>
            </div>
          </details>
        </div>
      `;
    }

    function showSubdevInspector(sd) {
      switchDrawerTab("insp");
      map.flyTo([sd.latitude, sd.longitude], 15, { duration: 0.7 });
      document.getElementById("inspectorContainer").innerHTML = `
        <div class="detail-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span class="brand-badge" style="background:#7e22ce;">${sd.subdev_id} • JVC Sub-Cluster</span>
            <span class="conf-pill b-est">${sd.confidence}</span>
          </div>
          <h4>${sd.development_name}</h4>
          <div style="font-size:0.78rem; color:var(--cyan); font-weight:700; margin-bottom:10px;">${sd.developer} • ${sd.community_district}</div>
          <div class="exec-metric-grid">
            <div class="exec-metric-box"><div class="em-lbl">Active Towers</div><div class="em-val">${sd.building_count} Towers</div><div class="em-sub">${sd.floors_range}</div></div>
            <div class="exec-metric-box"><div class="em-lbl">Total Units</div><div class="em-val" style="color:#38bdf8;">${sd.total_units.toLocaleString()}</div><div class="em-sub">${sd.active_gfa_sqm.toLocaleString()} m² GFA</div></div>
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
              <div><strong>Scenario HGV Movements:</strong> ${sd.estimated_midday_hgv_trips_per_day}<br/><span style="color:#fcd34d;">${sd.hgv_modelling_assumptions_and_sensitivity}</span></div>
            </div>
          </details>
        </div>
      `;
    }

    // =========================================================================
    // SECTION C4: ROAD-LEVEL DETAIL PANEL (Executive Summary + Progressive Disclosure)
    // =========================================================================
    function showRoadInspector(roadId) {
      switchDrawerTab("insp");
      const r = DATA.roads.find(x => x.road_id === roadId);
      if (!r) return;
      const roadObs = DATA.observations.filter(o => o.road_id === roadId);
      const cityObs = DATA.observations.find(o => o.observation_id === "OBS-DXB-CITY-00");
      const connectedLinks = DATA.impact_links.filter(l => l.primary_road_id === roadId || l.secondary_road_id === roadId);
      const midPt = r.geometry_wgs84[Math.floor(r.geometry_wgs84.length / 2)];
      map.flyTo([midPt[1], midPt[0]], 13, { duration: 0.7 });

      const obsHtml = roadObs.map(o => {
        const srcHtml = o.source_url
          ? `<a href="${o.source_url}" target="_blank" rel="noopener">${o.source_id}: ${o.source_report_title || 'Official Source'} (${o.publication_date || ''}) ↗</a>`
          : o.source_id;
        return `
        <div style="background:#090d16; border:1px solid #334155; padding:8px; border-radius:7px; margin-bottom:7px;">
          <div style="display:flex; justify-content:space-between; align-items:center; font-weight:700; color:#fff;">
            <span>${o.time_period}</span>
            <span style="color:${congestionColor(o.congestion_level)};">Modelled ~${o.average_speed_kmh} km/h (${o.travel_time_min_per_10km} min/10km)</span>
          </div>
          <div style="font-size:0.72rem; color:#34d399; margin-top:4px;"><span class="ep-pill-pub">PUBLISHED</span> ${o.officially_published_corridor_benchmark}</div>
          <div style="font-size:0.72rem; color:#cbd5e1; margin-top:4px;"><span class="ep-pill-mod">MODELLED</span> <strong>${o.congestion_level}</strong> | Volume: ${o.traffic_volume_vph}</div>
          <details class="tech-accordion" style="margin-top:6px;">
            <summary>BPR Equation Breakdown &amp; Source (${o.observation_id})</summary>
            <div class="tech-body">
              <div><strong>Two-Term BPR + Bottleneck Formula:</strong> v₀=${o.free_flow_speed_kmh} km/h (t₀=${o.free_flow_time_min_per_10km} min/10km) | V/C=${o.vc_ratio} (${o.modelled_demand_vph_dir}/${o.reference_capacity_vph_dir} vph/dir) → <strong>Uninterrupted BPR Link: ${o.bpr_uninterrupted_speed_kmh} km/h (${o.bpr_uninterrupted_time_min_per_10km} min/10km)</strong> + <strong>Bottleneck Assumption (+d_adj): +${o.bottleneck_and_control_delay_min_per_10km} min/10km</strong> = <strong>${o.travel_time_min_per_10km} min/10km → ${o.average_speed_kmh} km/h</strong></div>
              <div style="margin-top:4px;"><strong>Derivation:</strong> ${o.modelled_assumptions_and_derivation}</div>
              <div style="margin-top:4px;"><strong>2024 vs 2026 Comparison:</strong> ${o.comparison_period}</div>
              <div style="margin-top:4px;"><strong>Source:</strong> ${srcHtml}</div>
            </div>
          </details>
        </div>`;
      }).join("") || "<div style='color:#94a3b8; background:#090d16; border:1px dashed #64748b; padding:8px; border-radius:6px;'><strong>Data Unavailable (Distinguished from Zero Congestion):</strong> Segment-specific loop-detector speed breakdown is not published separately in open government CSVs for this corridor. Published statutory speed limit is " + r.speed_limit_kmh + ".</div>";

      const projHtml = connectedLinks.map(l =>
        `<div>• <a href="javascript:void(0)" onclick="showProjectInspector('${l.project_id}')"><strong>${l.project_id}</strong>: ${l.project_name}</a> (${l.distance_to_primary_road_km} km — ${l.epistemic_impact_classification.split('(')[0]})</div>`
      ).join("") || "Serves general corridor traffic";

      document.getElementById("inspectorContainer").innerHTML = `
        <div class="detail-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span class="brand-badge">${r.road_id} • ${r.road_code}</span>
            <span class="conf-pill ${r.confidence === 'Verified' ? 'b-ver' : 'b-est'}">${r.confidence}</span>
          </div>
          <h4>${r.road_name}</h4>
          <div style="font-size:0.78rem; color:var(--cyan); font-weight:700; margin-bottom:10px;">${r.authority} • ${r.road_type}</div>

          <div class="exec-metric-grid">
            <div class="exec-metric-box">
              <div class="em-lbl">Speed Limit &amp; Lanes</div>
              <div class="em-val">${r.speed_limit_kmh}</div>
              <div class="em-sub">${r.lanes_per_direction} lanes/dir (${r.direction})</div>
            </div>
            <div class="exec-metric-box">
              <div class="em-lbl">Published Capacity</div>
              <div class="em-val" style="color:#34d399; font-size:0.78rem;">${r.capacity_vph_per_dir}</div>
              <div class="em-sub">Connected Sites: ${connectedLinks.length}</div>
            </div>
          </div>

          <div class="kv-grid">
            <div class="kv-row"><div class="kv-lbl">HGV Truck Ban &amp; Salik Toll Policy</div><div class="kv-val"><strong>HGV Rule:</strong> ${r.hgv_truck_ban_window}<br/><strong>Salik:</strong> ${r.salik_toll_status}</div></div>
            <div class="kv-row"><div class="kv-lbl">Corridor Traffic Profiles (${roadObs.length} Time Windows)</div><div class="kv-val">${obsHtml}</div></div>
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

    function showIntersectionInspector(i) {
      switchDrawerTab("insp");
      map.flyTo([i.latitude, i.longitude], 15, { duration: 0.7 });
      document.getElementById("inspectorContainer").innerHTML = `
        <div class="detail-card">
          <span class="brand-badge" style="background:#e11d48;">${i.intersection_id} • Critical Junction</span>
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
      switchDrawerTab("insp");
      document.getElementById("inspectorContainer").innerHTML = `
        <div class="detail-card">
          <span class="brand-badge" style="background:#7c3aed;">${c.community_id} • Community Hotspot</span>
          <h4 style="margin-top:6px;">${c.community_name}</h4>
          <div class="kv-grid">
            <div class="kv-row"><div class="kv-lbl">Construction Activity Index &amp; Rank</div><div class="kv-val"><strong style="color:var(--cyan);">${c.construction_activity_index_score}</strong></div></div>
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
    function runUseCase(num) {
      switchDrawerTab("uc");
      document.querySelectorAll(".uc-btn").forEach((b, idx) => b.classList.toggle("active", idx === num - 1));

      if (num === 1) {
        document.getElementById("emirateSelect").value = "Dubai";
        populateCommunityDropdown();
        map.flyTo([25.105, 55.245], 11, { duration: 0.9 });
        document.getElementById("hudScope").textContent = "Use Case 1: Dubai Construction Hotspots";
        renderAllMapLayers();

        const dxbComms = DATA.communities.filter(c => c.emirate === "Dubai");
        document.getElementById("useCaseContainer").innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Use Case 1 — City-Wide Hotspot Intelligence</span>
            <h4 style="margin-top:6px;">"Which areas in Dubai currently have the highest construction activity?"</h4>
            <p style="font-size:0.76rem; color:#cbd5e1;">Grounded in Task 1's 20 Dubai Flagship Projects (<code>PRJ-D1..D20</code>), DLD <code>dld_projects-open</code> active escrow registries, and DM GIS community boundaries, construction activity in Dubai is concentrated across <strong>6 primary clusters</strong>:</p>
            ${dxbComms.map(c => `
              <div style="background:#090d16; border:1px solid #334155; padding:8px; border-radius:7px; margin-bottom:7px; cursor:pointer;" onclick="map.flyTo([${c.center_lat}, ${c.center_lon}], ${c.recommended_zoom}); showCommunityInspector(DATA.communities.find(x=>x.community_id==='${c.community_id}'))">
                <div style="display:flex; justify-content:space-between; font-size:0.78rem; font-weight:700; color:#fff;">
                  <span>${c.community_name}</span>
                  <span style="color:var(--cyan);">${c.construction_activity_index_score.split(' ')[0]}</span>
                </div>
                <div style="font-size:0.72rem; color:#94a3b8; margin-top:3px;">
                  <strong>${c.active_developments_count} Devs</strong> • <strong>${c.active_towers_and_buildings} Towers/Clusters</strong> • <strong>${c.scheduled_units_2025_2029.toLocaleString()} Units</strong> • <strong>${(c.active_structural_gfa_sqm/1e6).toFixed(2)}M m² GFA</strong>
                </div>
                <div style="font-size:0.71rem; color:${congestionColor(c.observed_congestion_severity)}; margin-top:2px;">Traffic: ${c.observed_congestion_severity}</div>
              </div>
            `).join("")}
            <div style="font-size:0.71rem; color:var(--muted); border-top:1px solid #334155; padding-top:6px;">
              <strong>Key Analytical Insight:</strong> High construction GFA does <em>not</em> automatically produce severe congestion. <strong>Dubai South / DWC (7.85M m² GFA)</strong> experiences <em>Low–Moderate</em> congestion because it is served by 12-lane 24/7 HGV-exempt freeways (<code>E611</code> &amp; <code>E77</code>), whereas <strong>JVC (3.42M m² GFA)</strong> and <strong>Business Bay (3.85M m² GFA)</strong> experience <em>Severe</em> peak congestion due to arterial/collector access funnels.
            </div>
          </div>
        `;
      } else if (num === 2) {
        document.getElementById("emirateSelect").value = "Dubai";
        populateCommunityDropdown();
        document.getElementById("communitySelect").value = "COM-DXB-01";
        map.flyTo([25.0565, 55.2090], 14, { duration: 0.9 });
        document.getElementById("hudScope").textContent = "Use Case 2: JVC Construction & Traffic Impact";
        renderAllMapLayers();

        document.getElementById("useCaseContainer").innerHTML = `
          <div class="detail-card">
            <span class="brand-badge" style="background:#e11d48;">Use Case 2 — JVC Community Deep-Dive</span>
            <h4 style="margin-top:6px;">"Show construction activity in JVC and the surrounding traffic conditions."</h4>
            <p style="font-size:0.76rem; color:#cbd5e1;"><strong>Jumeirah Village Circle (JVC)</strong> has <strong>38 active developments (64 towers, ~28,500 scheduled units, 3.42M m² active GFA)</strong> plus major Hessa St East masterplans (<a href="javascript:void(0)" onclick="showProjectInspector('PRJ-D16')">PRJ-D16 DAMAC Lagoons</a> &amp; <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-D19')">PRJ-D19 Tilal Al Ghaf</a>), all funneling into 3 primary corridors:</p>

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
        document.getElementById("emirateSelect").value = "Dubai";
        populateCommunityDropdown();
        map.flyTo([25.125, 55.255], 12, { duration: 0.9 });
        document.getElementById("hudScope").textContent = "Use Case 3: Temporal & Historical Comparison";
        renderAllMapLayers();

        document.getElementById("useCaseContainer").innerHTML = `
          <div class="detail-card">
            <span class="brand-badge" style="background:#0d9488;">Use Case 3 — Temporal &amp; Historical Analysis</span>
            <h4 style="margin-top:6px;">"Compare traffic conditions around construction hotspots across Morning, Midday, Evening &amp; 2024–2026."</h4>
            <p style="font-size:0.75rem; color:#cbd5e1;">Use the <strong>Time Window buttons in the top bar</strong> to watch the map update dynamically. Below is the multi-period comparison separating <strong>Published City-Wide &amp; RTA Benchmarks</strong> from <strong>Modelled Corridor Estimates</strong>:</p>

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
                  • <strong>Morning Peak (07:30–09:30):</strong> Formula BPR <code>v_BPR = 68.1 km/h</code> (8.81 min/10km at V/C=1.04) + modelled bottleneck-delay assumption <code>d_adj = +11.87 min/10km</code> = <strong>20.68 min/10km → 29.0 km/h</strong> (HGVs banned).<br/>
                  • <strong>Midday (12:00–14:00):</strong> Formula BPR <code>v_BPR = 75.8 km/h</code> (7.92 min/10km at V/C=0.78) + modelled bottleneck-delay assumption <code>d_adj = +4.58 min/10km</code> = <strong>12.50 min/10km → 48.0 km/h</strong>.<br/>
                  • <strong>Evening Peak (17:00–20:00):</strong> Formula BPR <code>v_BPR = 65.6 km/h</code> (9.15 min/10km at V/C=1.10) + modelled bottleneck-delay assumption <code>d_adj = +14.85 min/10km</code> = <strong>24.00 min/10km → 25.0 km/h</strong>.<br/>
                  • <strong>Night (22:00–05:00):</strong> Formula BPR <code>v_BPR = 79.9 km/h</code> (7.51 min/10km at V/C=0.29) + modelled bottleneck-delay assumption <code>d_adj = +1.31 min/10km</code> = <strong>8.82 min/10km → 68.0 km/h</strong>.<br/>
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
                <div class="kv-val" style="color:#fcd34d;">
                  Official RTA, SRTA, and Salik releases substantiate corridor capacities, bridge upgrades, travel-time reduction percentages, and HGV ban windows. TomTom's public Dubai Traffic Index is cited strictly at the city-wide level (<code>OBS-DXB-CITY-00</code>). All 21 corridor-level speed, volume, and congestion values (<code>OBS-DXB-001..015</code>, <code>OBS-SHJ-001..006</code>) are explicitly classified as <strong>Modelled Corridor Estimates</strong> (<code>confidence = "Estimated"</code>).
                </div>
              </div>
            </div>
          </div>
        `;
      } else if (num === 4) {
        document.getElementById("emirateSelect").value = "Sharjah";
        populateCommunityDropdown();
        map.flyTo([25.312, 55.505], 12, { duration: 0.9 });
        document.getElementById("hudScope").textContent = "Priority 2: Sharjah Expansion (12 Projects)";
        renderAllMapLayers();

        document.getElementById("useCaseContainer").innerHTML = `
          <div class="detail-card">
            <span class="brand-badge" style="background:#d97706;">Priority 2 — Sharjah Expansion</span>
            <h4 style="margin-top:6px;">Sharjah Construction &amp; Corridor Intelligence (12 Flagships on Unified Architecture)</h4>
            <p style="font-size:0.76rem; color:#cbd5e1;">Reusing the exact Dubai spatial schema, all 12 Sharjah Flagship Projects (<code>PRJ-SH1..SH12</code>) are mapped across Sharjah's 3 primary commuter &amp; megaproject corridors:</p>
            <div class="kv-grid">
              <div class="kv-row">
                <div class="kv-lbl">1. Muwaileh, Aljada &amp; Al Zahia Nexus (E311 × E88)</div>
                <div class="kv-val">
                  • <strong>Projects:</strong> <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH2')">PRJ-SH2 Aljada (25,000 units)</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH9')">PRJ-SH9 Al Zahia</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH8')">PRJ-SH8 Olfah</a>.<br/>
                  • <strong>Traffic:</strong> <a href="javascript:void(0)" onclick="showRoadInspector('RD-SHJ-01')">E311 Southbound</a> has a <strong>Modelled Corridor Estimate of ~28 km/h (Severe)</strong> in AM peak &amp; ~31 km/h in PM peak. SRTA &amp; Arada built dedicated Aljada/Airport Rd (E88) grade-separated bridges to bypass E311 queues.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">2. Emirates Road (E611) Forest &amp; Eco-City Belt</div>
                <div class="kv-val">
                  • <strong>Projects:</strong> <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH3')">PRJ-SH3 Masaar 1–3</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH5')">PRJ-SH5 Khalid Bin Sultan City (Zaha Hadid)</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH6')">PRJ-SH6 Hayyan</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH7')">PRJ-SH7 Tilal City</a>, <a href="javascript:void(0)" onclick="showProjectInspector('PRJ-SH10')">PRJ-SH10 Sharjah Sustainable City</a>.<br/>
                  • <strong>Traffic:</strong> <a href="javascript:void(0)" onclick="showRoadInspector('RD-SHJ-02')">Emirates Rd (E611)</a> operates at a <strong>Modelled Corridor Estimate of ~62 km/h (Moderate)</strong> in PM peak; SRTA's 320m Al Dhaid Bridge (E88) opens November 15, 2026.
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
            <p style="font-size:0.76rem; color:#cbd5e1;"><strong>Database Findings:</strong> JVC (<code>COM-DXB-01</code>) records <strong>38 active developments, 64 active towers, 28,500 scheduled units, and 3,420,000 m² active structural GFA</strong>. Officially published RTA capacity on <code>RD-DXB-05</code> (Hessa St D61) doubles from <strong>4,000 to 8,000 vph/dir</strong> under the AED 689M upgrade, while modelled corridor speeds are <strong>~29 km/h (AM Peak)</strong> and <strong>~25 km/h (PM Peak — Severe)</strong>, and <code>RD-DXB-03</code> (Al Khail Rd E44) is modelled at <strong>~58–64 km/h</strong> calibrated to RTA's published 30% travel-time reduction.</p>
            <div class="kv-grid">
              ${jvcLinks.map(l => `
                <div class="kv-row" style="cursor:pointer;" onclick="showProjectInspector('${l.project_id}')">
                  <div class="kv-lbl">${l.project_id} → ${l.primary_road_id} (${l.distance_to_primary_road_km} km Haversine to [${l.nearest_road_vertex_wgs84}])</div>
                  <div class="kv-val"><strong>${l.project_name}</strong><br/><span style="color:#34d399;">${l.published_road_capacity_and_upgrade_fact}</span><br/>${l.observed_road_traffic_condition}<br/><em>${l.modelled_daily_hgv_concrete_rebar_trips}</em><br/><span style="color:var(--cyan);">${l.epistemic_impact_classification}</span></div>
                </div>
              `).join("")}
            </div>
            <div style="margin-top:8px; font-size:0.70rem; color:var(--muted);"><strong>Sources:</strong> DLD <code>dld_projects-open</code> (<code>SRC-020</code> JVC Master Community), RTA AED 689M Hessa St D61 Capacity Release (<code>SRC-433</code>), and RTA AED 700M Al Khail Rd E44 Capacity Release (<code>SRC-434</code>).</div>
          </div>
        `;
      } else if (q.includes("morning") || q.includes("evening") || q.includes("compare") || q.includes("vary") || q.includes("time")) {
        map.flyTo([25.0645, 55.2095], 13, { duration: 0.8 });
        const d61Obs = DATA.observations.filter(o => o.road_id === "RD-DXB-05" || o.road_id === "RD-DXB-03");
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic Temporal Comparison Query • Hessa St (D61) &amp; Al Khail Rd (E44)</span>
            <h4 style="margin-top:6px;">Morning vs. Midday vs. Evening vs. Night Traffic Comparison (${d61Obs.length} Modelled Corridor Scenarios)</h4>
            <div class="kv-grid">
              ${d61Obs.map(o => `
                <div class="kv-row" style="cursor:pointer;" onclick="showRoadInspector('${o.road_id}')">
                  <div class="kv-lbl">${o.road_id} • ${o.time_period} (${o.evidence_level})</div>
                  <div class="kv-val"><strong>Corridor Speed: ~${o.average_speed_kmh} km/h</strong> (${o.travel_time_min_per_10km} min/10km) | <strong>Uninterrupted BPR: ${o.bpr_uninterrupted_speed_kmh} km/h</strong> (${o.bpr_uninterrupted_time_min_per_10km} min/10km at V/C=${o.vc_ratio}) + <strong>Bottleneck Delay (+d_adj): +${o.bottleneck_and_control_delay_min_per_10km} min/10km</strong><br/><strong>Published Benchmark:</strong> <span style="color:#34d399;">${o.officially_published_corridor_benchmark}</span><br/><strong>Modelled Derivation:</strong> ${o.modelled_assumptions_and_derivation}<br/><strong>Modelled Volume:</strong> ${o.traffic_volume_vph}</div>
                </div>
              `).join("")}
            </div>
            <div style="margin-top:8px; font-size:0.71rem; color:#fcd34d;"><strong>Epistemic Notice:</strong> Corridor capacities and upgrade travel-time reduction targets are officially published by RTA (<code>SRC-433</code>, <code>SRC-434</code>). Segment-specific hourly speeds and volumes are Modelled Corridor Estimates derived via the BPR volume-delay function.</div>
          </div>
        `;
      } else if (q.includes("dubai south") || q.includes("dwc") || q.includes("maktoum") || q.includes("expo") || q.includes("e611")) {
        map.flyTo([24.9120, 55.1580], 12, { duration: 0.8 });
        const dsLinks = DATA.impact_links.filter(l => ["PRJ-D1", "PRJ-D15", "PRJ-D18", "PRJ-D6"].includes(l.project_id));
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic Spatial Query • Auto-Zoomed to Dubai South &amp; DWC [24.912, 55.158]</span>
            <h4 style="margin-top:6px;">Dubai South, Expo City &amp; DWC Airport Traffic &amp; Freight Intelligence</h4>
            <p style="font-size:0.76rem; color:#cbd5e1;"><strong>Database Findings:</strong> Dubai South (<code>COM-DXB-04</code>) has the largest active construction GFA in the UAE (<strong>7.85M m²</strong> across <code>PRJ-D1</code> DWC AED 128B Airport, <code>PRJ-D15</code> Azizi Venice &amp; <code>PRJ-D18</code> Expo City), yet modelled congestion is <strong>Low (~86 km/h modelled speed on E611, LOS B)</strong> because <strong>Emirates Road (E611)</strong> provides a published 11,400 vph/dir 6-lane capacity and is <strong>100% exempt from Dubai's daytime HGV truck bans</strong>.</p>
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
        map.flyTo([25.155, 55.275], 11, { duration: 0.8 });
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
            <p style="font-size:0.75rem; color:#cbd5e1;">Individual plot-level consultant TIS reports submitted via the <strong>RTA Traffic Engineering System (TES)</strong> are confidential commercial records. However, <strong>RTA and SRTA publish official corridor-level engineering studies and capacity upgrades</strong> for all major hotspots:</p>
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
                  <div class="kv-val"><strong>Coverage &amp; Freq:</strong> ${p.dubai_and_uae_coverage} (${p.update_frequency})<br/><strong>Limits &amp; Pricing:</strong> ${p.api_rate_limits} | ${p.pricing_structure}<br/><strong>Retention Rule:</strong> ${p.commercial_usage_and_retention_terms}<br/><span style="color:var(--cyan);"><strong>Verdict:</strong> ${p.prototype_recommendation}</span></div>
                </div>
              `).join("")}
            </div>
          </div>
        `;
      } else if (q.includes("both") || q.includes("severe") || q.includes("hotspot") || q.includes("highest") || q.includes("concentrated")) {
        const ranked = [...DATA.communities].sort((a, b) => parseFloat(b.construction_activity_index_score) - parseFloat(a.construction_activity_index_score));
        map.flyTo([25.155, 55.305], 11, { duration: 0.8 });
        out.innerHTML = `
          <div class="detail-card">
            <span class="brand-badge">Deterministic Hotspot &amp; Congestion Cross-Query (${ranked.length} Communities)</span>
            <h4 style="margin-top:6px;">Communities Ranked by Construction Activity Index &amp; Observed Congestion</h4>
            <div class="kv-grid">
              ${ranked.map(c => `
                <div class="kv-row" style="cursor:pointer;" onclick="map.flyTo([${c.center_lat}, ${c.center_lon}], ${c.recommended_zoom}); showCommunityInspector(DATA.communities.find(x=>x.community_id==='${c.community_id}'))">
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
          map.flyTo([lat, lon], 13, { duration: 0.8 });
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

    # Inject a prominent Task 2 banner at the very top of web/index.html & web/validation_report.html
    banner_html = """<!-- TASK 2 GLOBAL SWITCHER BANNER -->
  <div id="task2-global-banner" style="background:linear-gradient(90deg,#090d16 0%,#0f172a 50%,#1e1b4b 100%); color:#fff; padding:10px 20px; border-bottom:2px solid #38bdf8; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; font-family:system-ui,sans-serif; z-index:9999;">
    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
      <span style="background:#0284c7; color:#fff; font-weight:800; font-size:0.74rem; padding:3px 9px; border-radius:999px; text-transform:uppercase;">New — Task 2 Live Prototype</span>
      <strong style="font-size:0.92rem;">Geographic Visualization, Construction Activity &amp; Traffic Impact Intelligence (Dubai &amp; Sharjah)</strong>
    </div>
    <div style="display:flex; gap:8px; flex-wrap:wrap;">
      <a href="task2_gis_intelligence.html" style="background:#0284c7; border:1px solid #38bdf8; color:#fff; padding:6px 14px; border-radius:7px; font-weight:700; font-size:0.80rem; text-decoration:none;">🗺️ Launch Task 2 Interactive GIS &amp; Traffic Map →</a>
      <a href="datasets/dubai_sharjah_gis_bundle.geojson" style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.25); color:#bae6fd; padding:6px 11px; border-radius:7px; font-weight:600; font-size:0.76rem; text-decoration:none;">GeoJSON Bundle</a>
      <a href="datasets/21_task2_spatial_database.sqlite" style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.25); color:#bae6fd; padding:6px 11px; border-radius:7px; font-weight:600; font-size:0.76rem; text-decoration:none;">Task 2 Spatial SQLite</a>
      <a href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/22_project_road_impact_links.csv" style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.25); color:#bae6fd; padding:6px 11px; border-radius:7px; font-weight:600; font-size:0.76rem; text-decoration:none;">Road Impact Links CSV</a>
    </div>
  </div>"""

    for page_fn in ("index.html", "validation_report.html"):
        p_file = WEB_DIR / page_fn
        if p_file.exists():
            txt = p_file.read_text(encoding="utf-8")
            if "id=\"task2-global-banner\"" not in txt:
                txt = txt.replace("<body>", "<body>\n" + banner_html, 1)
                p_file.write_text(txt, encoding="utf-8")
                print(f"Injected Task 2 Navigation Banner into {page_fn}")


if __name__ == "__main__":
    main()
