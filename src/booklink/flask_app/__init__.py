"""
Entry point of flask application
"""

import subprocess

from flask import Flask
from booklink.application_service import ApplicationServiceConfig


def get_git_revision_short_hash() -> str:
    "Get the short hash of the current git revision"
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("ascii").strip()


def get_git_revisition_branch() -> str:
    "Get the current git branch"
    return (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        .decode("ascii")
        .strip()
    )


def create_app(test_config=None):
    "Create and configure the app"
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        APP_SERVICE_CONFIG=ApplicationServiceConfig(
            max_clients_in_pairing=100,
            client_expiration_seconds=5 * 60,
        ),
        MAX_CLIENTS_IN_PAIRING=100,
        CLIENT_EXPIRATION_SECONDS=300,
        POLL_PAIRING_STATUS_SECONDS=1,
        GIT_REVISION_HASH=get_git_revision_short_hash(),
        GIT_REVISION_BRANCH=get_git_revisition_branch(),
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    from . import api

    app.register_blueprint(api.bp)
    with app.app_context():
        api.init_app(app)

    from . import frontend

    app.register_blueprint(frontend.bp)

    return app
