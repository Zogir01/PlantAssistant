import time
from machine import Pin

class Button:
    def __init__(self, pin_num, debounce_ms=200):
        self._debounce_ms = debounce_ms
        self._pin = pin_num
        self._state = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self._last_time = time.ticks_ms()

    def check_pressed(self) -> bool:
        """ Check button is pressed with debouncing. """
        state = self._state.value()
        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self._last_time)

        if state == 1 or elapsed < self._debounce_ms:
            return False
        
        self._last_time = now
        return True


