# =============================================================
#  CCA Remote Beispiel: Joystick Element mit Watchdog (WiFi)
#  Ein Joystick in der App steuert zwei PWM-Ausgänge (z.B.
#  Motoren eines RC-Fahrzeugs). Der Watchdog stoppt die Motoren
#  automatisch wenn die Verbindung unterbrochen wird.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =============================================================

from machine import Pin, PWM
import time

# Für WiFi-Verbindung:
from CCARemote.wifi import CCARemoteWiFi
remote = CCARemoteWiFi("MeinName")  # Namen hier anpassen!

# Für BLE-Verbindung stattdessen:
# from CCARemote.ble import CCARemoteBLE
# remote = CCARemoteBLE("MeinName")

MOTOR_A = PWM(Pin(18))  # PWM-Pin Motor A (z.B. Vorwärts / Rückwärts)
MOTOR_B = PWM(Pin(19))  # PWM-Pin Motor B (z.B. Links / Rechts)
MOTOR_A.freq(1000)
MOTOR_B.freq(1000)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.debug()           # Debug-Modus: CCA_DEBUG_IN, CCA_DEBUG_OUT oder CCA_DEBUG_ALL
remote.begin()           # WiFi-Hotspot starten (kein Passwort = offenes Netzwerk)
# remote.begin("geheim1234")  # Mit WPA2-Passwort (min. 8 Zeichen)

# Die Element-IDs aus der App werden mit Typen verknüpft.
# Werte abrufen mit: remote.get("Element-ID")
remote.receive("axisX", int)   # Joystick X  (-255 bis +255)
remote.receive("axisY", int)   # Joystick Y  (-255 bis +255)

# Watchdog: axisX und axisY werden auf 0 gesetzt wenn die App
# länger als 500 ms keine Werte sendet (z.B. bei Verbindungsverlust).
# So bleibt das Fahrzeug zuverlässig stehen wenn der Finger losgelassen
# wird oder die Verbindung abbricht.
remote.watchdog("axisX", 500)
remote.watchdog("axisY", 500)


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()     # Empfangene Befehle verarbeiten (erforderlich!)

    if remote.is_connected():
        axis_x = remote.get("axisX", 0)
        axis_y = remote.get("axisY", 0)

        # axisX / axisY: -255 bis +255 → duty_u16 erwartet 0 bis 65535
        # abs() liefert den Betrag; das Vorzeichen bestimmt die Richtung.
        MOTOR_A.duty_u16(abs(axis_y) * 257)  # Throttle
        MOTOR_B.duty_u16(abs(axis_x) * 257)  # Lenkung
    else:
        MOTOR_A.duty_u16(0)
        MOTOR_B.duty_u16(0)

    time.sleep_ms(10)
