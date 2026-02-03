
# responsibility:
# - pozwala przejść do trybu uśpienia na określony czas


import machine
import ujson

class PowerManager():
    def __init__(self, filename = None):
        self.filename = filename

    def prepare_for_sleep(self, state: dict):
        if self.filename is None:
            return
        
        with open(self.filename, "w") as f:
            ujson.dump(state, f)
    
    def sleep_ms(self, ms: int):
        machine.deepsleep(ms)
    
    def restore_after_wakeup(self) -> dict:
        if self.filename is None:
            return {}
        
        if not self.was_wakeup_from_sleep():
            return {}

        try:
            with open(self.filename, "r") as f:
                return ujson.load(f)
        except:
            return {}
    
    def was_wakeup_from_sleep(self) -> bool:
        return machine.reset_cause() == machine.DEEPSLEEP_RESET