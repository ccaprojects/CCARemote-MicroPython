# =============================================================
#  CCA Remote Beispiel: MQTT Verbindung
#  Ein Schalter in der App steuert die onboard-LED über MQTT.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
#  Benötigt: umqtt.simple (in Standard-Firmware enthalten)
# =============================================================

from CCARemote.mqtt import CCARemoteMQTT
from machine import Pin
import time

remote = CCARemoteMQTT("MeinName")  # Namen hier anpassen!

LED_PIN = Pin("LED", Pin.OUT)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.debug()
remote.begin(
    wifi_ssid     = "MeinWLAN",       # WLAN-SSID hier anpassen!
    wifi_password = "wlanpasswort",   # WLAN-Passwort hier anpassen!
    broker_host   = "192.168.1.100",  # MQTT-Broker IP hier anpassen!
    port          = 1883,
)

remote.receive("switch1", bool)


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()

    if remote.is_connected():
        LED_PIN.value(1 if remote.get("switch1", False) else 0)
    else:
        LED_PIN.value(0)

    time.sleep_ms(10)
