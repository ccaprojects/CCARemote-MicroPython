# CCARemote/__init__.py – Abstract base class
#
# Usage:
#   from CCARemote import create_remote, CCA_BLE, CCA_WIFI
#
# Developed by A. Eckhart (HTL Anichstraße) - MIT – see LICENSE

import time

# Version der Bibliothek
__version__ = "1.1.1"
# Protokollversion – wird nur bei Breaking Changes erhöht (synchron mit Arduino-Lib und App)
CCA_PROTOCOL_VERSION = "1"
CCA_PLATFORM         = "micropython"

# ------------------------------------------------------------------ #
#  Verbindungstyp-Konstanten                                          #
# ------------------------------------------------------------------ #
CCA_BLE  = 1
CCA_WIFI = 2

# ------------------------------------------------------------------ #
#  Debug-Modus Konstanten (kombinierbar mit |)                        #
# ------------------------------------------------------------------ #
CCA_DEBUG_OFF = 0   # kein Debug-Output
CCA_DEBUG_IN  = 1   # empfangene Werte ausgeben
CCA_DEBUG_OUT = 2   # gesendete Werte ausgeben
CCA_DEBUG_ALL = 3   # empfangene und gesendete Werte ausgeben


class CCARemote:
    """Abstrakte Basisklasse – nicht direkt verwenden!
    Verwende: create_remote(), CCARemoteBLE, CCARemoteWiFi, CCARemoteMQTT
    """

    def __init__(self, name, prefix="CCA-", debug_level=CCA_DEBUG_OFF, show_timestamp=True):
        self._device_name      = prefix + name
        self._debug_mode       = debug_level
        self._show_timestamp   = show_timestamp
        self._command_received = False
        self._last_command     = ""
        # cmd → callback (ohne oder mit Wert-Parameter)
        self._callbacks        = {}
        # cmd → aktueller Wert (für remote.get())
        self._values           = {}
        # key → Anzeige-Wert (für send / /display)
        # Handshake-Keys werden bei jeder Verbindung via _resync_display() gesendet
        self._display_values   = {
            "protocol":   CCA_PROTOCOL_VERSION,
            "platform":   CCA_PLATFORM,
            "libVersion": __version__,
        }
        # Watchdog: cmd → timeout_ms / letzter Update-Zeitstempel / bereits gefeuert
        self._watchdogs        = {}
        self._watchdog_last    = {}
        self._watchdog_fired   = {}
        # Farb-Bindings – Watchdog sendet "0;0;0" statt "0"
        self._color_keys       = set()

    # ---------------------------------------------------------------- #
    #  Öffentliche API                                                  #
    # ---------------------------------------------------------------- #

    def debug(self, mode=CCA_DEBUG_ALL, baud_rate=None):
        """Aktiviert den Debug-Modus.

        Args:
            mode:      CCA_DEBUG_OFF | CCA_DEBUG_IN | CCA_DEBUG_OUT | CCA_DEBUG_ALL
            baud_rate: wird in MicroPython ignoriert (REPL ist immer aktiv)
        """
        self._debug_mode = mode
        msgs = {
            CCA_DEBUG_OFF: "[CCA] Debug-Modus deaktiviert",
            CCA_DEBUG_IN:  "[CCA] Debug-Modus: nur IN",
            CCA_DEBUG_OUT: "[CCA] Debug-Modus: nur OUT",
            CCA_DEBUG_ALL: "[CCA] Debug-Modus: IN + OUT",
        }
        print(self._ts() + msgs.get(mode, "[CCA] Debug-Modus gesetzt"))

    def on_command(self, cmd, callback):
        """Registriert einen Callback für einen Befehl.

        Der Callback kann keinen oder einen Parameter (Wert) haben:
            remote.on_command("btn",    lambda: print("gedrückt"))
            remote.on_command("slider", lambda v: print("Wert:", v))
        """
        self._callbacks[cmd] = callback
        if self._debug_mode != CCA_DEBUG_OFF:
            print("{}Befehl registriert: {}".format(self._ts(), cmd))

    def receive(self, cmd, value_type=str):
        """Verknüpft eine Element-ID mit einem Typ für automatische Konvertierung.

        Werte abrufen mit: remote.get("element_id")

        Args:
            cmd:        Element-ID aus der CCA Remote App
            value_type: Typ für auto. Konvertierung – bool, int, float oder str
        """
        # Standardwert je nach Typ
        default = {bool: False, int: 0, float: 0.0}.get(value_type, "")
        self._values[cmd] = default

        def _handler(value):
            if value_type is bool:
                self._values[cmd] = value in ("1", "true", "on", "True")
            elif value_type is int:
                try:
                    self._values[cmd] = int(value)
                except (ValueError, TypeError):
                    self._values[cmd] = 0
            elif value_type is float:
                try:
                    self._values[cmd] = float(value)
                except (ValueError, TypeError):
                    self._values[cmd] = 0.0
            else:
                self._values[cmd] = value

            if self._debug_mode & CCA_DEBUG_IN:
                print(self._ts() + "[CCA] IN  {} = {}".format(cmd, value))

        self._callbacks[cmd] = _handler
        if self._debug_mode != CCA_DEBUG_OFF:
            print("{}Variable gebunden: {} ({})".format(self._ts(), cmd, value_type.__name__))

    def receive_color(self, cmd):
        """Verknüpft eine Color-Picker-ID für automatische R/G/B-Konvertierung.

        Werte abrufen mit: r, g, b = remote.get_color("color1")

        Wert-Format der App: R;G;B  (z.B. "255;128;0")

        Args:
            cmd: Element-ID des Color-Pickers aus der CCA Remote App
        """
        self._values[cmd] = (0, 0, 0)
        self._color_keys.add(cmd)

        def _handler(value):
            try:
                parts = value.split(";")
                r = max(0, min(255, int(parts[0]))) if len(parts) > 0 else 0
                g = max(0, min(255, int(parts[1]))) if len(parts) > 1 else 0
                b = max(0, min(255, int(parts[2]))) if len(parts) > 2 else 0
                self._values[cmd] = (r, g, b)
            except (ValueError, IndexError):
                self._values[cmd] = (0, 0, 0)

            if self._debug_mode & CCA_DEBUG_IN:
                r_v, g_v, b_v = self._values[cmd]
                print(self._ts() + "[CCA] IN  {} = R:{} G:{} B:{}".format(cmd, r_v, g_v, b_v))

        self._callbacks[cmd] = _handler
        if self._debug_mode != CCA_DEBUG_OFF:
            print("{}Farbe gebunden: {} (r,g,b)".format(self._ts(), cmd))

    def get_color(self, cmd, default=(0, 0, 0)):
        """Gibt den zuletzt empfangenen RGB-Farbwert zurück.

        Returns:
            Tuple (r, g, b) mit Ganzzahlen 0–255

        Beispiel:
            r, g, b = remote.get_color("color1")
            led_r.duty_u16(r * 257)
        """
        return self._values.get(cmd, default)

    def watchdog(self, cmd, timeout_ms):
        """Setzt cmd automatisch auf 0 wenn es länger als timeout_ms ms nicht aktualisiert wurde.

        Typischer Anwendungsfall: Joystick-Achsen bei RC-Fahrzeugen.

        Beispiel:
            remote.watchdog("axisX", 500)
            remote.watchdog("axisY", 500)
        """
        self._watchdogs[cmd]      = timeout_ms
        self._watchdog_last[cmd]  = time.ticks_ms()
        self._watchdog_fired[cmd] = False

    def get(self, cmd, default=None):
        """Gibt den zuletzt empfangenen Wert für eine Element-ID zurück.

        Args:
            cmd:     Element-ID aus der App
            default: Rückgabewert wenn noch kein Wert empfangen wurde

        Beispiel:
            helligkeit = remote.get("slider1", 0)
        """
        return self._values.get(cmd, default)

    def send(self, key, value=None, decimals=None):
        """Sendet einen Wert an ein Display-Element der App.

        Varianten:
            remote.send("display1", 42)
            remote.send("display1", 3.14)
            remote.send("display1", 3.14, decimals=2)
            remote.send("display1:42")   # String-Form
        """
        if value is None:
            colon = key.find(":")
            if colon > 0:
                self._send_if_changed(key[:colon], key[colon + 1:])
            else:
                self._send_if_changed(key, "")
        else:
            if isinstance(value, float):
                d = decimals if decimals is not None else 1
                str_val = "{:.{}f}".format(value, d)
            else:
                str_val = str(value)
            self._send_if_changed(key, str_val)

    def send_always(self, key, value=None, decimals=None):
        """Wie send(), aber sendet auch bei unverändertem Wert (für Charts)."""
        if value is None:
            colon = key.find(":")
            if colon > 0:
                self._display_values[key[:colon]] = key[colon + 1:]
                self._send_internal(key[:colon], key[colon + 1:])
            else:
                self._send_internal(key, "")
        else:
            if isinstance(value, float):
                d = decimals if decimals is not None else 1
                str_val = "{:.{}f}".format(value, d)
            else:
                str_val = str(value)
            self._display_values[key] = str_val
            if self._debug_mode & CCA_DEBUG_OUT:
                print(self._ts() + "[CCA] OUT {} = {}".format(key, str_val))
            self._send_internal(key, str_val)

    def _send_if_changed(self, key, str_val):
        if self._display_values.get(key) == str_val:
            return
        self._display_values[key] = str_val
        if self._debug_mode & CCA_DEBUG_OUT:
            if str_val:
                print(self._ts() + "[CCA] OUT {} = {}".format(key, str_val))
            else:
                print(self._ts() + "[CCA] OUT {}".format(key))
        self._send_internal(key, str_val)

    # ---------------------------------------------------------------- #
    #  Abstrakte Methoden – werden in Unterklassen überschrieben        #
    # ---------------------------------------------------------------- #

    def handle(self):
        """Muss in der Hauptschleife aufgerufen werden!
        Verarbeitet empfangene Befehle und aktualisiert Variablen.
        """
        raise NotImplementedError("handle() muss in der Unterklasse implementiert werden")

    def is_connected(self):
        """Gibt True zurück wenn eine Verbindung besteht."""
        raise NotImplementedError("is_connected() muss in der Unterklasse implementiert werden")

    def _send_internal(self, key, value):
        """Intern – wird von Unterklassen überschrieben."""
        raise NotImplementedError

    def _ts(self):
        """Zeitstempel '[HH:MM:SS.mmm] ' seit Boot – leer wenn show_timestamp=False."""
        if not self._show_timestamp:
            return ""
        t = time.ticks_ms()
        ms = t % 1000
        t //= 1000
        s = t % 60
        m = (t // 60) % 60
        h = (t // 3600) % 24
        return "[{:02d}:{:02d}:{:02d}.{:03d}] ".format(h, m, s, ms)

    def _watchdog_zero(self, cmd):
        return "0;0;0" if cmd in self._color_keys else "0"

    def _check_watchdogs(self):
        """Setzt Variablen auf 0 wenn sie länger als ihr Timeout nicht aktualisiert wurden."""
        if not self._watchdogs or not self.is_connected():
            return
        now = time.ticks_ms()
        for cmd, timeout_ms in self._watchdogs.items():
            if (not self._watchdog_fired.get(cmd, False) and
                    time.ticks_diff(now, self._watchdog_last.get(cmd, now)) >= timeout_ms):
                self._process_command("{}:{}".format(cmd, self._watchdog_zero(cmd)))
                self._watchdog_fired[cmd] = True  # nach _process_command, sonst sofort wieder False

    def _fire_all_watchdogs(self):
        """Setzt alle Watchdog-Variablen sofort auf 0 (einmalig bei Verbindungsabbruch)."""
        now = time.ticks_ms()
        for cmd in self._watchdogs:
            self._watchdog_last[cmd] = now
            self._process_command("{}:{}".format(cmd, self._watchdog_zero(cmd)))

    def _reset_watchdog_timers(self):
        """Setzt alle Watchdog-Zeitstempel zurück (bei Verbindungsaufbau)."""
        now = time.ticks_ms()
        for cmd in self._watchdog_last:
            self._watchdog_last[cmd]  = now
            self._watchdog_fired[cmd] = False

    def _resync_display(self):
        """Sendet alle gespeicherten Display-Werte erneut an die App."""
        for key, value in self._display_values.items():
            self._send_internal(key, value)

    # ---------------------------------------------------------------- #
    #  Interne Hilfsmethode                                             #
    # ---------------------------------------------------------------- #

    def _process_command(self, cmd):
        """Verarbeitet einen empfangenen Befehlsstring.

        Format:  "key:value"             → ein Befehl mit Wert
                "key"                   → ein Befehl ohne Wert
                "key1:val1,key2:val2"   → mehrere Befehle (kommasepariert)
        """
        parts = cmd.split(",")
        for part in parts:
            part = part.strip()
            if not part:
                continue

            colon = part.find(":")
            if colon > 0:
                key   = part[:colon]
                value = part[colon + 1:]
                if key in self._callbacks:
                    try:
                        self._callbacks[key](value)
                    except TypeError:
                        self._callbacks[key]()
                    if key in self._watchdog_last:
                        self._watchdog_last[key]  = time.ticks_ms()
                        self._watchdog_fired[key] = False
                else:
                    print(self._ts() + "Unbekannter Befehl: " + str(key))
            else:
                if part in self._callbacks:
                    if self._debug_mode & CCA_DEBUG_IN:
                        print(self._ts() + "[CCA] IN  {} (kein Wert)".format(part))
                    try:
                        self._callbacks[part]()
                    except TypeError:
                        self._callbacks[part]("")
                    if part in self._watchdog_last:
                        self._watchdog_last[part]  = time.ticks_ms()
                        self._watchdog_fired[part] = False
                else:
                    print(self._ts() + "Unbekannter Befehl: " + str(part))


# ------------------------------------------------------------------ #
#  Factory-Funktion – vereinfachte Konfiguration                      #
# ------------------------------------------------------------------ #

def create_remote(name, connection=CCA_BLE, password="", debug_level=CCA_DEBUG_OFF,
                prefix="CCA-", port=4210, show_timestamp=True):
    """Erstellt das passende remote-Objekt anhand der Konfigurationsparameter.

    Empfohlene Verwendung:
        from CCARemote import CCA_BLE, CCA_WIFI, CCA_DEBUG_ALL, create_remote

        DEVICE_NAME = "MeinName"
        CONNECTION  = CCA_BLE
        PASSWORD    = ""
        DEBUG_LEVEL = CCA_DEBUG_ALL

        remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL)
        remote.begin()

    Args:
        name:        Gerätename (wird als "CCA-<name>" angezeigt)
        connection:  CCA_BLE (Standard) oder CCA_WIFI
        password:    Passwort (WiFi: min. 8 Zeichen / leer = ohne)
        debug_level: CCA_DEBUG_OFF / CCA_DEBUG_IN / CCA_DEBUG_OUT / CCA_DEBUG_ALL
        prefix:      Geräte-Präfix (Standard: "CCA-")
        port:        TCP-Port (Standard: 4210, nur WiFi)
    """
    if connection == CCA_WIFI:
        from CCARemote.wifi import CCARemoteWiFi
        return CCARemoteWiFi(name, prefix=prefix, password=password,
                            port=port, debug_level=debug_level,
                            show_timestamp=show_timestamp)
    else:
        from CCARemote.ble import CCARemoteBLE
        return CCARemoteBLE(name, prefix=prefix, password=password,
                            debug_level=debug_level,
                            show_timestamp=show_timestamp)
