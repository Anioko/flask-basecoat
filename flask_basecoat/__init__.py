"""
flask_basecoat: the shadcn/ui design system as Jinja macros for Flask.

Every component in the shadcn/ui registry is available as a macro from ``basecoat/<name>.html`` or
through the barrel ``basecoat/index.html``. Visuals come from the upstream shadcn stylesheet pipeline
(Tailwind v4, the shadcn style pack and the neutral theme) compiled into the shipped CSS; behaviour
comes from ``flask-basecoat.js``.
"""
from flask import Blueprint, url_for
from jinja2 import ChoiceLoader, PackageLoader
from markupsafe import Markup

from .document import harvey_ball as _harvey_ball
from .icons import svg as _lucide_svg
from .slots import slot as _slot
from .twmerge import merge as _merge


def tw(*classes):
    """Jinja global: merge class strings with tailwind-merge semantics (later classes win)."""
    return _merge(classes)

__version__ = "1.0.0"

basecoat_bp = Blueprint(
    'basecoat',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/basecoat'
)


@basecoat_bp.route('/placeholder.svg')
def placeholder():
    """The neutral image the upstream blocks reference for cover art and avatars."""
    from flask import Response
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200">'
           '<rect width="1200" height="1200" fill="oklch(0.97 0 0)"/>'
           '<path d="M0 0L1200 1200M1200 0L0 1200" stroke="oklch(0.922 0 0)" stroke-width="4"/></svg>')
    return Response(svg, mimetype='image/svg+xml')


def lucide(name, class_name='', **attrs):
    """Jinja global rendering a Lucide icon exactly as lucide-react does (``class="lucide lucide-<name> ..."``)."""
    return _lucide_svg(name, class_name, **attrs)


class Basecoat:
    """Flask extension registering the templates, static assets and gallery."""

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if 'basecoat' not in app.blueprints:
            app.register_blueprint(basecoat_bp)

        package_loader = PackageLoader('flask_basecoat', 'templates')
        if app.jinja_loader is not None:
            app.jinja_loader = ChoiceLoader([app.jinja_loader, package_loader])
        else:
            app.jinja_loader = package_loader

        app.jinja_env.globals.setdefault('lucide', lucide)
        app.jinja_env.globals.setdefault('slot', _slot)
        app.jinja_env.globals.setdefault('tw', tw)
        app.jinja_env.globals.setdefault('harvey_ball_shape', _harvey_ball)
        from . import charts as _charts
        app.jinja_env.globals.setdefault('chart_spec', _charts.load_spec)
        app.jinja_env.globals.setdefault('chart_style_css', _charts.chart_style_css)
        app.jinja_env.globals.setdefault('chart_spec_json', _charts.spec_json)
        app.jinja_env.globals.setdefault('chart_uid', _charts.chart_uid)

        @app.context_processor
        def inject_basecoat():
            return {'basecoat': self}

        if app.config.get('BASECOAT_GALLERY_ENABLED', False) or app.debug or app.testing:
            from .gallery import gallery_bp
            if 'basecoat_gallery' not in app.blueprints:
                app.register_blueprint(gallery_bp, url_prefix='/basecoat')

        if app.config.get('BASECOAT_EXAMPLES_ENABLED', True):
            from .examples import examples_bp
            if 'basecoat_examples' not in app.blueprints:
                app.register_blueprint(examples_bp, url_prefix='/examples')

    def css(self):
        """``<link>`` for the compiled component stylesheet shipped with the package."""
        href = url_for('basecoat.static', filename='css/flask-basecoat.min.css')
        return Markup(f'<link rel="stylesheet" href="{href}">')

    def js(self):
        """``<script>`` for the behaviour runtime shipped with the package."""
        src = url_for('basecoat.static', filename='js/flask-basecoat.js')
        return Markup(f'<script src="{src}" defer></script>')

    def head(self):
        """Both tags together."""
        return Markup(f'{self.css()}\n{self.js()}')
