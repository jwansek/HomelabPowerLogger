import tasmotadevicecontroller
import database
import asyncio
import datetime
import json
import sys
import os

if not os.path.exists(os.path.join("/app", ".docker")):
    import dotenv
    dotenv.load_dotenv(dotenv_path = "power.env")
    HOST = "srv.athome"
else:
    HOST = None

async def get_energy_for(host, username = None, password = None):
    device = await tasmotadevicecontroller.TasmotaDevice().connect(host, username, password)
    energy = await device.sendRawRequest("Status 8")
    power = await device.getPower()
    # friendlyname = await device.getFriendlyName()
    return energy["StatusSNS"]["ENERGY"]
    # return {"%s_%s" % (status["FriendlyName"], k): v for k, v in status.items()}

async def poll_watt_for(db: database.PowerDatabase, host, username, password):
    power = await get_energy_for(host, username, password)
    power = float(power['Power'])
    db.append_watt_readings(host, power)
    print("'%s' is using %.1fW at %s" % (host, power, datetime.datetime.now()))

async def poll_yesterday_kwh_for(db: database.PowerDatabase, host, username, password):
    power = await get_energy_for(host, username, password)
    power = float(power['Yesterday'])
    db.append_kwh_readings(host, power)
    print("'%s' used %.1fkWh yesterday" % (host, power))


def poll_watt_all():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with database.PowerDatabase(host = HOST) as db:
        for host, username, password in db.get_tasmota_devices():
            while True:
                try:
                    asyncio.run(poll_watt_for(db, host, username, password))
                except:
                    print("Retrying %s..." % host)
                    continue
                break
                

def poll_kwh_all():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with database.PowerDatabase(host = HOST) as db:
        for host, username, password in db.get_tasmota_devices():
            while True:
                try:
                    asyncio.run(poll_yesterday_kwh_for(db, host, username, password))
                except ConnectionError:
                    print("Retrying %s..." % host)
                    continue
                break

if __name__  == "__main__":
    while True:
        try:
            if sys.argv[1] == "daily":
                poll_kwh_all()
            else:
                poll_watt_all()
        except ConnectionError as e:
            print("Couldn't connect: ", e, " retrying...")
            continue
        break

