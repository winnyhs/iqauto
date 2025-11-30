
from dataclasses import dataclass #, field
from typing import Optional

@dataclass
class AnalysisResult: 
    percentage: int = None

    test_id: int = None
    test_run_id: int = None
    test_case: str = None    # 'A' or None
    
    # Read data from analysis grid
    cat: str = None
    subcat: str = None
    description: str = None
    code:str = None  # A or None
    prescription: str = None
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
