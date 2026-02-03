# Config validators, used to validate configuration values in @property.setter methods across application classes.

def validate_integer_conv(func):
    def wrapper(self, v):
        try:
            converted = int(v)
        except Exception:
            raise ValueError("Wymagana jest liczba całkowita.")
        return func(self, converted)
    return wrapper

def validate_float_conv(func):
    def wrapper(self, v):
        try:
            converted = float(v)
        except ValueError:
            raise ValueError("Wymagana jest liczba zmiennoprzecinkowa.")
        return func(self, converted)
    return wrapper

def validate_bool_conv(func):
    def wrapper(self, v):
        if isinstance(v, bool):
            converted = v
        elif isinstance(v, str):
            if v.lower() in ("1", "true", "yes", "on"):
                converted = True
            elif v.lower() in ("0", "false", "no", "off"):
                converted = False
            else:
                raise ValueError("Wymagana jest wartość logiczna (true/false).")
        else:
            raise ValueError("Wymagana jest wartość logiczna (true/false).")
        return func(self, converted)
    return wrapper

def validate_time_conv(func):
    def wrapper(self, v: str):
        # Expected "HH:MM"
        if not isinstance(v, str):
            raise ValueError("Format czasu musi być tekstem w formacie HH:MM.")

        try:
            h, m = v.split(":")
            h, m = int(h), int(m)
        except Exception:
            raise ValueError("Niewłaściwy format czasu — oczekiwano HH:MM.")

        if not (0 <= h < 24 and 0 <= m < 60):
            raise ValueError("Godzina musi być w zakresie 00:00–23:59.")

        return func(self, f"{h:02d}:{m:02d}")
    return wrapper