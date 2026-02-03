## 📋 Overview
---

PlantAssistant is system for automatic watering plant pots and LED light regulation in home. Automatic control has been tested for three potted plants. 

This repositorium only contains software part of PlantAssistant system. Check out [this]() to check an hardware part of this project.

This project is related with Bachelor's thesis (in Polish language). Check it [here]() on github.

> [!WARNING]
> Status of this project is still experimental. Automatic algorithms were functionally tested, but not validated in real-world control scenarios. 
> In next commits, I will simplify the code and add comments in the code for better understanding.

## 📁 Project Structure
---

```
└── 📁Software
    ├── 📁.vscode       # VS Code related settings.
    ├── 📁dev_server    # Test implementation of HTTP Server (localhost).
    └── 📁upload        # Files loaded directly into microcontroller.
        ├── 📁app           # Main logic of application.
        ├── 📁config        # JSON files with user configuration.
        ├── 📁core          # Utility modules that defines the core of application.
        ├── 📁drivers       # Hardware related modules.
        ├── 📁utils         # Utility modules.
        ├── 📁web           # HTML, CSS, JavaScript and assets files related with web page.
        ├── boot.py 
        ├── main.py
    ├── README.md       # This file.
    ├── upload_cache.json
    └── upload.py       # Helper script for loading files into microcontroller.
```

## 🛠️ Technologies
---

