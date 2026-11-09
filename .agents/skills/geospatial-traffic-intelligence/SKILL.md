---
name: geospatial-traffic-intelligence
description: "Geospatial construction-to-traffic impact intelligence, WGS84/GeoJSON road network modeling, 4-tier epistemic impact classification, and map-linked deterministic Q&A."
---

# Geospatial Traffic & Construction Impact Intelligence (`geospatial-traffic-intelligence`)

## 1. Coordinate Reference Systems & Spatial Distance Mathematics
- **Storage & Web Visualization (WGS84 / EPSG:4326)**: Store and serve all GeoJSON features (`Point`, `LineString`, `Polygon`) in standard `[longitude, latitude]` WGS84 coordinates for direct compatibility with MapLibre GL JS / Leaflet and OGC APIs.
- **Metric Spatial Computation (UTM Zone 40N / EPSG:32640)**: Never compute Euclidean buffer distances or geometric areas in raw degrees. Project coordinates to **EPSG:32640 (WGS 84 / UTM zone 40N)** or apply geodesic Haversine/Vincenty formulas before computing:
  - Buffer radii ($100\text{ m}$, $250\text{ m}$, $500\text{ m}$, $1000\text{ m}$) around construction sites and roadworks.
  - Access-point snap distances from project boundaries to the nearest road segment node/edge.
  - Corridor chainage lengths and polygon areas ($\text{m}^2$).

## 2. Road Network Capacity & Traffic Flow Separation
Maintain strict separation between official published figures and engineering capacity estimates:
1. **Published RTA / Official Figures (`PUBLISHED_OFFICIAL`)**:
   - Explicitly cited lane counts, posted speed limits ($v_{\text{free}}$), and official corridor capacity or AADT figures from RTA / municipality documentation.
2. **HCM 7th Edition Engineering Estimates (`HCM_ESTIMATED`)**:
   - When official directional capacity is unpublished, compute baseline capacity using Highway Capacity Manual (HCM 7th Ed.) urban street / multilane highway equations:
     $$C_{\text{dir}} = N_{\text{lanes}} \times C_{\text{base}}(v_{\text{free}}, \text{road\_class}) \times f_{\text{HV}} \times f_{\text{zone}}$$
   - Store `capacity_basis: "HCM_7TH_EDITION_ESTIMATE"` alongside `heavy_vehicle_factor` ($f_{\text{HV}}$) and `active_workzone_capacity_reduction` ($\Delta C_{\text{wz}}$) so users and downstream models never conflate modeled capacity with statutory RTA baselines.

## 3. 4-Tier Epistemic Impact Classification
Every construction-to-traffic relationship and congestion anomaly must be classified into one of four mutually exclusive epistemic tiers:

| Tier | Code | Definition & Qualification Criteria | Allowed Phrasing |
| :--- | :--- | :--- | :--- |
| **Tier 1** | `OBSERVED_CONGESTION` | Direct telemetry observation (e.g., TomTom Flow / Incident API, live speed vs. free-flow speed ratio $v / v_{\text{free}} < 0.65$, or verified delay) on a road segment without asserting a construction cause. | *"Observed congestion / speed reduction of X% on Segment Y during window T."* |
| **Tier 2** | `SPATIAL_ASSOCIATION` | An active construction project or permit lies within a defined geodesic buffer ($\le 500\text{ m}$ or primary access road) of an impacted segment, with temporal overlap, but without an explicit lane-closure permit or deterministic trip-generation proof. | *"Spatially associated with Project Z (distance D m; overlapping active phase)."* |
| **Tier 3** | `MODELLED_CONSTRUCTION_IMPACT` | Quantitative engineering estimate of construction-induced load (e.g., concrete/excavation HGV trip generation, work-zone lane narrowing factor, or detoured V/C delta) derived from project phase, GFA, or work-zone geometry. | *"Modelled construction impact contributing an estimated +X PCE/hr (ΔV/C = +Y)."* |
| **Tier 4** | `CONFIRMED_CAUSAL_IMPACT` | Verified causal link backed by an official RTA/municipality roadworks permit, verified lane closure / diversion notice, or direct telemetry incident tag (`RoadWorks` / `LaneClosure`) tied to the specific construction activity. | *"Confirmed causal impact from active roadworks / closure [Permit/Incident ID]."* |

> **Epistemic Guardrail**: Never promote a `SPATIAL_ASSOCIATION` (Tier 2) or `MODELLED_CONSTRUCTION_IMPACT` (Tier 3) to `CONFIRMED_CAUSAL_IMPACT` (Tier 4) without a verifiable closure/incident record or official notice.

## 4. MapLibre / Leaflet 11-Layer GeoJSON Architecture
Structure the geospatial frontend and GeoJSON data catalog into 11 toggleable, schema-validated layers:
1. `L01_study_zones`: Macro study boundaries and community districts (`Polygon`).
2. `L02_road_network_base`: Primary/secondary road segments with lane counts, free-flow speeds, and HCM/RTA capacity attributes (`LineString`).
3. `L03_traffic_flow_live`: Real-time / time-sliced speed, congestion ratio, and travel-time index overlays (`LineString`).
4. `L04_traffic_incidents`: Point and linear traffic incidents, delays, and TomTom/RTA jam tail vectors (`Point` / `LineString`).
5. `L05_roadworks_closures`: Active lane closures, diversions, and right-of-way work zones (`LineString` / `Polygon`).
6. `L06_construction_footprints`: Building & infrastructure project parcels/footprints colored by project stage (`Polygon`).
7. `L07_construction_nodes`: Project centroids and metadata markers for high-speed clustering (`Point`).
8. `L08_site_access_gates`: Heavy-vehicle ingress/egress gates and curb-cut connection points (`Point`).
9. `L09_haul_routes_buffers`: Designated HGV haul corridors and $250\text{ m}$ / $500\text{ m}$ spatial impact buffers (`LineString` / `Polygon`).
10. `L10_impact_links`: Directed spatial-association and modelled-impact vectors connecting `project_id` to `segment_id` with epistemic tier styling (`LineString`).
11. `L11_bottleneck_hotspots`: Ranked multi-project cumulative stress zones and intersection pinch points (`Point` / `Polygon`).

## 5. Deterministic SQL/JSON Q&A Execution with Map Auto-Zoom
All natural-language or structured analytical queries in the dashboard must execute against the underlying SQLite/DuckDB/JSON relational store deterministically—never via ungrounded free-text hallucination:
- **Deterministic Query Execution**: Translate user intents into parameterized SQL/JSON filter pipelines over `projects`, `road_segments`, `traffic_observations`, and `project_segment_impacts`.
- **Structured Response Contract**: Every Q&A response payload must return:
  - `answer_markdown`: Fact-checked synthesis citing exact IDs, metric values, and epistemic tiers (`Tier 1`–`Tier 4`).
  - `evidence_rows`: Array of matching database records (`project_id`, `segment_id`, metrics, `epistemic_tier`, `source_provenance`).
  - `map_camera_action`: Deterministic viewport command (`bbox: [minLon, minLat, maxLon, maxLat]`, `center: [lon, lat]`, `zoom`, `pitch`, `highlight_feature_ids`, and `active_layers` to toggle on) so the map immediately auto-zooms and highlights the exact spatial entities referenced in the answer.
