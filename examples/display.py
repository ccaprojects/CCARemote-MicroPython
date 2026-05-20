# =============================================================
#  CCA Remote Beispiel: Display Element
#  Aktualisiert jede Sekunde einen Zähler und gibt den Wert
#  in einem Display-Element der App aus.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W or ESP32  |  MicroPython ≥ 1.23
# =============================================================

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


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.begin()

counter     = 0
last_update = time.ticks_ms()
UPDATE_MS   = 1000  # Aktualisierungsintervall in Millisekunden


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()     # Empfangene Befehle verarbeiten (erforderlich!)

    # Wert jede Sekunde senden (nur wenn App verbunden)
    if remote.is_connected():
        now = time.ticks_ms()
        if time.ticks_diff(now, last_update) >= UPDATE_MS:
            last_update = now
            counter += 1
            remote.send("display1", counter)

    time.sleep_ms(10)
