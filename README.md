# power.eda.gay

Logs Tasmota-flashed power usage monitors to InfluxDB and Grafana using MQTT.

Looking for the Mikrotik POE usage monitor/exporter? That's been moved to [MikrotikPOEPowerExporter](https://github.com/jwansek/MikrotikPOEPowerExporter)

![InfluxDB screenshot](https://pbs.twimg.com/media/F_U75tVXwAA5QfG?format=jpg&name=medium)

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
