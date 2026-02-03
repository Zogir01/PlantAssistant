from app.device import DeviceController
from app.place import PlantPlace
from core.config import ConfigManager
from core.wifi import WifiManager
from core.logging import logger
from core import system
from core.helpers import s_to_ms, ms_to_s, min_to_ms, ms_to_min

class DeviceAPI:

    def __init__(self, device : DeviceController):
        self._device = device

    def _get_plant(self, place_id) -> PlantPlace:
        for p in self._device.water_ctrl._places:
            if p.id == place_id:
                return p
            
    #region Decorators - validators

    def _validate_request(func):
        def wrapper(self, v):
            if not len(v):
                return False, "Parameters not found in request."   
            return func(self, v)
        return wrapper
    
    def _validate_plant_request(func):
        def wrapper(self, v):
            if not len(v):
                return False, "Parameters not found in request."   
            if "place_id" not in v:
                return False, "place_id not found in request."
            return func(self, v)
        return wrapper
    
    def _not_allowed_in_AP(func):
        def wrapper(self, *args, **kwargs):
            if WifiManager().get_ap_status()[0]:
                logger.warning("The received request cannot be handled in access point mode.")
                return False, "Nie dozwolone w trybie AP."
            return func(self, *args, **kwargs)
        return wrapper
    
    def _handle_errors(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                logger.exception(e)
                return False, "Wystąpił nieoczekiwany błąd serwera."
        return wrapper
    
    #endregion

    #region Configuration

    @_not_allowed_in_AP
    @_validate_request
    def update_config(self, v):
        """HTTP API method. """
        try:
            if "core" in v:     pass # Updating core configuration is currently not supported
            if "device" in v:   self._update_device_config(v["device"])
            if "watering" in v: self._update_watering_config(v["watering"])
            if "place1" in v:   self._update_place_config("place1", v["place1"])
            if "place2" in v:   self._update_place_config("place2", v["place2"])
            if "place3" in v:   self._update_place_config("place3", v["place3"])
            if "light" in v:    self._update_light_config(v["light"])
            logger.info("Configuration updated successfully.")
            return True, "OK"

        except Exception as e:
            logger.error(f"Exception occured while updating config: {e}.")
            return False, str(e) 
        
    def _update_place_config(self, place_id, v):
        place = self._get_plant(place_id)
        if "hum_threshold" in v:                place.set_hum_threshold             (int(v["hum_threshold"]))
        if "hum_target" in v:                   place.set_hum_target                (int(v["hum_target"]))
        if "min_watering_time" in v:            place.set_min_watering_time         (s_to_ms(int(v["min_watering_time"])))
        if "max_watering_time" in v:            place.set_max_watering_time         (s_to_ms(int(v["max_watering_time"])))
        if "wait_for_valve_time" in v:          place.set_wait_for_valve_time       (min_to_ms(int(v["wait_for_valve_time"])))
        if "post_watering_delay" in v:          place.set_post_watering_delay       (min_to_ms(int(v["post_watering_delay"])))
        if "measurement_interval" in v:         place.set_measurement_interval      (min_to_ms(int(v["measurement_interval"])))
        if "min_adc" in v:                      place.set_min_adc                   (int(v["min_adc"]))
        if "max_adc" in v:                      place.set_max_adc                   (int(v["max_adc"]))
        if "sample_count" in v:                 place.set_sample_count              (int(v["sample_count"]))
        if "sample_interval" in v:              place.set_sample_interval           (int(v["sample_interval"]))
        place.apply_setters()

    def _update_watering_config(self, v):
        ctrl = self._device.water_ctrl
        if "max_valves" in v:                   ctrl.set_max_valves                 (int(v["max_valves"]))
        if "pwm_min" in v:                      ctrl.set_pwm_min                    (int(v["pwm_min"]))
        if "pwm_max" in v:                      ctrl.set_pwm_max                    (int(v["pwm_max"]))
        if "pump_cooldown" in v:                ctrl.set_pump_cooldown_time         (min_to_ms(int(v["pump_cooldown"])))
        if "amb_temp_thresh" in v:              ctrl.set_amb_temp_thresh            (int(v["amb_temp_thresh"]))
        if "dht_interval_ms" in v:              ctrl.set_dht_interval               (min_to_ms(int(v["dht_interval"])))
        if "signal_check_interval" in v:        ctrl.set_signal_check_interval      (int(v["signal_check_interval"]))
        ctrl.apply_setters()

    def _update_device_config(self, v):
        ctrl = self._device
        if "enable_telemetry" in v:             ctrl.set_enable_telemetry           (True if v["enable_telemetry"] == "true" else False)
        if "telemetry_interval_ms" in v:        ctrl.set_telemetry_interval         (int(v["telemetry_interval"]))
        if "enable_energy_save_mode" in v:      ctrl.set_enable_energy_save_mode    (True if v["enable_energy_save_mode"] == "true" else False)
        if "min_dsleep_time_ms" in v:           ctrl.set_min_dsleep_time            (min_to_ms(int(v["min_dsleep_time"])))
        if "enable_work_schedule" in v:         ctrl.set_enable_work_schedule       (True if v["enable_work_schedule"] == "true" else False)
        if "work_schedule_from" in v:           ctrl.set_work_schedule_from         (v["work_schedule_from"])
        if "work_schedule_to" in v:             ctrl.set_work_schedule_to           (v["work_schedule_to"])
        if "schedule_interval_ms" in v:         ctrl.set_schedule_interval          (int(v["schedule_interval"]))
        ctrl.apply_setters()

    def _update_light_config(self, v):
        ctrl = self._device.led_ctrl
        if "enabled" in v:                      ctrl.set_enabled                    ((True if v["enabled"] == "true" else False))
        if "threshold" in v:                    ctrl.set_threshold                  (int(v["threshold"]))
        if "avg_count" in v:                    ctrl.set_avg_count                  (int(v["avg_count"]))
        ctrl.apply_setters()

    def get_config(self):
        """ HTTP API method. Return all device config from .json files. """
        return {
            "core"   :      self._device._dconf.get("core"),
            "device" :      self._get_device_config(),
            "watering" :    self._get_watering_config(),
            "place1" :      self._get_place_config("place1"),
            "place2" :      self._get_place_config("place2"),
            "place3" :      self._get_place_config("place3"),
            "light" :       self._get_light_config()
        }

    def _get_place_config(self, place_id):
        pconf = ConfigManager().get_config("places").get(place_id).copy()
        pconf["measurement_interval"]   = ms_to_min(pconf["measurement_interval"])
        pconf["post_watering_delay"]    = ms_to_min(pconf["post_watering_delay"])
        pconf["wait_for_valve_time"]    = ms_to_min(pconf["wait_for_valve_time"])
        pconf["min_watering_time"]      = ms_to_s(pconf["min_watering_time"])
        pconf["max_watering_time"]      = ms_to_s(pconf["max_watering_time"])
        return pconf
        
    def _get_watering_config(self):
        pconf = ConfigManager().get_config("water").get().copy()
        pconf["pump_cooldown"]      = ms_to_min(pconf["pump_cooldown"])
        pconf["dht_interval"]       = ms_to_min(pconf["dht_interval"])
        return pconf
    
    def _get_device_config(self):
        pconf = ConfigManager().get_config("device").get().copy()
        pconf["min_dsleep_time"]    = ms_to_min(pconf["min_dsleep_time"])
        return pconf
    
    def _get_light_config(self):
        pconf = ConfigManager().get_config("light").get().copy()
        return pconf
    
    #endregion

    #region Status

    @_handle_errors
    def get_status(self):
        ''' HTTP API method. '''

        place_state_pl_translation = {
            "STATE_DISABLED"            : "Wyłączone",
            "STATE_IDLE"                : "Bezczynne",
            "STATE_MEASURING"           : "Pomiar wilgotności",
            "STATE_PENDING_WATERING"    : "Potrzeba podlania",
            "STATE_WATERING"            : "Podlewanie",
            "STATE_POST_WATERING"       : "Stabilizacja po podlaniu"
        }

        wc = self._device.water_ctrl
        d = self._device

        status = {}
        for p in self._device.water_ctrl._places:
            status[p.id] = {
                "place_id"                          : p.id,
                "enabled"                           : p.is_enabled(),
                "state_name"                        : place_state_pl_translation[p.current_state],
                "need_watering"                     : p.need_watering,
                "valve_open"                        : p.valve_open,
                "humidity"                          : round(p.last_humidity, 1),
                "humidity_timestamp"                : p.last_humidity_timestamp,
                "evaluated_watering_time"           : round(ms_to_s(p.evaluated_watering_time), 1) if p.evaluated_watering_time else None,
                "evaluated_watering_efficiency"     : round(p.evaluated_watering_efficiency, 1),
                "evaluated_watering_timestamp"      : p.evaluated_watering_timestamp,
                "desired_watering_time"             : round(ms_to_s(p.desired_watering_time), 1) if p.desired_watering_time else None,
            }
        status["watering"] = {
            "is_watering"       : wc.is_watering(),
            "current_power"     : wc.current_power,
            "amb_humidity"      : wc.last_amb_humidity,
            "amb_temperature"   : wc.last_amb_temperature,
            "water_in_tank"     : wc.water_in_tank,
            "current_mode"      : wc.current_mode
        }
        status["device"] = {
            "schedule_active"   : d._enable_work_schedule,
            "telemetry_active"  : d._enable_telemetry,
            "energy_save_active": d._enable_energy_save_mode
        }

        return status
    
    @_handle_errors
    def get_system_info(self):
        chip = system.chip_info()
        mem = system.mem_info()
        fs = system.fs_info()
        return {
            "chip" : {
                "platform"      : chip[0],
                "ver"           : chip[1],
                "machine_id"    : chip[2],
                "cpu_freq"      : chip[3]
            },
            "mem" : {
                "ram_alloc_B"   : mem[0],
                "ram_free_B"    : mem[1],
                "flash_size_B"  : mem[2]
            },
            "fs" : {
                "total_KB"      : fs[3],
                "free_KB"       : fs[4]
            }
        }

    #endregion

    #region Control

    @_not_allowed_in_AP
    @_validate_plant_request
    @_handle_errors
    def start_manual_watering(self, v):
        ''' HTTP API method. Start manual watering for `place_id` given in http request. '''
        if "duration" not in v:
            return False, "Brak wymaganego parametru: duration."
        
        try: 
            duration_ms = s_to_ms(int(v["duration"]))
        except: 
            return False, "Parametr duration jest błędny."

        s, r = self._device.water_ctrl.start_manual_watering(self._get_plant(v["place_id"]), duration_ms)
        if not s: return s, r
            
        return True, "Udało się rozpocząć manualne podlewanie."
    
    @_not_allowed_in_AP
    @_validate_plant_request
    @_handle_errors
    def toggle_place(self, v):
        self._get_plant(v["place_id"]).switch_active()
        return True
    
    @_not_allowed_in_AP
    @_handle_errors
    def toggle_watering_mode(self, v):
        self._device.water_ctrl.switch_mode()
        return True

    @_handle_errors
    def stop_watering(self, v):
        ''' HTTP API method. Stop manual watering for `place_id` given in http request. '''
        self._device.water_ctrl.stop_all_watering()
        return True

    # @_not_allowed_in_AP
    # @_validate_plant_request
    # @_handle_errors
    # def enable_plant(self, v):
    #     ''' HTTP API method. Enable plant with given `place_id` in http request. '''
    #     print("tesststststs")
    #     self._get_plant(v["place_id"]).enable()
    #     return True


    # @_validate_plant_request
    # @_handle_errors
    # def disable_plant(self, v):
    #     ''' HTTP API method. Disable plant with given `place_id` in http request. '''
    #     self._get_plant(v["place_id"]).disable()
    #     return True
    
    # @_validate_plant_request
    # @_handle_errors
    # def update_measure(self, v):
    #     ''' HTTP API method. Disable plant with given `place_id` in http request. '''
    #     # self._get_plant(v["place_id"]).disable()
    #     return True

    #endregion

    #region Wi-Fi

    @_handle_errors
    def get_wifi_status(self):
        ''' HTTP API method. Return dictionary about current wifi status. '''
        wifi_mng = WifiManager()
        sta = wifi_mng.get_sta_status()
        ap = wifi_mng.get_ap_status()

        return {
            "sta" : {
                "connected"     : sta[0],
                "ip"            : sta[1],
                "mask"          : sta[2],
                "gw"            : sta[3],
                "dns"           : sta[4],
                "rssi"          : sta[5],
                "ssid"          : sta[6],
                "tx_power"      : sta[7]
            },
            "ap" : {
                "connected"     : ap[0],
                "ip"            : ap[1],
                "mask"          : ap[2],
                "gw"            : ap[3],
                "ssid"          : ap[4],
                "tx_power"      : ap[5],
                "client_cnt"    : ap[6]
            }
        }
    
    @_handle_errors
    def get_wifi_stations(self):
        ''' HTTP API method. Returns dictionary with available stations in range. '''
        wifi_mng = WifiManager()
        wifi_stations = {}
        for (ssid, bssid, channel, RSSI, security, hidden) in wifi_mng.scan_stations():
            wifi_stations[ssid] = {
                "ssid" : ssid,
                "RSSI" : RSSI, # RSSI - siła sygnału, można wyświetlic na froncie obrazkowo lub tekstowo
                "security" : security
            }
        return wifi_stations
    
    #@_validate_request # do sprawdzenia - chyba powodowało błąd
    @_handle_errors
    def connect_wifi(self, v):
        for p in self._device.plant_ctrls:
            if p.is_enabled():
                return False, f"Nie można połączyć z nową siecią gdy {p.id} jest odblokowane."
            
        if "ssid" not in v or "password" not in v:
            return False, "Błędne zapytanie"

        # Try connect with ssid and password from request.
        if WifiManager().connect_STA(v["ssid"], v["password"]):
            return True, "Udalo sie polaczyc z nowa siecia."
        
        return False, "Nie udalo sie polaczyc z siecia."
            
        