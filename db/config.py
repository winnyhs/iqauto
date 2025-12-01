import os, shutil, json
from common.singleton import SingletonMeta
from common.log import logger
from common.sys import choose_external_drive_name, force_delete, show_dir

'''
#--------------------------------------------------------
# Global config hold only 
# - directory structures 
# - file pathes for data feeding
# Directories and files are cleaned up and prepared 
#
In case of running on E: Drive
E:\medical\
    +-- auto_analyzer
    |   +-- config
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
    +-- config
    |   +-- config.py
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
class __GlobalConfig(metaclass = SingletonMeta): 
  def __init__(self, app_top = "C:\\analyzer", ext_top = None): # "E:\\analyzer"):
    self.file = {
        "mdb_file": "MEDICAL.mdb", 
        "output_files": ["must-have.json", "good_to_have.json", "virus.json"]
    }

    self.app_top = app_top

    self.db_top = os.path.join(self.app_top, "db")
    self.db = {
      "password": "I1D2E3A4", 
      "data_table_path": os.path.join(self.db_top, "data_table.json"), 
      "program_ddl_path": os.path.join(self.db_top, "program_ddl.json")
    }
    
    self.backend_top = os.path.join(self.app_top, "backend")
    self.backend = {}
    
    self.worker_top = os.path.join(self.app_top, "worker")
    self.worker_drv = {
      "client_dir" : os.path.join(self.worker_top, "client"),
      "json_dir"   : os.path.join(self.worker_top, "temp", "json"),
      "program_path" : os.path.join(self.worker_top, "temp", "json", "__analyzer_program.json"),
      "progress_path": os.path.join(self.worker_top, "temp", "json", "__analyzer_progress.jsonl")
    }
    
    self.sys_drv_top = self.find_sys_dir_top()
    self.sys_drv = {
      "mdb_path" : os.path.join(self.sys_drv_top, self.file["mdb_file"])
    }

    if ext_top is None: 
      name = choose_external_drive_name()
      self.ext_drv_top = name[0] + ":\\analyzer"
    else: 
      self.ext_drv_top = ext_top # "E:\\medical"
    self.ext_drv = {
      "mdb_dir": os.path.join(self.ext_drv_top, "temp"), 
      "mdb_path": os.path.join(self.ext_drv_top, "temp", self.file["mdb_file"])
    }

    self.clean_temp()


  def find_sys_dir_top(self, sys_top = None): 
    # 1. Configure the internal directory, if not provided under self.sysdrv["top_dir"]
    cand = [
      "C:\\Program Files\\medical", 
      "C:\\Program Files (x86)\\medical",
      "C:\\medical"
    ]
    mdb_file = "MEDICAL.mdb"
    if sys_top == None:
      for p in cand:
        if os.path.isdir(p) and os.path.isfile(os.path.join(p, mdb_file)): 
          return p
      logger.error("ERROR: No medical program is installed")
      return None

    sys_top = os.path.abspath(sys_top)
    if not os.path.isdir(sys_top) or \
      not os.path.isfile(os.path.join(sys_top, mdb_file)):
      logger.error("ERROR: No medical program is installed under %s", sys_top)
      return None
    else: 
      return sys_top


  def reconfigure(self, worker_drv_name = None, ext_drv_name = None): 
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

  def clean_temp(self):
    json_dir = self.worker_drv["json_dir"]
    mdb_dir  = self.ext_drv["mdb_dir"]

    # Delete all under json and mdb folder 
    for d in (json_dir, mdb_dir): 
      try: 
        force_delete(d) # shutil.rmtree(d)
        logger.info("%s is deleted", d)
      except Exception as e:
        logger.exception("ERROR: %s: Failed in deleting %s", e, d)

    for d in (json_dir, mdb_dir):
      try:
        os.makedirs(d)
        logger.info("%s is created", d)
      except Exception as e:
        logger.exception("ERROR: %s: Failed in creating folder %s", e, d)

    for d in (json_dir, mdb_dir): 
      show_dir(d)


GlobalConfig = __GlobalConfig()

if __name__ == "__main__": 

  GlobalConfig.clean_temp()
  # subprocess.call(r'cp .\output\must-have.json .\temp\json\must-have.json', shell=True)
  # subprocess.call(r'cp C:\Program Files (x86)\medical\MEDICAL.mdb E:\medical\temp\mdb\MEDICAL.mdb', shell=True)

  GlobalConfig.reconfigure("D", "F")