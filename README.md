# APRS Monitor 1.3.0

APRS Monitor is a tested Home Assistant custom integration for tracking multiple
amateur-radio stations through the aprs.fi API.

German documentation is available in [docs/README.de.md](docs/README.de.md).

Installation guides: [English](docs/installation.md) ·
[Deutsch](docs/installation.de.md)

## Requirements

- Home Assistant 2026.7.0 or newer
- an aprs.fi API key
- one or more exact APRS callsigns

## Installation with HACS

1. Add `https://github.com/DjangoToni/aprs-tracker` as a custom integration
   repository in HACS.
2. Install **APRS Monitor** and restart Home Assistant.
3. Open **Settings > Devices & services > Add integration > APRS Monitor**.

Published releases use the fixed HACS asset name `aprs_monitor.zip`.

## Optional dashboards and automation blueprints

Release 1.3.0 provides a separate `aprs_monitor-1.3.0-extras.zip`. Extract it
directly into Home Assistant's `/config` directory. It installs:

- `/config/blueprints/automation/aprs_monitor/station_activity_actions.yaml`
- `/config/blueprints/automation/aprs_monitor/api_connection_actions.yaml`
- `/config/blueprints/automation/aprs_monitor/zone_activity_actions.yaml`
- `/config/aprs_monitor_examples/dashboard.yaml`
- `/config/aprs_monitor_examples/README.md`

Reload automations or restart Home Assistant after copying the blueprints. Create
an automation from **Settings > Automations & scenes > Blueprints** and select the
desired APRS event entity and actions. Actions are deliberately generic, so the
blueprints are not tied to a particular notification integration.

The dashboard example contains explicit `REPLACE_WITH_...` placeholders because
Home Assistant entity IDs depend on the installation language and existing entity
registry. Replace them with entity IDs from your instance before copying the YAML
into a manual dashboard. Its map card uses Recorder history for a 24-hour trail and
does not make additional aprs.fi requests.

## APRS Monitor control center

In addition to the individual station devices, Home Assistant creates one central
`APRS Monitor` device with five entities:

- aprs.fi API connectivity
- overall status (`OK`, `Degraded`, or `Error`)
- counts of current, stale, and missing stations as status attributes
- last successful update timestamp
- API outage and recovery events
- an `Update now` button for an immediate coordinator refresh

The connection, overall-status, last-update, and refresh entities remain available
during an API outage. This makes recovery controls and failure automations usable
when the station entities are unavailable. No callsigns or coordinates are exposed
by the aggregate status.

## Entities per callsign

- one GPS `device_tracker`
- speed sensor in km/h
- course sensor in degrees
- translated eight-point course-direction sensor
- altitude sensor in meters
- distance-from-home sensor in kilometers
- bearing-from-home sensor in degrees
- diagnostic last-seen timestamp sensor
- diagnostic position-age sensor in minutes
- station-status sensor (`current`, `stale`, or `no position`)
- APRS-symbol sensor
- position-current binary sensor
- configurable near-home binary sensor
- configurable moving binary sensor
- station-activity event entity for automations

All entities share one aprs.fi request and belong to the same Home Assistant
device. A sensor is unavailable when the station does not report that specific
value.

Distance and bearing are calculated locally from Home Assistant's configured
home coordinates. They do not cause additional aprs.fi requests. Bearing means
the initial direction from home toward the station; the course sensor remains
the station's reported direction of movement.

## APRS symbols on the map

The GPS tracker converts common APRS station symbols into matching Home Assistant
MDI icons. Cars, bicycles, motorcycles, trucks, buses, aircraft, helicopters,
balloons, ships, weather stations, emergency vehicles, radio sites, and several
other station types therefore appear with a meaningful icon on Home Assistant
maps. Missing or unknown APRS symbols use a standard map marker.

