# CCARemote/wifi.py – WiFi Access Point + HTTP-Server Implementierung
#
# Basierend auf der Diplomarbeit von L. Eder und E. Duyar (HTL Anichstraße)
# Erweitert von A. Eckhart mit freundlicher Genehmigung der Originalautoren.
#
# Version: 1.0.0 | 2026-05-07 | MIT – siehe LICENSE
#
# Voraussetzung:
#   Raspberry Pi Pico 2 W mit MicroPython ≥ 1.23
#   Die Module network und socket sind im Standard-Firmware enthalten.

import network
import socket
import time
from . import CCARemote


class CCARemoteWiFi(CCARemote):
    """WiFi Access Point + HTTP-Server für den Raspberry Pi Pico 2 W.

    Der Pico 2 W öffnet einen eigenen WLAN-Hotspot.
    Die CCA Remote App verbindet sich mit diesem Hotspot und kommuniziert
    über ein simples HTTP-Protokoll:

        POST /command  – Body: "element_id:wert"  (App → Pico)
        GET  /display  – JSON mit Display-Werten   (Pico → App)

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
        self._ap             = None
        self._server_socket  = None
        self._wifi_enabled   = False
        self._prev_connected = False

    # ---------------------------------------------------------------- #
    #  Öffentliche Methoden                                             #
    # ---------------------------------------------------------------- #

    def begin(self, wifi_password=""):
        """Startet den WiFi Access Point und den HTTP-Server auf Port 80.

        Args:
            wifi_password: WLAN-Passwort (leer = offenes Netzwerk).
        """
        print("\nCCA Remote startet (WiFi)...")
        print("Gerätename:", self._device_name)

        self._ap = network.WLAN(network.AP_IF)
        self._ap.active(False)
        time.sleep(0.3)
        self._ap.active(True)

        if wifi_password:
            # WPA2-PSK (security=4)
            self._ap.config(ssid=self._device_name, password=wifi_password, security=4)
        else:
            self._ap.config(ssid=self._device_name, security=0)

        # Warten bis AP aktiv ist (max. 10 s)
        for _ in range(20):
            if self._ap.active():
                break
            time.sleep(0.5)

        if not self._ap.active():
            print("WiFi AP Start fehlgeschlagen!")
            return

        self._wifi_enabled = True
        ip = self._ap.ifconfig()[0]
        print("WiFi AP:", self._device_name)
        print("IP-Adresse:", ip)
        if wifi_password:
            print("Passwort:", wifi_password)

        # Non-blocking TCP-Server auf Port 80
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(("", 80))
        self._server_socket.listen(2)
        self._server_socket.setblocking(False)

        print("HTTP Server läuft auf Port 80")
        print("CCA Remote bereit!\n")

    def handle(self):
        """Muss in der Hauptschleife aufgerufen werden!
        Nimmt eingehende HTTP-Anfragen an und verarbeitet sie.
        """
        if not self._wifi_enabled or self._server_socket is None:
            return

        # Verbindungsstatus überwachen und Meldung ausgeben
        now_connected = self.is_connected()
        if now_connected and not self._prev_connected:
            print("Gerät verbunden!")
        elif not now_connected and self._prev_connected:
            print("Gerät getrennt!")
        self._prev_connected = now_connected

        # Alle ausstehenden Verbindungen in einem Durchlauf abarbeiten
        while True:
            try:
                conn, addr = self._server_socket.accept()
            except OSError:
                break  # Keine weiteren ausstehenden Verbindungen

            try:
                conn.settimeout(0.5)
                data = conn.recv(2048)
                if data:
                    request = data.decode("utf-8", "ignore")
                    # Body nachlesen wenn er in einem zweiten Paket kommt
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
                if e.args[0] != 110:  # 110 = ETIMEDOUT (erwartet bei GET ohne Body)
                    print("[CCA] HTTP Fehler:", e)
            except Exception as e:
                print("[CCA] HTTP Fehler:", e)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

    def is_connected(self):
        """Gibt True zurück wenn mindestens ein Gerät mit dem AP verbunden ist."""
        if not self._wifi_enabled or self._ap is None:
            return False
        try:
            return len(self._ap.status("stations")) > 0
        except Exception:
            return self._ap.active()

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
            # Command kann via POST (Body) oder GET (Query-String) kommen
            body = ""
            if method == "POST":
                if "\r\n\r\n" in request:
                    body = request.split("\r\n\r\n", 1)[1].strip()
                elif "\n\n" in request:
                    body = request.split("\n\n", 1)[1].strip()
            elif method == "GET" and query:
                # Query-String "key=value&key2=value2" → "key:value,key2:value2"
                body = ",".join(p.replace("=", ":", 1) for p in query.split("&") if p)
            if body:
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
            "<hr>"
            "<p><strong>POST /command</strong> &ndash; Body: element_id:wert</p>"
            "<p><strong>GET /display</strong> &ndash; JSON mit Display-Werten</p>"
            "</body></html>"
        ).format(n=self._device_name, ip=ip, c=clients)
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

    def _send_internal(self, key, value):
        """Speichert den Wert für GET /display (wird bei nächster Anfrage geliefert)."""
        self._display_values[key] = value
