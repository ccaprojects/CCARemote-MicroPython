# =============================================================
#  CCA Remote Beispiel: Button Element (BLE)
#  Ein Taster in der App schaltet die onboard-LED ein oder aus.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =============================================================

from CCARemote.ble import CCARemoteBLE
from machine import Pin
import time

# Für WiFi-Verbindung stattdessen:
# from CCARemote.wifi import CCARemoteWiFi
# remote = CCARemoteWiFi("MeinName")

remote = CCARemoteBLE("MeinName")   # Namen hier anpassen!

LED_PIN = Pin("LED", Pin.OUT)       # Onboard-LED des Pico 2 W
# Externe LED: LED_PIN = Pin(15, Pin.OUT)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.debug()          # Debug-Modus: CCA_DEBUG_IN, CCA_DEBUG_OUT oder CCA_DEBUG_ALL
remote.begin()          # BLE starten

# Die Element-IDs aus der App werden mit Typen verknüpft.
# Werte abrufen mit: remote.get("Element-ID")
remote.receive("button1", bool)


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()     # Empfangene Befehle verarbeiten (erforderlich!)

    if remote.is_connected():
        LED_PIN.value(1 if remote.get("button1", False) else 0)
    else:
        LED_PIN.value(0)    # LED ausschalten wenn keine Verbindung

    time.sleep_ms(10)