Version 1.3 adds the original aprs.fi APRS symbol graphics. Open the integration's
**Configure** dialog and change **Map marker style** from the compatible Home
Assistant station icon to **Original APRS symbol graphic**. Home Assistant then
crops the actual pictogram from the bundled primary or alternate APRS table and
applies alphanumeric overlays where required. Images are served locally without
requests to an image service and contain no callsign or position data. Switching
the style reloads the integration but preserves tracker entity IDs and history.
The graphics come from the [open aprs.fi symbol set](https://github.com/hessu/aprs-symbols),
with its complete per-symbol attribution included in the integration package.

The raw symbol remains available in the `APRS symbol` sensor and the tracker's
`symbol` attribute. The tracker also exposes `aprs_symbol_character` and
`aprs_symbol_icon`; the original APRS comment remains in the `comment` attribute.
No symbol or comment content is included in downloaded diagnostics.

Every current tracker also exposes a compact `map_label` attribute for Home
Assistant's standard map card. It combines the station profile display name with
available speed, eight-point course direction, and altitude, for example
`HB9ABC · 46 km/h · SE · 408 m`. Missing values are omitted. Configure a map
entity with `label_mode: attribute` and `attribute: map_label` to use it. The
more detailed `map_details` attribute additionally includes the callsign, course
in degrees, and coordinates, for example
`Rescue 1 (HB9ABC) · 46 km/h · SE (123°) · 408 m · 47.37690, 8.54170`.
The extras dashboard uses this detailed label in its telemetry view and keeps a
separate symbol view for the original APRS graphics. Home Assistant's standard
map card does not support custom multi-field hover tooltips.

### APRS Monitor Map Card

Version 1.3 includes the optional `custom:aprs-monitor-map-card`. It preserves
the original APRS pictograms and shows callsign, speed, cardinal and degree
course, altitude, coordinates, and last-seen time in a localized hover tooltip.
The card reads the existing tracker states and creates no additional aprs.fi
requests. Leaflet 1.9.4 is bundled locally under its BSD 2-Clause license; no
external JavaScript CDN is used.

Register this JavaScript module once under **Settings > Dashboards > Resources**:

```text
/api/aprs_monitor/frontend/aprs-monitor-map-card.js?v=1.3.0
```

Then use it in a manual card:

```yaml
type: custom:aprs-monitor-map-card
title: APRS Live
height: 500
auto_fit: true
scroll_wheel_zoom: true
entities:
  - device_tracker.first_callsign
  - device_tracker.second_callsign
```

Clicking a marker opens Home Assistant's normal entity details. Mouse-wheel zoom
is enabled explicitly in this example and remains opt-in so ordinary dashboard
scrolling is not captured unexpectedly. `tile_url`, `attribution`, `zoom`, and
`max_zoom` are optional advanced settings. The default map tiles are provided by
OpenStreetMap and require network access, just like other online tile maps.

## Station activity events

Every callsign has a `Station activity` event entity. It can emit:

- `movement_started` and `movement_stopped`
- `entered_home_radius` and `left_home_radius`
- `entered_zone` and `left_zone`
- `position_current`, `position_stale`, and `position_lost`

No event is emitted during integration startup or reload. A failed aprs.fi request
also emits no station event, because an API outage must not be interpreted as a
real movement or lost position.

Zone events follow Home Assistant's active-zone rules: the smallest matching
non-passive zone wins. A direct move between zones emits `left_zone` followed by
`entered_zone`. Event attributes include the zone name and entity ID plus origin
and destination context, but never coordinates. Stale and missing positions do
not imply a zone departure.

An automation can react to one event type by monitoring the event entity's
`event_type` attribute:

```yaml
trigger:
  - platform: state
    entity_id: event.aprs_hb9abc_station_activity
    attribute: event_type
    to: movement_started
action:
  - service: notify.notify
    data:
      message: "HB9ABC bewegt sich."
```

Use the actual entity ID shown by Home Assistant. Events include useful context
such as speed, distance from home, position age, and the applicable threshold,
but never coordinates.

## Options

Open **Settings > Devices & services > APRS Monitor > Configure** to change:

- the monitored callsigns
- the update interval from 5 to 60 minutes (default: 15 minutes)
- the maximum position age from 15 to 1440 minutes (default: 120 minutes)
- the near-home radius from 1 to 1000 kilometers (default: 25 kilometers)
- the movement threshold from 0.5 to 50 km/h (default: 1 km/h)
- the map marker style (`Home Assistant station icon` or `Original APRS symbol graphic`)

Saving options reloads the integration automatically. The API key remains
unchanged.

After the global options, a second form shows one collapsible profile section per
callsign. Each station can have its own display name, maximum position age,
near-home radius, and movement-speed threshold.

The callsign remains the stable device identifier and aprs.fi query value. Changing
only the display name therefore preserves devices, history, automations, and entity
unique IDs. Existing entries without profile data inherit the global values until
profiles are saved for the first time.

When a position exceeds the configured age, its tracker, speed, course, and
altitude entities become unavailable. The last-seen timestamp stays available
and exposes age and stale-status attributes for diagnostics and automations. The
position-age sensor also stays available for a stale position. The station-status
sensor explicitly reports `Current`, `Stale`, or `No position`; an API failure
makes it unavailable to preserve the distinction from a successful empty response.

## API key recovery

If aprs.fi rejects the stored API key, Home Assistant starts a reauthentication
flow. Enter a replacement key in the integration notification. APRS Monitor
validates it before updating the existing entry; callsigns, options, devices,
and entity IDs stay unchanged.

## Diagnostics

Download diagnostics from the APRS Monitor config entry menu on Home Assistant's
integrations page. The file includes integration version, options, coordinator
status, station count, position freshness, and field availability. API keys,
callsigns, coordinates, comments, and exact reception timestamps are excluded or
redacted.

## Position-current status

Each station has a translated `Position current` binary sensor. It is on while
the latest APRS position is within the configured maximum age, off when the
position is missing or stale, and unavailable only when the shared API update
fails. This makes freshness directly usable in dashboards and automations.

The `Near home` binary sensor is available only with a current position. It is
on inside the configured radius and off outside it. Missing or stale positions
make it unavailable so automations cannot mistake unknown location for absence.

The `Moving` binary sensor is on when the reported APRS speed reaches the
configured threshold. Missing speed or stale position data makes the entity
unavailable so unknown telemetry cannot be mistaken for standstill.

## Removing callsigns

When a callsign is removed in **Configure**, APRS Monitor removes the associated
device and its registered entities during the automatic reload. Cleanup only
targets devices with an APRS Monitor identifier that is no longer configured;
active callsigns and devices from other integrations are protected.

## System health

Open **Settings > System > Repairs > three-dot menu > System information** to
view aprs.fi reachability, configured and loaded entry counts, station count,
update settings, last update result, and the last successful update time. No API
key, callsign, coordinate, or packet content is included.

APRS Monitor relies on Home Assistant's DataUpdateCoordinator transition
logging: one error is logged when updates begin failing and one information
message is logged when updates recover.

## Development tests

The fast unit tests run without Home Assistant. The runtime suite loads the
custom integration inside Home Assistant 2026.7.2 and verifies config flows,
reauthentication, options, entity setup, unloading, and coordinator recovery.
CI runs this suite on Python 3.14, matching the Home Assistant release.

Release tags such as `v0.1.0` are accepted only when the manifest, Python
package, and integration constants contain the same version. The release job
then creates reproducible HACS and manual-install ZIP files with SHA-256 sums.

## Upgrade

1. Replace `/config/custom_components/aprs_monitor` with the directory from the
   direct-folder release ZIP, or update through HACS.
2. Restart Home Assistant.
3. Reload APRS Monitor or allow it to load during the restart.

The existing config entry, options, devices, and entity IDs remain installed
during this upgrade.

See the [German upgrade and rollback guide](docs/upgrade.de.md) and the
[stable entity contract](docs/entity-contract.md) before production upgrades.

## Data source

Data is provided by [aprs.fi](https://aprs.fi/). APRS Monitor is read-only and
does not transmit packets or messages.

## License

MIT
