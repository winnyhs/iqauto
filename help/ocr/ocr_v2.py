# -*- coding: utf-8 -*-
# Final OCR Engine (XP + Python 3.4 + Tesseract 3.x + Pillow 4.x)

from __future__ import print_function
import os, re, subprocess
from PIL import Image, ImageOps, ImageFilter
import win32gui, win32ui, win32con


class OcrEngine(object):

    _percent_re = re.compile(r"(\d{1,3})\s*%?")

    def __init__(self, config):
        self.tess_exe = config["Tesseract"]["exe"]
        self.tess_lang = config["Tesseract"].get("lang", "eng")
        self.tess_psm  = config["Tesseract"].get("psm", "13")
        self.fname_prefix = config["Tesseract"].get("fname_prefix", "ocr_")

        self.temp = os.path.abspath("./temp")
        if not os.path.isdir(self.temp):
            os.makedirs(self.temp)

    #  Blue Background Detector
    def is_strong_blue_background(self, img):
        r, g, b = img.split()

        total = float(img.width * img.height)
        avg_r = sum(r.getdata()) / total
        avg_g = sum(g.getdata()) / total
        avg_b = sum(b.getdata()) / total

        # Blue dominant
        return (avg_b > avg_r + avg_g)

    # Screen capture
    def capture_region_to_bmp(self, lt, rb, out_path):
        x1, y1 = lt
        x2, y2 = rb
        w, h = x2 - x1, y2 - y1
        if w <= 0 or h <= 0:
            raise ValueError("Invalid region")

        out_path = os.path.abspath(out_path)
        out_dir = os.path.dirname(out_path)
        if out_dir and not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        hwnd = win32gui.GetDesktopWindow()
        hdc  = win32gui.GetWindowDC(hwnd)

        src_dc = win32ui.CreateDCFromHandle(hdc)
        mem_dc = src_dc.CreateCompatibleDC()

        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(src_dc, w, h)
        mem_dc.SelectObject(bmp)

        mem_dc.BitBlt((0, 0), (w, h), src_dc, (x1, y1), win32con.SRCCOPY)
        bmp.SaveBitmapFile(mem_dc, out_path)

        win32gui.DeleteObject(bmp.GetHandle())
        mem_dc.DeleteDC()
        src_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hdc)

        return out_path

    # Preprocess for OCR (blue + red)
    def preprocess(self, img, dst_path):
        """ Blue background: R-channel threshold (x5) """
        if self.is_strong_blue_background(img):
            # -------- Blue background / Red text --------
            r, g, b = img.split()
            scale = 5
            r_big = r.resize((r.width * scale, r.height * scale), Image.NEAREST)
            bw = r_big.point(lambda x: 255 if x > 80 else 0, "1")
            bw.save(dst_path)
            return dst_path
        else: 
            print("Not Blue background: No preprocessing")
            return None

    # Run Tesseract
    def run_tesseract(self, bmp_path):
        out_base = os.path.join(self.temp, self.fname_prefix + "out")
        out_txt = out_base + ".txt"

        args = [
            self.tess_exe,
            bmp_path,
            out_base,
            "-l", self.tess_lang,
            "--psm", self.tess_psm
        ]

        subprocess.call(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(out_txt):
            return ""

        # XP + Python 3.4 → UTF-8 읽기 필수
        with open(out_txt, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    # Parse percentage from OCR result
    def parse_percent(self, raw):
        if not raw:
            return None, False

        s = raw.strip().replace("\n", " ").replace("\r", " ")
        m = self._percent_re.search(s)
        if not m:
            return None, ('%' in s)

        v = int(m.group(1))
        v = max(0, min(100, v))
        return v, ('%' in s)

    # High-level read wrapper
    def read_percent(self, lt, rb, fname=None, verbose=True):

        # 1) Capture
        if fname:
            fpname = fname
        else:
            fpname = os.path.join(self.temp, self.fname_prefix + "raw.bmp")

        self.capture_region_to_bmp(lt, rb, fpname)

        # 2) Preprocess
        img = Image.open(fpname)
        clean = fpname.replace(".bmp", "_clean.bmp")
        self.preprocess(img, clean)

        # 3) OCR
        raw = self.run_tesseract(clean)
        val, pct = self.parse_percent(raw)
        print("[OCR] txt=%r → val=%s pct=%s" % (raw, val, pct))

        return {
            "value": val,
            "text": raw,
            "had_percent": pct,
            "fpname": (fpname if fname else None)
        }


#────────────────────────────────────────────────────────────
# Main Test
#────────────────────────────────────────────────────────────
if __name__ == "__main__":

    config = {
        "Tesseract": {
            "exe": r"E:\App\Bin\Tesseract-OCR\tesseract.exe",
            "lang": "eng",
            "psm":  "13",
            "fname_prefix": "ocr_"
        }
    }

    engine = OcrEngine(config)

    # MATCH %
    res_match = engine.read_percent((419,406), (447,420), fname="out_match.bmp")
    print(res_match)

    # PROGRESS %
    res_prog = engine.read_percent((274,407), (308,422), fname="out_prog.bmp")
    print(res_prog)
