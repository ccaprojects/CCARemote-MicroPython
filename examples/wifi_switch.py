# =============================================================
#  CCA Remote Beispiel: WiFi Verbindung
#  Ein Schalter in der App schaltet die onboard-LED ein oder aus.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =============================================================

from CCARemote.wifi import CCARemoteWiFi
from machine import Pin
import time

# Für BLE-Verbindung stattdessen:
# from CCARemote.ble import CCARemoteBLE
# remote = CCARemoteBLE("MeinName")

remote = CCARemoteWiFi("MeinName")  # Namen hier anpassen!

LED_PIN = Pin("LED", Pin.OUT)       # Onboard-LED des Pico 2 W
# Externe LED: LED_PIN = Pin(15, Pin.OUT)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.debug()
remote.begin("geheim1234")  # WLAN-Hotspot-Passwort (leer = offenes Netzwerk)

remote.receive("switch1", bool)


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()     # HTTP-Anfragen verarbeiten (erforderlich!)

    if remote.is_connected():
        LED_PIN.value(1 if remote.get("switch1", False) else 0)
    else:
        LED_PIN.value(0)

    time.sleep_ms(10)
