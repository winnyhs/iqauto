from common.log import logger
from common.json import load_json, save_json, atomic_save_json
from common.sys import rename_leaf
from db.path_config import PathConfig
from .utils import make_image_url
from worker import worker_main


from flask import (Blueprint, current_app, request, 
    jsonify, url_for, abort, send_from_directory
)
import datetime, json, os, shutil

backend_bp = Blueprint("backend", __name__)


@backend_bp.route("/analysis/start", methods=["POST"])
def api_analysis_start():
    logger.info("=== POST /api/analysis/start")

    # 1. Parse request options
    try:
        data = request.get_json(force=True)
        logger.info("   %s" % data)
        run_count = int(data["run_count"])
        user_profile = data["user_profile"]
        test_cases   = data["test_cases"]

        if run_count < 1 or not test_cases:
            abort(400, "invalid params")
    except Exception as e:
        abort(400, str(e))

    user_profile["test_time"] = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    logger.info("Trigger a worker for automated analysis:")

    # 2. clean up and provision for this new analysis
    PathConfig.clean_and_provision_folder(user_profile)
    logger.debug("--- progress_dir: %s", PathConfig.worker_drv["progress_dir"])
    logger.debug("--- image_dir: %s", PathConfig.worker_drv["image_dir"])
    current_app.config["path_config"] = PathConfig
    current_app.config["user_profile"] = user_profile

    # 3. Call API to trigger worker main thread
    # worker.start(user_profile, test_cases, run_count)
    worker_main(user_profile, test_cases, run_count, PathConfig)

    # 변경된 상태 페이지 URL로 반환
    # report_url에 JSON 쿼리로 포함 (Flask가 자동 인코딩)
    user_profile = json.dumps(user_profile, ensure_ascii=False)
    test_cases   = json.dumps(test_cases, ensure_ascii=False)
    report_url = url_for(
        "frontend.analysis_status",
        user_profile= user_profile, 
        test_cases  = test_cases
    )
    return jsonify({"ok": True, "report_url": report_url})

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
    user_profile = data.get("user_profile")
    logger.info("    test_id=%s", test_id)
    
    config = current_app.config.get("path_config", None)
    progress_dir = config.worker_drv["progress_dir"]
    item_list = []
    path_list = []
    for tid in range(test_id, test_id + 10): 
        progress_path = config.progress_path(tid)
        print("----- %s" % progress_path)
        if not os.path.isfile(progress_path): # no more progress yet
            test_id_end = tid - 1
            finish_flag = False
            break

        prog_data = load_json(progress_path)
        path_list.append(progress_path)
        if prog_data["finish_flag"] == True: 
            test_id_end = tid - 1
            finish_flag = True
            break

        url = [make_image_url(path, config.worker_drv["image_dir"]) \
                for path in prog_data["item"]["image"]]
        prog_data["item"]["image"] = url  # url_for("backend.file_serve", rel_path=rel_path)
        test_id_end = tid
        finish_flag = False
        item_list.append(prog_data["item"])

    progress_data = {"test_id_start": test_id, 
                    "test_id_end": test_id_end, 
                    "finish_flag": finish_flag,  
                    "user_profile": user_profile, 
                    "items": item_list}
    for p in path_list: 
        os.remove(p)
    
    logger.debug("--- progress_data: %s", progress_data)
    return jsonify(progress_data)


@backend_bp.route("/files/<path:rel_path>")
def file_serve(rel_path): #: str):
    logger.info("=== GET /api/files/rel_path=%s", rel_path)

    worker_drv = current_app.config.get("worker_drv", None)
    # 안전 서빙: 루트 밖 접근 차단
    abs_path = os.path.realpath(os.path.join(worker_drv["image_drv"], rel_path))
    image_root = os.path.realpath(worker_drv["image_drv"])
    logger.debug("rel_path: %s", rel_path)
    logger.debug("abs_path: %s", abs_path)
    logger.debug("image_root: %s", image_root)
    if os.path.commonpath([image_root, abs_path]) != image_root:
        abort(403)

    # 캐시 헤더 등은 필요 시 추가
    directory = image_root
    filename = os.path.relpath(abs_path, image_root)
    image = send_from_directory(directory, filename)
    logger.debug("    --> %s", image)
    return image


@backend_bp.route("/")
def api_root():
    return "backend root"

