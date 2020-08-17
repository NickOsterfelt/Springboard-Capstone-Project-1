const API_URL = "http://127.0.0.1:5000/api/"

const $getDataBtn = $('#get-data')
const $allData = $('#all-data');

const stockId = parseInt($('#stock-id').attr('data-id'), 10);
// const axios = require('axios');

async function get_all_data() {
    res = await axios.get(`${API_URL}stocks/${stockId}`);
    return res.data
}

$getDataBtn.click(async function () {
    data = await get_all_data();
    i=1
    for (const [key, value] of Object.entries(data)) {
        $allData.append(`
        <div class="accordion" id="accordion${i}">
            <div class="card">
                <div class="card-header" id="heading">
                    <h2 class="mb-0">
                        <button class="btn btn-link" type="button" data-toggle="collapse" data-target="#dataCollapse${i}"
                            id="get-data">
                            ${key}
                        </button>
                    </h2>
                </div>
                <div id="dataCollapse${i}" class="collapse " data-parent="#accordion${i}">
                    <div class="card-body">
                        <ul id="">
                            ${parseObject(value)}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        `);
        i++;
    }
});

function parseObject(object) {
    let append = ""
    for (const [key, value] of Object.entries(object)) {
        if (value instanceof Object || value instanceof Array) {
            append += `<li>
                        <b>${key}</b>
                        <ul>${parseObject(value)}</ul>
                    </li> `;
        }
        else {
            append += `<li> ${key}: ${value} </li>`;
        }
    }
    return append
}
