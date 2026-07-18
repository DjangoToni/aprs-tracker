# APRS Monitor dashboard and blueprints

Extract the extras archive directly into the Home Assistant `/config` directory.
The three blueprints then reside below `/config/blueprints/automation/aprs_monitor`.
Reload automations or restart Home Assistant before creating an automation from a
blueprint.

The dashboard example is installed as
`/config/aprs_monitor_examples/dashboard.yaml`. Open it, replace every
`REPLACE_WITH_...` placeholder with the corresponding entity ID from your Home
Assistant instance, then copy the YAML into a new manual dashboard.

The dashboard contains separate zone, symbol, telemetry, and 24-hour history
views. The zone view uses each tracker's Home Assistant state as its label and
shows the latest station activity events beside the map. Replace the zone and
event placeholders just like the tracker placeholders.

Before using the symbol view, register this URL as a JavaScript module under
**Settings > Dashboards > Resources** and refresh the browser:

```text
/api/aprs_monitor/frontend/aprs-monitor-map-card.js?v=1.4.0
```

The symbol view uses `custom:aprs-monitor-map-card` to render the original APRS
graphic and show callsign, speed, direction, altitude, coordinates, and last-seen
time on hover. Clicking the symbol opens Home Assistant's normal entity details.
The included example enables `scroll_wheel_zoom: true`, so the map zooms around
the mouse pointer; remove that line if dashboard page scrolling should take
priority.
The same card draws a 24-hour Recorder trail for each configured tracker. Green,
orange, and grey marker rings represent current, stale, and unavailable stations.
Each entity can define its own trail `color`; set `hours_to_show: 0` to disable
history. Recorder access adds no aprs.fi request.
The separate telemetry view uses the tracker's `map_details` attribute as a text
marker for installations that prefer the standard Home Assistant map card.
Missing APRS telemetry values are omitted automatically.

The custom map card always uses the locally rendered APRS pictogram. The global
**Map marker style** integration option continues to control standard Home
Assistant map cards.

The zone arrival/departure blueprint filters `entered_zone` and `left_zone`
events for one selected active Home Assistant zone. It provides independent
action selectors for arrival and departure. Passive zones are not active zones.

The history view uses Home Assistant Recorder data. Change `hours_to_show` as
desired. None of the map views perform additional aprs.fi requests.
