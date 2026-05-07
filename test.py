# =============================================================
#  CCA Remote Beispiel: Switch Element (BLE)
#  Ein Schalter in der App schaltet die onboard-LED ein oder aus.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =============================================================

from machine import Pin
import time

# Für BLE-Verbindung:
from CCARemote.ble import CCARemoteBLE
remote = CCARemoteBLE("MeinName")   # Namen hier anpassen!

# Für WiFi-Verbindung stattdessen:
#from CCARemote.wifi import CCARemoteWiFi
#remote = CCARemoteWiFi("MeinName")


LED_PIN = Pin("LED", Pin.OUT)       # Onboard-LED des Pico 2 W
# Externe LED: LED_PIN = Pin(15, Pin.OUT)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.debug()
remote.begin()

remote.receive("switch1", bool)

last_val = 0
curr_val = 0

# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()
    
    if remote.is_connected():
        curr_val = 0
        if remote.get("switch1", False):
            curr_val = 1

        if curr_val != last_val:
            LED_PIN.value(curr_val)
            remote.send("chart1", curr_val)
            last_val = curr_val
    else:
        LED_PIN.value(0)

    time.sleep_ms(10)
