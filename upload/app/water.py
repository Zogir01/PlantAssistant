from drivers.water_pump import WaterPump
from app.place import PlantPlace
from app.config_validators import validate_integer_conv
from core.config import ConfigManager
from core.logging import logger
from core.neotimer import Neotimer
from drivers.float_switch import FloatSwitch
from core.helpers import clamp
from dht import DHT11

class WateringController:
    MODE_AUTO = 1
    MODE_MANUAL = 2

#region constructor

    def __init__(self, pump: WaterPump, dht: DHT11, places: list[PlantPlace], water_sensor : FloatSwitch):
        self._pump = pump
        self._dht = dht
        self._water_sens = water_sensor
        self._dconf = ConfigManager().get_config("water")
        self._places = places
        self._places_count = len(places)
        self._watering_status = {} # Status of currently watered PlantPlace`s.
        self._currently_watered = set()
        self._open_valves_count = 0 
        self._hum = None
        self._temp = None

        if self.mode != self.MODE_AUTO and self.mode != self.MODE_MANUAL:
            self.mode = self.MODE_MANUAL
            logger.error("Invalid mode set in the config for WateringController. Mode is set to MANUAL.")

        self._timer_check_signals   = Neotimer(self.signal_check_interval)      # Interval to check watering signals from PlantPlace
        self._timer_dht_measure     = Neotimer(self.dht_interval)               # Interval to measure from DHT11 sensor.
        self._timer_pump_cooldown   = Neotimer(self.pump_cooldown_time)
        self._watering_timers = {}

        for p in self._places:
            self._watering_timers[p.id] = Neotimer(0) # Setting 0 because this time is variable.

        self._measure_environment()

#endregion

#region properties

    @property
    def open_valves_count(self):
        return self._open_valves_count
    
    @property
    def last_amb_humidity(self):
        return self._hum
    
    @property
    def last_amb_temperature(self):
        return self._temp
    
    @property
    def water_in_tank(self):
        return self._water_sens.is_on()
    
    @property
    def current_power(self):
        return self._pump.get_power(precision=0)
    
    @property
    def current_mode(self):
        return "AUTO" if self.mode == self.MODE_AUTO else "MANUAL"

#endregion

#region configuration properties-getters

    @property
    def mode(self):
        return self._dconf.get('mode')

    @property
    def pwm_min(self):
        return self._dconf.get('pwm_min')

    @property
    def pwm_max(self):
        return self._dconf.get('pwm_max')

    @property
    def max_valves(self):
        return self._dconf.get('max_valves')

    @property
    def pump_cooldown(self):
        return self._dconf.get('pump_cooldown')

    @property
    def amb_temp_thresh(self):
        return self._dconf.get('amb_temp_thresh')

    @property
    def dht_interval(self):
        return self._dconf.get('dht_interval')

    @property
    def signal_check_interval(self):
        return self._dconf.get('signal_check_interval')

#endregion

#region public methods

    def update(self):
        self._update_places()
        self._update_sensors()
        self._update_watering()
        self._update_modes()
        
    def switch_to_auto(self) -> bool:
        if self.mode != self.MODE_MANUAL:
            return False
        self.mode = self.MODE_AUTO
        self._dconf.set("mode", value=self.MODE_AUTO)
        self._dconf.save()
        logger.info(f"WateringController switch mode to AUTO.")
        return True
        
    def switch_to_manual(self) -> bool:
        if self.mode != self.MODE_AUTO:
            return False
        self.mode = self.MODE_MANUAL
        self._dconf.set("mode", value=self.MODE_MANUAL)
        self._dconf.save()
        logger.info(f"WateringController switch mode to MANUAL.")
        return True

    def switch_mode(self) -> bool:
        if self.mode == self.MODE_AUTO:
            return self.switch_to_manual()

        elif self.mode == self.MODE_MANUAL:
            return self.switch_to_auto()

    def is_fully_idle(self) -> bool:
        if self._pump.is_on():
            return False

        for p in self._places:
            if p.is_enabled() and not p.is_idle():
                return False
            
        return True
    
    def get_min_idle_time(self) -> int:
        idle_plants = [p for p in self._places if p.is_idle()]

        if not idle_plants:
            return None
        
        return min(ip.remaining_idle_time for ip in idle_plants)

    def start_manual_watering(self, place: PlantPlace, duration):        
        if self.mode == self.MODE_AUTO:
            logger.error("Cannot start manual watering in AUTO mode.")
            return False

        success, reason = self._start_watering(place, duration)
        if not success:
            return False, f"Cannot start manual watering for {place.id}, reason: {reason}"
        
        return True, f"Watering for {place.id} started."

    def is_watering(self) -> bool:
        return len(self._currently_watered) > 0

    def stop_all_watering(self):
        for place_id in self._currently_watered:
            self._stop_watering(self._get_place(place_id))
        self._pump.off() # to be 100% sure
        
