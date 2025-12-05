
# =========================
# file: tasks/login.py
# =========================
# -*- coding: utf-8 -*-
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Optional
import win32api, win32con, win32gui, time

from common.singleton import SingletonMeta
from common.log import logger
from worker.analyzer.config.uimap        import Component
from worker.analyzer.tasks.main_win_ctrl import MainWinCtrl

from worker.analyzer.utils.win_ops import (
    find_sibling_popup,
)
from worker.analyzer.utils.input_ops import (
    click_component_screen,
    double_click_component_screen, 
    type_text, send_keys
)

class LoginTask(metaclass=SingletonMeta):
    def __init__(self, win_ctrl: MainWinCtrl):
        self.win_ctrl: MainWinCtrl = win_ctrl
        self.comp: Component = self.win_ctrl.wmap.login_button
        self.comp.callback = self.check_success_by_popup  # comp, popup, win
        self.try_cnt: int = 2

    def _type_text_by_dclick(self, comp, text: str, y_nudge: int = 0):
        """더블클릭으로 전체 선택 → 백스페이스 → 입력."""
        double_click_component_screen(comp, y_nudge=y_nudge) # select all
        # time.sleep(0.01)
        type_text("{BACKSPACE}" + text, clear=False) # delete and input text

    def check_success_by_popup(self, comp: Component) -> bool: 
        popup = comp.popup

        # 1.Search for login error dialog pop-up window
        logger.debug(f"{popup.title} {popup.cclass} -------- {self.win_ctrl}")
        dlg = find_sibling_popup(popup.title, popup.cclass, self.win_ctrl.win, timeout=popup.ready_timeout)
        if dlg == None: # no popup yet. may be success
            return True
        
        # 2. Search for OK button and click to close
        logger.debug(f"Error dialog poped up")
        try:
            dlg.set_focus()
            time.sleep(0.2)
            dlg.set_focus()
            time.sleep(0.2)
            send_keys("{ENTER}")   # default selection is clicked

            # try:
            #     for child in dlg.children(): 
            #         if child.friendly_class_name() == "Button" and \
            #             re.search(popup.text, child.window_text()): 
            #             logger.debug(f"{child} is caught to click")
            #             child.click_input()
            # except Exception as e:
            #     logger.info(f"{type(e).__name__}: {e}: No OK button in {popup.title} window")
            #     send_keys("{ENTER}")   # default selection is clicked
            time.sleep(0.1)
        except Exception as e: 
            raise OSError(f"{type(e).__name__}: {e}: Popup window is not accessible")    
        return False
    
    def click(self, comp:Component): 
        click_component_screen(comp)
        if comp.callback: 
            return comp.callback(comp)

    def _login(self, user_id: str, password: str) -> None:
        ui = self.win_ctrl.wmap
        user_id = user_id if user_id else ui.user_id_textbox.text
        password = password if password else ui.password_textbox.text 
        
        # User ID: 더블클릭 선택 → 삭제 → 입력
        # click_component_screen(ui.user_id_textbox)
        # type_text("{BACKSPACE}" + user_id, clear=False) # delete and input text
        self._type_text_by_dclick(ui.user_id_textbox, user_id, y_nudge=0)

        # click_component_screen(ui.password_textbox)
        # type_text("{BACKSPACE}" + password, clear=False)
        self._type_text_by_dclick(ui.password_textbox, password, y_nudge=0)

        # Login
        return self.click(ui.login_button)
    
    def run(self, user_id: str = None, password: str = None) -> bool:
        if not self.win_ctrl.win:
            raise RuntimeError("Window not initialized. Call wait_state('exists ready') first.")
        
        for _ in range(max(0, self.try_cnt)):
            return True if self._login(user_id, password) else False

            # is_success = check_success_by_popup(
            #     popup_title_re="medical",  # r"(?i)^medical$",
            #     popup_class="#32770", 
            #     parent_window=self.win_ctrl.win,
            #     max_wait=self.win_ctrl.wmap.login_button.popup.ready_time,
            # )
            # if is_success == True:
            #     return True
        return False