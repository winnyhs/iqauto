
from lib.analysis_result import AnalysisResult

data = {
    "must-have": [
        AnalysisResult(
            percentage=89,
            test_case="A",
            cat="오관",
            subcat="귀",
            description="귀 상태 여러가지(방전, 이명, 가려움, 청각손실, 이염 확인)",
            prescription="Ear_conditions_various",
            part="",
            code="A0306003", 
            test_id="1",
            test_run_id="1"
        ),
        AnalysisResult(
            percentage=99,
            test_case="A",
            cat="호흡",
            subcat="감기",
            description="인플루엔자 바이러스 영국",
            prescription="Influenza_virus_British",
            part="",
            code="A0715006",
            test_id="1",
            test_run_id="2"
        ), 
        AnalysisResult(
            percentage=85,
            test_case="cat",
            cat="경락",
            subcat="간경",
            description="족궐음 간경",
            prescription="GB 11-15",
            part="",
            code="F0307001",
            test_id="2",
            test_run_id="1"
        )], 

    "good-to-have": [
        AnalysisResult(
            percentage=10,
            test_case="A",
            cat="오관",
            subcat="귀",
            description="귀 상태 여러가지(방전, 이명, 가려움, 청각손실, 이염 확인)",
            prescription="Ear_conditions_various",
            part="",
            code="A0306003",
            test_id="1",
            test_run_id="3"
        ),
        AnalysisResult(
            percentage=20,
            test_case="cat",
            cat="호흡",
            subcat="감기",
            description="감기 1992",
            prescription="Influenza_virus_British",
            part="",
            code="F0715006",
            test_id="3",
            test_run_id="1"
        )], 
    "good-to-record" : [], 
    "virus": [], 
    "check": [
        AnalysisResult(
            percentage=70,
            test_case="A",
            fname=".\image\analysis_1.bmp",
            test_id="1",
            test_run_id="4"
        ),
        AnalysisResult(
            percentage=".\image\match_percent_1.img",
            test_case="cat",
            cat="호흡",
            subcat="감기",
            description="감기 1992",
            prescription="Influenza_virus_British",
            part="",
            code="F0715006",
            test_id="3",
            test_run_id="2"
        )], 
}
