# SNMP and MQTT Power Logger & Visualizer

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

Moreover mikrotik switches must be set up with an appropriate SSH key pair so they can be polled through SSH

## MQTT setup

We are using a [Tasmota-flashed zigbee coordinator](https://www.aliexpress.com/item/1005005254486268.html) to transmit zigbee messages to our MQTT castor, and [Tasmota-flashed plugs](https://www.aliexpress.com/item/1005008427641332.htm) for logging power from the wall over MQTT. Both must be configured with an appropriate friendlyname and told access the MQTT castor.

![Zigbee coordinator](https://i.imgur.com/GSyKSgS.png) ![MQTT Configuration](https://i.imgur.com/96q7nmo.png)
