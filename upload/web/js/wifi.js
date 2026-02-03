//region state

wifiStatus = {}
stations = {}

//endregion

//region page template

const WIFI_DEFS = {
    menu: [],
    views: {
        status_ap: {
            title: "Status Access-Point",
            sections: {
                "": [
                    { id: "ap.connected", label: "Połączone",                   type: FIELD_TYPES.BOOLEAN,       default: false },
                    { id: "ap.ssid",      label: "ssid",                        type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "ap.ip",        label: "Adres IP",                    type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "ap.mask",      label: "Maska podsieci",              type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "ap.gw",        label: "Brama",                       type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "ap.tx_power",  label: "Siła nad. sygnału",           type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "ap.client_cnt",label: "Ilość poł. klientów",         type: FIELD_TYPES.TEXT,          default: "Nieznany" }
                ],
            }
        },
        status_sta: {
            title: "Status sieci",
            sections: {
                "": [
                    { id: "sta.connected", label: "Połączone",                  type: FIELD_TYPES.BOOLEAN,       default: false },
                    { id: "sta.ssid",      label: "ssid",                       type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "sta.ip",        label: "Adres IP",                   type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "sta.mask",      label: "Maska podsieci",             type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "sta.gw",        label: "Brama",                      type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "sta.dns",       label: "Adres DNS",                  type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "sta.rssi",      label: "Siła odb. sygnału (rssi)",   type: FIELD_TYPES.TEXT,          default: "Nieznany" },
                    { id: "sta.tx_power",  label: "Siła nad. sygnału",          type: FIELD_TYPES.TEXT,          default: "Nieznany" }
                ]
            }
        },
        wifi_conn_form: {
            title: "Połącz z siecią WiFi",
            sections: {
                "": [
                    { id: "connect_wifi_ssid", label: "ssid:", type: FIELD_TYPES.INPUT_TEXT, skip_source: true},
                    { id: "connect_wifi_pass", label: "hasło:", type: FIELD_TYPES.INPUT_TEXT, skip_source: true},
                    { id: "connect_wifi_btn", label: " ", type: FIELD_TYPES.BUTTON, text: "Połącz", skip_source: true }
                ]
            }
        }
    }
}

//endregion

//region core functions

async function renderWifiPage() 
{
    wifiStatus = await makeJSONRequest("wifi_status.json");
    return renderPage(WIFI_DEFS, wifiStatus);
}

async function enterWifiPage()
{
    // Right now, there isn't functionality to generate general variable-sized dynamic content
    document.querySelector('.content-block-wrapper').innerHTML += await renderAvStations();
}

function exitWifiPage()
{

}

function updateWifiPage()
{
    loadWifiStatus()
}

//endregion

//region events

async function loadWifiStatus() {
    console.log('Aktualizuje status wifi...')
    wifiStatus = await makeJSONRequest(`wifi_status.json`);
    loadSectionsValues(WIFI_DEFS, wifiStatus);
}

//endregion

//region other

async function renderAvStations()
{
    stations = await makeJSONRequest("wifi_stations.json");
    let html = ""
    
    for (const station of Object.values(stations).sort((a, b) => b.RSSI - a.RSSI)) {
        html += `<button class = "button" onclick='fill_ssid("${station.ssid}")'>`;
        html += `<b>${station.ssid}</b>`;
        html += " sygnał: "

        if (station.RSSI >= -30)        html+="Wyśmienity";
        else if (station.RSSI >= -67)   html+="Bardzo dobry";
        else if (station.RSSI >= -70)   html+="Normalny";
        else if (station.RSSI >= -80)   html+="Słaby";
        else                            html+="Bardzo słaby";

        html +="</button>";
    }

    return `
    <div class="content-block" id="avStations">
        <div class="content-block-header">
            <h2>Dostępne sieci w zasięgu</h2>
        </div>
        <div class="content-block-wrapper">
            <div id="select-wifi" role="group" aria-label="Dostępne sieci Wi-Fi">
                ${html}
            </div>
        </div>
    </div>`
}

function fill_ssid(ssid) {
    document.getElementById("connect_wifi_ssid").value = ssid;
}

//endregion