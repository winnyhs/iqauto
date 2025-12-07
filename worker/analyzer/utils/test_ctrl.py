import os, shutil, datetime
from typing import Dict

from common.singleton import SingletonMeta
from common.log import logger


class __TestCtrl(metaclass=SingletonMeta): 
    def post_init(self, client: Dict, config) -> None: 
        self.client = client
        self.config = config # PathConfig.worker_drv
        print("--- TestCtrl::config = %s" % self.config)
           
        self.id = 0
        self.type = None
        self.case = None
        self.rid = 0

        self.match_err_cnt = 0     # how many times 부합율 is ocred
        self.completed_err_cnt = 0 # how many times complete percent is ocred
        self.arrow_err_cnt = 0     # how many tiems the arrow in Analysis grid is ocred

    def start_1test(self, type: str, case: str) -> None: 
        # self.id += 1
        self.type = type
        self.case = case
        self.rid = 0
        logger.info(f"=== Start a new test case: tid={self.id}: {self.type}, {self.case}")

    def setup_next_run(self) -> None: 
        self.id += 1
        self.rid += 1
        logger.info(f"--- Start a new test run: tid={self.id}, rid={self.rid}: ({self.type}, {self.case})")


    def make_fname(self, prefix: str, test_id: int = None,
                   run_id: int = None, case: str = None) -> str:
        # prefix can be progress, match, arrow, or agrid
        test_id = test_id if test_id else self.id
        run_id  = run_id  if run_id  else self.rid
        case    = case    if case    else self.case
        return f"{prefix}_tid{test_id}_rid{run_id}_{case}.bmp"

    def make_temp_fname(self, prefix: str, test_id: int = None, 
                        run_id: int = None, case: str = None) -> str:
        return os.path.join(self.config['temp_dir'], 
                            self.make_fname(prefix, test_id, run_id, case))
    
    def make_image_fname(self, prefix: str, test_id: int = None, 
                         run_id: int = None, case: str = None) -> str:
        return os.path.join(self.config['image_dir'], 
                            self.make_fname(prefix, test_id, run_id, case))

    def make_progress_fname(self, tid = None):
        tid = tid if tid else self.id
        return (os.path.join(self.config['progress_dir'], 'tmp.json'), 
                os.path.join(self.config['progress_dir'], str(tid) + '.json'))
        
    def make_test_data_html_fname(self, severity: str) -> str:
        return os.path.join(self.config['test_data_html_dir'], f"{severity}.html")
    
    def make_test_data_json_fname(self, severity: str) -> str:
        return os.path.join(self.config['test_data_json_dir'], f"{severity}.json")

    # Move the given file under image diectory
    def keep_temp_image(self, prefix: str) -> None:
        # if self.config["keep_all_images"] != True: 
        cur = self.make_temp_fname(prefix)
        new = self.make_image_fname(prefix)
        try: 
            shutil.move(cur, new)
            return new
        except Exception as e:
            logger.exception(f"{e}: {cur} --> {new}")
            return None
    
TestCtrl = __TestCtrl()
