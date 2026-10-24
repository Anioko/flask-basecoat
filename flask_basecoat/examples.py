"""
flask_basecoat.examples:
Application screens built with the Flask-Basecoat macros.

Most screens are ports of the shadcn-examples collection and live in ``templates/examples/ported/<slug>.html`` with a
``<slug>.json`` file describing them; they are served at ``/examples/<slug>`` and listed on ``/examples/``
automatically. The dashboards, two-step verification and notifications screens are original to Flask-Basecoat.
"""
import json
import pathlib

from flask import Blueprint, abort, redirect, render_template, url_for

examples_bp = Blueprint(
    'basecoat_examples',
    __name__,
    template_folder='templates',
    static_folder='static'
)

_PORTED = pathlib.Path(__file__).resolve().parent / 'templates' / 'examples' / 'ported'

DASHBOARDS = ('marketing', 'sales', 'overview', 'analytics', 'insights', 'pipeline')

# Addresses of earlier screens that the ported screens replace.
MOVED = {
    'dashboard': 'admin-dashboard',
    'pricing': 'pricing-tables',
    'profile': 'profile-page',
    'projects': 'projects-list',
    'changelog': 'changelog-page',
    'coming-soon': 'coming-soon-page',
    'blog': 'blog-page',
    'blog-detail': 'blog-detail-page',
    'onboarding': 'onboarding-flow',
    'chat': 'chat-app',
    'product-detail': 'product-detail-page',
    'kanban': 'kanban-board',
    'shopping-cart': 'cart',
    'checkout': 'checkout-page',
    'add-product': 'add-product-form',
    'mail': 'mail-app',
    'calendar': 'event-calendar',
}

ORIGINAL = [
    {
        'id': 'dashboards',
        'title': 'Dashboards',
        'description': 'Six dashboard layouts (marketing, sales, overview, analytics, insights and pipeline) sharing one sidebar, header and set of cards, charts and tables.',
        'endpoint': ('basecoat_examples.dashboards', {'name': 'marketing'}),
        'tags': ['Sidebar', 'Charts', 'Tables', 'Cards'],
    },
    {
        'id': 'two-factor',
        'title': 'Two-Step Verification',
        'description': 'Two-factor authentication (2FA) verification screen with 6-digit OTP code input, countdown, and resend trigger.',
        'endpoint': ('basecoat_examples.two_factor', {}),
        'tags': ['Security', 'Auth', 'Forms'],
    },
    {
        'id': 'solution-document',
        'title': 'Solution Document',
        'description': 'A ten-page solution document: cover, executive summary, options with Harvey balls, charts, recommendation, risks and next steps. Prints and saves to PDF in A4 or Letter.',
        'endpoint': ('basecoat_examples.solution_document', {}),
        'tags': ['Document', 'Print', 'Charts'],
    },
    {
        'id': 'notifications',
        'title': 'Notifications Center',
        'description': 'Centralized user notification feed with All/Unread/Mentions filter tabs, unread indicators, and mark-all-as-read.',
        'endpoint': ('basecoat_examples.notifications', {}),
        'tags': ['Notifications', 'Tabs', 'Badges'],
    },
]


def ported_examples():
    """Metadata of the ported screens, one JSON file per screen, in title order."""
    out = []
    for meta_file in _PORTED.glob('*.json'):
        meta = json.loads(meta_file.read_text(encoding='utf8'))
        meta.setdefault('id', meta_file.stem)
        if (_PORTED / f"{meta['id']}.html").exists():
            out.append(meta)
    return sorted(out, key=lambda m: m.get('title', m['id']).lower())


@examples_bp.route('/')
def index():
    """Directory of every application screen."""
    examples_list = [
        {k: v for k, v in dict(item, href=url_for(item['endpoint'][0], **item['endpoint'][1])).items() if k != 'endpoint'}
        for item in ORIGINAL
    ]
    examples_list += [dict(meta, href=url_for('basecoat_examples.ported', slug=meta['id'])) for meta in ported_examples()]
    return render_template('examples/index.html', examples=examples_list)


