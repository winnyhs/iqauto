from flask import (current_app, request, url_for, abort, send_from_directory)
import datetime, json, os, shutil, sys, subprocess, threading

from db.path_config import PathConfig
from common.log import logger
from common.json import load_json, save_json, atomic_save_json

from worker import worker_main
from .worker_mon import read_worker_stdout, monitor_worker_process



def analysis_start(request): 
    # 1. Parse request options
    try:
        data = request.get_json(force=True)
        logger.info("   %s" % data)
        run_count = int(data["run_count"])
        client_profile = data["user_profile"]
        test_cases   = data["test_cases"]

        if run_count < 1 or not test_cases:
            abort(400, "invalid params")
    except Exception as e:
        abort(400, str(e))

    client_profile["test_time"] = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    logger.info("Trigger a worker for automated analysis:")

    # 2. clean up and provision for this new analysis
    PathConfig.cleanup_and_provision_folder(client_profile)
    # logger.debug("--- progress_dir: %s", PathConfig.worker_drv["progress_dir"])
    # logger.debug("--- image_dir: %s", PathConfig.worker_drv["image_dir"])

    # 3. Call API to trigger worker main thread
    worker_param = {"client_profile": client_profile,
                    "test_cases": test_cases, 
                    "iter_cnt": run_count}
    worker_param_path = PathConfig.worker_drv["worker_param_path"]
    save_json(worker_param, worker_param_path)
    cmd = [sys.executable, "-m", "worker.__init__", worker_param_path]
    worker_process = subprocess.Popen(cmd, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT, 
                                    universal_newlines=True, 
                                    bufsize=1)
    threading.Thread(target=read_worker_stdout, args=(worker_process,), daemon=True).start()
    threading.Thread(target=monitor_worker_process, args=(worker_process,), daemon=True).start()


    current_app.config["path_config"] = PathConfig
    print("--- current_app.config['path_config'] = %s", current_app.config["path_config"])
    current_app.config["client_profile"] = client_profile
    current_app.config["worker_process"] = worker_process


    # 변경된 상태 페이지 URL로 반환
    # report_url에 JSON 쿼리로 포함 (Flask가 자동 인코딩)
    report_url = url_for(
        "frontend.analysis_status",
        user_profile= json.dumps(client_profile, ensure_ascii=False), 
        test_cases  = json.dumps(test_cases, ensure_ascii=False)
    )

    return report_url


def analysis_status_post(request): 
    """
    - 요청: { test_id }
    - 응답: { test_id_start, test_id_end, finish_flag, 
              items:[...] }
        각 item은 image_files(파일명 배열)가 있을 경우 
        image(데이터URL 배열)로 변환되어 반환.
    """
    data = request.get_json(force=True)
    test_id = int(data.get("test_id", 0))
    client_profile = data.get("user_profile")
    logger.info("    test_id=%s", test_id)
    
    config = current_app.config.get("path_config", None)
    print("-------- current_app.config['path_config'] = %s", config)

    progress_dir = PathConfig.worker_drv["progress_dir"]
    item_list = []
    path_list = []
    for tid in range(test_id, test_id + 10): 
        progress_path = PathConfig.progress_path(tid)
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

        url = [make_image_url(path, PathConfig.worker_drv["image_dir"]) \
                for path in prog_data["item"]["image"]]
        prog_data["item"]["image"] = url  # url_for("backend.file_serve", rel_path=rel_path)
        test_id_end = tid
        finish_flag = False
        item_list.append(prog_data["item"])

    progress_data = {"test_id_start": test_id, 
                    "test_id_end": test_id_end, 
                    "finish_flag": finish_flag,  
                    "user_profile": client_profile, 
                    "items": item_list}
    for p in path_list: 
        os.remove(p)
    
    return progress_data

def make_image_url(path, allowed_root): 
    """
    절대경로 -> /files/<rel> URL 생성.
    루트 밖 경로는 ValueError.
    """
    allowed_root = os.path.normcase(os.path.realpath(allowed_root))
    path         = os.path.normcase(os.path.realpath(path))
    if os.path.commonpath([allowed_root, path]) != allowed_root:
        print("--allowed_root: %s" % allowed_root)
        print("-- path: %s" % path)
        raise ValueError("path %s outside root: %s" % (path, allowed_root))

    rel_path = os.path.relpath(path, allowed_root).replace("\\", "/")
    return url_for("backend.api_file_serve", rel_path=rel_path)

def file_serve(rel_path): 
    worker_drv = current_app.config.get("path_config", None).worker_drv
    # 안전 서빙: 루트 밖 접근 차단
    abs_path = os.path.realpath(os.path.join(worker_drv["image_dir"], rel_path))
    image_root = os.path.realpath(worker_drv["image_dir"])
    logger.debug("rel_path: %s", rel_path)
    logger.debug("abs_path: %s", abs_path)
    logger.debug("image_root: %s", image_root)
    if os.path.commonpath([image_root, abs_path]) != image_root:
        abort(403)

    # 캐시 헤더 등은 필요 시 추가
    filename = os.path.relpath(abs_path, image_root)
    image = send_from_directory(image_root, filename)
    return image

