from ..common.log import logger
from ..common.sys import make_image_url
from db.config import GlobalConfig as config

from flask import (Blueprint, current_app, request, 
    jsonify, url_for, abort, send_from_directory
)
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
        user_profile = json.dumps(data["user_profile"], ensure_ascii=False)
        test_cases = json.dumps(tedata["test_option"], ensure_ascii=False)

        if run_count < 1 or not tests:
            abort(400, "invalid params")
    except Exception as e:
        abort(400, str(e))

    # let the worker to start, here
    # Trigger Quick...'s 시작함수
    # Domain 코드의 API function 들을 어떻게 연결할 것인가... 
    print("test_id = %s" % test_id)
    # worker = Worker()
    # current_app.config["worker"] = worker

    # 변경된 상태 페이지 URL로 반환
    # report_url에 JSON 쿼리로 포함 (Flask가 자동 인코딩)
    report_url = url_for(
        "frontend.analysis_status",
        test_id=test_id,
        user_profile=user_profile, 
        test_cases=test_cases
    )
    return jsonify({
        "ok": True,
        "report_url": report_url,
        "user_profile": user_profile,
        "test_cases": test_cases
    })

@backend_bp.route("analysis/status", methods=["POST"])
def api_analysis_status_post():
    """
    - 요청: { test_id }
    - 응답: { test_id_start, test_id_end, finish_flag, 
              items:[...] }
        각 item은 image_files(파일명 배열)가 있을 경우 
        image(데이터URL 배열)로 변환되어 반환.
    """
    logger.info("=== POST /api/analysis/status")
    data = request.get_json(force=True)
    test_id = int(data.get("test_id", 0))
    user_profile = data.get("user_profile")  # 그대로 되돌려줌(요구사항)

    # worker = current_app.config.get("worker", None)

    item_list = []
    progress_dir = config.worker_drv["progress_dir"]
    for sid in range(test_id, test_id + 5): 
        progress_path = os.path.join(progress_dir, str(test_id) + '.json')
        if not os.path.isfile(progress_path): # no more progress yet
            test_id_end = sid - 1
            finish_flag = False
            break

        item = load_json(progress_path)
        if item["finish_flag"] == True: 
            test_id_end = sid - 1
            finish_flag = True
            break

        item_list.append(item)

    progress_data = {"test_id_start": test_id, 
                    "test_id_end": test_id_end, 
                    "finish_flag": finish_flag,  
                    "user_profile": user_profile, 
                    "item": item_list}
    for sid in range(test_id, test_id_end + 1): 
        progress_path = os.path.join(progress_dir, str(test_id) + '.json')
        os.remove(progress_path)
        
    return jsonify(progress_data)


@backend_bp.route("/files/<path:rel>")
def file_serve(rel_path): #: str):
    # 안전 서빙: 루트 밖 접근 차단
    abs_path = os.path.realpath(os.path.join(config["image_root"], rel_path))
    image_root = os.path.realpath(config["image_root"])
    if os.path.commonpath([image_root, abs_path]):
        abort(403)

    logger.debug("rel_path: %s", rel_path)
    logger.debug("abs_path: %s", abs_path)
    logger.debug("image_root: %s", image_root)

    # 캐시 헤더 등은 필요 시 추가
    directory = image_root
    filename = os.path.relpath(abs_path, image_root)
    image = send_from_directory(directory, filename)
    logger.debug("    --> %s", image)
    return image





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

