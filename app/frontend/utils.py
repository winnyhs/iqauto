from common.log import logger
from common.json import load_json
from db.config import GlobalConfig as config

def load_options():
    try:
        test_cases   = load_json(config.db["test_case_path"])
        user_profile = load_json(config.db["user_profile_path"])
        return {"test_cases": test_cases, "user_profile": user_profile}
    except Exception as e:
        logger.exception("ERROR: %s" % e)
        return {"test_cases": [], "user_profile": []}