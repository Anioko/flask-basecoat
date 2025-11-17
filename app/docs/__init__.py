from flask import Blueprint


docs = Blueprint(
    "docs",
    __name__,
    template_folder="../templates/docs",
    static_folder="../static",
)

from . import routes  # noqa: F401
