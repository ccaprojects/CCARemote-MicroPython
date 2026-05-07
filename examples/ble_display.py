# =============================================================
#  CCA Remote Beispiel: Display Element (BLE)
#  Aktualisiert jede Sekunde einen Zähler und gibt den Wert
#  in einem Display-Element der App aus.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =============================================================

from CCARemote.ble import CCARemoteBLE
import time

# Für WiFi-Verbindung stattdessen:
# from CCARemote.wifi import CCARemoteWiFi
# remote = CCARemoteWiFi("MeinName")

remote = CCARemoteBLE("MeinName")   # Namen hier anpassen!


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
    remote.handle()

    # Wert jede Sekunde senden (nur wenn App verbunden)
    if remote.is_connected():
        now = time.ticks_ms()
        if time.ticks_diff(now, last_update) >= UPDATE_MS:
            last_update = now
            counter += 1
            remote.send("display1", counter)

    time.sleep_ms(10)
