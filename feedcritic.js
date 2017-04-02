function init() {
    loadJSON(function(response) {
        var mydata = JSON.parse(response);
        document.getElementById("result").innerHTML = get_result_podcasts(mydata);
    },
    "podcasts.json");
}

function showLatest() {
    loadJSON(function(response) {
        var mydata = JSON.parse(response);
        document.getElementById("result").innerHTML = get_result_latest(mydata);
    },
    "latest.json");
}

function showUntracked() {
    loadJSON(function(response) {
        var mydata = JSON.parse(response);
        document.getElementById("result").innerHTML = get_result_untracked(mydata);
    },
    "untracked.json");
}

function clearResult() {
    document.getElementById("result").innerHTML = "";
}

function get_result_podcasts(data) {
    var r = data.length + " feeds <ul>";
    for (var i = 0; i < data.length; ++i) {
        r = r + "<li style=\"list-style: none;\"><a href=\"" + data[i]["feed"] + "\"><img src=\"rssfeed.svg\" height=35px></a> <a href=\"" + data[i]["url"] + "\"><b>" + data[i]["title"] + "</b></a>";
        var latestEpisode = data[i]["latestEpisode"];
        r = r + "<br>" + latestEpisode["PubDate"] + ": " + "<a href='" + latestEpisode["Link"] + "'><b>" + latestEpisode["Title"] + "</b></a>";
        r = r + "<br><i>" + data[i]["description"] + "</i>";
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

function get_result_untracked(data) {
    var r = "Number of untracked podcasts: " + data.length + "<ul>";
    for (var i = 0; i < data.length; ++i) {
        r = r + "<li style=\"list-style: none;\"><a href=\"" + data[i]["feed"] + "\"><img src=\"rssfeed.svg\" height=35px></a> ";
        r = r + "<a href=\"" + data[i]["url"] + "\">" + data[i]["title"] + "</a>";
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