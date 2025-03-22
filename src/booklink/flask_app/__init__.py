"""
Entry point of flask application
"""

import os

from flask import Flask

from booklink.application_service import ApplicationService, ApplicationServiceConfig
from booklink.flask_app.utils import get_git_revision_short_hash, get_git_revisition_branch


def create_app(TestConfig=None) -> Flask:  # pylint: disable=C0103
    "Create and configure the app"
    app = Flask(__name__, instance_relative_config=True)

    Config = TestConfig or get_config_from_env()  # pylint: disable=C0103

    app.config.from_object(Config)
    Config.init_app(app)

    attach_service(app)

    from . import api

    app.register_blueprint(api.bp)

    from . import frontend

    app.register_blueprint(frontend.bp)

    return app


def attach_service(app: Flask):
    "Attach the application service to the flask app"

    service_config = ApplicationServiceConfig(
        client_jwt_secret=app.config["SECRET_KEY"],
        channel_jwt_secret=app.config["SECRET_KEY"],
        max_clients_in_pairing=app.config["MAX_CLIENTS_IN_PAIRING"],
        max_files_in_channel=app.config["MAX_FILES_IN_CHANNEL"],
        client_expiration_seconds=app.config["CLIENT_EXPIRATION_SECONDS"],
    )

    setattr(app, "service", ApplicationService(service_config))


class BaseConfig:
    "Configuration for the flask app"

    SECRET_KEY: str | None
    MAX_CLIENTS_IN_PAIRING: int = 100
    MAX_FILES_IN_CHANNEL: int = 20
    CLIENT_EXPIRATION_SECONDS: float = 60 * 60
    GIT_REVISION_HASH: str = get_git_revision_short_hash()
    GIT_REVISION_BRANCH: str = get_git_revisition_branch()

    @classmethod
    def init_app(cls, app: Flask):
        "Initialize the app with testing configuration"
        app.logger.info(f"Configuration is `{cls.__name__}`")
        app.logger.info(
            f"Git revision is `{cls.GIT_REVISION_HASH}` on branch `{cls.GIT_REVISION_BRANCH}`"
        )
        if app.config.get("SECRET_KEY") is None:
            raise ValueError("SECRET_KEY must be set in production environment")


class DevConfig(BaseConfig):
    "Configuration for the flask app in development"

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key"
    SERVER_NAME = "localhost:5001"


class ProdConfig(BaseConfig):
    "Configuration for the flask app"

    SECRET_KEY: str | None = os.environ.get("SECRET_KEY")  # No fallback


def get_config_from_env() -> type[BaseConfig]:
    "Get the configuration from the environment"
    if os.environ.get("FLASK_ENV") == "production":
        return ProdConfig
    return DevConfig
