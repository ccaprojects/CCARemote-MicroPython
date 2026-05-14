# CCARemote/wifi.py – WiFi Access Point + HTTP/TCP-Server Implementation
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
    """WiFi Access Point + HTTP/TCP-Server für den Raspberry Pi Pico 2 W.

    Der Pico 2 W öffnet einen eigenen WLAN-Hotspot.
    Die CCA Remote App verbindet sich mit diesem Hotspot und kommuniziert
    über eine persistente TCP-Verbindung (Port 81, KEY:VALUE\\n Protokoll):

        App → Pico:  "element_id:wert\\n"   (Kommando)
        Pico → App:  "key:wert\\n"           (Display-Push)

    Zusätzlich läuft ein HTTP-Server auf Port 80 für Browser-Zugriff
    und Device-Discovery (GET /status, GET /).

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
        self._server_socket     = None
        self._wifi_enabled      = False
        self._prev_connected    = False
        self._tcp_server_socket = None
        self._tcp_client        = None
        self._tcp_buf           = ""

    # ---------------------------------------------------------------- #
    #  Öffentliche Methoden                                             #
    # ---------------------------------------------------------------- #

    def begin(self, wifi_password=""):
        """Startet den WiFi Access Point, HTTP-Server (Port 80) und TCP-Server (Port 81).

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

        # Non-blocking HTTP-Server auf Port 80 (Browser + Device-Discovery)
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(("", 80))
        self._server_socket.listen(5)
        self._server_socket.setblocking(False)
        print("HTTP Server läuft auf Port 80")

        # Persistenter TCP-Server auf Port 81 (App-Kommunikation)
        self._tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_server_socket.bind(("", 81))
        self._tcp_server_socket.listen(1)
        self._tcp_server_socket.setblocking(False)
        print("TCP Server läuft auf Port 81")

        print("CCA Remote bereit!\n")

    def handle(self):
        """Muss in der Hauptschleife aufgerufen werden!
        Verarbeitet HTTP-Anfragen (Port 80) und TCP-Kommandos (Port 81).
        """
        if not self._wifi_enabled or self._server_socket is None:
            return

        # Verbindungsstatus überwachen und im Debug-Modus ausgeben
        now_connected = self.is_connected()
        if now_connected != self._prev_connected:
            self._prev_connected = now_connected
            if self._debug_mode:
                print("[CCA]", "Verbindung hergestellt" if now_connected else "Verbindung getrennt")

        # --- HTTP Port 80: alle ausstehenden Verbindungen abarbeiten ---
        while True:
            try:
                conn, addr = self._server_socket.accept()
            except OSError:
                break

            try:
                conn.settimeout(0.1)
                data = conn.recv(2048)
                if data:
                    request = data.decode("utf-8", "ignore")
                    if "\r\n\r\n" in request:
                        header_part, body_part = request.split("\r\n\r\n", 1)
                        content_length = 0
                        for line in header_part.split("\r\n"):
                            if line.lower().startswith("content-length:"):
                                try:
                                    content_length = int(line.split(":", 1)[1].strip())
                                except ValueError:
                                    pass
                                break
                        while len(body_part.encode("utf-8")) < content_length:
                            chunk = conn.recv(1024)
                            if not chunk:
                                break
                            body_part += chunk.decode("utf-8", "ignore")
                        request = header_part + "\r\n\r\n" + body_part
                    self._handle_request(conn, request)
            except OSError as e:
                if e.args[0] != 110:  # 110 = ETIMEDOUT
                    print("[CCA] HTTP Fehler:", e)
            except Exception as e:
                print("[CCA] HTTP Fehler:", e)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        # --- TCP Port 81: neuen Client annehmen ---
        if self._tcp_client is None and self._tcp_server_socket:
            try:
                conn, _ = self._tcp_server_socket.accept()
                conn.setblocking(False)
                self._tcp_client = conn
                self._tcp_buf = ""
                # Resync: alle aktuellen Display-Werte senden
                for k, v in self._display_values.items():
                    try:
                        conn.sendall("{}:{}\n".format(k, v).encode())
                    except OSError:
                        break
                if self._debug_mode:
                    print("[CCA] TCP Client verbunden")
            except OSError:
                pass

        # --- TCP Port 81: Daten lesen ---
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
                    self._tcp_disconnect()  # sauberes TCP-Close
            except OSError as e:
                if e.args[0] not in (11, 35):  # EAGAIN/EWOULDBLOCK = kein Fehler
                    self._tcp_disconnect()

    def is_connected(self):
        """Gibt True zurück wenn die App per TCP verbunden ist."""
        return self._tcp_client is not None

    # ---------------------------------------------------------------- #
    #  HTTP-Handler                                                     #
    # ---------------------------------------------------------------- #

    def _handle_request(self, conn, request):
        """Parst die HTTP-Anfrage und leitet an den passenden Handler weiter."""
        lines = request.split("\r\n")
        if not lines:
            return
        first = lines[0].split(" ")
        if len(first) < 2:
            return

        method    = first[0]
        raw_path  = first[1]
        path      = raw_path.split("?")[0]
        query     = raw_path[len(path) + 1:] if "?" in raw_path else ""

        if method == "GET" and path == "/":
            self._send_root(conn)
        elif method == "GET" and path == "/status":
            self._send_status(conn)
        elif path == "/command":
            body = ""
            if method == "POST":
                if "\r\n\r\n" in request:
                    body = request.split("\r\n\r\n", 1)[1].strip()
                elif "\n\n" in request:
                    body = request.split("\n\n", 1)[1].strip()
            elif method == "GET" and query:
                body = ",".join(p.replace("=", ":", 1) for p in query.split("&") if p)
            if body and body != "disconnect:1":
                self._process_command(body)
            self._send_json(conn, '{"status":"ok"}')
        elif method == "GET" and path == "/display":
            self._send_display(conn)
        else:
            self._send_response(conn, 404, "text/plain", "Not Found")

    def _send_root(self, conn):
        ip      = self._ap.ifconfig()[0] if self._ap else "?"
        clients = 0
        try:
            clients = len(self._ap.status("stations"))
        except Exception:
            pass
        html = (
            "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
            "<title>{n}</title></head><body>"
            "<h1>{n}</h1>"
            "<p>CCA Remote WiFi läuft</p>"
            "<p>IP: {ip}</p>"
            "<p>Verbundene Geräte: {c}</p>"
            "<p>TCP-Client: {tc}</p>"
            "<hr>"
            "<p><strong>TCP Port 81</strong> &ndash; KEY:VALUE\\n (App-Verbindung)</p>"
            "<p><strong>GET /status</strong> &ndash; Device-Info</p>"
            "</body></html>"
        ).format(n=self._device_name, ip=ip, c=clients,
                 tc="verbunden" if self._tcp_client else "getrennt")
        self._send_response(conn, 200, "text/html", html)

    def _send_status(self, conn):
        self._send_json(conn, '{{"type":"CCARemote","device":"{}"}}'.format(self._device_name))

    def _send_display(self, conn):
        pairs = ['"{}":{}'.format(k, '"{}"'.format(v)) for k, v in self._display_values.items()]
        self._send_json(conn, "{" + ",".join(pairs) + "}")

    def _send_json(self, conn, body):
        self._send_response(conn, 200, "application/json", body)

    def _send_response(self, conn, status, content_type, body):
        status_text = {200: "OK", 400: "Bad Request", 404: "Not Found"}.get(status, "OK")
        body_bytes  = body.encode("utf-8") if isinstance(body, str) else body
        header = (
            "HTTP/1.1 {} {}\r\n"
            "Content-Type: {}; charset=utf-8\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(status, status_text, content_type, len(body_bytes))
        try:
            conn.sendall(header.encode("utf-8") + body_bytes)
        except Exception as e:
            print("[CCA] HTTP Antwort-Fehler:", e)

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
        """Pusht Wert per TCP; speichert ihn immer für HTTP /display."""
        self._display_values[key] = value
        if self._tcp_client:
            try:
                self._tcp_client.sendall("{}:{}\n".format(key, value).encode())
            except OSError:
                self._tcp_disconnect()
