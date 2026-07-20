# Installing APRS Monitor

This guide covers installation through HACS, manual installation, initial setup,
updates, and the most common installation problems.

## Requirements

- Home Assistant 2026.7.0 or newer
- HACS 2.0 or newer for the recommended installation method
- an aprs.fi API key from <https://aprs.fi/account/>
- one or more exact APRS callsigns

## Recommended: install with HACS

1. Open **HACS** in the Home Assistant sidebar.
2. Open the three-dot menu in the upper-right corner and select
   **Custom repositories**.
3. Enter `https://github.com/DjangoToni/aprs-tracker` as the repository URL.
4. Select **Integration** as the type and choose **Add**.
5. Search for **APRS Monitor**, open it, and choose **Download**.
6. Select the latest release and confirm the download.
7. Restart Home Assistant when HACS requests it.
8. Open **Settings > Devices & services**, choose **Add integration**, and
   search for **APRS Monitor**.
9. Enter the aprs.fi API key and the callsigns to monitor.

HACS installs the fixed release asset `aprs_monitor.zip`. Do not extract the
direct-folder or extras archives into the HACS download dialog.

## Manual installation

1. Download `aprs_monitor-<version>-direct-folder.zip` from the matching GitHub
   release.
2. Create `/config/custom_components` if it does not exist.
3. Extract the archive into `/config/custom_components`.
4. Verify that this exact file exists:
   `/config/custom_components/aprs_monitor/manifest.json`.
5. Restart Home Assistant completely.
6. Open **Settings > Devices & services > Add integration** and search for
   **APRS Monitor**.

Avoid a duplicated directory such as
`/config/custom_components/aprs_monitor/aprs_monitor`. Home Assistant will not
discover the integration in that structure.

## Optional dashboards and blueprints

The complete card configuration, dashboard import, and troubleshooting guide is
available in [Configuring the APRS Monitor dashboard](dashboard.md).

1. Register `/api/aprs_monitor/frontend/aprs-monitor-map-card.js?v=1.4.0` as a
   JavaScript module under **Settings > Dashboards > Resources**, then refresh
   the browser. This enables the optional map with APRS graphics and telemetry
   hover tooltips.
2. Download `aprs_monitor-<version>-extras.zip` from the same release.
3. Extract it directly into Home Assistant's `/config` directory.
4. Replace every `REPLACE_WITH_...` placeholder in
   `/config/aprs_monitor_examples/dashboard.yaml` with an entity ID from your
   Home Assistant instance.
5. Add the required cards to a dashboard as manual YAML cards.
6. Reload automations or restart Home Assistant before using the included
   blueprints.

The extras archive is optional. APRS Monitor itself works without it.

## Updating

For a HACS installation, open APRS Monitor in HACS, install the offered update,
and restart Home Assistant. For a manual installation, replace only
`/config/custom_components/aprs_monitor` with the folder from the new
direct-folder archive and restart Home Assistant.

Do not delete the APRS Monitor config entry during an update. The API key,
callsigns, profiles, devices, entity IDs, automations, and recorder history are
preserved by a normal update.

## Troubleshooting

- **APRS Monitor is missing from Add integration:** verify the exact manifest
  path above, restart Home Assistant, and refresh the browser page.
- **The device exists but has no entities:** check that every file from the
  component archive was copied, especially the platform files such as
  `sensor.py` and `device_tracker.py`.
- **Authentication fails:** use an aprs.fi API key, not the aprs.fi account
  password, and confirm that Home Assistant can reach `api.aprs.fi`.
- **A new release is not offered in HACS:** open the repository menu, choose
  **Update information**, and check again after the GitHub release is published.
- **Support data is needed:** download diagnostics from the APRS Monitor config
  entry menu. Secrets, callsigns, coordinates, and comments are excluded.

For a production upgrade or rollback, also read the
[German backup and rollback guide](upgrade.de.md).
