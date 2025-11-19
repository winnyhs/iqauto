from flask import Blueprint, request, jsonify
from . import longtask

backend_bp = Blueprint("backend", __name__)

@backend_bp.route("/api/run_analysis", methods=["POST"])
def run_analysis():
    data = request.get_json() or {}
    print("[BACKEND] run_analysis:", data)
    longtask.start()
    return jsonify({"ok": True})

@backend_bp.route("/api/progress", methods=["GET"])
def progress():
    pct, done = longtask.progress()
    return jsonify({"percent": pct, "done": done})

@backend_bp.route("/api/hello")
def hello():
    return jsonify({"message": "hello", "ok": True})

@backend_bp.route("/")
def root():
    return "backend root"
