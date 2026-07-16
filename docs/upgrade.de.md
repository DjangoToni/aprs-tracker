# Upgrade, Sicherung und Wiederherstellung

## Vor einem Upgrade

1. Erstelle unter **Einstellungen > System > Sicherungen** eine Home-Assistant-Sicherung.
2. Sichere optional `/config/custom_components/aprs_monitor` separat.
3. Notiere die installierte APRS-Monitor-Version aus den Integrationsdiagnosen.

## Manuelles Upgrade

1. Lösche nur `/config/custom_components/aprs_monitor`.
2. Entpacke das Direct-Folder-Paket nach `/config/custom_components`.
3. Prüfe `/config/custom_components/aprs_monitor/manifest.json`.
4. Starte Home Assistant vollständig neu.
5. Kontrolliere das zentrale Gerät und mindestens eine Station.

Der Konfigurationseintrag darf nicht gelöscht werden. API-Key, Rufzeichen, Profile,
Entity-Registry, Automationen und Recorder-Verlauf bleiben dadurch erhalten.

## Rollback

1. Beende Home Assistant oder stoppe die Integration durch Herunterfahren.
2. Ersetze den Komponentenordner durch das zuvor gesicherte Release.
3. Starte Home Assistant neu.
4. Falls eine ältere Version das migrierte Optionsschema nicht lesen kann, stelle die
   vollständige Home-Assistant-Sicherung wieder her.

## Fehlerhafte Dateien

Wenn nur das gespeicherte Gerät, aber keine Entitäten sichtbar sind, kontrolliere,
dass kein doppelter Ordner
`/config/custom_components/aprs_monitor/aprs_monitor` entstanden ist.
