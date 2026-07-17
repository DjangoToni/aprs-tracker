# APRS Monitor 1.3.0 für Home Assistant

Installationsanleitungen: [Deutsch](installation.de.md) ·
[English](installation.md)

APRS Monitor verfolgt bis zu 20 APRS-Rufzeichen über die aprs.fi-API. Die
Integration ist ausschließlich lesend und sendet weder APRS-Pakete noch
Nachrichten.

## Voraussetzungen

- Home Assistant 2026.7.0 oder neuer
- persönlicher aprs.fi-API-Key
- mindestens ein konkretes Rufzeichen ohne Platzhalter

## Installation

Mit HACS wird das Repository `https://github.com/DjangoToni/aprs-tracker` als
benutzerdefiniertes Integrations-Repository hinzugefügt. Nach der Installation und
einem Neustart wird **APRS Monitor** unter **Einstellungen > Geräte & Dienste >
Integration hinzufügen** eingerichtet.

Bei manueller Installation wird das Direct-Folder-Paket nach
`/config/custom_components` entpackt. Der endgültige Pfad muss
`/config/custom_components/aprs_monitor/manifest.json` lauten.

## Geräte und Entitäten

Für jedes Rufzeichen entstehen ein GPS-Geräte-Tracker und 14 zusätzliche
Entitäten für Geschwindigkeit, Kurs, Kursrichtung, Höhe, Entfernung, Peilung,
Zeitstempel, Positionsalter, APRS-Symbol, Status, Aktualität, Heimnähe, Bewegung
und Stationsereignisse. Das zentrale Gerät **APRS Monitor** enthält fünf Entitäten
für API-Verbindung, Gesamtstatus, letzten erfolgreichen Abruf,
Verbindungsereignisse und manuelle Aktualisierung.

## Konfiguration

Der erste Konfigurationsschritt enthält Rufzeichen, Abrufintervall und globale
Vorgaben. Im zweiten Schritt besitzt jedes Rufzeichen ein einklappbares Profil mit
Anzeigename, maximalem Positionsalter, Heimradius und Bewegungsschwelle. Der
globale Kartenmarkierungsstil wechselt zwischen Home-Assistant-Stationssymbolen
und originalen APRS-Symbolgrafiken.
Anzeigenamen verändern keine Geräteidentitäten, Entity-IDs oder Verlaufsdaten.

## Karte und Automationen

Bekannte APRS-Symbole werden in passende Home-Assistant-Kartensymbole übersetzt.
Version 1.3 enthält zusätzlich die originalen APRS-Piktogramme aus dem offenen
aprs.fi-Symbolsatz. Home Assistant schneidet das richtige Bild aus der primären
oder alternativen Symboltabelle aus und ergänzt bei Bedarf ein Overlay. Die
Grafiken werden ausschließlich lokal bereitgestellt und enthalten weder
Rufzeichen noch Koordinaten. Die Auswahl befindet sich unter **APRS Monitor >
Konfigurieren > Kartenmarkierungsstil**. Quellen und Lizenzhinweise sind im
Integrationspaket enthalten.
Jeder aktuelle Tracker besitzt zusätzlich das Attribut `map_label`. Es verbindet
Anzeigename, Geschwindigkeit, achtteilige Kursrichtung und Höhe zu einer kompakten
Kartenbeschriftung; fehlende APRS-Werte werden ausgelassen. `map_details` ergänzt
Rufzeichen, Kurs in Grad und Koordinaten. Da die Home-Assistant-Standardkarte
keine frei konfigurierbaren Hover-Tooltips bietet, enthält Version 1.3 zusätzlich
die optionale `custom:aprs-monitor-map-card`. Sie zeigt das originale APRS-Symbol
und beim Überfahren Geschwindigkeit, Richtung, Höhe, Koordinaten und Zeitpunkt
des letzten Signals. Die Karte verwendet vorhandene Entitätszustände und erzeugt
keine zusätzlichen aprs.fi-Abfragen. Das optionale
Extras-Paket enthält drei Automations-Blueprints und ein Dashboard mit getrennten
Zonen-, Symbol-, Telemetrie- und 24-Stunden-Verlaufsansichten. Das Extras-Paket wird direkt
nach `/config` entpackt.

Die Kartenressource wird einmalig unter **Einstellungen > Dashboards > Ressourcen**
als JavaScript-Modul eingetragen:

```text
/api/aprs_monitor/frontend/aprs-monitor-map-card.js?v=1.3.0
```

Leaflet 1.9.4 wird mit der Integration lokal unter der BSD-2-Clause-Lizenz
ausgeliefert; es wird kein externes JavaScript-CDN verwendet. Die standardmäßig
verwendeten OpenStreetMap-Kacheln benötigen weiterhin Netzwerkzugriff.

Version 1.2 erkennt zusätzlich aktive Home-Assistant-Zonen. Die Stationsaktivität
meldet `entered_zone` und `left_zone` mit Zonenname und Entity-ID, jedoch ohne
Koordinaten. Passive Zonen sowie fehlende oder veraltete Positionen lösen keine
Zonenwechsel aus. Eine eigene Blueprint führt getrennte Aktionen bei Ankunft und
Abfahrt in einer ausgewählten Zone aus.

## Zustände und Fehler

Fehlende optionale APRS-Felder machen nur die jeweilige Entität nicht verfügbar.
Veraltete Positionen werden nicht als aktuelle Abwesenheit oder Stillstand
interpretiert. API-Ausfälle machen Stationsentitäten nicht verfügbar, während das
Kontrollzentrum den Fehler und den letzten erfolgreichen Abruf weiterhin zeigt.
Ein abgelehnter API-Key startet die Home-Assistant-Reauthentifizierung.

## Datenschutz

Diagnosen enthalten keine API-Keys, Rufzeichen, Anzeigenamen, Koordinaten,
Kommentare oder exakten Empfangszeitpunkte. Vor öffentlichen Fehlerberichten sind
auch Protokolle manuell auf persönliche APRS-Daten zu prüfen.

## Upgrade und Wiederherstellung

Vor Produktions-Upgrades sollte eine Home-Assistant-Sicherung erstellt werden.
Die ausführliche Anleitung steht in [upgrade.de.md](upgrade.de.md). Der stabile
Entity-Vertrag ist in [entity-contract.md](entity-contract.md) dokumentiert.
