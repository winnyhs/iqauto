'''
File Name: detect_arrow.py

- Run with Python 3.7 on Windows 10 (64 or 32 bit)

- Required package
    $ pip install pywin32

- How to make a .exe? 
    $ pip install pyinstaller
    $ pyinstaller --onefile --noconsole detect_arrow.py 
    or 
    $ pyinstaller --onefile --noconsole --icon=myicon.ico --name detect_arrow_gui detect_arrow.py 
    # This build command creates dist/detect_arrow.exe
    # | Flag                          | Meaning                                    |
    # | ----------------------------- | ------------------------------------------ |
    # | `--onefile`                   | Packs everything into a single `.exe`      |
    # | `--noconsole`                 | Suppresses console window — GUI popup only |
    # | (optional) `--icon=arrow.ico` | Add your own icon                          |
    
'''

# -*- coding: utf-8 -*-
import win32gui, win32ui, win32con, win32api

def capture_region(hwnd, rect):
    """Capture rectangular region of a window. rect=(x, y, w, h)"""

    # ⬛️ rect 튜플을 분리 — (x, y)는 캡처 시작 좌표, (w, h)는 영역 크기
    x, y, w, h = rect

    # 1️⃣ 윈도우의 DC(Device Context) 핸들을 얻음
    # DC는 화면 그리기 작업을 위한 “캔버스” 같은 개념.
    hwndDC = win32gui.GetWindowDC(hwnd)

    # 2️⃣ Win32 DC 핸들로부터 pywin32의 MFC Device Context 객체 생성
    # 이 객체를 이용하면 BitBlt 같은 그래픽 복사를 쉽게 수행 가능.
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)

    # 3️⃣ 복사를 받을 메모리용 DC를 하나 더 생성 (메모리 DC)
    # 실제 윈도우 화면 대신 메모리 버퍼로 그릴 수 있게 함.
    saveDC = mfcDC.CreateCompatibleDC()

    # 4️⃣ 지정된 크기(w, h)에 맞는 비트맵(Bitmap) 객체를 새로 생성
    saveBitMap = win32ui.CreateBitmap()

    # 5️⃣ 기존 DC(mfcDC)와 호환되는 비트맵을 생성 (색상포맷 일치)
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

    # 6️⃣ 메모리 DC(saveDC)에 방금 만든 비트맵 객체를 선택(attach)
    # 이제 이 DC에 그리는 내용은 비트맵 메모리에 저장됨.
    saveDC.SelectObject(saveBitMap)

    # 7️⃣ BitBlt (Bit-block Transfer) 수행
    #   (0,0)부터 (w,h) 크기만큼 원본 DC(mfcDC)의 (x,y) 위치를 복사.
    #   즉, 윈도우의 특정 좌표 영역을 메모리 DC로 픽셀 단위 복사.
    saveDC.BitBlt((0, 0), (w, h), mfcDC, (x, y), win32con.SRCCOPY)

    # 8️⃣ 비트맵의 메타정보 (폭, 높이, 비트수 등) 가져오기
    bmpinfo = saveBitMap.GetInfo()

    # 9️⃣ 실제 비트맵의 픽셀 데이터를 raw bytes 형태로 읽기
    # True → 비트 순서를 그대로 가져옴 (하단→상단, BGR 순서)
    bmpbytes = saveBitMap.GetBitmapBits(True)

    # 1️⃣0️⃣ GDI 리소스 해제 (중요)
    # 비트맵, DC는 Windows GDI 객체이므로 반드시 Release 필요.
    win32gui.DeleteObject(saveBitMap.GetHandle())  # 비트맵 객체 해제
    saveDC.DeleteDC()                              # 메모리 DC 해제
    mfcDC.DeleteDC()                               # 원본 DC 해제
    win32gui.ReleaseDC(hwnd, hwndDC)               # 윈도우 DC 반납

    # 1️⃣1️⃣ 결과 반환 (너비, 높이, 비트맵 raw 데이터)
    return w, h, bmpbytes


def contains_right_arrow(w, h, bmpbytes, threshold=60):
    """Check if a right-pointing black triangle likely exists in image data."""
    bits = bytearray(bmpbytes)
    stride = ((w * 3 + 3) // 4) * 4
    black = []

    for y in range(h):
        row = bits[y * stride : y * stride + w * 3]
        for x in range(w):
            b, g, r = row[x*3:x*3+3]
            if r < threshold and g < threshold and b < threshold:
                black.append((x, h - y - 1))

    if len(black) < 50:
        return False

    xs = [p[0] for p in black]
    ys = [p[1] for p in black]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    cx = sum(xs) / float(len(xs))
    w_box = x_max - x_min
    h_box = y_max - y_min
    aspect = float(w_box) / float(h_box + 1)

    left_half = [p for p in black if p[0] < (x_min + w_box * 0.5)]
    right_half = [p for p in black if p[0] >= (x_min + w_box * 0.5)]

    # ▶ shape heuristic
    if aspect > 1.1 and cx > (x_min + w_box * 0.55) and len(left_half)*2 < len(right_half):
        return True
    return False


def find_arrow_region_in_medical(regions):
    """Find which region (index) in 'Medical' window has a right arrow."""
    hwnd = win32gui.FindWindow(None, "Medical")
    if not hwnd:
        win32api.MessageBox(0, "Window 'Medical' not found", "Error", win32con.MB_ICONERROR)
        return None

    for i, rect in enumerate(regions):
        w, h, bmpbytes = capture_region(hwnd, rect)
        if contains_right_arrow(w, h, bmpbytes):
            win32api.MessageBox(0, "▶ Arrow found in region #{}".format(i+1),
                                "Result", win32con.MB_ICONASTERISK)
            return i
    win32api.MessageBox(0, "No right arrow found in any region",
                        "Result", win32con.MB_ICONEXCLAMATION)
    return None


# ==== Example usage ====
if __name__ == "__main__":
    # List of 15 regions (x, y, w, h) relative to the Medical window
    regions = [
        (10, 50, 80, 40), (100, 50, 80, 40), (190, 50, 80, 40),
        (10, 100, 80, 40), (100, 100, 80, 40), (190, 100, 80, 40),
        (10, 150, 80, 40), (100, 150, 80, 40), (190, 150, 80, 40),
        (10, 200, 80, 40), (100, 200, 80, 40), (190, 200, 80, 40),
        (10, 250, 80, 40), (100, 250, 80, 40), (190, 250, 80, 40),
    ]

    found_index = find_arrow_region_in_medical(regions)
    print("Arrow region index:", found_index)
