# backend.py
import os
import sys
import time
import threading
import subprocess
from datetime import datetime

from flask import Flask, jsonify, request

# worker 모듈 경로 (python -m worker__init__ 를 사용할 경우)
WORKER_MODULE = "worker.__init__"

app = Flask(__name__)

# --- 상태 관리용 전역 변수 ---
worker_process = None
status_lock = threading.Lock()

worker_state = {
    "pid": None,
    "running": False,
    "result_type": None,   # "running" / "normal_exit" / "abnormal_exit" / "crash"
    "message": "",
    "exit_code": None,
    "last_heartbeat": None,
    "last_status_tag": None,   # None / "STARTED" / "OK" / "ERROR"
    "updated_at": None,
}


def _set_state(**kwargs):
    with status_lock:
        for k, v in kwargs.items():
            worker_state[k] = v
        worker_state["updated_at"] = datetime.now().isoformat(timespec="seconds")


def _reset_state():
    _set_state(
        pid=None,
        running=False,
        result_type=None,
        message="",
        exit_code=None,
        last_heartbeat=None,
        last_status_tag=None,
    )


# --- worker stdout 읽기 스레드 ---
def read_worker_stdout(proc: subprocess.Popen):
    """
    worker의 stdout을 한 줄씩 읽어 STATUS 메시지를 파싱.
    STATUS:STARTED
    STATUS:OK
    STATUS:ERROR:<message>
    """
    global worker_state

    print("--- read_worker_stdout")

    for raw_line in proc.stdout:
        line = raw_line.strip()
        if not line:
            continue

        # 디버그용 로그
        print(f"[worker] stdout: {line}", flush=True)

        if line.startswith("STATUS:"):
            # STATUS:<TAG>[:<msg>]
            parts = line.split(":", 2)  # 최대 3조각
            tag = parts[1]

            if tag == "STARTED":
                _set_state(
                    last_status_tag="STARTED",
                    last_heartbeat=time.time(),
                    message="Worker started",
                )
            elif tag == "OK":
                _set_state(
                    last_status_tag="OK",
                    last_heartbeat=time.time(),
                    message="Worker completed successfully",
                )
            elif tag == "ERROR":
                msg = parts[2] if len(parts) >= 3 else "Unknown error"
                _set_state(
                    last_status_tag="ERROR",
                    last_heartbeat=time.time(),
                    message=msg,
                )
        else:
            # 필요하다면 일반 로그를 따로 저장할 수도 있음
            pass


# --- worker 종료 모니터링 스레드 ---
def monitor_worker_process(proc: subprocess.Popen):
    """
    프로세스 종료를 기다렸다가 exit_code와 마지막 STATUS를 보고
    normal_exit / abnormal_exit / crash 를 구분.
    """
    global worker_process

    exit_code = proc.wait()
    print(f"[backend] worker process exited with code {exit_code}")

    with status_lock:
        last_tag = worker_state["last_status_tag"]
        msg = worker_state["message"]

    # 분류 로직
    if exit_code == 0 and last_tag == "OK":
        result_type = "normal_exit"
        if not msg:
            msg = "Worker exited normally."
    elif last_tag == "ERROR":
        result_type = "abnormal_exit"
        if not msg:
            msg = "Worker reported an error and exited."
    else:
        # STATUS:OK / STATUS:ERROR 없이 종료된 경우 → crash로 간주
        result_type = "crash"
        if not msg:
            msg = "Worker crashed or was killed (no final STATUS)."

    _set_state(
        running=False,
        exit_code=exit_code,
        result_type=result_type,
        message=msg,
    )

    # 전역 참조 정리
    worker_process = None


def kill_existing_worker():
    global worker_process
    if worker_process is None:
        return

    if worker_process.poll() is None:
        print("[backend] terminating existing worker...")
        worker_process.terminate()
        try:
            worker_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("[backend] killing existing worker...")
            worker_process.kill()

    worker_process = None
    _reset_state()


def start_worker():
    """
    기존 worker가 있으면 정리하고 새로 시작.
    """
    global worker_process

    # 기존 worker 정리
    kill_existing_worker()

    # 상태 초기화
    _reset_state()
    _set_state(running=True, result_type="running", message="Worker starting...")

    # worker 프로세스 실행
    # python -m worker__init__ 를 사용 (worker__init__.py가 PYTHONPATH 상에 있어야 함)
    cmd = [sys.executable, "-m", WORKER_MODULE]
    print(f"[backend] starting worker: {cmd}")

    worker_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # stderr도 stdout으로 합침
        bufsize=1,
        universal_newlines=True,
    )

    _set_state(pid=worker_process.pid)

    # stdout reader thread
    t_reader = threading.Thread(target=read_worker_stdout, args=(worker_process,), daemon=True)
    t_reader.start()

    # monitor thread
    t_monitor = threading.Thread(target=monitor_worker_process, args=(worker_process,), daemon=True)
    t_monitor.start()

    return worker_process.pid


# --- Flask API ---

@app.route("/start-worker", methods=["POST"])
def api_start_worker():
    pid = start_worker()
    return jsonify({"status": "started", "pid": pid})


@app.route("/status", methods=["GET"])
def api_status():
    with status_lock:
        # 딥카피 대신 간단하게 dict 복사
        data = dict(worker_state)
    return jsonify(data)


@app.route("/")
def index():
    # 단순 테스트용 안내
    return "Backend is running. Use /start-worker (POST) and /status (GET)."


if __name__ == "__main__":
    # debug=True는 개발용, 운영 시 False
    app.run(host="127.0.0.1", port=5000, debug=True)
