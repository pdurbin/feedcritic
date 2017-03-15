function init() {
    loadJSON(function(response) {
        // Parse JSON string into object
        var mydata = JSON.parse(response);
        document.getElementById("result").innerHTML = get_result_podcasts(mydata);
    },
    "podcasts.json");
}

function showLatest() {
    loadJSON(function(response) {
        // Parse JSON string into object
        var mydata = JSON.parse(response);
        document.getElementById("result").innerHTML = get_result_latest(mydata);
    },
    "latest.json");
}

function clearResult() {
    document.getElementById("result").innerHTML = "";
}

function get_result_podcasts(data) {
    var r = data.length + " feeds <ul>";
    for (var i = 0; i < data.length; ++i) {
        r = r + "<li style=\"list-style: none;\"><a href=\"" + data[i]["feed"] + "\"><img src=\"rssfeed.svg\" height=35px></a> <a href=\"" + data[i]["url"] + "\">" + data[i]["title"] + "</a> (";
        var rating = data[i]["rating"];
        if (rating != '') {
            r = r + rating + " stars, ";
        }
        r = r + "updated " + data[i]["latest"] + "): " + data[i]["description"];
        var oldest = data[i]["oldest"];
        if (oldest != '' && oldest != '0001-01-01') {
            r = r + " (Oldest: " + oldest + ")";
        }
        /*
        var retired = data[i]["oldest"];
        if (retired == '') {
            r = r + " (retired)";
        }
        */
        r = r + "</li>";
    }
    return r + "</ul>";
}

function get_result_latest(data) {
    var r = data.length + " episodes <ul>";
    for (var i = 0; i < data.length; ++i) {
        r = r + "<li><a href=\"" + data[i]["Link"] + "\">" + data[i]["Title"] + "</a> (" + data[i]["Podcast"] + ")";
        r = r + "</li>";
    }
    return r + "</ul>";
}

// https://codepen.io/KryptoniteDove/post/load-json-file-locally-using-pure-javascript
function loadJSON(callback, jsonFile) {

    var xobj = new XMLHttpRequest();
    xobj.overrideMimeType("application/json");
    xobj.open('GET', jsonFile, true);
    xobj.onreadystatechange = function() {
        if (xobj.readyState == 4 && xobj.status == "200") {
            // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
            callback(xobj.responseText);
        }
    };
    xobj.send(null);
}