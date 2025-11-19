# -*- coding: utf-8 -*-
# Template Matching OCR (XP + Python 3.4 + Pillow 4.0)
# Author: ChatGPT Final Version

from __future__ import print_function
import os, re, subprocess
from PIL import Image, ImageChops, ImageOps
import win32gui, win32ui, win32con



class TemplateOCR(object):

    def __init__(self, template_dir="templates"):
        self.digit_template_dir = os.path.join(template_dir, "digit")
        self.digit_templates = {}  # {"0": Image, "1": Image, ...}

        # Load digit_templates
        for fname in os.listdir(self.digit_template_dir):
            if fname.lower().endswith(".bmp"):
                key = os.path.splitext(fname)[0]  # "0","1","2","+"
                path = os.path.join(self.digit_template_dir, fname)
                self.digit_templates[key] = Image.open(path)
        print("[TemplateOCR] Loaded digit templates:", self.digit_templates.keys())

        self.rarrow_template_dir = os.path.join(template_dir, "right_arrow")
        self.rarrow_templates = {}
        for fname in os.listdir(self.rarrow_template_dir):
            if fname.lower().endswith(".bmp"): 
                key = os.path.splitext(fname)[0]
                path = os.path.join(self.rarrow_template_dir, fname)
                self.rarrow_templates[key] = Image.open(path)
        print("[TemplateOCR] Loaded right arrow templates:", self.rarrow_templates.keys())

    #  Capture region to BMP
    def capture_region(self, rect, out_path):
        x1, y1, x2, y2 = rect
        w, h = x2 - x1, y2 - y1

        hwnd = win32gui.GetDesktopWindow()
        hdc = win32gui.GetWindowDC(hwnd)
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

    #  Best template match with saved templates
    def match_one(self, img, type):
        """
        img: PIL image of one digit
        return best key ("0".."9")
        """

        img_gray = ImageOps.grayscale(img)

        best_key = None
        best_score = 10**18  # large number
        templates = self.digit_templates if type == 'digit' else self.rarrow_templates

        for key, tpl in templates.items():
            # Resize template to match image
            tpl_gray = ImageOps.grayscale(tpl)
            tpl_resized = tpl_gray.resize(img_gray.size, Image.BILINEAR)

            # Compute pixel difference
            diff = ImageChops.difference(img_gray, tpl_resized)
            score = sum(diff.getdata())  # lower = better match

            if score < best_score:
                best_score = score
                best_key = key

        return best_key

    #  Read 1 digit at position
    def read_digit(self, type, rect, fname=None):
        """
        Read a single digit from screen region.
        """
        if fname:
            path = fname
        else:
            path = "tmp.bmp"
        self.capture_region(rect, path)

        img = Image.open(path)
        d = self.match_one(img, type)

        print("[Digit] region=", rect, " → ", d)
        return d

    #  Read multiple digits
    def read_number(self, regions):
        """
        regions: list of [(l,t,r,b), (l,t,r,b), ...]
        """
        digits = []
        for rect in regions:
            d = self.read_digit("digit", rect)
            digits.append(d)

        # Join digits → int
        s = "".join([d for d in digits if d in "0123456789"])
        if s:
            return int(s)
        return None

    def read_arrow(self, rect): 
        d = self.read_digit("select", rect)
        return True if d == 'True' else False

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
    def capture_region_to_bmp(self, rect, out_path):
        x1, y1, x2, y2 = rect
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
            logger.error("Not Blue background: No preprocessing")
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
    def read_percent(self, rect, fname=None, verbose=True):

        # 1) Capture
        if fname:
            fpname = fname
        else:
            fpname = os.path.join(self.temp, self.fname_prefix + "raw.bmp")

        self.capture_region_to_bmp(rect, fpname)

        # 2) Preprocess
        img = Image.open(fpname)
        clean = fpname.replace(".bmp", "_clean.bmp")
        self.preprocess(img, clean)

        # 3) OCR
        raw = self.run_tesseract(clean) # return a OCR text
        val, pct = self.parse_percent(raw)
        print("[OCR] txt=%r → val=%s pct=%s" % (raw, val, pct))

        return {
            "value": val, # Final OCR text
            "text": raw,  # OCR text from tesseract
            "had_percent": pct, # whether percentage mark is in
            "fpname": (fpname if fname else None)
        }


# ----------------------------------------------------------
# Example usage
# ----------------------------------------------------------
if __name__ == "__main__":

    ocr = TemplateOCR(template_dir="templates")

    # Example: 3 positions
    # (좌표는 예시 → 네가 사용하는 화면에 맞게 지정)
    regions = [
        (418,406, 425,420),  # hundredth
        (424,406, 431,420),  # tenth
        (430,406, 437,420),  # oneth 
    ]
    value = ocr.read_number(regions)
    print("Final Number:", value)

    for r in range(16): 
        rect = (11, 51 + 16*r, 29, 66 + 16*r)
        is_arrow = ocr.read_arrow(rect)
        print(f"Right arrow: {'not' if is_arrow == False else ''} selected")
        # input(f"Enter to go to {r}th row.")

    config = {
        "Tesseract": {
            "exe": r"E:\App\Bin\Tesseract-OCR\tesseract.exe",
            "lang": "eng",
            "psm":  "13",
            "fname_prefix": "ocr_"
        }
    }
    engine = OcrEngine(config)

    # PROGRESS %
    res_prog = engine.read_percent((274,407, 308,422), fname="out_prog.bmp")
    print(res_prog)
    