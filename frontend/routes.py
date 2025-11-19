import json
import os
from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "..", "config", "options.json")

def load_options():
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("options", [])
    except:
        return []

@frontend_bp.route("/ui/analysis")
def analysis_page():
    options = load_options()
    return render_template("analysis.html", options=options)

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
