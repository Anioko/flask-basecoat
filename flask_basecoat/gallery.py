"""Component and block gallery.

``/basecoat/``                       index of every component and block
``/basecoat/components/<name>``      port of the upstream example for one registry component
``/basecoat/blocks/<name>``          port of one upstream block
The page templates live in ``templates/basecoat/pages/`` and are the fixtures the compliance checks
compare against the golden upstream markup.
"""
import json
import pathlib

from flask import Blueprint, abort, render_template, request, flash, redirect, url_for
from jinja2 import TemplateNotFound
from wtforms import Form, StringField, PasswordField, BooleanField, SelectField, TextAreaField, validators

gallery_bp = Blueprint('basecoat_gallery', __name__, template_folder='templates')

_HERE = pathlib.Path(__file__).resolve().parent
_REGISTRY = _HERE.parent / 'compliance' / 'upstream' / 'shadcn' / 'registry' / 'index.json'
_BLOCKS = _HERE.parent / 'compliance' / 'upstream' / 'shadcn' / 'radix' / 'blocks'


def component_names():
    """Registry component names, from the pinned upstream index when present, else from the page templates."""
    if _REGISTRY.exists():
        return sorted(i['name'] for i in json.loads(_REGISTRY.read_text(encoding='utf8')) if i.get('type') == 'registry:ui')
    pages = _HERE / 'templates' / 'basecoat' / 'pages' / 'components'
    return sorted(p.stem for p in pages.glob('*.html'))


def block_names():
    if _BLOCKS.exists():
        return sorted(p.name for p in _BLOCKS.iterdir() if p.is_dir() and p.name.split('-')[0] in ('dashboard', 'login', 'signup', 'sidebar'))
    pages = _HERE / 'templates' / 'basecoat' / 'pages' / 'blocks'
    return sorted(p.stem for p in pages.glob('*.html'))


def has_page(kind, name):
    return (_HERE / 'templates' / 'basecoat' / 'pages' / kind / f'{name}.html').exists()


class DemoForm(Form):
    name = StringField('Full Name', [validators.Length(min=4, max=25), validators.InputRequired()], description="Enter your full legal name.")
    email = StringField('Email Address', [validators.Email(), validators.InputRequired()], description="We'll never share your email.")
    password = PasswordField('Password', [validators.Optional(), validators.Length(min=8)], description='At least 8 characters.')
    role = SelectField('Team Role', choices=[('dev', 'Developer'), ('lead', 'Tech Lead'), ('pm', 'Product Manager')])
    bio = TextAreaField('Short Biography', [validators.Optional(), validators.Length(max=200)], description="A brief summary.")
    terms = BooleanField('I agree to the terms and privacy policy', [validators.InputRequired()])


@gallery_bp.route('/')
def index():
    comps = [{'name': n, 'ready': has_page('components', n)} for n in component_names()]
    blocks = [{'name': n, 'ready': has_page('blocks', n)} for n in block_names()]
    return render_template('basecoat/pages/index.html', components=comps, blocks=blocks)


@gallery_bp.route('/components/<name>')
def component(name):
    try:
        return render_template(f'basecoat/pages/components/{name}.html', name=name)
    except TemplateNotFound:
        abort(404)


@gallery_bp.route('/blocks/<name>', methods=['GET', 'POST'])
def block(name):
    try:
        return render_template(f'basecoat/pages/blocks/{name}.html', name=name)
    except TemplateNotFound:
        abort(404)


_GOLDEN = _HERE.parent / 'compliance' / 'golden' / 'out'


@gallery_bp.route('/golden/<path:path>')
def golden(path):
    """The upstream React render of an example or block (compliance/golden/out), for side-by-side comparison."""
    from flask import send_from_directory
    if not _GOLDEN.exists():
        abort(404)
    return send_from_directory(str(_GOLDEN), path)


@gallery_bp.route('/compare/<name>')
def compare(name):
    """Upstream golden page on the left, our page on the right, same viewport and theme."""
    kind = 'blocks' if name in block_names() else 'components'
    if not has_page(kind, name):
        abort(404)
    return render_template('basecoat/pages/compare.html', name=name, kind=kind,
                           golden_url=url_for('basecoat_gallery.golden', path=(f'blocks/{name}.html' if kind == 'blocks' else f'{name}.html')),
                           ours_url=url_for(f'basecoat_gallery.{"block" if kind == "blocks" else "component"}', name=name),
                           components=component_names(), blocks=block_names())


@gallery_bp.route('/gallery', methods=['GET', 'POST'])
def gallery():
    """WTForms adapter demo: a real server-validated form rendered with the field macros."""
    form = DemoForm(request.form)
    if request.method == 'POST':
        if form.validate():
            flash('Demo form submitted successfully. All validations passed.', 'success')
            return redirect(url_for('basecoat_gallery.gallery'))
        flash('Please correct the validation errors in the form.', 'error')
    return render_template('basecoat/pages/forms.html', form=form)
