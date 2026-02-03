const FIELD_TYPES = {
    INPUT_NUMBER: 'input-number',
    INPUT_RANGE: 'input-range',
    INPUT_CHECKBOX: 'input-checkbox',
    INPUT_TIME: 'input-time',
    INPUT_TEXT: 'input-text',
    BUTTON: 'button',  
    BOOLEAN: 'boolean',
    TEXT: 'text',
    NUMBER: 'number',
    TIMESTAMP: 'timestamp',
    TOGGLE_BUTTON: 'toggle-button',
    RADIO_GROUP: 'radio-group'
};

const FIELD_ROLES = {
    STATUS: 'status',   // tylko wyświetlanie
    INPUT: 'input',     // formularze
    ACTION: 'action'    // przyciski / wywołania API
};

function renderPage(defs, data) 
{
    let menuHtml = ""; 
    defs.menu.forEach(field => {  
        menuHtml += renderField(field);
    });

    let viewsHtml = "";
    Object.entries(defs.views).forEach(([viewId, viewDef]) => {

        let sections_html = ""
        Object.entries(viewDef.sections).forEach(([sectionId, fields]) => {
            if (sectionId != "") sections_html += `<h3>${sectionId}</h3>`;

            fields.forEach(field => {
                const value = getFromPath(data, field.id);
                sections_html += renderField(field, value);
            });
        })

        viewsHtml += `
            <div class="content-block" id="${viewId}">
                <div class="content-block-header">
                    <h2>${viewDef.title}</h2>
                </div>
                <div class="fields">
                    ${sections_html}
                </div>
            </div>
        `;
    });

    return `
        <div class="content-menu">${menuHtml}</div>
        <div class="content-block-wrapper">${viewsHtml}</div>
    `;
}

function loadSectionsValues(defs, data)
{
    Object.entries(defs.views).forEach(([viewId, viewDef]) => {
        const viewData = data?.[viewId];
        if (!viewDef.sections || !viewData) return;

        Object.values(viewDef.sections).forEach(fields => {
            fields.forEach(field => {
                if (field.skip_source) return;

                let value = getFromPath(data, field.id);
                setFieldValue(field.id, value, field.type, field.default);
            });
        });
    });
}

function renderField(field, value) 
{
    let content = ` <div class="field">`;
    if (field.label != "") 
        content += `<label for="${field.id}">${field.label}</label>`;

    value = value ?? field.default;

    switch (field.type) {
        case FIELD_TYPES.INPUT_NUMBER: 
            return content += `<input type="number" id="${field.id}" name="${field.id}" min="${field.min}" max="${field.max}" value="${value}" required></div>`; 

        case FIELD_TYPES.INPUT_RANGE: 
            return content += `<input type="range" id="${field.id}" min="${field.min}" max="${field.max}" step="${field.step}" value="${value}"
                        oninput="document.getElementById('${field.id}-value').textContent=this.value">
                        <span id="${field.id}-value">${value}</span>
                        <span class="unit">${field.unit}</span></div>`;

        case FIELD_TYPES.INPUT_CHECKBOX: 
            return content += `<input type="checkbox" id="${field.id}" name="${field.id}" ${value ? "checked" : ""}></div>`;

        case FIELD_TYPES.INPUT_TIME: 
            return content += `<input type="time" id="${field.id}" name="${field.id}" min="00:00" max="23:59" value="${value}" required></div>`; 

        case FIELD_TYPES.INPUT_TEXT: 
            return content += `<input type="text" id="${field.id}" name="${field.id}" value="${value || ''}"></div>`;

        case FIELD_TYPES.BUTTON: 
            return content += `<button class="button" id=${field.id}>${field.text}</button></div>`;

        case FIELD_TYPES.BOOLEAN: 
            return content += `<p class='status-text parameter ${value ? 'on' : 'off'}' id=${field.id}><b>●</b></p></div>`;
        
        case FIELD_TYPES.TEXT: 
            return content += `<p class='status-text parameter' id=${field.id}><b>${value}</b></p></div>`;

        case FIELD_TYPES.NUMBER: 
            return content += `<p class='status-text parameter' id=${field.id}><b>${value}</b></p>
                                <span class="unit">${field.unit}</span></div>`;

        case FIELD_TYPES.TIMESTAMP: 
            return content += `<p class='status-text date' id=${field.id}><b>${formatDateDDMMHHMM(value)}</b></p></div>`;

        case FIELD_TYPES.TOGGLE_BUTTON: 
            return content += `<button class="button button--sm button--${value ? 'on' : 'off'}" 
                            id=${field.id}>${value ? 'ON' : 'OFF'}</button></div>`;

        case FIELD_TYPES.RADIO_GROUP: 
            content += `<div class="radio-group" id="${field.id}">`;

            field.options.forEach(opt => {
                const inputId = `${field.id}-${opt.value}`;
                content += `
                        <input type="radio" name="${field.id}" id="${inputId}" value="${opt.value}" 
                        ${field.selectedValue === opt.value ? "checked" : ""}>${opt.label}
                `;
                // onchange="${field.onChangeFn}('${opt.value}')"
            });
            return content += `</div></div>`;

        default: return content += "zły typ..</div>";
    }
}

