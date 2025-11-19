import os, shutil, datetime
from typing import Dict

from lib.singleton_meta import SingletonMeta
from lib.log import logger

def get_timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%dT%H-%M")

class _TestCtrl(metaclass=SingletonMeta): 
    client: Dict = None
    config: Dict = None

    id: int = 0      # test id
    type: str = None # test type
    case: str = None # test case in the test type
    
    rid: int = 0 # test run id

    match_err_cnt: int = 0 # how many times 부합율 is ocred
    completed_err_cnt: int = 0 # how many times complete percent is ocred
    arrow_err_cnt: int = 0 # how many tiems the arrow in Analysis grid is ocred

    def init(self, client: Dict, config: Dict) -> None: 
        self.client = client
        self.config = config

        # top directory for this clien: ./output/<client_name>/yyyy-mm-dd.hh-mm
        self.output_top = os.path.abspath(config["output_top_dir"])
        if not os.path.isdir(self.output_top):
            os.makedirs(self.output_top)
        self.user_top = os.path.join(self.output_top, client["name"])
        if not os.path.isdir(self.user_top):
            os.makedirs(self.user_top)
        self.user_top = os.path.join(self.user_top, get_timestamp())
        if not os.path.isdir(self.user_top):
            os.makedirs(self.user_top)
        

        # ./output/<client>/<yyyy-mm-dd.hh-mm>/
        #                                  +-- html/
        #                                  |    +-- image
        #                                  +-- json
        # ./temp
        self.config["html_dir"] = os.path.join(self.user_top, config["html_dir"])
        if not os.path.isdir(self.config["html_dir"]):
            os.makedirs(self.config["html_dir"])

        self.config["image_dir"] = os.path.join(self.user_top, config["image_dir"])
        if not os.path.isdir(self.config["image_dir"]):
            os.makedirs(self.config["image_dir"])

        self.config["json_dir"] = os.path.join(self.user_top, config["json_dir"])
        if not os.path.isdir(self.config["json_dir"]):
            os.makedirs(self.config["json_dir"])

        if config["keep_all_images"] == True: 
            self.config["temp_dir"] = self.config["image_dir"]
        else: 
            self.config["temp_dir"] = os.path.abspath(config["temp_dir"])
            if not os.path.isdir(self.config["temp_dir"]):
                os.makedirs(self.config["temp_dir"])
        
        self.id = 0
        self.type = None
        self.case = None

        self.rid = 0

        self.match_err_cnt = 0
        self.completed_err_cnt = 0
        self.arrow_err_cnt = 0

        logger.info(f"Prepare the test for {client['name']}")
        logger.info(f"    output top: {self.output_top}")
        logger.info(f"    user   top: {self.user_top}")
        logger.info(f"    html  dir : {self.config['html_dir']}")
        logger.info(f"    image dir : {self.config['image_dir']}")
        logger.info(f"    temp  dir : {self.config['temp_dir']}")

    def start_1test(self, type: str, case: str) -> None: 
        self.id += 1
        self.type = type
        self.case = case

        self.rid = 0
        logger.info(f"=== Start a new test case: tid={self.id}: {self.type}, {self.case}")

    def start_1run(self) -> None: 
        self.rid += 1
        logger.info(f"--- Start a new test run: tid={self.id}, rid={self.rid}: ({self.type}, {self.case})")


    def make_fname(self, prefix: str, test_id: int = None,
                   run_id: int = None, case: str = None) -> str:
        # prefix can be progress, match, arrow, or agrid
        test_id = test_id if test_id is not None else self.id
        run_id  = run_id  if run_id  is not None else self.rid
        case    = case    if case    is not None else self.case
        return f"{prefix}_tid{test_id}_rid{run_id}_{case}.bmp"

    def make_temp_fname(self, prefix: str, test_id: int = None, 
                        run_id: int = None, case: str = None) -> str:
        return os.path.join(self.config['temp_dir'], 
                            self.make_fname(prefix, test_id, run_id, case))
    
    def make_image_fname(self, prefix: str, test_id: int = None, 
                         run_id: int = None, case: str = None) -> str:
        return os.path.join(self.config['image_dir'], 
                            self.make_fname(prefix, test_id, run_id, case))
    
    # Move the given file under image diectory
    def keep_temp_image(self, prefix: str) -> None:
        if self.config["keep_all_images"] != True: 
            cur = self.make_temp_fname(prefix)
            new = self.make_image_fname(prefix)
            try: 
                shutil.move(cur, new)
                return new
            except Exception as e:
                logger.exception(f"{e}: {cur} --> {new}")
                return None
    
    def make_html_fname(self, severity: str) -> str:
        return os.path.join(self.config['html_dir'], f"{severity}.html")
    def make_json_fname(self, severity: str) -> str:
        return os.path.join(self.config['json_dir'], f"{severity}.json")
    
TestCtrl = _TestCtrl()