@examples_bp.route('/two-factor')
def two_factor():
    """Two-step verification screen."""
    return render_template('examples/two_factor.html')


@examples_bp.route('/notifications')
def notifications():
    """Notifications center screen."""
    return render_template('examples/notifications.html')


DOCUMENT_TITLE = 'Claims Platform Modernisation: Solution Document'

# Three-year cost by option, in pounds million (one-off build and migration, and running cost).
DOCUMENT_COSTS = [
    ('Option A', 1.2, 9.6),
    ('Option B', 3.4, 7.8),
    ('Option C', 5.1, 5.9),
    ('Option D', 11.8, 4.6),
]
# Share of claims migrated at the end of each quarter, as planned and as forecast with today's team.
DOCUMENT_DELIVERY = [
    ('Q2 27', 5, 5), ('Q3 27', 20, 15), ('Q4 27', 40, 30), ('Q1 28', 60, 45), ('Q2 28', 80, 60), ('Q3 28', 95, 75), ('Q4 28', 100, 90),
]


def _document_specs():
    """The two charts of the solution document: the bar and line chart specs with the document's data and value labels."""
    import copy
    from flask_basecoat.charts import load_spec
    label = {'position': 'top', 'offset': 8, 'className': 'fill-foreground', 'fontSize': 11}
    bar = copy.deepcopy(load_spec('chart-bar-multiple'))
    bar['config'] = {'build': {'label': 'Build and migration', 'color': 'var(--chart-1)'},
                     'run': {'label': 'Running cost', 'color': 'var(--chart-4)'}}
    bar['data'] = [{'option': o, 'build': b, 'run': r} for o, b, r in DOCUMENT_COSTS]
    bar['props'] = {'accessibilityLayer': True, 'margin': {'top': 20}}
    bar['series'] = [dict(s, dataKey=k, fill=f'var(--color-{k})', labelList=[dict(label)])
                     for s, k in zip(bar['series'], ('build', 'run'))]
    bar['axes'][0] = {k: v for k, v in bar['axes'][0].items() if k != 'tickFormatter'}
    bar['axes'][0]['dataKey'] = 'option'
    legend = load_spec('chart-area-legend')['legend']
    bar['legend'] = copy.deepcopy(legend)
    line = copy.deepcopy(load_spec('chart-line-label'))
    line['config'] = {'planned': {'label': 'Planned', 'color': 'var(--chart-5)'},
                      'forecast': {'label': 'Forecast with today\'s team', 'color': 'var(--chart-2)'}}
    line['data'] = [{'quarter': q, 'planned': p, 'forecast': f} for q, p, f in DOCUMENT_DELIVERY]
    line['series'] = [dict(line['series'][0], dataKey='planned', stroke='var(--color-planned)', type='linear',
                           dot={'fill': 'var(--color-planned)'}, labelList=[dict(label, offset=10)]),
                      dict(line['series'][0], dataKey='forecast', stroke='var(--color-forecast)', type='linear',
                           dot={'fill': 'var(--color-forecast)'}, labelList=[dict(label, position='bottom', offset=10)])]
    line['axes'][0] = {k: v for k, v in line['axes'][0].items() if k != 'tickFormatter'}
    line['axes'][0]['dataKey'] = 'quarter'
    line['props'] = {'accessibilityLayer': True, 'margin': {'top': 24, 'bottom': 16, 'left': 12, 'right': 12}}
    line['legend'] = copy.deepcopy(legend)
    return bar, line


@examples_bp.route('/document/solution-document')
def solution_document():
    """The solution document: the reading layout with a cover, printed through the print stylesheet (R17).
    ``?size=letter`` selects US Letter, A4 is the default."""
    from flask import request
    bar, line = _document_specs()
    return render_template('examples/document/solution-document.html', title=DOCUMENT_TITLE,
                           page_size='letter' if request.args.get('size') == 'letter' else 'a4',
                           cost_chart=bar, delivery_chart=line, costs=DOCUMENT_COSTS)


