# Configuring the APRS Monitor dashboard

This guide covers the bundled `custom:aprs-monitor-map-card` and the complete
example dashboard. The card displays original APRS graphics, telemetry tooltips,
colored Recorder trails, and the freshness state of every station.

## Requirements

- APRS Monitor 1.4.0 or newer is installed and configured.
- Home Assistant contains at least one APRS device tracker.
- Home Assistant Recorder records the trackers when trails are required.
- Enable **Advanced mode** in the user profile if dashboard resources are hidden.

Find the actual entity IDs under **Settings > Devices & services > APRS Monitor**
or **Developer tools > States**. Always use the IDs from your own installation.

## 1. Register the JavaScript resource

Open **Settings > Dashboards > Resources**, choose **Add resource**, and enter:

```text
/api/aprs_monitor/frontend/aprs-monitor-map-card.js?v=1.4.0
```

Select **JavaScript module** as the resource type. Register the URL only once and
fully reload the Home Assistant page afterward. Change the value after `?v=` when
upgrading so the browser loads the new file.

## 2. Minimal single-station card

Add a **Manual card** to a dashboard and use:

```yaml
type: custom:aprs-monitor-map-card
title: APRS Live
entities:
  - device_tracker.YOUR_CALLSIGN
```

This compatible configuration shows the current position without a trail.
Clicking the marker opens Home Assistant's normal entity details.

## 3. Recommended multi-station live card

```yaml
type: custom:aprs-monitor-map-card
title: APRS Live Telemetry
height: 500
auto_fit: true
scroll_wheel_zoom: true
hours_to_show: 24
history_refresh_minutes: 15
max_history_points: 2000
show_status: true
track_weight: 4
track_opacity: 0.7
entities:
  - entity: device_tracker.YOUR_FIRST_CALLSIGN
    color: "#039be5"
  - entity: device_tracker.YOUR_SECOND_CALLSIGN
    color: "#e53935"
  - entity: device_tracker.YOUR_THIRD_CALLSIGN
    color: "#43a047"
```

Hovering over a marker shows its callsign, speed, direction, altitude,
coordinates, last signal, and status. Marker rings mean:

- green: current position
- orange: stale position
- grey: unavailable station; the last Recorder position is retained when available

The card reads states and history only from Home Assistant. It never performs an
additional aprs.fi request.

## Card options

| Option | Default | Valid range and effect |
| --- | --- | --- |
| `entities` | required | Tracker IDs or objects containing `entity` and optional `color` |
| `title` | `APRS Monitor` | Card heading; an empty string hides it |
| `height` | `500` | Card height in pixels; at least 240 pixels are rendered |
| `auto_fit` | `true` | Initially fits the view to markers and trails |
| `scroll_wheel_zoom` | `false` | Enables pointer-centered mouse-wheel zoom |
| `zoom` | `8` | Initial zoom; auto-fit uses 13 by default for one marker |
| `max_zoom` | `16` | Maximum zoom used by automatic fitting |
| `hours_to_show` | `0` | `0` disables trails; `1` through `168` load Recorder history |
| `history_refresh_minutes` | `15` | History refresh interval, clamped to 5 through 60 minutes |
| `max_history_points` | `2000` | Maximum points per station, clamped to 100 through 5000 |
| `show_status` | `true` | Shows green, orange, and grey marker rings |
| `track_weight` | `4` | Trail width, clamped to 1 through 12 |
| `track_opacity` | `0.7` | Trail opacity, clamped to 0.1 through 1.0 |
| `tile_url` | OpenStreetMap | Optional Leaflet tile URL containing `{z}`, `{x}`, and `{y}` |
| `attribution` | OpenStreetMap | Required attribution for a custom tile provider |

A simple entity list receives automatic colors:

```yaml
entities:
  - device_tracker.first_station
  - device_tracker.second_station
```

Use the object form for fixed colors:

```yaml
entities:
  - entity: device_tracker.first_station
    color: "#1565c0"
```

## Importing the complete example dashboard

The complete template is available at
[`examples/dashboard.yaml`](../examples/dashboard.yaml). The release extras
archive installs it as `/config/aprs_monitor_examples/dashboard.yaml`.

### Import through the user interface

1. Open **Settings > Dashboards > Add dashboard** and create an empty dashboard.
2. Open it and select **Edit dashboard**.
3. Open the three-dot menu and select **Raw configuration editor**.
4. Replace the current content with the complete contents of
   `examples/dashboard.yaml`.
5. Replace every `REPLACE_WITH_...` value with a real entity ID before saving.

### Import as a YAML dashboard

When dashboards are managed in `configuration.yaml`, include the file installed
by the extras archive directly:

```yaml
lovelace:
  mode: storage
  dashboards:
    aprs-monitor:
      mode: yaml
      title: APRS Monitor
      icon: mdi:radio-tower
      show_in_sidebar: true
      filename: aprs_monitor_examples/dashboard.yaml
```

Check the configuration and restart Home Assistant. The `aprs-monitor` key must
contain a hyphen and must be unique among configured dashboards.

## Complete-template placeholders

| Placeholder | Required entity |
| --- | --- |
| `REPLACE_WITH_FIRST_TRACKER`, etc. | Station APRS `device_tracker` |
| `REPLACE_WITH_API_CONNECTED` | Central API connectivity binary sensor |
| `REPLACE_WITH_OVERALL_STATUS` | Central overall-status sensor |
| `REPLACE_WITH_LAST_SUCCESSFUL_UPDATE` | Last-successful-update sensor |
| `REPLACE_WITH_REFRESH` | Central **Update now** button |
| `REPLACE_WITH_STATION_STATUS` | Status sensor of one station |
| `REPLACE_WITH_SPEED`, `ALTITUDE`, etc. | Corresponding station telemetry sensors |
| `REPLACE_WITH_*_STATION_ACTIVITY` | Station activity event entity |
| `REPLACE_WITH_*_ZONE` | Desired Home Assistant zone |

Stations, zones, cards, or views that are not required can be removed from the
YAML file completely.

## Using Home Assistant's standard map card

Without the custom card, use `map_details` as the standard map label:

```yaml
type: map
title: APRS Telemetry
auto_fit: true
cluster: false
entities:
  - entity: device_tracker.YOUR_CALLSIGN
    label_mode: attribute
    attribute: map_details
  - entity: zone.home
    focus: false
```

A basic 24-hour standard-map trail is configured as follows:

```yaml
type: map
title: APRS trail – 24 hours
hours_to_show: 24
auto_fit: true
cluster: false
entities:
  - entity: device_tracker.YOUR_CALLSIGN
    label_mode: icon
```

The standard map does not provide the multi-line telemetry hover content and
per-station configurable trail lines available in the APRS Monitor card.

## Troubleshooting

- **“Custom element doesn't exist”:** verify the resource URL and type, restart
  Home Assistant, and fully refresh the browser cache.
- **Old card after an update:** change the version after `?v=` and fully reload
  the page again.
- **No trail:** `hours_to_show` must be greater than zero and Recorder must
  contain tracker states. A line requires two different positions.
- **The map captures page scrolling:** set `scroll_wheel_zoom: false` or remove
  the option.
- **Grey marker:** the tracker is unavailable. Its last position is shown only
  when Recorder history contains one.
- **No APRS graphic:** select **Original APRS symbol graphic** under
  **APRS Monitor > Configure** and verify that the station reports a symbol.
- **Empty tile area:** the default tiles require access to
  `tile.openstreetmap.org`; otherwise configure a reachable tile provider.
