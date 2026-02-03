from machine import Pin

class Valve:
    def __init__(self, pin_num):
        self._pin = Pin(pin_num, Pin.OUT)
        self._pin.off()
        self._prev = 0

    def open(self):
        self._pin.on()
        
    def close(self):
        self._pin.off()

    def is_open(self) -> bool:
        return self._pin.value()
    
    def just_opened(self) -> bool:
        now = self._pin.value()
        r = (self._prev == 0 and now == 1)
        self._prev = now
        return r

    def just_closed(self) -> bool:
        now = self._pin.value()
        f = (self._prev == 1 and now == 0)
        self._prev = now
        return f
