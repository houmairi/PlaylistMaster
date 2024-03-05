from flask import Flask
from .routes import bp as main_bp

def create_app():
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object('app.config.Config')
    app.register_blueprint(main_bp)
    return app