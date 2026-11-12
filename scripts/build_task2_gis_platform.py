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
    audits_all = {a["project_id"]: a for a in load_ds("06c_pipeline_and_calculation_audit")}
    supply_recon = load_ds("06b_supply_pipeline_reconciliation")
    sqlite_schemas = load_ds("11_sqlite_schema_inspector")

    for p in projs_all:
        a = audits_all.get(p["project_id"], {})
        p["gross_project_value_aed_b"] = a.get("gross_project_value_aed_b", 0.0)
        p["valuation_basis"] = a.get("valuation_basis", "Published Official GDV / Contract Award (Verified)")
        p["macro_sector"] = a.get("macro_sector", p.get("project_category", "Mixed-Use / Residential"))
        p["is_estimated_gdv"] = ("Est. GDV" in str(p.get("published_investment_value", "")))

    projs_dxb_shj = [p for p in projs_all if p["emirate"] in ("Dubai", "Sharjah")]
    uae_projects_summary = [
        {
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "developer": p["developer"],
            "emirate": p["emirate"],
            "community": p["city_district_community"],
            "coordinates": p["coordinates"],
            "lifecycle_status": p["lifecycle_status"],
            "published_investment_value": p["published_investment_value"],
            "gross_project_value_aed_b": p["gross_project_value_aed_b"],
            "is_estimated_gdv": p["is_estimated_gdv"],
            "gross_floor_area": p.get("gross_floor_area", ""),
            "confidence": p.get("confidence_classification", "Verified"),
        }
        for p in projs_all
    ]
    docs_all = load_ds("05_project_documents")
    arch_intel = {
        a["project_id"]: a
        for a in load_ds("05b_architectural_technical_intelligence")
        if a.get("emirate") in ("Dubai", "Sharjah")
    }
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
        "uae_projects_summary": uae_projects_summary,
        "supply_recon": supply_recon,
        "sqlite_schemas": sqlite_schemas,
        "documents": docs_all,
        "arch_intel": arch_intel,
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
  <link rel="stylesheet" href="./vendor/leaflet-1.9.4/leaflet.css" onerror="this.onerror=null;this.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'"/>
  <script src="./vendor/leaflet-1.9.4/leaflet.js" onerror="var s=document.createElement('script');s.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';document.head.appendChild(s);"></script>
  <link rel="stylesheet" href="./vendor/maplibre-gl-4.7.1/maplibre-gl.css" onerror="this.onerror=null;this.href='https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css'"/>
  <script src="./vendor/maplibre-gl-4.7.1/maplibre-gl.js" onerror="var s=document.createElement('script');s.src='https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js';document.head.appendChild(s);"></script>
  <script type="module">
    (async () => {{
      try {{
        const THREE_NS = await import("./vendor/three-0.170.0/three.module.js");
        window.THREE = Object.assign({{}}, THREE_NS);
      }} catch (localErr) {{
        try {{
          const THREE_CDN = await import("https://unpkg.com/three@0.170.0/build/three.module.js");
          window.THREE = Object.assign({{}}, THREE_CDN);
        }} catch (cdnErr) {{
          console.warn("Three.js 3D architectural layer fallback to native MapLibre/2D:", cdnErr);
        }}
      }}
      window.__haioVendorReady = true;
      window.dispatchEvent(new CustomEvent("haio-vendor-ready"));
    }})();
  </script>
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
      background: #141e2e;
      overflow: hidden;
    }}
    /* Primary WebGL 3D MapLibre Canvas (Full-Bleed) */
    #map3dCanvas {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      z-index: 2;
      opacity: 1;
    }}
    /* Backing Synchronized 2D Leaflet Canvas */
    #mapCanvas {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
      opacity: 1;
      pointer-events: none;
      background: #162231;
    }}
    #mapCanvas.basemap-sat {{
      background: #162231;
    }}
    #mapCanvas.basemap-light {{
      background: #e8e4d8;
    }}
    #mapCanvas.basemap-dark {{
      background: #1a1d23;
    }}
    .gis-dark-tiles {{
      filter: invert(1) hue-rotate(180deg) brightness(0.88) contrast(1.12) saturate(0.85);
    }}
    .map-stage.mode-2d-leaflet #mapCanvas {{
      opacity: 1;
      pointer-events: auto;
      z-index: 4;
    }}
    .map-stage.mode-2d-leaflet #map3dCanvas {{
      z-index: 1;
      pointer-events: none;
    }}
    .map-stage.mode-2d-leaflet #map3dCanvas .maplibregl-marker {{
      display: none;
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

    /* =========================================================================
       7-MODULE ANALYTICAL WORKSPACE, 4-LEVEL ZOOM BAR & 5-SECTION INSPECTOR CSS
       ========================================================================= */
    @media (max-width: 1860px) {{
      .kpi-strip {{
        display: none !important;
      }}
    }}
    .brand-cluster {{
      flex-shrink: 0;
    }}
    .mode-switcher {{
      gap: 3px;
      flex: 0 1 auto;
    }}
    .mode-btn {{
      padding: 6px 10px;
      font-size: 0.74rem;
    }}
    .ctrl-btn {{
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      color: #0f172a;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 0.73rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      white-space: nowrap;
    }}
    .ctrl-btn:hover {{
      background: #eff6ff;
      border-color: #2563eb;
      color: #2563eb;
    }}
    .ctrl-btn.primary {{
      background: #2563eb;
      border-color: #1d4ed8;
      color: #ffffff;
    }}
    .ev-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.74rem;
      color: #1e293b;
      background: #ffffff;
    }}
    .ev-table th, .ev-table td {{
      padding: 8px 10px;
      border-bottom: 1px solid #e2e8f0;
      text-align: left;
      vertical-align: top;
      line-height: 1.4;
    }}
    .ev-table th {{
      background: #f8fafc;
      color: #0f172a;
      font-weight: 800;
      font-size: 0.69rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      position: sticky;
      top: 0;
      z-index: 2;
      border-bottom: 2px solid #cbd5e1;
    }}
    .ev-table tr:hover td {{
      background: #f8fafc;
    }}
    .sidebar-right {{
      width: 432px;
    }}
    .analytical-workspace {{
      position: absolute;
      inset: 0;
      z-index: 1450;
      background: rgba(248, 250, 252, 0.98);
      backdrop-filter: blur(18px);
      overflow-y: auto;
      display: none;
      padding: 0 24px 48px 24px;
      color: #0f172a;
    }}
    .analytical-workspace .aw-sticky-bar {{
      margin: 0 -24px 18px -24px;
    }}
    .analytical-workspace.open {{
      display: block;
    }}
    .analytical-workspace.split-mode {{
      left: auto;
      right: 0;
      width: min(64vw, 980px);
      border-left: 1px solid #cbd5e1;
      box-shadow: -16px 0 48px rgba(15, 23, 42, 0.24);
    }}
    .aw-sticky-bar {{
      position: sticky;
      top: 0;
      z-index: 40;
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid #e2e8f0;
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .aw-container {{
      max-width: 1480px;
      margin: 0 auto;
      padding: 20px 24px;
    }}
    .aw-kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .aw-kpi-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 14px 16px;
      box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }}
    .aw-kpi-card .k-lbl {{
      font-size: 0.68rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #64748b;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 4px;
    }}
    .aw-kpi-card .k-val {{
      font-size: 1.38rem;
      font-weight: 800;
      color: #0f172a;
      margin: 5px 0 3px;
      letter-spacing: -0.02em;
    }}
    .aw-kpi-card .k-sub {{
      font-size: 0.72rem;
      color: #475569;
      line-height: 1.35;
    }}
    .aw-grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 16px;
      margin-bottom: 18px;
    }}
    .aw-panel-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
      margin-bottom: 16px;
    }}
    .aw-panel-card h3 {{
      margin: 0 0 6px 0;
      font-size: 1.05rem;
      font-weight: 800;
      color: #0f172a;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .aw-bar-row {{
      display: grid;
      grid-template-columns: 185px 1fr 110px;
      align-items: center;
      gap: 10px;
      padding: 6px 8px;
      border-radius: 8px;
      font-size: 0.76rem;
      cursor: pointer;
      transition: background 0.15s;
    }}
    .aw-bar-row:hover {{
      background: #f1f5f9;
    }}
    .aw-bar-track {{
      width: 100%;
      height: 10px;
      background: #f1f5f9;
      border-radius: 999px;
      overflow: hidden;
      position: relative;
    }}
    .aw-bar-fill {{
      height: 100%;
      border-radius: 999px;
      transition: width 0.35s ease;
    }}
    .geo-zoom-bar {{
      position: absolute;
      top: 62px;
      left: 16px;
      z-index: 800;
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      pointer-events: none;
    }}
    .geo-zoom-bar > * {{
      pointer-events: auto;
    }}
    .zoom-lvl-pill {{
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(10px);
      border: 1px solid #cbd5e1;
      border-radius: 999px;
      padding: 3px;
      display: inline-flex;
      align-items: center;
      gap: 2px;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.14);
    }}
    .zlvl-btn {{
      border: none;
      background: transparent;
      color: #475569;
      font-size: 0.71rem;
      font-weight: 700;
      padding: 5px 10px;
      border-radius: 999px;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s;
    }}
    .zlvl-btn:hover {{
      color: #0f172a;
      background: #f1f5f9;
    }}
    .zlvl-btn.active {{
      background: #0f172a;
      color: #ffffff;
    }}
    .preset-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 5px;
      margin: 8px 0 10px;
    }}
    .preset-btn {{
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      color: #334155;
      font-size: 0.69rem;
      font-weight: 700;
      padding: 6px 6px;
      border-radius: 8px;
      cursor: pointer;
      text-align: center;
      transition: all 0.15s;
    }}
    .preset-btn:hover, .preset-btn.active {{
      background: #eff6ff;
      border-color: #2563eb;
      color: #2563eb;
    }}
    .layer-group-hdr {{
      font-size: 0.66rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #2563eb;
      margin: 8px 0 3px;
      padding-left: 2px;
    }}
    .layer-meta-sub {{
      font-size: 0.64rem;
      color: #64748b;
      font-weight: 500;
      margin-left: 22px;
      line-height: 1.25;
    }}
    .prof-sec-hdr {{
      font-size: 0.71rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #1e293b;
      background: #f1f5f9;
      border-left: 3px solid #2563eb;
      padding: 6px 10px;
      border-radius: 6px;
      margin: 12px 0 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .badge-missing {{
      display: inline-block;
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      color: #475569;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 4px;
    }}
    .badge-hyp {{
      display: inline-block;
      background: #eef2ff;
      border: 1px solid #a5b4fc;
      color: #4338ca;
      font-size: 0.68rem;
      font-weight: 800;
      padding: 2px 8px;
      border-radius: 999px;
    }}
    @media (max-width: 1360px) {{
      .geo-zoom-bar {{
        top: 58px;
        left: 16px;
      }}
    }}
    @media (max-width: 1024px) {{
      .analytical-workspace {{
        position: relative;
        inset: auto;
      }}
      .analytical-workspace.split-mode {{
        width: 100%;
      }}
      .aw-grid-2 {{
        grid-template-columns: 1fr;
      }}
      .aw-bar-row {{
        grid-template-columns: 120px 1fr 90px;
      }}
      .geo-zoom-bar {{
        display: none;
      }}
    }}
    @media print {{
      .exec-header, .map-stage, .sidebar-right, .aw-sticky-bar button, .evidence-section {{
        display: none !important;
      }}
      html, body, .workbench {{
        height: auto !important;
        min-height: 0 !important;
        overflow: visible !important;
        background: #ffffff !important;
        color: #0f172a !important;
      }}
      .analytical-workspace {{
        display: block !important;
        position: static !important;
        inset: auto !important;
        width: 100% !important;
        height: auto !important;
        max-height: none !important;
        background: #ffffff !important;
        overflow: visible !important;
      }}
      .aw-container, .aw-panel-card, .t2-table-wrap, div[style*="max-height"] {{
        max-height: none !important;
        overflow: visible !important;
        break-inside: auto;
      }}
      .aw-kpi-card, .kv-row {{
        break-inside: avoid;
      }}
    }}
  </style>
</head>
<body>

  <!-- 1. HAIO-STYLE ULTRA-CLEAN WHITE TOP NAVBAR (7-MODULE INFORMATION ARCHITECTURE) -->
  <header class="exec-header">
    <div class="brand-cluster">
      <div class="brand-title" onclick="setPlatformMode('explorer', document.getElementById('mode-explorer'))">
        <span class="haio-logo-pin">🗺️</span>
        <span>UAE Construction Intelligence</span>
      </div>
      <div class="kpi-strip">
        <span class="kpi-chip">Scope <strong id="hudScope">Dubai Corridors</strong></span>
        <span class="kpi-chip">Sites <strong id="hudProjects">25 Active Sites</strong></span>
        <span class="kpi-chip">Avg Speed <strong id="hudAvgSpeed" style="color:#059669;">43.9 km/h</strong></span>
      </div>
    </div>

    <!-- 7 PROPOSED PLATFORM NAVIGATION MODULES -->
    <nav class="mode-switcher" aria-label="Primary Platform Navigation Modules">
      <button class="mode-btn" id="mode-overview" onclick="setPlatformMode('overview', this)" title="UAE-wide construction and transport intelligence summary">01 Overview</button>
      <button class="mode-btn" id="mode-construction" onclick="setPlatformMode('construction', this)" title="Projects, communities, development concentration and construction activity">02 Construction</button>
      <button class="mode-btn active" id="mode-explorer" onclick="setPlatformMode('explorer', this)" title="Interactive 2D/3D GIS, roads, projects, buildings and geographic layers">03 GIS Explorer</button>
      <button class="mode-btn" id="mode-traffic" onclick="setPlatformMode('traffic', this)" title="Traffic conditions, corridors, time comparisons and bottleneck analysis">04 Traffic</button>
      <button class="mode-btn" id="mode-impact" onclick="setPlatformMode('impact', this)" title="Project-road relationships, logistics movements, network and scenario simulator">05 Impact &amp; Logistics</button>
      <button class="mode-btn" id="mode-project" onclick="setPlatformMode('project', this)" title="Individual development, developer, investment and 5-section project profile">06 Project Explorer</button>
      <button class="mode-btn" id="mode-evidence" onclick="setPlatformMode('evidence', this)" title="Sources, official datasets, methodology, assumptions and validation">07 Data &amp; Evidence</button>
    </nav>

    <div class="header-actions">
      <select id="emirateSelect" class="emirate-pill-select" onchange="onEmirateChange()" aria-label="Select Emirate">
        <option value="Dubai" selected>Dubai (25 Sites)</option>
        <option value="Sharjah">Sharjah (12 Sites)</option>
        <option value="ALL">All UAE (85 National · 32 GIS + 5 JVC)</option>
      </select>

      <details class="export-dropdown">
        <summary>Data &amp; Exports ▾</summary>
        <div class="export-menu">
          <a href="javascript:void(0)" onclick="setPlatformMode('overview', document.getElementById('mode-overview')); setTimeout(()=>window.print(), 250);"><span>🖨️ Printable Executive Summary</span><span>PDF</span></a>
          <a href="javascript:void(0)" onclick="exportFilteredProjectsCsv()"><span>📥 Export Filtered Projects</span><span>CSV</span></a>
          <a href="csv/16_road_network_dataset.csv" download><span>🛣️ Road Corridors (23)</span><span>CSV</span></a>
          <a href="csv/17_traffic_congestion_observations.csv" download><span>🚦 Traffic Conditions (22)</span><span>CSV</span></a>
          <a href="csv/21b_intersections_and_nodes.csv" download><span>🛑 Bottleneck Intersections (16)</span><span>CSV</span></a>
          <a href="csv/22_project_road_impact_links.csv" download><span>🚛 Project-Road &amp; HGV Links (37)</span><span>CSV</span></a>
          <a href="csv/11_provenance_source_register.csv" download><span>📚 Source Register (452)</span><span>CSV</span></a>
          <a href="datasets/dubai_sharjah_gis_bundle.geojson" target="_blank"><span>📦 Spatial Bundle (123)</span><span>GeoJSON</span></a>
          <a href="datasets/21_task2_spatial_database.sqlite"><span>🗄️ Task 2 Spatial DB</span><span>SQLite</span></a>
          <a href="datasets/task2_verification_receipt.json" target="_blank"><span>✅ Verification Receipt (A–F)</span><span>JSON</span></a>
          <a href="task2_gis_and_traffic_intelligence_report.md" target="_blank"><span>📄 Full Task 2 Report</span><span>MD</span></a>
          <a href="index.html"><span>🏛️ Switch to Task 1 (85 Projects)</span><span>→</span></a>
        </div>
      </details>
    </div>
  </header>

  <!-- 2. FULL-BLEED REALISTIC 3D GIS STAGE + FLOATING INTELLIGENCE INSPECTOR + 7-MODULE WORKSPACE -->
  <main class="workbench" id="mainWorkbench">

    <!-- DEDICATED ANALYTICAL WORKSPACE OVERLAY FOR MODULES 01, 02, 04, 05, 07 -->
    <section class="analytical-workspace" id="analyticalWorkspaceModal" aria-label="Analytical Module Workspace">
      <div class="aw-sticky-bar">
        <div>
          <span class="brand-badge" id="awModuleBadge">MODULE 01</span>
          <strong style="font-size:1.05rem; margin-left:8px; color:#0f172a;" id="awModuleTitle">Executive Overview</strong>
          <span style="font-size:0.76rem; color:#64748b; margin-left:8px;" id="awModuleSub">UAE-wide construction activity, transport corridors &amp; traffic impact summary</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
          <span class="ep-pill-pub">PUBLISHED FACT</span>
          <span class="ep-pill-mod">MODELLED ESTIMATE</span>
          <span class="badge-hyp">HYPOTHETICAL SCENARIO</span>
          <button onclick="toggleAnalyticalSplitMode()" id="btnAwSplitToggle" style="background:#f8fafc; border:1px solid #cbd5e1; color:#0f172a; padding:6px 12px; border-radius:999px; font-size:0.75rem; font-weight:700; cursor:pointer;">◫ Split View with Map</button>
          <button onclick="window.print()" style="background:#f8fafc; border:1px solid #cbd5e1; color:#0f172a; padding:6px 12px; border-radius:999px; font-size:0.75rem; font-weight:700; cursor:pointer;">🖨️ Print Report</button>
          <button onclick="closeAnalyticalWorkspace()" style="background:#2563eb; border:1px solid #1d4ed8; color:#ffffff; padding:6px 14px; border-radius:999px; font-size:0.76rem; font-weight:700; cursor:pointer;">🗺️ Return to 3D GIS Map ✕</button>
        </div>
      </div>
      <div class="aw-container" id="analyticalWorkspaceBody"></div>
    </section>

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
          <span>⚙ Layers &amp; Presets (11)</span>
        </button>
      </div>

      <!-- Phase 4.1 & 3.2: 4 Adaptive Geographic Zoom Levels + Concentration Mode Switcher -->
      <div class="geo-zoom-bar" id="geoZoomLevelBar">
        <div class="zoom-lvl-pill" role="group" aria-label="4 Adaptive Geographic Zoom Levels">
          <button class="zlvl-btn" id="zlvl-1" onclick="setGeoZoomLevel(1)" title="Level 1: UAE National Overview (All 7 Emirates &amp; Primary Highways)">L1: UAE</button>
          <button class="zlvl-btn" id="zlvl-2" onclick="setGeoZoomLevel(2)" title="Level 2: Emirate Regional (Dubai or Sharjah Corridors &amp; Hotspots)">L2: Emirate</button>
          <button class="zlvl-btn" id="zlvl-3" onclick="setGeoZoomLevel(3)" title="Level 3: Community Local (JVC Sub-Clusters, Collectors &amp; Junctions)">L3: Community</button>
          <button class="zlvl-btn active" id="zlvl-4" onclick="setGeoZoomLevel(4)" title="Level 4: Project &amp; Corridor Detailed (3D Massing &amp; Vertex Vectors)">L4: Project 3D</button>
        </div>
        <div class="zoom-lvl-pill" role="group" aria-label="Construction Concentration Map Mode">
          <button class="zlvl-btn active" id="cmode-points" onclick="setConcentrationMode('points', this)" title="Proportional Project Points">● Points</button>
          <button class="zlvl-btn" id="cmode-heatmap" onclick="setConcentrationMode('heatmap', this)" title="Kernel Density Heatmap from Project Coordinates &amp; Active GFA">🔥 Density Heatmap</button>
          <button class="zlvl-btn" id="cmode-boundaries" onclick="setConcentrationMode('boundaries', this)" title="Community Hotspot Boundaries (10 Zones)">⬡ Communities</button>
          <button class="zlvl-btn" id="cmode-clusters" onclick="setConcentrationMode('clusters', this)" title="Development Sub-Clusters &amp; Impact Radii">◎ Clusters</button>
        </div>
      </div>

      <!-- 3D Projected Hero Tower Roof Callout ("Block 1 · 2 stacks") -->
      <div id="hero3DRoofCallout" class="haio-3d-block-callout" style="position:absolute; top:0; left:0; z-index:785; display:none; background:rgba(15,23,42,0.94); color:#ffffff; border:1px solid rgba(255,255,255,0.22); padding:6px 14px; font-size:0.78rem; font-weight:700; border-radius:999px; box-shadow:0 8px 24px rgba(0,0,0,0.45); pointer-events:auto;" onclick="select3DBlockCard('B1')">
        <span id="hero3DRoofCalloutText">Block 1 · 2 stacks</span>
      </div>

      <!-- Photorealistic 3D Attribution & Explicit Procedural vs. Sourced Massing Disclosure Badge -->
      <div id="photoreal3DAttribution" style="position:absolute; left:16px; bottom:96px; z-index:780; display:flex; align-items:center; gap:8px; pointer-events:none;">
        <div style="background:rgba(15,23,42,0.78); backdrop-filter:blur(8px); color:#f8fafc; padding:5px 11px; border-radius:8px; font-size:0.65rem; font-weight:600; line-height:1.3; text-align:left; border:1px solid rgba(255,255,255,0.16);">
          <strong style="font-size:0.72rem; display:block; color:#38bdf8;">4K Satellite · Dataset #05B Architectural 3D · Haio GLSL City</strong>
          <span>Selected Tower: Dataset #05B Floorplate &amp; Elevation Spec · City: OSM 3D + Rooftops</span>
        </div>
      </div>

      <!-- Center-Top Floating Scenario Dock (Hidden to avoid duplicate toolbar clutter) -->
      <div class="haio-lens-dock" id="haioLensDock" style="display:none;">
        <button class="haio-lens-btn active" id="lens-1" onclick="selectLensDock(1)"><span class="lens-ico">🔥</span><span>Hotspots</span></button>
        <button class="haio-lens-btn" id="lens-2" onclick="selectLensDock(2)"><span class="lens-ico">🚧</span><span>JVC Traffic</span></button>
        <button class="haio-lens-btn" id="lens-3" onclick="selectLensDock(3)"><span class="lens-ico">⏱️</span><span>AM vs PM</span></button>
        <button class="haio-lens-btn" id="lens-4" onclick="selectLensDock(4)"><span class="lens-ico">🏗️</span><span>Projects</span></button>
        <button class="haio-lens-btn" id="lens-5" onclick="selectLensDock(5)"><span class="lens-ico">🏢</span><span>Downtown 3D</span></button>
        <button class="haio-lens-btn" id="lens-6" onclick="selectLensDock(6)"><span class="lens-ico">🗺️</span><span>Sharjah</span></button>
      </div>

      <!-- Primary WebGL 3D MapLibre GL JS Canvas (Real OSM 3D Buildings + Satellite + Road Corridors) -->
      <div id="map3dCanvas"></div>
      <!-- Synchronized Backing 2D Leaflet Canvas -->
      <div id="mapCanvas" class="basemap-sat"></div>

      <!-- Phase 4.2: Organized 7-Group Layer System & 6 Layer Presets Popover -->
      <div class="layers-drawer-popover" id="layersPopover" style="width:376px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <strong style="font-size:0.84rem; color:#0f172a;">7-Group GIS Layers (11) &amp; Presets</strong>
          <div style="display:flex; gap:6px;">
            <button onclick="resetAllFilters()" style="background:#eff6ff;border:1px solid #bfdbfe;color:#2563eb;font-size:0.70rem;font-weight:700;padding:3px 9px;border-radius:999px;cursor:pointer;">Reset</button>
            <button onclick="toggleLayersPopover()" style="background:transparent;border:none;color:#64748b;font-size:0.95rem;cursor:pointer;">✕</button>
          </div>
        </div>

        <label class="ctrl-label" style="margin-top:2px;">One-Click Analytical Layer Presets (6)</label>
        <div class="preset-grid" id="layerPresetGrid">
          <button class="preset-btn active" onclick="applyLayerPreset('construction_overview', this)">1. Construction Overview</button>
          <button class="preset-btn" onclick="applyLayerPreset('traffic_overview', this)">2. Traffic Overview</button>
          <button class="preset-btn" onclick="applyLayerPreset('logistics', this)">3. Construction Logistics</button>
          <button class="preset-btn" onclick="applyLayerPreset('disruptions', this)">4. Road Disruptions</button>
          <button class="preset-btn" onclick="applyLayerPreset('project_impact', this)">5. Project Impact</button>
          <button class="preset-btn" onclick="applyLayerPreset('all_layers', this)">6. All 11 Layers</button>
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
              <option value="Severe">Severe (&lt;42% v₀)</option>
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
              <option value="ALL">All Epistemic Tiers</option>
              <option value="Tier 4">Confirmed Causal (ROW)</option>
              <option value="Tier 2">Spatial Association</option>
              <option value="Tier 3">Modelled HGV Load</option>
            </select>
          </div>
        </div>

        <div class="layer-list">
          <div class="layer-group-hdr">Group 1 — Construction Activity</div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L1" checked onchange="toggleLayerGroup('projects', this.checked)"/><span class="layer-dot" style="background:#2563eb;"></span> 1. Active Construction Projects (32 + 5)</label>
              <span class="prov-tag prov-ver">Published</span>
            </div>
            <div class="layer-meta-sub">Source: DLD / SRERD / Developer Releases (DS #04) · Updated: Nov 2026</div>
          </div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L3" checked onchange="toggleLayerGroup('communities', this.checked)"/><span class="layer-dot" style="background:#7c3aed;"></span> 2. Community Hotspots (10 Zones)</label>
              <span class="prov-tag prov-ver">Derived</span>
            </div>
            <div class="layer-meta-sub">Source: DM GIS &amp; DLD Escrow Boundaries (DS #21A) · Updated: Nov 2026</div>
          </div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L2" onchange="toggleLayerGroup('devbounds', this.checked)"/><span class="layer-dot" style="background:#8b5cf6;"></span> 5. JVC Sub-Clusters (5 Multi-Tower)</label>
              <span class="prov-tag prov-ver">Published</span>
            </div>
            <div class="layer-meta-sub">Source: DLD Plot Registry &amp; Developer Filings (DS #21D) · Updated: Nov 2026</div>
          </div>

          <div class="layer-group-hdr">Group 2 — Transport Network</div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L4" checked onchange="toggleLayerGroup('roads', this.checked)"/><span class="layer-dot" style="background:#64748b;"></span> 4. Base Road Network (23 Corridors)</label>
              <span class="prov-tag prov-ver">Published</span>
            </div>
            <div class="layer-meta-sub">Source: RTA / SRTA &amp; OSM Highway Polylines (DS #16) · Updated: Nov 2026</div>
          </div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L8" onchange="toggleLayerGroup('transit', this.checked)"/><span class="layer-dot" style="background:#3b82f6;"></span> 8. Metro Red/Blue &amp; Etihad Rail (3)</label>
              <span class="prov-tag prov-ver">Published</span>
            </div>
            <div class="layer-meta-sub">Source: RTA Rail Agency (SRC-440) &amp; Etihad Rail · Updated: May 2025</div>
          </div>

          <div class="layer-group-hdr">Group 3 — Traffic Conditions &amp; Bottlenecks</div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L6" checked onchange="toggleLayerGroup('traffic', this.checked)"/><span class="layer-dot" style="background:#FF0018;"></span> 3. Modelled Corridor Speeds (4 Windows)</label>
              <span class="prov-tag prov-mod">Modelled</span>
            </div>
            <div class="layer-meta-sub">Source: Two-Term BPR + Bottleneck Model on RTA Cap (DS #17) · Nov 2026</div>
          </div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L5" onchange="toggleLayerGroup('intersections', this.checked)"/><span class="layer-dot" style="background:#f43f5e;"></span> 6. Bottleneck Intersections (16 Nodes)</label>
              <span class="prov-tag prov-mod">Derived/LOS</span>
            </div>
            <div class="layer-meta-sub">Source: RTA/SRTA Interchange Upgrades (DS #21B) · Updated: Nov 2026</div>
          </div>

          <div class="layer-group-hdr">Group 4 — Construction Logistics</div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L9" onchange="toggleLayerGroup('facilities', this.checked)"/><span class="layer-dot" style="background:#10b981;"></span> 9. Logistics, Batching &amp; Urban Hubs (30)</label>
              <span class="prov-tag prov-ver">Observed</span>
            </div>
            <div class="layer-meta-sub">Source: Al Quoz/Ras Al Khor/JAFZA/Sajaa &amp; Civic Registry (DS #09B)</div>
          </div>

          <div class="layer-group-hdr">Group 5 — Road Disruption</div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L7" onchange="toggleLayerGroup('incidents', this.checked)"/><span class="layer-dot" style="background:#f97316;"></span> 7. Active RTA/SRTA Roadworks (5 Zones)</label>
              <span class="prov-tag prov-ver">Published</span>
            </div>
            <div class="layer-meta-sub">Source: Official RTA/SRTA Capital Works Releases (DS #21C) · 2024–2026</div>
          </div>

          <div class="layer-group-hdr">Group 6 — Project-to-Road Impact</div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L11" onchange="toggleLayerGroup('impacts', this.checked)"/><span class="layer-dot" style="background:#f59e0b;"></span> 11. Project-to-Road Impact Vectors (37)</label>
              <span class="prov-tag prov-mod">Derived/Mod</span>
            </div>
            <div class="layer-meta-sub">Source: WGS84 Haversine Nearest-Vertex + 4-Comp HGV (DS #22)</div>
          </div>

          <div class="layer-group-hdr">Group 7 — Urban Context &amp; Mobility</div>
          <div class="layer-item" style="flex-direction:column; align-items:stretch;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <label><input type="checkbox" id="chk-L10" onchange="toggleLayerGroup('parking', this.checked)"/><span class="layer-dot" style="background:#14b8a6;"></span> 10. Parking, EV &amp; Mobility Hubs (7)</label>
              <span class="prov-tag prov-ver">Published</span>
            </div>
            <div class="layer-meta-sub">Source: Parkin PJSC, RTA Park-and-Ride &amp; DEWA EV (DS #20)</div>
          </div>
        </div>
      </div>

      <!-- Bottom-Left Floating Pills: Compass Orbit + 4 Diurnal Time Windows + Basemap + Traffic Heatmap Legend -->
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

        <!-- Phase 5.3 Contextual Traffic Condition Heatmap Legend -->
        <div class="map-legend" id="contextualMapLegend" title="Traffic Condition Heatmap Legend (Ratio of Corridor Speed v to Free-Flow v₀)">
          <span class="leg-row"><span class="layer-dot" style="background:#00E054;"></span>Low</span>
          <span class="leg-row"><span class="layer-dot" style="background:#FFB800;"></span>Mod</span>
          <span class="leg-row"><span class="layer-dot" style="background:#FF4500;"></span>High</span>
          <span class="leg-row"><span class="layer-dot" style="background:#FF0018;"></span>Severe</span>
          <span class="leg-row"><span class="layer-dot" style="background:#64748b;"></span>N/A</span>
        </div>

        <span id="hudTime" style="display:none;">Evening Peak (17:00–20:00)</span>
        <span id="hudHgvStatus" style="background:rgba(15,23,42,0.92); color:#fca5a5; border:1px solid #ef4444; padding:5px 10px; border-radius:999px; font-weight:700; font-size:0.70rem; box-shadow:0 4px 12px rgba(15,23,42,0.22);">🚫 HGV Ban 17:00–20:00 (E11/E44/D61)</span>
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
        <button class="dtab-btn active" id="dtab-insp" onclick="switchDrawerTab('insp')">🏢 5-Sec Profile &amp; 3D</button>
        <button class="dtab-btn" id="dtab-uc" onclick="switchDrawerTab('uc')">📌 Hotspots &amp; Tour</button>
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
      if (s.includes("Severe")) return "#FF0018";
      if (s.includes("High")) return "#FF4500";
      if (s.includes("Moderate")) return "#FFB800";
      return "#00E054";
    }

    function congestionCasingColor(levelStr) {
      const s = String(levelStr || "");
      if (s.includes("Unavailable")) return "#1e293b";
      if (s.includes("Severe")) return "#5C0009";
      if (s.includes("High")) return "#6E1B00";
      if (s.includes("Moderate")) return "#664400";
      return "#004D1C";
    }

    function getOsmStreetTrafficExprs(tp) {
      const s = String(tp || "");
      if (s.includes("Night")) {
        return {
          flow: "#00E054",
          casing: "#004D1C"
        };
      }
      if (s.includes("Midday")) {
        return {
          flow: [
            "match", ["get", "class"],
            ["motorway", "trunk"], "#FF4500",
            ["primary", "secondary"], "#FFB800",
            "#00E054"
          ],
          casing: [
            "match", ["get", "class"],
            ["motorway", "trunk"], "#6E1B00",
            ["primary", "secondary"], "#664400",
            "#004D1C"
          ]
        };
      }
      if (s.includes("Morning")) {
        return {
          flow: [
            "match", ["get", "class"],
            ["motorway", "trunk"], "#FF0018",
            "primary", "#FF4500",
            "secondary", "#FFB800",
            "#00E054"
          ],
          casing: [
            "match", ["get", "class"],
            ["motorway", "trunk"], "#5C0009",
            "primary", "#6E1B00",
            "secondary", "#664400",
            "#004D1C"
          ]
        };
      }
      // Evening Peak (17:00–20:00) — Pure Vivid Google-Maps Live Traffic Spectrum
      return {
        flow: [
          "match", ["get", "class"],
          ["motorway", "trunk", "primary"], "#FF0018",
          "secondary", "#FF4500",
          "tertiary", "#FFB800",
          "#00E054"
        ],
        casing: [
          "match", ["get", "class"],
          ["motorway", "trunk", "primary"], "#5C0009",
          "secondary", "#6E1B00",
          "tertiary", "#664400",
          "#004D1C"
        ]
      };
    }

    function getOsmClassColorsFor2D(roadClass, tp) {
      const s = String(tp || "");
      const cls = String(roadClass || "minor");
      if (s.includes("Night")) return { flow: "#00E054", casing: "#004D1C" };
      if (s.includes("Midday")) {
        if (cls === "motorway" || cls === "trunk") return { flow: "#FF4500", casing: "#6E1B00" };
        if (cls === "primary" || cls === "secondary") return { flow: "#FFB800", casing: "#664400" };
        return { flow: "#00E054", casing: "#004D1C" };
      }
      if (s.includes("Morning")) {
        if (cls === "motorway" || cls === "trunk") return { flow: "#FF0018", casing: "#5C0009" };
        if (cls === "primary") return { flow: "#FF4500", casing: "#6E1B00" };
        if (cls === "secondary") return { flow: "#FFB800", casing: "#664400" };
        return { flow: "#00E054", casing: "#004D1C" };
      }
      if (cls === "motorway" || cls === "trunk" || cls === "primary") return { flow: "#FF0018", casing: "#5C0009" };
      if (cls === "secondary") return { flow: "#FF4500", casing: "#6E1B00" };
      if (cls === "tertiary") return { flow: "#FFB800", casing: "#664400" };
      return { flow: "#00E054", casing: "#004D1C" };
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
          hgvStyle: "background:rgba(15,23,42,0.92); color:#fca5a5; border:1px solid #ef4444; padding:5px 10px; border-radius:999px; font-weight:700; font-size:0.70rem; box-shadow:0 4px 12px rgba(15,23,42,0.22);",
          narrative: "Morning commuter wave toward Business Bay, DIFC & Dubai/Sharjah employment hubs. Heavy construction trucks are restricted on primary passenger arterials; commuter queues dominate Hessa St (29 km/h) and E311 Southbound (28 km/h)."
        };
      }
      if (tp.includes("Midday")) {
        return {
          shortTp: "Midday HGV (12:00–14:00)",
          hgvBadge: "🚛 HGV Haulage Active (08:30–16:30)",
          text: "🚛 ACTIVE HGV CONCRETE & REBAR HAULAGE WINDOW (08:30–16:30 Permitted)",
          color: "#fde68a",
          hgvStyle: "background:rgba(15,23,42,0.92); color:#fde68a; border:1px solid #f59e0b; padding:5px 10px; border-radius:999px; font-weight:700; font-size:0.70rem; box-shadow:0 4px 12px rgba(15,23,42,0.22);",
          narrative: "Passenger commuter peaks subside (Hessa St rises to 48 km/h; Al Khail Rd rises to 78 km/h), while active daytime HGV concrete mixers, rebar trailers, and earthworks tippers operate across JVC, Business Bay, Creek Harbour & Dubai South."
        };
      }
      if (tp.includes("Night")) {
        return {
          shortTp: "Night Pour Window (22:00–05:00)",
          hgvBadge: "🌙 Night Concrete Pours (22:00–05:00)",
          text: "🌙 NIGHT MASS CONCRETE POUR & HEAVY FREIGHT WINDOW (22:00–05:00 Free-Flow)",
          color: "#6ee7b7",
          hgvStyle: "background:rgba(15,23,42,0.92); color:#6ee7b7; border:1px solid #10b981; padding:5px 10px; border-radius:999px; font-weight:700; font-size:0.70rem; box-shadow:0 4px 12px rgba(15,23,42,0.22);",
          narrative: "Free-flow passenger conditions across all corridors (Hessa St 68 km/h; SZR 88 km/h; Al Khail 92 km/h). Continuous nocturnal raft-foundation concrete pours and oversized structural steel deliveries operate unimpeded."
        };
      }
      return {
        shortTp: "PM Peak (17:00–20:00)",
        hgvBadge: "🚫 HGV Ban 17:00–20:00 (E11/E44/D61)",
        text: "🚫 HGVs Banned on E11/E44/D61 (17:00–20:00 PM Rush) — Peak Commuter Bottlenecks",
        color: "#fca5a5",
        hgvStyle: "background:rgba(15,23,42,0.92); color:#fca5a5; border:1px solid #ef4444; padding:5px 10px; border-radius:999px; font-weight:700; font-size:0.70rem; box-shadow:0 4px 12px rgba(15,23,42,0.22);",
        narrative: "Highest diurnal congestion across the network. Return commuter flows create severe bottlenecks on Hessa St West (25 km/h), JVC Circle Blvd (21 km/h), Financial Centre Rd (22 km/h), and SZR (44 km/h)."
      };
    }

    // =========================================================================
    // HAIO.SG-GRADE 3D ARCHITECTURAL MASSING, STACK & FLOOR ENGINE (MAPLIBRE GL)
    // =========================================================================
    const IS_SAFARI_WEBKIT = (
      /^((?!chrome|android).)*safari/i.test(navigator.userAgent || "") ||
      (/AppleWebKit/.test(navigator.userAgent || "") && !/Chrome\/|Chromium\/|Edg\//.test(navigator.userAgent || ""))
    );
    let map3d = null;
    let map3dLoaded = false;
    let map3dContextLost = false;
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

    function hashProjectSeed(str) {
      let h = 2166136261 >>> 0;
      const s = String(str || "PRJ-D11");
      for (let i = 0; i < s.length; i++) {
        h ^= s.charCodeAt(i);
        h = Math.imul(h, 16777619) >>> 0;
      }
      return h;
    }

    function getProject3DSpec(p) {
      if (!p) p = DATA.projects[0];
      const pid = String(p.project_id || p.subdev_id || "PRJ-D11");
      const fh = String(p.floors_and_height || p.floors_range || "");
      const tb = String(p.towers_and_buildings_count || p.building_count || "");
      const uv = String(p.apartments_and_villas_count || p.total_units || "");
      const seed = hashProjectSeed(pid);
      const arch = (DATA.arch_intel && DATA.arch_intel[pid]) ? DATA.arch_intel[pid] : null;

      let storeys = 42;
      const fm = fh.match(/(\d{2,3})\s*(?:floors|storeys|levels|F|G\+)/i) || fh.match(/G\+\d+P\+(\d{2,3})/i) || fh.match(/(\d{2,3})/);
      if (fm) {
        const parsed = parseInt(fm[1], 10);
        if (parsed >= 8 && parsed <= 160) storeys = parsed;
      }

      // Exact published storey counts & architectural typologies for all 32 UAE Flagship Projects + 5 JVC Sub-Clusters
      let typology = "twin_triple_highrise";
      if (pid === "PRJ-D10") { storeys = 131; typology = "supertall_diamond"; }
      else if (pid === "PRJ-D11") { storeys = 104; typology = "supertall_diamond"; }
      else if (pid === "PRJ-D12") { storeys = 122; typology = "supertall_diamond"; }
      else if (pid === "PRJ-D13") { storeys = 106; typology = "supertall_diamond"; }
      else if (pid === "PRJ-D3")  { storeys = 110; typology = "supertall_diamond"; }
      else if (pid === "SUB-JVC-04") { storeys = 122; typology = "supertall_diamond"; }
      else if (pid === "PRJ-D14") { storeys = 71;  typology = "organic_terraced"; }
      else if (pid === "PRJ-SH1") { storeys = 36;  typology = "organic_terraced"; }
      else if (pid === "PRJ-SH4") { storeys = 24;  typology = "organic_terraced"; }
      else if (pid === "PRJ-SH11") { storeys = 18; typology = "organic_terraced"; }
      else if (pid === "PRJ-D20") { storeys = 65;  typology = "twin_triple_highrise"; }
      else if (pid === "PRJ-D15") { storeys = 38;  typology = "twin_triple_highrise"; }
      else if (pid === "PRJ-D18") { storeys = 28;  typology = "twin_triple_highrise"; }
      else if (pid === "SUB-JVC-01") { storeys = 34; typology = "twin_triple_highrise"; }
      else if (pid === "SUB-JVC-03") { storeys = 28; typology = "twin_triple_highrise"; }
      else if (["PRJ-D2", "PRJ-D4", "PRJ-SH2", "PRJ-SH7", "PRJ-SH8", "SUB-JVC-02", "SUB-JVC-05"].includes(pid)) {
        storeys = Math.max(14, Math.min(28, storeys));
        typology = "urban_courtyard";
      } else if (["PRJ-D5", "PRJ-D6", "PRJ-D7", "PRJ-D16", "PRJ-D17", "PRJ-D19", "PRJ-SH3", "PRJ-SH5", "PRJ-SH6", "PRJ-SH9", "PRJ-SH10"].includes(pid)) {
        storeys = (pid === "PRJ-D17") ? 44 : 14;
        typology = (pid === "PRJ-D17") ? "twin_triple_highrise" : "villa_lagoon_masterplan";
      } else if (["PRJ-D1", "PRJ-D8", "PRJ-D9", "PRJ-SH12"].includes(pid)) {
        storeys = (pid === "PRJ-SH12") ? 14 : 10;
        typology = "civic_infra_campus";
      }

      let homes = 420;
      const um = uv.replace(/,/g, "").match(/(\d{2,6})/);
      if (um) homes = parseInt(um[1], 10);

      let blocksCount = 2;
      if (typology === "supertall_diamond" || typology === "organic_terraced") blocksCount = 2;
      else if (typology === "twin_triple_highrise" || typology === "urban_courtyard" || typology === "villa_lagoon_masterplan") blocksCount = 3;
      else blocksCount = 2;

      const stacksPerBlock = (typology === "supertall_diamond") ? 2 : 4;
      const floorToFloorM = typology === "supertall_diamond" ? 3.8 : (typology === "civic_infra_campus" ? 4.5 : 3.4);
      const podiumLevels = typology === "supertall_diamond" ? 6 : (typology === "twin_triple_highrise" ? 4 : 3);
      const basementLevels = typology === "supertall_diamond" ? 5 : 3;
      const plateW = typology === "supertall_diamond" ? 38 : (typology === "organic_terraced" ? 42 : (typology === "urban_courtyard" ? 46 : 36));
      const plateD = typology === "supertall_diamond" ? 31 : (typology === "organic_terraced" ? 28 : (typology === "urban_courtyard" ? 24 : 26));
      const plateSqm = Math.round(plateW * plateD * 0.92);
      const efficiencyPct = typology === "supertall_diamond" ? 74 : (typology === "twin_triple_highrise" ? 80 : 84);
      const elevatorsCount = typology === "supertall_diamond" ? 12 : (typology === "twin_triple_highrise" ? 6 : 4);
      const skyGardenEvery = typology === "supertall_diamond" ? 16 : 12;

      // Authentic haio.sg PBR Facade Palettes (glass, slab/ledge, frame/mullion, fin/crown, podium stone, timber)
      const HAIO_ARCH_PALETTES = [
        // 0: Sapphire Crystal Curtain-Wall + Silver-Champagne Diamond Crown (Burj Binghatti / Supertalls)
        { name: "Sapphire Low-E Curtain Wall & Silver-Champagne Crown Fins", glass: 0x3a6488, ledge: 0xf4f1ea, frame: 0xbac6d2, fin: 0xd8c8b0, crown: 0xe6dac6, solid: 0xdcd5c8, podium: 0x8c4a38, timber: 0x9e6b43, roof: 0xc8c0b4 },
        // 1: Warm Bronze-Champagne & Anthracite Glass (Mercedes-Benz Places / DIFC / Bugatti)
        { name: "Champagne-Bronze Anodised Fins & Smoked Solar-Control Glazing", glass: 0x3b4d5e, ledge: 0xede6da, frame: 0x9a8468, fin: 0xc8ad88, crown: 0xdac29e, solid: 0xcfc4b4, podium: 0x5c4938, timber: 0xa67246, roof: 0xc2b8a8 },
        // 2: Coastal Marine Limestone, Travertine & Sea-Teal Glass (Creek Harbour / Palm Jebel Ali / Sharjah Waterfront)
        { name: "Marine Limestone, Warm Travertine & Acoustic Sea-Teal Glazing", glass: 0x356873, ledge: 0xf6f3ec, frame: 0xc4ccd0, fin: 0xe0d8c8, crown: 0xebe4d6, solid: 0xe2dbd0, podium: 0x736454, timber: 0xa8764a, roof: 0xd0c8bc },
        // 3: Terracotta GRC, Sand-Travertine & Biophilic Courtyard Louvres (Aljada / JVC / DAMAC Lagoons)
        { name: "Warm Terracotta GRC, Omani Travertine & Biophilic Timber Louvres", glass: 0x3d586b, ledge: 0xf2ece1, frame: 0xa8927a, fin: 0xc48b68, crown: 0xd8b898, solid: 0xd8cbb8, podium: 0x824636, timber: 0xad7444, roof: 0xc8bfb0 }
      ];
      let palIdx = seed % HAIO_ARCH_PALETTES.length;
      if (pid === "PRJ-D11" || pid === "PRJ-D10" || pid === "PRJ-D12") palIdx = 0;
      else if (pid === "PRJ-D6" || pid === "PRJ-D14" || pid === "PRJ-D20") palIdx = 1;
      else if (pid === "PRJ-D3" || pid === "PRJ-D2" || pid === "PRJ-D5" || pid === "PRJ-SH1") palIdx = 2;
      else if (pid === "PRJ-SH2" || pid === "PRJ-D16") palIdx = 3;
      const palette = HAIO_ARCH_PALETTES[palIdx];

      const pubHeightMatch = fh.match(/(\d{3})\s*m\s*(?:Height|Supertall)/i);
      const heightM = pubHeightMatch
        ? parseInt(pubHeightMatch[1], 10)
        : Math.min(395, Math.max(38, Math.round(storeys * floorToFloorM)));
      const rotDeg = ((seed % 7) - 3) * 14; // Deterministic per-project architectural orientation

      const blocks = [];
      for (let b = 1; b <= blocksCount; b++) {
        const bStoreys = b === 1 ? storeys : (b === 2 ? Math.max(10, Math.round(storeys * (typology === "supertall_diamond" ? 0.18 : 0.74))) : Math.max(8, Math.round(storeys * 0.56)));
        const bHeight = b === 1 ? heightM : Math.round(bStoreys * floorToFloorM);
        const blkTitle = (typology === "supertall_diamond" && b === 2)
          ? "Block 2 (Sky-Garden Podium)"
          : `Block ${b}`;
        blocks.push({
          blockNum: b,
          id: `B${b}`,
          label: blkTitle,
          stacksLabel: b === 1 ? `Stacks 01 to 0${stacksPerBlock}` : `Stacks 0${stacksPerBlock + 1} to 0${stacksPerBlock * 2}`,
          storeys: bStoreys,
          heightM: bHeight
        });
      }
      return {
        pid, storeys, homes, blocksCount, stacksPerBlock, heightM, typology, seed, rotDeg, blocks,
        floorToFloorM, podiumLevels, basementLevels, plateW, plateD, plateSqm, efficiencyPct,
        elevatorsCount, skyGardenEvery, palette, arch
      };
    }

    // Generates Interactive Scaled Typical Floor Plan + Vertical Building Elevation Section SVG from Dataset #05B
    function buildArchitecturalBlueprintSvg(p, spec) {
      if (spec.typology === "civic_infra_campus") {
        const assetCat = p.project_category || p.project_type || "Civil & Civic Infrastructure";
        return `
          <div class="kv-row" style="margin:8px 0 10px; background:#f8fafc; border:1px dashed #cbd5e1;">
            <div class="kv-lbl"><span class="badge-missing">Residential Floorplate Not Applicable · Engineering BIM/CAD Restricted</span></div>
            <div class="kv-val">
              <strong>${spec.pid}</strong> is classified under <strong>${assetCat}</strong>. Residential apartment stack schematics (4BR/5BR) do not apply.<br/>
              • <strong>Published Functional Capacity / Scope:</strong> ${p.apartments_and_villas_count || "Civic Utility / Infrastructure Network"}<br/>
              • <strong>Published Structural Envelope:</strong> ${p.floors_and_height || `${spec.storeys} structural levels`}
            </div>
          </div>
        `;
      }
      const arch = spec.arch || (DATA.arch_intel && DATA.arch_intel[spec.pid]) || null;
      const selBlk = active3DBlock === "ALL" ? spec.blocks[0] : (spec.blocks.find(b => b.id === active3DBlock) || spec.blocks[0]);
      const is4BrOnly = active3DShowMe === "4br";
      const is5BrOnly = active3DShowMe === "5br";
      const s1Col = is5BrOnly ? "#cbd5e1" : "#fbbf24";
      const s2Col = is4BrOnly ? "#cbd5e1" : "#34d399";
      const s3Col = is5BrOnly ? "#cbd5e1" : "#f59e0b";
      const s4Col = is4BrOnly ? "#cbd5e1" : "#10b981";
      const s1Stroke = active3DStack === "S1" ? "#1d4ed8" : "#0f172a";
      const s2Stroke = active3DStack === "S2" ? "#1d4ed8" : "#0f172a";
      const lowActive = active3DFloor === "ALL" || active3DFloor === "LOW";
      const midActive = active3DFloor === "ALL" || active3DFloor === "MID";
      const highActive = active3DFloor === "ALL" || active3DFloor === "HIGH";

      const fLowEnd = Math.round(spec.storeys * 0.35);
      const fMidEnd = Math.round(spec.storeys * 0.72);

      return `
        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:12px; padding:10px; margin:8px 0 10px; color:#f8fafc;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:4px; margin-bottom:6px;">
            <span style="font-size:0.68rem; font-weight:800; letter-spacing:0.04em; color:#38bdf8; text-transform:uppercase;">
              📐 Illustrative Structural Floorplate &amp; Massing Schematic (${arch ? arch.arch_id : spec.pid})
            </span>
            <span style="font-size:0.65rem; background:rgba(16,185,129,0.18); color:#6ee7b7; border:1px solid rgba(16,185,129,0.4); padding:1px 6px; border-radius:999px; font-weight:700;">
              ${spec.plateSqm.toLocaleString()} m² Plate · ${spec.efficiencyPct}% Eff · ${spec.floorToFloorM}m F2F
            </span>
          </div>
          <svg viewBox="0 0 540 230" style="width:100%; height:auto; display:block; background:#09101d; border-radius:8px; border:1px solid #1e293b;">
            <defs>
              <pattern id="bpGrid" width="18" height="18" patternUnits="userSpaceOnUse">
                <path d="M 18 0 L 0 0 0 18" fill="none" stroke="rgba(56,189,248,0.09)" stroke-width="0.7"/>
              </pattern>
            </defs>
            <rect width="540" height="230" fill="url(#bpGrid)"/>

            <!-- LEFT PANE: TYPICAL STRUCTURAL FLOOR PLAN (METRIC SCALE) -->
            <text x="14" y="18" fill="#94a3b8" font-size="9.5" font-weight="700">A. TYPICAL FLOOR PLAN (${spec.plateW}m × ${spec.plateD}m · ${selBlk.label})</text>
            <!-- Dimension lines -->
            <line x1="28" y1="32" x2="232" y2="32" stroke="#38bdf8" stroke-width="0.9" stroke-dasharray="2,2"/>
            <text x="130" y="29" fill="#38bdf8" font-size="8.5" text-anchor="middle" font-weight="700">${spec.plateW}.0 m Curtain-Wall Span</text>

            <!-- Outer Cantilevered Balcony Perimeter (1.45m deep glass balustrade) -->
            <rect x="24" y="38" width="212" height="154" rx="6" fill="rgba(56,189,248,0.07)" stroke="#38bdf8" stroke-width="1.1" stroke-dasharray="4,2"/>
            <!-- Main Insulated Curtain-Wall Envelope -->
            <rect x="34" y="48" width="192" height="134" rx="4" fill="#111c2d" stroke="#e2e8f0" stroke-width="1.6"/>

            <!-- STACK 01 (NORTH-WEST WING — 4BR SKY SUITE) -->
            <g style="cursor:pointer;" onclick="update3DBlockControls(undefined, undefined, '${active3DStack === 'S1' ? 'ALL' : 'S1'}', undefined)">
              <rect x="37" y="51" width="88" height="58" rx="2" fill="${s1Col}" fill-opacity="0.26" stroke="${s1Stroke}" stroke-width="${active3DStack === 'S1' ? 2.2 : 1.1}"/>
              <line x1="68" y1="51" x2="68" y2="109" stroke="rgba(255,255,255,0.28)" stroke-width="0.8"/>
              <line x1="96" y1="51" x2="96" y2="109" stroke="rgba(255,255,255,0.28)" stroke-width="0.8"/>
              <line x1="37" y1="82" x2="125" y2="82" stroke="rgba(255,255,255,0.28)" stroke-width="0.8"/>
              <text x="81" y="72" fill="#fef3c7" font-size="8.5" font-weight="700" text-anchor="middle">STACK 01 (4BR)</text>
              <text x="81" y="96" fill="#cbd5e1" font-size="7.2" text-anchor="middle">Living · Show Kit · En-Suite</text>
            </g>

            <!-- STACK 02 (NORTH-EAST WING — 5BR SKY MANSION) -->
            <g style="cursor:pointer;" onclick="update3DBlockControls(undefined, undefined, '${active3DStack === 'S2' ? 'ALL' : 'S2'}', undefined)">
              <rect x="135" y="51" width="88" height="58" rx="2" fill="${s2Col}" fill-opacity="0.26" stroke="${s2Stroke}" stroke-width="${active3DStack === 'S2' ? 2.2 : 1.1}"/>
              <line x1="165" y1="51" x2="165" y2="109" stroke="rgba(255,255,255,0.28)" stroke-width="0.8"/>
              <line x1="195" y1="51" x2="195" y2="109" stroke="rgba(255,255,255,0.28)" stroke-width="0.8"/>
              <line x1="135" y1="82" x2="223" y2="82" stroke="rgba(255,255,255,0.28)" stroke-width="0.8"/>
              <text x="179" y="72" fill="#d1fae5" font-size="8.5" font-weight="700" text-anchor="middle">STACK 02 (5BR)</text>
              <text x="179" y="96" fill="#cbd5e1" font-size="7.2" text-anchor="middle">Salon · Chef Kit · Terrace</text>
            </g>

            <!-- STACK 03 (SOUTH-WEST WING) -->
            <g style="cursor:pointer;" onclick="update3DBlockControls(undefined, undefined, 'S1', undefined)">
              <rect x="37" y="121" width="88" height="58" rx="2" fill="${s3Col}" fill-opacity="0.22" stroke="#475569" stroke-width="1.0"/>
              <line x1="72" y1="121" x2="72" y2="179" stroke="rgba(255,255,255,0.24)" stroke-width="0.8"/>
              <line x1="37" y1="150" x2="125" y2="150" stroke="rgba(255,255,255,0.24)" stroke-width="0.8"/>
              <text x="81" y="142" fill="#fde68a" font-size="8.0" font-weight="700" text-anchor="middle">STACK 03 (4BR)</text>
              <text x="81" y="167" fill="#cbd5e1" font-size="7.0" text-anchor="middle">Corner Glass · Balcony</text>
            </g>

            <!-- STACK 04 (SOUTH-EAST WING) -->
            <g style="cursor:pointer;" onclick="update3DBlockControls(undefined, undefined, 'S2', undefined)">
              <rect x="135" y="121" width="88" height="58" rx="2" fill="${s4Col}" fill-opacity="0.22" stroke="#475569" stroke-width="1.0"/>
              <line x1="182" y1="121" x2="182" y2="179" stroke="rgba(255,255,255,0.24)" stroke-width="0.8"/>
              <line x1="135" y1="150" x2="223" y2="150" stroke="rgba(255,255,255,0.24)" stroke-width="0.8"/>
              <text x="179" y="142" fill="#a7f3d0" font-size="8.0" font-weight="700" text-anchor="middle">STACK 04 (5BR)</text>
              <text x="179" y="167" fill="#cbd5e1" font-size="7.0" text-anchor="middle">Panoramic Suite · Loggia</text>
            </g>

            <!-- CENTRAL RC SHEAR CORE & HIGH-SPEED ELEVATOR BANK (C80/95 CONCRETE) -->
            <rect x="92" y="92" width="76" height="46" rx="2" fill="#1e293b" stroke="#f8fafc" stroke-width="1.5"/>
            <rect x="96" y="96" width="12" height="12" fill="#38bdf8" fill-opacity="0.35" stroke="#38bdf8" stroke-width="0.8"/>
            <rect x="111" y="96" width="12" height="12" fill="#38bdf8" fill-opacity="0.35" stroke="#38bdf8" stroke-width="0.8"/>
            <rect x="126" y="96" width="12" height="12" fill="#38bdf8" fill-opacity="0.35" stroke="#38bdf8" stroke-width="0.8"/>
            <rect x="141" y="96" width="12" height="12" fill="#f59e0b" fill-opacity="0.35" stroke="#f59e0b" stroke-width="0.8"/>
            <text x="130" y="121" fill="#ffffff" font-size="7.5" font-weight="800" text-anchor="middle">RC SHEAR CORE</text>
            <text x="130" y="131" fill="#94a3b8" font-size="6.8" text-anchor="middle">${spec.elevatorsCount} Lifts + 2 Fire Stairs</text>

            <!-- Curtain-wall structural mullions around perimeter -->
            <text x="130" y="206" fill="#94a3b8" font-size="7.5" text-anchor="middle">1.6m Unitized Curtain-Wall Mullions · 1.45m Cantilevered Glass Balconies</text>
            <text x="130" y="218" fill="#38bdf8" font-size="7.3" font-weight="700" text-anchor="middle">Click any Stack in Plan to Highlight on 3D Tower</text>

            <!-- DIVIDER -->
            <line x1="262" y1="12" x2="262" y2="218" stroke="#1e293b" stroke-width="1.2"/>

            <!-- RIGHT PANE: VERTICAL TOWER ELEVATION & SECTION (CAT 3 + CAT 5) -->
            <text x="276" y="18" fill="#94a3b8" font-size="9.5" font-weight="700">B. ELEVATION &amp; SECTION (${spec.heightM}m · ${spec.storeys}F)</text>

            <!-- Architectural Crown / Spire -->
            <polygon points="355,28 385,28 394,46 346,46" fill="rgba(230,218,198,0.28)" stroke="#fde68a" stroke-width="1.2"/>
            <line x1="370" y1="18" x2="370" y2="28" stroke="#fde68a" stroke-width="1.5"/>
            <text x="405" y="39" fill="#fde68a" font-size="7.5" font-weight="700">Crown Spire + TMD (${spec.heightM}m)</text>

            <!-- HIGH-RISE SKY SUITES TIER -->
            <g style="cursor:pointer;" onclick="update3DBlockControls(undefined, '${active3DFloor === 'HIGH' ? 'ALL' : 'HIGH'}', undefined, undefined)">
              <rect x="342" y="46" width="56" height="38" fill="${highActive ? 'rgba(52,211,153,0.30)' : 'rgba(148,163,184,0.12)'}" stroke="#34d399" stroke-width="${active3DFloor === 'HIGH' ? 2.0 : 1.1}"/>
              <text x="370" y="68" fill="#ecfdf5" font-size="7.5" font-weight="700" text-anchor="middle">F${fMidEnd + 1}–F${spec.storeys}</text>
              <text x="405" y="67" fill="#a7f3d0" font-size="7.3">Sky Suites / Penthouses</text>
            </g>

            <!-- SKY GARDEN / OUTRIGGER BELT TRUSS FLOOR -->
            <rect x="344" y="84" width="52" height="9" fill="rgba(34,197,94,0.45)" stroke="#4ade80" stroke-width="1.0"/>
            <text x="405" y="91" fill="#4ade80" font-size="7.2" font-weight="700">🌿 Sky-Garden &amp; Outrigger</text>

            <!-- MID-RISE TIER -->
            <g style="cursor:pointer;" onclick="update3DBlockControls(undefined, '${active3DFloor === 'MID' ? 'ALL' : 'MID'}', undefined, undefined)">
              <rect x="338" y="93" width="64" height="38" fill="${midActive ? 'rgba(56,189,248,0.28)' : 'rgba(148,163,184,0.12)'}" stroke="#38bdf8" stroke-width="${active3DFloor === 'MID' ? 2.0 : 1.1}"/>
              <text x="370" y="115" fill="#e0f2fe" font-size="7.5" font-weight="700" text-anchor="middle">F${fLowEnd + 1}–F${fMidEnd}</text>
              <text x="408" y="114" fill="#bae6fd" font-size="7.3">Mid-Rise Residences</text>
            </g>

            <!-- LOW-RISE TIER -->
            <g style="cursor:pointer;" onclick="update3DBlockControls(undefined, '${active3DFloor === 'LOW' ? 'ALL' : 'LOW'}', undefined, undefined)">
              <rect x="334" y="131" width="72" height="36" fill="${lowActive ? 'rgba(251,191,36,0.26)' : 'rgba(148,163,184,0.12)'}" stroke="#fbbf24" stroke-width="${active3DFloor === 'LOW' ? 2.0 : 1.1}"/>
              <text x="370" y="152" fill="#fef3c7" font-size="7.5" font-weight="700" text-anchor="middle">F01–F${fLowEnd}</text>
              <text x="411" y="151" fill="#fde68a" font-size="7.3">Low-Rise Horizon</text>
            </g>

            <!-- MULTI-LEVEL PODIUM + LAP POOL DECK -->
            <rect x="312" y="167" width="116" height="22" rx="2" fill="rgba(180,83,9,0.38)" stroke="#f59e0b" stroke-width="1.2"/>
            <rect x="316" y="163" width="28" height="4" fill="#38bdf8"/>
            <text x="370" y="181" fill="#fef3c7" font-size="7.4" font-weight="700" text-anchor="middle">G + ${spec.podiumLevels}P Podium &amp; Pool Deck</text>

            <!-- SUBTERRANEAN BASEMENT & RAFT FOUNDATION -->
            <rect x="318" y="189" width="104" height="17" fill="rgba(100,116,139,0.32)" stroke="#94a3b8" stroke-width="1.0" stroke-dasharray="3,2"/>
            <text x="370" y="200" fill="#cbd5e1" font-size="7.0" text-anchor="middle">${spec.basementLevels}B Basement + 4.5m Raft + Piles</text>
            <text x="405" y="218" fill="#38bdf8" font-size="7.3" font-weight="700" text-anchor="middle">Click Elevation Tier to Filter 3D</text>
          </svg>
          <div style="font-size:0.70rem; color:#cbd5e1; margin-top:6px; line-height:1.4;">
            <strong style="color:#38bdf8;">Facade System:</strong> ${spec.palette.name}<br/>
            ${arch ? `<span style="color:#94a3b8;">${arch.cat5_elevations_and_building_sections.split('|')[0].trim()}</span>` : ""}
          </div>
        </div>
      `;
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
      const showProjs = document.getElementById("chk-L1")?.checked ?? true;
      const showSubdevs = document.getElementById("chk-L2")?.checked ?? false;

      if (showProjs) {
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
      }

      if (showSubdevs) {
        DATA.subdevs.forEach(sd => {
          if (emFilter !== "ALL" && sd.emirate !== emFilter) return;
          if (q && !JSON.stringify(sd).toLowerCase().includes(q)) return;
          features.push({
            type: "Feature",
            properties: {
              project_id: sd.subdev_id,
              color: "#a855f7",
              fillOpacity: 0.22,
              lineWidth: 2.0
            },
            geometry: { type: "Polygon", coordinates: [makeSiteCircleRing(sd.longitude, sd.latitude, 175)] }
          });
        });
      }

      return { type: "FeatureCollection", features };
    }

    function formatBearingCompass(b) {
      const deg = ((Math.round(b) % 360) + 360) % 360;
      const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
      const dir = dirs[Math.round(deg / 45) % 8];
      return { deg, label: `${dir} ${deg}°` };
    }

    function updateCompassUI() {
      const lblEl = document.getElementById("compassLabel");
      const svgEl = document.getElementById("compassSvg");
      if (currentCameraDim === "2D" || !map3d) {
        if (lblEl) lblEl.textContent = "N 0° (2D)";
        if (svgEl) svgEl.style.transform = "rotate(0deg)";
        return;
      }
      const { deg, label } = formatBearingCompass(map3d.getBearing());
      if (lblEl) lblEl.textContent = label;
      if (svgEl) svgEl.style.transform = `rotate(${-deg}deg)`;
    }

    function orbitCameraStep() {
      if (currentCameraDim === "2D") {
        setCameraDimension("3D");
      }
      if (!map3d) return;
      const nextBearing = (Math.round(map3d.getBearing() / 45) * 45 + 45) % 360;
      map3d.easeTo({ bearing: nextBearing, pitch: currentCameraDim === "3D" ? 60 : 0, duration: 650 });
    }

    function syncMapCanvasBackdropClass() {
      const mc = document.getElementById("mapCanvas");
      if (!mc) return;
      const mode = currentBasemapMode || "sat";
      mc.classList.toggle("basemap-sat", mode === "sat");
      mc.classList.toggle("basemap-light", mode === "light");
      mc.classList.toggle("basemap-dark", mode === "dark");
    }

    function createResilientLeafletTileLayer(primaryUrl, fallbackUrls, opts) {
      const layer = L.tileLayer(primaryUrl, Object.assign({
        crossOrigin: "anonymous",
        minZoom: 8,
        maxZoom: 19,
        maxNativeZoom: 18,
        noWrap: true,
        keepBuffer: 2,
        updateWhenIdle: false,
        updateWhenZooming: false
      }, opts || {}));
      if (Array.isArray(fallbackUrls) && fallbackUrls.length) {
        layer.on("tileerror", function (ev) {
          const img = ev && ev.tile;
          const coords = ev && ev.coords;
          if (!img || !coords) return;
          const idx = (img._fbIdx || 0);
          if (idx >= fallbackUrls.length) return;
          img._fbIdx = idx + 1;
          const z = Math.min(coords.z, (opts && opts.maxNativeZoom) || 18);
          let tmpl = fallbackUrls[idx];
          if (idx === fallbackUrls.length - 1 && opts && opts.fallbackDarkFilter) {
            img.classList.add("gis-dark-tiles");
          }
          img.src = tmpl
            .replace("{s}", ["a", "b", "c", "d"][(coords.x + coords.y) & 3])
            .replace("{z}", String(z))
            .replace("{x}", String(coords.x))
            .replace("{y}", String(coords.y));
        });
      }
      return layer;
    }

    function ensureLeafletBaseTiles() {
      if (!map) return;
      const mode = currentBasemapMode || "sat";
      syncMapCanvasBackdropClass();
      if (baseTileLayer && map.hasLayer(baseTileLayer) && baseTileLayer._basemapKey === mode) return;
      if (baseTileLayer) {
        try { map.removeLayer(baseTileLayer); } catch (_) {}
        baseTileLayer = null;
      }
      if (mode === "sat") {
        baseTileLayer = createResilientLeafletTileLayer(
          "https://mt{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
          [
            "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          ],
          { subdomains: "0123", maxNativeZoom: 19, zIndex: 1 }
        );
        baseTileLayer._basemapKey = mode;
        baseTileLayer.addTo(map);
        baseTileLayer.bringToBack();
      } else if (mode === "dark") {
        const darkBase = createResilientLeafletTileLayer(
          "https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
          [
            "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
          ],
          { maxNativeZoom: 16, zIndex: 1, fallbackDarkFilter: true }
        );
        const darkRef = createResilientLeafletTileLayer(
          "https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
          [],
          { maxNativeZoom: 16, zIndex: 2 }
        );
        baseTileLayer = L.layerGroup([darkBase, darkRef]);
        baseTileLayer._basemapKey = mode;
        baseTileLayer.addTo(map);
        darkBase.bringToBack();
      } else {
        baseTileLayer = createResilientLeafletTileLayer(
          "https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
          [
            "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
          ],
          { subdomains: "0123", maxNativeZoom: 19, zIndex: 1 }
        );
        baseTileLayer._basemapKey = mode;
        baseTileLayer.addTo(map);
        baseTileLayer.bringToBack();
      }
    }

    function isMap3dGlAlive() {
      if (!map3d || map3dContextLost) return false;
      try {
        const c = map3d.getCanvas && map3d.getCanvas();
        if (!c) return false;
        const gl = c.getContext("webgl2") || c.getContext("webgl");
        return Boolean(gl && !gl.isContextLost());
      } catch (_) {
        return false;
      }
    }

    function forceMap3dRepaintBurst() {
      if (!map3d || map3dContextLost) return;
      const tick = () => {
        if (!map3d || map3dContextLost) return;
        try {
          map3d.resize();
          map3d.triggerRepaint();
        } catch (_) {}
      };
      tick();
      if (typeof requestAnimationFrame === "function") {
        requestAnimationFrame(() => {
          tick();
          requestAnimationFrame(tick);
        });
      }
      setTimeout(tick, 120);
      setTimeout(tick, 320);
    }

    function setCameraDimension(dim) {
      const stageEl = document.getElementById("mapStage");
      const calloutEl = document.getElementById("hero3DRoofCallout");
      const attrEl = document.getElementById("photoreal3DAttribution");

      if (dim === "2D") {
        currentCameraDim = "2D";
        document.getElementById("btnDim2D")?.classList.add("active");
        document.getElementById("btnDim3D")?.classList.remove("active");
        if (stageEl) stageEl.classList.add("mode-2d-leaflet");
        if (calloutEl) calloutEl.style.display = "none";
        if (attrEl) attrEl.style.display = "none";

        if (map) {
          try { map.stop(); } catch (_) {}
          map.invalidateSize({ pan: false, animate: false });
          if (map3d && typeof map3d.getCenter === "function") {
            try {
              const c = map3d.getCenter();
              const rawZ = map3d.getZoom();
              const z = rawZ >= 16.0 ? 16 : Math.min(18, Math.max(9, Math.round(rawZ)));
              map.setView([c.lat, c.lng], z, { animate: false });
            } catch (_) {}
          }
          ensureLeafletBaseTiles();
          renderAllMapLayers();
          setTimeout(() => {
            if (map && currentCameraDim === "2D") {
              map.invalidateSize({ pan: false, animate: false });
              render2DZoomedStreetTraffic();
            }
          }, 120);
        }
        updateCompassUI();
        return;
      }

      // Switching to 3D: verify live WebGL context (catches silent Safari CAMetalLayer eviction)
      if (!isMap3dGlAlive() && typeof maplibregl !== "undefined") {
        try {
          disposeAllThreeGpuResources();
          if (map3d) {
            try { map3d.remove(); } catch (_) {}
          }
          three3DLayer = null;
          map3d = null;
          map3dLoaded = false;
          map3dContextLost = false;
          const c3dEl = document.getElementById("map3dCanvas");
          if (c3dEl) c3dEl.innerHTML = "";
          init3DMap();
        } catch (err) {
          console.warn("3D WebGL unavailable; staying on 2D GIS canvas:", err);
        }
      }

      if (!isMap3dGlAlive()) {
        // Graceful fallback if WebGL is completely disabled in browser
        currentCameraDim = "2D";
        document.getElementById("btnDim2D")?.classList.add("active");
        document.getElementById("btnDim3D")?.classList.remove("active");
        if (stageEl) stageEl.classList.add("mode-2d-leaflet");
        ensureLeafletBaseTiles();
        if (map) map.invalidateSize({ pan: false, animate: false });
        return;
      }

      currentCameraDim = "3D";
      document.getElementById("btnDim2D")?.classList.remove("active");
      document.getElementById("btnDim3D")?.classList.add("active");
      if (stageEl) stageEl.classList.remove("mode-2d-leaflet");
      if (attrEl) attrEl.style.display = "flex";

      try {
        if (map) {
          const c2 = map.getCenter();
          const z2 = Math.min(18.5, Math.max(9.0, map.getZoom()));
          const c3 = map3d.getCenter();
          if (Math.hypot(c2.lat - c3.lat, c2.lng - c3.lng) > 0.002) {
            map3d.jumpTo({ center: [c2.lng, c2.lat], zoom: Math.max(z2, map3d.getZoom()) });
          }
        }
        if (map3d.getPitch() < 45) {
          map3d.easeTo({
            pitch: 58,
            bearing: 60,
            duration: 550
          });
        }
        syncPhotorealistic3DVisibility();
        if (map3dLoaded) {
          attachThree3DLayerIfReady();
          sync3DMapLayers();
          scheduleOsmCityRebuild(140);
        }
        forceMap3dRepaintBurst();
      } catch (_) {}
      updateCompassUI();
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

      function flyBothMaps(lat, lon, zoom, pitch = 58, bearing = 60) {
      const clampedZoom = Math.min(17.6, Math.max(9.0, zoom));
      if (map && currentCameraDim === "2D") {
        const z2 = clampedZoom >= 16.0 ? 16 : Math.min(18, Math.max(9, Math.round(clampedZoom)));
        const c2 = map.getCenter();
        const dist2 = Math.hypot(lat - c2.lat, lon - c2.lng);
        if (IS_SAFARI_WEBKIT || dist2 > 0.02) {
          try { map.stop(); } catch (_) {}
          map.setView([lat, lon], z2, { animate: false });
        } else {
          map.flyTo([lat, lon], z2, { duration: 0.75 });
        }
      }
      if (map3d && !map3dContextLost) {
        const isClose3D = clampedZoom >= 15.2 && currentCameraDim === "3D";
        const targetLon = isClose3D ? (lon + 0.00014) : lon;
        const targetLat = isClose3D ? (lat + 0.00004) : lat;
        const c3 = map3d.getCenter();
        const dist3 = Math.hypot(targetLat - c3.lat, targetLon - c3.lng);
        if (IS_SAFARI_WEBKIT || dist3 > 0.02 || currentCameraDim !== "3D") {
          map3d.jumpTo({
            center: [targetLon, targetLat],
            zoom: clampedZoom,
            pitch: currentCameraDim === "3D" ? pitch : 0,
            bearing: currentCameraDim === "3D" ? bearing : 0
          });
          if (currentCameraDim === "3D") {
            scheduleOsmCityRebuild(120);
            forceMap3dRepaintBurst();
          }
        } else {
          map3d.flyTo({
            center: [targetLon, targetLat],
            zoom: clampedZoom,
            pitch: currentCameraDim === "3D" ? pitch : 0,
            bearing: currentCameraDim === "3D" ? bearing : 0,
            duration: 1050,
            essential: true
          });
        }
      }
    }

    // =========================================================================
    // REAL UAE 4K SATELLITE + WHOLE-MAP OSM 3D CITY + 37 UNIQUE PROJECT MODELS
    // =========================================================================
    let three3DLayer = null;
    let osmCityRebuildTimer = null;

    const HAIO_EARTH_CIRC = 2 * Math.PI * 6371008.8;

    function haioProjectMerc(lon, lat) {
      return [
        (lon + 180) / 360,
        (1 - Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 180 / 2)) / Math.PI) / 2
      ];
    }

    function lonLatToOriginEnu(lon, lat, originLon, originLat) {
      const p0 = haioProjectMerc(originLon, originLat);
      const h0 = 1 / (HAIO_EARTH_CIRC * Math.cos((originLat * Math.PI) / 180));
      const p = haioProjectMerc(lon, lat);
      return [(p[0] - p0[0]) / h0, -(p[1] - p0[1]) / h0];
    }

    function expandEnuRing(pts, distM) {
      let cx = 0, cy = 0;
      const n = pts.length;
      for (const [x, y] of pts) {
        cx += x;
        cy += y;
      }
      cx /= Math.max(1, n);
      cy /= Math.max(1, n);
      let area2 = 0;
      for (let i = 0; i < n; i++) {
        const [x0, y0] = pts[i];
        const [x1, y1] = pts[(i + 1) % n];
        area2 += x0 * y1 - x1 * y0;
      }
      const effR = Math.max(2.0, Math.sqrt(Math.abs(area2 * 0.5) / Math.PI));
      const scale = Math.max(0.15, (effR + distM) / effR);
      return pts.map(([x, y]) => [cx + (x - cx) * scale, cy + (y - cy) * scale]);
    }

    function scaleEnuRing(pts, scaleFactor) {
      let cx = 0, cy = 0;
      const n = pts.length;
      for (const [x, y] of pts) {
        cx += x;
        cy += y;
      }
      cx /= Math.max(1, n);
      cy /= Math.max(1, n);
      return pts.map(([x, y]) => [cx + (x - cx) * scaleFactor, cy + (y - cy) * scaleFactor]);
    }

    function hexToRgb01(hexStr) {
      const c = new THREE.Color(hexStr);
      return [c.r, c.g, c.b];
    }

    // Generate articulated 2D architectural footprints in local ENU meters [x, y] rotated by rotRad
    function makeArchFootprint(shapeType, cx, cy, w, d, rotRad = 0) {
      const cosA = Math.cos(rotRad);
      const sinA = Math.sin(rotRad);
      const hw = w * 0.5;
      const hd = d * 0.5;
      let rawPts = [];

      if (shapeType === "chamfer_oct") {
        const cw = hw * 0.28;
        const cd = hd * 0.28;
        rawPts = [
          [-hw + cw, -hd], [hw - cw, -hd], [hw, -hd + cd], [hw, hd - cd],
          [hw - cw, hd], [-hw + cw, hd], [-hw, hd - cd], [-hw, -hd + cd]
        ];
      } else if (shapeType === "cruciform_spire") {
        const nw = hw * 0.46;
        const nd = hd * 0.46;
        rawPts = [
          [-nw, -hd], [nw, -hd], [nw, -nd], [hw, -nd],
          [hw, nd], [nw, nd], [nw, hd], [-nw, hd],
          [-nw, nd], [-hw, nd], [-hw, -nd], [-nw, -nd]
        ];
      } else if (shapeType === "stepped_wing") {
        const nw = hw * 0.36;
        const nd = hd * 0.32;
        rawPts = [
          [-hw, -hd], [nw, -hd], [nw, -hd + nd], [hw, -hd + nd],
          [hw, hd], [-nw, hd], [-nw, hd - nd], [-hw, hd - nd]
        ];
      } else if (shapeType === "l_courtyard") {
        const armW = hw * 0.15;
        const armD = hd * 0.15;
        rawPts = [
          [-hw, -hd], [hw, -hd], [hw, armD],
          [armW, armD], [armW, hd], [-hw, hd]
        ];
      } else if (shapeType === "u_boulevard") {
        const iw = hw * 0.45;
        const id = hd * 0.25;
        rawPts = [
          [-hw, -hd], [hw, -hd], [hw, hd], [iw, hd],
          [iw, -id], [-iw, -id], [-iw, hd], [-hw, hd]
        ];
      } else if (shapeType === "organic_oval") {
        const steps = 16;
        for (let i = 0; i < steps; i++) {
          const a = (i / steps) * Math.PI * 2;
          const rMod = 1.0 + 0.08 * Math.cos(3 * a);
          rawPts.push([Math.cos(a) * hw * rMod, Math.sin(a) * hd * rMod]);
        }
      } else {
        rawPts = [[-hw, -hd], [hw, -hd], [hw, hd], [-hw, hd]];
      }

      return rawPts.map(([lx, ly]) => [
        cx + lx * cosA - ly * sinA,
        cy + lx * sinA + ly * cosA
      ]);
    }

    // =========================================================================
    // HAIO.SG PBR ENVIRONMENT, PROCEDURAL ROOM/TIMBER TEXTURES & GLSL SHADERS
    // =========================================================================
    function createHaioRoomTextures() {
      const size = 256;
      const cMap = document.createElement("canvas");
      const cEm = document.createElement("canvas");
      cMap.width = cEm.width = size;
      cMap.height = cEm.height = size;
      const g = cMap.getContext("2d");
      const ge = cEm.getContext("2d");
      g.fillStyle = "#182430";
      g.fillRect(0, 0, size, size);
      ge.fillStyle = "#000000";
      ge.fillRect(0, 0, size, size);
      const cell = size / 4;
      let s = 42;
      const rnd = () => ((s = (1664525 * s + 1013904223) >>> 0) / 4294967296);
      const tones = ["#cfc6b6", "#bfb5a4", "#d6cec0", "#b3aa9b", "#c7beb0", "#dfd7c8"];
      for (let r = 0; r < 4; r++) {
        for (let c = 0; c < 4; c++) {
          const x = c * cell, y = r * cell, pad = 3, w = cell - pad * 2, h = cell - pad * 2;
          const tone = tones[(r * 4 + c) % tones.length];
          const lit = rnd() < 0.34;
          const grd = g.createLinearGradient(x, y + pad, x, y + pad + h);
          grd.addColorStop(0, "#5c574f");
          grd.addColorStop(0.24, tone);
          grd.addColorStop(0.76, "#8d8477");
          grd.addColorStop(1, "#48423b");
          g.fillStyle = grd;
          g.fillRect(x + pad, y + pad, w, h);
          g.fillStyle = "rgba(0,0,0,0.22)";
          g.fillRect(x + pad, y + pad, 6, h);
          g.fillRect(x + pad + w - 6, y + pad, 6, h);
          if (rnd() < 0.45) {
            const bw = w * (0.26 + 0.25 * rnd());
            g.fillStyle = "rgba(236,230,218,0.68)";
            g.fillRect(x + pad + 2, y + pad + 2, bw, h * 0.82);
          }
          const skyG = g.createLinearGradient(x, y + pad, x, y + pad + h);
          skyG.addColorStop(0, "rgba(170,206,235,0.44)");
          skyG.addColorStop(0.45, "rgba(115,155,186,0.18)");
          skyG.addColorStop(1, "rgba(38,56,72,0.26)");
          g.fillStyle = skyG;
          g.fillRect(x + pad, y + pad, w, h);
          if (lit) {
            const eg = ge.createRadialGradient(x + cell * 0.5, y + cell * 0.38, 2, x + cell * 0.5, y + cell * 0.5, cell * 0.52);
            const warm = rnd() < 0.65 ? "#ffdca0" : "#ffe9be";
            eg.addColorStop(0, warm);
            eg.addColorStop(0.65, "rgba(255,198,118,0.48)");
            eg.addColorStop(1, "rgba(0,0,0,0)");
            ge.fillStyle = eg;
            ge.fillRect(x + pad, y + pad, w, h);
          }
          g.strokeStyle = "#222a32";
          g.lineWidth = 2;
          g.strokeRect(x + pad, y + pad, w, h);
          g.fillStyle = "rgba(30,38,46,0.75)";
          g.fillRect(x + cell * 0.5 - 1, y + pad, 2, h);
        }
      }
      const wrap = (cv) => {
        const t = new THREE.CanvasTexture(cv);
        t.wrapS = THREE.RepeatWrapping;
        t.wrapT = THREE.RepeatWrapping;
        t.needsUpdate = true;
        return t;
      };
      return { map: wrap(cMap), emissiveMap: wrap(cEm) };
    }

    function createHaioTimberTexture() {
      const cv = document.createElement("canvas");
      cv.width = 128; cv.height = 128;
      const g = cv.getContext("2d");
      g.fillStyle = "#9c6b43";
      g.fillRect(0, 0, 128, 128);
      for (let i = 0; i < 16; i++) {
        const y = i * 8;
        g.fillStyle = (i % 2 === 0) ? "#a77449" : "#91613b";
        g.fillRect(0, y, 128, 7);
        g.fillStyle = "#5c3b21";
        g.fillRect(0, y + 7, 128, 1);
      }
      const t = new THREE.CanvasTexture(cv);
      t.wrapS = THREE.RepeatWrapping;
      t.wrapT = THREE.RepeatWrapping;
      t.needsUpdate = true;
      return t;
    }

    function ensureHaioEnvironmentAndLights(inRenderPass = false) {
      if (!three3DLayer || !three3DLayer.scene || !three3DLayer.renderer) return;
      if (!three3DLayer.lightsInitialized) {
        three3DLayer.lightsInitialized = true;

        const hemi = new THREE.HemisphereLight(0xf2f6fb, 0x7a7062, IS_SAFARI_WEBKIT ? 0.72 : 0.56);
        hemi.position.set(0, 0, 1);
        three3DLayer.scene.add(hemi);

        const sun = new THREE.DirectionalLight(0xfff5e8, IS_SAFARI_WEBKIT ? 0.94 : 0.86);
        sun.position.set(165, -145, 260);
        three3DLayer.scene.add(sun);

        const fill = new THREE.DirectionalLight(0xcfe2ff, IS_SAFARI_WEBKIT ? 0.36 : 0.28);
        fill.position.set(-140, 120, 150);
        three3DLayer.scene.add(fill);
      }

      // Never allocate offscreen PMREM float render targets outside render() or on Safari/WebKit (prevents shared WebGL FBO corruption & GPU memory eviction)
      if (!inRenderPass || IS_SAFARI_WEBKIT || three3DLayer.envInitialized) return;
      three3DLayer.envInitialized = true;

      try {
        if (typeof THREE.PMREMGenerator !== "undefined") {
          const pmrem = new THREE.PMREMGenerator(three3DLayer.renderer);
          const envScene = new THREE.Scene();
          const skyGeo = new THREE.SphereGeometry(80, 24, 16);
          const pos = skyGeo.attributes.position;
          const cols = new Float32Array(pos.count * 3);
          const cTop = new THREE.Color(0x6fa6d9);
          const cHor = new THREE.Color(0xeae2d3);
          const cBot = new THREE.Color(0x5b554c);
          const tmp = new THREE.Color();
          for (let i = 0; i < pos.count; i++) {
            const y = pos.getY(i) / 80;
            tmp.copy(y >= 0 ? cHor : cBot).lerp(y >= 0 ? cTop : cHor, Math.pow(Math.abs(y), 0.65));
            cols[i * 3] = tmp.r;
            cols[i * 3 + 1] = tmp.g;
            cols[i * 3 + 2] = tmp.b;
          }
          skyGeo.setAttribute("color", new THREE.BufferAttribute(cols, 3));
          envScene.add(new THREE.Mesh(skyGeo, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide })));
          const sunDisc = new THREE.Mesh(new THREE.SphereGeometry(6, 12, 12), new THREE.MeshBasicMaterial({ color: 0xfff6e0 }));
          sunDisc.position.set(38, 42, -32);
          envScene.add(sunDisc);
          const envRT = pmrem.fromScene(envScene, 0.03);
          three3DLayer.scene.environment = envRT.texture;
          three3DLayer.envRT = envRT;
          skyGeo.dispose();
          pmrem.dispose();
          three3DLayer.renderer.resetState();
        }
      } catch (err) {
        // Fallback if PMREMGenerator is unavailable
      }
    }

    // Build haio.sg's Exact Metric GLSL Architectural Facade Shader Material (hdb-facade-v25 + sun-window-glazing-v1)
    function createCityFacadeMaterials() {
      const S = 512;
      const cv = document.createElement("canvas");
      const ce = document.createElement("canvas");
      cv.width = ce.width = S;
      cv.height = ce.height = S;
      const g = cv.getContext("2d");
      const ge = ce.getContext("2d");

      g.fillStyle = "rgb(245,239,227)";
      g.fillRect(0, 0, S, S);
      ge.fillStyle = "#000";
      ge.fillRect(0, 0, S, S);

      for (let r = 0; r < 8; r++) {
        const y0 = r * 64;
        g.fillStyle = "rgba(0,0,0,0.12)";
        g.fillRect(0, y0 + 62, S, 2);
        g.fillStyle = "rgba(255,255,255,0.22)";
        g.fillRect(0, y0, S, 2);
        for (let c = 0; c < 4; c++) {
          const x0 = c * 128 + 14;
          const wy = y0 + 11, ww = 100, wh = 38;
          g.fillStyle = "rgba(0,0,0,0.24)";
          g.fillRect(x0 - 2, wy - 2, ww + 4, wh + 4);
          const grd = g.createLinearGradient(0, wy, 0, wy + wh);
          grd.addColorStop(0, "rgb(56,78,96)");
          grd.addColorStop(0.55, "rgb(34,50,64)");
          grd.addColorStop(1, "rgb(22,34,44)");
          g.fillStyle = grd;
          g.fillRect(x0, wy, ww, wh);
          g.fillStyle = "rgba(195,222,242,0.22)";
          g.fillRect(x0 + 2, wy + 2, ww - 4, 11);
          g.fillStyle = "rgb(218,214,206)";
          for (let p = 1; p < 4; p++) g.fillRect(x0 + p * 25 - 1, wy, 2, wh);
          if (((r * 7 + c * 13) % 5) === 0) {
            ge.fillStyle = "#ffdfa0";
            ge.fillRect(x0 + 2, wy + 2, ww - 4, wh - 4);
          }
        }
      }

      const tx = new THREE.CanvasTexture(cv);
      tx.wrapS = tx.wrapT = THREE.RepeatWrapping;
      tx.anisotropy = 8;
      tx.needsUpdate = true;

      const te = new THREE.CanvasTexture(ce);
      te.wrapS = te.wrapT = THREE.RepeatWrapping;
      te.needsUpdate = true;

      const mat = new THREE.MeshLambertMaterial({
        color: 0xffffff,
        vertexColors: true,
        map: tx,
        emissive: 0xffffff,
        emissiveMap: te,
        emissiveIntensity: 0.22,
        side: THREE.DoubleSide,
        polygonOffset: true,
        polygonOffsetFactor: 1,
        polygonOffsetUnits: 1
      });
      mat.extensions = { derivatives: true };
      mat.customProgramCacheKey = () => "haio-hdb-facade-v25-dubai";

      mat.onBeforeCompile = (sh) => {
        sh.vertexShader = sh.vertexShader
          .replace(
            "#include <common>",
            `#include <common>
            attribute vec4 hdbBand;
            attribute vec4 hdbWall;
            varying float vHdbZ;
            varying vec4 vHdbBand;
            varying vec4 vHdbWall;`
          )
          .replace(
            "#include <begin_vertex>",
            `#include <begin_vertex>
            vHdbZ = position.z;
            vHdbBand = hdbBand;
            vHdbWall = hdbWall;`
          );

        sh.fragmentShader = sh.fragmentShader
          .replace(
            "#include <common>",
            `#include <common>
            varying float vHdbZ;
            varying vec4 vHdbBand;
            varying vec4 vHdbWall;
            float hdbCov(float x, float a, float b, float p) {
              return clamp((min(x + 0.5 * p, b) - max(x - 0.5 * p, a)) / p, 0.0, 1.0);
            }`
          )
          .replace(
            "#include <color_fragment>",
            `#include <color_fragment>
            if (vHdbBand.w > 0.5) {
              float z = vHdbZ;
              float top = vHdbBand.w;
              float dTop = top - z;
              float scheme = floor(vHdbWall.w + 0.5);
              vec3 bandCol = vHdbBand.rgb;
              vec3 baseCol = diffuseColor.rgb;
              float upz = max(fwidth(z), 1e-4);
              float upu = max(fwidth(vHdbWall.x), 1e-4);

              if (scheme >= 99.5 && scheme < 200.0) {
                float cvar = clamp(scheme - 100.0, 0.0, 14.0);
                float cfh = (cvar == 2.0 || cvar == 7.0 || cvar == 12.0) ? 3.5 : 3.3;
                float cmod = (cvar == 1.0 || cvar == 6.0 || cvar == 11.0) ? 6.0 : ((cvar == 3.0 || cvar == 8.0 || cvar == 13.0) ? 8.0 : 7.0);
                float cu = vHdbWall.x;
                float clen = vHdbWall.y;
                float cz = max(z, 0.0);
                float cfz = mod(cz, cfh);
                float clevel = floor(cz / cfh);
                float topFloors = floor(top / cfh);
                vec3 stone = clamp(baseCol * 1.04 + vec3(0.03, 0.025, 0.015), 0.0, 1.0);
                vec3 copper = bandCol;
                vec3 inner = vec3(0.11, 0.17, 0.23);
                vec3 skyHi = vec3(0.36, 0.54, 0.68);
                vec3 balus = vec3(0.58, 0.74, 0.82);
                vec3 slabCol = clamp(stone * 1.07, 0.0, 1.0);

                if (clen < 4.5) {
                  float gMix = clamp(cz / max(top, 30.0), 0.0, 1.0);
                  vec3 col = mix(inner, skyHi, 0.34 + 0.36 * gMix);
                  float vMul = hdbCov(mod(cu, 1.5), 0.0, 0.07, upu);
                  float hSlab = hdbCov(cfz, 0.0, 0.22, upz);
                  col = mix(col, stone * 0.75, vMul * 0.7);
                  col = mix(col, slabCol, hSlab);
                  diffuseColor.rgb = col;
                } else {
                  float mods = max(1.0, floor(clen / cmod + 0.5));
                  float mlen = clen / mods;
                  float mu = mod(cu, mlen);
                  float bayIdx = floor(cu / mlen);
                  float pierW = 0.65;
                  float finW = 0.32;
                  float inPier = max(hdbCov(mu, 0.0, pierW, upu), hdbCov(mu, mlen - pierW, mlen, upu));
                  float inFin = max(hdbCov(mu, pierW, pierW + finW, upu), hdbCov(mu, mlen - pierW - finW, mlen - pierW, upu));
                  float inBay = clamp(1.0 - inPier - inFin, 0.0, 1.0);
                  float skyTer = 0.0;
                  if (top > 40.0 && clevel > 2.5 && dTop > cfh * 3.0) {
                    float every = (cvar < 5.0) ? 11.0 : ((cvar < 10.0) ? 13.0 : 10.0);
                    if (mod(clevel, every) == every - 1.0) skyTer = 1.0;
                  }
                  float isCrown = (dTop < cfh * 2.1 && mod(bayIdx, 2.0) < 0.5) ? 1.0 : 0.0;
                  float slab = hdbCov(cfz, 0.0, 0.24, upz);
                  float rail = hdbCov(cfz, 0.24, 1.15, upz);
                  float railBar = hdbCov(cfz, 1.10, 1.18, upz);
                  float soffit = hdbCov(cfz, cfh - 0.34, cfh, upz);
                  float gMix = clamp(cfz / cfh, 0.0, 1.0);
                  float hVar = fract(sin(clevel * 17.3 + bayIdx * 31.7) * 43758.5);
                  vec3 glassCol = mix(inner, skyHi, 0.22 + 0.35 * gMix + 0.14 * hVar);
                  float mStep = (mlen - 2.0 * (pierW + finW)) / 3.0;
                  float bu = mu - (pierW + finW);
                  float mul = hdbCov(mod(max(bu, 0.0), max(mStep, 0.8)), 0.0, 0.07, upu);
                  glassCol = mix(glassCol, vec3(0.06, 0.08, 0.10), mul * 0.85);
                  vec3 bayCol = glassCol;
                  bayCol = mix(bayCol, balus * (0.85 + 0.15 * gMix), rail * 0.65);
                  bayCol = mix(bayCol, slabCol * 0.92, railBar * 0.85);
                  bayCol *= (1.0 - 0.30 * soffit);
                  bayCol = mix(bayCol, slabCol, slab);
                  if (skyTer > 0.5) {
                    vec3 terBack = vec3(0.14, 0.16, 0.15) * (0.72 + 0.28 * gMix);
                    float greenBand = hdbCov(cfz, 0.24, 1.05, upz);
                    vec3 shrub = mix(vec3(0.16, 0.31, 0.14), vec3(0.24, 0.42, 0.19), fract(sin(cu * 2.3) * 19.7));
                    terBack = mix(terBack, shrub, greenBand * 0.9);
                    bayCol = mix(terBack, slabCol, slab);
                  }
                  if (isCrown > 0.5) {
                    float frame = max(hdbCov(cfz, cfh - 0.38, cfh, upz), hdbCov(bu, 0.0, 0.35, upu));
                    vec3 skyVoid = vec3(0.55, 0.66, 0.76);
                    bayCol = mix(skyVoid, copper * 1.06, frame);
                  }
                  vec3 finCol = copper * (0.88 + 0.12 * cos(cfz * 3.14159 / cfh));
                  finCol = mix(finCol, slabCol, slab * 0.55);
                  float pJoint = hdbCov(cfz, 0.0, 0.10, upz);
                  vec3 pierCol = stone * (1.0 - 0.12 * pJoint);
                  vec3 col = pierCol * inPier + finCol * inFin + bayCol * inBay;
                  if (cz < 3.6) {
                    float inLobby = hdbCov(cu, clen * 0.25, clen * 0.75, upu) * (1.0 - inPier);
                    vec3 lobbyGlass = mix(vec3(0.14, 0.18, 0.22), vec3(0.88, 0.72, 0.46), 0.58);
                    float canopy = hdbCov(cz, 2.85, 3.35, upz);
                    lobbyGlass = mix(lobbyGlass, copper * 0.85, canopy);
                    col = mix(col, lobbyGlass, inLobby * 0.88);
                  }
                  if (dTop < 1.3) {
                    float rim = hdbCov(dTop, 0.0, 0.45, upz);
                    col = mix(copper * 0.92, slabCol, rim);
                  }
                  diffuseColor.rgb = col;
                }
              } else if (scheme >= 799.5 && scheme < 900.0) {
                float ostyle = clamp(scheme - 800.0, 0.0, 2.0);
                float ofh = 3.8;
                float ou = vHdbWall.x;
                float olen = vHdbWall.y;
                float oz = max(z, 0.0);
                float ofz = mod(oz, ofh);
                float olevel = floor(oz / ofh);
                vec3 spandrel = baseCol;
                vec3 accent = bandCol;
                float hTone = fract(sin(olevel * 19.7 + floor(ou / 1.5) * 43.1) * 43758.5);
                float gGrad = clamp(oz / max(top, 60.0), 0.0, 1.0);
                vec3 col = spandrel;
                if (ostyle < 0.5) {
                  float sp = hdbCov(ofz, 0.0, 1.15, upz);
                  float sill = hdbCov(ofz, 1.12, 1.24, upz);
                  float head = hdbCov(ofz, ofh - 0.18, ofh, upz);
                  vec3 glass = mix(vec3(0.12, 0.21, 0.28), vec3(0.36, 0.53, 0.66), 0.35 + 0.45 * gGrad + 0.15 * hTone);
                  float mul = hdbCov(mod(ou, 1.5), 0.0, 0.07, upu);
                  float pier = (olen > 12.0) ? hdbCov(mod(ou, 9.0), 0.0, 0.55, upu) : 0.0;
                  glass = mix(glass, accent * 0.75, mul * 0.85);
                  col = mix(glass, spandrel, max(sp, head));
                  col = mix(col, spandrel * 0.72, sill);
                  col = mix(col, spandrel * 0.96, pier);
                } else if (ostyle < 1.5) {
                  vec3 gLow = spandrel * 0.55;
                  vec3 gHigh = mix(accent, vec3(0.62, 0.78, 0.88), 0.55);
                  vec3 glass = mix(gLow, gHigh, 0.25 + 0.55 * gGrad + 0.18 * hTone);
                  float sp = hdbCov(ofz, 0.0, 0.55, upz);
                  float shadowLine = hdbCov(ofz, 0.52, 0.62, upz);
                  float mul = hdbCov(mod(ou, 1.5), 0.0, 0.06, upu);
                  float trans = hdbCov(ofz, 2.55, 2.63, upz);
                  col = mix(glass, spandrel * 0.38, sp * 0.85);
                  col = mix(col, vec3(0.05, 0.08, 0.11), shadowLine * 0.9);
                  col = mix(col, accent, max(mul * 0.75, trans * 0.55));
                } else {
                  vec3 glass = mix(vec3(0.09, 0.13, 0.18), vec3(0.28, 0.38, 0.48), 0.30 + 0.45 * gGrad + 0.18 * hTone);
                  float sp = hdbCov(ofz, 0.0, 0.48, upz);
                  float fin = hdbCov(mod(ou, 1.5), 0.0, 0.22, upu);
                  float finShadow = hdbCov(mod(ou, 1.5), 0.22, 0.36, upu);
                  col = mix(glass, spandrel * 0.45, sp);
                  col *= (1.0 - 0.28 * finShadow);
                  col = mix(col, accent, fin * 0.92);
                }
                if (oz < 5.6 && olen > 8.0) {
                  float inEntry = hdbCov(ou, olen * 0.22, olen * 0.78, upu);
                  vec3 lobby = mix(vec3(0.14, 0.18, 0.22), vec3(0.92, 0.78, 0.54), 0.55);
                  float mull = hdbCov(mod(ou, 2.0), 0.0, 0.09, upu);
                  lobby = mix(lobby, accent * 0.7, mull);
                  float canopy = hdbCov(oz, 4.9, 5.5, upz);
                  lobby = mix(lobby, accent * 1.05, canopy);
                  col = mix(col, lobby, inEntry * 0.9);
                }
                if (dTop < 2.2) {
                  float cap = hdbCov(dTop, 0.0, 0.55, upz);
                  float louvre = hdbCov(mod(z, 0.35), 0.0, 0.16, upz);
                  vec3 crownCol = mix(spandrel * 0.65, accent, louvre * 0.7);
                  col = mix(crownCol, accent * 1.08, cap);
                }
                diffuseColor.rgb = col;
              } else if (scheme >= 1199.5 && scheme < 1300.0) {
                float hstyle = clamp(scheme - 1200.0, 0.0, 1.0);
                float hfh = 3.3;
                float hu = vHdbWall.x;
                float hlen = vHdbWall.y;
                float hz = max(z, 0.0);
                float hfz = mod(hz, hfh);
                float hlevel = floor(hz / hfh);
                float gGrad = clamp(hz / max(top, 45.0), 0.0, 1.0);
                float hTone = fract(sin(hlevel * 23.1 + floor(hu / 3.6) * 17.9) * 43758.5);
                vec3 col = baseCol;
                if (hstyle < 0.5) {
                  vec3 glass = mix(vec3(0.12, 0.22, 0.32), vec3(0.45, 0.64, 0.78), 0.3 + 0.5 * gGrad + 0.15 * hTone);
                  float sp = hdbCov(hfz, 0.0, 0.52, upz);
                  float mul = hdbCov(mod(hu, 1.8), 0.0, 0.07, upu);
                  col = mix(glass, baseCol * 0.42, sp * 0.85);
                  col = mix(col, bandCol, mul * 0.75);
                } else {
                  float bayMod = 4.0;
                  float bu = mod(hu, bayMod);
                  float pier = max(hdbCov(bu, 0.0, 0.42, upu), hdbCov(bu, bayMod - 0.42, bayMod, upu));
                  float slab = hdbCov(hfz, 0.0, 0.28, upz);
                  float rail = hdbCov(hfz, 0.28, 1.10, upz);
                  vec3 recess = mix(vec3(0.11, 0.15, 0.19), vec3(0.32, 0.44, 0.54), 0.35 + 0.4 * gGrad + 0.2 * hTone);
                  vec3 balCol = mix(recess, bandCol * 0.55, rail * 0.78);
                  balCol = mix(balCol, baseCol * 1.04, slab);
                  col = mix(balCol, baseCol, pier);
                }
                if (hz < 5.0 && hlen > 8.0) {
                  float inLobby = hdbCov(hu, hlen * 0.2, hlen * 0.8, upu);
                  vec3 lobby = mix(vec3(0.18, 0.16, 0.14), vec3(0.95, 0.80, 0.52), 0.65);
                  float canopy = hdbCov(hz, 4.3, 4.9, upz);
                  lobby = mix(lobby, bandCol * 1.05, canopy);
                  col = mix(col, lobby, inLobby * 0.9);
                }
                diffuseColor.rgb = col;
              } else if (scheme >= 299.5 && scheme < 400.0) {
                float mstyle = clamp(scheme - 300.0, 0.0, 2.0);
                float mu = vHdbWall.x;
                float mlen = vHdbWall.y;
                float mz = max(z, 0.0);
                vec3 col = baseCol;
                float sBay = 6.0;
                float su = mod(mu, sBay);
                float sIdx = floor(mu / sBay);
                float sHash = fract(sin(sIdx * 37.3 + mlen * 1.9) * 43758.5);
                if (mstyle < 0.5) {
                  vec3 panelBase = vec3(0.76, 0.73, 0.68);
                  vec3 podWhite = vec3(0.93, 0.92, 0.89);
                  if (mz < 4.5) {
                    float colPillar = hdbCov(su, 0.0, 0.7, upu);
                    vec3 shopG = mix(vec3(0.16, 0.18, 0.20), vec3(0.95, 0.82, 0.56), 0.55 + 0.25 * sHash);
                    col = mix(shopG, podWhite, colPillar);
                  } else {
                    float d1 = mod(mu * 0.7 + mz * 1.1, 7.5);
                    float d2 = mod(mu * 0.7 - mz * 1.1 + 40.0, 7.5);
                    float seam = max(hdbCov(d1, 0.0, 0.18, upu + upz), hdbCov(d2, 0.0, 0.18, upu + upz));
                    float fIdx = floor((mu * 0.7 + mz * 1.1) / 7.5) + floor((mu * 0.7 - mz * 1.1 + 40.0) / 7.5) * 7.0;
                    float fShade = 0.88 + 0.20 * fract(sin(fIdx * 19.1) * 43758.5);
                    col = mix(panelBase * fShade, vec3(0.28, 0.27, 0.25), seam * 0.85);
                  }
                } else {
                  vec3 stone = baseCol;
                  float course = hdbCov(mod(mz, 1.2), 0.0, 0.07, upz);
                  float vJoint = hdbCov(mod(mu, 3.0), 0.0, 0.07, upu);
                  col = stone * (1.0 - 0.10 * max(course, vJoint));
                  float inCurtain = max(hdbCov(mu, 0.0, mlen * 0.28, upu), hdbCov(mu, mlen * 0.72, mlen, upu));
                  vec3 cGlass = mix(vec3(0.14, 0.24, 0.30), vec3(0.46, 0.64, 0.74), clamp(mz / max(top, 20.0), 0.0, 1.0));
                  float cMul = max(hdbCov(mod(mu, 1.5), 0.0, 0.07, upu), hdbCov(mod(mz, 3.6), 0.0, 0.14, upz));
                  cGlass = mix(cGlass, vec3(0.75, 0.76, 0.78), cMul * 0.8);
                  col = mix(col, cGlass, inCurtain);
                }
                if (dTop < 0.7) col = mix(col, vec3(0.88, 0.86, 0.82), hdbCov(dTop, 0.0, 0.5, upz));
                diffuseColor.rgb = col;
              } else if (scheme >= 609.5 && scheme < 700.0) {
                float lfh = 3.4;
                float lu = vHdbWall.x;
                float llen = vHdbWall.y;
                float lz = max(z, 0.0);
                float lfz = mod(lz, lfh);
                float llevel = floor(lz / lfh);
                vec3 wallCol = baseCol;
                vec3 frameCol = vec3(0.16, 0.17, 0.18);
                vec3 glassDark = vec3(0.12, 0.19, 0.24);
                vec3 glassSky = vec3(0.36, 0.50, 0.60);
                vec3 col = wallCol;
                float slab = hdbCov(lfz, 0.0, 0.24, upz);
                col = mix(col, wallCol * 0.84, slab);
                if (llen >= 4.0) {
                  float margin = min(1.1, llen * 0.16);
                  float inOpen = hdbCov(lu, margin, llen - margin, upu);
                  float inH = hdbCov(lfz, 0.28, lfh - 0.34, upz);
                  float gMix = clamp(lfz / lfh, 0.0, 1.0);
                  vec3 gCol = mix(glassDark, glassSky, 0.25 + 0.45 * gMix);
                  float mul = hdbCov(mod(lu - margin, 1.6), 0.0, 0.07, upu);
                  gCol = mix(gCol, frameCol, mul * 0.9);
                  if (llevel >= 0.5) {
                    float bal = hdbCov(lfz, 0.24, 1.05, upz);
                    gCol = mix(gCol, vec3(0.55, 0.70, 0.78), bal * 0.55);
                  }
                  col = mix(col, gCol, inOpen * inH);
                }
                diffuseColor.rgb = col;
              }
            }`
          )
          .replace(
            "#include <emissivemap_fragment>",
            `#ifdef USE_EMISSIVEMAP
              vec4 emissiveColor = texture2D(emissiveMap, vEmissiveMapUv);
              float isWin = step(0.12, diffuseColor.b - diffuseColor.r * 0.82);
              vec3 nDir = normalize(vNormal);
              vec3 vDir = normalize(vViewPosition);
              float fres = pow(1.0 - abs(dot(nDir, vDir)), 3.5);
              diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.76, 0.88, 0.98), isWin * (0.16 + 0.32 * fres));
              totalEmissiveRadiance *= emissiveColor.rgb * isWin;
            #endif`
          );
      };

      return [mat];
    }

    // Phase 12: Complete WebGL GPU Resource Cleanup (Geometries, Materials, Procedural CanvasTextures & RenderLists)
    function disposeThreeGroup(grp, disposeMaterials = false) {
      if (!grp) return;
      grp.traverse((obj) => {
        if (obj.geometry && typeof obj.geometry.dispose === "function") {
          obj.geometry.dispose();
        }
        if (disposeMaterials && obj.material) {
          const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
          mats.forEach(m => {
            if (!m) return;
            if (m.map && typeof m.map.dispose === "function") m.map.dispose();
            if (m.emissiveMap && typeof m.emissiveMap.dispose === "function") m.emissiveMap.dispose();
            if (typeof m.dispose === "function") m.dispose();
          });
        }
      });
    }

    function disposeAllThreeGpuResources() {
      if (!three3DLayer) return;
      if (three3DLayer.heroGroup) {
        disposeThreeGroup(three3DLayer.heroGroup, true);
        if (three3DLayer.scene) three3DLayer.scene.remove(three3DLayer.heroGroup);
        three3DLayer.heroGroup = null;
      }
      if (three3DLayer.osmCityGroup) {
        disposeThreeGroup(three3DLayer.osmCityGroup, false);
        if (three3DLayer.scene) three3DLayer.scene.remove(three3DLayer.osmCityGroup);
        three3DLayer.osmCityGroup = null;
      }
      if (Array.isArray(three3DLayer.cityFacadeMats)) {
        three3DLayer.cityFacadeMats.forEach(m => {
          if (!m) return;
          if (m.map && typeof m.map.dispose === "function") m.map.dispose();
          if (m.emissiveMap && typeof m.emissiveMap.dispose === "function") m.emissiveMap.dispose();
          if (typeof m.dispose === "function") m.dispose();
        });
        three3DLayer.cityFacadeMats = null;
      }
      if (three3DLayer.cityRoofMat && typeof three3DLayer.cityRoofMat.dispose === "function") {
        three3DLayer.cityRoofMat.dispose();
        three3DLayer.cityRoofMat = null;
      }
      if (three3DLayer.sharedRoomTex) {
        if (three3DLayer.sharedRoomTex.map) three3DLayer.sharedRoomTex.map.dispose();
        if (three3DLayer.sharedRoomTex.emissiveMap) three3DLayer.sharedRoomTex.emissiveMap.dispose();
        three3DLayer.sharedRoomTex = null;
      }
      if (three3DLayer.sharedTimberTex) {
        three3DLayer.sharedTimberTex.dispose();
        three3DLayer.sharedTimberTex = null;
      }
      if (three3DLayer.envRT) {
        three3DLayer.envRT.dispose();
        three3DLayer.envRT = null;
      }
      if (three3DLayer.renderer && three3DLayer.renderer.renderLists && typeof three3DLayer.renderer.renderLists.dispose === "function") {
        three3DLayer.renderer.renderLists.dispose();
      }
    }

    // Rebuilds the Unique 14-Layer PBR 3D Architectural Complex for the Selected UAE Project (haio.sg Engine)
    function rebuildThreeHeroScene() {
      if (!three3DLayer || !three3DLayer.scene || typeof THREE === "undefined") return;
      ensureHaioEnvironmentAndLights();

      let p = DATA.projects.find(x => x.project_id === selected3DProjectId);
      let lat = 25.1850, lon = 55.2650;
      let cleanTitle = "Burj Binghatti Jacob & Co";

      if (p) {
        [lat, lon] = parseCoord(p.coordinates);
        cleanTitle = p.project_name.split("(")[0].trim();
      } else {
        const sd = DATA.subdevs.find(x => x.subdev_id === selected3DProjectId);
        if (sd) {
          p = sd;
          lat = sd.latitude;
          lon = sd.longitude;
          cleanTitle = sd.development_name.split(",")[0].trim();
        } else {
          p = DATA.projects[0];
          [lat, lon] = parseCoord(p.coordinates);
          cleanTitle = p.project_name.split("(")[0].trim();
        }
      }

      const spec = getProject3DSpec(p);
      const prevOrigin = three3DLayer.originLonLat || [0, 0];
      const originChanged = Math.hypot(lon - prevOrigin[0], lat - prevOrigin[1]) > 1e-5;
      three3DLayer.originLonLat = [lon, lat];
      // Exclude OSM footprints strictly inside the 106m × 88m hero parcel plinth so adjacent city towers remain 100% intact
      three3DLayer.heroExcludeRadiusM = 56.0;

      const calloutTxtEl = document.getElementById("hero3DRoofCalloutText");
      if (calloutTxtEl) {
        const shortLbl = cleanTitle.length > 24 ? cleanTitle.slice(0, 22).trim() + "…" : cleanTitle;
        if (active3DBlock !== "ALL") {
          const selB = spec.blocks.find(b => b.id === active3DBlock) || spec.blocks[0];
          calloutTxtEl.textContent = `${selB.label} · ${selB.storeys} storeys (${selB.heightM}m)`;
        } else {
          calloutTxtEl.textContent = `${shortLbl} · ${spec.storeys}F (${spec.heightM}m)`;
        }
      }

      if (three3DLayer.heroGroup) {
        disposeThreeGroup(three3DLayer.heroGroup, false);
        three3DLayer.scene.remove(three3DLayer.heroGroup);
      }

      if (!three3DLayer.sharedRoomTex) three3DLayer.sharedRoomTex = createHaioRoomTextures();
      if (!three3DLayer.sharedTimberTex) three3DLayer.sharedTimberTex = createHaioTimberTexture();
      if (!three3DLayer.cityFacadeMats) three3DLayer.cityFacadeMats = createCityFacadeMaterials();

      const pal = spec.palette;
      const mats = {
        glass: new THREE.MeshStandardMaterial({
          color: 0x486e8e,
          map: three3DLayer.sharedRoomTex.map,
          emissive: 0xffd89b,
          emissiveMap: three3DLayer.sharedRoomTex.emissiveMap,
          emissiveIntensity: 0.42,
          metalness: 0.26,
          roughness: 0.10,
          envMapIntensity: 1.55,
          side: THREE.DoubleSide
        }),
        slab: new THREE.MeshStandardMaterial({ color: pal.ledge, metalness: 0.08, roughness: 0.46, side: THREE.DoubleSide }),
        frame: new THREE.MeshStandardMaterial({ color: pal.frame, metalness: 0.58, roughness: 0.30, side: THREE.DoubleSide }),
        fin: new THREE.MeshStandardMaterial({ color: pal.fin, metalness: 0.64, roughness: 0.26, envMapIntensity: 1.35, side: THREE.DoubleSide }),
        crown: new THREE.MeshStandardMaterial({ color: pal.crown, metalness: 0.68, roughness: 0.24, envMapIntensity: 1.45, side: THREE.DoubleSide }),
        crownGlass: new THREE.MeshStandardMaterial({ color: pal.glass, metalness: 0.25, roughness: 0.08, transparent: true, opacity: 0.72, side: THREE.DoubleSide }),
        rail: new THREE.MeshStandardMaterial({ color: 0x9cc5db, metalness: 0.14, roughness: 0.08, transparent: true, opacity: 0.50, side: THREE.DoubleSide }),
        solid: new THREE.MeshStandardMaterial({ color: pal.solid, metalness: 0.04, roughness: 0.72, side: THREE.DoubleSide }),
        podium: new THREE.MeshStandardMaterial({ color: pal.podium, metalness: 0.08, roughness: 0.65, side: THREE.DoubleSide }),
        timber: new THREE.MeshStandardMaterial({ color: 0xffffff, map: three3DLayer.sharedTimberTex, metalness: 0.05, roughness: 0.62, side: THREE.DoubleSide }),
        amenityGlass: new THREE.MeshStandardMaterial({ color: 0x243848, emissive: 0xffd28e, emissiveIntensity: 0.28, metalness: 0.18, roughness: 0.12, side: THREE.DoubleSide }),
        darkroof: new THREE.MeshStandardMaterial({ color: 0x26292e, metalness: 0.32, roughness: 0.48, side: THREE.DoubleSide }),
        garden: new THREE.MeshStandardMaterial({ color: 0xffffff, map: three3DLayer.sharedTimberTex, metalness: 0.04, roughness: 0.70, side: THREE.DoubleSide }),
        green: new THREE.MeshStandardMaterial({ color: 0x3b6e38, metalness: 0.0, roughness: 0.92, side: THREE.DoubleSide }),
        lawn: new THREE.MeshStandardMaterial({ color: 0x467c42, metalness: 0.0, roughness: 0.95, side: THREE.DoubleSide }),
        pool: new THREE.MeshStandardMaterial({ color: 0x22b8cf, metalness: 0.12, roughness: 0.08, envMapIntensity: 1.4, side: THREE.DoubleSide }),
        deck: new THREE.MeshStandardMaterial({ color: 0xd8cfc2, metalness: 0.04, roughness: 0.78, side: THREE.DoubleSide }),
        driveway: new THREE.MeshStandardMaterial({ color: 0x4a4e54, metalness: 0.04, roughness: 0.86, side: THREE.DoubleSide }),
        court: new THREE.MeshStandardMaterial({ color: 0x2b6cb0, metalness: 0.04, roughness: 0.75, side: THREE.DoubleSide }),
        roof: new THREE.MeshStandardMaterial({ color: pal.roof, metalness: 0.05, roughness: 0.80, side: THREE.DoubleSide }),
        unit4br: new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xf59e0b, emissiveIntensity: 0.22, metalness: 0.12, roughness: 0.25, side: THREE.DoubleSide }),
        unit5br: new THREE.MeshStandardMaterial({ color: 0x10b981, emissive: 0x10b981, emissiveIntensity: 0.22, metalness: 0.12, roughness: 0.25, side: THREE.DoubleSide }),
        unitBlue: new THREE.MeshStandardMaterial({ color: 0x3b82f6, emissive: 0x3b82f6, emissiveIntensity: 0.22, metalness: 0.12, roughness: 0.25, side: THREE.DoubleSide })
      };

      const buckets = {};
      Object.keys(mats).forEach(k => { buckets[k] = { pos: [], norm: [], uv: [] }; });
      const heroShaderWall = { pos: [], norm: [], uv: [], col: [], band: [], meta: [] };

      function pushHeroShaderWallRing(ring2d, z0, z1, baseRgb, bandRgb, schemeCode, topHeightM) {
        const openRing = (ring2d.length > 3 && Math.hypot(ring2d[0][0] - ring2d[ring2d.length - 1][0], ring2d[0][1] - ring2d[ring2d.length - 1][1]) < 1e-4)
          ? ring2d.slice(0, -1)
          : ring2d;
        if (openRing.length < 3 || z1 <= z0) return;
        let cx = 0, cy = 0;
        for (const [x, y] of openRing) { cx += x; cy += y; }
        cx /= openRing.length; cy /= openRing.length;
        const v0 = z0 / 24.0, v1 = z1 / 24.0;
        for (let i = 0; i < openRing.length; i++) {
          const [x0, y0] = openRing[i];
          const [x1, y1] = openRing[(i + 1) % openRing.length];
          const dx = x1 - x0, dy = y1 - y0;
          const segLen = Math.hypot(dx, dy);
          if (segLen < 0.25) continue;
          let nx = dy / segLen, ny = -dx / segLen;
          const mx = (x0 + x1) * 0.5 - cx, my = (y0 + y1) * 0.5 - cy;
          if (nx * mx + ny * my < 0) { nx = -nx; ny = -ny; }
          const isFront = (segLen >= 5.0) ? 1.0 : 0.0;
          const u0 = 0.0, u1 = segLen / 16.0;
          heroShaderWall.pos.push(x0, y0, z0, x1, y1, z0, x1, y1, z1, x0, y0, z0, x1, y1, z1, x0, y0, z1);
          for (let k = 0; k < 6; k++) {
            heroShaderWall.norm.push(nx, ny, 0);
            heroShaderWall.col.push(baseRgb[0], baseRgb[1], baseRgb[2]);
            heroShaderWall.band.push(bandRgb[0], bandRgb[1], bandRgb[2], topHeightM);
          }
          heroShaderWall.uv.push(u0, v0, u1, v0, u1, v1, u0, v0, u1, v1, u0, v1);
          heroShaderWall.meta.push(
            0.0, segLen, isFront, schemeCode,
            segLen, segLen, isFront, schemeCode,
            segLen, segLen, isFront, schemeCode,
            0.0, segLen, isFront, schemeCode,
            segLen, segLen, isFront, schemeCode,
            0.0, segLen, isFront, schemeCode
          );
        }
      }

      function pushBox(bKey, cx, cy, z0, z1, w, d, rot = 0) {
        const pts = makeArchFootprint("rect", cx, cy, w, d, rot);
        pushExtrudedToBucket(bKey, pts, z0, z1, true);
      }

      function pushExtrudedToBucket(bKey, ring2d, z0, z1, capTop = true) {
        const b = buckets[bKey];
        if (!b || !ring2d || ring2d.length < 3 || z1 <= z0) return;
        const openRing = (ring2d.length > 3 && Math.hypot(ring2d[0][0] - ring2d[ring2d.length - 1][0], ring2d[0][1] - ring2d[ring2d.length - 1][1]) < 1e-4)
          ? ring2d.slice(0, -1)
          : ring2d;
        if (openRing.length < 3) return;
        let cx = 0, cy = 0;
        for (const [x, y] of openRing) { cx += x; cy += y; }
        cx /= openRing.length; cy /= openRing.length;

        let uAccum = 0;
        const uvScale = (bKey === "timber" || bKey === "garden") ? 3.2 : 6.4;
        const v0 = z0 / uvScale, v1 = z1 / uvScale;

        for (let i = 0; i < openRing.length; i++) {
          const [x0, y0] = openRing[i];
          const [x1, y1] = openRing[(i + 1) % openRing.length];
          const dx = x1 - x0, dy = y1 - y0;
          const segLen = Math.hypot(dx, dy);
          if (segLen < 0.04) continue;
          let nx = dy / segLen, ny = -dx / segLen;
          const mx = (x0 + x1) * 0.5 - cx, my = (y0 + y1) * 0.5 - cy;
          if (nx * mx + ny * my < 0) { nx = -nx; ny = -ny; }

          const u0 = uAccum / uvScale;
          const u1 = (uAccum + segLen) / uvScale;
          uAccum += segLen;

          b.pos.push(x0, y0, z0, x1, y1, z0, x1, y1, z1, x0, y0, z0, x1, y1, z1, x0, y0, z1);
          for (let k = 0; k < 6; k++) b.norm.push(nx, ny, 0);
          b.uv.push(u0, v0, u1, v0, u1, v1, u0, v0, u1, v1, u0, v1);
        }

        if (capTop && typeof THREE.ShapeUtils !== "undefined") {
          const contour = openRing.map(([x, y]) => new THREE.Vector2(x, y));
          const tris = THREE.ShapeUtils.triangulateShape(contour, []);
          for (const [i0, i1, i2] of tris) {
            const pA = openRing[i0], pB = openRing[i1], pC = openRing[i2];
            b.pos.push(pA[0], pA[1], z1, pB[0], pB[1], z1, pC[0], pC[1], z1);
            b.norm.push(0, 0, 1, 0, 0, 1, 0, 0, 1);
            b.uv.push(pA[0] / uvScale, pA[1] / uvScale, pB[0] / uvScale, pB[1] / uvScale, pC[0] / uvScale, pC[1] / uvScale);
          }
        }
      }

      // Build Mullions, Full-Height Architectural Fins & Cantilevered Glass Balconies along every facade edge
      function pushFacadeMullionsAndBalconies(ring2d, z0, z1, floorH, addBalconies, addCornerFins) {
        const openRing = (ring2d.length > 3 && Math.hypot(ring2d[0][0] - ring2d[ring2d.length - 1][0], ring2d[0][1] - ring2d[ring2d.length - 1][1]) < 1e-4)
          ? ring2d.slice(0, -1)
          : ring2d;
        if (openRing.length < 3 || z1 <= z0) return;
        let cx = 0, cy = 0;
        for (const [x, y] of openRing) { cx += x; cy += y; }
        cx /= openRing.length; cy /= openRing.length;

        for (let i = 0; i < openRing.length; i++) {
          const [x0, y0] = openRing[i];
          const [x1, y1] = openRing[(i + 1) % openRing.length];
          const dx = x1 - x0, dy = y1 - y0;
          const segLen = Math.hypot(dx, dy);
          if (segLen < 1.2) continue;
          const ux = dx / segLen, uy = dy / segLen;
          let nx = dy / segLen, ny = -dx / segLen;
          const mx = (x0 + x1) * 0.5 - cx, my = (y0 + y1) * 0.5 - cy;
          if (nx * mx + ny * my < 0) { nx = -nx; ny = -ny; }

          // Corner architectural megacolumn fin at vertex i
          if (addCornerFins) {
            const fw = 0.28, fd = 0.34;
            const cRing = [
              [x0 - ux * fw, y0 - uy * fw],
              [x0 + ux * fw, y0 + uy * fw],
              [x0 + ux * fw + nx * fd, y0 + uy * fw + ny * fd],
              [x0 - ux * fw + nx * fd, y0 - uy * fw + ny * fd]
            ];
            pushExtrudedToBucket("fin", cRing, z0, z1, true);
          }

          // Vertical curtain-wall mullions spaced every 3.6m
          const nMull = Math.max(1, Math.floor(segLen / 3.6));
          for (let m = 1; m < nMull; m++) {
            const t = m / nMull;
            const px = x0 + dx * t, py = y0 + dy * t;
            const mw = 0.04, md = 0.11;
            const mRing = [
              [px - ux * mw, py - uy * mw],
              [px + ux * mw, py + uy * mw],
              [px + ux * mw + nx * md, py + uy * mw + ny * md],
              [px - ux * mw + nx * md, py - uy * mw + ny * md]
            ];
            pushExtrudedToBucket((m % 3 === 0) ? "fin" : "frame", mRing, z0, z1, false);
          }

          // Cantilevered residential balconies with glass balustrades on segments >= 8.5m
          if (addBalconies && segLen >= 8.5 && (i % 2 === 0)) {
            const bDepth = 1.32;
            const tA = 0.24, tB = 0.76;
            const bx0 = x0 + dx * tA, by0 = y0 + dy * tA;
            const bx1 = x0 + dx * tB, by1 = y0 + dy * tB;
            const balRing = [
              [bx0, by0],
              [bx1, by1],
              [bx1 + nx * bDepth, by1 + ny * bDepth],
              [bx0 + nx * bDepth, by0 + ny * bDepth]
            ];
            const railThick = 0.06;
            const railRing = [
              [bx0 + nx * (bDepth - railThick), by0 + ny * (bDepth - railThick)],
              [bx1 + nx * (bDepth - railThick), by1 + ny * (bDepth - railThick)],
              [bx1 + nx * bDepth, by1 + ny * bDepth],
              [bx0 + nx * bDepth, by0 + ny * bDepth]
            ];
            const floors = Math.max(1, Math.round((z1 - z0) / floorH));
            for (let f = 1; f <= floors; f++) {
              const fz0 = z0 + (f - 1) * floorH;
              pushExtrudedToBucket("slab", balRing, fz0, fz0 + 0.16, true);
              pushExtrudedToBucket("rail", railRing, fz0 + 0.16, fz0 + 1.12, false);
              pushExtrudedToBucket("frame", railRing, fz0 + 1.12, fz0 + 1.18, true);
            }
          }
        }
      }

      const isDefaultMode = (active3DShowMe === "all" && active3DFloor === "ALL" && active3DStack === "ALL" && active3DBlock === "ALL");

      // Builds a 14-Layer PBR + GLSL Metric Architectural Tower Wing with Sky-Gardens, Floor Slabs, Corner Megacolumns & Crown Spire
      const heroBaseRgb = (spec.typology === "supertall_diamond" || spec.typology === "organic_terraced")
        ? [0.91, 0.89, 0.85]
        : [0.89, 0.87, 0.83];
      const heroBandRgb = (spec.typology === "supertall_diamond")
        ? [0.68, 0.54, 0.36]
        : [0.62, 0.44, 0.30];
      const heroSchemeCode = 100 + (spec.seed % 6);

      function buildPbrTowerWing(baseRing, zStart, numFloors, floorH, blkId, stId, is4BR, taperTop = 1.0, hasCrownSpire = false) {
        let curRing = baseRing;
        const skyEvery = spec.skyGardenEvery || 14;
        const wingTopZ = zStart + numFloors * floorH;

        for (let f = 1; f <= numFloors; f++) {
          const z0 = zStart + (f - 1) * floorH;
          const z1 = zStart + f * floorH;
          if (taperTop !== 1.0 && f > 1) {
            const frac = (f - 1) / Math.max(1, numFloors - 1);
            curRing = scaleEnuRing(baseRing, 1.0 - frac * (1.0 - taperTop));
          }
          const ledgeRing = expandEnuRing(curRing, 0.08);

          // Check if this floor is an open recessed Sky-Garden / Outrigger Amenity Terrace
          const isSkyGarden = (numFloors >= 18 && f > 4 && f < numFloors - 3 && (f % skyEvery === 0));
          if (isSkyGarden) {
            const coreRing = scaleEnuRing(curRing, 0.72);
            const planterRing = expandEnuRing(curRing, 0.12);
            pushExtrudedToBucket("garden", coreRing, z0, z1 - 0.18, false);
            pushExtrudedToBucket("green", planterRing, z0 + 0.18, z0 + 1.05, true);
            pushExtrudedToBucket("rail", ledgeRing, z0 + 0.18, z0 + 1.18, false);
            pushExtrudedToBucket("slab", ledgeRing, z1 - 0.18, z1, true);
            continue;
          }

          let wallBucket = "glass";
          if (!isDefaultMode) {
            const blkMatch = (active3DBlock === "ALL" || active3DBlock === blkId);
            if (blkMatch) {
              if (active3DShowMe === "4br" && is4BR) wallBucket = "unit4br";
              else if (active3DShowMe === "5br" && !is4BR) wallBucket = "unit5br";
              else if (active3DShowMe === "4br_5br_mix") wallBucket = is4BR ? "unit4br" : "unit5br";
              else if (active3DBlock === blkId && active3DShowMe === "all") wallBucket = is4BR ? "unit4br" : "unit5br";

              const lowLim = Math.max(3, Math.round(numFloors * 0.35));
              const midLim = Math.max(6, Math.round(numFloors * 0.72));
              if (active3DFloor === "LOW" && f <= lowLim) wallBucket = "unitBlue";
              else if (active3DFloor === "MID" && f > lowLim && f <= midLim) wallBucket = "unit4br";
              else if (active3DFloor === "HIGH" && f > midLim) wallBucket = "unit5br";

              if (active3DStack === "S1" && stId === "S1") wallBucket = "unit4br";
              else if (active3DStack === "S2" && stId === "S2") wallBucket = "unit5br";
            }
          }

          if (wallBucket === "glass") {
            pushHeroShaderWallRing(curRing, z0, z1 - 0.12, heroBaseRgb, heroBandRgb, heroSchemeCode, wingTopZ);
            pushExtrudedToBucket("slab", ledgeRing, z1 - 0.12, z1, f === numFloors);
          } else {
            pushExtrudedToBucket(wallBucket, curRing, z0, z1 - 0.16, false);
            pushExtrudedToBucket("slab", ledgeRing, z1 - 0.16, z1, f === numFloors);
          }
        }

        // Add full-height corner architectural megacolumn fins
        pushFacadeMullionsAndBalconies(curRing, zStart, zStart + numFloors * floorH, floorH, false, true);

        const topZ = zStart + numFloors * floorH;
        // Rooftop stone parapet + recessed weathered roof deck + mechanical core + architectural crown frame
        const parapetOuter = expandEnuRing(curRing, 0.20);
        const roofWell = scaleEnuRing(curRing, 0.86);
        pushExtrudedToBucket("crown", parapetOuter, topZ, topZ + 1.35, true);
        pushExtrudedToBucket("roof", roofWell, topZ + 1.35, topZ + 1.45, true);

        const mechCore = scaleEnuRing(curRing, 0.46);
        pushExtrudedToBucket("solid", mechCore, topZ + 1.35, topZ + 4.6, true);
        pushExtrudedToBucket("crownGlass", scaleEnuRing(curRing, 0.66), topZ + 1.35, topZ + 3.8, true);

        if (hasCrownSpire) {
          // Multi-tier sculpted supertall diamond/lantern crown spire (like Burj Binghatti / Creek Tower / haio.sg)
          const tierA = scaleEnuRing(curRing, 0.62);
          const tierB = scaleEnuRing(curRing, 0.42);
          const tierC = scaleEnuRing(curRing, 0.22);
          pushExtrudedToBucket("crown", tierA, topZ + 1.35, topZ + 8.5, true);
          pushExtrudedToBucket("crownGlass", scaleEnuRing(tierA, 0.88), topZ + 1.35, topZ + 12.0, true);
          pushExtrudedToBucket("fin", tierB, topZ + 8.5, topZ + 18.5, true);
          pushExtrudedToBucket("crown", tierC, topZ + 18.5, topZ + 26.0, true);
          return topZ + 26.0;
        }
        return topZ + 4.6;
      }

      const rotRad = (spec.rotDeg * Math.PI) / 180;
      const seedMod = (spec.seed % 5) * 1.2;
      let roofCalloutZ = 68.0;
      let roofCalloutXY = [0, 0];

      // -----------------------------------------------------------------------
      // FULL-PARCEL 3D ARCHITECTURAL SITE PLINTH & LANDSCAPED GROUNDS (ZERO 2D SHADOW BLEED)
      // Covers the entire development parcel (104m × 88m) so underlying 2D satellite roofs/shadows are 100% masked!
      // -----------------------------------------------------------------------
      const sitePlinthRing = makeArchFootprint("chamfer_oct", 2.0, -2.0, 106, 88, rotRad);
      const siteLawnRing = makeArchFootprint("chamfer_oct", 2.0, -2.0, 98, 80, rotRad);
      const siteDriveRing = makeArchFootprint("rect", 0.0, -28.0, 68, 14, rotRad);
      const siteCourtRing = makeArchFootprint("rect", -32.0, -18.0, 18, 10, rotRad);
      pushExtrudedToBucket("deck", sitePlinthRing, 0.0, 0.85, true);
      pushExtrudedToBucket("lawn", siteLawnRing, 0.85, 1.10, true);
      pushExtrudedToBucket("driveway", siteDriveRing, 1.10, 1.22, true);
      pushExtrudedToBucket("court", siteCourtRing, 1.10, 1.25, true);
      pushExtrudedToBucket("rail", expandEnuRing(siteCourtRing, 0.15), 1.25, 3.2, false);

      if (spec.typology === "supertall_diamond") {
        // Sculpted Supertall Tower (Block 1) at Full Architectural Height + Luxury Terracotta/Timber/Glass Sky-Garden Podium (Block 2)
        const visFloors = Math.min(125, Math.max(44, spec.storeys || 68));
        const targetShaftH = Math.max(visFloors * 3.45, (spec.heightM || visFloors * 3.8) - 31.2);
        const fH = Math.min(5.25, Math.max(3.45, targetShaftH / visFloors));
        const tier1F = Math.round(visFloors * 0.56);
        const tier2F = Math.round(visFloors * 0.26);
        const tier3F = Math.max(6, visFloors - tier1F - tier2F);

        // Multi-level articulated podium base under Block 1 & Block 2
        const mainPod = makeArchFootprint("chamfer_oct", 4.0, -4.0, 74, 56, rotRad);
        pushExtrudedToBucket("podium", mainPod, 1.10, 6.2, true);
        pushExtrudedToBucket("timber", scaleEnuRing(mainPod, 0.96), 6.2, 11.4, true);
        pushExtrudedToBucket("slab", expandEnuRing(mainPod, 0.35), 11.1, 11.6, true);
        pushExtrudedToBucket("lawn", scaleEnuRing(mainPod, 0.88), 11.6, 12.0, true);

        const w1Ring = makeArchFootprint("cruciform_spire", -10.5, -2.0, 26 + seedMod, 21, rotRad);
        const w2Ring = makeArchFootprint("chamfer_oct", 7.0, 6.5, 22, 19 + seedMod, rotRad + 0.18);

        const zT1 = buildPbrTowerWing(w1Ring, 11.6, tier1F, fH, "B1", "S1", true, 0.94, false);
        buildPbrTowerWing(w2Ring, 11.6, tier1F, fH, "B1", "S2", false, 0.94, false);

        const w1Mid = scaleEnuRing(w1Ring, 0.80);
        const w2Mid = scaleEnuRing(w2Ring, 0.80);
        const zT2 = buildPbrTowerWing(w1Mid, zT1 - 3.2, tier2F, fH, "B1", "S1", true, 0.88, false);
        buildPbrTowerWing(w2Mid, zT1 - 3.2, tier2F, fH, "B1", "S2", false, 0.88, false);

        const w1Top = scaleEnuRing(w1Ring, 0.60);
        const zT3 = buildPbrTowerWing(w1Top, zT2 - 3.2, tier3F, fH, "B1", "S1", true, 0.84, true);

        // Adjoining Block 2: Haio.sg Terracotta + Timber Louvre + Smoked-Glass Amenity Pavilion with Rooftop Sky-Garden & 25m Lap Pool
        const podRing = makeArchFootprint("rect", 24.0, -15.0, 30, 22, rotRad);
        pushExtrudedToBucket("podium", podRing, 11.6, 18.5, true);
        pushExtrudedToBucket("timber", scaleEnuRing(podRing, 0.97), 18.5, 22.8, true);
        pushExtrudedToBucket("amenityGlass", scaleEnuRing(podRing, 0.94), 22.8, 30.5, true);
        pushExtrudedToBucket("darkroof", expandEnuRing(podRing, 0.45), 30.5, 31.4, true);
        pushExtrudedToBucket("green", scaleEnuRing(podRing, 0.84), 31.4, 32.1, true);
        const poolDeckRing = makeArchFootprint("rect", 25.0, -15.0, 18, 9, rotRad);
        pushExtrudedToBucket("deck", poolDeckRing, 32.1, 32.35, true);
        const poolRing = makeArchFootprint("rect", 25.0, -15.0, 14, 6, rotRad);
        pushExtrudedToBucket("pool", poolRing, 32.35, 32.65, true);

        roofCalloutZ = zT3 + 3.0;
        roofCalloutXY = [-6.0, 1.0];
      } else if (spec.typology === "organic_terraced") {
        // Cascading Organic Terraced Waterfront Tower (Bugatti / Como / Maryam Island / Sharjah Waterfront)
        const visFloors = Math.min(85, Math.max(24, spec.storeys || 36));
        const fH = 3.45;
        const podBase = makeArchFootprint("organic_oval", 2.0, -4.0, 78, 56, rotRad);
        pushExtrudedToBucket("podium", podBase, 1.10, 6.5, true);
        pushExtrudedToBucket("timber", scaleEnuRing(podBase, 0.94), 6.5, 10.2, true);
        pushExtrudedToBucket("deck", scaleEnuRing(podBase, 0.88), 10.2, 10.6, true);
        const lagoonPool = makeArchFootprint("organic_oval", 8.0, -16.0, 26, 11, rotRad);
        pushExtrudedToBucket("pool", lagoonPool, 10.6, 11.0, true);

        const mainOval = makeArchFootprint("organic_oval", -7.0, 4.0, 32 + seedMod, 23, rotRad);
        const sideOval = makeArchFootprint("organic_oval", 16.0, -6.0, 25, 18 + seedMod, rotRad - 0.25);

        const zTop1 = buildPbrTowerWing(mainOval, 10.6, visFloors, fH, "B1", "S1", true, 0.62, true);
        buildPbrTowerWing(sideOval, 10.6, Math.round(visFloors * 0.72), fH, "B2", "S2", false, 0.70, false);

        roofCalloutZ = zTop1 + 3.0;
        roofCalloutXY = [-7.0, 4.0];
      } else if (spec.typology === "twin_triple_highrise") {
        // 3 Articulated High-Rise Residential Towers on Shared Landscaped Resort Podium
        const f1 = Math.min(80, Math.max(18, spec.storeys || 32));
        const f2 = Math.max(14, Math.round(f1 * 0.82));
        const f3 = Math.max(12, Math.round(f1 * 0.66));
        const fH = 3.35;

        const podBase = makeArchFootprint("chamfer_oct", 0, 0, 78, 58, rotRad);
        pushExtrudedToBucket("podium", podBase, 1.10, 6.4, true);
        pushExtrudedToBucket("timber", scaleEnuRing(podBase, 0.96), 6.4, 10.4, true);
        pushExtrudedToBucket("slab", expandEnuRing(podBase, 0.3), 10.4, 10.9, true);
        pushExtrudedToBucket("lawn", scaleEnuRing(podBase, 0.90), 10.9, 11.3, true);
        const poolDeck = makeArchFootprint("rect", 2.0, -2.0, 26, 12, rotRad);
        pushExtrudedToBucket("deck", poolDeck, 11.3, 11.55, true);
        const lapPool = makeArchFootprint("rect", 2.0, -2.0, 22, 8.5, rotRad);
        pushExtrudedToBucket("pool", lapPool, 11.55, 11.85, true);

        const t1Ring = makeArchFootprint("stepped_wing", -19.0, 9.0, 24, 16, rotRad);
        const t2Ring = makeArchFootprint("stepped_wing", 18.0, 10.0, 22, 15, rotRad + 0.45);
        const t3Ring = makeArchFootprint("chamfer_oct", 0.0, -16.0, 22, 15, rotRad - 0.30);

        const z1 = buildPbrTowerWing(t1Ring, 11.3, f1, fH, "B1", "S1", true, 0.92, true);
        buildPbrTowerWing(t2Ring, 11.3, f2, fH, "B2", "S2", false, 0.92, false);
        buildPbrTowerWing(t3Ring, 11.3, f3, fH, "B3", "S1", true, 0.94, false);

        roofCalloutZ = z1 + 3.0;
        roofCalloutXY = [-19.0, 9.0];
      } else if (spec.typology === "urban_courtyard") {
        // Stepped Mid-Rise Courtyard & Boulevard Masterplan (Aljada / JVC / Palm Jebel Ali / Dubai Islands)
        const f1 = Math.min(22, Math.max(12, spec.storeys));
        const f2 = Math.max(10, Math.round(f1 * 0.82));
        const f3 = Math.max(8, Math.round(f1 * 0.68));
        const fH = 3.4;

        const uRing = makeArchFootprint("u_boulevard", -12.0, 6.0, 42, 30, rotRad);
        const lRing = makeArchFootprint("l_courtyard", 22.0, -8.0, 30, 26, rotRad + Math.PI * 0.5);
        const pavRing = makeArchFootprint("stepped_wing", -8.0, -22.0, 26, 16, rotRad);

        const z1 = buildPbrTowerWing(uRing, 1.10, f1, fH, "B1", "S1", true, 1.0, false);
        buildPbrTowerWing(lRing, 1.10, f2, fH, "B2", "S2", false, 1.0, false);
        buildPbrTowerWing(pavRing, 1.10, f3, fH, "B3", "S1", true, 1.0, false);

        const cDeck = makeArchFootprint("rect", 4.0, -4.0, 24, 16, rotRad);
        pushExtrudedToBucket("deck", cDeck, 1.10, 1.5, true);
        const cPool = makeArchFootprint("rect", 4.0, -4.0, 16, 7.5, rotRad);
        pushExtrudedToBucket("pool", cPool, 1.5, 1.85, true);

        roofCalloutZ = z1 + 3.0;
        roofCalloutXY = [-12.0, 6.0];
      } else if (spec.typology === "villa_lagoon_masterplan") {
        // Signature Waterfront Clubhouse Tower + Stepped Luxury Villa Mansions & Crystal Lagoon
        const clubFloors = Math.min(18, Math.max(10, spec.storeys));
        const fH = 3.5;
        const clubRing = makeArchFootprint("stepped_wing", 0, 16.0, 30, 18, rotRad);
        const z1 = buildPbrTowerWing(clubRing, 1.10, clubFloors, fH, "B1", "S1", true, 0.90, false);

        const crystalLagoon = makeArchFootprint("organic_oval", 0, -6.0, 48, 22, rotRad);
        pushExtrudedToBucket("deck", expandEnuRing(crystalLagoon, 2.2), 1.10, 1.45, true);
        pushExtrudedToBucket("pool", crystalLagoon, 1.45, 1.80, true);

        const villaOffsets = [
          [-28, -6, "B2", "S1", true], [-16, -24, "B2", "S2", false],
          [16, -24, "B3", "S1", true],  [28, -6, "B3", "S2", false],
          [-26, 18, "B2", "S1", true],  [26, 18, "B3", "S2", false]
        ];
        for (const [vx, vy, bId, sId, is4] of villaOffsets) {
          const vRing = makeArchFootprint("l_courtyard", vx, vy, 14, 12, rotRad);
          buildPbrTowerWing(vRing, 1.10, 4, 3.6, bId, sId, is4, 0.92, false);
        }

        roofCalloutZ = z1 + 3.0;
        roofCalloutXY = [0, 16.0];
      } else {
        // Mega-Civic / Aviation Concourse / Metro Interchange / Campus (PRJ-D1, PRJ-D8, PRJ-D9, PRJ-SH12)
        const concourseBase = makeArchFootprint("chamfer_oct", 0, 0, 76, 44, rotRad);
        pushExtrudedToBucket("amenityGlass", concourseBase, 1.10, 10.5, true);
        pushExtrudedToBucket("crown", expandEnuRing(concourseBase, 1.2), 10.5, 12.0, true);
        const wingA = makeArchFootprint("cruciform_spire", -18.0, 4.0, 30, 24, rotRad);
        const wingB = makeArchFootprint("stepped_wing", 18.0, -4.0, 28, 22, rotRad);
        const z1 = buildPbrTowerWing(wingA, 12.0, 12, 3.8, "B1", "S1", true, 0.86, true);
        buildPbrTowerWing(wingB, 12.0, 9, 3.8, "B2", "S2", false, 0.90, false);
        roofCalloutZ = z1 + 3.0;
        roofCalloutXY = [-18.0, 4.0];
      }

      // Add 3D Landscaping Trees around the Hero Site Perimeter & Podium Deck
      const treeSpots = [
        [-42, -32, 1.1], [-28, -36, 1.1], [28, -36, 1.1], [42, -32, 1.1],
        [-44, 0, 1.1], [44, 0, 1.1], [-40, 30, 1.1], [40, 30, 1.1],
        [-16, 34, 1.1], [16, 34, 1.1], [18, -12, 12.0], [30, -8, 12.0]
      ];
      for (const [tx, ty, tz] of treeSpots) {
        const rx = tx * Math.cos(rotRad) - ty * Math.sin(rotRad);
        const ry = tx * Math.sin(rotRad) + ty * Math.cos(rotRad);
        pushBox("timber", rx, ry, tz, tz + 2.6, 0.55, 0.55, 0);
        const canopyRing = makeArchFootprint("organic_oval", rx, ry, 4.8, 4.8, 0);
        pushExtrudedToBucket("green", canopyRing, tz + 2.2, tz + 5.8, true);
      }

      three3DLayer.heroRoofLocalVec = new THREE.Vector3(roofCalloutXY[0], roofCalloutXY[1], roofCalloutZ);

      const heroGroup = new THREE.Group();
      if (heroShaderWall.pos.length && three3DLayer.cityFacadeMats && three3DLayer.cityFacadeMats[0]) {
        const hwg = new THREE.BufferGeometry();
        hwg.setAttribute("position", new THREE.Float32BufferAttribute(heroShaderWall.pos, 3));
        hwg.setAttribute("normal", new THREE.Float32BufferAttribute(heroShaderWall.norm, 3));
        hwg.setAttribute("uv", new THREE.Float32BufferAttribute(heroShaderWall.uv, 2));
        hwg.setAttribute("color", new THREE.Float32BufferAttribute(heroShaderWall.col, 3));
        hwg.setAttribute("hdbBand", new THREE.Float32BufferAttribute(heroShaderWall.band, 4));
        hwg.setAttribute("hdbWall", new THREE.Float32BufferAttribute(heroShaderWall.meta, 4));
        const hwm = new THREE.Mesh(hwg, three3DLayer.cityFacadeMats[0]);
        hwm.frustumCulled = false;
        heroGroup.add(hwm);
      }
      Object.keys(buckets).forEach(k => {
        const b = buckets[k];
        if (!b.pos.length) return;
        const geo = new THREE.BufferGeometry();
        geo.setAttribute("position", new THREE.Float32BufferAttribute(b.pos, 3));
        geo.setAttribute("normal", new THREE.Float32BufferAttribute(b.norm, 3));
        geo.setAttribute("uv", new THREE.Float32BufferAttribute(b.uv, 2));
        const mesh = new THREE.Mesh(geo, mats[k]);
        mesh.frustumCulled = false;
        heroGroup.add(mesh);
      });

      three3DLayer.heroGroup = heroGroup;
      three3DLayer.scene.add(heroGroup);

      if (originChanged) {
        scheduleOsmCityRebuild(60);
      }
      if (map3d) map3d.triggerRepaint();
    }

    // =========================================================================
    // PERSISTENT MULTI-ZOOM z14 MVT 3D TILE BUILDING CACHE (ZERO ZOOM-OUT LOSS)
    // OpenMapTiles strips 99.5% of buildings at z=13 and 100% at z<=12. By streaming
    // and LRU-caching up to 240 z=14 MVT tiles (~1,600 km² = 100% of Dubai & Sharjah),
    // every district (Downtown, Business Bay, DIFC, Marina, Palm, JVC, Creek, Sharjah)
    // stays standing in full 3D across all zooms (z=8.8..19) without ever starving!
    // =========================================================================
    const osmZ14TileBuildings = new Map(); // tileKey "tx/ty" -> { cLon, cLat, recs: [...] }
    const fetchedZ14TileKeys = new Set();
    const inflightZ14TileKeys = new Set();
    let openFreeMapTileTemplate = null;
    let openFreeMapTileJsonPromise = null;

    // Core Dubai & Sharjah urban skyline z=14 tiles so wide L3 / L2 / L1 regional cameras immediately display full 3D skylines
    const CORE_UAE_Z14_SKYLINE_TILES = [
      // Downtown Dubai, Burj Khalifa, Business Bay & DIFC / SZR Corridor
      [10707, 7006], [10707, 7007], [10707, 7005], [10708, 7005], [10708, 7006], [10708, 7007],
      [10706, 7006], [10706, 7007], [10706, 7008], [10707, 7008], [10708, 7004], [10707, 7004],
      // Al Wasl, Jumeirah, Satwa, Karama, Bur Dubai, Deira & Creek Harbour
      [10705, 7006], [10705, 7007], [10706, 7005], [10709, 7003], [10709, 7004], [10708, 7003],
      [10710, 7003], [10710, 7005], [10710, 7006], [10711, 7005], [10709, 7005], [10709, 7006],
      // Dubai Marina, JBR, JLT, Media City, Palm Jumeirah & JVC / Hessa St
      [10701, 7012], [10701, 7013], [10700, 7012], [10700, 7013], [10702, 7011], [10702, 7012],
      [10701, 7010], [10701, 7011], [10700, 7010], [10700, 7011], [10702, 7010],
      [10704, 7013], [10704, 7012], [10703, 7013], [10705, 7012], [10705, 7011],
      // Sharjah Al Khan, Maryam Island (PRJ-SH4), Al Majaz, Corniche & Aljada (PRJ-SH2)
      [10711, 7000], [10711, 6999], [10712, 6999], [10712, 7000], [10713, 6999],
      [10715, 7000], [10716, 7000], [10716, 6999]
    ];

    function lonLatToZ14Tile(lon, lat) {
      const n = 16384.0;
      const clampedLat = Math.max(-85.05, Math.min(85.05, lat));
      const latRad = (clampedLat * Math.PI) / 180.0;
      const tx = Math.max(0, Math.min(16383, Math.floor(((lon + 180.0) / 360.0) * n)));
      const ty = Math.max(0, Math.min(16383, Math.floor(((1.0 - Math.log(Math.tan(latRad) + 1.0 / Math.cos(latRad)) / Math.PI) / 2.0) * n)));
      return [tx, ty];
    }

    function z14TileCenterLonLat(tx, ty) {
      const n = 16384.0;
      const lon = ((tx + 0.5) / n) * 360.0 - 180.0;
      const lat = (Math.atan(Math.sinh(Math.PI * (1.0 - (2.0 * (ty + 0.5)) / n))) * 180.0) / Math.PI;
      return [lon, lat];
    }

    function buildCachedBuildingRec(outerLonLat, holesLonLat, rawH, minH) {
      if (!outerLonLat || outerLonLat.length < 4 || outerLonLat.length > 1601) return null;
      const nPts = outerLonLat.length - 1;
      let polyLon = 0, polyLat = 0;
      for (let i = 0; i < nPts; i++) {
        polyLon += outerLonLat[i][0];
        polyLat += outerLonLat[i][1];
      }
      polyLon /= nPts;
      polyLat /= nPts;

      const cosLatM = 111320.0 * Math.cos((polyLat * Math.PI) / 180.0);
      let area2 = 0;
      for (let i = 0; i < nPts; i++) {
        const x0 = (outerLonLat[i][0] - polyLon) * cosLatM;
        const y0 = (outerLonLat[i][1] - polyLat) * 111320.0;
        const x1 = (outerLonLat[(i + 1) % nPts][0] - polyLon) * cosLatM;
        const y1 = (outerLonLat[(i + 1) % nPts][1] - polyLat) * 111320.0;
        area2 += x0 * y1 - x1 * y0;
      }
      const areaM2 = Math.abs(area2 * 0.5);
      const effR = Math.sqrt(areaM2 / Math.PI);
      const minEffR = (rawH >= 24.0 || minH > 0) ? 0.15 : 1.25;
      if (effR < minEffR || effR > 1600.0) return null;

      const isHighRiseZone = (polyLat >= 25.05 && polyLat <= 25.35 && polyLon >= 55.12 && polyLon <= 55.42);
      const blockHash = Math.abs(Math.round(polyLon * 1800) * 73 + Math.round(polyLat * 1800) * 137);
      const posHash = Math.abs(Math.round(polyLon * 18000) * 17 + Math.round(polyLat * 18000) * 31);
      let h = rawH;
      if (!Number.isFinite(h) || h <= 3.2) {
        if (areaM2 < 240.0) {
          h = isHighRiseZone ? (12.0 + (blockHash % 4) * 3.2) : (7.8 + (blockHash % 3) * 3.0);
        } else if (areaM2 < 950.0) {
          h = isHighRiseZone ? (26.0 + (blockHash % 6) * 4.5) : (16.0 + (blockHash % 5) * 3.6);
        } else {
          h = 18.0 + (blockHash % 4) * 3.8;
        }
      } else {
        h = Math.min(1100.0, Math.max(minH + 1.2, h));
      }

      const worldKey = `${Math.round(polyLon * 40000)}_${Math.round(polyLat * 40000)}_${Math.round(minH * 2)}_${Math.round(h * 2)}_${Math.round(areaM2)}`;
      return {
        worldKey,
        outerLonLat,
        holesLonLat: (holesLonLat && holesLonLat.length) ? holesLonLat : null,
        polyLon,
        polyLat,
        h,
        minH,
        areaM2,
        effR,
        blockHash,
        posHash
      };
    }

    function storeTileRecsLru(tileKey, tx, ty, recs) {
      if (osmZ14TileBuildings.has(tileKey)) {
        osmZ14TileBuildings.delete(tileKey);
      }
      while (osmZ14TileBuildings.size >= 240) {
        const oldestKey = osmZ14TileBuildings.keys().next().value;
        if (!oldestKey) break;
        osmZ14TileBuildings.delete(oldestKey);
        fetchedZ14TileKeys.delete(oldestKey);
      }
      const [cLon, cLat] = z14TileCenterLonLat(tx, ty);
      osmZ14TileBuildings.set(tileKey, { cLon, cLat, recs });
    }

    function readMvtVarint(u8, posObj) {
      let res = 0, mul = 1, p = posObj.p;
      const len = u8.length;
      while (p < len) {
        const b = u8[p++];
        res += (b & 0x7f) * mul;
        if ((b & 0x80) === 0) break;
        mul *= 128;
      }
      posObj.p = p;
      return res;
    }

    function skipMvtField(u8, posObj, wt) {
      if (wt === 0) readMvtVarint(u8, posObj);
      else if (wt === 1) posObj.p += 8;
      else if (wt === 2) { const l = readMvtVarint(u8, posObj); posObj.p += l; }
      else if (wt === 5) posObj.p += 4;
      else posObj.p = u8.length;
    }

    async function decodeMvtBuildingBuffer(arrayBuffer, tileX, tileY) {
      let u8 = new Uint8Array(arrayBuffer);
      if (u8.length >= 2 && u8[0] === 0x1f && u8[1] === 0x8b && typeof DecompressionStream !== "undefined") {
        const ds = new DecompressionStream("gzip");
        u8 = new Uint8Array(await new Response(new Blob([u8]).stream().pipeThrough(ds)).arrayBuffer());
      }
      const dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
      const td = new TextDecoder();
      const topPos = { p: 0 };
      const tileRecs = [];

      while (topPos.p < u8.length) {
        const tag = readMvtVarint(u8, topPos);
        const fn = Math.floor(tag / 8), wt = tag & 7;
        if (fn === 3 && wt === 2) {
          const lLen = readMvtVarint(u8, topPos);
          const lEnd = Math.min(u8.length, topPos.p + lLen);
          const lPos = { p: topPos.p };
          let layerName = "", extent = 4096, abortLayer = false;
          const keySlices = [], valSlices = [], featSlices = [];

          while (lPos.p < lEnd) {
            const lTag = readMvtVarint(u8, lPos);
            const lFn = Math.floor(lTag / 8), lWt = lTag & 7;
            if (lFn === 1 && lWt === 2) {
              const sLen = readMvtVarint(u8, lPos);
              layerName = td.decode(u8.subarray(lPos.p, lPos.p + sLen));
              lPos.p += sLen;
              if (layerName !== "building") { abortLayer = true; break; }
            } else if (lFn === 2 && lWt === 2) {
              const fLen = readMvtVarint(u8, lPos);
              featSlices.push([lPos.p, lPos.p + fLen]);
              lPos.p += fLen;
            } else if (lFn === 3 && lWt === 2) {
              const kLen = readMvtVarint(u8, lPos);
              keySlices.push([lPos.p, lPos.p + kLen]);
              lPos.p += kLen;
            } else if (lFn === 4 && lWt === 2) {
              const vLen = readMvtVarint(u8, lPos);
              valSlices.push([lPos.p, lPos.p + vLen]);
              lPos.p += vLen;
            } else if (lFn === 5 && lWt === 0) {
              extent = readMvtVarint(u8, lPos) || 4096;
            } else {
              skipMvtField(u8, lPos, lWt);
            }
          }
          topPos.p = lEnd;
          if (abortLayer || layerName !== "building") continue;

          const keys = keySlices.map(([s, e]) => td.decode(u8.subarray(s, e)));
          const vals = valSlices.map(([s, e]) => {
            const vp = { p: s };
            let out = null;
            while (vp.p < e) {
              const vt = readMvtVarint(u8, vp);
              const vf = Math.floor(vt / 8), vw = vt & 7;
              if (vf === 1 && vw === 2) { const sl = readMvtVarint(u8, vp); out = td.decode(u8.subarray(vp.p, vp.p + sl)); vp.p += sl; }
              else if (vf === 2 && vw === 5) { out = dv.getFloat32(vp.p, true); vp.p += 4; }
              else if (vf === 3 && vw === 1) { out = dv.getFloat64(vp.p, true); vp.p += 8; }
              else if ((vf === 4 || vf === 5) && vw === 0) { out = readMvtVarint(u8, vp); }
              else if (vf === 6 && vw === 0) { const zv = readMvtVarint(u8, vp); out = (zv >>> 1) ^ -(zv & 1); }
              else if (vf === 7 && vw === 0) { out = Boolean(readMvtVarint(u8, vp)); }
              else skipMvtField(u8, vp, vw);
            }
            return out;
          });

          const nTiles = 16384.0;
          for (const [fs, fe] of featSlices) {
            const fp = { p: fs };
            let fType = 0, tStart = 0, tEnd = 0, gStart = 0, gEnd = 0;
            while (fp.p < fe) {
              const ft = readMvtVarint(u8, fp);
              const ff = Math.floor(ft / 8), fw = ft & 7;
              if (ff === 2 && fw === 2) { const tl = readMvtVarint(u8, fp); tStart = fp.p; tEnd = fp.p + tl; fp.p = tEnd; }
              else if (ff === 3 && fw === 0) { fType = readMvtVarint(u8, fp); }
              else if (ff === 4 && fw === 2) { const gl = readMvtVarint(u8, fp); gStart = fp.p; gEnd = fp.p + gl; fp.p = gEnd; }
              else skipMvtField(u8, fp, fw);
            }
            if (fType !== 3 || gEnd <= gStart) continue;

            let hide3d = false, rawH = 0, minH = 0;
            if (tEnd > tStart) {
              const tp = { p: tStart };
              while (tp.p < tEnd) {
                const ki = readMvtVarint(u8, tp);
                const vi = readMvtVarint(u8, tp);
                const kName = keys[ki];
                const vVal = vals[vi];
                if (kName === "hide_3d" && vVal === true) hide3d = true;
                else if (kName === "render_height" || (kName === "height" && !rawH)) rawH = parseFloat(vVal) || 0;
                else if (kName === "render_min_height" || (kName === "min_height" && !minH)) minH = Math.max(0, parseFloat(vVal) || 0);
              }
            }
            if (hide3d) continue;

            const gp = { p: gStart };
            let cx = 0, cy = 0, curRing = null;
            const rawRings = [];
            while (gp.p < gEnd) {
              const cmdInt = readMvtVarint(u8, gp);
              const cmd = cmdInt & 7, cnt = cmdInt >>> 3;
              if (cmd === 1) {
                for (let c = 0; c < cnt; c++) {
                  const dx = readMvtVarint(u8, gp), dy = readMvtVarint(u8, gp);
                  cx += (dx >>> 1) ^ -(dx & 1);
                  cy += (dy >>> 1) ^ -(dy & 1);
                  if (curRing && curRing.length >= 3) rawRings.push(curRing);
                  curRing = [[cx, cy]];
                }
              } else if (cmd === 2) {
                for (let c = 0; c < cnt; c++) {
                  const dx = readMvtVarint(u8, gp), dy = readMvtVarint(u8, gp);
                  cx += (dx >>> 1) ^ -(dx & 1);
                  cy += (dy >>> 1) ^ -(dy & 1);
                  if (curRing) curRing.push([cx, cy]);
                }
              } else if (cmd === 7) {
                if (curRing && curRing.length >= 3) rawRings.push(curRing);
                curRing = null;
              } else {
                break;
              }
            }
            if (curRing && curRing.length >= 3) rawRings.push(curRing);

            let curOuter = null, curHoles = [];
            for (const r of rawRings) {
              let sa = 0;
              for (let i = 0; i < r.length; i++) {
                const [x0, y0] = r[i], [x1, y1] = r[(i + 1) % r.length];
                sa += x0 * y1 - x1 * y0;
              }
              if (Math.abs(sa) < 1e-3) continue;
              const ptsLL = r.map(([px, py]) => {
                const lon = ((tileX + px / extent) / nTiles) * 360.0 - 180.0;
                const lat = (Math.atan(Math.sinh(Math.PI * (1.0 - (2.0 * (tileY + py / extent)) / nTiles))) * 180.0) / Math.PI;
                return [lon, lat];
              });
              ptsLL.push(ptsLL[0]);
              if (sa > 0) {
                if (curOuter) {
                  const rec = buildCachedBuildingRec(curOuter, curHoles, rawH, minH);
                  if (rec) tileRecs.push(rec);
                }
                curOuter = ptsLL;
                curHoles = [];
              } else if (curOuter) {
                curHoles.push(ptsLL);
              }
            }
            if (curOuter) {
              const rec = buildCachedBuildingRec(curOuter, curHoles, rawH, minH);
              if (rec) tileRecs.push(rec);
            }
          }
        } else {
          skipMvtField(u8, topPos, wt);
        }
      }
      storeTileRecsLru(`${tileX}/${tileY}`, tileX, tileY, tileRecs);
      return tileRecs.length;
    }

    function ensureZ14ViewportBuildings() {
      if (!map3d || map3dContextLost || !is3DBlocksEnabled || currentCameraDim === "2D") return;
      const zNow = map3d.getZoom();
      if (zNow < 8.8) return;

      if (!openFreeMapTileTemplate) {
        if (!openFreeMapTileJsonPromise) {
          openFreeMapTileJsonPromise = fetch("https://tiles.openfreemap.org/planet")
            .then(r => r.ok ? r.json() : null)
            .then(tj => {
              if (tj && Array.isArray(tj.tiles) && tj.tiles[0]) {
                openFreeMapTileTemplate = tj.tiles[0];
                ensureZ14ViewportBuildings();
              }
            })
            .catch(() => { openFreeMapTileJsonPromise = null; });
        }
        return;
      }

      const c = map3d.getCenter();
      const [cxT, cyT] = lonLatToZ14Tile(c.lng, c.lat);
      const wanted = [];
      const seenT = new Set();
      const pushTile = (tx, ty) => {
        const k = `${tx}/${ty}`;
        if (osmZ14TileBuildings.has(k)) {
          // Refresh LRU recency for active viewport tiles
          const ent = osmZ14TileBuildings.get(k);
          osmZ14TileBuildings.delete(k);
          osmZ14TileBuildings.set(k, ent);
          return;
        }
        if (seenT.has(k) || fetchedZ14TileKeys.has(k) || inflightZ14TileKeys.has(k)) return;
        seenT.add(k);
        wanted.push([tx, ty, Math.hypot(tx - cxT, ty - cyT)]);
      };

      if (zNow >= 12.2) {
        const b = map3d.getBounds();
        const [minTxRaw, minTyRaw] = lonLatToZ14Tile(b.getWest(), b.getNorth());
        const [maxTxRaw, maxTyRaw] = lonLatToZ14Tile(b.getEast(), b.getSouth());
        const halfSpan = zNow >= 14.5 ? 2 : 4;
        const x0 = Math.max(minTxRaw, cxT - halfSpan);
        const x1 = Math.min(maxTxRaw, cxT + halfSpan);
        const y0 = Math.max(minTyRaw, cyT - halfSpan);
        const y1 = Math.min(maxTyRaw, cyT + halfSpan);
        for (let tx = x0; tx <= x1; tx++) {
          for (let ty = y0; ty <= y1; ty++) {
            pushTile(tx, ty);
          }
        }
      } else {
        for (let dx = -2; dx <= 2; dx++) {
          for (let dy = -2; dy <= 2; dy++) {
            pushTile(cxT + dx, cyT + dy);
          }
        }
      }

      if (zNow < 13.9) {
        for (const [sx, sy] of CORE_UAE_Z14_SKYLINE_TILES) {
          if (Math.hypot(sx - cxT, sy - cyT) <= (zNow >= 12.2 ? 12 : 34)) {
            pushTile(sx, sy);
          }
        }
      }

      if (!wanted.length) return;
      wanted.sort((a, b) => a[2] - b[2]);
      const batch = wanted.slice(0, 10);
      let anyAdded = false;

      Promise.all(batch.map(async ([tx, ty]) => {
        const k = `${tx}/${ty}`;
        inflightZ14TileKeys.add(k);
        try {
          const tileUrl = openFreeMapTileTemplate
            .replace("{z}", "14")
            .replace("{x}", String(tx))
            .replace("{y}", String(ty));
          const resp = await fetch(tileUrl);
          if (resp.ok) {
            const ab = await resp.arrayBuffer();
            const nAdded = await decodeMvtBuildingBuffer(ab, tx, ty);
            fetchedZ14TileKeys.add(k);
            if (nAdded > 0) anyAdded = true;
          } else if (resp.status === 204 || resp.status === 404) {
            fetchedZ14TileKeys.add(k);
          }
        } catch (_) {
          // Transient tile fetch failure; allow future retry
        } finally {
          inflightZ14TileKeys.delete(k);
        }
      })).then(() => {
        if (anyAdded) {
          scheduleOsmCityRebuild(75, true);
        }
        if (wanted.length > batch.length) {
          setTimeout(ensureZ14ViewportBuildings, 35);
        }
      });
    }

    // Rebuilds All Surrounding Real OpenStreetMap 3D City Buildings + All 36 Non-Selected Task 2 Projects Across ALL Zooms (z=8.8..19)
    function rebuildOsmCityScene() {
      if (!three3DLayer || !three3DLayer.scene || !map3d || !map3dLoaded || typeof THREE === "undefined") return;
      const zNow = map3d.getZoom();
      if (zNow < 8.8) return;
      ensureHaioEnvironmentAndLights();

      // Stream & warm authoritative z=14 building footprints across viewport + Dubai/Sharjah corridors
      ensureZ14ViewportBuildings();

      // Instant zero-latency seed on initial close-zoom frame before the first z=14 .pbf stream resolves; NEVER read generalised z<14 tiles!
      let transientSeedRecs = null;
      if (osmZ14TileBuildings.size === 0 && zNow >= 14.0 && map3d.getLayer("osm-3d-buildings")) {
        transientSeedRecs = [];
        const rawFeats = map3d.querySourceFeatures("openmaptiles", { sourceLayer: "building" }) || [];
        for (const f of rawFeats) {
          if (!f || !f.geometry) continue;
          const props = f.properties || {};
          if (props.hide_3d === true) continue;
          const rawH = parseFloat(props.render_height ?? props.height ?? 0);
          const minH = Math.max(0, parseFloat(props.render_min_height ?? props.min_height ?? 0));
          const polys = f.geometry.type === "Polygon"
            ? [f.geometry.coordinates]
            : (f.geometry.type === "MultiPolygon" ? f.geometry.coordinates : []);
          for (const poly of polys) {
            if (poly && poly[0] && poly[0].length >= 4) {
              const rec = buildCachedBuildingRec(poly[0], poly.length > 1 ? poly.slice(1) : null, rawH, minH);
              if (rec) transientSeedRecs.push(rec);
            }
          }
        }
      }

      if (!three3DLayer.cityFacadeMats) {
        three3DLayer.cityFacadeMats = createCityFacadeMaterials();
      }
      if (!three3DLayer.cityRoofMat) {
        three3DLayer.cityRoofMat = new THREE.MeshBasicMaterial({
          vertexColors: true,
          side: THREE.DoubleSide,
          polygonOffset: true,
          polygonOffsetFactor: 1,
          polygonOffsetUnits: 1
        });
      }

      const [originLon, originLat] = three3DLayer.originLonLat || [55.2650, 25.1850];
      const camCenter = map3d.getCenter();
      const [camX, camY] = lonLatToOriginEnu(camCenter.lng, camCenter.lat, originLon, originLat);
      three3DLayer.lastCityBuildCenter = [camCenter.lng, camCenter.lat];
      three3DLayer.lastCityBuildZoom = zNow;
      const excludeRad = three3DLayer.heroExcludeRadiusM || 56.0;

      // Zoom-adaptive horizon radius & LOD so L4 (Project), L3 (Community), L2 (Emirate), and L1 (UAE) keep full 3D skylines at 60 FPS
      let maxCamDist = 6800.0;
      let cityCap = IS_SAFARI_WEBKIT ? 9500 : 14000;
      let isDetailLod = true;
      if (zNow < 10.4) {
        maxCamDist = 115000.0;
        cityCap = IS_SAFARI_WEBKIT ? 16000 : 22000;
        isDetailLod = false;
      } else if (zNow < 12.2) {
        maxCamDist = 48000.0;
        cityCap = IS_SAFARI_WEBKIT ? 24000 : 32000;
        isDetailLod = false;
      } else if (zNow < 14.2) {
        maxCamDist = 19500.0;
        cityCap = IS_SAFARI_WEBKIT ? 28000 : 38000;
        isDetailLod = false;
      }

      // Build list of active non-selected Task 2 Flagship Projects & JVC Sub-Clusters so we also render all 36 in 3D simultaneously
      const emFilter = document.getElementById("emirateSelect") ? document.getElementById("emirateSelect").value : "ALL";
      const showProjs = document.getElementById("chk-L1")?.checked ?? true;
      const showSubdevs = document.getElementById("chk-L2")?.checked ?? false;
      const otherProjectSites = [];
      if (showProjs && Array.isArray(DATA.projects)) {
        for (const p of DATA.projects) {
          if (p.project_id === selected3DProjectId) continue;
          if (emFilter !== "ALL" && p.emirate !== emFilter) continue;
          const [pLat, pLon] = parseCoord(p.coordinates);
          const [px, py] = lonLatToOriginEnu(pLon, pLat, originLon, originLat);
          if (Math.hypot(px - camX, py - camY) <= maxCamDist) {
            otherProjectSites.push({ ent: p, px, py, pLon, pLat });
          }
        }
      }
      if ((showSubdevs || zNow < 14.5) && Array.isArray(DATA.subdevs)) {
        for (const sd of DATA.subdevs) {
          if (sd.subdev_id === selected3DProjectId) continue;
          if (emFilter !== "ALL" && sd.emirate !== emFilter) continue;
          const [px, py] = lonLatToOriginEnu(sd.longitude, sd.latitude, originLon, originLat);
          if (Math.hypot(px - camX, py - camY) <= maxCamDist) {
            otherProjectSites.push({ ent: sd, px, py, pLon: sd.longitude, pLat: sd.latitude });
          }
        }
      }

      // Single merged metric shader wall buffer (with hdbBand & hdbWall attributes) + 3D roof/trellis/plant/tree buffer
      const wallPos = [];
      const wallNorm = [];
      const wallUv = [];
      const wallCol = [];
      const wallBand = [];
      const wallMeta = [];

      const roofPos = [];
      const roofNorm = [];
      const roofCol = [];

      function pushMetricShaderWallRing(ring2d, z0, z1, baseRgb, bandRgb, schemeCode, topHeightM, invertNormals = false) {
        const openRing = (ring2d.length > 3 && Math.hypot(ring2d[0][0] - ring2d[ring2d.length - 1][0], ring2d[0][1] - ring2d[ring2d.length - 1][1]) < 1e-4)
          ? ring2d.slice(0, -1)
          : ring2d;
        if (openRing.length < 3 || z1 <= z0) return;

        let cx = 0, cy = 0;
        for (const [x, y] of openRing) { cx += x; cy += y; }
        cx /= openRing.length; cy /= openRing.length;

        const v0 = z0 / 24.0;
        const v1 = z1 / 24.0;

        for (let i = 0; i < openRing.length; i++) {
          const [x0, y0] = openRing[i];
          const [x1, y1] = openRing[(i + 1) % openRing.length];
          const dx = x1 - x0, dy = y1 - y0;
          const segLen = Math.hypot(dx, dy);
          if (segLen < 0.10) continue;

          let nx = dy / segLen, ny = -dx / segLen;
          const mx = (x0 + x1) * 0.5 - cx, my = (y0 + y1) * 0.5 - cy;
          if (nx * mx + ny * my < 0) { nx = -nx; ny = -ny; }
          if (invertNormals) { nx = -nx; ny = -ny; }

          const isFront = (segLen >= 5.5) ? 1.0 : 0.0;
          const u0 = 0.0;
          const u1 = segLen / 16.0;

          wallPos.push(
            x0, y0, z0, x1, y1, z0, x1, y1, z1,
            x0, y0, z0, x1, y1, z1, x0, y0, z1
          );
          for (let k = 0; k < 6; k++) {
            wallNorm.push(nx, ny, 0);
            wallCol.push(baseRgb[0], baseRgb[1], baseRgb[2]);
            wallBand.push(bandRgb[0], bandRgb[1], bandRgb[2], topHeightM);
          }
          wallUv.push(
            u0, v0, u1, v0, u1, v1,
            u0, v0, u1, v1, u0, v1
          );
          // vHdbWall = vec4(alongWallMetersU, wallLengthMeters, isFrontFlag, schemeCode)
          wallMeta.push(
            0.0, segLen, isFront, schemeCode,
            segLen, segLen, isFront, schemeCode,
            segLen, segLen, isFront, schemeCode,
            0.0, segLen, isFront, schemeCode,
            segLen, segLen, isFront, schemeCode,
            0.0, segLen, isFront, schemeCode
          );
        }
      }

      function pushSolidRoofPoly(ring2d, z0, z1, sideRgb, topRgb, holes2d = null) {
        const openRing = (ring2d.length > 3 && Math.hypot(ring2d[0][0] - ring2d[ring2d.length - 1][0], ring2d[0][1] - ring2d[ring2d.length - 1][1]) < 1e-4)
          ? ring2d.slice(0, -1)
          : ring2d;
        if (openRing.length < 3) return;

        let cx = 0, cy = 0;
        for (const [x, y] of openRing) { cx += x; cy += y; }
        cx /= openRing.length; cy /= openRing.length;

        const emitSideWalls = (rPts, flipInward) => {
          for (let i = 0; i < rPts.length; i++) {
            const [x0, y0] = rPts[i];
            const [x1, y1] = rPts[(i + 1) % rPts.length];
            const dx = x1 - x0, dy = y1 - y0;
            const segLen = Math.hypot(dx, dy);
            if (segLen < 0.06) continue;
            let nx = dy / segLen, ny = -dx / segLen;
            const mx = (x0 + x1) * 0.5 - cx, my = (y0 + y1) * 0.5 - cy;
            if (nx * mx + ny * my < 0) { nx = -nx; ny = -ny; }
            if (flipInward) { nx = -nx; ny = -ny; }
            roofPos.push(
              x0, y0, z0, x1, y1, z0, x1, y1, z1,
              x0, y0, z0, x1, y1, z1, x0, y0, z1
            );
            const sideLit = 0.62 + 0.34 * Math.max(0.0, nx * 0.52 - ny * 0.48);
            const sr = Math.min(1.0, sideRgb[0] * sideLit);
            const sg = Math.min(1.0, sideRgb[1] * sideLit);
            const sb = Math.min(1.0, sideRgb[2] * sideLit);
            for (let k = 0; k < 6; k++) {
              roofNorm.push(nx, ny, 0);
              roofCol.push(sr, sg, sb);
            }
          }
        };

        if (z1 > z0 && sideRgb) {
          emitSideWalls(openRing, false);
          if (holes2d && holes2d.length) {
            for (const hr of holes2d) {
              if (hr && hr.length >= 3) emitSideWalls(hr, true);
            }
          }
        }

        if (topRgb && typeof THREE.ShapeUtils !== "undefined" && openRing.length <= 450) {
          const contour = openRing.map(([x, y]) => new THREE.Vector2(x, y));
          const holeVecs = (holes2d && holes2d.length)
            ? holes2d.filter(hr => hr && hr.length >= 3).map(hr => hr.map(([x, y]) => new THREE.Vector2(x, y)))
            : [];
          const tris = THREE.ShapeUtils.triangulateShape(contour, holeVecs);
          const allPts = holeVecs.length ? openRing.concat(...holes2d.filter(hr => hr && hr.length >= 3)) : openRing;
          const tr = Math.min(1.0, topRgb[0] * 0.92);
          const tg = Math.min(1.0, topRgb[1] * 0.92);
          const tb = Math.min(1.0, topRgb[2] * 0.92);
          for (const [i0, i1, i2] of tris) {
            const a = allPts[i0], b = allPts[i1], c = allPts[i2];
            if (!a || !b || !c) continue;
            roofPos.push(a[0], a[1], z1, b[0], b[1], z1, c[0], c[1], z1);
            for (let k = 0; k < 3; k++) {
              roofNorm.push(0, 0, 1);
              roofCol.push(tr, tg, tb);
            }
          }
        }
      }

      // Pitched 3D Hip/Gable Roof for Low-Rise Villas & Townhouses (like haio.sg landedRoof)
      function pushPitchedVillaRoof(ring2d, zBase, ridgeH, roofRgb) {
        const openRing = (ring2d.length > 3 && Math.hypot(ring2d[0][0] - ring2d[ring2d.length - 1][0], ring2d[0][1] - ring2d[ring2d.length - 1][1]) < 1e-4)
          ? ring2d.slice(0, -1)
          : ring2d;
        if (openRing.length < 3) return;
        let cx = 0, cy = 0;
        for (const [x, y] of openRing) { cx += x; cy += y; }
        cx /= openRing.length; cy /= openRing.length;
        const zPeak = zBase + ridgeH;
        for (let i = 0; i < openRing.length; i++) {
          const [x0, y0] = openRing[i];
          const [x1, y1] = openRing[(i + 1) % openRing.length];
          const ux = x1 - x0, uy = y1 - y0;
          const vx = cx - x0, vy = cy - y0;
          let nx = uy * ridgeH, ny = -ux * ridgeH, nz = ux * vy - uy * vx;
          const nl = Math.hypot(nx, ny, nz) || 1;
          nx /= nl; ny /= nl; nz = Math.abs(nz / nl);
          const pLit = 0.64 + 0.34 * Math.max(0.0, nx * 0.45 - ny * 0.45 + nz * 0.76);
          const pr = Math.min(1.0, roofRgb[0] * pLit);
          const pg = Math.min(1.0, roofRgb[1] * pLit);
          const pb = Math.min(1.0, roofRgb[2] * pLit);
          roofPos.push(x0, y0, zBase, x1, y1, zBase, cx, cy, zPeak);
          for (let k = 0; k < 3; k++) {
            roofNorm.push(nx, ny, nz);
            roofCol.push(pr, pg, pb);
          }
        }
      }

      const candidates = [];
      const seenWorldKeys = new Set();
      const degLatRadius = maxCamDist / 110000.0;
      const degLonRadius = maxCamDist / 98000.0;

      const considerRecList = (recList) => {
        for (let ri = 0; ri < recList.length; ri++) {
          const bRec = recList[ri];
          const { worldKey, outerLonLat, holesLonLat, polyLon, polyLat, h, minH, areaM2, effR, blockHash, posHash } = bRec;
          if (Math.abs(polyLat - camCenter.lat) > degLatRadius || Math.abs(polyLon - camCenter.lng) > degLonRadius) continue;

          if (zNow < 10.4) {
            if (h < 20.0 && areaM2 < 850.0) continue;
          } else if (zNow < 12.2) {
            if (h < 12.0 && areaM2 < 420.0) continue;
          } else if (zNow < 13.8) {
            if (h < 14.0 && areaM2 < 52.0) continue;
          }

          if (seenWorldKeys.has(worldKey)) continue;
          seenWorldKeys.add(worldKey);

          const [cxApprox, cyApprox] = lonLatToOriginEnu(polyLon, polyLat, originLon, originLat);
          const distFromCam = Math.hypot(cxApprox - camX, cyApprox - camY);
          if (distFromCam > maxCamDist) continue;
          const distFromOrigin = Math.hypot(cxApprox, cyApprox);
          if (distFromOrigin < excludeRad) continue;

          // Avoid low-rise construction-plot footprints intersecting our 36 non-selected flagship 3D tower parcels
          let insideFlagshipParcel = false;
          for (let pi = 0; pi < otherProjectSites.length; pi++) {
            const ps = otherProjectSites[pi];
            if (Math.hypot(cxApprox - ps.px, cyApprox - ps.py) < 36.0 && h < 120.0) {
              insideFlagshipParcel = true;
              break;
            }
          }
          if (insideFlagshipParcel) continue;

          const nPts = outerLonLat.length - 1;
          const enuRing = new Array(nPts);
          let cx = 0, cy = 0, minVertDist = Infinity;
          for (let i = 0; i < nPts; i++) {
            const [ex, ey] = lonLatToOriginEnu(outerLonLat[i][0], outerLonLat[i][1], originLon, originLat);
            enuRing[i] = [ex, ey];
            cx += ex;
            cy += ey;
            if (distFromOrigin < excludeRad * 2.2) {
              const vd = Math.hypot(ex, ey);
              if (vd < minVertDist) minVertDist = vd;
            }
          }
          if (minVertDist < excludeRad * 0.80) continue;
          cx /= nPts;
          cy /= nPts;

          const holesEnu = [];
          if (holesLonLat && holesLonLat.length && (isDetailLod || areaM2 >= 600.0)) {
            for (let hi = 0; hi < holesLonLat.length; hi++) {
              const hLL = holesLonLat[hi];
              if (!hLL || hLL.length < 4) continue;
              const hRing = [];
              for (let k = 0; k < hLL.length - 1; k++) {
                hRing.push(lonLatToOriginEnu(hLL[k][0], hLL[k][1], originLon, originLat));
              }
              if (hRing.length >= 3) holesEnu.push(hRing);
            }
          }

          const heightBoost = h >= 120.0 ? 8500.0 : (h >= 45.0 ? 4200.0 : ((h >= 18.0 || areaM2 >= 380.0) ? 1600.0 : 0.0));
          candidates.push({
            enuRing, holesEnu, cx, cy, polyLon, polyLat, h, minH, effR, areaM2,
            distFromOrigin, distFromCam, heightBoost, posHash, blockHash
          });
        }
      };

      for (const tileEnt of osmZ14TileBuildings.values()) {
        if (Math.abs(tileEnt.cLat - camCenter.lat) > degLatRadius + 0.035 || Math.abs(tileEnt.cLon - camCenter.lng) > degLonRadius + 0.035) continue;
        considerRecList(tileEnt.recs);
      }
      if (transientSeedRecs && transientSeedRecs.length) {
        considerRecList(transientSeedRecs);
      }

      // Sort by camera distance with skyline priority so 100% of nearby blocks + all skyline towers/malls render completely
      candidates.sort((a, b) => (a.distFromCam - a.heightBoost) - (b.distFromCam - b.heightBoost));
      const baseMaxBuildings = Math.min(950, candidates.length);
      const maxBuildings = Math.min(cityCap, candidates.length);
      three3DLayer.osmCityTruncated = (candidates.length > maxBuildings || candidates.length > baseMaxBuildings);

      // Haio.sg's Condo Stone & Metallic Fin Palettes + Skyscraper Curtain-Wall Palettes + Hotel, Mall & Villa Palettes
      const CONDO_PALETTES = [
        { base: [0.92, 0.90, 0.86], band: [0.64, 0.45, 0.30] }, // Warm limestone + copper bronze fin
        { base: [0.89, 0.87, 0.83], band: [0.72, 0.63, 0.48] }, // Travertine + champagne gold fin
        { base: [0.86, 0.88, 0.90], band: [0.34, 0.42, 0.50] }, // Cool architectural grey + slate blue fin
        { base: [0.94, 0.92, 0.88], band: [0.46, 0.36, 0.28] }, // Ivory stone + dark espresso bronze fin
        { base: [0.84, 0.79, 0.73], band: [0.58, 0.34, 0.26] }, // Warm sandstone + terracotta bronze fin
        { base: [0.90, 0.89, 0.87], band: [0.52, 0.55, 0.58] }, // Pearl precast + brushed titanium fin
        { base: [0.88, 0.84, 0.78], band: [0.68, 0.52, 0.36] }  // Gulf sand stone + warm amber bronze fin
      ];
      const OFFICE_PALETTES = [
        { base: [0.86, 0.83, 0.77], band: [0.44, 0.48, 0.52] }, // 800: Ribbed warm limestone & dark ribbon windows
        { base: [0.28, 0.45, 0.58], band: [0.74, 0.82, 0.90] }, // 801: Sapphire-silver reflective curtain wall with stainless mullions
        { base: [0.22, 0.28, 0.34], band: [0.68, 0.58, 0.42] }  // 802: Anthracite glass with champagne-bronze vertical fins
      ];
      const HOTEL_PALETTES = [
        { base: [0.30, 0.46, 0.58], band: [0.76, 0.68, 0.54] }, // 1200: Reflective azure curtain wall + champagne trim
        { base: [0.88, 0.83, 0.75], band: [0.56, 0.40, 0.30] }  // 1201: Warm travertine precast with recessed dark balconies
      ];
      const MALL_PALETTES = [
        { base: [0.84, 0.81, 0.76], band: [0.55, 0.48, 0.40] }, // 300: Faceted greige panels over white finned retail podium
        { base: [0.86, 0.81, 0.73], band: [0.42, 0.54, 0.62] }, // 301: Natural stone courses with corner glass curtain wall
        { base: [0.80, 0.76, 0.70], band: [0.62, 0.44, 0.30] }  // 302: Timber architectural fins & glass atrium
      ];
      const VILLA_PALETTES = [
        { base: [0.95, 0.92, 0.87], band: [0.35, 0.32, 0.28], roof: [0.58, 0.35, 0.26] },
        { base: [0.90, 0.86, 0.80], band: [0.28, 0.30, 0.32], roof: [0.34, 0.36, 0.38] },
        { base: [0.93, 0.89, 0.83], band: [0.48, 0.36, 0.26], roof: [0.52, 0.38, 0.28] }
      ];

      const burjCurtainPal = { base: [0.68, 0.80, 0.90], band: [0.92, 0.96, 1.00] };
      const burjSilverCapRgb = [0.80, 0.87, 0.94];
      const burjSpireSteelRgb = [0.90, 0.94, 0.98];
      const roofStoneRgb = [0.78, 0.75, 0.71];
      const mallRoofDeckRgb = [0.65, 0.64, 0.61];
      const roofSlabRgb = [0.54, 0.52, 0.49];
      const skyParapetRgb = [0.76, 0.80, 0.85];
      const skyRoofWellRgb = [0.50, 0.55, 0.60];
      const plantWallRgb = [0.48, 0.46, 0.43];
      const plantTopRgb = [0.64, 0.62, 0.58];
      const coolingRgb = [0.66, 0.69, 0.72];

      const extrudeAllWalls = (outerR, holesArr, z0, z1, baseC, bandC, sCode, topHM) => {
        pushMetricShaderWallRing(outerR, z0, z1, baseC, bandC, sCode, topHM, false);
        if (holesArr && holesArr.length) {
          for (const hr of holesArr) {
            pushMetricShaderWallRing(hr, z0, z1, baseC, bandC, sCode, topHM, true);
          }
        }
      };

      for (let idx = 0; idx < maxBuildings; idx++) {
        const { enuRing, holesEnu, cx, cy, polyLon, polyLat, h, minH, effR, areaM2, posHash, blockHash } = candidates[idx];

        // 0. Iconic Landmark: Burj Khalifa (28 stepped Y-lobes + 828m telescopic titanium spire) & ultra-supertalls
        const distToBurjM = Math.hypot((polyLon - 55.27418) * 100500.0, (polyLat - 25.19720) * 111320.0);
        if ((distToBurjM < 78.0 && h >= 14.0) || h >= 390.0) {
          extrudeAllWalls(enuRing, holesEnu, minH, h, burjCurtainPal.base, burjCurtainPal.band, 801, h);
          pushSolidRoofPoly(enuRing, isDetailLod ? Math.max(minH, h - 0.55) : h, isDetailLod ? (h + 0.65) : h, isDetailLod ? burjSilverCapRgb : null, burjSilverCapRgb, holesEnu);
          if (h >= 800.0) {
            // Seamlessly bridge the 710m hexagonal core up through the 828m telescopic structural titanium spire
            const s1 = makeArchFootprint("chamfer_oct", cx, cy, 7.2, 7.2, 0);
            const s2 = makeArchFootprint("chamfer_oct", cx, cy, 4.8, 4.8, 0);
            const s3 = makeArchFootprint("chamfer_oct", cx, cy, 2.8, 2.8, 0);
            const sTip = makeArchFootprint("chamfer_oct", cx, cy, 1.4, 1.4, 0);
            pushMetricShaderWallRing(s1, 706.0, 744.0, burjCurtainPal.base, burjCurtainPal.band, 801, 828.0, false);
            pushSolidRoofPoly(s1, 743.5, 744.5, burjSpireSteelRgb, burjSpireSteelRgb);
            pushMetricShaderWallRing(s2, 744.0, 778.0, burjCurtainPal.base, burjCurtainPal.band, 801, 828.0, false);
            pushSolidRoofPoly(s2, 777.5, 778.5, burjSpireSteelRgb, burjSpireSteelRgb);
            pushSolidRoofPoly(s3, 778.0, 808.0, burjSpireSteelRgb, burjSpireSteelRgb);
            pushSolidRoofPoly(sTip, 808.0, 828.5, [0.95, 0.97, 1.0], [0.98, 0.99, 1.0]);
          }
          continue;
        }

        // Fast Regional / Community LOD (z < 14.2): 1 metric GLSL wall shaft + 1 crisp roof cap per building -> 16,500+ buildings at 60 FPS!
        if (!isDetailLod) {
          let wScheme = 100 + (blockHash % 15);
          let wPal = CONDO_PALETTES[blockHash % CONDO_PALETTES.length];
          let wRoof = roofStoneRgb;
          if (h >= 140.0 || minH > 0 || (h >= 62.0 && effR < 13.5)) {
            const sIdx = blockHash % 4;
            wScheme = sIdx < 3 ? (800 + sIdx) : 1200;
            wPal = sIdx < 3 ? OFFICE_PALETTES[sIdx] : HOTEL_PALETTES[0];
            wRoof = skyParapetRgb;
          } else if (h <= 13.5 && areaM2 < 420.0 && minH === 0) {
            const vp = VILLA_PALETTES[posHash % VILLA_PALETTES.length];
            wScheme = 610 + (posHash % 4) * 10 + (posHash % 3);
            wPal = vp;
            wRoof = vp.roof;
          } else if (h <= 34.0 && areaM2 >= 850.0) {
            wPal = MALL_PALETTES[blockHash % MALL_PALETTES.length];
            wScheme = 300 + (blockHash % 3);
            wRoof = mallRoofDeckRgb;
          } else if (h >= 50.0 && (blockHash % 3 === 0)) {
            const oIdx = blockHash % 3;
            wScheme = 800 + oIdx;
            wPal = OFFICE_PALETTES[oIdx];
          }
          extrudeAllWalls(enuRing, holesEnu, minH, h, wPal.base, wPal.band, wScheme, h);
          pushSolidRoofPoly(enuRing, h, h, null, wRoof, holesEnu);
          continue;
        }

        // 1. Stepped Compound Skyscrapers, Skybridges (minH > 0), & Supertalls (Address Sky View, Emirates Towers, Index, Marina 101, etc.)
        if (h >= 150.0 || minH > 0 || (h >= 62.0 && effR < 13.5)) {
          const skyIdx = blockHash % 4;
          const skyScheme = skyIdx < 3 ? (800 + skyIdx) : 1200;
          const skyPal = skyIdx < 3 ? OFFICE_PALETTES[skyIdx] : HOTEL_PALETTES[0];
          extrudeAllWalls(enuRing, holesEnu, minH, h, skyPal.base, skyPal.band, skyScheme, h);
          pushSolidRoofPoly(enuRing, Math.max(minH, h - 0.45), h + 0.85, skyParapetRgb, skyParapetRgb, holesEnu);
          if (holesEnu.length === 0 && effR >= 4.5 && enuRing.length <= 48) {
            const wellR = scaleEnuRing(enuRing, 0.86);
            pushSolidRoofPoly(wellR, h + 0.85, h + 0.95, null, skyRoofWellRgb);
          }
          continue;
        }

        // 2. Low-Rise Villa / Townhouse (h <= 13.5m and area < 420 m²)
        if (h <= 13.5 && areaM2 < 420.0 && minH === 0) {
          const vp = VILLA_PALETTES[posHash % VILLA_PALETTES.length];
          const vScheme = 610 + (posHash % 4) * 10 + (posHash % 3);
          const lotRing = expandEnuRing(enuRing, 1.4);
          pushSolidRoofPoly(lotRing, 0.0, 0.30, [0.74, 0.71, 0.66], [0.44, 0.56, 0.38]);
          extrudeAllWalls(enuRing, holesEnu, 0.30, h, vp.base, vp.band, vScheme, h);
          if (holesEnu.length === 0 && enuRing.length <= 24) {
            pushPitchedVillaRoof(expandEnuRing(enuRing, 0.30), h, Math.min(2.6, Math.max(1.5, effR * 0.26)), vp.roof);
          } else {
            pushSolidRoofPoly(enuRing, h - 0.3, h + 0.45, roofStoneRgb, vp.roof, holesEnu);
          }
          continue;
        }

        // 3. Large Shopping Mall / Opera / Cultural & Retail Podium (Dubai Mall, Souk Al Bahar, Dubai Opera: h <= 34m and area >= 850 m²)
        if (h <= 34.0 && areaM2 >= 850.0) {
          const mp = MALL_PALETTES[blockHash % MALL_PALETTES.length];
          const mScheme = 300 + (blockHash % 3);
          extrudeAllWalls(enuRing, holesEnu, minH, h, mp.base, mp.band, mScheme, h);
          pushSolidRoofPoly(enuRing, Math.max(minH, h - 0.6), h + 0.85, roofStoneRgb, mallRoofDeckRgb, holesEnu);
          if (holesEnu.length === 0 && enuRing.length <= 44) {
            const insetRoof = scaleEnuRing(enuRing, 0.90);
            pushSolidRoofPoly(insetRoof, h + 0.85, h + 0.95, null, roofSlabRgb);
            const skylightRing = scaleEnuRing(enuRing, 0.42);
            pushSolidRoofPoly(skylightRing, h + 0.95, h + 3.0, [0.35, 0.52, 0.64], [0.48, 0.68, 0.80]);
          }
          continue;
        }

        // 4. High-Rise / Mid-Rise Buildings (Office 800..802, Hotel 1200..1201, or Condo 100..114) — Complete Continuous Shafts
        let schemeCode = 100 + (blockHash % 15);
        let pal = CONDO_PALETTES[blockHash % CONDO_PALETTES.length];
        let isOffice = false;

        if (h >= 50.0 && (blockHash % 3 === 0)) {
          const oIdx = blockHash % 3;
          schemeCode = 800 + oIdx;
          pal = OFFICE_PALETTES[oIdx];
          isOffice = true;
        } else if (h >= 34.0 && (blockHash % 5 === 1)) {
          const hIdx = blockHash % 2;
          schemeCode = 1200 + hIdx;
          pal = HOTEL_PALETTES[hIdx];
        }

        if (minH === 0 && effR >= 8.0 && holesEnu.length === 0 && enuRing.length <= 36) {
          const apronRing = expandEnuRing(enuRing, 1.6);
          pushSolidRoofPoly(apronRing, 0.0, 0.45, roofStoneRgb, [0.74, 0.71, 0.66]);
        }

        if (h >= 65.0 && effR >= 13.5 && minH === 0 && holesEnu.length === 0 && enuRing.length <= 36) {
          const podZ = Math.min(14.5, Math.max(9.5, Math.round(h * 0.12)));
          const podRing = expandEnuRing(enuRing, 1.8);
          pushMetricShaderWallRing(podRing, 0.45, podZ, pal.base, pal.band, schemeCode, h, false);
          pushSolidRoofPoly(podRing, podZ - 0.35, podZ + 0.40, roofStoneRgb, roofSlabRgb);
          pushMetricShaderWallRing(enuRing, podZ, h, pal.base, pal.band, schemeCode, h, false);
        } else {
          extrudeAllWalls(enuRing, holesEnu, minH, h, pal.base, pal.band, schemeCode, h);
        }

        // 5. Complete Architectural Rooftop: Perimeter Parapet + Recessed Roof Well + Mechanical Core
        pushSolidRoofPoly(enuRing, Math.max(minH, h - 0.45), h + 1.05, roofStoneRgb, roofStoneRgb, holesEnu);
        if (holesEnu.length === 0 && enuRing.length <= 48) {
          const wellRing = scaleEnuRing(enuRing, 0.88);
          pushSolidRoofPoly(wellRing, h + 1.05, h + 1.15, null, roofSlabRgb);
          if (effR >= 7.5 && h >= 20.0) {
            const plantRing = scaleEnuRing(enuRing, 0.40);
            const plantH = Math.min(4.0, Math.max(2.6, h * 0.035));
            pushSolidRoofPoly(plantRing, h + 1.15, h + 1.15 + plantH, plantWallRgb, plantTopRgb);
            if (isOffice) {
              const featRing = scaleEnuRing(enuRing, 0.64);
              pushSolidRoofPoly(featRing, h + 1.15, h + 2.4, coolingRgb, plantTopRgb);
            } else {
              const crownFrameOuter = scaleEnuRing(enuRing, 0.80);
              pushSolidRoofPoly(crownFrameOuter, h + 2.5, h + 3.05, pal.band, pal.base);
            }
          }
        }
      }

      // 6. Simultaneous 3D Architectural Massing for ALL 36 Non-Selected Task 2 Flagship Projects & JVC Sub-Clusters
      // Ensures PRJ-D10 (Burj Azizi 725m), PRJ-D11 (557m), PRJ-D20 (DIFC Zabeel), PRJ-D3 (Creek Harbour), PRJ-SH4, etc. ALL stand in 3D when zoomed out!
      for (const ps of otherProjectSites) {
        const pSpec = getProject3DSpec(ps.ent);
        const rotR = (pSpec.rotDeg * Math.PI) / 180.0;
        const pH = Math.max(42.0, pSpec.heightM || 140.0);
        const podRing = makeArchFootprint("chamfer_oct", ps.px, ps.py, 72, 54, rotR);
        pushMetricShaderWallRing(podRing, 0.0, 11.5, [0.88, 0.85, 0.79], [0.64, 0.48, 0.34], 301, pH, false);
        pushSolidRoofPoly(podRing, 11.0, 11.8, roofStoneRgb, [0.42, 0.66, 0.40]);

        if (pSpec.typology === "supertall_diamond") {
          const tPal = { base: [0.30, 0.48, 0.64], band: [0.84, 0.90, 0.96] };
          const zA = 11.8 + (pH - 32.0) * 0.56;
          const zB = 11.8 + (pH - 32.0) * 0.84;
          const zC = Math.max(zB + 12.0, pH - 20.0);
          const rA = makeArchFootprint("cruciform_spire", ps.px - 6.0, ps.py, 30, 24, rotR);
          const rSide = makeArchFootprint("chamfer_oct", ps.px + 10.0, ps.py + 5.0, 22, 18, rotR + 0.18);
          const rB = scaleEnuRing(rA, 0.78);
          const rC = scaleEnuRing(rA, 0.56);
          const rCrown = scaleEnuRing(rA, 0.32);
          pushMetricShaderWallRing(rA, 11.8, zA, tPal.base, tPal.band, 801, pH, false);
          pushMetricShaderWallRing(rSide, 11.8, zA * 0.92, tPal.base, tPal.band, 801, pH, false);
          pushSolidRoofPoly(rSide, zA * 0.92 - 0.5, zA * 0.92 + 0.8, skyParapetRgb, skyParapetRgb);
          pushMetricShaderWallRing(rB, zA, zB, tPal.base, tPal.band, 801, pH, false);
          pushSolidRoofPoly(rA, zA - 0.5, zA + 0.6, skyParapetRgb, skyParapetRgb);
          pushMetricShaderWallRing(rC, zB, zC, tPal.base, tPal.band, 801, pH, false);
          pushSolidRoofPoly(rB, zB - 0.5, zB + 0.6, skyParapetRgb, skyParapetRgb);
          pushSolidRoofPoly(rC, zC - 0.5, zC + 1.2, burjSilverCapRgb, burjSilverCapRgb);
          pushSolidRoofPoly(rCrown, zC + 1.2, pH, burjSpireSteelRgb, [0.96, 0.98, 1.0]);
        } else if (pSpec.typology === "organic_terraced") {
          const oPal = HOTEL_PALETTES[0];
          const r1 = makeArchFootprint("organic_oval", ps.px - 7.0, ps.py + 4.0, 32, 22, rotR);
          const r2 = makeArchFootprint("organic_oval", ps.px + 15.0, ps.py - 6.0, 25, 18, rotR - 0.25);
          pushMetricShaderWallRing(r1, 11.8, pH, oPal.base, oPal.band, 1200, pH, false);
          pushSolidRoofPoly(r1, pH - 0.5, pH + 1.0, skyParapetRgb, skyParapetRgb);
          pushMetricShaderWallRing(r2, 11.8, pH * 0.72, oPal.base, oPal.band, 1200, pH * 0.72, false);
          pushSolidRoofPoly(r2, pH * 0.72 - 0.5, pH * 0.72 + 0.8, skyParapetRgb, skyParapetRgb);
        } else if (pSpec.typology === "twin_triple_highrise") {
          const hPal = OFFICE_PALETTES[2];
          const t1 = makeArchFootprint("stepped_wing", ps.px - 18.0, ps.py + 8.0, 24, 16, rotR);
          const t2 = makeArchFootprint("stepped_wing", ps.px + 17.0, ps.py + 9.0, 22, 15, rotR + 0.45);
          const t3 = makeArchFootprint("chamfer_oct", ps.px, ps.py - 15.0, 22, 15, rotR - 0.30);
          pushMetricShaderWallRing(t1, 11.8, pH, hPal.base, hPal.band, 802, pH, false);
          pushSolidRoofPoly(t1, pH - 0.5, pH + 1.0, skyParapetRgb, skyParapetRgb);
          pushMetricShaderWallRing(t2, 11.8, pH * 0.82, hPal.base, hPal.band, 802, pH * 0.82, false);
          pushSolidRoofPoly(t2, pH * 0.82 - 0.5, pH * 0.82 + 0.9, skyParapetRgb, skyParapetRgb);
          pushMetricShaderWallRing(t3, 11.8, pH * 0.66, hPal.base, hPal.band, 802, pH * 0.66, false);
          pushSolidRoofPoly(t3, pH * 0.66 - 0.5, pH * 0.66 + 0.9, skyParapetRgb, skyParapetRgb);
        } else {
          const cPal = CONDO_PALETTES[pSpec.seed % CONDO_PALETTES.length];
          const cScheme = 100 + (pSpec.seed % 12);
          const wA = makeArchFootprint("u_boulevard", ps.px - 10.0, ps.py + 5.0, 40, 28, rotR);
          const wB = makeArchFootprint("chamfer_oct", ps.px + 18.0, ps.py - 8.0, 26, 20, rotR + 0.35);
          pushMetricShaderWallRing(wA, 11.8, pH, cPal.base, cPal.band, cScheme, pH, false);
          pushSolidRoofPoly(wA, pH - 0.5, pH + 0.9, roofStoneRgb, roofStoneRgb);
          pushMetricShaderWallRing(wB, 11.8, pH * 0.76, cPal.base, cPal.band, cScheme, pH * 0.76, false);
          pushSolidRoofPoly(wB, pH * 0.76 - 0.5, pH * 0.76 + 0.9, roofStoneRgb, roofStoneRgb);
        }
      }

      if (!wallPos.length && !roofPos.length) {
        three3DLayer.osmCityBuildingCount = 0;
        three3DLayer.osmCityTruncated = false;
        syncPhotorealistic3DVisibility();
        return;
      }

      if (three3DLayer.osmCityGroup) {
        disposeThreeGroup(three3DLayer.osmCityGroup, false);
        three3DLayer.scene.remove(three3DLayer.osmCityGroup);
      }

      const cityGroup = new THREE.Group();
      if (wallPos.length) {
        const wg = new THREE.BufferGeometry();
        wg.setAttribute("position", new THREE.Float32BufferAttribute(wallPos, 3));
        wg.setAttribute("normal", new THREE.Float32BufferAttribute(wallNorm, 3));
        wg.setAttribute("uv", new THREE.Float32BufferAttribute(wallUv, 2));
        wg.setAttribute("color", new THREE.Float32BufferAttribute(wallCol, 3));
        wg.setAttribute("hdbBand", new THREE.Float32BufferAttribute(wallBand, 4));
        wg.setAttribute("hdbWall", new THREE.Float32BufferAttribute(wallMeta, 4));
        const wm = new THREE.Mesh(wg, three3DLayer.cityFacadeMats[0]);
        wm.frustumCulled = false;
        cityGroup.add(wm);
      }

      if (roofPos.length) {
        const rg = new THREE.BufferGeometry();
        rg.setAttribute("position", new THREE.Float32BufferAttribute(roofPos, 3));
        rg.setAttribute("normal", new THREE.Float32BufferAttribute(roofNorm, 3));
        rg.setAttribute("color", new THREE.Float32BufferAttribute(roofCol, 3));
        const rm = new THREE.Mesh(rg, three3DLayer.cityRoofMat);
        rm.frustumCulled = false;
        cityGroup.add(rm);
      }

      three3DLayer.osmCityGroup = cityGroup;
      three3DLayer.osmCityBuildingCount = maxBuildings;
      three3DLayer.scene.add(cityGroup);
      syncPhotorealistic3DVisibility();
      if (map3d) map3d.triggerRepaint();
    }

    function scheduleOsmCityRebuild(delayMs = 220, resetExisting = true) {
      if (osmCityRebuildTimer) {
        if (!resetExisting) return;
        clearTimeout(osmCityRebuildTimer);
      }
      osmCityRebuildTimer = setTimeout(() => {
        osmCityRebuildTimer = null;
        rebuildOsmCityScene();
      }, delayMs);
    }

    function sync3DSunLighting() {
      if (map3d) map3d.triggerRepaint();
    }

    function createPhotorealistic3DCustomLayer() {
      const layer = {
        id: "haio-photoreal-3d-layer",
        type: "custom",
        renderingMode: "3d",
        originLonLat: [55.2650, 25.1850],
        lastCityBuildCenter: null,
        lastCityBuildZoom: null,
        heroExcludeRadiusM: 56.0,
        osmCityBuildingCount: 0,
        osmCityTruncated: false,
        heroRoofLocalVec: new THREE.Vector3(0, 0, 68.0),
        onAdd: function (mapInstance, gl) {
          this.map = mapInstance;
          this.scene = new THREE.Scene();
          this.renderCamera = new THREE.Camera();
          this.mat4Tmp = new THREE.Matrix4();
          this.localScaleMat = new THREE.Matrix4();

          this.renderer = new THREE.WebGLRenderer({
            canvas: mapInstance.getCanvas(),
            context: gl,
            antialias: !IS_SAFARI_WEBKIT
          });
          this.renderer.autoClear = false;

          mapInstance.getCanvas().addEventListener("webglcontextlost", () => {
            disposeAllThreeGpuResources();
          }, { passive: true });

          rebuildThreeHeroScene();
          ensureZ14ViewportBuildings();
          scheduleOsmCityRebuild(140);
        },
        onRemove: function () {
          disposeAllThreeGpuResources();
        },
        render: function (gl, matrix) {
          const calloutEl = document.getElementById("hero3DRoofCallout");
          if (!is3DBlocksEnabled || currentCameraDim === "2D" || map3dContextLost || !this.renderer || !this.scene) {
            if (calloutEl) calloutEl.style.display = "none";
            return;
          }
          const zNow = this.map.getZoom();
          if (zNow < 8.8) {
            if (calloutEl) calloutEl.style.display = "none";
            return;
          }

          const rawMat = (!Array.isArray(matrix) && matrix?.defaultProjectionData?.mainMatrix) || matrix;
          const p0 = haioProjectMerc(this.originLonLat[0], this.originLonLat[1]);
          const h0 = 1 / (HAIO_EARTH_CIRC * Math.cos((this.originLonLat[1] * Math.PI) / 180));
          // Exact 1:1 metric height at z>=13.8; smooth cartographic vertical legibility scale when zoomed far out (L3/L2/L1) so 3D skylines stay clearly visible from altitude
          const vScale = zNow >= 13.8 ? 1.0 : Math.min(2.65, 1.0 + (13.8 - zNow) * 0.36);
          this.localScaleMat.makeTranslation(p0[0], p0[1], 0).scale(new THREE.Vector3(h0, -h0, h0 * vScale));

          this.renderCamera.projectionMatrix.copy(this.mat4Tmp.fromArray(rawMat).multiply(this.localScaleMat));
          // Expand clip-space Z range (without altering X/Y projection or monotonic depth order) so 828m Burj Khalifa & 557m supertalls never clip against MapLibre's close-zoom near plane
          const pe = this.renderCamera.projectionMatrix.elements;
          pe[2] *= 0.18;
          pe[6] *= 0.18;
          pe[10] *= 0.18;
          pe[14] *= 0.18;
          this.renderCamera.projectionMatrixInverse.copy(this.renderCamera.projectionMatrix).invert();

          this.renderer.resetState();
          ensureHaioEnvironmentAndLights(true);
          // MapLibre v4 enables gl.SCISSOR_TEST to clip ground tiles at the 3D horizon line; disable it here so 828m Burj Khalifa & all skyscrapers soar cleanly into the sky!
          gl.disable(gl.SCISSOR_TEST);
          this.renderer.setScissorTest(false);
          gl.enable(gl.DEPTH_TEST);
          gl.depthFunc(gl.LEQUAL);
          gl.depthMask(true);
          gl.clear(gl.DEPTH_BUFFER_BIT);
          this.renderer.setViewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
          this.renderer.render(this.scene, this.renderCamera);
          this.renderer.resetState();

          const canvas = this.map.getCanvas();
          if (calloutEl && zNow >= 14.5) {
            const ndc = this.heroRoofLocalVec.clone().applyMatrix4(this.renderCamera.projectionMatrix);
            if (ndc.z >= -1 && ndc.z <= 1) {
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

    function attachThree3DLayerIfReady() {
      if (!map3d || !map3dLoaded || map3dContextLost) return;
      if (typeof THREE === "undefined") return;
      if (!map3d.getLayer("haio-photoreal-3d-layer")) {
        try {
          map3d.addLayer(createPhotorealistic3DCustomLayer());
          if (!is3DBlocksEnabled && map3d.getLayer("haio-photoreal-3d-layer")) {
            map3d.setLayoutProperty("haio-photoreal-3d-layer", "visibility", "none");
          }
        } catch (err) {
          console.warn("Three.js custom layer mount skipped:", err);
        }
      }
    }

    function attachOpenMapTilesVectorLayers() {
      if (!map3d || map3dContextLost) return;
      if (map3d.getSource("openmaptiles")) return;
      try {
        map3d.addSource("openmaptiles", {
          type: "vector",
          url: "https://tiles.openfreemap.org/planet"
        });
        const beforeHero = map3d.getLayer("haio-photoreal-3d-layer") ? "haio-photoreal-3d-layer" : undefined;
        const beforePrimaryRoads = map3d.getLayer("roads-casing-3d") ? "roads-casing-3d" : beforeHero;
        const showTrafficInit = document.getElementById("chk-L6")?.checked ?? true;
        const osmTrafficExprs = getOsmStreetTrafficExprs(currentTimeWindow);
        if (!map3d.getLayer("osm-city-traffic-casing")) {
          map3d.addLayer({
            id: "osm-city-traffic-casing",
            type: "line",
            source: "openmaptiles",
            "source-layer": "transportation",
            minzoom: 12.0,
            maxzoom: 22.0,
            filter: ["in", "class", "motorway", "trunk", "primary", "secondary", "tertiary", "minor"],
            layout: {
              visibility: showTrafficInit ? "visible" : "none",
              "line-cap": "round",
              "line-join": "round"
            },
            paint: {
              "line-color": osmTrafficExprs.casing,
              "line-width": [
                "interpolate", ["exponential", 1.45], ["zoom"],
                12.0, ["match", ["get", "class"], ["motorway", "trunk"], 3.8, "primary", 3.0, "secondary", 2.3, 0.0],
                14.0, ["match", ["get", "class"], ["motorway", "trunk"], 6.6, "primary", 5.2, "secondary", 4.3, "tertiary", 3.4, 2.5],
                16.0, ["match", ["get", "class"], ["motorway", "trunk"], 12.0, "primary", 9.8, "secondary", 8.2, "tertiary", 6.8, 5.4],
                18.0, ["match", ["get", "class"], ["motorway", "trunk"], 19.2, "primary", 15.8, "secondary", 13.0, "tertiary", 10.8, 8.8]
              ],
              "line-opacity": [
                "interpolate", ["linear"], ["zoom"],
                12.0, 0.90,
                13.8, 0.96,
                17.0, 0.98
              ]
            }
          }, beforePrimaryRoads);
        }
        if (!map3d.getLayer("osm-city-traffic-flow")) {
          map3d.addLayer({
            id: "osm-city-traffic-flow",
            type: "line",
            source: "openmaptiles",
            "source-layer": "transportation",
            minzoom: 12.0,
            maxzoom: 22.0,
            filter: ["in", "class", "motorway", "trunk", "primary", "secondary", "tertiary", "minor"],
            layout: {
              visibility: showTrafficInit ? "visible" : "none",
              "line-cap": "round",
              "line-join": "round"
            },
            paint: {
              "line-color": osmTrafficExprs.flow,
              "line-width": [
                "interpolate", ["exponential", 1.45], ["zoom"],
                12.0, ["match", ["get", "class"], ["motorway", "trunk"], 2.3, "primary", 1.8, "secondary", 1.3, 0.0],
                14.0, ["match", ["get", "class"], ["motorway", "trunk"], 4.4, "primary", 3.5, "secondary", 2.9, "tertiary", 2.2, 1.6],
                16.0, ["match", ["get", "class"], ["motorway", "trunk"], 8.6, "primary", 7.0, "secondary", 5.8, "tertiary", 4.7, 3.6],
                18.0, ["match", ["get", "class"], ["motorway", "trunk"], 14.2, "primary", 11.6, "secondary", 9.6, "tertiary", 7.8, 6.2]
              ],
              "line-opacity": 1.0
            }
          }, beforePrimaryRoads);
        }
        if (!map3d.getLayer("osm-3d-buildings")) {
          map3d.addLayer({
            id: "osm-3d-buildings",
            type: "fill-extrusion",
            source: "openmaptiles",
            "source-layer": "building",
            minzoom: 12.0,
            maxzoom: 22.0,
            filter: ["!=", ["get", "hide_3d"], true],
            layout: { visibility: is3DBlocksEnabled ? "visible" : "none" },
            paint: {
              "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
              "fill-extrusion-height": ["coalesce", ["get", "render_height"], 16],
              "fill-extrusion-color": [
                "interpolate", ["linear"], ["coalesce", ["get", "render_height"], 16],
                0, "#e8e3d9",
                40, "#dcd5c7",
                110, "#c5d2e0",
                320, "#9ab6cf",
                650, "#7ea3c4"
              ],
              "fill-extrusion-vertical-gradient": true,
              "fill-extrusion-opacity": is3DBlocksEnabled ? 0.82 : 0.0
            }
          }, beforeHero);
        }
        if (!map3d.getLayer("osm-road-labels")) {
          map3d.addLayer({
            id: "osm-road-labels",
            type: "symbol",
            source: "openmaptiles",
            "source-layer": "transportation_name",
            minzoom: 11,
            maxzoom: 18.5,
            layout: {
              "symbol-placement": "line",
              "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]],
              "text-font": ["Noto Sans Regular"],
              "text-size": 11
            },
            paint: {
              "text-color": "#f8fafc",
              "text-halo-color": "#0f172a",
              "text-halo-width": 1.6
            }
          });
        }
        if (!map3d.getLayer("osm-place-labels")) {
          map3d.addLayer({
            id: "osm-place-labels",
            type: "symbol",
            source: "openmaptiles",
            "source-layer": "place",
            minzoom: 10,
            maxzoom: 16.5,
            layout: {
              "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]],
              "text-font": ["Noto Sans Bold"],
              "text-size": 12
            },
            paint: {
              "text-color": "#ffffff",
              "text-halo-color": "rgba(15, 23, 42, 0.9)",
              "text-halo-width": 2.0
            }
          });
        }
        syncPhotorealistic3DVisibility();
      } catch (vecErr) {
        console.warn("Vector city layer deferred; raster + Three.js 3D active:", vecErr);
      }
    }

    function init3DMap() {
      if (typeof maplibregl === "undefined") {
        setCameraDimension("2D");
        return;
      }
      if (typeof maplibregl.supported === "function" && !maplibregl.supported()) {
        map3dContextLost = true;
        setCameraDimension("2D");
        return;
      }

      const defaultProj = DATA.projects.find(x => x.project_id === selected3DProjectId) || DATA.projects[0];
      const [initLat, initLon] = parseCoord(defaultProj.coordinates);
      const initSpec = getProject3DSpec(defaultProj);
      const initCam = getOptimalProject3DCamera(initLat, initLon, initSpec, false);
      const safeDpr = Math.min(window.devicePixelRatio || 1, IS_SAFARI_WEBKIT ? 1.25 : 2.0);
      const initMode = currentBasemapMode || "sat";
      const initBg = initMode === "dark" ? "#1a1d23" : (initMode === "light" ? "#e8e4d8" : "#162231");

      try {
        map3d = new maplibregl.Map({
          container: "map3dCanvas",
          center: [initCam.lon, initCam.lat],
          zoom: initCam.zoom,
          pitch: initCam.pitch,
          bearing: initCam.bearing,
          minZoom: 8.5,
          maxZoom: 19.2,
          maxBounds: [[51.0, 22.4], [56.8, 26.5]],
          pixelRatio: safeDpr,
          maxTileCacheSize: IS_SAFARI_WEBKIT ? 75 : 110,
          antialias: !IS_SAFARI_WEBKIT,
          preserveDrawingBuffer: true,
          fadeDuration: 0,
          attributionControl: false,
          style: {
            version: 8,
            glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
            sky: {
              "sky-color": initMode === "dark" ? "#0b1324" : "#6ea3d4",
              "horizon-color": initMode === "dark" ? "#1e293b" : "#dbe9f6",
              "sky-horizon-blend": 0.55
            },
            light: {
              anchor: "viewport",
              color: "#fffbeb",
              intensity: 0.62,
              position: [1.45, 215, 48]
            },
            sources: {
              "sat-tiles": {
                type: "raster",
                tiles: [
                  "https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                  "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                  "https://mt2.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                  "https://mt3.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
                ],
                tileSize: 256,
                maxzoom: IS_SAFARI_WEBKIT ? 17 : 19
              },
              "light-tiles": {
                type: "raster",
                tiles: [
                  "https://mt0.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                  "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                  "https://mt2.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                  "https://mt3.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
                ],
                tileSize: 256,
                maxzoom: IS_SAFARI_WEBKIT ? 17 : 19
              },
              "dark-tiles": {
                type: "raster",
                tiles: [
                  "https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
                ],
                tileSize: 256,
                maxzoom: 16
              },
              "dark-ref-tiles": {
                type: "raster",
                tiles: [
                  "https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
                ],
                tileSize: 256,
                maxzoom: 16
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
              },
              "projects-heat-source-3d": {
                type: "geojson",
                data: { type: "FeatureCollection", features: [] }
              },
              "intersections-3d": {
                type: "geojson",
                data: { type: "FeatureCollection", features: [] }
              },
              "incidents-3d": {
                type: "geojson",
                data: { type: "FeatureCollection", features: [] }
              },
              "transit-lines-3d": {
                type: "geojson",
                data: { type: "FeatureCollection", features: [] }
              },
              "transit-stations-3d": {
                type: "geojson",
                data: { type: "FeatureCollection", features: [] }
              },
              "facilities-3d": {
                type: "geojson",
                data: { type: "FeatureCollection", features: [] }
              },
              "parking-3d": {
                type: "geojson",
                data: { type: "FeatureCollection", features: [] }
              }
            },
            layers: [
              {
                id: "bg-dark-layer",
                type: "background",
                paint: { "background-color": initBg }
              },
              {
                id: "sat-raster-layer",
                type: "raster",
                source: "sat-tiles",
                layout: { visibility: initMode === "sat" ? "visible" : "none" },
                paint: { "raster-opacity": 1.0, "raster-contrast": -0.04, "raster-brightness-min": 0.05, "raster-saturation": 0.04 }
              },
              {
                id: "light-raster-layer",
                type: "raster",
                source: "light-tiles",
                layout: { visibility: initMode === "light" ? "visible" : "none" },
                paint: { "raster-opacity": 1.0 }
              },
              {
                id: "dark-raster-layer",
                type: "raster",
                source: "dark-tiles",
                layout: { visibility: initMode === "dark" ? "visible" : "none" },
                paint: { "raster-opacity": 1.0, "raster-contrast": 0.08 }
              },
              {
                id: "dark-ref-raster-layer",
                type: "raster",
                source: "dark-ref-tiles",
                layout: { visibility: initMode === "dark" ? "visible" : "none" },
                paint: { "raster-opacity": 0.96 }
              },
              {
                id: "communities-fill-3d",
                type: "fill",
                source: "communities-3d",
                maxzoom: 22,
                paint: {
                  "fill-color": ["get", "color"],
                  "fill-opacity": 0.08
                }
              },
              {
                id: "communities-line-3d",
                type: "line",
                source: "communities-3d",
                maxzoom: 22,
                paint: {
                  "line-color": ["get", "color"],
                  "line-width": 1.6,
                  "line-opacity": 0.72
                }
              },
              {
                id: "projects-heatmap-3d",
                type: "heatmap",
                source: "projects-heat-source-3d",
                maxzoom: 17.5,
                layout: { visibility: "none" },
                paint: {
                  "heatmap-weight": ["coalesce", ["get", "heatWeight"], 0.6],
                  "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 8, 1.1, 14, 2.6],
                  "heatmap-color": [
                    "interpolate", ["linear"], ["heatmap-density"],
                    0, "rgba(37, 99, 235, 0)",
                    0.2, "rgba(56, 189, 248, 0.55)",
                    0.45, "rgba(52, 211, 153, 0.72)",
                    0.7, "rgba(251, 191, 36, 0.85)",
                    1.0, "rgba(239, 68, 68, 0.95)"
                  ],
                  "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 8, 22, 13, 44, 16, 62],
                  "heatmap-opacity": 0.86
                }
              },
              {
                id: "projects-zone-fill-3d",
                type: "fill",
                source: "projects-zones-3d",
                maxzoom: 16.0,
                paint: {
                  "fill-color": ["get", "color"],
                  "fill-opacity": ["get", "fillOpacity"]
                }
              },
              {
                id: "projects-zone-line-3d",
                type: "line",
                source: "projects-zones-3d",
                maxzoom: 16.0,
                paint: {
                  "line-color": ["get", "color"],
                  "line-width": ["get", "lineWidth"],
                  "line-opacity": 0.92
                }
              },
              {
                id: "transit-line-3d",
                type: "line",
                source: "transit-lines-3d",
                maxzoom: 22,
                paint: {
                  "line-color": ["get", "color"],
                  "line-width": 3.0,
                  "line-opacity": 0.88
                }
              },
              {
                id: "roads-casing-3d",
                type: "line",
                source: "roads-3d",
                maxzoom: 22,
                layout: {
                  "line-cap": "round",
                  "line-join": "round"
                },
                paint: {
                  "line-color": ["coalesce", ["get", "casingColor"], "#0f172a"],
                  "line-width": [
                    "interpolate", ["exponential", 1.45], ["zoom"],
                    9, ["*", ["get", "casingWidth"], 0.80],
                    13, ["*", ["get", "casingWidth"], 1.32],
                    15.5, ["*", ["get", "casingWidth"], 2.15],
                    17.5, ["*", ["get", "casingWidth"], 3.35]
                  ],
                  "line-opacity": 0.98
                }
              },
              {
                id: "roads-traffic-3d",
                type: "line",
                source: "roads-3d",
                maxzoom: 22,
                layout: {
                  "line-cap": "round",
                  "line-join": "round"
                },
                paint: {
                  "line-color": ["get", "color"],
                  "line-width": [
                    "interpolate", ["exponential", 1.45], ["zoom"],
                    9, ["*", ["get", "trafficWidth"], 0.88],
                    13, ["*", ["get", "trafficWidth"], 1.50],
                    15.5, ["*", ["get", "trafficWidth"], 2.50],
                    17.5, ["*", ["get", "trafficWidth"], 3.95]
                  ],
                  "line-opacity": 1.0
                }
              },
              {
                id: "impacts-line-3d",
                type: "line",
                source: "impacts-3d",
                maxzoom: 22,
                paint: {
                  "line-color": "#fbbf24",
                  "line-width": 2.4,
                  "line-dasharray": [2, 2],
                  "line-opacity": 0.90
                }
              },
              {
                id: "transit-station-3d",
                type: "circle",
                source: "transit-stations-3d",
                maxzoom: 22,
                paint: {
                  "circle-radius": 4.8,
                  "circle-color": ["get", "color"],
                  "circle-stroke-color": "#ffffff",
                  "circle-stroke-width": 1.4
                }
              },
              {
                id: "facilities-circle-3d",
                type: "circle",
                source: "facilities-3d",
                maxzoom: 22,
                paint: {
                  "circle-radius": 5.0,
                  "circle-color": "#10b981",
                  "circle-stroke-color": "#064e3b",
                  "circle-stroke-width": 1.4
                }
              },
              {
                id: "parking-circle-3d",
                type: "circle",
                source: "parking-3d",
                maxzoom: 22,
                paint: {
                  "circle-radius": 5.6,
                  "circle-color": "#14b8a6",
                  "circle-stroke-color": "#ffffff",
                  "circle-stroke-width": 1.5
                }
              },
              {
                id: "intersections-circle-3d",
                type: "circle",
                source: "intersections-3d",
                maxzoom: 22,
                paint: {
                  "circle-radius": 6.0,
                  "circle-color": "#f43f5e",
                  "circle-stroke-color": "#ffffff",
                  "circle-stroke-width": 1.6
                }
              },
              {
                id: "incidents-circle-3d",
                type: "circle",
                source: "incidents-3d",
                maxzoom: 22,
                paint: {
                  "circle-radius": 7.0,
                  "circle-color": "#ea580c",
                  "circle-stroke-color": "#fed7aa",
                  "circle-stroke-width": 1.8
                }
              }
            ]
          }
        });
      } catch (err) {
        console.warn("MapLibre WebGL initialization failed; activating 2D GIS canvas:", err);
        map3d = null;
        map3dContextLost = true;
        setCameraDimension("2D");
        return;
      }

      const canvas3d = map3d.getCanvas();
      canvas3d.addEventListener("webglcontextlost", (ev) => {
        ev.preventDefault();
        map3dContextLost = true;
        disposeAllThreeGpuResources();
        // Automatically switch to synchronized 2D Leaflet GIS so Safari never displays a black canvas
        setCameraDimension("2D");
      });
      canvas3d.addEventListener("webglcontextrestored", () => {
        map3dContextLost = false;
        if (map3dLoaded) {
          attachThree3DLayerIfReady();
          attachOpenMapTilesVectorLayers();
          syncPhotorealistic3DVisibility();
          sync3DMapLayers();
          scheduleOsmCityRebuild(180);
          forceMap3dRepaintBurst();
        }
      });

      const finalize3DMapReady = () => {
        if (map3dLoaded || !map3d || map3dContextLost) return;
        if (!map3d.getSource("roads-3d")) return;
        map3dLoaded = true;
        attachThree3DLayerIfReady();
        attachOpenMapTilesVectorLayers();
        syncPhotorealistic3DVisibility();
        sync3DMapLayers();
        scheduleOsmCityRebuild(150);
        updateCompassUI();
        forceMap3dRepaintBurst();
      };

      map3d.on("sourcedata", (ev) => {
        if (ev && ev.sourceId === "openmaptiles" && ev.isSourceLoaded) {
          scheduleOsmCityRebuild(140);
        }
      });
      map3d.on("rotate", updateCompassUI);
      map3d.on("move", () => {
        updateCompassUI();
        if (map3d && !map3dContextLost) {
          const zCur = map3d.getZoom();
          if (three3DLayer && three3DLayer.lastCityBuildCenter && zCur >= 8.8) {
            const mc = map3d.getCenter();
            const dDeg = Math.hypot(mc.lng - three3DLayer.lastCityBuildCenter[0], mc.lat - three3DLayer.lastCityBuildCenter[1]);
            const panThresh = 0.0052 * Math.pow(2, Math.max(0, Math.min(4.5, 15.0 - zCur)));
            if (dDeg > panThresh) {
              scheduleOsmCityRebuild(120, false);
            }
          }
          map3d.triggerRepaint();
        }
      });
      map3d.on("moveend", () => {
        scheduleOsmCityRebuild(120);
      });
      map3d.on("idle", () => {
        if (!map3dLoaded) finalize3DMapReady();
        if (!three3DLayer || three3DLayer.osmCityBuildingCount === 0) {
          scheduleOsmCityRebuild(120);
        }
      });
      map3d.on("zoom", () => {
        syncPhotorealistic3DVisibility();
        if (three3DLayer && map3d && map3d.getZoom() >= 8.8) {
          if (Math.abs(map3d.getZoom() - (three3DLayer.lastCityBuildZoom || 0)) >= 0.55) {
            scheduleOsmCityRebuild(110, false);
          }
        }
        if (typeof updateZoomLevelIndicator === "function") updateZoomLevelIndicator();
      });
      map3d.on("zoomend", () => {
        sync3DMapLayers();
        scheduleOsmCityRebuild(120);
        if (typeof updateZoomLevelIndicator === "function") updateZoomLevelIndicator();
      });

      map3d.on("load", finalize3DMapReady);
      setTimeout(finalize3DMapReady, 1800);

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

      map3d.on("click", "intersections-circle-3d", (e) => {
        if (e.features && e.features.length > 0) {
          const iid = e.features[0].properties.intersection_id;
          const inter = DATA.intersections.find(x => x.intersection_id === iid);
          if (inter) showIntersectionInspector(inter, true);
        }
      });
    }

    // Keeps Satellite (3D Earth), Street, and Dark cartographic basemaps visible across all UAE locations and transitions OSM 3D Buildings
    function syncPhotorealistic3DVisibility() {
      if (!map3d || map3dContextLost) return;
      if (!map3d.getLayer("sat-raster-layer")) return;
      const mode = currentBasemapMode || "sat";
      const zNow = map3d.getZoom();

      map3d.setLayoutProperty(
        "sat-raster-layer",
        "visibility",
        mode === "sat" ? "visible" : "none"
      );
      if (map3d.getLayer("light-raster-layer")) {
        map3d.setLayoutProperty(
          "light-raster-layer",
          "visibility",
          mode === "light" ? "visible" : "none"
        );
      }
      if (map3d.getLayer("dark-raster-layer")) {
        map3d.setLayoutProperty(
          "dark-raster-layer",
          "visibility",
          mode === "dark" ? "visible" : "none"
        );
      }
      if (map3d.getLayer("dark-ref-raster-layer")) {
        map3d.setLayoutProperty(
          "dark-ref-raster-layer",
          "visibility",
          mode === "dark" ? "visible" : "none"
        );
      }
      if (map3d.getLayer("bg-dark-layer")) {
        map3d.setPaintProperty(
          "bg-dark-layer",
          "background-color",
          mode === "dark" ? "#1a1d23" : (mode === "light" ? "#e8e4d8" : "#162231")
        );
      }
      if (typeof map3d.setSky === "function") {
        try {
          map3d.setSky({
            "sky-color": mode === "dark" ? "#0b1324" : "#6ea3d4",
            "horizon-color": mode === "dark" ? "#1e293b" : "#dbe9f6",
            "sky-horizon-blend": 0.55
          });
        } catch (_) {}
      }
      if (map3d.getLayer("osm-3d-buildings")) {
        const hasThreeCity = Boolean(three3DLayer && three3DLayer.osmCityBuildingCount > 0 && zNow >= 8.8);
        const showFallbackExtrusion = Boolean(three3DLayer && three3DLayer.osmCityTruncated && zNow >= 14.0 && zNow < 14.4);
        const fillExtOpacity = !is3DBlocksEnabled
          ? 0.0
          : (hasThreeCity ? (showFallbackExtrusion ? 0.55 : 0.002) : (zNow >= 14.0 ? 0.82 : 0.0));
        map3d.setPaintProperty(
          "osm-3d-buildings",
          "fill-extrusion-opacity",
          fillExtOpacity
        );
      }
    }

    function sync3DMapLayers() {
      if (!map3d || !map3dLoaded) return;

      attachThree3DLayerIfReady();
      rebuildThreeHeroScene();
      syncPhotorealistic3DVisibility();

      const emFilter = document.getElementById("emirateSelect") ? document.getElementById("emirateSelect").value : "ALL";
      const q = (document.getElementById("searchInput")?.value || "").toLowerCase().trim();
      const showProjs = document.getElementById("chk-L1")?.checked ?? true;
      const showSubdevs = document.getElementById("chk-L2")?.checked ?? false;
      const showComm = document.getElementById("chk-L3")?.checked ?? true;
      const showRoads = document.getElementById("chk-L4")?.checked ?? true;
      const showInts = document.getElementById("chk-L5")?.checked ?? false;
      const showTraffic = document.getElementById("chk-L6")?.checked ?? true;
      const showIncidents = document.getElementById("chk-L7")?.checked ?? false;
      const showTransit = document.getElementById("chk-L8")?.checked ?? false;
      const showFacilities = document.getElementById("chk-L9")?.checked ?? false;
      const showParking = document.getElementById("chk-L10")?.checked ?? false;
      const showImpacts = document.getElementById("chk-L11")?.checked ?? false;

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

      // 2. Roads & Traffic GeoJSON (All 23 Real OpenStreetMap Highway Geometries + Whole-City Zoomed-In OSM Street Flow)
      const osmExprs = getOsmStreetTrafficExprs(currentTimeWindow);
      if (map3d.getLayer("osm-city-traffic-casing")) {
        map3d.setLayoutProperty("osm-city-traffic-casing", "visibility", showTraffic ? "visible" : "none");
        map3d.setPaintProperty("osm-city-traffic-casing", "line-color", osmExprs.casing);
      }
      if (map3d.getLayer("osm-city-traffic-flow")) {
        map3d.setLayoutProperty("osm-city-traffic-flow", "visibility", showTraffic ? "visible" : "none");
        map3d.setPaintProperty("osm-city-traffic-flow", "line-color", osmExprs.flow);
      }

      const roadFeats = [];
      if (showRoads || showTraffic) {
        DATA.roads.forEach(r => {
          if (emFilter !== "ALL" && r.emirate !== emFilter) return;
          const { obs } = getCorridorProfileForWindow(r, currentTimeWindow);
          const congLvl = obs ? obs.congestion_level : "Unavailable";
          const tCol = showTraffic ? congestionColor(congLvl) : "#64748b";
          const cCol = showTraffic ? congestionCasingColor(congLvl) : "#0f172a";
          const isFwy = r.road_type.includes("Freeway") || r.road_type.includes("Express");
          roadFeats.push({
            type: "Feature",
            properties: {
              road_id: r.road_id,
              color: tCol,
              casingColor: cCol,
              casingWidth: isFwy ? 6.2 : 4.6,
              trafficWidth: isFwy ? 4.2 : 3.0
            },
            geometry: { type: "LineString", coordinates: r.geometry_wgs84 }
          });
        });
      }
      map3d.getSource("roads-3d")?.setData({ type: "FeatureCollection", features: roadFeats });

      // 3. Impact Vectors GeoJSON (Projects + Sub-Clusters)
      const impFeats = [];
      DATA.impact_links.forEach(l => {
        if (!showImpacts && l.project_id !== selected3DProjectId) return;
        if (emFilter !== "ALL" && l.emirate !== emFilter) return;
        if (l.nearest_road_vertex_lat !== undefined && l.nearest_road_vertex_lon !== undefined) {
          const p = DATA.projects.find(x => x.project_id === l.project_id);
          const sd = !p ? DATA.subdevs.find(x => x.subdev_id === l.project_id) : null;
          if (p) {
            const [lat, lon] = parseCoord(p.coordinates);
            impFeats.push({
              type: "Feature",
              properties: { project_id: l.project_id },
              geometry: { type: "LineString", coordinates: [[lon, lat], [l.nearest_road_vertex_lon, l.nearest_road_vertex_lat]] }
            });
          } else if (sd) {
            impFeats.push({
              type: "Feature",
              properties: { project_id: l.project_id },
              geometry: { type: "LineString", coordinates: [[sd.longitude, sd.latitude], [l.nearest_road_vertex_lon, l.nearest_road_vertex_lat]] }
            });
          }
        }
      });
      map3d.getSource("impacts-3d")?.setData({ type: "FeatureCollection", features: impFeats });

      // 4. Active Construction Site Perimeter Zones & Concentration Heatmap Source
      map3d.getSource("projects-zones-3d")?.setData((showProjs || showSubdevs) ? buildProjectSiteZonesGeoJSON() : { type: "FeatureCollection", features: [] });

      // 4B. Intersections (Layer 5), Roadworks (Layer 7), Transit (Layer 8), Facilities (Layer 9), Parking Hubs (Layer 10)
      const intFeats = [];
      if (showInts) {
        DATA.intersections.forEach(i => {
          if (emFilter !== "ALL" && i.emirate !== emFilter) return;
          intFeats.push({
            type: "Feature",
            properties: { intersection_id: i.intersection_id },
            geometry: { type: "Point", coordinates: [i.longitude, i.latitude] }
          });
        });
      }
      map3d.getSource("intersections-3d")?.setData({ type: "FeatureCollection", features: intFeats });

      const incFeats = [];
      if (showIncidents) {
        DATA.incidents.forEach(inc => {
          if (emFilter !== "ALL" && inc.emirate !== emFilter) return;
          incFeats.push({
            type: "Feature",
            properties: { incident_id: inc.incident_id, road_id: inc.road_id },
            geometry: { type: "Point", coordinates: [inc.longitude, inc.latitude] }
          });
        });
      }
      map3d.getSource("incidents-3d")?.setData({ type: "FeatureCollection", features: incFeats });

      const trLineFeats = [];
      const trStatFeats = [];
      if (showTransit) {
        DATA.transit_lines.forEach(t => {
          trLineFeats.push({
            type: "Feature",
            properties: { transit_id: t.transit_id, color: t.color },
            geometry: { type: "LineString", coordinates: t.coords }
          });
          t.stations.forEach(st => {
            trStatFeats.push({
              type: "Feature",
              properties: { name: st.name, color: t.color },
              geometry: { type: "Point", coordinates: [st.lon, st.lat] }
            });
          });
        });
      }
      map3d.getSource("transit-lines-3d")?.setData({ type: "FeatureCollection", features: trLineFeats });
      map3d.getSource("transit-stations-3d")?.setData({ type: "FeatureCollection", features: trStatFeats });

      const facFeats = [];
      if (showFacilities) {
        DATA.facilities.forEach(f => {
          if (emFilter !== "ALL" && f.emirate !== emFilter) return;
          const [lat, lon] = parseCoord(f.coordinates);
          facFeats.push({
            type: "Feature",
            properties: { feature_name: f.feature_name },
            geometry: { type: "Point", coordinates: [lon, lat] }
          });
        });
      }
      map3d.getSource("facilities-3d")?.setData({ type: "FeatureCollection", features: facFeats });

      const prkFeats = [];
      if (showParking) {
        DATA.parking.forEach(pk => {
          if (emFilter !== "ALL" && pk.emirate !== emFilter) return;
          prkFeats.push({
            type: "Feature",
            properties: { parking_id: pk.parking_id },
            geometry: { type: "Point", coordinates: [pk.longitude, pk.latitude] }
          });
        });
      }
      map3d.getSource("parking-3d")?.setData({ type: "FeatureCollection", features: prkFeats });

      const heatFeats = [];
      DATA.projects.forEach(p => {
        if (emFilter !== "ALL" && p.emirate !== emFilter) return;
        const [lat, lon] = parseCoord(p.coordinates);
        const st = projectScaleStyle(p);
        const w = st.radius >= 11 ? 1.0 : (st.radius >= 8.5 ? 0.75 : 0.5);
        heatFeats.push({
          type: "Feature",
          properties: { project_id: p.project_id, heatWeight: w },
          geometry: { type: "Point", coordinates: [lon, lat] }
        });
      });
      DATA.subdevs.forEach(sd => {
        if (emFilter !== "ALL" && sd.emirate !== emFilter) return;
        heatFeats.push({
          type: "Feature",
          properties: { project_id: sd.subdev_id, heatWeight: 0.65 },
          geometry: { type: "Point", coordinates: [sd.longitude, sd.latitude] }
        });
      });
      map3d.getSource("projects-heat-source-3d")?.setData({ type: "FeatureCollection", features: heatFeats });

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

      if (showSubdevs && zNow < 15.2) {
        DATA.subdevs.forEach(sd => {
          if (emFilter !== "ALL" && sd.emirate !== emFilter) return;
          if (q && !JSON.stringify(sd).toLowerCase().includes(q)) return;
          const el = document.createElement("div");
          el.className = "haio-3d-block-callout";
          el.style.padding = "3px 8px";
          el.style.fontSize = "0.67rem";
          el.style.borderLeft = "3px solid #a855f7";
          el.innerHTML = `<span style="width:6px;height:6px;border-radius:50%;background:#a855f7;display:inline-block;"></span><span><strong>${sd.subdev_id}</strong></span>`;
          el.onclick = (ev) => {
            ev.stopPropagation();
            showSubdevInspector(sd, true);
          };
          const mk = new maplibregl.Marker({ element: el, anchor: "bottom", offset: [0, -5] })
            .setLngLat([sd.longitude, sd.latitude])
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
        minZoom: 8,
        maxZoom: 19,
        maxBounds: [[22.4, 51.0], [26.5, 56.8]],
        maxBoundsViscosity: 0.9,
        fadeAnimation: false,
        zoomAnimation: !IS_SAFARI_WEBKIT,
        preferCanvas: true,
        zoomControl: false
      });

      syncMapCanvasBackdropClass();

      // Enable only the 4 core executive layers by default (Clean Initial View)
      ["communities", "roads", "traffic", "projects"].forEach(k => {
        layerGroups[k].addTo(map);
      });

      map.on("zoomend", () => {
        if (currentCameraDim === "2D") {
          renderAllMapLayers();
        }
      });
      map.on("moveend", () => {
        if (currentCameraDim === "2D") {
          render2DZoomedStreetTraffic();
        }
      });

      init3DMap();
      setBasemap("sat", document.querySelector(".bm-btn.active"));
      if (!isMap3dGlAlive()) {
        setCameraDimension("2D");
      }

      populateCommunityDropdown();
      renderAllMapLayers();
      runUseCase(1, false);
      showProjectInspector("PRJ-D11", false);
    }

    let currentPlatformMode = "explorer";
    let currentConcentrationMode = "points";
    let analyticalSplitView = false;
    let activeWorkspaceCommunityId = "COM-DXB-01";

    // =========================================================================
    // PHASE 4: ADAPTIVE GEOGRAPHIC ZOOM LEVELS (L1 UAE -> L2 EMIRATE -> L3 COMMUNITY -> L4 PROJECT 3D)
    // =========================================================================
    function setGeoZoomLevel(lvl) {
      const numLvl = String(lvl).replace("L", "");
      document.querySelectorAll("#geoZoomLevelBar .zlvl-btn[id^='zlvl-']").forEach(b => b.classList.remove("active"));
      const btn = document.getElementById(`zlvl-${numLvl}`);
      if (btn) btn.classList.add("active");

      if (numLvl === "1") {
        document.getElementById("emirateSelect").value = "ALL";
        populateCommunityDropdown();
        setLayerSet(["communities", "roads", "traffic", "projects"]);
        flyBothMaps(25.120, 55.340, 9.6, 38, 15);
        document.getElementById("hudScope").textContent = "L1: UAE National Overview";
        renderAllMapLayers();
      } else if (numLvl === "2") {
        const em = document.getElementById("emirateSelect").value === "Sharjah" ? "Sharjah" : "Dubai";
        document.getElementById("emirateSelect").value = em;
        populateCommunityDropdown();
        setLayerSet(["communities", "roads", "traffic", "projects"]);
        if (em === "Sharjah") {
          flyBothMaps(25.318, 55.475, 11.8, 50, 30);
          document.getElementById("hudScope").textContent = "L2: Sharjah Regional";
        } else {
          flyBothMaps(25.165, 55.265, 11.6, 50, 32);
          document.getElementById("hudScope").textContent = "L2: Dubai Regional";
        }
        renderAllMapLayers();
      } else if (numLvl === "3") {
        const cid = document.getElementById("communitySelect").value !== "ALL" ? document.getElementById("communitySelect").value : "COM-DXB-01";
        const c = DATA.communities.find(x => x.community_id === cid) || DATA.communities[0];
        if (c) {
          setLayerSet(["communities", "devbounds", "roads", "traffic", "intersections", "projects"]);
          flyBothMaps(c.center_lat, c.center_lon, 14.1, 56, 38);
          document.getElementById("hudScope").textContent = `L3: ${c.community_name}`;
          showCommunityInspector(c);
        }
      } else if (numLvl === "4") {
        const pid = selected3DProjectId || "PRJ-D11";
        setLayerSet(["communities", "devbounds", "roads", "traffic", "impacts", "projects"]);
        showProjectInspector(pid, true);
        document.getElementById("hudScope").textContent = `L4: ${pid} 3D & Corridor`;
      }
    }

    function updateZoomLevelIndicator() {
      if (!map3d) return;
      const z = map3d.getZoom();
      let activeId = "zlvl-4";
      if (z < 10.6) activeId = "zlvl-1";
      else if (z < 13.0) activeId = "zlvl-2";
      else if (z < 15.2) activeId = "zlvl-3";
      document.querySelectorAll("#geoZoomLevelBar .zlvl-btn[id^='zlvl-']").forEach(b => {
        b.classList.toggle("active", b.id === activeId);
      });
    }

    // =========================================================================
    // PHASE 3.2: CONSTRUCTION CONCENTRATION MAP SWITCHER (POINTS / HEATMAP / COMMUNITIES / CLUSTERS)
    // =========================================================================
    function setConcentrationMode(mode, btnEl) {
      const normMode = (mode === "communities") ? "boundaries" : mode;
      currentConcentrationMode = normMode;
      ["cmode-points", "cmode-heatmap", "cmode-boundaries", "cmode-clusters"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.toggle("active", id === `cmode-${normMode}`);
      });
      if (btnEl) btnEl.classList.add("active");

      if (map3d && map3dLoaded) {
        if (map3d.getLayer("projects-heatmap-3d")) {
          map3d.setLayoutProperty("projects-heatmap-3d", "visibility", normMode === "heatmap" ? "visible" : "none");
        }
        if (map3d.getLayer("communities-fill-3d")) {
          map3d.setPaintProperty("communities-fill-3d", "fill-opacity", normMode === "boundaries" ? 0.28 : 0.08);
        }
        if (map3d.getLayer("communities-line-3d")) {
          map3d.setPaintProperty("communities-line-3d", "line-width", normMode === "boundaries" ? 2.8 : 1.4);
        }
      }

      if (normMode === "points") {
        setLayerSet(["communities", "roads", "traffic", "projects"]);
      } else if (normMode === "heatmap") {
        setLayerSet(["communities", "roads", "projects"]);
        if (map3d && map3d.getZoom() > 13.5) {
          flyBothMaps(25.165, 55.285, 11.4, 46, 25);
        }
      } else if (normMode === "boundaries") {
        setLayerSet(["communities", "roads", "traffic", "projects"]);
        if (map3d && map3d.getZoom() > 13.5) {
          flyBothMaps(25.165, 55.285, 11.6, 48, 28);
        }
      } else if (normMode === "clusters") {
        setLayerSet(["communities", "devbounds", "projects", "roads", "impacts"]);
        flyBothMaps(25.0585, 55.2090, 14.1, 56, 38);
      }
      renderAllMapLayers();
    }

    // =========================================================================
    // PHASE 4.2: 6 ONE-CLICK LAYER PRESETS
    // =========================================================================
    function applyLayerPreset(presetName, btnEl) {
      document.querySelectorAll("#layerPresetGrid .preset-btn").forEach(b => b.classList.remove("active"));
      if (btnEl) btnEl.classList.add("active");

      const p = String(presetName || "").toLowerCase();
      if (p === "construction" || p === "construction_overview") {
        setLayerSet(["projects", "devbounds", "communities", "roads"]);
      } else if (p === "traffic" || p === "traffic_overview") {
        setLayerSet(["roads", "traffic", "intersections", "communities"]);
      } else if (p === "logistics") {
        setLayerSet(["roads", "traffic", "facilities", "parking", "impacts", "projects"]);
      } else if (p === "disruptions") {
        setLayerSet(["roads", "traffic", "incidents", "intersections"]);
      } else if (p === "impact" || p === "project_impact") {
        setLayerSet(["projects", "devbounds", "roads", "traffic", "impacts", "intersections"]);
      } else if (p === "all" || p === "all_layers") {
        setLayerSet(["projects", "devbounds", "communities", "roads", "intersections", "traffic", "incidents", "transit", "facilities", "parking", "impacts"]);
      }
    }

    // =========================================================================
    // PHASE 2: 7-MODULE INFORMATION ARCHITECTURE & DEDICATED ANALYTICAL WORKSPACE
    // =========================================================================
    function closeAnalyticalWorkspace() {
      const aw = document.getElementById("analyticalWorkspaceModal");
      if (aw) aw.classList.remove("open", "split-mode");
      document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
      const expBtn = document.getElementById("mode-explorer");
      if (expBtn) expBtn.classList.add("active");
      currentPlatformMode = "explorer";
      setTimeout(() => {
        if (map) map.invalidateSize();
        if (map3d) map3d.resize();
      }, 150);
    }

    function toggleAnalyticalSplitMode() {
      analyticalSplitView = !analyticalSplitView;
      const aw = document.getElementById("analyticalWorkspaceModal");
      if (aw) aw.classList.toggle("split-mode", analyticalSplitView);
      setTimeout(() => {
        if (map) map.invalidateSize();
        if (map3d) map3d.resize();
      }, 220);
    }

    function setPlatformMode(mode, btnEl) {
      currentPlatformMode = mode;
      document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
      if (btnEl) {
        btnEl.classList.add("active");
      } else {
        const targetBtn = document.getElementById(`mode-${mode}`);
        if (targetBtn) targetBtn.classList.add("active");
      }

      const aw = document.getElementById("analyticalWorkspaceModal");
      const wb = document.getElementById("mainWorkbench");

      if (mode === "explorer") {
        if (aw) aw.classList.remove("open", "split-mode");
        if (wb && wb.classList.contains("panel-collapsed")) toggleRightPanel();
        switchDrawerTab("uc");
        setLayerSet(["communities", "roads", "traffic", "projects"]);
        setTimeout(() => { if (map3d) map3d.resize(); }, 120);
        return;
      }

      if (mode === "project") {
        if (aw) aw.classList.remove("open", "split-mode");
        if (wb && wb.classList.contains("panel-collapsed")) toggleRightPanel();
        switchDrawerTab("insp");
        setLayerSet(["communities", "roads", "traffic", "impacts", "projects", "devbounds"]);
        showProjectInspector(selected3DProjectId || "PRJ-D11", true);
        return;
      }

      // Modes 01 (overview), 02 (construction), 04 (traffic), 05 (impact), 07 (evidence) open the dedicated Analytical Workspace
      if (!aw) return;
      aw.classList.add("open");
      aw.classList.toggle("split-mode", analyticalSplitView);

      if (mode === "overview") {
        renderExecutiveOverviewModule(aw);
      } else if (mode === "construction") {
        renderConstructionIntelligenceModule(aw);
      } else if (mode === "traffic") {
        renderTrafficIntelligenceModule(aw);
      } else if (mode === "impact") {
        renderImpactAndLogisticsModule(aw);
      } else if (mode === "evidence") {
        renderDataAndEvidenceModule(aw);
      }
      aw.scrollTop = 0;
    }

    function inspectEntityOnMapFromWorkspace(type, id) {
      closeAnalyticalWorkspace();
      if (type === "project") {
        showProjectInspector(id, true);
      } else if (type === "road") {
        showRoadInspector(id, true);
      } else if (type === "community") {
        const c = DATA.communities.find(x => x.community_id === id);
        if (c) {
          flyBothMaps(c.center_lat, c.center_lon, (c.recommended_zoom || 13) + 0.8, 56, 38);
          showCommunityInspector(c);
        }
      } else if (type === "intersection") {
        const i = DATA.intersections.find(x => x.intersection_id === id);
        if (i) showIntersectionInspector(i, true);
      } else if (type === "subdev") {
        const sd = DATA.subdevs.find(x => x.subdev_id === id);
        if (sd) showSubdevInspector(sd, true);
      }
    }

    function exportFilteredProjectsCsv() {
      const emFilter = document.getElementById("emirateSelect") ? document.getElementById("emirateSelect").value : "ALL";
      const rows = (DATA.uae_projects_summary && DATA.uae_projects_summary.length) ? DATA.uae_projects_summary : DATA.projects;
      const filtered = rows.filter(r => emFilter === "ALL" || r.emirate === emFilter);
      const headers = ["project_id", "project_name", "emirate", "city_district_community", "developer", "project_type", "lifecycle_status", "published_investment_value", "gross_project_value_aed_b", "hard_construction_cost_aed_b", "is_estimated_gdv", "gross_floor_area", "expected_completion_date", "coordinates", "confidence", "source_url"];
      const csvLines = [headers.join(",")];
      filtered.forEach(r => {
        const vals = headers.map(h => {
          const v = r[h] !== undefined && r[h] !== null ? String(r[h]).replace(/"/g, '""') : "";
          return `"${v}"`;
        });
        csvLines.push(vals.join(","));
      });
      const blob = new Blob([csvLines.join("\n")], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `uae_construction_projects_${emFilter.toLowerCase()}_export.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    function exportTask2JsonBundle() {
      const emFilter = document.getElementById("emirateSelect") ? document.getElementById("emirateSelect").value : "ALL";
      const allNational = DATA.uae_projects_summary || [];
      const bundle = {
        metadata: {
          platform: "UAE Construction Activity, Geographic Intelligence & Traffic Impact Analysis Platform (Task 2)",
          active_emirate_filter: emFilter,
          active_time_window: currentTimeWindow,
          generated_at_iso: new Date().toISOString(),
          counts: {
            national_flagships_7_emirates: allNational.length,
            deep_gis_flagships_dubai_sharjah: DATA.projects.length,
            national_only_other_5_emirates: Math.max(0, allNational.length - DATA.projects.length),
            jvc_subdevelopments: DATA.subdevs.length,
            total_task2_spatial_entities: DATA.projects.length + DATA.subdevs.length,
            communities: DATA.communities.length,
            road_corridors: DATA.roads.length,
            intersections: DATA.intersections.length,
            traffic_observations: DATA.observations.length,
            nearby_facilities_09b: DATA.facilities.length,
            parking_mobility_hubs_20: DATA.parking.length,
            project_road_impact_links: DATA.impact_links.length
          }
        },
        uae_national_projects_filtered: allNational.filter(r => emFilter === "ALL" || r.emirate === emFilter),
        task2_deep_gis_projects: DATA.projects.filter(p => emFilter === "ALL" || p.emirate === emFilter),
        jvc_subdevelopments: DATA.subdevs.filter(s => emFilter === "ALL" || s.emirate === emFilter),
        communities: DATA.communities.filter(c => emFilter === "ALL" || c.emirate === emFilter),
        road_corridors: DATA.roads.filter(r => emFilter === "ALL" || r.emirate === emFilter),
        intersections: DATA.intersections.filter(i => emFilter === "ALL" || i.emirate === emFilter),
        traffic_observations: DATA.observations,
        nearby_facilities_09b: DATA.facilities.filter(f => emFilter === "ALL" || f.emirate === emFilter),
        parking_and_staging_hubs_20: DATA.parking.filter(pk => emFilter === "ALL" || pk.emirate === emFilter),
        project_road_impact_links: DATA.impact_links.filter(l => emFilter === "ALL" || l.emirate === emFilter)
      };
      const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `uae_task2_intelligence_${emFilter.toLowerCase()}_bundle.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    function printExecutiveReport() {
      const aw = document.getElementById("analyticalWorkspaceModal");
      if (aw && !aw.classList.contains("open")) {
        setPlatformMode("overview");
      }
      setTimeout(() => { window.print(); }, 80);
    }

    function buildWorkspaceStickyHeader(badgeText, titleText, subtitleText) {
      return `
        <div class="aw-sticky-bar">
          <div>
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
              <span class="brand-badge" style="background:#dbeafe; color:#1d4ed8;">${badgeText}</span>
              <span style="font-size:0.72rem; color:#64748b; font-weight:700;">Active Window: <strong style="color:#0f172a;">${currentTimeWindow}</strong></span>
            </div>
            <h2 style="margin:4px 0 0; font-size:1.18rem; font-weight:800; color:#0f172a;">${titleText}</h2>
            <div style="font-size:0.76rem; color:#475569; margin-top:2px;">${subtitleText}</div>
          </div>
          <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
            <button class="ctrl-btn" onclick="toggleAnalyticalSplitMode()" title="View Analytical Dashboard Side-by-Side with 3D GIS Map">${analyticalSplitView ? '🗖 Full Width View' : '◫ Split Screen with 3D Map'}</button>
            <button class="ctrl-btn" onclick="printExecutiveReport()" title="Print / Save PDF Executive Report">🖨️ Print PDF</button>
            <button class="ctrl-btn" style="background:#0f172a; color:#fff; border-color:#0f172a;" onclick="closeAnalyticalWorkspace()">🗺️ Return to 3D GIS Map ✕</button>
          </div>
        </div>
      `;
    }

    // =========================================================================
    // MODULE 01: EXECUTIVE OVERVIEW (UAE-WIDE & DUBAI/SHARJAH INTELLIGENCE SUMMARY)
    // =========================================================================
    function renderExecutiveOverviewModule(container) {
      const allUae = DATA.uae_projects_summary || [];
      const emCounts = {};
      allUae.forEach(p => {
        emCounts[p.emirate] = (emCounts[p.emirate] || 0) + 1;
      });
      const emRowsHtml = Object.entries(emCounts).map(([em, cnt]) => {
        const isDeepGis = (em === "Dubai" || em === "Sharjah");
        const pct = Math.round((cnt / Math.max(1, allUae.length)) * 100);
        return `
          <div class="aw-bar-row">
            <div><strong>${em}</strong> ${isDeepGis ? '<span class="ep-pill-pub">Task 2 Deep GIS</span>' : '<span class="ep-pill-mod">Task 1 Baseline</span>'}</div>
            <div class="aw-bar-track"><div class="aw-bar-fill" style="width:${Math.max(8, pct * 2.5)}%; background:${isDeepGis ? '#2563eb' : '#64748b'};"></div></div>
            <div style="text-align:right; font-weight:800;">${cnt} Flagships</div>
          </div>
        `;
      }).join("");

      container.innerHTML = `
        ${buildWorkspaceStickyHeader("MODULE 01 — EXECUTIVE OVERVIEW", "UAE Construction Activity, Geographic Intelligence & Traffic Impact Summary", "Unified executive command center across all 7 UAE Emirates (85 Flagship Developments) with deep spatial & corridor traffic modelling for Dubai (20 Flagships + 5 JVC Clusters) and Sharjah (12 Flagships).")}

        <div class="aw-kpi-grid">
          <div class="aw-kpi-card">
            <div class="k-lbl">UAE National vs. Task 2 GIS Scope</div>
            <div class="k-val">85 National → 37 Deep GIS</div>
            <div class="k-sub"><strong>85</strong> UAE Flagships across 7 Emirates (<code>04_project_inventory.csv</code>) · <strong>37</strong> Deep-Dive Task 2 Entities (<strong>20</strong> Dubai + <strong>12</strong> Sharjah Flagships = <strong>32</strong> + <strong>5</strong> JVC Sub-Clusters; <strong>53</strong> other-emirate flagships have national inventory coverage only)</div>
          </div>
          <div class="aw-kpi-card">
            <div class="k-lbl">Published Official Value (27/32)</div>
            <div class="k-val" style="color:#059669;">AED 765.9B / 776.4B</div>
            <div class="k-sub"><span class="ep-pill-pub">PUBLISHED</span> <strong>3</strong> Civil Infrastructure Capex Awards (<strong>AED 176.0B</strong> initial / <strong>178.5B</strong> in <code>06c</code>) + <strong>24</strong> Published Real Estate GDV (<strong>AED 589.9B</strong> initial / <strong>597.9B</strong> in <code>06c</code>) — Never mixed with Estimated GDV</div>
          </div>
          <div class="aw-kpi-card">
            <div class="k-lbl">Estimated Masterplan GDV (5/32)</div>
            <div class="k-val" style="color:#b45309;">AED 253.0B</div>
            <div class="k-sub"><span class="badge-missing">ESTIMATED GDV</span> 5 Masterplans with partial contract awards (<code>PRJ-D2</code>, <code>PRJ-D4</code>, <code>PRJ-D11</code>, <code>PRJ-D16</code>, <code>PRJ-SH5</code>) · Modelled Hard Construction Cost (32/32): <strong>AED 595.8B</strong></div>
          </div>
          <div class="aw-kpi-card">
            <div class="k-lbl">Transport &amp; Logistics Network</div>
            <div class="k-val" style="color:#2563eb;">23 Corridors · 37 Hubs</div>
            <div class="k-sub"><strong>16</strong> Dubai + <strong>7</strong> Sharjah OSM Corridors · <strong>16</strong> Intersections · <strong>30</strong> Urban/Industrial Facilities in <code>09b</code> (incl. <strong>5</strong> Major Industrial/Logistics Zones) + <strong>7</strong> Mobility/Staging Hubs in <code>20</code></div>
          </div>
          <div class="aw-kpi-card">
            <div class="k-lbl">City Baseline vs. Corridor BPR Speed</div>
            <div class="k-val" style="color:#dc2626;">31.3 km/h</div>
            <div class="k-sub"><span class="ep-pill-pub">TomTom SRC-436</span> <strong>42.7%</strong> 24/7 annual metro congestion in <code>OBS-DXB-CITY-00</code> (42.3% AM / 94.4% PM; vs. 47.5% daytime urban-core narrative note) · Hessa St AM: <strong>29.0 km/h (V/C=1.04)</strong></div>
          </div>
        </div>

        <div class="aw-grid-2">
          <div class="aw-panel-card">
            <h3>1. UAE 7-Emirate Geographic Coverage (85 Flagship Projects)</h3>
            <p style="font-size:0.76rem; color:#475569; margin-bottom:10px;">
              Task 1 catalogued <strong>85 flagship projects across all 7 UAE Emirates</strong>. Task 2 performs deep-dive spatial GIS, road network, HGV logistics, and 4-window BPR traffic impact modelling across <strong>Dubai (20 flagships + 5 JVC sub-clusters)</strong> and <strong>Sharjah (12 flagships)</strong>:
            </p>
            ${emRowsHtml}
            <div style="margin-top:12px; display:flex; gap:8px; flex-wrap:wrap;">
              <button class="ctrl-btn" onclick="closeAnalyticalWorkspace(); setGeoZoomLevel('L1');">🗺️ View L1 UAE National Map</button>
              <button class="ctrl-btn" onclick="closeAnalyticalWorkspace(); document.getElementById('emirateSelect').value='Dubai'; setGeoZoomLevel('L2');">🏙️ View L2 Dubai Regional Map</button>
              <button class="ctrl-btn" onclick="closeAnalyticalWorkspace(); document.getElementById('emirateSelect').value='Sharjah'; setGeoZoomLevel('L2');">🏛️ View L2 Sharjah Regional Map</button>
            </div>
          </div>

          <div class="aw-panel-card">
            <h3>2. Platform Navigation &amp; Analytical Modules (01–07)</h3>
            <div class="kv-grid">
              <div class="kv-row" style="cursor:pointer;" onclick="setPlatformMode('construction')">
                <div class="kv-lbl">02 — Construction Intelligence</div>
                <div class="kv-val">Published vs. Estimated Investment separation, Developer &amp; Lifecycle distribution, Missing-Data Register, Density Heatmap switcher, and <strong>10-Community Intelligence Explorer</strong>.</div>
              </div>
              <div class="kv-row" style="cursor:pointer;" onclick="setPlatformMode('explorer')">
                <div class="kv-lbl">03 — Geographic Explorer (2D/3D GIS)</div>
                <div class="kv-val">4 Adaptive Zoom Levels (<code>L1 UAE</code> → <code>L2 Emirate</code> → <code>L3 Community</code> → <code>L4 Project 3D</code>), 7 Organized Layer Groups, and 6 One-Click Layer Presets.</div>
              </div>
              <div class="kv-row" style="cursor:pointer;" onclick="setPlatformMode('traffic')">
                <div class="kv-lbl">04 — Traffic Intelligence</div>
                <div class="kv-val">23-Corridor Speed/Capacity/V/C Table, 4-Window Visual Time Comparison Charts, 16-Intersection Bottleneck Explorer, and <strong>Multi-Factor Traffic Cause Matrix</strong>.</div>
              </div>
              <div class="kv-row" style="cursor:pointer;" onclick="setPlatformMode('impact')">
                <div class="kv-lbl">05 — Construction Impact &amp; Logistics</div>
                <div class="kv-val"><strong>30</strong> Dubai/Sharjah Urban &amp; Industrial Facilities in <code>09b</code> (incl. <strong>5</strong> Industrial/Logistics Zones) + <strong>7</strong> Mobility/Staging Hubs in <code>20</code>, 4-Component HGV Model, 37-Link Epistemic Matrix, and <strong>Interactive Scenario Simulator</strong>.</div>
              </div>
              <div class="kv-row" style="cursor:pointer;" onclick="setPlatformMode('project')">
                <div class="kv-lbl">06 — Project Explorer (5-Section Profile + 3D)</div>
                <div class="kv-val">Structured 5-Section Project Profile with explicit <code>Unavailable / Restricted</code> indicators + interactive 3D Block/Floor/Stack massing.</div>
              </div>
              <div class="kv-row" style="cursor:pointer;" onclick="setPlatformMode('evidence')">
                <div class="kv-lbl">07 — Data, Methodology &amp; Evidence</div>
                <div class="kv-val">Searchable 11-Dataset Catalogue, Source Register, Step-by-Step Worked BPR &amp; HGV Equations, Data-Quality Dashboard (TomTom 42.7% vs 47.5%), and 12 Exports.</div>
              </div>
            </div>
          </div>
        </div>

        <div class="aw-panel-card">
          <h3>3. Top 10 Dubai &amp; Sharjah Construction Hotspots Ranked by Composite Activity Index</h3>
          <div style="overflow-x:auto;">
            <table class="ev-table">
              <thead>
                <tr>
                  <th>Community ID</th>
                  <th>Emirate</th>
                  <th>Community / Corridor Name</th>
                  <th>Activity Index Score</th>
                  <th>Active Devs</th>
                  <th>Active Towers</th>
                  <th>Scheduled Units (2025–29)</th>
                  <th>Active Structural GFA (m²)</th>
                  <th>Primary Road Corridors</th>
                  <th>Observed / Modelled Congestion</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${DATA.communities.map(c => `
                  <tr>
                    <td><code>${c.community_id}</code></td>
                    <td><strong>${c.emirate}</strong></td>
                    <td><strong>${c.community_name}</strong></td>
                    <td><strong style="color:#2563eb;">${c.construction_activity_index_score}</strong></td>
                    <td>${c.active_developments_count}</td>
                    <td>${c.active_towers_and_buildings}</td>
                    <td>${c.scheduled_units_2025_2029.toLocaleString()}</td>
                    <td><strong>${c.active_structural_gfa_sqm.toLocaleString()} m²</strong></td>
                    <td>${c.primary_road_corridors}</td>
                    <td><span style="color:${congestionColor(c.observed_congestion_severity)}; font-weight:700;">${c.observed_congestion_severity}</span></td>
                    <td><button class="ctrl-btn" onclick="inspectEntityOnMapFromWorkspace('community', '${c.community_id}')">🗺️ Zoom 3D</button></td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    // =========================================================================
    // MODULE 02: CONSTRUCTION INTELLIGENCE (DASHBOARD, INVESTMENT SEPARATION, MISSING DATA, COMMUNITY EXPLORER)
    // =========================================================================
    function selectCommunityInWorkspace(cid) {
      activeWorkspaceCommunityId = cid;
      const aw = document.getElementById("analyticalWorkspaceModal");
      if (aw) renderConstructionIntelligenceModule(aw);
    }

    function filterConstructionEmirate(em) {
      const emSel = document.getElementById("emirateSelect");
      if (emSel) emSel.value = em;
      const matchingComms = DATA.communities.filter(c => em === "ALL" || c.emirate === em);
      if (matchingComms.length && !matchingComms.some(c => c.community_id === activeWorkspaceCommunityId)) {
        activeWorkspaceCommunityId = matchingComms[0].community_id;
      }
      onEmirateChange();
      const aw = document.getElementById("analyticalWorkspaceModal");
      if (aw && aw.classList.contains("open") && currentPlatformMode === "construction") {
        renderConstructionIntelligenceModule(aw);
      }
    }

    function renderConstructionIntelligenceModule(container) {
      const activeEmFilter = document.getElementById("emirateSelect") ? document.getElementById("emirateSelect").value : "ALL";
      const summaryRows = (DATA.uae_projects_summary || []).filter(r => r.emirate === "Dubai" || r.emirate === "Sharjah");
      const pubProjs = summaryRows.filter(r => !r.is_estimated_gdv);
      const estProjs = summaryRows.filter(r => r.is_estimated_gdv);

      const filteredProjs = DATA.projects.filter(p => activeEmFilter === "ALL" || p.emirate === activeEmFilter);
      const filteredSubdevs = DATA.subdevs.filter(s => activeEmFilter === "ALL" || s.emirate === activeEmFilter);
      const filteredComms = DATA.communities.filter(c => activeEmFilter === "ALL" || c.emirate === activeEmFilter);

      // Developer aggregation (respects Emirate filter)
      const devMap = {};
      filteredProjs.forEach(p => {
        const dName = p.developer.split("(")[0].trim();
        devMap[dName] = (devMap[dName] || 0) + 1;
      });
      const devSorted = Object.entries(devMap).sort((a, b) => b[1] - a[1]).slice(0, 10);

      // Selected community deep intelligence
      const selComm = filteredComms.find(c => c.community_id === activeWorkspaceCommunityId)
        || DATA.communities.find(c => c.community_id === activeWorkspaceCommunityId)
        || filteredComms[0]
        || DATA.communities[0];
      const commFlagshipIds = (selComm.flagship_project_ids || "").split(",").map(s => s.trim()).filter(Boolean);
      const commProjs = DATA.projects.filter(p => commFlagshipIds.some(fid => p.project_id === fid.split("(")[0].trim()) || p.city_district_community.toLowerCase().includes(selComm.community_name.split("(")[0].trim().toLowerCase().slice(0, 8)));
      const commSubdevs = selComm.community_id === "COM-DXB-01" ? DATA.subdevs : [];
      const commLinks = DATA.impact_links.filter(l => commProjs.some(p => p.project_id === l.project_id) || commSubdevs.some(s => s.subdev_id === l.project_id));
      const commRoadIds = new Set();
      commLinks.forEach(l => { commRoadIds.add(l.primary_road_id); commRoadIds.add(l.secondary_road_id); });
      const commRoads = DATA.roads.filter(r => commRoadIds.has(r.road_id) || (selComm.primary_road_corridors || "").includes(r.road_code.split("/")[0].trim()));
      const commInts = DATA.intersections.filter(i => i.emirate === selComm.emirate && (i.community.toLowerCase().includes(selComm.community_name.split("(")[0].trim().toLowerCase().slice(0, 6)) || commRoads.some(r => i.connected_road_ids.includes(r.road_id))));
      const commIncidents = DATA.incidents.filter(inc => commRoads.some(r => r.road_id === inc.road_id));
      const commLogistics = DATA.parking.filter(pk => pk.emirate === selComm.emirate);

      container.innerHTML = `
        ${buildWorkspaceStickyHeader("MODULE 02 — CONSTRUCTION INTELLIGENCE", "Construction Activity Dashboard, Published CAPEX/GDV vs. Estimated GDV & Community Explorer", "Strict separation of Combined Published Official Value (AED 765.9B = AED 176.0B Infrastructure/Civil CAPEX across 3 projects + AED 589.9B Real Estate GDV across 24 projects) from Estimated Masterplan GDV (AED 253.0B across 5 projects) and Modelled Hard Construction Cost (AED 595.8B).")}

        <!-- EMIRATE SCOPE FILTER BAR -->
        <div class="aw-panel-card" style="padding:10px 14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; background:#f8fafc;">
          <div style="font-size:0.78rem; color:#334155;">
            <strong>Emirate Intelligence Scope:</strong> Showing <strong>${filteredProjs.length + filteredSubdevs.length}</strong> active Task 2 spatial entities (<strong>${filteredProjs.length}</strong> Flagships + <strong>${filteredSubdevs.length}</strong> JVC Sub-Clusters across <strong>${filteredComms.length}</strong> Hotspot Communities; synced with GIS Map filter)
          </div>
          <div style="display:flex; gap:6px; flex-wrap:wrap;">
            <button id="cmod-em-all" class="ctrl-btn ${activeEmFilter === 'ALL' ? 'primary' : ''}" onclick="filterConstructionEmirate('ALL')">All Dubai &amp; Sharjah (37 Sites · 10 Communities)</button>
            <button id="cmod-em-dxb" class="ctrl-btn ${activeEmFilter === 'Dubai' ? 'primary' : ''}" onclick="filterConstructionEmirate('Dubai')">Dubai Only (25 Sites · 7 Communities)</button>
            <button id="cmod-em-shj" class="ctrl-btn ${activeEmFilter === 'Sharjah' ? 'primary' : ''}" onclick="filterConstructionEmirate('Sharjah')">Sharjah Only (12 Sites · 3 Communities)</button>
          </div>
        </div>

        <!-- 3.1 CONSTRUCTION ACTIVITY OVERVIEW KPIs -->
        <div class="aw-kpi-grid">
          <div class="aw-kpi-card">
            <div class="k-lbl">Total Identified Task 2 Sites</div>
            <div class="k-val">37 Active Entities</div>
            <div class="k-sub"><strong>85</strong> National Projects across 7 Emirates, of which <strong>32</strong> (<strong>20</strong> Dubai + <strong>12</strong> Sharjah) have detailed Task 2 GIS coverage (53 in other 5 Emirates have national inventory coverage only), plus <strong>5</strong> JVC sub-clusters = <strong>37</strong> deep-dive spatial entities</div>
          </div>
          <div class="aw-kpi-card">
            <div class="k-lbl">Combined Published Value (${pubProjs.length}/32)</div>
            <div class="k-val" style="color:#059669;">AED 765.9B</div>
            <div class="k-sub"><span class="ep-pill-pub">PUBLISHED CAPEX + GDV</span> <strong>AED 176.0B</strong> Infrastructure/Civil CAPEX (3 projects) + <strong>AED 589.9B</strong> Published Real Estate GDV (24 projects: 13 Dubai AED 499.4B + 11 Sharjah AED 90.5B)</div>
          </div>
          <div class="aw-kpi-card">
            <div class="k-lbl">Estimated Masterplan GDV (${estProjs.length}/32)</div>
            <div class="k-val" style="color:#b45309;">AED 253.0B</div>
            <div class="k-sub"><span class="badge-missing">ESTIMATED MASTERPLAN GDV</span> 5 Projects with partial contract awards (<code>PRJ-D2</code> AED 100B+, <code>PRJ-D4</code> AED 90B+, <code>PRJ-D11</code> AED 3B+, <code>PRJ-D16</code> AED 55B+, <code>PRJ-SH5</code> AED 5B+)</div>
          </div>
          <div class="aw-kpi-card">
            <div class="k-lbl">Active Structural GFA (10 Communities)</div>
            <div class="k-val" style="color:#2563eb;">31.69M m²</div>
            <div class="k-sub"><strong>199,200</strong> scheduled residential/mixed units (2025–2029) across <strong>180</strong> active developments &amp; <strong>400</strong> towers/clusters</div>
          </div>
          <div class="aw-kpi-card">
            <div class="k-lbl">Incomplete / Restricted Information</div>
            <div class="k-val" style="color:#dc2626;">5 Sub-Clusters</div>
            <div class="k-sub"><span class="badge-missing">NO STANDALONE GDV</span> <code>SUB-JVC-01..05</code> tracked by Active GFA (1.20M m²) &amp; Units (9,330); Plot-level TIS filings restricted in RTA TES portal</div>
          </div>
        </div>

        <!-- 3.2 CONCENTRATION MAP MODE SWITCHER & DISCLOSURE -->
        <div class="aw-panel-card">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
              <h3 style="margin:0;">3.2 Construction Concentration &amp; Spatial Density Controls</h3>
              <p style="font-size:0.75rem; color:#475569; margin:4px 0 0;">
                <strong>Disclosed Density Calculation Method:</strong> MapLibre WebGL kernel density estimation (<code>projects-heatmap-3d</code>) weighted strictly by verified project coordinates and normalized GFA/investment scale tier (Mega ≥25B weight <code>1.0</code>, Major 5–25B weight <code>0.75</code>, Sub-Cluster weight <code>0.65</code>, Standard weight <code>0.50</code>). Does not extrapolate intensity into unmapped parcels.
              </p>
            </div>
            <div style="display:flex; gap:6px; flex-wrap:wrap;">
              <button class="ctrl-btn" onclick="closeAnalyticalWorkspace(); setConcentrationMode('points');">● Switch Map to Project Points</button>
              <button class="ctrl-btn" style="background:#fef3c7; border-color:#f59e0b; color:#92400e;" onclick="closeAnalyticalWorkspace(); setConcentrationMode('heatmap');">🔥 Launch Density Heatmap on Map</button>
              <button class="ctrl-btn" onclick="closeAnalyticalWorkspace(); setConcentrationMode('communities');">⬡ Community Boundaries</button>
              <button class="ctrl-btn" onclick="closeAnalyticalWorkspace(); setConcentrationMode('clusters');">◎ JVC Development Clusters</button>
            </div>
          </div>
        </div>

        <div class="aw-grid-2">
          <!-- PUBLISHED VS ESTIMATED INVESTMENT & MISSING DATA REGISTER -->
          <div class="aw-panel-card">
            <h3>3.1A Valuation Basis Separation (Published Capex vs. Published GDV vs. Estimated GDV) &amp; Missing-Data Register</h3>
            <div class="kv-grid">
              <div class="kv-row">
                <div class="kv-lbl"><span class="ep-pill-pub">CATEGORY 1A — PUBLISHED INFRASTRUCTURE &amp; CIVIL CAPEX</span> 3 Flagship Projects (AED 176.0B Initial / AED 178.5B Awarded in <code>06c</code>)</div>
                <div class="kv-val">
                  Direct government capital expenditure &amp; contract awards (not real estate GDV): <code>PRJ-D1</code> Al Maktoum Int'l Airport Phase 1 (<strong>AED 128.0B</strong> civil aviation capex, Dubai Media Office), <code>PRJ-D8</code> Dubai Metro Blue Line (<strong>AED 18.0B</strong> initial budget / <strong>AED 20.5B</strong> awarded turnkey contract), and <code>PRJ-D9</code> Tasreef Strategic Sewer Tunnel (<strong>AED 30.0B</strong> municipal drainage capex).
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl"><span class="ep-pill-pub">CATEGORY 1B — PUBLISHED REAL ESTATE DEVELOPMENT GDV / INVESTMENT</span> 24 Flagship Projects (AED 589.9B Initial / AED 597.9B in <code>06c</code>)</div>
                <div class="kv-val">
                  Official developer/DLD published gross development value across <strong>13 Dubai real estate flagships</strong> (<strong>AED 499.4B</strong> initial / <strong>AED 507.4B</strong> in <code>06c</code> with <code>PRJ-D3</code> Palm Jebel Ali at AED 150B–158B, <code>PRJ-D5</code> Dubai Creek Harbour AED 75.0B) and <strong>11 Sharjah real estate flagships</strong> (<strong>AED 90.5B</strong>: e.g., <code>PRJ-SH2</code> Aljada AED 35.0B, <code>PRJ-SH1</code> Sharjah Waterfront City AED 25.0B).<br/>
                  • <strong>Combined Published Official Value (27/32 Flagships = 1A + 1B):</strong> <strong>AED 765.9B</strong> (Initial Baseline) / <strong>AED 776.4B</strong> (<code>06c_pipeline_and_calculation_audit.csv</code> Upper Audit Baseline).
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl"><span class="badge-missing">CATEGORY 2 — ESTIMATED MASTERPLAN GDV</span> 5 Flagship Projects (AED 253.0B)</div>
                <div class="kv-val">
                  Masterplans where total GDV is estimated from partial contract awards and phased launches (strictly separated from Category 1A/1B Published Value):<br/>
                  • <code>PRJ-D2</code> Dubai Islands (Est. AED 100.0B+ Masterplan GDV; AED 8.5B+ published villa/hotel awards)<br/>
                  • <code>PRJ-D4</code> Dubai South Residential &amp; Logistics (Est. AED 90.0B+ Multi-Developer GDV; AED 4.0B+ published awards)<br/>
                  • <code>PRJ-D16</code> DAMAC Lagoons (Est. AED 55.0B+ Masterplan GDV; AED 7.0B+ main works package)<br/>
                  • <code>PRJ-SH5</code> Khalid Bin Sultan City (Est. AED 5.0B+ Masterplan GDV; Zaha Hadid masterplan)<br/>
                  • <code>PRJ-D11</code> Burj Binghatti Jacob &amp; Co (Est. AED 3.0B+ GDV; AED 876M DLD baseline)
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl"><span class="badge-missing">CATEGORY 3 — MODELLED HARD COST &amp; MISSING / RESTRICTED DATA</span></div>
                <div class="kv-val">
                  • <strong>Modelled Hard Construction Cost (32/32 Flagships = AED 595.8B):</strong> Derived via RICS / Turner &amp; Townsend GFA unit-cost benchmarks in <code>06c_pipeline_and_calculation_audit.csv</code> (excludes land &amp; developer margin).<br/>
                  • <strong>5 JVC Sub-Clusters (<code>SUB-JVC-01..05</code>):</strong> Multi-parcel developer clusters do not publish a single consolidated GDV; tracked strictly via verified DLD active tower counts (29 towers), total units (9,330), and active structural GFA (1.20M m²).<br/>
                  • <strong>Plot-Level Consultant TIS Reports:</strong> Confidential in RTA's TES portal; platform uses published RTA/SRTA corridor capacity studies (<code>TIS-001..008</code>).
                </div>
              </div>
            </div>
          </div>

          <!-- DEVELOPER & LIFECYCLE DISTRIBUTION -->
          <div class="aw-panel-card">
            <h3>3.1B Top Developers &amp; Lifecycle Status Distribution (Dubai &amp; Sharjah)</h3>
            <div style="font-size:0.74rem; color:#475569; margin-bottom:8px;"><strong>Leading Developers by Flagship Count (Dataset #04):</strong></div>
            ${devSorted.map(([dev, count]) => `
              <div class="aw-bar-row">
                <div><strong>${dev}</strong></div>
                <div class="aw-bar-track"><div class="aw-bar-fill" style="width:${Math.min(100, count * 18)}%; background:#0284c7;"></div></div>
                <div style="text-align:right; font-weight:700;">${count} Flagship${count > 1 ? 's' : ''}</div>
              </div>
            `).join("")}
            <div style="margin-top:12px; font-size:0.74rem; color:#475569;"><strong>Lifecycle Status Breakdown (32 Flagships + 5 Sub-Clusters):</strong></div>
            <div class="kv-grid" style="margin-top:6px;">
              <div class="kv-row">
                <div class="kv-lbl">Active Under Construction / Phased Handover</div>
                <div class="kv-val"><strong>29 Flagship Developments + 5 JVC Sub-Clusters</strong> (Earthworks, Piling, Superstructure, MEP, or Phased Handover verified via DLD Oqood/Escrow &amp; satellite imagery).</div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">Masterplan / Early Infrastructure / Piling Launch</div>
                <div class="kv-val"><strong>3 Developments</strong> (<code>PRJ-D10</code> Burj Azizi piling, <code>PRJ-SH5</code> Khalid Bin Sultan City phase 1 launch, <code>PRJ-SH12</code> Jebel Jais/East Coast).</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3.3 INTERACTIVE COMMUNITY INTELLIGENCE EXPLORER -->
        <div class="aw-panel-card">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:12px;">
            <div>
              <h3 style="margin:0;">3.3 Community Intelligence Explorer — Select Any Community for Full Spatial &amp; Traffic Breakdown</h3>
              <div style="font-size:0.75rem; color:#475569;">Inspect community boundaries, sub-clusters, projects, nearby roads, intersections, roadworks, logistics hubs, and project-to-road connections:</div>
            </div>
            <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
              <select class="haio-select" style="width:auto; min-width:280px;" onchange="selectCommunityInWorkspace(this.value)" aria-label="Select Community in Explorer">
                ${DATA.communities.map(c => `<option value="${c.community_id}" ${c.community_id === selComm.community_id ? 'selected' : ''}>${c.community_id}: ${c.community_name} (${c.emirate} · Score ${c.construction_activity_index_score})</option>`).join("")}
              </select>
              <button class="ctrl-btn" style="background:#2563eb; color:#fff; border-color:#2563eb;" onclick="inspectEntityOnMapFromWorkspace('community', '${selComm.community_id}')">🗺️ Open ${selComm.community_id} on 3D Map</button>
            </div>
          </div>

          <div class="aw-kpi-grid" style="margin-bottom:12px;">
            <div class="aw-kpi-card">
              <div class="k-lbl">Community &amp; Activity Score</div>
              <div class="k-val" style="font-size:1.05rem; color:#2563eb;">${selComm.construction_activity_index_score}</div>
              <div class="k-sub">${selComm.community_name} (<code>${selComm.community_id}</code> · Center: <code>[${selComm.center_lat}, ${selComm.center_lon}]</code>)</div>
            </div>
            <div class="aw-kpi-card">
              <div class="k-lbl">Active Developments &amp; Towers</div>
              <div class="k-val">${selComm.active_developments_count} Devs / ${selComm.active_towers_and_buildings} Towers</div>
              <div class="k-sub">Scheduled Units (2025–2029): <strong>${selComm.scheduled_units_2025_2029.toLocaleString()}</strong></div>
            </div>
            <div class="aw-kpi-card">
              <div class="k-lbl">Active Structural GFA</div>
              <div class="k-val" style="color:#059669;">${selComm.active_structural_gfa_sqm.toLocaleString()} m²</div>
              <div class="k-sub">Boundary Polygon: <strong>${selComm.polygon_wgs84.length} WGS84 Vertices</strong></div>
            </div>
            <div class="aw-kpi-card">
              <div class="k-lbl">Associated Traffic Corridors</div>
              <div class="k-val" style="font-size:0.95rem; color:#dc2626;">${selComm.primary_road_corridors}</div>
              <div class="k-sub">${selComm.observed_congestion_severity}</div>
            </div>
          </div>

          <div class="aw-grid-2">
            <div>
              <h4 style="margin:0 0 8px; font-size:0.84rem; color:#0f172a;">Projects &amp; Sub-Clusters in ${selComm.community_name} (${commProjs.length + commSubdevs.length})</h4>
              <div class="kv-grid">
                ${commProjs.map(p => {
                  const lk = DATA.impact_links.find(x => x.project_id === p.project_id);
                  return `
                  <div class="kv-row" style="cursor:pointer;" onclick="inspectEntityOnMapFromWorkspace('project', '${p.project_id}')">
                    <div class="kv-lbl">${p.project_id} · ${p.developer} · ${(p.published_investment_value || '').split('[')[0]}</div>
                    <div class="kv-val"><strong>${p.project_name}</strong> (${p.lifecycle_status})<br/>${lk ? `Connected to <strong>${lk.primary_road_name} (${lk.distance_to_primary_road_km} km)</strong> · Scenario HGV: ${lk.total_hgv_round_trips_day} round-trips/d` : ''}</div>
                  </div>`;
                }).join("")}
                ${commSubdevs.map(sd => `
                  <div class="kv-row" style="cursor:pointer;" onclick="inspectEntityOnMapFromWorkspace('subdev', '${sd.subdev_id}')">
                    <div class="kv-lbl">${sd.subdev_id} (Sub-Cluster) · ${sd.developer} · <span class="badge-missing">No Standalone GDV</span></div>
                    <div class="kv-val"><strong>${sd.development_name}</strong> — ${sd.building_count} Towers, ${sd.total_units.toLocaleString()} Units, ${sd.active_gfa_sqm.toLocaleString()} m² GFA · <strong>${sd.distance_to_road_km} km</strong> to ${sd.primary_access_road_id}</div>
                  </div>
                `).join("")}
              </div>
            </div>

            <div>
              <h4 style="margin:0 0 8px; font-size:0.84rem; color:#0f172a;">Nearby Roads (${commRoads.length}), Intersections (${commInts.length}), Roadworks (${commIncidents.length}) &amp; Logistics (${commLogistics.length})</h4>
              <div class="kv-grid">
                ${commRoads.map(r => {
                  const obs = getCorridorProfileForWindow(r, currentTimeWindow).obs;
                  return `
                  <div class="kv-row" style="cursor:pointer;" onclick="inspectEntityOnMapFromWorkspace('road', '${r.road_id}')">
                    <div class="kv-lbl">Road Corridor: ${r.road_id} (${r.road_code})</div>
                    <div class="kv-val"><strong>${r.road_name}</strong> · Capacity: ${r.capacity_vph_per_dir}<br/>${obs ? `<span style="color:${congestionColor(obs.congestion_level)}; font-weight:700;">${currentTimeWindow.split('(')[0]}: ~${obs.average_speed_kmh} km/h (V/C=${obs.vc_ratio})</span>` : ''}</div>
                  </div>`;
                }).join("")}
                ${commInts.slice(0, 4).map(i => `
                  <div class="kv-row" style="cursor:pointer;" onclick="inspectEntityOnMapFromWorkspace('intersection', '${i.intersection_id}')">
                    <div class="kv-lbl">Junction Bottleneck: ${i.intersection_id} (${i.peak_level_of_service.split('(')[0]})</div>
                    <div class="kv-val"><strong>${i.intersection_name}</strong> — ${i.rta_upgrade_and_mitigation}</div>
                  </div>
                `).join("")}
                ${commIncidents.map(inc => `
                  <div class="kv-row">
                    <div class="kv-lbl">🚧 Active Roadworks: ${inc.incident_id} (${inc.epistemic_tier})</div>
                    <div class="kv-val"><strong>${inc.road_name}</strong> — ${inc.speed_and_capacity_impact}</div>
                  </div>
                `).join("")}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    // =========================================================================
    // MODULE 04: TRAFFIC INTELLIGENCE (23 CORRIDORS, 4-WINDOW CHARTS, 16 BOTTLENECKS, MULTI-FACTOR CAUSES)
    // =========================================================================
    function renderTrafficIntelligenceModule(container) {
      const keyChartRoadIds = ["RD-DXB-05", "RD-DXB-03", "RD-DXB-01", "RD-DXB-12", "RD-DXB-09", "RD-SHJ-01", "RD-SHJ-02"];
      const timeComparisonRowsHtml = keyChartRoadIds.map(rid => {
        const r = DATA.roads.find(x => x.road_id === rid);
        if (!r) return "";
        const winCells = ALL_TIME_WINDOWS.map(tp => {
          const obs = getCorridorProfileForWindow(r, tp).obs;
          if (!obs) return `<td>—</td>`;
          const col = congestionColor(obs.congestion_level);
          const pct = Math.min(100, Math.round((obs.average_speed_kmh / 100) * 100));
          return `
            <td>
              <div style="display:flex; justify-content:space-between; font-size:0.72rem; font-weight:800; color:${col};">
                <span>${obs.average_speed_kmh} km/h</span>
                <span>V/C ${obs.vc_ratio}</span>
              </div>
              <div class="aw-bar-track" style="margin:3px 0;"><div class="aw-bar-fill" style="width:${pct}%; background:${col};"></div></div>
              <div style="font-size:0.66rem; color:#64748b;">${obs.travel_time_min_per_10km} min/10km · ${obs.modelled_demand_vph_dir}/${obs.reference_capacity_vph_dir} vph</div>
            </td>
          `;
        }).join("");
        return `
          <tr>
            <td><a href="javascript:void(0)" onclick="inspectEntityOnMapFromWorkspace('road', '${r.road_id}')"><strong>${r.road_id}</strong>: ${r.road_name.split('(')[0]}</a><br/><span style="font-size:0.68rem; color:#64748b;">${r.hgv_truck_ban_window.slice(0, 58)}...</span></td>
            ${winCells}
          </tr>
        `;
      }).join("");

      container.innerHTML = `
        ${buildWorkspaceStickyHeader("MODULE 04 — TRAFFIC INTELLIGENCE", "Corridor Performance, 4-Window Diurnal Comparison, Bottleneck Intersections & Multi-Factor Causes", "Published RTA/SRTA statutory capacities, upgrade travel-time reduction targets, and TomTom city-wide baselines combined with transparent two-term BPR + bottleneck-delay corridor modelling.")}

        <!-- 5.2 4-WINDOW VISUAL TIME COMPARISON -->
        <div class="aw-panel-card">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
            <div>
              <h3 style="margin:0;">5.2 Diurnal Time-of-Day Comparison Across Key Corridors (Morning vs. Midday vs. Evening vs. Night)</h3>
              <div style="font-size:0.74rem; color:#475569;">Click any time-window button below to synchronize the entire platform and 3D map lighting/speeds:</div>
            </div>
            <div style="display:flex; gap:6px; flex-wrap:wrap;">
              ${ALL_TIME_WINDOWS.map(tp => `<button class="ctrl-btn ${currentTimeWindow === tp ? 'primary' : ''}" onclick="setTimeWindow('${tp}'); renderTrafficIntelligenceModule(document.getElementById('analyticalWorkspaceModal'));">${tp}</button>`).join("")}
            </div>
          </div>
          <div style="overflow-x:auto;">
            <table class="ev-table">
              <thead>
                <tr>
                  <th>Corridor &amp; HGV Restriction Window</th>
                  <th>🌅 Morning Peak (07:30–09:30)<br/><span style="font-weight:500; color:#dc2626;">HGVs Banned on E11/E44/D61</span></th>
                  <th>🚛 Midday Peak (12:00–14:00)<br/><span style="font-weight:500; color:#d97706;">Active HGV Delivery Window</span></th>
                  <th>🌇 Evening Peak (17:00–20:00)<br/><span style="font-weight:500; color:#dc2626;">HGVs Banned on E11/E44/D61</span></th>
                  <th>🌙 Night Logistics (22:00–05:00)<br/><span style="font-weight:500; color:#059669;">Unrestricted Concrete Pours</span></th>
                </tr>
              </thead>
              <tbody>
                ${timeComparisonRowsHtml}
              </tbody>
            </table>
          </div>
        </div>

        <div class="aw-grid-2">
          <!-- 5.4 MULTI-FACTOR TRAFFIC CAUSE ANALYSIS MATRIX -->
          <div class="aw-panel-card">
            <h3>5.4 Multi-Factor Contextual Congestion Contributors (Non-Exclusive Potential Contributors — Not Single-Factor Proven Causes)</h3>
            <p style="font-size:0.75rem; color:#475569; margin-bottom:8px;">
              <strong>Epistemic &amp; Causal Guardrail:</strong> Isolating exact percentage causal attribution on any road segment requires continuous loop-detector and Origin-Destination (O-D) telemetry. The 8 factors below are presented strictly as <strong>co-existing, non-exclusive contextual contributors</strong> — never as proven single-factor causes — explaining why congestion persists even during 06:30–08:30 AM and 17:30–20:00 PM when HGVs are legally banned on E11, E44, and D61:
            </p>
            <div class="kv-grid">
              <div class="kv-row">
                <div class="kv-lbl">1. Commuter Demand &amp; Cross-Border Flows (Contextual AM/PM Contributor)</div>
                <div class="kv-val"><span class="ep-pill-pub">NON-EXCLUSIVE CONTRIBUTOR (PUBLISHED CONTEXT)</span> Morning &amp; evening rush-hour queues on <code>RD-DXB-05</code> (Hessa St), <code>RD-DXB-01</code> (E11), and <code>RD-SHJ-01</code> (Sharjah E311 National Paints) coincide with peak resident commuter flows when HGVs are banned.</div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">2. Rapid Population &amp; Handover Growth (Background Demand Contributor)</div>
                <div class="kv-val"><span class="ep-pill-pub">NON-EXCLUSIVE CONTRIBUTOR (PUBLISHED CONTEXT)</span> Completed residential handovers in JVC (28,500 scheduled units), Business Bay (19,400 units), and Aljada (25,000 units) contribute background resident vehicles to collector grids.</div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">3. School Zones &amp; Hospital Peak Trips (07:15–08:15 &amp; 14:30–15:30 Contributor)</div>
                <div class="kv-val"><span class="ep-pill-pub">NON-EXCLUSIVE CONTRIBUTOR (GIS LAYER 9: 10 CLUSTERS)</span> 10 mapped education &amp; healthcare facility clusters in <code>09b_nearby_facilities_dataset.csv</code> (5 Education + 5 Healthcare clusters in Dubai &amp; Sharjah, e.g., GEMS/Al Barsha South 0.35 km from Hessa St, University City Sharjah) contribute localized drop-off/pick-up demand.</div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">4. Commercial Attractions, Malls &amp; Parks (Evening &amp; Weekend Contributor)</div>
                <div class="kv-val"><span class="ep-pill-pub">NON-EXCLUSIVE CONTRIBUTOR (GIS LAYER 9: 15 CLUSTERS)</span> 15 mapped retail, park, and commercial districts in <code>09b</code> (e.g., Dubai Mall <code>FAC-DXB-07</code>, Circle Mall JVC <code>FAC-DXB-06</code>, Mall of the Emirates <code>FAC-DXB-08</code>) contribute evening and weekend visitor traffic on D71 and D63.</div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">5. Active RTA/SRTA Capital Roadworks &amp; Diversion Zones (Capacity Contributor)</div>
                <div class="kv-val"><span class="ep-pill-pub">NON-EXCLUSIVE CONTRIBUTOR (5 WORK ZONES)</span> 5 active capital work zones in <code>21c_traffic_incidents_and_roadworks.csv</code> (e.g., <code>INC-DXB-01</code> AED 689M Hessa St flyover works, <code>INC-SHJ-02</code> Etihad Rail University City bridge diversion) temporarily constrain lane geometry during construction before doubling long-term capacity.</div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">6. Signalized &amp; Weaving Intersection Bottlenecks (16 Nodes)</div>
                <div class="kv-val"><span class="ep-pill-mod">NON-EXCLUSIVE CONTRIBUTOR (MODELLED + PUBLISHED)</span> Ramp-weaving and signal delay (modelled <code>+d_adj</code> up to +14.85 min/10km at <code>INT-DXB-01</code> Hessa × Al Khail and <code>INT-SHJ-01</code> National Paints) contribute intersection queuing beyond mid-block link V/C.</div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">7. Dynamic Salik Toll Pricing &amp; Route Redistribution</div>
                <div class="kv-val"><span class="ep-pill-pub">NON-EXCLUSIVE CONTRIBUTOR (PUBLISHED SRC-435)</span> Variable Salik pricing (AED 6 Peak / AED 4 Off-Peak from Jan 31, 2025) + Al Safa South &amp; Business Bay gates incentivize toll-sensitive drivers to use alternative corridors such as Al Khail Rd (E44) and E311.</div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">8. Construction HGV &amp; Industrial Supply Logistics (Midday &amp; Night Contributor)</div>
                <div class="kv-val"><span class="ep-pill-mod">NON-EXCLUSIVE CONTRIBUTOR (TIER 3 SCENARIO)</span> Concrete mixers (8.5 m³) and rebar trailers (25 t) from the 5 Industrial/Logistics zones in <code>09b</code> and 7 Mobility/Staging hubs in <code>20</code> operate primarily on local collector boulevards (<code>RD-DXB-07</code>, <code>RD-DXB-13</code>) and freight corridors during permitted Midday and Night windows.</div>
              </div>
            </div>
          </div>

          <!-- 5.3 BOTTLENECK INTERSECTION EXPLORER (16 NODES) -->
          <div class="aw-panel-card">
            <h3>5.3 Constrained Intersection &amp; Bottleneck Explorer (16 Nodes)</h3>
            <div style="max-height:540px; overflow-y:auto;">
              <table class="ev-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Intersection Name &amp; Type</th>
                    <th>Peak LOS</th>
                    <th>Connected Roads &amp; Projects</th>
                    <th>RTA / SRTA Capital Mitigation</th>
                    <th>Map</th>
                  </tr>
                </thead>
                <tbody>
                  ${DATA.intersections.map(i => `
                    <tr>
                      <td><code>${i.intersection_id}</code></td>
                      <td><strong>${i.intersection_name}</strong><br/><span style="color:#64748b; font-size:0.68rem;">${i.community} · ${i.intersection_type}</span></td>
                      <td><strong style="color:${i.peak_level_of_service.includes('LOS F') || i.peak_level_of_service.includes('LOS E') ? '#dc2626' : '#d97706'};">${i.peak_level_of_service}</strong></td>
                      <td>Roads: <code>${i.connected_road_ids}</code><br/>Projects: <code>${i.served_project_ids}</code></td>
                      <td>${i.rta_upgrade_and_mitigation}</td>
                      <td><button class="ctrl-btn" onclick="inspectEntityOnMapFromWorkspace('intersection', '${i.intersection_id}')">🗺️</button></td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 5.1 FULL 23-CORRIDOR EXPLORER TABLE -->
        <div class="aw-panel-card">
          <h3>5.1 Complete 23-Corridor Engineering &amp; Traffic Intelligence Table (${currentTimeWindow})</h3>
          <div style="overflow-x:auto;">
            <table class="ev-table">
              <thead>
                <tr>
                  <th>Road ID</th>
                  <th>Corridor Name &amp; Code</th>
                  <th>Authority &amp; Type</th>
                  <th>Lanes &amp; Speed Limit</th>
                  <th>Published Capacity (vph/dir)</th>
                  <th>Modelled Speed (${currentTimeWindow.split('(')[0].trim()})</th>
                  <th>Modelled Volume &amp; V/C</th>
                  <th>Congestion Level</th>
                  <th>Evidence &amp; Source</th>
                  <th>Map</th>
                </tr>
              </thead>
              <tbody>
                ${DATA.roads.map(r => {
                  const { obs, exactMatch } = getCorridorProfileForWindow(r, currentTimeWindow);
                  const col = obs ? congestionColor(obs.congestion_level) : "#64748b";
                  return `
                  <tr>
                    <td><code>${r.road_id}</code></td>
                    <td><strong>${r.road_name}</strong> (<code>${r.road_code}</code>)</td>
                    <td>${r.authority}<br/><span style="color:#64748b;">${r.road_type}</span></td>
                    <td>${r.lanes_per_direction} lanes/dir<br/>Limit: ${r.speed_limit_kmh}</td>
                    <td><span class="ep-pill-pub">PUBLISHED</span><br/><strong>${r.capacity_vph_per_dir.split('[')[0]}</strong></td>
                    <td><strong style="color:${col}; font-size:0.82rem;">~${obs ? obs.average_speed_kmh : '—'} km/h</strong><br/><span style="color:#64748b;">${obs ? obs.travel_time_min_per_10km : '—'} min/10km</span></td>
                    <td><span class="ep-pill-mod">MODELLED</span><br/>${obs ? `${obs.modelled_demand_vph_dir}/${obs.reference_capacity_vph_dir} vph (V/C=${obs.vc_ratio})` : '—'}</td>
                    <td><strong style="color:${col};">${obs ? obs.congestion_level : '—'}</strong></td>
                    <td>${exactMatch ? `<span class="ep-pill-pub">Dataset #17 (${obs.observation_id})</span>` : `<span class="ep-pill-mod">Diurnal BPR</span>`}<br/><code>${r.source_id}</code></td>
                    <td><button class="ctrl-btn" onclick="inspectEntityOnMapFromWorkspace('road', '${r.road_id}')">🗺️ Inspect</button></td>
                  </tr>`;
                }).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    // =========================================================================
    // MODULE 05: CONSTRUCTION IMPACT & LOGISTICS (FACILITIES, HGV CHART, 37 LINKS, HYPOTHETICAL SCENARIO ENGINE)
    // =========================================================================
    function runHypotheticalScenario() {
      const roadId = document.getElementById("simRoadSelect")?.value || "RD-DXB-05";
      const hgvMult = parseFloat(document.getElementById("simHgvMultiplier")?.value || "1.0");
      const banMode = document.getElementById("simBanPolicy")?.value || "enforced";
      const capMode = document.getElementById("simUpgradeStage")?.value || "baseline";

      const r = DATA.roads.find(x => x.road_id === roadId) || DATA.roads[4];
      const baseObs = getCorridorProfileForWindow(r, currentTimeWindow).obs;
      if (!baseObs) return;

      const connectedLinks = DATA.impact_links.filter(l => l.primary_road_id === roadId || l.secondary_road_id === roadId);
      const baseDailyHgvMovements = connectedLinks.reduce((acc, l) => acc + (l.total_hgv_one_way_movements_day || 0), 0);

      // Hourly HGV PCE (1 HGV = 2.5 Passenger Car Equivalent)
      const isPeakWindow = currentTimeWindow.includes("Morning") || currentTimeWindow.includes("Evening");
      let hourlyHgvTrips = Math.round((baseDailyHgvMovements * hgvMult) * (isPeakWindow ? (banMode === "enforced" ? 0.02 : 0.14) : 0.12));
      const hgvPceAdded = Math.round(hourlyHgvTrips * 2.5);

      // Capacity adjustment under upgrade stage
      let simCapacity = baseObs.reference_capacity_vph_dir;
      if (capMode === "phased") simCapacity = Math.round(simCapacity * 1.35);
      else if (capMode === "completed") simCapacity = Math.round(simCapacity * 1.85);

      const baseNonHgvDemand = Math.max(400, baseObs.modelled_demand_vph_dir - Math.round((baseDailyHgvMovements * 0.05) * 2.5));
      const simDemand = Math.round(baseNonHgvDemand + hgvPceAdded);
      const simVc = +(simDemand / simCapacity).toFixed(2);

      const t0 = baseObs.free_flow_time_min_per_10km;
      const alpha = baseObs.bpr_alpha || 0.15;
      const beta = baseObs.bpr_beta || 4.0;
      const simBprTime = +(t0 * (1 + alpha * Math.pow(simVc, beta))).toFixed(2);
      const capDelayFactor = capMode === "completed" ? 0.42 : (capMode === "phased" ? 0.70 : 1.0);
      const simBottleneckDelay = +(baseObs.bottleneck_and_control_delay_min_per_10km * capDelayFactor * Math.pow(simVc / Math.max(0.3, baseObs.vc_ratio), 1.4)).toFixed(2);
      const simTotalTime = +(simBprTime + simBottleneckDelay).toFixed(2);
      const simSpeed = +(600.0 / simTotalTime).toFixed(1);
      const speedDelta = +(simSpeed - baseObs.average_speed_kmh).toFixed(1);

      const outEl = document.getElementById("hypotheticalScenarioOutput");
      if (outEl) {
        outEl.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:8px;">
            <span class="badge-hyp">⚠️ HYPOTHETICAL SCENARIO SIMULATION — NOT OBSERVED LIVE TRAFFIC</span>
            <span style="font-size:0.74rem; color:#475569;">Corridor: <strong>${r.road_id} (${r.road_name})</strong> · Window: <strong>${currentTimeWindow}</strong></span>
          </div>
          <div class="aw-kpi-grid" style="margin-bottom:6px;">
            <div class="aw-kpi-card">
              <div class="k-lbl">Baseline Modelled Speed &amp; V/C</div>
              <div class="k-val">${baseObs.average_speed_kmh} km/h</div>
              <div class="k-sub">V/C = <strong>${baseObs.vc_ratio}</strong> (${baseObs.modelled_demand_vph_dir}/${baseObs.reference_capacity_vph_dir} vph/dir)</div>
            </div>
            <div class="aw-kpi-card">
              <div class="k-lbl">Simulated Scenario Speed</div>
              <div class="k-val" style="color:${simSpeed >= baseObs.average_speed_kmh ? '#059669' : '#dc2626'};">${simSpeed} km/h (${speedDelta >= 0 ? '+' : ''}${speedDelta} km/h)</div>
              <div class="k-sub">Travel Time: <strong>${simTotalTime} min/10km</strong> (vs ${baseObs.travel_time_min_per_10km} min/10km baseline)</div>
            </div>
            <div class="aw-kpi-card">
              <div class="k-lbl">Simulated V/C &amp; Capacity</div>
              <div class="k-val" style="color:${simVc <= 0.85 ? '#059669' : '#dc2626'};">V/C = ${simVc}</div>
              <div class="k-sub">Demand: <strong>${simDemand} vph/dir</strong> (incl. +${hgvPceAdded} HGV PCE/hr) · Cap: <strong>${simCapacity} vph/dir</strong></div>
            </div>
            <div class="aw-kpi-card">
              <div class="k-lbl">Simulated BPR + Queue Breakdown</div>
              <div class="k-val" style="font-size:0.95rem;">t_BPR=${simBprTime} + d_adj=${simBottleneckDelay}</div>
              <div class="k-sub">Connected Sites: <strong>${connectedLinks.length}</strong> (${hourlyHgvTrips} HGV movements/hr simulated)</div>
            </div>
          </div>
        `;
      }
    }

    function renderImpactAndLogisticsModule(container) {
      const topHgvLinks = [...DATA.impact_links].sort((a, b) => (b.total_hgv_round_trips_day || 0) - (a.total_hgv_round_trips_day || 0)).slice(0, 10);

      // Corridor exposure ranking
      const roadExposure = DATA.roads.map(r => {
        const links = DATA.impact_links.filter(l => l.primary_road_id === r.road_id || l.secondary_road_id === r.road_id);
        const totalHgv = links.reduce((s, l) => s + (l.total_hgv_round_trips_day || 0), 0);
        const amObs = getCorridorProfileForWindow(r, "Morning Peak (07:30–09:30)").obs;
        return { road: r, linkCount: links.length, totalHgv, amSpeed: amObs ? amObs.average_speed_kmh : 50, amVc: amObs ? amObs.vc_ratio : 0.7 };
      }).sort((a, b) => (b.linkCount * 100 + b.totalHgv) - (a.linkCount * 100 + a.totalHgv)).slice(0, 8);

      container.innerHTML = `
        ${buildWorkspaceStickyHeader("MODULE 05 — CONSTRUCTION IMPACT & LOGISTICS", "Construction Logistics Hubs, 4-Component HGV Movements, 5-Category Epistemic Impact & Scenario Engine", "Explicitly distinguishing Spatial Proximity (Tier 1/2), Modelled HGV Logistics Load (Tier 3), Observed Roadworks Interaction (Tier 4), and Hypothetical Scenario Simulations.")}

        <!-- 7.3 INTERACTIVE HYPOTHETICAL SCENARIO SIMULATOR -->
        <div class="aw-panel-card" style="border:2px solid #cbd5e1; background:#f8fafc;">
          <h3 style="margin:0 0 6px;">7.3 Interactive What-If Construction &amp; Corridor Scenario Simulator</h3>
          <p style="font-size:0.75rem; color:#475569; margin:0 0 10px;">
            Adjust construction HGV intensity, HGV peak-hour ban enforcement, and RTA/SRTA bridge upgrade completion below to compute hypothetical BPR V/C and speed impacts:
          </p>
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px; margin-bottom:12px;">
            <div>
              <label class="haio-field-lbl">TARGET CORRIDOR</label>
              <select id="simRoadSelect" class="haio-select" onchange="runHypotheticalScenario()">
                ${DATA.roads.slice(0, 12).map(r => `<option value="${r.road_id}" ${r.road_id === 'RD-DXB-05' ? 'selected' : ''}>${r.road_id}: ${r.road_name.split('(')[0]}</option>`).join("")}
              </select>
            </div>
            <div>
              <label class="haio-field-lbl">ACTIVE CONSTRUCTION HGV INTENSITY</label>
              <select id="simHgvMultiplier" class="haio-select" onchange="runHypotheticalScenario()">
                <option value="0.5">50% Intensity (Off-Peak / Earthworks Complete)</option>
                <option value="1.0" selected>100% Baseline Active Core Pour Intensity</option>
                <option value="1.5">150% Surge Intensity (Simultaneous Raft Pours)</option>
                <option value="2.0">200% Extreme Stress Test (2x Active Sites)</option>
              </select>
            </div>
            <div>
              <label class="haio-field-lbl">RTA PEAK-WINDOW HGV BAN POLICY</label>
              <select id="simBanPolicy" class="haio-select" onchange="runHypotheticalScenario()">
                <option value="enforced" selected>Statutory HGV Ban Enforced (06:30–08:30 &amp; 17:30–20:00)</option>
                <option value="unrestricted">Hypothetical Unrestricted HGV Access in Peak Hours</option>
              </select>
            </div>
            <div>
              <label class="haio-field-lbl">RTA / SRTA CAPITAL UPGRADE STAGE</label>
              <select id="simUpgradeStage" class="haio-select" onchange="runHypotheticalScenario()">
                <option value="baseline" selected>Current Work-Zone Baseline Capacity</option>
                <option value="phased">Phased Flyover Opening (+35% Capacity)</option>
                <option value="completed">Full Upgrade Complete (+85% Capacity / Grade-Separated)</option>
              </select>
            </div>
          </div>
          <div id="hypotheticalScenarioOutput"></div>
        </div>

        <div class="aw-grid-2">
          <!-- 6.1 & 6.3 LOGISTICS FACILITIES & CORRIDOR NETWORK -->
          <div class="aw-panel-card">
            <h3>6.1 &amp; 6.3 Industrial Logistics Zones (5 in Dataset #09b) &amp; Mobility/Delivery Staging Hubs (7 in Dataset #20)</h3>
            <p style="font-size:0.74rem; color:#475569; margin-bottom:8px;">
              <strong>Exact Two-Tier Facility Reconciliation:</strong> Dataset <code>09b_nearby_facilities_dataset.csv</code> maps <strong>30 Dubai &amp; Sharjah Urban/Industrial Facility Clusters</strong> (18 Dubai + 12 Sharjah across 6 categories, including <strong>5 Major Industrial, Port &amp; Construction Supply Zones</strong>: <code>FAC-DXB-16</code> JAFZA/NIP, <code>FAC-DXB-17</code> Dubai South Logistics/DWC, <code>FAC-DXB-18</code> Al Quoz/Ras Al Khor/Warsan Industrial, <code>FAC-SHJ-11</code> SAIF/Hamriyah Port, <code>FAC-SHJ-12</code> Sajaa &amp; Sharjah Industrial 1–18), while Dataset <code>20_parking_and_mobility_facilities.csv</code> below maps <strong>7 Dedicated Parking, EV &amp; Last-Mile Delivery Staging Hubs</strong> (6 Dubai + 1 Sharjah):
            </p>
            <div style="overflow-x:auto;">
              <table class="ev-table">
                <thead>
                  <tr>
                    <th>Hub ID</th>
                    <th>Facility Name &amp; Type</th>
                    <th>Capacity / Fleet</th>
                    <th>Corridor → Projects Network &amp; HGV Rule</th>
                  </tr>
                </thead>
                <tbody>
                  ${DATA.parking.map(pk => `
                    <tr>
                      <td><code>${pk.parking_id}</code></td>
                      <td><strong>${pk.facility_name}</strong><br/><span style="color:#64748b; font-size:0.68rem;">${pk.emirate} · ${pk.community} (${pk.facility_category || pk.facility_type || 'Logistics & Staging'})</span></td>
                      <td><strong>${pk.capacity_bays}</strong></td>
                      <td>${pk.occupancy_and_congestion_impact}</td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
            <details class="tech-accordion" style="margin-top:10px;" open>
              <summary>🏭 Inspect All 30 Dubai &amp; Sharjah Urban &amp; Industrial Facility Clusters (<code>09b_nearby_facilities_dataset.csv</code> — 18 Dubai + 12 Sharjah)</summary>
              <div class="tech-body" style="max-height:290px; overflow-y:auto; padding:6px;">
                <table class="ev-table">
                  <thead>
                    <tr>
                      <th>Facility ID</th>
                      <th>Emirate</th>
                      <th>Category</th>
                      <th>Facility / Industrial Cluster Name</th>
                      <th>Dist to Projects</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${DATA.facilities.map(f => `
                      <tr>
                        <td><code>${f.facility_id || f.id || 'FAC'}</code></td>
                        <td><strong>${f.emirate}</strong></td>
                        <td>${f.facility_category}</td>
                        <td><strong>${f.feature_name}</strong></td>
                        <td>${f.distance_to_projects_km} km</td>
                      </tr>
                    `).join("")}
                  </tbody>
                </table>
              </div>
            </details>
          </div>

          <!-- 6.2 4-COMPONENT HGV LOAD BREAKDOWN & TOP GENERATORS -->
          <div class="aw-panel-card">
            <h3>6.2 Top 10 Projects Ranked by Scenario Daily HGV Round-Trips (4-Component Model)</h3>
            <p style="font-size:0.74rem; color:#475569; margin-bottom:8px;">
              <strong>Disclosed Formula:</strong> Sum of Ready-Mix Concrete (<code>0.42 m³/m² ÷ 8.5 m³ mixer</code>), Rebar (<code>0.065 t/m² ÷ 25 t trailer</code>), Earthworks (<code>0.35 m³/m² ÷ 18 m³ tipper</code>), and MEP/Fit-Out (<code>0.18 t/m² ÷ 12 t truck</code>) over 1,825 days × active phase multiplier:
            </p>
            ${topHgvLinks.map(l => {
              const pct = Math.min(100, Math.round((l.total_hgv_round_trips_day / 1600) * 100));
              return `
                <div class="aw-bar-row" style="cursor:pointer;" onclick="inspectEntityOnMapFromWorkspace('project', '${l.project_id}')">
                  <div><strong>${l.project_id}</strong>: ${l.project_name.split('(')[0].slice(0, 22)}</div>
                  <div class="aw-bar-track"><div class="aw-bar-fill" style="width:${pct}%; background:#d97706;"></div></div>
                  <div style="text-align:right; font-size:0.72rem;"><strong>${l.total_hgv_round_trips_day} trips/d</strong> (${l.concrete_mixer_loads_day} mix / ${l.rebar_trailer_loads_day} reb)</div>
                </div>
              `;
            }).join("")}

            <h4 style="margin:14px 0 6px; font-size:0.82rem; color:#0f172a;">7.2 Top Corridors Ranked by Connected Construction Exposure</h4>
            <div style="overflow-x:auto;">
              <table class="ev-table">
                <thead>
                  <tr>
                    <th>Road ID</th>
                    <th>Corridor Name</th>
                    <th>Connected Sites</th>
                    <th>Combined Scenario HGV Trips/Day</th>
                    <th>AM Peak Speed &amp; V/C</th>
                  </tr>
                </thead>
                <tbody>
                  ${roadExposure.map(re => `
                    <tr style="cursor:pointer;" onclick="inspectEntityOnMapFromWorkspace('road', '${re.road.road_id}')">
                      <td><code>${re.road.road_id}</code></td>
                      <td><strong>${re.road.road_name}</strong></td>
                      <td><strong>${re.linkCount} Sites</strong></td>
                      <td><strong>${re.totalHgv.toLocaleString()} round-trips/d</strong></td>
                      <td>~${re.amSpeed} km/h (V/C=${re.amVc})</td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 7.1 COMPLETE 37-LINK PROJECT-TO-ROAD IMPACT TABLE WITH 5 EPISTEMIC CATEGORIES -->
        <div class="aw-panel-card">
          <h3>7.1 Complete 37-Link Project-to-Road Spatial &amp; Epistemic Impact Matrix (Dataset #22)</h3>
          <p style="font-size:0.74rem; color:#475569; margin-bottom:8px;">
            Every link is classified into our strict Epistemic Impact Hierarchy: <strong>1. Spatial Proximity Only</strong> (WGS84 Haversine distance to nearest vertex), <strong>2. Shared Corridor Exposure</strong> (Tier 2), <strong>3. Modelled Construction Logistics Load</strong> (Tier 3 4-component HGV trips), <strong>4. Observed Roadworks / Bottleneck Interaction</strong> (Tier 4), and <strong>5. Confirmed Direct Traffic Impact</strong> (substantiated by official RTA/SRTA work-zone/corridor filings).<br/>
            <strong>Computational Consistency vs. Positional/Causal Qualification:</strong> The <code>37/37</code> nearest-vertex checks establish computational consistency between stored project-road links and referenced OpenStreetMap highway geometries (<code>0.00 km</code> discrepancy). They do not independently establish positional road survey accuracy, verified cadastral plot boundaries, or that the geometrically nearest road is necessarily the sole or primary road affected by construction—making this 5-category spatial-association classification essential:
          </p>
          <div style="max-height:520px; overflow-y:auto;">
            <table class="ev-table">
              <thead>
                <tr>
                  <th>Link ID</th>
                  <th>Project / Sub-Cluster</th>
                  <th>Primary Road Corridor &amp; Vertex Dist</th>
                  <th>Nearest Junction &amp; Dist</th>
                  <th>4-Component Scenario HGV Trips/Day</th>
                  <th>HGV Window Compliance</th>
                  <th>Epistemic Impact Classification</th>
                  <th>Map</th>
                </tr>
              </thead>
              <tbody>
                ${DATA.impact_links.map(l => `
                  <tr>
                    <td><code>${l.link_id}</code></td>
                    <td><strong>${l.project_id}</strong>: ${l.project_name.split('(')[0]}<br/><span style="color:#64748b; font-size:0.68rem;">${l.emirate} · ${l.community}</span></td>
                    <td><a href="javascript:void(0)" onclick="inspectEntityOnMapFromWorkspace('road', '${l.primary_road_id}')"><strong>${l.primary_road_id}</strong>: ${l.primary_road_name.split('(')[0]}</a><br/><strong>${l.distance_to_primary_road_km} km</strong> to <code>[${l.nearest_road_vertex_wgs84}]</code></td>
                    <td><code>${l.nearest_intersection_id}</code> (${l.distance_to_intersection_km} km)<br/><span style="color:#64748b; font-size:0.68rem;">${l.nearest_intersection_name}</span></td>
                    <td><strong>${l.total_hgv_round_trips_day} round-trips/d</strong> (${l.total_hgv_one_way_movements_day} one-way)<br/><span style="font-size:0.68rem; color:#64748b;">Mix:${l.concrete_mixer_loads_day} | Reb:${l.rebar_trailer_loads_day} | Tip:${l.earthworks_tipper_loads_day} | MEP:${l.mep_fitout_truck_loads_day}</span></td>
                    <td>${l.hgv_routing_and_ban_compliance}</td>
                    <td><span class="ep-pill-mod">${l.epistemic_impact_classification}</span></td>
                    <td><button class="ctrl-btn" onclick="inspectEntityOnMapFromWorkspace('${l.project_id.startsWith('SUB-') ? 'subdev' : 'project'}', '${l.project_id}')">🗺️</button></td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
      runHypotheticalScenario();
    }

    // =========================================================================
    // MODULE 07: DATA, METHODOLOGY & EVIDENCE (DATA CATALOGUE, WORKED BPR/HGV MATH, DATA QUALITY, EXPORTS)
    // =========================================================================
    function renderDataAndEvidenceModule(container) {
      const catList = [
        { id: "15_transport_open_data_register", name: "UAE & Emirate Transport Open-Data Source Register", rows: DATA.tds.length, type: "Published Official Portals", src: "RTA, Dubai Pulse, DLD, SRTA, FCSC, OSM", csv: "15_transport_open_data_register.csv" },
        { id: "16_road_network_dataset", name: "Dubai & Sharjah Road Network Corridors (OSM WGS84)", rows: DATA.roads.length, type: "Published Capacity + Verified GIS", src: "RTA (SRC-433, SRC-434), SRTA, OpenStreetMap", csv: "16_road_network_dataset.csv" },
        { id: "17_traffic_congestion_observations", name: "City-Wide Baseline & Corridor BPR Observations", rows: DATA.observations.length, type: "1 Published Baseline + 21 Modelled BPR", src: "TomTom Index (SRC-436), RTA, BPR Model", csv: "17_traffic_congestion_observations.csv" },
        { id: "18_tomtom_and_provider_assessment", name: "Traffic Telemetry & GIS Data Provider Audit", rows: DATA.providers.length, type: "Verified Technical Audit", src: "TomTom, Dubai Pulse, HERE, Google, Mapbox", csv: "18_tomtom_and_provider_assessment.csv" },
        { id: "19_traffic_impact_studies_and_logistics", name: "Corridor Traffic Impact Studies (TIS) & HGV Logistics", rows: DATA.tis.length, type: "Published Corridor Studies", src: "RTA TES & Corridor Releases, SRTA", csv: "19_traffic_impact_studies_and_logistics.csv" },
        { id: "20_parking_and_mobility_facilities", name: "Parking (Parkin PJSC), EV & Delivery Staging Hubs", rows: DATA.parking.length, type: "Published Statutory + Verified GIS", src: "Parkin PJSC, RTA, DEWA EV Green Charger", csv: "20_parking_and_mobility_facilities.csv" },
        { id: "21a_communities_and_hotspots", name: "Community Construction Hotspots & Polygons", rows: DATA.communities.length, type: "Published + Derived Index", src: "DLD Open Data (SRC-020), DM GIS, SRTA", csv: "21a_communities_and_hotspots.csv" },
        { id: "21b_intersections_and_nodes", name: "Major Road Intersections & Bottleneck Nodes", rows: DATA.intersections.length, type: "Published Upgrades + Modelled LOS", src: "RTA Hessa/Al Khail Releases, SRTA", csv: "21b_intersections_and_nodes.csv" },
        { id: "21c_traffic_incidents_and_roadworks", name: "Active RTA/SRTA Capital Roadworks & Diversions", rows: DATA.incidents.length, type: "Published Official Works", src: "RTA Media Releases, SRTA, Etihad Rail", csv: "21c_traffic_incidents_and_roadworks.csv" },
        { id: "21d_jvc_and_community_subdevelopments", name: "JVC Multi-Tower Sub-Development Clusters", rows: DATA.subdevs.length, type: "Published Registry + Modelled HGV", src: "DLD dld_projects-open (SRC-020)", csv: "21d_jvc_and_community_subdevelopments.csv" },
        { id: "22_project_road_impact_links", name: "Project-to-Road Spatial & Epistemic Impact Links", rows: DATA.impact_links.length, type: "Derived Geodesic + Modelled HGV", src: "WGS84 Haversine + 4-Component HGV Model", csv: "22_project_road_impact_links.csv" }
      ];
      const totalCatRows = catList.reduce((acc, c) => acc + c.rows, 0);

      container.innerHTML = `
        ${buildWorkspaceStickyHeader("MODULE 07 — DATA, METHODOLOGY & EVIDENCE", "Data Catalogue, Worked BPR & HGV Mathematical Equations, Data-Quality Reconciliation & Exports", "100% traceability from published government/regulatory benchmarks (RTA, SRTA, DLD, TomTom, Salik) to derived spatial geometry and modelled BPR/HGV outputs.")}

        <!-- PHASE 10: EXPORT & REPORTING BAR -->
        <div class="aw-panel-card" style="background:#f8fafc; border:1.5px solid #cbd5e1;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div>
              <h3 style="margin:0;">10.1 Client Export &amp; Reporting Center</h3>
              <div style="font-size:0.75rem; color:#475569;">Download filtered CSV tables, the unified GeoJSON GIS bundle, the 30-object Spatial SQLite database, or print a formatted Executive PDF Report:</div>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              <button id="btnExportCsv" class="ctrl-btn primary" onclick="exportFilteredProjectsCsv()">📥 Export Filtered Projects CSV</button>
              <button id="btnExportJson" class="ctrl-btn" onclick="exportTask2JsonBundle()">📄 Export Task 2 JSON Bundle</button>
              <a id="btnExportGeojson" class="ctrl-btn" style="text-decoration:none;" href="datasets/dubai_sharjah_gis_bundle.geojson" download="dubai_sharjah_gis_bundle.geojson">🗺️ GeoJSON Bundle (123 Features)</a>
              <a id="btnExportSqlite" class="ctrl-btn" style="text-decoration:none;" href="datasets/21_task2_spatial_database.sqlite" download="21_task2_spatial_database.sqlite">🗄️ Spatial SQLite DB (30 Objects)</a>
              <button id="btnPrintPdf" class="ctrl-btn" onclick="printExecutiveReport()">🖨️ Print Executive Report (PDF)</button>
            </div>
          </div>
        </div>

        <!-- 8.3 DATA QUALITY & RECONCILIATION DASHBOARD -->
        <div class="aw-panel-card">
          <h3>8.3 Data-Quality, Epistemic Separation &amp; Reconciliation Dashboard (All 8 Audit Items Reconciled)</h3>
          <div class="aw-grid-2">
            <div class="kv-grid">
              <div class="kv-row">
                <div class="kv-lbl">1. TomTom Dubai Traffic Index Reconciliation (42.7% Stored Baseline vs. 47.5% Narrative Note)</div>
                <div class="kv-val">
                  • <strong>Authoritative Stored Baseline (<code>OBS-DXB-CITY-00</code> in <code>17_traffic_congestion_observations.csv</code> / <code>SRC-436</code>):</strong> Records <strong>42.7%</strong> full-year 24/7 metropolitan congestion level (% additional travel time above free-flow), <strong>31.3 km/h</strong> average speed (<strong>19 min 10 sec</strong> per 10 km), <strong>42.3%</strong> AM rush congestion (32.1 km/h, 18m 41s / 10km), and <strong>94.4%</strong> PM rush congestion (22.6 km/h, 26m 33s / 10km).<br/>
                  • <strong>Why 47.5% Appeared in Earlier Narrative Notes:</strong> Referenced an urban-core / daytime edition comparison (+4.8 pp variance between city-center boundary vs. wider metropolitan bounding box and YoY vehicle growth). <code>47.5%</code> is <em>not</em> stored in any Task 2 CSV table.<br/>
                  • <strong>Strict Epistemic Rule:</strong> City-wide aggregates are never disaggregated to individual road segments.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">2. Valuation Terminology Reconciliation (Published Capex vs. Published GDV vs. Estimated GDV)</div>
                <div class="kv-val">
                  • <strong>Category 1A — Published Infrastructure &amp; Civil Capex (3/32 Flagships):</strong> <strong>AED 176.0B</strong> initial budget / <strong>AED 178.5B</strong> contract award in <code>06c</code> (<code>PRJ-D1</code> AED 128.0B, <code>PRJ-D8</code> AED 18.0B–20.5B, <code>PRJ-D9</code> AED 30.0B).<br/>
                  • <strong>Category 1B — Published Real Estate Development GDV / Investment (24/32 Flagships):</strong> <strong>AED 589.9B</strong> initial baseline / <strong>AED 597.9B</strong> in <code>06c</code> (13 Dubai real estate projects = AED 499.4B–507.4B; 11 Sharjah real estate projects = AED 90.5B).<br/>
                  • <strong>Combined Published Official Value (27/32 = 1A + 1B):</strong> <strong>AED 765.9B</strong> (Initial Baseline) / <strong>AED 776.4B</strong> (<code>06c</code> Audit Total).<br/>
                  • <strong>Category 2 — Estimated Masterplan GDV (5/32 Flagships):</strong> <strong>AED 253.0B</strong> across 5 masterplans with partial contract awards (<code>PRJ-D2</code>, <code>PRJ-D4</code>, <code>PRJ-D11</code>, <code>PRJ-D16</code>, <code>PRJ-SH5</code>).<br/>
                  • <strong>Category 3 — Modelled Hard Construction Cost (32/32 Flagships):</strong> <strong>AED 595.8B</strong> via RICS/T&amp;T unit-cost benchmarks (<code>06c_pipeline_and_calculation_audit.csv</code>).
                </div>
              </div>
            </div>
            <div class="kv-grid">
              <div class="kv-row">
                <div class="kv-lbl">3. Scope &amp; Facility Grouping Reconciliation (85 vs. 37 Sites; 30 Facilities vs. 7 Hubs)</div>
                <div class="kv-val">
                  • <strong>85 National Projects vs. 37 Deep-Dive Entities:</strong> <code>04_project_inventory.csv</code> contains <strong>85</strong> flagship projects across all 7 Emirates. Task 2 performs deep spatial &amp; BPR/HGV corridor modelling on <strong>37</strong> entities in Dubai &amp; Sharjah (<strong>20</strong> Dubai flagships + <strong>12</strong> Sharjah flagships = <strong>32</strong> flagships, plus <strong>5</strong> JVC multi-tower sub-clusters <code>SUB-JVC-01..05</code>). The remaining <strong>53</strong> flagships (Abu Dhabi 15, RAK 12, Ajman 10, UAQ 8, Fujairah 8) have national inventory/GFA/cost/coordinate coverage only.<br/>
                  • <strong>30 Urban/Industrial Facilities (<code>09b</code>) vs. 7 Mobility/Staging Hubs (<code>20</code>):</strong> Layer 9 (<code>09b_nearby_facilities_dataset.csv</code>) maps <strong>30</strong> Dubai &amp; Sharjah facility clusters (out of 80 UAE-wide), including <strong>5</strong> Major Industrial/Port/Logistics Zones (<code>FAC-DXB-16..18</code>, <code>FAC-SHJ-11..12</code>) and <strong>25</strong> Schools, Hospitals, Malls, Parks &amp; Commercial Centres. Layer 10 (<code>20_parking_and_mobility_facilities.csv</code>) maps <strong>7</strong> dedicated Parking, EV &amp; Delivery Staging Hubs (<code>PRK-DXB-01..06</code>, <code>PRK-SHJ-01</code>).
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">4. 3D Building Coverage (950 Cap Fallback) &amp; Complete WebGL GPU Disposal</div>
                <div class="kv-val">
                  • <strong>Zero Geographic Gaps Across Zoom Levels:</strong> At zoom ≥ 14.0, the nearest <strong>950</strong> OpenMapTiles building footprints render as Three.js meshes with procedural 4K façades. Whenever <code>candidates.length &gt; 950</code> (<code>osmCityTruncated = true</code>), MapLibre's native GPU <code>osm-3d-buildings</code> <code>fill-extrusion</code> layer automatically remains visible at <code>0.55</code> opacity so buildings beyond the 950 cap still render in 3D with zero geographic holes.<br/>
                  • <strong>Full GPU Resource Cleanup:</strong> <code>disposeThreeGroup(grp, true)</code> and <code>disposeAllThreeGpuResources()</code> explicitly dispose buffer geometries, materials, procedural <code>CanvasTexture</code> maps, and <code>renderer.renderLists</code>.
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 8.2 STEP-BY-STEP WORKED METHODOLOGY EXPLORER -->
        <div class="aw-panel-card">
          <h3>8.2 Step-by-Step Mathematical Methodology &amp; Worked Examples</h3>
          <div class="aw-grid-2">
            <div class="kv-grid">
              <div class="kv-row">
                <div class="kv-lbl">Equation 1 — Two-Term BPR Link + Bottleneck Delay Model</div>
                <div class="kv-val">
                  <code>t_BPR = t₀ × [1 + α × (V / C)^β]</code> &nbsp;|&nbsp; <code>t_total = t_BPR + d_adj</code> &nbsp;|&nbsp; <code>v_modelled = 600 / t_total</code><br/>
                  <strong>Worked Example (<code>OBS-DXB-001</code> — Hessa St D61 Morning Peak 07:30–09:30):</strong><br/>
                  1. Free-flow speed <code>v₀ = 80 km/h</code> → <code>t₀ = 600 / 80 = 7.50 min/10km</code>.<br/>
                  2. Pre-upgrade capacity <code>C = 4,000 vph/dir</code> (published RTA <code>SRC-433</code>); AM demand <code>V = 4,160 vph/dir</code> → <code>V/C = 1.04</code>.<br/>
                  3. Uninterrupted BPR time (<code>α=0.15, β=4.0</code>): <code>t_BPR = 7.50 × [1 + 0.15 × (1.04)⁴] = 8.81 min/10km</code> (<code>v_BPR = 68.1 km/h</code>).<br/>
                  4. Signal/ramp queue delay at Al Khail &amp; SZR interchanges: <code>d_adj = +11.87 min/10km</code>.<br/>
                  5. Total travel time: <code>8.81 + 11.87 = 20.68 min/10km</code> → Modelled Speed = <strong><code>600 / 20.68 = 29.0 km/h</code></strong>.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">Equation 2 — 4-Component Scenario Daily HGV Trip Estimation</div>
                <div class="kv-val">
                  <code>Trips/day = [(GFA×0.42/8.5) + (GFA×0.065/25) + (GFA×0.35/18) + (GFA×0.18/12)] / 1,825 × M_phase</code><br/>
                  <strong>Worked Example (<code>PRJ-D6</code> — JVC Active High-Rise Cluster, <code>GFA = 3,420,000 m²</code>, <code>M_phase = 2.085</code>):</strong><br/>
                  • Concrete Mixers (8.5 m³): <strong>193 loads/day</strong> | Rebar Trailers (25 t): <strong>11 loads/day</strong><br/>
                  • Earthworks Tippers (18 m³): <strong>76 loads/day</strong> | MEP/Fit-Out Trucks (12 t): <strong>59 loads/day</strong><br/>
                  • Total Scenario Load: <strong>339 round-trips/day (678 one-way HGV movements/day)</strong>.
                </div>
              </div>
            </div>
            <div class="kv-grid">
              <div class="kv-row">
                <div class="kv-lbl">Equation 3 — Composite Construction Activity Index (0–100 Scale)</div>
                <div class="kv-val">
                  <code>Score = 0.35 × Norm(GFA) + 0.25 × Norm(Units) + 0.20 × Norm(Towers) + 0.20 × Norm(Devs)</code><br/>
                  <strong>Worked Example (<code>COM-DXB-01</code> — JVC &amp; Al Barsha South):</strong><br/>
                  38 active developments, 64 active towers, 28,500 scheduled units, 3.42M m² active structural GFA → Composite Score = <strong>94.5 / 100 (Rank #2 in UAE behind Dubai South 96.0)</strong>.
                </div>
              </div>
              <div class="kv-row">
                <div class="kv-lbl">Equation 4 — WGS84 Geodesic Nearest-Vertex Distance (Haversine)</div>
                <div class="kv-val">
                  <code>d = 2R × arcsin(√[sin²(Δφ/2) + cos(φ₁)cos(φ₂)sin²(Δλ/2)])</code>, <code>R = 6,371.0 km</code><br/>
                  Computed from each project centroid <code>[lat, lon]</code> to the exact nearest vertex along the OpenStreetMap highway polyline (verified to <code>0.00 km</code> computational consistency at stored 2-decimal precision across all 37 links; maximum unrounded floating-point rounding difference is <code>0.00495 km</code> / <code>~4.95 m</code>). Note: nearest-vertex computational consistency does not independently establish positional road survey accuracy, verified cadastral plot boundaries, or that the nearest road is necessarily the road affected by construction; therefore each link is governed by the 5-category epistemic spatial-association classification.
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 8.1 DATA CATALOGUE TABLE -->
        <div class="aw-panel-card">
          <h3>8.1 Complete Task 2 Dataset Catalogue (${catList.length} Datasets · ${totalCatRows} Verified Records + Spatial SQLite)</h3>
          <div style="overflow-x:auto;">
            <table class="ev-table">
              <thead>
                <tr>
                  <th>Dataset ID</th>
                  <th>Dataset Title</th>
                  <th>Row Count</th>
                  <th>Epistemic Type</th>
                  <th>Primary Sources</th>
                  <th>Download CSV</th>
                </tr>
              </thead>
              <tbody>
                ${catList.map(c => `
                  <tr>
                    <td><code>${c.id}</code></td>
                    <td><strong>${c.name}</strong></td>
                    <td><strong>${c.rows} rows</strong></td>
                    <td><span class="ep-pill-pub">${c.type}</span></td>
                    <td>${c.src}</td>
                    <td><a class="ctrl-btn" style="text-decoration:none;" href="csv/${c.csv}" download="${c.csv}">📥 CSV</a> <a class="ctrl-btn" style="text-decoration:none;" href="https://raw.githubusercontent.com/Siddiqahmed26/uae-construction-intelligence/main/csv/${c.csv}" target="_blank" rel="noopener">Raw ↗</a></td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
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
      document.querySelectorAll(".bm-btn").forEach(b => {
        if (b.id !== "btn3dTilt" && b.id !== "collapseRightBtn") {
          const oc = b.getAttribute("onclick") || "";
          const matchMode = btnEl ? (b === btnEl) : oc.includes(`'${currentBasemapMode}'`);
          b.classList.toggle("active", Boolean(matchMode));
        }
      });
      syncMapCanvasBackdropClass();
      if (isMap3dGlAlive()) {
        syncPhotorealistic3DVisibility();
        forceMap3dRepaintBurst();
      }
      if (map) {
        if (currentCameraDim === "2D") {
          ensureLeafletBaseTiles();
        } else if (baseTileLayer) {
          try { map.removeLayer(baseTileLayer); } catch (_) {}
          baseTileLayer = null;
        }
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
      const aw = document.getElementById("analyticalWorkspaceModal");
      if (aw && aw.classList.contains("open")) {
        if (currentPlatformMode === "construction") renderConstructionIntelligenceModule(aw);
        else if (currentPlatformMode === "traffic") renderTrafficIntelligenceModule(aw);
        else if (currentPlatformMode === "impact") renderImpactAndLogisticsModule(aw);
        else if (currentPlatformMode === "overview") renderExecutiveOverviewModule(aw);
        else if (currentPlatformMode === "evidence") renderDataAndEvidenceModule(aw);
      }
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


    let localStreetTraffic2DGroup = null;

    function render2DZoomedStreetTraffic() {
      if (!map || !layerGroups || !layerGroups.traffic) return;
      if (!localStreetTraffic2DGroup) {
        localStreetTraffic2DGroup = L.layerGroup();
      }
      localStreetTraffic2DGroup.clearLayers();
      if (!layerGroups.traffic.hasLayer(localStreetTraffic2DGroup)) {
        localStreetTraffic2DGroup.addTo(layerGroups.traffic);
      }
      const showTraffic = document.getElementById("chk-L6")?.checked ?? true;
      const z2d = map.getZoom();
      if (!showTraffic || z2d < 12.5) return;
      if (!map3d || typeof map3d.querySourceFeatures !== "function" || !map3d.getSource || !map3d.getSource("openmaptiles")) return;

      let feats = [];
      try {
        feats = map3d.querySourceFeatures("openmaptiles", { sourceLayer: "transportation" }) || [];
      } catch (_) {
        return;
      }
      if (!feats.length) return;

      const b = map.getBounds().pad(0.18);
      const minLat = b.getSouth(), maxLat = b.getNorth(), minLng = b.getWest(), maxLng = b.getEast();
      const allowed = z2d >= 14.2
        ? new Set(["motorway", "trunk", "primary", "secondary", "tertiary", "minor"])
        : new Set(["motorway", "trunk", "primary", "secondary", "tertiary"]);
      const zMul = z2d >= 17 ? 1.55 : (z2d >= 16 ? 1.25 : (z2d >= 14.5 ? 0.95 : 0.72));
      const baseWeightByClass = { motorway: 6.4, trunk: 6.0, primary: 5.0, secondary: 4.2, tertiary: 3.4, minor: 2.7 };
      let drawn = 0;
      const seenKeys = new Set();

      for (let i = 0; i < feats.length && drawn < 420; i++) {
        const f = feats[i];
        const cls = f && f.properties && f.properties.class;
        if (!allowed.has(cls)) continue;
        const g = f.geometry;
        if (!g) continue;
        const lines = g.type === "LineString" ? [g.coordinates] : (g.type === "MultiLineString" ? g.coordinates : []);
        const cols = getOsmClassColorsFor2D(cls, currentTimeWindow);
        const coreW = (baseWeightByClass[cls] || 2.8) * zMul;
        const caseW = coreW + Math.max(1.8, 1.4 * zMul);

        for (let j = 0; j < lines.length && drawn < 420; j++) {
          const ring = lines[j];
          if (!ring || ring.length < 2) continue;
          const p0 = ring[0], pN = ring[ring.length - 1];
          if ((p0[1] < minLat && pN[1] < minLat) || (p0[1] > maxLat && pN[1] > maxLat) ||
              (p0[0] < minLng && pN[0] < minLng) || (p0[0] > maxLng && pN[0] > maxLng)) {
            continue;
          }
          const key = `${cls}:${p0[0].toFixed(5)},${p0[1].toFixed(5)}-${pN[0].toFixed(5)},${pN[1].toFixed(5)}:${ring.length}`;
          if (seenKeys.has(key)) continue;
          seenKeys.add(key);
          const latlngs = ring.map(pt => [pt[1], pt[0]]);
          L.polyline(latlngs, {
            color: cols.casing,
            weight: caseW,
            lineCap: "round",
            lineJoin: "round",
            opacity: 0.92,
            interactive: false
          }).addTo(localStreetTraffic2DGroup);
          L.polyline(latlngs, {
            color: cols.flow,
            weight: coreW,
            lineCap: "round",
            lineJoin: "round",
            opacity: 0.98,
            interactive: false
          }).addTo(localStreetTraffic2DGroup);
          drawn++;
        }
      }
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
        const isBoundMode = currentConcentrationMode === "boundaries";
        const poly = L.polygon(latlngs, {
          color: col,
          weight: isBoundMode ? 2.8 : 1.5,
          opacity: isBoundMode ? 0.90 : 0.65,
          dashArray: isBoundMode ? null : "5,4",
          fillColor: col,
          fillOpacity: isBoundMode ? 0.24 : 0.08
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
      const z2dNow = map ? map.getZoom() : 14;
      const z2dScale = z2dNow >= 17 ? 2.65 : (z2dNow >= 16 ? 2.10 : (z2dNow >= 14.5 ? 1.55 : (z2dNow >= 13 ? 1.22 : 1.0)));

      // 2a. Zoomed-in 2D Local Street Grid Traffic Layer (beneath primary corridors)
      render2DZoomedStreetTraffic();

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
        const isFwy2D = r.road_type.includes("Freeway") || r.road_type.includes("Express");
        const tCol = congestionColor(congLvl);
        const cCol = congestionCasingColor(congLvl);

        // Base chromatic casing line (scales cleanly with zoom so zoomed-in corridors stay bold and crisp)
        const baseLine = L.polyline(latlngs, {
          color: cCol,
          weight: (isFwy2D ? 5.4 : 4.0) * z2dScale,
          lineCap: "round",
          lineJoin: "round",
          opacity: 0.95
        });
        baseLine.on("click", () => showRoadInspector(r.road_id));
        baseLine.addTo(layerGroups.roads);

        // Vivid Google-Maps-style traffic color overlay line
        const speedTxt = obs ? `${obs.average_speed_kmh} km/h (${obs.travel_time_min_per_10km} min/10km | V/C=${obs.vc_ratio})` : "Data Unavailable";
        const matchNote = exactMatch
          ? `[Primary Dataset #17 Record: ${obs.observation_id}] Source: ${obs.source_id}`
          : `[Diurnal BPR Profile for ${currentTimeWindow}] Source: ${r.source_id}`;
        const trafLine = L.polyline(latlngs, {
          color: tCol,
          weight: (isFwy2D ? 3.8 : 2.8) * z2dScale,
          lineCap: "round",
          lineJoin: "round",
          opacity: 1.0
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

        // Project Marker (Layer 1 — Scaled by Investment Tier, plus 2D Heatmap Halo when in Heatmap Mode)
        const st = projectScaleStyle(p);
        if (currentConcentrationMode === "heatmap") {
          L.circle([lat, lon], {
            radius: st.radius >= 10 ? 2800 : 1900,
            stroke: false,
            fillColor: st.radius >= 10 ? "#ef4444" : "#f59e0b",
            fillOpacity: 0.24,
            interactive: false
          }).addTo(layerGroups.projects);
        } else if (st.radius >= 10) {
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
      const sd = !p ? DATA.subdevs.find(x => x.subdev_id === selected3DProjectId) : null;
      if ((p || sd) && map3d && !map3dContextLost) {
        const [lat, lon] = p ? parseCoord(p.coordinates) : [sd.latitude, sd.longitude];
        const bSpec = getProject3DSpec(p || sd);
        const optCam = getOptimalProject3DCamera(lat, lon, bSpec, Boolean(sd));
        map3d.flyTo({
          center: [optCam.lon, optCam.lat],
          zoom: active3DBlock === "ALL" ? optCam.zoom : Math.min(17.0, optCam.zoom + 0.35),
          pitch: optCam.pitch,
          bearing: active3DBlock === "ALL" ? optCam.bearing : (optCam.bearing - 10),
          duration: 900
        });
      }
      sync3DMapLayers();
      showProjectInspector(selected3DProjectId, false);
    }

    // Computes height-aware camera framing so even 557m–725m supertalls render 100% complete from ground plinth to crown spire inside the viewport
    function getOptimalProject3DCamera(lat, lon, spec, isSubdev) {
      const isMob = window.innerWidth <= 768;
      const hM = (spec && spec.heightM) ? spec.heightM : 140;
      const isBusBayDowntownView = (lat >= 25.175 && lat <= 25.195 && lon >= 55.255 && lon <= 55.278);
      const bearing = isSubdev ? 52 : (isBusBayDowntownView ? 36 : 52);
      const bRad = (bearing * Math.PI) / 180;
      if (hM >= 450) {
        const shiftDeg = 0.0024;
        return {
          lat: lat + Math.cos(bRad) * shiftDeg,
          lon: lon + Math.sin(bRad) * shiftDeg,
          zoom: isMob ? 15.05 : 15.42,
          pitch: 54,
          bearing
        };
      }
      if (hM >= 250) {
        const shiftDeg = 0.0012;
        return {
          lat: lat + Math.cos(bRad) * shiftDeg,
          lon: lon + Math.sin(bRad) * shiftDeg,
          zoom: isMob ? 15.45 : 15.85,
          pitch: 56,
          bearing
        };
      }
      return {
        lat: lat + 0.00018,
        lon: lon + 0.00024,
        zoom: isMob ? 15.85 : (isSubdev ? 16.28 : 16.52),
        pitch: 57,
        bearing
      };
    }

    // =========================================================================
    // SECTION C3: HAIO.SG 3D BLOCK EXPLORER + 5-SECTION STRUCTURED PROJECT PROFILE
    // =========================================================================
    function showProjectInspector(pid, fly = true) {
      selected3DProjectId = pid;
      switchDrawerTab("insp");
      const rawProj = DATA.projects.find(x => x.project_id === pid);
      const rawSubdev = !rawProj ? DATA.subdevs.find(x => x.subdev_id === pid) : null;
      if (!rawProj && !rawSubdev) return;

      const isSubdev = Boolean(rawSubdev);
      currentInspState = isSubdev ? { type: "subdev", obj: rawSubdev } : { type: "project", id: pid };

      // Normalize entity record so both 32 PRJ-* Flagships and 5 SUB-JVC-* Clusters render the complete 5-Section Profile
      const p = rawProj || {
        project_id: rawSubdev.subdev_id,
        project_name: rawSubdev.development_name,
        emirate: rawSubdev.emirate,
        city_district_community: rawSubdev.community_district,
        developer: rawSubdev.developer,
        project_category: "JVC Multi-Tower Residential Sub-Cluster (DLD Active Registry)",
        lifecycle_status: rawSubdev.construction_status,
        timeline_milestones: `Task 1 Cross-Ref: ${rawSubdev.linked_task1_ref} · Active 2025–2026 Superstructure & Handover Window`,
        coordinates: `${rawSubdev.latitude.toFixed(4)}, ${rawSubdev.longitude.toFixed(4)}`,
        land_plot_area: "",
        published_investment_value: "",
        estimated_hard_cost_and_rate: "",
        gross_floor_area: `${rawSubdev.active_gfa_sqm.toLocaleString()} m² Active Structural GFA (${rawSubdev.building_count} Active Towers)`,
        floors_and_height: rawSubdev.floors_range,
        apartments_and_villas_count: `${rawSubdev.total_units.toLocaleString()} residential units`,
        towers_and_buildings_count: `${rawSubdev.building_count} active towers`,
        main_contractor_and_consultants: "",
        confidence_classification: rawSubdev.confidence || "Estimated",
        source_id: rawSubdev.source_id || "SRC-020",
        publisher: "Dubai Land Department (dld_projects-open) & RTA Corridor Releases",
        publication_date: "2025–2026",
        source_url: "https://www.dubaipulse.gov.ae/data/dld-registration/dld_projects-open"
      };

      const link = DATA.impact_links.find(x => x.project_id === pid);
      const docs = DATA.documents.filter(d => d.project_id === pid);
      const summaryRow = (DATA.uae_projects_summary || []).find(x => x.project_id === pid);
      const [lat, lon] = isSubdev ? [rawSubdev.latitude, rawSubdev.longitude] : parseCoord(p.coordinates);
      const spec = getProject3DSpec(rawProj || rawSubdev);
      const isCivicInfra = spec.typology === "civic_infra_campus";

      sync3DMapLayers();
      if (fly) {
        const optCam = getOptimalProject3DCamera(lat, lon, spec, isSubdev);
        flyBothMaps(optCam.lat, optCam.lon, optCam.zoom, optCam.pitch, optCam.bearing);
        document.getElementById("hudScope").textContent = `${p.project_id}: ${p.project_name.split('(')[0].trim()}`;
      }

      const primRoadId = link ? link.primary_road_id : (rawSubdev ? rawSubdev.primary_access_road_id : null);
      const primRoadObs = primRoadId ? getRoadObsForWindow(primRoadId, currentTimeWindow) : null;
      const cleanTitle = p.project_name.split("(")[0].trim();
      const u4br = Math.max(16, Math.round(spec.homes * 0.50));
      const u5br = Math.max(16, spec.homes - u4br);

      const isEstGdv = isSubdev
        ? false
        : (summaryRow ? summaryRow.is_estimated_gdv : (p.published_investment_value || "").toLowerCase().includes("est."));
      const valBadge = isSubdev
        ? `<span class="badge-missing" title="Multi-Parcel Sub-Cluster — Tracked by GFA & Units">NO STANDALONE GDV</span>`
        : (isEstGdv
          ? `<span class="badge-missing" title="Masterplan GDV Estimate with Partial Contract Awards">ESTIMATED MASTERPLAN GDV</span>`
          : `<span class="ep-pill-pub" title="Officially Published Value">PUBLISHED VALUE</span>`);
      const confVal = p.confidence_classification || p.confidence || "Verified";
      const projType = p.project_category || p.project_type || "Mixed-Use Development";
      const timelineTxt = p.timeline_milestones || p.status_evidence_and_history || '<span class="badge-missing">Unavailable / Not Published</span>';
      const plotAreaTxt = p.land_plot_area || p.site_area || (isSubdev ? '<span class="badge-missing">Unavailable — Multi-Parcel JVC District Cluster</span>' : '<span class="badge-missing">Plot Area Unavailable</span>');
      const investLabel = isSubdev ? "Standalone Cluster GDV" : (isEstGdv ? "Est. Masterplan GDV" : "Published Investment");
      const investValHtml = isSubdev
        ? `<span class="badge-missing">Unavailable (No Standalone GDV)</span>`
        : ((p.published_investment_value || "").split("[")[0].trim() || '<span class="badge-missing">Unavailable</span>');
      const hardCostTxt = isSubdev
        ? `<span class="badge-missing">Tracked via JVC Master-Community GFA</span>`
        : ((p.estimated_hard_cost_and_rate || "").split("[")[0].trim() || (summaryRow && summaryRow.hard_construction_cost_aed_b ? `AED ${summaryRow.hard_construction_cost_aed_b}B` : '<span class="badge-missing">Unavailable</span>'));
      const contractorHtml = p.main_contractor_and_consultants
        ? p.main_contractor_and_consultants
        : (isSubdev
          ? `<span class="badge-missing">Plot-Level Contractor Filings Aggregated Across ${rawSubdev.building_count} DLD Escrow Plots</span> (Developer: <strong>${rawSubdev.developer}</strong>)`
          : '<span class="badge-missing">Unavailable / Restricted</span>');
      const secRoadObj = link && link.secondary_road_id ? DATA.roads.find(r => r.road_id === link.secondary_road_id) : null;
      const secRoadLabel = secRoadObj ? `${secRoadObj.road_name.split('(')[0].trim()} (${secRoadObj.road_id})` : (link && link.secondary_road_id ? link.secondary_road_id : '<span class="badge-missing">None</span>');

      const docsHtml = docs.map(d =>
        `<div style="margin-bottom:4px;">• <a href="${d.source_url || d.document_url || d.secondary_portal_url}" target="_blank" rel="noopener">${d.document_title} ↗</a> <span style="color:#64748b;">(${d.document_type} | ${d.availability_status})</span></div>`
      ).join("") || `<span class="badge-missing">No Standalone Plot-Level Document Linked — Verified via DLD Open Registry (${p.source_id || 'SRC-020'})</span>`;

      const projOptionsHtml =
        `<optgroup label="Flagship Developments — Dubai &amp; Sharjah (${DATA.projects.length})">` +
        DATA.projects.map(pr => `<option value="${pr.project_id}" ${pr.project_id === pid ? 'selected' : ''}>${pr.project_id}: ${pr.project_name.split('(')[0].trim()} (${pr.emirate} · ${pr.city_district_community.split('/')[0].trim()})</option>`).join("") +
        `</optgroup>` +
        `<optgroup label="JVC Multi-Tower Sub-Clusters (${DATA.subdevs.length})">` +
        DATA.subdevs.map(sd => `<option value="${sd.subdev_id}" ${sd.subdev_id === pid ? 'selected' : ''}>${sd.subdev_id}: ${sd.development_name.split('(')[0].trim()} (${sd.building_count} Towers · ${sd.total_units.toLocaleString()} Units)</option>`).join("") +
        `</optgroup>`;

      const subHeaderSummary = isCivicInfra
        ? `${p.apartments_and_villas_count || 'Civil / Civic Infrastructure Asset'} · ${spec.blocksCount} campus zones · ${p.project_id}`
        : `${spec.homes.toLocaleString()} homes · ${spec.stacksPerBlock * spec.blocksCount} stacks · ${spec.blocksCount} blocks · ${p.project_id}`;

      const unitControlsHtml = isCivicInfra ? `
          <div class="kv-row" style="margin-bottom:8px; background:#fffbeb; border-color:#fde68a;">
            <div class="kv-lbl"><span class="badge-missing">Residential Unit Mix Not Applicable — ${projType}</span></div>
            <div class="kv-val">Published Functional Capacity / Program: <strong>${p.apartments_and_villas_count || 'Civic Infrastructure Network'}</strong></div>
          </div>
      ` : `
          <!-- SHOW ME PILLS -->
          <label class="haio-field-lbl">SHOW ME</label>
          <div class="haio-showme-row">
            <button class="haio-showme-pill ${active3DShowMe === 'all' ? 'active' : ''}" onclick="update3DBlockControls(undefined, undefined, undefined, 'all')">All homes</button>
            <button class="haio-showme-pill ${active3DShowMe === '4br' ? 'active' : ''}" onclick="update3DBlockControls(undefined, undefined, undefined, '4br')">4 bedrooms</button>
            <button class="haio-showme-pill ${active3DShowMe === '5br' ? 'active' : ''}" onclick="update3DBlockControls(undefined, undefined, undefined, '5br')">5 bedrooms</button>
          </div>

          <!-- UNIT TYPES · HOMES SUMMARY BAR -->
          <div class="haio-unit-bar" style="margin-bottom:8px;">
            <span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:9px;height:9px;border-radius:50%;background:#fbbf24;display:inline-block;"></span> 4BR</span>
            <strong>${u4br}</strong>
            <span style="display:inline-flex; align-items:center; gap:6px; margin-left:8px;"><span style="width:9px;height:9px;border-radius:50%;background:#34d399;display:inline-block;"></span> 5BR</span>
            <strong>${u5br}</strong>
          </div>
      `;

      document.getElementById("inspectorContainer").innerHTML = `
        <div style="padding:2px 2px 10px;">
          <!-- Compact Project & Sub-Cluster Switcher at Top -->
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px; margin-bottom:10px;">
            <select id="projectExplorerSelect" class="haio-select" style="padding:6px 10px; font-size:0.75rem; background:#f8fafc; border-color:#e2e8f0;" onchange="showProjectInspector(this.value, true)" aria-label="Select Active Construction Project">
              ${projOptionsHtml}
            </select>
            <button class="mobile-back-map-btn" onclick="document.getElementById('mapStage').scrollIntoView({behavior:'smooth',block:'center'})">🗺️ ↑ Map</button>
          </div>

          <!-- HAIO.SG EXACT CLEAN HEADER & SUBTITLE -->
          <h3 class="haio-card-title">${cleanTitle}</h3>
          <div class="haio-card-sub">${subHeaderSummary}</div>

          <!-- 01. PROJECT INFORMATION -->
          <div class="prof-sec-hdr"><span>01. Project Information</span><span class="conf-pill ${confVal === 'Verified' ? 'b-ver' : 'b-est'}">${confVal}</span></div>
          <div class="kv-grid" style="margin-bottom:10px;">
            <div class="kv-row">
              <div class="kv-lbl">Entity ID · Developer · Type</div>
              <div class="kv-val"><strong>${p.project_id}</strong> · <strong style="color:#059669;">${p.developer}</strong><br/>Category: <strong>${projType}</strong></div>
            </div>
            <div class="kv-row">
              <div class="kv-lbl">Lifecycle Status &amp; Construction Timeline</div>
              <div class="kv-val"><strong>${p.lifecycle_status}</strong><br/>${timelineTxt}</div>
            </div>
          </div>

          <!-- 02. GEOGRAPHIC CONTEXT -->
          <div class="prof-sec-hdr"><span>02. Geographic Context</span><span>WGS84 Verified</span></div>
          <div class="kv-grid" style="margin-bottom:10px;">
            <div class="kv-row">
              <div class="kv-lbl">Emirate · Community · Coordinates &amp; Plot Area</div>
              <div class="kv-val"><strong>${p.emirate}</strong> · ${p.city_district_community}<br/>Coordinates: <code>${p.coordinates}</code><br/>Plot/Site Area: <strong>${plotAreaTxt}</strong></div>
            </div>
            <div class="kv-row">
              <div class="kv-lbl">Connected Road Corridors &amp; Nearest Intersections</div>
              <div class="kv-val">
                ${link ? `Primary: <a href="javascript:void(0)" onclick="showRoadInspector('${link.primary_road_id}')"><strong>${link.primary_road_name} (${link.primary_road_id})</strong></a> — <strong>${link.distance_to_primary_road_km} km</strong> Haversine to vertex <code>[${link.nearest_road_vertex_wgs84}]</code><br/>Secondary Corridor: <a href="javascript:void(0)" onclick="showRoadInspector('${link.secondary_road_id}')">${secRoadLabel}</a><br/>Nearest Junction: <strong>${link.nearest_intersection_name} (${link.nearest_intersection_id})</strong> — ${link.distance_to_intersection_km} km` : '<span class="badge-missing">No Spatial Link</span>'}
              </div>
            </div>
          </div>

          <!-- 03. CONSTRUCTION ACTIVITY, INVESTMENT & 3D MASSING -->
          <div class="prof-sec-hdr"><span>03. Construction Activity &amp; 3D Massing</span>${valBadge}</div>
          <div class="exec-metric-grid" style="margin-top:6px;">
            <div class="exec-metric-box">
              <div class="em-lbl">${investLabel}</div>
              <div class="em-val" style="color:${isEstGdv || isSubdev ? '#b45309' : '#2563eb'}; font-size:${isSubdev ? '0.74rem' : '0.92rem'};">${investValHtml}</div>
              <div class="em-sub">Hard Cost: ${hardCostTxt}</div>
            </div>
            <div class="exec-metric-box">
              <div class="em-lbl">Gross Floor Area (GFA)</div>
              <div class="em-val" style="font-size:0.78rem; color:#0f172a;">${(p.gross_floor_area || '').split('[')[0].trim()}</div>
              <div class="em-sub">${p.floors_and_height ? p.floors_and_height.split(';')[0].slice(0, 42) : `${spec.storeys} storeys`}</div>
            </div>
          </div>

          <!-- BLOCK SELECTOR -->
          <label class="haio-field-lbl">3D MASSING BLOCK SELECTOR (STOREY-PROPORTIONAL PROCEDURAL MASSING)</label>
          <select class="haio-select" style="margin-bottom:10px;" onchange="update3DBlockControls(this.value, undefined, undefined, undefined)" aria-label="Select 3D Building Block">
            <option value="ALL" ${active3DBlock === 'ALL' ? 'selected' : ''}>All blocks (${spec.blocksCount})</option>
            ${spec.blocks.map(b => `<option value="${b.id}" ${active3DBlock === b.id ? 'selected' : ''}>${b.label} (${b.storeys} storeys)</option>`).join("")}
          </select>

          <!-- FLOOR & STACK 2-COLUMN SELECTORS (100% UNLOCKED) -->
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px;">
            <div>
              <label class="haio-field-lbl">FLOOR</label>
              <select class="haio-select" onchange="update3DBlockControls(undefined, this.value, undefined, undefined)" aria-label="Select Floor Zone">
                <option value="ALL" ${active3DFloor === 'ALL' ? 'selected' : ''}>Select a block / All</option>
                <option value="LOW" ${active3DFloor === 'LOW' ? 'selected' : ''}>Low-Rise (F01–F${Math.round(spec.storeys*0.35)})</option>
                <option value="MID" ${active3DFloor === 'MID' ? 'selected' : ''}>Mid-Rise (F${Math.round(spec.storeys*0.35)+1}–F${Math.round(spec.storeys*0.72)})</option>
                <option value="HIGH" ${active3DFloor === 'HIGH' ? 'selected' : ''}>Upper Levels (F${Math.round(spec.storeys*0.72)+1}–F${spec.storeys})</option>
              </select>
            </div>
            <div>
              <label class="haio-field-lbl">STACK / ZONE</label>
              <select class="haio-select" onchange="update3DBlockControls(undefined, undefined, this.value, undefined)" aria-label="Select Stack">
                <option value="ALL" ${active3DStack === 'ALL' ? 'selected' : ''}>Select floor first / All</option>
                <option value="S1" ${active3DStack === 'S1' ? 'selected' : ''}>Zone 01 (North Wing)</option>
                <option value="S2" ${active3DStack === 'S2' ? 'selected' : ''}>Zone 02 (South Wing)</option>
              </select>
            </div>
          </div>

          ${unitControlsHtml}

          <!-- ILLUSTRATIVE FLOORPLATE / INFRASTRUCTURE NOTICE -->
          ${buildArchitecturalBlueprintSvg(p, spec)}

          <!-- OR PICK A BLOCK -->
          <div class="haio-block-grid">
            ${spec.blocks.map(b => `
            <div class="haio-block-card ${active3DBlock === b.id ? 'active' : ''}" onclick="select3DBlockCard('${b.id}')">
              <strong>${b.label}</strong>
              <span>${b.stacksLabel}<br/>${b.storeys} storeys</span>
            </div>`).join("")}
          </div>

          ${spec.arch ? `
          <details class="tech-accordion" style="margin:8px 0 10px;">
            <summary>🏛️ Supporting Plot &amp; Massing Reference (${spec.arch.arch_id} — Task 2 Scope: Construction Geography, Traffic &amp; Logistics)</summary>
            <div class="tech-body" style="font-size:0.71rem; line-height:1.45;">
              <div style="margin-bottom:4px;"><strong>1. Masterplan &amp; Site Layout:</strong> ${spec.arch.cat1_masterplan_and_site_layout}</div>
              <div style="margin-bottom:4px;"><strong>2. Plot Layout &amp; DM Boundaries:</strong> ${spec.arch.cat2_plot_layout_and_boundaries}</div>
              <div style="margin-bottom:4px;"><strong>3. Tower &amp; Building Floor Plans:</strong> ${spec.arch.cat3_tower_and_building_floor_plans}</div>
              <div style="margin-bottom:4px;"><strong>4. Typical Floor Plates &amp; Cores:</strong> ${spec.arch.cat4_typical_floor_plans_and_plates}</div>
              <div style="margin-bottom:4px;"><strong>5. Elevations, Curtain-Wall &amp; Structural System:</strong> ${spec.arch.cat5_elevations_and_building_sections}</div>
              <div style="margin-bottom:4px;"><strong>6. Apartment Mix &amp; Area Schedule:</strong> ${spec.arch.cat6_apartment_config_and_area_schedule}</div>
              <div style="margin-bottom:4px;"><strong>7. Landscape, Pools &amp; MEP Utilities:</strong> ${spec.arch.cat7_landscape_and_infrastructure_plan}</div>
              <div style="margin-bottom:4px;"><strong>8. Parking Layouts &amp; Ratios:</strong> ${spec.arch.cat8_parking_layouts_and_allocation}</div>
              <div><strong>9. Concrete/Rebar Grade &amp; Brochure Status:</strong> ${spec.arch.cat9_published_specs_and_brochure_status}</div>
            </div>
          </details>` : ""}

          <!-- 04. TRAFFIC RELATIONSHIP & LOGISTICS -->
          <div class="prof-sec-hdr"><span>04. Traffic Relationship &amp; HGV Load</span><span class="ep-pill-mod">MODELLED + PUBLISHED</span></div>
          ${primRoadObs && link ? `
          <div class="live-window-banner" style="margin-top:6px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:4px;">
              <strong style="color:#2563eb;">⏱️ ${currentTimeWindow.split('(')[0].trim()} Speed</strong>
              <span style="color:${congestionColor(primRoadObs.congestion_level)}; font-weight:800;">~${primRoadObs.average_speed_kmh} km/h (${primRoadObs.travel_time_min_per_10km} min/10km)</span>
            </div>
            <div style="margin-top:4px; color:#334155; font-size:0.74rem;">
              Access Road: <a href="javascript:void(0)" onclick="showRoadInspector('${link.primary_road_id}')"><strong>${link.primary_road_name} (${link.primary_road_id})</strong></a> · <strong>${link.distance_to_primary_road_km} km</strong> Haversine<br/>
              Status: <strong>${primRoadObs.congestion_level.split('(')[0].trim()} Congestion</strong> · V/C = ${primRoadObs.vc_ratio} (${primRoadObs.modelled_demand_vph_dir}/${primRoadObs.reference_capacity_vph_dir} vph/dir)<br/>
              Epistemic Impact Tier: <strong style="color:#1d4ed8;">${link.epistemic_impact_classification}</strong>
            </div>
          </div>` : ""}

          <div class="kv-grid" style="margin-bottom:10px;">
            <div class="kv-row">
              <div class="kv-lbl">Scenario Daily HGV Logistics Load (4-Component Breakdown)</div>
              <div class="kv-val">
                ${link ? `<strong>${link.total_hgv_round_trips_day} round-trips/day (${link.total_hgv_one_way_movements_day} one-way movements/day)</strong><br/>• Ready-Mix Concrete (8.5 m³): <strong>${link.concrete_mixer_loads_day}/d</strong> | Steel Rebar (25 t): <strong>${link.rebar_trailer_loads_day}/d</strong> | Earthworks (18 m³): <strong>${link.earthworks_tipper_loads_day}/d</strong> | MEP/Fit-Out (12 t): <strong>${link.mep_fitout_truck_loads_day}/d</strong><br/><span style="color:#059669; font-weight:700;">HGV Window Rule:</span> ${link.hgv_routing_and_ban_compliance}` : '<span class="badge-missing">Unavailable</span>'}
              </div>
            </div>
            <div class="kv-row">
              <div class="kv-lbl">Plot-Level Consultant Traffic Impact Study (TIS) Filing</div>
              <div class="kv-val">
                <span class="badge-missing">Plot-Level Consultant TIS Restricted in RTA TES Portal</span><br/>
                <span style="font-size:0.72rem; color:#334155;">Substantiated at corridor level via <strong>${link ? link.published_road_capacity_and_upgrade_fact : 'RTA/SRTA Corridor Release'}</strong>.</span>
              </div>
            </div>
          </div>

          <!-- 05. EVIDENCE & SOURCES -->
          <div class="prof-sec-hdr"><span>05. Evidence, Documents (${docs.length}) &amp; Provenance</span><span>${confVal}</span></div>
          <div class="kv-grid">
            <div class="kv-row">
              <div class="kv-lbl">Contractors &amp; Engineering Consultants</div>
              <div class="kv-val">${contractorHtml}</div>
            </div>
            <div class="kv-row">
              <div class="kv-lbl">Official Documents &amp; Regulatory Filings (${docs.length})</div>
              <div class="kv-val">${docsHtml}</div>
            </div>
            <div class="kv-row">
              <div class="kv-lbl">Primary Source Citation &amp; Verification Notes</div>
              <div class="kv-val">
                <a href="${p.source_url}" target="_blank" rel="noopener"><strong>${p.source_id || 'SRC'}: ${p.publisher} (${p.publication_date}) ↗</strong></a>
                ${link ? `<br/><a href="${link.corridor_source_url}" target="_blank" rel="noopener">${link.corridor_traffic_source_id || link.source_id}: ${link.corridor_source_title} ↗</a>` : ""}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function showSubdevInspector(sd, fly = true) {
      const subId = typeof sd === "string" ? sd : (sd && sd.subdev_id ? sd.subdev_id : "SUB-JVC-01");
      showProjectInspector(subId, fly);
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
            
... [truncated for diff preview]