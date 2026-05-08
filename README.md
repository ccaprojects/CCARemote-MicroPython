# CCA Remote – Installationsanleitung für den Raspberry Pi Pico 2 W

# CCARemote – MicroPython Bibliothek

Flexible Steuerung von Mikrocontrollern über Bluetooth Low Energy (BLE) oder WLAN (WiFi). Die erforderliche App **CCA Remote** ist für Android und iOS kostenlos verfügbar.
Dieses Projekt wurde von der HTL Anichstraße (Abteilung Wirtschaftsingenieure – Betriebsinformatik) entwickelt.

Unterstützte Protokolle:
- **Bluetooth Low Energy (BLE)**
- **WiFi (WLAN-Hotspot + HTTP)**
- **MQTT** (in Arbeit)

Unterstützte Hardware:
- **ESP32** – natives BLE, WiFi, MQTT
- **ESP8266** - WiFi, MQTT
- **Arduino Uno / Nano** – BLE über HM-10-Modul (SoftwareSerial)
- **Raspberry Pi Pico 2W** – natives BLE, WiFi, MQTT

Dieses Dokument beschreibt die Installation der **CCARemote MicroPython-Bibliothek**
für den Raspberry Pi Pico 2 W in **Thonny** und **VS Code**.

> Für **ESP32, ESP8266 und Arduino** steht die Arduino-Bibliothek unter
> [github.com/ccaprojects/CCARemote-Arduino](https://github.com/ccaprojects/CCARemote-Arduino) zur Verfügung.

---

## Voraussetzungen

| Anforderung | Details |
|---|---|
| Hardware | Raspberry Pi **Pico 2 W** (mit WLAN/BLE-Chip CYW43) |
| Firmware | MicroPython **≥ 1.23** für Pico 2 W |
| Thonny | Version 4.x oder neuer |
| VS Code | mit Extension **MicroPico** oder **RT-Thread MicroPython** |

### MicroPython-Firmware flashen

1. [micropython.org/download/RPI_PICO2_W](https://micropython.org/download/RPI_PICO2_W/) aufrufen
2. Die neueste `.uf2`-Datei herunterladen
3. **BOOTSEL**-Taste am Pico gedrückt halten → USB-Kabel einstecken → Taste loslassen
4. Pico erscheint als USB-Laufwerk → `.uf2`-Datei draufziehen → Pico startet automatisch

---

## Installation der Bibliothek

### Option A – Thonny (empfohlen für Einsteiger)

1. Thonny starten und den Pico 2 W verbinden
2. Im Menü: **Datei → Öffnen** → `micropython/CCARemote/` (diesen Ordner öffnen)
3. Im Thonny-Dateimanager (unten rechts: „Raspberry Pi Pico"):
   - Rechtsklick → **Neuer Ordner** → `lib` erstellen (falls noch nicht vorhanden)
   - Rechtsklick auf `lib` → **Neuer Ordner** → `CCARemote` erstellen
4. Alle 4 Dateien aus `micropython/CCARemote/` auf den Pico kopieren:
   - `__init__.py`
   - `ble.py`
   - `wifi.py`
   - `mqtt.py`
   
   Ziel auf dem Pico: `/lib/CCARemote/`

**Alternativ per Drag & Drop im Thonny-Dateimanager:**
Den gesamten Ordner `CCARemote/` in `/lib/` auf dem Pico ziehen.

### Option B – VS Code mit MicroPico Extension

1. Extension **MicroPico** installieren (ID: `paulober.pico-w-go`)
2. `micropython/CCARemote/`-Ordner in VS Code öffnen
3. In der Statusleiste unten: **MicroPico – Upload project to Pico** klicken
4. Alternativ: Rechtsklick auf den `CCARemote`-Ordner → **Upload folder to Pico**
5. Bibliothek muss sich auf dem Pico unter `/lib/CCARemote/` befinden

### Option C – mpremote (Kommandozeile)

```bash
pip install mpremote

# Bibliothek auf den Pico übertragen
mpremote mkdir /lib
mpremote mkdir /lib/CCARemote
mpremote cp micropython/CCARemote/__init__.py :/lib/CCARemote/__init__.py
mpremote cp micropython/CCARemote/ble.py      :/lib/CCARemote/ble.py
mpremote cp micropython/CCARemote/wifi.py     :/lib/CCARemote/wifi.py
mpremote cp micropython/CCARemote/mqtt.py     :/lib/CCARemote/mqtt.py
```

---

## Verwendung

Nach der Installation liegt die Bibliothek unter `/lib/CCARemote/` auf dem Pico.
MicroPython findet sie automatisch beim Import.

### BLE-Verbindung

```python
from CCARemote.ble import CCARemoteBLE
from machine import Pin
import time

remote = CCARemoteBLE("MeinPico")   # Gerätename in der App
remote.begin()                       # BLE starten (kein Passwort)
# remote.begin("geheim1234")        # Mit BLE-Passwort

remote.receive("button1", bool)      # Element-ID aus der App
remote.receive("slider1", int)
remote.receive("switch1", bool)

led = Pin("LED", Pin.OUT)

while True:
    remote.handle()                              # Pflicht in der Hauptschleife!
    if remote.is_connected():
        led.value(1 if remote.get("button1", False) else 0)
    time.sleep_ms(10)
```

### WiFi-Verbindung (Hotspot)

> ⚠️ **Einschränkung:** Der MicroPython-Treiber des CYW43439-Chips unterstützt
> WPA2-Verschlüsselung im Access-Point-Modus **nicht**. Der Hotspot startet immer
> als **offenes Netzwerk** – ein übergebenes Passwort wird ignoriert. Wer eine
> gesicherte Verbindung benötigt, sollte stattdessen **BLE** verwenden.

```python
from CCARemote.wifi import CCARemoteWiFi
from machine import Pin
import time

remote = CCARemoteWiFi("MeinPico")
remote.begin()                        # Kein Passwort – WiFi ist immer offen

remote.receive("switch1", bool)

led = Pin("LED", Pin.OUT)

while True:
    remote.handle()
    if remote.is_connected():
        led.value(1 if remote.get("switch1", False) else 0)
    time.sleep_ms(10)
```

### MQTT-Verbindung

```python
from CCARemote.mqtt import CCARemoteMQTT
from machine import Pin
import time

remote = CCARemoteMQTT("MeinPico")
remote.begin("MeinWLAN", "wlanpasswort", "192.168.1.100")

remote.receive("switch1", bool)

led = Pin("LED", Pin.OUT)

while True:
    remote.handle()
    if remote.is_connected():
        led.value(1 if remote.get("switch1", False) else 0)
    time.sleep_ms(10)
```

---

## API-Referenz

### Gemeinsame Methoden (alle Verbindungstypen)

| Methode | Beschreibung |
|---|---|
| `remote.begin(...)` | Verbindung starten (Parameter je nach Typ) |
| `remote.handle()` | **Pflicht in der Hauptschleife!** Befehle verarbeiten |
| `remote.is_connected()` | `True` wenn App verbunden |
| `remote.receive("id", typ)` | Element-ID mit Typ verknüpfen: `bool` (Button, Switch), `int` (Slider, Joystick-Achse), `float`, `str` (Input) |
| `remote.get("id", default)` | Zuletzt empfangenen Wert abrufen |
| `remote.send("id", wert)` | Wert an Display-Element der App senden |
| `remote.on_command("id", cb)` | Callback für Befehl registrieren |
| `remote.debug()` | Debug-Ausgaben im REPL aktivieren |

### Debug-Modus

```python
from CCARemote import CCA_DEBUG_ALL, CCA_DEBUG_IN, CCA_DEBUG_OUT, CCA_DEBUG_OFF

remote.debug(CCA_DEBUG_ALL)   # IN + OUT ausgeben (Standard)
remote.debug(CCA_DEBUG_IN)    # nur empfangene Werte
remote.debug(CCA_DEBUG_OUT)   # nur gesendete Werte
remote.debug(CCA_DEBUG_OFF)   # kein Output
```

### Elemente und Typen

| Element | Typ | Richtung | Hinweis |
|---|---|---|---|
| Button | `bool` | App → Pico | `True` = gedrückt |
| Switch | `bool` | App → Pico | `True` = ein |
| Slider | `int` | App → Pico | Bereich in der App einstellbar (Standard 0–255) |
| Joystick | `int` | App → Pico | X und Y als separate Element-IDs |
| Input | `str` | App → Pico | Freier Text |
| Display | `send()` | Pico → App | Messwert anzeigen |
| Gauge / Bar | `send()` | Pico → App | Balken / Kreisbogen |
| Chart | `send()` | Pico → App | Liniendiagramm |
| Status-LED | `send()` | Pico → App | Ganzzahl 0–3 |
| Label | `send()` | Pico → App | Text (optional, nur wenn Element-ID gesetzt) |

> **Joystick:** Jede Achse hat eine eigene Element-ID:
> ```python
> remote.receive("axisX", int)  # Joystick X (−255 – +255)
> remote.receive("axisY", int)  # Joystick Y (−255 – +255)
> ```

### Callbacks

```python
# Callback ohne Wert (z. B. Button-Tap)
remote.on_command("btn", lambda: print("Button gedrückt!"))

# Callback mit Wert
remote.on_command("slider1", lambda v: print("Slider:", v))
```

### Werte senden

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

---

## Unterschiede zum ESP32-Original

| Arduino/ESP32 | MicroPython/Pico 2 W |
|---|---|
| `remote.isConnected()` | `remote.is_connected()` |
| `remote.begin()` | `remote.begin()` – identisch |
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
        ├── wifi.py
        └── mqtt.py
```

---

## Troubleshooting

**BLE wird nicht gefunden:**
- Stellt sicher, dass die Pico 2 W Firmware (nicht Pico W oder Pico 2) verwendet wird
- BLE und WiFi gleichzeitig auf dem Pico 2 W ist möglich, kann aber zu Interferenzen führen

**WiFi AP erscheint nicht:**
- Nur der **Pico 2 W** (mit CYW43) unterstützt WiFi – nicht der normale Pico 2
- Passwörter müssen mindestens 8 Zeichen lang sein

**MQTT: `umqtt.simple` nicht gefunden:**
```python
import mip
mip.install("umqtt.simple")
```

**ImportError: no module named 'CCARemote':**
- Bibliothek unter `/lib/CCARemote/` auf dem Pico platzieren (nicht im Root-Verzeichnis)

---

*Basierend auf der Diplomarbeit von L. Eder und E. Duyar (HTL Anichstraße)*  
*Erweitert von A. Eckhart mit freundlicher Genehmigung der Originalautoren.*  
*Version 1.0.0 | 2026-05-07 | MIT-Lizenz*
