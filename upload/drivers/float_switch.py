from machine import Pin
import time

class FloatSwitch():
    """ Minimal version for now. """
    def __init__(self, pin_num):
        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)

    def is_on(self) -> bool:
        return self._pin.value() == 1
    
    def is_off(self) -> bool:
        return self._pin.value() == 0