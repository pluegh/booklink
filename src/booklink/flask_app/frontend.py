"Serving the frontend routes"

from functools import wraps

from flask import (
    Blueprint,
    current_app,
    render_template,
    redirect,
    request,
    url_for,
)

bp = Blueprint("frontend", __name__)


def redirect_ereader_to_pair(f):
    "Decorator to redirect to pairing if user is on e-reader"

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_agent = request.headers.get("User-Agent").lower()
        print(f"User agent: {user_agent}")
        agent_identifiers = ["kobo", "kindle"]
        for agent_id in agent_identifiers:
            if agent_id not in user_agent:
                continue
            return redirect(url_for(".pair_ereader"))
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/")
@redirect_ereader_to_pair
def landing_page():
    "Render the landing page"
    return render_template("landing_page.html")


@bp.route("/pair_ereader")
def pair_ereader():
    "Pairing route for e-reader"
    return render_template(
        "simple_pair.html",
        client_expiration_seconds=current_app.config["CLIENT_EXPIRATION"],
        poll_pairing_status_every=current_app.config["POLL_PAIRING_STATUS_EVERY"],
    )


@bp.route("/pair")
def pair():
    "Pairing route"

    # Only ask to enter code of e-reader device
    return render_template(
        "pair.html",
        client_expiration_seconds=current_app.config["CLIENT_EXPIRATION"],
    )


agent_to_friendly_name = {
    "kobo": "Kobo Device",
    "kindle": "Kindle Device",
}


@bp.route("/receive/<channel_id>/<client_id>")
def receive(channel_id, client_id):
    "Receive route"
    return render_template(
        "simple_receive.html",
        channel_id=channel_id,
        client_id=client_id,
        token=request.args.get("token"),
    )


@bp.route("/send/<channel_id>/<client_id>")
def send(channel_id, client_id):
    "Send route"
    return render_template(
        "send.html",
        channel_id=channel_id,
        client_id=client_id,
        token=request.args.get("token"),
        sender_name=request.args.get("sender") or "Sender Device",
        ereader_name=request.args.get("ereader") or "E-Reader",
        file_poll_interval=current_app.config["POLL_FILE_STATUS_EVERY"],
    )
