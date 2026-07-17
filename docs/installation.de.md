# APRS Monitor installieren

Diese Anleitung beschreibt die Installation mit HACS, die manuelle Installation,
die Ersteinrichtung, Aktualisierungen und die häufigsten Installationsprobleme.

## Voraussetzungen

- Home Assistant 2026.7.0 oder neuer
- HACS 2.0 oder neuer für die empfohlene Installationsart
- ein aprs.fi-API-Key von <https://aprs.fi/account/>
- mindestens ein exaktes APRS-Rufzeichen

## Empfohlen: Installation mit HACS

1. Öffne **HACS** in der Seitenleiste von Home Assistant.
2. Öffne oben rechts das Drei-Punkte-Menü und wähle
   **Benutzerdefinierte Repositories** beziehungsweise **Custom repositories**.
3. Trage `https://github.com/DjangoToni/aprs-tracker` als Repository-URL ein.
4. Wähle als Typ **Integration** und anschließend **Hinzufügen**.
5. Suche nach **APRS Monitor**, öffne den Eintrag und wähle **Herunterladen**.
6. Wähle das neueste Release und bestätige den Download.
7. Starte Home Assistant neu, sobald HACS dazu auffordert.
8. Öffne **Einstellungen > Geräte & Dienste**, wähle
   **Integration hinzufügen** und suche nach **APRS Monitor**.
9. Trage den aprs.fi-API-Key und die zu überwachenden Rufzeichen ein.

HACS installiert das feste Release-Paket `aprs_monitor.zip`. Die Direct-Folder-
und Extras-Pakete gehören nicht in den HACS-Downloaddialog.

## Manuelle Installation

1. Lade `aprs_monitor-<version>-direct-folder.zip` vom passenden GitHub-Release
   herunter.
2. Erstelle `/config/custom_components`, falls der Ordner noch nicht existiert.
3. Entpacke das Archiv nach `/config/custom_components`.
4. Prüfe, ob exakt diese Datei vorhanden ist:
   `/config/custom_components/aprs_monitor/manifest.json`.
5. Starte Home Assistant vollständig neu.
6. Öffne **Einstellungen > Geräte & Dienste > Integration hinzufügen** und suche
   nach **APRS Monitor**.

Vermeide einen doppelten Ordner wie
`/config/custom_components/aprs_monitor/aprs_monitor`. Mit dieser Struktur kann
Home Assistant die Integration nicht finden.

## Optionale Dashboards und Blueprints

1. Lade `aprs_monitor-<version>-extras.zip` vom selben Release herunter.
2. Entpacke es direkt in das Home-Assistant-Verzeichnis `/config`.
3. Ersetze in `/config/aprs_monitor_examples/dashboard.yaml` alle Platzhalter
   `REPLACE_WITH_...` durch Entity-IDs aus deiner Home-Assistant-Installation.
4. Füge die gewünschten Karten als manuelle YAML-Karten in ein Dashboard ein.
5. Lade die Automationen neu oder starte Home Assistant neu, bevor du die
   mitgelieferten Blueprints verwendest.

Das Extras-Paket ist optional. APRS Monitor funktioniert auch ohne dieses Paket.

## Aktualisieren

Bei einer HACS-Installation öffnest du APRS Monitor in HACS, installierst das
angebotene Update und startest Home Assistant neu. Bei einer manuellen
Installation ersetzt du nur `/config/custom_components/aprs_monitor` durch den
Ordner aus dem neuen Direct-Folder-Paket und startest Home Assistant neu.

Lösche bei einem Update nicht den APRS-Monitor-Konfigurationseintrag. API-Key,
Rufzeichen, Profile, Geräte, Entity-IDs, Automationen und Recorder-Verlauf bleiben
bei einem normalen Update erhalten.

## Fehlerbehebung

- **APRS Monitor fehlt unter „Integration hinzufügen“:** Prüfe den exakten
  Manifest-Pfad, starte Home Assistant neu und aktualisiere danach die Browserseite.
- **Das Gerät ist vorhanden, aber Entitäten fehlen:** Prüfe, ob wirklich alle
  Dateien aus dem Komponentenarchiv kopiert wurden, insbesondere Plattformdateien
  wie `sensor.py` und `device_tracker.py`.
- **Die Anmeldung schlägt fehl:** Verwende den aprs.fi-API-Key und nicht das
  aprs.fi-Kontopasswort. Home Assistant muss `api.aprs.fi` erreichen können.
- **HACS bietet ein neues Release nicht an:** Öffne das Repository-Menü, wähle
  **Informationen aktualisieren** beziehungsweise **Update information** und prüfe
  erneut, nachdem das GitHub-Release veröffentlicht wurde.
- **Für eine Fehlermeldung werden Systemdaten benötigt:** Lade die Diagnosedatei
  über das Menü des APRS-Monitor-Konfigurationseintrags herunter. Geheimnisse,
  Rufzeichen, Koordinaten und Kommentare werden nicht ausgegeben.

Für produktive Aktualisierungen und Wiederherstellungen lies zusätzlich die
[Anleitung zu Sicherung und Rollback](upgrade.de.md).

