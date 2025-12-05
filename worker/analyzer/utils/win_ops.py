# =========================
# file: common/window_ops.py
# =========================
# -*- coding: utf-8 -*-
"""Windows-level ops: DPI, window focus, dialogs, Win32 text (screen coords only)."""
from __future__ import annotations
import time, re, ctypes, inspect
from typing import Tuple

import win32con, win32gui
from pywinauto import Desktop, WindowSpecification
from pywinauto.timings import wait_until_passes, TimeoutError as WaitTimeout
from pywinauto.keyboard import send_keys

from common.log import logger
from worker.analyzer.config.uimap import Component, WindowMap


# DPI awareness (권장)
def set_dpi_awareness() -> None:
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)  # Per-Monitor V2
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # System DPI
    except Exception:
        pass

def wrapper(win: WindowSpecification): 
    return win.wrapper_object()

def bring_to_front(win, do_wait:bool = True):
    '''return win if succeeded, None, otherwise'''
    if not win: 
        raise ValueError(f"Valid window must be given: {win}")
    try:
        win.restore()
        win.set_focus()  # put it foreground. might be neglected
        time.sleep(0.3)  # 0.2 ~ 0.5s is usual. 1s for heavy app
        win.set_focus()  # give it focus (but, doesn't move mouse lt)
        if do_wait == True: 
            return wait_win_state(win, "exists ready active", timeout=1.0)
        
    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}: bring_to_front failed: {win}")
        return None

def wait_win_state(win, state: str = None, timeout:float = 10.0):
    '''return win if succeeded, None, otherwise'''
    state = state if state else "exists ready"
    if hasattr(win, "wait"): # WindowSpecification
        try: 
            win.wait(state, timeout=timeout)
            return win
        except Exception as e: 
            logger.error(f"{type(e).__name__}: {e}: Window Spec failed in getting '{state}' in {timeout}s")
            return None
    
    else: # Wrapper object like ButtonWrapper, DialogWrapper, WindowWrapper
        end_time = time.time() + timeout
        if re.search("exists", state): 
            return win
        while time.time() < end_time:
            try:
                print(f"{re.search('active', state)} {re.search('ready', state)}")
                if re.search("active", state) and win.is_active(): 
                    return win
                if re.search("ready", state) and win.is_visible():
                    return win
            except Exception as e: 
                logger.error(f"{type(e).__name__}: {e}: Window Wrapper failed in getting '{state}' in {timeout}s")
                return None
            time.sleep(0.2)

        logger.error(f"Window failed in getting '{state}' in {timeout}s")
        return None

def find_window_by_title(title_re: str, backend: str = "win32", timeout: float = 10.0):
    try:
        dlg = Desktop(backend=backend).window(title_re=title_re)
        dlg.wait("exists ready", timeout=timeout)
        return dlg
    except TimeoutError as e: 
        logger.error(f"{type(e).__name__}: {e}: not ready in {timeout}s: kill")
        # TODO: raise this so that the caller can kill this process to be restarted anyway
    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}: no window of title {title_re}")
        return None

def find_child_popup(popup_title: str, popup_class: str, 
                     parent_win = None, parent_title: str = None, backend: str = "win32", 
                     timeout: float = 1.0): 
    if parent_win == None:
        if parent_title == None or parent_title == "": 
            raise ValueError(f"parent window object or its title must be given")
        parent_win = Desktop(backend=backend).window(title_re=parent_title)
        parent_win.wait("exists ready", timeout=0.01)
        # parent_win = parent_win.wrapper_object() 
    
    wait_until = time.time() + timeout
    while True:
        siblings = parent_win.children() 
        for win in siblings: 
            if win.window_text() == popup_title and win.class_name() == popup_class: 
                wait_win_state(win, "exists ready", timeout = timeout)
                return win
        logger.error(f"No such sibling window yet: title={popup_title} parent={parent_win.window_text()}")
        time.sleep(0.5)
        if wait_until < time.time(): 
            break
    return None

def find_sibling_popup( popup_title: str, popup_class: str, 
                        parent_win: WindowSpecification = None, parent_title: str = None, backend: str = "win32", 
                        timeout: float = 1.0): 
    if parent_win == None:
        if parent_title == None or parent_title == "": 
            raise ValueError(f"parent window object or its title must be given")
        parent_win = Desktop(backend=backend).window(title_re=parent_title)
        parent_win.wait("exists ready", timeout=0.01)
        # parent_win = parent_win.wrapper_object() 
    
    wait_until = time.time() + timeout
    while True:
        # --- choose correct sibling scope ---
        if parent_win.wrapper_object().parent() is None:
            # top-level window → get all top-level windows
            siblings = Desktop(backend=backend).windows(top_level_only=True)
        else:
            siblings = parent_win.parent().children()
        
        for win in siblings: 
            #logger.debug(f"{type(win).__name__} : [{win.window_text()}] [{win.class_name()}]")
            if re.search(popup_title, win.window_text()) and win.class_name() == popup_class: 
                wait_win_state(win, "exists ready", timeout = timeout)
                return win
        
        logger.error(f"No such sibling window yet: title={popup_title} parent={parent_win.window_text()}")
        time.sleep(timeout/2)
        if wait_until < time.time(): 
            break
    return None


            # is_success = check_success_by_popup(
            #     popup_title_re="medical",  # r"(?i)^medical$",
            #     popup_class="#32770", 
            #     parent_window=self.win_ctrl.win,
            #     max_wait=self.popup_wait_sec,
            # )

'''
def check_success_by_popup(comp: Component, win) -> bool: 
    popup = comp.popup

    # 1.Search for login error dialog pop-up window
    dlg = find_sibling_popup(popup.title, popup.cclass, win, timeout=popup.ready_timeout)
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

def get_text_at_mouse(x: int, y: int) -> str:
    # x, y = win32api.GetCursorPos() 
    hwnd = win32gui.WindowFromPoint((x, y))
    if hwnd == 0:
        logger.error(f"No window found under cursor ({x}, {y}).")
        return None

    # text = win32gui.GetWindowText(hwnd)
    buf = ctypes.create_unicode_buffer(512)
    win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, 512, buf)
    print(f"Text: {buf.value!r}")
    # cls_name = win32gui.GetClassName(hwnd)
    # rect = win32gui.GetWindowRect(hwnd) # parent, dimension, ...
    # left, top, right, bottom = rect
    return buf.value
'''