from .config import ConfigManager
from .singleton import singleton

import network
import time
import ntptime
from machine import RTC

class WifiError(Exception):
    '''General error related to Wifi.'''

class WifiConnectionError(WifiError):
    """Nie udało się połączyć z siecią WiFi."""

class WifiTimeoutError(WifiError):
    """Przekroczono limit czasu połączenia."""

class TimeSyncError(WifiError):
    ''''''

TIMEZONE = 1 # timezone used in setting correct time in RTC unit while syncing time with NTP.

@singleton
class WifiManager:

    def __init__(self): 
        self._time_synced = False

        self._core_conf = ConfigManager().get_config("core")
        self._sta_ssid  = self._core_conf.get("wifi", "sta_ssid", required=True)
        self._sta_pass  = self._core_conf.get("wifi", "sta_pass", required=True)
        self._ap_ssid   = self._core_conf.get("wifi", "ap_ssid" , required=True)
        self._ap_pass   = self._core_conf.get("wifi", "ap_pass" , required=True)

        self._wlan_sta  = network.WLAN(network.STA_IF)
        self._wlan_ap   = network.WLAN(network.AP_IF)

    def initialise(self):
        if not self._ap_ssid or not self._ap_pass:
            raise WifiError("Cannot find AP credentials in config.")
        
        self._wlan_sta.active(True)
        self._wlan_ap.active(True)
        time.sleep_ms(500)
        self.create_AP(self._ap_ssid, self._ap_pass)

        if self._wlan_sta.isconnected():
            print("Wi-Fi already connected. Syncing time...")
            self.sync_time()

        elif self._sta_ssid and self._sta_pass:
            print(f"Connecting with ssid = {self._sta_ssid}")
            self.connect_STA(self._sta_ssid, self._sta_pass)
    
    def connect_STA(self, sta_ssid, sta_pass):
        try:
            self._wlan_sta.connect(sta_ssid, sta_pass)
        except Exception as e:
            raise WifiConnectionError(f"Connection with {sta_ssid} failed: {e}")

        for _ in range(100):
            if not self._wlan_sta.isconnected():
                time.sleep_ms(5)
                continue
            
            if not self._time_synced:
                self.sync_time()

            self._core_conf.set("wifi", "sta_ssid", value=sta_ssid)
            self._core_conf.set("wifi", "sta_pass", value=sta_pass)
            self._core_conf.save()

            return True
        
        raise WifiTimeoutError(f"Wifi connection timeout with {sta_ssid}")

    def create_AP(self, ssid, password):
        self._wlan_ap.active(True)
        self._wlan_ap.config(ssid=ssid, password=password) 

    def sync_time(self, retries=3):
        for i in range(retries):
            try:
                ntptime.settime()
                self._time_synced = True

                # Set timezone in RTC unit
                local_ts = time.time() + TIMEZONE * 60 * 60
                tm = time.localtime(local_ts)

                rtc = RTC()
                rtc.datetime((
                    tm[0], tm[1], tm[2],
                    tm[6],
                    tm[3], tm[4], tm[5],
                    0
                ))

                print("Time synced successfully")

                return
            except OSError as e:
                print(f"NTP sync attempt {i+1} failed: {e}")
                time.sleep(2)  # odczekaj przed kolejną próbą
        raise TimeSyncError("NTP sync failed after retries")
    
    def get_sta_status(self):
        """ Returns status of connected station as an tuple: 
        (connected, ip, mask, gw, dns, rssi, ssid, tx_power) 
        """
        if not self._wlan_sta.active():
            return (False, None, None, None, None, None, None, None)

        connected = self._wlan_sta.isconnected()
        if not connected:
            return (False, None, None, None, None, None, None, None)

        # check https://docs.micropython.org/en/latest/library/network.WLAN.html
        # for full list of useful parameters.
        ip, mask, gw, dns = self._wlan_sta.ifconfig()
        rssi = self._wlan_sta.status('rssi')
        ssid = self._wlan_sta.config('essid')
        tx_power = self._wlan_sta.config('txpower') # dBm
        # wlan_sta.status('channel')
        # ubinascii.hexlify(wlan_sta.config('mac'))
        return connected, ip, mask, gw, dns, rssi, ssid, tx_power

    def get_ap_status(self):
        """ Returns status of access-point as an tuple:
        (connected, ip, mask, gw, ssid, tx_power, client_cnt) 
        """
        if not self._wlan_ap.active():
            return (False, None, None, None, None, None, None)
        
        connected = self._wlan_ap.isconnected()
        
        # check https://docs.micropython.org/en/latest/library/network.WLAN.html
        # for full list of useful parameters.
        ip, mask, gw, dns = self._wlan_ap.ifconfig()
        ssid = self._wlan_ap.config('ssid')
        tx_power = self._wlan_ap.config('txpower') # dBm
        client_cnt = len(self._wlan_ap.status('stations'))
        return connected, ip, mask, gw, ssid, tx_power, client_cnt
    
    def disconnect_STA(self):
        if self._wlan_sta.active():
            self._wlan_sta.disconnect()
            return True
        else:
            return False

    def disconnect_AP(self):
        if self._wlan_ap.active():
            self._wlan_ap.disconnect()
            return True
        else:
            return False

    def is_time_synced(self):
        return self._time_synced

    def scan_stations(self):
        if self._wlan_sta.isconnected():
            return self._wlan_sta.scan()
        return None
    

