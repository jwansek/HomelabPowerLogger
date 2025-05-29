# power.eda.gay

Logs Tasmota-flashed power usage monitors, and TP-Link Omada/Mikrotik POE switches, to InfluxDB and Grafana using MQTT, SNMP and prometheus.
Also logs Zigbee informtion with a Tasmota-flashed Zigbee bridge.

Looking for the Mikrotik POE usage monitor/exporter? That's in [`mikrotik.py`](/switch-snmp/mikrotik.py)

![Grafana screenshot](https://i.imgur.com/YcAmIf5.png)

## Setup

- `cp power.env.example power.env`
- Edit `power.env` as appropriate
- `touch .passwords`
- `sudo docker-compose up -d --build`
- `sudo docker exec -it poweredagay_mqtt_1 sh` Then in the container:
    - `chmod 0700 /mosquitto/passwd_file`
    - `chmod root:root /mosquitto/passwd_file`
    - ` mosquitto_passwd -c /mosquitto/passwd_file user_name` Changing `user_name` as appropriate, then it will prompt for a password
- `sudo docker-compose restart`
- Test with the `mosquitto_sub` and `mosquitto_pub` commands, the name of the package on debian is `mosquitto-clients`
- Change the config in the Tasmota MQTT web UI, then check the logs to make sure it connects nicely
- I like to run `TelePeriod 30` in the Tasmota console to set it to send MQTT messages every 30 seconds, for example. The default is every 5 minutes I believe 

## Switch setup

You must enable SNMP in the Omada controller with the community string `tplink`:

![SNMP](https://i.imgur.com/bWUGPQO.png)
