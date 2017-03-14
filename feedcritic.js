function init() {
    loadJSON(function(response) {
        // Parse JSON string into object
        var mydata = JSON.parse(response);
        document.getElementById("result").innerHTML = get_result(mydata);

    });
}

function clearResult() {
    document.getElementById("result").innerHTML = "";
}

function get_result(data) {
    var r = data.length + " feeds <ul>";
    for (var i = 0; i < data.length; ++i) {
        r = r + "<li style=\"list-style: none;\"><a href=\"" + data[i]["feed"] + "\"><img src=\"rssfeed.svg\" height=35px></a> <a href=\"" + data[i]["url"] + "\">" + data[i]["title"] + "</a> " + "(updated " + data[i]["Latest"] + "): " + data[i]["description"];
        r = r + "</li>";
    }
    return r + "</ul>";
}

// https://codepen.io/KryptoniteDove/post/load-json-file-locally-using-pure-javascript
function loadJSON(callback) {

    var xobj = new XMLHttpRequest();
    xobj.overrideMimeType("application/json");
    xobj.open('GET', 'podcasts.json', true);
    xobj.onreadystatechange = function() {
        if (xobj.readyState == 4 && xobj.status == "200") {
            // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
            callback(xobj.responseText);
        }
    };
    xobj.send(null);
}