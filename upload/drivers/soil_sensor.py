from upload.core.helpers import clamp, range_percent
from machine import ADC

TEST_SOIL_SENSOR = True

# This class is an test implementation.

class SoilSensor:
    def __init__(self, pin_num, min_adc, max_adc):

        self._adc = ADC(pin_num)
        self._adc.atten(ADC.ATTN_11DB)
        self._adc.width(ADC.WIDTH_12BIT)
        self.min_adc = min_adc
        self.max_adc = max_adc
        
        # Mock variables (dont use outside this class)
        if TEST_SOIL_SENSOR:
            self._hum = 35
            self._gain = 5 # Gain of humidity for 1 second of watering
            self._decr = 0.005 # Decrease of humidity for 1 second of waiting over time
            self._sim_time = 1000 # 
            self._min_hum = 1
            self._max_hum = 100

    def get_percent(self, raw, precision = None) -> float:
        """ Returns percented value of moisture from raw ADC value. 
        Value is clamped around `self.min_adc` and `self.max_adc`
        in case of problems with range. """
        if TEST_SOIL_SENSOR:
            return self._hum
        
        raw = clamp(raw, self.min_adc, self.max_adc)
        return range_percent(raw, self.min_adc, self.max_adc, precision)
    
    def measure(self, clamped = True) -> int:
        """ Returns raw value of moisture from ADC. This value is clamped around `self.min_adc` and `self.max_adc`. """
        if TEST_SOIL_SENSOR:
            return 500 # 
        
        return clamp(self._adc.read(), self.min_adc, self.max_adc) if clamped else self._adc.read()

    # def set_place(self, place):
    #     if TEST_SOIL_SENSOR:
    #         self._place = place
    
    def simulate_water(self, watering_time_ms):
        if TEST_SOIL_SENSOR:
            self._hum += self._gain * (watering_time_ms / 1000.0) #* self._sim_time

            self._hum = clamp(self._hum, self._min_hum, self._max_hum)

            if self._hum >= self._max_hum:
                self._hum = self._min_hum

#endregion