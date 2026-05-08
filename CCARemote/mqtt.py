# CCARemote/mqtt.py – MQTT-Client Implementation
#
# Handles MQTT support for the CCARemote App for remote control.
#
# Developed by Andreas E.
# Version: 1.0.0 | 2026-05-07 | MIT – see LICENSE
#
# Requirements:
#   Raspberry Pi Pico 2 W with MicroPython >= 1.23
#   The umqtt.simple module is included in the standard firmware.
#   If not available:
#     import mip
#     mip.install("umqtt.simple")

import network
import time
from . import CCARemote

try:
    from umqtt.simple import MQTTClient as _MQTTClient
    _UMQTT_OK = True
except ImportError:
    _UMQTT_OK = False


class CCARemoteMQTT(CCARemote):
    """MQTT-Client für den Raspberry Pi Pico 2 W.

    Der Pico 2 W verbindet sich mit einem vorhandenen WLAN (Station-Modus)
    und kommuniziert über einen MQTT-Broker.

    Topics:
        cca/<gerätename>/cmd      – App → Pico  (subscribe)
        cca/<gerätename>/display  – Pico → App  (publish)

    Beispiel:
        from CCARemote.mqtt import CCARemoteMQTT

        remote = CCARemoteMQTT("MeinPico")
        remote.begin("MeinWLAN", "wlanpasswort", "192.168.1.100")
        remote.receive("switch1", bool)

        while True:
            remote.handle()
            if remote.is_connected():
                led.value(1 if remote.get("switch1", False) else 0)
    """

    def __init__(self, name, prefix="CCA-"):
        super().__init__(name, prefix)
        self._wlan             = None
        self._mqtt             = None
        self._broker_host      = ""
        self._broker_port      = 1883
        self._topic_command    = b""
        self._topic_display    = b""
        self._last_reconnect   = 0

    # ---------------------------------------------------------------- #
    #  Öffentliche Methoden                                             #
    # ---------------------------------------------------------------- #

    def begin(self, wifi_ssid, wifi_password, broker_host, port=1883):
        """Verbindet mit WiFi (Station-Modus) und MQTT-Broker.

        Args:
            wifi_ssid:     SSID des vorhandenen WLANs
            wifi_password: WLAN-Passwort
            broker_host:   IP-Adresse oder Hostname des MQTT-Brokers
            port:          MQTT-Port (Standard: 1883)
        """
        if not _UMQTT_OK:
            raise RuntimeError(
                "umqtt.simple nicht verfügbar!\n"
                "Installiere mit: import mip; mip.install('umqtt.simple')"
            )

        self._broker_host = broker_host
        self._broker_port = port

        print("\nCCA Remote startet (MQTT)...")
        print("Gerätename:", self._device_name)

        self._connect_wifi(wifi_ssid, wifi_password)

        self._topic_command = ("cca/" + self._device_name + "/cmd").encode()
        self._topic_display = ("cca/" + self._device_name + "/display").encode()

        print("MQTT Broker:", broker_host + ":" + str(port))
        print("Befehl-Topic: ", self._topic_command.decode())
        print("Display-Topic:", self._topic_display.decode())

        while not self._connect_mqtt():
            print("Erneuter Versuch in 2 s...")
            time.sleep(2)

        print("CCA Remote bereit!\n")

    def handle(self):
        """Muss in der Hauptschleife aufgerufen werden!
        Verarbeitet eingehende MQTT-Nachrichten und sendet bei Verbindungsverlust
        automatisch einen Reconnect-Versuch (alle 5 s).
        """
        if self._mqtt is None:
            return

        try:
            self._mqtt.check_msg()
        except Exception:
            # Verbindung verloren – Reconnect versuchen
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_reconnect) >= 5000:
                self._last_reconnect = now
                try:
                    self._connect_mqtt()
                except Exception:
                    pass
            return

        if self._command_received:
            self._process_command(self._last_command)
            self._command_received = False

    def is_connected(self):
        """Gibt True zurück wenn eine MQTT-Verbindung besteht."""
        return self._mqtt is not None

    # ---------------------------------------------------------------- #
    #  Interne Methoden                                                 #
    # ---------------------------------------------------------------- #

    def _connect_wifi(self, ssid, password):
        """Verbindet mit dem angegebenen WLAN (Station-Modus)."""
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(True)
        if self._wlan.isconnected():
            print("WiFi bereits verbunden, IP:", self._wlan.ifconfig()[0])
            return

        print("Verbinde mit WiFi:", ssid, end="")
        self._wlan.connect(ssid, password)
        for _ in range(30):            # max. 15 s warten
            if self._wlan.isconnected():
                break
            time.sleep(0.5)
            print(".", end="")
        print()

        if not self._wlan.isconnected():
            raise RuntimeError("WiFi-Verbindung fehlgeschlagen! SSID/Passwort prüfen.")

        print("WiFi verbunden, IP:", self._wlan.ifconfig()[0])

    def _connect_mqtt(self):
        """Baut die MQTT-Verbindung auf und abonniert das Befehls-Topic."""
        try:
            print("Verbinde mit MQTT Broker...", end="")
            self._mqtt = _MQTTClient(
                client_id=self._device_name,
                server=self._broker_host,
                port=self._broker_port,
                keepalive=60,
            )
            self._mqtt.set_callback(self._mqtt_callback)
            self._mqtt.connect()
            self._mqtt.subscribe(self._topic_command)
            print(" verbunden!")
            return True
        except Exception as e:
            print(" Fehler:", e)
            self._mqtt = None
            return False

    def _mqtt_callback(self, topic, msg):
        """Wird aufgerufen wenn eine MQTT-Nachricht auf dem Befehls-Topic eintrifft."""
        self._last_command     = msg.decode("utf-8", "ignore")
        self._command_received = True

    def _send_internal(self, key, value):
        """Veröffentlicht einen Wert auf dem Display-Topic."""
        if self._mqtt is not None:
            self._display_values[key] = value
            payload = (key + ":" + value).encode("utf-8")
            try:
                self._mqtt.publish(self._topic_display, payload)
            except Exception as e:
                print("[CCA] MQTT Sendefehler:", e)
                self._mqtt = None  # Reconnect beim nächsten handle() auslösen
