from typing import Literal 


DiagTarget = {
    "test" : {"code": ["A", ],
              # "cat": ["신경", ]
              }, 
    "common" : 
        {"code": ["A",], 
        "cat" : [
                "골격", "극성", "근건", "내분비", "뇌",        # 0
                "면역", "바흐플라워", "병원균", "소화", "순환",  # 5
                "신경", "암", "운동", "장부", "정서"           # 10
                ]
        }, 
    "woman" : 
        {"code": ["A"], 
         "cat": ["생식", "DIET", "피부"] }, 
}

# Add directly from mdb
SymtomTarget = {
    "kids": [("소아", "성장"), ("소아", "학습")], 
    "월경통": [  ("생식", "여성", "^월경통"), 
                ("생식", "여성", "월경"), 
                ("생식", "여성", "자궁"), 
                ("생식", "여성", "Menstrual cramps")], 
    "혈압": (("순환", "림프"), ("순환", "혈관"), ("순환", "혈압"), 
            ("순환", "혈액"), ("순환", "혈행"),
            ("운동", "관절", "^통풍")), 
}


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
