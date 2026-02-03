from app.config_validators import validate_integer_conv
from core.state_machine import StateMachine
from core.config import ConfigManager
from core.logging import logger
from core.neotimer import Neotimer
from drivers.soil_sensor import SoilSensor
from drivers.valve import Valve
from drivers.button import Button
from core.helpers import clamp, get_timestamp

class PlantPlace:
    
#region constructor

    TIME_MULTIPLIER = 100 # Variable for tests. Set this to 1 in non-testing.

    def __init__(self, id, valve: Valve, soil_sens: SoilSensor, on_off_button : Button):
        self.id = id
        self._valve = valve
        self._soil_sens = soil_sens
        self._btn = on_off_button
        self._sm = StateMachine()
        self._dconf = ConfigManager().get_config("places")

        # FSM states
        self.DISABLED         = self._sm.add_state(self._state_disabled,         "STATE_DISABLED")
        self.IDLE             = self._sm.add_state(self._state_idle,             "STATE_IDLE")
        self.MEASURING        = self._sm.add_state(self._state_measuring,        "STATE_MEASURING")
        self.PENDING_WATERING = self._sm.add_state(self._state_pending_watering, "STATE_PENDING_WATERING")
        self.WATERING         = self._sm.add_state(self._state_watering,         "STATE_WATERING")
        self.POST_WATERING    = self._sm.add_state(self._state_post_watering,    "STATE_POST_WATERING")

        # Watering variables
        self._need_watering = None               # Flag to notify watering need (for WateringController or user)
        self._watering_time_ms = None            # Time of last watering
        self._watering_timestamp = None          # Timestamp of last watering in ISO 8601 format
        self._desired_watering_time_ms = None    # Suggested watering time based on the effectiveness of the last watering
        self._correction = None                  # Current correction added to desired watering time after last watering.     
        self._correction_add = False             # Helper variable to detect added correction   
        self._correction_factor = 2              # Proportional factor of P-type correction regulation

        self._evaluated_watering_time_ms = None
        self._evaluated_watering_timestamp = None
        self._evaluated_watering_efficiency = None         # How much gain of humidity for 1 s of watering

        # Humidity measurement variables
        self._samples = []
        self._next_sample_ms = None
        self._last_raw = None
        self._avg_raw = None
        self._hum_percent = None
        self._hum_previous = None       
        self._hum_delta = None                  # Difference between previous humidity and current humidity measurement.
        self._hum_timestamp = None              # Timestamp of last humidity measurement in ISO 8601 format.
        self._hum_desired = None                # How much humidity we must gain from current humidity to target humidity. 

        # Callbacks
        self.on_measure_finished = None
        self.on_watering_finished = None

        # User configuration
        try:
            enabled                          = self._dconf.get(id, "enabled",                required=True)#default = False)
            self._hum_threshold              = self._dconf.get(id, "hum_threshold",          required=True)#default = 50)
            self._hum_target                 = self._dconf.get(id, "hum_target",             required=True)#default = 80)
            self._min_watering_time          = self._dconf.get(id, "min_watering_time",      required=True)#default = s_to_ms(1))
            self._max_watering_time          = self._dconf.get(id, "max_watering_time",      required=True)#default = s_to_ms(5))
            self._wait_for_valve_time        = self._dconf.get(id, "wait_for_valve_time",    required=True)#default = s_to_ms(2))
            self._post_watering_delay        = self._dconf.get(id, "post_watering_delay",    required=True)#default = s_to_ms(1))
            self._measurement_interval       = self._dconf.get(id, "measurement_interval",   required=True)#default = 10)
            self._min_adc                    = self._dconf.get(id, "min_adc",                required=True)#default = 1200)
            self._max_adc                    = self._dconf.get(id, "max_adc",                required=True)#default = 3000)
            self._sample_count               = self._dconf.get(id, "sample_count",           required=True)#default = 5)
            self._sample_interval            = self._dconf.get(id, "sample_interval",        required=True)#default = 5)

        except KeyError as e:
            logger.critical(e)

        if enabled:
            logger.debug(f"[{self.id}] is enabled in configuration. Going to MEASURING state.")
            self._sm.set_initial_state(self.MEASURING)
        else:
            logger.debug(f"[{self.id}] is disabled in configuration. Going to DISABLED state.")
            self._sm.set_initial_state(self.DISABLED)

        self._timer_sample = Neotimer(self._sample_interval)

