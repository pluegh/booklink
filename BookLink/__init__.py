"""
Entry point of flask application
"""
import os

from flask import Flask

def create_app(test_config=None):
    "Create and configure the app"
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='secrete-dev-key',
        JWT_SECRET='secret-jwt-key',
        MAX_CLIENTS_IN_PAIRING=100,
        CLIENT_EXPIRATION_SECONDS=5,
        POLL_PAIRING_STATUS_SECONDS=1,
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    from . import api
    app.register_blueprint(api.bp)
    with app.app_context():
        api.init_app(app)

    from . import frontend
    app.register_blueprint(frontend.bp)

    return app
