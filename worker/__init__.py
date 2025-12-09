'''
# file: main.py
# -*- coding: utf-8 -*-
uimap.UIMap의 컴포넌트(user_id_textbox, password_textbox, login_button)를 사용해 
창 기준 좌표 클릭+키 입력으로 로그인. 콜백 있으면 실행.
분석을 클릭해서 분석창이 뜨면 분석 시작. 
'''
import sys, os, shutil, time
from datetime import date

from common.log import logger
from common.json import load_json
from db.path_config import PathConfig

from worker.analyzer.config.config import Config
from worker.analyzer.config.uimap  import UIMap
from worker.analyzer.tasks.login         import LoginTask
from worker.analyzer.tasks.main_win_ctrl import MainWinCtrl
from worker.analyzer.tasks.analysis_win_ctrl import AnalysisWinCtrl
from worker.analyzer.tasks.prescription_ctrl import PrescriptionCtrl
from worker.analyzer.utils.win_ops     import set_dpi_awareness
from worker.analyzer.utils.test_ctrl   import TestCtrl
from worker.analyzer.utils.proc_ctrl   import ProcessControl


''' TODO
- On Windows local server/client program
- Options
  1) Automatic 전사 기능
  2) Automatic 분석
    - 완료되면 최종 버전의 formatted 진단 chart 웹 화면에 보여주는 기능 
    - 진단 chart를 USB에도 저장
    - 고객 PC의 MEDICAL.mdb를 USB에 복사하는 기능
 
  3) DB Merge (client's DB and Automatic 분석 결과)
'''
def worker_main(worker_param_path):
    inparam = load_json(worker_param_path)
    client_profile = inparam["client_profile"]
    test_cases = inparam["test_cases"]
    iter_cnt = inparam["iter_cnt"]

    is_failed = True

    # 1. Get worker common config from the global path config
    # PathConfig.cleanup_and_provision_folder(client_profile)
    PathConfig.post_init(client_profile)
    print("--- PathConfig.worker_drv: %s" % PathConfig.worker_drv)
    TestCtrl.post_init(client_profile, PathConfig.worker_drv)
    
    try: 
      set_dpi_awareness()  # screen 확대 비율, screen 선택 등
      
      # 1. Look up or run, and then activate the app
      mw_ctrl = MainWinCtrl().start()  # main window control
      
      # 2. Log in
      ok = LoginTask(mw_ctrl).run() # user_id = login["uid"], password = login["pw"])
      if ok == False: 
          raise RuntimeError(f"Login failed")
      logger.info(f"Logged in")
      
      # 3. Set main window config
      mw_ctrl.select_square_wave()
      mw_ctrl.select_mixed_wave()
      logger.info(f"Main configuration is set up")

      # 4. Open analysis window for automatic analysis
      aw = mw_ctrl.click(UIMap.main.analysis_button)  # analysis popup window
      if not aw:
        raise RuntimeError(f"Analysis popup window failed in starting") 

      logger.info("Analysis starts with iter_cnt:%s, test cases: %s" % 
                    (iter_cnt, test_cases))
      aw_ctrl = AnalysisWinCtrl(aw, PathConfig)
      aw_ctrl.start(test_cases, iter_cnt)

      # 5. Manage prescription
      ps = PrescriptionCtrl(client_profile, aw_ctrl.prescription)
      ps.show()

      # 6. Convert the Prescription to a program and add it to mdb, 
      #    that is handed over it to backend

    except Exception as e:
       logger.exception(f"{e}")
       # test_top 에 FAILED.txt를 생성.
       is_failed = True
    
    ProcessControl.kill_all()
    time.sleep(2.0)  # wait for medical.exe and freqgen.exe to be terminated completely

    return is_failed



if __name__ == "__main__": 
    from db.path_config import PathConfig
    import datetime
    
    is_failed = worker_main(PathConfig.worker_drv["worker_param_path"])
    exit(is_failed)

    # user_profile = {"name": "kkk", "bdate": "1990-01-01", "sex": "여", 
    #                 "weight": 55, "height": 170, 
    #                 "test_time": datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") }
    #                 # "2025-12-04T14-23"}
    # test_cases = ['A', '골격', '극성', '근건', '내분비', '뇌', '면역', 
    #             '바흐플라워','병원균', '소화', '순환', '신경', '암', 
    #             '오관', '운동', '장부', '장부보사본초', '정서', '차크라', '혈액']
    # PathConfig.clean_and_provision_folder(user_profile)
    # worker_main(user_profile, test_cases, 10, PathConfig)

