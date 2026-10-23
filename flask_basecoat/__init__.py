"""
flask_basecoat: Canonical shadcn/ui-aligned Jinja macros wrapping Basecoat UI.
"""
from flask import Blueprint
from jinja2 import ChoiceLoader, PackageLoader

__version__ = "0.1.0"

basecoat_bp = Blueprint(
    'basecoat',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/basecoat'
)


class Basecoat:
    """Flask extension for Basecoat UI integration."""

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Register Basecoat templates and static assets into Flask so that
        `{% from 'basecoat/button.html' import button %}`
        works across all blueprints and templates in the host application.
        """
        if 'basecoat' not in app.blueprints:
            app.register_blueprint(basecoat_bp)

        package_loader = PackageLoader('flask_basecoat', 'templates')
        if app.jinja_loader is not None:
            app.jinja_loader = ChoiceLoader([app.jinja_loader, package_loader])
        else:
            app.jinja_loader = package_loader

        # Register component gallery blueprint in debug/test/enabled environments
        if app.config.get('BASECOAT_GALLERY_ENABLED', False) or app.debug or app.testing:
            from .gallery import gallery_bp
            if 'basecoat_gallery' not in app.blueprints:
                app.register_blueprint(gallery_bp, url_prefix='/basecoat')
