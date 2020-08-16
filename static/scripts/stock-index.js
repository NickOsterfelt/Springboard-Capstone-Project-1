const API_URL = "http://127.0.0.1:5000/api/"

const $searchInput = $('#search-input');

async function getSearchLabels(){
    res = await axios.get(`${API_URL}stocks`);
    return res.data["stock_names"];
}


// async function autocomplete(terms){
//     $searchInput.autocomplete({"source":terms});
// }

// async function get_terms(){
//     terms = await getSearchLabels();
//     console.log(terms);
//     await autocomplete(terms);
// }

// get_terms();
// $searchInput.autocomplete({
//     source:auto_complete_data
// });

$( async function() {
    let availableTags = await getSearchLabels();
    
    $( "#search-input" ).autocomplete({
      source: availableTags[0]
    });
  } );