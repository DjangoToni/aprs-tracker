# Coordinator and entity architecture

Version 1.0.0 expands the shared coordinator data into station and hub entities:

```text
aprs.fi API -> shared coordinator -> GPS device tracker + dynamic APRS map icon
                                  -> position-current binary sensor
                                  -> near-home binary sensor
                                  -> moving binary sensor
                                  -> station-status sensor
                                  -> speed sensor
                                  -> course sensor
                                  -> course-direction sensor
                                  -> altitude sensor
                                  -> distance-from-home sensor
                                  -> bearing-from-home sensor
                                  -> last-seen sensor
                                  -> position-age sensor
                                  -> APRS-symbol sensor
                                  -> station-activity event entity
            shared coordinator -> central APRS Monitor hub device
                               -> API connectivity binary sensor
                               -> overall-status sensor with aggregate counts
                               -> last-successful-update sensor
                               -> API connection event entity
                               -> manual refresh button
```

No sensor performs its own network request. Missing optional fields make only the
corresponding sensor unavailable. The options flow updates callsigns and the
5-to-60-minute polling interval, then reloads the config entry once.

Distance and initial bearing are derived locally from Home Assistant's configured
home coordinates and the shared APRS position. They create no extra network
request and are intentionally excluded from diagnostics.

The near-home sensor compares the local distance with a configurable 1-to-1000
kilometer threshold. It becomes unavailable for missing or stale position data,
which preserves an explicit unknown state for safety-sensitive automations.

The moving sensor compares current APRS speed with a configurable 0.5-to-50
km/h threshold. Missing speed and stale data remain unavailable rather than
being interpreted as stationary.

Position freshness is evaluated from the aprs.fi `lasttime` timestamp. Tracker,
speed, course, and altitude entities become unavailable after the configured
15-to-1440-minute limit. The last-seen and position-age diagnostic sensors remain
available. The station-status enum distinguishes a current position, a stale
position, and a successful API response containing no position for that station.

The tracker translates the station-type character of common APRS symbols into
MDI icons used by Home Assistant maps. The complete raw APRS symbol remains
unchanged in entity data. Unknown symbol characters fall back to `mdi:map-marker`.
Symbol and comment values remain excluded from config-entry diagnostics.

Version 1.1 adds a presentation-only `map_label` tracker attribute. It combines
the effective station display name with available speed, compact course direction,
and altitude. Formatting is local, creates no additional entity or API request,
and omits unknown telemetry instead of inserting placeholder values.

Version 1.3 adds a presentation-only `map_details` tracker attribute containing
the callsign, available speed, cardinal and degree course, altitude, and current
coordinates. It is formatted locally from the same position response and is used
by the example dashboard's standard telemetry map.

The optional APRS Monitor Map Card is served through Home Assistant's static-path
API and registered manually as a Lovelace JavaScript module. It uses only existing
tracker states, escapes all entity-derived tooltip content, and never receives an
API key or performs an aprs.fi request. A pinned local Leaflet 1.9.4 distribution
renders the OpenStreetMap tile layer, APRS markers, and localized hover tooltips;
the integration does not depend on undocumented Home Assistant frontend elements
or an external JavaScript CDN.

Version 1.4 optionally requests device-tracker history from Home Assistant's
permission-filtered `history/history_during_period` WebSocket command. It keeps
live state rendering independent from Recorder availability, limits the requested
time range to 168 hours, caps rendered points per station, removes consecutive
duplicate positions, and downsamples longer tracks. History is refreshed on a
bounded interval and never causes an aprs.fi request. Marker state is derived from
the live tracker attributes; when live coordinates are unavailable, only the last
Recorder coordinate is reused and the marker remains visibly unavailable.

Version 1.2 extends the immutable station activity snapshot with Home Assistant's
active zone. Zone selection delegates to the core zone integration, which ignores
passive zones and prefers the smallest matching active zone. Only two consecutive
current snapshots can emit a zone transition. Direct zone-to-zone movement emits
the departure before the arrival and carries names and entity IDs without
coordinates. This calculation is local and adds no aprs.fi request.

Version 1.3 optionally exposes a local `entity_picture` for each current tracker.
The URL contains only hexadecimal encodings of two validated printable APRS
symbol characters. A read-only Home Assistant view crops the matching transparent
PNG from bundled primary and alternate aprs.fi sprite tables and composites the
overlay table where required. Rendering runs in Home Assistant's executor and is
cached; it never receives a callsign, coordinate, comment, or credential. The
default MDI style remains unchanged for existing installations. Changing the
presentation style reloads entities without changing their unique IDs.

The activity event entity stores a snapshot after each successful coordinator
update and emits only meaningful transitions. Its first snapshot is established
during entity construction, preventing false startup and reload events. Failed
coordinator updates are ignored, so an aprs.fi outage cannot produce movement,
radius, stale, or lost-position events. Unknown speed never means stopped, and an
unknown radius state never means outside the configured radius.

Hub entities use a reserved `hub:` device identifier. Registry cleanup excludes
that prefix before comparing identifiers with configured callsigns. Connectivity,
summary, last-successful-update, connection-event, and refresh entities override
coordinator availability where necessary so failures remain visible and recovery
controls remain usable.

Optional automation blueprints consume the event entities through Home Assistant
state triggers and expose action selectors instead of calling a notification
service directly. Dashboard history is provided by Home Assistant Recorder. The
extras are packaged separately from the HACS integration so blueprint and example
files can be extracted at the correct `/config` paths without changing the custom
component layout.

Station profiles are normalized once when the coordinator is created. Every
callsign receives an effective immutable profile, even for legacy entries that have
no stored profile block. Entities use the callsign for identifiers and the profile
only for presentation and thresholds. This keeps entity IDs and Recorder history
stable when a display name changes. Profile dictionaries are redacted as a whole in
diagnostics because both dictionary keys and friendly names can identify stations.

Config-entry schema 2 materializes normalized profiles for legacy entries. Runtime
setup repeats defensive normalization so externally damaged options cannot bypass
range checks. A future schema version is rejected instead of being downgraded.

Authentication failures raised by the coordinator start Home Assistant's reauth
flow. A replacement API key is validated against the active callsigns before the
existing config entry is updated and reloaded.

Config-entry diagnostics expose only technical state. Credentials and callsigns
are redacted; station identifiers are replaced with sequential aliases, and no
coordinates, comments, or exact reception timestamps are included.

The position-current binary sensor stays off for a missing or stale position.
Coordinator failures make it unavailable, preserving the distinction between
old station data and a failed aprs.fi request.

After a successful coordinator refresh, registry cleanup compares APRS Monitor
device identifiers with the configured callsign set. Only devices with a known
APRS identifier that is no longer configured have this config-entry association
removed, which also removes their entities.

The system-health platform reports endpoint reachability and aggregate runtime
state without callsigns, credentials, coordinates, or packet contents. The
coordinator records the last successful request time and delegates transition
logging to Home Assistant's DataUpdateCoordinator.
