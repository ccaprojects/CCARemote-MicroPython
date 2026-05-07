# =================================
#  CCA Remote – Profil: Standard
#  Generiert von der CCA Remote App
# =================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W  |  MicroPython ≥ 1.23
# =================================

from CCARemote.ble import CCARemoteBLE
from machine import Pin, PWM
import time
import random

# Für WiFi-Verbindung stattdessen:
# from CCARemote.wifi import CCARemoteWiFi
# remote = CCARemoteWiFi("Pico-MeinWiFi")  # Namen hier anpassen!

remote = CCARemoteBLE("Pico-MeinBLE")   # Namen hier anpassen!

# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.debug()          # Debug-Modus aktivieren – vor begin() aufrufen!
remote.begin("1234")    # Initialisierung mit optionalem Passwort

# Element-IDs mit Typen verknüpfen:
#   remote.receive("Element-ID aus der App", typ)
# Werte abrufen mit: remote.get("Element-ID", standardwert)
# Hinweis: Element-ID und Variablenname können unterschiedlich sein!
remote.receive("button1", bool)   # Button (True = gedrückt)
remote.receive("slider1", int)    # Slider (0 – 255)
remote.receive("switch1", bool)   # Switch (True = ein; False = aus)

LED_PIN = PWM(Pin(18))
LED_PIN.freq(1000)

# Zeitsteuerung
previous_millis = 0
interval = 1000   # Intervall in Millisekunden (1 Sekunde)

# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()   # Empfangene Befehle verarbeiten (erforderlich!)

    if remote.is_connected():
        current_millis = time.ticks_ms()

        if time.ticks_diff(current_millis, previous_millis) >= interval:
            previous_millis = current_millis

            # Zufälligen Float-Wert zwischen 2.0 und 5.0 erzeugen
            chart1 = random.randint(200, 500) / 100.0
            remote.send("chart1", chart1)

            fill1 = random.randint(0, 10000) / 100.0
            remote.send("fill1", fill1)

        # Werte an die App senden:
        #   remote.send("Element-ID aus der App", wert)

        # Hier eigenen Code einfügen ...
        switch1 = remote.get("switch1", False)
        slider1 = remote.get("slider1", 0)

        if switch1:
            LED_PIN.duty_u16(slider1 * 257)   # 0–255 → 0–65535
        else:
            LED_PIN.duty_u16(0)

    else:
        LED_PIN.duty_u16(0)

    time.sleep_ms(10)
