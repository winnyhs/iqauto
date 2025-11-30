
def make_config(): 
    config = {
        "common": { 
            # .\output\<client_name>\{html, html\img}
            "output_top_dir": r"output", 
            "html_dir": r"html", 
            "json_dir": r"json", 
            "image_dir": r"html\image", 

            "temp_dir": r"temp",
        }, 
        "test": {
            "keep_all_images": True, 
            "cleanup_temp_files": False, 
        }, 
        "ocr": {
            "arrow_template_dir": r".\templates\arrow", 
            "digit_template_dir": r".\templates\digit", 
        },
        "Tesseract": {
            "exe" : r"E:\App\Bin\Tesseract-OCR\tesseract.exe", 
            "lang": "eng", 
            "psm" : "13",       # 7 for single line, 13 for small text
            "fname_prefix": "ocr_",
        },
    }
    
    return config


config = make_config()