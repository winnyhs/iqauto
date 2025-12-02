
from dataclasses import dataclass #, field
from typing import Optional

@dataclass
class AnalysisResult: 
    percentage: int = None

    test_id: int = None      # unique, serial number
    test_run_id: int = None  # iteration number in a test case
    test_case: str = None    # 'A' or 대분류
    
    # Read data from analysis grid
    cat: str = None    # 대분류
    subcat: str = None # 소분류
    description: str = None   # 주파수 설명
    code:str = None           # 주파수 코드
    prescription: str = None  # 혈자리
    part: str = None

    fname: Optional[str] = None # image of analysis grid capture

    def as_dict(self): 
        return {
            'percentage': self.percentage, 
            'test_id': self.test_id, 
            'test_run_id': self.test_run_id,
            'test_case': self.test_case,
            'cat': self.cat,
            'subcat': self.subcat,
            'description': self.description,
            'code': self.code,
            'prescription': self.prescription,
            'part': self.part,
            'fname': self.fname
        }
