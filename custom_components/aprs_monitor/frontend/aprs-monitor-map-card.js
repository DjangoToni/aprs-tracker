const FRONTEND_BASE = new URL(".", import.meta.url);
const LEAFLET_SCRIPT = new URL("vendor/leaflet/leaflet.js", FRONTEND_BASE).href;
const LEAFLET_STYLE = new URL("vendor/leaflet/leaflet.css", FRONTEND_BASE).href;

let leafletPromise;

function loadLeaflet() {
  if (leafletPromise) return leafletPromise;
  leafletPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = LEAFLET_SCRIPT;
    script.dataset.aprsMonitorLeaflet = "true";
    script.onload = () => resolve(window.L.noConflict());
    script.onerror = () => reject(new Error("Leaflet could not be loaded"));
    document.head.appendChild(script);
  });
  return leafletPromise;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function numeric(value) {
  if (value === null || value === undefined || value === "") return null;
  const result = Number(value);
  return Number.isFinite(result) ? result : null;
}

function localeText(language) {
  if (String(language).toLowerCase().startsWith("de")) {
    return {
      altitude: "Höhe",
      coordinates: "Koordinaten",
      course: "Richtung",
      empty: "Keine aktuellen APRS-Positionen verfügbar",
      lastSeen: "Letztes Signal",
      speed: "Geschwindigkeit",
    };
  }
  return {
    altitude: "Altitude",
    coordinates: "Coordinates",
    course: "Direction",
    empty: "No current APRS positions available",
    lastSeen: "Last signal",
    speed: "Speed",
  };
}

function cardinal(course, language) {
  if (course === null) return null;
  const german = String(language).toLowerCase().startsWith("de");
  const points = german
    ? ["N", "NO", "O", "SO", "S", "SW", "W", "NW"]
    : ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return points[Math.round((((course % 360) + 360) % 360) / 45) % 8];
}

class AprsMonitorMapCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._markers = new Map();
    this._fitted = false;
  }

  setConfig(config) {
    if (!Array.isArray(config.entities) || config.entities.length === 0) {
      throw new Error("APRS Monitor Map Card requires at least one tracker entity");
    }
    this._config = {
      auto_fit: true,
      height: 500,
      max_zoom: 16,
      ...config,
      entities: config.entities.map((item) =>
        typeof item === "string" ? item : item.entity,
      ),
    };
    if (this._config.entities.some((entityId) => !entityId)) {
      throw new Error("Every APRS Monitor map entity needs an entity ID");
    }
    this._resizeObserver?.disconnect();
    this._map?.remove();
    this._map = undefined;
    this._markers.clear();
    this._fitted = false;
    this._renderShell();
    this._startMap();
  }

  set hass(hass) {
    this._hass = hass;
    this._updateTitle();
    this._updateMarkers();
  }

  connectedCallback() {
    this._startMap();
  }

  disconnectedCallback() {
    this._resizeObserver?.disconnect();
  }

  getCardSize() {
    return Math.max(3, Math.ceil((this._config?.height ?? 500) / 50));
  }

  getGridOptions() {
    return { columns: "full", rows: 8, min_rows: 4 };
  }

  static getStubConfig() {
    return { entities: ["device_tracker.aprs_station"], title: "APRS Monitor" };
  }

  _renderShell() {
    const height = Math.max(240, Number(this._config.height) || 500);
    this.shadowRoot.innerHTML = `
      <link rel="stylesheet" href="${LEAFLET_STYLE}">
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; }
        .header {
          color: var(--ha-card-header-color, var(--primary-text-color));
          font-family: var(--ha-card-header-font-family, inherit);
          font-size: var(--ha-card-header-font-size, 24px);
          line-height: 32px;
          padding: 16px 16px 8px;
        }
        #map { height: ${height}px; width: 100%; background: var(--secondary-background-color); }
        .empty {
          align-items: center;
          background: color-mix(in srgb, var(--card-background-color) 88%, transparent);
          color: var(--secondary-text-color);
          display: none;
          inset: 64px 16px auto;
          justify-content: center;
          padding: 12px;
          pointer-events: none;
          position: absolute;
          text-align: center;
          z-index: 800;
        }
        .aprs-monitor-marker { background: transparent; border: 0; }
        .aprs-monitor-marker img {
          filter: drop-shadow(0 1px 2px rgb(0 0 0 / 65%));
          height: 48px;
          object-fit: contain;
          width: 48px;
        }
        .aprs-monitor-fallback {
          align-items: center;
          background: var(--primary-color, #03a9f4);
          border: 2px solid white;
          border-radius: 18px;
          box-shadow: 0 1px 4px rgb(0 0 0 / 55%);
          color: white;
          display: flex;
          font: 700 10px/1 sans-serif;
          height: 32px;
          justify-content: center;
          overflow: hidden;
          padding: 0 4px;
          width: 40px;
        }
        .leaflet-tooltip.aprs-monitor-tooltip {
          background: var(--card-background-color, white);
          border: 0;
          border-radius: 8px;
          box-shadow: 0 3px 12px rgb(0 0 0 / 35%);
          color: var(--primary-text-color, #212121);
          line-height: 1.45;
          padding: 10px 12px;
        }
        .aprs-tooltip-title { font-size: 15px; font-weight: 700; margin-bottom: 5px; }
        .aprs-tooltip-row { display: grid; gap: 12px; grid-template-columns: auto auto; }
        .aprs-tooltip-row span:first-child { color: var(--secondary-text-color, #666); }
        .aprs-tooltip-row span:last-child { font-variant-numeric: tabular-nums; text-align: right; }
        .leaflet-control-attribution { font-size: 10px; }
      </style>
      <ha-card>
        <div class="header"></div>
        <div style="position:relative">
          <div id="map" role="application" aria-label="APRS Monitor map"></div>
          <div class="empty"></div>
        </div>
      </ha-card>`;
    this._mapElement = this.shadowRoot.querySelector("#map");
    this._emptyElement = this.shadowRoot.querySelector(".empty");
    this._updateTitle();
  }

  async _startMap() {
    if (!this.isConnected || !this._config || !this._mapElement || this._map) return;
    try {
      const L = await loadLeaflet();
      if (!this.isConnected || this._map) return;
      this._L = L;
      const center = [
        numeric(this._hass?.config?.latitude) ?? 46.8,
        numeric(this._hass?.config?.longitude) ?? 8.2,
      ];
      this._map = L.map(this._mapElement, {
        attributionControl: true,
        scrollWheelZoom: this._config.scroll_wheel_zoom === true,
      }).setView(center, numeric(this._config.zoom) ?? 8);
      L.tileLayer(
        this._config.tile_url ?? "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution:
            this._config.attribution ??
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
        },
      ).addTo(this._map);
      this._resizeObserver = new ResizeObserver(() => this._map?.invalidateSize());
      this._resizeObserver.observe(this._mapElement);
      this._updateMarkers();
      requestAnimationFrame(() => this._map?.invalidateSize());
    } catch (error) {
      this._emptyElement.textContent = error.message;
      this._emptyElement.style.display = "flex";
    }
  }

  _updateTitle() {
    const header = this.shadowRoot?.querySelector(".header");
    if (!header || !this._config) return;
    const title = this._config.title ?? "APRS Monitor";
    header.textContent = title;
    header.style.display = title ? "block" : "none";
  }

  _updateMarkers() {
    if (!this._map || !this._hass || !this._config) return;
    const active = new Set();
    const bounds = [];
    for (const entityId of this._config.entities) {
      const state = this._hass.states[entityId];
      const latitude = numeric(state?.attributes?.latitude);
      const longitude = numeric(state?.attributes?.longitude);
      if (
        !state ||
        state.state === "unavailable" ||
        state.state === "unknown" ||
        latitude === null ||
        longitude === null
      ) {
        continue;
      }
      active.add(entityId);
      bounds.push([latitude, longitude]);
      const picture = state.attributes.entity_picture ?? state.attributes.aprs_symbol_picture;
      let marker = this._markers.get(entityId);
      if (!marker) {
        marker = this._L.marker([latitude, longitude], {
          icon: this._markerIcon(state, picture),
          keyboard: true,
          title: state.attributes.friendly_name ?? state.attributes.callsign ?? entityId,
        });
        marker._aprsPicture = picture;
        marker.bindTooltip(this._tooltip(state), {
          className: "aprs-monitor-tooltip",
          direction: "top",
          offset: [0, -22],
          opacity: 1,
        });
        marker.on("click", () => this._showMoreInfo(entityId));
        marker.addTo(this._map);
        this._markers.set(entityId, marker);
      } else {
        marker.setLatLng([latitude, longitude]);
        marker.setTooltipContent(this._tooltip(state));
        if (marker._aprsPicture !== picture) {
          marker.setIcon(this._markerIcon(state, picture));
          marker._aprsPicture = picture;
        }
      }
    }
    for (const [entityId, marker] of this._markers) {
      if (!active.has(entityId)) {
        marker.removeFrom(this._map);
        this._markers.delete(entityId);
      }
    }
    const text = localeText(this._hass.language);
    this._emptyElement.textContent = text.empty;
    this._emptyElement.style.display = bounds.length ? "none" : "flex";
    if (this._config.auto_fit && !this._fitted && bounds.length) {
      if (bounds.length === 1) {
        this._map.setView(bounds[0], numeric(this._config.zoom) ?? 13);
      } else {
        this._map.fitBounds(bounds, {
          maxZoom: numeric(this._config.max_zoom) ?? 16,
          padding: [40, 40],
        });
      }
      this._fitted = true;
    }
  }

  _markerIcon(state, picture) {
    if (picture) {
      return this._L.divIcon({
        className: "aprs-monitor-marker",
        html: `<img src="${escapeHtml(picture)}" alt="">`,
        iconAnchor: [24, 24],
        iconSize: [48, 48],
      });
    }
    const callsign = state.attributes.callsign ?? state.attributes.friendly_name ?? "APRS";
    return this._L.divIcon({
      className: "aprs-monitor-marker",
      html: `<div class="aprs-monitor-fallback">${escapeHtml(callsign)}</div>`,
      iconAnchor: [24, 18],
      iconSize: [48, 36],
    });
  }

  _tooltip(state) {
    const attrs = state.attributes;
    const labels = localeText(this._hass.language);
    const speed = numeric(attrs.speed_kmh);
    const course = numeric(attrs.course);
    const altitude = numeric(attrs.altitude_m);
    const latitude = numeric(attrs.latitude);
    const longitude = numeric(attrs.longitude);
    const name = attrs.friendly_name ?? attrs.callsign ?? state.entity_id;
    const callsign = attrs.callsign && attrs.callsign !== name ? ` (${attrs.callsign})` : "";
    const rows = [];
    if (speed !== null) rows.push([labels.speed, `${speed.toFixed(0)} km/h`]);
    if (course !== null) {
      rows.push([labels.course, `${cardinal(course, this._hass.language)} (${course.toFixed(0)}°)`]);
    }
    if (altitude !== null) rows.push([labels.altitude, `${altitude.toFixed(0)} m`]);
    if (latitude !== null && longitude !== null) {
      rows.push([labels.coordinates, `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`]);
    }
    if (attrs.last_seen) {
      const lastSeen = new Date(attrs.last_seen);
      if (!Number.isNaN(lastSeen.getTime())) {
        rows.push([labels.lastSeen, lastSeen.toLocaleString(this._hass.language)]);
      }
    }
    return `<div class="aprs-tooltip-title">${escapeHtml(name + callsign)}</div>${rows
      .map(
        ([label, value]) =>
          `<div class="aprs-tooltip-row"><span>${escapeHtml(label)}</span><span>${escapeHtml(value)}</span></div>`,
      )
      .join("")}`;
  }

  _showMoreInfo(entityId) {
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        bubbles: true,
        composed: true,
        detail: { entityId },
      }),
    );
  }
}

if (!customElements.get("aprs-monitor-map-card")) {
  customElements.define("aprs-monitor-map-card", AprsMonitorMapCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "aprs-monitor-map-card")) {
  window.customCards.push({
    type: "aprs-monitor-map-card",
    name: "APRS Monitor Map Card",
    description: "APRS map with local symbols and telemetry tooltips",
    documentationURL: "https://github.com/DjangoToni/aprs-tracker#aprs-monitor-map-card",
    preview: false,
  });
}
