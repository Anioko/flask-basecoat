"""
flask_basecoat.examples:
Showcase blueprint demonstrating real-world applications ported from shadcn-examples.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from wtforms import Form, StringField, TextAreaField, validators

examples_bp = Blueprint(
    'basecoat_examples',
    __name__,
    template_folder='templates',
    static_folder='static'
)


class AuthForm(Form):
    email = StringField('Email', [validators.Email(), validators.InputRequired()])


class ProfileForm(Form):
    username = StringField('Username', [validators.Length(min=3, max=30), validators.InputRequired()])
    email = StringField('Email', [validators.Email(), validators.InputRequired()])
    bio = TextAreaField('Bio', [validators.Optional()])


@examples_bp.route('/')
def index():
    """Directory of all ported shadcn application examples."""
    examples_list = [
        {
            'id': 'authentication',
            'title': 'Authentication',
            'description': 'Split-screen authentication screen with hero branding, email input, social OAuth, and terms.',
            'href': url_for('basecoat_examples.authentication'),
            'tags': ['Forms', 'Buttons', 'Layout']
        },
        {
            'id': 'dashboard',
            'title': 'Admin Dashboard',
            'description': 'Executive dashboard with KPI metric cards, tabbed overview charts, and recent sales transaction feeds.',
            'href': url_for('basecoat_examples.dashboard'),
            'tags': ['Cards', 'Tabs', 'Badges', 'Buttons']
        },
        {
            'id': 'tasks',
            'title': 'Tasks & Data Management',
            'description': 'Interactive task management data table with search, status facet badges, priority icons, and row actions.',
            'href': url_for('basecoat_examples.tasks'),
            'tags': ['Table', 'Dropdown', 'Badge', 'Input']
        },
        {
            'id': 'pricing',
            'title': 'Pricing Tables',
            'description': 'Transparent tier comparison cards, feature checklists, and billing frequency toggles.',
            'href': url_for('basecoat_examples.pricing'),
            'tags': ['Cards', 'Badges', 'Buttons']
        },
        {
            'id': 'profile',
            'title': 'Profile & Account Settings',
            'description': 'User profile settings with tabbed sections (General, Account, Appearance, Notifications) and form fields.',
            'href': url_for('basecoat_examples.profile'),
            'tags': ['Tabs', 'Forms', 'Cards', 'Avatar']
        },
        {
            'id': 'projects',
            'title': 'Projects List',
            'description': 'Card grid of active deliverables with progress bars, team avatar stacks, and status badges.',
            'href': url_for('basecoat_examples.projects'),
            'tags': ['Cards', 'Dropdown', 'Progress', 'Badges']
        },
        {
            'id': 'changelog',
            'title': 'Product Changelog',
            'description': 'Chronological product release notes with semantic version tags, feature badges, and enhancement lists.',
            'href': url_for('basecoat_examples.changelog'),
            'tags': ['Timeline', 'Badges', 'Cards']
        },
        {
            'id': 'coming-soon',
            'title': 'Coming Soon & Waitlist',
            'description': 'Hero countdown timer with email waitlist collection form and feature teaser cards.',
            'href': url_for('basecoat_examples.coming_soon'),
            'tags': ['Hero', 'Countdown', 'Forms']
        },
        {
            'id': 'blog',
            'title': 'Blog & Article Feed',
            'description': 'Publication layout with featured article hero, category pills, trending sidebar, and recent post cards.',
            'href': url_for('basecoat_examples.blog'),
            'tags': ['Cards', 'Badges', 'Grid']
        },
        {
            'id': 'onboarding',
            'title': 'Onboarding Wizard',
            'description': 'Multi-step guided onboarding card with progress indicators, account tier selector, and governance toggles.',
            'href': url_for('basecoat_examples.onboarding'),
            'tags': ['Cards', 'Forms', 'Wizard']
        },
        {
            'id': 'chat',
            'title': 'Chat Application',
            'description': 'Full-featured messaging interface with channel search, active status badges, interleaved chat bubbles, and composer.',
            'href': url_for('basecoat_examples.chat'),
            'tags': ['Chat', 'Badges', 'Buttons']
        },
        {
            'id': 'ai-chat',
            'title': 'AI Prompt Interface',
            'description': 'Copilot conversational interface with prompt suggestion cards, assistant stream bubbles, and token badges.',
            'href': url_for('basecoat_examples.ai_chat'),
            'tags': ['AI', 'Cards', 'Badges']
        },
        {
            'id': 'playground',
            'title': 'LLM Playground',
            'description': 'Interactive model inference workbench with hyperparameter tuning sliders, prompt canvas, and stop sequences.',
            'href': url_for('basecoat_examples.playground'),
            'tags': ['Playground', 'Tabs', 'Sliders']
        },
        {
            'id': 'product-list',
            'title': 'Product Catalog',
            'description': 'E-commerce hardware directory with multi-facet filters, sorting controls, price badges, and card grid.',
            'href': url_for('basecoat_examples.product_list'),
            'tags': ['E-Commerce', 'Cards', 'Badges']
        },
        {
            'id': 'product-detail',
            'title': 'Product Detail Page',
            'description': 'Comprehensive product showcase with thumbnail gallery, spec data table, finish selector, and cart CTA.',
            'href': url_for('basecoat_examples.product_detail'),
            'tags': ['Table', 'Badges', 'Gallery']
        },
        {
            'id': 'kanban',
            'title': 'Kanban Project Board',
            'description': 'Agile sprint task board with Backlog, Todo, In Progress, Done columns and priority tag badges.',
            'href': url_for('basecoat_examples.kanban'),
            'tags': ['Kanban', 'Cards', 'Badges']
        }
    ]
    return render_template('examples/index.html', examples=examples_list)


@examples_bp.route('/authentication', methods=['GET', 'POST'])
def authentication():
    """Shadcn Authentication screen."""
    form = AuthForm(request.form)
    if request.method == 'POST' and form.validate():
        flash(f"Sign-in link dispatched to {form.email.data}!", "success")
        return redirect(url_for('basecoat_examples.authentication'))
    return render_template('examples/authentication.html', form=form)


@examples_bp.route('/dashboard')
def dashboard():
    """Shadcn Admin Dashboard screen."""
    kpi_cards = [
        {
            'title': 'Total Revenue',
            'value': '$45,231.89',
            'change': '+20.1% from last month',
            'icon': 'dollar-sign'
        },
        {
            'title': 'Subscriptions',
            'value': '+2,350',
            'change': '+180.1% from last month',
            'icon': 'users'
        },
        {
            'title': 'Sales',
            'value': '+12,234',
            'change': '+19% from last month',
            'icon': 'credit-card'
        },
        {
            'title': 'Active Now',
            'value': '+573',
            'change': '+201 since last hour',
            'icon': 'activity'
        }
    ]

    recent_sales = [
        {'name': 'Olivia Martin', 'email': 'olivia.martin@email.com', 'amount': '+$1,999.00', 'initials': 'OM'},
        {'name': 'Jackson Lee', 'email': 'jackson.lee@email.com', 'amount': '+$39.00', 'initials': 'JL'},
        {'name': 'Isabella Nguyen', 'email': 'isabella.nguyen@email.com', 'amount': '+$299.00', 'initials': 'IN'},
        {'name': 'William Kim', 'email': 'will@email.com', 'amount': '+$99.00', 'initials': 'WK'},
        {'name': 'Sofia Davis', 'email': 'sofia.davis@email.com', 'amount': '+$39.00', 'initials': 'SD'}
    ]

    return render_template('examples/dashboard.html', kpi_cards=kpi_cards, recent_sales=recent_sales)


@examples_bp.route('/tasks')
def tasks():
    """Shadcn Tasks Data Table screen."""
    import json, os
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'tasks.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_tasks = json.load(f)
            task_items = []
            for t in raw_tasks:
                st = t.get('status', 'todo').lower()
                st_norm = st.replace(' ', '-')
                task_items.append({
                    'code': t.get('id', ''),
                    'title': t.get('title', ''),
                    'status': st_norm,
                    'status_label': t.get('status', '').title(),
                    'priority': t.get('priority', 'medium').lower(),
                    'label': t.get('label', 'feature')
                })
        except Exception:
            task_items = []
    else:
        task_items = []

    if not task_items:
        task_items = [
            {'code': 'TASK-8782', 'title': "You can't compress the program without quantifying the open-source SSD pixel!", 'status': 'in-progress', 'status_label': 'In Progress', 'priority': 'medium', 'label': 'documentation'},
            {'code': 'TASK-7878', 'title': 'Try to calculate the EXE feed, maybe it will index the multi-byte pixel!', 'status': 'backlog', 'status_label': 'Backlog', 'priority': 'medium', 'label': 'documentation'},
            {'code': 'TASK-7839', 'title': 'We need to bypass the neural TCP card!', 'status': 'todo', 'status_label': 'Todo', 'priority': 'high', 'label': 'bug'}
        ]

    return render_template('examples/tasks.html', tasks=task_items)


@examples_bp.route('/pricing')
def pricing():
    """Shadcn Pricing Tables screen."""
    return render_template('examples/pricing.html')


@examples_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """Shadcn Profile & Settings screen."""
    form = ProfileForm(request.form)
    if request.method == 'POST' and form.validate():
        flash("Profile settings saved successfully!", "success")
        return redirect(url_for('basecoat_examples.profile'))
    return render_template('examples/profile.html', form=form)


@examples_bp.route('/projects')
def projects():
    """Shadcn Projects List screen."""
    project_items = [
        {
            'title': 'Mobile Banking Redesign',
            'subtitle': 'iOS & Android Native App',
            'progress': 78,
            'time_left': '1 week left',
            'date': 'May 01, 2026',
            'status': 'In Progress',
            'icon': '📱',
            'team': ['JD', 'OM', 'SD']
        },
        {
            'title': 'Architecture Governance Portal',
            'subtitle': 'Entelim ArchiMate 3.2 Engine',
            'progress': 92,
            'time_left': '3 days left',
            'date': 'June 04, 2026',
            'status': 'Review',
            'icon': '🏛️',
            'team': ['JD', 'WK']
        },
        {
            'title': 'Design Token CI Pipeline',
            'subtitle': 'Tailwind & Basecoat CSS Integration',
            'progress': 100,
            'time_left': 'Completed',
            'date': 'Oct 27, 2026',
            'status': 'Done',
            'icon': '🎨',
            'team': ['JL', 'IN', 'OM']
        },
        {
            'title': 'Enterprise SSO & IAM Bridge',
            'subtitle': 'Okta, SAML 2.0 & OIDC Claim Sync',
            'progress': 45,
            'time_left': '4 weeks left',
            'date': 'Nov 15, 2026',
            'status': 'In Progress',
            'icon': '🔒',
            'team': ['WK', 'SD']
        },
        {
            'title': 'Microservices Telemetry Mesh',
            'subtitle': 'OpenTelemetry & Prometheus Ingestion',
            'progress': 60,
            'time_left': '2 weeks left',
            'date': 'Dec 02, 2026',
            'status': 'In Progress',
            'icon': '⚡',
            'team': ['JD', 'OM', 'JL']
        },
        {
            'title': 'Customer Self-Serve Billing Portal',
            'subtitle': 'Stripe Connect & Invoice Automation',
            'progress': 25,
            'time_left': '6 weeks left',
            'date': 'Dec 20, 2026',
            'status': 'Backlog',
            'icon': '💳',
            'team': ['SD', 'IN']
        }
    ]
    return render_template('examples/projects.html', projects=project_items)


@examples_bp.route('/changelog')
def changelog():
    """Shadcn Product Changelog screen."""
    changelog_entries = [
        {
            'version': 'v1.2.0',
            'date': 'Oct 23, 2026',
            'summary': 'Full architectural alignment with shadcn/ui and Basecoat UI upstream engine. Introduced semantic cards, dialog zoom transitions, Inter typography tokens, and WTForms error rings.',
            'tags': [
                {'name': 'Major Release', 'variant': 'default'},
                {'name': 'UI Engine', 'variant': 'secondary'}
            ],
            'improvements': [
                'Aligned button, card, and dialog macro DOM structure with Basecoat CSS selectors.',
                'Integrated Inter font family for crisp, genuine shadcn aesthetics on all operating systems.',
                'Implemented caller slot composability for data tables and dialog action footers.'
            ],
            'fixes': [
                'Resolved dialog centering bug by enclosing content in a single modal container wrapper.',
                'Fixed WTForms container class to bind native .field destructive ring selectors.'
            ]
        },
        {
            'version': 'v1.1.0',
            'date': 'Oct 15, 2026',
            'summary': 'Packaged flask-basecoat as an installable Python module with automated anti-drift CI ratchets and WTForms adapters.',
            'tags': [
                {'name': 'Governance', 'variant': 'secondary'},
                {'name': 'Packaging', 'variant': 'outline'}
            ],
            'improvements': [
                'Added pyproject.toml and setuptools build support.',
                'Implemented check_raw_components.py CI ratchet locking baseline raw tag counts.'
            ],
            'fixes': [
                'Fixed setuptools 84+ pkg_resources compatibility in virtual environment.'
            ]
        },
        {
            'version': 'v1.0.0',
            'date': 'Oct 01, 2026',
            'summary': 'Initial release of flask-basecoat boilerplate with Basecoat UI and Tailwind CSS.',
            'tags': [
                {'name': 'Initial Release', 'variant': 'secondary'}
            ],
            'improvements': [
                'Replaced obsolete Semantic UI with Basecoat UI and Tailwind utility classes.',
                'Modernized Python dependencies to Python 3.11+.'
            ]
        }
    ]
    return render_template('examples/changelog.html', changelog=changelog_entries)


@examples_bp.route('/coming-soon', methods=['GET', 'POST'])
def coming_soon():
    """Shadcn Coming Soon screen."""
    if request.method == 'POST':
        email = request.form.get('email', '')
        if email:
            flash(f"You have been added to the waitlist ({email})!", "success")
            return redirect(url_for('basecoat_examples.coming_soon'))
    return render_template('examples/coming_soon.html')


@examples_bp.route('/blog')
def blog():
    """Shadcn Blog & Articles screen."""
    return render_template('examples/blog.html')


@examples_bp.route('/onboarding')
def onboarding():
    """Shadcn Onboarding Flow screen."""
    return render_template('examples/onboarding.html')


@examples_bp.route('/chat')
def chat():
    """Shadcn Chat Messenger screen."""
    return render_template('examples/chat.html')


@examples_bp.route('/ai-chat')
def ai_chat():
    """Shadcn AI Prompt Assistant screen."""
    return render_template('examples/ai_chat.html')


@examples_bp.route('/playground')
def playground():
    """Shadcn LLM Playground screen."""
    return render_template('examples/playground.html')


@examples_bp.route('/product-list')
def product_list():
    """Shadcn Product Catalog screen."""
    return render_template('examples/product_list.html')


@examples_bp.route('/product-detail')
def product_detail():
    """Shadcn Product Detail Page screen."""
    return render_template('examples/product_detail.html')


@examples_bp.route('/kanban')
def kanban():
    """Shadcn Kanban Project Board screen."""
    return render_template('examples/kanban.html')
