# APRS Monitor 1.1.0 für Home Assistant

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
Anzeigename, maximalem Positionsalter, Heimradius und Bewegungsschwelle.
Anzeigenamen verändern keine Geräteidentitäten, Entity-IDs oder Verlaufsdaten.

## Karte und Automationen

Bekannte APRS-Symbole werden in passende Home-Assistant-Kartensymbole übersetzt.
Jeder aktuelle Tracker besitzt zusätzlich das Attribut `map_label`. Es verbindet
Anzeigename, Geschwindigkeit, achtteilige Kursrichtung und Höhe zu einer kompakten
Kartenbeschriftung; fehlende APRS-Werte werden ausgelassen. Das optionale
Extras-Paket enthält zwei Automations-Blueprints und ein Dashboard mit getrennten
Symbol-, Telemetrie- und 24-Stunden-Verlaufsansichten. Das Extras-Paket wird direkt
nach `/config` entpackt.

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
