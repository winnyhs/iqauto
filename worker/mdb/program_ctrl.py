# mdb_sync.py
import json, os, sys, shutil, datetime, subprocess, time
import unicodedata, re
import win32com.client

from common.singleton import SingletonMeta
from common.log import logger
from common.json import save_json, load_json
from common.sys import path_type, safe_copy
from db.path_config import PathConfig

from .sql import Sql
from .db_ctrl import DbCtrl


class ProgramCtrl(metaclass = SingletonMeta): 
    def __init__(self, global_config): 
        self.cfg = global_config
        self.sql = Sql

        self.data_table = "M_DATA"
        logger.debug("M_DATA table is in %s", self.cfg.db["data_table_path"])

        self.program_table = "M_HISTORY"
        logger.debug("M_HISTORY table's DDL is in %s", self.cfg.db["program_ddl_path"])

        # This instance is to update MEDICAL.mdb in the system
        self.sys_db_ctrl = DbCtrl(self.cfg.sys_drv["mdb_path"], self.cfg.db["password"])
        try: 
            self.ext_db_ctrl = DbCtrl(self.cfg.ext_drv["mdb_path"], self.cfg.db["password"])
        except Exception as e: 
            logger.info("External DB is not installed yet. Postpone connecting.")
            self.ext_db_ctrl = None  # External drive is not installed yet
        
        # Hash table for data table
        self.prefix_len = 24  # cat2's string length to compare
        # For a program, htime is fixed as today's 00:00:00.000000
        self.htime = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod # Remove all white spaces and the get the prefix of <len> length
    def str_normalize(s, len):
        # Normalize Korean/English text for matching while preserving () , [] {}.
        if not s:
            return ""
        s = unicodedata.normalize("NFKC", s) # Unicode Normalize
        s = s.lower() # Lowercase (영문만 영향)
        s = s.strip() # Strip leading/trailing spaces

        # Remove ALL white spaces (space/tabs/newlines)
        s = re.sub(r"[ \t\r\n]+", "", s)
        # Remove punctuation EXCEPT (), [], {}, and ,
        # we remove: . , ; : ! ? ' " - _ / \ |
        s = re.sub(r"[.;:!?'\"/_\\\-|]+", "", s)

        return s[:len]

        # TODO: 그냥 matching 하는 것과 비교해 보기. 맨 앞 20글자만 matching 했을 때와도 비교하기
        # 개수를 봐서 차이가 있는지 없는지 확인하기 
        # TODO: table a, b, c, M_LIST, M_DATA 상호 비교해서 차이 정리하기 
    
    @staticmethod
    def hash_key(cat, subcat, value, str_len): 
        return (ProgramCtrl.str_normalize(cat, str_len),    # 대분류
                ProgramCtrl.str_normalize(subcat, str_len), # 소분류
                ProgramCtrl.str_normalize(value, str_len))  # 값
    
    @staticmethod  # Build the hash for exact match: key = (TYPE, ITEM, MEMO), value = row
    def build_hash(table_rows, str_len):
        index = {}
        for row in table_rows:
            key = ProgramCtrl.hash_key(row.get("TYPE"), row.get("ITEM"), row.get("MEMO"), str_len)  
            # 대분류, 소분류, 값
            index.setdefault(key, []).append(row)

        # for testing
        # print("example of value length %s: %s" % (len(index[("오관", "코", "정맥동염(축농증)")]), index[("오관", "코", "정맥동염(축농증)")]))
        # for item in index: # .keys():
        #     if item[0] == "오관" and item[1] == "코" and item[2].startswith("정맥동염"):
        #         print("key = {}".format(item))
        return index

    def exact_match(self, item, hash_table):
        key = ProgramCtrl.hash_key(item["cat"], item["subcat"], item["description"], self.prefix_len)
        return hash_table.get(key)   # 없으면 []

    def _get_json_path(self, default_path_key, json_path): 
        if json_path == None: 
            if default_path_key: 
                if default_path_key in self.cfg.worker_drv.keys(): 
                    json_path = self.cfg.worker_drv[default_path_key]
                elif default_path_key in self.cfg.ext_drv.keys(): 
                    json_path = self.cfg.ext_drv[default_path_key]
                elif default_path_key in self.cfg.sys_drv.keys(): 
                    json_path = self.cfg.sys_drv[default_path_key]
                else: 
                    logger.error("ERROR: invalid json path_key: %s", default_path_key)    
            else: 
                logger.error("ERROR: file path must be given: %s, %s", default_path_key, json_path)
        else: 
            pt = path_type(json_path)
            if pt == "file_name_only": 
                json_path = os.path.join(self.cfg.worker_drv["json_dir"], json_path)
            else: 
                json_path = os.path.abspath(json_path)
        return json_path

    def export_data_table(self, db, json_path = None): 
        '''{
                "CODE": "A0001002",
                "TYPE": "기관",   # 대분류
                "ITEM": "복부",   # 소분류
                "DETAIL": "",
                "NAME": "Abdominal_inflammation", # English, Grp, or same with MEMO
                "DATA1": 1.2,     # 주파수
                "DATA2": 180.0,   # 시간
                "GRP": "digestion", # 혈자리
                "VOICE": "",
                "VIDEO": "digestvideo",
                "MEMO": "복부염증",   # 내용. In some case, it has null string or None
                "WDATE": "2004-07-05T12:37:47+00:00",
                "MDATE": "2004-07-05T12:37:47+00:00",
                "WRITER": "ADMIN",
                "MODIFYER": "ADMIN"
            }
        '''
        # 1. Check the number of rows in M_DATA table
        def count_query(): 
            return "SELECT COUNT(*) AS TOTAL FROM M_DATA;"
        sql = count_query()
        logger.info("%s rows in M_DATA table", self.sql.query(db, sql))

        # 2. Read meaningful columns from M_DATA table
        def build_query(): 
            return (
                "SELECT " 
                    "CODE, TYPE, ITEM, NAME, DATA1, "
                    "FIX(DATA2 / 60) AS DATA200, GRP, VIDEO, MEMO "
                "FROM M_DATA;"
            )   # TYPE: 대분류, ITEM: 소분류, DATA1: 주파수, MEMO: 주파수 설명, GRP: 혈자리
        sql = build_query()
        json_data = self.sql.query(db, sql)

        for d in json_data: 
            v = d.pop("DATA200")
            d["DATA2"] = v
        # logger.info("%s rows in M_DATA table: Example row: %s", \
        #     len(json_data), json_data[100])

        # 3. Save as a json file 
        save_json(json_data, self.cfg.db["data_table_path"])
        logger.info("%s rows in M_DATA table are saved in %s", \
            len(json_data), self.cfg.db["data_table_path"])
    
    def _build_1program(self, data_table_hash, analysis_data, prog_name): 
        # Convert analysis json data into a program json data
        logger.info("Build a program for the analysis result...") #, flush=True)

        added_row_cnt = 0    # 실제 insert된 row 개수
        skipped_json_cnt = 0 # json element 기준으로 실패한 개수
        added_list = []
        skipped_list = []
        for item in analysis_data:
            # 1) Do exact match of a json element and M_DATA table 
            #    and get rows in M_DATA table
            matched_rows = self.exact_match(item, data_table_hash)
            if not matched_rows:
                skipped_list.append([item, norm_desc])
                skipped_json_cnt += 1
                logger.error(f"ERROR: --- dropped {item}")
                continue

            # 2) Add the matched rows into M_HISTORY table
            logger.info(f"--- Programmed {len(matched_rows)} row(s) for {item}")
            for table_row in matched_rows:
                added_row_cnt += 1
                added_list.append({
                    "HTIME": DbCtrl.normalize_value(self.htime),  # !!! 
                    "DESP": prog_name, 
                    "CODE": table_row.get("CODE"),
                    "NAME": table_row.get("MEMO"),  
                    "DATA1": table_row.get("DATA1"),
                    "DATA2": table_row.get("DATA2"),
                    "GRP": table_row.get("GRP"),
                    "VIDEO": table_row.get("VIDEO")
                })
        
        logger.info("")
        logger.info("───────────────────────────────────")
        logger.info("Completed programming from %s analysis results", len(analysis_data))
        logger.info("    Dropped : %s", skipped_json_cnt)
        logger.info("    Programs: %s", added_row_cnt)
        logger.info("    Dropped details: %s", skipped_list)
        logger.info("───────────────────────────────────")
        return added_row_cnt, added_list, skipped_json_cnt, skipped_list

    # Build a program for the analysis results
    def build_1program(self, analysis_file_list, prog_name):
        # 1) Read table M_DATA
        logger.info(f"Loading data table, M_DATA, s...") #, flush=True)
        data_table = load_json(self.cfg.db["data_table_path"])

        # 2) Build a hash table for table M_DATA
        logger.info("Building hash table for fast exact matching...") # , flush=True)
        data_table_hash = self.build_hash(data_table, self.prefix_len)  # 24 characters only

        program_data = []
        for af in analysis_file_list:
            # 3) Read analysis result data, that is new prescription to add into M_HISTORY
            logger.info("Loading analysis result, %s, ...", af) #, flush=True)
            af_path = self._get_json_path(None, af)
            af_data = load_json(af_path)
            if len(af_data) == 0: 
                logger.info("    None in there. Skip...")
                continue

            # 4) Build a program for the analysis result
            result = self._build_1program(data_table_hash, af_data, prog_name)
            program_data.extend(result[1])

        # 5) Save the program
        program_path = self._get_json_path("program_path", None)
        # subprocess.call("rm %s" % (program_path), shell = True)
        # time.sleep(0.3)

        save_json(program_data, program_path)
        logger.info("%s programs are saved as %s", len(program_data), program_path)
        return program_data

    # Delete all rows of a table
    def delete_all_rows_in_table(self, db, table_name): 
        sql = "DELETE FROM %s" % (table_name)
        try:
            db.Execute(sql) # "DELETE FROM M_HISTORY")
        except Exception as e:
            logger.error("%s: ERROR: Failed in empty table %s: %s", e, table_name, sql)
        else: 
            logger.info("Table %s gets empty", table_name)
    
    # Insert a dict data into a table
    def insert(self, db, table_name, table_ddl, json_data):
        """
        Insert rows from json_data into DAO table without using transactions.
        Compatible with all Jet/DAO modes, including cases where BeginTrans() fails.
        """
        cnt = 0
        for row in json_data:
            cols = []
            vals = []

            for k, v in row.items():
                cols.append(k)
                v = DbCtrl.restore_value(v, table_ddl[k])
                vals.append(v)

            col_list = ", ".join(cols)

            # Build VALUES part
            val_list = []
            for v in vals:
                if v is None:
                    val_list.append("NULL")
                elif isinstance(v, (int, float)):
                    val_list.append(str(v))
                elif isinstance(v, (datetime.datetime, datetime.date)):
                    val_list.append("#%04d-%02d-%02d 00:00:00#" % (v.year, v.month, v.day))
                else: 
                    s = str(v).replace("'", "''")
                    val_list.append("'" + s + "'")

            val_expr = ", ".join(val_list)

            sql = "INSERT INTO %s (%s) VALUES (%s)" % (
                table_name, col_list, val_expr
            )
            if cnt < 3: 
                logger.debug("--- %s", sql)
                cnt += 1
            # Execute immediately (auto-commit mode)
            db.Execute(sql)

    # Insert multiple program files into the program table of the db
    def insert_from_json(self, db, json_path_list):
        for path in json_path_list: 
            # 1. Load a json file 
            path = self._get_json_path(None, path)
            data = load_json(path)

            # 2. Insert the json dagta
            ddl = load_json(self.cfg.db["program_ddl_path"])[self.program_table]
            program_table_ddl = {f["name"]:f["type"] for f in ddl["fields"]}

            self.insert(db, self.program_table, program_table_ddl, data)
            logger.info("%s rows are inserted into %s from %s", \
                len(data), self.program_table, path)

    # Export multiple programs from the program table of the db
    def export_programs(self, db, program_name_list, json_path): 
        # 1. Find the json path to export
        json_path = self._get_json_path(None, json_path)
        if os.path.exists(json_path): 
            os.remove(json_path)

        # 2. Read and save the program list table (M_HISTORY)
        set_phrase = ",".join("'{}'".format(s.replace("'", "''")) for s in program_name_list)
        sql = r"SELECT * FROM M_HISTORY WHERE DESP IN ({})".format(set_phrase)
        logger.debug("--- SQL: %s", sql)
        data = self.sql.query(db, sql)
        if len(data) == 0: 
            logger.info("None is selected. Skip...")

        # 3. Save as a json file 
        save_json(data, json_path)
        logger.info("%s rows are exported as %s", len(data), json_path)
        return data, json_path



