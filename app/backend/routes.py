from . import longtask
from flask import Blueprint, request, jsonify, url_for, abort
import datetime

backend_bp = Blueprint("backend", __name__)


@backend_bp.route("/analysis/start", methods=["POST"])
def api_analysis_start():
    print("=== [POST] /api/analysis/start")
    try:
        data = request.get_json(force=True)
        run_count = int(data["run_count"])
        profile = data["user_profile"]
        tests = data["test_option"]
        if run_count < 1 or not tests:
            abort(400, "invalid params")
    except Exception as e:
        abort(400, str(e))

    # 실제 작업 등록/비동기 처리 로직은 생략
    run_id = "run-" + datetime.datetime.now().strftime("%m%d%H%M")
    print("run_id = %s" % run_id)
    # 변경된 상태 페이지 URL로 반환
    report_url = url_for("frontend.analysis_status", run_id=run_id)
    return jsonify({"ok": True, "report_url": report_url, 
                    "description": "Triggered analyzing"})



@backend_bp.route("/run_analysis", methods=["POST"])
def run_analysis():
    data = request.get_json() or {}
    print("[BACKEND] run_analysis:", data)
    longtask.start()
    return jsonify({"ok": True})

@backend_bp.route("/progress", methods=["GET"])
def progress():
    pct, done = longtask.progress()
    return jsonify({"percent": pct, "done": done})

@backend_bp.route("/hello")
def hello():
    return jsonify({"message": "hello", "ok": True})

@backend_bp.route("/")
def root():
    return "backend root"

