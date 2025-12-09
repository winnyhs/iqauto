import os
from db.path_config import PathConfig
from common.sys import safe_copy
from worker.mdb.program_ctrl import ProgramCtrl

def insert_program(client_profile, analysis_result_list, prog_name): 

    PathConfig.post_init(client_profile)
    prog_ctrl = ProgramCtrl(PathConfig, client_profile)

    # Copy the client test result data in for processing
    for file in analysis_result_list: 
        src_path = os.path.join(PathConfig.worker_drv['test_data_json_dir'], file)
        dst_path = os.path.join(PathConfig.worker_drv['json_dir'], file)
        safe_copy(src_path, dst_path)
    
    # logger.debug("worker_drv['json_dir'] : %s", os.listdir(c.worker_drv["json_dir"]))

    # 2. Build the program from the analysis result json and 
    #    the program is saved as PathConfig.worker_drv["program_path"]
    prog_ctrl.build_1program(analysis_result_list, prog_name)  # ["must-have.json"]

    # 3. Insert the program into the system mdb
    db = prog_ctrl.sys_db_ctrl.open_db()
    prog_ctrl.insert_from_json(db, [PathConfig.worker_drv["program_path"]]) # basic_file = "basic1.json"
    db.Close()

    # # 5. Import the programs that are not in the system mdb
    # json_list = ["exported_programs.json"]
    # db = prog_ctrl.ext_db_ctrl.open_db()
    # prog_ctrl.insert_from_json(db, json_list)
    # db.Close()

    # # 6. Put back the updated MEDICAL.mdb
    # src = c.sys_drv["mdb_path"]
    # dst = c.sys_drv["mdb_path"] + ".backup"
    # safe_copy(src, dst)
    
    # src = c.ext_drv["mdb_path"]
    # dst = c.sys_drv["mdb_path"]
    # safe_copy(src, dst)

    # dst = c.ext_drv["mdb_path"]
    # src = c.sys_drv["mdb_path"]
    # # shutil.copy2(src, dst)
    # safe_copy(src, dst)

if __name__ == "__main__": 
    import datetime
    client_profile = {"name": "jj",  "bdate": "1990-01-01", "sex": "남", "weight": 80, "height": 170}
    client_profile['test_time'] = "2025-12-09T02-46-33"
    insert_program(client_profile, ["must-have.json"], "jjj_test")