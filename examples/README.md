# APRS Monitor dashboard and blueprints

Extract the extras archive directly into the Home Assistant `/config` directory.
The two blueprints then reside below `/config/blueprints/automation/aprs_monitor`.
Reload automations or restart Home Assistant before creating an automation from a
blueprint.

The dashboard example is installed as
`/config/aprs_monitor_examples/dashboard.yaml`. Open it, replace every
`REPLACE_WITH_...` placeholder with the corresponding entity ID from your Home
Assistant instance, then copy the YAML into a new manual dashboard.

The map card uses Home Assistant Recorder history for a 24-hour track. Change
`hours_to_show` as desired. The integration performs no additional API requests
for this history.
