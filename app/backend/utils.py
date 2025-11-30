import os, base64, mimetypes
from flask import jsonify, request, abort

# 이미지가 놓인 루트 경로(예: 프로젝트 내 static/images). 실제 경로로 맞추세요.
IMAGE_ROOT = os.path.join(os.path.dirname(__file__), "static", "images")

def _img_to_data_url(filepath):
    """ filename → data URL(base64). 파일이 없으면 None."""
    if not filepath:
        return None
    # 절대경로/상대경로 모두 지원
    path = filepath if os.path.isabs(filepath) else os.path.join(IMAGE_ROOT, filepath)
    if not os.path.exists(path):
        return None
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return "data:%s;base64,%s" % (mime, b64)