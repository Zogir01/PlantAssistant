from machine import Pin, PWM
import time
from app.config_validators import validate_integer_conv
from core.neotimer import Neotimer
from core.config import ConfigManager
from core.logging import logger

# --- stałe i tryby ---
ContinuousMeasure = b'\x10'   # pomiar ciągły high-res
OneTimeMeasure    = 0x20      # pojedynczy pomiar
SingleMode        = 0
ContinuousMode    = 1

# --- driver BH1750 ---
class LightSensor:
    def __init__(self, i2c, addr=0x23, mode_input=5):
        self.i2c = i2c
        self.addr = addr
        self.mode_input = Pin(mode_input, Pin.IN)
        self.mode_choice = None
        self.init_sensor()

    def init_sensor(self):
        mode = self.mode_input.value()

        if mode == ContinuousMode:
            self.i2c.writeto(self.addr, ContinuousMeasure)
            self.mode_choice = ContinuousMode

        elif mode == SingleMode:
            self.mode_choice = SingleMode

        else:
            raise ValueError("Nieznany tryb pracy sensora")
        
    def set(self):
        self.i2c.writeto(self.addr, bytes([OneTimeMeasure]))

    def read(self):
        data = self.i2c.readfrom(self.addr, 2)
        return (data[0] << 8 | data[1]) / 1.2

# --- Warstwa logiki: kontrola LED ---
class LEDController:
    def __init__(self, led : Pin, sensor: LightSensor):
        self.led = led
        self.sensor = sensor

        # PWM do sterowania jasnością (continuous)
        self.pwm = PWM(self.led)
        self.pwm.freq(1000)

        # nieblokujące pomiary
        self._setted = False
        self._timer_sample = Neotimer(50) # timer interwału pomiędzy próbkami do średniej
        self._samples = []
        self._timer_sens_conv = Neotimer(180) # timer czasu konwersji czujnika BH1750

        # User configuration
        self._dconf = ConfigManager().get_config("light")
        try:
            self.enabled = self._dconf.get("enabled", required=True)
            self.threshold = self._dconf.get("threshold", required=True)
            self.avg_count = self._dconf.get("avg_count", required=True)

        except KeyError as e:
            logger.critical(e)

    def update(self):
        if not self.enabled:
            return

        if self._timer_sample.repeat_execution():
            # Wykonywane co ustalony czas przez _timer_sample

            if self.sensor.mode_choice == ContinuousMode:
                self._samples.append(self.sensor.read())

            elif self.sensor.mode_choice == SingleMode:
                if not self._setted:
                    # Jeśli nie ustawiono sensora
                    self.sensor.set()
                    self._setted = True
                    self._timer_sens_conv.start() # wystartuj timer odczekania czasu konwersji sensora

                elif self._setted and self._timer_sens_conv.finished(): 
                    # sensor ustawiony i czas konwersji odczekany
                    self._setted = False
                    self._samples.append(self.sensor.read())
                
            if len(self._samples) >= self.avg_count:
                light_level = sum(self._samples) / len(self._samples)
                self._samples.clear()
                logger.debug(f"Średnia Lux: {light_level}")

                if self.sensor.mode_choice == ContinuousMode:
                    self.pwm_led(light_level)

                elif self.sensor.mode_choice == SingleMode:
                    self.one_time_led(light_level)

    def isEnabled(self):
        return self.enabled

    def turn_on(self):
        self.led.value(1)

    def turn_off(self):
        self.led.value(0)

    def pwm_led(self, light_level):
        """Sterowanie LED jasnością przez PWM w trybie Continuous."""
        # im jaśniej, tym jaśniejsza LED (skalowanie)
        duty = int(max(0, min(1023, (light_level / self.threshold) * 1023)))
        self.pwm.duty(duty)

    def one_time_led(self, light_level):
        """Sterowanie LED on/off w trybie Single."""
        if light_level < self.threshold:
            self.turn_on()
        else:
            self.turn_off()

#region properties-setters and validators

    @validate_integer_conv
    def set_enabled(self, value: bool):
        self._enabled_temp = value

    @validate_integer_conv
    def set_threshold(self, value):
        if not (0 <= value <= 100):
            raise ValueError("Próg musi być w zakresie 0-100 %.")
        self._threshold_temp = value

    @validate_integer_conv
    def set_avg_count(self, value):
        if value <= 0:
            raise ValueError("Liczba próbek musi być większa od zera.")
        self._avg_count_temp = value

    def apply_setters(self):
        # Create copy of parameters
        enabled = getattr(self, "_enabled_temp", self.enabled)
        threshold = getattr(self, "_threshold_temp", self.threshold)
        avg_count = getattr(self, "_avg_count_temp", self.avg_count)

        # Group validation
        # ...

        # Apply changes
        self.threshold = threshold
        self.avg_count = avg_count
        self.enabled = enabled

        # Remove temporary attributes
        for attr in ["_enabled_temp", "_threshold_temp", "_avg_count_temp"]:
            if hasattr(self, attr):
                delattr(self, attr)

        self._dconf.save()

#endregion
