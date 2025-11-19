'''
- Work with python 3.4 on Windows XP
- required packages: 
    $ pip install pywin32==220
    $ pip install pyautogui==0.9.36
    $ pip install Pillow==3.0.0
    $ pip install py2exe==0.6.9
    
- run:
    $ python setup_detect_arrow_gui.py py2exe

'''

# -*- coding: utf-8 -*-
from __future__ import print_function
import win32gui, win32api, win32con
import pyautogui
from PIL import Image
import sys

def find_right_arrow_in_window(title, threshold=60):
    """Detect a black right-pointing triangle (arrow head) inside a window."""

    hwnd = win32gui.FindWindow(None, title)
    if hwnd == 0:
        raise OSError("Window '{}' not found".format(title))

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width, height = right - left, bottom - top
    print("Region:", left, top, width, height)

    # Capture window image
    img = pyautogui.screenshot(region=(left, top, width, height))
    pixels = img.load()

    # Collect black pixel coordinates
    black = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            if r < threshold and g < threshold and b < threshold:
                black.append((x, y))

    if len(black) < 40:
        return False

    # Compute bounding box and centroid
    xs = [p[0] for p in black]
    ys = [p[1] for p in black]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    cx = sum(xs) / float(len(xs))
    cy = sum(ys) / float(len(ys))

    w = x_max - x_min
    h = y_max - y_min
    aspect = float(w) / (h + 1)

    # Slice left/right halves
    left_half = [p for p in black if p[0] < (x_min + w * 0.5)]
    right_half = [p for p in black if p[0] >= (x_min + w * 0.5)]

    # Heuristic for ▶ shape:
    #  - wider than tall (aspect > 1)
    #  - centroid on right side
    #  - fewer black pixels on left than right
    if aspect > 1.1 and cx > (x_min + w * 0.55) and len(left_half) * 2 < len(right_half):
        return True
    else:
        return False


def show_message(title, text, icon=win32con.MB_ICONINFORMATION):
    win32api.MessageBox(0, text, title, icon)


if __name__ == "__main__":
    target_title = "Medical"   # change to your window name
    try:
        found = find_right_arrow_in_window(target_title)
        if found:
            show_message("Arrow Detection", "▶ Black right-arrowhead detected.", win32con.MB_ICONASTERISK)
        else:
            show_message("Arrow Detection", "No right-arrowhead found.", win32con.MB_ICONEXCLAMATION)
    except Exception as e:
        show_message("Error", str(e), win32con.MB_ICONERROR)
        sys.exit(1)
