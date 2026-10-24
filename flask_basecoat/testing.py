"""A bare Flask application with only Flask-Basecoat installed.

Used by the compliance checks and the test suite so component pages are rendered without the demo
application's database, login or mail configuration.
"""
from flask import Flask

from . import Basecoat


def make_app(**config):
    app = Flask('flask_basecoat_testing', static_folder=None)
    app.config.update(
        SECRET_KEY='flask-basecoat-testing',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        BASECOAT_GALLERY_ENABLED=True,
    )
    app.config.update(config)
    Basecoat(app)
    return app
