// ============================================================================
// UNREAL-STYLE THREE.JS r170 PBR ARCHVIZ WALKTHROUGH & RIGHT-SIDE-UP CAD ENGINE
// Powers PRJ-D2 (Palm Jebel Ali) & PRJ-D19 (Tilal Al Ghaf) Street & Villa Tours
// ============================================================================
(function () {
  "use strict";

  window.wtState = {
    active: false,
    projectId: null,
    mode: "zones", // "zones" | "street" | "villa"
    selectedZoneId: null,
    stopIndex: 0,
    domMarkers: [],
    leafletGroup: null,
    roverMesh: null
  };

  const avz = {
    open: false,
    sceneKind: "villa", // "street" | "villa"
    typologyId: "TYP-TAG-SERENITY-6BR",
    floorKey: "G", // "B" | "G" | "F1" | "F2"
    camStyle: "fpv", // "fpv" | "cutaway" | "dollhouse"
    exploded: false,
    cadStyle: "brochure", // "brochure" | "cad"
    fullscreen3D: false,
    timeOfDay: "golden", // "golden" | "noon" | "dusk" | "night"
    selectedRoomId: null,

    // Singleton WebGLRenderer & cached PBR assets (zero WebGL context churn)
    renderer: null,
    scene: null,
    camera: null,
    pmremGen: null,
    envRT: null,
    mats: null,
    skyMesh: null,
    sunLight: null,
    hemiLight: null,
    waterUniforms: null,
    swayCrowns: [],
    interiorLights: [],
    streetPortalPos: null,

    // First-person & Orbit camera state
    camPos: { x: 0, y: 1.7, z: 12 },
    camTargetPos: null,
    yaw: 0, // 0 = looking North (-Z, toward Lagoon/Sea!)
    pitch: -0.04,
    orbitYaw: -0.55,
    orbitPitch: 0.58,
    orbitDist: 38,
    orbitTarget: { x: 0, y: 1.2, z: 0 },

    keys: {},
    dragging: false,
    lastMX: 0,
    lastMY: 0,
    rafId: null,
    lastFrameTs: 0,
    autoWalkActive: false,
    autoWalkT: 0,
    autoWaypoints: []
  };
  window.avzState = avz;

  // ---------------- HELPERS ----------------
  function hasSocietyWalkthrough(pid) {
    return Boolean(DATA.walkthroughs && DATA.walkthroughs.projects && DATA.walkthroughs.projects[pid]);
  }
  window.hasSocietyWalkthrough = hasSocietyWalkthrough;

  function getSocietyData(pid) {
    return (DATA.walkthroughs && DATA.walkthroughs.projects) ? DATA.walkthroughs.projects[pid] : null;
  }
  window.getSocietyData = getSocietyData;

  function cleanSqftStr(s) {
    return String(s || "").replace(/\s*sq\.?ft\.?/ig, "").trim();
  }

  function latLonRingToGeoJson(ringLatLon) {
    if (!Array.isArray(ringLatLon) || ringLatLon.length < 3) return [];
    const coords = ringLatLon.map(pt => [pt[1], pt[0]]);
    const f = coords[0], l = coords[coords.length - 1];
    if (f[0] !== l[0] || f[1] !== l[1]) coords.push([f[0], f[1]]);
    return coords;
  }

  function detectZoneForLatLon(soc, lat, lon) {
    if (!soc || !Array.isArray(soc.zones)) return null;
    for (const z of soc.zones) {
      if (!z.polygon || z.polygon.length < 3) continue;
      let inside = false;
      for (let i = 0, j = z.polygon.length - 1; i < z.polygon.length; j = i++) {
        const yi = z.polygon[i][0], xi = z.polygon[i][1];
        const yj = z.polygon[j][0], xj = z.polygon[j][1];
        const inter = ((yi > lat) !== (yj > lat)) && (lon < ((xj - xi) * (lat - yi)) / ((yj - yi) || 1e-12) + xi);
        if (inter) inside = !inside;
      }
      if (inside) return z;
    }
    let best = soc.zones[0] || null, bestD = Infinity;
    for (const z of soc.zones) {
      if (!z.center) continue;
      const d = Math.hypot(lat - z.center[0], lon - z.center[1]);
      if (d < bestD) { bestD = d; best = z; }
    }
    return best;
  }

  // =========================================================================
  // LAYER 1: GIS MASTERPLAN & CONTRACTOR DIGITAL TWIN ON MAPLIBRE 3D / LEAFLET
  // =========================================================================
  function clearSocietyDomAndLeafletOverlays() {
    if (wtState.domMarkers && wtState.domMarkers.length) {
      wtState.domMarkers.forEach(m => { try { m.remove(); } catch (_) {} });
      wtState.domMarkers = [];
    }
    if (wtState.leafletGroup && typeof map !== "undefined" && map) {
      try { map.removeLayer(wtState.leafletGroup); } catch (_) {}
      wtState.leafletGroup = null;
    }
    const emptyFC = { type: "FeatureCollection", features: [] };
    if (typeof map3d !== "undefined" && map3d && map3dLoaded) {
      ["wt-water-src", "wt-islands-src", "wt-zones-src", "wt-streets-src", "wt-route-src"].forEach(sid => {
        const s = map3d.getSource(sid);
        if (s) s.setData(emptyFC);
      });
    }
  }

  function ensureSocietyMap3dLayers() {
    if (!map3d || !map3dLoaded) return;
    const emptyFC = { type: "FeatureCollection", features: [] };
    ["wt-water-src", "wt-islands-src", "wt-zones-src", "wt-streets-src", "wt-route-src"].forEach(id => {
      if (!map3d.getSource(id)) map3d.addSource(id, { type: "geojson", data: emptyFC });
    });
    const beforeLayer = map3d.getLayer("haio-photoreal-3d-layer") ? "haio-photoreal-3d-layer" : undefined;

    if (!map3d.getLayer("wt-water-fill")) {
      map3d.addLayer({ id: "wt-water-fill", type: "fill", source: "wt-water-src", paint: { "fill-color": "#06b6d4", "fill-opacity": 0.56 } }, beforeLayer);
      map3d.addLayer({ id: "wt-water-line", type: "line", source: "wt-water-src", paint: { "line-color": "#67e8f9", "line-width": 2.0, "line-opacity": 0.9 } }, beforeLayer);
    }
    if (!map3d.getLayer("wt-islands-fill")) {
      map3d.addLayer({ id: "wt-islands-fill", type: "fill", source: "wt-islands-src", paint: { "fill-color": "#fde68a", "fill-opacity": 0.20 } }, beforeLayer);
      map3d.addLayer({ id: "wt-islands-line", type: "line", source: "wt-islands-src", paint: { "line-color": "#fbbf24", "line-width": 1.4, "line-opacity": 0.75 } }, beforeLayer);
    }
    if (!map3d.getLayer("wt-zones-fill")) {
      map3d.addLayer({
        id: "wt-zones-fill", type: "fill", source: "wt-zones-src",
        paint: { "fill-color": ["get", "color"], "fill-opacity": ["case", ["==", ["get", "selected"], 1], 0.36, 0.19] }
      }, beforeLayer);
      map3d.addLayer({
        id: "wt-zones-line", type: "line", source: "wt-zones-src",
        paint: {
          "line-color": ["case", ["==", ["get", "selected"], 1], "#ffffff", ["get", "color"]],
          "line-width": ["case", ["==", ["get", "selected"], 1], 3.5, 2.0],
          "line-opacity": 0.95
        }
      }, beforeLayer);
      map3d.on("click", "wt-zones-fill", (ev) => {
        if (!wtState.active || !ev.features || !ev.features.length) return;
        const zid = ev.features[0].properties.zone_id;
        if (zid) selectSocietyZone(zid, true);
      });
    }
    if (!map3d.getLayer("wt-streets-line")) {
      map3d.addLayer({
        id: "wt-streets-casing", type: "line", source: "wt-streets-src",
        paint: { "line-color": "#0f172a", "line-width": ["interpolate", ["linear"], ["zoom"], 13, 2.0, 17, 7.5], "line-opacity": 0.65 }
      }, beforeLayer);
      map3d.addLayer({
        id: "wt-streets-line", type: "line", source: "wt-streets-src",
        paint: {
          "line-color": ["match", ["get", "hw"], "primary", "#fbbf24", "secondary", "#fde047", "tertiary", "#f8fafc", "footway", "#34d399", "cycleway", "#34d399", "#e2e8f0"],
          "line-width": ["interpolate", ["linear"], ["zoom"], 13, 1.1, 17, 4.4],
          "line-opacity": 0.92
        }
      }, beforeLayer);
    }
    if (!map3d.getLayer("wt-route-line")) {
      map3d.addLayer({ id: "wt-route-casing", type: "line", source: "wt-route-src", paint: { "line-color": "#022c22", "line-width": 6, "line-opacity": 0.85 } });
      map3d.addLayer({ id: "wt-route-line", type: "line", source: "wt-route-src", paint: { "line-color": "#10b981", "line-width": 3.5, "line-dasharray": [2, 1.4], "line-opacity": 0.98 } });
    }
  }

  function populateSocietyOverlays(soc) {
    clearSocietyDomAndLeafletOverlays();
    if (!soc) return;
    ensureSocietyMap3dLayers();

    const waterFeats = [];
    (soc.water_polygons || []).forEach(ring => {
      const c = latLonRingToGeoJson(ring);
      if (c.length >= 4) waterFeats.push({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [c] } });
    });
    (soc.pools_parks || []).forEach(pp => {
      if (pp.kind === "water" && pp.pts && pp.pts.length >= 3) {
        const c = latLonRingToGeoJson(pp.pts);
        if (c.length >= 4) waterFeats.push({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [c] } });
      }
    });
    const islandFeats = (soc.island_polygons || []).map(ring => ({
      type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [latLonRingToGeoJson(ring)] }
    })).filter(f => f.geometry.coordinates[0].length >= 4);

    const zoneFeats = (soc.zones || []).map(z => ({
      type: "Feature",
      properties: { zone_id: z.zone_id, name: z.name, color: z.color || "#10b981", selected: z.zone_id === wtState.selectedZoneId ? 1 : 0 },
      geometry: { type: "Polygon", coordinates: [latLonRingToGeoJson(z.polygon)] }
    }));

    const streetFeats = [];
    (soc.osm_streets || []).forEach(st => {
      if (st.pts && st.pts.length >= 2) {
        streetFeats.push({ type: "Feature", properties: { hw: st.hw || "residential" }, geometry: { type: "LineString", coordinates: st.pts.map(p => [p[1], p[0]]) } });
      }
    });
    (soc.fronds || []).forEach(fr => {
      if (fr.pts && fr.pts.length >= 2) {
        streetFeats.push({ type: "Feature", properties: { hw: "secondary" }, geometry: { type: "LineString", coordinates: fr.pts.map(p => [p[1], p[0]]) } });
      }
    });
    const routeCoords = (soc.street_tour || []).map(s => [s.lon, s.lat]);
    const routeFeats = routeCoords.length >= 2 ? [{ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: routeCoords } }] : [];

    if (map3d && map3dLoaded) {
      map3d.getSource("wt-water-src")?.setData({ type: "FeatureCollection", features: waterFeats });
      map3d.getSource("wt-islands-src")?.setData({ type: "FeatureCollection", features: islandFeats });
      map3d.getSource("wt-zones-src")?.setData({ type: "FeatureCollection", features: zoneFeats });
      map3d.getSource("wt-streets-src")?.setData({ type: "FeatureCollection", features: streetFeats });
      map3d.getSource("wt-route-src")?.setData({ type: "FeatureCollection", features: routeFeats });

      (soc.zones || []).forEach(z => {
        if (!z.center) return;
        const el = document.createElement("div");
        el.className = "wt-zone-map-pill";
        el.style.borderColor = z.color || "#38bdf8";
        if (z.zone_id === wtState.selectedZoneId) {
          el.style.background = z.color || "#0284c7";
          el.style.color = "#ffffff";
        }
        const shortContr = (z.main_contractor || "").split("(")[0].split("&")[0].trim().slice(0, 22);
        el.innerHTML = `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:${z.color};margin-right:5px;"></span>${z.short_label} · <span style="color:#6ee7b7;">${shortContr}</span>`;
        el.onclick = (ev) => { ev.stopPropagation(); selectSocietyZone(z.zone_id, true); };
        wtState.domMarkers.push(new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([z.center[1], z.center[0]]).addTo(map3d));
      });

      (soc.fronds || []).forEach(fr => {
        if (!fr.pts || !fr.pts.length) return;
        const tip = fr.pts[fr.pts.length - 1];
        const zMatch = (soc.zones || []).find(z => z.zone_id === fr.zone_id);
        const el = document.createElement("div");
        el.className = "wt-zone-map-pill frond-tag";
        el.style.borderColor = zMatch ? zMatch.color : "#38bdf8";
        el.title = `${fr.frond} · ${fr.contractor}`;
        el.textContent = `Frond ${fr.letter}`;
        el.onclick = (ev) => {
          ev.stopPropagation();
          selectSocietyZone(fr.zone_id, false);
          wtFlyMapCamera(tip[0], tip[1], 16.2, 60, -25, 850);
        };
        wtState.domMarkers.push(new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([tip[1], tip[0]]).addTo(map3d));
      });
    }

    if (typeof map !== "undefined" && map && typeof L !== "undefined") {
      const lg = L.layerGroup();
      (soc.water_polygons || []).forEach(ring => L.polygon(ring, { color: "#06b6d4", fillColor: "#06b6d4", fillOpacity: 0.5, weight: 1.5 }).addTo(lg));
      (soc.zones || []).forEach(z => {
        if (!z.polygon) return;
        const poly = L.polygon(z.polygon, { color: z.color || "#10b981", fillColor: z.color || "#10b981", fillOpacity: 0.22, weight: 2 });
        poly.on("click", () => selectSocietyZone(z.zone_id, true));
        poly.addTo(lg);
      });
      lg.addTo(map);
      wtState.leafletGroup = lg;
    }
  }

  function syncThreeSocietyWalkGroup() {
    if (typeof three3DLayer === "undefined" || !three3DLayer || !three3DLayer.scene || typeof THREE === "undefined") return;
    if (three3DLayer.societyWalkGroup) {
      disposeThreeGroup(three3DLayer.societyWalkGroup, true);
      three3DLayer.scene.remove(three3DLayer.societyWalkGroup);
      three3DLayer.societyWalkGroup = null;
    }
    if (!wtState.active || !wtState.projectId) {
      if (three3DLayer.heroGroup) three3DLayer.heroGroup.visible = true;
      three3DLayer.heroExcludeRadiusM = 56.0;
      return;
    }
    const soc = getSocietyData(wtState.projectId);
    if (!soc) return;
    if (three3DLayer.heroGroup) three3DLayer.heroGroup.visible = false;
    three3DLayer.heroExcludeRadiusM = 2.0;

    const [originLon, originLat] = three3DLayer.originLonLat || [soc.center[1], soc.center[0]];
    const zoneColorMap = {};
    (soc.zones || []).forEach(z => { zoneColorMap[z.zone_id] = new THREE.Color(z.color || "#e2e8f0"); });

    const wallPos = [], wallNorm = [], wallCol = [];
    const glassPos = [], glassNorm = [], glassCol = [];
    const poolPos = [], poolNorm = [];

    const pushQuad = (pa, na, ca, x0, y0, z0, x1, y1, z1, nx, ny, nz, r, g, b) => {
      pa.push(x0, y0, z0, x1, y1, z0, x1, y1, z1, x0, y0, z0, x1, y1, z1, x0, y0, z1);
      for (let k = 0; k < 6; k++) { na.push(nx, ny, nz); if (ca) ca.push(r, g, b); }
    };
    const pushHRect = (pa, na, ca, cx, cy, z, w, d, cA, sA, r, g, b) => {
      const hw = w * 0.5, hd = d * 0.5;
      const pts = [[-hw, -hd], [hw, -hd], [hw, hd], [-hw, hd]].map(([lx, ly]) => [cx + lx * cA - ly * sA, cy + lx * sA + ly * cA]);
      pa.push(pts[0][0], pts[0][1], z, pts[1][0], pts[1][1], z, pts[2][0], pts[2][1], z, pts[0][0], pts[0][1], z, pts[2][0], pts[2][1], z, pts[3][0], pts[3][1], z);
      for (let k = 0; k < 6; k++) { na.push(0, 0, 1); if (ca) ca.push(r, g, b); }
    };
    const pushOBox = (pa, na, ca, cx, cy, z0, z1, w, d, cA, sA, r, g, b) => {
      const hw = w * 0.5, hd = d * 0.5;
      const pts = [[-hw, -hd], [hw, -hd], [hw, hd], [-hw, hd]].map(([lx, ly]) => [cx + lx * cA - ly * sA, cy + lx * sA + ly * cA]);
      for (let i = 0; i < 4; i++) {
        const [x0, y0] = pts[i], [x1, y1] = pts[(i + 1) % 4];
        const dx = x1 - x0, dy = y1 - y0, len = Math.hypot(dx, dy) || 1;
        pushQuad(pa, na, ca, x0, y0, z0, x1, y1, z1, dy / len, -dx / len, 0, r * 0.93, g * 0.93, b * 0.93);
      }
      pushHRect(pa, na, ca, cx, cy, z1, w, d, cA, sA, r, g, b);
    };

    (soc.osm_buildings || []).forEach((ring, idx) => {
      if (!ring || ring.length < 4) return;
      const ptsEnu = ring.map(([lat, lon]) => lonLatToOriginEnu(lon, lat, originLon, originLat));
      const h = 7.8 + (idx % 4) * 1.1;
      const sh = 0.89 + (idx % 5) * 0.02;
      const r = 0.96 * sh, g = 0.93 * sh, b = 0.87 * sh;
      for (let i = 0; i < ptsEnu.length - 1; i++) {
        const [x0, y0] = ptsEnu[i], [x1, y1] = ptsEnu[i + 1];
        const dx = x1 - x0, dy = y1 - y0, len = Math.hypot(dx, dy);
        if (len < 0.4) continue;
        pushQuad(wallPos, wallNorm, wallCol, x0, y0, 0, x1, y1, h, dy / len, -dx / len, 0, r, g, b);
      }
      const [rx0, ry0] = ptsEnu[0];
      for (let i = 1; i < ptsEnu.length - 2; i++) {
        const [rx1, ry1] = ptsEnu[i], [rx2, ry2] = ptsEnu[i + 1];
        wallPos.push(rx0, ry0, h, rx1, ry1, h, rx2, ry2, h);
        for (let k = 0; k < 3; k++) { wallNorm.push(0, 0, 1); wallCol.push(r, g, b); }
      }
    });

    (soc.procedural_villas || []).forEach((v, idx) => {
      const [cx, cy] = lonLatToOriginEnu(v.lon, v.lat, originLon, originLat);
      const w = v.w || 16, d = v.d || 14, h = v.h || 9.5;
      const ang = ((idx * 37) % 360) * (Math.PI / 180) * 0.08;
      const cA = Math.cos(ang), sA = Math.sin(ang);
      const zc = zoneColorMap[v.zone] || new THREE.Color("#f8fafc");
      const wr = 0.86 + zc.r * 0.12, wg = 0.83 + zc.g * 0.12, wb = 0.78 + zc.b * 0.12;
      const hG = Math.min(4.2, h * 0.44), hF1 = h * 0.84;
      pushOBox(wallPos, wallNorm, wallCol, cx, cy, 0, hG, w, d, cA, sA, wr, wg, wb);
      pushOBox(glassPos, glassNorm, glassCol, cx, cy, hG, hF1, w * 0.88, d * 0.82, cA, sA, 0.38, 0.68, 0.86);
      pushOBox(wallPos, wallNorm, wallCol, cx + 0.5, cy - 0.4, hF1, h, w * 0.62, d * 0.58, cA, sA, wr * 0.92, wg * 0.90, wb * 0.85);
      if (v.pool) pushHRect(poolPos, poolNorm, null, cx - sA * (d * 0.66), cy + cA * (d * 0.66), 0.28, w * 0.68, d * 0.34, cA, sA, 0, 0, 0);
    });

    const group = new THREE.Group();
    if (wallPos.length) {
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.Float32BufferAttribute(wallPos, 3));
      g.setAttribute("normal", new THREE.Float32BufferAttribute(wallNorm, 3));
      g.setAttribute("color", new THREE.Float32BufferAttribute(wallCol, 3));
      const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.6, metalness: 0.08, side: THREE.DoubleSide }));
      m.frustumCulled = false;
      group.add(m);
    }
    if (glassPos.length) {
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.Float32BufferAttribute(glassPos, 3));
      g.setAttribute("normal", new THREE.Float32BufferAttribute(glassNorm, 3));
      g.setAttribute("color", new THREE.Float32BufferAttribute(glassCol, 3));
      const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.18, metalness: 0.55, transparent: true, opacity: 0.84, side: THREE.DoubleSide }));
      m.frustumCulled = false;
      group.add(m);
    }
    if (poolPos.length) {
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.Float32BufferAttribute(poolPos, 3));
      g.setAttribute("normal", new THREE.Float32BufferAttribute(poolNorm, 3));
      const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: 0x06b6d4, side: THREE.DoubleSide }));
      m.frustumCulled = false;
      group.add(m);
    }
    three3DLayer.societyWalkGroup = group;
    three3DLayer.scene.add(group);
    if (map3d) map3d.triggerRepaint();
  }
  window.syncThreeSocietyWalkGroup = syncThreeSocietyWalkGroup;

  function wtFlyMapCamera(lat, lon, zoom, pitch, bearing, durationMs = 900) {
    if (map3d && map3dLoaded && currentCameraDim === "3D") {
      map3d.easeTo({ center: [lon, lat], zoom: Math.min(18.2, Math.max(11.0, zoom)), pitch: Math.min(72, Math.max(0, pitch)), bearing: bearing || 0, duration: durationMs, essential: true });
    }
    if (typeof map !== "undefined" && map) {
      map.setView([lat, lon], Math.min(18, Math.max(11, Math.round(zoom))), { animate: false });
    }
  }

  function enterSocietyWalkthrough(pid, initialMode = "zones") {
    const soc = getSocietyData(pid);
    if (!soc) { showProjectInspector(pid, true); return; }
    closeAnalyticalWorkspace();
    if (currentCameraDim === "2D" && !map3dContextLost) setCameraDimension("3D");

    wtState.active = true;
    wtState.projectId = pid;
    wtState.selectedZoneId = soc.zones && soc.zones[0] ? soc.zones[0].zone_id : null;
    wtState.stopIndex = 0;

    selected3DProjectId = pid;
    document.body.classList.add("wt-society-active");
    document.getElementById("wtTopBanner").style.display = "flex";
    document.getElementById("wtSwitchD2").classList.toggle("active", pid === "PRJ-D2");
    document.getElementById("wtSwitchD19").classList.toggle("active", pid === "PRJ-D19");

    const bldgCount = (soc.osm_buildings ? soc.osm_buildings.length : 0) + (soc.procedural_villas ? soc.procedural_villas.length : 0);
    document.getElementById("wtTopStatsChip").textContent = `${soc.zones.length} Contractor Zones · ${(soc.osm_streets || []).length} Streets · ${bldgCount.toLocaleString()} 3D Villas`;
    document.getElementById("hudScope").textContent = `Walkthrough: ${soc.name}`;

    switchDrawerTab("insp");
    rebuildThreeHeroScene();
    sync3DMapLayers();
    populateSocietyOverlays(soc);
    renderSocietyInspectorPanel(soc);

    if (initialMode === "street") {
      openUnrealStreetWalk(0);
    } else if (initialMode === "villa") {
      openCurrentSocietyVillaModal();
    } else {
      closeArchvizStudioModal(false);
      wtState.mode = "zones";
      updateTopModeButtons("zones");
      wtFlyMapCamera(soc.center[0], soc.center[1], soc.entry_zoom || 14.3, soc.entry_pitch || 56, soc.entry_bearing || -20, 950);
    }
  }
  window.enterSocietyWalkthrough = enterSocietyWalkthrough;

  function exitSocietyWalkthrough(flyOverview = true) {
    closeArchvizStudioModal(false);
    const prevPid = wtState.projectId || "PRJ-D11";
    wtState.active = false;
    wtState.projectId = null;
    document.body.classList.remove("wt-society-active");
    const tb = document.getElementById("wtTopBanner");
    if (tb) tb.style.display = "none";
    clearSocietyDomAndLeafletOverlays();
    syncThreeSocietyWalkGroup();
    sync3DMapLayers();
    if (flyOverview) {
      flyBothMaps(25.095, 55.165, 11.2, 50, 20);
      showProjectInspector(prevPid, false);
    }
  }
  window.exitSocietyWalkthrough = exitSocietyWalkthrough;

  function updateTopModeButtons(m) {
    document.getElementById("wtModeZonesBtn")?.classList.toggle("active", m === "zones");
    document.getElementById("wtModeStreetBtn")?.classList.toggle("active", m === "street");
    document.getElementById("wtModeInsideBtn")?.classList.toggle("active", m === "villa");
  }

  function setSocietyWalkMode(mode) {
    if (!wtState.active) return;
    if (mode === "street") {
      openUnrealStreetWalk(wtState.stopIndex || 0);
    } else if (mode === "villa") {
      openCurrentSocietyVillaModal();
    } else {
      closeArchvizStudioModal(false);
      wtState.mode = "zones";
      updateTopModeButtons("zones");
      const soc = getSocietyData(wtState.projectId);
      if (soc) wtFlyMapCamera(soc.center[0], soc.center[1], soc.entry_zoom || 14.3, soc.entry_pitch || 56, soc.entry_bearing || -20, 850);
    }
  }
  window.setSocietyWalkMode = setSocietyWalkMode;

  function selectSocietyZone(zoneId, flyToZone = true) {
    const soc = getSocietyData(wtState.projectId);
    if (!soc) return;
    const z = (soc.zones || []).find(x => x.zone_id === zoneId);
    if (!z) return;
    wtState.selectedZoneId = zoneId;
    populateSocietyOverlays(soc);
    renderSocietyInspectorPanel(soc);
    if (flyToZone && z.center) wtFlyMapCamera(z.center[0], z.center[1], z.zoom || 15.8, z.pitch || 60, z.bearing || -20, 850);
  }
  window.selectSocietyZone = selectSocietyZone;

  function renderSocietyInspectorPanel(soc) {
    const container = document.getElementById("inspectorContainer");
    if (!container || !soc) return;
    const selZ = (soc.zones || []).find(z => z.zone_id === wtState.selectedZoneId) || soc.zones[0];
    const typologiesForProj = Object.values(DATA.walkthroughs.typologies || {}).filter(t => t.project_id === soc.project_id);

    const zoneCardsHtml = (soc.zones || []).map(z => {
      const isAct = selZ && z.zone_id === selZ.zone_id;
      return `
        <div class="wt-zone-card ${isAct ? 'active' : ''}" style="border-left-color:${z.color};" onclick="selectSocietyZone('${z.zone_id}', true)">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
            <strong style="font-size:0.78rem; color:#0f172a;">${z.name}</strong>
            <span style="background:${z.color}22; color:#0f172a; border:1px solid ${z.color}; font-size:0.65rem; font-weight:800; padding:1px 7px; border-radius:999px; white-space:nowrap;">${z.units_count}</span>
          </div>
          <div style="font-size:0.72rem; color:#047857; font-weight:700; margin-top:3px;">🏗️ ${z.main_contractor}</div>
          <div style="font-size:0.69rem; color:#475569; margin-top:2px;">💰 ${z.contract_value} · 📐 BUA ${cleanSqftStr(z.bua_range_sqft)} sq.ft.</div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px; gap:6px;">
            <button type="button" onclick="event.stopPropagation(); selectSocietyZone('${z.zone_id}', false); openUnrealStreetWalkForZone('${z.zone_id}')" style="background:#059669; color:#fff; border:none; border-radius:6px; padding:3px 8px; font-size:0.67rem; font-weight:700; cursor:pointer;">🚶 3D Street Walk</button>
            <button type="button" onclick="event.stopPropagation(); openVillaInteriorModal('${z.default_typology_id}')" style="background:#0f172a; color:#fff; border:none; border-radius:6px; padding:3px 8px; font-size:0.67rem; font-weight:700; cursor:pointer;">🏠 3D Villa &amp; CAD →</button>
          </div>
        </div>
      `;
    }).join("");

    const frondTableHtml = (soc.fronds && soc.fronds.length) ? `
      <div class="prof-sec-hdr" style="margin-top:10px;"><span>🌴 All 16 Fronds (A–P) Contractor Directory</span><span>Click to Enter</span></div>
      <div style="display:grid; grid-template-columns:repeat(2,1fr); gap:5px; margin-bottom:10px;">
        ${soc.fronds.map(fr => `
          <button type="button" onclick="selectSocietyZone('${fr.zone_id}', false); wtFlyCameraFrond(${fr.pts[1][0]}, ${fr.pts[1][1]});" style="text-align:left; background:#f8fafc; border:1px solid #cbd5e1; border-radius:7px; padding:5px 7px; cursor:pointer; font-size:0.68rem;">
            <strong style="color:#0f172a;">${fr.frond}</strong><br/>
            <span style="color:#047857; font-weight:700;">${fr.contractor.split('(')[0].trim()}</span>
          </button>
        `).join("")}
      </div>
    ` : "";

    container.innerHTML = `
      <div style="padding:2px 2px 14px;">
        <div style="background:linear-gradient(135deg,#0f172a 0%,#064e3b 100%); color:#fff; border-radius:12px; padding:12px; margin-bottom:10px; border:1px solid #10b981;">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px; margin-bottom:4px;">
            <span style="background:#10b981; color:#022c22; font-size:0.65rem; font-weight:900; padding:2px 8px; border-radius:999px;">UNREAL 3D ARCHVIZ DIGITAL TWIN</span>
            <button type="button" onclick="showProjectInspector('${soc.project_id}', false)" style="background:rgba(255,255,255,0.14); color:#e2e8f0; border:1px solid rgba(255,255,255,0.28); border-radius:999px; padding:2px 8px; font-size:0.66rem; font-weight:700; cursor:pointer;">📋 5-Sec GIS Profile</button>
          </div>
          <h3 style="margin:4px 0 2px; font-size:1.02rem; color:#fff;">${soc.name} (${soc.project_id})</h3>
          <div style="font-size:0.73rem; color:#a7f3d0; font-weight:600;">${soc.developer} · ${soc.area_summary}</div>
          <div style="font-size:0.71rem; color:#cbd5e1; margin-top:4px;">GDV / Awards: <strong>${soc.headline_gdv}</strong></div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:9px;">
            <button type="button" onclick="openUnrealStreetWalk(0)" style="background:#10b981; color:#022c22; border:none; border-radius:8px; padding:8px; font-size:0.73rem; font-weight:900; cursor:pointer;">🚶 Unreal 3D Street Walk</button>
            <button type="button" onclick="openVillaInteriorModal('${selZ ? selZ.default_typology_id : typologiesForProj[0].id}')" style="background:#38bdf8; color:#082f49; border:none; border-radius:8px; padding:8px; font-size:0.73rem; font-weight:900; cursor:pointer;">🏠 Inside 3D Villa + CAD</button>
          </div>
        </div>

        ${selZ ? `
          <div class="prof-sec-hdr"><span>📍 Selected Enclave Contractor Dossier</span><span style="color:#059669; font-weight:800;">${selZ.zone_id}</span></div>
          <div class="kv-grid" style="margin-bottom:10px; background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px; padding:9px;">
            <div style="font-size:0.86rem; font-weight:800; color:#0f172a; margin-bottom:4px;">${selZ.name}</div>
            <div style="font-size:0.73rem; line-height:1.45; color:#1e293b;">
              • <strong>Main Building Contractor:</strong> <span style="color:#047857; font-weight:800;">${selZ.main_contractor}</span><br/>
              • <strong>Contract Value / Package:</strong> <strong>${selZ.contract_value}</strong><br/>
              • <strong>Infrastructure / Marine Contractor:</strong> ${selZ.infrastructure_contractor}<br/>
              • <strong>Lead Architects:</strong> ${selZ.architects}<br/>
              • <strong>Interior Designer:</strong> ${selZ.interior_designer}<br/>
              • <strong>Engineering Consultants (AOR):</strong> ${selZ.consultants}<br/>
              • <strong>Units &amp; Typologies:</strong> ${selZ.units_count} (${selZ.unit_types})<br/>
              • <strong>BUA / Plot / Levels:</strong> BUA ${cleanSqftStr(selZ.bua_range_sqft)} sq.ft. · Plot ${cleanSqftStr(selZ.plot_range_sqft)} sq.ft. · ${selZ.floors_spec}<br/>
              • <strong>Key Highlights:</strong> ${Array.isArray(selZ.highlights) ? selZ.highlights.join(" · ") : selZ.highlights}<br/>
              • <strong>Source Basis:</strong> <span style="color:#64748b;">${selZ.source_note}</span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:8px;">
              <button type="button" onclick="openUnrealStreetWalkForZone('${selZ.zone_id}')" style="background:#059669; color:#fff; border:none; border-radius:8px; padding:8px; font-size:0.73rem; font-weight:800; cursor:pointer;">🚶 Walk ${selZ.short_label} Street</button>
              <button type="button" onclick="openVillaInteriorModal('${selZ.default_typology_id}')" style="background:linear-gradient(135deg,#2563eb,#7c3aed); color:#fff; border:none; border-radius:8px; padding:8px; font-size:0.73rem; font-weight:800; cursor:pointer;">🏠 Step Inside Villa 3D →</button>
            </div>
          </div>
        ` : ""}

        <div class="prof-sec-hdr"><span>🏗️ All Villa 3D ArchViz &amp; CAD Collections (${typologiesForProj.length})</span><span>PBR 3D</span></div>
        <div style="display:flex; flex-direction:column; gap:5px; margin-bottom:10px;">
          ${typologiesForProj.map(t => `
            <button type="button" onclick="openVillaInteriorModal('${t.id}')" style="display:flex; justify-content:space-between; align-items:center; text-align:left; background:#fff; border:1px solid #cbd5e1; border-radius:8px; padding:7px 9px; cursor:pointer;">
              <div>
                <strong style="font-size:0.74rem; color:#0f172a; display:block;">${t.title}</strong>
                <span style="font-size:0.68rem; color:#475569;">BUA ${t.bua_sqft} · ${t.levels_label} · ${t.contractor.split('(')[0].trim()}</span>
              </div>
              <span style="background:#eff6ff; color:#1d4ed8; font-weight:800; font-size:0.68rem; padding:3px 7px; border-radius:6px;">3D Walk →</span>
            </button>
          `).join("")}
        </div>
        ${frondTableHtml}
        <div class="prof-sec-hdr"><span>🗺️ All ${soc.zones.length} Society Contractor Zones</span><span>Click Card</span></div>
        ${zoneCardsHtml}
      </div>
    `;
  }
  window.wtFlyCameraFrond = (lat, lon) => wtFlyMapCamera(lat, lon, 16.3, 62, -25, 850);

  // =========================================================================
  // REAL-TIME THREE.JS r170 PBR ARCHVIZ ENGINE (STREET WALK + VILLA INTERIOR)
  // =========================================================================
  function makeProceduralTexture(drawFn, repeatX = 4, repeatY = 4) {
    const c = document.createElement("canvas");
    c.width = 512; c.height = 512;
    const ctx = c.getContext("2d");
    drawFn(ctx, 512, 512);
    const tex = new THREE.CanvasTexture(c);
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(repeatX, repeatY);
    tex.colorSpace = THREE.SRGBColorSpace;
    return tex;
  }

  function ensureArchvizRenderer() {
    if (typeof THREE === "undefined") return false;
    const canvas = document.getElementById("archvizWebglCanvas");
    if (!canvas) return false;
    if (!avz.renderer) {
      avz.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
      avz.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
      avz.renderer.outputColorSpace = THREE.SRGBColorSpace;
      avz.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      avz.renderer.toneMappingExposure = 1.12;
      avz.renderer.shadowMap.enabled = true;
      avz.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      avz.pmremGen = new THREE.PMREMGenerator(avz.renderer);
      avz.pmremGen.compileEquirectangularShader();
      avz.camera = new THREE.PerspectiveCamera(65, 1.6, 0.12, 750);
      initArchvizMaterials();
      bindArchvizControlsOnce(canvas);
    }
    return true;
  }

  function initArchvizMaterials() {
    // 1. Calacatta Gold Honed Marble
    const marbleTex = makeProceduralTexture((ctx, w, h) => {
      ctx.fillStyle = "#faf8f4";
      ctx.fillRect(0, 0, w, h);
      for (let i = 0; i < 26; i++) {
        ctx.strokeStyle = i % 3 === 0 ? "rgba(196,154,86,0.20)" : "rgba(148,163,184,0.20)";
        ctx.lineWidth = 1.0 + (i % 3) * 1.2;
        ctx.beginPath();
        let x = (i * 73) % w, y = 0;
        ctx.moveTo(x, y);
        while (y < h) {
          y += 28;
          x += Math.sin(y * 0.025 + i) * 20;
          ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
      ctx.strokeStyle = "rgba(203,213,225,0.40)";
      ctx.lineWidth = 1.2;
      ctx.strokeRect(1, 1, 254, 254); ctx.strokeRect(257, 1, 254, 254);
      ctx.strokeRect(1, 257, 254, 254); ctx.strokeRect(257, 257, 254, 254);
    }, 3, 3);

    // 2. Honed Desert Travertine Limestone
    const travTex = makeProceduralTexture((ctx, w, h) => {
      ctx.fillStyle = "#efe7d6";
      ctx.fillRect(0, 0, w, h);
      for (let y = 0; y < h; y += 3) {
        const v = 228 + Math.round(Math.sin(y * 0.11) * 9 + ((y * 17) % 7));
        ctx.fillStyle = `rgb(${v + 7}, ${v}, ${v - 14})`;
        ctx.fillRect(0, y, w, 2);
      }
      ctx.strokeStyle = "rgba(168,152,128,0.36)";
      ctx.lineWidth = 1.6;
      for (let y = 0; y < h; y += 85) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
      for (let x = 0; x < w; x += 170) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
    }, 4, 4);

    // 3. European Warm Oak Planks
    const oakTex = makeProceduralTexture((ctx, w, h) => {
      ctx.fillStyle = "#b98756";
      ctx.fillRect(0, 0, w, h);
      for (let p = 0; p < 8; p++) {
        const py = p * 64;
        ctx.fillStyle = p % 2 === 0 ? "#c2905e" : "#ad7b4a";
        ctx.fillRect(0, py, w, 62);
        ctx.fillStyle = "rgba(92,54,24,0.14)";
        for (let g = 0; g < 10; g++) ctx.fillRect(0, py + g * 6, w, 1.3);
        ctx.strokeStyle = "rgba(110,71,35,0.45)";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(0, py, w, 64);
      }
    }, 4, 4);

    // 4. Luxury Brushed Asphalt & Paver Boulevard with Crisp Markings
    const asphaltTex = makeProceduralTexture((ctx, w, h) => {
      ctx.fillStyle = "#2b313c";
      ctx.fillRect(0, 0, w, h);
      for (let i = 0; i < 3200; i++) {
        const x = (i * 97) % w, y = (i * 53) % h;
        ctx.fillStyle = i % 2 ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.16)";
        ctx.fillRect(x, y, 2, 2);
      }
      // Subtle tire wear polish tracks
      ctx.fillStyle = "rgba(255,255,255,0.025)";
      ctx.fillRect(110, 0, 75, h);
      ctx.fillRect(325, 0, 75, h);
      // Center dashed line & edge lines
      ctx.fillStyle = "#f8fafc";
      ctx.fillRect(251, 36, 10, 175);
      ctx.fillRect(251, 292, 10, 175);
      ctx.fillStyle = "#f59e0b";
      ctx.fillRect(12, 0, 5, h);
      ctx.fillRect(w - 17, 0, 5, h);
    }, 1, 14);

    // 5. Lush Manicured Resort Lawn
    const lawnTex = makeProceduralTexture((ctx, w, h) => {
      ctx.fillStyle = "#2d6e3c";
      ctx.fillRect(0, 0, w, h);
      for (let y = 0; y < h; y += 32) {
        ctx.fillStyle = (y / 32) % 2 === 0 ? "rgba(74,222,128,0.11)" : "rgba(20,83,45,0.13)";
        ctx.fillRect(0, y, w, 32);
      }
      for (let i = 0; i < 1400; i++) {
        ctx.fillStyle = i % 2 ? "rgba(134,239,172,0.10)" : "rgba(22,101,52,0.14)";
        ctx.fillRect((i * 83) % w, (i * 61) % h, 2, 3);
      }
    }, 6, 6);

    // 6. Pinnate Date Palm Frond Alpha-Cutout Texture (38 Feather Leaflets per Side!)
    const palmLeafCanvas = document.createElement("canvas");
    palmLeafCanvas.width = 256; palmLeafCanvas.height = 512;
    const pctx = palmLeafCanvas.getContext("2d");
    pctx.clearRect(0, 0, 256, 512);
    // Central golden-olive rachis stem
    const stemGrad = pctx.createLinearGradient(0, 512, 0, 0);
    stemGrad.addColorStop(0, "#6d7c3a");
    stemGrad.addColorStop(1, "#3f7a38");
    pctx.fillStyle = stemGrad;
    pctx.beginPath();
    pctx.moveTo(123, 512); pctx.lineTo(133, 512); pctx.lineTo(129, 8); pctx.lineTo(127, 8);
    pctx.closePath();
    pctx.fill();
    // Individual feather leaflets fanning outward
    for (let i = 0; i < 42; i++) {
      const t = i / 41;
      const y = 496 - t * 476;
      const span = Math.sin(Math.pow(t, 0.72) * Math.PI) * 116 + 10;
      const droop = -18 - t * 24;
      [-1, 1].forEach(dir => {
        pctx.fillStyle = (i % 3 === 0) ? "#3b7d44" : (i % 3 === 1 ? "#2d6838" : "#498947");
        pctx.beginPath();
        pctx.moveTo(128, y);
        pctx.quadraticCurveTo(128 + dir * span * 0.55, y + droop * 0.45, 128 + dir * span, y + droop);
        pctx.quadraticCurveTo(128 + dir * span * 0.52, y + droop * 0.45 + 7.5, 128, y + 6.5);
        pctx.closePath();
        pctx.fill();
      });
    }
    const palmFrondTex = new THREE.CanvasTexture(palmLeafCanvas);
    palmFrondTex.colorSpace = THREE.SRGBColorSpace;

    // 7. Woven Silk & Berber Designer Area Rug Texture
    const rugTex = makeProceduralTexture((ctx, w, h) => {
      ctx.fillStyle = "#e7dfd3";
      ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = "#c7bba8";
      ctx.lineWidth = 18;
      ctx.strokeRect(24, 24, w - 48, h - 48);
      ctx.strokeStyle = "#94a3b8";
      ctx.lineWidth = 3;
      ctx.strokeRect(46, 46, w - 92, h - 92);
      for (let i = 0; i < 1800; i++) {
        ctx.fillStyle = i % 2 ? "rgba(255,255,255,0.12)" : "rgba(120,113,108,0.10)";
        ctx.fillRect((i * 71) % w, (i * 43) % h, 3, 2);
      }
    }, 1, 1);

    // 8. Contemporary Gallery Abstract Canvas Artwork Texture
    const artTex = makeProceduralTexture((ctx, w, h) => {
      const g = ctx.createLinearGradient(0, 0, w, h);
      g.addColorStop(0, "#f8fafc"); g.addColorStop(0.5, "#f1e7d6"); g.addColorStop(1, "#e2d5c1");
      ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = "rgba(14,116,144,0.78)";
      ctx.beginPath(); ctx.arc(w * 0.36, h * 0.48, 125, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "rgba(217,119,6,0.72)";
      ctx.fillRect(w * 0.48, h * 0.24, 155, 220);
      ctx.fillStyle = "rgba(15,23,42,0.85)";
      ctx.fillRect(w * 0.22, h * 0.62, 240, 26);
    }, 1, 1);

    // 9. Distant Dubai Marina Glass Curtain-Wall Skyline Texture
    const skylineTex = makeProceduralTexture((ctx, w, h) => {
      ctx.fillStyle = "#1e293b";
      ctx.fillRect(0, 0, w, h);
      for (let r = 0; r < 32; r++) {
        for (let c = 0; c < 12; c++) {
          const lit = ((r * 13 + c * 7) % 5 === 0);
          ctx.fillStyle = lit ? "rgba(253,230,138,0.65)" : "rgba(148,163,184,0.22)";
          ctx.fillRect(8 + c * 42, 8 + r * 16, 28, 10);
        }
      }
    }, 1, 2);

    avz.waterUniforms = {
      uTime: { value: 0 },
      uSunDir: { value: new THREE.Vector3(0.5, 0.4, -0.7).normalize() },
      uDeepCol: { value: new THREE.Color("#0369a1") },
      uShallowCol: { value: new THREE.Color("#06b6d4") },
      uSunCol: { value: new THREE.Color("#fffbeb") }
    };

    // Distance-filtered Gerstner-inspired Water Shader (Zero Distant Moiré!)
    const waterMat = new THREE.ShaderMaterial({
      uniforms: avz.waterUniforms,
      transparent: true,
      side: THREE.DoubleSide,
      vertexShader: `
        uniform float uTime;
        varying vec3 vWorldPos;
        void main() {
          vec3 p = position;
          vec4 wp0 = modelMatrix * vec4(p, 1.0);
          float swell = sin(wp0.x * 0.45 + uTime * 1.4) * 0.022 + cos(wp0.z * 0.52 - uTime * 1.2) * 0.022;
          p.y += swell;
          vec4 wp = modelMatrix * vec4(p, 1.0);
          vWorldPos = wp.xyz;
          gl_Position = projectionMatrix * viewMatrix * wp;
        }
      `,
      fragmentShader: `
        uniform float uTime;
        uniform vec3 uSunDir;
        uniform vec3 uDeepCol;
        uniform vec3 uShallowCol;
        uniform vec3 uSunCol;
        varying vec3 vWorldPos;
        void main() {
          float dist = length(cameraPosition - vWorldPos);
          float detailAtten = 1.0 - smoothstep(14.0, 78.0, dist);
          float wLarge = sin(vWorldPos.x * 0.55 + uTime * 1.3) * cos(vWorldPos.z * 0.48 - uTime * 1.1);
          float wMed   = sin(vWorldPos.x * 2.1 - uTime * 2.0 + vWorldPos.z * 1.7) * detailAtten;
          float wFine  = sin(vWorldPos.x * 4.8 + uTime * 2.7 - vWorldPos.z * 4.1) * detailAtten * 0.5;
          vec3 n = normalize(vec3(wLarge * 0.08 + wMed * 0.09 + wFine * 0.05, 1.0, wLarge * 0.07 - wMed * 0.08));
          vec3 viewDir = normalize(cameraPosition - vWorldPos);
          float fresnel = pow(1.0 - max(dot(viewDir, n), 0.0), 3.0);
          vec3 refl = reflect(-uSunDir, n);
          float spec = pow(max(dot(viewDir, refl), 0.0), 120.0);
          float caustic = smoothstep(0.42, 0.96, abs(wMed + wFine)) * detailAtten;
          float depthMix = clamp(fresnel * 0.72 + smoothstep(8.0, 90.0, dist) * 0.35, 0.0, 1.0);
          vec3 base = mix(uShallowCol, uDeepCol, depthMix);
          base += vec3(0.18, 0.42, 0.46) * caustic * 0.32;
          vec3 col = base + uSunCol * spec * 1.45;
          gl_FragColor = vec4(col, 0.88);
        }
      `
    });

    avz.mats = {
      marble: new THREE.MeshPhysicalMaterial({ map: marbleTex, roughness: 0.14, metalness: 0.02, clearcoat: 0.55, clearcoatRoughness: 0.12 }),
      travertine: new THREE.MeshStandardMaterial({ map: travTex, roughness: 0.50, metalness: 0.03 }),
      plasterWarm: new THREE.MeshStandardMaterial({ color: 0xf8f6f0, roughness: 0.62, metalness: 0.01, emissive: 0xfaf6ee, emissiveIntensity: 0.10 }),
      ceilingWhite: new THREE.MeshStandardMaterial({ color: 0xfdfcf9, roughness: 0.68, metalness: 0.0, emissive: 0xfbf7ee, emissiveIntensity: 0.44 }),
      pocheCap: new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.75 }),
      oak: new THREE.MeshStandardMaterial({ map: oakTex, roughness: 0.36, metalness: 0.04 }),
      rug: new THREE.MeshStandardMaterial({ map: rugTex, roughness: 0.92 }),
      artwork: new THREE.MeshStandardMaterial({ map: artTex, roughness: 0.42 }),
      skyline: new THREE.MeshStandardMaterial({ map: skylineTex, roughness: 0.35, metalness: 0.45 }),
      bronze: new THREE.MeshStandardMaterial({ color: 0x3b2e22, roughness: 0.26, metalness: 0.85 }),
      charcoal: new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.40, metalness: 0.38 }),
      glass: new THREE.MeshPhysicalMaterial({ color: 0xe0f2fe, transparent: true, opacity: 0.22, roughness: 0.04, metalness: 0.10, reflectivity: 0.95, side: THREE.DoubleSide }),
      glassBalustrade: new THREE.MeshPhysicalMaterial({ color: 0xbae6fd, transparent: true, opacity: 0.34, roughness: 0.05, metalness: 0.12, side: THREE.DoubleSide }),
      sheerCurtain: new THREE.MeshStandardMaterial({ color: 0xfaf8f5, transparent: true, opacity: 0.62, roughness: 0.88, side: THREE.DoubleSide }),
      fabricCream: new THREE.MeshStandardMaterial({ color: 0xf3efe6, roughness: 0.84 }),
      fabricNavy: new THREE.MeshStandardMaterial({ color: 0x1e3a8a, roughness: 0.78 }),
      fabricTerracotta: new THREE.MeshStandardMaterial({ color: 0xc25934, roughness: 0.80 }),
      fabricTaupe: new THREE.MeshStandardMaterial({ color: 0xb5aba0, roughness: 0.82 }),
      leatherTan: new THREE.MeshStandardMaterial({ color: 0x9c5d34, roughness: 0.42, metalness: 0.08 }),
      poolTile: new THREE.MeshStandardMaterial({ color: 0x0e7490, roughness: 0.25 }),
      gold: new THREE.MeshStandardMaterial({ color: 0xd9b343, roughness: 0.20, metalness: 0.90 }),
      chrome: new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.14, metalness: 0.92 }),
      ledWarm: new THREE.MeshBasicMaterial({ color: 0xfff1d6 }),
      ledCyan: new THREE.MeshBasicMaterial({ color: 0x38bdf8 }),
      oledScreen: new THREE.MeshBasicMaterial({ color: 0x0369a1 }),
      asphalt: new THREE.MeshStandardMaterial({ map: asphaltTex, roughness: 0.72 }),
      lawn: new THREE.MeshStandardMaterial({ map: lawnTex, roughness: 0.86 }),
      hedge: new THREE.MeshStandardMaterial({ color: 0x22543d, roughness: 0.88 }),
      bougainvillea: new THREE.MeshStandardMaterial({ color: 0xdb2777, roughness: 0.75 }),
      sand: new THREE.MeshStandardMaterial({ color: 0xf4ead5, roughness: 0.90 }),
      palmTrunk: new THREE.MeshStandardMaterial({ color: 0x6e543b, roughness: 0.88 }),
      palmFrond: new THREE.MeshStandardMaterial({ map: palmFrondTex, alphaTest: 0.32, roughness: 0.55, side: THREE.DoubleSide }),
      carPaintBlue: new THREE.MeshPhysicalMaterial({ color: 0x0369a1, roughness: 0.12, metalness: 0.78, clearcoat: 1.0 }),
      carPaintSilver: new THREE.MeshPhysicalMaterial({ color: 0xe2e8f0, roughness: 0.14, metalness: 0.85, clearcoat: 1.0 }),
      carPaintBlack: new THREE.MeshPhysicalMaterial({ color: 0x0f172a, roughness: 0.10, metalness: 0.80, clearcoat: 1.0 }),
      carPaintChampagne: new THREE.MeshPhysicalMaterial({ color: 0xd6c7b2, roughness: 0.14, metalness: 0.76, clearcoat: 1.0 }),
      water: waterMat
    };
  }

  function disposeArchvizScene() {
    if (!avz.scene) return;
    const sharedMats = new Set(Object.values(avz.mats || {}));
    avz.scene.traverse(obj => {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        const arr = Array.isArray(obj.material) ? obj.material : [obj.material];
        arr.forEach(m => { if (m && !sharedMats.has(m)) m.dispose(); });
      }
    });
    avz.scene = null;
    avz.swayCrowns = [];
    avz.interiorLights = [];
  }

  function setupSkyAndLighting(scene) {
    const skyGeo = new THREE.SphereGeometry(520, 36, 24);
    const skyUniforms = {
      uTop: { value: new THREE.Color("#0c4a6e") },
      uMid: { value: new THREE.Color("#38bdf8") },
      uBot: { value: new THREE.Color("#fed7aa") },
      uSunDir: { value: new THREE.Vector3(0.55, 0.34, -0.76).normalize() },
      uSunCol: { value: new THREE.Color("#fff7ed") }
    };
    const skyMat = new THREE.ShaderMaterial({
      uniforms: skyUniforms,
      side: THREE.BackSide,
      depthWrite: false,
      vertexShader: `
        varying vec3 vDir;
        void main() {
          vDir = normalize(position);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 uTop;
        uniform vec3 uMid;
        uniform vec3 uBot;
        uniform vec3 uSunDir;
        uniform vec3 uSunCol;
        varying vec3 vDir;
        void main() {
          vec3 d = normalize(vDir);
          float h = clamp(d.y, -0.15, 1.0);
          vec3 col = h < 0.24
            ? mix(uBot, uMid, clamp((h + 0.15) / 0.39, 0.0, 1.0))
            : mix(uMid, uTop, pow(clamp((h - 0.24) / 0.76, 0.0, 1.0), 0.82));
          // Subtle high-altitude Arabian cirrus clouds
          if (d.y > 0.03) {
            vec2 uv = d.xz / (d.y + 0.22);
            float c1 = sin(uv.x * 2.3 + 1.1) * cos(uv.y * 1.9 - 0.5);
            float c2 = sin(uv.x * 5.1 - uv.y * 3.7) * 0.5;
            float cloud = smoothstep(0.28, 0.92, c1 + c2) * smoothstep(0.03, 0.28, d.y) * 0.18;
            col = mix(col, mix(vec3(1.0), uSunCol, 0.45), cloud);
          }
          float sunAmt = max(dot(d, uSunDir), 0.0);
          col += uSunCol * pow(sunAmt, 36.0) * 0.65 + uSunCol * pow(sunAmt, 480.0) * 2.4;
          gl_FragColor = vec4(col, 1.0);
        }
      `
    });
    avz.skyMesh = new THREE.Mesh(skyGeo, skyMat);
    scene.add(avz.skyMesh);

    avz.hemiLight = new THREE.HemisphereLight(0xe8f4fd, 0xe7dccb, 1.15);
    scene.add(avz.hemiLight);
    scene.add(new THREE.AmbientLight(0xfffaf2, 0.36));

    avz.sunLight = new THREE.DirectionalLight(0xffe4b5, 3.2);
    avz.sunLight.castShadow = true;
    avz.sunLight.shadow.mapSize.set(2048, 2048);
    avz.sunLight.shadow.camera.near = 2;
    avz.sunLight.shadow.camera.far = 240;
    const d = 68;
    avz.sunLight.shadow.camera.left = -d;
    avz.sunLight.shadow.camera.right = d;
    avz.sunLight.shadow.camera.top = d;
    avz.sunLight.shadow.camera.bottom = -d;
    avz.sunLight.shadow.bias = -0.0004;
    scene.add(avz.sunLight);

    applyTimeOfDayPreset(avz.timeOfDay);
  }

  function applyTimeOfDayPreset(preset) {
    avz.timeOfDay = preset;
    document.querySelectorAll(".avz-tod-btn").forEach(b => b.classList.toggle("active", b.dataset.tod === preset));
    if (!avz.scene || !avz.skyMesh || !avz.sunLight) return;

    const u = avz.skyMesh.material.uniforms;
    let sunPos = [48, 26, -55], sunCol = "#ffd8a8", sunInt = 3.2, hemiInt = 1.05, exp = 1.15, intGlow = 14.0, fogCol = "#dbeafe";
    if (preset === "noon") {
      u.uTop.value.set("#0369a1"); u.uMid.value.set("#7dd3fc"); u.uBot.value.set("#f0f9ff");
      sunPos = [24, 84, -30]; sunCol = "#ffffff"; sunInt = 3.6; hemiInt = 1.18; exp = 1.06; intGlow = 8.0; fogCol = "#e0f2fe";
    } else if (preset === "dusk") {
      u.uTop.value.set("#0f172a"); u.uMid.value.set("#334155"); u.uBot.value.set("#f97316");
      sunPos = [-65, 10, -56]; sunCol = "#fb923c"; sunInt = 2.15; hemiInt = 0.72; exp = 1.12; intGlow = 24.0; fogCol = "#475569";
    } else if (preset === "night") {
      u.uTop.value.set("#020617"); u.uMid.value.set("#0f172a"); u.uBot.value.set("#1e293b");
      sunPos = [-30, 50, 40]; sunCol = "#93c5fd"; sunInt = 0.38; hemiInt = 0.40; exp = 1.04; intGlow = 34.0; fogCol = "#0f172a";
    } else {
      // Golden Hour 17:20
      u.uTop.value.set("#075985"); u.uMid.value.set("#38bdf8"); u.uBot.value.set("#fdba74");
      sunPos = [56, 23, -50]; sunCol = "#ffd89b"; sunInt = 3.30; hemiInt = 1.08; exp = 1.15; intGlow = 14.0; fogCol = "#fef3c7";
    }

    if (avz.scene.fog) avz.scene.fog.color.set(fogCol);
    avz.sunLight.position.set(sunPos[0], sunPos[1], sunPos[2]);
    avz.sunLight.color.set(sunCol);
    avz.sunLight.intensity = sunInt;
    avz.hemiLight.intensity = hemiInt;
    avz.renderer.toneMappingExposure = exp;
    u.uSunDir.value.set(sunPos[0], sunPos[1], sunPos[2]).normalize();
    if (avz.waterUniforms) avz.waterUniforms.uSunDir.value.copy(u.uSunDir.value);
    avz.interiorLights.forEach(l => { l.intensity = intGlow; });

    if (avz.pmremGen) {
      const envScene = new THREE.Scene();
      const skyClone = avz.skyMesh.clone();
      envScene.add(skyClone);
      if (avz.envRT) avz.envRT.dispose();
      avz.envRT = avz.pmremGen.fromScene(envScene, 0.04);
      avz.scene.environment = avz.envRT.texture;
      skyClone.geometry.dispose();
    }
  }
  window.setArchvizTimeOfDay = applyTimeOfDayPreset;

  // ---------------- PHOTOREALISTIC 3D ARCHITECTURAL & LANDSCAPE PROPS ----------------
  function addBox(parent, w, h, d, mat, x, y, z, castShadow = true, receiveShadow = true) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    m.position.set(x, y, z);
    m.castShadow = castShadow;
    m.receiveShadow = receiveShadow;
    parent.add(m);
    return m;
  }

  function createDatePalm(height = 8.5, seed = 0) {
    const g = new THREE.Group();
    const segs = 9;
    const leanDir = (seed % 2 === 0 ? 1 : -1);
    for (let i = 0; i < segs; i++) {
      const t = i / segs;
      const r0 = 0.27 * (1 - t * 0.34), r1 = 0.24 * (1 - t * 0.34);
      const cyl = new THREE.Mesh(new THREE.CylinderGeometry(r1, r0, height / segs + 0.07, 10), avz.mats.palmTrunk);
      const curveX = leanDir * Math.sin(t * 1.35) * 0.42;
      cyl.position.set(curveX, (i + 0.5) * (height / segs), 0);
      cyl.rotation.z = -leanDir * Math.cos(t * 1.35) * 0.07;
      cyl.castShadow = true;
      g.add(cyl);
    }
    const topX = leanDir * Math.sin(1.35) * 0.42;
    // Crownshaft + Golden Date Clusters
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.32, 10, 8), avz.mats.palmTrunk);
    bulb.position.set(topX, height - 0.08, 0);
    g.add(bulb);
    for (let d = 0; d < 3; d++) {
      const da = (d / 3) * Math.PI * 2 + seed;
      const dates = new THREE.Mesh(new THREE.SphereGeometry(0.16, 8, 8), avz.mats.gold);
      dates.scale.set(0.8, 1.4, 0.8);
      dates.position.set(topX + Math.cos(da) * 0.32, height - 0.34, Math.sin(da) * 0.32);
      g.add(dates);
    }

    // 18 Gracefully Arching Multi-Segment Pinnate Fronds (Upper + Mid + Lower Canopy!)
    const crown = new THREE.Group();
    crown.position.set(topX, height, 0);
    for (let f = 0; f < 18; f++) {
      const tier = f < 6 ? 0 : (f < 13 ? 1 : 2);
      const ang = (f / 18) * Math.PI * 2 + tier * 0.25;
      const frondGrp = new THREE.Group();
      frondGrp.rotation.y = ang;

      const fLen = tier === 0 ? 2.5 : (tier === 1 ? 3.25 : 2.95);
      const fWid = tier === 0 ? 0.95 : 1.18;
      const segGeo = new THREE.PlaneGeometry(fWid, fLen, 2, 6);
      const pos = segGeo.attributes.position;
      // Parabolic gravity arch + subtle V-fold along center spine
      for (let k = 0; k < pos.count; k++) {
        const vx = pos.getX(k);
        const vy = pos.getY(k); // -fLen/2 .. +fLen/2
        const u = Math.max(0, Math.min(1, (vy + fLen * 0.5) / fLen)); // clamped 0..1 so Math.pow never NaNs!
        const archZ = u * fLen * (tier === 0 ? 0.72 : 0.92);
        const archY = Math.sin(u * Math.PI * 0.65) * (tier === 0 ? 1.15 : (tier === 1 ? 0.65 : 0.22)) - Math.pow(u, 2.2) * (tier === 2 ? 1.35 : 0.85);
        const vFold = -Math.abs(vx) * 0.16;
        pos.setXYZ(k, vx, archY + vFold, archZ);
      }
      segGeo.computeVertexNormals();
      const blade = new THREE.Mesh(segGeo, avz.mats.palmFrond);
      blade.castShadow = true;
      frondGrp.add(blade);
      crown.add(frondGrp);
    }
    g.add(crown);
    avz.swayCrowns.push(crown);
    return g;
  }

  function createResortUmbrella() {
    const u = new THREE.Group();
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.04, 2.45, 10), avz.mats.bronze);
    pole.position.y = 1.22;
    pole.castShadow = true;
    u.add(pole);
    const canopy = new THREE.Mesh(new THREE.ConeGeometry(1.55, 0.42, 8), avz.mats.fabricCream);
    canopy.position.y = 2.38;
    canopy.castShadow = true;
    u.add(canopy);
    return u;
  }

  function createSunLounger() {
    const l = new THREE.Group();
    addBox(l, 0.84, 0.18, 2.05, avz.mats.oak, 0, 0.12, 0);
    addBox(l, 0.76, 0.09, 1.32, avz.mats.fabricCream, 0, 0.25, -0.30);
    const back = new THREE.Mesh(new THREE.BoxGeometry(0.76, 0.09, 0.68), avz.mats.fabricCream);
    back.position.set(0, 0.42, 0.62);
    back.rotation.x = -0.48;
    back.castShadow = true;
    l.add(back);
    addBox(l, 0.52, 0.08, 0.22, avz.mats.fabricTerracotta, 0, 0.54, 0.74);
    return l;
  }

  function createDiningChair(matSeat) {
    const ch = new THREE.Group();
    addBox(ch, 0.48, 0.07, 0.48, matSeat, 0, 0.45, 0);
    const back = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.42, 0.07), matSeat);
    back.position.set(0, 0.68, 0.21);
    back.rotation.x = 0.10;
    back.castShadow = true;
    ch.add(back);
    [[-0.20, -0.20], [0.20, -0.20], [-0.20, 0.20], [0.20, 0.20]].forEach(([lx, lz]) => {
      addBox(ch, 0.035, 0.44, 0.035, avz.mats.bronze, lx, 0.22, lz);
    });
    return ch;
  }

  function createIndoorPlant() {
    const p = new THREE.Group();
    const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.24, 0.55, 14), avz.mats.travertine);
    pot.position.y = 0.28;
    pot.castShadow = true;
    p.add(pot);
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.045, 1.35, 8), avz.mats.oak);
    stem.position.y = 1.1;
    p.add(stem);
    [[-0.18, 1.65, 0.12, 0.42], [0.20, 1.85, -0.10, 0.48], [0.0, 2.08, 0.08, 0.38]].forEach(([fx, fy, fz, r]) => {
      const fol = new THREE.Mesh(new THREE.SphereGeometry(r, 12, 10), avz.mats.hedge);
      fol.scale.set(1.15, 0.82, 1.15);
      fol.position.set(fx, fy, fz);
      fol.castShadow = true;
      p.add(fol);
    });
    return p;
  }

  function createLuxuryCar(paintMat, isSuv = false) {
    const car = new THREE.Group();
    const bodyH = isSuv ? 0.72 : 0.54;
    const cabH = isSuv ? 0.58 : 0.44;
    // Sculpted lower body + metallic hood + cabin greenhouse
    addBox(car, 2.04, bodyH, 4.78, paintMat, 0, 0.34 + bodyH * 0.5, 0);
    addBox(car, 1.80, cabH, isSuv ? 2.85 : 2.25, paintMat, 0, 0.34 + bodyH + cabH * 0.46, isSuv ? 0.15 : -0.15);
    addBox(car, 1.83, cabH * 0.78, isSuv ? 2.68 : 2.10, avz.mats.glass, 0, 0.34 + bodyH + cabH * 0.46, isSuv ? 0.15 : -0.15, false, false);
    // Front grille + LED DRL Headlights + Rear Lightbar
    addBox(car, 1.15, 0.28, 0.05, avz.mats.charcoal, 0, 0.54, -2.40);
    addBox(car, 1.88, 0.07, 0.06, avz.mats.ledWarm, 0, 0.68, -2.40, false, false);
    addBox(car, 1.88, 0.07, 0.06, new THREE.MeshBasicMaterial({ color: 0xef4444 }), 0, 0.74, 2.40, false, false);
    const wheelGeo = new THREE.CylinderGeometry(0.38, 0.38, 0.26, 16);
    wheelGeo.rotateZ(Math.PI * 0.5);
    const rimGeo = new THREE.CylinderGeometry(0.24, 0.24, 0.28, 12);
    rimGeo.rotateZ(Math.PI * 0.5);
    [[-0.98, 0.38, -1.52], [0.98, 0.38, -1.52], [-0.98, 0.38, 1.52], [0.98, 0.38, 1.52]].forEach(([wx, wy, wz]) => {
      const w = new THREE.Mesh(wheelGeo, avz.mats.charcoal);
      w.position.set(wx, wy, wz);
      w.castShadow = true;
      car.add(w);
      const rim = new THREE.Mesh(rimGeo, avz.mats.chrome);
      rim.position.set(wx, wy, wz);
      car.add(rim);
    });
    return car;
  }

  function populate3DRoomFurniture(group, r, wx, baseY, wz, rw, rd, flHeight) {
    const t = r.type;
    const nm = (r.name || "").toLowerCase();
    if (t === "living") {
      // Designer Woven Silk Rug centered in lounge zone
      const rugW = Math.min(rw * 0.54, 6.4), rugD = Math.min(rd * 0.58, 5.6);
      const loungeX = wx - rw * 0.16, loungeZ = wz - rd * 0.04;
      addBox(group, rugW, 0.018, rugD, avz.mats.rug, loungeX, baseY + 0.02, loungeZ, false, true);

      // Bespoke Minotti L-Sectional Sofa facing the Waterfront & Coffee Table
      const sw = Math.min(3.8, rw * 0.38), sd = Math.min(2.6, rd * 0.34);
      // Oak plinth + plush seat cushions + low architectural backrest + accent pillows
      addBox(group, sw + 0.12, 0.10, 1.02, avz.mats.oak, loungeX, baseY + 0.07, loungeZ + sd * 0.42);
      addBox(group, sw, 0.28, 0.96, avz.mats.fabricCream, loungeX, baseY + 0.26, loungeZ + sd * 0.42);
      addBox(group, sw, 0.38, 0.22, avz.mats.fabricCream, loungeX, baseY + 0.52, loungeZ + sd * 0.42 + 0.38);
      // Chaise wing on West side
      const chX = loungeX - sw * 0.5 + 0.50;
      addBox(group, 1.02, 0.10, sd, avz.mats.oak, chX, baseY + 0.07, loungeZ);
      addBox(group, 0.98, 0.28, sd - 0.06, avz.mats.fabricCream, chX, baseY + 0.26, loungeZ);
      addBox(group, 0.22, 0.38, sd - 0.12, avz.mats.fabricCream, chX - 0.38, baseY + 0.52, loungeZ);
      // Throw pillows
      addBox(group, 0.42, 0.28, 0.16, avz.mats.fabricTerracotta, loungeX - 0.75, baseY + 0.50, loungeZ + sd * 0.42 + 0.22);
      addBox(group, 0.42, 0.28, 0.16, avz.mats.fabricNavy, loungeX + 0.85, baseY + 0.50, loungeZ + sd * 0.42 + 0.22);

      // Sculpted Travertine & Bronze Dual Coffee Table + Art Books + Gold Vessel
      const ctW = Math.min(1.85, sw * 0.54);
      addBox(group, ctW, 0.30, 0.98, avz.mats.travertine, loungeX + 0.22, baseY + 0.17, loungeZ - 0.24);
      addBox(group, 0.42, 0.06, 0.32, avz.mats.fabricNavy, loungeX - 0.10, baseY + 0.35, loungeZ - 0.24);
      const vase = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.13, 0.28, 14), avz.mats.gold);
      vase.position.set(loungeX + 0.52, baseY + 0.46, loungeZ - 0.22);
      group.add(vase);

      // Two Bouclé Accent Lounge Chairs facing sofa
      [-0.55, 0.65].forEach(ox => {
        addBox(group, 0.82, 0.36, 0.80, avz.mats.fabricTaupe, loungeX + ox * 1.15, baseY + 0.20, loungeZ - 1.38);
        addBox(group, 0.82, 0.34, 0.18, avz.mats.fabricTaupe, loungeX + ox * 1.15, baseY + 0.48, loungeZ - 1.70);
      });

      // Fluted Oak Feature Console + Framed Contemporary Canvas Art on West Wall + Olive Tree
      addBox(group, 0.48, 0.58, Math.min(3.4, rd * 0.38), avz.mats.oak, wx - rw * 0.46, baseY + 0.30, wz);
      addBox(group, 0.06, 1.75, Math.min(2.6, rd * 0.30), avz.mats.artwork, wx - rw * 0.48, baseY + 1.85, wz);
      const olive = createIndoorPlant();
      olive.position.set(wx - rw * 0.42, baseY + 0.02, wz - rd * 0.38);
      group.add(olive);

      // Formal 10-to-14-Seat Calacatta Marble Dining Table + Sculpted Chairs on East Side
      if (rw >= 5.5 && rd >= 5.5) {
        const dx = wx + rw * 0.25, dz = wz - rd * 0.06;
        const tLen = Math.min(3.8, rd * 0.42);
        // Sculptural dual bronze pedestals + bevelled Calacatta tabletop
        addBox(group, 0.55, 0.72, 0.55, avz.mats.bronze, dx, baseY + 0.36, dz - tLen * 0.26);
        addBox(group, 0.55, 0.72, 0.55, avz.mats.bronze, dx, baseY + 0.36, dz + tLen * 0.26);
        addBox(group, 1.32, 0.07, tLen, avz.mats.marble, dx, baseY + 0.74, dz);

        const nSide = tLen >= 3.2 ? 4 : 3;
        for (let c = 0; c < nSide; c++) {
          const cz = dz - (tLen * 0.36) + (c / Math.max(1, nSide - 1)) * (tLen * 0.72);
          const chL = createDiningChair(avz.mats.leatherTan);
          chL.position.set(dx - 0.92, baseY + 0.02, cz);
          chL.rotation.y = Math.PI * 0.5;
          group.add(chL);
          const chR = createDiningChair(avz.mats.leatherTan);
          chR.position.set(dx + 0.92, baseY + 0.02, cz);
          chR.rotation.y = -Math.PI * 0.5;
          group.add(chR);
        }

        // Multi-Tier Floating Golden Halo Chandelier above Dining Table!
        if (avz.camStyle !== "cutaway") {
          [1.05, 0.68].forEach((rad, ri) => {
            const halo = new THREE.Mesh(new THREE.TorusGeometry(rad, 0.032, 12, 42), avz.mats.gold);
            halo.rotation.x = Math.PI * 0.5;
            halo.rotation.y = ri * 0.14;
            halo.position.set(dx, baseY + flHeight - 0.95 - ri * 0.28, dz);
            group.add(halo);
            const glow = new THREE.Mesh(new THREE.TorusGeometry(rad - 0.03, 0.018, 8, 36), avz.mats.ledWarm);
            glow.rotation.x = Math.PI * 0.5;
            glow.rotation.y = ri * 0.14;
            glow.position.set(dx, baseY + flHeight - 0.97 - ri * 0.28, dz);
            group.add(glow);
          });
        }
      }
    } else if (t === "kitchen") {
      // Full-Height Walnut Gaggenau Appliance Wall + Waterfall Calacatta Island + Sculpted Barstools
      addBox(group, rw * 0.84, 2.55, 0.68, avz.mats.oak, wx, baseY + 1.28, wz + rd * 0.38);
      addBox(group, 1.25, 0.68, 0.70, avz.mats.charcoal, wx - rw * 0.18, baseY + 1.38, wz + rd * 0.38);
      const iw = Math.min(3.4, rw * 0.68);
      addBox(group, iw, 0.92, 1.12, avz.mats.marble, wx, baseY + 0.46, wz - 0.25);
      addBox(group, 0.90, 0.025, 0.52, avz.mats.charcoal, wx - iw * 0.20, baseY + 0.935, wz - 0.25);
      for (let s = -1; s <= 1; s++) {
        const st = createDiningChair(avz.mats.leatherTan);
        st.scale.set(0.88, 1.28, 0.88);
        st.position.set(wx + s * (iw * 0.30), baseY + 0.02, wz - 1.05);
        group.add(st);
      }
    } else if (t === "master" || t === "bedroom") {
      // Orient King Bed along West Feature Wall so Sea-View Glass Terrace (-Z) & Bed Suite frame together!
      const bw = t === "master" ? Math.min(2.25, rd * 0.40) : Math.min(1.90, rd * 0.42);
      const bd = Math.min(2.35, rw * 0.44);
      const bx = wx - rw * 0.44 + bd * 0.5 + 0.18;
      const bz = wz + rd * 0.02;
      addBox(group, bd + 1.1, 0.018, bw + 1.5, avz.mats.rug, bx + 0.25, baseY + 0.02, bz, false, true);
      addBox(group, bd + 0.24, 0.26, bw + 0.28, avz.mats.oak, bx, baseY + 0.14, bz);
      addBox(group, bd, 0.30, bw, avz.mats.fabricCream, bx, baseY + 0.42, bz);
      addBox(group, bd * 0.40, 0.12, bw + 0.04, avz.mats.fabricNavy, bx + bd * 0.28, baseY + 0.58, bz);
      // Wide Upholstered & Oak Feature Headboard on West Wall + Bedside Tables + Warm Globe Lamps + Bench
      const hbX = wx - rw * 0.46;
      addBox(group, 0.14, 1.52, bw + 1.65, avz.mats.oak, hbX, baseY + 0.76, bz);
      addBox(group, 0.18, 1.08, bw + 0.22, avz.mats.fabricTaupe, hbX + 0.06, baseY + 0.68, bz);
      addBox(group, 0.05, 1.15, Math.min(1.8, bw * 0.78), avz.mats.artwork, hbX + 0.08, baseY + 2.25, bz);
      addBox(group, 0.42, 0.18, bw * 0.40, avz.mats.fabricCream, bx - bd * 0.32, baseY + 0.64, bz - bw * 0.24);
      addBox(group, 0.42, 0.18, bw * 0.40, avz.mats.fabricCream, bx - bd * 0.32, baseY + 0.64, bz + bw * 0.24);
      [-1, 1].forEach(sd => {
        const nz = bz + sd * (bw * 0.5 + 0.48), nx = hbX + 0.34;
        addBox(group, 0.48, 0.46, 0.58, avz.mats.travertine, nx, baseY + 0.23, nz);
        const globe = new THREE.Mesh(new THREE.SphereGeometry(0.13, 12, 10), avz.mats.ledWarm);
        globe.position.set(nx, baseY + 0.62, nz);
        group.add(globe);
      });
      addBox(group, 0.48, 0.42, bw * 0.84, avz.mats.fabricTaupe, bx + bd * 0.64, baseY + 0.21, bz);
      const fig = createIndoorPlant();
      fig.position.set(wx + rw * 0.36, baseY + 0.02, wz - rd * 0.36);
      group.add(fig);
    } else if (t === "bath") {
      const tub = new THREE.Mesh(new THREE.CylinderGeometry(0.50, 0.42, 0.60, 22), avz.mats.marble);
      tub.scale.set(1.80, 1, 0.96);
      tub.position.set(wx - rw * 0.18, baseY + 0.31, wz - rd * 0.20);
      tub.castShadow = true;
      group.add(tub);
      addBox(group, Math.min(2.3, rw * 0.58), 0.54, 0.62, avz.mats.oak, wx + rw * 0.12, baseY + 0.56, wz + rd * 0.32);
      addBox(group, Math.min(2.34, rw * 0.59), 0.08, 0.64, avz.mats.marble, wx + rw * 0.12, baseY + 0.86, wz + rd * 0.32);
    } else if (t === "core" || t === "void") {
      const steps = 12;
      const runLen = Math.min(3.6, rd * 0.66);
      for (let s = 0; s < steps; s++) {
        const f = s / steps;
        addBox(group, Math.min(1.40, rw * 0.34), 0.09, 0.34, avz.mats.oak, wx - rw * 0.22, baseY + 0.26 + f * (flHeight - 0.30), wz + runLen * 0.5 - f * runLen);
      }
      // Glass Stair Balustrade + Panoramic Glass Lift Core
      addBox(group, 0.05, 0.95, runLen, avz.mats.glassBalustrade, wx - rw * 0.22 + 0.72, baseY + flHeight * 0.45, wz, false, false);
      addBox(group, 1.58, flHeight * 0.94, 1.58, avz.mats.glassBalustrade, wx + rw * 0.22, baseY + flHeight * 0.47, wz, false, false);
      addBox(group, 1.66, 0.12, 1.66, avz.mats.bronze, wx + rw * 0.22, baseY + 0.06, wz);
    } else if (t === "garage") {
      const nCars = Math.max(1, Math.min(4, Math.floor(rw / 3.1)));
      const paints = [avz.mats.carPaintBlue, avz.mats.carPaintChampagne, avz.mats.carPaintBlack, avz.mats.carPaintSilver];
      for (let c = 0; c < nCars; c++) {
        const car = createLuxuryCar(paints[c % paints.length], c % 2 === 0);
        const cx = wx - ((nCars - 1) * 1.48) + c * 2.96;
        car.position.set(cx, baseY + 0.02, wz);
        group.add(car);
      }
    } else if (t === "wellness") {
      if (nm.includes("cinema")) {
        addBox(group, rw * 0.78, 2.05, 0.10, avz.mats.oledScreen, wx, baseY + 1.42, wz - rd * 0.43, false, false);
        addBox(group, rw * 0.66, 0.46, 0.98, avz.mats.fabricNavy, wx, baseY + 0.24, wz + 0.15);
        addBox(group, rw * 0.66, 0.68, 0.98, avz.mats.fabricNavy, wx, baseY + 0.36, wz + 1.55);
      } else {
        addBox(group, 0.88, 1.28, 1.90, avz.mats.charcoal, wx - rw * 0.22, baseY + 0.64, wz);
        addBox(group, 0.98, 0.56, 2.05, avz.mats.fabricCream, wx + rw * 0.22, baseY + 0.28, wz);
      }
    } else if (t === "pool") {
      // Deep Turquoise Tiled Pool Basin + Animated GLSL Water + Reclining Resort Sunbeds + Parasol Umbrellas!
      const pw = Math.max(2.5, rw - 1.2), pd = Math.max(2.5, rd - 2.4);
      addBox(group, pw + 0.35, 0.12, pd + 0.35, avz.mats.marble, wx, baseY + 0.08, wz - 0.45, false, true);
      addBox(group, pw, 0.06, pd, avz.mats.poolTile, wx, baseY + 0.04, wz - 0.45, false, true);
      const waterMesh = new THREE.Mesh(new THREE.PlaneGeometry(pw, pd, 28, 28), avz.mats.water);
      waterMesh.rotation.x = -Math.PI * 0.5;
      waterMesh.position.set(wx, baseY + 0.20, wz - 0.45);
      group.add(waterMesh);

      const nBeds = Math.min(5, Math.max(2, Math.floor(rw / 4.4)));
      const deckZ = wz + rd * 0.36;
      for (let b = 0; b < nBeds; b++) {
        const bx = wx - ((nBeds - 1) * 1.35) + b * 2.70;
        const lounger = createSunLounger();
        lounger.position.set(bx, baseY + 0.04, deckZ);
        group.add(lounger);
        if (b < nBeds - 1 && b % 2 === 0) {
          const umb = createResortUmbrella();
          umb.position.set(bx + 1.35, baseY + 0.04, deckZ + 0.25);
          group.add(umb);
        }
      }
    }
  }

  // ---------------- SCENE A: UNREAL 3D STREET-LEVEL WALKTHROUGH ----------------
  function buildArchvizStreetScene() {
    disposeArchvizScene();
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0xdbeafe, 0.0022);
    avz.scene = scene;
    setupSkyAndLighting(scene);

    const soc = getSocietyData(wtState.projectId || "PRJ-D19");
    const stop = (soc && soc.street_tour && soc.street_tour[wtState.stopIndex]) || (soc && soc.street_tour && soc.street_tour[0]);
    const zone = stop ? ((soc.zones || []).find(z => z.zone_id === stop.zone_id) || soc.zones[0]) : (soc ? soc.zones[0] : null);
    const isPJA = (wtState.projectId === "PRJ-D2");
    const isFrondOrWater = isPJA || (stop && /Lagoon|Lanai|Serenity|Frond|Spine/i.test(stop.title));

    // Base Terrain + Brushed Luxury Boulevard Asphalt + Raised Travertine Promenades
    addBox(scene, 280, 0.2, 290, avz.mats.sand, 0, -0.16, -45, false, true);
    addBox(scene, 9.6, 0.06, 200, avz.mats.asphalt, 0, 0.01, -40, false, true);

    [-6.8, 6.8].forEach(sx => {
      addBox(scene, 4.0, 0.16, 200, avz.mats.travertine, sx, 0.08, -40, false, true);
      addBox(scene, 28, 0.14, 200, avz.mats.lawn, sx < 0 ? -22.5 : 22.5, 0.06, -40, false, true);
      // Manicured Emerald Hedge + Blooming Magenta Bougainvillea along Villa Frontage!
      addBox(scene, 0.75, 0.68, 188, avz.mats.hedge, sx < 0 ? -8.95 : 8.95, 0.42, -40);
    });
    if (!isPJA) {
      // Signature Tilal Al Ghaf Terracotta Jogging & Cycling Track
      addBox(scene, 1.45, 0.17, 200, new THREE.MeshStandardMaterial({ color: 0xc2410c, roughness: 0.68 }), 5.45, 0.085, -40, false, true);
    }

    // If Palm Jebel Ali Frond or Lagoon Enclave: Shimmering Turquoise Water Channels flanking behind the Frond Villas!
    if (isFrondOrWater) {
      [-58, 58].forEach(wx => {
        const sideSea = new THREE.Mesh(new THREE.PlaneGeometry(56, 220, 24, 36), avz.mats.water);
        sideSea.rotation.x = -Math.PI * 0.5;
        sideSea.position.set(wx, 0.10, -45);
        scene.add(sideSea);
      });
    }

    // Crystal Lagoon / Arabian Gulf Waterfront Panorama at the North Horizon (-Z)
    addBox(scene, 280, 0.18, 9, avz.mats.sand, 0, 0.05, -138, false, true);
    const sea = new THREE.Mesh(new THREE.PlaneGeometry(320, 150, 48, 48), avz.mats.water);
    sea.rotation.x = -Math.PI * 0.5;
    sea.position.set(0, 0.12, -210);
    scene.add(sea);

    // Textured Glass Curtain-Wall Coastline / Dubai Marina Skyline Silhouette across the water
    for (let i = -9; i <= 9; i++) {
      if (isPJA && Math.abs(i) < 4) continue; // Open Arabian Gulf sea horizon in center of Frond!
      const th = 20 + ((Math.abs(i * 37 + 11) % 48));
      const tw = 6.5 + (Math.abs(i) % 3) * 2.2;
      addBox(scene, tw, th, tw, avz.mats.skyline, i * 13.5, th * 0.5, -268 - (Math.abs(i) % 3) * 9, false, false);
    }

    // Cruising Luxury Cars on the Boulevard!
    const roadCar1 = createLuxuryCar(avz.mats.carPaintChampagne, true);
    roadCar1.position.set(2.3, 0.04, 8.0);
    scene.add(roadCar1);
    const roadCar2 = createLuxuryCar(avz.mats.carPaintBlue, false);
    roadCar2.rotation.y = Math.PI;
    roadCar2.position.set(-2.3, 0.04, -34.0);
    scene.add(roadCar2);

    // 10 Architectural SAOTA / Nakheel / MAF Luxury Mansions (5 Left, 5 Right)
    const carPaints = [avz.mats.carPaintSilver, avz.mats.carPaintBlack, avz.mats.carPaintBlue, avz.mats.carPaintChampagne];
    for (let row = 0; row < 5; row++) {
      const vz = 32 - row * 32;
      [-1, 1].forEach((side, sIdx) => {
        const vx = side * 22.0;
        const gateX = side * 9.35;
        const vGrp = new THREE.Group();

        // Low Architectural Travertine Plinth + Bronze Louver Screen + Wide Open Driveway Gate (Cars 100% Visible!)
        addBox(vGrp, 0.36, 1.05, 9.5, avz.mats.travertine, gateX, 0.52, vz - 8.2);
        addBox(vGrp, 0.12, 0.95, 9.2, avz.mats.bronze, gateX, 1.52, vz - 8.2);
        addBox(vGrp, 0.36, 1.85, 6.2, avz.mats.travertine, gateX, 0.92, vz + 9.2);
        // Organic Cascading Bougainvillea & Tropical Shrub Clusters along Boundary Wall
        [-1.0, 0.0, 1.0].forEach((bz, bi) => {
          const bush = new THREE.Mesh(new THREE.SphereGeometry(0.46, 10, 8), avz.mats.hedge);
          bush.scale.set(0.85, 0.72, 1.35);
          bush.position.set(gateX - side * 0.22, 1.18, vz - 6.2 + bz * 0.95);
          vGrp.add(bush);
          const bloom = new THREE.Mesh(new THREE.SphereGeometry(0.32, 8, 8), avz.mats.bougainvillea);
          bloom.scale.set(0.9, 0.65, 1.15);
          bloom.position.set(gateX - side * 0.34, 1.34 + (bi % 2) * 0.08, vz - 6.2 + bz * 0.90);
          vGrp.add(bloom);
        });

        // Feature Travertine Gate Pier + Warm Backlit Plot Plaque + LED Strip
        addBox(vGrp, 0.65, 2.45, 1.25, avz.mats.travertine, gateX, 1.22, vz - 2.8);
        addBox(vGrp, 0.70, 0.22, 0.82, avz.mats.ledWarm, gateX, 1.58, vz - 2.8, false, false);

        // Open Travertine Forecourt + Cantilevered Oak Carport + Visible Luxury SUV & Sports Coupe!
        addBox(vGrp, 13.8, 0.15, 8.8, avz.mats.travertine, side * 15.2, 0.08, vz + 2.2, false, true);
        const car = createLuxuryCar(carPaints[(row + sIdx) % carPaints.length], (row + sIdx) % 2 === 0);
        car.rotation.y = side < 0 ? Math.PI * 0.42 : -Math.PI * 0.42;
        car.position.set(side * 13.4, 0.15, vz + 2.2);
        vGrp.add(car);

        // Villa Ground Floor Volume: Travertine + Double-Height Glass Atrium + Glowing Interior Halo Chandelier
        addBox(vGrp, 15.2, 4.4, 18.8, avz.mats.plasterWarm, vx, 2.20, vz - 0.5);
        addBox(vGrp, 1.4, 4.5, 2.8, avz.mats.travertine, vx - side * 7.3, 2.25, vz - 6.8);
        addBox(vGrp, 0.45, 4.2, 10.6, avz.mats.glass, vx - side * 7.62, 2.15, vz - 0.6, false, false);
        const streetHalo = new THREE.Mesh(new THREE.TorusGeometry(0.68, 0.04, 10, 28), avz.mats.ledWarm);
        streetHalo.rotation.x = Math.PI * 0.5;
        streetHalo.position.set(vx - side * 5.2, 3.65, vz - 0.6);
        vGrp.add(streetHalo);

        // Cantilevered Upper Master Volume + Warm Oak Soffit + Continuous 2700K LED Cove Strip + Glass Terrace!
        const cantShift = ((row + sIdx) % 2 === 0) ? 1.35 : 0.85;
        addBox(vGrp, 16.8, 3.85, 15.4, avz.mats.travertine, vx - side * cantShift, 6.32, vz - 1.2);
        addBox(vGrp, 16.9, 0.14, 15.5, avz.mats.oak, vx - side * cantShift, 4.42, vz - 1.2);
        addBox(vGrp, 0.14, 0.08, 14.8, avz.mats.ledWarm, vx - side * (cantShift + 8.35), 4.38, vz - 1.2, false, false);
        addBox(vGrp, 0.45, 3.35, 11.4, avz.mats.glass, vx - side * (cantShift + 8.38), 6.22, vz - 1.2, false, false);
        addBox(vGrp, 0.10, 1.08, 14.8, avz.mats.glassBalustrade, vx - side * (cantShift + 8.48), 4.96, vz - 1.2, false, false);
        // Vertical Architectural Bronze Privacy Screens on Upper Facade
        for (let lv = 0; lv < 5; lv++) {
          addBox(vGrp, 0.18, 3.6, 0.14, avz.mats.bronze, vx - side * (cantShift + 8.45), 6.25, vz - 6.6 + lv * 0.55);
        }

        // Sky Roof Penthouse + Bronze Pergola Louvres
        addBox(vGrp, 10.2, 0.36, 9.8, avz.mats.charcoal, vx, 8.42, vz - 1.0);
        for (let l = -4; l <= 4; l++) {
          addBox(vGrp, 9.6, 0.12, 0.18, avz.mats.bronze, vx - side * 2.4, 10.75, vz - 1.0 + l * 0.65);
        }
        addBox(vGrp, 0.24, 2.5, 0.24, avz.mats.bronze, vx - side * 7.0, 9.48, vz - 3.6);
        addBox(vGrp, 0.24, 2.5, 0.24, avz.mats.bronze, vx - side * 7.0, 9.48, vz + 1.6);

        // Garden Palm behind Villa
        const gPalm = createDatePalm(9.2, row * 3 + sIdx + 1);
        gPalm.position.set(vx + side * 4.5, 0.12, vz - 8.5);
        vGrp.add(gPalm);

        const ptLight = new THREE.PointLight(0xffd8a8, 1.4, 24);
        ptLight.position.set(vx - side * 6.0, 3.8, vz);
        vGrp.add(ptLight);
        avz.interiorLights.push(ptLight);

        scene.add(vGrp);
      });

      // Arching Pinnate Date Palms, Path Bollards & Architectural Street Luminaires along both sidewalks
      [-7.85, 7.85].forEach((px, pi) => {
        const palm = createDatePalm(8.4 + ((row + pi) % 3) * 0.85, row * 2 + pi);
        palm.position.set(px, 0.14, vz - 10.2);
        scene.add(palm);

        // Warm Landscape Bollard Light
        addBox(scene, 0.16, 0.78, 0.16, avz.mats.bronze, px * 0.96, 0.48, vz - 2.8);
        addBox(scene, 0.18, 0.12, 0.18, avz.mats.ledWarm, px * 0.96, 0.82, vz - 2.8, false, false);

        // Sleek Bronze Street Lamp
        addBox(scene, 0.13, 5.4, 0.13, avz.mats.bronze, px * 0.64, 2.7, vz + 5.2);
        addBox(scene, 0.82, 0.10, 0.26, avz.mats.bronze, px * 0.58, 5.4, vz + 5.2);
        addBox(scene, 0.68, 0.07, 0.20, avz.mats.ledWarm, px * 0.57, 5.34, vz + 5.2, false, false);
      });
    }

    // Glowing Interactive Villa Entry Portal Marker on Hero Right-Hand Mansion
    avz.streetPortalPos = { x: 9.2, y: 1.7, z: 2.2, defaultTypology: zone ? zone.default_typology_id : "TYP-TAG-SERENITY-6BR" };
    const portalRing = new THREE.Mesh(new THREE.RingGeometry(1.15, 1.52, 36), avz.mats.ledCyan);
    portalRing.rotation.x = -Math.PI * 0.5;
    portalRing.position.set(9.2, 0.20, 2.2);
    scene.add(portalRing);

    avz.camStyle = "fpv";
    avz.camPos = { x: 1.1, y: 1.70, z: 34 };
    avz.yaw = 0.05;
    avz.pitch = 0.02;
    avz.autoWaypoints = [
      { x: 1.1, y: 1.70, z: 36, yaw: 0.05 },
      { x: 0.6, y: 1.70, z: 10, yaw: -0.24 },
      { x: -0.7, y: 1.70, z: -20, yaw: 0.22 },
      { x: 0.4, y: 1.70, z: -56, yaw: -0.14 },
      { x: 0.0, y: 1.70, z: -98, yaw: 0.0 }
    ];
    applyTimeOfDayPreset(avz.timeOfDay);
  }

  // ---------------- SCENE B: UNREAL 3D VILLA INTERIOR + EXTERIOR ESTATE ----------------
  function buildArchvizVillaScene() {
    disposeArchvizScene();
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0xdbeafe, 0.0018);
    avz.scene = scene;
    setupSkyAndLighting(scene);

    const typ = DATA.walkthroughs.typologies[avz.typologyId] || Object.values(DATA.walkthroughs.typologies)[0];
    if (!typ) return;
    const pw = typ.plot_w, pd = typ.plot_d;

    // Surrounding Resort Context: White-Sand Beach (-Z North), Crystal Lagoon / Arabian Gulf, Lush Lawn, Boulevard (+Z South)
    addBox(scene, 300, 0.3, 300, avz.mats.sand, 0, -0.22, 0, false, true);
    addBox(scene, pw + 3.2, 0.14, pd + 2.4, avz.mats.lawn, 0, -0.05, 0, false, true);
    // White-sand private beach strip between Pool Deck and Lagoon
    addBox(scene, 240, 0.12, 8.5, avz.mats.sand, 0, -0.02, -pd * 0.5 - 3.8, false, true);
    addBox(scene, 160, 0.10, 9.5, avz.mats.asphalt, 0, -0.02, pd * 0.5 + 6.8, false, true);

    const ocean = new THREE.Mesh(new THREE.PlaneGeometry(300, 150, 56, 56), avz.mats.water);
    ocean.rotation.x = -Math.PI * 0.5;
    ocean.position.set(0, 0.04, -pd * 0.5 - 82);
    scene.add(ocean);

    // Plot Privacy Walls, Emerald Hedges & Arching Pinnate Date Palms framing the Sea View!
    [-pw * 0.5 - 0.35, pw * 0.5 + 0.35].forEach((wx, sideIdx) => {
      addBox(scene, 0.32, 2.15, pd * 0.84, avz.mats.travertine, wx, 1.08, pd * 0.04);
      addBox(scene, 0.68, 0.85, pd * 0.82, avz.mats.hedge, wx + (wx < 0 ? 0.5 : -0.5), 0.45, pd * 0.04);
      for (let p = -1; p <= 1; p++) {
        const palm = createDatePalm(8.2 + Math.abs(p) * 0.8, sideIdx * 5 + p + 2);
        palm.position.set(wx + (wx < 0 ? -1.4 : 1.4), 0, p * (pd * 0.28) - 2.0);
        scene.add(palm);
      }
    });

    const isSingleCutaway = (avz.camStyle === "cutaway");
    const isExploded = (avz.camStyle === "dollhouse" && avz.exploded);
    const floorsToBuild = isSingleCutaway
      ? typ.floors.filter(f => f.level === avz.floorKey)
      : typ.floors;

    // Exploded Multi-Storey Alignment Guide Columns (Architectural Presentation Style!)
    if (isExploded && floorsToBuild.length > 1) {
      const totalH = (floorsToBuild.length - 1) * 9.5 + 5.0;
      [[-pw * 0.43, -pd * 0.28], [pw * 0.43, -pd * 0.28], [-pw * 0.43, pd * 0.36], [pw * 0.43, pd * 0.36]].forEach(([gx, gz]) => {
        addBox(scene, 0.10, totalH, 0.10, avz.mats.bronze, gx, totalH * 0.5 - 2.0, gz, false, false);
      });
    }

    floorsToBuild.forEach((fl, fIdx) => {
      const explodeOffset = isExploded ? fIdx * 9.5 : 0;
      const baseY = (isSingleCutaway ? 0 : fl.elevation_m) + explodeOffset;
      const flH = fl.height_m || 3.8;
      // In Exploded mode, cut partition walls to 1.45m gallery height so EVERY floor's luxury interior is 100% visible!
      const wallH = isSingleCutaway ? 2.35 : (isExploded ? 1.45 : flH - 0.18);
      const showSectionCap = isSingleCutaway || isExploded;

      // Structural Travertine Floor Slab (0.14m thick so it NEVER intrudes below lower-floor ceiling!)
      if (baseY >= -0.05 || isExploded) {
        addBox(scene, pw * 0.90, 0.14, pd * 0.76, avz.mats.travertine, 0, baseY - 0.07, pd * 0.06, true, true);
        if (isExploded && fIdx > 0) {
          addBox(scene, pw * 0.91, 0.07, pd * 0.77, avz.mats.bronze, 0, baseY - 0.15, pd * 0.06, false, false);
        }
      } else {
        addBox(scene, pw * 0.88, 0.18, pd * 0.66, avz.mats.travertine, 0, baseY - 0.09, pd * 0.08, true, true);
      }

      fl.rooms.forEach(r => {
        const wx = (r.x + r.w * 0.5) - pw * 0.5;
        const wz = pd * 0.5 - (r.z + r.d * 0.5);
        const rw = r.w, rd = r.d;

        let floorMat = avz.mats.marble;
        if (r.type === "bedroom" || r.type === "master" || r.type === "wellness") floorMat = avz.mats.oak;
        else if (r.type === "terrace" || r.type === "pool" || r.type === "garage") floorMat = avz.mats.travertine;

        addBox(scene, rw - 0.06, 0.04, rd - 0.06, floorMat, wx, baseY + 0.02, wz, false, true);

        if (r.type !== "pool" && r.type !== "terrace" && r.type !== "garden") {
          const wt = 0.22;
          const northZ = wz - rd * 0.5, southZ = wz + rd * 0.5;
          const westX = wx - rw * 0.5, eastX = wx + rw * 0.5;
          const facesWaterfront = (r.z + r.d >= pd * 0.50);

          // North Wall (-Z, facing Infinity Pool & Lagoon): Slim Minimalist Bronze Sliding Glass + Sheer Linen Drapery!
          if (facesWaterfront) {
            addBox(scene, rw, wallH, 0.05, avz.mats.glass, wx, baseY + wallH * 0.5, northZ, false, false);
            for (let m = -1; m <= 1; m++) {
              addBox(scene, 0.06, wallH, 0.10, avz.mats.bronze, wx + m * (rw * 0.33), baseY + wallH * 0.5, northZ);
            }
            if (!showSectionCap && rw > 4.5) {
              // Flowing Sheer Linen Curtains flanking the Panoramic Glass!
              addBox(scene, 0.85, wallH - 0.08, 0.18, avz.mats.sheerCurtain, westX + 0.55, baseY + wallH * 0.5, northZ + 0.18, false, false);
              addBox(scene, 0.85, wallH - 0.08, 0.18, avz.mats.sheerCurtain, eastX - 0.55, baseY + wallH * 0.5, northZ + 0.18, false, false);
            }
          } else {
            const segW = Math.max(0.3, (rw - 1.55) * 0.5);
            addBox(scene, segW, wallH, wt, avz.mats.plasterWarm, westX + segW * 0.5, baseY + wallH * 0.5, northZ);
            addBox(scene, segW, wallH, wt, avz.mats.plasterWarm, eastX - segW * 0.5, baseY + wallH * 0.5, northZ);
            if (showSectionCap) {
              addBox(scene, segW, 0.05, wt + 0.02, avz.mats.pocheCap, westX + segW * 0.5, baseY + wallH + 0.025, northZ, false, false);
              addBox(scene, segW, 0.05, wt + 0.02, avz.mats.pocheCap, eastX - segW * 0.5, baseY + wallH + 0.025, northZ, false, false);
            }
          }

          // South Wall (+Z, Street/Corridor side)
          if (r.type === "garage") {
            if (!showSectionCap) addBox(scene, rw, 0.45, wt, avz.mats.bronze, wx, baseY + wallH - 0.22, southZ);
          } else {
            const segW = Math.max(0.3, (rw - 1.55) * 0.5);
            addBox(scene, segW, wallH, wt, avz.mats.plasterWarm, westX + segW * 0.5, baseY + wallH * 0.5, southZ);
            addBox(scene, segW, wallH, wt, avz.mats.plasterWarm, eastX - segW * 0.5, baseY + wallH * 0.5, southZ);
            if (showSectionCap) {
              addBox(scene, segW, 0.05, wt + 0.02, avz.mats.pocheCap, westX + segW * 0.5, baseY + wallH + 0.025, southZ, false, false);
              addBox(scene, segW, 0.05, wt + 0.02, avz.mats.pocheCap, eastX - segW * 0.5, baseY + wallH + 0.025, southZ, false, false);
            }
          }

          // West & East Partition Walls with Framed Open Portals
          const sideSeg = Math.max(0.3, (rd - 1.55) * 0.5);
          [westX, eastX].forEach(sx => {
            addBox(scene, wt, wallH, sideSeg, avz.mats.plasterWarm, sx, baseY + wallH * 0.5, northZ + sideSeg * 0.5);
            addBox(scene, wt, wallH, sideSeg, avz.mats.plasterWarm, sx, baseY + wallH * 0.5, southZ - sideSeg * 0.5);
            if (showSectionCap) {
              addBox(scene, wt + 0.02, 0.05, sideSeg, avz.mats.pocheCap, sx, baseY + wallH + 0.025, northZ + sideSeg * 0.5, false, false);
              addBox(scene, wt + 0.02, 0.05, sideSeg, avz.mats.pocheCap, sx, baseY + wallH + 0.025, southZ - sideSeg * 0.5, false, false);
            }
          });

          // Coffered Architectural White Gypsum Ceiling (unobstructed below upper slab!) + Warm Walnut Inlay + 2700K LED Cove!
          if (!showSectionCap) {
            addBox(scene, rw, 0.10, rd, avz.mats.ceilingWhite, wx, baseY + flH - 0.21, wz, false, false);
            if (rw >= 4.5 && rd >= 4.5) {
              addBox(scene, rw * 0.56, 0.04, rd * 0.52, avz.mats.oak, wx, baseY + flH - 0.27, wz, false, false);
              addBox(scene, rw * 0.80, 0.035, 0.09, avz.mats.ledWarm, wx, baseY + flH - 0.27, wz - rd * 0.38, false, false);
              addBox(scene, rw * 0.80, 0.035, 0.09, avz.mats.ledWarm, wx, baseY + flH - 0.27, wz + rd * 0.38, false, false);
            }
            if (r.type === "living" || r.type === "master" || r.type === "kitchen" || r.type === "void") {
              const pl = new THREE.PointLight(0xffe8c2, 14.0, 24, 1.3);
              pl.position.set(wx, baseY + flH - 0.72, wz);
              scene.add(pl);
              avz.interiorLights.push(pl);
            }
          }
        } else if (r.type === "terrace" && (baseY > 1.0 || isExploded)) {
          addBox(scene, rw, 1.08, 0.08, avz.mats.glassBalustrade, wx, baseY + 0.54, wz - rd * 0.5, false, false);
          addBox(scene, 0.08, 1.08, rd, avz.mats.glassBalustrade, wx - rw * 0.5, baseY + 0.54, wz, false, false);
          addBox(scene, 0.08, 1.08, rd, avz.mats.glassBalustrade, wx + rw * 0.5, baseY + 0.54, wz, false, false);
        }

        populate3DRoomFurniture(scene, r, wx, baseY, wz, rw, rd, flH);
      });
    });

    const activeFl = typ.floors.find(f => f.level === avz.floorKey) || typ.floors[0];
    avz.autoWaypoints = activeFl.rooms.map(r => ({
      x: (r.x + r.w * 0.5) - pw * 0.5,
      y: (avz.camStyle === "cutaway" ? 0 : activeFl.elevation_m) + 1.68,
      z: pd * 0.5 - (r.z + r.d * 0.18),
      yaw: 0.0,
      roomId: r.id
    }));

    applyTimeOfDayPreset(avz.timeOfDay);
  }

  // =========================================================================
  // RIGHT-SIDE-UP ARCHITECTURAL CAD & RENDERED BROCHURE FLOOR-PLAN ENGINE
  // =========================================================================
  const CAD_ROOM_STYLES = {
    living:   { cad: "#0c2545", bro: "#f5efe6", stroke: "#1e293b" },
    kitchen:  { cad: "#0e294d", bro: "#ede4d3", stroke: "#1e293b" },
    master:   { cad: "#102c54", bro: "#e6d5c3", stroke: "#1e293b" },
    bedroom:  { cad: "#0d2647", bro: "#eadbc8", stroke: "#1e293b" },
    bath:     { cad: "#0a2e4d", bro: "#e2e8f0", stroke: "#1e293b" },
    core:     { cad: "#0b223f", bro: "#f1ebe1", stroke: "#1e293b" },
    void:     { cad: "#0b223f", bro: "#f1ebe1", stroke: "#1e293b" },
    garage:   { cad: "#091d36", bro: "#cbd5e1", stroke: "#1e293b" },
    staff:    { cad: "#0b223f", bro: "#e2e8f0", stroke: "#1e293b" },
    wellness: { cad: "#112a4f", bro: "#e5d4c0", stroke: "#1e293b" },
    terrace:  { cad: "#09213c", bro: "#e7dec8", stroke: "#475569" },
    pool:     { cad: "#0369a1", bro: "#22d3ee", stroke: "#0284c7" }
  };

  function draw2DFurnitureSvg(r, rx, ry, rw, rd, isBrochure = true) {
    const cx = rx + rw * 0.5, cy = ry + rd * 0.5;
    const t = r.type;
    const fFill = isBrochure ? "#ffffff" : "rgba(14,165,233,0.14)";
    const fSub  = isBrochure ? "#e2e8f0" : "rgba(56,189,248,0.22)";
    const fStr  = isBrochure ? "#334155" : "#7dd3fc";
    let s = "";
    if (t === "living" && rw > 54 && rd > 54) {
      const sw = Math.min(rw * 0.42, 68), sd = Math.min(rd * 0.34, 48);
      s += `<rect x="${rx + 10}" y="${cy - sd * 0.4}" width="${sw}" height="${sd}" rx="2" fill="none" stroke="${fStr}" stroke-width="0.9" stroke-dasharray="3,2"/>`;
      s += `<path d="M ${rx + 12} ${cy + sd * 0.45} H ${rx + 12 + sw * 0.85} V ${cy + sd * 0.45 - 13} H ${rx + 25} V ${cy - sd * 0.35} H ${rx + 12} Z" fill="${fFill}" stroke="${fStr}" stroke-width="1.2"/>`;
      s += `<rect x="${rx + 29}" y="${cy - 6}" width="${sw * 0.42}" height="14" rx="2" fill="${fSub}" stroke="${fStr}" stroke-width="1.0"/>`;
      if (rw > 90) {
        const tx = rx + rw * 0.72, ty = cy - 22, tw = 22, th = Math.min(46, rd * 0.45);
        s += `<rect x="${tx - tw * 0.5}" y="${ty}" width="${tw}" height="${th}" rx="3" fill="${fFill}" stroke="${fStr}" stroke-width="1.2"/>`;
        for (let i = 0; i < 3; i++) {
          const chy = ty + 6 + i * ((th - 12) / 2);
          s += `<rect x="${tx - tw * 0.5 - 6}" y="${chy - 3}" width="4.5" height="7" rx="1" fill="${fSub}" stroke="${fStr}" stroke-width="0.9"/>`;
          s += `<rect x="${tx + tw * 0.5 + 1.5}" y="${chy - 3}" width="4.5" height="7" rx="1" fill="${fSub}" stroke="${fStr}" stroke-width="0.9"/>`;
        }
      }
    } else if ((t === "master" || t === "bedroom") && rw > 42 && rd > 42) {
      const bw = Math.min(36, rw * 0.46), bh = Math.min(40, rd * 0.48);
      const bx = cx - bw * 0.5, by = ry + rd - bh - 8;
      s += `<rect x="${bx}" y="${by}" width="${bw}" height="${bh}" rx="2" fill="${fFill}" stroke="${fStr}" stroke-width="1.2"/>`;
      s += `<line x1="${bx}" y1="${by + bh * 0.35}" x2="${bx + bw}" y2="${by + bh * 0.35}" stroke="${fStr}" stroke-width="0.9"/>`;
      s += `<rect x="${bx + 3}" y="${by + bh - 10}" width="${bw * 0.4}" height="7" rx="1.5" fill="${fSub}" stroke="${fStr}" stroke-width="0.9"/>`;
      s += `<rect x="${bx + bw * 0.53}" y="${by + bh - 10}" width="${bw * 0.4}" height="7" rx="1.5" fill="${fSub}" stroke="${fStr}" stroke-width="0.9"/>`;
      s += `<rect x="${bx - 8}" y="${by + bh - 9}" width="6" height="6" fill="${fFill}" stroke="${fStr}" stroke-width="0.9"/>`;
      s += `<rect x="${bx + bw + 2}" y="${by + bh - 9}" width="6" height="6" fill="${fFill}" stroke="${fStr}" stroke-width="0.9"/>`;
    } else if (t === "kitchen" && rw > 42 && rd > 42) {
      s += `<rect x="${rx + 5}" y="${ry + rd - 14}" width="${rw - 10}" height="10" fill="${fSub}" stroke="${fStr}" stroke-width="1.1"/>`;
      const iw = Math.min(rw * 0.56, 48);
      s += `<rect x="${cx - iw * 0.5}" y="${cy - 8}" width="${iw}" height="15" rx="1.5" fill="${fFill}" stroke="${fStr}" stroke-width="1.2"/>`;
      s += `<circle cx="${cx - 6}" cy="${cy - 1}" r="2.3" fill="none" stroke="${fStr}" stroke-width="0.9"/>`;
      s += `<circle cx="${cx + 2}" cy="${cy - 1}" r="2.3" fill="none" stroke="${fStr}" stroke-width="0.9"/>`;
    } else if (t === "bath" && rw > 30 && rd > 36) {
      s += `<ellipse cx="${rx + 14}" cy="${ry + 15}" rx="9" ry="5.5" fill="${fFill}" stroke="${fStr}" stroke-width="1.2"/>`;
      s += `<rect x="${rx + rw - 14}" y="${ry + 6}" width="10" height="22" fill="${fSub}" stroke="${fStr}" stroke-width="1"/>`;
    } else if (t === "garage" && rw > 46 && rd > 46) {
      const nCars = Math.min(3, Math.max(1, Math.floor(rw / 36)));
      for (let c = 0; c < nCars; c++) {
        const gx = cx - ((nCars - 1) * 16) + c * 32 - 11, gy = cy - 20;
        s += `<rect x="${gx}" y="${gy}" width="22" height="40" rx="5" fill="${fFill}" stroke="${fStr}" stroke-width="1.2"/>`;
        s += `<rect x="${gx + 3}" y="${gy + 9}" width="16" height="18" rx="2" fill="${fSub}" stroke="${fStr}" stroke-width="0.9"/>`;
      }
    } else if (t === "core" || t === "void") {
      const sw = Math.min(20, rw * 0.34), sh = Math.min(34, rd * 0.56);
      const sx = rx + 7, sy = cy - sh * 0.5;
      s += `<rect x="${sx}" y="${sy}" width="${sw}" height="${sh}" fill="${fSub}" stroke="${fStr}" stroke-width="1.1"/>`;
      for (let k = 1; k < 6; k++) {
        const ly = sy + (sh * k) / 6;
        s += `<line x1="${sx}" y1="${ly}" x2="${sx + sw}" y2="${ly}" stroke="${fStr}" stroke-width="0.8"/>`;
      }
      const lx = rx + rw - 21, ly = cy - 8;
      s += `<rect x="${lx}" y="${ly}" width="15" height="15" fill="${fFill}" stroke="${fStr}" stroke-width="1.1"/>`;
      s += `<line x1="${lx}" y1="${ly}" x2="${lx + 15}" y2="${ly + 15}" stroke="${fStr}" stroke-width="0.8"/>`;
      s += `<line x1="${lx + 15}" y1="${ly}" x2="${lx}" y2="${ly + 15}" stroke="${fStr}" stroke-width="0.8"/>`;
    } else if (t === "pool") {
      s += `<rect x="${rx + 6}" y="${ry + 6}" width="${Math.max(8, rw - 12)}" height="${Math.max(8, rd - 16)}" rx="3" fill="#06b6d4" fill-opacity="0.45" stroke="#38bdf8" stroke-width="1.2"/>`;
      for (let b = 0; b < 4; b++) {
        s += `<rect x="${cx - 34 + b * 19}" y="${ry + rd - 8}" width="11" height="5.5" rx="1" fill="${fFill}" stroke="${fStr}" stroke-width="0.9"/>`;
      }
    }
    return s;
  }

  function renderRightSideUpCadSvg() {
    const container = document.getElementById("archvizSvgContainer");
    if (!container) return;
    const typ = DATA.walkthroughs.typologies[avz.typologyId];
    if (!typ) return;
    const activeFl = typ.floors.find(f => f.level === avz.floorKey) || typ.floors[0];

    const pw = typ.plot_w, pd = typ.plot_d;
    const scale = Math.max(12.5, Math.min(25, 470 / Math.max(pw, pd)));
    const padL = 52, padT = 56, padR = 44, padB = 78;
    const W = Math.round(pw * scale + padL + padR);
    const H = Math.round(pd * scale + padT + padB);
    const isBrochure = (avz.cadStyle === "brochure");
    container.style.background = isBrochure ? "#ffffff" : "#041022";

    const sheetBg   = isBrochure ? "#faf7f2" : "#07192f";
    const sheetBdr  = isBrochure ? "#cbd5e1" : "#1e3a8a";
    const plotFill  = isBrochure ? "#e4eedb" : "#091e38";
    const plotStr   = isBrochure ? "#475569" : "#38bdf8";
    const gridStr   = isBrochure ? "#cbd5e1" : "rgba(56,189,248,0.28)";
    const dimCol    = isBrochure ? "#475569" : "#7dd3fc";

    // Structural Grid A..E (X) + Outer Plot Dimension Chain along Left Margin!
    const cols = ["A", "B", "C", "D", "E"];
    const gridX = [0, 0.25, 0.5, 0.75, 1.0].map((f, i) => {
      const gx = padL + pw * f * scale;
      return `<line x1="${gx}" y1="${padT - 8}" x2="${gx}" y2="${padT + pd * scale + 8}" stroke="${gridStr}" stroke-width="0.7" stroke-dasharray="3,3"/>
              <circle cx="${gx}" cy="${padT - 16}" r="7.5" fill="${isBrochure ? '#fff' : '#0c2545'}" stroke="${plotStr}" stroke-width="1"/>
              <text x="${gx}" y="${padT - 13}" text-anchor="middle" font-size="8" font-weight="800" fill="${isBrochure ? '#0f172a' : '#e0f2fe'}">${cols[i]}</text>`;
    }).join("");

    const dimLeftSvg = `
      <line x1="22" y1="${padT}" x2="22" y2="${padT + pd * scale}" stroke="${dimCol}" stroke-width="1"/>
      <line x1="17" y1="${padT}" x2="29" y2="${padT}" stroke="${dimCol}" stroke-width="1.2"/>
      <line x1="17" y1="${padT + pd * scale}" x2="29" y2="${padT + pd * scale}" stroke="${dimCol}" stroke-width="1.2"/>
      <text x="15" y="${padT + (pd * scale) * 0.5}" text-anchor="middle" font-size="8" font-weight="800" fill="${dimCol}" transform="rotate(-90 15 ${padT + (pd * scale) * 0.5})">PLOT DEPTH ${pd.toFixed(1)}m</text>
    `;

    const roomsHtml = activeFl.rooms.map(r => {
      // CRITICAL RIGHT-SIDE-UP TRANSFORM:
      // r.z = 0 (Garage / Street Entry) -> BOTTOM of sheet!
      // r.z = pd (Infinity Pool / Lagoon Beach) -> TOP of sheet!
      const rx = padL + r.x * scale;
      const ry = padT + (pd - (r.z + r.d)) * scale;
      const rw = r.w * scale;
      const rd = r.d * scale;
      const st = CAD_ROOM_STYLES[r.type] || CAD_ROOM_STYLES.core;
      const fillCol = isBrochure ? st.bro : st.cad;
      const isSel = (r.id === avz.selectedRoomId);
      const isOutdoor = (r.type === "pool" || r.type === "terrace");
      const sqft = Math.round(r.w * r.d * 10.7639);

      const wallStroke = isSel ? (isBrochure ? "#2563eb" : "#34d399") : (isBrochure ? "#0f172a" : "#bae6fd");
      const wallW = isSel ? 4.2 : (isOutdoor ? 1.5 : 3.2);
      let openingsSvg = "";
      if (!isOutdoor && r.z + r.d >= pd * 0.50) {
        openingsSvg += `<line x1="${rx + 4}" y1="${ry}" x2="${rx + rw - 4}" y2="${ry}" stroke="#06b6d4" stroke-width="4.2"/>`;
        openingsSvg += `<line x1="${rx + 4}" y1="${ry}" x2="${rx + rw - 4}" y2="${ry}" stroke="#e0f2fe" stroke-width="1.2"/>`;
      }
      if (!isOutdoor && rw > 34 && rd > 34) {
        const dr = Math.min(13, rw * 0.22);
        const dx = rx + rw * 0.5 - dr * 0.5, dy = ry + rd;
        openingsSvg += `<line x1="${dx}" y1="${dy}" x2="${dx + dr}" y2="${dy}" stroke="${fillCol}" stroke-width="4.5"/>`;
        openingsSvg += `<path d="M ${dx} ${dy} L ${dx} ${dy - dr} A ${dr} ${dr} 0 0 1 ${dx + dr} ${dy}" fill="none" stroke="${isBrochure ? '#334155' : '#38bdf8'}" stroke-width="1.1"/>`;
      }

      const furnSvg = draw2DFurnitureSvg(r, rx, ry, rw, rd, isBrochure);
      const lblY = ry + rd * 0.46;
      const pillBg = isBrochure ? "rgba(255,255,255,0.88)" : "rgba(2,6,23,0.82)";
      const pillTxt = isBrochure ? "#0f172a" : "#f8fafc";
      const pillSub = isBrochure ? "#0369a1" : "#38bdf8";

      const pillW = Math.max(24, Math.min(rw - 6, 108));
      const maxCh = Math.max(7, Math.floor(pillW / 4.8));
      const cleanLbl = r.name.length > maxCh ? r.name.slice(0, maxCh - 1) + "…" : r.name;

      return `
        <g style="cursor:pointer;" onclick="teleportVillaRoom('${r.id}')">
          <rect x="${rx}" y="${ry}" width="${rw}" height="${rd}" fill="${fillCol}" stroke="${wallStroke}" stroke-width="${wallW}"/>
          ${furnSvg}
          ${openingsSvg}
          <rect x="${rx + rw * 0.5 - pillW * 0.5}" y="${lblY - 9}" width="${pillW}" height="${rd >= 42 ? 25 : 16}" rx="3" fill="${pillBg}"/>
          <text x="${rx + rw * 0.5}" y="${lblY + 1}" text-anchor="middle" font-size="${rw < 58 ? 6.4 : (rw < 74 ? 7.2 : 8.2)}" font-weight="800" fill="${pillTxt}">${cleanLbl}</text>
          ${rd >= 42 ? `<text x="${rx + rw * 0.5}" y="${lblY + 11}" text-anchor="middle" font-size="${rw < 58 ? 6.0 : 6.9}" font-weight="700" fill="${pillSub}">${r.w.toFixed(1)}×${r.d.toFixed(1)}m · ${sqft} sf</text>` : ""}
        </g>
      `;
    }).join("");

    const fullFloorHeader = `${activeFl.level} — ${activeFl.name}`;
    const safeFloorHeader = fullFloorHeader.length > 48 ? fullFloorHeader.slice(0, 46) + "…" : fullFloorHeader;

    container.innerHTML = `
      <svg id="archvizFloorSvg" viewBox="0 0 ${W} ${H}" data-pw="${pw}" data-pd="${pd}" data-scale="${scale}" data-padl="${padL}" data-padt="${padT}" style="width:100%; max-height:100%; font-family:Inter,system-ui,sans-serif; user-select:none;">
        <rect x="2" y="2" width="${W - 4}" height="${H - 4}" rx="8" fill="${sheetBg}" stroke="${sheetBdr}" stroke-width="1.5"/>
        <!-- TOP WATERFRONT / LAGOON / SEA ORIENTATION HEADER (NORTH UP) -->
        <rect x="${padL}" y="8" width="${pw * scale}" height="19" rx="4" fill="#0891b2"/>
        <text x="${padL + (pw * scale) * 0.5}" y="20.5" text-anchor="middle" font-size="8.4" font-weight="900" fill="#ffffff" letter-spacing="0.04em">🌊 ▲ PRIVATE LAGOON / ARABIAN GULF WATERFRONT VIEW (NORTH) ▲</text>
        ${gridX}
        ${dimLeftSvg}
        <!-- Plot Lawn / Blueprint Envelope -->
        <rect x="${padL}" y="${padT}" width="${pw * scale}" height="${pd * scale}" fill="${plotFill}" stroke="${plotStr}" stroke-width="1.6" stroke-dasharray="5,3"/>
        ${roomsHtml}
        <!-- LIVE 3D CAMERA POSITION & FOV CONE OVERLAY -->
        <g id="cadLiveCamMarker" pointer-events="none"></g>
        <!-- BOTTOM STREET ARRIVAL / MAIN ENTRANCE INDICATOR (SOUTH DOWN) -->
        <rect x="${padL}" y="${padT + pd * scale + 7}" width="${pw * scale}" height="19" rx="4" fill="#1e293b"/>
        <text x="${padL + (pw * scale) * 0.5}" y="${padT + pd * scale + 19.5}" text-anchor="middle" font-size="8.2" font-weight="900" fill="#34d399" letter-spacing="0.04em">▲ MAIN STREET ARRIVAL, FORECOURT &amp; GARAGE ENTRANCE ▲</text>
        <!-- CAD Architectural Title Block -->
        <g transform="translate(${padL}, ${padT + pd * scale + 30})">
          <rect x="0" y="0" width="${pw * scale}" height="38" rx="5" fill="#0f172a" stroke="${isBrochure ? 'none' : '#1e3a8a'}"/>
          <text x="9" y="15" font-size="8.5" font-weight="800" fill="#38bdf8">${safeFloorHeader}</text>
          <text x="9" y="28.5" font-size="7.4" fill="#cbd5e1">Plot: ${pw}m×${pd}m · Elev +${activeFl.elevation_m.toFixed(1)}m · H ${activeFl.height_m.toFixed(1)}m · ${typ.contractor.split('(')[0].trim().slice(0, 26)}</text>
          <g transform="translate(${pw * scale - 24}, 19)">
            <circle cx="0" cy="0" r="10.5" fill="#0284c7" stroke="#bae6fd" stroke-width="1.2"/>
            <polygon points="0,-7.5 3.8,4.8 0,1.8 -3.8,4.8" fill="#ffffff"/>
            <text x="0" y="-12.5" text-anchor="middle" font-size="6.2" font-weight="900" fill="#38bdf8">N</text>
          </g>
        </g>
      </svg>
    `;
    updateCadLiveCameraCone();
  }

  function updateCadLiveCameraCone() {
    const g = document.getElementById("cadLiveCamMarker");
    const svg = document.getElementById("archvizFloorSvg");
    if (!g || !svg || avz.sceneKind !== "villa") return;
    const pw = parseFloat(svg.dataset.pw), pd = parseFloat(svg.dataset.pd);
    const sc = parseFloat(svg.dataset.scale), padL = parseFloat(svg.dataset.padl), padT = parseFloat(svg.dataset.padt);
    // World (wx, wz) -> SVG (sx, sy): wx = x - pw/2 => x = wx + pw/2; wz = pd/2 - z => svgY = padT + (pd - z)*sc = padT + (wz + pd/2)*sc!
    const sx = padL + (avz.camPos.x + pw * 0.5) * sc;
    const sy = padT + (avz.camPos.z + pd * 0.5) * sc;
    // yaw = 0 looks toward -Z (TOP of SVG, angle -90 deg in screen space); rotating left (+yaw) turns counter-clockwise!
    const deg = (-avz.yaw * 180) / Math.PI;
    g.innerHTML = `
      <g transform="translate(${sx.toFixed(1)}, ${sy.toFixed(1)}) rotate(${deg.toFixed(1)})">
        <polygon points="0,0 -20,-34 20,-34" fill="rgba(16,185,129,0.34)" stroke="#10b981" stroke-width="1"/>
        <circle cx="0" cy="0" r="5.5" fill="#10b981" stroke="#ffffff" stroke-width="2"/>
      </g>
    `;
  }

  // =========================================================================
  // STUDIO UI, CAMERA LOOP & USER INTERACTION CONTROLLERS
  // =========================================================================
  function startArchvizLoop() {
    if (avz.rafId) return;
    avz.lastFrameTs = performance.now();
    const tick = (now) => {
      if (!avz.open || !avz.renderer || !avz.scene || !avz.camera) {
        avz.rafId = null;
        return;
      }
      const dt = Math.min(0.08, (now - avz.lastFrameTs) / 1000);
      avz.lastFrameTs = now;

      if (avz.waterUniforms) avz.waterUniforms.uTime.value = now * 0.001;
      avz.swayCrowns.forEach((c, idx) => {
        c.rotation.z = Math.sin(now * 0.0014 + idx) * 0.035;
      });

      const canvas = avz.renderer.domElement;
      const w = canvas.clientWidth || 800, h = canvas.clientHeight || 600;
      if (canvas.width !== Math.round(w * avz.renderer.getPixelRatio()) || canvas.height !== Math.round(h * avz.renderer.getPixelRatio())) {
        avz.renderer.setSize(w, h, false);
        avz.camera.aspect = w / Math.max(1, h);
        avz.camera.updateProjectionMatrix();
      }

      // Smooth waypoint auto-tour
      if (avz.autoWalkActive && avz.autoWaypoints.length >= 2) {
        avz.autoWalkT += dt * (avz.sceneKind === "street" ? 0.055 : 0.14);
        if (avz.autoWalkT >= avz.autoWaypoints.length - 1) avz.autoWalkT = 0;
        const i0 = Math.floor(avz.autoWalkT), frac = avz.autoWalkT - i0;
        const a = avz.autoWaypoints[i0], b = avz.autoWaypoints[(i0 + 1) % avz.autoWaypoints.length];
        avz.camPos.x = a.x + (b.x - a.x) * frac;
        avz.camPos.y = a.y + (b.y - a.y) * frac;
        avz.camPos.z = a.z + (b.z - a.z) * frac;
        avz.yaw = a.yaw + (b.yaw - a.yaw) * frac;
        if (avz.sceneKind === "villa" && a.roomId && a.roomId !== avz.selectedRoomId) {
          avz.selectedRoomId = a.roomId;
          renderVillaRoomScheduleList();
          renderRightSideUpCadSvg();
        }
      } else if (avz.camTargetPos) {
        // Smooth glide to clicked room
        const k = Math.min(1, dt * 6.5);
        avz.camPos.x += (avz.camTargetPos.x - avz.camPos.x) * k;
        avz.camPos.y += (avz.camTargetPos.y - avz.camPos.y) * k;
        avz.camPos.z += (avz.camTargetPos.z - avz.camPos.z) * k;
        if (Math.hypot(avz.camTargetPos.x - avz.camPos.x, avz.camTargetPos.z - avz.camPos.z) < 0.08) avz.camTargetPos = null;
      }

      // WASD / Arrow smooth first-person movement
      const speed = (avz.keys.shift ? 11.5 : 5.6) * dt;
      const fwd = (avz.keys.w || avz.keys.arrowup ? 1 : 0) - (avz.keys.s || avz.keys.arrowdown ? 1 : 0);
      const str = (avz.keys.d || avz.keys.arrowright ? 1 : 0) - (avz.keys.a || avz.keys.arrowleft ? 1 : 0);
      if (fwd !== 0 || str !== 0) {
        avz.autoWalkActive = false;
        avz.camTargetPos = null;
        const sinY = Math.sin(avz.yaw), cosY = Math.cos(avz.yaw);
        avz.camPos.x += (-sinY * fwd + cosY * str) * speed;
        avz.camPos.z += (-cosY * fwd - sinY * str) * speed;
      }

      if (avz.camStyle === "fpv") {
        avz.camera.position.set(avz.camPos.x, avz.camPos.y, avz.camPos.z);
        const lookX = avz.camPos.x - Math.sin(avz.yaw) * Math.cos(avz.pitch) * 10;
        const lookY = avz.camPos.y + Math.sin(avz.pitch) * 10;
        const lookZ = avz.camPos.z - Math.cos(avz.yaw) * Math.cos(avz.pitch) * 10;
        avz.camera.lookAt(lookX, lookY, lookZ);
      } else {
        const cx = avz.orbitTarget.x + Math.sin(avz.orbitYaw) * Math.cos(avz.orbitPitch) * avz.orbitDist;
        const cy = avz.orbitTarget.y + Math.sin(avz.orbitPitch) * avz.orbitDist;
        const cz = avz.orbitTarget.z + Math.cos(avz.orbitYaw) * Math.cos(avz.orbitPitch) * avz.orbitDist;
        avz.camera.position.set(cx, cy, cz);
        avz.camera.lookAt(avz.orbitTarget.x, avz.orbitTarget.y, avz.orbitTarget.z);
      }

      avz.renderer.render(avz.scene, avz.camera);
      if (avz.sceneKind === "villa") updateCadLiveCameraCone();
      avz.rafId = requestAnimationFrame(tick);
    };
    avz.rafId = requestAnimationFrame(tick);
  }

  let __avzBound = false;
  function bindArchvizControlsOnce(canvas) {
    if (__avzBound) return;
    __avzBound = true;

    canvas.addEventListener("pointerdown", (e) => {
      avz.dragging = true;
      avz.lastMX = e.clientX;
      avz.lastMY = e.clientY;
      canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!avz.dragging) return;
      const dx = e.clientX - avz.lastMX, dy = e.clientY - avz.lastMY;
      avz.lastMX = e.clientX; avz.lastMY = e.clientY;
      if (avz.camStyle === "fpv") {
        avz.yaw -= dx * 0.0055;
        avz.pitch = Math.max(-1.1, Math.min(1.1, avz.pitch - dy * 0.0045));
      } else {
        avz.orbitYaw -= dx * 0.007;
        avz.orbitPitch = Math.max(0.18, Math.min(1.38, avz.orbitPitch + dy * 0.006));
      }
    });
    canvas.addEventListener("pointerup", () => { avz.dragging = false; });
    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      if (avz.camStyle === "fpv") {
        const step = e.deltaY < 0 ? 1.8 : -1.8;
        avz.camPos.x += -Math.sin(avz.yaw) * step;
        avz.camPos.z += -Math.cos(avz.yaw) * step;
      } else {
        avz.orbitDist = Math.max(10, Math.min(120, avz.orbitDist * (e.deltaY < 0 ? 0.90 : 1.11)));
      }
    }, { passive: false });

    window.addEventListener("keydown", (e) => {
      if (!avz.open) return;
      const tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : "";
      if (tag === "input" || tag === "select" || tag === "textarea") return;
      const k = e.key.toLowerCase();
      avz.keys[k] = true;
      if (k === "e" && avz.sceneKind === "street" && avz.streetPortalPos) {
        openVillaInteriorModal(avz.streetPortalPos.defaultTypology);
      }
    });
    window.addEventListener("keyup", (e) => {
      avz.keys[e.key.toLowerCase()] = false;
    });
  }

  // ---------------- PUBLIC LAUNCHERS FOR STREET & VILLA STUDIO ----------------
  function openUnrealStreetWalk(stopIdx = 0) {
    if (!wtState.active) {
      enterSocietyWalkthrough("PRJ-D19", "street");
      return;
    }
    if (!ensureArchvizRenderer()) return;
    const soc = getSocietyData(wtState.projectId);
    if (!soc) return;
    wtState.mode = "street";
    wtState.stopIndex = ((stopIdx % soc.street_tour.length) + soc.street_tour.length) % soc.street_tour.length;
    updateTopModeButtons("street");

    avz.open = true;
    avz.sceneKind = "street";
    avz.autoWalkActive = false;
    const modal = document.getElementById("archvizStudioModal");
    modal.style.display = "flex";
    modal.classList.add("street-full-mode");
    modal.classList.remove("villa-split-mode", "villa-full3d");

    buildArchvizStreetScene();
    refreshArchvizHeaderAndHud();
    startArchvizLoop();
  }
  window.openUnrealStreetWalk = openUnrealStreetWalk;

  function openUnrealStreetWalkForZone(zoneId) {
    const soc = getSocietyData(wtState.projectId || "PRJ-D19");
    if (!soc) return;
    const idx = (soc.street_tour || []).findIndex(s => s.zone_id === zoneId);
    openUnrealStreetWalk(idx >= 0 ? idx : 0);
  }
  window.openUnrealStreetWalkForZone = openUnrealStreetWalkForZone;

  function openVillaInteriorModal(typologyId) {
    if (!ensureArchvizRenderer()) return;
    const allTyps = (DATA.walkthroughs && DATA.walkthroughs.typologies) || {};
    const typ = allTyps[typologyId] || Object.values(allTyps)[0];
    if (!typ) return;

    wtState.mode = "villa";
    updateTopModeButtons("villa");

    avz.open = true;
    avz.sceneKind = "villa";
    avz.typologyId = typ.id;
    const gFl = typ.floors.find(f => f.level === "G") || typ.floors[0];
    avz.floorKey = gFl.level;
    avz.camStyle = "fpv";
    avz.exploded = false;
    avz.autoWalkActive = false;

    // Start standing at the rear entrance threshold of the Grand Salon looking straight North (-Z) across the Designer Lounge, Dining Chandelier & Infinity Pool to the Lagoon!
    const startR = gFl.rooms.find(r => r.type === "living") || gFl.rooms[0];
    avz.selectedRoomId = startR.id;
    avz.camPos = {
      x: (startR.x + startR.w * 0.5) - typ.plot_w * 0.5,
      y: gFl.elevation_m + 1.68,
      z: typ.plot_d * 0.5 - (startR.z + startR.d * 0.14)
    };
    avz.yaw = 0.0;
    avz.pitch = -0.025;
    const diag = Math.hypot(typ.plot_w, typ.plot_d);
    avz.orbitDist = Math.max(36, diag * 0.90);
    avz.orbitTarget = { x: 0, y: 1.6, z: -2.0 };
    avz.orbitYaw = -0.52;
    avz.orbitPitch = 0.56;

    const modal = document.getElementById("archvizStudioModal");
    modal.style.display = "flex";
    modal.classList.remove("street-full-mode");
    modal.classList.add("villa-split-mode");
    modal.classList.toggle("villa-full3d", avz.fullscreen3D);

    buildArchvizVillaScene();
    refreshArchvizHeaderAndHud();
    renderRightSideUpCadSvg();
    renderVillaRoomScheduleList();
    startArchvizLoop();
  }
  window.openVillaInteriorModal = openVillaInteriorModal;

  function openCurrentSocietyVillaModal() {
    const soc = getSocietyData(wtState.projectId || "PRJ-D19");
    const z = soc ? ((soc.zones || []).find(x => x.zone_id === wtState.selectedZoneId) || soc.zones[0]) : null;
    openVillaInteriorModal(z ? z.default_typology_id : "TYP-TAG-SERENITY-6BR");
  }
  window.openCurrentSocietyVillaModal = openCurrentSocietyVillaModal;

  function closeArchvizStudioModal(returnToZones = true) {
    avz.open = false;
    avz.autoWalkActive = false;
    if (avz.rafId) { cancelAnimationFrame(avz.rafId); avz.rafId = null; }
    const modal = document.getElementById("archvizStudioModal");
    if (modal) modal.style.display = "none";
    if (returnToZones && wtState.active) {
      wtState.mode = "zones";
      updateTopModeButtons("zones");
    }
  }
  window.closeArchvizStudioModal = closeArchvizStudioModal;
  window.closeVillaInteriorModal = () => closeArchvizStudioModal(true);

  function setArchvizCamStyle(style) {
    avz.camStyle = style;
    avz.autoWalkActive = false;
    if (avz.sceneKind === "villa") {
      const typ = DATA.walkthroughs.typologies[avz.typologyId];
      if (typ && style !== "fpv") {
        const diag = Math.hypot(typ.plot_w, typ.plot_d);
        avz.orbitDist = Math.max(36, diag * (style === "cutaway" ? 0.86 : 0.96));
        avz.orbitTarget = { x: 0, y: style === "cutaway" ? 1.2 : 3.2, z: -2.0 };
        avz.orbitPitch = style === "cutaway" ? 0.62 : 0.48;
      }
      buildArchvizVillaScene();
    } else if (style !== "fpv") {
      avz.orbitTarget = { x: 0, y: 2.5, z: -18 };
      avz.orbitDist = 52;
      avz.orbitPitch = 0.50;
    }
    refreshArchvizHeaderAndHud();
  }
  window.setArchvizCamStyle = setArchvizCamStyle;

  function toggleArchvizExploded() {
    avz.camStyle = "dollhouse";
    avz.exploded = !avz.exploded;
    const typ = DATA.walkthroughs.typologies[avz.typologyId];
    const diag = typ ? Math.hypot(typ.plot_w, typ.plot_d) : 50;
    avz.orbitDist = avz.exploded ? Math.max(54, diag * 1.12) : Math.max(38, diag * 0.94);
    avz.orbitTarget = { x: 0, y: avz.exploded ? 8.5 : 3.2, z: -1.5 };
    avz.orbitPitch = avz.exploded ? 0.44 : 0.52;
    avz.orbitYaw = -0.58;
    buildArchvizVillaScene();
    refreshArchvizHeaderAndHud();
  }
  window.toggleArchvizExploded = toggleArchvizExploded;

  function toggleArchvizAutoTour() {
    avz.autoWalkActive = !avz.autoWalkActive;
    if (avz.autoWalkActive) avz.camStyle = "fpv";
    refreshArchvizHeaderAndHud();
  }
  window.toggleArchvizAutoTour = toggleArchvizAutoTour;

  function toggleArchvizFullscreen3D() {
    avz.fullscreen3D = !avz.fullscreen3D;
    document.getElementById("archvizStudioModal")?.classList.toggle("villa-full3d", avz.fullscreen3D);
    refreshArchvizHeaderAndHud();
  }
  window.toggleArchvizFullscreen3D = toggleArchvizFullscreen3D;

  function setCadVisualStyle(st) {
    avz.cadStyle = st;
    renderRightSideUpCadSvg();
    refreshArchvizHeaderAndHud();
  }
  window.setCadVisualStyle = setCadVisualStyle;

  function selectVillaFloorInArchviz(fLevel) {
    avz.floorKey = fLevel;
    avz.autoWalkActive = false;
    const typ = DATA.walkthroughs.typologies[avz.typologyId];
    if (typ) {
      const fl = typ.floors.find(f => f.level === fLevel) || typ.floors[0];
      const r0 = fl.rooms.find(r => r.type === "master") || fl.rooms.find(r => r.type === "living") || fl.rooms[0];
      if (r0) {
        avz.selectedRoomId = r0.id;
        const isBed = (r0.type === "master" || r0.type === "bedroom");
        avz.camPos = {
          x: (r0.x + r0.w * (isBed ? 0.78 : 0.50)) - typ.plot_w * 0.5,
          y: (avz.camStyle === "cutaway" ? 0 : fl.elevation_m) + 1.68,
          z: typ.plot_d * 0.5 - (r0.z + r0.d * 0.14)
        };
        avz.yaw = isBed ? 0.56 : 0;
      }
    }
    buildArchvizVillaScene();
    refreshArchvizHeaderAndHud();
    renderRightSideUpCadSvg();
    renderVillaRoomScheduleList();
  }
  window.selectVillaFloorInArchviz = selectVillaFloorInArchviz;

  function teleportVillaRoom(roomId) {
    const typ = DATA.walkthroughs.typologies[avz.typologyId];
    if (!typ) return;
    const fl = typ.floors.find(f => f.level === avz.floorKey) || typ.floors[0];
    const r = fl.rooms.find(x => x.id === roomId);
    if (!r) return;
    avz.autoWalkActive = false;
    avz.selectedRoomId = r.id;
    const isBed = (r.type === "master" || r.type === "bedroom");
    avz.camTargetPos = {
      x: (r.x + r.w * (isBed ? 0.78 : 0.50)) - typ.plot_w * 0.5,
      y: (avz.camStyle === "cutaway" ? 0 : fl.elevation_m) + 1.68,
      z: typ.plot_d * 0.5 - (r.z + r.d * 0.14)
    };
    avz.yaw = isBed ? 0.56 : 0.0; // Angle 32-deg NW in bedrooms so King Bed + Sea View both frame cleanly!
    if (avz.camStyle === "fpv") {
      avz.pitch = -0.025;
    }
    renderRightSideUpCadSvg();
    renderVillaRoomScheduleList();
  }
  window.teleportVillaRoom = teleportVillaRoom;

  function stepArchvizPad(fwd, turn) {
    avz.autoWalkActive = false;
    avz.yaw += turn * 0.24;
    if (fwd !== 0) {
      avz.camPos.x += -Math.sin(avz.yaw) * fwd * 2.8;
      avz.camPos.z += -Math.cos(avz.yaw) * fwd * 2.8;
    }
  }
  window.stepArchvizPad = stepArchvizPad;

  function refreshArchvizHeaderAndHud() {
    const topControls = document.getElementById("avzModeSpecificTop");
    const streetHud = document.getElementById("avzStreetBottomHud");
    const metaStrip = document.getElementById("avzMetaStrip");
    if (!topControls || !metaStrip) return;

    if (avz.sceneKind === "street") {
      const soc = getSocietyData(wtState.projectId || "PRJ-D19");
      const st = soc.street_tour[wtState.stopIndex] || soc.street_tour[0];
      const z = (soc.zones || []).find(x => x.zone_id === st.zone_id) || soc.zones[0];

      topControls.innerHTML = `
        <span style="background:linear-gradient(135deg,#10b981,#0284c7); color:#fff; font-size:0.69rem; font-weight:900; padding:5px 11px; border-radius:999px;">🚶 UNREAL 3D STREET WALK · 1.70m EYE LEVEL</span>
        <button type="button" class="vim-floor-btn ${avz.camStyle === 'fpv' ? 'active' : ''}" onclick="setArchvizCamStyle('fpv')">👁️ First-Person Walk</button>
        <button type="button" class="vim-floor-btn ${avz.camStyle === 'dollhouse' ? 'active' : ''}" onclick="setArchvizCamStyle('dollhouse')">🚁 Drone Boulevard Orbit</button>
        <button type="button" class="wt-btn primary" onclick="toggleArchvizAutoTour()">${avz.autoWalkActive ? "⏸ Pause Boulevard Walk" : "▶ Auto-Walk Boulevard"}</button>
        <button type="button" class="wt-btn inside-cta" onclick="openVillaInteriorModal('${z ? z.default_typology_id : 'TYP-TAG-SERENITY-6BR'}')">🚪 Walk Inside Villa (3D + CAD) →</button>
      `;

      metaStrip.innerHTML = `
        <div><strong>📍 ${soc.name}</strong> · <span style="color:#38bdf8; font-weight:800;">Stop ${st.stop}/${soc.street_tour.length}: ${st.title}</span> (${st.street})</div>
        <div>🏗️ <strong>Contractor:</strong> <strong style="color:#34d399;">${z ? z.main_contractor : soc.developer}</strong> (${z ? z.contract_value : ""}) · 📐 <strong>Architect:</strong> ${z ? z.architects : ""}</div>
      `;

      if (streetHud) {
        streetHud.style.display = "block";
        streetHud.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:7px;">
            <div>
              <span style="background:#10b981; color:#022c22; font-weight:900; font-size:0.67rem; padding:2px 8px; border-radius:999px;">LIVE ENCLAVE</span>
              <strong style="font-size:0.88rem; margin-left:6px;">${st.title}</strong>
              <span style="font-size:0.74rem; color:#cbd5e1; margin-left:6px;">— ${st.note}</span>
            </div>
            <div style="display:flex; gap:5px;">
              <button type="button" class="wt-btn" onclick="openUnrealStreetWalk(${wtState.stopIndex - 1})">⏮ Prev Street</button>
              <button type="button" class="wt-btn" onclick="openUnrealStreetWalk(${wtState.stopIndex + 1})">Next Street ⏭</button>
              <button type="button" class="wt-btn inside-cta" onclick="openVillaInteriorModal('${z ? z.default_typology_id : 'TYP-TAG-SERENITY-6BR'}')">🚪 Enter Villa Gate [E] →</button>
            </div>
          </div>
          <div style="display:flex; gap:5px; flex-wrap:wrap; align-items:center;">
            <span style="font-size:0.68rem; color:#94a3b8;">Teleport Street / Frond:</span>
            ${soc.street_tour.map((s, idx) => {
              const w = s.title.split(" ");
              const lbl = (w[0] === "Frond" && w[1]) ? `${w[0]} ${w[1]}` : w[0];
              return `<button type="button" class="wt-stop-dot ${idx === wtState.stopIndex ? 'active' : ''}" onclick="openUnrealStreetWalk(${idx})">${s.stop}. ${lbl}</button>`;
            }).join("")}
          </div>
        `;
      }
    } else {
      if (streetHud) streetHud.style.display = "none";
      const allTyps = DATA.walkthroughs.typologies || {};
      const typ = allTyps[avz.typologyId];

      topControls.innerHTML = `
        <select onchange="openVillaInteriorModal(this.value)" style="background:#0f172a; color:#f8fafc; border:1px solid #38bdf8; border-radius:8px; padding:5px 9px; font-size:0.76rem; font-weight:700; max-width:340px;">
          ${Object.values(allTyps).map(t => `<option value="${t.id}" ${t.id === typ.id ? "selected" : ""}>${t.project_id === "PRJ-D2" ? "🌴 PJA" : "🌊 TAG"} · ${t.title} (${t.bua_sqft})</option>`).join("")}
        </select>
        <div class="vim-floor-pills">
          <button type="button" class="vim-floor-btn ${avz.camStyle === 'fpv' ? 'active' : ''}" onclick="setArchvizCamStyle('fpv')">👁️ First-Person Walk</button>
          <button type="button" class="vim-floor-btn ${avz.camStyle === 'cutaway' ? 'active' : ''}" onclick="setArchvizCamStyle('cutaway')">🔪 3D Cutaway</button>
          <button type="button" class="vim-floor-btn ${avz.camStyle === 'dollhouse' && !avz.exploded ? 'active' : ''}" onclick="avz.exploded=false; setArchvizCamStyle('dollhouse')">🏠 Full 3D Villa</button>
          <button type="button" class="vim-floor-btn ${avz.camStyle === 'dollhouse' && avz.exploded ? 'active' : ''}" onclick="toggleArchvizExploded()">↕ Explode Floors</button>
        </div>
        <div class="vim-floor-pills">
          ${typ.floors.map(fl => `<button type="button" class="vim-floor-btn ${avz.floorKey === fl.level ? 'active' : ''}" onclick="selectVillaFloorInArchviz('${fl.level}')">${fl.level}</button>`).join("")}
        </div>
        <button type="button" class="wt-btn primary" onclick="toggleArchvizAutoTour()">${avz.autoWalkActive ? "⏸ Pause Tour" : "▶ Room-by-Room Tour"}</button>
        <button type="button" class="wt-btn" onclick="toggleArchvizFullscreen3D()">${avz.fullscreen3D ? "◫ Show Floor Plan" : "⛶ Fullscreen 3D"}</button>
        <button type="button" class="wt-btn" onclick="openUnrealStreetWalk(wtState.stopIndex || 0)">🚶 ← Outside Street</button>
      `;

      metaStrip.innerHTML = `
        <div>🏗️ <strong>Contractor:</strong> <strong style="color:#34d399;">${typ.contractor}</strong> · 📐 <strong>Architect:</strong> <strong style="color:#38bdf8;">${typ.architect}</strong> · 📏 <strong>BUA:</strong> ${typ.bua_sqft} · <strong>Plot:</strong> ${typ.plot_w}m × ${typ.plot_d}m</div>
        <div style="display:flex; gap:6px; align-items:center;">
          <button type="button" class="wt-stop-dot ${avz.cadStyle === 'brochure' ? 'active' : ''}" onclick="setCadVisualStyle('brochure')">🎨 Brochure Plan</button>
          <button type="button" class="wt-stop-dot ${avz.cadStyle === 'cad' ? 'active' : ''}" onclick="setCadVisualStyle('cad')">📐 CAD Blueprint</button>
        </div>
      `;
    }
  }

  function renderVillaRoomScheduleList() {
    const box = document.getElementById("archvizRoomSchedule");
    if (!box) return;
    const typ = DATA.walkthroughs.typologies[avz.typologyId];
    if (!typ) return;
    const fl = typ.floors.find(f => f.level === avz.floorKey) || typ.floors[0];
    const sel = fl.rooms.find(r => r.id === avz.selectedRoomId) || fl.rooms[0];

    box.innerHTML = `
      ${sel ? `
        <div style="background:#0f172a; color:#f8fafc; border-radius:9px; padding:8px 11px; margin-bottom:8px; border-left:4px solid #10b981;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:0.80rem; color:#34d399;">📍 Standing In: ${sel.name} (${fl.level})</strong>
            <span style="background:#0284c7; color:#fff; font-size:0.67rem; font-weight:800; padding:2px 7px; border-radius:999px;">${(sel.w * sel.d).toFixed(1)} m² · ${Math.round(sel.w * sel.d * 10.7639)} sq.ft.</span>
          </div>
          <div style="font-size:0.71rem; color:#cbd5e1; margin-top:3px;">${sel.w.toFixed(1)}m × ${sel.d.toFixed(1)}m × ${fl.height_m.toFixed(1)}m H · Spec: <strong style="color:#f8fafc;">${sel.spec}</strong></div>
        </div>
      ` : ""}
      <div style="font-size:0.70rem; font-weight:800; color:#334155; text-transform:uppercase; margin-bottom:5px;">Click Any Room to Walk Camera Inside (${fl.rooms.length} Spaces):</div>
      ${fl.rooms.map(r => `
        <div class="vim-room-chip ${r.id === avz.selectedRoomId ? 'active' : ''}" onclick="teleportVillaRoom('${r.id}')">
          <div>
            <strong style="color:#0f172a;">${r.name}</strong>
            <div style="font-size:0.67rem; color:#64748b;">${r.spec}</div>
          </div>
          <div style="text-align:right; white-space:nowrap;">
            <strong style="color:#0369a1;">${Math.round(r.w * r.d * 10.7639)} sq.ft.</strong>
            <div style="font-size:0.66rem; color:#64748b;">${r.w.toFixed(1)}×${r.d.toFixed(1)}m</div>
          </div>
        </div>
      `).join("")}
    `;
  }
})();
