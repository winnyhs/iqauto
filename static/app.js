function startAnalysis() {
    var btn = document.getElementById("btn_start");
    btn.disabled = true;
    btn.style.background = "gray";

    var rc = document.getElementById("run_count").value;

    var selected = [];
    var i;
    for (i = 1; i <= 77; i++) {
        var id = "opt" + i;
        var el = document.getElementById(id);
        if (el && el.checked) {
            selected.push(id);
        }
    }

    var jsonTxt = '{"run_count":"' + rc + '","options":[';
    for (i = 0; i < selected.length; i++) {
        jsonTxt += '"' + selected[i] + '"';
        if (i < selected.length - 1) jsonTxt += ",";
    }
    jsonTxt += "]}";

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/run_analysis", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4) {
            document.getElementById("progress_text").innerHTML =
                "분석 시작됨 (1분마다 업데이트)";
            window._progressTimer = setInterval(requestProgress, 60000);
        }
    };
    xhr.send(jsonTxt);
}

function requestProgress() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/api/progress", true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var r = JSON.parse(xhr.responseText);
            var msg = "진행률: " + r.percent + "%";
            if (r.done) {
                msg += " (완료)";
                clearInterval(window._progressTimer);
            }
            document.getElementById("progress_text").innerHTML = msg;
        }
    };
    xhr.send(null);
}
