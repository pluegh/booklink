"""
Provides the API backend.

This module translates the service layer to the flask routes.
"""

from io import BytesIO

from flask import Blueprint, current_app, request, send_file
from werkzeug.utils import secure_filename

from booklink.application_service import ApplicationService


bp = Blueprint("api", __name__, url_prefix="")


def app_service() -> ApplicationService:
    "Get the service from the current app"
    return current_app.service  # type: ignore[attr-defined]


def token_arg():
    "Get token from request argument"
    token = request.args.get("token")
    if not token:
        return "No token provided", 400
    return token


@bp.route("/api/new_client")
def new_client():
    "Generate a new client for pairing"

    name = request.args.get("friendly_name") or ""

    try:
        client = current_app.service.new_client(friendly_name=name)
    except Exception:  # pylint: disable=broad-except
        return "Cannot create new client", 500

    return {
        "client_id": client.id,
        "pairing_code": client.pairing_code,
        "token": client.token,
    }


@bp.route("/api/pair/<client_id>/<pairing_code_ereader>")
def pair_with_ereader(client_id, pairing_code_ereader):
    "Pair two clients"

    channel = app_service().new_channel_using_code(client_id, token_arg(), pairing_code_ereader)
    return {
        "channel_id": channel.id,
        "client_id": client_id,
        "token": channel.token,
    }


@bp.route("/api/channels_for/<client_id>")
def channels_for_ereader(client_id):
    "Return the results of pairings for a client"

    channels = app_service().channels_for_client(client_id, token_arg())

    return [
        {
            "channel_id": c.id,
            "token": c.token,
        }
        for c in channels
    ]


@bp.route("/api/upload/<channel_id>/<client_id>", methods=["POST"])
def upload_file(channel_id, client_id):
    "Upload a file to the channel"

    if "file" not in request.files:
        return {"error": "No file part"}, 400

    raw_file = request.files["file"]
    if raw_file.filename == "":
        return {"error": "No selected file"}, 400

    if raw_file:
        filename = secure_filename(raw_file.filename)
        data_buffer = BytesIO(raw_file.read())

        try:
            current_app.service.store_file_for_channel(
                channel_id, client_id, token_arg(), filename, data_buffer
            )
        except Exception:  # pylint: disable=broad-except
            return {"error": "Cannot store file"}, 400

        return {"message": "File uploaded successfully"}, 200

    return {"error": "File type not allowed"}, 400


@bp.route("/api/delete/<channel_id>/<client_id>/<file_id>", methods=["DELETE"])
def delete_file(channel_id, client_id, file_id):
    "Delete a file from the channel"

    try:
        app_service().remove_file(channel_id, client_id, token_arg(), file_id)
    except Exception:  # pylint: disable=broad-except
        return {"error": "Cannot delete file"}, 400

    return {"message": "File deleted successfully"}, 200


@bp.route("/api/files/<channel_id>/<client_id>")
def get_files(channel_id, client_id):
    "Get all files for a channel"

    files = app_service().get_files_for_channel(channel_id, client_id, token_arg())

    return [
        {
            "name": f.name,
            "size": f.size,
            "title": f.title,
            "author": f.author,
            "id": f.id,
            "expires_at_unixutc": f.expires_at_unixutc,
        }
        for f in files
    ]


@bp.route("/<file_name>")
def download_file(file_name):  # pylint: disable=unused-argument
    """Download a file.

    The kobo ereader needs the url to be at the root.
    Internally, the file is fetched with a unique ID passed as a query parameter.
    """

    file = app_service().get_file(
        request.args.get("channel_id"),
        request.args.get("client_id"),
        token_arg(),
        file_id=request.args.get("file_id"),
    )

    # Copy file since flask will close the file after sending
    sending_buffer = BytesIO()
    sending_buffer.write(file.data.read())
    file.data.seek(0)  # Reset file buffer after read

    return send_file(
        sending_buffer,
        as_attachment=True,
        download_name=file.name,
    )
