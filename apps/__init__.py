
# from apps.authentication.oauth import github_blueprint
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_mail import Mail, Message
from apps.utils.principal import principal

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()  # instantiate the mail class



def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    principal.init_app(app)


def register_blueprints(app):
    for module_name in ('authentication', 'home', 'resource', 'permission', 'role', 'user', 'product'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):
    
    @app.before_first_request
    def initialize_database():
        db.create_all()
        # db.create_all(bind='thip')

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)

    # app.register_blueprint(github_blueprint, url_prefix="/login")

    register_blueprints(app)
    configure_database(app)
    return app
