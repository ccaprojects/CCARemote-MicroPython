# CCARemote/ble.py – Bluetooth Low Energy (BLE) Implementation
#
# Handles BLE advertising, connection management and data transfer
# for the CCARemote App for remote control.
#
# Developed by A. Eckhart (HTL Anichstraße) - MIT – see LICENSE
#
# Requirements:
#   Raspberry Pi Pico 2 W or ESP32 with MicroPython >= 1.23
#   The bluetooth module is included in the standard firmware.

import bluetooth
import time
from . import CCARemote, CCA_DEBUG_ALL, CCA_PROTOCOL_VERSION, __version__

# BLE IRQ Event-Codes (MicroPython bluetooth-Modul)
_IRQ_CENTRAL_CONNECT    = 1
_IRQ_CENTRAL_DISCONNECT = 2
_IRQ_GATTS_WRITE        = 3

# GATT Charakteristik-Flags
_FLAG_READ              = 0x0002
_FLAG_WRITE_NO_RESPONSE = 0x0004
_FLAG_WRITE             = 0x0008
_FLAG_NOTIFY            = 0x0010

# ------------------------------------------------------------------ #
#  Service- und Charakteristik-UUIDs                                  #
#  Identisch mit der ESP32-Version – kompatibel mit der CCA Remote App#
# ------------------------------------------------------------------ #
_SERVICE_UUID = bluetooth.UUID("4fafc201-1fb5-459e-8fcc-c5c9c331914b")
_CONTROL_UUID = bluetooth.UUID("cba1d466-344c-4be3-ab3f-189f80dd7518")  # App  → Pico
_DISPLAY_UUID = bluetooth.UUID("d9a98a3e-7c1f-4b2a-9e8f-6d2c3a1b5e7f")  # Pico → App

_SERVICE = (
    _SERVICE_UUID,
    (
        (_CONTROL_UUID, _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE),
        (_DISPLAY_UUID, _FLAG_READ  | _FLAG_NOTIFY),
    ),
)


