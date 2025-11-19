from flask import Flask
from .routes import frontend_bp
from .proxy import proxy_bp

def create_frontend_app():
    app = Flask(__name__)
    app.register_blueprint(frontend_bp)
    app.register_blueprint(proxy_bp)
    return app
