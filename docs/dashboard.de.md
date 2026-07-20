# APRS-Monitor-Dashboard einrichten

Diese Anleitung beschreibt die mit APRS Monitor ausgelieferte Kartenkomponente
`custom:aprs-monitor-map-card` und das vollständige Beispiel-Dashboard. Die Karte
zeigt originale APRS-Symbole, Telemetrie im Hovertext, farbige Recorder-Verläufe
und den Aktualitätsstatus jeder Station.

## Voraussetzungen

- APRS Monitor 1.4.0 oder neuer ist installiert und eingerichtet.
- Mindestens ein APRS-Geräte-Tracker ist in Home Assistant vorhanden.
- Für Streckenverläufe zeichnet der Home-Assistant-Recorder den Geräte-Tracker auf.
- Für die Verwaltung von Dashboard-Ressourcen muss gegebenenfalls im
  Benutzerprofil der **Erweiterte Modus** aktiviert werden.

Die tatsächlichen Entity-IDs findest du unter **Einstellungen > Geräte & Dienste
> APRS Monitor** oder in **Entwicklerwerkzeuge > Zustände**. Verwende immer die
IDs deiner eigenen Installation.

## 1. JavaScript-Ressource registrieren

Öffne **Einstellungen > Dashboards > Ressourcen**, wähle **Ressource hinzufügen**
und trage Folgendes ein:

```text
/api/aprs_monitor/frontend/aprs-monitor-map-card.js?v=1.4.0
```

Der Ressourcentyp ist **JavaScript-Modul**. Registriere die URL nur einmal. Lade
danach die Home-Assistant-Seite vollständig neu. Bei einer späteren Version wird
die Versionsnummer hinter `?v=` angepasst, damit der Browser die neue Datei lädt.

## 2. Minimale Karte für eine Station

Füge einem Dashboard eine **Manuelle Karte** hinzu und verwende:

```yaml
type: custom:aprs-monitor-map-card
title: APRS Live
entities:
  - device_tracker.DEIN_RUFZEICHEN
```

Diese kompatible Grundkonfiguration zeigt die aktuelle Position ohne Verlauf.
Ein Klick auf das Symbol öffnet die normalen Home-Assistant-Entitätsdetails.

## 3. Empfohlene Live-Karte mit mehreren Stationen

```yaml
type: custom:aprs-monitor-map-card
title: APRS Live-Telemetrie
height: 500
auto_fit: true
scroll_wheel_zoom: true
hours_to_show: 24
history_refresh_minutes: 15
max_history_points: 2000
show_status: true
track_weight: 4
track_opacity: 0.7
entities:
  - entity: device_tracker.DEIN_ERSTES_RUFZEICHEN
    color: "#039be5"
  - entity: device_tracker.DEIN_ZWEITES_RUFZEICHEN
    color: "#e53935"
  - entity: device_tracker.DEIN_DRITTES_RUFZEICHEN
    color: "#43a047"
```

Beim Überfahren eines Symbols erscheinen Rufzeichen, Geschwindigkeit, Richtung,
Höhe, Koordinaten, letztes Signal und Status. Die Ringe bedeuten:

- Grün: Position aktuell
- Orange: Position veraltet
- Grau: Station nicht verfügbar; falls vorhanden wird die letzte Recorder-Position angezeigt

Die Karte liest Zustände und Verlauf ausschließlich aus Home Assistant. Sie führt
keine zusätzliche aprs.fi-Abfrage aus.

## Kartenoptionen

| Option | Standard | Gültiger Bereich und Wirkung |
| --- | --- | --- |
| `entities` | erforderlich | Liste von Tracker-IDs oder Objekten mit `entity` und optionaler `color` |
| `title` | `APRS Monitor` | Überschrift; eine leere Zeichenfolge blendet sie aus |
| `height` | `500` | Kartenhöhe in Pixeln; mindestens 240 Pixel werden dargestellt |
| `auto_fit` | `true` | Passt den Ausschnitt beim ersten Laden an Marker und Verläufe an |
| `scroll_wheel_zoom` | `false` | Aktiviert Zoomen mit dem Mausrad um den Mauszeiger |
| `zoom` | `8` | Anfangszoom; bei einer einzelnen Station verwendet Auto-Fit standardmäßig 13 |
| `max_zoom` | `16` | Maximaler Zoom beim automatischen Einpassen |
| `hours_to_show` | `0` | `0` deaktiviert Verlauf; `1` bis `168` laden Recorder-Verlauf |
| `history_refresh_minutes` | `15` | Aktualisierung des Verlaufs, begrenzt auf 5 bis 60 Minuten |
| `max_history_points` | `2000` | Maximale Punkte je Station, begrenzt auf 100 bis 5000 |
| `show_status` | `true` | Zeigt die grünen, orangen und grauen Statusringe |
| `track_weight` | `4` | Linienstärke, begrenzt auf 1 bis 12 |
| `track_opacity` | `0.7` | Deckkraft des Verlaufs, begrenzt auf 0.1 bis 1.0 |
| `tile_url` | OpenStreetMap | Optionale Leaflet-Kachel-URL mit `{z}`, `{x}` und `{y}` |
| `attribution` | OpenStreetMap | Erforderlicher Quellenhinweis eines eigenen Kachelanbieters |

Einfache Entity-Listen erhalten automatisch unterschiedliche Farben:

