import time, re, os, shutil
from typing import List, Dict, Tuple, Any, Union

from config.config import config
from config.uimap import UIMap, Component, Point, AnalysisGridMap, Rect
from config.diag  import DiagTarget, PrescriptionType, VirusPolicy, Policy

from common.singleton import SingletonMeta
from common.log       import logger
from utils.analysis_result import AnalysisResult
from utils.input_ops import (
    drag_left, click_stable_at, 
    get_text_at_point, set_text_at_point
)
from utils.ocr import TemplateOCR, OcrEngine
from utils.test_ctrl import TestCtrl

test_config = {**config["common"], **config["test"]}
tess_config = {**config["common"], **config["Tesseract"]}

class AnalysisGridCtrl(metaclass = SingletonMeta): 
    def __init__(self, spec: AnalysisGridMap): 
        self.gmap = spec  # Grid Map
        self.ocr_select = TemplateOCR()
        self.test_ctrl = TestCtrl
    
    def find_selected_row(self) -> int: 
        for row in range(self.gmap.row_cnt):
            is_selected = self.ocr_select.read_arrow(self.gmap.select_col.cell_rect(row), 
                                        self.test_ctrl.make_temp_fname(f"arrow{row}"))
            if is_selected == True: 
                return row
        # for debugging
        logger.error(f"Error: check arrow[0,15]_tid{self.test_ctrl.id}_rid{self.test_ctrl.rid}_*.bmp files")
        for row in range(self.gmap.row_cnt): 
            self.test_ctrl.keep_temp_image(f"arrow{row}")
        return None
    
    def read_cell_text(self, p: Point, wait: float = 0.1) -> str:
        click_stable_at(p[0], p[1])
        return get_text_at_point(p[0], p[1])
    
    def read_row(self, row: int) -> AnalysisResult: 
        result = AnalysisResult()
        result.code   = self.read_cell_text(self.gmap.code_col.cell_center(row))  # "A0899020"
        result.cat    = self.read_cell_text(self.gmap.cat_col.cell_center(row))
        result.subcat = self.read_cell_text(self.gmap.subcat_col.cell_center(row))
        result.part   = self.read_cell_text(self.gmap.part_col.cell_center(row)) 
        result.prescription = self.read_cell_text(self.gmap.prescription_col.cell_center(row))
        result.description  = self.read_cell_text(self.gmap.description_col.cell_center(row))
        return result

    def resize_colums(self) -> bool:
        duration = 0.2
        steps = 30
        ordered = self.gmap.title_row.as_dict()  # keep the order declared in the class
        for name, spec in ordered.items():
            orect = getattr(spec, "orect", None)
            rect = getattr(spec, "rect", None)
            x0, x1 = orect[2], rect[2]
            if x0 == x1:
                continue

            x = (orect[0] + orect[2])//2
            y = (orect[1] + orect[3])//2  # 드래그 수직 위치: 타이틀 셀 중앙 y
            click_stable_at(x, y)         # for visible debugging
            # logger.debug(f"[DRAG] {name} ({(x0, y)})-> ({(x1, y)}) for {duration} in {steps} steps")
            time.sleep(0.5)
            
            try:
                drag_left((x0, y), (x1, y), duration=duration, steps=steps)
            except Exception as e: 
                logger.exception(f"{type(e).__name__}: {e}: title={spec}")
                return False
            time.sleep(0.5)
        return True
    
    def read_selected_row(self, tid: Tuple): 
        row = self.find_selected_row()
        if row != None: 
            result = self.read_row(row)
            return result

        logger.error(f"Failed in finding the selected row: "
                     f"{self.test_ctrl.id}.{self.test_ctrl.rid} {self.test_ctrl.case}")
        self.select_fail_cnt += 1 
        l, t = self.gmap.lt
        rect = (l, t, l + self.gmap.size[0], t + self.gmap.size[1]) # (9,31, 437,306))
        fname = self.test_ctrl.make_image_fname("agrid")
        self.ocr_select.capture_region(rect, fname)
        return fname



