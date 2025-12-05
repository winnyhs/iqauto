from typing import Literal 

PrescriptionType = Literal["MUST-HAVE", "GOOD-TO-HAVE", "GOOD-TO-RECORD", "VIRUS", "NEVER-MIND"]
Policy = { 
    "MUST-HAVE": 35,      # 85
    "GOOD-TO-HAVE": 25,   # 75 
    "GOOD-TO-RECORD": 1, # 70
    "VIRUS": 15,          # 55
} 

CovidVacinSideEffectPolicy = {
    # 뇌, 심장에 특히 세게 생긴다. 
    "뇌": "*", 
    "장부": {"심장": "*"},
    "기타": "해독", 
    "병원균": {"세균": "*"}
}
VirusPolicy = {
        "병원균": "*",
        "호흡" : {
            "감기": "*", 
            "감염": "*", 
            "객담": "*",
            "기관지": ["^기관지염",], 
            "재치기": "*",
            "후두": "*", 
            "편도선": "*", 
            "인두": "*",
        },
        "알러지": {
            "알러지" : "*"
        }
}
FeverPolicy = {
    "소아": {
        "성홍열": "*", 
        "소아마비": "*"
    }, 
}
HardToBreathePolicy = {
    "호흡" : {
        "호흡곤란": "*", 
        "산소부족": "*"
    }
}

FeverColdPolicy = {**VirusPolicy, **FeverPolicy}
