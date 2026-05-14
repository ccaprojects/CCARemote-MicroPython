# CCARemote/wifi.py – WiFi Access Point + TCP-Server Implementation
#
# Handles WiFi Access Point advertising, connection management
# and data transfer for the CCARemote App for remote control.
#
# Developed by A. Eckhart (HTL Anichstraße) - MIT – see LICENSE
#
# Requirements:
#   Raspberry Pi Pico 2 W with MicroPython >= 1.23
#   The network module is included in the standard firmware.

import network
import socket
import time
from . import CCARemote


class CCARemoteWiFi(CCARemote):
    """WiFi Access Point + TCP-Server für den Raspberry Pi Pico 2 W.

    Der Pico 2 W öffnet einen eigenen WLAN-Hotspot.
    Die CCA Remote App verbindet sich mit diesem Hotspot und kommuniziert
    über eine persistente TCP-Verbindung auf Port 81:

        App → Pico:  "element_id:wert\\n"   (Kommando)
        Pico → App:  "key:wert\\n"           (Display-Push)

    Beispiel:
        from CCARemote.wifi import CCARemoteWiFi

        remote = CCARemoteWiFi("MeinPico")
        remote.begin("geheim1234")
        remote.receive("switch1", bool)

        while True:
            remote.handle()
            if remote.is_connected():
                led.value(1 if remote.get("switch1", False) else 0)
    """

    def __init__(self, name, prefix="CCA-"):
        super().__init__(name, prefix)
        self._ap                = None
        self._wifi_enabled      = False
        self._prev_connected    = False
        self._tcp_server_socket = None
        self._tcp_client        = None
        self._tcp_buf           = ""

    # ---------------------------------------------------------------- #
    #  Öffentliche Methoden                                             #
    # ---------------------------------------------------------------- #

    def begin(self, wifi_password=""):
        """Startet den WiFi Access Point und den TCP-Server auf Port 81.

        Args:
            wifi_password: WLAN-Passwort (leer = offenes Netzwerk, sonst WPA2).
        """
        print("\nCCA Remote startet (WiFi)...")
        print("Gerätename:", self._device_name)

        self._ap = network.WLAN(network.WLAN.IF_AP)
        self._ap.active(False)
        time.sleep(0.5)

        cfg = dict(ssid=self._device_name, channel=6)
        if wifi_password:
            cfg["password"] = wifi_password
            cfg["security"] = network.WLAN.SEC_WPA_WPA2
        else:
            cfg["security"] = 0
        self._ap.config(**cfg)

        self._ap.active(True)
        while not self._ap.active():
            time.sleep(0.1)

        self._wifi_enabled = True
        ip = self._ap.ifconfig()[0]
        enc = "WPA2" if wifi_password else "offen"
        print("WiFi AP:", self._device_name, "(" + enc + ")")
        print("IP-Adresse:", ip)

        self._tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_server_socket.bind(("", 81))
        self._tcp_server_socket.listen(1)
        self._tcp_server_socket.setblocking(False)
        print("TCP Server läuft auf Port 81")

        print("CCA Remote bereit!\n")

    def handle(self):
        """Muss in der Hauptschleife aufgerufen werden!
        Nimmt eingehende TCP-Verbindungen an und verarbeitet Kommandos.
        """
        if not self._wifi_enabled or self._tcp_server_socket is None:
            return

        # Verbindungsstatus überwachen und im Debug-Modus ausgeben
        now_connected = self.is_connected()
        if now_connected != self._prev_connected:
            self._prev_connected = now_connected
            if self._debug_mode:
                print("[CCA]", "Verbindung hergestellt" if now_connected else "Verbindung getrennt")

        # Neuen TCP-Client annehmen
        if self._tcp_client is None:
            try:
                conn, _ = self._tcp_server_socket.accept()
                conn.setblocking(False)
                self._tcp_client = conn
                self._tcp_buf = ""
                for k, v in self._display_values.items():
                    try:
                        conn.sendall("{}:{}\n".format(k, v).encode())
                    except OSError:
                        break
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
                        elif line:
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
            try:
                self._tcp_client.close()
            except Exception:
                pass
            self._tcp_client = None
        self._tcp_buf = ""

    def _send_internal(self, key, value):
        """Pusht Wert per TCP; speichert ihn für spätere Resync."""
        self._display_values[key] = value
        if self._tcp_client:
            try:
                self._tcp_client.sendall("{}:{}\n".format(key, value).encode())
            except OSError:
                self._tcp_disconnect()
