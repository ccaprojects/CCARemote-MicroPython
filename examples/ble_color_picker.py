# =============================================================
#  CCA Remote Beispiel: Color Picker (BLE)
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

from CCARemote.ble import CCARemoteBLE
remote = CCARemoteBLE("MeinName")  # Namen hier anpassen!

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
remote.debug()   # Debug-Modus aktivieren (optional)
remote.begin()   # BLE starten

# Element-ID "color1" aus der App registrieren
# Die Element-ID muss mit der ID in der App übereinstimmen
remote.receive_color("color1")


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()  # Empfangene Befehle verarbeiten (erforderlich!)

    if remote.is_connected():
        # Farbwerte als Tuple (r, g, b) abrufen
        r, g, b = remote.get_color("color1")

        # RGB-LED ansteuern
        led_r.duty_u16(r * 257)
        led_g.duty_u16(g * 257)
        led_b.duty_u16(b * 257)

    else:
        # LED ausschalten wenn keine Verbindung
        for led in (led_r, led_g, led_b):
            led.duty_u16(0)

    time.sleep_ms(10)