#endregion

#region properties

    @property
    def need_watering(self):
        return self._need_watering
    
    @property
    def desired_watering_time(self):
        return self._desired_watering_time_ms

    @property
    def remaining_idle_time(self):
        """ Returns how much time remains until the next measurement in miliseconds.
        If controller isn't in idle state, returns None. 
        """
        return (self._measurement_interval - self._sm.state_elapsed_time()) \
            if self._sm.current_state == self.IDLE else None

    @property
    def current_state(self):
        """ Returns name of the current state. """
        return self._sm.state_name()
    
    @property
    def valve_open(self):
        return self._valve.is_open()

    @property
    def last_humidity(self):
        """ Returns last measured humidity in percent (0–100). 
        Value is None if no measurement was ever taken. 
        """
        return self._hum_percent
    
    @property
    def last_humidity_timestamp(self):
        """ Returns last measured humidity timestamp in ISO 8601 format. 
        Value is None if no measurement was ever taken. 
        """
        return self._hum_timestamp
    
    @property
    def evaluated_watering_time(self):
        """ Returns last watering time in miliseconds."""
        return self._evaluated_watering_time_ms
    
    @property
    def evaluated_watering_timestamp(self):
        """ Returns last watering timestamp in ISO 8601 format. 
        Value is None if no measurement was ever taken. 
        """
        return self._evaluated_watering_timestamp
    
    @property
    def evaluated_watering_efficiency(self):
        """ Returns how much gain of humidity for 1 s of last watering. """
        return self._evaluated_watering_efficiency
    
#endregion

#region public methods

    def update(self):
        """ Call this method periodically to run the controller properly. """
        self._sm.update()  

    def enable(self) -> bool:
        """ Enable place. Place must be in DISABLED state.
        Returns boolean status of this operation. """
        if self._sm.in_state(self.DISABLED):
            self._sm.change_state(self.IDLE)
            return True
        return False

    def disable(self) -> bool:
        """ Disable place. Place must be in IDLE or PENDING_WATERING state. 
        Returns boolean status of this operation. """
        if self._sm.in_state(self.IDLE, self.PENDING_WATERING):
            self._sm.change_state(self.DISABLED)
            return True
        return False
    
    def switch_active(self) -> bool:
        if self._sm.in_state(self.DISABLED):
            return self.enable()
        else:
            return self.disable()

    def open_valve(self) -> bool:
        """ Open valve of this place. Place must be in IDLE or PENDING_WATERING state.
        Returns boolean status of this operation. """
        if self._sm.in_state(self.PENDING_WATERING, self.IDLE):
            self._valve.open()
            logger.debug(f"[{self.id}] Valve opened. Going to WATERING state.")
            self._sm.change_state(self.WATERING)
            return True
        return False

    def close_valve(self) -> bool:
        """ Close valve of this place. Place must be in WATERING state.
        Returns boolean status of this operation. """
        if self._sm.in_state(self.WATERING):
            self._valve.close()
            logger.debug(f"[{self.id}] Valve closed. Going to POST_WATERING state.")
            self._sm.change_state(self.POST_WATERING)
            return True
        return False

    def is_enabled(self) -> bool:
        return self._sm.current_state != self.DISABLED
    
    def is_idle(self) -> bool:
        return self._sm.current_state == self.IDLE
    
    def get_telemetry_data(self) -> str:
        """ Returns telemetry data in csv string:

        "last_raw, avg_raw, hum_percent, hum_delta,
        need_watering, desired_watering_time_ms, 
        current_state, state_elapsed_time"
        """
        def prepare(v):
            if isinstance(v, bool):
                return "1" if v else "0"
            if v is None:
                return "-1"
            return v

        return (
            f"{prepare(self._last_raw)},"
            f"{prepare(self._avg_raw)},"
            f"{prepare(self._hum_percent)},"
            f"{prepare(self._hum_delta)},"
            f"{prepare(self._hum_desired)},"

            f"{prepare(self._need_watering)},"
            f"{prepare(self._watering_time_ms)},"
            f"{prepare(self._evaluated_watering_efficiency)},"
            f"{prepare(self._desired_watering_time_ms)},"

            f"{prepare(self._sm.current_state)},"
            f"{prepare(self._sm.state_elapsed_time())}"
        )
    
