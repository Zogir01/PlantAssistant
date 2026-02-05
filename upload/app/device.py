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

        # self._timer_history_flush       = Neotimer(20000)
        # self._timer_logging_flush       = Neotimer(10000)
        self._timer_check_schedule      = Neotimer(self.schedule_interval)
        self._timer_send_telemetry      = Neotimer(self.telemetry_interval)

        self._disabled_by_schedule = set()

        if self.enable_telemetry:
            logger.info("Telemetry is enabled. Disabling logger...")
            logger.disable()

        if self._power_mng.was_wakeup_from_sleep():
            pass

#region configuration properties-getters

    @property
    def enable_telemetry(self):
        return self._dconf.get('enable_telemetry')

    @property
    def telemetry_interval(self):
        return self._dconf.get('telemetry_interval')

    @property
    def enable_energy_save_mode(self):
        return self._dconf.get('enable_energy_save_mode')

    @property
    def min_dsleep_time(self):
        return self._dconf.get('min_dsleep_time')

    @property
    def enable_work_schedule(self):
        return self._dconf.get('enable_work_schedule')

    @property
    def work_schedule_from(self):
        return self._dconf.get('work_schedule_from')

    @property
    def work_schedule_to(self):
        return self._dconf.get('work_schedule_to')

    @property
    def schedule_interval(self):
        return self._dconf.get('schedule_interval')
    
#endregion

    def update(self):
        self.water_ctrl.update()

        if self._can_set_schedule() and self._timer_check_schedule.repeat_execution():
            if not self._cur_time_in_range(self.work_schedule_from, self.work_schedule_to):
                logger.info("Turning off the controllers via the set work schedule.")
                self.water_ctrl.switch_to_manual()
            
        if self._can_energy_save_mode():

            ds_time = self._get_deep_sleep_time()
            if ds_time:
                self._power_mng.sleep_ms(ds_time)
                
        if self.enable_telemetry and self._timer_send_telemetry.repeat_execution():
            self._send_telemetry()
            #send_telemetry(self.plants[0]._hum_percent, self.plants[0]._hum_raw, self.plants[0]._sample_raw)
        
    def _can_set_schedule(self):
        if not self.enable_work_schedule:
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
        if not self.enable_energy_save_mode:
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

        if min_idle_time <= self.min_dsleep_time:
            return 0
        
        return min_idle_time

    def _send_telemetry(self):
        telemetry_str = self.water_ctrl._places[0].get_telemetry_data()
        print(telemetry_str)
