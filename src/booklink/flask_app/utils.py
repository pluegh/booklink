"""Utility functions for the Flask app"""

import subprocess


def get_git_revisition_branch() -> str:
    "Get the current git branch"
    return (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        .decode("ascii")
        .strip()
    )


def get_git_revision_short_hash() -> str:
    "Get the short hash of the current git revision"
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("ascii").strip()
