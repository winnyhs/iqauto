
# =========================
# file: common/input_ops.py
# =========================
# -*- coding: utf-8 -*-
"""Input ops (screen coords only): mouse/keyboard and component-centric clicks."""
from __future__ import annotations
import time, ctypes
import win32api, win32con, win32gui

from typing import Tuple
from pywinauto.mouse import move
from pywinauto.keyboard import send_keys

_SLEEP_TIME = 0.1
'''
def component_center_screen(comp) -> Tuple[int, int]:
    if hasattr(comp, c): 
        return comp.c
    if hasattr(comp, lt) and hasattr(comp, rb): 
        l, t = comp.lt
        r, b = comp.rb
        if r <= l or b <= t:
            raise ValueError(f"Invalid geometry for {comp}") # {getattr(comp, 'name', '?')}
        return (l + r) // 2, (t + b) // 2
    if hasattr(comp, rect): 
        l, t, r, b = comp.rect
        if r <= l or b <= t:
            raise ValueError(f"Invalid geometry for {comp}") # {getattr(comp, 'name', '?')}
        return (l + r) // 2, (t + b) // 2
    return None
'''

def click_stable_at(ax: int, ay: int, pre_move_px: int = 2) -> None:
    # 미리 살짝 빼두기 
    # - escape from Hit test boundary, tool-tip, or hover state
    # - not to be a drag or not to have any offset bug
    move(coords=(ax - pre_move_px, ay - pre_move_px)); 
    time.sleep(0.02)
    
    move(coords=(ax, ay)); 
    time.sleep(0.02)
    win32api.SetCursorPos((ax, ay)) # to pretect move's mal-positioning
    
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0) # low level mouse press 
    time.sleep(0.01)  # not to be a double click or a drag
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0) # Confirm a click
    time.sleep(_SLEEP_TIME)

def click_component_screen(comp, verify: bool = False, y_nudge: int = 0) -> None:
    """컴포넌트 스크린 중심 클릭. 필요 시 y축 미세 보정 재클릭."""
    cx, cy = comp.c # component_center_screen(comp)
    cy += int(y_nudge)
    click_stable_at(cx, cy)
    # if verify:
    #     # 상단 경계 히트 이슈 회피용 아래쪽 재시도
    #     click_stable_at(cx, cy + 6)

def double_click_stable_at(ax: int, ay: int, interval: float = 0.12, pre_move_px: int = 2) -> None:
    """작은 이동 후 빠른 연속 클릭 2회."""
    move(coords=(ax - pre_move_px, ay - pre_move_px)); time.sleep(0.01)
    
    move(coords=(ax, ay)); time.sleep(0.01)
    win32api.SetCursorPos((ax, ay))
    for _ in range(2):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(interval)
    time.sleep(_SLEEP_TIME)

def double_click_component_screen(comp, y_nudge: int = 0, verify: bool = False) -> None:
    cx, cy = comp.c
    cy += int(y_nudge)
    double_click_stable_at(cx, cy)
    # if verify:
    #     # 상단 경계 오인 클릭 시 살짝 아래로 재시도
    #     double_click_stable_at(cx, cy + 6)

def drag_left(src, dst, duration=0.2, steps=30):
    """
    Left-button drag from screen point `from` to `to`.
    Args:
        from: (x, y) ints.
        to:   (x, y) ints.
        duration: total seconds. (0.2 ~ 0.3 추천)
        steps: number of intermediate moves. (20 ~ 40 추천)
    Example:
        drag_left((229, 40), (200, 40), duration=0.2, steps=20)
    Why duration and steps: 
        많은 XP/구형 그리드/리사이저는 버튼 다운 상태에서 
        연속 WM_MOUSEMOVE 이벤트를 받아야 정상적으로 리사이즈가 진행됩니다.
        시작→끝 한 번에 “점프”하면 앱은 중간 이동을 못 보고 마지막 위치만 받아, 
        리사이즈가 먹히지 않거나 덜 반응적일 수 있습니다.
        분할 이동(+짧은 sleep)은 이벤트 손실/합치기(coalescing) 완화, 
        사람 손 움직임에 가까운 타이밍 제공 → 호환성↑
    """
    x0, y0 = src[0], src[1]   # assume ints
    x1, y1 = dst[0], dst[1]       # assume ints
    if steps < 1:
        steps = 1
    if duration < 0:
        duration = 0.0
    per = duration / float(steps) if duration else 0.0

    win32api.SetCursorPos((x0, y0))
    time.sleep(0.01)  # why: 일부 구형 앱에서 다운 전 안정화

    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

    dx, dy = (x1 - x0), (y1 - y0)
    for i in range(1, steps + 1):
        t = float(i) / float(steps)
        xi = x0 + int(dx * t)
        yi = y0 + int(dy * t)
        win32api.SetCursorPos((xi, yi))
        if per:
            time.sleep(per)

    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.01)  # why: 업 이벤트 전달 안정화

'''-----------------
input text 
--------------------
'''
def backspace_once() -> None:
    send_keys("{BACKSPACE}")
    time.sleep(_SLEEP_TIME)
    
def type_text(text: str, clear: bool = False) -> None:
    if clear:
        send_keys("^a{BACKSPACE}")
    send_keys(text, with_spaces=True)
    # time.sleep(_SLEEP_TIME)

def set_text(hwnd: int, text: str, echo: bool = False) -> str|None:
    """Edit 컨트롤의 전체 텍스트를 지정."""
    win32gui.SendMessage(hwnd, win32con.WM_SETTEXT, 0, text)
    if echo:
        time.sleep(0.2)
        return get_text(hwnd)
    return None

