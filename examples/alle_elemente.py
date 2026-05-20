# =============================================================
#  CCA Remote Beispiel: Alle Elemente
#  Alle unterstützten Steuerelemente der App.
#  Empfangene Werte werden im REPL ausgegeben.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W or ESP32  |  MicroPython ≥ 1.23
# =============================================================

from machine import Pin, PWM
import time
import random
import neopixel

from CCARemote import CCA_BLE, CCA_WIFI, CCA_DEBUG_OFF, CCA_DEBUG_ALL, create_remote

# ---- Konfiguration – hier anpassen! -----------------------
DEVICE_NAME     = "MeinName"    # Gerätename (wird als "CCA-MeinName" angezeigt)
CONNECTION      = CCA_BLE       # CCA_BLE  oder  CCA_WIFI
PASSWORD        = ""            # Passwort (WiFi: min. 8 Zeichen / leer = ohne)
DEBUG_LEVEL     = CCA_DEBUG_ALL # CCA_DEBUG_OFF / _IN / _OUT / _ALL
DEBUG_TIMESTAMP = True          # False = kein Debug Zeitstempel

# Optional – nur setzen wenn Standardwert nicht passt:
# DEVICE_PREFIX = "XYZ-"   # Standard: "CCA-"
# TCP_PORT      = 4211      # Standard: 4210  (nur WiFi)
# -----------------------------------------------------------

remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL,
                       show_timestamp=DEBUG_TIMESTAMP)

LED_BUTTON = Pin("LED",  Pin.OUT)   # Onboard-LED  → Button-Element
LED_SLIDER = PWM(Pin(15))           # PWM-LED (GP15) → Slider-Element
LED_SLIDER.freq(1000)
LED_SWITCH = Pin(16, Pin.OUT)       # LED (GP16) → Switch-Element
LED_INPUT  = Pin(17, Pin.OUT)       # LED (GP17) → Input-Element

# PWM-Ausgänge für RGB-LED → Color-Picker-Element
# App-Wert 0–255 → duty_u16: 0–65535 (Faktor 257)
LED_R = PWM(Pin(19))
LED_G = PWM(Pin(20))
LED_B = PWM(Pin(21))
for led in (LED_R, LED_G, LED_B):
    led.freq(1000)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.begin()

# Element-IDs aus der App mit Typen verknüpfen
# Werte abrufen mit: remote.get("Element-ID")
remote.receive("button1", bool)    # true = gedrückt
remote.receive("slider1", int)     # 0 – 255
remote.receive("switch1", bool)    # true = aktiv
remote.receive("input1",  str)     # beliebige Texteingabe

# Joystick
remote.receive("axisX",   int)     # Joystick X: -255 – +255
remote.receive("axisY",   int)     # Joystick Y: -255 – +255
# Automatischer Nullwert bei Verbindungsverlust für Joystick
remote.watchdog("axisX", 500);  // axisX → 0 wenn 500 ms kein Update
remote.watchdog("axisY", 500);  // axisY → 0 wenn 500 ms kein Update

# Color-Picker
remote.receive_color("color1")     # Color Picker: liefert (r, g, b) via get_color()


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()     # Empfangene Befehle verarbeiten (erforderlich!)

    if remote.is_connected():
        button1_val = remote.get("button1", False)
        slider1_val = remote.get("slider1", 0)
        switch1_val = remote.get("switch1", False)
        command     = remote.get("input1",  "")

        # LED mit Button-Element schalten
        LED_BUTTON.value(1 if button1_val else 0)

        # LED mit Slider-Element dimmen
        # App-Wert 0–255 → duty_u16: 0–65535
        LED_SLIDER.duty_u16(slider1_val * 257)

        # LED mit Switch-Element schalten
        LED_SWITCH.value(1 if switch1_val else 0)

        # LED mit Input-Element steuern: "ON" = an, alles andere = aus
        if command:
            LED_INPUT.value(1 if command.upper() == "ON" else 0)

        # Color-Picker-Werte auf RGB-LED ausgeben
        r, g, b = remote.get_color("color1")
        LED_R.duty_u16(r * 257)
        LED_G.duty_u16(g * 257)
        LED_B.duty_u16(b * 257)

        # Slider-Wert an Display-Element der App senden
        remote.send("display1", slider1_val)

        # Hardware-Typ an Label-Element der App senden
        remote.send("label1", "Pico 2W")

    else:
        # Alle Ausgaben auf sicheren Zustand setzen
        LED_BUTTON.value(0)
        LED_SLIDER.duty_u16(0)
        LED_SWITCH.value(0)
        LED_INPUT.value(0)
        LED_R.duty_u16(0)
        LED_G.duty_u16(0)
        LED_B.duty_u16(0)

    time.sleep_ms(10)
