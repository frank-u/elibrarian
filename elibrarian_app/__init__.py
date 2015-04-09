from config import config
from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.restful import Api
from flask.ext.sqlalchemy import SQLAlchemy

api = Api()
bootstrap = Bootstrap()
db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    api.init_app(app)
    bootstrap.init_app(app)
    db.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1')

    from .webui import webui as webui_blueprint
    app.register_blueprint(webui_blueprint, url_prefix='/ui')

    return app