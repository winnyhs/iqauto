# worker__init__.py
import time
import sys
import random
import traceback


def worker_main():
    """
    실제 GUI 자동화 작업이 들어갈 main 함수.
    여기서는 데모용으로 sleep + 랜덤 오류를 넣어둠.
    """
    # 시작 상태 알림
    print("STATUS:STARTED", flush=True)

    for i in range(0,20): 
        time.sleep(1.0)
        print("%s seconds since started" % i, flush=True) 

    try:
        # 예시: 10단계 작업을 수행
        # for i in range(10):
        #     print(f"[worker] working step {i+1}/10", flush=True)
        #     time.sleep(1.0)

        # 데모용: 30% 확률로 내부 오류 발생
        i = random.random()
        if i < 0.3:
            raise RuntimeError(f"Something went wrong: %s" % i)

        # 모든 작업이 정상 완료된 경우
        print("STATUS:OK", flush=True)
        sys.exit(0)

    except Exception as e:
        # 비정상 종료(내부에서 예외를 잡고 종료)
        err_msg = f"{type(e).__name__}: {e}"
        print(f"STATUS:ERROR:{err_msg}", flush=True)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    worker_main()

'''
$ (venv)$ python -m worker.__init__
STATUS:STARTED
STATUS:ERROR:RuntimeError: Something went wrong: 0.18195166600082802
Traceback (most recent call last):
  File "C:\analyzer\help\process_ctrl\worker\__init__.py", line 25, in worker_main
    raise RuntimeError(f"Something went wrong: %s" % i)
RuntimeError: Something went wrong: 0.18195166600082802

user01@MedicalWin10 MINGW64 /c/analyzer/help/process_ctrl (main)
$ (venv)$ python -m worker.__init__
STATUS:STARTED
STATUS:OK
'''