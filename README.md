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
| `persist` | `True` | Zustandsspeicherung in `/cca_state.json` – `False` deaktiviert die Persistenz |

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
| `remote.send_always("id", wert)` | Wie `send()`, aber auch bei gleichem Wert – für Charts |
| `remote.on_command("id", cb)` | Callback für Befehl registrieren |
| `remote.watchdog("id", ms)` | Variable automatisch auf 0 setzen wenn länger als `ms` ms kein Update |
| `remote.set_profile(config)` | Profil-Definition einbetten – wird beim Verbindungsaufbau an die App übertragen |
| `remote.load_state()` | Letzten Zustand sofort aus `/cca_state.json` laden (ohne App-Verbindung) |
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

### `receive_color()` / `get_color()` – RGB-Farbwerte empfangen

Verknüpft ein Color-Picker-Element; Werte werden als Tupel `(r, g, b)` (je 0–255) geliefert.

```python
remote.receive_color("color1")        # Element-ID aus der App registrieren
r, g, b = remote.get_color("color1")  # RGB-Werte abrufen
```

Mit `resync=True` wird die zuletzt empfangene Farbe bei jedem Reconnect zur App zurückgesendet:

```python
remote.receive_color("color1", resync=True)
```

### `receive()` – Mode Selector

Der Mode Selector sendet bei jeder Auswahl den **Index** der gewählten Option (`0`, `1`, `2`, …) als `int`. Mit der Option **„Label senden"** in der App wird stattdessen der Label-Text als `str` übermittelt.

```python
# Standard: Index-Modus
remote.receive("modus", int)

# Mit Option „Label senden" aktiv:
# remote.receive("modus", str)

# Wert abrufen:
modus = remote.get("modus", 0)       # int
# modus = remote.get("modus", "Aus") # str

# Index-Modus verwenden (0 = Aus, 1 = Langsam, 2 = Schnell):
if modus == 0:
    pass  # Aus
elif modus == 1:
    pass  # Langsam
elif modus == 2:
    pass  # Schnell

# Label-Modus:
# if modus == "Langsam": ...
```

| Einstellung | Typ | Empfangener Wert |
|---|---|---|
| Standard (Index) | `int` | `0`, `1`, `2`, … |
| „Label senden" aktiv | `str` | `"Aus"`, `"Langsam"`, `"Schnell"`, … |

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

### `send_always()` – Wert immer senden (für Charts)

`send()` unterdrückt Duplikate und sendet nur bei Wertänderung. `send_always()` sendet bei jedem Aufruf — nötig für Chart-Elemente, die jeden einzelnen Messpunkt empfangen sollen.

```python
remote.send_always("chart1", sensor_wert)          # int
remote.send_always("chart1", 3.14, 2)              # float mit 2 Nachkommastellen
```

### Persistente Zustandsspeicherung

Variablenwerte werden beim Trennen der Verbindung automatisch in `/cca_state.json` gespeichert und beim nächsten Start wiederhergestellt — auch nach Neustart oder Stromverlust.

```python
# Standard: persist=True – Werte werden automatisch gespeichert
remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL)

# Deaktivieren:
remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL, persist=False)
```

Ablauf beim Connect nach einem Neustart:
1. `begin()` lädt Werte aus `/cca_state.json`
2. Bei Verbindungsaufbau überträgt der Pico alle gespeicherten Werte an die App
3. Die App zeigt den letzten Zustand sofort an — ohne Interaktion des Benutzers

Gespeichert werden alle über `receive()` registrierten Typen (`bool`, `int`, `float`, `str`) sowie Farben (`receive_color()`). Die Datei `/cca_state.json` liegt im Root-Dateisystem des Pico und wird automatisch angelegt.

> **Hinweis:** Die Persistenz ergänzt `resync=True` — `resync=True` sendet den aktuellen
> In-Memory-Wert bei jedem Reconnect; die Persistenz stellt zusätzlich sicher, dass dieser
> Wert auch nach einem Neustart noch korrekt ist.

**Letzten Zustand beim Start laden:** Standardmäßig werden die gespeicherten Werte erst beim ersten App-Connect in die Variablen geladen. Mit `load_state()` kann der Zustand bereits beim Start befüllt werden — ohne dass eine Verbindung nötig ist. Nützlich wenn der Controller ohne App sofort mit den letzten Einstellungen laufen soll (z. B. Licht, Effekt, Farbe):

```python
remote.begin()
remote.receive("switch1", bool, resync=True)
remote.receive("slider1", int,  resync=True)
remote.receive_color("color1",  resync=True)

remote.load_state()   # letzte Einstellungen sofort laden
                      # Ohne diese Zeile: Laden beim ersten App-Connect (bisheriges Verhalten)
```

> **Hinweis:** `load_state()` muss nach allen `receive()`-Aufrufen aufgerufen werden. Nur wirksam wenn `persist=True` (Standard).