#endregion

#region state methods

    def _state_disabled(self, event, phase):
        if phase == "entry":
            logger.info(f"Place {self.id} has been disabled.")
            self._dconf.set(self.id, "enabled", value=False)
            self._dconf.save()
            return

        if phase == "exit":
            logger.info(f"Place {self.id} has been enabled.")
            self._dconf.set(self.id, "enabled", value=True)
            self._dconf.save()
            return
        
        if phase == "do":
            if self._btn.check_pressed():
                self.enable()

    def _state_idle(self, event, phase):
        if phase == "do":
            if self._state_elapsed_time() >= self._measurement_interval:
                logger.debug(f"{self.id} measurement_interval elapsed. Changing state to STATE_MEASURING.")
                self._sm.change_state(self.MEASURING)

            if self._btn.check_pressed():
                self.disable()
        
    def _state_measuring(self, event, phase):
        if phase == "entry":
            self._samples.clear()
            #self._next_sample_ms = time.ticks_ms()
            self._timer_sample.start()
            return

        if phase == "exit":
            return

        #if time.ticks_diff(time.ticks_ms(), self._next_sample_ms) >= self.sample_interval:
        if self._timer_sample.finished():
            self._last_raw = self._soil_sens.measure()
            self._samples.append(self._last_raw)

            if len(self._samples) >= self._sample_count:
                threshold = None
                self._hum_previous = self._hum_percent
                self._avg_raw = sum(self._samples) // len(self._samples) # znak '//' - dzielenie całkowitoliczbowe (floor devision)
                self._hum_percent = self._soil_sens.get_percent(self._avg_raw)
                self._hum_timestamp = get_timestamp()

                # Calculate the diff in humidity since last measurement
                if self._hum_previous is not None:
                    self._hum_delta = round(self._hum_percent - self._hum_previous, 1)
                else:
                    self._hum_delta = None

                if self._sm._previous_state == self.IDLE or self._sm._previous_state == None:
                    # Last humidity value was stable, so we checking basic threshold
                    threshold = self._hum_threshold
                    self._desired_watering_time_ms = self._min_watering_time

                elif self._sm._previous_state in [self.POST_WATERING, self.PENDING_WATERING]:
                    threshold = self._hum_target

                    if self._sm._previous_state == self.PENDING_WATERING and self._correction_add:
                        self._desired_watering_time_ms = self._desired_watering_time_ms - self._correction
                        self._correction_add = False

                    elif self._sm._previous_state == self.PENDING_WATERING and self._desired_watering_time_ms == self._min_watering_time:
                        # Starting-point with lowest watering time.
                        pass

                    else:
                        self._correction = (self._hum_target - self._hum_percent) * self._correction_factor
                        self._desired_watering_time_ms = self._desired_watering_time_ms + self._correction
                        self._desired_watering_time_ms = clamp(self._desired_watering_time_ms, 
                                                            self._min_watering_time, 
                                                            self._max_watering_time)
                        self._correction_add = True
                    
                    if self._sm._previous_state == self.POST_WATERING:
                        # Calculate watering efficiency - how much gain of humidity for 1 s of watering.
                        watering_time_s = self._watering_time_ms / 1000.0
                        self._evaluated_watering_efficiency = self._hum_delta / watering_time_s
                        # 
                        self._evaluated_watering_time_ms = self._watering_time_ms
                        self._evaluated_watering_timestamp = self._watering_timestamp

                else:
                    logger.critical("Critical unrecognized error in PlantPlace")


                # Watering decision
                if self._hum_percent < threshold:
                    logger.debug(f"[{self.id}] humidity = {self._hum_percent} is low. Going to PENDING_WATERING.")
                    self._sm.change_state(self.PENDING_WATERING)
                else:
                    logger.debug(f"[{self.id}] humidity = {self._hum_percent} is okey. Going to IDLE.")
                    self._sm.change_state(self.IDLE)

            else:
                self._timer_sample.start()

    def _state_pending_watering(self, event, phase):
        if phase == "entry":
            self._need_watering = True
            return
        
        if phase == "exit":
            self._need_watering = False
            return
             
        if self._state_elapsed_time() >= self._wait_for_valve_time:
            logger.debug(f"[{self.id}] Valve opening timeout expired. Going to MEASURING.")
            self._sm.change_state(self.MEASURING)

    def _state_watering(self, event, phase):
        if phase == "entry":
            self._watering_timestamp = get_timestamp()
            return

        if phase == "exit":
            self._watering_time_ms = self._sm.state_elapsed_time()  
            self._soil_sens.simulate_water(self._watering_time_ms)          
            return

    def _state_post_watering(self, event, phase):
        if phase == "entry":
            return
        
        if phase == "exit":
            return
        
        if self._state_elapsed_time() >= self._post_watering_delay:
            # Tu będzie obliczana efektywność podlania? 
            # Perform correction measure
            logger.debug(f"[{self.id}] Post watering delay elapsed. Going to MEASURING.")
            self._sm.change_state(self.MEASURING)

