# Flask-Basecoat: Canonical shadcn/ui for Flask & Jinja2

A production-grade component system and application boilerplate that brings **shadcn/ui** aesthetics and ergonomics to **Flask** and **Jinja2**.

Powered by upstream [Basecoat UI](https://basecoatui.com/) (`basecoat-css`), `flask-basecoat` provides composable Jinja2 macros with caller slots, an automatic WTForms field adapter, tokenized HSL/oklch themes (Light & Dark), and an interactive component gallery.

---

## 📸 Visual Showcase

Explore the canonical components running in the live interactive gallery (`/basecoat/gallery`).

### 🌓 Desktop Gallery — Light & Dark Mode (1440px)

| Light Theme | Dark Theme |
| :---: | :---: |
| ![Flask-Basecoat Component Gallery - Light Mode](readme_media/gallery-light-1440.png) | ![Flask-Basecoat Component Gallery - Dark Mode](readme_media/gallery-dark-1440.png) |

---

### 📱 Responsive Mobile Layout & Native Dialog Modal

| Mobile Viewport (390px) | Native Accessible Modal Dialog (`<dialog>`) |
| :---: | :---: |
| ![Flask-Basecoat Mobile Gallery](readme_media/gallery-mobile-390.png) | ![Flask-Basecoat Accessible Dialog Modal](readme_media/dialog-modal.png) |

---

### 🛡️ WTForms Integration & Server-Side Validation State

Zero hand-written markup. The WTForms adapter automatically connects labels, help text, input validation rings, error summaries, and ARIA attributes:

![Flask-Basecoat WTForms Server-side Validation](readme_media/form-validation.png)

---

## 🚀 Ported shadcn/ui Application Suite (16 Live Production Screens)

Production application screens ported directly from official [shadcn-examples](https://github.com/shadcn-examples/shadcn-examples). Every screen is built 100% with canonical macros from `flask_basecoat/templates/basecoat/` and tokenized HSL CSS variables with dark mode support. Accessible at `/examples/`.

### 🧭 Application Directory (`/examples/`)
Interactive directory displaying all 16 ported applications categorized with badges and direct preview links:

![shadcn Application Directory](readme_media/examples-index-1440.png)

---

### Phase 1: Foundation Application Suite

| 1. Split-Screen Authentication (`/examples/authentication`) | 2. Executive Admin Dashboard (`/examples/dashboard`) |
| :---: | :---: |
| ![shadcn Authentication Screen](readme_media/examples-auth-1440.png) | ![shadcn Admin Dashboard](readme_media/examples-dashboard-1440.png) |
| *Split hero branding, customer testimonial, WTForms email input, and OAuth buttons.* | *KPI metric cards, monthly overview chart, tabbed analytics, and transaction feed.* |

| 3. Tasks & Data Management (`/examples/tasks`) |
| :---: |
| ![shadcn Tasks Data Table](readme_media/examples-tasks-1440.png) |
| *Data table toolbar, status facet badges, priority icons, and row actions dropdown.* |

---

### Phase 2: Core SaaS & Account Suite

| 4. Pricing Tables (`/examples/pricing`) | 5. Profile & Settings (`/examples/profile`) |
| :---: | :---: |
| ![shadcn Pricing Tables](readme_media/examples-pricing-1440.png) | ![shadcn Profile & Settings](readme_media/examples-profile-1440.png) |
| *Transparent tier comparison cards, feature checklists, and billing frequency toggles.* | *Account center with avatar header, WTForms inputs, tabbed preferences, and theme toggle.* |

| 6. Deliverable Projects List (`/examples/projects`) | 7. Product Changelog (`/examples/changelog`) |
| :---: | :---: |
| ![shadcn Projects List](readme_media/examples-projects-1440.png) | ![shadcn Product Changelog](readme_media/examples-changelog-1440.png) |
| *Deliverable card grid with progress bars, team avatar stacks, and status badges.* | *Release notes timeline with semantic version tags, feature badges, and bug fixes.* |

---

### Phase 3: Marketing & Conversion Flows

| 8. Coming Soon & Waitlist (`/examples/coming-soon`) | 9. Blog & Article Feed (`/examples/blog`) |
| :---: | :---: |
| ![shadcn Coming Soon](readme_media/examples-coming-soon-1440.png) | ![shadcn Blog & Article Feed](readme_media/examples-blog-1440.png) |
| *Countdown timer cards, waitlist email capture form, and feature teaser highlights.* | *Featured article hero, trending sidebar pills, and recent post card grid.* |

| 10. Multi-Step Onboarding Wizard (`/examples/onboarding`) |
| :---: |
| ![shadcn Onboarding Flow](readme_media/examples-onboarding-1440.png) |
| *Step progress stepper, account purpose cards, workspace inputs, and CI governance toggles.* |

---

### Phase 4: Interactive Applications

| 11. Team Chat Messenger (`/examples/chat`) | 12. AI Prompt Assistant (`/examples/ai-chat`) |
| :---: | :---: |
| ![shadcn Chat Application](readme_media/examples-chat-1440.png) | ![shadcn AI Prompt Assistant](readme_media/examples-ai-chat-1440.png) |
| *Channel sidebar, active status indicators, interleaved chat bubbles, and message composer.* | *Copilot greeting, 2x2 suggestion prompt cards, assistant stream bubbles, and prompt bar.* |

| 13. LLM Playground (`/examples/playground`) | 14. Hardware Product Catalog (`/examples/product-list`) |
| :---: | :---: |
| ![shadcn LLM Playground](readme_media/examples-playground-1440.png) | ![shadcn Product Catalog](readme_media/examples-product-list-1440.png) |
| *Dual-prompt canvas, model selector, temperature/max-token tuning sliders, and presets.* | *Hardware card grid, multi-facet brand filters, price slider, and sorting toolbar.* |

| 15. Product Detail Showcase (`/examples/product-detail`) | 16. Agile Kanban Sprint Board (`/examples/kanban`) |
| :---: | :---: |
| ![shadcn Product Detail](readme_media/examples-product-detail-1440.png) | ![shadcn Kanban Board](readme_media/examples-kanban-1440.png) |
| *Thumbnail gallery, specification data table, color finish swatches, and cart CTA.* | *Backlog, Todo, In Progress, Done columns with task cards, priority badges, and assignees.* |

---

## 💡 Why Flask-Basecoat?

Traditional Flask applications either hand-code raw HTML tags across dozens of templates (causing visual drift and accessibility regressions) or rely on heavy client-side JavaScript frameworks.

`flask-basecoat` takes a modern server-rendered approach:

1. **Wrap, Don't Re-invent**: [Basecoat UI](https://basecoatui.com/) is our CSS and micro-JS upstream. Focus traps, keyboard navigation, dialog backdrops, and dropdown positioning are solved upstream—no bespoke Alpine.js state machines to debug.
2. **Jinja2 Macros with Caller Slots**: Every component is a single macro call with standard arguments and caller slots for composable markup.
3. **Deep WTForms Integration**: `{{ bc.render_field(form.email) }}` inspects the WTForm field type, renders semantic labels, inputs, validation errors, and focus rings with zero template boilerplate.
4. **shadcn/ui Design Tokens**: 100% tokenized CSS variables matching shadcn/ui (`--primary`, `--background`, `--card`, `--destructive`, `--ring`, `--radius`), with full Dark mode support (`.dark`).
5. **Anti-Drift Governance**: Includes a CI ratchet script (`check_raw_components.py`) ensuring pages adopt canonical macros instead of raw `<button>` and `<input>` tags.

---

## 📦 Installation & Setup

### 1. Install as a Python Package

Install directly from Git or your local checkout:

```bash
pip install -e /path/to/flask-basecoat
# or from GitHub:
pip install git+https://github.com/Anioko/flask-basecoat.git
```

### 2. Initialize in your Flask Application

```python
from flask import Flask
from flask_basecoat import Basecoat

app = Flask(__name__)
basecoat = Basecoat(app)
```

The `Basecoat` extension automatically:
- Registers the `basecoat` static blueprint (`/static/basecoat/*`).
- Configures Jinja's `ChoiceLoader` so all `basecoat/*.html` templates are instantly importable by any template.
- Mounts the interactive gallery at `/basecoat/gallery` (in development mode or when explicitly enabled).

### 3. Include Assets in your Base Template

In your `layout.html` or `base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}My App{% endblock %}</title>

    {# Basecoat & Tailwind CSS assets #}
    {{ basecoat.css() }}
</head>
<body class="bg-background text-foreground antialiased min-h-screen">
    {% block content %}{% endblock %}

    {# Basecoat micro-JS #}
    {{ basecoat.js() }}
</body>
</html>
```

---

## 🧩 Component Catalog & Macro Usage

Import the canonical macros once at the top of any template:

```jinja2
{% import 'basecoat/index.html' as bc %}
```

Or import individual modules:
```jinja2
{% from 'basecoat/button.html' import button %}
{% from 'basecoat/form.html' import render_field, render_form %}
```

---

### 1. Button

Supports 6 shadcn variants (`default`, `secondary`, `destructive`, `outline`, `ghost`, `link`), 4 sizes (`sm`, `md`, `lg`, `icon`), and loading states.

```jinja2
{# Standard buttons #}
{{ bc.button('Save Changes', variant='default') }}
{{ bc.button('Cancel', variant='outline') }}
{{ bc.button('Delete Account', variant='destructive') }}

{# Icon button with caller slot #}
{% call bc.button(variant='ghost', size='icon') %}
    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
    </svg>
{% endcall %}

{# Link styled as button #}
{{ bc.button('Back to Dashboard', href=url_for('main.index'), variant='ghost') }}
```

---

### 2. Form & WTForms Adapter

Zero-boilerplate rendering for `Flask-WTF` forms with automatic validation error feedback, CSRF token handling, and focus rings:

```jinja2
{# Render entire WTForms form automatically #}
{{ bc.render_form(form, action=url_for('account.login'), submit_text='Sign In') }}

{# Or render fields individually with fine control #}
<form method="POST" action="">
    {{ form.hidden_tag() }}
    
    {{ bc.render_field(form.email, placeholder='user@company.com') }}
    {{ bc.render_field(form.password) }}
    {{ bc.render_field(form.remember_me) }}
    
    <div class="mt-4">
        {{ bc.button('Sign In', type='submit') }}
    </div>
</form>
```

---

### 3. Card

Composable container with header, title, description, content, and footer slots:

```jinja2
{% call bc.card(title='Account Settings', description='Manage your email preferences and security keys.') %}
    <div class="space-y-4">
        <p class="text-sm text-muted-foreground">Your primary email is verified.</p>
    </div>
    
    {% block card_footer %}
        {{ bc.button('Save Preferences') }}
    {% endblock %}
{% endcall %}
```

---

### 4. Badge

Semantic status indicators:

```jinja2
{{ bc.badge('Active', variant='default') }}
{{ bc.badge('Pending', variant='secondary') }}
{{ bc.badge('Failed', variant='destructive') }}
{{ bc.badge('Draft', variant='outline') }}
```

---

### 5. Dialog Modal

Accessible native HTML5 `<dialog>` component with trigger button, backdrop click dismissal, title, and action buttons:

```jinja2
{% call bc.dialog(id='invite-modal', trigger_text='Invite Teammate', title='Invite Team Member', description='Send an invitation link to collaborate.') %}
    <div class="py-4 space-y-3">
        <label class="text-sm font-medium">Email address</label>
        <input type="email" class="input w-full" placeholder="colleague@domain.com">
    </div>
    
    {% block dialog_footer %}
        {{ bc.button('Send Invite', type='button') }}
    {% endblock %}
{% endcall %}
```

---

### 6. Dropdown Menu

Keyboard-navigable dropdown menu with trigger slot and action items:

```jinja2
{% call bc.dropdown(id='actions-menu', trigger_text='Options') %}
    {{ bc.dropdown_item('Edit Details', href=url_for('main.index')) }}
    {{ bc.dropdown_item('Duplicate', href='#') }}
    <div class="my-1 border-t border-border"></div>
    {{ bc.dropdown_item('Delete', href='#', variant='destructive') }}
{% endcall %}
```

---

### 7. Tabs

Accessible tab navigation for switching content panels:

```jinja2
{% set tab_items = [
    {'id': 'overview', 'label': 'Overview', 'active': true},
    {'id': 'security', 'label': 'Security'},
    {'id': 'billing', 'label': 'Billing'}
] %}

{% call bc.tabs(id='account-tabs', items=tab_items) %}
    <div id="overview" class="tab-panel">Overview content...</div>
    <div id="security" class="tab-panel hidden">Security content...</div>
    <div id="billing" class="tab-panel hidden">Billing content...</div>
{% endcall %}
```

---

### 8. Data Table & Empty State

Accessible data tables with headers, zebra striping, and canonical empty states:

```jinja2
{% call bc.table() %}
    <thead>
        <tr>
            <th>User</th>
            <th>Role</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for user in users %}
        <tr>
            <td class="font-medium">{{ user.name }}</td>
            <td>{{ user.role }}</td>
            <td>{{ bc.badge('Active', variant='default') }}</td>
            <td>{{ bc.button('Edit', variant='ghost', size='sm') }}</td>
        </tr>
        {% else %}
        <tr>
            <td colspan="4">
                {{ bc.empty_state(
                    title='No team members found',
                    description='Get started by adding your first team member.',
                    action_text='Add Member',
                    action_href='#'
                ) }}
            </td>
        </tr>
        {% endfor %}
    </tbody>
{% endcall %}
```

---

### 9. Toast Notifications

Renders Flask flash messages (`get_flashed_messages(with_categories=true)`) with auto-dismiss animations and severity variants:

```jinja2
{# Include once in layout.html #}
{{ bc.toast_container() }}
```

In your Flask routes:
```python
flash("Changes saved successfully!", "success")
flash("Invalid credentials provided.", "error")
```

---

### 10. Skeleton Loader

Accessible placeholder shapes for async content:

```jinja2
<div class="space-y-3">
    {{ bc.skeleton(width='w-48', height='h-6') }}
    {{ bc.skeleton(width='w-full', height='h-4') }}
    {{ bc.skeleton(width='w-3/4', height='h-4') }}
</div>
```

---

## 🏛️ Anti-Drift CI Ratchet

To prevent codebases from regressing to raw HTML tags (`<button>`, `<input>`), `flask-basecoat` includes a strict CI ratchet check:

```bash
python scripts/ops/ci/check_raw_components.py
```

The ratchet verifies that the count of raw tags never exceeds the baseline established in `raw_components_baseline.json`. As templates are refactored to use `bc.*` macros, update the baseline with `--update`:

```bash
python scripts/ops/ci/check_raw_components.py --update
```

---

## 🧪 Testing

Run the automated test suite with pytest:

```bash
pytest tests/test_basecoat_macros.py tests/test_wtforms_adapter.py tests/test_basecoat_extension.py
```

All 21 unit and integration tests verify:
- Macro output HTML and ARIA attribute presence.
- WTForms rendering and server validation feedback.
- Extension blueprint registration and ChoiceLoader setup.

Browser tests start a live server on the port in the `TEST_SERVER_PORT` environment variable (default `5100`).
To run two suites on one host, give each its own port, e.g. `TEST_SERVER_PORT=5107 pytest tests`.

---

## 🚀 Running the Development Server & Gallery

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # Unix/macOS

# 2. Install dependencies
pip install -r requirements.txt
pip install -e .

# 3. Setup database
python manage.py recreate_db
python manage.py setup_dev

# 4. Start the server
python manage.py runserver
```

Visit the component gallery at: **`http://localhost:5000/basecoat/gallery`**

---

## 📄 License

MIT License. Upstream [Basecoat UI](https://basecoatui.com/) CSS and components are MIT licensed.