function setFieldValue(id, value, type, default_val) 
{
    const e = document.getElementById(id)
    if(!e) return false;

    value = value ?? default_val;

    switch(type) {
        case FIELD_TYPES.INPUT_NUMBER: 
            document.getElementById(id).valueAsNumber = Number(value) || 0;
            return;
        
        case FIELD_TYPES.INPUT_RANGE: 
            document.getElementById(id).value = value;
            document.getElementById(`${id}-value`).textContent = value; // Update also an <span>
            return;

        case FIELD_TYPES.INPUT_CHECKBOX:
            document.getElementById(id).checked = !!value;  // conversion to boolean
            return;

        case FIELD_TYPES.INPUT_TIME:
            document.getElementById(id).value = value || "";
            return;

        case FIELD_TYPES.INPUT_TEXT:
            document.getElementById(id).value = value || "";
            return;

        case FIELD_TYPES.BOOLEAN:
            let eb = document.getElementById(id)
            eb.textContent = "●";
            eb.className = `status-text parameter ${value ? "on" : "off"}`;
            return;

        case FIELD_TYPES.TEXT:
            document.getElementById(id).innerHTML = `<b>${value}</b>`;
            return;

        case FIELD_TYPES.NUMBER:
            document.getElementById(id).innerHTML = `<b>${value}</b>`;
            return;

        case FIELD_TYPES.TIMESTAMP: 
            document.getElementById(id).innerHTML = `<b>${formatDateDDMMHHMM(value)}</b>`;
            return;

        case FIELD_TYPES.TOGGLE_BUTTON:
            const isOn = !!value; // conversion to boolean
            let et = document.getElementById(id);
            et.textContent = isOn ? "ON" : "OFF";
            et.className = `button button--sm button--${isOn ? "on" : "off"}`;
            return;

        default: {}
    }
}

// Load an value from object by path like "a.b.c"
// example: console.log(getFromPath(state, "place1.humidity"));
function getFromPath(obj, path) 
{
    return path.split('.').reduce((acc, key) => acc?.[key], obj);
}

// Set an value in object by path like "a.b.c"
// example: setByPath(state, "place1.humidity", 55);
function setByPath(obj, path, value) 
{
    const keys = path.split('.');
    const lastKey = keys.pop();
    const target = keys.reduce((acc, key) => {
        if (!acc[key]) acc[key] = {};   // tworzy obiekt jeśli nie istnieje
        return acc[key];
    }, obj);
    target[lastKey] = value;
}

function formatDateDDMMHHMM(timestamp) 
{
    if (timestamp == null) return "--";
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return "--";

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0'); // miesiące od 0
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${day}.${month}, ${hours}:${minutes}`;
}
