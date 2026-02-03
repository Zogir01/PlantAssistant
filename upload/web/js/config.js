//region state

config = {}
selected_place = "place1"

//endregion

//region page template

const CONFIG_DEFS = {

    menu: [
        { id: "load-config-btn", label: "", type: FIELD_TYPES.BUTTON, text: "Wczytaj", skip_source: true },
        { id: "save-config-btn", label: "", type: FIELD_TYPES.BUTTON, text: "Zapisz", skip_source: true },
        { id: "select_place", type: FIELD_TYPES.RADIO_GROUP, label: "Wybierz wyświetlane miejsce:",
            options: [
                { value: "place1", label: "L" },
                { value: "place2", label: "C" },
                { value: "place3", label: "R" }
            ]
        }
    ],
    views: {
        place1: {
            title: "Miejsce lewe",
            sections: {
                "Podlewanie": [
                    { id: "place1.hum_threshold",      label: "Próg wilgotności:",      type: FIELD_TYPES.INPUT_RANGE, unit: "%", min: 20, max: 80, step: 1 },
                    { id: "place1.hum_target",         label: "Docelowa wilgotność:",   type: FIELD_TYPES.INPUT_RANGE, unit: "%", min: 20, max: 80, step: 1 },
                    { id: "place1.min_watering_time",  label: "Min. czas podlania:",    type: FIELD_TYPES.INPUT_RANGE, unit: "s", min: 1,  max: 20, step: 1 },
                    { id: "place1.max_watering_time",  label: "Maks. czas podlania:",   type: FIELD_TYPES.INPUT_RANGE, unit: "s", min: 1,  max: 20, step: 1 }
                ],
                "Harmonogramy": [
                    { id: "place1.measurement_interval", label: "Interwał pomiaru wilgotności:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1,  max: 100, step: 1 },
                    { id: "place1.post_watering_delay",  label: "Czas odczekania po podlaniu:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1,  max: 30, step: 1 },
                    { id: "place1.wait_for_valve_time",  label: "Limit czasu oczekiwania na zawór:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1,  max: 30, step: 1 }
                ],
                "Czujnik wilgotności": [
                    { id: "place1.min_adc",         label: "Min. zakres ADC:",          type: FIELD_TYPES.INPUT_NUMBER, min: 0, max: 4096 },
                    { id: "place1.max_adc",         label: "Maks. zakres ADC:",         type: FIELD_TYPES.INPUT_NUMBER, min: 0, max: 4096 },
                    { id: "place1.sample_count",    label: "Ilość próbek do średniej:", type: FIELD_TYPES.INPUT_NUMBER, min: 1, max: 200 },
                    { id: "place1.sample_interval", label: "Interwał próbkowania:",     type: FIELD_TYPES.INPUT_RANGE, unit: "ms", min: 5, max: 25, step: 5 }
                ]
            }
        },
        place2: {
            title: "Miejsce środkowe",
            sections: {
                "Podlewanie": [
                    { id: "place2.hum_threshold",      label: "Próg wilgotności:",      type: FIELD_TYPES.INPUT_RANGE, unit: "%", min: 20, max: 80, step: 1 },
                    { id: "place2.hum_target",         label: "Docelowa wilgotność:",   type: FIELD_TYPES.INPUT_RANGE, unit: "%", min: 20, max: 80, step: 1 },
                    { id: "place2.min_watering_time",  label: "Min. czas podlania:",    type: FIELD_TYPES.INPUT_RANGE, unit: "s", min: 1,  max: 20, step: 1 },
                    { id: "place2.max_watering_time",  label: "Maks. czas podlania:",   type: FIELD_TYPES.INPUT_RANGE, unit: "s", min: 1,  max: 20, step: 1 }
                ],
                "Harmonogramy": [
                    { id: "place2.measurement_interval", label: "Interwał pomiaru wilgotności:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1,  max: 100, step: 1 },
                    { id: "place2.post_watering_delay",  label: "Czas odczekania po podlaniu:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1,  max: 30, step: 1 },
                    { id: "place2.wait_for_valve_time",  label: "Limit czasu oczekiwania na zawór:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1,  max: 30, step: 1 }
                ],
                "Czujnik wilgotności": [
                    { id: "place2.min_adc",         label: "Min. zakres ADC:",          type: FIELD_TYPES.INPUT_NUMBER, min: 0, max: 4096 },
                    { id: "place2.max_adc",         label: "Maks. zakres ADC:",         type: FIELD_TYPES.INPUT_NUMBER, min: 0, max: 4096 },
                    { id: "place2.sample_count",    label: "Ilość próbek do średniej:", type: FIELD_TYPES.INPUT_NUMBER, min: 1, max: 200 },
                    { id: "place2.sample_interval", label: "Interwał próbkowania:",     type: FIELD_TYPES.INPUT_RANGE, unit: "ms", min: 5, max: 25, step: 5 }
                ]
            }
        },
        place3: {
            title: "Miejsce prawe",
            sections: {
                "Podlewanie": [
                    { id: "place3.hum_threshold",      label: "Próg wilgotności:",      type: FIELD_TYPES.INPUT_RANGE, unit: "%", min: 20, max: 80, step: 1 },
                    { id: "place3.hum_target",         label: "Docelowa wilgotność:",   type: FIELD_TYPES.INPUT_RANGE, unit: "%", min: 20, max: 80, step: 1 },
                    { id: "place3.min_watering_time",  label: "Min. czas podlania:",    type: FIELD_TYPES.INPUT_RANGE, unit: "s", min: 1,  max: 20, step: 1 },
                    { id: "place3.max_watering_time",  label: "Maks. czas podlania:",   type: FIELD_TYPES.INPUT_RANGE, unit: "s", min: 1,  max: 20, step: 1 }
                ],
                "Harmonogramy": [
                    { id: "place3.measurement_interval", label: "Interwał pomiaru wilgotności:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1,  max: 100, step: 1 },
                    { id: "place3.post_watering_delay",  label: "Czas odczekania po podlaniu:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1,  max: 30, step: 1 },
                    { id: "place3.wait_for_valve_time",  label: "Limit czasu oczekiwania na zawór:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1,  max: 30, step: 1 }
                ],
                "Czujnik wilgotności": [
                    { id: "place3.min_adc",         label: "Min. zakres ADC:",          type: FIELD_TYPES.INPUT_NUMBER, min: 0, max: 4096 },
                    { id: "place3.max_adc",         label: "Maks. zakres ADC:",         type: FIELD_TYPES.INPUT_NUMBER, min: 0, max: 4096 },
                    { id: "place3.sample_count",    label: "Ilość próbek do średniej:", type: FIELD_TYPES.INPUT_NUMBER, min: 1, max: 200 },
                    { id: "place3.sample_interval", label: "Interwał próbkowania:",     type: FIELD_TYPES.INPUT_RANGE, unit: "ms", min: 5, max: 25, step: 5 }
                ]
            }
        },
        device: {
            title: "Urządzenie",
            sections: {
                "Telemetria": [
                    { id: "device.enable_telemetry",    label: "Aktywuj telemetrię:", type: FIELD_TYPES.INPUT_CHECKBOX },
                    { id: "device.telemetry_interval",  label: "Interwał telemetrii:", type: FIELD_TYPES.INPUT_RANGE, unit: "ms", min: 1, max: 30, step: 1 }
                ],
                "Oszczędzanie energii": [
                    { id: "device.enable_energy_save_mode", label: "Aktywuj tryb oszczędzania energii:", type: FIELD_TYPES.INPUT_CHECKBOX },
                    { id: "device.min_dsleep_time",         label: "Minimalny czas uśpienia:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1, max: 30, step: 1 }
                ],
                "Harmonogram": [
                    { id: "device.enable_work_schedule", label: "Aktywuj harmonogram:", type: FIELD_TYPES.INPUT_CHECKBOX },
                    { id: "device.work_schedule_from",   label: "Praca od:", type: FIELD_TYPES.INPUT_TIME },
                    { id: "device.work_schedule_to",     label: "Praca do:", type: FIELD_TYPES.INPUT_TIME }
                ]
            }
        },
        watering: {
            title: "Kontroler podlewania",
            sections: {
                "Pompa": [
                    { id: "watering.pwm_min",       label: "Minimalna moc:", type: FIELD_TYPES.INPUT_RANGE, unit: "%", min: 1, max: 100, step: 1 },
                    { id: "watering.pwm_max",       label: "Maksymalna moc:", type: FIELD_TYPES.INPUT_RANGE, unit: "%", min: 1, max: 100, step: 1 },
                    { id: "watering.pump_cooldown", label: "Cooldown:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1, max: 30, step: 1 },
                    { id: "watering.max_valves",    label: "Limit równocześnie podlewanych:", type: FIELD_TYPES.INPUT_RANGE, unit: "", min: 1, max: 3, step: 1 }
                ],
                "Otoczenie": [
                    { id: "watering.amb_temp_thresh", label: "Próg temperatury:", type: FIELD_TYPES.INPUT_RANGE, unit: "°C", min: 20, max: 50, step: 1 },
                    { id: "watering.dht_interval",    label: "Interwał pomiarów:", type: FIELD_TYPES.INPUT_RANGE, unit: "min", min: 1, max: 30, step: 1 }
                ]
            }
        },
        light: {
            title: "Kontroler oświetlenia LED",
            sections: {
                "Ogólne": [
                    { id: "light.enable",    label: "Aktywuj:",  type: FIELD_TYPES.INPUT_CHECKBOX },
                    { id: "light.threshold", label: "Próg:",     type: FIELD_TYPES.INPUT_RANGE, unit: "%", min: 20, max: 80, step: 1 },
                    { id: "light.avg_count", label: "Ilość próbek do średniej:", type: FIELD_TYPES.INPUT_NUMBER, min: 1, max: 50}
                ]
            }
        }
    }
};

//endregion

//region core functions

async function renderConfigPage() {
    config = await makeJSONRequest(`config.json`);
    return renderPage(CONFIG_DEFS, config);
}

async function enterConfigPage() {

    // Bind buttons

    document.getElementById('load-config-btn').addEventListener('click', () => {loadConfig();});
    document.getElementById('save-config-btn').addEventListener('click', () => {saveConfig();});

    // Bind changing values from all inputs into config (json dictionary) values.
    // This works because we assigning id of this inputs to id of config values
    // in render functions.
    document.querySelectorAll('input[type="range"], input[type="number"]').forEach(input => {
        input.addEventListener('input', function() { setByPath(config, this.id, this.valueAsNumber || this.value) }); 
    });

    document.querySelectorAll('input[type="checkbox"]').forEach(input => {
        input.addEventListener('change', function() { setByPath(config, this.id, this.checked) });
    });

    document.querySelectorAll('input[type="time"]').forEach(input => {
        input.addEventListener('change', function() { setByPath(config, this.id, this.value)});
    });

    document.getElementById("place1").hidden = false; 
    document.getElementById("place2").hidden = true;
    document.getElementById("place3").hidden = true;

    document.getElementById("select_place-place1").checked = true;

    document.getElementById("select_place-place1").addEventListener("click", () => showPlace("place1"));
    document.getElementById("select_place-place2").addEventListener("click", () => showPlace("place2"));
    document.getElementById("select_place-place3").addEventListener("click", () => showPlace("place3"));
}

function exitConfigPage() {

}

function updateConfigPage() {
    
}

//endregion

//region events

function showPlace(placeId) {
    ["place1", "place2", "place3"].forEach(id => {
        document.getElementById(id).hidden = (id !== placeId);
    });
}

async function loadConfig() {
    config = await makeJSONRequest(`config.json`);
    loadSectionsValues(CONFIG_DEFS, config)
}

async function saveConfig() {
    success = postJSON('update_config', config);
    console.log(success);
}

//endregion


// function selectPlace(place_id) {
//     // Change state
//     selected_place = place_id

//     // Change whole place content-block html 
//     document.getElementById("place").innerHTML = renderPlaceConfig()
    
//     // Bind inputs again because we changing html structure
//     bindConfigInputs()
// }