@examples_bp.route('/dashboards/')
@examples_bp.route('/dashboards/<name>')
def dashboards(name='marketing'):
    """Six dashboard layouts that share one sidebar and header."""
    if name not in DASHBOARDS:
        abort(404)
    return render_template(f'examples/dashboards/{name}.html')


def _portfolio_spec():
    """The interactive area chart of the reference portfolio page: the dashboard-01 chart with portfolio data."""
    import copy
    import datetime
    import random
    from flask_basecoat.charts import load_spec
    spec = copy.deepcopy(load_spec('chart-area-interactive'))
    rng = random.Random(7)
    start = datetime.date(2026, 7, 2)
    rows = []
    changes, incidents = 30.0, 9.0
    for i in range(91):
        day = start + datetime.timedelta(days=i)
        changes = max(12.0, min(60.0, changes + rng.uniform(-4, 4.5)))   # a slow random walk reads as a trend
        incidents = max(2.0, min(20.0, incidents + rng.uniform(-1.5, 1.4)))
        rows.append({'date': day.isoformat(), 'changes': round(changes), 'incidents': round(incidents)})
    spec['data'] = rows
    spec['config'] = {'events': {'label': 'Events'},
                      'changes': {'label': 'Changes', 'color': 'var(--primary)'},
                      'incidents': {'label': 'Incidents', 'color': 'var(--primary)'}}
    remap = {'desktop': 'changes', 'mobile': 'incidents', 'Desktop': 'Changes', 'Mobile': 'Incidents'}

    def rename(obj):
        if isinstance(obj, dict):
            return {k: rename(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [rename(v) for v in obj]
        if isinstance(obj, str):
            for a, b in remap.items():
                obj = obj.replace(a, b)
        return obj
    for key in ('series', 'defs', 'tooltip', 'legend'):
        if key in spec:
            spec[key] = rename(spec[key])
    spec['legend'] = None  # dashboard-01 shows no legend
    if isinstance(spec.get('derive'), dict):
        spec['derive']['reference'] = (start + datetime.timedelta(days=90)).isoformat()
    return spec


PORTFOLIO_APPS = [
    # name, capability, lifecycle, owner, run cost (k$ a year), health
    ('Customer Portal', 'Customer engagement', 'Invest', 'Ana Silva', 420, 'Healthy'),
    ('Order Hub', 'Order management', 'Invest', 'Daniel Okafor', 610, 'Healthy'),
    ('Ledger Pro', 'Financial accounting', 'Tolerate', 'Mei Chen', 380, 'At risk'),
    ('Fieldforce', 'Field service', 'Migrate', 'Tom Becker', 290, 'At risk'),
    ('HR Suite', 'Workforce management', 'Tolerate', 'Priya Nair', 340, 'Healthy'),
    ('Legacy Billing', 'Billing', 'Eliminate', 'Mei Chen', 520, 'Critical'),
    ('Data Lakehouse', 'Analytics', 'Invest', 'Ana Silva', 710, 'Healthy'),
    ('Partner Gateway', 'Partner management', 'Migrate', 'Lukas Weber', 180, 'Healthy'),
    ('Warehouse WMS', 'Inventory', 'Tolerate', 'Daniel Okafor', 450, 'At risk'),
    ('Intranet 2012', 'Collaboration', 'Eliminate', 'Priya Nair', 95, 'Critical'),
]


@examples_bp.route('/reference/portfolio')
def reference_portfolio():
    """Reference page: an application portfolio dashboard composed only of shadcn parts in the dashboard-01 frame."""
    return render_template('examples/reference/portfolio.html', chart=_portfolio_spec(), apps=PORTFOLIO_APPS)


@examples_bp.route('/<slug>', methods=['GET', 'POST'])
def ported(slug):
    """A ported screen (templates/examples/ported/<slug>.html); earlier addresses redirect to their replacement."""
    if slug in MOVED:
        return redirect(url_for('basecoat_examples.ported', slug=MOVED[slug]), code=301)
    if not (_PORTED / f'{slug}.html').exists():
        abort(404)
    return render_template(f'examples/ported/{slug}.html')