class CCARemoteBLE(CCARemote):
    """BLE-Verbindung für den Raspberry Pi Pico 2 W.

    Der Pico 2 W startet als BLE-Peripheral (GATT-Server) und wartet
    auf eine Verbindung der CCA Remote App.

    Beispiel (empfohlene Verwendung mit create_remote):
        from CCARemote import CCA_BLE, CCA_DEBUG_ALL, create_remote

        DEVICE_NAME = "MeinPico"
        CONNECTION  = CCA_BLE
        PASSWORD    = ""
        DEBUG_LEVEL = CCA_DEBUG_ALL

        remote = create_remote(DEVICE_NAME, CONNECTION, PASSWORD, DEBUG_LEVEL)
        remote.begin()
        remote.receive("button1", bool)

        while True:
            remote.handle()
            if remote.is_connected():
                led.value(1 if remote.get("button1", False) else 0)
    """

    def __init__(self, name, prefix="CCA-", password="", debug_level=0, show_timestamp=True):
        super().__init__(name, prefix, debug_level, show_timestamp)
        self._ble               = bluetooth.BLE()
        self._conn_handle       = None
        self._control_handle    = None
        self._display_handle    = None
        self._connected         = False
        self._password          = password
        self._authenticated     = False
        self._restart_advertise       = False  # wird in handle() ausgewertet
        self._pending_auth_fail       = False  # wird in handle() ausgewertet
        self._pending_resync          = False  # wird in handle() ausgewertet
        self._pending_fire_watchdogs  = False  # wird in handle() ausgewertet

    # ---------------------------------------------------------------- #
    #  Öffentliche Methoden                                             #
    # ---------------------------------------------------------------- #

    def begin(self):
        """Startet den BLE GATT-Server und beginnt mit dem Advertising.

        Passwort und Debug-Level werden über den Konstruktor oder create_remote() gesetzt.
        """

        print("\n" + self._ts() + "CCA Remote startet (BLE)...")
        if self._debug_mode == CCA_DEBUG_ALL:
            print(self._ts() + "[CCA] Library: {}  |  Protokoll: {}".format(__version__, CCA_PROTOCOL_VERSION))

        print(self._ts() + "Gerätename: " + self._device_name)

        self._ble.active(True)
        self._ble.irq(self._ble_irq)

        # MTU erhöhen für längere Nachrichten (Standard: 23 Bytes)
        self._ble.config(mtu=256)

        # GATT-Services registrieren
        ((self._control_handle, self._display_handle),) = \
            self._ble.gatts_register_services((_SERVICE,))

        # Empfangspuffer für Control-Charakteristik vergrößern
        self._ble.gatts_set_buffer(self._control_handle, 256, True)

        self._start_advertising()

        print(self._ts() + "BLE Server läuft!")
        if self._password:
            pwd = self._password if self._debug_mode == CCA_DEBUG_ALL else "*" * len(self._password)
            print(self._ts() + "BLE Passwort: " + pwd)
        print(self._ts() + "Warte auf Verbindung...\n")

    def handle(self):
        """Muss in der Hauptschleife aufgerufen werden!
        Verarbeitet empfangene BLE-Befehle.
        """
        if self._pending_fire_watchdogs:
            self._pending_fire_watchdogs = False
            self._fire_all_watchdogs()
        self._check_watchdogs()
        # Advertising-Neustart außerhalb des IRQ-Callbacks durchführen
        if self._restart_advertise:
            self._restart_advertise = False
            self._start_advertising()

        # Disconnect nach AUTH:FAIL – mit Delay damit Notify übertragen wird
        if self._pending_auth_fail:
            self._pending_auth_fail = False
            time.sleep_ms(50)
            if self._conn_handle is not None:
                try:
                    self._ble.gap_disconnect(self._conn_handle)
                except Exception:
                    pass

        # Display-Werte nach Verbindungsaufbau erneut senden
        if self._pending_resync and self._connected and self._authenticated:
            self._pending_resync = False
            self._resync_display()

        if self._command_received:
            self._process_command(self._last_command)
            self._command_received = False

    def is_connected(self):
        """Gibt True zurück wenn ein Gerät verbunden und authentifiziert ist."""
        return self._connected and self._authenticated

    # ---------------------------------------------------------------- #
    #  Interne Methoden                                                 #
    # ---------------------------------------------------------------- #

    def _start_advertising(self):
        """Startet BLE-Advertising mit dem Gerätenamen."""
        name_bytes = self._device_name.encode("utf-8")
        # Advertising-Daten: Flags + Complete Local Name
        adv_data = (
            b"\x02\x01\x06"                          # Flags: LE General Discoverable
            + bytes([len(name_bytes) + 1, 0x09])     # AD Type 0x09: Complete Local Name
            + name_bytes
        )
        # Auf 31 Bytes begrenzen (BLE-Limit für Advertising Data)
        if len(adv_data) > 31:
            adv_data = adv_data[:31]
        self._ble.gap_advertise(100_000, adv_data=adv_data)  # 100 ms Intervall

    def _ble_irq(self, event, data):
        """BLE Interrupt-Handler (wird vom BLE-Stack aufgerufen)."""
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._conn_handle    = conn_handle
            self._connected      = True
            # Ohne Passwort sofort authentifiziert
            self._authenticated  = not bool(self._password)
            self._pending_resync = True
            self._reset_watchdog_timers()
            if self._debug_mode:
                print(self._ts() + "[CCA] Verbindung hergestellt")

        elif event == _IRQ_CENTRAL_DISCONNECT:
            self._conn_handle            = None
            self._connected              = False
            self._authenticated          = False
            self._restart_advertise      = True   # Neustart in handle() – nicht hier!
            self._pending_fire_watchdogs = True   # _fire_all_watchdogs() in handle()
            if self._debug_mode:
                print(self._ts() + "[CCA] Verbindung getrennt")

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            if attr_handle == self._control_handle:
                raw = self._ble.gatts_read(self._control_handle)
                value = raw.decode("utf-8", "ignore").strip()
                if not value:
                    return
                # '>' Startmarker entfernen (BLE sendet '>cmd', Pico braucht das nicht,
                # aber für Kompatibilität mit der App wird es still entfernt)
                gte = value.find('>')
                if gte >= 0:
                    value = value[gte + 1:]
                if not value:
                    return

                # Authentifizierung prüfen wenn Passwort gesetzt
                if self._password and not self._authenticated:
                    if value == "AUTH:" + self._password:
                        self._authenticated  = True
                        self._pending_resync = True
                        self._reset_watchdog_timers()
                        print(self._ts() + "BLE Authentifizierung erfolgreich!")
                        try:
                            self._ble.gatts_write(self._display_handle, b"AUTH:OK\n")
                            self._ble.gatts_notify(self._conn_handle, self._display_handle)
                        except Exception:
                            pass
                    else:
                        print(self._ts() + "BLE Authentifizierung fehlgeschlagen! Verbindung wird getrennt.")
                        if self._conn_handle is not None:
                            try:
                                self._ble.gatts_write(self._display_handle, b"AUTH:FAIL\n")
                                self._ble.gatts_notify(self._conn_handle, self._display_handle)
                            except Exception:
                                pass
                            self._pending_auth_fail = True  # Disconnect nach Delay in handle()
                    return

                if value == "AUTH" or value.startswith("AUTH:"):
                    # AUTH-Befehl der App = Subscription aktiv → Display-Werte jetzt sicher senden
                    self._pending_resync = True
                    return

                if value.startswith("ping:"):
                    return  # Heartbeat der App

                self._last_command     = value
                self._command_received = True

    def _send_internal(self, key, value):
        """Sendet einen Wert an die App via BLE NOTIFY."""
        if self._connected and self._authenticated and self._display_handle is not None:
            msg = (key + ":" + value + "\n").encode("utf-8")
            try:
                self._ble.gatts_write(self._display_handle, msg)
                if self._conn_handle is not None:
                    self._ble.gatts_notify(self._conn_handle, self._display_handle)
            except Exception as e:
                print(self._ts() + "[CCA] BLE Sendefehler: " + str(e))

    def _resync_display(self):
        """Sendet alle gespeicherten Display-Werte erneut an die App."""
        for key, value in self._display_values.items():
            self._send_internal(key, value)
