from dataclasses import dataclass, field
import threading
import serial
import devices
import time
import os
import re

@dataclass
class MikroTikSerialDevice:
    """This is a horrible, horrible way of doing this
    pretty much anything else would be better, for example connecting
    over SSH instead of serial

    Even using a serial connection like this is an abomination
    Please seriously do not do this, this is some necromancy, like it doesn't
    log out of the serial connection properly so make sure nothing else is plugged
    into the switch serial port

    I am doing it this way because I do not understand mikrotik scripting
    """
    device: str = os.environ["MIKROTIK_DEVICE"]
    user: str = os.environ["MIKROTIK_USER"]
    passwd: str = os.environ["MIKROTIK_PASS"]

    def __post_init__(self):
        self.interfaces = {}
        self.last_return = {}
        for i in os.environ["MIKROTIK_INTERFACES"].split(","):
            self.interfaces.__setitem__(*i.split(":"))
        self.is_being_polled = threading.Event()
        self.poe_cache = {interface: {} for interface in self.interfaces}

    def get_poe_info(self, interface):
        print(self.poe_cache)
        if self.is_being_polled.is_set():
            fetched_cache = self.poe_cache[interface]
            fetched_cache["cached"] = True
            return fetched_cache

        self.is_being_polled.set()
        self.ser = serial.Serial(self.device, int(os.environ["MIKROTIK_BAUD"]), timeout=0.25)

        if self.last_return == {}:
            self._push_serial("")
            self._push_serial(self.user)
            self._push_serial(self.passwd)
        self._push_serial("/interface/ethernet/poe/monitor %s" % interface)
        time.sleep(0.05)
        self.ser.write(bytes("q", 'ISO-8859-1'))
        out = self._read()
        self.ser.close()
        self.is_being_polled.clear()

        return self._post_out(out, interface)

    def _push_serial(self, text):
        time.sleep(0.05)
        self.ser.write(bytes(text + "\r\n", 'ISO-8859-1'))
        time.sleep(0.05)

    def _read(self):
        return self.ser.readlines()

    def _post_out(self, out, interface, was_cached = False):
        d = {}
        for line in out:
            line = line.decode().strip()
            # print("line:", line)
            if line.startswith("poe"):
                d.__setitem__(*line.split(": "))

        self.last_return = d
        self.poe_cache[interface] = d
        d["cached"] = was_cached
        return d




if __name__ == "__main__":
    if not os.path.exists(os.path.join("/app", ".docker")):
        import dotenv
        dotenv.load_dotenv(dotenv_path = "power.env")

    mikrotik = MikroTikSerialDevice()
    for interface in mikrotik.interfaces:
        print(interface, mikrotik.get_poe_info(interface))