```yaml
entities:
  - device_tracker.erste_station
  - device_tracker.zweite_station
```

Für feste Farben wird die Objektform verwendet:

```yaml
entities:
  - entity: device_tracker.erste_station
    color: "#1565c0"
```

## Vollständiges Beispiel-Dashboard importieren

Die vollständige Vorlage liegt unter
[`examples/dashboard.yaml`](../examples/dashboard.yaml). Das Extras-Archiv eines
Releases installiert sie als `/config/aprs_monitor_examples/dashboard.yaml`.

### Import über die Benutzeroberfläche

1. Öffne **Einstellungen > Dashboards > Dashboard hinzufügen** und erstelle ein
   leeres Dashboard.
2. Öffne das neue Dashboard und wähle **Dashboard bearbeiten**.
3. Öffne das Drei-Punkte-Menü und danach den **Rohkonfigurationseditor**.
4. Ersetze den vorhandenen Inhalt durch den gesamten Inhalt von
   `examples/dashboard.yaml`.
5. Ersetze vor dem Speichern alle Werte mit `REPLACE_WITH_...` durch reale
   Entity-IDs aus deiner Installation.

### Import als YAML-Dashboard

Wenn du Dashboards in `configuration.yaml` verwaltest, kann die aus dem
Extras-Archiv installierte Datei direkt eingebunden werden:

```yaml
lovelace:
  mode: storage
  dashboards:
    aprs-monitor:
      mode: yaml
      title: APRS Monitor
      icon: mdi:radio-tower
      show_in_sidebar: true
      filename: aprs_monitor_examples/dashboard.yaml
```

Prüfe danach die Konfiguration und starte Home Assistant neu. Der Schlüssel
`aprs-monitor` muss einen Bindestrich enthalten und innerhalb deiner Dashboards
eindeutig sein.

## Platzhalter der vollständigen Vorlage

| Platzhalter | Benötigte Entität |
| --- | --- |
| `REPLACE_WITH_FIRST_TRACKER` usw. | APRS-`device_tracker` der Station |
| `REPLACE_WITH_API_CONNECTED` | zentrale API-Verbindungs-Binärentität |
| `REPLACE_WITH_OVERALL_STATUS` | zentraler Gesamtstatus-Sensor |
| `REPLACE_WITH_LAST_SUCCESSFUL_UPDATE` | Sensor der letzten erfolgreichen Aktualisierung |
| `REPLACE_WITH_REFRESH` | zentrale Schaltfläche **Jetzt aktualisieren** |
| `REPLACE_WITH_STATION_STATUS` | Statussensor einer Station |
| `REPLACE_WITH_SPEED`, `ALTITUDE` usw. | jeweilige Telemetrie-Sensoren der Station |
| `REPLACE_WITH_*_STATION_ACTIVITY` | Stationsereignis-Entität |
| `REPLACE_WITH_*_ZONE` | gewünschte Home-Assistant-Zone |

Nicht benötigte Stationen, Zonen, Karten oder Ansichten können vollständig aus
der YAML-Datei entfernt werden.

## Home-Assistant-Standardkarte verwenden

Für eine Installation ohne benutzerdefinierte Karte kann `map_details` als
Beschriftung der Standardkarte verwendet werden:

```yaml
type: map
title: APRS-Telemetrie
auto_fit: true
cluster: false
entities:
  - entity: device_tracker.DEIN_RUFZEICHEN
    label_mode: attribute
    attribute: map_details
  - entity: zone.home
    focus: false
```

Ein einfacher 24-Stunden-Verlauf mit der Standardkarte lautet:

```yaml
type: map
title: APRS-Verlauf – 24 Stunden
hours_to_show: 24
auto_fit: true
cluster: false
entities:
  - entity: device_tracker.DEIN_RUFZEICHEN
    label_mode: icon
```

Die Standardkarte unterstützt nicht den mehrzeiligen Telemetrie-Hovertext und
die pro Station konfigurierbaren Verlaufslinien der APRS-Monitor-Karte.

## Fehlerbehebung

- **„Custom element doesn't exist“:** Ressourcen-URL und Typ prüfen, Home Assistant
  neu starten und Browser-Cache vollständig aktualisieren.
- **Alte Karte trotz Update:** Versionsnummer hinter `?v=` erhöhen und die Seite
  erneut vollständig laden.
- **Keine Verlaufslinie:** `hours_to_show` muss größer als null sein und Recorder
  muss Zustände des Geräte-Trackers enthalten. Zwei unterschiedliche Positionen
  sind für eine Linie erforderlich.
- **Karte fängt das Scrollen ab:** `scroll_wheel_zoom: false` setzen oder die
  Option entfernen.
- **Graues Symbol:** Der Tracker ist nicht verfügbar. Die letzte bekannte Position
  wird nur angezeigt, wenn Recorder-Verlauf vorhanden ist.
- **Keine APRS-Grafik:** Unter **APRS Monitor > Konfigurieren** den
  Kartenmarkierungsstil auf **Original APRS-Symbolgrafik** stellen und prüfen, ob
  die Station ein APRS-Symbol meldet.
- **Leere Kartenfläche:** Die Standard-Kacheln benötigen Zugriff auf
  `tile.openstreetmap.org`; alternativ einen erreichbaren Kacheldienst konfigurieren.
