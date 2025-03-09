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
            return redirect(url_for(".pair", friendly_name=f"{agent_id} device", is_ereader="on"))
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/")
def landing_page():
    "Render the landing page"
    return render_template("landing_page.html")


@bp.route("/pair")
def pair():
    "Pairing route"

    # Autofill and contiunue if user is on e-reader
    if "friendly_name" not in request.args:
        user_agent = request.headers.get("User-Agent").lower()
        print(f"User agent: {user_agent}")
        agent_identifiers = agent_to_friendly_name.keys()
        for agent_id in agent_identifiers:
            if agent_id not in user_agent:
                continue
            url = url_for(
                ".pair",
                friendly_name=f"{agent_to_friendly_name.get(agent_id, 'unknown')}",
                is_ereader="on",
            )
            print(f"Redirecting to {url}")
            return redirect(url)

    if "friendly_name" not in request.args:
        return render_template(
            "pair_configuration.html",
            is_ereader_preselection=False,
        )

    if "is_ereader" in request.args:
        # Only show code to enter on sender device
        return render_template(
            "simple_pair.html",
            client_expiration_seconds=current_app.config["CLIENT_EXPIRATION_SECONDS"],
            poll_pairing_status_seconds=current_app.config["POLL_PAIRING_STATUS_SECONDS"],
        )

    # Only ask to enter code of e-reader device
    return render_template(
        "pair.html",
        expiration_seconds=current_app.config["CLIENT_EXPIRATION_SECONDS"],
    )


agent_to_friendly_name = {
    "kobo": "Kobo Device",
    "kindle": "Kindle Device",
}


@bp.route("/receive")
def receive():
    "Receive route"
    return render_template("simple_receive.html")


@bp.route("/send/<channel_token>")
def send(channel_token):
    "Send route"
    return render_template("send.html", channel_token=channel_token)
