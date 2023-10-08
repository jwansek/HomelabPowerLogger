import database
import mikrotik
import devices
import flask
import os

app = flask.Flask(__name__)
switch = mikrotik.MikroTikSerialDevice()

@app.route("/")
def route_index():
    with database.PowerDatabase(host = devices.HOST) as db:
        return flask.render_template(
            "index.html.j2",
            tasmota_devices = db.get_tasmota_devices()
        )

@app.route("/api/mikrotik_devices")
def api_get_mikrotik_devices():
    return flask.jsonify(switch.interfaces)

@app.route("/api/mikrotik_interface/<interface>")
def api_poll_mikrotik_interface(interface):
    try:
        return flask.jsonify(
            {
                "interface": interface,
                "description": switch.interfaces[interface],
                "poe_status": switch.get_poe_info(interface)
            }
        )
    except (IndexError, KeyError):
        return flask.abort(400)
    
@app.route("/api/plugs")
def api_poll_plugs():
    with database.PowerDatabase(host = devices.HOST) as db:
        return flask.jsonify(db.get_last_plug_readings())

@app.route("/api/daily_chart")
def api_get_watt_chart():
    with database.PowerDatabase(host = devices.HOST) as db:
        return flask.jsonify(db.get_watt_chart())

@app.route("/api/longterm_chart")
def api_get_kwh_chart():
    with database.PowerDatabase(host = devices.HOST) as db:
        return flask.jsonify(db.get_kwh_chart())

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = int(os.environ["APP_PORT"]), debug = True)