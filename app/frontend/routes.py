import json, os
from flask import Blueprint, render_template, request

frontend_bp = Blueprint("frontend", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_TEST_OPTION_PATH  = os.path.join(BASE_DIR, "..", "db", "test_option.json")
DB_USER_PROFILE_PATH = os.path.join(BASE_DIR, "..", "db", "user_profile.json")

print("--- BASE_DIR: %s" % BASE_DIR)
print("--- DB: test option: %s" % DB_TEST_OPTION_PATH)
print("---     user profile: %s" % DB_USER_PROFILE_PATH)

def load_options():
    test_option = []
    user_profile = []
    try:
        with open(DB_TEST_OPTION_PATH, "r", encoding="utf-8") as f:
            test_option = json.load(f)
        with open(DB_USER_PROFILE_PATH, "r", encoding="utf-8") as f: 
            user_profile = json.load(f)
        return {"test_option": test_option, "user_profile": user_profile}
    except Exception as e:
        print("ERROR: %s" % e)
        return {"test_option": [], "user_profile": []}

@frontend_bp.route("/ui/analysis")
def analysis_page():
    options = load_options()  # 기존 함수
    return render_template("analysis.html", options=options)

@frontend_bp.route("/ui/analysis/status", methods=["GET"], endpoint="analysis_status")
def analysis_status():  # url_for('frontend.analysis_status')
    run_id = request.args.get("run_id", "")
    # Why: 이후 폴링/중간 결과 바인딩을 위해 run_id 전달
    return render_template("analysis_status.html", run_id=run_id)







@frontend_bp.route("/")
@frontend_bp.route("/ui/customer")
def customer_page():
    return render_template("customer.html")

@frontend_bp.route("/ui/result")
def result_page():
    return render_template("result.html")

@frontend_bp.route("/ui/prescribe")
def prescribe_page():
    return render_template("prescribe.html")

@frontend_bp.route("/ui/prescribe_view")
def prescribe_view_page():
    return render_template("prescribe_view.html")
