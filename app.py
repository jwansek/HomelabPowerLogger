import database
import devices
import flask
import os

app = flask.Flask(__name__)

@app.route("/")
def route_index():
    with database.PowerDatabase(host = devices.HOST) as db:
        return flask.render_template(
            "index.html.j2",
            tasmota_devices = db.get_tasmota_devices()
        )

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = int(os.environ["APP_PORT"]), debug = True)