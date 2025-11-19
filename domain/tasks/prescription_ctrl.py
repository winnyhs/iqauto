import os, platform, subprocess, json
import webbrowser
from typing import List, Dict, Optional
from dataclasses import dataclass #, field

from lib.test_ctrl import TestCtrl
from lib.analysis_result import AnalysisResult


class PrescriptionCtrl: # (metaclass=SingletonMeta):

    def __init__(self, client: Dict, prescription: Dict[str, List]) :
        self.test_ctrl = TestCtrl
        self.ps = {severity: {} for severity in [
            "must-have", "good-to-have", "good-to-record", "virus", "check"]}

        for severity in self.ps: 
            html_fname = self.test_ctrl.make_html_fname(severity)
            json_fname = self.test_ctrl.make_json_fname(severity)
            self.ps[severity] = {
                            "prescription": prescription[severity], 
                            "html_fname": html_fname,
                            "json_fname": json_fname
            }

            with open(html_fname, "w", encoding="utf-8") as f:
                f.write(self.html_table(severity, self.ps[severity]["prescription"]))

            json_data = [r.as_dict() for r in prescription[severity]]
            with open(json_fname, "w", encoding="utf-8") as f: 
                json.dump(json_data, f, ensure_ascii=False, indent=2)

    def html_result_table(self, severity, results) -> str:
        prefixes = ("LR", "HT", "SP", "LU", "KI",
                    "PC", "GV", "GB", "SI", "ST",
                    "LI", "BL", "TE", "CV")
        # 1. Table data
        code_rows = []
        cat_rows = []
        for r in results:
            match_fname = TestCtrl.make_image_fname("match", r.test_id, r.test_run_id, r.test_case)
            progress_fname = TestCtrl.make_image_fname("progress", r.test_id, r.test_run_id, r.test_case)

            presc = r.prescription.strip() if isinstance(r.prescription, str) else ""
            presc = presc if presc.startswith(prefixes) else ""

            if r.test_case.upper() == "A": 
                code_rows.append(f"""
                    <tr>
                        <td>{r.cat}</td>
                        <td>{r.subcat}</td>
                        <td>{r.description}</td>
                        <td>{r.percentage}</td>
                        <td>{presc}</td>

                        <td>
                            <img src="{match_fname}" onerror="this.style.display='none';">
                            <img src="{progress_fname}" onerror="this.style.display='none';">
                        </td>
                        <td>{r.test_id}</td>
                        <td>{r.test_run_id}</td>
                        <td>{r.code}</td>
                        <td>{r.part}</td>
                    </tr>
                    """)
            else: 
                cat_rows.append(f"""
                    <tr>
                        <td>{r.cat}</td>
                        <td>{r.subcat}</td>
                        <td>{r.description}</td>
                        <td>{r.percentage}</td>
                        <td>{presc}</td>

                        <td>
                            <img src="{match_fname}" onerror="this.style.display='none';">
                            <img src="{progress_fname}" onerror="this.style.display='none';">
                        </td>
                        <td>{r.test_id}</td>
                        <td>{r.test_run_id}</td>
                        <td>{r.code}</td>
                        <td>{r.part}</td>
                    </tr>
                    """)

         
        # 2. Table Format
        # <td style="white-space: nowrap;">Ear conditions various</td>
        # <td style="word-wrap: break-word; word-break: break-all;">...</td>
        table_head = """
            <colgroup>
                <col style="width: 10%; min-width: 60px;">
                <col style="width: 10%; min-width: 60px;">
                <col style="width: 30%; min-width: 200px;">
                <col style="width: 5%; min-width: 20px;">
                <col style="width: 10%; min-width: 70px;">

                <col style="width: 10%; min-width: 50px;">
                <col style="width: 5%; min-width: 20px;">
                <col style="width: 5%; min-width: 20px;">
                <col style="width: 10%; min-width: 60px;">
                <col style="width: 5%; min-width: 50px;">
            </colgroup>
            <tr>
                <th>대분류</th>
                <th>소분류</th>
                <th>설명</th>
                <th>%</th>
                <th>경락</th>

                <th>이미지</th>
                <th>TC</th>
                <th>Run</th>
                <th>코드</th>
                <th>부분</th>
            </tr>

        """
        
        return f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Analysis Result</title>
            <style>
                table {{border-collapse: collapse; margin: 10px; font-size: 14px;}}
                th, td {{border: 1px solid #444;padding: 4px 8px;}}
                th {{background-color: #ddd;}}
            </style>
        </head>
        <body>
            <h2>{severity}</h2>
            <h3>A 코드 분석 결과</h2>
            <table>
                {table_head}
                {''.join(code_rows)}
            </table>
            
            <h3>대분류 분석 결과</h2>
            <table>
                {table_head}
                {''.join(cat_rows)}
            </table>
        </body>
        </html>
        """

    def html_check_table(self, results: AnalysisResult) -> str:
        # have_row_data = []
        # have_no_row_data = []
        # for r in results: 
        #     if r.cat is not None: # hold a row data
        #         pass # have_row_data render all just like normal case
        #     else: # hold no row data
        #         pass # have_no_row_data
        return "TODO: IMPLEMENT !!!"
        
    def html_table(self, severity: str, results: AnalysisResult) -> str:
        if severity.lower() == "check":
            return self.html_check_table(results)
        else: 
            return self.html_result_table(severity, results)

    def open_in_default_browser(self, fname:str):
        """Open HTML file depending on OS version (XP/7 → IE, Win10+ → Edge)."""

        system = platform.system()
        release = platform.release()   # "XP", "7", "10", "11"

        html_abspath = os.path.abspath(fname)

        # Windows OS
        if system == "Windows":

            # Windows XP or 7 → Internet Explorer
            if release.startswith("XP") or release.startswith("7"):
                ie_path = r"C:\Program Files\Internet Explorer\iexplore.exe"
                if os.path.exists(ie_path):
                    subprocess.Popen([ie_path, html_abspath])
                else:
                    webbrowser.open(html_abspath)
                return

            # Windows 10 or higher → Microsoft Edge
            if int(release) >= 10:
                # Newer Edge (Chromium) command
                edge_cmd = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
                edge_cmd2 = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

                if os.path.exists(edge_cmd):
                    subprocess.Popen([edge_cmd, html_abspath])
                elif os.path.exists(edge_cmd2):
                    subprocess.Popen([edge_cmd2, html_abspath])
                else:
                    webbrowser.open(html_abspath)
                return

        # Other OS (Linux, Mac)
        else: 
            webbrowser.open(html_abspath)

    def show(self): 
        # TODO - change.... 
        # 4 buttons to select to show
        # check is selected when open the page
        # when clicking a button, show its corrensponding table 
        self.open_in_default_browser(self.ps["must-have"]["html_fname"])
        self.open_in_default_browser(self.ps["check"]["html_fname"])
