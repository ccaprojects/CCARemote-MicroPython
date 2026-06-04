# Changelog

Alle wesentlichen Änderungen werden in dieser Datei dokumentiert.
Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [1.2.1] – 2026-06-04

### Neu
- **Persistente Zustandsspeicherung:** Variablenwerte (`receive()`, `receive_color()`) werden beim Disconnect automatisch in `/cca_state.json` gespeichert und nach einem Neustart oder Stromverlust wiederhergestellt. Mit `persist=False` in `create_remote()` deaktivierbar.
- **Vollständiger Resync beim Connect:** Beim Verbindungsaufbau überträgt der Controller alle registrierten Variablenwerte an die App – nicht nur Variablen mit `resync=True`.

### Behoben
- **BLE:** Eigene `_resync_display()`-Implementierung in `ble.py` sendete nur `_display_values` und unterdrückte damit den Lazy-Load aus der persistenten Datei sowie die Übertragung aller Steuerwerte.
- **WiFi:** Der Connect-Handler iterierte `_display_values` direkt, anstatt `_resync_display()` aufzurufen – Steuerwerte und persistierter Zustand wurden nicht zur App übertragen.

---

## [1.2.0] – 2026-05-27

### Neu
- Profil-Konfiguration: `set_profile()` – Profil-String wird beim Verbindungsaufbau an die App übertragen
- `resync=True` Parameter in `receive()` und `receive_color()` – Wert bei Reconnect zur App senden
- `send_always()` – Wert auch bei Gleichheit senden (für Chart-Elemente)
- Authentifizierung per Passwort (BLE und WiFi)
- Watchdog-Mechanismus: Variable automatisch auf 0 setzen bei Verbindungsabbruch
- `debug()` – Debug-Level zur Laufzeit ändern
- Mode Selector: Index- und Label-Modus

---

## [1.1.0] – 2026-05-21

### Neu
- Connection Manager: erlaubt das Speichern verschiedener Verbindungsprofile
- Color Picker hinzugefügt
- Watchdog Funktion: Wenn Joystick in definierter Zeitspanne keinen Wert sendet wird automatisch für X- und y-Achse der Wert 0 gesetzt

### Behoben
- WiFi Übertragungsgeschwindigkeit verbessert
- vereifachte Library Konfiguration
- Protokoll Versionierung hinzugefügt

---

## [1.0.0] – 2025-xx-xx

### Erstveröffentlichung
- BLE-Verbindung (Raspberry Pi Pico 2 W)
- WiFi-Verbindung (Access Point + TCP)
- `receive()` für `bool`, `int`, `float`, `str`
- `receive_color()` / `get_color()` für RGB-Color-Picker
- `send()` für Display-Elemente
- `watchdog()` für Joystick-Achsen
- `on_command()` – Callback-Registrierung
- `create_remote()` Factory-Funktion
