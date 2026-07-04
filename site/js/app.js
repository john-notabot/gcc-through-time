/* GCC Through Time — time-slider map */
(async function () {
  const AOI = { w: -118.245, s: 34.150, e: -118.210, n: 34.195 };
  const CAMPUS = [-118.2312, 34.1672];

  const erasResp = await fetch("data/eras.json");
  const ERAS = (await erasResp.json()).eras;

  // ---------- map ----------
  const style = {
    version: 8,
    sources: {},
    layers: [{
      id: "bg", type: "background",
      paint: { "background-color": "#23201a" }
    }]
  };
  // two layer sets: "color" (AI-assisted reconstruction, default) and "orig"
  const MODES = ["color", "orig"];
  let mode = "color";
  ERAS.forEach(e => {
    MODES.forEach(m => {
      // 2022 is already color imagery — both modes share the original tiles
      const path = (m === "color" && e.id !== "2022") ? "color/" + e.id : "orig/" + e.id;
      style.sources["era" + e.id + m] = {
        type: "raster",
        tiles: ["tiles/" + path + "/{z}/{x}/{y}.webp"],
        tileSize: 256,
        minzoom: 11, maxzoom: 17,
        bounds: [AOI.w, AOI.s, AOI.e, AOI.n]
      };
      style.layers.push({
        id: "era" + e.id + m, type: "raster", source: "era" + e.id + m,
        paint: {
          "raster-opacity": 0,
          "raster-fade-duration": 0,
          "raster-resampling": "linear"
        }
      });
    });
  });

  const map = new maplibregl.Map({
    container: "map",
    style,
    bounds: [[AOI.w, AOI.s], [AOI.e, AOI.n]],
    fitBoundsOptions: { padding: 8 },
    minZoom: 12.2,
    maxZoom: 17.6,
    maxBounds: [[AOI.w - 0.012, AOI.s - 0.008], [AOI.e + 0.012, AOI.n + 0.008]],
    attributionControl: false,
    pitchWithRotate: false,
    dragRotate: false,
    touchPitch: false
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.addControl(new maplibregl.AttributionControl({
    compact: true,
    customAttribution: "UCSB Library · USGS · USDA · © OpenStreetMap contributors"
  }), "bottom-right");

  // ---------- slider / crossfade ----------
  const slider = document.getElementById("slider");
  const yearEl = document.getElementById("era-year");
  const labelEl = document.getElementById("era-label");
  let current = ERAS.length - 1;

  function apply(v) {
    ERAS.forEach((e, i) => {
      const o = Math.max(0, 1 - Math.abs(v - i));
      MODES.forEach(m => {
        map.setPaintProperty("era" + e.id + m, "raster-opacity", m === mode ? o : 0);
      });
    });
    const idx = Math.round(v);
    if (yearEl.textContent !== ERAS[idx].year) {
      yearEl.textContent = ERAS[idx].year;
      labelEl.textContent = ERAS[idx].label;
    }
    current = idx;
  }

  slider.addEventListener("input", () => apply(parseFloat(slider.value)));
  const snap = () => {
    const idx = Math.round(parseFloat(slider.value));
    slider.value = idx;
    apply(idx);
  };
  slider.addEventListener("change", snap);
  slider.addEventListener("pointerup", snap);
  // keyboard: arrows step whole eras
  slider.addEventListener("keydown", (ev) => {
    if (["ArrowLeft", "ArrowDown", "ArrowRight", "ArrowUp"].includes(ev.key)) {
      ev.preventDefault();
      const d = (ev.key === "ArrowLeft" || ev.key === "ArrowDown") ? -1 : 1;
      const idx = Math.min(ERAS.length - 1, Math.max(0, Math.round(parseFloat(slider.value)) + d));
      slider.value = idx;
      apply(idx);
    }
  });

  // tick labels
  const ticks = document.getElementById("ticks");
  ERAS.forEach((e, i) => {
    const t = document.createElement("span");
    t.className = "tick";
    t.style.left = (i / (ERAS.length - 1) * 100) + "%";
    t.textContent = e.year.replace("~", "");
    ticks.appendChild(t);
  });

  map.on("load", () => apply(parseFloat(slider.value)));

  // ---------- mode toggle ----------
  const toggle = document.getElementById("mode-toggle");
  toggle.addEventListener("click", () => {
    mode = mode === "color" ? "orig" : "color";
    toggle.setAttribute("aria-pressed", mode === "orig" ? "true" : "false");
    toggle.querySelector("span").textContent =
      mode === "color" ? "Color reconstruction" : "Original imagery";
    toggle.classList.toggle("orig", mode === "orig");
    apply(parseFloat(slider.value));
  });

  // ---------- story pins ----------
  const card = document.getElementById("pin-card");
  const cardTitle = document.getElementById("pin-title");
  const cardBody = document.getElementById("pin-body");
  const cardEras = document.getElementById("pin-eras");
  document.getElementById("pin-close").onclick = () => card.hidden = true;

  const pinsResp = await fetch("data/pins.geojson");
  const pins = await pinsResp.json();
  pins.features.forEach(f => {
    const el = document.createElement("button");
    el.className = "pin";
    el.setAttribute("aria-label", "Story: " + f.properties.title);
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      cardTitle.textContent = f.properties.title;
      cardBody.textContent = f.properties.body;
      cardEras.textContent = "Best viewed: " + f.properties.eras;
      card.hidden = false;
    });
    new maplibregl.Marker({ element: el, anchor: "center" })
      .setLngLat(f.geometry.coordinates)
      .addTo(map);
  });
  map.on("click", () => card.hidden = true);

  // ---------- intro / credits ----------
  const intro = document.getElementById("intro");
  document.getElementById("intro-start").onclick = () => intro.style.display = "none";
  const credits = document.getElementById("credits");
  const list = document.getElementById("credits-list");
  ERAS.forEach(e => {
    const li = document.createElement("li");
    li.innerHTML = "<strong>" + e.year + " — " + e.label + ":</strong> " + e.credit;
    list.appendChild(li);
  });
  document.getElementById("credits-link").onclick = (ev) => {
    ev.preventDefault();
    intro.style.display = "none";
    credits.hidden = false;
  };
  document.getElementById("btn-about").onclick = () => { credits.hidden = false; };
  document.getElementById("credits-close").onclick = () => credits.hidden = true;
})();
