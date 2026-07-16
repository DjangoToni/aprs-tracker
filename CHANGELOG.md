# Changelog

## 1.0.0 - 2026-07-16

- Declared the config schema, station and hub unique IDs, migration behavior, and
  privacy rules stable for the 1.x release line.
- Added complete German user documentation and a production release checklist.
- Added structured GitHub bug and feature issue forms with mandatory privacy
  confirmation and a private security-reporting link.
- Added recursive source, English, and German translation-contract validation.
- Added Home Assistant YAML validation for public support metadata.
- Completed final runtime, packaging, migration, blueprint, diagnostics, and
  deterministic-archive audits without changing existing entity identities.

## 0.10.0 - 2026-07-16

- Added config-entry schema 2 and automatic migration of legacy global settings into
  complete per-station profiles.
- Added defensive normalization for malformed callsigns, thresholds, intervals, and
  profile containers while preserving unknown future option keys.
- Added explicit HTTP 429 rate-limit classification with parsed `Retry-After` delays.
- Added a ZIP smoke test that compiles every packaged Python module.
- Documented the stable 15-per-station and five-hub entity unique-ID contract.
- Added a German backup, manual upgrade, rollback, and installation-repair guide.
- Added migration, damaged-option, rate-limit, legacy-runtime, package, and entity
  contract coverage.

## 0.9.0 - 2026-07-15

- Added a second, collapsible options step with one profile section per callsign.
- Added configurable station display names without changing callsign identifiers,
  tracker identities, or existing entity unique IDs.
- Added individual maximum-position-age, near-home-radius, and movement-speed
  thresholds for every station.
- Existing installations without profiles automatically inherit their current global
  defaults and require no migration.
- Removed profiles are discarded when their callsign is removed.
- Redacts the complete callsign-indexed profile block from diagnostics while exposing
  only an aggregate profile count.
- Added profile normalization, options-flow, device-name, threshold, privacy, legacy,
  and Home Assistant runtime coverage.

## 0.8.0 - 2026-07-15

- Added configurable Home Assistant automation blueprints for station activity and
  aprs.fi API outage/recovery events.
- Blueprint actions are user-defined and work with mobile notifications, Home
  Assistant Cloud, Telegram, persistent notifications, or arbitrary actions.
- Added a manual dashboard example with APRS map icons, 24-hour Recorder tracks,
  station telemetry, and central control entities.
- Added a deterministic extras archive designed for extraction directly into the
  Home Assistant `/config` directory.
- Added Home Assistant blueprint-schema validation, dashboard structure checks,
  extras packaging checks, and reproducibility coverage.

## 0.7.0 - 2026-07-15

- Added a central APRS Monitor hub device alongside the individual station devices.
- Added an always-visible aprs.fi connectivity binary sensor and API outage/recovery
  event entity.
- Added an aggregate translated status sensor with current, stale, and missing station
  counts.
- Added a persistent last-successful-update timestamp and a manual update button.
- Protects the hub identifier from callsign device cleanup.
- Added API failure, recovery, manual refresh, aggregate status, cleanup, and
  three-station runtime coverage.

## 0.6.0 - 2026-07-15

- Added one translated station-activity event entity for every callsign.
- Emits events when movement starts or stops and when the configured home radius
  is entered or left.
- Emits separate events for a position becoming current, stale, or missing.
- Establishes an initial baseline without emitting startup or reload events.
- Ignores coordinator failures so network outages are not reported as real station
  transitions.
- Adds useful event context without coordinates, including speed, distance, position
  age, and the relevant configured threshold.
- Added transition, failure-recovery, multi-station, translation, and Home Assistant
  runtime coverage.

## 0.5.0 - 2026-07-15

- Added translated station-status, position-age, course-direction, and APRS-symbol
  sensors for every callsign.
- Added dynamic APRS station-type icons to device trackers for Home Assistant maps.
- Maps common cars, bicycles, aircraft, balloons, ships, weather stations, emergency
  vehicles, radio sites, and other station types to MDI icons.
- Preserves the raw APRS symbol and comment as tracker attributes while keeping them
  out of privacy-preserving diagnostics.
- Uses a standard map marker for missing or unknown APRS symbol codes.
- Added unit, translation, missing-position, stale-position, and Home Assistant runtime
  coverage for the complete station-status package.

## 0.4.0 - 2026-07-15

- Added a configurable movement threshold from 0.5 to 50 km/h.
- Added a translated moving binary sensor for every callsign.
- Treats missing speed, stale positions, and API failures as unavailable.
- Exposes the non-sensitive threshold in diagnostics and system health.
- Added validation, options-flow, icon, transition, and missing-data coverage.

