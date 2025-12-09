import os, sys, time, threading, subprocess
from datetime import datetime

worker_process = None
status_lock = threading.Lock()

worker_state = {
    "pid": None,
    "running": False, 
    "exit_code": None,
    "updated_at": None,
}

def _set_state(**kwargs):
    with status_lock:
        for k, v in kwargs.items():
            worker_state[k] = v
        worker_state["updated_at"] = datetime.now().isoformat(timespec="seconds")

'''
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
'''

def read_worker_stdout(proc):
    """
    worker stdout 을 실시간으로 읽어,
    backend 의 stdout (콘솔) 에 그대로 출력하는 함수.
    """
    for raw_line in proc.stdout:
        line = raw_line.rstrip("\n")
        print(f"[worker] {line}", flush=True)  # backend 콘솔에 실시간 표시됨

def monitor_worker_process(proc):
    print("%s" % proc.pid)
    _set_state(
        running=True,
        pid = proc.pid
    )
    exit_code = proc.wait()

    if exit_code == 0:
        result = "normal_exit"
    else:
        result = "crash"

    _set_state(
        running=False,
        exit_code=result
    )

