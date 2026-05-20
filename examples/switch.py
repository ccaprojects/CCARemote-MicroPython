# =============================================================
#  CCA Remote Beispiel: Switch Element
#  Ein Schalter in der App schaltet die onboard-LED ein oder aus.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W or ESP32 |  MicroPython ≥ 1.23
# =============================================================

from machine import Pin
import time

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

LED_PIN = Pin("LED", Pin.OUT)       # Onboard-LED des Pico 2 W
# Externe LED: LED_PIN = Pin(15, Pin.OUT)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.begin()

remote.receive("switch1", bool)


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()     # Empfangene Befehle verarbeiten (erforderlich!)

    if remote.is_connected():
        LED_PIN.value(1 if remote.get("switch1", False) else 0)
    else:
        LED_PIN.value(0)    # LED ausschalten wenn keine Verbindung

    time.sleep_ms(10)
