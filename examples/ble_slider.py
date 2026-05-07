# =============================================================
#  CCA Remote Beispiel: Slider Element (BLE)
#  Ein Slider in der App steuert die Helligkeit einer LED.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =============================================================

from CCARemote.ble import CCARemoteBLE
from machine import Pin, PWM
import time

# Für WiFi-Verbindung stattdessen:
# from CCARemote.wifi import CCARemoteWiFi
# remote = CCARemoteWiFi("MeinName")

remote = CCARemoteBLE("MeinName")   # Namen hier anpassen!

# PWM-fähiger Pin für LED-Dimmung
# Alle GPIO-Pins des Pico 2 W unterstützen PWM.
LED_PIN = PWM(Pin(15))
LED_PIN.freq(1000)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.debug()
remote.begin()

# Slider liefert Werte 0 – 255 (Bereich in der App einstellbar)
remote.receive("slider1", int)


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()

    if remote.is_connected():
        helligkeit = remote.get("slider1", 0)
        # Pico 2 W PWM: 16-bit Auflösung (0 – 65535)
        # App-Wert 0–255 → duty_u16: 0–65535
        LED_PIN.duty_u16(helligkeit * 257)
    else:
        LED_PIN.duty_u16(0)

    time.sleep_ms(10)
