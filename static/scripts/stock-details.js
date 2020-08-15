const API_URL = "http://127.0.0.1:5000/api/"

const $getDataBtn = $('#get-data')
const $allData = $('#all-data');

const stockId = parseInt($('#stock-id').attr('data-id'), 10);
// const axios = require('axios');

async function get_all_data() {
    res = await axios.get(`${API_URL}${stockId}`);
    return res.data
}

$getDataBtn.click(async function(){
    data = await get_all_data();
    $allData.append(parseObject(data))


    // $('ul').each(function(){
    //     $(this).click(function(){            #TODO: slide toggle all-data list (fix this code)
    //         $(this).children().each(function(){
    //             $(this).slideToggle("slow");
    //         });
    //     });
    // });
    
   
});

function parseObject(object){
    let append = ""
    for (const [key, value] of Object.entries(object)) {
        if(value instanceof Object || value instanceof Array){
            append += `<li>
                        ${key}
                        <ul>${parseObject(value)}</ul>
                    </li> `;
        }
        else{
            append+= `<li> ${key}: ${value} </li>`;
        }
    }
    return append
}