#endregion

#region private methods
    
    def _state_elapsed_time(self):
        return int(self._sm.state_elapsed_time() * self.TIME_MULTIPLIER)

#endregion

#region properties-setters and validators

    @validate_integer_conv
    def set_hum_threshold(self, value):
        if not (0 <= value <= 100):
            raise ValueError("Próg wilgotności musi być w zakresie 0-100 %.")
        self._hum_threshold_temp = value

    @validate_integer_conv
    def set_hum_target(self, value):
        if not (0 <= value <= 100):
            raise ValueError("Docelowa wilgotność musi być w zakresie 0-100 %.")
        self._hum_target_temp = value

    @validate_integer_conv
    def set_min_watering_time(self, value):
        if value < 0:
            raise ValueError("Minimalny czas podlewania musi być nieujemny.")
        self._min_watering_time_temp = value

    @validate_integer_conv
    def set_max_watering_time(self, value):
        if value < 0:
            raise ValueError("Maksymalny czas podlewania musi być nieujemny.")
        self._max_watering_time_temp = value

    @validate_integer_conv
    def set_wait_for_valve_time(self, value):
        if value < 0:
            raise ValueError("Czas oczekiwania na zawór musi być nieujemny.")
        self._wait_for_valve_time_temp = value

    @validate_integer_conv
    def set_post_watering_delay(self, value):
        if value < 0:
            raise ValueError("Opóźnienie po podlewaniu musi być nieujemne.")
        self._post_watering_delay_temp = value

    @validate_integer_conv
    def set_measurement_interval(self, value):
        if value <= 0:
            raise ValueError("Interwał pomiaru musi być większy od zera.")
        self._measurement_interval_temp = value

    @validate_integer_conv
    def set_min_adc(self, value):
        if value < 0:
            raise ValueError("Minimalny ADC musi być nieujemny.")
        self._min_adc_temp = value

    @validate_integer_conv
    def set_max_adc(self, value):
        if value < 0:
            raise ValueError("Maksymalny ADC musi być nieujemny.")
        self._max_adc_temp = value

    @validate_integer_conv
    def set_sample_count(self, value):
        if value <= 0:
            raise ValueError("Liczba próbek musi być większa od zera.")
        self._sample_count_temp = value

    @validate_integer_conv
    def set_sample_interval(self, value):
        if value <= 0:
            raise ValueError("Interwał próbkowania musi być większy od zera.")
        self._sample_interval_temp = value

    def apply_setters(self):
        if not self._sm.in_state(self.DISABLED):
            raise ValueError("Zmiana konfiguracji jest możliwa tylko gdy miejsce podlewania jest bezczynne.")
        
        # Create copy of parameters
        hum_threshold        = getattr(self, "_hum_threshold_temp",        self._hum_threshold)
        hum_target           = getattr(self, "_hum_target_temp",           self._hum_target)
        min_watering_time    = getattr(self, "_min_watering_time_temp",    self._min_watering_time)
        max_watering_time    = getattr(self, "_max_watering_time_temp",    self._max_watering_time)
        wait_for_valve_time  = getattr(self, "_wait_for_valve_time_temp",  self._wait_for_valve_time)
        post_watering_delay  = getattr(self, "_post_watering_delay_temp",  self._post_watering_delay)
        measurement_interval = getattr(self, "_measurement_interval_temp", self._measurement_interval)
        min_adc              = getattr(self, "_min_adc_temp",              self._min_adc)
        max_adc              = getattr(self, "_max_adc_temp",              self._max_adc)
        sample_count         = getattr(self, "_sample_count_temp",         self._sample_count)
        sample_interval      = getattr(self, "_sample_interval_temp",      self._sample_interval)

        # Group validation
        if hum_target <= hum_threshold:
            raise ValueError("Docelowa wilgotność musi być większa niż próg wilgotności.")

        if max_watering_time < min_watering_time:
            raise ValueError("Maksymalny czas podlewania nie może być mniejszy od minimalnego.")

        if max_adc < min_adc:
            raise ValueError("Maksymalny ADC nie może być mniejszy od minimalnego.")

        # Apply changes (runtime)
        self._hum_threshold        = hum_threshold
        self._hum_target           = hum_target
        self._min_watering_time    = min_watering_time
        self._max_watering_time    = max_watering_time
        self._wait_for_valve_time  = wait_for_valve_time
        self._post_watering_delay  = post_watering_delay
        self._measurement_interval = measurement_interval
        self._min_adc              = min_adc
        self._max_adc              = max_adc
        self._sample_count         = sample_count
        self._sample_interval      = sample_interval

        self._timer_sample.duration = sample_interval
        self._soil_sens.min_adc = min_adc
        self._soil_sens.max_adc = max_adc

        # Apply changes in configuration
        self._dconf.set(self.id, "hum_threshold",               value=hum_threshold)
        self._dconf.set(self.id, "hum_target",                  value=hum_target)
        self._dconf.set(self.id, "min_watering_time",           value=min_watering_time)
        self._dconf.set(self.id, "max_watering_time",           value=max_watering_time)
        self._dconf.set(self.id, "wait_for_valve_time",         value=wait_for_valve_time)
        self._dconf.set(self.id, "post_watering_delay",         value=post_watering_delay)
        self._dconf.set(self.id, "measurement_interval",        value=measurement_interval)
        self._dconf.set(self.id, "min_adc",                     value=min_adc)
        self._dconf.set(self.id, "max_adc",                     value=max_adc)
        self._dconf.set(self.id, "sample_count",                value=sample_count)
        self._dconf.set(self.id, "sample_interval",             value=sample_interval)
        self._dconf.save()

        # Remove temporary attributes
        for attr in [
            "_hum_threshold_temp", "_hum_target_temp",
            "_min_watering_time_temp", "_max_watering_time_temp",
            "_wait_for_valve_time_temp", "_post_watering_delay_temp",
            "_measurement_interval_temp", "_min_adc_temp", "_max_adc_temp",
            "_sample_count_temp", "_sample_interval_temp"
        ]:
            if hasattr(self, attr):
                delattr(self, attr)

#endregion
