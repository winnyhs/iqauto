import os, shutil, json

from common.singleton import SingletonMeta
from common.json import save_json
from common.log import logger
from db.config import GlobalConfig

'''In case of running on E: Drive
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
'''

class __Config(metaclass = SingletonMeta): 
    def __init__(self, global_config): 
        self.gcfg = global_config
        self.db = global_config.db
        self.sys_drv = global_config.sys_drv
        self.ext_drv = global_config.ext_drv
        self.run_drv = global_config.worker  # workder_drv
        
        # self.clean_temp()
        logger.info("------------------------------------------------")
        logger.info("config: ")
        logger.info("    sys_drv: %s", self.gcfg.sys_drv_top)
        logger.info("    run_drv: %s", self.gcfg.worker_top)
        logger.info("    ext_drv: %s", self.gcfg.ext_drv_top)
        logger.info("            sys mdb_path: %s", self.sys_drv["mdb_path"])
        logger.info("            ext mdb_path: %s", self.ext_drv["mdb_path"])
        logger.info("------------------------------------------------")
    
    def save_config(self, path): 
        config = {
            "must_have_file" : self.must_have_file, 
            "good_to_have_file" : self.good_to_have_file, 
            "virus_file" : self.virus_file, 

            "sys_drv" : self.sys_drv, 
            "run_drv" : self.run_drv, 
            "ext_drv" : self.ext_drv
        }
        path = os.path.abspath(path)
        save_json(config, path)
        logger.info(json.dumps(config, indent=2, sort_keys=True))
        return config

Config = __Config(GlobalConfig)

if __name__ == "__main__": 
    # To export config as file
    # Config.save_config(cfg.run_drv["config_path"])

    Config.gcfg.reconfigure(run_drv_name = "E:", ext_drv_name = "D")
    print("--- sys_drv: %s" % json.dumps(Config.sys_drv, indent=4, sort_keys=True))
    print("--- ext_drv: %s" % json.dumps(Config.ext_drv, indent=4, sort_keys=True))
    print("--- run_drv: %s" % json.dumps(Config.run_drv, indent=4, sort_keys=True))