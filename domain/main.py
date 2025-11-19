'''
# file: main.py
# -*- coding: utf-8 -*-
uimap.UIMap의 컴포넌트(user_id_textbox, password_textbox, login_button)를 사용해 창 기준 좌표 클릭+키 입력으로 로그인. 콜백 있으면 실행.

계획 (pseudocode)
- import: AppProperty, MainUIMap, ProcessControl, MainWinCtrl, send_keys, click.
- helpers:
    comp_center(comp) -> (x,y) : 컴포넌트 rect 중심 좌표(창 좌상단 상대).
    to_abs(win, rel_xy) -> (x,y) : 창 rect 기준 절대 좌표 변환.
    click_comp(win, comp) : 컴포넌트 중심 클릭, 콜백 호출.
    type_into(comp, text, clear=True) : 포커스 전제, 텍스트 입력.
- LoginTask:
    __init__(ap, ui).
    ensure_ready() : 프로세스 시작/연결 → 메인 윈도우 획득.
    run(user_id, password) :
    click_comp(user_id_textbox) → type_into(..., user_id).
    click_comp(password_textbox) → type_into(..., password).
    click_comp(login_button).
- 옵션: focus_window() : 필요 시 전면 활성.
- 예외 처리: 필수 컴포넌트 누락/사이즈 0이면 ValueError.
'''
import sys, os, shutil, time
from datetime import date
from config.config import config
from config.uimap    import UIMap
from tasks.login     import LoginTask
from tasks.main_win_ctrl import MainWinCtrl
from tasks.analysis_win_ctrl import AnalysisWinCtrl
from tasks.prescription_ctrl import PrescriptionCtrl
from tasks.access_ctrl import AccessCtrl
from lib.win_ops   import set_dpi_awareness
from lib.log import logger
from lib.test_ctrl import TestCtrl


''' TODO
- On Windows local server/client program
- Options
  1) Automatic 전사
  2) Automatic 분석
    - 분석 결과를 간단히 화면에 보여주면서 진행
    - 완료되면 최종 버전의 formatted 진단 chart 웹 화면에 보여주는 기능 
      csv 파일로 저장하는 기능 (진단_고객명_날짜.csv) 
    - 진단 chart를 medical_고객명_날짜.mdb로 구성 (기본1 + 진단)
      USB에도 저장
    - 고객 PC의 medical2.mdb를 USB에 복사하는 기능
    - 내 PC에서 medical_고객명_날짜.mdb를 medical2.mdb에 머지하는 기능
    - 

  3) DB Merge (client's DB and Automatic 분석 결과)
'''
def main(client_profile, login):
    test_config = {**config["common"], **config["test"]} # Must be here for exception cases
    TestCtrl.init(client_profile, test_config)

    '''# ---- test
    from util.test_result_data import data
    ps = PrescriptionCtrl(client_profile, data)
    ps.show()
    exit()
    # ---- test
    '''
    
    try: 
      set_dpi_awareness()  # screen 확대 비율, screen 선택 등
      
      # 1. Look up and activate
      #    - Start the process if not running yet
      mw_ctrl = MainWinCtrl().start()  # main window control
      
      # # 2. Log in
      # ok = LoginTask(mw_ctrl).run(user_id = login["uid"], password = login["pw"])
      # if ok == False: 
      #     raise RuntimeError(f"Login failed")
      # logger.info(f"Logged in")
      
      # # 3. Set main window config
      # mw_ctrl.select_square_wave()
      # mw_ctrl.select_mixed_wave()
      # logger.info(f"Main configuration is set up")

      # 4. Open analysis window for automatic analysis
      aw = mw_ctrl.click(UIMap.main.analysis_button)  # analysis popup window
      if not aw:
        raise RuntimeError(f"Analysis popup window failed in starting") 
      logger.info(f"Analysis starts")
      aw_ctrl = AnalysisWinCtrl(aw)
      # aw_ctrl.start(iters = 3)
      aw_ctrl.start(targets="test", iters = 10)

      # 5. Manage prescription
      ps = PrescriptionCtrl(client_profile, aw_ctrl.prescription)
      ps.show()

      # 6. Manage database
      # db = AccessCtrl(ps.prescription())  # 기본 1 + 처방
      # db.export(client_profile['name'] + date.today().strftime("%Y.%m.%d") + ".mdb")
      # db.merge() 

    except Exception as e:
       logger.exception(f"{e}")
      # logger.exception(f"{e}: Cleaning up...")
      # if test_config["cleanup_temp_files"] != False: 
      #   try: 
      #     path = os.path.abspath(test_config["temp_dir"])
      #     if os.path.isdir(path): 
      #         shutil.rmtree(path)
        
      #     path = os.path.abspath(test_config["html_dir"])
      #     if os.path.isdir(path): 
      #         shutil.rmtree(path)
      #     time.time(1.0)

      #     os.makedirs(os.path.abspath(test_config["temp_dir"]))
      #     os.makedirs(os.path.abspath(test_config["html_dir"]))

      #   except Exception as e: 
      #     logger.exception(f"{e}: Failed in cleaning up: Do it by yourself!")


if __name__ == "__main__":
  main(client_profile = {"name": "kkk", 
                          "birthdate": "1999.9.9", 
                          "sex": "male", "height": "176", "weight": "69"}, 
      login = {"uid": "user01", "pw": "user01"})
