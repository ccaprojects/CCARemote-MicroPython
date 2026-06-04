# CCARemote/wifi.py – WiFi Access Point + TCP-Server Implementation
#
# Handles WiFi Access Point advertising, connection management
# and data transfer for the CCARemote App for remote control.
#
# Developed by A. Eckhart (HTL Anichstraße) - MIT – see LICENSE
#
# Requirements:
#   Raspberry Pi Pico 2 W or ESP32 with MicroPython >= 1.23
#   The network module is included in the standard firmware.

import network
import socket
import time
from . import CCARemote, CCA_DEBUG_ALL, CCA_PROTOCOL_VERSION, __version__


class CCARemoteWiFi(CCARemote):
    """WiFi Access Point + TCP-Server für den Raspberry Pi Pico 2 W.

    Der Pico 2 W öffnet einen eigenen WLAN-Hotspot.
    Die CCA Remote App verbindet sich mit diesem Hotspot und kommuniziert
    über eine persistente TCP-Verbindung auf Port 4210:

        App → Pico:  "element_id:wert\\n"   (Kommando)
        Pico → App:  "key:wert\\n"           (Display-Push)

    Beispiel (empfohlene Verwendung mit create_remote):
        from CCARemote import CCA_WIFI, CCA_DEBUG_ALL, create_remote

        DEVICE_NAME = "MeinPico"
        CONNECTION  = CCA_WIFI
        PASSWORD    = ""
        DEBUG_LEVEL = CCA_DEBUG_ALL

        remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL)
        remote.begin()
        remote.receive("switch1", bool)

        while True:
            remote.handle()
            if remote.is_connected():
                led.value(1 if remote.get("switch1", False) else 0)
    """

    def __init__(self, name, prefix="CCA-", password="", port=4210, debug_level=0, show_timestamp=True, persist=True):
        super().__init__(name, prefix, debug_level, show_timestamp, persist)
        self._password          = password
        self._port              = port
        self._ap                = None
        self._wifi_enabled      = False
        self._prev_connected    = False
        self._tcp_server_socket = None
        self._tcp_client        = None
        self._tcp_buf           = ""
        self._last_rx_ms        = 0

    # ---------------------------------------------------------------- #
    #  Öffentliche Methoden                                             #
    # ---------------------------------------------------------------- #

    def begin(self):
        """Startet den WiFi Access Point und den TCP-Server.

        Passwort, Port und Debug-Level werden über den Konstruktor oder create_remote() gesetzt.
        """
        print("\n" + self._ts() + "CCA Remote startet (WiFi)...")
        if self._debug_mode == CCA_DEBUG_ALL:
            print(self._ts() + "[CCA] Library: {}  |  Protokoll: {}".format(__version__, CCA_PROTOCOL_VERSION))

        print(self._ts() + "Gerätename: " + self._device_name)

        self._ap = network.WLAN(network.WLAN.IF_AP)
        self._ap.active(False)
        time.sleep(0.5)

        cfg = dict(ssid=self._device_name, channel=6)
        if self._password:
            cfg["password"] = self._password
            cfg["security"] = network.WLAN.SEC_WPA_WPA2
        else:
            cfg["security"] = 0
        self._ap.config(**cfg)

        self._ap.active(True)
        while not self._ap.active():
            time.sleep(0.1)

        self._wifi_enabled = True
        ip = self._ap.ifconfig()[0]
        enc = "WPA2" if self._password else "offen"
        print(self._ts() + "WiFi AP: {} ({})".format(self._device_name, enc))
        if self._password:
            pwd = self._password if self._debug_mode == CCA_DEBUG_ALL else "*" * len(self._password)
            print(self._ts() + "WiFi Passwort: " + pwd)
        print(self._ts() + "IP-Adresse: " + ip)

        self._tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_server_socket.bind(("", self._port))
        self._tcp_server_socket.listen(1)
        self._tcp_server_socket.setblocking(False)
        print(self._ts() + "TCP Server läuft auf Port " + str(self._port))

        print(self._ts() + "CCA Remote bereit!\n")
        self._load_state()

    def handle(self):
        """Muss in der Hauptschleife aufgerufen werden!
        Nimmt eingehende TCP-Verbindungen an und verarbeitet Kommandos.
        """
        self._check_watchdogs()
        if not self._wifi_enabled or self._tcp_server_socket is None:
            return

        # Aktivitäts-Timeout: kein Ping/Daten seit 2500 ms → Verbindung tot
        if self._tcp_client is not None and self._last_rx_ms > 0:
            if time.ticks_diff(time.ticks_ms(), self._last_rx_ms) >= 2500:
                self._fire_all_watchdogs()
                self._tcp_disconnect()

        # Verbindungsstatus überwachen und im Debug-Modus ausgeben
        now_connected = self.is_connected()
        if now_connected != self._prev_connected:
            self._prev_connected = now_connected
            if not now_connected:
                self._fire_all_watchdogs()
            if self._debug_mode:
                print(self._ts() + ("[CCA] Verbindung hergestellt" if now_connected else "[CCA] Verbindung getrennt"))

        # Neuen TCP-Client annehmen
        if self._tcp_client is None:
            try:
                conn, _ = self._tcp_server_socket.accept()
                conn.setblocking(False)
                self._tcp_client = conn
                self._tcp_buf    = ""
                self._last_rx_ms = time.ticks_ms()
                self._reset_watchdog_timers()
                self._resync_display()
            except OSError:
                pass

        # Eingehende Zeilen lesen
        if self._tcp_client is not None:
            try:
                chunk = self._tcp_client.recv(256)
                if chunk:
                    self._tcp_buf += chunk.decode("utf-8", "ignore")
                    while "\n" in self._tcp_buf:
                        line, self._tcp_buf = self._tcp_buf.split("\n", 1)
                        line = line.strip()
                        if line == "disconnect:1":
                            self._tcp_disconnect()
                            break
                        elif line.startswith("ping:") or line == "ping":
                            self._last_rx_ms = time.ticks_ms()
                        elif line:
                            self._last_rx_ms = time.ticks_ms()
                            self._process_command(line)
                else:
                    self._tcp_disconnect()
            except OSError as e:
                if e.args[0] not in (11, 35):  # EAGAIN/EWOULDBLOCK = kein Fehler
                    self._tcp_disconnect()

    def is_connected(self):
        """Gibt True zurück wenn die App per TCP verbunden ist."""
        return self._tcp_client is not None

    # ---------------------------------------------------------------- #
    #  Interne Methoden                                                 #
    # ---------------------------------------------------------------- #

    def _tcp_disconnect(self):
        if self._tcp_client:
            self._save_state()
            try:
                self._tcp_client.close()
            except Exception:
                pass
            self._tcp_client = None
        self._tcp_buf    = ""
        self._last_rx_ms = 0

    def _send_internal(self, key, value):
        """Pusht Wert per TCP; speichert ihn für spätere Resync."""
        self._display_values[key] = value
        if self._tcp_client:
            try:
                self._tcp_client.sendall("{}:{}\n".format(key, value).encode())
            except OSError:
                self._tcp_disconnect()