if __name__ == "__main__": 
    drive = os.path.splitdrive(os.getcwd())[0]
    logger.info("Running on %s", drive)

    # logger.debug(sys.argv, flush=True)
    if len(sys.argv) < 2: 
        logger.error("Usage Example) python -m worker.mdb.program_ctrl test5")
        exit()
    prog_name = sys.argv[1]

    c = PathConfig
    dst = c.worker_drv["json_dir"]
    src_dir = os.path.join(c.worker_drv["client_dir"], r"kkk\2025-11-18T22-43\json")
    src = os.path.join(src_dir, "must-have.json")
    shutil.copy2(src, dst)
    src = os.path.join(src_dir, "good-to-have.json")
    shutil.copy2(src, dst)

    dst = c.ext_drv["mdb_path"]
    src = c.sys_drv["mdb_path"]
    # shutil.copy2(src, dst)
    safe_copy(src, dst)


    p = ProgramCtrl(c)

    # logger.debug("worker_drv['json_dir'] : %s", os.listdir(c.worker_drv["json_dir"]))

    # 1. export the program table as json file
    # db = p.sys_db_ctrl.open_db()
    # p.export_data_table(db)
    # db.Close()

    # 2. Build the program from the analysis result json and 
    #    the program is saved as c.worker_drv["program_path"]
    p.build_1program(["must-have.json", "good-to-have.json"], prog_name)

    # # 3. Insert the program into the system mdb
    db = p.sys_db_ctrl.open_db()
    p.insert_from_json(db, [c.worker_drv["program_path"]])
    db.Close()

    # 4. Export the program table (M_HISTORY) to the external driver
    program_list = ["기억2", "test4"]
    db = p.sys_db_ctrl.open_db()
    json_data, path = p.export_programs(db, program_list, "exported_programs.json")
    db.Close()
    logger.info("%s directory: %s", c.worker_drv["json_dir"], os.listdir(c.worker_drv["json_dir"]))

    # --- DO delete some program from the system mdb --- 
    input("Enter when ready: ")

    # 5. Import the programs that are not in the system mdb
    json_list = ["exported_programs.json"]
    db = p.ext_db_ctrl.open_db()
    p.insert_from_json(db, json_list)
    db.Close()

    input("Enter when ready: ")

    # 6. Put back the updated MEDICAL.mdb
    src = c.sys_drv["mdb_path"]
    dst = c.sys_drv["mdb_path"] + ".backup"
    safe_copy(src, dst)

    input("Enter when ready: ")
    
    src = c.ext_drv["mdb_path"]
    dst = c.sys_drv["mdb_path"]
    safe_copy(src, dst)


