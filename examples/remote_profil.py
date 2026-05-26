# =============================================================
#  CCA Remote Beispiel: Remote Profil
#  Das Profil-Layout wird direkt im Code eingebettet –
#  die App erstellt es beim ersten Verbinden automatisch.
#  Ein Slider steuert die LED-Helligkeit, ein Display
#  zeigt den aktuellen Prozentwert an.
# =============================================================
#  Erfordert die kostenlose CCA Remote App (Android / iOS)
#  Raspberry Pi Pico 2 W or ESP32  |  MicroPython ≥ 1.23
# =============================================================

from machine import Pin, PWM
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

# PWM-LED an GP15 – die Onboard-LED unterstützt kein PWM
LED = PWM(Pin(15))
LED.freq(1000)

# Profil-String – erzeugt in der App unter Profil → Exportieren → „Als Arduino-String kopieren".
PROFILE = (
    "v:3"
    "|nm:LED Demo"
    "|lb:titel:LED Helligkeit:fs=22:b=1:c=FF2196F3"
    "@0.0000,0.0000,400.0000,44.0000,0.0000,0.0000,400.0000,44.0000"
    "|sl:helligkeit:0:255:sv=1:c=FF2196F3"
    "@0.0400,0.1143,370.0000,100.0000,0.0400,0.1143,370.0000,100.0000"
    "|di:anzeige:lb=Helligkeit:u=%"
    "@0.0400,0.3143,180.0000,60.0000,0.0400,0.3143,180.0000,60.0000"
)


# ---------------------------------------------------------------- #
#  Setup                                                            #
# ---------------------------------------------------------------- #
remote.set_profile(PROFILE)  # Profil einbetten – wird beim Verbinden an die App übertragen
remote.begin()

remote.receive("helligkeit", int)  # Slider-Wert: 0 – 255


# ---------------------------------------------------------------- #
#  Hauptschleife                                                    #
# ---------------------------------------------------------------- #
while True:
    remote.handle()     # Empfangene Befehle verarbeiten (erforderlich!)

    if remote.is_connected():
        helligkeit = remote.get("helligkeit", 0)

        # LED-Helligkeit via PWM steuern (0–255 → 0–65535)
        LED.duty_u16(helligkeit * 257)

        # Prozentwert an Display-Element der App senden
        remote.send("anzeige", helligkeit * 100 // 255)
    else:
        LED.duty_u16(0)

    time.sleep_ms(10)
