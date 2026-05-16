# =============================================================
#  CCA Remote Beispiel: Color Picker
#  Steuert eine RGB-LED mit dem Color-Picker-Element der App.
#
#  Wert-Format der App:  R;G;B  (z.B. "255;128;0")
#  get_color() liefert ein Tuple (r, g, b) mit Werten 0–255.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =============================================================

from machine import PWM, Pin
import time

from CCARemote import CCA_BLE, CCA_WIFI, CCA_DEBUG_OFF, CCA_DEBUG_ALL, create_remote

# ---- Konfiguration – hier anpassen! -----------------------
DEVICE_NAME = "MeinName"    # Gerätename (wird als "CCA-MeinName" angezeigt)
CONNECTION  = CCA_BLE       # CCA_BLE  oder  CCA_WIFI
PASSWORD    = ""            # Passwort (WiFi: min. 8 Zeichen / leer = ohne)
DEBUG_LEVEL = CCA_DEBUG_ALL # CCA_DEBUG_OFF / _IN / _OUT / _ALL

# Optional – nur setzen wenn Standardwert nicht passt:
# DEVICE_PREFIX = "XYZ-"   # Standard: "CCA-"
# TCP_PORT      = 4211      # Standard: 4210  (nur WiFi)
# -----------------------------------------------------------

remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL)

# PWM-Ausgänge für RGB-LED mit gemeinsamer Kathode
# App-Wert 0–255 → duty_u16: 0–65535  (Faktor 257)
led_r = PWM(Pin(13))
led_g = PWM(Pin(14))
led_b = PWM(Pin(15))
for led in (led_r, led_g, led_b):
    led.freq(1000)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.begin()

# Element-ID "color1" aus der App registrieren
remote.receive_color("color1")


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()     # Empfangene Befehle verarbeiten (erforderlich!)

    if remote.is_connected():
        r, g, b = remote.get_color("color1")
        led_r.duty_u16(r * 257)
        led_g.duty_u16(g * 257)
        led_b.duty_u16(b * 257)
    else:
        for led in (led_r, led_g, led_b):
            led.duty_u16(0)

    time.sleep_ms(10)