## 0.3.0 - 2026-07-15

- Added a configurable near-home radius from 1 to 1000 kilometers.
- Added a translated near-home binary sensor for every callsign.
- Marks proximity unavailable when a position is missing, stale, or the API fails.
- Exposes the non-sensitive radius in diagnostics and system health.
- Added validation, options-flow, icon, and Home Assistant runtime coverage.

## 0.2.0 - 2026-07-15

- Added a distance-from-home sensor for every callsign.
- Added a bearing-from-home sensor with a normalized 0–360° value.
- Uses local great-circle calculations without additional aprs.fi requests.
- Keeps derived home-location values out of diagnostics and system health.
- Added geographic unit and Home Assistant runtime coverage.

## 0.1.0 - 2026-07-15

- Added deterministic HACS and direct-folder release archives with SHA-256 sums.
- Added a tag-driven GitHub release workflow gated by lint and runtime tests.
- Added synchronized version checks across the manifest, package metadata, and constants.
- Added explicit integration type, issue tracker, and single-entry metadata.
- Updated the minimum supported Home Assistant version to 2026.7.0.
- Added local APRS Monitor brand icons for Home Assistant and HACS.

## 0.0.16 - 2026-07-15

- Added Home Assistant runtime tests for config-entry setup and unloading.
- Verifies tracker, sensor, and binary-sensor creation with mocked aprs.fi data.
- Verifies coordinator failure and recovery behavior.
- Added config-flow coverage for success, API errors, duplicates, reauthentication,
  and options.
- Pins CI runtime testing to Home Assistant 2026.7.2 on Python 3.14.
- Corrected the manifest IoT class to `cloud_polling`.

## 0.0.15

- Added translated Home Assistant system-health information.
- Reports aprs.fi reachability and non-sensitive aggregate runtime state.
- Tracks the timestamp of the last successful aprs.fi update.
- Explicitly associates the coordinator with its config entry.
- Uses DataUpdateCoordinator's one-time failure and recovery transition logging.

## 0.0.14

- Removes devices and entities for callsigns deleted through the options flow.
- Protects active callsigns and devices owned by other integrations.
- Enables manual device removal only for callsigns no longer configured.

## 0.0.13

- Added a position-current binary sensor for every callsign.
- Distinguishes missing or stale station data from coordinator/API failures.
- Added translated entity names and state-dependent marker icons.

## 0.0.12

- Added downloadable config-entry diagnostics.
- Redacts API keys and callsigns.
- Excludes coordinates, comments, and exact reception timestamps.
- Includes anonymized update, freshness, and field-presence information.

## 0.0.11

- Added a translated reauthentication flow for rejected aprs.fi API keys.
- Replacement keys are validated before the existing config entry is updated.
- Callsigns, options, devices, and entity IDs remain unchanged during reauth.

## 0.0.10

- Added a configurable maximum position age from 15 to 1440 minutes.
- Stale trackers and movement sensors are marked unavailable.
- The last-seen sensor remains available and exposes freshness diagnostics.

## 0.0.9

- Added a translated Home Assistant options flow.
- Callsigns can be changed without removing the integration.
- The shared update interval can be configured from 5 to 60 minutes.
- Saving options automatically reloads the integration once.

## 0.0.8

- Replaced the nonexistent `UnitOfAngle` import with Home Assistant's supported
  `DEGREE` constant so the sensor platform can load.

## 0.0.7

- Preloads the device-tracker and sensor platforms at module level so their
  imports run safely in Home Assistant's import executor.

## 0.0.6

- Replaced the deprecated device-tracker `TrackerEntity` compatibility import.

## 0.0.5

- Added separate speed, course, altitude, and last-seen sensors.
- Added German and English entity names.
- Sensors share the existing coordinator and station device.

## 0.0.4

- Added 15-minute batched aprs.fi location updates.
- Added one GPS device tracker per configured callsign.
- Exposes course, speed, altitude, symbol, comment, and last-seen metadata.

## 0.0.3

- Added a live HTTPS authentication check against aprs.fi.
- Distinguishes rejected API keys from temporary connection failures.
- Still creates no devices or entities.

## 0.0.2

- Added a masked aprs.fi API-key field.
- Added local validation for 1 to 20 exact callsigns.
- Stores the validated configuration without performing network requests.

## 0.0.1

- Complete bootstrap restart.
- Minimal config flow without API or entity dependencies.
- Cross-platform package structure tests.
