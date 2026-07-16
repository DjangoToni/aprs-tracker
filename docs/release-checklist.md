# Release checklist

## Code and compatibility

- [ ] Manifest, constants, package metadata, README, and changelog use one version.
- [ ] Ruff and the complete Home Assistant 2026.7.2 runtime suite pass.
- [ ] Config-entry migration from schema 1 succeeds and future schemas are rejected.
- [ ] Stable station and hub unique-ID contracts remain unchanged.
- [ ] German, English, and source translation trees have identical keys.

## Privacy and behavior

- [ ] Diagnostics exclude credentials, callsigns, profiles, coordinates, comments,
      and exact packet timestamps.
- [ ] API failure, authentication failure, rate limiting, stale data, and recovery
      remain distinguishable.
- [ ] Startup and reload do not emit false station events.

## Packaging

- [ ] HACS, direct-folder, and extras archives are deterministic.
- [ ] Every packaged Python module compiles.
- [ ] Archive roots match their documented extraction directory.
- [ ] SHA-256 sums cover all published ZIP files.
- [ ] Upgrade and rollback instructions match the final archives.
