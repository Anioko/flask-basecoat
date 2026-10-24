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
        # --- 10 Core Application Blocks (Entelim Canonical) ---
        {
            'id': 'dashboard',
            'title': 'Admin Dashboard',
            'description': 'Executive dashboard with KPI metric cards, tabbed overview charts, and recent sales transaction feeds.',
            'href': url_for('basecoat_examples.dashboard'),
            'tags': ['Core Block', 'Cards', 'Tabs', 'Badges']
        },
        {
            'id': 'tasks',
            'title': 'Tasks & Data Table',
            'description': 'Interactive task management data table with search, status facet badges, priority icons, and row actions.',
            'href': url_for('basecoat_examples.tasks'),
            'tags': ['Core Block', 'Table', 'Popover', 'Input']
        },
        {
            'id': 'task-detail',
            'title': 'Record Detail View',
            'description': 'Deep record inspection view with priority badges, checklist progress tracker, and activity comments log.',
            'href': url_for('basecoat_examples.task_detail'),
            'tags': ['Core Block', 'Checklist', 'Comments', 'Badges']
        },
        {
            'id': 'add-product',
            'title': 'Record Form',
            'description': 'Comprehensive multi-field record creation form with media drag-and-drop, variations, and pricing.',
            'href': url_for('basecoat_examples.add_product'),
            'tags': ['Core Block', 'Forms', 'Media', 'Pricing']
        },
        {
            'id': 'profile',
            'title': 'Settings & Profile',
            'description': 'User profile and account settings with native Basecoat tabs (Personal, Account, Security, Notifications).',
            'href': url_for('basecoat_examples.profile'),
            'tags': ['Core Block', 'Tabs', 'Forms', 'Avatar']
        },
        {
            'id': 'chat',
            'title': 'Chat Application',
            'description': 'Full-featured messaging interface with channel search, active status badges, interleaved chat bubbles, and composer.',
            'href': url_for('basecoat_examples.chat'),
            'tags': ['Core Block', 'Chat', 'Badges', 'Buttons']
        },
        {
            'id': 'kanban',
            'title': 'Kanban Project Board',
            'description': 'Agile sprint task board with Backlog, Todo, In Progress, Done columns and priority tag badges.',
            'href': url_for('basecoat_examples.kanban'),
            'tags': ['Core Block', 'Kanban', 'Cards', 'Badges']
        },
        {
            'id': 'onboarding',
            'title': 'Onboarding Wizard',
            'description': 'Multi-step guided onboarding card with progress indicators, account tier selector, and governance toggles.',
            'href': url_for('basecoat_examples.onboarding'),
            'tags': ['Core Block', 'Wizard', 'Cards', 'Forms']
        },
        {
            'id': 'pricing',
            'title': 'Pricing Tables',
            'description': 'Transparent tier comparison cards, feature checklists, and billing frequency toggles.',
            'href': url_for('basecoat_examples.pricing'),
            'tags': ['Core Block', 'Cards', 'Badges', 'Buttons']
        },
        {
            'id': 'authentication',
            'title': 'Authentication',
            'description': 'Split-screen authentication screen with hero branding, email input, social OAuth, and terms.',
            'href': url_for('basecoat_examples.authentication'),
            'tags': ['Core Block', 'Forms', 'Buttons', 'Layout']
        },

        # --- Workspace & Security Companions ---
        {
            'id': 'two-factor',
            'title': 'Two-Step Verification',
            'description': 'Two-factor authentication (2FA) verification screen with 6-digit OTP code input, countdown, and resend trigger.',
            'href': url_for('basecoat_examples.two_factor'),
            'tags': ['Security', 'Auth', 'Forms']
        },
        {
            'id': 'notifications',
            'title': 'Notifications Center',
            'description': 'Centralized user notification feed with All/Unread/Mentions filter tabs, unread indicators, and mark-all-as-read.',
            'href': url_for('basecoat_examples.notifications'),
            'tags': ['Notifications', 'Tabs', 'Badges']
        },
        {
            'id': 'mail',
            'title': 'Mail Application',
            'description': 'Triple-panel desktop email client with mailbox folders, searchable message list, reading pane, and reply composer.',
            'href': url_for('basecoat_examples.mail'),
            'tags': ['Mail', 'Resizable', 'Search', 'Tabs']
        },
        {
            'id': 'calendar',
            'title': 'Event Calendar',
            'description': 'Monthly schedule grid with color-categorized event pills, month navigator, and interactive event modal.',
            'href': url_for('basecoat_examples.calendar'),
            'tags': ['Calendar', 'Modal', 'Badges']
        },
        {
            'id': 'file-manager',
            'title': 'File Manager',
            'description': 'Cloud drive file browser with storage usage breakdown, folder cards, and searchable files table.',
            'href': url_for('basecoat_examples.file_manager'),
            'tags': ['Files', 'Table', 'Progress', 'Cards']
        },
        {
            'id': 'changelog',
            'title': 'Product Changelog',
            'description': 'Chronological product release notes with semantic version tags, feature badges, and enhancement lists.',
            'href': url_for('basecoat_examples.changelog'),
            'tags': ['Timeline', 'Badges', 'Cards']
        },
        {
            'id': 'blog',
            'title': 'Blog & Article Feed',
            'description': 'Publication layout with featured article hero, category pills, trending sidebar, and recent post cards.',
            'href': url_for('basecoat_examples.blog'),
            'tags': ['Cards', 'Badges', 'Grid']
        },
        {
            'id': 'blog-detail',
            'title': 'Blog Post Detail',
            'description': 'Editorial long-form publication view with author byline, hero media, blockquotes, social share, and reader comments.',
            'href': url_for('basecoat_examples.blog_detail'),
            'tags': ['Blog', 'Typography', 'Comments']
        },
        {
            'id': 'shopping-cart',
            'title': 'Shopping Cart',
            'description': 'Multi-item e-commerce shopping bag with quantity stepper, coupon applicator, gift wrap toggle, and price breakdown.',
            'href': url_for('basecoat_examples.shopping_cart'),
            'tags': ['E-Commerce', 'Cart', 'Forms', 'Cards']
        },
        {
            'id': 'checkout',
            'title': 'Checkout Page',
            'description': 'Multi-step checkout with delivery/pickup selector, shipping address form, and live order summary.',
            'href': url_for('basecoat_examples.checkout'),
            'tags': ['E-Commerce', 'Checkout', 'Forms', 'Wizard']
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
            'id': 'projects',
            'title': 'Projects List',
            'description': 'Card grid of active deliverables with progress bars, team avatar stacks, and status badges.',
            'href': url_for('basecoat_examples.projects'),
            'tags': ['Cards', 'Dropdown', 'Progress', 'Badges']
        },
        {
            'id': 'coming-soon',
            'title': 'Coming Soon & Waitlist',
            'description': 'Hero countdown timer with email waitlist collection form and feature teaser cards.',
            'href': url_for('basecoat_examples.coming_soon'),
            'tags': ['Hero', 'Countdown', 'Forms']
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
    """Shadcn Marketly E-Commerce Admin Dashboard screen."""
    kpi_cards = [
        {
            'title': 'Total Revenue',
            'value': '$48,920',
            'change': '+12.4%',
            'change_type': 'positive',
            'period': 'This Month',
            'icon': 'coins'
        },
        {
            'title': 'Orders',
            'value': '1,284',
            'change': '+6.1%',
            'change_type': 'positive',
            'period': 'This Month',
            'icon': 'shopping-bag'
        },
        {
            'title': 'Refunds',
            'value': '$1,260',
            'change': '-2.3%',
            'change_type': 'negative',
            'period': 'This Month',
            'icon': 'receipt'
        }
    ]

    customer_inquiries = [
        {
            'name': 'Hannah Reid',
            'avatar': 'https://randomuser.me/api/portraits/women/14.jpg',
            'message': 'Do you ship to Canada?',
            'time': '9 min ago',
            'unread': 3
        },
        {
            'name': 'Omar Haddad',
            'avatar': 'https://randomuser.me/api/portraits/men/52.jpg',
            'message': 'Where is my order #4821?',
            'time': '1 h ago',
            'unread': 0
        },
        {
            'name': 'Lina Park',
            'avatar': 'https://randomuser.me/api/portraits/women/61.jpg',
            'message': 'Can I exchange the size?',
            'time': '3 h ago',
            'unread': 0
        }
    ]

    best_sellers = [
        {'name': 'Linen Shirt', 'sold': '212 sold', 'price': '$48.00', 'icon': 'shirt'},
        {'name': 'Leather Tote', 'sold': '164 sold', 'price': '$96.00', 'icon': 'shopping-bag'},
        {'name': 'Wireless Earbuds', 'sold': '131 sold', 'price': '$79.00', 'icon': 'headphones'},
        {'name': 'Trail Sneakers', 'sold': '97 sold', 'price': '$112.00', 'icon': 'footprints'}
    ]

    inventory_items = [
        {'name': 'Canvas Cap', 'sku': 'CAP-5520', 'status': 'In Stock', 'status_type': 'emerald', 'stock': '210', 'price': '$24.00', 'icon': 'hard-hat'},
        {'name': 'Leather Tote', 'sku': 'TOT-2210', 'status': 'Low Stock', 'status_type': 'amber', 'stock': '9', 'price': '$96.00', 'icon': 'shopping-bag'},
        {'name': 'Linen Shirt', 'sku': 'LIN-1042', 'status': 'In Stock', 'status_type': 'emerald', 'stock': '320', 'price': '$48.00', 'icon': 'shirt'},
        {'name': 'Trail Sneakers', 'sku': 'SNK-4401', 'status': 'Out of Stock', 'status_type': 'destructive', 'stock': '0', 'price': '$112.00', 'icon': 'footprints'},
        {'name': 'Wireless Earbuds', 'sku': 'EAR-3307', 'status': 'In Stock', 'status_type': 'emerald', 'stock': '142', 'price': '$79.00', 'icon': 'headphones'},
        {'name': 'Wool Scarf', 'sku': 'SCF-6613', 'status': 'Low Stock', 'status_type': 'amber', 'stock': '6', 'price': '$36.00', 'icon': 'sparkles'}
    ]

    return render_template(
        'examples/dashboard.html',
        kpi_cards=kpi_cards,
        customer_inquiries=customer_inquiries,
        best_sellers=best_sellers,
        inventory_items=inventory_items
    )


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
            'title': 'Mobile App',
            'category': 'Prototyping',
            'progress': 78,
            'time_left': '1 week left',
            'color': 'orange',
            'icon': 'smartphone',
            'members': [
                {'name': 'Maya Chen', 'avatar': 'https://randomuser.me/api/portraits/women/44.jpg'},
                {'name': 'James Wilson', 'avatar': 'https://randomuser.me/api/portraits/men/32.jpg'},
                {'name': 'Sofia Rodriguez', 'avatar': 'https://randomuser.me/api/portraits/women/68.jpg'}
            ]
        },
        {
            'title': 'Design Learn Management System',
            'category': 'UI/UX Design',
            'progress': 32,
            'time_left': '2 weeks left',
            'color': 'blue',
            'icon': 'layout-dashboard',
            'members': [
                {'name': 'James Wilson', 'avatar': 'https://randomuser.me/api/portraits/men/32.jpg'},
                {'name': 'Sofia Rodriguez', 'avatar': 'https://randomuser.me/api/portraits/women/68.jpg'},
                {'name': 'Daniel Park', 'avatar': 'https://randomuser.me/api/portraits/men/15.jpg'}
            ]
        },
        {
            'title': 'Chat Mobile App',
            'category': 'Prototyping',
            'progress': 64,
            'time_left': '6 weeks left',
            'color': 'pink',
            'icon': 'message-circle',
            'members': [
                {'name': 'Maya Chen', 'avatar': 'https://randomuser.me/api/portraits/women/44.jpg'},
                {'name': 'Sofia Rodriguez', 'avatar': 'https://randomuser.me/api/portraits/women/68.jpg'},
                {'name': 'Emma Thompson', 'avatar': 'https://randomuser.me/api/portraits/women/32.jpg'}
            ]
        },
        {
            'title': 'Store Dashboard',
            'category': 'UI/UX Design',
            'progress': 45,
            'time_left': '3 weeks left',
            'color': 'green',
            'icon': 'chart-column',
            'members': [
                {'name': 'James Wilson', 'avatar': 'https://randomuser.me/api/portraits/men/32.jpg'},
                {'name': 'Daniel Park', 'avatar': 'https://randomuser.me/api/portraits/men/15.jpg'},
                {'name': 'Emma Thompson', 'avatar': 'https://randomuser.me/api/portraits/women/32.jpg'}
            ]
        },
        {
            'title': 'NFT Marketplace App',
            'category': 'Prototyping',
            'progress': 69,
            'time_left': '4 weeks left',
            'color': 'red',
            'icon': 'palette',
            'members': [
                {'name': 'Maya Chen', 'avatar': 'https://randomuser.me/api/portraits/women/44.jpg'},
                {'name': 'Sofia Rodriguez', 'avatar': 'https://randomuser.me/api/portraits/women/68.jpg'}
            ]
        },
        {
            'title': 'Mobile App Redesign',
            'category': 'Prototyping',
            'progress': 56,
            'time_left': '2 weeks left',
            'color': 'blue',
            'icon': 'smartphone',
            'members': [
                {'name': 'James Wilson', 'avatar': 'https://randomuser.me/api/portraits/men/32.jpg'},
                {'name': 'Daniel Park', 'avatar': 'https://randomuser.me/api/portraits/men/15.jpg'}
            ]
        },
        {
            'title': 'Learning Platform Web',
            'category': 'UI/UX Design',
            'progress': 82,
            'time_left': '1 week left',
            'color': 'yellow',
            'icon': 'graduation-cap',
            'members': [
                {'name': 'Maya Chen', 'avatar': 'https://randomuser.me/api/portraits/women/44.jpg'},
                {'name': 'Emma Thompson', 'avatar': 'https://randomuser.me/api/portraits/women/32.jpg'}
            ]
        },
        {
            'title': 'Fitness Tracker App',
            'category': 'Development',
            'progress': 91,
            'time_left': '3 days left',
            'color': 'emerald',
            'icon': 'activity',
            'members': [
                {'name': 'James Wilson', 'avatar': 'https://randomuser.me/api/portraits/men/32.jpg'},
                {'name': 'Daniel Park', 'avatar': 'https://randomuser.me/api/portraits/men/15.jpg'},
                {'name': 'Sofia Rodriguez', 'avatar': 'https://randomuser.me/api/portraits/women/68.jpg'}
            ]
        }
    ]
    return render_template('examples/projects.html', projects=project_items)


