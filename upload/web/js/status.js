//region state

systemStatus = {}
selected_man_watering_place = null

//endregion

//region page template

const STATUS_DEFS = {
    menu: [
        
    ],
    views: {
        place1: {
            title: "Miejsce lewe",
            sections: {
                "Stan ogólny": [
                    { id: "place1.enabled",       label: "Aktywne",             type: FIELD_TYPES.TOGGLE_BUTTON, default: "Nie" },
                    { id: "place1.state_name",    label: "Aktualny stan",       type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "place1.need_watering", label: "Potrzebuje podlania", type: FIELD_TYPES.BOOLEAN,       highlight: true, default: false },
                    { id: "place1.valve_open",    label: "Zawór otwarty",       type: FIELD_TYPES.BOOLEAN,       highlight: true, default: false }
                ],
                "Pomiar wilgotności": [
                    { id: "place1.humidity",            label: "Wilgotność",      type: FIELD_TYPES.NUMBER,    unit: "%", default: "—" },
                    { id: "place1.humidity_timestamp", label: "Ostatni pomiar",   type: FIELD_TYPES.TIMESTAMP, default: "—" }
                ],
                "Ostatnie podlanie": [
                    { id: "place1.evaluated_watering_time",        label: "Czas podlania",      type: FIELD_TYPES.NUMBER, unit: "s",   default: "—" },
                    { id: "place1.evaluated_watering_efficiency", label: "Efektywność",       type: FIELD_TYPES.NUMBER, unit: "%/s", format: "percent", default: "—" },
                    { id: "place1.evaluated_watering_timestamp",  label: "Ostatnie podlanie", type: FIELD_TYPES.TIMESTAMP, default: "" },
                    { id: "place1.desired_watering_time", label: "Sugerowany czas następnego podlania", type: FIELD_TYPES.NUMBER, unit: "s", default: "—" }
                ]
            }
        },

        place2: {
            title: "Miejsce środkowe",
            sections: {
                "Stan ogólny": [
                    { id: "place2.enabled",       label: "Aktywne",             type: FIELD_TYPES.TOGGLE_BUTTON, default: "Nie" },
                    { id: "place2.state_name",    label: "Aktualny stan",       type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "place2.need_watering", label: "Potrzebuje podlania", type: FIELD_TYPES.BOOLEAN,       highlight: true, default: false },
                    { id: "place2.valve_open",    label: "Zawór otwarty",       type: FIELD_TYPES.BOOLEAN,       highlight: true, default: false }
                ],
                "Pomiar wilgotności": [
                    { id: "place2.humidity",            label: "Wilgotność",    type: FIELD_TYPES.NUMBER,    unit: "%", default: "—" },
                    { id: "place2.humidity_timestamp", label: "Ostatni pomiar", type: FIELD_TYPES.TIMESTAMP, default: "—" }
                ],
                "Ostatnie podlanie": [
                    { id: "place2.evaluated_watering_time",        label: "Czas podlania",      type: FIELD_TYPES.NUMBER, unit: "s",   default: "—" },
                    { id: "place2.evaluated_watering_efficiency", label: "Efektywność",       type: FIELD_TYPES.NUMBER, unit: "%/s", format: "percent", default: "—" },
                    { id: "place2.evaluated_watering_timestamp",  label: "Ostatnie podlanie", type: FIELD_TYPES.TIMESTAMP, default: "—" },
                    { id: "place2.desired_watering_time", label: "Sugerowany czas następnego podlania", type: FIELD_TYPES.NUMBER, unit: "s", default: "—" }
                ]
            }
        },

        place3: {
            title: "Miejsce prawe",
            sections: {
                "Stan ogólny": [
                    { id: "place3.enabled",       label: "Aktywne",             type: FIELD_TYPES.TOGGLE_BUTTON, default: "Nie" },
                    { id: "place3.state_name",    label: "Aktualny stan",       type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "place3.need_watering", label: "Potrzebuje podlania", type: FIELD_TYPES.BOOLEAN,       highlight: true, default: false },
                    { id: "place3.valve_open",    label: "Zawór otwarty",       type: FIELD_TYPES.BOOLEAN,       highlight: true, default: false }
                ],
                "Pomiar wilgotności": [
                    { id: "place3.humidity",            label: "Wilgotność",    type: FIELD_TYPES.NUMBER,    unit: "%", default: "—" },
                    { id: "place3.humidity_timestamp", label: "Ostatni pomiar", type: FIELD_TYPES.TIMESTAMP, default: "—" }
                ],
                "Ostatnie podlanie": [
                    { id: "place3.evaluated_watering_time",        label: "Czas podlania",      type: FIELD_TYPES.NUMBER, unit: "s",   default: "—" },
                    { id: "place3.evaluated_watering_efficiency", label: "Efektywność",       type: FIELD_TYPES.NUMBER, unit: "%/s", format: "percent", default: "—" },
                    { id: "place3.evaluated_watering_timestamp",  label: "Ostatnie podlanie", type: FIELD_TYPES.TIMESTAMP, default: "—" },
                    { id: "place3.desired_watering_time", label: "Sugerowany czas następnego podlania", type: FIELD_TYPES.NUMBER, unit: "s", default: "—" }
                ]
            }
        },

        device: {
            title: "Urządzenie",
            sections: {
                "Harmonogram": [
                    { id: "device.schedule_active", label: "Harmonogram aktywny", type: FIELD_TYPES.BOOLEAN, highlight: true, default: false }
                ],
                "Telemetria": [
                    { id: "device.telemetry_active", label: "Telemetria aktywna", type: FIELD_TYPES.BOOLEAN, highlight: true, default: false }
                ],
                "Oszczędzanie energii": [
                    { id: "device.energy_save_active", label: "Tryb oszczędzania energii", type: FIELD_TYPES.BOOLEAN, highlight: true, default: false }
                ]
            }
        },

        watering: {
            title: "Kontroler podlewania",
            sections: {
                "Aktualny stan": [
                    { id: "watering.is_watering",   label: "Trwa podlewanie",     type: FIELD_TYPES.BOOLEAN, highlight: true, default: false },
                    { id: "watering.current_power", label: "Aktualna moc pompy", type: FIELD_TYPES.NUMBER,  unit: "%", default: "0" },
                    { id: "watering.current_mode",  label: "Tryb pracy",         type: FIELD_TYPES.TEXT,    default: "—" },
                    { id: "toggle_wat_mode_btn",    label: " ", type: FIELD_TYPES.BUTTON, text: "Przełącz tryb", skip_source: true }
                ],
                "Otoczenie": [
                    { id: "watering.amb_humidity",    label: "Wilgotność",  type: FIELD_TYPES.NUMBER, unit: "%",  default: "—" },
                    { id: "watering.amb_temperature", label: "Temperatura", type: FIELD_TYPES.NUMBER, unit: "°C", default: "—" }
                ],
                "Zasoby": [
                    { id: "watering.water_in_tank", label: "Woda w zbiorniku", type: FIELD_TYPES.BOOLEAN, highlight: true, default: false }
                ],
                "Manualne podlewanie": [
                    { id: "manual_watering_place", type: FIELD_TYPES.RADIO_GROUP, label: "Wybierz miejsce:",
                        options: [
                            { value: "place1", label: "L" },
                            { value: "place2", label: "C" },
                            { value: "place3", label: "R" }
                        ]
                    },
                    { id: "manual_watering_time", label: "Czas podlania:", type: FIELD_TYPES.INPUT_RANGE, unit: "s", min: 1, max: 10, step: 1, skip_source: true, default: 5 },
                    { id: "manual_watering_btn", label: " ", type: FIELD_TYPES.BUTTON, text: "Podlej", skip_source: true },
                    { id: "stop_watering_btn", label: " ", type: FIELD_TYPES.BUTTON, text: "Zatrzymaj wszystko", skip_source: true }
                ]
            }
        }
    }
};