- Microcontroller: [ESP32-WROOM-32D]()
- Language: [MicroPython v1.25.0 (2025-04-15)](https://micropython.org/download/ESP32_GENERIC/) for ESP32/WROOM modules
- User configuration: JSON files
- User interface: HTML/CSS/JS web page

## ✨ Features
---
Base:
- automatic watering three plants based on their moisture level using solenoid valves and single water pump,
- power of the water pump regulated by PWM,
- automatic light on/off control based on readings from the BH1750 sensor,
- time-based schedulement for automatic control,
- entering deep sleep mode after a period of activity,
- relative humidity and air temperature readings from DHT11,
- 0/1 water level sensor readings,
- device configuration stored in JSON files in FLASH,
- working in AP and STA WiFi mode,
- hosting HTTP server and API endpoints for user control

Tests/implementation process:
- HTTP server implementation in Django framework (localhost),
- soil humidity simulation for algorithm functionality tests,
- time multiplier simulation for algorithm functionality tests

## 🌐 Features from web interface
---

- displays device status
- watering with a set period of time,
- activation/deactivation of automatic control,
- changing device configuration,
- displays available networks in range and WiFi status,
- connecting with new network

## 💧 Watering logic
---

The `WateringController` class acts as the main coordinator for the watering system, managing multiple watering locations (`PlantPlace` objects) and shared components (water pump, DHT11 sensor, water level sensor).

Operating modes:
- **AUTO mode** – watering triggered by plant locations - based on `PlantPlace` class decision and suggested duration,
- **MANUAL mode** – watering initiated by user with specified duration.

Watering process can only start when following conditions are met:

- watering location must be unlocked,
- location not been currently watered,
- water in the tank available (signal from water level sensor),
- number of open valves not exceed limit (`max_valves⚙`),
- pump cooldown elapsed – protects pump from frequent starts ( `pump_cooldown⚙`),
- ambient temperature not exceed threshold – protects soil from scalding (`amb_temp_thresh⚙`).

Water pump power regulation:

- 0 open valves → power set to 0%,
- 1 open valve → power set to `pwm_max⚙`,
- \>1 open valves → power set proportional to number of watering locations:
 $$\frac{pwm_{\mathrm{max}}}{N_{\mathrm{places}}}~\cdot~N_{\mathrm{open}} \cdot 100~\%$$

## 🤖 Automatic watering decision and duration logic
---
Each watering location (`PlantPlace` object) operates as a finite state machine with the following states:
- **IDLE** → periodic soil humidity measurement,
- **MEASURING** → humidity evaluation and watering need assessment,
- **PENDING_WATERING** → waiting for valve opening,
- **WATERING** → active watering process,
- **POST_WATERING** → humidity stabilization after watering,
- **DISABLED** → location locked, no automatic transitions.

Watering decision is triggered when measured humidity falls below threshold:
- `hum_threshold⚙` – initial watering trigger (from IDLE state),
- `hum_target⚙` – target humidity after watering (from POST_WATERING or PENDING_WATERING states).

Watering duration is calculated using:
- **Initial watering**: `min_watering_time⚙` (safe starting point),
- **Subsequent watering**: previous duration + proportional correction:
  $$\Delta t = k \cdot (H_{\mathrm{target}} - H_{\mathrm{current}})$$
  > [!NOTE] 
  > where $k$ is proportional gain, 
  > final value is clamped between `min_watering_time⚙` and `max_watering_time⚙`.

## ⚙️ Core configuration (`core.json`)
---

Basic device configuration for network connectivity.

|   Param  |    Default    | Description |
|----------|---------------|-------------|
| `ap_ssid` | PlantAssist | Access Point (AP) network name |
| `ap_pass` | 12345678 | Access Point password |
| `sta_ssid` | -- | Wi-Fi network name for client mode (STA) |
| `sta_pass` | -- | STA network password |

## ⚙️ LED regulation configuration (`light.json`)
---

Configuration for the `LEDController` component.

|   Param  |    Default    | Description |
|----------|---------------|-------------|
| `enabled` | true | Enable automatic light control |
| `threshold` | 50 | Light intensity threshold for turning on LED lamp (lux) |
| `avg_count` | 15 | Number of measurements to average |

## ⚙️ Watering configuration (`water.json`)
---

Configuration for the `WateringController` component.

|   Param  |    Default    | Description |
|----------|---------------|-------------|
| `mode` | 2 | Controller operating mode (`AUTO=1`, `MANUAL=2`) |
| `pwm_min` | 20 | Minimum pump power (%) |
| `pwm_max` | 80 | Maximum pump power (%) |
| `max_valves` | 1 | Maximum number of simultaneously open valves |
| `pump_cooldown` | 5000 | Time the pump cannot be restarted (ms) |
| `amb_temp_thresh` | 35 | Ambient temperature threshold preventing watering (°C) |
| `dht_interval` | 200000 | DHT11 sensor measurement interval (ms) |
| `signal_check_interval` | 2000 | Interval for checking watering signals from PlantPlace class (ms) |

## ⚙️ General device configuration (`device.json`)
---

Configuration for the `DeviceController` component.

|   Param  |    Default    | Description |
|----------|---------------|-------------|
| `enable_telemetry` | false | Enable telemetry data transmission |
| `telemetry_interval` | 10 | Telemetry data transmission interval (ms) |
| `enable_energy_save_mode` | false | Enable energy saving mode |
| `min_dsleep_time` | 600000 | Minimum sleep time in energy saving mode (ms) |
| `enable_work_schedule` | false | Enable device work schedule |
| `work_schedule_from` | 8:00 | Device work start time (hh:mm format) |
| `work_schedule_to` | 22:00 | Device work end time (hh:mm format) |
| `schedule_interval` | 5000 | Schedule check interval (ms) |

## ⚙️ Watering locations configuration (`places.json`)
---

Configuration for individual `PlantPlace` instances (example for `place1` section).

|   Param  |    Default    | Description |
|----------|---------------|-------------|
| `enabled` | false | Enable watering location |
| `hum_threshold` | 30 | Humidity threshold initiating watering need (%) |
| `hum_target` | 70 | Target soil humidity after watering (%) |
| `min_watering_time` | 1000 | Minimum watering time (ms) |
| `max_watering_time` | 10000 | Maximum watering time (ms) |
| `post_watering_delay` | 600000 | Humidity stabilization time (ms) |
| `wait_for_valve_time` | 300000 | Maximum wait time for valve opening (ms) |
| `measurement_interval` | 1800000 | Soil humidity measurement and watering decision interval (ms) |
| `min_adc` | 1200 | ADC conversion result defining 0% soil humidity |
| `max_adc` | 3050 | ADC conversion result defining 100% soil humidity |
| `sample_count` | 25 | Number of samples taken in one measurement |
| `sample_interval` | 5 | Interval between samples (ms) |

> [!NOTE] 
> - All time values are in milliseconds (ms)
> - Temperature values are in degrees Celsius (°C)
> - Percentage values are in the range 0-100
> - The `places.json` file can contain multiple plant place configurations (place1, place2, etc.)

## 🏗️ Architecture 
---


## 📸 Images
---




## ⬆️ Uploading files
---

To upload code to the ESP32 microcontroller, make sure that the appropriate MicroPython firmware is installed. For this purpose, please refer to the official [instruction](https://micropython.org/download/ESP32_GENERIC/).

To simplify uploading files to the ESP32, a dedicated script `upload.py` was created. This script uploads all files from `upload` directory. To run the script, you need to install [Python](https://www.python.org/downloads/) and the [mpremote](https://pypi.org/project/mpremote/) tool. You can run this with the following flags:
```
python upload.py update   # updates existing files on the ESP32.
 python upload.py full     # deletes all files and uploads them again from scratch.
```
> [!NOTE]  
> if you change the file structure (adding a new directory or moving a file) it is recommended to first run the script with the `full` flag.*

## 🙏 Credits
---

This project is based in part on:
- Logging implementation: [ESPlog](https://github.com/armanghobadi/ESPlog/tree/main) by armanghobadi, **MIT**.
- Software timers: [micropython_neotimer](https://github.com/jrullan/micropython_neotimer/tree/main) by jrullan, **Apache-2.0**.
- Singleton implementation: [micropython-samples](https://github.com/peterhinch/micropython-samples/blob/master/functor_singleton/examples.py) by peterhinch, **MIT**.
- HTTP server implementation: [K-ESP-CTRL](https://github.com/Kuszki/K-ESP-CTRL) by Kuszki, **GPL-3.0-only**.

## 👥 Authors
---

- Tomasz Wojtasek, github: [Zogir01](https://github.com/Zogir01): 
    → software implementation (this repo)
- Paweł Kurek, github: [PANP4W3L](https://github.com/PANP4W3L):
    → hardware implementation ([check here]())
    → LED regulation logic (`LightController` class)

## 📜 License
---

This project is licensed under the **GNU General Public License v3.0**.
See the [LICENSE](LICENSE) file for full details.
