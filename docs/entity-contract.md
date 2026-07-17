# Stable entity contract

APRS Monitor 1.0.0 freezes the following unique-ID structure for the 1.x line.
Display names and Home Assistant entity IDs may be customized by the user, but
integration upgrades must not change these unique IDs.

## Per station

The tracker uses `{entry_id}_{callsign}`. The remaining 14 station entities append:

- `_speed`, `_course`, `_course_direction`, `_altitude`
- `_distance_from_home`, `_bearing_from_home`
- `_last_seen`, `_position_age`, `_aprs_symbol`, `_station_status`
- `_position_current`, `_near_home`, `_moving`
- `_station_activity`

## Central hub

The five hub entities append:

- `_api_connected`
- `_overall_status`
- `_last_successful_update`
- `_connection_activity`
- `_refresh`

Callsigns and config-entry IDs remain the identity sources. Station profile display
names never participate in a device or entity unique ID.

Tracker attributes, including the version 1.1 `map_label` and version 1.3
`map_details`, are presentation data and do not change this unique-ID contract.

Version 1.2 adds `entered_zone` and `left_zone` to the existing station activity
event entity. No entity or device unique ID changes, and no migration is required.

Version 1.3 adds the optional `entity_picture` and `aprs_symbol_picture` tracker
attributes. They are presentation data; selecting APRS symbol graphics does not
change entity IDs, devices, automations, or Recorder history.