class AnalysisWinCtrl(metaclass=SingletonMeta):
    def __init__(self, win): 
        self.wmap = UIMap["analysis"]  # analysis window map
        self.win = None # main window WindowSpecification 
                        # self.win.wrapper_object() can be  DialogWrapper, WindowWrapper, ButtonWrapper, EditWrapper, 등
        
        self.grid_ctrl = AnalysisGridCtrl(self.wmap.grid)
        self.prescription = {key: [] for key in [
            "must-have", "good-to-have", "good-to-record", "virus", "check"]} # List[AnalysisResult]
        self.wmap.exec_button.callback = self.read_match_percent
        self.iteration: int = 10
        self.show_prescription: bool = False
        self.fe = None  # TODO
        self.ocr_progress = OcrEngine(tess_config)
        self.ocr_match = TemplateOCR()

        self.test_ctrl = TestCtrl

    # --- callback functiosn ---
    def read_match_percent(self, comp) -> Union[str, int]:
        # 1. Wait until the exec progress gets 100%
        logger.debug(f"Start waiting progress 100%: tid{self.test_ctrl.id} rid{self.test_ctrl.rid}")
        time.sleep(8)  # usual time + small margin, that it took for the progress to reach 100%

        start = time.time()
        timeout = 7
        is_100 = False
        fname = self.test_ctrl.make_temp_fname("progress")
        while time.time() < start + timeout: 
            progress = self.ocr_progress.read_percent(self.wmap.progress_region.rect, fname)
            if progress["value"] == 100: 
                is_100 = True
                break
        if is_100 == False: 
            logger.error(f"ERROR: Completions took more than {timeout} sec. Increse!!! ")
        time.sleep(0.5)  # wait more for the new match percent shows up

        # 2. Read the match percentage
        logger.debug(f"Start ocr-ing match percent: tid{self.test_ctrl.id} rid{self.test_ctrl.rid}")
        fname = self.test_ctrl.make_temp_fname("match")
        match_percent = self.ocr_match.read_number(self.wmap.match_region.regions, fname)
        if isinstance(match_percent, int): 
            if 0 <= match_percent <= 100: 
                return match_percent
            logger.error(f"OCR ERROR: match percent = {match_percent} ")
            
        # match_percent is the image file name
        self.match_fail_cnt += 1
        new_fname = self.test_ctrl.make_image_fname("match")
        shutil.move(match_percent, new_fname)
        return new_fname
    
    def run_callback(self, comp: Component) -> Any: 
        return comp.callback(comp)

    def click(self, comp: Component, p: Point = None, wait: float = 0.2) -> Any:
        # 1. Click 
        if p: 
            click_stable_at(p[0], p[1])
        else:     
            click_stable_at(comp.c[0], comp.c[1])
        time.sleep(wait)

        # 2. Run the callback
        if comp.callback: 
            return self.run_callback(comp)
        else: 
            return None

    def select_pulldown_item(self, test_type: str, test_case: str) -> str:
        # 1. Select code type
        self.click(self.wmap.option[test_type.lower()])
        
        # 2. Select the pulldown item and check that the pulldown item is configured
        edit = self.wmap.pulldown.edit
        set_text_at_point(edit.c[0], edit.c[1], test_case) # type in edit
        self.click(self.wmap.pulldown.arrow)                # select it and update grid area
        self.click(self.wmap.pulldown.selected, wait=1.0)
        self.click(self.wmap.pulldown.edit)                 # work-around the app bug (broken word)
        selected = get_text_at_point(edit.c[0], edit.c[1])  # check that test_case is selected
        if selected != test_case: 
            logger.error(f"No {test_case} under {test_type}: {selected} is selected instead")
            return None
        
        time.sleep(1.0)  # wait for the grid section to be refreshed with the selected
        return selected
    
    # --- Maintain test result data ---
    def policy_match(self, policy: dict, cat: str, subcat: str = None, description: str = None) -> bool:
        # 1) 1st layer: cat must exist
        if cat not in policy:
            return False
        rule = policy[cat]
        if rule == "*":     # case 1: cat level rule is "*"
            return True
        if not isinstance(rule, dict): # ??? description 없는 1-layer match 방지
            return False
        
        # 2) 2nd layer: subcat must exist
        if subcat not in rule: 
            return False
        subrule = rule[subcat]
        if subrule == "*":  # case 2: subcat level wildcard "*"
            return True

        # 3) 3rd layer: description regex match
        # subrule is a set of regex patterns
        if isinstance(subrule, (set, list)):
            if description is None:
                return False
            for pattern in subrule:
                if re.search(pattern, description):
                    return True
            return False

        return False  # if other unexpected type
    
    def add_prescription(self, match_percent: int, data: AnalysisResult) -> None:
        ''' return PrescriptionType = Literal["MUST-HAVE", 
                "GOOD-TO-HAVE", "GOOD-TO-RECORD", "VIRUS", "NEVER-MIND"]
        '''
        # Fill up the lackings
        data.test_id = self.test_ctrl.id
        data.test_run_id = self.test_ctrl.rid
        data.test_case = self.test_ctrl.case   # 'A', '골격', ...

        data.percentage = match_percent
        
        # Add data into the proper type 
        cat = data.cat
        subcat = data.subcat
        description = data.description
        logger.info(f"{data}")

        if match_percent >= Policy["MUST-HAVE"]: 
            self.prescription["must-have"].append(data)
            logger.info("\t\t ==> [MUST-HAVE]")
            return data
        
        # Virus case
        if self.policy_match(VirusPolicy, cat, subcat, description) == True:
           if match_percent >= Policy["VIRUS"]:
                self.prescription["virus"].append(data)
                logger.info("\t\t ==> [VIRUS]")
                if match_percent >= Policy["GOOD-TO-HAVE"]: 
                    self.prescription["good-to-have"].append(data)
                    logger.info("\t\t ==> [GOOD-TO-HAVE]")
                elif match_percent >= Policy["GOOD-TO-RECORD"]: 
                    self.prescription["good-to-record"].append(data)
                    logger.info("\t\t ==> [GOOD-TO-RECORD]")
        
        # Not virus case
        else: 
            if match_percent >= Policy["GOOD-TO-HAVE"]: 
                self.prescription["good-to-have"].append(data)
                logger.info("\t\t ==> [GOOD-TO-HAVE]")
            elif match_percent >= Policy["GOOD-TO-RECORD"]: 
                self.prescription["good-to-record"].append(data)
                logger.info("\t\t ==> [GOOD-TO-RECORD]")
        
        return data
    
    def add_prescription_check(self, match_percent, # Union(int, str), 
                               test_data # Union(AnalysisResult, str)
                               ) -> AnalysisResult:
        
        if isinstance(test_data, str): 
            # failed in reading the selected row from Analysis Grid 
            return {"percentage": match_percent, # int or image file name
                    "test_id": self.test_ctrl.id, 
                    "test_run_id": self.test_ctrl.rid, 
                    "test_case": self.test_ctrl.case, 
                    "fname": test_data}

        # matching percent is image, and matching row is analyzed as dict
        test_data.percentage = match_percent  # int or image file name
        test_data.test_id = self.test_ctrl.id
        test_data.test_run_id = self.test_ctrl.rid
        test_data.test_case = self.test_ctrl.case # "A", "골격", ...
        return test_data
   
   # --- Run a test ---
    def run_1cat(self, test_type: str, test_case: str, iters: int = 10) -> None:
        self.test_ctrl.start_1test(test_type, test_case)

        # 1. Choose the code type
        self.select_pulldown_item(test_type, test_case) # ex) "code", "A" or "cat", "골격"

        # 2. Resize the grid columns
        for c in range(2): 
            ok = self.grid_ctrl.resize_colums()
            if ok == True:
                break 
            logger.error(f"TODO: select aother in pull-down menu "
                        f"to reset the column size\n"
                        f" -> try again resize_colums")
         
        # 3. iterate analysis
        for _ in range(iters): 
            self.test_ctrl.start_1run()

            # 3.1. wait until progress gets 100% and read match percentage
            #      "bmp file name", or "int"
            match_percent = self.click(self.wmap.exec_button)

            # 3.2. find and read the selected grid row
            row_data = self.grid_ctrl.read_selected_row(self.test_ctrl)

            if isinstance(match_percent, int) and isinstance(row_data, AnalysisResult): # success
                result = self.add_prescription(match_percent, row_data)
            else:
                logger.error(f"Failed to collect test result: {self.test_ctrl}: {match_percent}, {row_data}") 
                result = self.add_prescription_check(match_percent, row_data)

            # 3.3. send prescription to te front-end
            # if self.show_prescription: 
            #     self.feq.push_msg(result: AnalysisResult)        
    
    def start(self, targets: Dict[str, List] = None, iters: int = 10): 
        '''Start analyzing '''
        # 1. Collect target to analyze. 
        targets = DiagTarget[targets] if targets else DiagTarget["common"]
        self.iteration = iters
        
        # 2. Test all test cases, case by case
        self.prescription_list: List[AnalysisResult] = list()
        for test_type, test_cases in targets.items(): 
            if test_type.lower() == 'subcat': 
                logger.info(f"ERROR: Not support: {test_type}")
                continue
            
            for case in test_cases: 
                self.run_1cat(test_type, case, self.iteration)
                time.sleep(1.0)




        