import prometheus_client
import snmpOmada
import mikrotik
import os

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

def append(points):
    influxc = InfluxDBClient(
        url = "http://%s:8086" % INFLUXDB_HOST,
        token = os.environ["DOCKER_INFLUXDB_INIT_ADMIN_TOKEN"],
        org = os.environ["DOCKER_INFLUXDB_INIT_ORG"] 
    )
    influxc.ping()

    for measurement in points:
        for field in measurement["fields"].keys():
            try:
                float(measurement["fields"][field])
            except ValueError:
                continue
            else:
                switch_power.labels(
                    field = field,
                    type = measurement["tags"]["type"],
                    port = str(measurement["tags"]["port"]),
                    port_name = measurement["tags"]["port_name"],
                    host = measurement["tags"]["switch_host"]
                ).set(float(measurement["fields"][field]))

    write_api = influxc.write_api(write_options = SYNCHRONOUS)
    write_api.write(
        os.environ["DOCKER_INFLUXDB_INIT_BUCKET"],
        os.environ["DOCKER_INFLUXDB_INIT_ORG"],
        points,
        write_precision = WritePrecision.S
    )

if __name__ == "__main__":
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.env")
    if os.path.exists(env_path):
        import dotenv
        dotenv.load_dotenv(dotenv_path = env_path)
        INFLUXDB_HOST = "dns.athome"
        PUSHGATEWAY_HOST = "dns.athome"
    else:
        INFLUXDB_HOST = "influxdb"
        PUSHGATEWAY_HOST = "pushgateway"

    registry = prometheus_client.CollectorRegistry()
    switch_power = prometheus_client.Gauge(
        "switch_power",
        "POE switch power usage metrics from Omada and Mikrotik switches, using Omada SNMP names",
        labelnames = ["field", "type", "port", "port_name", "host"]
    )

    points = snmpOmada.get_points() + mikrotik.get_points()
    mikrotik.print_points(points)
    append(points)

    prometheus_client.push_to_gateway("%s:9091" % PUSHGATEWAY_HOST, job = "switchSNMP", registry = registry)