**Persistierten Zustand löschen:** Beim Wechsel zu einem Profil mit anderen Element-IDs können veraltete Einträge in `/cca_state.json` gelöscht werden:

```python
remote.clear_state()  # löscht /cca_state.json
```

`clear_state()` greift nur in den gespeicherten Zustand ein — die aktuellen In-Memory-Werte der laufenden Session bleiben unverändert.

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

### `set_profile()` – Profil automatisch erstellen

Bettet eine Profil-Definition in den Controller ein. Der Config-String wird beim Verbindungsaufbau an die App übertragen; die App erstellt das Profil automatisch, falls es noch nicht existiert, und wechselt dann zu diesem Profil.

Den String generiert man in der App unter **Profil → „Profil-Code kopieren" → Plattform wählen**.

```python
# Exportierten Profil-String hier einfügen:
PROFILE = (
    "v:3"
    "|nm:MeinGerät"
    "|sl:speed:0:255@10,10,340,80|..."
)

remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL)
remote.set_profile(PROFILE)   # vor begin() aufrufen
remote.begin()
```

> **Tipp:** `set_profile()` muss vor `begin()` aufgerufen werden, damit der String beim
> ersten Verbindungsaufbau übertragen wird.

### `debug()` – Debug-Level zur Laufzeit ändern

Normalerweise wird der Debug-Level über den `DEBUG_LEVEL`-Parameter von `create_remote()` festgelegt. Mit `debug()` kann er im Programm nachträglich geändert werden:

```python
from CCARemote import CCA_DEBUG_ALL, CCA_DEBUG_IN, CCA_DEBUG_OUT, CCA_DEBUG_OFF

remote.debug(CCA_DEBUG_ALL)   # IN + OUT ausgeben
remote.debug(CCA_DEBUG_IN)    # nur empfangene Werte
remote.debug(CCA_DEBUG_OUT)   # nur gesendete Werte
remote.debug(CCA_DEBUG_OFF)   # kein Output
```

| Modus | Beschreibung |
|---|---|
| `CCA_DEBUG_OFF` | Kein Debug-Output |
| `CCA_DEBUG_IN`  | Empfangene Werte ausgeben (`[CCA] IN  key = wert`) |
| `CCA_DEBUG_OUT` | Gesendete Werte ausgeben (`[CCA] OUT key = wert`) |
| `CCA_DEBUG_ALL` | Empfangene und gesendete Werte ausgeben |

### Gerätename und Prefix anpassen

```python
remote = create_remote("Roboter", CONNECTION, PASSWORD, DEBUG_LEVEL,
                       prefix="HTL-")  # → "HTL-Roboter"

# Kein Prefix:
remote = create_remote("Roboter", CONNECTION, PASSWORD, DEBUG_LEVEL,
                       prefix="")      # → "Roboter"
```

---

## Vollständiges Beispiel

```python
from machine import Pin, PWM
import time
from CCARemote import CCA_BLE, CCA_DEBUG_ALL, create_remote

# ---- Konfiguration – hier anpassen! -----------------------
DEVICE_NAME     = "MeinName"
CONNECTION      = CCA_BLE
PASSWORD        = ""
DEBUG_LEVEL     = CCA_DEBUG_ALL
DEBUG_TIMESTAMP = True
# -----------------------------------------------------------

remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL,
                       show_timestamp=DEBUG_TIMESTAMP)

LED_PIN = Pin("LED", Pin.OUT)
pwm     = PWM(Pin(15)); pwm.freq(1000)  # PWM-fähiger Pin

remote.begin()
remote.receive("switch1",    bool)
remote.receive("brightness", int)

last_send = 0

while True:
    remote.handle()

    if remote.is_connected():
        LED_PIN.value(1 if remote.get("switch1", False) else 0)
        pwm.duty_u16(remote.get("brightness", 0) * 257)  # 0–255 → 0–65535

        now = time.ticks_ms()
        if time.ticks_diff(now, last_send) >= 2000:
            last_send = now
            remote.send("uptime", time.ticks_ms() // 1000)
    else:
        LED_PIN.value(0)
        pwm.duty_u16(0)

    time.sleep_ms(10)
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
| Mode Selector | `receive()` | `int` | Ausgewählter Index (0–N); mit Option „Label senden": `str` (Label-Text) |

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
| `remote.loadState()` | `remote.load_state()` |
| `remote.clearState()` | `remote.clear_state()` |
| `analogWrite(pin, val)` | `PWM(Pin(nr)).duty_u16(val * 257)` |
| `Serial.println(...)` | `print(...)` |
| `millis()` | `time.ticks_ms()` |
| `delay(ms)` | `time.sleep_ms(ms)` |

---

## Dateistruktur auf dem Pico

```
/                       ← Root-Dateisystem des Pico
├── main.py             ← Dein Programm (wird beim Start ausgeführt)
├── cca_state.json      ← Persistente Zustandsdaten (automatisch erstellt, nur wenn persist=True)
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
