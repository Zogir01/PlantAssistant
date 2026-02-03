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

        try:
            self._mode                       = self._dconf.get("mode",                       required=True)#default = self.MODE_MANUAL)
            self._max_valves                 = self._dconf.get("max_valves",                 required=True)#default = 1)
            self._pwm_min                    = self._dconf.get("pwm_min",                    required=True)#default = 20)
            self._pwm_max                    = self._dconf.get("pwm_max",                    required=True)#default = 80)
            self._pump_cooldown_time         = self._dconf.get("pump_cooldown",           required=True)#default = 5000)
            self._amb_temp_thresh            = self._dconf.get("amb_temp_thresh",            required=True)#default = 35)
            self._dht_interval               = self._dconf.get("dht_interval",               required=True)#default = 3000
            self._signal_check_interval      = self._dconf.get("signal_check_interval",   required=True)#default = 2000

        except KeyError as e:
            logger.critical(e)

        if self._mode != self.MODE_AUTO and self._mode != self.MODE_MANUAL:
            self._mode = self.MODE_MANUAL
            logger.error("Invalid mode set in the config for WateringController. Mode is set to MANUAL.")

        self._timer_check_signals   = Neotimer(self._signal_check_interval)      # Interval to check watering signals from PlantPlace
        self._timer_dht_measure     = Neotimer(self._dht_interval)               # Interval to measure from DHT11 sensor.
        self._timer_pump_cooldown   = Neotimer(self._pump_cooldown_time)
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
        return "AUTO" if self._mode == self.MODE_AUTO else "MANUAL"


#endregion

#region public methods

    def update(self):
        self._update_places()
        self._update_sensors()
        self._update_watering()
        self._update_modes()
        
    def switch_to_auto(self) -> bool:
        if self._mode != self.MODE_MANUAL:
            return False
        self._mode = self.MODE_AUTO
        self._dconf.set("mode", value=self.MODE_AUTO)
        self._dconf.save()
        logger.info(f"WateringController switch mode to AUTO.")
        return True
        
    def switch_to_manual(self) -> bool:
        if self._mode != self.MODE_AUTO:
            return False
        self._mode = self.MODE_MANUAL
        self._dconf.set("mode", value=self.MODE_MANUAL)
        self._dconf.save()
        logger.info(f"WateringController switch mode to MANUAL.")
        return True

    def switch_mode(self) -> bool:
        if self._mode == self.MODE_AUTO:
            return self.switch_to_manual()

        elif self._mode == self.MODE_MANUAL:
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
        if self._mode == self.MODE_AUTO:
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
        if self._mode == self.MODE_MANUAL:
            self._manual_cycle()
        
        if self._mode == self.MODE_AUTO:
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
        
        if self._open_valves_count >= self._max_valves:
            return False, "Max valves reached."
        
        return True, ""
    
    def _can_start_watering(self):
        if self._timer_pump_cooldown.started and not self._timer_pump_cooldown.finished():
            remaining = self._timer_pump_cooldown.duration - self._timer_pump_cooldown.get_elapsed()
            return False, f"Pump is in cooldown ({remaining} ms remaining)"
        
        if self._temp > self._amb_temp_thresh:
            return False, f"Ambient temperature ({self._temp}) above threshold ({self._amb_temp_thresh})."

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
            pwm = self._pwm_max

        else:
            pwm = int((self._pwm_max / self._places_count) * self._open_valves_count)
            pwm = clamp(pwm, self._pwm_min, self._pwm_max)

        self._pump.on(pwm)
        logger.debug(f'Pump started with power = {pwm} %.')

#endregion

