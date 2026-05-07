# =============================================================
#  CCA Remote Beispiel: Alle Elemente (WiFi)
#  Alle unterstützten Steuerelemente der App über WiFi.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =============================================================

from CCARemote.wifi import CCARemoteWiFi
from machine import Pin, PWM
import time

remote = CCARemoteWiFi("MeinName")  # Namen hier anpassen!

LED_BUTTON = Pin("LED",  Pin.OUT)   # Onboard-LED  → Button-Element
LED_SLIDER = PWM(Pin(15))           # PWM-LED (GP15) → Slider-Element
LED_SLIDER.freq(1000)
LED_SWITCH = Pin(16, Pin.OUT)       # LED (GP16) → Switch-Element
LED_INPUT  = Pin(17, Pin.OUT)       # LED (GP17) → Input-Element


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.debug()
remote.begin()          # Offener WiFi-Hotspot (kein Passwort)
# remote.begin("geheim1234")  # Mit Passwort

remote.receive("button1", bool)
remote.receive("slider1", int)
remote.receive("switch1", bool)
remote.receive("input1",  str)
remote.receive("axisX",   int)
remote.receive("axisY",   int)


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()

    if remote.is_connected():
        button1_val = remote.get("button1", False)
        slider1_val = remote.get("slider1", 0)
        switch1_val = remote.get("switch1", False)
        command     = remote.get("input1",  "")

        LED_BUTTON.value(1 if button1_val else 0)
        LED_SLIDER.duty_u16(slider1_val * 257)
        LED_SWITCH.value(1 if switch1_val else 0)

        if command:
            LED_INPUT.value(1 if command.upper() == "ON" else 0)

        remote.send("display1", slider1_val)

    else:
        LED_BUTTON.value(0)
        LED_SLIDER.duty_u16(0)
        LED_SWITCH.value(0)
        LED_INPUT.value(0)

    time.sleep_ms(10)
