# =============================================================
#  CCA Remote Beispiel: WiFi Verbindung
#  Ein Schalter in der App schaltet die onboard-LED ein oder aus.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =============================================================

from machine import Pin
import time

# Für BLE-Verbindung:
# from CCARemote.ble import CCARemoteBLE
# remote = CCARemoteBLE("MeinName")   # Namen hier anpassen!

# Für WiFi-Verbindung stattdessen:
from CCARemote.wifi import CCARemoteWiFi
remote = CCARemoteWiFi("MeinName")

LED_PIN = Pin("LED", Pin.OUT)       # Onboard-LED des Pico 2 W
# Externe LED: LED_PIN = Pin(15, Pin.OUT)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.debug()
remote.begin()              # BLE starten (kein Passwort)

remote.receive("switch1", bool)


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()     # Empfangene Befehle verarbeiten (erforderlich!)

    if remote.is_connected():
        LED_PIN.value(1 if remote.get("switch1", False) else 0)
    else:
        LED_PIN.value(0)

    time.sleep_ms(10)
