
# config = { 
#     "common": None, 
#     "ocr": {
#         "arrow_template_dir": r".\templates\arrow", 
#         "digit_template_dir": r".\templates\digit", 
#     },
#     "Tesseract": {
#         "exe" : r"E:\App\Bin\Tesseract-OCR\tesseract.exe", 
#         "lang": "eng", 
#         "psm" : "13",       # 7 for single line, 13 for small text
#         "fname_prefix": "ocr_",
#     },
# }

import os, shutil, json

from common.singleton import SingletonMeta
from common.json import save_json
from common.log import logger
from db.path_config import PathConfig


class __Config(metaclass = SingletonMeta): 
    def __init__(self, global_config): 
        self.path = global_config

        ocr_template_top = os.path.join(global_config.worker_top, 
                                        'analyzer', 'templates') 
        self.ocr = {
            "arrow_template_dir": os.path.join(ocr_template_top, r"arrow"), 
            "digit_template_dir": os.path.join(ocr_template_top, r"digit"),
            "temp_dir": global_config.worker_drv["temp_dir"]
        }
        self.tesseract = {
            "exe" : global_config.tesseract_bin_path, 
            "lang": "eng", 
            "psm" : "13",       # 7 for single line, 13 for small text
            "fname_prefix": "ocr_",
            "temp_dir": global_config.worker_drv["temp_dir"]
        }


Config = __Config(PathConfig)