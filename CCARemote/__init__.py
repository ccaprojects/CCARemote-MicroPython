# CCARemote/__init__.py – Abstrakte Basisklasse
#
# Basierend auf der Diplomarbeit von L. Eder und E. Duyar (HTL Anichstraße)
# Erweitert von A. Eckhart mit freundlicher Genehmigung der Originalautoren.
#
# Version: 1.0.0 | 2026-05-07 | MIT – siehe LICENSE
#
# Verwendung:
#   from CCARemote.ble  import CCARemoteBLE   # für BLE-Verbindung
#   from CCARemote.wifi import CCARemoteWiFi  # für WiFi-Verbindung
#   from CCARemote.mqtt import CCARemoteMQTT  # für MQTT-Verbindung

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
            # "key:value"-Form
            colon = key.find(":")
            if colon > 0:
                k = key[:colon]
                v = key[colon + 1:]
                if self._debug_mode & CCA_DEBUG_OUT:
                    print("[CCA] OUT", k, "=", v)
                self._send_internal(k, v)
            else:
                if self._debug_mode & CCA_DEBUG_OUT:
                    print("[CCA] OUT", key)
                self._send_internal(key, "")
        else:
            if isinstance(value, float):
                d = decimals if decimals is not None else 1
                str_val = "{:.{}f}".format(value, d)
            else:
                str_val = str(value)
            if self._debug_mode & CCA_DEBUG_OUT:
                print("[CCA] OUT", key, "=", str_val)
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
