from dataclasses import dataclass
from paramiko.ssh_exception import NoValidConnectionsError
import configparser
import threading
import fabric
import logging
import time
import os
import re

logging.basicConfig( 
    format = "%(levelname)s\t[%(asctime)s]\t%(message)s", 
    level = logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

INFLUXDB_MAPPINGS = {
    "poe-out-voltage": "tpPoeVoltage",
    "poe-out-current": "tpPoeCurrent",
    "poe-out-power": "tpPoePower",
}

@dataclass
class MikroTikSSHDevice:

    host: str
    ssh_key_path: str
    user: str = "admin"

    def __post_init__(self):
        self.is_being_polled = threading.Event()

    def _get_conn(self):
        return fabric.Connection(
            user = self.user,
            host = self.host,
            connect_kwargs = {"key_filename": self.ssh_key_path}
        )
    
    def _poll_four_interfaces(self, four_interfaces):
        # only poll four interfaces at the same time since we can only get a certain amount of information through SSH at the same time
        self.is_being_polled.set()
        result = self._get_conn().run("/interface/ethernet/poe/monitor %s once" % ",".join(four_interfaces), hide = True)
        self.is_being_polled.clear()
        return self._parse_result(result)

    def _parse_result(self, result):
        r = result.stdout
        # print(r)
        s = [re.split(r" +", row.rstrip())[1:] for row in r.split("\r\n")][:-2]
        out = {i: {} for i in s[0][1:]}
        off_interfaces = set()
        for row in s[1:]:
            column_decrimator = 0
            output_name = row[0][:-1]
            # print(output_name)

            for i, interface_name in enumerate(out.keys(), 0):
                # print("off_interfaces:", off_interfaces)
                # print(i, interface_name, row[1:][i])
                if interface_name in off_interfaces:
                    # print("Skipping '%s' for %s..." % (output_name, interface_name))
                    column_decrimator += 1
                else:
                    out[interface_name][output_name] = row[1:][i - column_decrimator]

                if output_name == "poe-out-status":
                    if row[1:][i] != "powered-on":
                        # print("Adding %s to off interfaces" % interface_name)
                        off_interfaces.add(interface_name)
        return out
    
    def get_poe_interfaces(self, interface_names):
        out = {}
        for four_interfaces in [interface_names[i:i + 4] for i in range(0, len(interface_names), 4)]:
            out = {**out, **self._poll_four_interfaces(four_interfaces)}
        return out

def remove_measurement_type(type_str):
    type_str = "".join([s for s in type_str if s.isdigit() or s == "."])
    if "." in type_str:
        return float(type_str)
    else:
        return int(type_str)

def fields_to_points(fields, switch_host, config):
    return [{
        "measurement": "switch_status", 
        "tags": {"port": port, "port_name": config.get(switch_host, port), "switch_host": switch_host, "type": "MikroTik"}, 
        "fields": {INFLUXDB_MAPPINGS[k]: remove_measurement_type(v) for k, v in values.items() if k in INFLUXDB_MAPPINGS}
    } for port, values in fields.items()]

def get_points():
    mikrotik_switches = configparser.ConfigParser()
    mikrotik_switches.read(os.path.join(os.path.dirname(__file__), "mikrotik-switches.conf"))
    points = []
    for mikrotik_switch in mikrotik_switches.sections():
        mikrotik_device = MikroTikSSHDevice(mikrotik_switch, os.path.join(os.path.dirname(__file__), "mikrotik.pem"))
        try:
            points += fields_to_points(mikrotik_device.get_poe_interfaces(list(mikrotik_switches[mikrotik_switch].keys())), mikrotik_switch, mikrotik_switches)
        except NoValidConnectionsError as e:
            logging.error("Could not connect to mikrotik switch @ %s" % mikrotik_switch)
    return points

def print_points(points):
    for measurement in points:
        if set(INFLUXDB_MAPPINGS.values()) <= set(measurement["fields"].keys()):
            if measurement["fields"]["tpPoePower"] > 0:
                logging.info("Port %s (%s) of %s switch %s is currently using %.1fW (%imA / %.1fV)" % (
                    str(measurement["tags"]["port"]),
                    measurement["tags"]["port_name"],
                    measurement["tags"]["type"],
                    measurement["tags"]["switch_host"],
                    measurement["fields"]["tpPoePower"],
                    measurement["fields"]["tpPoeCurrent"],
                    measurement["fields"]["tpPoeVoltage"],
                ))

if __name__ == "__main__":
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "mikrotik-switches.conf")):
        raise FileNotFoundError("Couldn't find mikrotik config file")
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "mikrotik.pem")):
        raise FileNotFoundError("Couldn't find mikrotik public key file")
    
    import json
    points = get_points()
    print(json.dumps(points, indent = 4))
    
