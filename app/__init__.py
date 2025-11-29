from flask import Flask

# frontend / backend 모듈 import
from app.frontend.routes import frontend_bp
from app.backend.routes import backend_bp

def create_app():
    app = Flask(__name__)

    # FRONTEND 등록
    app.register_blueprint(frontend_bp)

    # BACKEND 등록
    app.register_blueprint(backend_bp, url_prefix="/api")

    print("--- URL MAP:", app.url_map)
    return app
