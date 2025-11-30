from .worker import Worker
from ..common.log import logger
from flask import Blueprint, current_app, request, jsonify, url_for, abort
import datetime, json

backend_bp = Blueprint("backend", __name__)
worker = None

@backend_bp.route("/analysis/start", methods=["POST"])
def api_analysis_start():
    logger.info("=== POST /api/analysis/start")

    # 1. Parse request options
    try:
        data = request.get_json(force=True)
        run_count = int(data["run_count"])
        profile = data["user_profile"]
        tests = data["test_option"]

        if run_count < 1 or not tests:
            abort(400, "invalid params")

        # Trigger Quick...'s 시작함수
        # Domain 코드의 API function 들을 어떻게 연결할 것인가... 
    except Exception as e:
        abort(400, str(e))

    # 실제 작업 등록/비동기 처리 로직은 생략
    run_id = "run-" + profile["name"] + "-" + datetime.datetime.now().strftime("%m%d%H%M%S")
    print("run_id = %s" % run_id)

    # 2. Build directory structure
    worker = Worker()
    current_app.config["worker"] = worker

    # 변경된 상태 페이지 URL로 반환
    # (a) report_url에 JSON 쿼리로 포함 (Flask가 자동 인코딩)
    report_url = url_for(
        "frontend.analysis_status",
        run_id=run_id,
        user_profile=json.dumps(profile, ensure_ascii=False),
        test_option=json.dumps(tests, ensure_ascii=False),
    )
    return jsonify({
        "ok": True,
        "report_url": report_url,
        "user_profile": json.dumps(profile, ensure_ascii=False),
        "test_option": json.dumps(tests, ensure_ascii=False),
        "run_id": run_id
    })

@backend_bp.route("analysis/status", methods=["POST"])
def api_analysis_status_post():
    """
    - 요청: { run_id, serial_id }
    - 응답: { serial_id_start, serial_id_end, finish_flag, 
              items:[...], session_payload:{...} }
        각 item은 image_files(파일명 배열)가 있을 경우 
        image(데이터URL 배열)로 변환되어 반환.
    """
    logger.info("=== POST /api/analysis/status")
    data = request.get_json(force=True)
    run_id = data.get("run_id")
    serial_id = int(data.get("serial_id", 0))
    user_profile = data.get("user_profile")  # 그대로 되돌려줌(요구사항)

    worker = current_app.config.get("worker", None)
    # job = RUNS.get(run_id)
    # if not job:
    #     abort(404, "run not found")

    # # 현재까지 완료된 구간 계산
    # all_items = job.get("items", [])

    # # 새로 보낼 아이템들만 슬라이싱(직관을 위해 filter)
    # new_items = [it for it in all_items if (it.get("serial_id", -1) >= serial_id)]
    # serial_id_end = job.get("serial_id_end", -1)
    new_items = [
        {"serial_id": serial_id, # test_ctrl.id
        "cat": "오관", "subcat": "눈", "description": "맥립종", 
        "percent": 50, "group": "GB 11-32", 
        "image": [
            "E:\App\Data\VSCode\iqa\domain\output\kkk\2025-11-18T22-43\html\image\match_tid1_rid2_A.bmp", 
            "E:\App\Data\VSCode\iqa\domain\output\kkk\2025-11-18T22-43\html\image\progress_tid1_rid2_A.bmp"], 
        "test_case": "A", "run_id": 2, "code": "A0010001", "part": ""
        }, 
        {"serial_id": serial_id + 1, 
        "cat": "오관", "subcat": "코", "description": "정맥동염", 
        "percent": 10, "group": "GB 11-32", 
        "image": [
            "E:\App\Data\VSCode\iqa\domain\output\kkk\2025-11-18T22-43\html\image\match_tid1_rid3_A.bmp", 
            "E:\App\Data\VSCode\iqa\domain\output\kkk\2025-11-18T22-43\html\image\progress_tid1_rid3_A.bmp"], 
        "test_case": "A", "run_id": 3, "code": "A0010001", "part": ""
        }]

    return jsonify({
        "serial_id_start": serial_id, #serial_id,
        "serial_id_end": serial_id + 1, #serial_id_end,
        "user_profile": user_profile,
        "finish_flag": False, #bool(job.get("finished", False)),
        "items": new_items
    })







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

