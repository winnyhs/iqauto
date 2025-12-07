from common.log import logger
from flask import Blueprint, request, jsonify
import app.backend.route_handler as route_handler

backend_bp = Blueprint("backend", __name__)


@backend_bp.route("/analysis/start", methods=["POST"])
def api_analysis_start():
    logger.info("=== POST /api/analysis/start")
    report_url = route_handler.analysis_start(request)
    logger.debug("--- report_url: %s", report_url)
    return jsonify({"ok": True, "report_url": report_url})

@backend_bp.route("analysis/status", methods=["POST"])
def api_analysis_status_post():
    logger.info("=== POST /api/analysis/status")
    progress_data = route_handler.analysis_status_post(request)
    logger.debug("--- progress_data: %s", progress_data)
    return jsonify(progress_data)

@backend_bp.route("/files/<path:rel_path>")
def api_file_serve(rel_path): #: str):
    logger.info("=== GET /api/files/rel_path=%s", rel_path)
    image = route_handler.file_serve(rel_path)
    logger.debug("--- %s", image)
    return image


@backend_bp.route("/")
def api_root():
    return "backend root"

