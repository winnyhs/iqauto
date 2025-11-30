
# -*- coding: utf-8 -*-
# XP compatible OCR Engine
# Python 3.4 + Pillow 4.0 + pywin32 + Tesseract 3.x

from __future__ import print_function
import os, re, subprocess

from PIL import Image, ImageOps, ImageFilter
import win32gui, win32ui, win32con


class OcrEngine(object):

    _percent_re = re.compile(r"(\d{1,3})\s*%?")

    # ------------------------------------------------------
    # Constructor
    # ------------------------------------------------------
    def __init__(self, config):
        self.tess_exe = config["Tesseract"]["exe"]
        self.tess_lang = config["Tesseract"].get("lang", "eng")
        self.tess_psm  = config["Tesseract"].get("psm", "13")
        self.fname_prefix = config["Tesseract"].get("fname_prefix", "ocr_")

        # temp folder
        self.temp = os.path.abspath("./temp")
        if not os.path.isdir(self.temp):
            os.makedirs(self.temp)


    # ------------------------------------------------------
    # Detect strong blue background
    # ------------------------------------------------------
    def is_strong_blue_background(self, img):
        r, g, b = img.split()

        total = float(img.size[0] * img.size[1])
        avg_r = sum(r.getdata()) / total
        avg_g = sum(g.getdata()) / total
        avg_b = sum(b.getdata()) / total

        # blue background: B >> R+G
        return avg_b > avg_r + avg_g


    # ------------------------------------------------------
    # Morphology for stabilizing digit shapes
    # ------------------------------------------------------
    def dilate(self, bw):
        """Dilation (expand black pixels)."""
        w, h = bw.size
        src = bw.load()
        out = Image.new("1", (w, h), 255)
        dst = out.load()

        for y in range(1, h-1):
            for x in range(1, w-1):
                if any(src[x+dx, y+dy] == 0 for dx in (-1,0,1) for dy in (-1,0,1)):
                    dst[x, y] = 0
        return out

    def erode(self, bw):
        """Erosion (shrink black pixels)."""
        w, h = bw.size
        src = bw.load()
        out = Image.new("1", (w, h), 255)
        dst = out.load()

        for y in range(1, h-1):
            for x in range(1, w-1):
                if all(src[x+dx, y+dy] == 0 for dx in (-1,0,1) for dy in (-1,0,1)):
                    dst[x, y] = 0
        return out

    # Screen capture using win32 BitBlt
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

    # Full preprocessing pipeline (XP safe)
    def preprocess(self, img, dst_path):

        # BLUE BACKGROUND → use R channel directly
        if self.is_strong_blue_background(img):
            r, _, _ = img.split()

            scale = 5
            r_big = r.resize(
                (r.width * scale, r.height * scale),
                Image.NEAREST
            )

            # threshold for red text
            bw = r_big.point(lambda x: 255 if x > 80 else 0, "1")

            # morphology to restore digit shapes
            bw = self.dilate(bw)
            bw = self.erode(bw)

            bw.save(dst_path)
            return dst_path

        # PURPLE / LIGHT PURPLE CASE (24%, 52%, 77% 문제 해결)
        scale = 6
        big = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)

        gray = ImageOps.grayscale(big)
        gray = gray.filter(ImageFilter.BLUR)

        # dual threshold approach
        bw1 = gray.point(lambda x: 0 if x < 150 else 255, "1")
        bw2 = gray.point(lambda x: 0 if x < 120 else 255, "1")

        # OR merge
        merge = Image.new("1", bw1.size)
        p1 = bw1.load()
        p2 = bw2.load()
        p3 = merge.load()

        for y in range(merge.size[1]):
            for x in range(merge.size[0]):
                p3[x,y] = 0 if (p1[x,y] == 0 or p2[x,y] == 0) else 255

        # morphology
        merge = self.dilate(merge)
        merge = self.erode(merge)

        merge.save(dst_path)
        return dst_path

    # Tesseract runner
    def run_tesseract(self, bmp_path):
        out_base = os.path.join(self.temp, self.fname_prefix + "out")
        out_txt  = out_base + ".txt"

        args = [
            self.tess_exe,
            bmp_path,
            out_base,
            "-l", self.tess_lang,
            "--psm", self.tess_psm,
        ]

        subprocess.call(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(out_txt):
            return ""

        with open(out_txt, "r") as f:
            txt = f.read()

        return txt

    # Parse extracted text
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

    # High-level API
    def read_percent(self, lt, rb, fname=None, verbose=True):
        # 1) capture
        if fname:
            fp = fname
        else:
            fp = os.path.join(self.temp, self.fname_prefix + "raw.bmp")

        self.capture_region_to_bmp(lt, rb, fp)

        # 2) preprocess
        img = Image.open(fp)
        clean = fp.replace(".bmp", "_clean.bmp")
        self.preprocess(img, clean)

        # 3) OCR
        raw = self.run_tesseract(clean)
        val, pct = self.parse_percent(raw)

        if verbose:
            print("[OCR] txt=%r -> val=%s pct=%s" % (raw, val, pct))

        return {
            "value": val,
            "text": raw,
            "had_percent": pct,
            "fpname": fp if fname else None,
        }


if __name__ == "__main__":
    config = {
        "Tesseract": {
            "exe": r"E:\App\Bin\Tesseract-OCR\tesseract.exe",
            "lang": "eng",
            "psm": "7",        # 7: single line, 13: raw line
            "fname_prefix": "ocr_",
        },
    }
    engine = OcrEngine(config)

    # match 영역 (보라/연보라 배경)
    res_match = engine.read_percent((419, 406), (447, 420),
                                    fname="out_match.bmp", verbose=True)
    print(res_match)

    # progress 영역 (진한 파랑 배경, 100%)
    res_prog = engine.read_percent((274, 407), (308, 422),
                                   fname="out_prog.bmp", verbose=True)
    print(res_prog)

    # selected 영역 (보라/연보라 배경)
    # r --> (r+1) : +16
    # (11, 51 + 16*r), (29, 65 + 16*r)
    for r in range(16): 
        res_prog = engine.read_percent((11, 51 + 16*r), (29, 65 + 16*r),
                                        fname="out_select"+str(r) +".bmp", verbose=True)
    print(res_prog)