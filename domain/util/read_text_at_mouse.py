import win32api
import win32gui
import win32con
import time, ctypes

def get_window_info_from_mouse():
    # 1️⃣ 현재 마우스 포인터 위치 얻기
    x, y = win32api.GetCursorPos()

    # 2️⃣ 해당 좌표의 윈도우 핸들 얻기
    hwnd = win32gui.WindowFromPoint((x, y))

    if hwnd == 0:
        print("No window found under cursor.")
        return

    # 3️⃣ 윈도우 텍스트(라벨, 버튼 등)
    text = win32gui.GetWindowText(hwnd)
    print(f"Text: {text!r}")
    buf = ctypes.create_unicode_buffer(512)
    win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, 512, buf)
    print(f"Text: {buf.value!r}")

    # 4️⃣ 클래스명 (컨트롤 타입)
    cls_name = win32gui.GetClassName(hwnd)

    # 5️⃣ 부모 및 크기 등 부가정보
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect

    # 6️⃣ 출력
    print(f"Mouse position: ({x},{y})")
    print(f"Handle (hwnd): 0x{hwnd:08X}")
    print(f"Class name: {cls_name}")
    print(f"Rect: {rect}")
    print("-" * 50)

if __name__ == "__main__":

    
    print("Move your mouse to any control (window, textbox, button, etc.) ...")
    time.sleep(3)
    get_window_info_from_mouse()
