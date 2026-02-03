from app.water import WateringController
from app.light import LEDController
from app.config_validators import validate_bool_conv, validate_integer_conv, validate_time_conv
from core.config import ConfigManager
from core.power import PowerManager
from core.logging import logger
from core.wifi import WifiManager
from core.neotimer import Neotimer
from core.helpers import get_time, parse_time

class DeviceController:

    def __init__(self, water_ctrl : WateringController, led_ctrl : LEDController):
        self.led_ctrl = led_ctrl
        self.water_ctrl = water_ctrl
        self._power_mng = PowerManager()
        self._dconf = ConfigManager().get_config("device")
        self._wifi = WifiManager()
 
        # Load user configuration from filesystem, if errors set defaults.
        try:
            self._enable_telemetry           = self._dconf.get("enable_telemetry",         required=True)#default = False)
            self._telemetry_interval         = self._dconf.get("telemetry_interval",    required=True)#default = 10)
            self._enable_energy_save_mode    = self._dconf.get("enable_energy_save_mode",  required=True)#default = True)
            self._min_dsleep_time            = self._dconf.get("min_dsleep_time",       required=True)#default = 600000) # 10 min
            self._enable_work_schedule       = self._dconf.get("enable_work_schedule",     required=True)#default = True)
            self._work_schedule_from         = self._dconf.get("work_schedule_from",       required=True)#default = "00:00")
            self._work_schedule_to           = self._dconf.get("work_schedule_to",         required=True)#default = "24:00")
            self._schedule_interval          = self._dconf.get("schedule_interval",     required=True)#default = 5000
        except KeyError as e:
            logger.critical(e)

        # self._timer_history_flush       = Neotimer(20000)
        # self._timer_logging_flush       = Neotimer(10000)
        self._timer_check_schedule      = Neotimer(self._schedule_interval)
        self._timer_send_telemetry      = Neotimer(self._telemetry_interval)

        self._disabled_by_schedule = set()

        if self._enable_telemetry:
            logger.info("Telemetry is enabled. Disabling logger...")
            logger.disable()

        if self._power_mng.was_wakeup_from_sleep():
            pass

    def update(self):
        self.water_ctrl.update()

        if self._can_set_schedule() and self._timer_check_schedule.repeat_execution():
            if not self._cur_time_in_range(self._work_schedule_from, self._work_schedule_to):
                logger.info("Turning off the controllers via the set work schedule.")
                self.water_ctrl.switch_to_manual()
            
        if self._can_energy_save_mode():

            ds_time = self._get_deep_sleep_time()
            if ds_time:
                self._power_mng.sleep_ms(ds_time)
                
        if self._enable_telemetry and self._timer_send_telemetry.repeat_execution():
            self._send_telemetry()
            #send_telemetry(self.plants[0]._hum_percent, self.plants[0]._hum_raw, self.plants[0]._sample_raw)
        
    def _can_set_schedule(self):
        if not self._enable_work_schedule:
            return False
        
        if not self._wifi.is_time_synced():
            return False
        
        return True
    
    def _cur_time_in_range(self, r_from : str, r_to : str):
        """ Returns True if current time is in (r_from, r_to) range. 
        Range variables must be in format HH:MM. """
        cur_h, cur_m = parse_time(get_time())
        r_from_h, r_from_m = parse_time(r_from)
        r_to_h, r_to_m = parse_time(r_to)

        cur_total_m = cur_h * 60 + cur_m 
        from_total_m = r_from_h * 60 + r_from_m 
        to_total_m = r_to_h * 60 + r_to_m 

        if from_total_m <= to_total_m:
            # normal range, e.g. 08:00-20:00
            return from_total_m <= cur_total_m < to_total_m
        else:
            # over-night range, e.g. 22:00-06:00
            return cur_total_m >= from_total_m or cur_total_m > to_total_m # return cur_minutes >= from_minutes or cur_minutes < to_minutes

    def _can_energy_save_mode(self):
        if not self._enable_energy_save_mode:
            return False
        
        if not self.water_ctrl.is_fully_idle():
            return False
        
        if self.led_ctrl.isEnabled():
            return False
        
        return True
        
    def _get_deep_sleep_time(self):
        if not self._can_energy_save_mode():
            return 0
        
        min_idle_time = self.water_ctrl.get_min_idle_time()

        if min_idle_time <= self._min_dsleep_time:
            return 0
        
        return min_idle_time

    def _send_telemetry(self):
        telemetry_str = self.water_ctrl._places[0].get_telemetry_data()
        print(telemetry_str)


