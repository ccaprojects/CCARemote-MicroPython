# CCARemote – MicroPython Bibliothek

Flexible Steuerung von Mikrocontrollern über Bluetooth Low Energy (BLE) oder WLAN (WiFi). Die erforderliche App **CCA Remote** ist für Android und iOS kostenlos verfügbar.
Dieses Projekt wurde von der HTL Anichstraße (Abteilung Wirtschaftsingenieure – Betriebsinformatik) entwickelt.

Unterstützte Protokolle:
- **Bluetooth Low Energy (BLE)**
- **WiFi (WLAN-Hotspot + TCP)**

Unterstützte Hardware:
- **Raspberry Pi Pico 2W** und **ESP32** – natives BLE, WiFi

Dieses Dokument beschreibt die Installation der **CCARemote MicroPython-Bibliothek**
für den Raspberry Pi Pico 2 W in **Thonny** und **VS Code**.

> Die Arduino-Bibliothek für **ESP32, ESP8266 und Arduino** steht unter
> [github.com/ccaprojects/CCARemote-Arduino](https://github.com/ccaprojects/CCARemote-Arduino) zur Verfügung.

---

## Voraussetzungen

| Anforderung | Details |
|---|---|
| Hardware | Raspberry Pi **Pico 2 W** (mit WLAN/BLE-Chip CYW43) |
| Firmware | MicroPython **≥ 1.25** für Pico 2 W |
| Thonny | Version 4.x oder neuer |
| VS Code | mit Extension **MicroPico** oder **RT-Thread MicroPython** |

### MicroPython-Firmware flashen

1. [micropython.org/download/RPI_PICO2_W](https://micropython.org/download/RPI_PICO2_W/) aufrufen
2. Die neueste `.uf2`-Datei herunterladen
3. **BOOTSEL**-Taste am Pico gedrückt halten → USB-Kabel einstecken → Taste loslassen
4. Pico erscheint als USB-Laufwerk → `.uf2`-Datei draufziehen → Pico startet automatisch

---

## Installation der Bibliothek

### Option A – ZIP-Datei via Thonny *(empfohlen)*

Die einfachste Methode: ZIP von GitHub herunterladen und direkt über den Thonny-Paketmanager installieren – kein manuelles Entpacken nötig.

**Schritt 1 – ZIP herunterladen**

1. Auf [github.com/ccaprojects/CCARemote-MicroPython](https://github.com/ccaprojects/CCARemote-MicroPython) gehen
2. **Releases** → neueste Version → `CCARemote-MicroPython-vX.X.X.zip` herunterladen

**Schritt 2 – In Thonny installieren**

1. Thonny starten und den Pico 2 W per USB verbinden
2. Sicherstellen dass unten rechts **MicroPython (Raspberry Pi Pico)** als Interpreter ausgewählt ist
3. Menü öffnen:
   - DE: **Werkzeuge → Pakete verwalten**
   - EN: **Tools → Manage packages**
4. Im Paketmanager-Dialog unten auf:
   - DE: **Lokale Datei installieren**
   - EN: **Install from local file**
5. Die heruntergeladene `.zip`-Datei auswählen → **OK**

Thonny installiert die Bibliothek automatisch unter `/lib/CCARemote/` auf dem Pico.

### Option B – Manuell via Thonny-Dateimanager

1. ZIP von GitHub herunterladen und entpacken
2. Thonny starten und den Pico 2 W per USB verbinden
3. Menü:
   - DE: **Ansicht → Dateien**
   - EN: **View → Files**
4. Links (PC) zum entpackten `CCARemote/`-Ordner navigieren
5. Rechts (Pico) in `/lib/` wechseln – falls nicht vorhanden:
   Rechtsklick → **Neuer Ordner** / **New directory** → `lib`
6. Rechtsklick auf den `CCARemote/`-Ordner (PC-Seite) →
   - DE: **Hochladen nach /lib/**
   - EN: **Upload to /lib/**

Ergebnis auf dem Pico: `/lib/CCARemote/__init__.py`, `ble.py`, `wifi.py`

### Option C – VS Code mit MicroPico Extension

1. Extension **MicroPico** installieren (ID: `paulober.pico-w-go`)
2. `micropython/CCARemote/`-Ordner in VS Code öffnen
3. In der Statusleiste unten: **MicroPico – Upload project to Pico** klicken
4. Alternativ: Rechtsklick auf den `CCARemote`-Ordner → **Upload folder to Pico**
5. Bibliothek muss sich auf dem Pico unter `/lib/CCARemote/` befinden

### Option D – mpremote (Kommandozeile)

```bash
pip install mpremote

# Bibliothek auf den Pico übertragen
mpremote mkdir /lib
mpremote mkdir /lib/CCARemote
mpremote cp micropython/CCARemote/__init__.py :/lib/CCARemote/__init__.py
mpremote cp micropython/CCARemote/ble.py      :/lib/CCARemote/ble.py
mpremote cp micropython/CCARemote/wifi.py     :/lib/CCARemote/wifi.py
```

---

## Schnellstart

4 Zeilen konfigurieren, `create_remote()` aufrufen – fertig. `begin()` hat keine Parameter:

```python
from machine import Pin
import time
from CCARemote import CCA_BLE, CCA_WIFI, CCA_DEBUG_ALL, create_remote

# ---- Konfiguration – hier anpassen! -----------------------
DEVICE_NAME = "MeinName"    # Gerätename (wird als "CCA-MeinName" angezeigt)
CONNECTION  = CCA_BLE       # CCA_BLE  oder  CCA_WIFI
PASSWORD    = ""            # Passwort (WiFi: min. 8 Zeichen / leer = ohne)
DEBUG_LEVEL     = CCA_DEBUG_ALL # CCA_DEBUG_OFF / _IN / _OUT / _ALL
DEBUG_TIMESTAMP = True          # False = kein Debug Zeitstempel

# Optional – nur setzen wenn Standardwert nicht passt:
# DEVICE_PREFIX = "XYZ-"   # Standard: "CCA-"
# TCP_PORT      = 4211      # Standard: 4210  (nur WiFi)
# -----------------------------------------------------------

remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL,
                       show_timestamp=DEBUG_TIMESTAMP)

LED_PIN = Pin("LED", Pin.OUT)  # Onboard-LED des Pico 2 W

remote.begin()
remote.receive("switch1", bool)

while True:
    remote.handle()     # Pflicht in der Hauptschleife!

    if remote.is_connected():
        LED_PIN.value(1 if remote.get("switch1", False) else 0)
    else:
        LED_PIN.value(0)

    time.sleep_ms(10)
```

Um zwischen BLE und WiFi zu wechseln, nur `CONNECTION` ändern – der restliche Code bleibt identisch.

---

## Konfiguration

| Konstante | Standard | Beschreibung |
|---|---|---|
| `DEVICE_NAME` | – | **Pflicht.** Gerätename, wird als `CCA-<name>` angezeigt |
| `CONNECTION` | – | **Pflicht.** `CCA_BLE` oder `CCA_WIFI` |
| `PASSWORD` | `""` | Passwort (BLE: AUTH-Passwort, WiFi: WPA2 ≥ 8 Zeichen) |
| `DEBUG_LEVEL` | `CCA_DEBUG_OFF` | `CCA_DEBUG_OFF` / `CCA_DEBUG_IN` / `CCA_DEBUG_OUT` / `CCA_DEBUG_ALL` |
| `DEBUG_TIMESTAMP` | `True` | `True` = Zeitstempel im Debug-Output / `False` = ohne Zeitstempel |
| `DEVICE_PREFIX` | `"CCA-"` | Prefix für den Gerätenamen (optionaler Parameter von `create_remote`) |
| `TCP_PORT` | `4210` | TCP-Port (optionaler Parameter von `create_remote`, nur WiFi) |

---

## API-Referenz

### Gemeinsame Methoden (alle Verbindungstypen)

| Methode | Beschreibung |
|---|---|
| `remote.begin()` | Verbindung starten – keine Parameter, alles über `create_remote()` konfiguriert |
| `remote.handle()` | **Pflicht in der Hauptschleife!** Befehle verarbeiten |
| `remote.is_connected()` | `True` wenn App verbunden |
| `remote.receive("id", typ)` | Element-ID mit Typ verknüpfen: `bool`, `int`, `float`, `str` |
| `remote.receive_color("id")` | Color-Picker-Element registrieren |
| `remote.get("id", default)` | Zuletzt empfangenen Wert abrufen |
| `remote.get_color("id")` | RGB-Werte als Tupel `(r, g, b)` abrufen (je 0–255) |
| `remote.send("id", wert)` | Wert an Display-Element der App senden |
| `remote.on_command("id", cb)` | Callback für Befehl registrieren |
| `remote.watchdog("id", ms)` | Variable automatisch auf 0 setzen wenn länger als `ms` ms kein Update |
| `remote.debug(modus)` | Debug-Level zur Laufzeit ändern |

### `receive()` – Variable mit App verknüpfen *(empfohlen)*

```python
remote.receive("button1", bool)    # bool  – für Button, Switch
remote.receive("slider1", int)     # int   – für Slider, Joystick-Achse
remote.receive("temp",    float)   # float – für Dezimalwerte
remote.receive("text1",   str)     # str   – für Texteingabe
```

Werte abrufen mit `remote.get("element_id", default)`.

Mit `resync=True` wird der aktuelle Variablenwert bei jedem Reconnect automatisch zur App
gesendet — so bleibt die Anzeige nach einem Verbindungsabbruch mit dem MCU-Zustand synchron:

```python
remote.receive("speed",  int,  resync=True)   # Slider – Wert bei Reconnect senden
remote.receive("power",  bool, resync=True)   # Switch – Zustand bei Reconnect senden
remote.receive_color("color1", resync=True)   # Color Picker – Farbe bei Reconnect senden
```

> **Joystick:** Jede Achse hat eine eigene Element-ID:
> ```python
> remote.receive("axisX", int)  # Joystick X (−255 – +255)
> remote.receive("axisY", int)  # Joystick Y (−255 – +255)
> ```

### `send()` – Werte in der App anzeigen

```python
remote.send("display1", 42)             # int
remote.send("display1", 3.14)           # float (1 Nachkommastelle)
remote.send("display1", 3.14159, 3)     # float mit 3 Nachkommastellen
remote.send("display1", "Hallo!")       # str
remote.send("display1:42")              # String-Form "key:value"
```

> **Hinweis – Label-Element:** Neben Display-, Gauge-, Chart- und LED-Elementen kann
> auch das **Label**-Element Werte empfangen. Wird `remote.send("label1", "Text")`
> aufgerufen, aktualisiert die App den angezeigten Text des Labels dynamisch.
> Die Element-ID muss dazu im Label-Editor der App eingetragen sein.

### `watchdog()` – Automatischer Nullwert bei Verbindungsverlust

Setzt eine Variable automatisch auf `0` zurück wenn sie länger als das angegebene Timeout nicht aktualisiert wurde. Typischer Anwendungsfall: Joystick-Achsen bei RC-Fahrzeugen.

```python
remote.receive("axisX", int)
remote.receive("axisY", int)
remote.watchdog("axisX", 500)  # axisX → 0 wenn 500 ms kein Update
remote.watchdog("axisY", 500)  # axisY → 0 wenn 500 ms kein Update
```

| Parameter | Typ | Beschreibung |
|---|---|---|
| `cmd` | `str` | Element-ID — muss mit `receive()` registriert sein |
| `timeout_ms` | `int` | Timeout in Millisekunden |

### `on_command()` – Callback bei Empfang *(für komplexe Logik)*

```python
# Callback ohne Wert (z. B. Button-Tap)
remote.on_command("btn", lambda: print("Button gedrückt!"))

# Callback mit Wert
remote.on_command("slider1", lambda v: print("Slider:", v))
```

### `debug()` – Debug-Level zur Laufzeit ändern

Normalerweise wird der Debug-Level über den `DEBUG_LEVEL`-Parameter von `create_remote()` festgelegt. Mit `debug()` kann er im Programm nachträglich geändert werden:

```python
from CCARemote import CCA_DEBUG_ALL, CCA_DEBUG_IN, CCA_DEBUG_OUT, CCA_DEBUG_OFF

remote.debug(CCA_DEBUG_ALL)   # IN + OUT ausgeben
remote.debug(CCA_DEBUG_IN)    # nur empfangene Werte
remote.debug(CCA_DEBUG_OUT)   # nur gesendete Werte
remote.debug(CCA_DEBUG_OFF)   # kein Output
```

---

## Steuerelemente (App → Pico)

| Element | Methode | Typ | Hinweis |
|---|---|---|---|
| Button | `receive()` | `bool` | `True` = gedrückt |
| Switch | `receive()` | `bool` | `True` = ein |
| Slider | `receive()` | `int` | Bereich in der App einstellbar (Standard 0–255) |
| Joystick | `receive()` | `int` | X und Y als separate Element-IDs |
| Input | `receive()` | `str` | Freier Text |
| Color Picker | `receive_color()` | – | Werte mit `get_color()` als `(r, g, b)` abrufen |

## Anzeigeelemente (Pico → App)

| Element | Methode | Hinweis |
|---|---|---|
| Display | `send()` | Messwert anzeigen |
| Gauge / Bar | `send()` | Balken / Kreisbogen |
| Chart | `send()` | Liniendiagramm |
| Status-LED | `send()` | Ganzzahl 0–3 |
| Label | `send()` | Text (optional, nur wenn Element-ID gesetzt) |

---

## Color Picker – RGB-LED Beispiel

```python
from CCARemote import CCA_BLE, CCA_DEBUG_ALL, create_remote
from machine import Pin, PWM

# ---- Konfiguration – hier anpassen! -----------------------
DEVICE_NAME     = "MeinName"
CONNECTION      = CCA_BLE
PASSWORD        = ""
DEBUG_LEVEL     = CCA_DEBUG_ALL
DEBUG_TIMESTAMP = True          # False = kein Debug Zeitstempel
# -----------------------------------------------------------

remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL,
                       show_timestamp=DEBUG_TIMESTAMP)

# Pins der gemeinsamen Kathode RGB-LED (PWM-fähige Pins)
pwm_r = PWM(Pin(13)); pwm_r.freq(1000)
pwm_g = PWM(Pin(14)); pwm_g.freq(1000)
pwm_b = PWM(Pin(15)); pwm_b.freq(1000)

remote.begin()
remote.receive_color("color1")  # Element-ID aus der App

while True:
    remote.handle()

    if remote.is_connected():
        r, g, b = remote.get_color("color1")
        pwm_r.duty_u16(r * 257)  # 0–255 → 0–65535
        pwm_g.duty_u16(g * 257)
        pwm_b.duty_u16(b * 257)
```

> **Hinweis:** Bei einer gemeinsamen Anode RGB-LED die Werte invertieren: `(255 - r) * 257` usw.

---

## Unterschiede zum ESP32/Arduino

| Arduino/ESP32 | MicroPython/Pico 2 W |
|---|---|
| `#define ... #include <CCARemote.h>` | `create_remote(DEVICE_NAME, CONNECTION, ...)` |
| `remote.isConnected()` | `remote.is_connected()` |
| `bool var; remote.receive("id", var)` | `remote.receive("id", bool)` + `remote.get("id")` |
| `analogWrite(pin, val)` | `PWM(Pin(nr)).duty_u16(val * 257)` |
| `Serial.println(...)` | `print(...)` |
| `millis()` | `time.ticks_ms()` |
| `delay(ms)` | `time.sleep_ms(ms)` |

---

## Dateistruktur auf dem Pico

```
/                       ← Root-Dateisystem des Pico
├── main.py             ← Dein Programm (wird beim Start ausgeführt)
└── lib/
    └── CCARemote/
        ├── __init__.py
        ├── ble.py
        └── wifi.py
```

---

## Troubleshooting

**BLE wird nicht gefunden:**
- Stellt sicher, dass die Pico 2 W Firmware (nicht Pico W oder Pico 2) verwendet wird
- BLE und WiFi gleichzeitig auf dem Pico 2 W ist möglich, kann aber zu Interferenzen führen

**WiFi AP erscheint nicht:**
- Nur der **Pico 2 W** (mit CYW43) unterstützt WiFi – nicht der normale Pico 2
- Passwörter müssen mindestens 8 Zeichen lang sein

**ImportError: no module named 'CCARemote':**
- Bibliothek unter `/lib/CCARemote/` auf dem Pico platzieren (nicht im Root-Verzeichnis)

---

## Hinweis
Diese Bibliothek wurde von A. Eckhart entwickelt. Die Nutzung erfolgt auf eigene Verantwortung – es wird keine Gewährleistung für Richtigkeit, Vollständigkeit oder Eignung für einen bestimmten Zweck übernommen.
