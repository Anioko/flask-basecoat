"""
flask_basecoat: Canonical shadcn/ui-aligned Jinja macros wrapping Basecoat UI.
"""
from flask import Blueprint, current_app, url_for
from markupsafe import Markup
from jinja2 import ChoiceLoader, PackageLoader

__version__ = "0.1.0"

basecoat_bp = Blueprint(
    'basecoat',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/basecoat'
)


def _render_docs(source):
    """Render a registry entry's docs source (Jinja) in the current app, keeping its trailing newline."""
    return Markup(current_app.jinja_env.from_string(source + '\n').render())


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

        # Context processor for {{ basecoat.css() }} and {{ basecoat.js() }}
        @app.context_processor
        def inject_basecoat():
            return {
                'basecoat': self
            }

        # Registry entries drive the gallery index and the docs component pages
        from .gallery_registry import get_entry
        app.add_template_global(get_entry, 'basecoat_entry')
        app.add_template_global(_render_docs, 'basecoat_render_docs')

        # Register component gallery blueprint in debug/test/enabled environments
        if app.config.get('BASECOAT_GALLERY_ENABLED', False) or app.debug or app.testing:
            from .gallery import gallery_bp
            if 'basecoat_gallery' not in app.blueprints:
                app.register_blueprint(gallery_bp, url_prefix='/basecoat')

        # Register ported shadcn examples blueprint
        if app.config.get('BASECOAT_EXAMPLES_ENABLED', True):
            from .examples import examples_bp
            if 'basecoat_examples' not in app.blueprints:
                app.register_blueprint(examples_bp, url_prefix='/examples')

    def css(self):
        """Render Basecoat CSS link tags."""
        basecoat_url = url_for('basecoat.static', filename='css/basecoat.min.css')
        return Markup(f'<link rel="stylesheet" href="{basecoat_url}">')

    def js(self):
        """Render Basecoat JS script tag."""
        js_url = url_for('basecoat.static', filename='js/all.min.js')
        return Markup(f'<script src="{js_url}" defer></script>')
