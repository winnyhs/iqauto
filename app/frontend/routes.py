from common.log import logger
from common.json import load_json
from db.path_config import PathConfig as config
from .utils import load_options

import json, os, datetime
from flask import Blueprint, render_template, request

frontend_bp = Blueprint("frontend", __name__)



@frontend_bp.route("/analysis")
def analysis_page():
    logger.info("=== GET /ui/analysis")
    options = load_options()
    # logger.info("Load options: %s", options)
    return render_template("analysis.html", options=options)

@frontend_bp.route("/analysis/status", endpoint="analysis_status")
def analysis_status():  # url_for('frontend.analysis_status')
    logger.info("=== GET /ui/analysis/status")
    test_id = request.args.get("test_id", "")
    options = {
        "user_profile": json.loads(request.args.get("user_profile", "{}")),
        "test_cases": json.loads(request.args.get("test_cases", "[]")),
    }
    logger.info("options: %s, %s", options["user_profile"], options["test_cases"])
    return render_template("analysis_status.html", options=options)







@frontend_bp.route("/")
@frontend_bp.route("/customer")
def customer_page():
    return render_template("customer.html")

@frontend_bp.route("/result")
def result_page():
    return render_template("result.html")

@frontend_bp.route("/prescribe")
def prescribe_page():
    return render_template("prescribe.html")

@frontend_bp.route("/prescribe_view")
def prescribe_view_page():
    return render_template("prescribe_view.html")
