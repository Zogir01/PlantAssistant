from machine import PWM, Pin
from upload.core.helpers import clamp

class WaterPump:

    _MAX_PWM_U16 = 65535 # Max PWM in u16 related to 100%

    def __init__(self, pin_num, frequency):
        self._pin = Pin(pin_num)
        self._pwm = PWM(self._pin, freq=frequency, duty_u16=0)
        self._current_pwm = 0

    def on(self, percent):
        self._current_pwm = int(clamp((percent / 100 * self._MAX_PWM_U16), 0, self._MAX_PWM_U16))
        self._pwm.duty_u16(self._current_pwm) 

    def off(self):
        self._pwm.duty_u16(0)
        self._current_pwm = 0

    def is_on(self) -> bool:
        return self._current_pwm > 0

    def get_power(self, precision = None) -> float:
        return round(self._current_pwm, precision) if precision is not None else self._current_pwm
