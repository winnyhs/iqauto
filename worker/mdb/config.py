import os, shutil, json

from common.singleton import SingletonMeta
from common.json import save_json
from common.log import logger
from db.path_config import PathConfig


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

Config = __Config(PathConfig)

if __name__ == "__main__": 
    # To export config as file
    # Config.save_config(cfg.run_drv["config_path"])

    Config.gcfg.reconfigure(run_drv_name = "E:", ext_drv_name = "D")
    print("--- sys_drv: %s" % json.dumps(Config.sys_drv, indent=4, sort_keys=True))
    print("--- ext_drv: %s" % json.dumps(Config.ext_drv, indent=4, sort_keys=True))
    print("--- run_drv: %s" % json.dumps(Config.run_drv, indent=4, sort_keys=True))