# wget https://static.tp-link.com/upload/software/2022/202209/20220915/privateMibs(20220831).zip
# cp -v *.mib /home/eden/.snmp/mibs
# sudo apt install snmp
# sudo apt-get install snmp-mibs-downloader

import subprocess
from dataclasses import dataclass
import dotenv
import os
import pandas
import configparser

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

DIVIDE_BY_10_ENDPOINTS = ["tpPoePower", "tpPoeVoltage"]

@dataclass
class SNMPReading:
    endpoint: str
    port: int
    reading: float

    @classmethod
    def from_string(cls, str_):
        s = str_.split()
        if len(s) != 4:
            raise Exception("Couldn't parse")
        endpoint_and_port, _, type_, reading = s
        endpoint, port = endpoint_and_port.split(".")

        if reading.isdigit():
            reading = int(reading)
        if endpoint in DIVIDE_BY_10_ENDPOINTS:
            reading = reading / 10

        return cls(endpoint, int(port), reading)

def get_alternate_name(port, host):
    port_names = configparser.ConfigParser()
    port_names.read(os.path.join(os.path.dirname(__file__), "omada-switches.conf"))
    port_names = {int(k): v for k, v in port_names[host].items()}

    try:
        return port_names[port]
    except KeyError:
        return port

def snmp_walk(host):
    proc = subprocess.Popen(
        ["snmpwalk", "-Os", "-c", "tplink", "-v", "2c", "-m", "TPLINK-POWER-OVER-ETHERNET-MIB", host, "tplinkPowerOverEthernetMIB"],
        stdout = subprocess.PIPE
    )
    out = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        try:
            out.append(SNMPReading.from_string(line.rstrip().decode()))
        except Exception:
            pass

    return out

def readings_to_points(readings, switch_host):
    points = []
    df = pandas.DataFrame(readings)
    df["port_name"] = df["port"].apply(get_alternate_name, args = (switch_host, ))
    for p, group_df in df.groupby(["port", "port_name"]):
        port, port_name = p
        fields = dict(zip(group_df['endpoint'], group_df['reading']))

        points.append({
            "measurement": "switch_status", 
            "tags": {"port": port, "port_name": port_name, "switch_host": switch_host, "type": "Omada"}, 
            "fields": fields
        })
    
    return points

def get_points():
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "omada-switches.conf")):
        raise FileNotFoundError("Couldn't find config file")
    switches = configparser.ConfigParser()
    switches.read(os.path.join(os.path.dirname(__file__), "omada-switches.conf"))
    points = []
    for switch_host in switches.sections():
        points += readings_to_points(snmp_walk(switch_host), switch_host)
    return points

if __name__ == "__main__":
    import mikrotik
    points = get_points()
    print(points)
    mikrotik.append(points)