# ===============================================
# file: medical_automation/win_control.py
# ===============================================
# -*- coding: utf-8 -*-
from typing import Optional, Tuple
from pywinauto.keyboard import send_keys
from pywinauto.mouse import click
import time
from common.log import logger
from common.singleton import SingletonMeta

from worker.analyzer.config.uimap import UIMap, Component, WindowMap
from worker.analyzer.utils.proc_ctrl import ProcessControl
from worker.analyzer.utils.input_ops import click_component_screen
from worker.analyzer.utils.win_ops import (
    find_window_by_title, wait_win_state, bring_to_front, 
    find_sibling_popup
)



class MainWinCtrl(metaclass=SingletonMeta):
    """Title-based window attach. Waits for 'exists ready', then activates."""
    def __init__(self):
        self.wmap = UIMap.main  # main window property
        self.wmap.analysis_button.callback = self.find_popup   # comp, popup, win
        self.wmap.read_button.callback  = self.find_popup
        self.wmap.write_button.callback = self.find_popup

        self.pctrl = ProcessControl  # main process control
        self.win = None # main window WindowSpecification 
                        # self.win.wrapper_object() can be  DialogWrapper, WindowWrapper, ButtonWrapper, EditWrapper, 등등
    
    def start(self): 
        # 1. Start the process. Kill and start the process, if already running
        self.pctrl.start()

        # 2. Connect the window of the process
        win = find_window_by_title(self.wmap.title, self.wmap.backend, self.wmap.start_timeout)
        if win == None: 
            raise OSError(f"Failed to start {self.wmap.title} in {self.wmap.start_timeout}")
        
        # 3. Wait for the process to be ready (exists and visible)
        wait_win_state(win, "exists ready", timeout=self.wmap.ready_timeout)

        # 4. Move the window to (0, 0) so that window border coords be the same with screen coords
        win.move_window(0, 0)

        # 5. Bring the window to the front anyway
        bring_to_front(win)

        # 6. All things are ready now. Set the window in
        self.win = win
        return self
        
    # Select square wave option without verifying
    def select_square_wave(self):
        click_component_screen(self.wmap.square_wave_option)
        return

    # Select mixed wave option without verifying
    def select_mixed_wave(self):
        click_component_screen(self.wmap.mixed_wave_option, verify = False)  # verify MUST be FALSE
        # TODO: Sometimes, not checked
        return
    
    # Click read button → wait popup r"^처방일기$" → move to (0,0)
    def find_popup(self, comp: Component) -> bool:
        end_time = time.time() + max(1.0, comp.popup.ready_timeout)
        timeout = 0.5
        while time.time() < end_time:
            try:
                # 2. Connect Read pop-up window and wait to be ready, visible
                popup = find_sibling_popup(comp.popup.title, comp.popup.cclass, 
                                            parent_win = self.win, timeout = timeout)
                if popup == None:
                    raise OSError(f"Failed to connect {popup} in {timeout}")
                
                # 3. Move the window to (0, 0) so that its border coords be the same with screen ones
                popup.move_window(0, 0)
                # 4. Move to the front
                bring_to_front(popup)
                return popup
            except Exception as e:
                time.sleep(0.5)
                logger.error(f"{type(e).__name__}: {e}: Failed to get ready read window {comp.popup.title} in {timeout}s")
        return None
    
    def click(self, comp: Component, verify:bool = False): 
        # 1. click component
        click_component_screen(comp, verify=verify)
        if comp.callback: 
            return comp.callback(comp)

    def click_xy(self, xy: Tuple[int, int]):
        click(button='left', coords=xy)
