from flask import Flask
from .routes import backend_bp

def create_backend_app():
    app = Flask(__name__)
    app.register_blueprint(backend_bp)
    return app
