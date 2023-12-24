# wget https://static.tp-link.com/upload/software/2022/202209/20220915/privateMibs(20220831).zip
# cp -v *.mib /home/eden/.snmp/mibs
# sudo apt install snmp
# sudo apt-get install snmp-mibs-downloader

import subprocess
from dataclasses import dataclass
import dotenv
import os
import pandas

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

DIVIDE_BY_10_ENDPOINTS = ["tpPoePower", "tpPoeVoltage"]

PORT_NAMES = dotenv.dotenv_values(os.path.join(os.path.dirname(__file__), "port-names.conf"))
PORT_NAMES = {int(k): v for k, v in PORT_NAMES.items()}

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

def get_alternate_name(port):
    try:
        return PORT_NAMES[port]
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
    df["port_name"] = df["port"].apply(get_alternate_name)
    for p, group_df in df.groupby(["port", "port_name"]):
        port, port_name = p
        fields = dict(zip(group_df['endpoint'], group_df['reading']))

        points.append({"measurement": "switch_status", "tags": {"port": port, "port_name": port_name, "switch_host": switch_host}, "fields": fields})
    
    return points

if __name__ == "__main__":
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.env")
    if os.path.exists(env_path):
        import dotenv
        dotenv.load_dotenv(dotenv_path = env_path)
        INFLUXDB_HOST = "dns.athome"
    else:
        INFLUXDB_HOST = "influxdb"

    influxc = InfluxDBClient(
        url = "http://%s:8086" % INFLUXDB_HOST,
        token = os.environ["DOCKER_INFLUXDB_INIT_ADMIN_TOKEN"],
        org = os.environ["DOCKER_INFLUXDB_INIT_ORG"] 
    )
    influxc.ping()

    for switch_host in os.environ["OMADA_SWITCHES"].split(","):
        points = readings_to_points(snmp_walk(switch_host), switch_host)
        write_api = influxc.write_api(write_options = SYNCHRONOUS)
        write_api.write(
            os.environ["DOCKER_INFLUXDB_INIT_BUCKET"],
            os.environ["DOCKER_INFLUXDB_INIT_ORG"],
            points,
            write_precision = WritePrecision.S
        )