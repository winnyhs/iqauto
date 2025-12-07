import os, shutil, json
from common.singleton import SingletonMeta
from common.log import logger
from common.sys import choose_external_drive_name, force_delete, show_dir

'''
#--------------------------------------------------------
# Global self hold only 
# - directory structures 
# - file pathes for data feeding
# Directories and files are cleaned up and prepared 
#
In case of running on E: Drive
E:\medical\
    +-- auto_analyzer
    |   +-- self
    |   +-- db
    |   +-- temp
    |       +-- json
    |       +-- mdb
    +-- client
    +-- install_package

C:\Program Files (32)\medical
    +-- medical.exe
    +-- MEDICAL.mdb
C:\Python_38
C:\Python_venv

In case of running on C: Drive
C:\Program Files (32)\auto_analyzer
    +-- mdb_copier.exe  # Run on the clients PC. 
    |                   # Copy(delete and then copy) its MEDICAL.mdb 
    |                   # under E:\medical\mdb
    +-- auto_analyzer.exe
    +-- self
    |   +-- self.py
    +-- db
    |   +-- data_table.json   # Exort of M_DATA table
    +-- temp
        +-- json
        |   +-- program.json       # program, final level analysis result from auto_analyzer
        |   +-- program_table.json # export of M_HISTORY table
        |   +-- must-have.json     # level-1 analysis result from auto_analyzer
        |   +-- good-to-have.json, virus.json, ...
        |
        +-- mdb
            +-- MEDICAL.mdb

E:\medical\
    +-- install_package
    |   +-- auto_analyzer_install.exe # To install python 3.8.10, python 3.7, pywin32, ...
    |   +-- auto_start_install.exe    # To install the automatic start of medical.exe
    |   +-- MDBPlus.exe               # To read a mdb file and to run SQL on it
    |
    +-- client
        +-- 김나라
        |   +-- 김나라_profile.json
        |   +-- 김나라_memo.txt
        |   +-- 2025-11-11T10-00
        |   |   +-- html
        |   |   |   +-- image
        |   |   +-- json
        |   |       +-- must-have.json, good-to-have.json, virus.json, ...
        |   +-- 2025-12-01T10-00
        |
        +-- 배나라 
#---------------------------------------------------------'''
class __PathConfig(metaclass = SingletonMeta): 
  def __init__(self, 
    app_top = "C:\\analyzer", 
    tesseract_bin_path = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe", 
    ext_top = None): # "E:\\analyzer"):

    self.file = {
        "mdb_file": "MEDICAL.mdb", 
        "output_files": ["must-have.json", "good_to_have.json", "virus.json"]
    }

    self.app_top = app_top

    # --- db
    self.db_top = os.path.join(self.app_top, "db")
    self.db = {
      "password": "I1D2E3A4", 
      "data_table_path": os.path.join(self.db_top, "data_table.json"), 
      "program_ddl_path": os.path.join(self.db_top, "program_ddl.json"), 
      
      "user_profile_path": os.path.join(self.db_top, "user_profile.json"), 
      "test_case_path": os.path.join(self.db_top, "test_case.json"), 
    }

    # --- ocr
    if os.path.isfile(tesseract_bin_path): 
      self.tesseract_bin_path = tesseract_bin_path
    elif os.path.isfile(r"C:\Program Files\Tesseract-OCR\tesseract.exe"): 
      self.tesseract_bin_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    elif os.path.isfile(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"): 
      self.tesseract_bin_path = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    else: 
      self.tesseract_bin_path = None
      raise FileNotFound(f"ERROR: Install Tesseract")
    
    # --- backend
    self.backend_top = os.path.join(self.app_top, "backend")
    self.backend = {}
    
    # --- service worker
    self.worker_top = os.path.join(self.app_top, "worker")
    self.worker_drv = {
      "client_dir" : os.path.join(self.worker_top, "client"),
      "test_data_dir": None,
      "test_data_html_dir": None, 
      "test_data_json_dir": None, 
      "image_dir": None, 

      "temp_dir"   : os.path.join(self.worker_top, "temp"), 
      "json_dir"   : os.path.join(self.worker_top, "temp", "json"),
      "progress_dir": os.path.join(self.worker_top, "temp", "progress"), 
      "program_path": os.path.join(self.worker_top, "temp", "json", "__analyzer_program.json"),
      "worker_param_path": os.path.join(self.worker_top, "temp", "json", "__worker_param.json")
    }
    
    # --- medical 
    self.sys_drv_top = None
    self.sys_drv = {}
    for p in [r"C:\Program Files (x86)\medical\medical.exe", 
              r"C:\Program Files\medical\medical.exe", 
              r"C:\medical\medical.exe"]: 
      if os.path.isfile(p): 
        self.sys_drv_top = os.path.dirname(p)
        self.sys_drv["mdb_path"] = os.path.join(self.sys_drv_top, self.file["mdb_file"]) 
        self.sys_drv["exe_path"] = os.path.join(self.sys_drv_top, "medical.exe") 
        break
    if self.sys_drv_top is None: 
      raise FileNotFoundError(f"medical.exe is not installed")

    for p in [r"C:\Program Files\FreqGen\freqgen.exe", 
              r"C:\Program Files (x86)\FreqGen\freqgen.exe"]: 
      if os.path.isfile(p): 
        self.sys_drv["worker_exe_path"] = p
        break
    if self.sys_drv.get("worker_exe_path", None) is None: 
      raise FileNotFoundError(f"freqgen.exe is not installed")

    # --- external drive like usb
    if ext_top is None: 
      name = choose_external_drive_name()
      self.ext_drv_top = name[0] + ":\\analyzer"
    else: 
      self.ext_drv_top = ext_top # "E:\\medical"
    self.ext_drv = {
      "mdb_dir": os.path.join(self.ext_drv_top, "temp"), 
      "mdb_path": os.path.join(self.ext_drv_top, "temp", self.file["mdb_file"])
    }

    # self.clean_and_provision(user_profile)


  def reconfigure_drv(self, worker_drv_name = None, ext_drv_name = None): 
    if worker_drv_name is not None: 
      if self.worker_top[0].upper() != worker_drv_name[0].upper(): 
        drive, tail = os.path.splitdrive(self.worker_top)
        self.worker_top = worker_drv_name[0] + ":" + tail
        for i in self.worker_drv: 
          drive, tail = os.path.splitdrive(self.worker_drv[i]) # drive="c:", tail="\\analyzer..."
          self.worker_drv[i] = worker_drv_name[0] + ":" + tail
        logger.info(json.dumps(self.worker_drv, indent=4, sort_keys=True))

    if ext_drv_name is not None: 
      if self.ext_drv_top[0].upper() != ext_drv_name[0].upper():
        drive, tail = os.path.splitdrive(self.ext_drv_top)
        self.ext_drv_top = ext_drv_name[0] + ":" + tail
        for i in self.ext_drv: 
          drive, tail = os.path.splitdrive(self.ext_drv[i]) # drive="c:", tail="\\analyzer..."
          self.ext_drv[i] = ext_drv_name[0] + ":" + tail
        logger.info(json.dumps(self.ext_drv, indent=4, sort_keys=True))

  def cleanup_and_provision_folder(self, user_profile):

    # 1. Make worker\client\<client-name>\<test-date>\{html, json} and 
    #         worker\client\<client-name>\<test-date>\html\image
    test_data_top = os.path.join(self.worker_drv["client_dir"], user_profile["name"])
    os.makedirs(test_data_top, exist_ok=True)  # worker\client\kkk
    test_data_top = os.path.join(test_data_top, user_profile["test_time"])
    os.makedirs(test_data_top)
    self.test_data_top = test_data_top
    logger.info("%s is created as test data top", self.test_data_top)
    # Now, base directory is worker\client\kkk\2025-11-11T11-11

    self.worker_drv["test_data_json_dir"] = os.path.join(self.test_data_top, "json")
    self.worker_drv["test_data_html_dir"] = os.path.join(self.test_data_top, "html")
    self.worker_drv["image_dir"]          = os.path.join(self.test_data_top, "html", "image")
    os.makedirs(self.worker_drv["test_data_json_dir"])  # worker\client\kkk\2025-11-11T11-11\json
    os.makedirs(self.worker_drv["test_data_html_dir"])  # worker\client\kkk\2025-11-11T11-11\html
    os.makedirs(self.worker_drv["image_dir"]) #, exist_ok=True)  

    # 2. Clean up worker\temp\{json, progress}
    base = self.worker_drv["temp_dir"]
    force_delete(base)                          # delete worker\temp
    os.makedirs(base)                           # create worker\temp
    os.makedirs(os.path.join(base, "json"))     # worker\temp\json
    os.makedirs(os.path.join(base, "progress")) # worker\temp\json
    logger.info("%s is created", base)

    # 3. Clean up ext_drv
    mdb_dir  = self.ext_drv["mdb_dir"]
    try: 
      force_delete(mdb_dir) # shutil.rmtree(d)
      logger.info("%s is deleted", mdb_dir)
    except Exception as e:
      logger.exception("ERROR: %s: Failed in deleting %s", e, mdb_dir)

    try:
      os.makedirs(mdb_dir)
      logger.info("%s is created", mdb_dir)
    except Exception as e:
      logger.exception("ERROR: %s: Failed in creating folder %s", e, mdb_dir)

    # for d in (json_dir, mdb_dir): 
    #   show_dir(d)

  def post_init(self, user_profile): 
    test_data_top = os.path.join(self.worker_drv["client_dir"], 
                                user_profile["name"],
                                user_profile["test_time"])
    # worker\client\kkk\2025-11-11T11-11-11
    self.test_data_top = test_data_top
    self.worker_drv["test_data_json_dir"] = os.path.join(self.test_data_top, "json")
    self.worker_drv["test_data_html_dir"] = os.path.join(self.test_data_top, "html")
    self.worker_drv["image_dir"]          = os.path.join(self.test_data_top, "html", "image")

  def post_init_ext_drv(self): 
    # Clean up ext_drv
    mdb_dir  = self.ext_drv["mdb_dir"]
    try: 
      force_delete(mdb_dir) # shutil.rmtree(d)
      logger.info("%s is deleted", mdb_dir)
    except Exception as e:
      logger.exception("ERROR: %s: Failed in deleting %s", e, mdb_dir)

    try:
      os.makedirs(mdb_dir)
      logger.info("%s is created", mdb_dir)
    except Exception as e:
      logger.exception("ERROR: %s: Failed in creating folder %s", e, mdb_dir)

  def progress_path(self, tid): 
    return os.path.join(self.worker_drv["progress_dir"], str(tid) + '.json')

  def get(self, owner = None): 
    if owner.lower() == "worker": 
      worker = {"top": self.worker_top}
      worker.update(self.worker_drv)
      return worker
    return None


PathConfig = __PathConfig()



if __name__ == "__main__": 

  PathConfig.clean_temp()
  # subprocess.call(r'cp .\output\must-have.json .\temp\json\must-have.json', shell=True)
  # subprocess.call(r'cp C:\Program Files (x86)\medical\MEDICAL.mdb E:\medical\temp\mdb\MEDICAL.mdb', shell=True)

  PathConfig.reconfigure_drv("D", "F")