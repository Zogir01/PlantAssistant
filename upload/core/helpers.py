import ujson
import time

# TIMEZONE = 2
# UTC_OFFSET = TIMEZONE * 60 * 60


def get_timestamp():
    """ Returns current timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SS. """
    # t = time.localtime(time.time() + UTC_OFFSET)
    t = time.localtime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )

def get_time():
    """ Returns current time in format HH:MM. """
    #t = time.localtime(time.time() + UTC_OFFSET)
    t = time.localtime()
    return "{:02d}:{:02d}".format(t[3], t[4])

def parse_time(t: str):
    """ Parse time from format HH:MM to tuple: (hour, minutes). """
    h, m = t.split(":")
    return int(h), int(m)

def get_ticks_ms():
    return time.ticks_ms()

def s_to_ms(seconds):
    '''Convert seconds to milliseconds.'''
    return int(seconds * 1000)

def ms_to_s(milliseconds):
    '''Convert milliseconds to seconds.'''
    return round(milliseconds / 1000, 2)

def min_to_ms(minutes):
    '''Convert minutes to milliseconds.'''
    return int(minutes * 60 * 1000)

def ms_to_min(milliseconds):
    '''Convert milliseconds to minutes.'''
    return round(milliseconds / 1000 / 60, 2)

def clamp(val, min_val, max_val):
    '''Returns value limited to specified range.'''
    if val < min_val: return min_val
    if val > max_val: return max_val
    return val

def range_percent(val, min_val, max_val, precision = None):
    '''Returns a percentage of a value in a given range.'''
    percent = 100 - ((val - min_val) / (max_val - min_val)) * 100
    return percent if precision is None else round(percent, precision)

def send_telemetry(*args):
    '''Prints data in CSV-like format: arg1, arg2, arg3'''
    result = ""
    i = 0
    for x in args:
        result += str(x)
        i += 1
        if i < len(args):
            result += ','
    print(result)
    
# def save_file(path: str, data):
#     '''Save python object to JSON file.'''
#     with open(path, "w") as f:
#         ujson.dump(data, f)

# def load_file(path):
#     '''Load JSON file into python object.'''
#     with open(path, "r") as f:
#         return ujson.load(f)

# def print_debug(text, tag = "undefined"):
#     ''' '''
#     if not DEBUG_UNLOCK:
#         return
#     if tag in UNLOCKED_DEBUG_TAGS:
#         print("[{} ms] [{}] {}".format(time.ticks_ms(), tag, text))

# def time_benchmark(function):
#     start_time = time.ticks_ms()
#     function()
#     end_time = time.ticks_ms()
#     return time.ticks_diff(end_time, start_time)

# def send_telemetry(data_dict : dict):
#     h = ""
#     d = ""
#     i = 0
#     for k, v in sorted(data_dict.items()):
#         #h += k + ","
#         d += str(v)

#         if i < len(data_dict) - 1:
#             #h += ","
#             d += ","
#         i += 1
    
#     #h += "\n"
#     r = h + d
#     print(r)
    

