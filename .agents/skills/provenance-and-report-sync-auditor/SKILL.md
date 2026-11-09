---
name: provenance-and-report-sync-auditor
description: "Enforces primary-source sub-metric and publication-date verification, 100% programmatic CSV-to-Markdown report generation, and explicit epistemic labelling of modelled delay assumptions"
---

# Provenance, Source-Date & Report-to-CSV Sync Auditor Skill

## Core Mandate
Eliminate multi-round audit corrections by enforcing **Zero-Drift Programmatic Generation** and **Primary-Source Field-by-Field Verification** across all datasets, provenance registers, interactive UIs, and Markdown/PDF reports.

## 4 Non-Negotiable Verification Gates

### Gate 1 — Primary-Source Sub-Metric & Publication-Date Verification
- Never verify only headline metrics (e.g., annual average speed) while leaving secondary sub-metrics (e.g., morning/evening rush-hour travel-time seconds or congestion percentages) or metadata (`publication_date`) approximate.
- For every external benchmark row (such as TomTom Traffic Index `OBS-DXB-CITY-00`) and every provenance record (`11_provenance_source_register`):
  - Verify exact travel-time seconds (`18 min 41 sec`, `26 min 33 sec`) and exact congestion percentages (`42.3%`, `94.4%`).
  - Verify that `publication_date` in both `11_provenance_source_register` and `17_traffic_congestion_observations` matches the linked official release date (`SRC-439` = `2022-12-25`, `SRC-452` = `2025-05-04`, `SRC-440` = `2025-05-25`, `SRC-451` = `2024-12-19`, `SRC-438` = `2025-07-13`, `SRC-434` = `2024-09-01`, `SRC-433` = `2025-11-18`).

### Gate 2 — Zero Manual Report Tables (100% Programmatic CSV-to-Report Generation)
- **Never hand-type or partially edit a data table in a Markdown report or UI template.**
- Every Markdown report (`task2_gis_and_traffic_intelligence_report.md`) and UI summary must be **programmatically generated directly from the committed CSV/JSON files** (`17_traffic_congestion_observations.csv`, `22_project_road_impact_links.csv`, `11_provenance_source_register.csv`), and an automated verifier must parse the Markdown table rows back out and assert 100% cell-for-cell equality against the CSV.

### Gate 3 — Epistemic Labelling of Modelled Delay Terms
- When a transport model combines a formula-derived link term ($t_{\text{BPR}} = t_0[1 + 0.15(V/C)^4]$) with an additive intersection/queue/weaving delay term ($+d_{\text{adj}}$), always label $+d_{\text{adj}}$ as a **Modelled, HCM-Informed Bottleneck-Delay Assumption (Not Independently Validated Signal/Queue Telemetry)**.
- In verification receipts, report both:
  - **Stored-precision discrepancy** (comparing rounded stored columns: `0.00 min/10km`, `0.0 km/h`), and
  - **Unrounded floating-point discrepancy** (recomputing from rounded CSV inputs before final rounding: e.g., `max_time_diff = 0.0053 min/10km`, `max_speed_diff = 0.049 km/h`).
