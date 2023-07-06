import tasmotadevicecontroller
import database
import asyncio
import json
import os

COUNTER_NAMES = ["Total", "Today"]
GAUGE_NAMES = ["Power", "ApparentPower", "ReactivePower", "Factor", "Voltage", "Current"]
SUMMARY_NAMES = ["TotalStartTime", "Yesterday"]
BOOLEAN_ENUM_NAMES = ["Power"]

async def get_energy_for(host, username = None, password = None):
    device = await tasmotadevicecontroller.TasmotaDevice().connect(host, username, password)
    energy = await device.sendRawRequest("Status 8")
    power = await device.getPower()
    # friendlyname = await device.getFriendlyName()
    energy["StatusSNS"]["ENERGY"]["Power"] = power
    return energy["StatusSNS"]["ENERGY"]
    # return {"%s_%s" % (status["FriendlyName"], k): v for k, v in status.items()}

async def log_energies_for(db: database.PowerDatabase, host, username, password):
    pass

if __name__  == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        print(asyncio.run(get_energy_for("switch.plug", "admin", "securebackdoor")))
        # asyncio.run(get_all_plugs("4u.plug:admin:securebackdoor,switch.plug:admin:securebackdoor,router.plug:admin:securebackdoor,nas.plug:admin:securebackdoor"))
    except KeyboardInterrupt:
        pass