#region properties-setters and validators


    @validate_integer_conv
    def set_max_valves(self, value):
        if value <= 0:
            raise ValueError("Maksymalna liczba zaworów musi być większa od zera.")
        self._max_valves_temp = value

    @validate_integer_conv
    def set_pwm_min(self, value):
        if not (0 <= value <= 100):
            raise ValueError("Minimalne PWM musi być w zakresie 0–100 %.")
        self._pwm_min_temp = value

    @validate_integer_conv
    def set_pwm_max(self, value):
        if not (0 <= value <= 100):
            raise ValueError("Maksymalne PWM musi być w zakresie 0–100 %.")
        self._pwm_max_temp = value

    @validate_integer_conv
    def set_pump_cooldown_time(self, value):
        if value < 0:
            raise ValueError("Cooldown pompy musi być nieujemny.")
        self._pump_cooldown_time_temp = value

    @validate_integer_conv
    def set_amb_temp_thresh(self, value):
        if value < -40:
            raise ValueError("Próg temperatury otoczenia jest nieprawidłowy.")
        self._amb_temp_thresh_temp = value

    @validate_integer_conv
    def set_dht_interval(self, value):
        if value <= 0:
            raise ValueError("Interwał pomiaru DHT musi być większy od zera.")
        self._dht_interval_temp = value

    @validate_integer_conv
    def set_signal_check_interval(self, value):
        if value <= 0:
            raise ValueError("Interwał sprawdzania sygnałów musi być większy od zera.")
        self._signal_check_interval_temp = value

    def apply_setters(self):
        if not self._mode == self.MODE_MANUAL:
            raise ValueError("Zmiana konfiguracji podlewania jest możliwa tylko w trybie manualnym.")

        # Create copy of parameters
        max_valves               = getattr(self, "_max_valves_temp",               self._max_valves)
        pwm_min                  = getattr(self, "_pwm_min_temp",                  self._pwm_min)
        pwm_max                  = getattr(self, "_pwm_max_temp",                  self._pwm_max)
        pump_cooldown_time       = getattr(self, "_pump_cooldown_time_temp",       self._pump_cooldown_time)
        amb_temp_thresh          = getattr(self, "_amb_temp_thresh_temp",          self._amb_temp_thresh)
        dht_interval             = getattr(self, "_dht_interval_temp",             self._dht_interval)
        signal_check_interval    = getattr(self, "_signal_check_interval_temp",    self._signal_check_interval)

        # Group validation
        if pwm_min > pwm_max:
            raise ValueError("Minimalne PWM nie może być większe od maksymalnego.")

        # if mode not in (self.MODE_MANUAL, self.MODE_AUTO):
        #     raise ValueError("Nieprawidłowy tryb pracy.")

        if max_valves <= 0:
            raise ValueError("Maksymalna liczba zaworów musi być większa od zera.")

        # Apply changes (runtime)
        self._max_valves               = max_valves
        self._pwm_min                  = pwm_min
        self._pwm_max                  = pwm_max
        self._pump_cooldown_time       = pump_cooldown_time
        self._amb_temp_thresh          = amb_temp_thresh
        self._dht_interval             = dht_interval
        self._signal_check_interval    = signal_check_interval

        # Update timer durations
        self._timer_check_signals.duration = signal_check_interval
        self._timer_dht_measure.duration = dht_interval
        self._timer_pump_cooldown.duration = pump_cooldown_time

        # Apply changes in configuration
        self._dconf.set("max_valves",              value=max_valves)
        self._dconf.set("pwm_min",                 value=pwm_min)
        self._dconf.set("pwm_max",                 value=pwm_max)
        self._dconf.set("pump_cooldown",           value=pump_cooldown_time)
        self._dconf.set("amb_temp_thresh",         value=amb_temp_thresh)
        self._dconf.set("dht_interval",            value=dht_interval)
        self._dconf.set("signal_check_interval",   value=signal_check_interval)
        self._dconf.save()

        # Remove temporary attributes
        for attr in [
            "_max_valves_temp", "_pwm_min_temp", "_pwm_max_temp",
            "_pump_cooldown_time_temp", "_amb_temp_thresh_temp", "_dht_interval_temp",
            "_signal_check_interval_temp"
        ]:
            if hasattr(self, attr):
                delattr(self, attr)


#endregion
