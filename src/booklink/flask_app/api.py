"""
Provides the API backend.
"""

from flask import Blueprint, current_app, request
from werkzeug.utils import secure_filename

from booklink.application_service import ApplicationService
from booklink.pair_devices import TooManyClientsError

bp = Blueprint("api", __name__, url_prefix="/api")


def init_app(app):
    "Define registration of the blueprint with the app"
    current_app.service = ApplicationService(config=current_app.config["APP_SERVICE_CONFIG"])


def token_arg():
    "Get token from request argument"
    token = request.args.get("token")
    if not token:
        return "No token provided", 400
    return token


@bp.route("/new_client")
def new_client():
    "Generate a new client for pairing"

    name = request.args.get("friendly_name") or ""

    try:
        client_id, pairing_code, token = current_app.service.new_client(friendly_name=name)
    except TooManyClientsError:
        return "Too many clients in pairing process", 500

    return {
        "client_id": client_id,
        "pairing_code": pairing_code,
        "token": token,
    }


@bp.route("/config")
def get_config():
    "Get the configuration for the client"
    return current_app.service.get_config()


@bp.route("/pair/<client_id>/<pairing_code_ereader>")
def pair_with_ereader(client_id, pairing_code_ereader):
    "Pair two clients"

    channel_id, token = current_app.service.pair_with_ereader(
        client_id, token_arg(), pairing_code_ereader
    )
    return {
        "channel_id": channel_id,
        "client_id": client_id,
        "token": token,
    }


@bp.route("/channels_for/<client_id>")
def channels_for_ereader(client_id):
    "Return the results of pairings for a client"

    channels = current_app.service.channels_for_client(client_id, token_arg())

    return [
        {
            "channel_id": c["id"],
            "token": c["token"],
        }
        for c in channels
    ]


@bp.route("/upload/<channel_id>/<client_id>", methods=["POST"])
def upload_file(channel_id, client_id):
    "Upload a file to the channel"

    current_app.logger.info("Uploading file")

    if "file" not in request.files:
        return {"error": "No file part"}, 400

    raw_file = request.files["file"]
    if raw_file.filename == "":
        return {"error": "No selected file"}, 400

    if raw_file:
        filename = secure_filename(raw_file.filename)
        file_content = raw_file.read()

        current_app.service.store_file_for_channel(
            channel_id, client_id, token_arg(), filename, file_content
        )

        return {"message": "File uploaded successfully"}, 200

    return {"error": "File type not allowed"}, 400


@bp.route("/files/<channel_id>/<client_id>")
def get_files(channel_id, client_id):
    "Get all files for a channel"

    files = current_app.service.get_files_for_channel(channel_id, client_id, token_arg())

    return [
        {
            "name": f["name"],
            "size": f["size"],
            "id": f["id"],
        }
        for f in files
    ]
