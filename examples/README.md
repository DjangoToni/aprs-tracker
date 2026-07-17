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

The symbol view renders each tracker's dynamic APRS-derived icon. The telemetry
view uses the tracker's `map_label` attribute to show its display name, speed,
course direction, and altitude in one compact marker label. Missing APRS values
are omitted automatically.

The zone arrival/departure blueprint filters `entered_zone` and `left_zone`
events for one selected active Home Assistant zone. It provides independent
action selectors for arrival and departure. Passive zones are not active zones.

The history view uses Home Assistant Recorder data. Change `hours_to_show` as
desired. None of the map views perform additional aprs.fi requests.
