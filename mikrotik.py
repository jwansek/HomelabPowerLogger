from dataclasses import dataclass, field
import serial
import devices
import time
import os
import re

@dataclass
class MikroTikSerialDevice:
    device: str = os.environ["MIKROTIK_DEVICE"]
    user: str = os.environ["MIKROTIK_USER"]
    passwd: str = os.environ["MIKROTIK_PASS"]

    def __post_init__(self):
        self.interfaces = {}
        for i in os.environ["MIKROTIK_INTERFACES"].split(","):
            self.interfaces.__setitem__(*i.split(":"))

    def _get_poe_info(self, port):
        self.ser = serial.Serial(self.device, 115200, timeout=0.25)

        self._push_serial("")
        self._push_serial(self.user)
        self._push_serial(self.passwd)
        self._push_serial("/interface/ethernet/poe/monitor %s" % port)
        time.sleep(0.05)
        self.ser.write(bytes("q", 'ISO-8859-1'))
        out = self._read()
        self.ser.close()

        return self._post_out(out)

    def _push_serial(self, text):
        time.sleep(0.05)
        self.ser.write(bytes(text + "\r\n", 'ISO-8859-1'))
        time.sleep(0.05)

    def _read(self):
        return self.ser.readlines()

    def _post_out(self, out):
        d = {}
        for line in out:
            line = line.decode().strip()
            if line.startswith("poe"):
                d.__setitem__(*line.split(": "))

        return d

    def get_poes(self):

        print(self.interfaces)


if __name__ == "__main__":
    mikrotik = MikroTikSerialDevice()
    print(mikrotik.get_poes())