#region properties-setters and validators

    # ---------------- TELEMETRY ----------------
    @validate_bool_conv
    def set_enable_telemetry(self, value):
        self._enable_telemetry_temp = value

    @validate_integer_conv
    def set_telemetry_interval(self, value):
        if value <= 0:
            raise ValueError("Interwał telemetrii musi być większy od zera.")
        self._telemetry_interval_temp = value

    # ---------------- ENERGY SAVE ----------------
    @validate_bool_conv
    def set_enable_energy_save_mode(self, value):
        self._enable_energy_save_mode_temp = value

    # ---------------- DEEP SLEEP ----------------
    @validate_integer_conv
    def set_min_dsleep_time(self, value):
        if value < 0:
            raise ValueError("Minimalny czas deep-sleep musi być nieujemny.")
        self._min_dsleep_time_temp = value

    # ---------------- WORK SCHEDULE ----------------
    @validate_bool_conv
    def set_enable_work_schedule(self, value):
        self._enable_work_schedule_temp = value

    @validate_time_conv
    def set_work_schedule_from(self, value):
        self._work_schedule_from_temp = value

    @validate_time_conv
    def set_work_schedule_to(self, value):
        self._work_schedule_to_temp = value

    @validate_integer_conv
    def set_schedule_interval(self, value):
        if value <= 0:
            raise ValueError("Interwał harmonogramu musi być większy od zera.")
        self._schedule_interval_temp = value

    def apply_setters(self):
        # Load temporary or current values
        enable_telemetry        = getattr(self, "_enable_telemetry_temp",           self._enable_telemetry)
        telemetry_interval      = getattr(self, "_telemetry_interval_temp",         self._telemetry_interval)
        enable_energy_save_mode = getattr(self, "_enable_energy_save_mode_temp",    self._enable_energy_save_mode)
        min_dsleep_time         = getattr(self, "_min_dsleep_time_temp",            self._min_dsleep_time)
        enable_work_schedule    = getattr(self, "_enable_work_schedule_temp",       self._enable_work_schedule)
        work_schedule_from      = getattr(self, "_work_schedule_from_temp",         self._work_schedule_from)
        work_schedule_to        = getattr(self, "_work_schedule_to_temp",           self._work_schedule_to)
        schedule_interval       = getattr(self, "_schedule_interval_temp",          self._schedule_interval)

        # Group validation
        if enable_work_schedule:
            # time format validated earlier, here we validate logical consistency
            h1, m1 = parse_time(work_schedule_from)
            h2, m2 = parse_time(work_schedule_to)
            total1 = h1*60 + m1
            total2 = h2*60 + m2

            if total1 == total2:
                raise ValueError("Zakres pracy nie może mieć identycznego czasu początku i końca.")

        # Telemetry must not conflict with energy saving
        if enable_energy_save_mode and enable_telemetry:
            # Depending on logic you want:
            # raise ValueError("Tryb oszczędzania energii nie może być aktywny z włączoną telemetrią.")
            pass

        # Apply changes (runtime)
        self._enable_telemetry          = enable_telemetry
        self._telemetry_interval        = telemetry_interval
        self._enable_energy_save_mode   = enable_energy_save_mode
        self._min_dsleep_time           = min_dsleep_time
        self._enable_work_schedule      = enable_work_schedule
        self._work_schedule_from        = work_schedule_from
        self._work_schedule_to          = work_schedule_to
        self._schedule_interval         = schedule_interval

        if self._enable_telemetry:
            logger.disable()
        else:
            logger.enable()

        # Update timer durations
        self._timer_check_schedule.duration = schedule_interval
        self._timer_send_telemetry.duration = telemetry_interval

        # Apply changes in configuration
        self._dconf.set("enable_telemetry",          value=enable_telemetry)
        self._dconf.set("telemetry_interval",        value=telemetry_interval)
        self._dconf.set("enable_energy_save_mode",   value=enable_energy_save_mode)
        self._dconf.set("min_dsleep_time",           value=min_dsleep_time)
        self._dconf.set("enable_work_schedule",      value=enable_work_schedule)
        self._dconf.set("work_schedule_from",        value=work_schedule_from)
        self._dconf.set("work_schedule_to",          value=work_schedule_to)
        self._dconf.set("schedule_interval",         value=schedule_interval)
        self._dconf.save()

        # Remove temporary attributes
        for attr in [
            "_enable_telemetry_temp",
            "_telemetry_interval_temp",
            "_enable_energy_save_mode_temp",
            "_min_dsleep_time_temp",
            "_enable_work_schedule_temp",
            "_work_schedule_from_temp",
            "_work_schedule_to_temp",
            "_schedule_interval_temp",
        ]:
            if hasattr(self, attr):
                delattr(self, attr)

#endregion

        