def set_text_at_point(ax: int, ay: int, echo: bool = False) -> str|None: 
    hwnd = win32gui.WindowFromPoint( (int(ax), int(ay)) )
    if not hwnd:
        return ""
    return set_text(hwnd, echo)

def clear_text_via_messages_at_component(comp) -> bool:
    """
    스크린 좌표 기준 컴포넌트 중앙의 컨트롤 텍스트를 메시지로 삭제.
    True=성공적으로 비움, False=이미 비어있거나 실패.
    """
    cx, cy = comp.c # component_center_screen(comp)
    hwnd = win32gui.WindowFromPoint((int(cx), int(cy)))
    if not hwnd:
        return False

    # 1) WM_SETTEXT("")
    try:
        _wm_settext(hwnd, "")
        if _wm_gettextlen(hwnd) == 0:
            return True
    except Exception:
        pass

    # 2) EM_SETSEL(0,-1) + EM_REPLACESEL("")
    try:
        _em_setsel(hwnd, 0, -1)
        _em_replacesel(hwnd, "")
        if _wm_gettextlen(hwnd) == 0:
            return True
    except Exception:
        pass

    # 3) 키보드 폴백: 길이만큼 백스페이스
    try:
        length = _wm_gettextlen(hwnd)
        if length > 0:
            # 포커스는 이미 클릭 루틴으로 맞춰놓는 걸 전제
            send_keys("{BACKSPACE " + str(length) + "}")
            return _wm_gettextlen(hwnd) == 0
    except Exception:
        pass

    return _wm_gettextlen(hwnd) == 0

def type_text_overwrite(comp, text: str):
    """
    Ctrl+A 없이 '모두 선택 후 덮어쓰기' 동작을 메시지로 구현.
    """
    cx, cy = comp.c # component_center_screen(comp)
    hwnd = win32gui.WindowFromPoint((int(cx), int(cy)))
    if not hwnd:
        return
    try:
        _em_setsel(hwnd, 0, -1)
        _em_replacesel(hwnd, text)
        return
    except Exception:
        pass
    # 실패하면 WM_SETTEXT로 대체(커서/undo 무시)
    

'''-----------------
get component property
--------------------
'''
def _wm_gettextlen(hwnd: int) -> int:
    return win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)

def get_text(hwnd: int) -> str:
    """현재 Edit 컨트롤의 전체 텍스트를 반환."""
    length = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
    if length <= 0:
        return win32gui.GetWindowText(hwnd) or ""
    buf = ctypes.create_unicode_buffer(length + 1)
    win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, length + 1, ctypes.addressof(buf))
    return buf.value

def get_text_at_point(ax: int, ay: int) -> str:
    # Win32 text read (no UIA). screen coords 기준. 
    # 좌표에 실제로 위치한 “가장 깊은(innermost)” 자식 컨트롤의 HWND 를 반환
    hwnd = win32gui.WindowFromPoint((int(ax), int(ay)))
    if not hwnd:
        return ""
    return get_text(hwnd)

def get_text_in_component(comp) -> str:
    """컴포넌트의 스크린 중심 좌표에서 텍스트 읽기."""
    l, t, r, b = comp.rect()  # 이미 스크린 좌표
    cx, cy = (l + r) // 2, (t + b) // 2
    return get_text_at_point(cx, cy)



def _em_getsel(hwnd: int) -> tuple[int, int]:
    """현재 선택 영역의 (start, end) 인덱스를 반환."""
    start = ctypes.c_int()
    end = ctypes.c_int()
    win32gui.SendMessage(hwnd, win32con.EM_GETSEL,
                         ctypes.byref(start), ctypes.byref(end))
    return start.value, end.value

def _em_setsel(hwnd: int, start: int, end: int) -> None:
    """start~end 범위의 텍스트를 선택."""
    win32gui.SendMessage(hwnd, win32con.EM_SETSEL, start, end)

def _em_replacesel(hwnd: int, text: str, can_undo: bool = True) -> None:
    """현재 선택 영역의 텍스트를 text로 교체."""
    win32gui.SendMessage(hwnd, win32con.EM_REPLACESEL, can_undo, text)

def _em_select_all(hwnd: int) -> None:
    """전체 텍스트 선택."""
    _em_setsel(hwnd, 0, -1)

def _em_move_caret_to_end(hwnd: int) -> None:
    """커서를 텍스트 끝으로 이동."""
    length = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
    _em_setsel(hwnd, length, length)


if __name__ == "__main__": 
    import win32api
    import time

    # 📍 현재 마우스가 가리키는 컨트롤 찾기
    x, y = win32api.GetCursorPos()
    hwnd = win32gui.WindowFromPoint((x, y))

    print(f"HWND: 0x{hwnd:08X}")
    cls = win32gui.GetClassName(hwnd)
    print(f"Class: {cls}")

    if cls.lower() == "edit":
        print("✅ Edit 컨트롤 감지됨!")

        # 1. 현재 텍스트 읽기
        text_before = _wm_gettext(hwnd)
        print("현재 텍스트:", repr(text_before))

        # 2. 전체 선택
        _em_select_all(hwnd)
        time.sleep(0.5)

        # 3. 새 텍스트 쓰기
        _wm_settext(hwnd, "This text was inserted by Python!")
        time.sleep(0.5)

        # 4. 커서를 맨 끝으로 이동
        _em_move_caret_to_end(hwnd)

        # 5. 선택 영역 읽기
        sel = _em_getsel(hwnd)
        print("현재 선택 영역:", sel)

        # 6. 일부 영역 교체
        _em_setsel(hwnd, 5, 9)
        _em_replacesel(hwnd, "[REPLACED]")
        print("변경 완료!")

    else:
        print("⚠️ 현재 위치는 Edit 컨트롤이 아닙니다.")