#endregion

#region private methods

    def _get_place(self, place_id) -> PlantPlace:
        for p in self._places:
            if p.id == place_id:
                return p

    def _update_places(self):
        for p in self._places:
            p.update()

    def _update_sensors(self):
        if self._timer_dht_measure.repeat_execution():
            self._measure_environment()

    def _update_watering(self):
        for place_id in self._currently_watered:
            self._do_watering(self._get_place(place_id))

    def _update_modes(self):
        if self.mode == self.MODE_MANUAL:
            self._manual_cycle()
        
        if self.mode == self.MODE_AUTO:
            self._auto_cycle()

    def _manual_cycle(self):
        pass

    def _auto_cycle(self): 
        if self._timer_check_signals.repeat_execution():
            logger.debug("Checking watering signals from PlantPlace`s.")

            for p in self._places:
                if not p.need_watering:
                    continue
                
                desired_time = p.desired_watering_time # If necessary, desired can be conditionally reduced or increased 
                success, reason = self._start_watering(p, desired_time)
                if not success:
                    logger.error(f"Cannot start automatic watering for {p.id}, reason: {reason}")
                    continue
                logger.info(f"Watering process for {p.id} started.")

    def _measure_environment(self):
        self._dht.measure()
        self._hum = self._dht.humidity()
        self._temp = self._dht.temperature()

    def _can_start_watering_place(self, p: PlantPlace):
        if not p.is_enabled():
            return False, "Place is not enabled."
        
        if p.id in self._currently_watered:
            return False, "Place is currently watered."
        
        if self._open_valves_count >= self.max_valves:
            return False, "Max valves reached."
        
        return True, ""
    
    def _can_start_watering(self):
        if self._timer_pump_cooldown.started and not self._timer_pump_cooldown.finished():
            remaining = self._timer_pump_cooldown.duration - self._timer_pump_cooldown.get_elapsed()
            return False, f"Pump is in cooldown ({remaining} ms remaining)"
        
        if self._temp > self.amb_temp_thresh:
            return False, f"Ambient temperature ({self._temp}) above threshold ({self.amb_temp_thresh})."

        if self._water_sens.is_off():
          return False, "No water in the tank."

        return True, ""

    def _start_watering(self, p: PlantPlace, duration):
        success, reason = self._can_start_watering()
        if not success: return False, reason

        success, reason = self._can_start_watering_place(p)
        if not success: return False, reason

        self._watering_timers[p.id].duration = duration
        self._watering_timers[p.id].start()
        
        if not p.open_valve():
            return False, f"Cannot open valve for {p.id}!"

        self._currently_watered.add(p.id)
        self._open_valves_count += 1
        self._regulate_pwm()

        return True, ""
    
    def _do_watering(self, p: PlantPlace):
        if self._watering_timers[p.id].finished():
            self._stop_watering(p)

    def _stop_watering(self, p: PlantPlace):
        total_elapsed = self._watering_timers[p.id].get_elapsed()

        self._currently_watered.remove(p.id)
        self._open_valves_count -= 1

        if not p.close_valve():
            logger.critical(f"Cannot close valve for {p.id}!")

        logger.info(f"Watering for {p.id} stopped.")
        self._regulate_pwm()

    def _regulate_pwm(self):
        """ Regulate pwm of pump based on how many valves are opened. """
        if self._places_count <= 0 or self._open_valves_count < 0:
            return
        
        if self._open_valves_count == 0:
            pwm = 0
            if self._pump.is_on():
                self._timer_pump_cooldown.start()

        elif self._open_valves_count == 1:
            pwm = self.pwm_max

        else:
            pwm = int((self.pwm_max / self._places_count) * self._open_valves_count)
            pwm = clamp(pwm, self.pwm_min, self.pwm_max)

        self._pump.on(pwm)
        logger.debug(f'Pump started with power = {pwm} %.')

#endregion