//endregion

//region core functions

async function renderStatusPage() {
    systemStatus = await makeJSONRequest("status.json");
    return renderPage(STATUS_DEFS, systemStatus);
}

async function enterStatusPage()
{
    selected_man_watering_place = null;
    document.getElementById("manual_watering_btn").addEventListener('click', async () => { await manualWatering()});
    document.getElementById("stop_watering_btn").addEventListener('click', async () => { await stopWatering()});
    document.getElementById("toggle_wat_mode_btn").addEventListener('click', async () => { await toggleWateringMode()});
    document.getElementById("place1.enabled").addEventListener("click", async () => { await togglePlace("place1") });
    document.getElementById("place2.enabled").addEventListener("click", async () => { await togglePlace("place2") });
    document.getElementById("place3.enabled").addEventListener("click", async () => { await togglePlace("place3") });
    document.getElementById("manual_watering_place-place1").addEventListener("click", async () => { await selectManualWateringPlace("place1") });
    document.getElementById("manual_watering_place-place2").addEventListener("click", async () => { await selectManualWateringPlace("place2") });
    document.getElementById("manual_watering_place-place3").addEventListener("click", async () => { await selectManualWateringPlace("place3") });
}


function exitStatusPage()
{
    
}

async function updateStatusPage()
{
    loadStatus();
}

//endregion

//region events

async function loadStatus() 
{
    systemStatus = await makeJSONRequest(`status.json`);
    loadSectionsValues(STATUS_DEFS, systemStatus);
}
    
function selectManualWateringPlace(placeId) 
{
    // This function is registered in STATUS_DEFS
    console.log('selectManualWateringPlace()')
    selected_man_watering_place = placeId;
}

async function manualWatering() 
{
    console.log('manualWatering()')
    if(selected_man_watering_place == null) alert("Wybierz miejsce do podlania.");
    duration = document.getElementById("manual_watering_time").value;
    const result = await makeRequest(`water?place_id=${selected_man_watering_place}&duration=${duration}`);
}

async function stopWatering()
{
    console.log('stopWatering()')
    const result = await makeRequest(`stop_water`);
}

async function togglePlace(placeId)
{
    console.log('togglePlace()')
    if(placeId == null) alert("Wybierz miejsce.");
    const result = await makeRequest(`toggle_place?place_id=${placeId}`);
}

async function toggleWateringMode()
{
    console.log('toggleWateringMode()')
    const result = await makeRequest(`toggle_wt_mode`);
}


//endregion

//region other

// async function bindStatusListeners() 
// {
//     let places = ["place1", "place2", "place3"]

//     places.forEach(place =>{
//         document.getElementById(`${place}.enabled`).addEventListener('click',  async () => {
//             const endpoint = systemStatus[place]["enabled"] ? 'disable' : 'enable';
//             if (makeRequest(`${endpoint}?place_id=${place}`)) {
//                 loadStatus()
//             }
//         });
//     });
// }

//endregion