@examples_bp.route('/changelog')
def changelog():
    """Shadcn Product Changelog screen."""
    changelog_entries = [
        {
            'version': '4.3.0',
            'date': 'Apr 2, 2025',
            'badges': [
                {'name': 'New Features', 'color': 'violet', 'icon': 'sparkles'},
                {'name': 'Improvements', 'color': 'blue', 'icon': 'zap'}
            ],
            'sections': [
                {
                    'title': 'New Features',
                    'color': 'violet',
                    'icon': 'sparkles',
                    'items': [
                        'Introduced an AI-powered search bar with semantic query understanding.',
                        'Added real-time collaboration — multiple users can now edit dashboards simultaneously.',
                        'New chart types: Waterfall, Funnel, and Sankey diagrams.'
                    ]
                },
                {
                    'title': 'Improvements',
                    'color': 'blue',
                    'icon': 'zap',
                    'items': [
                        'Redesigned the onboarding flow with interactive step-by-step guidance.',
                        'Dashboard loading time reduced by 40% through lazy rendering.'
                    ]
                }
            ]
        },
        {
            'version': '4.2.92',
            'date': 'Mar 22, 2025',
            'badges': [
                {'name': 'Improvements', 'color': 'blue', 'icon': 'zap'},
                {'name': 'Security', 'color': 'emerald', 'icon': 'shield-check'},
                {'name': 'Bug Fixes', 'color': 'rose', 'icon': 'bug'}
            ],
            'sections': [
                {
                    'title': 'Improvements',
                    'color': 'blue',
                    'icon': 'zap',
                    'items': [
                        'Improved tooltip UI and keyboard navigation in settings panels.',
                        'New bulk-action toolbar in the user management table.'
                    ]
                },
                {
                    'title': 'Security',
                    'color': 'emerald',
                    'icon': 'shield-check',
                    'items': [
                        'Added SAML request signing support for enterprise SSO providers.',
                        'Enabled SAML encrypted assertion claims.'
                    ]
                },
                {
                    'title': 'Bug Fixes',
                    'color': 'rose',
                    'icon': 'bug',
                    'items': [
                        'Fixed a race condition causing duplicate webhook deliveries.',
                        'Resolved layout shift on initial page load in Safari.'
                    ]
                }
            ]
        },
        {
            'version': '4.2.88',
            'date': 'Mar 15, 2025',
            'badges': [
                {'name': 'Improvements', 'color': 'blue', 'icon': 'zap'},
                {'name': 'Bug Fixes', 'color': 'rose', 'icon': 'bug'}
            ],
            'sections': [
                {
                    'title': 'Improvements',
                    'color': 'blue',
                    'icon': 'zap',
                    'items': [
                        'Enhanced dashboard loading performance with incremental data fetching.',
                        'New advanced filtering options for the user management view.'
                    ]
                },
                {
                    'title': 'Bug Fixes',
                    'color': 'rose',
                    'icon': 'bug',
                    'items': [
                        'Fixed report generation failing silently for datasets over 50k rows.',
                        'Resolved minor UI glitches on small-screen mobile devices.',
                        'Corrected incorrect timezone conversion in scheduled report emails.'
                    ]
                }
            ]
        },
        {
            'version': '4.2.85',
            'date': 'Mar 8, 2025',
            'badges': [
                {'name': 'New Features', 'color': 'violet', 'icon': 'sparkles'},
                {'name': 'Bug Fixes', 'color': 'rose', 'icon': 'bug'}
            ],
            'sections': [
                {
                    'title': 'New Features',
                    'color': 'violet',
                    'icon': 'sparkles',
                    'items': [
                        'Dark mode support across the entire application.',
                        'Customizable notification preferences per workspace.',
                        'CSV and PDF export for all data tables.'
                    ]
                },
                {
                    'title': 'Bug Fixes',
                    'color': 'rose',
                    'icon': 'bug',
                    'items': [
                        'Fixed broken pagination on the audit log screen.'
                    ]
                }
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
    hero_post = {
        'title': 'Mastering UI Elements: A Practical Guide for Designers',
        'badge': 'Business',
        'image': 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1200&q=80'
    }
    featured_posts = [
        {
            'title': 'Revolutionizing industries through SaaS implementation',
            'read_time': '10 min',
            'image': 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=600&q=80'
        },
        {
            'title': 'Synergizing saas and UX design for elevating digital experiences',
            'read_time': '8 min',
            'image': 'https://images.unsplash.com/photo-1559028012-481c04fa702d?auto=format&fit=crop&w=600&q=80'
        },
        {
            'title': 'Navigating saas waters with intuitive UI and UX',
            'read_time': '9 min',
            'image': 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=600&q=80'
        },
        {
            'title': 'Sculpting saas success - the art of UI and UX design',
            'read_time': '4 min',
            'image': 'https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=600&q=80'
        },
        {
            'title': 'Transforming saas platforms - a UI/UX design odyssey',
            'read_time': '12 min',
            'image': 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80'
        }
    ]
    recent_posts = [
        {
            'title': 'Mastering UI Elements: A Practical Guide for Designers',
            'snippet': 'Dive into the world of user interfaces with our expert guides, latest trends, and practical tips.',
            'author': 'Jennifer Taylor',
            'avatar': 'https://i.pravatar.cc/48?img=5',
            'read_time': '3 min read',
            'image': 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=600&q=80'
        },
        {
            'title': 'Crafting Seamless Experiences: The Art of Intuitive UI Design',
            'snippet': 'Explore the principles and techniques that drive user-centric UI design, ensuring a seamless and intuitive experience for your audience.',
            'author': 'Jennifer Taylor',
            'avatar': 'https://i.pravatar.cc/48?img=5',
            'read_time': '5 min read',
            'image': 'https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=600&q=80'
        },
        {
            'title': 'Beyond Aesthetics: The Power of Emotional UX Design',
            'snippet': 'Delve into the realm of emotional design and discover how incorporating empathy and psychological insights can elevate user experiences.',
            'author': 'Ryan A.',
            'avatar': 'https://i.pravatar.cc/48?img=12',
            'read_time': '2 min read',
            'image': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=600&q=80'
        }
    ]
    return render_template(
        'examples/blog.html',
        hero_post=hero_post,
        featured_posts=featured_posts,
        recent_posts=recent_posts
    )


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
    products = [
        {
            'id': 1,
            'title': 'iPhone 14 Pro Max 256GB Space Black',
            'price': '$999.00',
            'old_price': '$1299.00',
            'discount': '-23%',
            'rating': '4.8',
            'orders': '234',
            'delivery': 'Tomorrow',
            'is_new': True,
            'image': 'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400&h=300&q=80&fit=crop',
            'category': 'phones',
            'brand': 'apple'
        },
        {
            'id': 2,
            'title': 'Samsung Galaxy S23 Ultra 512GB',
            'price': '$899.00',
            'old_price': '$1199.00',
            'discount': '-25%',
            'rating': '4.7',
            'orders': '189',
            'delivery': '2 days',
            'is_new': True,
            'image': 'https://images.unsplash.com/photo-1610945264803-c22b62831454?w=400&h=300&q=80&fit=crop',
            'category': 'phones',
            'brand': 'samsung'
        },
        {
            'id': 3,
            'title': 'Huawei P50 Pro 128GB Golden',
            'price': '$699.00',
            'old_price': '$899.00',
            'discount': '-22%',
            'rating': '4.5',
            'orders': '154',
            'delivery': '3 days',
            'is_new': False,
            'image': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&q=80&fit=crop',
            'category': 'phones',
            'brand': 'huawei'
        },
        {
            'id': 4,
            'title': 'Sony WH-1000XM5 Wireless Headphones',
            'price': '$299.00',
            'old_price': '$399.00',
            'discount': '-25%',
            'rating': '4.9',
            'orders': '456',
            'delivery': 'Tomorrow',
            'is_new': True,
            'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&q=80&fit=crop',
            'category': 'headsets',
            'brand': 'sony'
        },
        {
            'id': 5,
            'title': 'Bose QuietComfort 45 Headphones',
            'price': '$249.00',
            'old_price': None,
            'discount': None,
            'rating': '4.6',
            'orders': '321',
            'delivery': '2 days',
            'is_new': False,
            'image': 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=400&h=300&q=80&fit=crop',
            'category': 'headsets',
            'brand': 'bose'
        },
        {
            'id': 6,
            'title': 'MacBook Pro 16" M2 Pro 512GB Space Gray',
            'price': '$1999.00',
            'old_price': '$2499.00',
            'discount': '-20%',
            'rating': '4.9',
            'orders': '112',
            'delivery': 'Tomorrow',
            'is_new': False,
            'image': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400&h=300&q=80&fit=crop',
            'category': 'laptops',
            'brand': 'apple'
        },
        {
            'id': 7,
            'title': 'Dell XPS 15 9530 i7 1TB',
            'price': '$1499.00',
            'old_price': '$1799.00',
            'discount': '-16%',
            'rating': '4.6',
            'orders': '89',
            'delivery': 'Within 7 days',
            'is_new': False,
            'image': 'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=400&h=300&q=80&fit=crop',
            'category': 'laptops',
            'brand': 'dell'
        },
        {
            'id': 8,
            'title': 'Microsoft Surface Laptop 5 15"',
            'price': '$1299.00',
            'old_price': None,
            'discount': None,
            'rating': '4.5',
            'orders': '76',
            'delivery': 'Tomorrow',
            'is_new': False,
            'image': 'https://images.unsplash.com/photo-1611186871525-9b90e2e48fde?w=400&h=300&q=80&fit=crop',
            'category': 'laptops',
            'brand': 'microsoft'
        },
        {
            'id': 9,
            'title': 'LG C3 55" 4K OLED evo TV',
            'price': '$1199.00',
            'old_price': '$1499.00',
            'discount': '-20%',
            'rating': '4.8',
            'orders': '64',
            'delivery': 'Within 7 days',
            'is_new': True,
            'image': 'https://images.unsplash.com/photo-1593359677879-a4bb92f829e1?w=400&h=300&q=80&fit=crop',
            'category': 'tv',
            'brand': 'lg'
        },
        {
            'id': 10,
            'title': 'Samsung 65" QN90C Neo QLED 4K TV',
            'price': '$1599.00',
            'old_price': None,
            'discount': None,
            'rating': '4.7',
            'orders': '53',
            'delivery': 'Within 7 days',
            'is_new': False,
            'image': 'https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=400&h=300&q=80&fit=crop',
            'category': 'tv',
            'brand': 'samsung'
        },
        {
            'id': 11,
            'title': 'JBL Charge 5 Portable Bluetooth Speaker',
            'price': '$179.00',
            'old_price': None,
            'discount': None,
            'rating': '4.8',
            'orders': '512',
            'delivery': 'Today',
            'is_new': False,
            'image': 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=300&q=80&fit=crop',
            'category': 'sound',
            'brand': 'jbl'
        },
        {
            'id': 12,
            'title': 'Apple Watch Series 9 GPS 45mm Midnight',
            'price': '$399.00',
            'old_price': None,
            'discount': None,
            'rating': '4.9',
            'orders': '342',
            'delivery': 'Today',
            'is_new': True,
            'image': 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400&h=300&q=80&fit=crop',
            'category': 'watches',
            'brand': 'apple'
        }
    ]
    return render_template('examples/product_list.html', products=products)


@examples_bp.route('/product-detail')
def product_detail():
    """Shadcn Product Detail Page screen."""
    return render_template('examples/product_detail.html')


@examples_bp.route('/kanban')
def kanban():
    """Shadcn Kanban Project Board screen."""
    return render_template('examples/kanban.html')

@examples_bp.route('/shopping-cart')
def shopping_cart():
    """Shadcn Shopping Cart screen."""
    return render_template('examples/shopping_cart.html')


@examples_bp.route('/checkout')
def checkout():
    """Shadcn Checkout Page screen."""
    return render_template('examples/checkout.html')


@examples_bp.route('/add-product')
def add_product():
    """Shadcn Add Product Form screen."""
    return render_template('examples/add_product.html')


@examples_bp.route('/mail')
def mail():
    """Shadcn Mail Application screen."""
    return render_template('examples/mail.html')


@examples_bp.route('/calendar')
def calendar():
    """Shadcn Event Calendar screen."""
    return render_template('examples/calendar.html')


@examples_bp.route('/file-manager')
def file_manager():
    """Shadcn File Manager screen."""
    return render_template('examples/file_manager.html')


@examples_bp.route('/two-factor')
def two_factor():
    """Shadcn Two-Step Verification screen."""
    return render_template('examples/two_factor.html')


@examples_bp.route('/task-detail')
def task_detail():
    """Shadcn Task Detail screen."""
    return render_template('examples/task_detail.html')


@examples_bp.route('/blog-detail')
def blog_detail():
    """Shadcn Blog Post Detail screen."""
    return render_template('examples/blog_detail.html')


@examples_bp.route('/notifications')
def notifications():
    """Shadcn Notifications Center screen."""
    return render_template('examples/notifications.html')
