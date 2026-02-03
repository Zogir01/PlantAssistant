from core.logging import * ; gc.collect()

logger.debug(f"Free RAM before imports: {gc.mem_free()}")

from app.place import PlantPlace ; gc.collect()
from app.water import WateringController ; gc.collect()
from app.light import LEDController, LightSensor ; gc.collect()
from app.device import DeviceController ; gc.collect()
from app.device_api import DeviceAPI ; gc.collect()
from drivers.soil_sensor import SoilSensor ; gc.collect()
from drivers.valve import Valve ; gc.collect()
from drivers.water_pump import WaterPump ; gc.collect()
from drivers.float_switch import FloatSwitch ; gc.collect()
from drivers.button import Button ; gc.collect()
from dht import DHT11 ; gc.collect()
from app.server import HttpServer ; gc.collect()

logger.debug(f"Free RAM after imports: {gc.mem_free()}")

from machine import I2C, Pin
import ujson
import gc

logger.debug(f"Free RAM before init: {gc.mem_free()}")

# Initialize hardware

pump = WaterPump(pin_num=19, frequency=5000)
v1 = Valve(pin_num=18)
v2 = Valve(pin_num=17)
v3 = Valve(pin_num=16)
s1 = SoilSensor(pin_num=34, min_adc=1200, max_adc=3050)
s2 = SoilSensor(pin_num=35, min_adc=1200, max_adc=3050)
s3 = SoilSensor(pin_num=32, min_adc=1200, max_adc=3050)
b1 = Button(pin_num=9)
b2 = Button(pin_num=10)
b3 = Button(pin_num=15)
wat_lev = FloatSwitch(pin_num=3)
dht = DHT11(5)
ls = LightSensor(i2c=I2C(0, scl=Pin(27), sda=Pin(14)))
led = Pin(6, Pin.OUT)

pump.off()
v1.close()
v2.close()
v3.close()

# Initialize application

places = [
    PlantPlace(id="place1", valve=v1, soil_sens=s1, on_off_button=b1),
    PlantPlace(id="place2", valve=v2, soil_sens=s2, on_off_button=b2),
    PlantPlace(id="place3", valve=v3, soil_sens=s3, on_off_button=b3)
]
water_ctrl = WateringController(places=places, dht=dht, pump=pump, water_sensor=wat_lev)
led_ctrl = LEDController(led=led, sensor=ls)
device_ctrl = DeviceController(water_ctrl=water_ctrl, led_ctrl=led_ctrl)
api = DeviceAPI(device_ctrl)
server = HttpServer()

# Register HTTP endpoints.

# Status
server.defslite('system_info.json', lambda v: ujson.dumps(api.get_system_info())) 
server.defslite('status.json', lambda v: ujson.dumps(api.get_status()))
# Wi-Fi
server.defslite('wifi_status.json', lambda v: ujson.dumps(api.get_wifi_status()))
server.defslite('wifi_stations.json', lambda v: ujson.dumps(api.get_wifi_stations()))
# Config
server.defslite('config.json', lambda v: ujson.dumps(api.get_config()))
server.defslite('update_config', lambda v: api.update_config(v))
# Control
server.defslite('water', lambda v: api.start_manual_watering(v))
server.defslite('stop_water', lambda v: api.stop_watering(v))
server.defslite('toggle_place', lambda v: api.toggle_place(v))
server.defslite('toggle_wt_mode', lambda v: api.toggle_watering_mode(v))
server.defslite('connect_wifi', lambda v: api.connect_wifi(v))

gc.collect()
logger.debug(f"Free RAM after init: {gc.mem_free()}")

# Main loop
while(True):
    server.accept()
    device_ctrl.update()
    gc.collect()

