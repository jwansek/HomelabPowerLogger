import paho.mqtt.client as paho
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import os

class MQTTClient:
    def __init__(self):
        self.influxc = InfluxDBClient(
            url = "http://%s:8086" % INFLUXDB_HOST,
            token = os.environ["DOCKER_INFLUXDB_INIT_ADMIN_TOKEN"],
            org = os.environ["DOCKER_INFLUXDB_INIT_ORG"] 
        )
        self.influxc.ping()

        self.mqttc = paho.Client('power-listener', clean_session = True)
        self.mqttc.on_connect = self._on_connect_cb
        self.mqttc.on_message = self._on_message_cb

        self.mqttc.username_pw_set(os.environ["MQTT_USER"], password = os.environ["MQTT_PASSWD"])
        self.mqttc.connect(MQTT_HOST, 1883, 60)
        self.mqttc.loop_forever()

    def _on_connect_cb(self, mqtt, userdata, flags, rc):
        print("Connected to broker")
        self.mqttc.subscribe("tele/+/SENSOR")

    def _on_message_cb(self, mqtt, userdata, msg):
        print('Topic: {0} | Message: {1}'.format(msg.topic, msg.payload))

        if "Tasmota" in msg.topic:
            self.handle_tasmota(msg)

    def handle_tasmota(self, msg):
        from_ = msg.topic.split("/")[1]
        msg_j = json.loads(msg.payload.decode())
        #print(from_)
        fields = {k: v for k, v in msg_j["ENERGY"].items() if k not in {"TotalStartTime"}}
        points = [{"measurement": "tasmota_power", "tags": {"plug": from_}, "fields": fields}]
        write_api = self.influxc.write_api(write_options = SYNCHRONOUS)
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
        INFLUXDB_HOST = "localhost"
        MQTT_HOST = "localhost"
    else:
        INFLUXDB_HOST = "influxdb"
        MQTT_HOST = "mqtt"

    mqtt_client = MQTTClient()




