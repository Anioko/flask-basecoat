"""
flask_basecoat.examples:
Showcase blueprint demonstrating real-world applications ported from shadcn-examples.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from wtforms import Form, StringField, validators

examples_bp = Blueprint(
    'basecoat_examples',
    __name__,
    template_folder='templates',
    static_folder='static'
)


class AuthForm(Form):
    email = StringField('Email', [validators.Email(), validators.InputRequired()])


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
    task_items = [
        {
            'code': 'TASK-8782',
            'title': "You can't compress the program without quantifying the open-source SSD pixel!",
            'status': 'in-progress',
            'status_label': 'In Progress',
            'priority': 'medium'
        },
        {
            'code': 'TASK-7878',
            'title': 'Try to calculate the EXE feed, maybe it will index the multi-byte pixel!',
            'status': 'backlog',
            'status_label': 'Backlog',
            'priority': 'medium'
        },
        {
            'code': 'TASK-7839',
            'title': 'We need to bypass the neural TCP card!',
            'status': 'todo',
            'status_label': 'Todo',
            'priority': 'high'
        },
        {
            'code': 'TASK-5562',
            'title': 'The SAS interface is down, bypass the open-source pixel so we can back up the PNG bandwidth!',
            'status': 'backlog',
            'status_label': 'Backlog',
            'priority': 'medium'
        },
        {
            'code': 'TASK-8686',
            'title': "I'll parse the wireless SSL protocol, that should driver the API panel!",
            'status': 'canceled',
            'status_label': 'Canceled',
            'priority': 'medium'
        },
        {
            'code': 'TASK-1280',
            'title': 'Use the digital TLS panel, then you can transmit the haptic system!',
            'status': 'done',
            'status_label': 'Done',
            'priority': 'high'
        },
        {
            'code': 'TASK-7262',
            'title': 'The UTF8 array is down, navigate the neural transmitter so we can generate the RAM microchip!',
            'status': 'done',
            'status_label': 'Done',
            'priority': 'low'
        },
        {
            'code': 'TASK-1138',
            'title': "Generating the driver won't do anything, we need to index the open-source TCP microchip!",
            'status': 'in-progress',
            'status_label': 'In Progress',
            'priority': 'medium'
        },
        {
            'code': 'TASK-7184',
            'title': 'We need to program the back-end GB pixel!',
            'status': 'todo',
            'status_label': 'Todo',
            'priority': 'low'
        },
        {
            'code': 'TASK-5160',
            'title': "Calculating the bus won't do anything, we need to navigate the back-end JSON protocol!",
            'status': 'in-progress',
            'status_label': 'In Progress',
            'priority': 'high'
        }
    ]

    return render_template('examples/tasks.html', tasks=task_items)
