// const apiEndpoint = window.location.origin;
const apiEndpoint = "http://192.168.50.88";

const routes = 
{
    '#/status': {"render": renderStatusPage, "onEnter": enterStatusPage,  "onExit": exitStatusPage,  "onUpdate":updateStatusPage,    "updateInterval": 500},
    '#/config': {"render": renderConfigPage, "onEnter": enterConfigPage,  "onExit": exitConfigPage,  "onUpdate":updateConfigPage,    "updateInterval": 10000},
    '#/wifi' :  {"render": renderWifiPage,   "onEnter": enterWifiPage,    "onExit": exitWifiPage,    "onUpdate":updateWifiPage,      "updateInterval": 5000},
};

const state = {
    "previousRoute" : null,
    "currentRoute" : null,
    "updateTimeoutId" : null
}

async function handleRoute() 
{
    const hash = window.location.hash || '#/start'; // Default to home if no hash
    const content = document.getElementById('content');
    state.previousRoute = state.currentRoute;
    state.currentRoute = hash;

    if (!(hash in routes)) {
        content.innerHTML = '<p>Nie znaleziono strony</p>'
        return;
    }

    // Exit previous page
    if(state.previousRoute != null) {
        clearTimeout(state.updateTimeoutId)
        routes[state.previousRoute]?.onExit?.();
    }
    
    // Enter new page
    content.innerHTML = '<p>Ładuje stronę...</p>';
    content.innerHTML = await routes[state.currentRoute]?.render?.();
    routes[state.currentRoute]?.onEnter?.();

    // Start updating
    const update = async () => {
        await routes[state.currentRoute]?.onUpdate?.();
        state.updateTimeoutId = setTimeout(update, routes[hash]["updateInterval"]);
    }
    update();
}

async function makeJSONRequest(endpoint)
{
    const response = await fetch(apiEndpoint + "/" + endpoint); // Make request
    const data = await response.json();
    if (response.ok) {
        return data;
    }
    else {
        console.error("HTTP error:", response.status, response.statusText);
    }
}

async function postJSON(endpoint, payload)
{
    const response = await fetch(`${apiEndpoint}/${endpoint}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        console.error("HTTP error:", response.status, response.statusText);
        return false;
    }

    return true;
}

async function makeRequest(endpoint)
{
    const response = await fetch(apiEndpoint + "/" + endpoint); // Make request
    if (response.ok) {
        console.log("Okey")
        return true
    }
    else {
        console.error("HTTP error:", response.status, response.statusText);
    }
}

document.getElementById("hamburger").addEventListener("click", () => {
    document.getElementById('menu').classList.toggle('active'); /* Toggle menu while clicking hamburger */
});

document.getElementById("menu").querySelectorAll("a").forEach(link => {
    link.addEventListener("click", () => {
        document.getElementById("menu").classList.remove("active"); /* Hide menu while clicking menu link */
    });
});

// Listen for navigation events
window.addEventListener('hashchange', handleRoute);
window.addEventListener('load', handleRoute);
