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

        if self.enabled:
            logger.debug(f"[{self.id}] is enabled in configuration. Going to MEASURING state.")
            self._sm.set_initial_state(self.MEASURING)
        else:
            logger.debug(f"[{self.id}] is disabled in configuration. Going to DISABLED state.")
            self._sm.set_initial_state(self.DISABLED)

        self._timer_sample = Neotimer(self.sample_interval)

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
        return (self.measurement_interval - self._sm.state_elapsed_time()) \
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

#region configuration properties-getters

    @property
    def enabled(self):
        return self._dconf.get('enabled')

    @property
    def hum_threshold(self):
        return self._dconf.get('hum_threshold')

    @property
    def hum_target(self):
        return self._dconf.get('hum_target')

    @property
    def min_watering_time(self):
        return self._dconf.get('min_watering_time')

    @property
    def max_watering_time(self):
        return self._dconf.get('max_watering_time')

    @property
    def post_watering_delay(self):
        return self._dconf.get('post_watering_delay')

    @property
    def wait_for_valve_time(self):
        return self._dconf.get('wait_for_valve_time')

    @property
    def measurement_interval(self):
        return self._dconf.get('measurement_interval')

    @property
    def min_adc(self):
        return self._dconf.get('min_adc')

    @property
    def max_adc(self):
        return self._dconf.get('max_adc')

    @property
    def sample_count(self):
        return self._dconf.get('sample_count')

    @property
    def sample_interval(self):
        return self._dconf.get('sample_interval')

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
            if self._state_elapsed_time() >= self.measurement_interval:
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

            if len(self._samples) >= self.sample_count:
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
                    threshold = self.hum_threshold
                    self._desired_watering_time_ms = self.min_watering_time

                elif self._sm._previous_state in [self.POST_WATERING, self.PENDING_WATERING]:
                    threshold = self.hum_target

                    if self._sm._previous_state == self.PENDING_WATERING and self._correction_add:
                        self._desired_watering_time_ms = self._desired_watering_time_ms - self._correction
                        self._correction_add = False

                    elif self._sm._previous_state == self.PENDING_WATERING and self._desired_watering_time_ms == self.min_watering_time:
                        # Starting-point with lowest watering time.
                        pass

                    else:
                        self._correction = (self.hum_target - self._hum_percent) * self._correction_factor
                        self._desired_watering_time_ms = self._desired_watering_time_ms + self._correction
                        self._desired_watering_time_ms = clamp(self._desired_watering_time_ms, 
                                                            self.min_watering_time, 
                                                            self.max_watering_time)
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
             
        if self._state_elapsed_time() >= self.wait_for_valve_time:
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
        
        if self._state_elapsed_time() >= self.post_watering_delay:
            # Tu będzie obliczana efektywność podlania? 
            # Perform correction measure
            logger.debug(f"[{self.id}] Post watering delay elapsed. Going to MEASURING.")
            self._sm.change_state(self.MEASURING)

#endregion

#region private methods
    
    def _state_elapsed_time(self):
        return int(self._sm.state_elapsed_time() * self.TIME_MULTIPLIER)

#endregion

