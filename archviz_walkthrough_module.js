// ============================================================================
// V3.0 UNREAL / BLENDER-GRADE THREE.JS r170 HDR POST-FX & PLANAR REFLECTION
// ARCHVIZ ENGINE + EFFORTLESS 3-STEP NAVIGATION + RIGHT-SIDE-UP CAD STUDIO
// Powers PRJ-D2 (Palm Jebel Ali) & PRJ-D19 (Tilal Al Ghaf) End-to-End Tours
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

    // Singleton WebGLRenderer, HDR Post-Processing & Planar Reflection RTs
    renderer: null,
    post: null,
    reflectRT: null,
    reflCam: null,
    clipPlane: null,
    reflectPlaneY: 0.10,
    reflectiveMeshes: [],
    waterUniforms: null,
    floorReflectUniforms: null,

    scene: null,
    camera: null,
    pmremGen: null,
    envRT: null,
    mats: null,
    geoCache: new Map(),
    skyMesh: null,
    sunLight: null,
    hemiLight: null,
    fillLight: null,
    swayCrowns: [],
    interiorLights: [],
    worldPins: [],
    streetPortalPos: null,
    cursorRing: null,
    walkSurfaceY: 0.08,
    walkBounds: { minX: -7.5, maxX: 7.5, minZ: -125, maxZ: 40 },

    // Smooth Velocity-Damped Camera & Orbit State
    camPos: { x: 0, y: 1.65, z: 12 },
    camVel: { x: 0, z: 0 },
    camTargetPos: null,
    camTargetYaw: null,
    yaw: 0, // 0 = looking North (-Z, toward Lagoon/Sea)
    pitch: -0.02,
    orbitYaw: -0.55,
    orbitPitch: 0.56,
    orbitDist: 38,
    orbitTarget: { x: 0, y: 1.4, z: 0 },

    keys: {},
    dragging: false,
    dragDist: 0,
    downX: 0,
    downY: 0,
    lastMX: 0,
    lastMY: 0,
    hoverNdc: { x: 0, y: -0.25, active: false },
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
          if (fr.zone_id) selectSocietyZone(fr.zone_id, false);
          wtFlyMapCamera(fr.pts[1][0], fr.pts[1][1], 16.3, 62, -25, 850);
        };
        wtState.domMarkers.push(new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([tip[1], tip[0]]).addTo(map3d));
      });
    }

    if (typeof L !== "undefined" && typeof map !== "undefined" && map) {
      const lg = L.layerGroup();
      (soc.zones || []).forEach(z => {
        if (!z.polygon || z.polygon.length < 3) return;
        const poly = L.polygon(z.polygon, {
          color: z.zone_id === wtState.selectedZoneId ? "#ffffff" : (z.color || "#10b981"),
          weight: z.zone_id === wtState.selectedZoneId ? 3 : 1.8,
          fillColor: z.color || "#10b981",
          fillOpacity: z.zone_id === wtState.selectedZoneId ? 0.34 : 0.16
        });
        poly.on("click", () => selectSocietyZone(z.zone_id, true));
        lg.addLayer(poly);
      });
      lg.addTo(map);
      wtState.leafletGroup = lg;
    }
  }

  function syncThreeSocietyWalkGroup() {
    if (typeof three3DLayer === "undefined" || !three3DLayer || !three3DLayer.scene || typeof THREE === "undefined") return;
    if (three3DLayer.societyWalkGroup) {
      if (typeof disposeThreeGroup === "function") disposeThreeGroup(three3DLayer.societyWalkGroup, true);
      three3DLayer.scene.remove(three3DLayer.societyWalkGroup);
      three3DLayer.societyWalkGroup = null;
      wtState.roverMesh = null;
    }
    if (!wtState.active || !wtState.projectId) return;
    const soc = getSocietyData(wtState.projectId);
    if (!soc || typeof createSiteAnchoredGroup !== "function") return;

    const cLat = soc.center[0], cLon = soc.center[1];
    const mPerDegLat = 111132.92;
    const mPerDegLon = 111412.84 * Math.cos((cLat * Math.PI) / 180);
    const toXZ = (lat, lon) => [(lon - cLon) * mPerDegLon, -(lat - cLat) * mPerDegLat];

    const grp = createSiteAnchoredGroup(cLon, cLat);
    const matBody = new THREE.MeshStandardMaterial({ color: 0xf5f0e6, roughness: 0.45, metalness: 0.08 });
    const matUpper = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.38, metalness: 0.12 });
    const matGlass = new THREE.MeshStandardMaterial({ color: 0x38bdf8, roughness: 0.14, metalness: 0.72, transparent: true, opacity: 0.76 });
    const matPool = new THREE.MeshStandardMaterial({ color: 0x06b6d4, roughness: 0.16, metalness: 0.25 });
    const matTree = new THREE.MeshStandardMaterial({ color: 0x15803d, roughness: 0.78 });
    const matTrunk = new THREE.MeshStandardMaterial({ color: 0x78350f, roughness: 0.88 });

    (soc.osm_buildings || []).forEach((b, idx) => {
      if (!b.pts || b.pts.length < 3) return;
      let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
      b.pts.forEach(p => {
        const [x, z] = toXZ(p[0], p[1]);
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (z < minZ) minZ = z; if (z > maxZ) maxZ = z;
      });
      const w = Math.clamp ? Math.max(6, Math.min(85, maxX - minX)) : Math.max(6, Math.min(85, maxX - minX));
      const d = Math.max(6, Math.min(85, maxZ - minZ));
      const cx = (minX + maxX) * 0.5, cz = (minZ + maxZ) * 0.5;
      const h = b.h || 8.5;
      const base = new THREE.Mesh(new THREE.BoxGeometry(w, h * 0.58, d), matBody);
      base.position.set(cx, h * 0.29, cz);
      grp.add(base);
      const top = new THREE.Mesh(new THREE.BoxGeometry(w * 0.82, h * 0.42, d * 0.80), idx % 3 === 0 ? matGlass : matUpper);
      top.position.set(cx + (idx % 2 ? 0.6 : -0.6), h * 0.79, cz);
      grp.add(top);
    });

    (soc.procedural_villas || []).forEach((v, idx) => {
      const [vx, vz] = toXZ(v.lat, v.lon);
      const h = v.h || 10.5, w = v.w || 14, d = v.d || 18;
      const vGrp = new THREE.Group();
      vGrp.position.set(vx, 0, vz);
      vGrp.rotation.y = ((v.angle || 0) * Math.PI) / 180;
      const gf = new THREE.Mesh(new THREE.BoxGeometry(w, h * 0.48, d * 0.72), matBody);
      gf.position.set(0, h * 0.24, -d * 0.06);
      vGrp.add(gf);
      const f1 = new THREE.Mesh(new THREE.BoxGeometry(w * 0.88, h * 0.40, d * 0.58), matUpper);
      f1.position.set(w * 0.05, h * 0.68, -d * 0.04);
      vGrp.add(f1);
      const pool = new THREE.Mesh(new THREE.BoxGeometry(w * 0.68, 0.35, d * 0.24), matPool);
      pool.position.set(0, 0.2, d * 0.36);
      vGrp.add(pool);
      if (idx % 2 === 0) {
        const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.32, 5.2, 6), matTrunk);
        tr.position.set(-w * 0.45, 2.6, d * 0.32);
        vGrp.add(tr);
        const cr = new THREE.Mesh(new THREE.DodecahedronGeometry(2.0, 0), matTree);
        cr.scale.set(1.2, 0.55, 1.2);
        cr.position.set(-w * 0.45, 5.4, d * 0.32);
        vGrp.add(cr);
      }
      grp.add(vGrp);
    });

    three3DLayer.societyWalkGroup = grp;
    three3DLayer.scene.add(grp);
    if (map3d) map3d.triggerRepaint();
  }
  window.syncThreeSocietyWalkGroup = syncThreeSocietyWalkGroup;

  function wtFlyMapCamera(lat, lon, zoom, pitch, bearing, durationMs = 900) {
    if (typeof currentCameraDim !== "undefined" && currentCameraDim === "2D" && typeof setCameraDimension === "function" && typeof map3dContextLost !== "undefined" && !map3dContextLost) {
      setCameraDimension("3D");
    }
    if (typeof map3d !== "undefined" && map3d && map3dLoaded && !map3dContextLost) {
      map3d.easeTo({ center: [lon, lat], zoom, pitch, bearing, duration: durationMs, essential: true });
    }
    if (typeof map !== "undefined" && map) {
      map.setView([lat, lon], Math.min(18, Math.round(zoom)), { animate: false });
    }
  }

  function enterSocietyWalkthrough(pid, initialMode = "zones") {
    const soc = getSocietyData(pid);
    if (!soc) return;
    if (typeof closeAnalyticalWorkspace === "function") closeAnalyticalWorkspace();

    wtState.active = true;
    wtState.projectId = pid;
    wtState.selectedZoneId = soc.zones && soc.zones.length ? soc.zones[0].zone_id : null;
    wtState.stopIndex = 0;
    selected3DProjectId = pid;

    document.body.classList.add("wt-society-active");
    const tb = document.getElementById("wtTopBanner");
    if (tb) tb.style.display = "flex";
    document.getElementById("wtSwitchD2")?.classList.toggle("active", pid === "PRJ-D2");
    document.getElementById("wtSwitchD19")?.classList.toggle("active", pid === "PRJ-D19");

    const bldgCount = (soc.osm_buildings ? soc.osm_buildings.length : 0) + (soc.procedural_villas ? soc.procedural_villas.length : 0);
    const chip = document.getElementById("wtTopStatsChip");
    if (chip) chip.textContent = `${soc.zones.length} Enclaves · ${bldgCount.toLocaleString()} 3D Villas`;
    const hud = document.getElementById("hudScope");
    if (hud) hud.textContent = `Walkthrough: ${soc.name}`;

    if (typeof switchDrawerTab === "function") switchDrawerTab("insp");
    if (typeof rebuildThreeHeroScene === "function") rebuildThreeHeroScene();
    if (typeof sync3DMapLayers === "function") sync3DMapLayers();
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
    if (typeof sync3DMapLayers === "function") sync3DMapLayers();
    if (flyOverview) {
      if (typeof flyBothMaps === "function") flyBothMaps(25.095, 55.165, 11.2, 50, 20);
      if (typeof showProjectInspector === "function") showProjectInspector(prevPid, false);
    }
  }
  window.exitSocietyWalkthrough = exitSocietyWalkthrough;

  function updateTopModeButtons(m) {
    document.getElementById("wtModeZonesBtn")?.classList.toggle("active", m === "zones");
    document.getElementById("wtModeStreetBtn")?.classList.toggle("active", m === "street");
    document.getElementById("wtModeInsideBtn")?.classList.toggle("active", m === "villa");
  }

  function setSocietyWalkMode(mode) {
    if (!wtState.active) {
      enterSocietyWalkthrough("PRJ-D19", mode);
      return;
    }
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
            <button type="button" onclick="event.stopPropagation(); selectSocietyZone('${z.zone_id}', false); openUnrealStreetWalkForZone('${z.zone_id}')" style="background:#059669; color:#fff; border:none; border-radius:6px; padding:4px 9px; font-size:0.68rem; font-weight:700; cursor:pointer;">② 🚶 Walk Street</button>
            <button type="button" onclick="event.stopPropagation(); openVillaInteriorModal('${z.default_typology_id}')" style="background:#0f172a; color:#fff; border:none; border-radius:6px; padding:4px 9px; font-size:0.68rem; font-weight:700; cursor:pointer;">③ 🏠 Inside Villa →</button>
          </div>
        </div>
      `;
    }).join("");

    const frondTableHtml = (soc.fronds && soc.fronds.length) ? `
      <div class="prof-sec-hdr" style="margin-top:10px;"><span>🌴 All 16 Fronds (A–P) Contractor Directory</span><span>Click Frond</span></div>
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
        <div style="background:linear-gradient(135deg,#090d16 0%,#064e3b 100%); color:#fff; border-radius:12px; padding:12px; margin-bottom:10px; border:1px solid #10b981;">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px; margin-bottom:4px;">
            <span style="background:#10b981; color:#022c22; font-size:0.64rem; font-weight:900; padding:2px 8px; border-radius:999px;">3-STEP ARCHVIZ DIGITAL TWIN</span>
            <button type="button" onclick="showProjectInspector('${soc.project_id}', false)" style="background:rgba(255,255,255,0.14); color:#e2e8f0; border:1px solid rgba(255,255,255,0.28); border-radius:999px; padding:2px 8px; font-size:0.66rem; font-weight:700; cursor:pointer;">📋 5-Sec GIS Profile</button>
          </div>
          <h3 style="margin:4px 0 2px; font-size:1.02rem; color:#fff;">${soc.name} (${soc.project_id})</h3>
          <div style="font-size:0.73rem; color:#a7f3d0; font-weight:600;">${soc.developer} · ${soc.area_summary}</div>
          <div style="font-size:0.71rem; color:#cbd5e1; margin-top:4px;">Awards / GDV: <strong>${soc.headline_gdv}</strong></div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:7px; margin-top:10px;">
            <button type="button" onclick="openUnrealStreetWalk(0)" style="background:#10b981; color:#022c22; border:none; border-radius:8px; padding:8px; font-size:0.73rem; font-weight:900; cursor:pointer;">② 🚶 Walk Streets (3D)</button>
            <button type="button" onclick="openVillaInteriorModal('${selZ ? selZ.default_typology_id : typologiesForProj[0].id}')" style="background:#38bdf8; color:#082f49; border:none; border-radius:8px; padding:8px; font-size:0.73rem; font-weight:900; cursor:pointer;">③ 🏠 Walk Inside Villa</button>
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
              • <strong>Source Basis:</strong> <span style="color:#64748b;">${selZ.source_note}</span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:8px;">
              <button type="button" onclick="openUnrealStreetWalkForZone('${selZ.zone_id}')" style="background:#059669; color:#fff; border:none; border-radius:8px; padding:8px; font-size:0.73rem; font-weight:800; cursor:pointer;">🚶 Walk ${selZ.short_label} Street</button>
              <button type="button" onclick="openVillaInteriorModal('${selZ.default_typology_id}')" style="background:linear-gradient(135deg,#0284c7,#2563eb); color:#fff; border:none; border-radius:8px; padding:8px; font-size:0.73rem; font-weight:800; cursor:pointer;">🏠 Step Inside Villa →</button>
            </div>
          </div>
        ` : ""}

        <div class="prof-sec-hdr"><span>🏗️ Villa 3D Interiors &amp; Floor Plans (${typologiesForProj.length})</span><span>Click to Enter</span></div>
        <div style="display:flex; flex-direction:column; gap:5px; margin-bottom:10px;">
          ${typologiesForProj.map(t => `
            <button type="button" onclick="openVillaInteriorModal('${t.id}')" style="display:flex; justify-content:space-between; align-items:center; text-align:left; background:#fff; border:1px solid #cbd5e1; border-radius:8px; padding:7px 9px; cursor:pointer;">
              <div>
                <strong style="font-size:0.74rem; color:#0f172a; display:block;">${t.title}</strong>
                <span style="font-size:0.68rem; color:#475569;">BUA ${t.bua_sqft} · ${t.levels_label} · ${t.contractor.split('(')[0].trim()}</span>
              </div>
              <span style="background:#ecfdf5; color:#047857; font-weight:800; font-size:0.68rem; padding:3px 8px; border-radius:6px;">Enter 3D →</span>
            </button>
          `).join("")}
        </div>
        ${frondTableHtml}
        <div class="prof-sec-hdr"><span>🗺️ All ${soc.zones.length} Contractor Enclaves</span><span>Click Card</span></div>
        ${zoneCardsHtml}
      </div>
    `;
  }
  window.wtFlyCameraFrond = (lat, lon) => wtFlyMapCamera(lat, lon, 16.3, 62, -25, 850);

  // =========================================================================
  // PART 2: PROCEDURAL PBR TEXTURES (ALBEDO + SOBEL NORMAL + ROUGHNESS MAPS)
  // =========================================================================
  function createPbrMaps(size, repX, repY, strength, drawAlbedoAndHeight) {
    const albC = document.createElement("canvas");
    albC.width = size; albC.height = size;
    const actx = albC.getContext("2d");

    const hgtC = document.createElement("canvas");
    hgtC.width = size; hgtC.height = size;
    const hctx = hgtC.getContext("2d");
    hctx.fillStyle = "rgb(128,128,128)";
    hctx.fillRect(0, 0, size, size);

    const rghC = document.createElement("canvas");
    rghC.width = size; rghC.height = size;
    const rctx = rghC.getContext("2d");
    rctx.fillStyle = "rgb(140,140,140)";
    rctx.fillRect(0, 0, size, size);

    drawAlbedoAndHeight(actx, hctx, rctx, size);

    // Convert height canvas to tangent-space NormalMap via wrap-around Sobel filter
    const hData = hctx.getImageData(0, 0, size, size).data;
    const normBytes = new Uint8Array(size * size * 4);
    const mask = size - 1;
    const hAt = (x, y) => hData[(((y & mask) * size) + (x & mask)) * 4] / 255.0;

    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const tl = hAt(x - 1, y - 1), t = hAt(x, y - 1), tr = hAt(x + 1, y - 1);
        const l  = hAt(x - 1, y),                        r  = hAt(x + 1, y);
        const bl = hAt(x - 1, y + 1), b = hAt(x, y + 1), br = hAt(x + 1, y + 1);
        const dX = ((tr + 2 * r + br) - (tl + 2 * l + bl)) * strength;
        const dY = ((bl + 2 * b + br) - (tl + 2 * t + tr)) * strength;
        const invLen = 1.0 / Math.sqrt(dX * dX + dY * dY + 1.0);
        const idx = (y * size + x) * 4;
        normBytes[idx]     = Math.round((-dX * invLen * 0.5 + 0.5) * 255);
        normBytes[idx + 1] = Math.round((-dY * invLen * 0.5 + 0.5) * 255);
        normBytes[idx + 2] = Math.round((invLen * 0.5 + 0.5) * 255);
        normBytes[idx + 3] = 255;
      }
    }

    const map = new THREE.CanvasTexture(albC);
    map.wrapS = map.wrapT = THREE.RepeatWrapping;
    map.repeat.set(repX, repY);
    map.colorSpace = THREE.SRGBColorSpace;
    map.anisotropy = 4;

    const normalMap = new THREE.DataTexture(normBytes, size, size, THREE.RGBAFormat);
    normalMap.wrapS = normalMap.wrapT = THREE.RepeatWrapping;
    normalMap.repeat.set(repX, repY);
    normalMap.needsUpdate = true;

    const roughnessMap = new THREE.CanvasTexture(rghC);
    roughnessMap.wrapS = roughnessMap.wrapT = THREE.RepeatWrapping;
    roughnessMap.repeat.set(repX, repY);

    return { map, normalMap, roughnessMap };
  }

  // =========================================================================
  // PART 3: HDR POST-PROCESSING (DEPTH SSAO + KAWASE BLOOM + ACES FILMIC)
  //         & EXACT REAL-TIME PLANAR MIRROR REFLECTION PASS
  // =========================================================================
  function initPostAndReflectionPipeline() {
    const r = avz.renderer;
    const isWebGL2 = Boolean(r.capabilities && r.capabilities.isWebGL2);
    avz.clipPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    avz.reflCam = new THREE.PerspectiveCamera(48, 1.6, 0.20, 480);

    const rtType = isWebGL2 ? THREE.HalfFloatType : THREE.UnsignedByteType;
    avz.reflectRT = new THREE.WebGLRenderTarget(512, 512, {
      type: rtType,
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      depthBuffer: true
    });

    if (!isWebGL2) {
      avz.post = null;
      return;
    }

    const depthTex = new THREE.DepthTexture(1024, 768, THREE.UnsignedIntType);
    depthTex.format = THREE.DepthFormat;
    const sceneRT = new THREE.WebGLRenderTarget(1024, 768, {
      type: THREE.HalfFloatType,
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      depthBuffer: true,
      depthTexture: depthTex
    });
    const bloomRT1 = new THREE.WebGLRenderTarget(512, 384, {
      type: THREE.HalfFloatType,
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      depthBuffer: false
    });
    const bloomRT2 = new THREE.WebGLRenderTarget(512, 384, {
      type: THREE.HalfFloatType,
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      depthBuffer: false
    });

    const orthoCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const quadGeo = new THREE.PlaneGeometry(2, 2);

    const threshMat = new THREE.ShaderMaterial({
      uniforms: {
        tDiffuse: { value: null },
        uThreshold: { value: 1.05 }
      },
      depthTest: false, depthWrite: false,
      vertexShader: `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
      `,
      fragmentShader: `
        uniform sampler2D tDiffuse;
        uniform float uThreshold;
        varying vec2 vUv;
        void main() {
          vec3 c = texture2D(tDiffuse, vUv).rgb;
          float br = max(c.r, max(c.g, c.b));
          float soft = clamp((br - uThreshold + 0.35) / 0.70, 0.0, 1.0);
          float contrib = max(0.0, br - uThreshold) + soft * soft * 0.28;
          gl_FragColor = vec4(c * (contrib / max(br, 0.0001)), 1.0);
        }
      `
    });

    const blurMat = new THREE.ShaderMaterial({
      uniforms: {
        tDiffuse: { value: null },
        uTexel: { value: new THREE.Vector2(1 / 512, 1 / 384) },
        uOffset: { value: 1.5 }
      },
      depthTest: false, depthWrite: false,
      vertexShader: `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
      `,
      fragmentShader: `
        uniform sampler2D tDiffuse;
        uniform vec2 uTexel;
        uniform float uOffset;
        varying vec2 vUv;
        void main() {
          vec2 d = uTexel * uOffset;
          vec3 s = texture2D(tDiffuse, vUv).rgb * 0.28;
          s += texture2D(tDiffuse, vUv + vec2( d.x,  d.y)).rgb * 0.18;
          s += texture2D(tDiffuse, vUv + vec2(-d.x,  d.y)).rgb * 0.18;
          s += texture2D(tDiffuse, vUv + vec2( d.x, -d.y)).rgb * 0.18;
          s += texture2D(tDiffuse, vUv + vec2(-d.x, -d.y)).rgb * 0.18;
          gl_FragColor = vec4(s, 1.0);
        }
      `
    });

    const compositeMat = new THREE.ShaderMaterial({
      uniforms: {
        tDiffuse: { value: sceneRT.texture },
        tDepth: { value: depthTex },
        tBloom: { value: bloomRT1.texture },
        uRes: { value: new THREE.Vector2(1024, 768) },
        uNear: { value: 0.20 },
        uFar: { value: 480.0 },
        uExposure: { value: 1.05 },
        uBloomStrength: { value: 0.28 },
        uAoStrength: { value: 0.44 }
      },
      depthTest: false, depthWrite: false,
      vertexShader: `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
      `,
      fragmentShader: `
        uniform sampler2D tDiffuse;
        uniform sampler2D tDepth;
        uniform sampler2D tBloom;
        uniform vec2 uRes;
        uniform float uNear;
        uniform float uFar;
        uniform float uExposure;
        uniform float uBloomStrength;
        uniform float uAoStrength;
        varying vec2 vUv;

        float linearDepth(vec2 uv) {
          float z = texture2D(tDepth, uv).x * 2.0 - 1.0;
          return (2.0 * uNear * uFar) / (uFar + uNear - z * (uFar - uNear));
        }

        vec3 acesFilm(vec3 x) {
          const float a = 2.51;
          const float b = 0.03;
          const float c = 2.43;
          const float d = 0.59;
          const float e = 0.14;
          return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
        }

        vec3 linearToSRGB(vec3 c) {
          vec3 lo = c * 12.92;
          vec3 hi = 1.055 * pow(max(c, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055;
          return mix(lo, hi, step(vec3(0.0031308), c));
        }

        void main() {
          vec3 hdr = texture2D(tDiffuse, vUv).rgb;
          float rawD = texture2D(tDepth, vUv).x;

          // Screen-Space Ambient Occlusion (16-tap Rotated Golden-Angle Spiral)
          float ao = 1.0;
          if (rawD < 0.9994) {
            float centerZ = linearDepth(vUv);
            float distFade = 1.0 - smoothstep(45.0, 130.0, centerZ);
            if (distFade > 0.01) {
              float ign = fract(52.9829189 * fract(dot(gl_FragCoord.xy, vec2(0.06711056, 0.00583715))));
              float baseAng = ign * 6.2831853;
              vec2 aspect = vec2(uRes.y / max(1.0, uRes.x), 1.0);
              float radPx = clamp(0.52 / max(0.8, centerZ * 0.12), 0.0025, 0.024);
              float occ = 0.0;
              for (int i = 0; i < 16; i++) {
                float fi = float(i);
                float r = sqrt((fi + 0.5) / 16.0) * radPx;
                float th = baseAng + fi * 2.3999632;
                vec2 sUv = vUv + vec2(cos(th), sin(th)) * aspect * r;
                float sZ = linearDepth(sUv);
                float diff = centerZ - sZ;
                float rangeCheck = smoothstep(0.0, 1.0, 0.95 / (abs(diff) + 0.18));
                occ += (diff > 0.022 && diff < 1.35 ? 1.0 : 0.0) * rangeCheck;
              }
              ao = 1.0 - clamp((occ / 16.0) * uAoStrength * 1.65 * distFade, 0.0, 0.52);
            }
          }

          // Apply Physical Warm-Cool Ambient Occlusion + Soft Unreal Bloom
          hdr *= mix(vec3(0.80, 0.84, 0.90), vec3(1.0), ao);
          vec3 bloom = texture2D(tBloom, vUv).rgb;
          hdr += bloom * uBloomStrength;

          // ACES Filmic Tone Mapping + Subtle Architectural Contrast & Optical Vignette
          vec3 mapped = acesFilm(hdr * uExposure);
          mapped = mix(mapped, smoothstep(0.0, 1.0, mapped), 0.10);
          vec2 vc = vUv - 0.5;
          mapped *= 1.0 - dot(vc, vc) * 0.20;

          vec3 srgb = linearToSRGB(mapped);
          float dither = (fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453) - 0.5) / 255.0;
          gl_FragColor = vec4(clamp(srgb + dither, 0.0, 1.0), 1.0);
        }
      `
    });

    const fsMesh = new THREE.Mesh(quadGeo, threshMat);
    const fsScene = new THREE.Scene();
    fsScene.add(fsMesh);

    avz.post = {
      sceneRT, bloomRT1, bloomRT2,
      orthoCam, fsMesh, fsScene,
      threshMat, blurMat, compositeMat,
      w: 1024, h: 768
    };
  }

  function renderArchvizFrame() {
    const r = avz.renderer;
    if (!r || !avz.scene || !avz.camera) return;

    const canvas = r.domElement;
    const cssW = Math.max(2, canvas.clientWidth || 800);
    const cssH = Math.max(2, canvas.clientHeight || 600);
    const dpr = r.getPixelRatio();
    const pxW = Math.round(cssW * dpr);
    const pxH = Math.round(cssH * dpr);

    if (canvas.width !== pxW || canvas.height !== pxH) {
      r.setSize(cssW, cssH, false);
      avz.camera.aspect = cssW / cssH;
      avz.camera.updateProjectionMatrix();
    }

    if (avz.post && (avz.post.w !== pxW || avz.post.h !== pxH)) {
      avz.post.w = pxW; avz.post.h = pxH;
      avz.post.sceneRT.setSize(pxW, pxH);
      const bw = Math.max(64, Math.round(pxW * 0.45));
      const bh = Math.max(64, Math.round(pxH * 0.45));
      avz.post.bloomRT1.setSize(bw, bh);
      avz.post.bloomRT2.setSize(bw, bh);
      avz.post.blurMat.uniforms.uTexel.value.set(1 / bw, 1 / bh);
      avz.post.compositeMat.uniforms.uRes.value.set(pxW, pxH);
    }

    if (avz.waterUniforms) avz.waterUniforms.uViewport.value.set(pxW, pxH);
    if (avz.floorReflectUniforms) avz.floorReflectUniforms.uViewport.value.set(pxW, pxH);

    // 1. REAL-TIME PLANAR MIRROR REFLECTION PASS (512x512)
    const H = avz.reflectPlaneY;
    if (avz.reflectRT && avz.reflCam && avz.camera.position.y > H + 0.12) {
      avz.reflCam.fov = avz.camera.fov;
      avz.reflCam.aspect = avz.camera.aspect;
      avz.reflCam.updateProjectionMatrix();

      const cp = avz.camera.position;
      const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(avz.camera.quaternion);
      const lookPt = new THREE.Vector3(cp.x + fwd.x * 10, cp.y + fwd.y * 10, cp.z + fwd.z * 10);

      avz.reflCam.position.set(cp.x, 2 * H - cp.y, cp.z);
      avz.reflCam.up.set(0, 1, 0);
      avz.reflCam.lookAt(lookPt.x, 2 * H - lookPt.y, lookPt.z);

      avz.reflectiveMeshes.forEach(m => { m.visible = false; });
      if (avz.cursorRing) avz.cursorRing.visible = false;
      avz.clipPlane.set(new THREE.Vector3(0, 1, 0), -H + 0.015);
      r.localClippingEnabled = true;
      r.clippingPlanes = [avz.clipPlane];
      r.toneMapping = THREE.NoToneMapping;
      r.setRenderTarget(avz.reflectRT);
      r.clear();
      r.render(avz.scene, avz.reflCam);
      r.clippingPlanes = [];
      r.localClippingEnabled = false;
      avz.reflectiveMeshes.forEach(m => { m.visible = true; });
      if (avz.cursorRing && avz.hoverNdc.active && avz.camStyle === "fpv") avz.cursorRing.visible = true;
    }

    // 2. HDR SCENE + BLOOM + DEPTH SSAO + ACES COMPOSITE PASS
    if (avz.post) {
      const p = avz.post;
      r.toneMapping = THREE.NoToneMapping;
      r.setRenderTarget(p.sceneRT);
      r.clear();
      r.render(avz.scene, avz.camera);

      // Extract bright HDR emissives/highlights
      p.fsMesh.material = p.threshMat;
      p.threshMat.uniforms.tDiffuse.value = p.sceneRT.texture;
      r.setRenderTarget(p.bloomRT1);
      r.render(p.fsScene, p.orthoCam);

      // 2-iteration Dual Kawase smooth bloom blur
      p.fsMesh.material = p.blurMat;
      p.blurMat.uniforms.tDiffuse.value = p.bloomRT1.texture;
      p.blurMat.uniforms.uOffset.value = 1.4;
      r.setRenderTarget(p.bloomRT2);
      r.render(p.fsScene, p.orthoCam);

      p.blurMat.uniforms.tDiffuse.value = p.bloomRT2.texture;
      p.blurMat.uniforms.uOffset.value = 2.8;
      r.setRenderTarget(p.bloomRT1);
      r.render(p.fsScene, p.orthoCam);

      // Final Depth-SSAO + Bloom + ACES Filmic + Vignette Composite to Screen
      p.fsMesh.material = p.compositeMat;
      r.setRenderTarget(null);
      r.render(p.fsScene, p.orthoCam);
    } else {
      r.toneMapping = THREE.ACESFilmicToneMapping;
      r.setRenderTarget(null);
      r.render(avz.scene, avz.camera);
    }
  }

  function ensureArchvizRenderer() {
    if (typeof THREE === "undefined") return false;
    const canvas = document.getElementById("archvizWebglCanvas");
    if (!canvas) return false;
    if (!avz.renderer) {
      avz.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
      avz.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
      avz.renderer.outputColorSpace = THREE.SRGBColorSpace;
      avz.renderer.shadowMap.enabled = true;
      avz.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      avz.pmremGen = new THREE.PMREMGenerator(avz.renderer);
      avz.pmremGen.compileEquirectangularShader();
      avz.camera = new THREE.PerspectiveCamera(48, 1.6, 0.20, 480);
      initPostAndReflectionPipeline();
      initArchvizMaterials();
      bindArchvizControlsOnce(canvas);
    }
    return true;
  }

  function initArchvizMaterials() {
    // 1. Bookmatched Polished Calacatta Gold Marble (1024px Albedo + Normal + Roughness)
    const calacatta = createPbrMaps(512, 3, 3, 1.2, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#f7f4ee"; actx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(32,32,32)"; rctx.fillRect(0, 0, s, s);
      hctx.fillStyle = "rgb(132,132,132)"; hctx.fillRect(0, 0, s, s);
      // Soft organic cloudy marble mineral veining
      for (let v = 0; v < 34; v++) {
        const isGold = (v % 4 === 0);
        actx.strokeStyle = isGold ? "rgba(184,142,78,0.22)" : "rgba(142,150,162,0.18)";
        rctx.strokeStyle = "rgb(78,78,78)";
        actx.lineWidth = isGold ? 1.6 : (1.2 + (v % 4) * 1.4);
        rctx.lineWidth = actx.lineWidth;
        actx.beginPath(); rctx.beginPath();
        let x = (v * 89) % s, y = 0;
        actx.moveTo(x, y); rctx.moveTo(x, y);
        while (y < s) {
          y += 22;
          x += Math.sin(y * 0.021 + v * 0.9) * 24 + Math.cos(y * 0.055 - v) * 8;
          actx.lineTo(x, y); rctx.lineTo(x, y);
        }
        actx.stroke(); rctx.stroke();
      }
      // Subtle precision rectified 1200x1200mm slab joints
      hctx.strokeStyle = "rgb(82,82,82)"; hctx.lineWidth = 2.0;
      actx.strokeStyle = "rgba(180,174,164,0.34)"; actx.lineWidth = 1.2;
      [0, 256].forEach(ox => [0, 256].forEach(oy => {
        actx.strokeRect(ox + 1, oy + 1, 254, 254);
        hctx.strokeRect(ox + 1, oy + 1, 254, 254);
      }));
    });

    // 2. Honed Roman Travertine Ashlar Stone Cladding (Running-Bond Courses + Pore NormalMap)
    const travertine = createPbrMaps(512, 4, 4, 2.4, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#e8decb"; actx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(138,138,138)"; rctx.fillRect(0, 0, s, s);
      const rows = 6, rowH = s / rows;
      for (let r = 0; r < rows; r++) {
        const y = r * rowH;
        const cols = 3;
        const colW = s / cols;
        const shift = (r % 2) * (colW * 0.5);
        for (let c = -1; c <= cols; c++) {
          const x = c * colW + shift;
          const tone = 224 + ((r * 13 + c * 29) % 14) - 7;
          actx.fillStyle = `rgb(${tone + 9}, ${tone + 1}, ${tone - 14})`;
          actx.fillRect(x + 2, y + 2, colW - 3, rowH - 3);
          hctx.fillStyle = "rgb(142,142,142)";
          hctx.fillRect(x + 2, y + 2, colW - 3, rowH - 3);
          // Natural horizontal sedimentary travertine pores
          for (let p = 0; p < 26; p++) {
            const px = x + 6 + ((p * 47 + r * 19) % Math.max(8, colW - 16));
            const py = y + 5 + ((p * 31 + c * 23) % Math.max(8, rowH - 10));
            const pw = 6 + (p % 14);
            actx.fillStyle = "rgba(162,144,118,0.22)";
            actx.fillRect(px, py, pw, 1.6);
            hctx.fillStyle = "rgb(104,104,104)";
            hctx.fillRect(px, py, pw, 1.8);
          }
          // Recessed mortar joints
          actx.strokeStyle = "rgba(145,131,110,0.52)"; actx.lineWidth = 2.0;
          actx.strokeRect(x, y, colW, rowH);
          hctx.strokeStyle = "rgb(62,62,62)"; hctx.lineWidth = 3.0;
          hctx.strokeRect(x, y, colW, rowH);
        }
      }
    });

    // 3. Smoked European Wide-Plank Oak (Cathedral Grain + V-Groove Bevels)
    const oak = createPbrMaps(512, 4, 4, 2.0, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#9c6f44"; actx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(98,98,98)"; rctx.fillRect(0, 0, s, s);
      const planks = 8, ph = s / planks;
      for (let p = 0; p < planks; p++) {
        const y = p * ph;
        const v = (p % 3 === 0) ? 8 : (p % 3 === 1 ? -6 : 2);
        actx.fillStyle = `rgb(${158 + v}, ${113 + v}, ${70 + v})`;
        actx.fillRect(0, y + 1, s, ph - 2);
        hctx.fillStyle = "rgb(138,138,138)";
        hctx.fillRect(0, y + 1, s, ph - 2);
        for (let g = 0; g < 14; g++) {
          actx.strokeStyle = g % 2 ? "rgba(82,48,22,0.16)" : "rgba(214,172,126,0.10)";
          actx.lineWidth = 1.2;
          actx.beginPath();
          const gy = y + 4 + g * (ph / 15);
          actx.moveTo(0, gy);
          actx.bezierCurveTo(s * 0.33, gy + Math.sin(p + g) * 4, s * 0.66, gy - Math.cos(p + g) * 4, s, gy);
          actx.stroke();
        }
        hctx.fillStyle = "rgb(55,55,55)";
        hctx.fillRect(0, y, s, 2.2);
        const jointX = ((p * 193) % (s - 60)) + 30;
        hctx.fillRect(jointX, y, 2.2, ph);
        actx.fillStyle = "rgba(68,39,18,0.45)";
        actx.fillRect(0, y, s, 1.5);
        actx.fillRect(jointX, y, 1.5, ph);
      }
    });

    // 4. Architectural Fluted Walnut Acoustic Slats (Deep Shadow-Felt Channels!)
    const flutedWalnut = createPbrMaps(512, 3, 1, 3.6, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#181310"; actx.fillRect(0, 0, s, s);
      hctx.fillStyle = "rgb(38,38,38)"; hctx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(175,175,175)"; rctx.fillRect(0, 0, s, s);
      const slats = 24, sw = s / slats;
      for (let i = 0; i < slats; i++) {
        const x = i * sw;
        const tone = (i % 3) * 6;
        actx.fillStyle = `rgb(${124 + tone}, ${80 + tone}, ${46 + tone})`;
        actx.fillRect(x + 4, 0, sw - 7, s);
        hctx.fillStyle = "rgb(215,215,215)";
        hctx.fillRect(x + 4, 0, sw - 7, s);
        rctx.fillStyle = "rgb(92,92,92)";
        rctx.fillRect(x + 4, 0, sw - 7, s);
      }
    });

    // 5. Tactile Belgian Bouclé & Linen Upholstery Weave
    const boucle = createPbrMaps(256, 8, 8, 1.8, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#efeae0"; actx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(222,222,222)"; rctx.fillRect(0, 0, s, s);
      for (let y = 0; y < s; y += 4) {
        for (let x = 0; x < s; x += 4) {
          const n = ((x * 37 + y * 59) % 23) - 11;
          actx.fillStyle = `rgb(${238 + n}, ${232 + n}, ${221 + n})`;
          actx.fillRect(x, y, 3, 3);
          const h = 115 + ((x * 19 + y * 41) % 55);
          hctx.fillStyle = `rgb(${h},${h},${h})`;
          hctx.fillRect(x, y, 3, 3);
        }
      }
    });

    // 6. Porphyry Interlocking Driveway Cobblestones
    const cobble = createPbrMaps(512, 5, 5, 2.8, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#645f58"; actx.fillRect(0, 0, s, s);
      hctx.fillStyle = "rgb(52,52,52)"; hctx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(190,190,190)"; rctx.fillRect(0, 0, s, s);
      const rows = 10, rh = s / rows;
      for (let r = 0; r < rows; r++) {
        const cols = 8, cw = s / cols, sh = (r % 2) * (cw * 0.5);
        for (let c = -1; c <= cols; c++) {
          const x = c * cw + sh, y = r * rh;
          const v = 132 + ((r * 23 + c * 41) % 26) - 13;
          actx.fillStyle = `rgb(${v + 6}, ${v + 2}, ${v - 4})`;
          actx.fillRect(x + 3, y + 3, cw - 6, rh - 6);
          hctx.fillStyle = "rgb(185,185,185)";
          hctx.fillRect(x + 3, y + 3, cw - 6, rh - 6);
        }
      }
    });

    // 7. Weathered Granite Boulevard Asphalt (Aggregate Bump + Subtle Tire Tracks + Crisp Lane Markings)
    const asphalt = createPbrMaps(512, 1, 14, 2.2, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#262930"; actx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(188,188,188)"; rctx.fillRect(0, 0, s, s);
      for (let i = 0; i < 6500; i++) {
        const x = (i * 97) % s, y = (i * 53) % s;
        const d = (i % 3 === 0) ? 14 : -10;
        actx.fillStyle = `rgb(${38 + d}, ${41 + d}, ${48 + d})`;
        actx.fillRect(x, y, 2, 2);
        const h = 105 + (i % 55);
        hctx.fillStyle = `rgb(${h},${h},${h})`;
        hctx.fillRect(x, y, 2, 2);
      }
      // Subtle specular wheel-path wear bands
      rctx.fillStyle = "rgb(122,122,122)";
      rctx.fillRect(92, 0, 86, s);
      rctx.fillRect(334, 0, 86, s);
      actx.fillStyle = "rgba(255,255,255,0.022)";
      actx.fillRect(92, 0, 86, s);
      actx.fillRect(334, 0, 86, s);
      // Crisp thermoplastic road markings
      actx.fillStyle = "#e2e8f0";
      actx.fillRect(252, 40, 8, 176);
      actx.fillRect(252, 296, 8, 176);
      actx.fillStyle = "rgba(226,232,240,0.65)";
      actx.fillRect(14, 0, 4, s);
      actx.fillRect(s - 18, 0, 4, s);
    });

    // 8. Diamond-Scaled Date Palm Bark (Authentic Overlapping Frond-Base Scars!)
    const palmBark = createPbrMaps(256, 2, 7, 3.2, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#5c4632"; actx.fillRect(0, 0, s, s);
      hctx.fillStyle = "rgb(60,60,60)"; hctx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(225,225,225)"; rctx.fillRect(0, 0, s, s);
      const rows = 8, rh = s / rows, cols = 6, cw = s / cols;
      for (let r = 0; r < rows; r++) {
        const sh = (r % 2) * (cw * 0.5);
        for (let c = -1; c <= cols; c++) {
          const cx = c * cw + sh + cw * 0.5, cy = r * rh + rh * 0.5;
          actx.fillStyle = (r + c) % 2 ? "#765c43" : "#695039";
          actx.beginPath();
          actx.moveTo(cx, cy - rh * 0.45);
          actx.lineTo(cx + cw * 0.46, cy);
          actx.lineTo(cx, cy + rh * 0.45);
          actx.lineTo(cx - cw * 0.46, cy);
          actx.closePath();
          actx.fill();
          actx.strokeStyle = "#3d2c1e"; actx.lineWidth = 2.0; actx.stroke();

          hctx.fillStyle = "rgb(195,195,195)";
          hctx.beginPath();
          hctx.moveTo(cx, cy - rh * 0.42);
          hctx.lineTo(cx + cw * 0.42, cy);
          hctx.lineTo(cx, cy + rh * 0.42);
          hctx.lineTo(cx - cw * 0.42, cy);
          hctx.closePath();
          hctx.fill();
        }
      }
    });

    // 9. Resort Bermudagrass Lawn (Subtle Mowing Bands + Micro Blade Normal)
    const lawn = createPbrMaps(512, 7, 7, 1.6, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#355e38"; actx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(218,218,218)"; rctx.fillRect(0, 0, s, s);
      for (let y = 0; y < s; y += 64) {
        actx.fillStyle = (y / 64) % 2 === 0 ? "rgba(132,188,108,0.10)" : "rgba(24,52,28,0.10)";
        actx.fillRect(0, y, s, 64);
      }
      for (let i = 0; i < 4500; i++) {
        const x = (i * 83) % s, y = (i * 61) % s;
        actx.fillStyle = i % 2 ? "rgba(148,197,115,0.14)" : "rgba(31,64,34,0.16)";
        actx.fillRect(x, y, 2, 4);
        const h = 100 + (i % 65);
        hctx.fillStyle = `rgb(${h},${h},${h})`;
        hctx.fillRect(x, y, 2, 4);
      }
    });

    // 10. High-Detail Pinnate Date Palm Frond Alpha-Cutout Texture (Sunlit Olive-Emerald Gradient)
    const palmLeafCanvas = document.createElement("canvas");
    palmLeafCanvas.width = 256; palmLeafCanvas.height = 512;
    const pctx = palmLeafCanvas.getContext("2d");
    pctx.clearRect(0, 0, 256, 512);
    const stemGrad = pctx.createLinearGradient(0, 512, 0, 0);
    stemGrad.addColorStop(0, "#7c7842");
    stemGrad.addColorStop(1, "#4d783b");
    pctx.fillStyle = stemGrad;
    pctx.beginPath();
    pctx.moveTo(124, 512); pctx.lineTo(132, 512); pctx.lineTo(129, 6); pctx.lineTo(127, 6);
    pctx.closePath(); pctx.fill();
    for (let i = 0; i < 48; i++) {
      const t = i / 47;
      const y = 500 - t * 484;
      const span = Math.sin(Math.pow(t, 0.68) * Math.PI) * 118 + 8;
      const droop = -14 - t * 28;
      [-1, 1].forEach(dir => {
        const g = pctx.createLinearGradient(128, y, 128 + dir * span, y + droop);
        g.addColorStop(0, "#4f7c3f");
        g.addColorStop(0.65, (i % 2 === 0) ? "#3b6b35" : "#45743a");
        g.addColorStop(1, "#698a46");
        pctx.fillStyle = g;
        pctx.beginPath();
        pctx.moveTo(128, y);
        pctx.quadraticCurveTo(128 + dir * span * 0.54, y + droop * 0.42, 128 + dir * span, y + droop);
        pctx.quadraticCurveTo(128 + dir * span * 0.50, y + droop * 0.42 + 6.4, 128, y + 5.6);
        pctx.closePath(); pctx.fill();
      });
    }
    const palmFrondTex = new THREE.CanvasTexture(palmLeafCanvas);
    palmFrondTex.colorSpace = THREE.SRGBColorSpace;

    // 11. Mediterranean Olive / Ghaf Branching Leaf Cluster Alpha-Cutout Texture
    const oliveLeafCanvas = document.createElement("canvas");
    oliveLeafCanvas.width = 256; oliveLeafCanvas.height = 256;
    const octx = oliveLeafCanvas.getContext("2d");
    octx.clearRect(0, 0, 256, 256);
    for (let b = 0; b < 72; b++) {
      const ang = (b * 2.39996);
      const rad = Math.sqrt(b / 72) * 102;
      const lx = 128 + Math.cos(ang) * rad, ly = 128 + Math.sin(ang) * rad;
      octx.save();
      octx.translate(lx, ly);
      octx.rotate(ang + 0.5);
      octx.fillStyle = (b % 3 === 0) ? "#5a7851" : (b % 3 === 1 ? "#44623f" : "#6e8a63");
      octx.beginPath();
      octx.ellipse(0, 0, 16, 6.2, 0, 0, Math.PI * 2);
      octx.fill();
      octx.restore();
    }
    const oliveFoliageTex = new THREE.CanvasTexture(oliveLeafCanvas);
    oliveFoliageTex.colorSpace = THREE.SRGBColorSpace;

    // 12. Soft Gaussian Ground Contact Shadow Decal Texture (Key Blender Cycles Realism Secret!)
    const shCanvas = document.createElement("canvas");
    shCanvas.width = 128; shCanvas.height = 128;
    const sctx = shCanvas.getContext("2d");
    const sgrad = sctx.createRadialGradient(64, 64, 6, 64, 64, 62);
    sgrad.addColorStop(0.0, "rgba(8, 12, 22, 0.56)");
    sgrad.addColorStop(0.48, "rgba(8, 12, 22, 0.28)");
    sgrad.addColorStop(0.80, "rgba(8, 12, 22, 0.07)");
    sgrad.addColorStop(1.0, "rgba(8, 12, 22, 0.0)");
    sctx.fillStyle = sgrad;
    sctx.fillRect(0, 0, 128, 128);
    const contactShadowTex = new THREE.CanvasTexture(shCanvas);

    // 13. Woven Berber Rug & Contemporary Gallery Artwork
    const rugC = document.createElement("canvas");
    rugC.width = 512; rugC.height = 512;
    const rgx = rugC.getContext("2d");
    rgx.fillStyle = "#dfd7ca"; rgx.fillRect(0, 0, 512, 512);
    rgx.strokeStyle = "#bfb29f"; rgx.lineWidth = 14; rgx.strokeRect(22, 22, 468, 468);
    rgx.strokeStyle = "#8c7f6e"; rgx.lineWidth = 2; rgx.strokeRect(42, 42, 428, 428);
    for (let i = 0; i < 3600; i++) {
      rgx.fillStyle = i % 2 ? "rgba(255,255,255,0.14)" : "rgba(105,95,82,0.12)";
      rgx.fillRect((i * 71) % 512, (i * 43) % 512, 4, 2);
    }
    const rugTex = new THREE.CanvasTexture(rugC);
    rugTex.colorSpace = THREE.SRGBColorSpace;

    const artC = document.createElement("canvas");
    artC.width = 512; artC.height = 512;
    const arx = artC.getContext("2d");
    const ag = arx.createLinearGradient(0, 0, 512, 512);
    ag.addColorStop(0, "#f5efe6"); ag.addColorStop(0.55, "#e6d8c5"); ag.addColorStop(1, "#cbb79d");
    arx.fillStyle = ag; arx.fillRect(0, 0, 512, 512);
    arx.fillStyle = "rgba(24, 58, 74, 0.82)";
    arx.beginPath(); arx.arc(210, 250, 138, 0, Math.PI * 2); arx.fill();
    arx.fillStyle = "rgba(194, 118, 56, 0.78)";
    arx.beginPath(); arx.arc(315, 215, 96, 0, Math.PI * 2); arx.fill();
    arx.strokeStyle = "rgba(248, 244, 236, 0.85)"; arx.lineWidth = 7;
    arx.beginPath(); arx.moveTo(70, 340); arx.quadraticCurveTo(256, 240, 442, 330); arx.stroke();
    const artTex = new THREE.CanvasTexture(artC);
    artTex.colorSpace = THREE.SRGBColorSpace;

    // 14. Distant Atmospheric Curtain-Wall Skyline Texture
    const skyC = document.createElement("canvas");
    skyC.width = 256; skyC.height = 512;
    const skx = skyC.getContext("2d");
    skx.fillStyle = "#33475b"; skx.fillRect(0, 0, 256, 512);
    for (let r = 0; r < 40; r++) {
      for (let c = 0; c < 10; c++) {
        const lit = ((r * 17 + c * 11) % 7 === 0);
        skx.fillStyle = lit ? "rgba(255, 224, 166, 0.45)" : "rgba(186, 214, 235, 0.16)";
        skx.fillRect(6 + c * 25, 6 + r * 12.5, 18, 8);
      }
    }
    const skylineTex = new THREE.CanvasTexture(skyC);
    skylineTex.colorSpace = THREE.SRGBColorSpace;

    // 14b. Fine Wind-Rippled White Coral Beach Sand & Large-Format Terrace Limestone Pavers + Pool Mosaic
    const fineSand = createPbrMaps(256, 38, 38, 1.1, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#eee3cf"; actx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(232,232,232)"; rctx.fillRect(0, 0, s, s);
      for (let y = 0; y < s; y += 2) {
        const ripple = Math.sin((y / s) * Math.PI * 6.0) * 6;
        actx.fillStyle = ripple > 0 ? "rgba(255,250,240,0.14)" : "rgba(186,168,140,0.12)";
        actx.fillRect(0, y, s, 2);
        const rh = Math.round(128 + ripple * 2.2);
        hctx.fillStyle = `rgb(${rh},${rh},${rh})`;
        hctx.fillRect(0, y, s, 2);
      }
      for (let i = 0; i < 2400; i++) {
        const x = (i * 73) % s, y = (i * 41) % s;
        actx.fillStyle = i % 2 ? "rgba(255,255,255,0.16)" : "rgba(168,148,118,0.14)";
        actx.fillRect(x, y, 2, 2);
      }
    });

    const terracePaver = createPbrMaps(512, 14, 14, 1.3, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#eae2d3"; actx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(172,172,172)"; rctx.fillRect(0, 0, s, s);
      const tiles = 4, ts = s / tiles;
      for (let r = 0; r < tiles; r++) {
        for (let c = 0; c < tiles; c++) {
          const v = ((r * 17 + c * 31) % 10) - 5;
          actx.fillStyle = `rgb(${234 + v}, ${226 + v}, ${211 + v})`;
          actx.fillRect(c * ts + 2, r * ts + 2, ts - 3, ts - 3);
          hctx.fillStyle = "rgb(138,138,138)";
          hctx.fillRect(c * ts + 2, r * ts + 2, ts - 3, ts - 3);
          actx.strokeStyle = "rgba(160,150,134,0.42)"; actx.lineWidth = 1.5;
          actx.strokeRect(c * ts, r * ts, ts, ts);
          hctx.strokeStyle = "rgb(82,82,82)"; hctx.lineWidth = 2.0;
          hctx.strokeRect(c * ts, r * ts, ts, ts);
        }
      }
    });

    const poolMosaic = createPbrMaps(256, 10, 10, 1.5, (actx, hctx, rctx, s) => {
      actx.fillStyle = "#087f96"; actx.fillRect(0, 0, s, s);
      rctx.fillStyle = "rgb(48,48,48)"; rctx.fillRect(0, 0, s, s);
      const n = 16, cs = s / n;
      const palette = ["#0891b2", "#0e7490", "#0d9488", "#0284c7", "#14b8a6"];
      for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
          actx.fillStyle = palette[(r * 7 + c * 13) % palette.length];
          actx.fillRect(c * cs + 1, r * cs + 1, cs - 2, cs - 2);
          hctx.fillStyle = "rgb(150,150,150)";
          hctx.fillRect(c * cs + 1, r * cs + 1, cs - 2, cs - 2);
        }
      }
    });

    // 15. REAL-TIME PLANAR-REFLECTED TROPICAL LAGOON / INFINITY POOL SHADER (Zero Checkerboard Moiré!)
    avz.waterUniforms = {
      uTime: { value: 0 },
      uSunDir: { value: new THREE.Vector3(0.5, 0.32, -0.8).normalize() },
      uDeepCol: { value: new THREE.Color("#065a82") },
      uShallowCol: { value: new THREE.Color("#0ea5b7") },
      uSunCol: { value: new THREE.Color("#ffe7c2") },
      uReflectTex: { value: avz.reflectRT ? avz.reflectRT.texture : null },
      uViewport: { value: new THREE.Vector2(1024, 768) }
    };

    const waterMat = new THREE.ShaderMaterial({
      uniforms: avz.waterUniforms,
      transparent: true,
      side: THREE.DoubleSide,
      vertexShader: `
        uniform float uTime;
        varying vec3 vWorldPos;
        void main() {
          vec4 wp = modelMatrix * vec4(position, 1.0);
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
        uniform sampler2D uReflectTex;
        uniform vec2 uViewport;
        varying vec3 vWorldPos;

        float waveHash(vec2 p) {
          return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
        }
        float waveNoise(vec2 p) {
          vec2 i = floor(p);
          vec2 f = fract(p);
          vec2 u = f * f * (3.0 - 2.0 * f);
          return mix(mix(waveHash(i), waveHash(i + vec2(1.0, 0.0)), u.x),
                     mix(waveHash(i + vec2(0.0, 1.0)), waveHash(i + vec2(1.0, 1.0)), u.x), u.y);
        }
        float fbmWaves(vec2 p, float t) {
          float v = 0.0;
          mat2 rot = mat2(0.80, -0.60, 0.60, 0.80);
          v += 0.50 * waveNoise(p * 0.55 + vec2(t * 0.35, -t * 0.28));
          p = rot * p;
          v += 0.30 * waveNoise(p * 1.35 + vec2(-t * 0.52, t * 0.41));
          p = rot * p;
          v += 0.20 * waveNoise(p * 3.10 + vec2(t * 0.78, t * 0.62));
          return v;
        }

        void main() {
          float dist = length(cameraPosition - vWorldPos);
          float atten = 1.0 - smoothstep(22.0, 145.0, dist);
          float eps = 0.18;
          float h0 = fbmWaves(vWorldPos.xz, uTime);
          float hx = fbmWaves(vWorldPos.xz + vec2(eps, 0.0), uTime);
          float hz = fbmWaves(vWorldPos.xz + vec2(0.0, eps), uTime);
          vec3 n = normalize(vec3((h0 - hx) * 0.40 * atten, 1.0, (h0 - hz) * 0.40 * atten));

          vec3 viewDir = normalize(cameraPosition - vWorldPos);
          float fresnel = 0.04 + 0.88 * pow(1.0 - max(dot(viewDir, n), 0.0), 4.0);

          vec2 screenUv = clamp(gl_FragCoord.xy / max(uViewport, vec2(1.0)), 0.002, 0.998);
          vec2 reflUv = clamp(vec2(screenUv.x, 1.0 - screenUv.y) + n.xz * 0.040, 0.004, 0.996);
          vec3 reflCol = texture2D(uReflectTex, reflUv).rgb;

          // Subtle caustic shimmer + depth absorption so lagoon & pools stay rich turquoise!
          float caustic = smoothstep(0.56, 0.84, h0) * 0.14 * atten;
          float depthFactor = clamp(smoothstep(4.0, 95.0, dist) * 0.72 + fresnel * 0.22, 0.0, 1.0);
          vec3 waterBody = mix(uShallowCol, uDeepCol, depthFactor) + vec3(0.05, 0.24, 0.26) * caustic;

          vec3 halfV = normalize(uSunDir + viewDir);
          float spec = pow(max(dot(n, halfV), 0.0), 260.0) * (0.45 + 0.55 * atten);
          vec3 col = mix(waterBody, reflCol, clamp(fresnel * 0.46, 0.05, 0.44)) + uSunCol * spec * 1.9;
          gl_FragColor = vec4(col, 0.88);
        }
      `
    });

    // 16. GLOSSY MARBLE FLOOR PLANAR REFLECTION OVERLAY SHADER
    avz.floorReflectUniforms = {
      uReflectTex: { value: avz.reflectRT ? avz.reflectRT.texture : null },
      uViewport: { value: new THREE.Vector2(1024, 768) },
      uNormalMap: { value: calacatta.normalMap },
      uRoughness: { value: 0.14 }
    };
    const marbleReflectOverlayMat = new THREE.ShaderMaterial({
      uniforms: avz.floorReflectUniforms,
      transparent: true,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: -1,
      polygonOffsetUnits: -1,
      vertexShader: `
        varying vec3 vWorldPos;
        varying vec2 vUv;
        void main() {
          vUv = uv * 4.0;
          vec4 wp = modelMatrix * vec4(position, 1.0);
          vWorldPos = wp.xyz;
          gl_Position = projectionMatrix * viewMatrix * wp;
        }
      `,
      fragmentShader: `
        uniform sampler2D uReflectTex;
        uniform sampler2D uNormalMap;
        uniform vec2 uViewport;
        varying vec3 vWorldPos;
        varying vec2 vUv;
        void main() {
          vec3 viewDir = normalize(cameraPosition - vWorldPos);
          vec2 nm = texture2D(uNormalMap, vUv).xy * 2.0 - 1.0;
          vec3 n = normalize(vec3(nm.x * 0.04, 1.0, nm.y * 0.04));
          float fresnel = 0.05 + 0.36 * pow(1.0 - max(dot(viewDir, n), 0.0), 3.4);

          vec2 sUv = gl_FragCoord.xy / max(uViewport, vec2(1.0));
          vec2 rUv = clamp(vec2(sUv.x, 1.0 - sUv.y) + nm * 0.005, 0.005, 0.995);
          // 5-tap glossy marble reflection blur
          vec2 b = vec2(0.0032);
          vec3 refl = texture2D(uReflectTex, rUv).rgb * 0.36;
          refl += texture2D(uReflectTex, rUv + vec2( b.x,  b.y)).rgb * 0.16;
          refl += texture2D(uReflectTex, rUv + vec2(-b.x,  b.y)).rgb * 0.16;
          refl += texture2D(uReflectTex, rUv + vec2( b.x, -b.y)).rgb * 0.16;
          refl += texture2D(uReflectTex, rUv + vec2(-b.x, -b.y)).rgb * 0.16;
          // Soft clamp extreme specular spikes in floor reflection
          refl = refl / (vec3(1.0) + refl * 0.35);
          gl_FragColor = vec4(refl, clamp(fresnel, 0.04, 0.34));
        }
      `
    });

    avz.mats = {
      marble: new THREE.MeshPhysicalMaterial({
        map: calacatta.map, normalMap: calacatta.normalMap, roughnessMap: calacatta.roughnessMap,
        normalScale: new THREE.Vector2(0.28, 0.28), roughness: 0.20, metalness: 0.02, clearcoat: 0.65, clearcoatRoughness: 0.12
      }),
      marbleReflectOverlay: marbleReflectOverlayMat,
      travertine: new THREE.MeshStandardMaterial({
        map: travertine.map, normalMap: travertine.normalMap, roughnessMap: travertine.roughnessMap,
        normalScale: new THREE.Vector2(0.75, 0.75), roughness: 0.62, metalness: 0.02
      }),
      plasterWarm: new THREE.MeshStandardMaterial({ color: 0xf4f0e8, roughness: 0.76, metalness: 0.01 }),
      plasterSand: new THREE.MeshStandardMaterial({ color: 0xe8dfd1, roughness: 0.78, metalness: 0.01 }),
      ceilingWhite: new THREE.MeshStandardMaterial({ color: 0xf8f6f1, roughness: 0.80, metalness: 0.0, emissive: 0xfff8eb, emissiveIntensity: 0.12 }),
      pocheCap: new THREE.MeshStandardMaterial({ color: 0x151c28, roughness: 0.72 }),
      oak: new THREE.MeshStandardMaterial({
        map: oak.map, normalMap: oak.normalMap, roughnessMap: oak.roughnessMap,
        normalScale: new THREE.Vector2(0.55, 0.55), roughness: 0.42, metalness: 0.03
      }),
      flutedWalnut: new THREE.MeshStandardMaterial({
        map: flutedWalnut.map, normalMap: flutedWalnut.normalMap, roughnessMap: flutedWalnut.roughnessMap,
        normalScale: new THREE.Vector2(1.4, 1.4), roughness: 0.48, metalness: 0.04
      }),
      cobble: new THREE.MeshStandardMaterial({
        map: cobble.map, normalMap: cobble.normalMap, roughnessMap: cobble.roughnessMap,
        normalScale: new THREE.Vector2(0.95, 0.95), roughness: 0.78, metalness: 0.04
      }),
      rug: new THREE.MeshStandardMaterial({ map: rugTex, normalMap: boucle.normalMap, normalScale: new THREE.Vector2(0.7, 0.7), roughness: 0.94 }),
      artwork: new THREE.MeshStandardMaterial({ map: artTex, roughness: 0.36, metalness: 0.04 }),
      skyline: new THREE.MeshStandardMaterial({ map: skylineTex, roughness: 0.42, metalness: 0.35, transparent: true, opacity: 0.78 }),
      bronze: new THREE.MeshStandardMaterial({ color: 0x382c22, roughness: 0.28, metalness: 0.86 }),
      brass: new THREE.MeshStandardMaterial({ color: 0xc8a258, roughness: 0.22, metalness: 0.90 }),
      charcoal: new THREE.MeshStandardMaterial({ color: 0x1e242e, roughness: 0.42, metalness: 0.45 }),
      graniteKerb: new THREE.MeshStandardMaterial({ color: 0x948e84, normalMap: cobble.normalMap, normalScale: new THREE.Vector2(0.3, 0.3), roughness: 0.74 }),
      cycleSandstone: new THREE.MeshStandardMaterial({ color: 0x9e5a44, normalMap: asphalt.normalMap, normalScale: new THREE.Vector2(0.45, 0.45), roughness: 0.82 }),
      glass: new THREE.MeshPhysicalMaterial({
        color: 0xdbeafe, transparent: true, opacity: 0.20, roughness: 0.04, metalness: 0.12, reflectivity: 0.96, side: THREE.DoubleSide
      }),
      glassDark: new THREE.MeshPhysicalMaterial({
        color: 0x1e293b, transparent: true, opacity: 0.58, roughness: 0.06, metalness: 0.30, clearcoat: 1.0, side: THREE.DoubleSide
      }),
      glassBalustrade: new THREE.MeshPhysicalMaterial({
        color: 0xcffafe, transparent: true, opacity: 0.28, roughness: 0.05, metalness: 0.10, side: THREE.DoubleSide
      }),
      sheerCurtain: new THREE.MeshStandardMaterial({
        color: 0xf7f4ee, transparent: true, opacity: 0.68, roughness: 0.92, side: THREE.DoubleSide, emissive: 0xfff8eb, emissiveIntensity: 0.08
      }),
      fabricBoucle: new THREE.MeshStandardMaterial({
        map: boucle.map, normalMap: boucle.normalMap, normalScale: new THREE.Vector2(0.65, 0.65), roughness: 0.90
      }),
      fabricTaupe: new THREE.MeshStandardMaterial({
        color: 0xb8aca0, normalMap: boucle.normalMap, normalScale: new THREE.Vector2(0.6, 0.6), roughness: 0.88
      }),
      fabricCharcoal: new THREE.MeshStandardMaterial({
        color: 0x3b424c, normalMap: boucle.normalMap, normalScale: new THREE.Vector2(0.6, 0.6), roughness: 0.88
      }),
      fabricOlive: new THREE.MeshStandardMaterial({
        color: 0x5c6b57, normalMap: boucle.normalMap, normalScale: new THREE.Vector2(0.6, 0.6), roughness: 0.88
      }),
      leatherCognac: new THREE.MeshStandardMaterial({ color: 0x8a5232, roughness: 0.44, metalness: 0.06 }),
      terracePaver: new THREE.MeshStandardMaterial({
        map: terracePaver.map, normalMap: terracePaver.normalMap, roughnessMap: terracePaver.roughnessMap,
        normalScale: new THREE.Vector2(0.45, 0.45), roughness: 0.68, metalness: 0.02
      }),
      poolTile: new THREE.MeshStandardMaterial({
        map: poolMosaic.map, normalMap: poolMosaic.normalMap, roughnessMap: poolMosaic.roughnessMap,
        normalScale: new THREE.Vector2(0.55, 0.55), roughness: 0.18, metalness: 0.05
      }),
      chrome: new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.12, metalness: 0.94 }),
      ledWarm: new THREE.MeshStandardMaterial({ color: 0xfff3db, emissive: 0xffd28a, emissiveIntensity: 3.4, roughness: 0.2 }),
      ledFire: new THREE.MeshStandardMaterial({ color: 0xffb36b, emissive: 0xff7b29, emissiveIntensity: 4.2, roughness: 0.2 }),
      ledRuby: new THREE.MeshStandardMaterial({ color: 0xff6b7a, emissive: 0xef233c, emissiveIntensity: 3.6, roughness: 0.2 }),
      ledEmerald: new THREE.MeshStandardMaterial({ color: 0xa7f3d0, emissive: 0x10b981, emissiveIntensity: 2.8, roughness: 0.2 }),
      oledScreen: new THREE.MeshStandardMaterial({ color: 0x0f172a, emissive: 0x0c4a6e, emissiveIntensity: 0.85, roughness: 0.12 }),
      asphalt: new THREE.MeshStandardMaterial({
        map: asphalt.map, normalMap: asphalt.normalMap, roughnessMap: asphalt.roughnessMap,
        normalScale: new THREE.Vector2(0.65, 0.65), roughness: 0.78
      }),
      lawn: new THREE.MeshStandardMaterial({
        map: lawn.map, normalMap: lawn.normalMap, normalScale: new THREE.Vector2(0.55, 0.55), roughness: 0.90
      }),
      hedge: new THREE.MeshStandardMaterial({ color: 0x2b4c2f, normalMap: lawn.normalMap, normalScale: new THREE.Vector2(0.8, 0.8), roughness: 0.90 }),
      oliveFoliage: new THREE.MeshStandardMaterial({ map: oliveFoliageTex, alphaTest: 0.35, roughness: 0.74, side: THREE.DoubleSide }),
      sand: new THREE.MeshStandardMaterial({
        map: fineSand.map, normalMap: fineSand.normalMap, roughnessMap: fineSand.roughnessMap,
        normalScale: new THREE.Vector2(0.35, 0.35), roughness: 0.92
      }),
      palmTrunk: new THREE.MeshStandardMaterial({
        map: palmBark.map, normalMap: palmBark.normalMap, normalScale: new THREE.Vector2(1.25, 1.25), roughness: 0.90
      }),
      palmFrond: new THREE.MeshStandardMaterial({ map: palmFrondTex, alphaTest: 0.32, roughness: 0.58, side: THREE.DoubleSide }),
      contactShadow: new THREE.MeshBasicMaterial({
        map: contactShadowTex, transparent: true, opacity: 0.85, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2
      }),
      carPaintMidnight: new THREE.MeshPhysicalMaterial({ color: 0x132238, roughness: 0.12, metalness: 0.82, clearcoat: 1.0, clearcoatRoughness: 0.06 }),
      carPaintSilver: new THREE.MeshPhysicalMaterial({ color: 0xcbd5e1, roughness: 0.14, metalness: 0.88, clearcoat: 1.0, clearcoatRoughness: 0.06 }),
      carPaintObsidian: new THREE.MeshPhysicalMaterial({ color: 0x0f1319, roughness: 0.10, metalness: 0.84, clearcoat: 1.0, clearcoatRoughness: 0.05 }),
      carPaintChampagne: new THREE.MeshPhysicalMaterial({ color: 0xc8baa6, roughness: 0.14, metalness: 0.78, clearcoat: 1.0, clearcoatRoughness: 0.06 }),
      water: waterMat
    };
  }

  // =========================================================================
  // PART 4: PHYSICALLY-BASED SKY, VOLUMETRIC CLOUDS & ARCHITECTURAL LIGHTING
  // =========================================================================
  function disposeArchvizScene() {
    if (!avz.scene) return;
    const sharedMats = new Set(Object.values(avz.mats || {}));
    const cachedGeos = new Set(avz.geoCache.values());
    avz.scene.traverse(obj => {
      if (obj.geometry && !cachedGeos.has(obj.geometry)) obj.geometry.dispose();
      if (obj.material) {
        const arr = Array.isArray(obj.material) ? obj.material : [obj.material];
        arr.forEach(m => { if (m && !sharedMats.has(m)) m.dispose(); });
      }
    });
    avz.scene = null;
    avz.swayCrowns = [];
    avz.interiorLights = [];
    avz.reflectiveMeshes = [];
    avz.worldPins = [];
    avz.cursorRing = null;
  }

  function setupSkyAndLighting(scene) {
    const skyGeo = new THREE.SphereGeometry(420, 40, 28);
    const skyUniforms = {
      uZenith: { value: new THREE.Color("#1a4b75") },
      uMid: { value: new THREE.Color("#5b94b8") },
      uHorizon: { value: new THREE.Color("#ebd0b3") },
      uSunDir: { value: new THREE.Vector3(0.56, 0.24, -0.79).normalize() },
      uSunCol: { value: new THREE.Color("#ffe3b8") },
      uCloudTint: { value: new THREE.Color("#fff3e0") }
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
        uniform vec3 uZenith;
        uniform vec3 uMid;
        uniform vec3 uHorizon;
        uniform vec3 uSunDir;
        uniform vec3 uSunCol;
        uniform vec3 uCloudTint;
        varying vec3 vDir;

        float shash(vec2 p) {
          return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
        }
        float snoise(vec2 p) {
          vec2 i = floor(p), f = fract(p);
          vec2 u = f * f * (3.0 - 2.0 * f);
          return mix(mix(shash(i), shash(i + vec2(1.0, 0.0)), u.x),
                     mix(shash(i + vec2(0.0, 1.0)), shash(i + vec2(1.0, 1.0)), u.x), u.y);
        }
        float cloudFbm(vec2 p) {
          float v = 0.0;
          v += 0.52 * snoise(p); p *= 2.07;
          v += 0.28 * snoise(p); p *= 2.11;
          v += 0.14 * snoise(p);
          return v;
        }

        void main() {
          vec3 d = normalize(vDir);
          float h = clamp(d.y, -0.08, 1.0);
          vec3 sky = h < 0.22
            ? mix(uHorizon, uMid, smoothstep(-0.08, 0.22, h))
            : mix(uMid, uZenith, pow(clamp((h - 0.22) / 0.78, 0.0, 1.0), 0.78));

          float sunCos = max(dot(d, uSunDir), 0.0);
          // Warm Mie atmospheric forward-scatter haze near sun azimuth (NOT a white cartoon circle!)
          sky += uSunCol * pow(sunCos, 6.0) * 0.22 * (1.0 - smoothstep(0.0, 0.55, abs(h - uSunDir.y)));
          sky += uSunCol * pow(sunCos, 48.0) * 0.42;

          // Soft Volumetric Cumulus / Altocumulus Clouds with Sunlit Silver-Gold Rim
          if (d.y > 0.015) {
            vec2 cuv = d.xz / (d.y + 0.16) * 0.85;
            float n = cloudFbm(cuv + vec2(1.7, -0.8));
            float density = smoothstep(0.50, 0.82, n) * smoothstep(0.015, 0.18, d.y) * (1.0 - smoothstep(0.55, 0.95, d.y));
            float rim = pow(sunCos, 4.0) * 0.45 + 0.55;
            vec3 cCol = mix(uMid * 0.88, uCloudTint, rim);
            sky = mix(sky, cCol, density * 0.58);
          }

          // Crisp Realistic 0.55-deg Solar Disc (softened by HDR bloom)
          float sunDisc = smoothstep(0.99935, 0.99985, sunCos);
          sky += uSunCol * sunDisc * 3.2;

          gl_FragColor = vec4(sky, 1.0);
        }
      `
    });
    avz.skyMesh = new THREE.Mesh(skyGeo, skyMat);
    scene.add(avz.skyMesh);

    avz.hemiLight = new THREE.HemisphereLight(0xdceefb, 0xd8cbb8, 1.05);
    scene.add(avz.hemiLight);

    // Subtle cool sky fill from opposite azimuth so shadows have rich Blender Cycles GI detail
    avz.fillLight = new THREE.DirectionalLight(0xcce3f8, 0.48);
    avz.fillLight.position.set(-45, 32, 55);
    scene.add(avz.fillLight);

    avz.sunLight = new THREE.DirectionalLight(0xffe0b2, 2.85);
    avz.sunLight.castShadow = true;
    avz.sunLight.shadow.mapSize.set(2048, 2048);
    avz.sunLight.shadow.camera.near = 2;
    avz.sunLight.shadow.camera.far = 230;
    const d = 62;
    avz.sunLight.shadow.camera.left = -d;
    avz.sunLight.shadow.camera.right = d;
    avz.sunLight.shadow.camera.top = d;
    avz.sunLight.shadow.camera.bottom = -d;
    avz.sunLight.shadow.bias = -0.00035;
    avz.sunLight.shadow.normalBias = 0.02;
    scene.add(avz.sunLight);

    // Interactive 3D Floor Walk-Target Ring (Matterport / Twinmotion Teleport Cursor!)
    const ringGrp = new THREE.Group();
    const outerR = new THREE.Mesh(new THREE.RingGeometry(0.42, 0.50, 36), avz.mats.ledEmerald);
    outerR.rotation.x = -Math.PI * 0.5;
    ringGrp.add(outerR);
    const innerR = new THREE.Mesh(new THREE.CircleGeometry(0.14, 24), avz.mats.ledWarm);
    innerR.rotation.x = -Math.PI * 0.5;
    innerR.position.y = 0.004;
    ringGrp.add(innerR);
    ringGrp.visible = false;
    scene.add(ringGrp);
    avz.cursorRing = ringGrp;

    applyTimeOfDayPreset(avz.timeOfDay);
  }

  function applyTimeOfDayPreset(preset) {
    avz.timeOfDay = preset;
    document.querySelectorAll(".avz-tod-btn").forEach(b => b.classList.toggle("active", b.dataset.tod === preset));
    if (!avz.scene || !avz.skyMesh || !avz.sunLight) return;

    const u = avz.skyMesh.material.uniforms;
    let sunPos = [58, 19, -62], sunCol = "#ffd59e", sunInt = 2.85, hemiInt = 0.98, exp = 1.02, bloom = 0.28, intGlow = 15.0, fogCol = "#dfd4c3";

    if (preset === "noon") {
      u.uZenith.value.set("#165082"); u.uMid.value.set("#67a8d4"); u.uHorizon.value.set("#e2eff7");
      u.uCloudTint.value.set("#ffffff");
      sunPos = [28, 78, -34]; sunCol = "#fffaf0"; sunInt = 3.25; hemiInt = 1.12; exp = 0.96; bloom = 0.20; intGlow = 8.0; fogCol = "#dcebf5";
    } else if (preset === "dusk") {
      u.uZenith.value.set("#0b162c"); u.uMid.value.set("#283c5c"); u.uHorizon.value.set("#d97742");
      u.uCloudTint.value.set("#f6ad7b");
      sunPos = [-68, 7.5, -58]; sunCol = "#ff9654"; sunInt = 1.65; hemiInt = 0.62; exp = 1.08; bloom = 0.36; intGlow = 26.0; fogCol = "#36455c";
    } else if (preset === "night") {
      u.uZenith.value.set("#030712"); u.uMid.value.set("#0c1829"); u.uHorizon.value.set("#192940");
      u.uCloudTint.value.set("#334155");
      sunPos = [-32, 48, 42]; sunCol = "#93c5fd"; sunInt = 0.28; hemiInt = 0.30; exp = 1.10; bloom = 0.42; intGlow = 36.0; fogCol = "#0c1626";
    } else {
      // Natural Dubai Golden Hour (Warm Architectural Photography)
      u.uZenith.value.set("#1c4d78"); u.uMid.value.set("#6197ba"); u.uHorizon.value.set("#eccba8");
      u.uCloudTint.value.set("#fff0db");
      sunPos = [58, 19, -62]; sunCol = "#ffd6a0"; sunInt = 2.85; hemiInt = 0.98; exp = 1.02; bloom = 0.28; intGlow = 15.0; fogCol = "#e3d6c4";
    }

    if (avz.scene.fog) avz.scene.fog.color.set(fogCol);
    avz.sunLight.position.set(sunPos[0], sunPos[1], sunPos[2]);
    avz.sunLight.color.set(sunCol);
    avz.sunLight.intensity = sunInt;
    avz.hemiLight.intensity = hemiInt;
    u.uSunDir.value.set(sunPos[0], sunPos[1], sunPos[2]).normalize();
    u.uSunCol.value.set(sunCol);
    if (avz.waterUniforms) {
      avz.waterUniforms.uSunDir.value.copy(u.uSunDir.value);
      avz.waterUniforms.uSunCol.value.set(sunCol);
    }
    if (avz.post) {
      avz.post.compositeMat.uniforms.uExposure.value = exp;
      avz.post.compositeMat.uniforms.uBloomStrength.value = bloom;
    } else if (avz.renderer) {
      avz.renderer.toneMappingExposure = exp;
    }
    avz.interiorLights.forEach(l => { l.intensity = intGlow * (l.userData.mult || 1.0); });

    if (avz.pmremGen) {
      if (!avz.envCache) avz.envCache = {};
      if (!avz.envCache[preset]) {
        const gl = avz.renderer.getContext();
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
        gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
        const envScene = new THREE.Scene();
        const skyClone = new THREE.Mesh(new THREE.SphereGeometry(420, 24, 16), avz.skyMesh.material);
        envScene.add(skyClone);
        avz.envCache[preset] = avz.pmremGen.fromScene(envScene, 0.04);
        skyClone.geometry.dispose();
      }
      avz.envRT = avz.envCache[preset];
      avz.scene.environment = avz.envRT.texture;
      avz.scene.environmentIntensity = (preset === "night") ? 0.35 : 0.78;
    }
  }
  window.setArchvizTimeOfDay = applyTimeOfDayPreset;

  // =========================================================================
  // PART 5: BEVELLED & SCULPTED ARCHITECTURAL / BOTANICAL / AUTOMOTIVE ASSETS
  // =========================================================================
  function getRoundedBoxGeo(w, h, d, radius = 0.04) {
    const r = Math.min(radius, w * 0.35, h * 0.35, d * 0.35);
    const key = `rb_${w.toFixed(2)}_${h.toFixed(2)}_${d.toFixed(2)}_${r.toFixed(3)}`;
    if (avz.geoCache.has(key)) return avz.geoCache.get(key);

    const iw = Math.max(0.01, w - r * 2);
    const ih = Math.max(0.01, h - r * 2);
    const hw = iw * 0.5, hh = ih * 0.5;
    const sh = new THREE.Shape();
    sh.moveTo(-hw, -hh - r);
    sh.lineTo(hw, -hh - r);
    sh.quadraticCurveTo(hw + r, -hh - r, hw + r, -hh);
    sh.lineTo(hw + r, hh);
    sh.quadraticCurveTo(hw + r, hh + r, hw, hh + r);
    sh.lineTo(-hw, hh + r);
    sh.quadraticCurveTo(-hw - r, hh + r, -hw - r, hh);
    sh.lineTo(-hw - r, -hh);
    sh.quadraticCurveTo(-hw - r, -hh - r, -hw, -hh - r);

    const geo = new THREE.ExtrudeGeometry(sh, {
      depth: Math.max(0.01, d - r * 2),
      bevelEnabled: true,
      bevelSegments: 2,
      steps: 1,
      bevelSize: r,
      bevelThickness: r
    });
    geo.center();
    avz.geoCache.set(key, geo);
    return geo;
  }

  function addBox(parent, w, h, d, mat, x, y, z, castShadow = true, receiveShadow = true) {
    const key = `bx_${w.toFixed(2)}_${h.toFixed(2)}_${d.toFixed(2)}`;
    let geo = avz.geoCache.get(key);
    if (!geo) {
      geo = new THREE.BoxGeometry(w, h, d);
      avz.geoCache.set(key, geo);
    }
    const m = new THREE.Mesh(geo, mat);
    m.position.set(x, y, z);
    m.castShadow = castShadow;
    m.receiveShadow = receiveShadow;
    parent.add(m);
    return m;
  }

  function addBevelBox(parent, w, h, d, r, mat, x, y, z, castShadow = true, receiveShadow = true) {
    const m = new THREE.Mesh(getRoundedBoxGeo(w, h, d, r), mat);
    m.position.set(x, y, z);
    m.castShadow = castShadow;
    m.receiveShadow = receiveShadow;
    parent.add(m);
    return m;
  }

  function addSoftShadow(parent, w, d, x, y, z, scaleAlpha = 1.0) {
    const key = `sh_${w.toFixed(2)}_${d.toFixed(2)}`;
    let geo = avz.geoCache.get(key);
    if (!geo) {
      geo = new THREE.PlaneGeometry(w, d);
      geo.rotateX(-Math.PI * 0.5);
      avz.geoCache.set(key, geo);
    }
    const mat = scaleAlpha >= 0.95 ? avz.mats.contactShadow : avz.mats.contactShadow.clone();
    if (scaleAlpha < 0.95) mat.opacity = 0.85 * scaleAlpha;
    const m = new THREE.Mesh(geo, mat);
    m.position.set(x, y + 0.008, z);
    parent.add(m);
    return m;
  }

  function createPhotorealDatePalm(height = 8.6, seed = 0) {
    const g = new THREE.Group();
    addSoftShadow(g, 4.4, 4.4, 0, 0, 0, 0.72);
    const segs = 11;
    const leanDir = (seed % 2 === 0 ? 1 : -1) * (0.65 + (seed % 3) * 0.18);
    const leanZ = ((seed % 5) - 2) * 0.09;
    for (let i = 0; i < segs; i++) {
      const t = i / segs;
      const r0 = 0.29 * (1 - t * 0.36), r1 = 0.26 * (1 - t * 0.36);
      const cyl = new THREE.Mesh(new THREE.CylinderGeometry(r1, r0, height / segs + 0.09, 12), avz.mats.palmTrunk);
      const cx = leanDir * Math.sin(t * 1.42) * 0.44;
      const cz = leanZ * Math.sin(t * 1.3) * 0.35;
      cyl.position.set(cx, (i + 0.5) * (height / segs), cz);
      cyl.rotation.z = -leanDir * Math.cos(t * 1.42) * 0.065;
      cyl.castShadow = true;
      cyl.receiveShadow = true;
      g.add(cyl);
    }
    const topX = leanDir * Math.sin(1.42) * 0.44;
    const topZ = leanZ * Math.sin(1.3) * 0.35;

    // Fibrous Crownshaft + Natural Amber Date Clusters
    const bulb = new THREE.Mesh(new THREE.CylinderGeometry(0.30, 0.21, 0.62, 10), avz.mats.palmTrunk);
    bulb.position.set(topX, height - 0.18, topZ);
    g.add(bulb);

    const dateMat = avz.mats.leatherCognac;
    for (let d = 0; d < 4; d++) {
      const da = (d / 4) * Math.PI * 2 + seed;
      for (let b = 0; b < 3; b++) {
        const cl = new THREE.Mesh(new THREE.SphereGeometry(0.09 - b * 0.015, 7, 7), dateMat);
        cl.position.set(topX + Math.cos(da) * (0.28 + b * 0.07), height - 0.28 - b * 0.13, topZ + Math.sin(da) * (0.28 + b * 0.07));
        g.add(cl);
      }
    }

    // 26 Multi-Tiered Arching Pinnate Fronds (Upper Plume, Mid Canopy, Lower Skirt)
    const crown = new THREE.Group();
    crown.position.set(topX, height, topZ);
    for (let f = 0; f < 26; f++) {
      const tier = f < 7 ? 0 : (f < 17 ? 1 : 2);
      const ang = (f / 26) * Math.PI * 2 + tier * 0.31 + seed * 0.4;
      const frondGrp = new THREE.Group();
      frondGrp.rotation.y = ang;

      const fLen = tier === 0 ? 2.45 : (tier === 1 ? 3.35 : 2.95);
      const fWid = tier === 0 ? 0.92 : 1.16;
      const key = `pfrond_${tier}`;
      let segGeo = avz.geoCache.get(key);
      if (!segGeo) {
        segGeo = new THREE.PlaneGeometry(fWid, fLen, 2, 7);
        const pos = segGeo.attributes.position;
        for (let k = 0; k < pos.count; k++) {
          const vx = pos.getX(k);
          const vy = pos.getY(k);
          const u = Math.max(0, Math.min(1, (vy + fLen * 0.5) / fLen));
          const archZ = u * fLen * (tier === 0 ? 0.68 : 0.90);
          const archY = Math.sin(u * Math.PI * 0.64) * (tier === 0 ? 1.25 : (tier === 1 ? 0.68 : 0.18)) - Math.pow(u, 2.15) * (tier === 2 ? 1.42 : 0.82);
          const vFold = -Math.abs(vx) * 0.18;
          pos.setXYZ(k, vx, archY + vFold, archZ);
        }
        segGeo.computeVertexNormals();
        avz.geoCache.set(key, segGeo);
      }
      const blade = new THREE.Mesh(segGeo, avz.mats.palmFrond);
      blade.castShadow = true;
      frondGrp.add(blade);
      crown.add(frondGrp);
    }
    g.add(crown);
    avz.swayCrowns.push(crown);
    return g;
  }

  function createArchitecturalTree(scale = 1.0, withPlanter = true) {
    const g = new THREE.Group();
    addSoftShadow(g, 2.2 * scale, 2.2 * scale, 0, 0, 0, 0.78);
    let baseH = 0;
    if (withPlanter) {
      const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.42 * scale, 0.32 * scale, 0.62 * scale, 18), avz.mats.travertine);
      pot.position.y = 0.31 * scale;
      pot.castShadow = true; pot.receiveShadow = true;
      g.add(pot);
      const soil = new THREE.Mesh(new THREE.CircleGeometry(0.38 * scale, 16), avz.mats.charcoal);
      soil.rotation.x = -Math.PI * 0.5;
      soil.position.y = 0.625 * scale;
      g.add(soil);
      baseH = 0.55 * scale;
    }
    // Multi-stem gnarled olive branches
    const branches = [
      { rx: 0.12, rz: -0.14, h: 1.45 * scale, tx: 0.18, tz: 0.12 },
      { rx: -0.15, rz: 0.16, h: 1.55 * scale, tx: -0.22, tz: -0.14 },
      { rx: 0.05, rz: 0.06, h: 1.75 * scale, tx: 0.06, tz: 0.06 }
    ];
    branches.forEach((b, bi) => {
      const limb = new THREE.Mesh(new THREE.CylinderGeometry(0.032 * scale, 0.065 * scale, b.h, 8), avz.mats.oak);
      limb.position.set(b.tx * 0.5 * scale, baseH + b.h * 0.48, b.tz * 0.5 * scale);
      limb.rotation.set(b.rx, bi * 1.1, b.rz);
      limb.castShadow = true;
      g.add(limb);

      // Crossed alpha-cutout olive leaf cluster cards for airy organic foliage!
      const cx = b.tx * 1.35 * scale, cy = baseH + b.h + 0.12 * scale, cz = b.tz * 1.35 * scale;
      for (let c = 0; c < 4; c++) {
        const card = new THREE.Mesh(new THREE.PlaneGeometry(1.15 * scale, 0.92 * scale), avz.mats.oliveFoliage);
        card.position.set(cx + Math.cos(c * 1.6) * 0.14 * scale, cy + (c % 2) * 0.16 * scale, cz + Math.sin(c * 1.6) * 0.14 * scale);
        card.rotation.set((c - 1.5) * 0.28, (c * Math.PI) / 4 + bi, 0.15);
        card.castShadow = true;
        g.add(card);
      }
    });
    return g;
  }

  function createOrnamentalGrass(scale = 1.0) {
    const g = new THREE.Group();
    const bladeGeoKey = "grass_blade";
    let bladeGeo = avz.geoCache.get(bladeGeoKey);
    if (!bladeGeo) {
      bladeGeo = new THREE.PlaneGeometry(0.06, 0.72, 1, 4);
      const p = bladeGeo.attributes.position;
      for (let i = 0; i < p.count; i++) {
        const vy = p.getY(i);
        const u = (vy + 0.36) / 0.72;
        p.setXYZ(i, p.getX(i) * (1.0 - u * 0.82), u * 0.62, u * u * 0.36);
      }
      bladeGeo.computeVertexNormals();
      avz.geoCache.set(bladeGeoKey, bladeGeo);
    }
    for (let i = 0; i < 14; i++) {
      const m = new THREE.Mesh(bladeGeo, avz.mats.hedge);
      m.rotation.y = (i / 14) * Math.PI * 2;
      m.scale.setScalar(scale * (0.82 + (i % 3) * 0.14));
      g.add(m);
    }
    return g;
  }

  function createSleekLuxuryCar(paintMat, isSuv = false) {
    const car = new THREE.Group();
    addSoftShadow(car, 2.65, 5.45, 0, 0.01, 0, 0.96);

    // Extruded Aerodynamic Side-Silhouette Body (Sleek GT Coupe / Range-Rover-Class SUV!)
    const profKey = isSuv ? "car_suv_prof" : "car_gt_prof";
    let bodyGeo = avz.geoCache.get(profKey);
    if (!bodyGeo) {
      const sh = new THREE.Shape();
      if (isSuv) {
        sh.moveTo(-2.32, 0.28);
        sh.lineTo(-2.36, 0.78);
        sh.quadraticCurveTo(-2.28, 0.94, -1.52, 0.98);
        sh.lineTo(-0.82, 1.54);
        sh.lineTo(1.58, 1.52);
        sh.lineTo(2.18, 1.02);
        sh.lineTo(2.30, 0.88);
        sh.lineTo(2.32, 0.32);
        sh.closePath();
      } else {
        sh.moveTo(-2.35, 0.24);
        sh.lineTo(-2.38, 0.62);
        sh.quadraticCurveTo(-2.15, 0.78, -1.25, 0.82);
        sh.lineTo(-0.42, 1.26);
        sh.quadraticCurveTo(0.45, 1.28, 1.48, 0.96);
        sh.lineTo(2.26, 0.82);
        sh.lineTo(2.32, 0.28);
        sh.closePath();
      }
      bodyGeo = new THREE.ExtrudeGeometry(sh, {
        depth: 1.76,
        bevelEnabled: true,
        bevelSegments: 3,
        steps: 1,
        bevelSize: 0.11,
        bevelThickness: 0.11
      });
      // Rotate so length is along Z (-Z front, +Z rear), width along X!
      bodyGeo.translate(0, 0, -0.88);
      bodyGeo.rotateY(-Math.PI * 0.5);
      avz.geoCache.set(profKey, bodyGeo);
    }
    const body = new THREE.Mesh(bodyGeo, paintMat);
    body.castShadow = true; body.receiveShadow = true;
    car.add(body);

    // Flush Panoramic Tinted Side Glass + Sloped Front & Rear Windshields + Panoramic Glass Roof!
    const cabY = isSuv ? 1.22 : 1.01;
    const cabLen = isSuv ? 2.45 : 1.92;
    addBevelBox(car, 2.00, isSuv ? 0.44 : 0.34, cabLen * 0.88, 0.05, avz.mats.glassDark, 0, cabY + 0.02, isSuv ? 0.30 : 0.10, false, false);
    addBox(car, 1.56, 0.03, isSuv ? 1.95 : 1.35, avz.mats.glassDark, 0, isSuv ? 1.54 : 1.28, isSuv ? 0.32 : 0.08, false, false);

    const fWind = new THREE.Mesh(new THREE.BoxGeometry(1.68, 0.56, 0.05), avz.mats.glassDark);
    fWind.position.set(0, isSuv ? 1.24 : 1.02, isSuv ? -1.16 : -0.84);
    fWind.rotation.x = isSuv ? -0.68 : -0.92;
    car.add(fWind);

    const rWind = new THREE.Mesh(new THREE.BoxGeometry(1.66, isSuv ? 0.50 : 0.48, 0.05), avz.mats.glassDark);
    rWind.position.set(0, isSuv ? 1.26 : 1.02, isSuv ? 1.88 : 1.48);
    rWind.rotation.x = isSuv ? 0.64 : 0.98;
    car.add(rWind);

    // Sculpted Front Intake Grille + Razor LED DRL Blades
    addBevelBox(car, 1.26, isSuv ? 0.32 : 0.22, 0.08, 0.03, avz.mats.charcoal, 0, isSuv ? 0.62 : 0.48, -2.38);
    [-0.68, 0.68].forEach(hx => {
      addBox(car, 0.36, 0.045, 0.08, avz.mats.ledWarm, hx, isSuv ? 0.80 : 0.64, -2.39, false, false);
    });

    // Sculpted Rear Tailgate: Split Ruby LED Clusters + Thin Horizon Lightbar + Recessed Dubai Plate + Diffuser & Quad Exhausts!
    const tailY = isSuv ? 0.92 : 0.76;
    addBox(car, 1.72, 0.028, 0.07, avz.mats.ledRuby, 0, tailY, 2.34, false, false);
    [-0.66, 0.66].forEach(tx => {
      addBevelBox(car, 0.40, 0.085, 0.08, 0.02, avz.mats.ledRuby, tx, tailY - 0.01, 2.35, false, false);
    });
    // Recessed Rear License Plate Bay + Crisp White Plate
    addBevelBox(car, 0.66, 0.18, 0.06, 0.02, avz.mats.charcoal, 0, tailY - 0.20, 2.34);
    addBox(car, 0.50, 0.11, 0.065, avz.mats.plasterWarm, 0, tailY - 0.20, 2.35, false, false);
    // Matte-Carbon Lower Rear Bumper Diffuser + Dual Twin Chrome Exhaust Tips
    addBevelBox(car, 1.84, 0.22, 0.12, 0.03, avz.mats.charcoal, 0, 0.36, 2.32);
    [-0.64, -0.51, 0.51, 0.64].forEach(ex => {
      const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.042, 0.042, 0.14, 12), avz.mats.chrome);
      pipe.rotation.x = Math.PI * 0.5;
      pipe.position.set(ex, 0.33, 2.37);
      car.add(pipe);
    });

    // Aerodynamic Side Mirrors
    [-0.98, 0.98].forEach(mx => {
      addBevelBox(car, 0.16, 0.09, 0.22, 0.03, paintMat, mx, isSuv ? 1.02 : 0.84, -0.78);
    });

    // Multi-Spoke Alloy Wheels + Low-Profile Michelin Tires + Metallic Brake Discs
    const tireGeo = new THREE.CylinderGeometry(0.37, 0.37, 0.27, 22);
    tireGeo.rotateZ(Math.PI * 0.5);
    const rimGeo = new THREE.CylinderGeometry(0.26, 0.26, 0.285, 16);
    rimGeo.rotateZ(Math.PI * 0.5);
    const hubGeo = new THREE.CylinderGeometry(0.09, 0.09, 0.30, 12);
    hubGeo.rotateZ(Math.PI * 0.5);

    [[-0.94, 0.37, -1.46], [0.94, 0.37, -1.46], [-0.94, 0.37, 1.48], [0.94, 0.37, 1.48]].forEach(([wx, wy, wz]) => {
      const tire = new THREE.Mesh(tireGeo, avz.mats.charcoal);
      tire.position.set(wx, wy, wz);
      tire.castShadow = true;
      car.add(tire);
      const rim = new THREE.Mesh(rimGeo, avz.mats.chrome);
      rim.position.set(wx, wy, wz);
      car.add(rim);
      const hub = new THREE.Mesh(hubGeo, avz.mats.bronze);
      hub.position.set(wx, wy, wz);
      car.add(hub);
    });
    return car;
  }

  function createCurvedDiningChair(seatMat) {
    const ch = new THREE.Group();
    addSoftShadow(ch, 0.68, 0.68, 0, 0, 0, 0.62);
    // Bevelled upholstered seat cushion
    addBevelBox(ch, 0.50, 0.075, 0.48, 0.032, seatMat, 0, 0.45, 0);
    // Curved wrap-around Poliform backrest shell (150-deg open cylinder arc!)
    const arcKey = "chair_arc_shell";
    let shellGeo = avz.geoCache.get(arcKey);
    if (!shellGeo) {
      shellGeo = new THREE.CylinderGeometry(0.255, 0.265, 0.34, 18, 1, true, -Math.PI * 0.42, Math.PI * 0.84);
      avz.geoCache.set(arcKey, shellGeo);
    }
    const back = new THREE.Mesh(shellGeo, seatMat);
    back.position.set(0, 0.64, 0.02);
    back.castShadow = true;
    ch.add(back);

    // 4 Tapered Angled Bronze Legs
    const legGeo = new THREE.CylinderGeometry(0.018, 0.012, 0.45, 8);
    [[-0.19, -0.18, -0.06, 0.06], [0.19, -0.18, -0.06, -0.06], [-0.19, 0.18, 0.06, 0.06], [0.19, 0.18, 0.06, -0.06]].forEach(([lx, lz, rx, rz]) => {
      const leg = new THREE.Mesh(legGeo, avz.mats.bronze);
      leg.position.set(lx, 0.225, lz);
      leg.rotation.set(rx, 0, rz);
      leg.castShadow = true;
      ch.add(leg);
    });
    return ch;
  }

  function createPleatedCurtain(width, height) {
    const key = `curtain_${width.toFixed(2)}_${height.toFixed(2)}`;
    let geo = avz.geoCache.get(key);
    if (!geo) {
      geo = new THREE.PlaneGeometry(width, height, 28, 4);
      const p = geo.attributes.position;
      for (let i = 0; i < p.count; i++) {
        const vx = p.getX(i);
        const wave = Math.sin((vx / Math.max(0.2, width)) * Math.PI * 9.0) * 0.065;
        p.setZ(i, wave);
      }
      geo.computeVertexNormals();
      avz.geoCache.set(key, geo);
    }
    const m = new THREE.Mesh(geo, avz.mats.sheerCurtain);
    return m;
  }

  function createResortUmbrella() {
    const u = new THREE.Group();
    addSoftShadow(u, 2.6, 2.6, 0, 0, 0, 0.55);
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.34, 0.07, 16), avz.mats.travertine);
    base.position.y = 0.035;
    u.add(base);
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.032, 0.038, 2.48, 10), avz.mats.oak);
    pole.position.y = 1.24;
    pole.castShadow = true;
    u.add(pole);
    const canopy = new THREE.Mesh(new THREE.ConeGeometry(1.62, 0.38, 8), avz.mats.fabricBoucle);
    canopy.position.y = 2.40;
    canopy.castShadow = true;
    u.add(canopy);
    return u;
  }

  function createSunLounger() {
    const l = new THREE.Group();
    addSoftShadow(l, 1.05, 2.30, 0, 0, 0, 0.72);
    addBevelBox(l, 0.84, 0.14, 2.06, 0.03, avz.mats.oak, 0, 0.14, 0);
    addBevelBox(l, 0.76, 0.09, 1.34, 0.035, avz.mats.fabricBoucle, 0, 0.25, -0.30);
    const back = new THREE.Mesh(getRoundedBoxGeo(0.76, 0.09, 0.68, 0.035), avz.mats.fabricBoucle);
    back.position.set(0, 0.42, 0.62);
    back.rotation.x = -0.48;
    back.castShadow = true;
    l.add(back);
    // Rolled resort towel
    const towel = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.065, 0.52, 12), avz.mats.fabricTaupe);
    towel.rotation.z = Math.PI * 0.5;
    towel.position.set(0, 0.54, 0.72);
    l.add(towel);
    return l;
  }

  function addCeilingDownlights(group, wx, ceilY, wz, rw, rd) {
    const nx = Math.max(2, Math.min(4, Math.floor(rw / 3.8)));
    const nz = Math.max(2, Math.min(4, Math.floor(rd / 3.8)));
    for (let ix = 0; ix < nx; ix++) {
      for (let iz = 0; iz < nz; iz++) {
        const lx = wx - rw * 0.32 + (nx > 1 ? (ix / (nx - 1)) * rw * 0.64 : 0);
        const lz = wz - rd * 0.32 + (nz > 1 ? (iz / (nz - 1)) * rd * 0.64 : 0);
        const trim = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.02, 12), avz.mats.charcoal);
        trim.position.set(lx, ceilY - 0.01, lz);
        group.add(trim);
        const core = new THREE.Mesh(new THREE.CircleGeometry(0.045, 10), avz.mats.ledWarm);
        core.rotation.x = Math.PI * 0.5;
        core.position.set(lx, ceilY - 0.022, lz);
        group.add(core);
      }
    }
  }

  function populate3DRoomFurniture(group, r, wx, baseY, wz, rw, rd, flHeight) {
    const t = r.type;
    const nm = (r.name || "").toLowerCase();

    if (t === "living") {
      // Woven Berber Rug + Soft Floor Contact Shadow (Golden-Ratio Composition for Wide-Angle FPV!)
      const rugW = Math.min(rw * 0.46, 5.6), rugD = Math.min(rd * 0.50, 4.8);
      const loungeX = wx - Math.min(2.25, rw * 0.14), loungeZ = wz - rd * 0.04;
      addBevelBox(group, rugW, 0.022, rugD, 0.01, avz.mats.rug, loungeX, baseY + 0.03, loungeZ, false, true);

      // Bespoke Bevelled Minotti Bouclé L-Sectional Sofa
      const sw = Math.min(3.35, rw * 0.34), sd = Math.min(2.40, rd * 0.30);
      const mainSofaZ = loungeZ + sd * 0.40;
      addSoftShadow(group, sw + 0.55, 1.45, loungeX, baseY + 0.03, mainSofaZ, 0.92);
      addBevelBox(group, sw + 0.08, 0.09, 1.00, 0.02, avz.mats.oak, loungeX, baseY + 0.08, mainSofaZ);
      // 3 Individual Plump Bevelled Seat Cushions + Back Cushions (Real Cushion Seams!)
      for (let c = 0; c < 3; c++) {
        const cw = (sw - 0.08) / 3;
        const cx = loungeX - sw * 0.5 + cw * (c + 0.5) + 0.04;
        addBevelBox(group, cw - 0.03, 0.24, 0.94, 0.06, avz.mats.fabricBoucle, cx, baseY + 0.24, mainSofaZ);
        addBevelBox(group, cw - 0.04, 0.36, 0.22, 0.06, avz.mats.fabricBoucle, cx, baseY + 0.50, mainSofaZ + 0.36);
      }
      // Chaise Wing on West Side
      const chX = loungeX - sw * 0.5 + 0.50;
      addSoftShadow(group, 1.36, sd + 0.35, chX, baseY + 0.03, loungeZ, 0.88);
      addBevelBox(group, 0.98, 0.09, sd, 0.02, avz.mats.oak, chX, baseY + 0.08, loungeZ);
      addBevelBox(group, 0.94, 0.24, sd - 0.06, 0.06, avz.mats.fabricBoucle, chX, baseY + 0.24, loungeZ);
      addBevelBox(group, 0.22, 0.36, sd - 0.14, 0.06, avz.mats.fabricBoucle, chX - 0.36, baseY + 0.50, loungeZ);

      // Curated Designer Throw Pillows (Muted Olive, Cognac Leather, Charcoal)
      addBevelBox(group, 0.42, 0.32, 0.15, 0.05, avz.mats.leatherCognac, loungeX - 0.64, baseY + 0.48, mainSofaZ + 0.20);
      addBevelBox(group, 0.40, 0.30, 0.15, 0.05, avz.mats.fabricOlive, loungeX + 0.72, baseY + 0.48, mainSofaZ + 0.20);
      addBevelBox(group, 0.38, 0.28, 0.15, 0.05, avz.mats.fabricCharcoal, chX - 0.18, baseY + 0.47, loungeZ - 0.32);

      // Dual-Tier Honed Travertine & Smoked-Bronze Coffee Table + Sculptural Decor
      const ctW = Math.min(1.62, sw * 0.50);
      const ctX = loungeX + 0.20, ctZ = loungeZ - 0.24;
      addSoftShadow(group, ctW + 0.45, 1.35, ctX, baseY + 0.03, ctZ, 0.88);
      addBevelBox(group, ctW * 0.75, 0.22, 0.72, 0.03, avz.mats.bronze, ctX, baseY + 0.14, ctZ);
      addBevelBox(group, ctW, 0.08, 0.96, 0.035, avz.mats.travertine, ctX, baseY + 0.29, ctZ);
      addBevelBox(group, 0.40, 0.055, 0.30, 0.015, avz.mats.fabricCharcoal, ctX - 0.24, baseY + 0.36, ctZ);
      const vessel = new THREE.Mesh(new THREE.LatheGeometry([
        new THREE.Vector2(0.0, 0.0), new THREE.Vector2(0.12, 0.02), new THREE.Vector2(0.16, 0.11),
        new THREE.Vector2(0.10, 0.24), new THREE.Vector2(0.06, 0.28)
      ], 18), avz.mats.brass);
      vessel.position.set(ctX + 0.34, baseY + 0.33, ctZ - 0.05);
      vessel.castShadow = true;
      group.add(vessel);

      // Two Curved Bouclé Accent Armchairs Facing Sofa
      [-0.54, 0.60].forEach(ox => {
        const ax = loungeX + ox * 1.08, az = loungeZ - 1.32;
        addSoftShadow(group, 1.08, 1.08, ax, baseY + 0.03, az, 0.82);
        const cylSeat = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.40, 0.34, 20), avz.mats.fabricTaupe);
        cylSeat.position.set(ax, baseY + 0.20, az);
        cylSeat.castShadow = true;
        group.add(cylSeat);
        const cylBack = new THREE.Mesh(new THREE.CylinderGeometry(0.43, 0.43, 0.36, 18, 1, true, Math.PI * 0.58, Math.PI * 0.84), avz.mats.fabricTaupe);
        cylBack.position.set(ax, baseY + 0.48, az);
        cylBack.castShadow = true;
        group.add(cylBack);
      });

      // Architectural Fluted-Walnut & Bookmatched Marble Linear Fireplace Wall + Gallery Canvas + Olive Tree
      const featWallX = wx - rw * 0.46;
      addBox(group, 0.16, flHeight * 0.84, Math.min(3.8, rd * 0.44), avz.mats.flutedWalnut, featWallX, baseY + flHeight * 0.42, wz);
      addBevelBox(group, 0.46, 0.44, Math.min(3.6, rd * 0.42), 0.03, avz.mats.travertine, featWallX + 0.18, baseY + 0.24, wz);
      // Recessed Linear Bio-Ethanol Fireplace Hearth Strip
      addBox(group, 0.18, 0.22, Math.min(2.0, rd * 0.24), avz.mats.charcoal, featWallX + 0.12, baseY + 0.62, wz);
      addBox(group, 0.06, 0.07, Math.min(1.75, rd * 0.20), avz.mats.ledFire, featWallX + 0.19, baseY + 0.58, wz, false, false);
      // Framed Contemporary Artwork + Brass Picture Light
      addBevelBox(group, 0.06, 1.68, Math.min(2.3, rd * 0.28), 0.015, avz.mats.bronze, featWallX + 0.11, baseY + 1.98, wz);
      addBox(group, 0.04, 1.58, Math.min(2.2, rd * 0.268), avz.mats.artwork, featWallX + 0.135, baseY + 1.98, wz);
      addBox(group, 0.18, 0.035, 0.78, avz.mats.brass, featWallX + 0.20, baseY + 2.90, wz);

      const olive = createArchitecturalTree(1.08, true);
      olive.position.set(wx - Math.min(4.2, rw * 0.34), baseY + 0.03, wz - rd * 0.36);
      group.add(olive);

      // Formal Oval-Bevelled Calacatta Marble Dining Table + Curved Poliform Chairs + Multi-Ring Halo Chandelier
      if (rw >= 5.5 && rd >= 5.5) {
        const dx = wx + Math.min(2.55, rw * 0.175), dz = wz - rd * 0.05;
        const tLen = Math.min(3.85, rd * 0.42);
        addSoftShadow(group, 2.25, tLen + 0.85, dx, baseY + 0.03, dz, 0.90);
        [-tLen * 0.26, tLen * 0.26].forEach(pz => {
          const drum = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.30, 0.71, 20), avz.mats.flutedWalnut);
          drum.position.set(dx, baseY + 0.365, dz + pz);
          drum.castShadow = true;
          group.add(drum);
        });
        addBevelBox(group, 1.34, 0.065, tLen, 0.03, avz.mats.marble, dx, baseY + 0.745, dz);

        const nSide = tLen >= 3.2 ? 4 : 3;
        for (let c = 0; c < nSide; c++) {
          const cz = dz - (tLen * 0.36) + (c / Math.max(1, nSide - 1)) * (tLen * 0.72);
          const chL = createCurvedDiningChair(avz.mats.leatherCognac);
          chL.position.set(dx - 0.92, baseY + 0.02, cz);
          chL.rotation.y = Math.PI * 0.5;
          group.add(chL);
          const chR = createCurvedDiningChair(avz.mats.leatherCognac);
          chR.position.set(dx + 0.92, baseY + 0.02, cz);
          chR.rotation.y = -Math.PI * 0.5;
          group.add(chR);
        }

        if (avz.camStyle !== "cutaway") {
          const chY = baseY + flHeight - 1.02;
          // Suspended fine bronze cables + Dual Brushed-Brass Luminous Rings
          [-0.45, 0.45].forEach(cxOff => {
            const wire = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.95, 6), avz.mats.bronze);
            wire.position.set(dx + cxOff, baseY + flHeight - 0.55, dz);
            group.add(wire);
          });
          [1.06, 0.68].forEach((rad, ri) => {
            const halo = new THREE.Mesh(new THREE.TorusGeometry(rad, 0.028, 14, 48), avz.mats.brass);
            halo.rotation.x = Math.PI * 0.5;
            halo.rotation.y = ri * 0.16;
            halo.position.set(dx, chY - ri * 0.25, dz);
            group.add(halo);
            const glow = new THREE.Mesh(new THREE.TorusGeometry(rad - 0.026, 0.016, 10, 42), avz.mats.ledWarm);
            glow.rotation.x = Math.PI * 0.5;
            glow.rotation.y = ri * 0.16;
            glow.position.set(dx, chY - 0.02 - ri * 0.25, dz);
            group.add(glow);
          });
        }
      }
    } else if (t === "kitchen") {
      // Full-Height Fluted Walnut & Matte Charcoal Gaggenau Cabinetry + Backlit Wine Display + Waterfall Island
      const cabW = rw * 0.86;
      addSoftShadow(group, cabW + 0.3, 1.1, wx, baseY + 0.03, wz + rd * 0.38, 0.90);
      addBox(group, cabW, 2.68, 0.66, avz.mats.flutedWalnut, wx, baseY + 1.35, wz + rd * 0.38);
      addBevelBox(group, 1.42, 0.76, 0.70, 0.02, avz.mats.charcoal, wx - rw * 0.16, baseY + 1.42, wz + rd * 0.38);
      // Warm Backlit Glass Wine Cellar Niche
      addBox(group, 1.08, 2.05, 0.70, avz.mats.glassDark, wx + rw * 0.22, baseY + 1.38, wz + rd * 0.38);
      addBox(group, 0.96, 0.05, 0.56, avz.mats.ledWarm, wx + rw * 0.22, baseY + 2.34, wz + rd * 0.38, false, false);
      addBox(group, 0.96, 0.04, 0.56, avz.mats.ledWarm, wx + rw * 0.22, baseY + 1.42, wz + rd * 0.38, false, false);

      const iw = Math.min(3.5, rw * 0.68);
      addSoftShadow(group, iw + 0.5, 1.6, wx, baseY + 0.03, wz - 0.25, 0.92);
      addBevelBox(group, iw - 0.08, 0.88, 1.06, 0.02, avz.mats.charcoal, wx, baseY + 0.45, wz - 0.25);
      addBevelBox(group, iw, 0.07, 1.14, 0.025, avz.mats.marble, wx, baseY + 0.91, wz - 0.25);
      // Brass Gooseneck Kitchen Faucet + Undermount Sink
      addBox(group, 0.72, 0.02, 0.46, avz.mats.charcoal, wx - iw * 0.18, baseY + 0.95, wz - 0.25);
      const tap = new THREE.Mesh(new THREE.TorusGeometry(0.14, 0.014, 10, 20, Math.PI), avz.mats.brass);
      tap.position.set(wx - iw * 0.18, baseY + 1.12, wz - 0.05);
      group.add(tap);

      for (let s = -1; s <= 1; s++) {
        const st = createCurvedDiningChair(avz.mats.leatherCognac);
        st.scale.set(0.88, 1.28, 0.88);
        st.rotation.y = Math.PI;
        st.position.set(wx + s * (iw * 0.30), baseY + 0.02, wz - 1.04);
        group.add(st);
      }
    } else if (t === "master" || t === "bedroom") {
      // Plush Layered King Suite along West Slatted-Walnut Feature Wall + Panoramic Sea View (-Z)
      const bw = t === "master" ? Math.min(2.25, rd * 0.40) : Math.min(1.90, rd * 0.42);
      const bd = Math.min(2.35, rw * 0.44);
      const bx = wx - rw * 0.44 + bd * 0.5 + 0.20;
      const bz = wz + rd * 0.02;

      addBevelBox(group, bd + 1.15, 0.022, bw + 1.55, 0.01, avz.mats.rug, bx + 0.25, baseY + 0.03, bz, false, true);
      addSoftShadow(group, bd + 0.65, bw + 0.65, bx, baseY + 0.03, bz, 0.94);
      // Recessed Walnut Platform + Plush Bevelled Mattress + Overhanging Linen Duvet + Runner
      addBevelBox(group, bd + 0.22, 0.22, bw + 0.24, 0.03, avz.mats.oak, bx, baseY + 0.14, bz);
      addBevelBox(group, bd, 0.26, bw, 0.07, avz.mats.fabricBoucle, bx, baseY + 0.38, bz);
      addBevelBox(group, bd * 0.72, 0.09, bw + 0.08, 0.04, avz.mats.fabricBoucle, bx + bd * 0.14, baseY + 0.52, bz);
      addBevelBox(group, bd * 0.34, 0.10, bw + 0.10, 0.035, avz.mats.fabricOlive, bx + bd * 0.31, baseY + 0.54, bz);

      // Full-Height Fluted Walnut + Taupe Suede Headboard Wall + Vertical Warm LED Cove Strips
      const hbX = wx - rw * 0.46;
      addBox(group, 0.14, flHeight * 0.86, bw + 1.85, avz.mats.flutedWalnut, hbX, baseY + flHeight * 0.43, bz);
      addBevelBox(group, 0.18, 1.16, bw + 0.24, 0.05, avz.mats.fabricTaupe, hbX + 0.07, baseY + 0.72, bz);
      [-1, 1].forEach(sd => {
        addBox(group, 0.05, flHeight * 0.80, 0.04, avz.mats.ledWarm, hbX + 0.09, baseY + flHeight * 0.42, bz + sd * (bw * 0.5 + 0.22), false, false);
      });
      addBox(group, 0.05, 1.18, Math.min(1.75, bw * 0.76), avz.mats.artwork, hbX + 0.09, baseY + 2.22, bz);

      // 4 Plump Layered Sleeping & Accent Pillows
      [-0.24, 0.24].forEach(pz => {
        addBevelBox(group, 0.38, 0.22, bw * 0.40, 0.06, avz.mats.fabricBoucle, bx - bd * 0.33, baseY + 0.60, bz + pz * bw);
        addBevelBox(group, 0.30, 0.20, bw * 0.32, 0.05, avz.mats.leatherCognac, bx - bd * 0.21, baseY + 0.59, bz + pz * bw);
      });

      // Floating Travertine Nightstands + Suspended Alabaster Pendant Globes
      [-1, 1].forEach(sd => {
        const nz = bz + sd * (bw * 0.5 + 0.48), nx = hbX + 0.36;
        addSoftShadow(group, 0.65, 0.72, nx, baseY + 0.03, nz, 0.65);
        addBevelBox(group, 0.48, 0.22, 0.56, 0.03, avz.mats.travertine, nx, baseY + 0.34, nz);
        const cord = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.005, flHeight - 0.85, 6), avz.mats.bronze);
        cord.position.set(nx, baseY + 0.72 + (flHeight - 0.85) * 0.5, nz);
        group.add(cord);
        const globe = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 14), avz.mats.ledWarm);
        globe.position.set(nx, baseY + 0.72, nz);
        group.add(globe);
      });

      // Upholstered End-of-Bed Bench + Olive Tree
      addSoftShadow(group, 0.68, bw * 0.92, bx + bd * 0.64, baseY + 0.03, bz, 0.80);
      addBevelBox(group, 0.48, 0.42, bw * 0.84, 0.05, avz.mats.fabricTaupe, bx + bd * 0.64, baseY + 0.22, bz);
      const tree = createArchitecturalTree(0.92, true);
      tree.position.set(wx + rw * 0.36, baseY + 0.03, wz - rd * 0.36);
      group.add(tree);
    } else if (t === "bath") {
      // Sculpted Hollow Oval Stone Bathtub + Brass Floor Filler + Floating Double Vanity + Backlit Pill Mirrors
      const tubX = wx - rw * 0.18, tubZ = wz - rd * 0.18;
      addSoftShadow(group, 1.95, 1.15, tubX, baseY + 0.03, tubZ, 0.88);
      const tubOuter = new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.38, 0.58, 28, 1, true), avz.mats.marble);
      tubOuter.scale.set(1.82, 1, 0.95);
      tubOuter.position.set(tubX, baseY + 0.30, tubZ);
      tubOuter.castShadow = true;
      group.add(tubOuter);
      const tubRim = new THREE.Mesh(new THREE.TorusGeometry(0.475, 0.032, 12, 32), avz.mats.marble);
      tubRim.rotation.x = Math.PI * 0.5;
      tubRim.scale.set(1.82, 0.95, 1);
      tubRim.position.set(tubX, baseY + 0.59, tubZ);
      group.add(tubRim);
      const filler = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.022, 0.82, 10), avz.mats.brass);
      filler.position.set(tubX - 0.95, baseY + 0.42, tubZ);
      group.add(filler);

      const vw = Math.min(2.3, rw * 0.58), vx = wx + rw * 0.14, vz = wz + rd * 0.32;
      addBevelBox(group, vw, 0.48, 0.60, 0.025, avz.mats.flutedWalnut, vx, baseY + 0.58, vz);
      addBevelBox(group, vw + 0.04, 0.07, 0.62, 0.02, avz.mats.marble, vx, baseY + 0.85, vz);
      [-vw * 0.26, vw * 0.26].forEach(mx => {
        const basin = new THREE.Mesh(new THREE.CylinderGeometry(0.21, 0.16, 0.13, 20), avz.mats.marble);
        basin.position.set(vx + mx, baseY + 0.95, vz);
        group.add(basin);
        addBevelBox(group, 0.56, 1.08, 0.04, 0.24, avz.mats.ledWarm, vx + mx, baseY + 1.68, vz + 0.26, false, false);
        addBevelBox(group, 0.52, 1.04, 0.05, 0.22, avz.mats.chrome, vx + mx, baseY + 1.68, vz + 0.25);
      });
    } else if (t === "core" || t === "void") {
      // Floating Cantilevered Oak Treads + Frameless Glass Balustrade + Panoramic Glass Elevator
      const steps = 13;
      const runLen = Math.min(3.8, rd * 0.68);
      for (let s = 0; s < steps; s++) {
        const f = s / steps;
        addBevelBox(group, Math.min(1.42, rw * 0.34), 0.085, 0.33, 0.02, avz.mats.oak, wx - rw * 0.22, baseY + 0.24 + f * (flHeight - 0.28), wz + runLen * 0.5 - f * runLen);
      }
      addBox(group, 0.04, 0.98, runLen, avz.mats.glassBalustrade, wx - rw * 0.22 + 0.72, baseY + flHeight * 0.46, wz, false, false);
      addBox(group, 1.56, flHeight * 0.95, 1.56, avz.mats.glassBalustrade, wx + rw * 0.22, baseY + flHeight * 0.48, wz, false, false);
      addBevelBox(group, 1.66, 0.10, 1.66, 0.02, avz.mats.bronze, wx + rw * 0.22, baseY + 0.06, wz);
    } else if (t === "garage") {
      const nCars = Math.max(1, Math.min(4, Math.floor(rw / 3.1)));
      const paints = [avz.mats.carPaintMidnight, avz.mats.carPaintChampagne, avz.mats.carPaintObsidian, avz.mats.carPaintSilver];
      for (let c = 0; c < nCars; c++) {
        const car = createSleekLuxuryCar(paints[c % paints.length], c % 2 === 0);
        const cx = wx - ((nCars - 1) * 1.48) + c * 2.96;
        car.position.set(cx, baseY + 0.02, wz);
        group.add(car);
      }
    } else if (t === "wellness") {
      if (nm.includes("cinema")) {
        addBox(group, rw * 0.78, 2.05, 0.08, avz.mats.oledScreen, wx, baseY + 1.45, wz - rd * 0.43, false, false);
        addBevelBox(group, rw * 0.68, 0.44, 0.98, 0.06, avz.mats.fabricCharcoal, wx, baseY + 0.24, wz + 0.15);
        addBevelBox(group, rw * 0.68, 0.64, 0.98, 0.06, avz.mats.fabricCharcoal, wx, baseY + 0.34, wz + 1.55);
      } else {
        addBevelBox(group, 0.88, 1.28, 1.90, 0.04, avz.mats.charcoal, wx - rw * 0.22, baseY + 0.64, wz);
        addBevelBox(group, 0.98, 0.52, 2.05, 0.05, avz.mats.fabricBoucle, wx + rw * 0.22, baseY + 0.28, wz);
      }
    } else if (t === "pool") {
      // Hollow Perimeter Calacatta Marble Coping + Turquoise Glass Mosaic Basin + Planar-Reflected Water + Sunbeds & Parasols!
      const pw = Math.max(2.5, rw - 1.2), pd = Math.max(2.5, rd - 2.4);
      const pcz = wz - 0.45, copeW = 0.28;
      // 4 Perimeter Honed Marble Coping Curbs (keeps center open so mosaic basin shines through!)
      addBevelBox(group, pw + copeW * 2, 0.14, copeW, 0.025, avz.mats.marble, wx, baseY + 0.08, pcz - pd * 0.5 - copeW * 0.5, false, true);
      addBevelBox(group, pw + copeW * 2, 0.14, copeW, 0.025, avz.mats.marble, wx, baseY + 0.08, pcz + pd * 0.5 + copeW * 0.5, false, true);
      addBevelBox(group, copeW, 0.14, pd, 0.025, avz.mats.marble, wx - pw * 0.5 - copeW * 0.5, baseY + 0.08, pcz, false, true);
      addBevelBox(group, copeW, 0.14, pd, 0.025, avz.mats.marble, wx + pw * 0.5 + copeW * 0.5, baseY + 0.08, pcz, false, true);
      // Deep Turquoise Sukabumi / Glass Mosaic Pool Basin + Underwater Cove Strip
      addBox(group, pw, 0.03, pd, avz.mats.poolTile, wx, baseY + 0.045, pcz, false, true);
      addBox(group, pw * 0.92, 0.025, 0.04, avz.mats.ledWarm, wx, baseY + 0.09, pcz + pd * 0.48, false, false);
      const waterMesh = new THREE.Mesh(new THREE.PlaneGeometry(pw, pd, 4, 4), avz.mats.water);
      waterMesh.rotation.x = -Math.PI * 0.5;
      waterMesh.position.set(wx, baseY + 0.145, pcz);
      group.add(waterMesh);
      avz.reflectiveMeshes.push(waterMesh);

      const nBeds = Math.min(5, Math.max(2, Math.floor(rw / 4.4)));
      const deckZ = wz + rd * 0.36;
      for (let b = 0; b < nBeds; b++) {
        const bx = wx - ((nBeds - 1) * 1.35) + b * 2.70;
        const lounger = createSunLounger();
        lounger.position.set(bx, baseY + 0.04, deckZ);
        group.add(lounger);
        if (b < nBeds - 1 && b % 2 === 0) {
          const umb = createResortUmbrella();
          umb.position.set(bx + 1.35, baseY + 0.04, deckZ + 0.28);
          group.add(umb);
        }
      }
    }
  }

  // =========================================================================
  // PART 6: SCENE A — PHOTOREALISTIC BOULEVARD & FROND STREET WALKTHROUGH
  // =========================================================================
  function buildArchvizStreetScene() {
    disposeArchvizScene();
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0xe3d6c4, 0.0013);
    avz.scene = scene;
    avz.reflectPlaneY = 0.10;
    avz.walkSurfaceY = 0.08;
    avz.walkBounds = { minX: -7.2, maxX: 7.2, minZ: -128, maxZ: 38 };
    setupSkyAndLighting(scene);

    const soc = getSocietyData(wtState.projectId || "PRJ-D19");
    const stop = (soc && soc.street_tour && soc.street_tour[wtState.stopIndex]) || (soc && soc.street_tour && soc.street_tour[0]);
    const zone = stop ? ((soc.zones || []).find(z => z.zone_id === stop.zone_id) || soc.zones[0]) : (soc ? soc.zones[0] : null);
    const isPJA = (wtState.projectId === "PRJ-D2");
    const isFrondOrWater = isPJA || (stop && /Lagoon|Lanai|Serenity|Frond|Spine/i.test(stop.title));

    // Base Terrain + Weathered Granite Asphalt Boulevard + Bevelled Granite Kerbstones + Travertine Sidewalks
    addBox(scene, 300, 0.2, 300, avz.mats.sand, 0, -0.16, -45, false, true);
    addBox(scene, 9.4, 0.06, 204, avz.mats.asphalt, 0, 0.01, -42, false, true);

    [-1, 1].forEach(side => {
      // Bevelled granite curbstone + honed travertine pedestrian promenade + manicured bermudagrass verge
      addBevelBox(scene, 0.28, 0.17, 204, 0.03, avz.mats.graniteKerb, side * 4.84, 0.085, -42, true, true);
      addBox(scene, 3.8, 0.15, 204, avz.mats.travertine, side * 6.88, 0.075, -42, false, true);
      addBox(scene, 28, 0.13, 204, avz.mats.lawn, side * 22.8, 0.055, -42, false, true);
      // Sculpted Boxwood Hedge along Villa Boundary (NO pink macaron balls!)
      addBevelBox(scene, 0.72, 0.74, 190, 0.14, avz.mats.hedge, side * 9.05, 0.44, -42);
    });

    if (!isPJA) {
      // Subtle Muted Architectural Terracotta-Sandstone Cycle Path on Right Promenade
      addBox(scene, 1.35, 0.156, 204, avz.mats.cycleSandstone, 5.72, 0.078, -42, false, true);
    }

    // Flanking Turquoise Lagoon / Arabian Gulf Channels (with Real-Time Planar Reflection!)
    if (isFrondOrWater) {
      [-58, 58].forEach(wx => {
        const sideSea = new THREE.Mesh(new THREE.PlaneGeometry(58, 224, 4, 4), avz.mats.water);
        sideSea.rotation.x = -Math.PI * 0.5;
        sideSea.position.set(wx, 0.10, -45);
        scene.add(sideSea);
        avz.reflectiveMeshes.push(sideSea);
      });
    }

    // North Waterfront Horizon (-Z): White-Sand Beach + Planar-Reflected Lagoon / Arabian Gulf
    addBox(scene, 300, 0.16, 10, avz.mats.sand, 0, 0.04, -142, false, true);
    const sea = new THREE.Mesh(new THREE.PlaneGeometry(340, 160, 4, 4), avz.mats.water);
    sea.rotation.x = -Math.PI * 0.5;
    sea.position.set(0, 0.10, -218);
    scene.add(sea);
    avz.reflectiveMeshes.push(sea);

    // Distant Atmospheric-Haze Dubai Coastline Silhouettes across the water
    for (let i = -11; i <= 11; i++) {
      if (isPJA && Math.abs(i) < 4) continue;
      const th = 18 + ((Math.abs(i * 41 + 13) % 44));
      const tw = 7.2 + (Math.abs(i) % 3) * 2.4;
      addBox(scene, tw, th, tw, avz.mats.skyline, i * 13.0, th * 0.5, -285 - (Math.abs(i) % 4) * 11, false, false);
    }

    // Sleek Sculpted Luxury Cars Cruising on the Boulevard
    const roadCar1 = createSleekLuxuryCar(avz.mats.carPaintChampagne, true);
    roadCar1.position.set(2.35, 0.04, 3.5);
    scene.add(roadCar1);
    const roadCar2 = createSleekLuxuryCar(avz.mats.carPaintMidnight, false);
    roadCar2.rotation.y = Math.PI;
    roadCar2.position.set(-2.35, 0.04, -32.0);
    scene.add(roadCar2);

    // 10 Architect-Grade Contemporary Mansions (3 Distinct SAOTA / BLINK / WATG Archetypes!)
    const carPaints = [avz.mats.carPaintSilver, avz.mats.carPaintObsidian, avz.mats.carPaintMidnight, avz.mats.carPaintChampagne];
    const villaTyps = Object.values(DATA.walkthroughs.typologies || {}).filter(t => t.project_id === (wtState.projectId || "PRJ-D19"));
    const defTypId = zone ? zone.default_typology_id : (villaTyps[0] ? villaTyps[0].id : "TYP-TAG-SERENITY-6BR");

    for (let row = 0; row < 5; row++) {
      const vz = 30 - row * 32;
      [-1, 1].forEach((side, sIdx) => {
        const archetype = (row + sIdx) % 3;
        const vx = side * 22.4;
        const gateX = side * 9.55;
        const vGrp = new THREE.Group();

        // Honed Roman Travertine Boundary Wall + Dark Bronze Coping + Slatted Privacy Screen + Open Porphyry Driveway
        addBox(vGrp, 0.38, 1.25, 10.2, avz.mats.travertine, gateX, 0.625, vz - 8.0);
        addBevelBox(vGrp, 0.44, 0.08, 10.3, 0.02, avz.mats.bronze, gateX, 1.28, vz - 8.0);
        // Horizontal Bronze Architectural Slats above Plinth Wall
        for (let sl = 0; sl < 5; sl++) {
          addBox(vGrp, 0.08, 0.07, 9.8, avz.mats.bronze, gateX, 1.44 + sl * 0.16, vz - 8.0);
        }
        addBox(vGrp, 0.38, 2.10, 5.8, avz.mats.travertine, gateX, 1.05, vz + 9.4);
        addBevelBox(vGrp, 0.44, 0.08, 5.9, 0.02, avz.mats.bronze, gateX, 2.14, vz + 9.4);

        // Feature Travertine Gate Totem + Warm Backlit Laser-Cut Villa Plaque
        addBox(vGrp, 0.68, 2.48, 1.35, avz.mats.travertine, gateX, 1.24, vz - 2.4);
        addBevelBox(vGrp, 0.72, 0.28, 0.86, 0.02, avz.mats.charcoal, gateX, 1.56, vz - 2.4);
        addBox(vGrp, 0.74, 0.05, 0.72, avz.mats.ledWarm, gateX, 1.41, vz - 2.4, false, false);

        // Porphyry Cobblestone Forecourt + Parked Sculpted GT / SUV
        addBox(vGrp, 14.2, 0.14, 8.8, avz.mats.cobble, side * 15.4, 0.07, vz + 2.5, false, true);
        const car = createSleekLuxuryCar(carPaints[(row + sIdx) % carPaints.length], (row + sIdx) % 2 === 0);
        car.rotation.y = side < 0 ? Math.PI * 0.44 : -Math.PI * 0.44;
        car.position.set(side * 13.6, 0.14, vz + 2.4);
        vGrp.add(car);

        // Ornamental Grasses & Olive Tree in Front Courtyard
        const olive = createArchitecturalTree(1.25, true);
        olive.position.set(gateX + side * 2.1, 0.12, vz - 5.6);
        vGrp.add(olive);
        for (let gr = -1; gr <= 1; gr++) {
          const grass = createOrnamentalGrass(0.95);
          grass.position.set(gateX - side * 0.62, 0.14, vz - 7.8 + gr * 2.2);
          vGrp.add(grass);
        }

        // Ground-Floor Mansion Massing + Double-Height Mullioned Glass Atrium + Visible Interior Chandelier & Stairs!
        const gfMat = archetype === 1 ? avz.mats.plasterSand : avz.mats.plasterWarm;
        addBox(vGrp, 15.6, 4.5, 19.2, gfMat, vx, 2.25, vz - 0.5);
        addBox(vGrp, 1.6, 4.7, 3.4, avz.mats.travertine, vx - side * 7.4, 2.35, vz - 7.2);
        // Tall Walnut Pivot Front Door + Bronze Portico Canopy
        addBox(vGrp, 0.22, 3.5, 1.75, avz.mats.flutedWalnut, vx - side * 7.75, 1.75, vz + 3.2);
        addBevelBox(vGrp, 2.8, 0.18, 3.8, 0.03, avz.mats.bronze, vx - side * 8.6, 3.65, vz + 3.2);
        // Double-Height Atrium Curtain Wall with Slim Bronze Mullions
        addBox(vGrp, 0.18, 4.2, 10.4, avz.mats.glass, vx - side * 7.82, 2.20, vz - 1.4, false, false);
        for (let m = -2; m <= 2; m++) {
          addBox(vGrp, 0.24, 4.25, 0.08, avz.mats.bronze, vx - side * 7.85, 2.20, vz - 1.4 + m * 2.1);
        }
        const streetHalo = new THREE.Mesh(new THREE.TorusGeometry(0.68, 0.032, 10, 28), avz.mats.ledWarm);
        streetHalo.rotation.x = Math.PI * 0.5;
        streetHalo.position.set(vx - side * 5.6, 3.65, vz - 1.4);
        vGrp.add(streetHalo);

        // Cantilevered Upper Master Volume + Slatted Walnut Soffit + Recessed Downlights + Mashrabiya Screens!
        const cantShift = archetype === 0 ? 1.55 : (archetype === 1 ? 0.95 : 1.25);
        const upperMat = archetype === 2 ? avz.mats.plasterWarm : avz.mats.travertine;
        addBox(vGrp, 17.0, 3.9, 15.8, upperMat, vx - side * cantShift, 6.45, vz - 1.2);
        addBox(vGrp, 17.1, 0.16, 15.9, avz.mats.flutedWalnut, vx - side * cantShift, 4.46, vz - 1.2);
        addBox(vGrp, 0.12, 0.06, 15.2, avz.mats.ledWarm, vx - side * (cantShift + 8.42), 4.40, vz - 1.2, false, false);
        addBox(vGrp, 0.20, 3.4, 11.2, avz.mats.glass, vx - side * (cantShift + 8.45), 6.32, vz - 1.2, false, false);
        addBox(vGrp, 0.08, 1.10, 15.2, avz.mats.glassBalustrade, vx - side * (cantShift + 8.58), 5.05, vz - 1.2, false, false);

        // Vertical Bronze Mashrabiya Privacy Fin Screen on Upper Facade
        const nFins = archetype === 0 ? 9 : 6;
        for (let lv = 0; lv < nFins; lv++) {
          addBox(vGrp, 0.22, 3.72, 0.10, avz.mats.bronze, vx - side * (cantShift + 8.54), 6.35, vz - 6.8 + lv * 0.46);
        }

        // Penthouse Sky Lounge + Architectural Bronze Pergola Louvres
        addBox(vGrp, 10.6, 0.34, 10.2, avz.mats.charcoal, vx, 8.56, vz - 1.0);
        for (let l = -5; l <= 5; l++) {
          addBox(vGrp, 9.8, 0.10, 0.16, avz.mats.bronze, vx - side * 2.2, 10.85, vz - 1.0 + l * 0.58);
        }
        addBox(vGrp, 0.22, 2.45, 0.22, avz.mats.bronze, vx - side * 6.9, 9.60, vz - 3.6);
        addBox(vGrp, 0.22, 2.45, 0.22, avz.mats.bronze, vx - side * 6.9, 9.60, vz + 1.6);

        // Tall Date Palms Framing the Mansion
        const gPalm = createPhotorealDatePalm(9.4 + (row % 2) * 0.8, row * 5 + sIdx + 1);
        gPalm.position.set(vx + side * 4.2, 0.10, vz - 8.8);
        vGrp.add(gPalm);

        const ptLight = new THREE.PointLight(0xffd699, 1.0, 22, 1.4);
        ptLight.userData.mult = 0.18;
        ptLight.position.set(vx - side * 6.2, 3.8, vz - 1.0);
        vGrp.add(ptLight);
        avz.interiorLights.push(ptLight);

        scene.add(vGrp);

        // Register Interactive 3D Floating Villa Gate Pins on Foremost Mansions!
        if (row <= 1) {
          const pinTyp = villaTyps[(row + sIdx) % Math.max(1, villaTyps.length)];
          const tId = pinTyp ? pinTyp.id : defTypId;
          const shortTitle = pinTyp ? pinTyp.title.split("—")[0].trim() : "Flagship Villa";
          avz.worldPins.push({
            pos: new THREE.Vector3(gateX, 2.85, vz + 0.5),
            label: `🏠 Villa 0${row * 2 + sIdx + 1} · ${shortTitle} — Enter 3D →`,
            onClick: () => openVillaInteriorModal(tId)
          });
        }
      });

      // Boulevard Date Palms, Architectural Path Bollards & Sleek Dark-Bronze Street Luminaires
      [-7.85, 7.85].forEach((px, pi) => {
        const palm = createPhotorealDatePalm(8.5 + ((row + pi) % 3) * 0.85, row * 3 + pi + 7);
        palm.position.set(px, 0.12, vz - 10.4);
        scene.add(palm);

        // Recessed Louvered Landscape Bollard
        addBevelBox(scene, 0.16, 0.82, 0.16, 0.03, avz.mats.bronze, px * 0.96, 0.48, vz - 2.8);
        addBox(scene, 0.17, 0.08, 0.17, avz.mats.ledWarm, px * 0.96, 0.78, vz - 2.8, false, false);

        // Minimalist Tapered Bronze Street Lamp Pole
        const poleX = px * 0.63;
        const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.048, 0.075, 5.6, 10), avz.mats.bronze);
        pole.position.set(poleX, 2.85, vz + 5.2);
        pole.castShadow = true;
        scene.add(pole);
        addBevelBox(scene, 0.88, 0.08, 0.24, 0.02, avz.mats.bronze, poleX - Math.sign(px) * 0.38, 5.62, vz + 5.2);
        addBox(scene, 0.72, 0.04, 0.18, avz.mats.ledWarm, poleX - Math.sign(px) * 0.38, 5.57, vz + 5.2, false, false);
      });
    }

    avz.streetPortalPos = { x: 9.2, y: 1.70, z: 2.2, defaultTypology: defTypId };
    avz.camStyle = "fpv";
    avz.camera.fov = 48;
    avz.camera.updateProjectionMatrix();
    avz.camPos = { x: 1.35, y: 1.70, z: 33.5 };
    avz.camVel = { x: 0, z: 0 };
    avz.camTargetPos = null;
    avz.camTargetYaw = null;
    avz.yaw = 0.045;
    avz.pitch = 0.025;
    avz.autoWaypoints = [
      { x: 1.35, y: 1.70, z: 34, yaw: 0.05 },
      { x: 0.5, y: 1.70, z: 8, yaw: -0.22 },
      { x: -0.6, y: 1.70, z: -22, yaw: 0.20 },
      { x: 0.3, y: 1.70, z: -58, yaw: -0.14 },
      { x: 0.0, y: 1.70, z: -98, yaw: 0.0 }
    ];
    applyTimeOfDayPreset(avz.timeOfDay);
  }

  // =========================================================================
  // PART 7: SCENE B — PHOTOREALISTIC VILLA INTERIOR, CUTAWAY & EXPLODED STACK
  // =========================================================================
  function buildArchvizVillaScene() {
    disposeArchvizScene();
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0xe3d6c4, 0.00042);
    avz.scene = scene;

    const typ = DATA.walkthroughs.typologies[avz.typologyId] || Object.values(DATA.walkthroughs.typologies)[0];
    if (!typ) return;
    const pw = typ.plot_w, pd = typ.plot_d;

    const activeFl = typ.floors.find(f => f.level === avz.floorKey) || typ.floors[0];
    const isSingleCutaway = (avz.camStyle === "cutaway");
    const isExploded = (avz.camStyle === "dollhouse" && avz.exploded);
    const activeBaseY = isSingleCutaway ? 0 : activeFl.elevation_m;

    // Reflect across polished marble floor in FPV, or across Lagoon/Pool water in Orbit/Cutaway!
    avz.reflectPlaneY = (avz.camStyle === "fpv") ? (activeBaseY + 0.045) : 0.12;
    avz.walkSurfaceY = activeBaseY + 0.04;
    avz.walkBounds = { minX: -pw * 0.45, maxX: pw * 0.45, minZ: -pd * 0.45, maxZ: pd * 0.45 };

    setupSkyAndLighting(scene);
    avz.camera.fov = (avz.camStyle === "fpv") ? 55 : 42;
    avz.camera.updateProjectionMatrix();

    // Resort Estate Context: Sand Beach (-Z North), Planar-Reflected Lagoon / Gulf, Manicured Lawn, Arrival Street (+Z South)
    addBox(scene, 320, 0.3, 320, avz.mats.sand, 0, -0.24, 0, false, true);
    addBox(scene, pw + 4.0, 0.14, pd + 2.8, avz.mats.lawn, 0, -0.06, 0, false, true);
    // Continuous Large-Format Rectified Limestone Plinth & Courtyard Deck (Realistic 1.2m Tile Scale!)
    addBevelBox(scene, pw * 0.92, 0.10, pd * 0.86, 0.03, avz.mats.terracePaver, 0, -0.01, -pd * 0.02, false, true);
    // Porphyry Cobblestone Arrival Forecourt at South Entrance (+Z)
    addBox(scene, pw * 0.86, 0.11, 4.2, avz.mats.cobble, 0, -0.005, pd * 0.43, false, true);

    addBox(scene, 260, 0.12, 9.0, avz.mats.sand, 0, -0.02, -pd * 0.5 - 4.2, false, true);
    addBox(scene, 180, 0.10, 9.5, avz.mats.asphalt, 0, -0.02, pd * 0.5 + 6.8, false, true);

    const ocean = new THREE.Mesh(new THREE.PlaneGeometry(320, 165, 4, 4), avz.mats.water);
    ocean.rotation.x = -Math.PI * 0.5;
    ocean.position.set(0, 0.10, -pd * 0.5 - 88);
    scene.add(ocean);
    avz.reflectiveMeshes.push(ocean);

    // Estate Perimeter Travertine Walls, Boxwood Hedges, Olive Trees & Framing Date Palms
    [-pw * 0.5 - 0.35, pw * 0.5 + 0.35].forEach((wx, sideIdx) => {
      addBox(scene, 0.34, 2.15, pd * 0.86, avz.mats.travertine, wx, 1.08, pd * 0.04);
      addBevelBox(scene, 0.40, 0.07, pd * 0.865, 0.02, avz.mats.bronze, wx, 2.18, pd * 0.04);
      addBevelBox(scene, 0.68, 0.82, pd * 0.82, 0.12, avz.mats.hedge, wx + (wx < 0 ? 0.52 : -0.52), 0.44, pd * 0.04);
      for (let p = -1; p <= 1; p++) {
        const palm = createPhotorealDatePalm(8.4 + Math.abs(p) * 0.9, sideIdx * 7 + p + 3);
        palm.position.set(wx + (wx < 0 ? -1.4 : 1.4), 0, p * (pd * 0.28) - 2.5);
        scene.add(palm);
      }
    });

    const floorsToBuild = isSingleCutaway
      ? typ.floors.filter(f => f.level === avz.floorKey)
      : typ.floors;

    if (isExploded && floorsToBuild.length > 1) {
      const totalH = (floorsToBuild.length - 1) * 9.5 + 5.0;
      [[-pw * 0.43, -pd * 0.28], [pw * 0.43, -pd * 0.28], [-pw * 0.43, pd * 0.36], [pw * 0.43, pd * 0.36]].forEach(([gx, gz]) => {
        addBox(scene, 0.09, totalH, 0.09, avz.mats.bronze, gx, totalH * 0.5 - 2.0, gz, false, false);
      });
    }

    floorsToBuild.forEach((fl, fIdx) => {
      const explodeOffset = isExploded ? fIdx * 9.5 : 0;
      const baseY = (isSingleCutaway ? 0 : fl.elevation_m) + explodeOffset;
      const flH = fl.height_m || 3.8;
      const wallH = isSingleCutaway ? 2.40 : (isExploded ? 1.48 : flH - 0.18);
      const showSectionCap = isSingleCutaway || isExploded;

      if (baseY >= -0.05 || isExploded) {
        // Smooth Architectural Plaster Slab + Slim Dark-Bronze Fascia Edge (Zero stretched brick soffits!)
        addBox(scene, pw * 0.92, 0.14, pd * 0.80, avz.mats.plasterWarm, 0, baseY - 0.07, pd * 0.05, true, true);
        if (baseY > 1.0) {
          addBox(scene, pw * 0.925, 0.08, 0.16, avz.mats.bronze, 0, baseY - 0.06, pd * 0.05 - pd * 0.40);
          addBox(scene, pw * 0.88, 0.025, 3.2, avz.mats.flutedWalnut, 0, baseY - 0.145, pd * 0.05 - pd * 0.40 + 1.8, false, false);
        }
        if (isExploded && fIdx > 0) {
          addBox(scene, pw * 0.93, 0.07, pd * 0.81, avz.mats.bronze, 0, baseY - 0.15, pd * 0.05, false, false);
        }
      } else {
        addBox(scene, pw * 0.88, 0.18, pd * 0.68, avz.mats.plasterWarm, 0, baseY - 0.09, pd * 0.08, true, true);
      }

      const hasNorthTerraceRoom = fl.rooms.some(rm => rm.type === "terrace" && (rm.z + rm.d >= pd * 0.65));

      fl.rooms.forEach(r => {
        const wx = (r.x + r.w * 0.5) - pw * 0.5;
        const wz = pd * 0.5 - (r.z + r.d * 0.5);
        const rw = r.w, rd = r.d;

        let isMarble = true;
        let floorMat = avz.mats.marble;
        if (r.type === "bedroom" || r.type === "master" || r.type === "wellness") {
          floorMat = avz.mats.oak; isMarble = false;
        } else if (r.type === "terrace" || r.type === "pool") {
          floorMat = avz.mats.terracePaver; isMarble = false;
        } else if (r.type === "garage") {
          floorMat = avz.mats.cobble; isMarble = false;
        }

        addBox(scene, rw - 0.04, 0.04, rd - 0.04, floorMat, wx, baseY + 0.02, wz, false, true);

        // Add Real-Time Glossy Planar Reflection Overlay on Active-Floor Marble Rooms in FPV!
        if (isMarble && avz.camStyle === "fpv" && fl.level === avz.floorKey) {
          const reflQuad = new THREE.Mesh(new THREE.PlaneGeometry(rw - 0.08, rd - 0.08), avz.mats.marbleReflectOverlay);
          reflQuad.rotation.x = -Math.PI * 0.5;
          reflQuad.position.set(wx, baseY + 0.044, wz);
          scene.add(reflQuad);
          avz.reflectiveMeshes.push(reflQuad);
        }

        if (r.type !== "pool" && r.type !== "terrace" && r.type !== "garden") {
          const wt = 0.22;
          const northZ = wz - rd * 0.5, southZ = wz + rd * 0.5;
          const westX = wx - rw * 0.5, eastX = wx + rw * 0.5;
          const facesWaterfront = (r.z + r.d >= pd * 0.50);

          // North Wall (-Z, facing Infinity Pool & Lagoon): Slim Vitrocsa Sliding Glass + Open Center Pocket + Pleated Sheer Curtains!
          if (facesWaterfront) {
            // Top & bottom recessed bronze sliding tracks
            addBox(scene, rw, 0.06, 0.14, avz.mats.bronze, wx, baseY + 0.04, northZ);
            addBox(scene, rw, 0.08, 0.14, avz.mats.bronze, wx, baseY + wallH - 0.04, northZ);
            // Flanking glass panels (center panel slid open for indoor-outdoor resort flow!)
            addBox(scene, rw * 0.34, wallH - 0.08, 0.04, avz.mats.glass, westX + rw * 0.17, baseY + wallH * 0.5, northZ, false, false);
            addBox(scene, rw * 0.34, wallH - 0.08, 0.04, avz.mats.glass, eastX - rw * 0.17, baseY + wallH * 0.5, northZ, false, false);
            [-0.16, 0.16, -0.49, 0.49].forEach(mf => {
              addBox(scene, 0.055, wallH, 0.10, avz.mats.bronze, wx + rw * mf, baseY + wallH * 0.5, northZ);
            });
            if (!showSectionCap && rw > 4.2) {
              const cL = createPleatedCurtain(1.05, wallH - 0.10);
              cL.position.set(westX + 0.62, baseY + wallH * 0.5, northZ + 0.20);
              scene.add(cL);
              const cR = createPleatedCurtain(1.05, wallH - 0.10);
              cR.position.set(eastX - 0.62, baseY + wallH * 0.5, northZ + 0.20);
              scene.add(cR);
            }
            // Cantilevered Sea-View Glass Balcony + Resort Lounge Chairs on Upper Waterfront Suites!
            if (baseY > 1.0 && !hasNorthTerraceRoom) {
              const balD = 2.8;
              const balZ = northZ - balD * 0.5;
              addBox(scene, rw, 0.05, balD, avz.mats.terracePaver, wx, baseY + 0.02, balZ, false, true);
              addBox(scene, rw, 1.06, 0.05, avz.mats.glassBalustrade, wx, baseY + 0.55, northZ - balD, false, false);
              addBox(scene, rw, 0.045, 0.08, avz.mats.bronze, wx, baseY + 1.09, northZ - balD);
              if (rw >= 6.0 && (r.type === "master" || r.type === "bedroom")) {
                const lng = createSunLounger();
                lng.position.set(wx + rw * 0.16, baseY + 0.04, balZ + 0.15);
                scene.add(lng);
              }
            }
          } else {
            const doorW = Math.min(1.65, rw * 0.36);
            const segW = Math.max(0.25, (rw - doorW) * 0.5);
            addBox(scene, segW, wallH, wt, avz.mats.plasterWarm, westX + segW * 0.5, baseY + wallH * 0.5, northZ);
            addBox(scene, segW, wallH, wt, avz.mats.plasterWarm, eastX - segW * 0.5, baseY + wallH * 0.5, northZ);
            // Architectural bronze door portal frame + recessed lintel
            if (!showSectionCap && wallH > 2.7) {
              addBox(scene, doorW + 0.16, wallH - 2.55, wt, avz.mats.plasterWarm, wx, baseY + 2.55 + (wallH - 2.55) * 0.5, northZ);
              addBox(scene, doorW + 0.06, 0.05, wt - 0.04, avz.mats.bronze, wx, baseY + 2.55, northZ);
            }
            if (showSectionCap) {
              addBox(scene, segW, 0.055, wt + 0.02, avz.mats.pocheCap, westX + segW * 0.5, baseY + wallH + 0.028, northZ, false, false);
              addBox(scene, segW, 0.055, wt + 0.02, avz.mats.pocheCap, eastX - segW * 0.5, baseY + wallH + 0.028, northZ, false, false);
            }
          }

          // South Wall (+Z) — solid if exterior facade or wet/culinary back wall
          const hasSouthNeighbor = fl.rooms.some(o => o !== r && o.type !== "terrace" && o.type !== "pool" && Math.abs((o.z + o.d) - r.z) < 0.35 && o.x < r.x + r.w - 0.5 && o.x + o.w > r.x + 0.5);
          const isOuterSouth = (!hasSouthNeighbor && baseY > 0.5) || r.type === "bath" || r.type === "kitchen";
          if (r.type === "garage") {
            if (!showSectionCap) addBox(scene, rw, 0.45, wt, avz.mats.bronze, wx, baseY + wallH - 0.22, southZ);
          } else if (isOuterSouth) {
            addBox(scene, rw, wallH, wt, avz.mats.plasterWarm, wx, baseY + wallH * 0.5, southZ);
            addBox(scene, rw, 0.07, wt + 0.03, avz.mats.bronze, wx, baseY + 0.06, southZ);
            if (showSectionCap) addBox(scene, rw, 0.055, wt + 0.02, avz.mats.pocheCap, wx, baseY + wallH + 0.028, southZ, false, false);
          } else {
            const doorW = Math.min(1.65, rw * 0.36);
            const segW = Math.max(0.25, (rw - doorW) * 0.5);
            addBox(scene, segW, wallH, wt, avz.mats.plasterWarm, westX + segW * 0.5, baseY + wallH * 0.5, southZ);
            addBox(scene, segW, wallH, wt, avz.mats.plasterWarm, eastX - segW * 0.5, baseY + wallH * 0.5, southZ);
            if (!showSectionCap && wallH > 2.7) {
              addBox(scene, doorW + 0.16, wallH - 2.55, wt, avz.mats.plasterWarm, wx, baseY + 2.55 + (wallH - 2.55) * 0.5, southZ);
              addBox(scene, doorW + 0.06, 0.05, wt - 0.04, avz.mats.bronze, wx, baseY + 2.55, southZ);
            }
            if (showSectionCap) {
              addBox(scene, segW, 0.055, wt + 0.02, avz.mats.pocheCap, westX + segW * 0.5, baseY + wallH + 0.028, southZ, false, false);
              addBox(scene, segW, 0.055, wt + 0.02, avz.mats.pocheCap, eastX - segW * 0.5, baseY + wallH + 0.028, southZ, false, false);
            }
          }

          // West & East Partition / Perimeter Facade Walls (Topological Neighbor Check!)
          const doorD = Math.min(1.65, rd * 0.34);
          const sideSeg = Math.max(0.25, (rd - doorD) * 0.5);
          const hasWestNeighbor = fl.rooms.some(o => o !== r && o.type !== "terrace" && o.type !== "pool" && Math.abs((o.x + o.w) - r.x) < 0.35 && o.z < r.z + r.d - 0.5 && o.z + o.d > r.z + 0.5);
          const hasEastNeighbor = fl.rooms.some(o => o !== r && o.type !== "terrace" && o.type !== "pool" && Math.abs(o.x - (r.x + r.w)) < 0.35 && o.z < r.z + r.d - 0.5 && o.z + o.d > r.z + 0.5);
          [westX, eastX].forEach((sx, sideIdx) => {
            const isOuterSide = (sideIdx === 0 && !hasWestNeighbor) || (sideIdx === 1 && !hasEastNeighbor);
            if (isOuterSide) {
              addBox(scene, wt, wallH, rd, avz.mats.plasterWarm, sx, baseY + wallH * 0.5, wz);
              addBox(scene, wt + 0.03, 0.07, rd, avz.mats.bronze, sx, baseY + 0.06, wz);
              if (showSectionCap) addBox(scene, wt + 0.02, 0.055, rd, avz.mats.pocheCap, sx, baseY + wallH + 0.028, wz, false, false);
            } else {
              addBox(scene, wt, wallH, sideSeg, avz.mats.plasterWarm, sx, baseY + wallH * 0.5, northZ + sideSeg * 0.5);
              addBox(scene, wt, wallH, sideSeg, avz.mats.plasterWarm, sx, baseY + wallH * 0.5, southZ - sideSeg * 0.5);
              addBox(scene, wt + 0.03, 0.07, sideSeg, avz.mats.bronze, sx, baseY + 0.06, northZ + sideSeg * 0.5);
              addBox(scene, wt + 0.03, 0.07, sideSeg, avz.mats.bronze, sx, baseY + 0.06, southZ - sideSeg * 0.5);
              if (!showSectionCap && wallH > 2.7) {
                addBox(scene, wt, wallH - 2.55, doorD + 0.16, avz.mats.plasterWarm, sx, baseY + 2.55 + (wallH - 2.55) * 0.5, wz);
              }
              if (showSectionCap) {
                addBox(scene, wt + 0.02, 0.055, sideSeg, avz.mats.pocheCap, sx, baseY + wallH + 0.028, northZ + sideSeg * 0.5, false, false);
                addBox(scene, wt + 0.02, 0.055, sideSeg, avz.mats.pocheCap, sx, baseY + wallH + 0.028, southZ - sideSeg * 0.5, false, false);
              }
            }
          });

          // Architectural Coffered Gypsum Ceiling + Fluted Walnut Coffer + 2700K Cove + Recessed Downlights!
          if (!showSectionCap) {
            const ceilY = baseY + flH - 0.21;
            addBox(scene, rw, 0.10, rd, avz.mats.ceilingWhite, wx, ceilY, wz, false, false);
            if (rw >= 4.5 && rd >= 4.5) {
              addBox(scene, rw * 0.58, 0.045, rd * 0.54, avz.mats.flutedWalnut, wx, ceilY - 0.06, wz, false, false);
              addBox(scene, rw * 0.78, 0.03, 0.07, avz.mats.ledWarm, wx, ceilY - 0.055, wz - rd * 0.36, false, false);
              addBox(scene, rw * 0.78, 0.03, 0.07, avz.mats.ledWarm, wx, ceilY - 0.055, wz + rd * 0.36, false, false);
              addCeilingDownlights(scene, wx, ceilY - 0.04, wz, rw, rd);
            }
            if (r.type === "living" || r.type === "master" || r.type === "kitchen" || r.type === "void" || r.type === "bath") {
              const pl = new THREE.PointLight(0xffe6bf, 15.0, 26, 1.35);
              pl.userData.mult = 1.0;
              pl.position.set(wx, ceilY - 0.52, wz);
              scene.add(pl);
              avz.interiorLights.push(pl);
            }
          }
        } else if (r.type === "terrace" && (baseY > 1.0 || isExploded)) {
          addBox(scene, rw, 1.08, 0.06, avz.mats.glassBalustrade, wx, baseY + 0.54, wz - rd * 0.5, false, false);
          addBox(scene, rw, 0.05, 0.09, avz.mats.bronze, wx, baseY + 1.09, wz - rd * 0.5);
          addBox(scene, 0.06, 1.08, rd, avz.mats.glassBalustrade, wx - rw * 0.5, baseY + 0.54, wz, false, false);
          addBox(scene, 0.06, 1.08, rd, avz.mats.glassBalustrade, wx + rw * 0.5, baseY + 0.54, wz, false, false);
        }

        populate3DRoomFurniture(scene, r, wx, baseY, wz, rw, rd, flH);

        // In Cutaway / Dollhouse mode, add clean 3D clickable room pins so user can jump straight into FPV!
        if (avz.camStyle !== "fpv" && fl.level === avz.floorKey) {
          const shortRm = r.name.split("&")[0].split("+")[0].trim().slice(0, 22);
          avz.worldPins.push({
            pos: new THREE.Vector3(wx, baseY + (isExploded ? 2.1 : 2.65), wz),
            label: `👁️ ${shortRm}`,
            onClick: () => { avz.camStyle = "fpv"; avz.exploded = false; buildArchvizVillaScene(); teleportVillaRoom(r.id); refreshArchvizHeaderAndHud(); }
          });
        }
      });
    });

    avz.autoWaypoints = activeFl.rooms.map(r => {
      const cam = computeIdealRoomCamera(r, activeFl, typ, isSingleCutaway);
      return { x: cam.x, y: cam.y, z: cam.z, yaw: cam.yaw, roomId: r.id };
    });

    applyTimeOfDayPreset(avz.timeOfDay);
  }

  function computeIdealRoomCamera(r, fl, typ, isCutaway = false) {
    const pw = typ.plot_w, pd = typ.plot_d;
    const wx = (r.x + r.w * 0.5) - pw * 0.5;
    const wz = pd * 0.5 - (r.z + r.d * 0.5);
    const rw = r.w, rd = r.d;
    const y = (isCutaway ? 0 : fl.elevation_m) + 1.58;
    let cx = wx, cz = wz + rd * 0.42, fx = wx, fz = wz - rd * 0.30, pitch = -0.03;

    if (r.type === "living") {
      cx = wx + rw * 0.01;
      cz = wz + rd * 0.5 - 0.55;
      fx = wx - rw * 0.01;
      fz = wz - rd * 0.28;
      pitch = -0.03;
    } else if (r.type === "master" || r.type === "bedroom") {
      cx = wx + rw * 0.5 - Math.min(1.25, rw * 0.14);
      cz = wz + rd * 0.5 - Math.min(1.05, rd * 0.12);
      fx = wx - rw * 0.13;
      fz = wz - rd * 0.14;
      pitch = -0.025;
    } else if (r.type === "kitchen") {
      cx = wx - rw * 0.30;
      cz = wz - rd * 0.43;
      fx = wx + rw * 0.08;
      fz = wz + rd * 0.14;
      pitch = -0.05;
    } else if (r.type === "bath") {
      cx = wx - rw * 0.28;
      cz = wz - rd * 0.44;
      fx = wx + rw * 0.03;
      fz = wz + rd * 0.06;
      pitch = -0.10;
    } else if (r.type === "pool") {
      cx = wx - rw * 0.32;
      cz = wz + rd * 0.42;
      fx = wx + rw * 0.05;
      fz = wz - rd * 0.25;
      pitch = -0.06;
    }
    const yaw = Math.atan2(cx - fx, cz - fz);
    return { x: cx, y, z: cz, yaw, pitch };
  }

  // =========================================================================
  // PART 8: RIGHT-SIDE-UP ARCHITECTURAL BROCHURE & DARK-NAVY CAD BLUEPRINT
  // =========================================================================
  const CAD_ROOM_STYLES = {
    living:   { cad: "#0c2545", bro: "#f6f1e7", stroke: "#1e293b" },
    kitchen:  { cad: "#0e294d", bro: "#ede4d3", stroke: "#1e293b" },
    master:   { cad: "#102c54", bro: "#e7d8c5", stroke: "#1e293b" },
    bedroom:  { cad: "#0d2647", bro: "#eadbc8", stroke: "#1e293b" },
    bath:     { cad: "#0a2e4d", bro: "#e2e8f0", stroke: "#1e293b" },
    core:     { cad: "#0b223f", bro: "#f1ebe1", stroke: "#1e293b" },
    void:     { cad: "#0b223f", bro: "#f1ebe1", stroke: "#1e293b" },
    garage:   { cad: "#091d36", bro: "#d6dce5", stroke: "#1e293b" },
    staff:    { cad: "#0b223f", bro: "#e2e8f0", stroke: "#1e293b" },
    wellness: { cad: "#112a4f", bro: "#e5d4c0", stroke: "#1e293b" },
    terrace:  { cad: "#09213c", bro: "#e9e0ce", stroke: "#475569" },
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
        const tx = rx + rw * 0.74, ty = cy - 22, tw = 22, th = Math.min(46, rd * 0.45);
        s += `<rect x="${tx - tw * 0.5}" y="${ty}" width="${tw}" height="${th}" rx="5" fill="${fFill}" stroke="${fStr}" stroke-width="1.2"/>`;
        for (let i = 0; i < 3; i++) {
          const chy = ty + 6 + i * ((th - 12) / 2);
          s += `<rect x="${tx - tw * 0.5 - 6}" y="${chy - 3}" width="4.5" height="7" rx="1.5" fill="${fSub}" stroke="${fStr}" stroke-width="0.9"/>`;
          s += `<rect x="${tx + tw * 0.5 + 1.5}" y="${chy - 3}" width="4.5" height="7" rx="1.5" fill="${fSub}" stroke="${fStr}" stroke-width="0.9"/>`;
        }
      }
    } else if ((t === "master" || t === "bedroom") && rw > 42 && rd > 42) {
      // West-wall King Bed + Headboard + Dual Nightstands (matches 3D room layout 1:1!)
      const bd = Math.min(40, rw * 0.46), bw = Math.min(34, rd * 0.44);
      const bx = rx + 6, by = cy - bw * 0.5;
      s += `<rect x="${bx}" y="${by}" width="${bd}" height="${bw}" rx="2" fill="${fFill}" stroke="${fStr}" stroke-width="1.2"/>`;
      s += `<line x1="${bx + bd * 0.65}" y1="${by}" x2="${bx + bd * 0.65}" y2="${by + bw}" stroke="${fStr}" stroke-width="0.9"/>`;
      s += `<rect x="${bx + 3}" y="${by + 3}" width="7" height="${bw * 0.40}" rx="1.5" fill="${fSub}" stroke="${fStr}" stroke-width="0.9"/>`;
      s += `<rect x="${bx + 3}" y="${by + bw * 0.54}" width="7" height="${bw * 0.40}" rx="1.5" fill="${fSub}" stroke="${fStr}" stroke-width="0.9"/>`;
      s += `<rect x="${bx}" y="${by - 7}" width="6" height="5" rx="1" fill="${fSub}" stroke="${fStr}" stroke-width="0.8"/>`;
      s += `<rect x="${bx}" y="${by + bw + 2}" width="6" height="5" rx="1" fill="${fSub}" stroke="${fStr}" stroke-width="0.8"/>`;
    } else if (t === "kitchen" && rw > 42 && rd > 42) {
      s += `<rect x="${rx + 5}" y="${ry + rd - 14}" width="${rw - 10}" height="10" fill="${fSub}" stroke="${fStr}" stroke-width="1.1"/>`;
      const iw = Math.min(rw * 0.56, 48);
      s += `<rect x="${cx - iw * 0.5}" y="${cy - 8}" width="${iw}" height="15" rx="1.5" fill="${fFill}" stroke="${fStr}" stroke-width="1.2"/>`;
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
      s += `<rect x="${rx + 6}" y="${ry + 6}" width="${Math.max(8, rw - 12)}" height="${Math.max(8, rd - 16)}" rx="3" fill="#0891b2" fill-opacity="0.52" stroke="#38bdf8" stroke-width="1.2"/>`;
      for (let b = 0; b < 4; b++) {
        s += `<rect x="${cx - 34 + b * 19}" y="${ry + rd - 8}" width="11" height="5.5" rx="1" fill="${fFill}" stroke="${fStr}" stroke-width="0.9"/>`;
      }
    }
    return s;
  }

  function splitTwoLines(text, maxCh) {
    if (text.length <= maxCh) return [text, ""];
    const words = text.split(/\s+/);
    let l1 = "", l2 = "";
    for (const w of words) {
      if ((l1 + " " + w).trim().length <= maxCh) l1 = (l1 + " " + w).trim();
      else l2 = (l2 + " " + w).trim();
    }
    if (!l1) { l1 = text.slice(0, maxCh); l2 = text.slice(maxCh); }
    if (l2.length > maxCh) l2 = l2.slice(0, maxCh - 1) + "…";
    return [l1, l2];
  }

  function renderRightSideUpCadSvg() {
    const container = document.getElementById("archvizSvgContainer");
    if (!container) return;
    const typ = DATA.walkthroughs.typologies[avz.typologyId];
    if (!typ) return;
    const activeFl = typ.floors.find(f => f.level === avz.floorKey) || typ.floors[0];

    const pw = typ.plot_w, pd = typ.plot_d;
    const scale = Math.max(12.5, Math.min(24, 455 / Math.max(pw, pd)));
    const padL = 48, padT = 54, padR = 38, padB = 76;
    const W = Math.round(pw * scale + padL + padR);
    const H = Math.round(pd * scale + padT + padB);
    const isBrochure = (avz.cadStyle === "brochure");
    container.style.background = isBrochure ? "#0d1424" : "#040c1a";

    const sheetBg  = isBrochure ? "#f6f3ec" : "#061529";
    const sheetBdr = isBrochure ? "#94a3b8" : "#1e3a8a";
    const plotFill = isBrochure ? "#dce7d0" : "#081b33";
    const deckFill = isBrochure ? "#ece5d5" : "#0b2240";
    const plotStr  = isBrochure ? "#475569" : "#38bdf8";
    const gridStr  = isBrochure ? "rgba(100,116,139,0.28)" : "rgba(56,189,248,0.24)";
    const dimCol   = isBrochure ? "#334155" : "#7dd3fc";

    const cols = ["A", "B", "C", "D", "E"];
    const gridX = [0, 0.25, 0.5, 0.75, 1.0].map((f, i) => {
      const gx = padL + pw * f * scale;
      return `<line x1="${gx}" y1="${padT - 6}" x2="${gx}" y2="${padT + pd * scale + 6}" stroke="${gridStr}" stroke-width="0.7" stroke-dasharray="3,3"/>
              <circle cx="${gx}" cy="${padT - 15}" r="7" fill="${isBrochure ? '#fff' : '#0c2545'}" stroke="${plotStr}" stroke-width="1"/>
              <text x="${gx}" y="${padT - 12.2}" text-anchor="middle" font-size="7.8" font-weight="800" fill="${isBrochure ? '#0f172a' : '#e0f2fe'}">${cols[i]}</text>`;
    }).join("");

    const dimLeftSvg = `
      <line x1="20" y1="${padT}" x2="20" y2="${padT + pd * scale}" stroke="${dimCol}" stroke-width="1"/>
      <line x1="15" y1="${padT}" x2="26" y2="${padT}" stroke="${dimCol}" stroke-width="1.2"/>
      <line x1="15" y1="${padT + pd * scale}" x2="26" y2="${padT + pd * scale}" stroke="${dimCol}" stroke-width="1.2"/>
      <text x="13" y="${padT + (pd * scale) * 0.5}" text-anchor="middle" font-size="7.8" font-weight="800" fill="${dimCol}" transform="rotate(-90 13 ${padT + (pd * scale) * 0.5})">PLOT DEPTH ${pd.toFixed(1)}m</text>
    `;

    // 2D Architectural Palm Canopy Symbols along Plot Margins
    const palmPlanSvg = [0.18, 0.52, 0.82].map(fz => {
      const py = padT + pd * fz * scale;
      return [padL + 9, padL + pw * scale - 9].map(px => {
        const col = isBrochure ? "rgba(34,120,62,0.38)" : "rgba(52,211,153,0.22)";
        return `<circle cx="${px}" cy="${py}" r="8" fill="${col}" stroke="${isBrochure ? '#15803d' : '#34d399'}" stroke-width="0.7"/>`;
      }).join("");
    }).join("");

    const roomsHtml = activeFl.rooms.map(r => {
      // RIGHT-SIDE-UP NORTH-UP TRANSFORM:
      // r.z = 0 (Garage / South Street Arrival) -> BOTTOM of sheet!
      // r.z = pd (Infinity Pool / North Lagoon/Sea) -> TOP of sheet!
      const rx = padL + r.x * scale;
      const ry = padT + (pd - (r.z + r.d)) * scale;
      const rw = r.w * scale;
      const rd = r.d * scale;
      const st = CAD_ROOM_STYLES[r.type] || CAD_ROOM_STYLES.core;
      const fillCol = isBrochure ? st.bro : st.cad;
      const isSel = (r.id === avz.selectedRoomId);
      const isOutdoor = (r.type === "pool" || r.type === "terrace");
      const sqft = Math.round(r.w * r.d * 10.7639);

      const wallStroke = isSel ? "#10b981" : (isBrochure ? "#0f172a" : "#bae6fd");
      const wallW = isSel ? 4.2 : (isOutdoor ? 1.5 : 3.2);
      let openingsSvg = "";
      if (!isOutdoor && r.z + r.d >= pd * 0.50) {
        openingsSvg += `<line x1="${rx + 4}" y1="${ry}" x2="${rx + rw - 4}" y2="${ry}" stroke="#06b6d4" stroke-width="4.0"/>`;
        openingsSvg += `<line x1="${rx + 4}" y1="${ry}" x2="${rx + rw - 4}" y2="${ry}" stroke="#e0f2fe" stroke-width="1.2"/>`;
      }
      if (!isOutdoor && rw > 34 && rd > 34) {
        const dr = Math.min(12.5, rw * 0.22);
        const dx = rx + rw * 0.5 - dr * 0.5, dy = ry + rd;
        openingsSvg += `<line x1="${dx}" y1="${dy}" x2="${dx + dr}" y2="${dy}" stroke="${fillCol}" stroke-width="4.4"/>`;
        openingsSvg += `<path d="M ${dx} ${dy} L ${dx} ${dy - dr} A ${dr} ${dr} 0 0 1 ${dx + dr} ${dy}" fill="none" stroke="${isBrochure ? '#334155' : '#38bdf8'}" stroke-width="1.0"/>`;
      }

      const furnSvg = draw2DFurnitureSvg(r, rx, ry, rw, rd, isBrochure);
      const pillW = Math.max(28, Math.min(rw - 5, 118));
      const maxCh = Math.max(8, Math.floor(pillW / 4.5));
      const [line1, line2] = splitTwoLines(r.name, maxCh);
      const hasL2 = Boolean(line2 && rd >= 46);
      const pillH = rd >= 46 ? (hasL2 ? 32 : 24) : 15;
      const lblY = ry + rd * 0.50;
      const pillBg = isBrochure ? "rgba(255,255,255,0.90)" : "rgba(2,6,23,0.86)";
      const pillTxt = isBrochure ? "#0f172a" : "#f8fafc";
      const pillSub = isBrochure ? "#0369a1" : "#38bdf8";
      const fSz = rw < 58 ? 6.3 : (rw < 76 ? 7.0 : 7.8);

      return `
        <g style="cursor:pointer;" onclick="teleportVillaRoom('${r.id}')">
          <rect x="${rx}" y="${ry}" width="${rw}" height="${rd}" fill="${fillCol}" stroke="${wallStroke}" stroke-width="${wallW}"/>
          ${furnSvg}
          ${openingsSvg}
          <rect x="${rx + rw * 0.5 - pillW * 0.5}" y="${lblY - pillH * 0.5}" width="${pillW}" height="${pillH}" rx="3.5" fill="${pillBg}" stroke="${isSel ? '#10b981' : 'none'}" stroke-width="1.2"/>
          <text x="${rx + rw * 0.5}" y="${lblY - (hasL2 ? 6.5 : (rd >= 46 ? 2.5 : -2.5))}" text-anchor="middle" font-size="${fSz}" font-weight="800" fill="${pillTxt}">${line1}</text>
          ${hasL2 ? `<text x="${rx + rw * 0.5}" y="${lblY + 2.2}" text-anchor="middle" font-size="${fSz - 0.3}" font-weight="700" fill="${pillTxt}">${line2}</text>` : ""}
          ${rd >= 46 ? `<text x="${rx + rw * 0.5}" y="${lblY + (hasL2 ? 11.2 : 7.5)}" text-anchor="middle" font-size="${Math.max(5.8, fSz - 1.0)}" font-weight="700" fill="${pillSub}">${r.w.toFixed(1)}×${r.d.toFixed(1)}m · ${sqft} sf</text>` : ""}
        </g>
      `;
    }).join("");

    const fullFloorHeader = `${activeFl.level} — ${activeFl.name}`;
    const safeFloorHeader = fullFloorHeader.length > 44 ? fullFloorHeader.slice(0, 42) + "…" : fullFloorHeader;

    container.innerHTML = `
      <svg id="archvizFloorSvg" viewBox="0 0 ${W} ${H}" data-pw="${pw}" data-pd="${pd}" data-scale="${scale}" data-padl="${padL}" data-padt="${padT}" style="width:100%; max-height:100%; font-family:Inter,system-ui,sans-serif; user-select:none;">
        <rect x="2" y="2" width="${W - 4}" height="${H - 4}" rx="8" fill="${sheetBg}" stroke="${sheetBdr}" stroke-width="1.5"/>
        <!-- TOP WATERFRONT / LAGOON / SEA ORIENTATION HEADER (NORTH UP) -->
        <rect x="${padL}" y="8" width="${pw * scale}" height="19" rx="4" fill="#0891b2"/>
        <text x="${padL + (pw * scale) * 0.5}" y="20.5" text-anchor="middle" font-size="8.0" font-weight="900" fill="#ffffff" letter-spacing="0.03em">🌊 ▲ PRIVATE LAGOON / ARABIAN GULF WATERFRONT VIEW (NORTH) ▲</text>
        ${gridX}
        ${dimLeftSvg}
        <!-- Plot Landscape + Paved Architectural Terrace Envelope -->
        <rect x="${padL}" y="${padT}" width="${pw * scale}" height="${pd * scale}" fill="${plotFill}" stroke="${plotStr}" stroke-width="1.5" stroke-dasharray="5,3"/>
        <rect x="${padL + pw * 0.05 * scale}" y="${padT + pd * 0.06 * scale}" width="${pw * 0.90 * scale}" height="${pd * 0.86 * scale}" rx="3" fill="${deckFill}" stroke="${gridStr}" stroke-width="1"/>
        ${palmPlanSvg}
        ${roomsHtml}
        <!-- LIVE 3D CAMERA POSITION & FOV CONE OVERLAY -->
        <g id="cadLiveCamMarker" pointer-events="none"></g>
        <!-- BOTTOM STREET ARRIVAL / MAIN ENTRANCE INDICATOR (SOUTH DOWN) -->
        <rect x="${padL}" y="${padT + pd * scale + 7}" width="${pw * scale}" height="19" rx="4" fill="#1e293b"/>
        <text x="${padL + (pw * scale) * 0.5}" y="${padT + pd * scale + 19.5}" text-anchor="middle" font-size="7.8" font-weight="900" fill="#34d399" letter-spacing="0.03em">▲ MAIN STREET ARRIVAL, FORECOURT &amp; GARAGE ENTRANCE ▲</text>
        <!-- Architectural Title Block -->
        <g transform="translate(${padL}, ${padT + pd * scale + 30})">
          <rect x="0" y="0" width="${pw * scale}" height="38" rx="5" fill="#0f172a" stroke="${isBrochure ? 'none' : '#1e3a8a'}"/>
          <text x="9" y="15" font-size="8.2" font-weight="800" fill="#38bdf8">${safeFloorHeader}</text>
          <text x="9" y="28.5" font-size="7.1" fill="#cbd5e1">Plot: ${pw}m×${pd}m · Elev +${activeFl.elevation_m.toFixed(1)}m · H ${activeFl.height_m.toFixed(1)}m · ${typ.contractor.split('(')[0].trim().slice(0, 24)}</text>
          <g transform="translate(${pw * scale - 22}, 19)">
            <circle cx="0" cy="0" r="10" fill="#0284c7" stroke="#bae6fd" stroke-width="1.2"/>
            <polygon points="0,-7 3.6,4.5 0,1.6 -3.6,4.5" fill="#ffffff"/>
            <text x="0" y="-12" text-anchor="middle" font-size="6.0" font-weight="900" fill="#38bdf8">N</text>
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
    const sx = padL + (avz.camPos.x + pw * 0.5) * sc;
    const sy = padT + (avz.camPos.z + pd * 0.5) * sc;
    const deg = (-avz.yaw * 180) / Math.PI;
    g.innerHTML = `
      <g transform="translate(${sx.toFixed(1)}, ${sy.toFixed(1)}) rotate(${deg.toFixed(1)})">
        <polygon points="0,0 -19,-32 19,-32" fill="rgba(16,185,129,0.34)" stroke="#10b981" stroke-width="1"/>
        <circle cx="0" cy="0" r="5.5" fill="#10b981" stroke="#ffffff" stroke-width="2"/>
      </g>
    `;
  }

  // =========================================================================
  // PART 9: EFFORTLESS 3-STEP HUD, CLICK-TO-WALK RAYCAST & 3D WORLD PINS
  // =========================================================================
  function updateProjectedWorldPins() {
    const layer = document.getElementById("avzWorldPinsLayer");
    if (!layer || !avz.camera || !avz.renderer) return;
    const canvas = avz.renderer.domElement;
    const w = canvas.clientWidth || 800, h = canvas.clientHeight || 600;

    if (!avz.worldPins.length) {
      if (layer.childElementCount > 0) layer.innerHTML = "";
      return;
    }
    while (layer.children.length < avz.worldPins.length) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "avz-world-pin";
      layer.appendChild(btn);
    }
    while (layer.children.length > avz.worldPins.length) {
      layer.removeChild(layer.lastChild);
    }

    const tmpV = new THREE.Vector3();
    avz.worldPins.forEach((pin, idx) => {
      const el = layer.children[idx];
      tmpV.copy(pin.pos);
      const dist = avz.camera.position.distanceTo(tmpV);
      tmpV.project(avz.camera);
      if (tmpV.z > 1.0 || tmpV.z < -1.0 || dist > 68 || tmpV.x < -0.92 || tmpV.x > 0.92 || tmpV.y < -0.85 || tmpV.y > 0.85) {
        el.style.display = "none";
      } else {
        el.style.display = "block";
        el.style.left = `${((tmpV.x * 0.5 + 0.5) * w).toFixed(1)}px`;
        el.style.top = `${((-tmpV.y * 0.5 + 0.5) * h).toFixed(1)}px`;
        if (el.textContent !== pin.label) el.textContent = pin.label;
        el.onclick = (ev) => { ev.stopPropagation(); pin.onClick(); };
      }
    });
  }

  function computeFloorHitFromNdc(ndcX, ndcY) {
    if (!avz.camera) return null;
    const ray = new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2(ndcX, ndcY), avz.camera);
    const dy = ray.ray.direction.y;
    if (dy >= -0.02) return null;
    const t = (avz.walkSurfaceY - ray.ray.origin.y) / dy;
    if (t <= 0.4 || t > 65) return null;
    const hx = ray.ray.origin.x + ray.ray.direction.x * t;
    const hz = ray.ray.origin.z + ray.ray.direction.z * t;
    const b = avz.walkBounds;
    return {
      x: Math.max(b.minX, Math.min(b.maxX, hx)),
      z: Math.max(b.minZ, Math.min(b.maxZ, hz))
    };
  }

  function clampCameraToBounds() {
    const b = avz.walkBounds;
    avz.camPos.x = Math.max(b.minX, Math.min(b.maxX, avz.camPos.x));
    avz.camPos.z = Math.max(b.minZ, Math.min(b.maxZ, avz.camPos.z));
  }

  function startArchvizLoop() {
    if (avz.rafId) return;
    avz.lastFrameTs = performance.now();
    const tick = (now) => {
      if (!avz.open || !avz.renderer || !avz.scene || !avz.camera) {
        avz.rafId = null;
        return;
      }
      const dt = Math.min(0.06, Math.max(0.001, (now - avz.lastFrameTs) / 1000));
      avz.lastFrameTs = now;

      if (avz.waterUniforms) avz.waterUniforms.uTime.value = now * 0.001;
      avz.swayCrowns.forEach((c, idx) => {
        c.rotation.z = Math.sin(now * 0.0011 + idx) * 0.026;
      });

      // Smooth Guided Auto-Tour
      if (avz.autoWalkActive && avz.autoWaypoints.length >= 2) {
        avz.autoWalkT += dt * (avz.sceneKind === "street" ? 0.055 : 0.14);
        if (avz.autoWalkT >= avz.autoWaypoints.length - 1) avz.autoWalkT = 0;
        const i0 = Math.floor(avz.autoWalkT), frac = avz.autoWalkT - i0;
        const a = avz.autoWaypoints[i0], b = avz.autoWaypoints[(i0 + 1) % avz.autoWaypoints.length];
        avz.camPos.x = a.x + (b.x - a.x) * frac;
        avz.camPos.y = a.y + (b.y - a.y) * frac;
        avz.camPos.z = a.z + (b.z - a.z) * frac;
        let dYawA = ((b.yaw - a.yaw + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI;
        avz.yaw = a.yaw + dYawA * frac;
        if (avz.sceneKind === "villa" && a.roomId && a.roomId !== avz.selectedRoomId) {
          avz.selectedRoomId = a.roomId;
          renderVillaRoomScheduleList();
          renderRightSideUpCadSvg();
          refreshArchvizHeaderAndHud();
        }
      } else if (avz.camTargetPos) {
        const k = Math.min(1, dt * 8.0);
        avz.camPos.x += (avz.camTargetPos.x - avz.camPos.x) * k;
        avz.camPos.y += (avz.camTargetPos.y - avz.camPos.y) * k;
        avz.camPos.z += (avz.camTargetPos.z - avz.camPos.z) * k;
        if (avz.camTargetYaw !== null) {
          let dYaw = ((avz.camTargetYaw - avz.yaw + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI;
          avz.yaw += dYaw * k;
        }
        if (Math.hypot(avz.camTargetPos.x - avz.camPos.x, avz.camTargetPos.z - avz.camPos.z) < 0.05) {
          avz.camTargetPos = null;
          avz.camTargetYaw = null;
        }
      }

      // Smooth Velocity-Damped WASD / Arrow Movement + Plot Boundary Clamping
      const maxSpd = avz.keys.shift ? 10.5 : 5.2;
      const fwd = (avz.keys.w || avz.keys.arrowup ? 1 : 0) - (avz.keys.s || avz.keys.arrowdown ? 1 : 0);
      const str = (avz.keys.d || avz.keys.arrowright ? 1 : 0) - (avz.keys.a || avz.keys.arrowleft ? 1 : 0);
      if (fwd !== 0 || str !== 0) {
        avz.autoWalkActive = false;
        avz.camTargetPos = null;
        avz.camTargetYaw = null;
      }
      const sinY = Math.sin(avz.yaw), cosY = Math.cos(avz.yaw);
      const desVx = (-sinY * fwd + cosY * str) * maxSpd;
      const desVz = (-cosY * fwd - sinY * str) * maxSpd;
      const damp = Math.min(1, dt * 10.0);
      avz.camVel.x += (desVx - avz.camVel.x) * damp;
      avz.camVel.z += (desVz - avz.camVel.z) * damp;
      if (Math.abs(avz.camVel.x) > 0.01 || Math.abs(avz.camVel.z) > 0.01) {
        avz.camPos.x += avz.camVel.x * dt;
        avz.camPos.z += avz.camVel.z * dt;
        clampCameraToBounds();
      }

      if (avz.camStyle === "fpv") {
        avz.camera.position.set(avz.camPos.x, avz.camPos.y, avz.camPos.z);
        const lookX = avz.camPos.x - Math.sin(avz.yaw) * Math.cos(avz.pitch) * 10;
        const lookY = avz.camPos.y + Math.sin(avz.pitch) * 10;
        const lookZ = avz.camPos.z - Math.cos(avz.yaw) * Math.cos(avz.pitch) * 10;
        avz.camera.lookAt(lookX, lookY, lookZ);

        // Update 3D Floor Cursor Ring
        if (avz.cursorRing && avz.hoverNdc.active && !avz.dragging) {
          const hit = computeFloorHitFromNdc(avz.hoverNdc.x, avz.hoverNdc.y);
          if (hit) {
            avz.cursorRing.visible = true;
            avz.cursorRing.position.set(hit.x, avz.walkSurfaceY + 0.018, hit.z);
          } else {
            avz.cursorRing.visible = false;
          }
        } else if (avz.cursorRing) {
          avz.cursorRing.visible = false;
        }
      } else {
        if (avz.cursorRing) avz.cursorRing.visible = false;
        const cx = avz.orbitTarget.x + Math.sin(avz.orbitYaw) * Math.cos(avz.orbitPitch) * avz.orbitDist;
        const cy = avz.orbitTarget.y + Math.sin(avz.orbitPitch) * avz.orbitDist;
        const cz = avz.orbitTarget.z + Math.cos(avz.orbitYaw) * Math.cos(avz.orbitPitch) * avz.orbitDist;
        avz.camera.position.set(cx, cy, cz);
        avz.camera.lookAt(avz.orbitTarget.x, avz.orbitTarget.y, avz.orbitTarget.z);
      }

      renderArchvizFrame();
      updateProjectedWorldPins();
      if (avz.sceneKind === "villa") updateCadLiveCameraCone();
      avz.rafId = requestAnimationFrame(tick);
    };
    avz.rafId = requestAnimationFrame(tick);
  }

  let __avzBound = false;
  function bindArchvizControlsOnce(canvas) {
    if (__avzBound) return;
    __avzBound = true;

    const updateNdc = (e) => {
      const rect = canvas.getBoundingClientRect();
      avz.hoverNdc.x = ((e.clientX - rect.left) / Math.max(1, rect.width)) * 2 - 1;
      avz.hoverNdc.y = -((e.clientY - rect.top) / Math.max(1, rect.height)) * 2 + 1;
      avz.hoverNdc.active = true;
    };

    canvas.addEventListener("pointerdown", (e) => {
      avz.dragging = true;
      avz.dragDist = 0;
      avz.downX = e.clientX; avz.downY = e.clientY;
      avz.lastMX = e.clientX; avz.lastMY = e.clientY;
      updateNdc(e);
      canvas.setPointerCapture(e.pointerId);
    });

    canvas.addEventListener("pointermove", (e) => {
      updateNdc(e);
      if (!avz.dragging) return;
      const dx = e.clientX - avz.lastMX, dy = e.clientY - avz.lastMY;
      avz.dragDist += Math.hypot(dx, dy);
      avz.lastMX = e.clientX; avz.lastMY = e.clientY;
      if (avz.camStyle === "fpv") {
        // Natural panorama/first-person drag feel
        avz.yaw += dx * 0.0045;
        avz.pitch = Math.max(-0.85, Math.min(0.85, avz.pitch + dy * 0.0038));
      } else {
        avz.orbitYaw -= dx * 0.0065;
        avz.orbitPitch = Math.max(0.18, Math.min(1.36, avz.orbitPitch + dy * 0.0055));
      }
    });

    canvas.addEventListener("pointerleave", () => {
      avz.hoverNdc.active = false;
    });

    canvas.addEventListener("pointerup", (e) => {
      const wasClick = avz.dragging && avz.dragDist < 6;
      avz.dragging = false;
      if (wasClick && avz.camStyle === "fpv") {
        updateNdc(e);
        const hit = computeFloorHitFromNdc(avz.hoverNdc.x, avz.hoverNdc.y);
        if (hit) {
          avz.autoWalkActive = false;
          const eyeH = avz.sceneKind === "street" ? 1.70 : 1.62;
          avz.camTargetPos = { x: hit.x, y: avz.walkSurfaceY + eyeH - 0.04, z: hit.z };
          avz.camTargetYaw = null;
        }
      }
    });

    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      if (avz.camStyle === "fpv") {
        const step = e.deltaY < 0 ? 1.6 : -1.6;
        avz.camPos.x += -Math.sin(avz.yaw) * step;
        avz.camPos.z += -Math.cos(avz.yaw) * step;
        clampCameraToBounds();
      } else {
        avz.orbitDist = Math.max(12, Math.min(125, avz.orbitDist * (e.deltaY < 0 ? 0.91 : 1.10)));
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
      } else if (k === "escape") {
        closeArchvizStudioModal(true);
      }
    });
    window.addEventListener("keyup", (e) => {
      avz.keys[e.key.toLowerCase()] = false;
    });
  }

  // ---------------- PUBLIC LAUNCHERS & STUDIO CONTROLLERS ----------------
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

    if (!wtState.active || wtState.projectId !== typ.project_id) {
      wtState.active = true;
      wtState.projectId = typ.project_id;
    }
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
    avz.camTargetPos = null;
    avz.camTargetYaw = null;

    const startR = gFl.rooms.find(r => r.type === "living") || gFl.rooms[0];
    avz.selectedRoomId = startR.id;
    const initCam = computeIdealRoomCamera(startR, gFl, typ, false);
    avz.camPos = { x: initCam.x, y: initCam.y, z: initCam.z };
    avz.yaw = initCam.yaw;
    avz.pitch = initCam.pitch;
    const diag = Math.hypot(typ.plot_w, typ.plot_d);
    avz.orbitDist = Math.max(36, diag * 0.88);
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
        avz.orbitDist = Math.max(36, diag * (style === "cutaway" ? 0.86 : 0.94));
        avz.orbitTarget = { x: 0, y: style === "cutaway" ? 1.2 : 3.2, z: -2.0 };
        avz.orbitPitch = style === "cutaway" ? 0.62 : 0.48;
      }
      buildArchvizVillaScene();
    } else {
      avz.camera.fov = (style === "fpv") ? 48 : 44;
      avz.camera.updateProjectionMatrix();
      if (style !== "fpv") {
        avz.orbitTarget = { x: 0, y: 2.5, z: -18 };
        avz.orbitDist = 54;
        avz.orbitPitch = 0.50;
      }
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
    if (avz.autoWalkActive && avz.camStyle !== "fpv") {
      setArchvizCamStyle("fpv");
      avz.autoWalkActive = true;
    }
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
    avz.camTargetPos = null;
    const typ = DATA.walkthroughs.typologies[avz.typologyId];
    if (typ) {
      const fl = typ.floors.find(f => f.level === fLevel) || typ.floors[0];
      const r0 = fl.rooms.find(r => r.type === "master") || fl.rooms.find(r => r.type === "living") || fl.rooms[0];
      if (r0) {
        avz.selectedRoomId = r0.id;
        const cam = computeIdealRoomCamera(r0, fl, typ, avz.camStyle === "cutaway");
        avz.camPos = { x: cam.x, y: cam.y, z: cam.z };
        avz.yaw = cam.yaw;
        avz.pitch = cam.pitch;
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
    const cam = computeIdealRoomCamera(r, fl, typ, avz.camStyle === "cutaway");
    avz.camTargetPos = { x: cam.x, y: cam.y, z: cam.z };
    avz.camTargetYaw = cam.yaw;
    if (avz.camStyle === "fpv") avz.pitch = cam.pitch;
    else avz.orbitTarget = { x: cam.x, y: cam.y - 0.5, z: cam.z - 2.0 };
    renderRightSideUpCadSvg();
    renderVillaRoomScheduleList();
    refreshArchvizHeaderAndHud();
  }
  window.teleportVillaRoom = teleportVillaRoom;

  function stepArchvizPad(fwd, turn) {
    avz.autoWalkActive = false;
    avz.camTargetPos = null;
    avz.yaw += turn * 0.24;
    if (fwd !== 0) {
      avz.camPos.x += -Math.sin(avz.yaw) * fwd * 2.6;
      avz.camPos.z += -Math.cos(avz.yaw) * fwd * 2.6;
      clampCameraToBounds();
    }
  }
  window.stepArchvizPad = stepArchvizPad;

  function roomIconForType(t) {
    if (t === "living") return "🛋️";
    if (t === "kitchen") return "🍳";
    if (t === "master" || t === "bedroom") return "🛏️";
    if (t === "bath") return "🛁";
    if (t === "pool") return "🏊";
    if (t === "garage") return "🚗";
    if (t === "wellness") return "🎬";
    return "🏛️";
  }

  function refreshArchvizHeaderAndHud() {
    const topControls = document.getElementById("avzModeSpecificTop");
    const infoCard = document.getElementById("avzFloatingInfoCard");
    const bottomDock = document.getElementById("avzBottomDock");
    const metaStrip = document.getElementById("avzMetaStrip");
    if (!topControls) return;

    const curPid = wtState.projectId || "PRJ-D19";
    const soc = getSocietyData(curPid) || getSocietyData("PRJ-D19");

    // Unified Single-Row 3-Step Breadcrumb Bar (Impossible to get lost!)
    topControls.innerHTML = `
      <button type="button" class="wt-soc-switch ${curPid === 'PRJ-D19' ? 'active' : ''}" onclick="enterSocietyWalkthrough('PRJ-D19', '${avz.sceneKind}')">🌊 Tilal Al Ghaf</button>
      <button type="button" class="wt-soc-switch ${curPid === 'PRJ-D2' ? 'active' : ''}" onclick="enterSocietyWalkthrough('PRJ-D2', '${avz.sceneKind}')">🌴 Palm Jebel Ali</button>
      <div class="wt-mode-group" role="tablist">
        <button type="button" class="wt-mode-pill" onclick="closeArchvizStudioModal(true)">① 🗺️ Aerial Map</button>
        <button type="button" class="wt-mode-pill ${avz.sceneKind === 'street' ? 'active' : ''}" onclick="openUnrealStreetWalk(${wtState.stopIndex || 0})">② 🚶 Walk Streets</button>
        <button type="button" class="wt-mode-pill ${avz.sceneKind === 'villa' ? 'active' : ''}" onclick="openCurrentSocietyVillaModal()">③ 🏠 Walk Inside Villa</button>
      </div>
    `;

    if (avz.sceneKind === "street") {
      const st = soc.street_tour[wtState.stopIndex] || soc.street_tour[0];
      const z = (soc.zones || []).find(x => x.zone_id === st.zone_id) || soc.zones[0];

      if (infoCard) {
        infoCard.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
            <span style="font-size:0.65rem; font-weight:900; color:#34d399; letter-spacing:0.05em; text-transform:uppercase;">② Street Walk · Stop ${st.stop}/${soc.street_tour.length}</span>
            <span style="font-size:0.67rem; color:#94a3b8;">${soc.name}</span>
          </div>
          <div style="font-size:0.92rem; font-weight:800; color:#ffffff; margin-top:2px;">${st.title}</div>
          <div style="font-size:0.72rem; color:#cbd5e1; margin-top:4px; line-height:1.4;">
            🏗️ <strong style="color:#6ee7b7;">${z ? z.main_contractor : soc.developer}</strong> <span style="color:#94a3b8;">(${z ? z.contract_value : ""})</span><br/>
            📐 <span style="color:#93c5fd;">${z ? z.architects : ""}</span>
          </div>
        `;
      }

      if (bottomDock) {
        bottomDock.innerHTML = `
          <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap; justify-content:center;">
            <div class="vim-floor-pills">
              <button type="button" class="vim-floor-btn ${avz.camStyle === 'fpv' ? 'active' : ''}" onclick="setArchvizCamStyle('fpv')">👁️ Walk Street (1.7m)</button>
              <button type="button" class="vim-floor-btn ${avz.camStyle === 'dollhouse' ? 'active' : ''}" onclick="setArchvizCamStyle('dollhouse')">🚁 Drone Orbit</button>
            </div>
            <button type="button" class="wt-btn" onclick="openUnrealStreetWalk(${wtState.stopIndex - 1})">⏮ Prev</button>
            <button type="button" class="wt-btn primary" onclick="toggleArchvizAutoTour()">${avz.autoWalkActive ? "⏸ Pause Walk" : "▶ Guided Street Walk"}</button>
            <button type="button" class="wt-btn" onclick="openUnrealStreetWalk(${wtState.stopIndex + 1})">Next ⏭</button>
            <button type="button" class="wt-btn inside-cta" onclick="openVillaInteriorModal('${z ? z.default_typology_id : 'TYP-TAG-SERENITY-6BR'}')">③ 🏠 Step Inside Villa →</button>
          </div>
          <div style="display:flex; gap:4px; flex-wrap:wrap; justify-content:center; align-items:center;">
            <span style="font-size:0.67rem; color:#94a3b8; margin-right:3px;">Jump to Enclave:</span>
            ${soc.street_tour.map((s, idx) => {
              const w = s.title.split(" ");
              const lbl = (w[0] === "Frond" && w[1]) ? `${w[0]} ${w[1]}` : w[0];
              return `<button type="button" class="wt-stop-dot ${idx === wtState.stopIndex ? 'active' : ''}" onclick="openUnrealStreetWalk(${idx})">${s.stop}. ${lbl}</button>`;
            }).join("")}
          </div>
        `;
      }
    } else {
      const allTyps = DATA.walkthroughs.typologies || {};
      const typ = allTyps[avz.typologyId];
      const fl = typ.floors.find(f => f.level === avz.floorKey) || typ.floors[0];

      if (infoCard) {
        infoCard.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:4px;">
            <span style="font-size:0.65rem; font-weight:900; color:#38bdf8; letter-spacing:0.05em; text-transform:uppercase;">③ Inside 3D Villa · Level ${fl.level}</span>
            <button type="button" onclick="toggleArchvizFullscreen3D()" style="background:rgba(255,255,255,0.10); color:#e2e8f0; border:1px solid rgba(148,163,184,0.3); border-radius:999px; padding:2px 9px; font-size:0.66rem; font-weight:700; cursor:pointer;">${avz.fullscreen3D ? "◫ Show Floor Plan" : "⛶ Fullscreen 3D"}</button>
          </div>
          <select onchange="openVillaInteriorModal(this.value)" style="width:100%; background:rgba(15,23,42,0.92); color:#f8fafc; border:1px solid rgba(56,189,248,0.45); border-radius:8px; padding:5px 8px; font-size:0.76rem; font-weight:800; cursor:pointer;">
            ${Object.values(allTyps).map(t => `<option value="${t.id}" ${t.id === typ.id ? "selected" : ""}>${t.project_id === "PRJ-D2" ? "🌴 PJA" : "🌊 TAG"} · ${t.title} (${t.bua_sqft})</option>`).join("")}
          </select>
          <div style="font-size:0.71rem; color:#cbd5e1; margin-top:5px; line-height:1.38;">
            🏗️ <strong style="color:#6ee7b7;">${typ.contractor}</strong><br/>
            📐 <span style="color:#93c5fd;">${typ.architect}</span> · Plot ${typ.plot_w}×${typ.plot_d}m
          </div>
        `;
      }

      if (bottomDock) {
        bottomDock.innerHTML = `
          <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap; justify-content:center;">
            <div class="vim-floor-pills">
              <button type="button" class="vim-floor-btn ${avz.camStyle === 'fpv' ? 'active' : ''}" onclick="setArchvizCamStyle('fpv')">👁️ Walk Inside</button>
              <button type="button" class="vim-floor-btn ${avz.camStyle === 'cutaway' ? 'active' : ''}" onclick="setArchvizCamStyle('cutaway')">🔪 3D Cutaway</button>
              <button type="button" class="vim-floor-btn ${avz.camStyle === 'dollhouse' && !avz.exploded ? 'active' : ''}" onclick="avz.exploded=false; setArchvizCamStyle('dollhouse')">🏠 Full 3D Villa</button>
              <button type="button" class="vim-floor-btn ${avz.camStyle === 'dollhouse' && avz.exploded ? 'active' : ''}" onclick="toggleArchvizExploded()">↕ Explode Levels</button>
            </div>
            <div class="vim-floor-pills" title="Switch Villa Storey">
              ${typ.floors.map(f => `<button type="button" class="vim-floor-btn ${avz.floorKey === f.level ? 'active' : ''}" onclick="selectVillaFloorInArchviz('${f.level}')">${f.level}</button>`).join("")}
            </div>
            <button type="button" class="wt-btn primary" onclick="toggleArchvizAutoTour()">${avz.autoWalkActive ? "⏸ Pause Tour" : "▶ Auto-Tour Rooms"}</button>
          </div>
          <div style="display:flex; gap:5px; flex-wrap:wrap; justify-content:center; align-items:center;">
            <span style="font-size:0.67rem; color:#94a3b8;">Teleport Camera:</span>
            ${fl.rooms.map(r => {
              const shortN = r.name.split("&")[0].split("+")[0].trim().slice(0, 20);
              return `<button type="button" class="wt-stop-dot ${r.id === avz.selectedRoomId ? 'active' : ''}" onclick="teleportVillaRoom('${r.id}')">${roomIconForType(r.type)} ${shortN}</button>`;
            }).join("")}
          </div>
        `;
      }

      if (metaStrip) {
        metaStrip.innerHTML = `
          <div style="font-weight:800; color:#e2e8f0;">🧭 North-Up Floor Plan <span style="color:#38bdf8;">(${fl.level})</span></div>
          <div style="display:flex; gap:4px;">
            <button type="button" class="wt-stop-dot ${avz.cadStyle === 'brochure' ? 'active' : ''}" onclick="setCadVisualStyle('brochure')">🎨 Brochure</button>
            <button type="button" class="wt-stop-dot ${avz.cadStyle === 'cad' ? 'active' : ''}" onclick="setCadVisualStyle('cad')">📐 CAD</button>
          </div>
        `;
      }
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
        <div style="background:rgba(16,185,129,0.12); color:#f8fafc; border-radius:9px; padding:8px 10px; margin-bottom:8px; border-left:3px solid #10b981;">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
            <strong style="font-size:0.76rem; color:#6ee7b7;">📍 ${sel.name}</strong>
            <span style="background:#0284c7; color:#fff; font-size:0.65rem; font-weight:800; padding:2px 7px; border-radius:999px; white-space:nowrap;">${Math.round(sel.w * sel.d * 10.7639)} sq.ft.</span>
          </div>
          <div style="font-size:0.68rem; color:#cbd5e1; margin-top:2px;">${sel.w.toFixed(1)}m × ${sel.d.toFixed(1)}m · ${sel.spec}</div>
        </div>
      ` : ""}
      <div style="font-size:0.66rem; font-weight:800; color:#94a3b8; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:5px;">Click Space to Teleport (${fl.rooms.length} Rooms):</div>
      ${fl.rooms.map(r => `
        <div class="vim-room-chip ${r.id === avz.selectedRoomId ? 'active' : ''}" onclick="teleportVillaRoom('${r.id}')">
          <div>
            <strong style="color:#f8fafc;">${roomIconForType(r.type)} ${r.name}</strong>
            <div style="font-size:0.66rem; color:#94a3b8;">${r.spec}</div>
          </div>
          <div style="text-align:right; white-space:nowrap;">
            <strong style="color:#38bdf8;">${Math.round(r.w * r.d * 10.7639)} sf</strong>
            <div style="font-size:0.64rem; color:#64748b;">${r.w.toFixed(1)}×${r.d.toFixed(1)}m</div>
          </div>
        </div>
      `).join("")}
    `;
  }
})();
