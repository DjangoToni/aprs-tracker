const FRONTEND_BASE = new URL(".", import.meta.url);
const LEAFLET_SCRIPT = new URL("vendor/leaflet/leaflet.js", FRONTEND_BASE).href;
const LEAFLET_STYLE = new URL("vendor/leaflet/leaflet.css", FRONTEND_BASE).href;
const TRACK_COLORS = ["#039be5", "#e53935", "#43a047", "#fb8c00", "#8e24aa", "#00897b"];

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
      current: "Aktuell",
      empty: "Keine aktuellen APRS-Positionen verfügbar",
      historyUnavailable: "Recorder-Verlauf konnte nicht geladen werden",
      lastSeen: "Letztes Signal",
      speed: "Geschwindigkeit",
      stale: "Veraltet",
      status: "Status",
      unavailable: "Nicht verfügbar",
    };
  }
  return {
    altitude: "Altitude",
    coordinates: "Coordinates",
    course: "Direction",
    current: "Current",
    empty: "No current APRS positions available",
    historyUnavailable: "Recorder history could not be loaded",
    lastSeen: "Last signal",
    speed: "Speed",
    stale: "Stale",
    status: "Status",
    unavailable: "Unavailable",
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

function validCoordinate(latitude, longitude) {
  return (
    latitude !== null &&
    longitude !== null &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180
  );
}

function markerStatus(state, usesHistoryFallback = false) {
  if (usesHistoryFallback || state?.state === "unknown" || state?.state === "unavailable") {
    return "unavailable";
  }
  if (state?.attributes?.position_stale === true) return "stale";
  return "current";
}

function historyPoints(states, maximum) {
  const points = [];
  for (const item of states ?? []) {
    const attrs = item.attributes ?? item.a ?? {};
    const latitude = numeric(attrs.latitude);
    const longitude = numeric(attrs.longitude);
    if (!validCoordinate(latitude, longitude)) continue;
    const previous = points.at(-1);
    if (previous?.[0] === latitude && previous?.[1] === longitude) continue;
    points.push([latitude, longitude]);
  }
  if (points.length <= maximum) return points;
  const step = (points.length - 1) / (maximum - 1);
  return Array.from({ length: maximum }, (_, index) => points[Math.round(index * step)]);
}

export { historyPoints, markerStatus, validCoordinate };

class AprsMonitorMapCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._markers = new Map();
    this._historyLayers = new Map();
    this._historyPositions = new Map();
    this._historyLoadedAt = 0;
    this._historyLoading = false;
    this._historyRequest = 0;
    this._fitted = false;
  }

  setConfig(config) {
    if (!Array.isArray(config.entities) || config.entities.length === 0) {
      throw new Error("APRS Monitor Map Card requires at least one tracker entity");
    }
    this._config = {
      auto_fit: true,
      height: 500,
      history_refresh_minutes: 15,
      hours_to_show: 0,
      max_zoom: 16,
      max_history_points: 2000,
      show_status: true,
      track_opacity: 0.7,
      track_weight: 4,
      ...config,
    };
    this._entityConfigs = config.entities.map((item, index) => ({
      color: TRACK_COLORS[index % TRACK_COLORS.length],
      ...(typeof item === "string" ? { entity: item } : item),
    }));
    this._config.entities = this._entityConfigs.map((item) => item.entity);
    if (this._entityConfigs.some((item) => !item.entity)) {
      throw new Error("Every APRS Monitor map entity needs an entity ID");
    }
    const historyHours = numeric(this._config.hours_to_show) ?? 0;
    if (historyHours < 0 || historyHours > 168) {
      throw new Error("hours_to_show must be between 0 and 168");
    }
    this._resizeObserver?.disconnect();
    this._map?.remove();
    this._map = undefined;
    this._markers.clear();
    this._historyLayers.clear();
    this._historyPositions.clear();
    this._historyLoadedAt = 0;
    this._historyLoading = false;
    this._historyRequest += 1;
    this._fitted = false;
    this._renderShell();
    this._startMap();
  }

  set hass(hass) {
    this._hass = hass;
    this._updateTitle();
    this._updateMarkers();
    this._scheduleHistoryLoad();
  }

  connectedCallback() {
    this._startMap();
  }

  disconnectedCallback() {
    this._resizeObserver?.disconnect();
    this._historyRequest += 1;
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
        .aprs-marker-frame {
          align-items: center;
          border-radius: 50%;
          display: flex;
          height: 48px;
          justify-content: center;
          position: relative;
          transition: filter 160ms ease, box-shadow 160ms ease;
          width: 48px;
        }
        .aprs-marker-frame.status-current { box-shadow: 0 0 0 3px #43a047; }
        .aprs-marker-frame.status-stale { box-shadow: 0 0 0 4px #fb8c00; }
        .aprs-marker-frame.status-unavailable {
          box-shadow: 0 0 0 4px #757575;
          filter: grayscale(1) opacity(0.72);
        }
        .aprs-marker-frame img {
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
        .notice {
          background: color-mix(in srgb, var(--warning-color, #ff9800) 18%, var(--card-background-color));
          border-radius: 8px;
          bottom: 24px;
          color: var(--primary-text-color);
          display: none;
          font-size: 12px;
          left: 50%;
          max-width: calc(100% - 48px);
          padding: 7px 10px;
          pointer-events: none;
          position: absolute;
          transform: translateX(-50%);
          z-index: 800;
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
          <div class="notice"></div>
        </div>
      </ha-card>`;
    this._mapElement = this.shadowRoot.querySelector("#map");
    this._emptyElement = this.shadowRoot.querySelector(".empty");
    this._noticeElement = this.shadowRoot.querySelector(".notice");
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
      this._scheduleHistoryLoad();
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
    for (const entityConfig of this._entityConfigs) {
      const entityId = entityConfig.entity;
      const state = this._hass.states[entityId];
      if (!state) continue;
      const currentLatitude = numeric(state.attributes.latitude);
      const currentLongitude = numeric(state.attributes.longitude);
      const currentValid = validCoordinate(currentLatitude, currentLongitude);
      const fallback = this._historyPositions.get(entityId);
      const usesHistoryFallback = !currentValid && Boolean(fallback);
      const latitude = currentValid ? currentLatitude : fallback?.[0] ?? null;
      const longitude = currentValid ? currentLongitude : fallback?.[1] ?? null;
      if (!validCoordinate(latitude, longitude)) continue;
      const status = markerStatus(state, usesHistoryFallback);
      active.add(entityId);
      bounds.push([latitude, longitude]);
      const picture = state.attributes.entity_picture ?? state.attributes.aprs_symbol_picture;
      let marker = this._markers.get(entityId);
      if (!marker) {
        marker = this._L.marker([latitude, longitude], {
          icon: this._markerIcon(state, picture, status),
          keyboard: true,
          title: state.attributes.friendly_name ?? state.attributes.callsign ?? entityId,
        });
        marker._aprsPicture = picture;
        marker._aprsStatus = status;
        marker.bindTooltip(this._tooltip(state, status, latitude, longitude), {
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
        marker.setTooltipContent(this._tooltip(state, status, latitude, longitude));
        if (marker._aprsPicture !== picture || marker._aprsStatus !== status) {
          marker.setIcon(this._markerIcon(state, picture, status));
          marker._aprsPicture = picture;
          marker._aprsStatus = status;
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

  _scheduleHistoryLoad() {
    const hours = numeric(this._config?.hours_to_show) ?? 0;
    if (!this._map || !this._hass?.callWS || hours <= 0 || this._historyLoading) return;
    const refreshMinutes = Math.max(
      5,
      Math.min(60, numeric(this._config.history_refresh_minutes) ?? 15),
    );
    if (Date.now() - this._historyLoadedAt < refreshMinutes * 60_000) return;
    this._loadHistory();
  }

  async _loadHistory() {
    const hours = numeric(this._config.hours_to_show) ?? 0;
    const request = ++this._historyRequest;
    const firstLoad = this._historyLoadedAt === 0;
    this._historyLoading = true;
    try {
      const end = new Date();
      const start = new Date(end.getTime() - hours * 60 * 60 * 1000);
      const result = await this._hass.callWS({
        type: "history/history_during_period",
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        entity_ids: this._config.entities,
        include_start_time_state: true,
        significant_changes_only: false,
        minimal_response: false,
        no_attributes: false,
      });
      if (request !== this._historyRequest || !this._map) return;
      const maximum = Math.max(
        100,
        Math.min(5000, Math.round(numeric(this._config.max_history_points) ?? 2000)),
      );
      const allHistoryBounds = [];
      this._historyPositions.clear();
      for (const entityConfig of this._entityConfigs) {
        const points = historyPoints(result?.[entityConfig.entity], maximum);
        if (points.length) {
          this._historyPositions.set(entityConfig.entity, points.at(-1));
          allHistoryBounds.push(...points);
        }
        this._renderHistory(entityConfig, points);
      }
      this._historyLoadedAt = Date.now();
      this._setNotice();
      this._updateMarkers();
      if (firstLoad && this._config.auto_fit && allHistoryBounds.length) {
        const markerBounds = [...this._markers.values()].map((marker) => {
          const point = marker.getLatLng();
          return [point.lat, point.lng];
        });
        const bounds = [...allHistoryBounds, ...markerBounds];
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
    } catch (error) {
      if (request === this._historyRequest) {
        this._historyLoadedAt = Date.now();
        this._setNotice(localeText(this._hass.language).historyUnavailable);
        console.warn("APRS Monitor history request failed", error);
      }
    } finally {
      if (request === this._historyRequest) this._historyLoading = false;
    }
  }

  _renderHistory(entityConfig, points) {
    const existing = this._historyLayers.get(entityConfig.entity);
    if (points.length < 2) {
      if (existing) {
        existing.removeFrom(this._map);
        this._historyLayers.delete(entityConfig.entity);
      }
      return;
    }
    const style = {
      color: entityConfig.color,
      interactive: false,
      opacity: Math.max(0.1, Math.min(1, numeric(this._config.track_opacity) ?? 0.7)),
      weight: Math.max(1, Math.min(12, numeric(this._config.track_weight) ?? 4)),
    };
    if (existing) {
      existing.setLatLngs(points);
      existing.setStyle(style);
      return;
    }
    this._historyLayers.set(
      entityConfig.entity,
      this._L.polyline(points, style).addTo(this._map),
    );
  }

  _setNotice(message = "") {
    if (!this._noticeElement) return;
    this._noticeElement.textContent = message;
    this._noticeElement.style.display = message ? "block" : "none";
  }

  _markerIcon(state, picture, status) {
    const statusClass = this._config.show_status === false ? "" : ` status-${status}`;
    if (picture) {
      return this._L.divIcon({
        className: "aprs-monitor-marker",
        html: `<div class="aprs-marker-frame${statusClass}"><img src="${escapeHtml(picture)}" alt=""></div>`,
        iconAnchor: [24, 24],
        iconSize: [48, 48],
      });
    }
    const callsign = state.attributes.callsign ?? state.attributes.friendly_name ?? "APRS";
    return this._L.divIcon({
      className: "aprs-monitor-marker",
      html: `<div class="aprs-marker-frame${statusClass}"><div class="aprs-monitor-fallback">${escapeHtml(callsign)}</div></div>`,
      iconAnchor: [24, 18],
      iconSize: [48, 36],
    });
  }

  _tooltip(state, status, markerLatitude, markerLongitude) {
    const attrs = state.attributes;
    const labels = localeText(this._hass.language);
    const speed = numeric(attrs.speed_kmh);
    const course = numeric(attrs.course);
    const altitude = numeric(attrs.altitude_m);
    const latitude = numeric(markerLatitude);
    const longitude = numeric(markerLongitude);
    const name = attrs.friendly_name ?? attrs.callsign ?? state.entity_id;
    const callsign = attrs.callsign && attrs.callsign !== name ? ` (${attrs.callsign})` : "";
    const rows = [[labels.status, labels[status] ?? status]];
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
