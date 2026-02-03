
from core.wifi import WifiManager, WifiError
from core.logging import logger
import time
import machine

try:
    wifi = WifiManager()
    wifi.initialise()
    logger.debug(f"AP Status: {wifi.get_ap_status()}, STA status: {wifi.get_sta_status()}")

except WifiError as e:
    logger.critical(f"Cannot initialise wifi: {e}. Resetting ESP32 in 2 seconds...")
    time.sleep(2)
    #machine.reset()
    
except Exception as e:
    logger.critical(f"Unexpected error occured: {e}. Resetting ESP32 in 2 seconds...")
    time.sleep(2)
    #machine.reset()

# import network
# sta = network.WLAN(network.STA_IF)
# ap  = network.WLAN(network.AP_IF)

# sta.active(False)        # wyłącz STA przed konfiguracją AP
# ap.active(True)          # włącz AP
# ap.config(ssid="TestAP", password="12345678")

# print(ap.ifconfig())
