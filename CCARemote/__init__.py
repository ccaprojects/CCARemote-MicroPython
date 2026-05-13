# CCARemote/__init__.py – Abstract base class
#
# Usage:
#   from CCARemote.ble  import CCARemoteBLE   # for BLE-Connection
#   from CCARemote.wifi import CCARemoteWiFi  # for WiFi-Connection
#   from CCARemote.mqtt import CCARemoteMQTT  # for MQTT-Connection
#
# Developed by A. Eckhart (HTL Anichstraße) - MIT – see LICENSE

# Version der Bibliothek
__version__ = "1.1.0"

# ------------------------------------------------------------------ #
#  Debug-Modus Konstanten (kombinierbar mit |)                        #
# ------------------------------------------------------------------ #
CCA_DEBUG_OFF = 0   # kein Debug-Output
CCA_DEBUG_IN  = 1   # empfangene Werte ausgeben
CCA_DEBUG_OUT = 2   # gesendete Werte ausgeben
CCA_DEBUG_ALL = 3   # empfangene und gesendete Werte ausgeben


class CCARemote:
    """Abstrakte Basisklasse – nicht direkt verwenden!
    Verwende: CCARemoteBLE, CCARemoteWiFi, CCARemoteMQTT
    """

    def __init__(self, name, prefix="CCA-"):
        self._device_name      = prefix + name
        self._debug_mode       = CCA_DEBUG_OFF
        self._command_received = False
        self._last_command     = ""
        # cmd → callback (ohne oder mit Wert-Parameter)
        self._callbacks        = {}
        # cmd → aktueller Wert (für remote.get())
        self._values           = {}
        # key → Anzeige-Wert (für send / /display)
        self._display_values   = {}

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
        print(msgs.get(mode, "[CCA] Debug-Modus gesetzt"))

    def on_command(self, cmd, callback):
        """Registriert einen Callback für einen Befehl.

        Der Callback kann keinen oder einen Parameter (Wert) haben:
            remote.on_command("btn",    lambda: print("gedrückt"))
            remote.on_command("slider", lambda v: print("Wert:", v))
        """
        self._callbacks[cmd] = callback
        if self._debug_mode != CCA_DEBUG_OFF:
            print("Befehl registriert:", cmd)

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
                print("[CCA] IN ", cmd, "=", value)

        self._callbacks[cmd] = _handler
        if self._debug_mode != CCA_DEBUG_OFF:
            print("Variable gebunden:", cmd, "({})".format(value_type.__name__))

    def receive_color(self, cmd):
        """Verknüpft eine Color-Picker-ID für automatische R/G/B-Konvertierung.

        Werte abrufen mit: r, g, b = remote.get_color("color1")

        Wert-Format der App: R;G;B  (z.B. "255;128;0")

        Args:
            cmd: Element-ID des Color-Pickers aus der CCA Remote App
        """
        self._values[cmd] = (0, 0, 0)

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
                print("[CCA] IN  {} = R:{} G:{} B:{}".format(cmd, r_v, g_v, b_v))

        self._callbacks[cmd] = _handler
        if self._debug_mode != CCA_DEBUG_OFF:
            print("Farbe gebunden: {} (r,g,b)".format(cmd))

    def get_color(self, cmd, default=(0, 0, 0)):
        """Gibt den zuletzt empfangenen RGB-Farbwert zurück.

        Returns:
            Tuple (r, g, b) mit Ganzzahlen 0–255

        Beispiel:
            r, g, b = remote.get_color("color1")
            led_r.duty_u16(r * 257)
        """
        return self._values.get(cmd, default)

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

    def _send_if_changed(self, key, str_val):
        if self._display_values.get(key) == str_val:
            return
        self._display_values[key] = str_val
        if self._debug_mode & CCA_DEBUG_OUT:
            if str_val:
                print("[CCA] OUT", key, "=", str_val)
            else:
                print("[CCA] OUT", key)
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
                    # Callback aufrufen – mit Wert wenn möglich, sonst ohne
                    try:
                        self._callbacks[key](value)
                    except TypeError:
                        self._callbacks[key]()
                else:
                    print("Unbekannter Befehl:", key)
            else:
                if part in self._callbacks:
                    if self._debug_mode & CCA_DEBUG_IN:
                        print("[CCA] IN ", part, "(kein Wert)")
                    try:
                        self._callbacks[part]()
                    except TypeError:
                        self._callbacks[part]("")
                else:
                    print("Unbekannter Befehl:", part)
