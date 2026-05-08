# =============================================================
#  CCA Remote Beispiel: Alle Elemente (BLE)
#  Alle unterstützten Steuerelemente der App.
#  Empfangene Werte werden im REPL ausgegeben.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =============================================================

from machine import Pin, PWM
import time

# Für BLE-Verbindung:
from CCARemote.ble import CCARemoteBLE
remote = CCARemoteBLE("MeinName")   # Namen hier anpassen!

# Für WiFi-Verbindung stattdessen:
# from CCARemote.wifi import CCARemoteWiFi
# remote = CCARemoteWiFi("MeinName")

LED_BUTTON = Pin("LED",  Pin.OUT)   # Onboard-LED  → Button-Element
LED_SLIDER = PWM(Pin(15))           # PWM-LED (GP15) → Slider-Element
LED_SLIDER.freq(1000)
LED_SWITCH = Pin(16, Pin.OUT)       # LED (GP16) → Switch-Element
LED_INPUT  = Pin(17, Pin.OUT)       # LED (GP17) → Input-Element


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.debug()          # Debug-Modus aktivieren
remote.begin()          # BLE starten

# Element-IDs aus der App mit Typen verknüpfen
# Werte abrufen mit: remote.get("Element-ID")
remote.receive("button1", bool)    # true = gedrückt
remote.receive("slider1", int)     # 0 – 255
remote.receive("switch1", bool)    # true = aktiv
remote.receive("input1",  str)     # beliebige Texteingabe
remote.receive("axisX",   int)     # Joystick X: -255 – +255
remote.receive("axisY",   int)     # Joystick Y: -255 – +255


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

        # Slider-Wert an Display-Element der App senden
        remote.send("display1", slider1_val)

        # Hardware-Typ (Pico 2W) an Label-Element der App senden
        remote.send("label1", "Pico 2W")

    else:
        # Alle Ausgaben auf sicheren Zustand setzen
        LED_BUTTON.value(0)
        LED_SLIDER.duty_u16(0)
        LED_SWITCH.value(0)
        LED_INPUT.value(0)

    time.sleep_ms(10)
