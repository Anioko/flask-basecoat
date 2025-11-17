# Systematic Fix Guide - No More Individual Page Checks

## The Problem

We cannot check individual pages to find styling issues. We need a **systematic approach** to ensure all pages use the design system consistently.

## The Solution: 3-Layer Strategy

### Layer 1: Global CSS Classes (✅ DONE)

**File:** [app/assets/styles/input.css](app/assets/styles/input.css)

All these classes are available on EVERY page automatically:
- `.btn` + variants (`.btn--ghost`, `.btn--outline`, `.btn--secondary`, `.btn--sm`, `.btn--lg`)
- `.input` - All form inputs
- `.card`, `.card-header`, `.card-content` - Card containers

**No action needed** - These work everywhere already.

### Layer 2: Reusable Layout Macros (✅ NEW)

**File:** [app/templates/macros/layout_macros.html](app/templates/macros/layout_macros.html)

Instead of manually adding card markup to every page, use these macros:

#### Basic Page with Card

**Before** (manual, error-prone):
```html
{% block content %}
    <div class="container mx-auto px-4 py-8">
        <h2>Title</h2>
        <p>Description</p>
        <!-- Content without card -->
    </div>
{% endblock %}
```

**After** (using macro):
```html
{% import 'macros/layout_macros.html' as layout %}

{% block content %}
    {% call layout.simple_card(title="Title", description="Description") %}
        <!-- Your content here - automatically wrapped in card -->
    {% endcall %}
{% endblock %}
```

#### Page with Back Button

```html
{% import 'macros/layout_macros.html' as layout %}

{% block content %}
    {% call layout.page_container(
        title="Registered Users",
        description="View and manage users",
        back_url=url_for('admin.index'),
        back_text="Back to dashboard"
    ) %}
        <!-- Content -->
    {% endcall %}
{% endblock %}
```

#### Two-Column Layout (Sidebar + Content)

```html
{% import 'macros/layout_macros.html' as layout %}

{% block content %}
    {% call layout.two_column_layout(
        left_title="Navigation",
        right_title="Content"
    ) %}
        <!-- Left column -->
        {% call('left') %}
            <nav>...</nav>
        {% endcall %}

        <!-- Right column -->
        {% call('right') %}
            <div>...</div>
        {% endcall %}
    {% endcall %}
{% endblock %}
```

### Layer 3: Update Core Macros (🔄 IN PROGRESS)

Update the existing macros that are used across multiple pages:

#### Files to Update:

1. **✅ form_macros.html** - Already uses `.btn` and `.input`
2. **✅ nav_macros.html** - Uses proper Tailwind classes
3. **🔄 page_macros.html** - Needs button class updates
4. **✅ sidebar_macros.html** - Already complete

## Systematic Migration Plan

### Step 1: Identify Page Categories

Group pages by type to apply fixes systematically:

**A. Admin Pages**
- `/admin/users` ✅ - Updated with card
- `/admin/user/<id>` - Needs card
- `/admin/dashboard` - Check if needs card

**B. Account Pages**
- `/account/login` ✅ - Has card
- `/account/register` ✅ - Has card
- `/account/manage` ✅ - Has card with sidebar
- `/account/change-email` - Check if needs card
- `/account/change-password` - Check if needs card

**C. Main Pages**
- `/` (home) - Check layout
- `/about` - Check layout

### Step 2: Create Template Checklist Script

Create a Python script to audit all templates:

```python
# scripts/audit_templates.py
import os
import re

template_dir = 'app/templates'
issues = []

for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()

                # Check for old button classes
                if 'ui.button' in content or 'ui.primary' in content:
                    issues.append(f"{path}: Uses old Semantic UI button classes")

                # Check for inline styles
                if 'style="' in content and 'overflow' not in content:
                    issues.append(f"{path}: Has inline styles (possible layout issue)")

                # Check if extends base but missing card wrapper
                if 'extends' in content and 'block content' in content:
                    if '.card' not in content and 'layout.simple_card' not in content:
                        issues.append(f"{path}: Missing card wrapper")

for issue in issues:
    print(issue)
```

### Step 3: Priority Fix Order

Fix pages in this order (highest impact first):

**Priority 1: User-Facing Pages** (Affects all users)
1. Login / Register ✅
2. Account management ✅
3. Password reset
4. Home page

**Priority 2: Admin Pages** (Affects admins)
1. User list ✅
2. User detail pages
3. Admin dashboard

**Priority 3: Utility Pages** (Lower traffic)
1. About
2. Error pages
3. Email templates

## Quick Reference: What to Use When

### Buttons

```html
<!-- Primary action -->
<button class="btn">Save</button>
<input type="submit" class="btn" value="Submit">

<!-- Navigation / Links -->
<a class="btn btn--ghost" href="#">Back</a>

<!-- Secondary actions -->
<button class="btn btn--outline">Cancel</button>
<button class="btn btn--secondary">Draft</button>

<!-- Sizes -->
<button class="btn btn--sm">Small</button>
<button class="btn btn--lg">Large</button>
```

### Form Inputs

```html
<!-- All inputs use .input class -->
<input type="text" class="input" placeholder="Name">
<input type="email" class="input" placeholder="Email">
<select class="input">...</select>
<textarea class="input"></textarea>

<!-- Fixed width -->
<input type="text" class="input w-64">
```

### Cards

```html
<!-- Manual card (when you need full control) -->
<div class="card">
    <div class="card-header">
        <h2 class="text-2xl font-semibold">Title</h2>
        <p class="text-sm text-slate-600">Description</p>
    </div>
    <div class="card-content">
        <!-- Content -->
    </div>
</div>

<!-- Macro card (recommended) -->
{% import 'macros/layout_macros.html' as layout %}
{% call layout.simple_card(title="Title", description="Desc") %}
    <!-- Content -->
{% endcall %}
```

## Automated Checks

### Pre-commit Hook (Recommended)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Check for old Semantic UI classes
if git diff --cached --name-only | grep -q '\.html$'; then
    if git diff --cached | grep -E 'ui\.(button|primary|secondary|segment)'; then
        echo "ERROR: Old Semantic UI classes detected"
        echo "Please use new design system classes (.btn, .input, .card)"
        exit 1
    fi
fi

# Check for inline styles (except whitelisted)
if git diff --cached | grep 'style=' | grep -v 'overflow'; then
    echo "WARNING: Inline styles detected. Consider using Tailwind classes."
fi
```

### VSCode Extension (Optional)

Install "Tailwind CSS IntelliSense" extension for:
- Autocomplete for Tailwind classes
- Warnings for non-existent classes
- Color previews

## Common Patterns

### Pattern 1: Simple Form Page

```html
{% extends 'layouts/base.html' %}
{% import 'macros/form_macros.html' as f %}
{% import 'macros/layout_macros.html' as layout %}

{% block content %}
    {% call layout.simple_card(
        title="Page Title",
        description="Page description",
        max_width="max-w-md"
    ) %}
        {{ f.render_form(form) }}
    {% endcall %}
{% endblock %}
```

### Pattern 2: List/Table Page

```html
{% extends 'layouts/base.html' %}
{% import 'macros/layout_macros.html' as layout %}

{% block content %}
    {% call layout.page_container(
        title="Items",
        description="Manage items",
        back_url=url_for('admin.index'),
        back_text="Back to dashboard"
    ) %}
        <div class="flex gap-3 mb-4">
            <select class="input w-64">...</select>
            <input type="text" class="input w-64" placeholder="Search...">
        </div>

        <div class="overflow-x-auto">
            <table class="table w-full">
                <!-- Table content -->
            </table>
        </div>
    {% endcall %}
{% endblock %}
```

### Pattern 3: Settings Page (Sidebar + Content)

```html
{% extends 'layouts/base.html' %}

{% block content %}
    <div class="container mx-auto px-4 py-8">
        <h2 class="text-2xl font-semibold mb-6">Settings</h2>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- Sidebar (25%) -->
            <div class="lg:col-span-3">
                <nav class="flex flex-col gap-1 bg-slate-50 dark:bg-slate-900 p-2 rounded-lg border border-slate-200 dark:border-slate-800">
                    <a class="btn btn--ghost" href="#">General</a>
                    <a class="btn btn--ghost" href="#">Security</a>
                </nav>
            </div>

            <!-- Content (75%) -->
            <div class="lg:col-span-9">
                <div class="card">
                    <div class="card-content">
                        <!-- Content -->
                    </div>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

## Next Steps

1. **Run audit script** to find all pages needing updates
2. **Update templates** using the layout macros
3. **Test each page** in the browser
4. **Add browser tests** for critical pages
5. **Document** any custom patterns

## Files Reference

- **CSS:** [app/assets/styles/input.css](app/assets/styles/input.css)
- **Macros:** [app/templates/macros/layout_macros.html](app/templates/macros/layout_macros.html)
- **Examples:**
  - [app/templates/account/login.html](app/templates/account/login.html)
  - [app/templates/account/register.html](app/templates/account/register.html)
  - [app/templates/admin/registered_users.html](app/templates/admin/registered_users.html)
  - [app/templates/account/manage.html](app/templates/account/manage.html)

---

**Status:** 🔄 In Progress
**Updated:** 2025-11-15

**Key Principle:** Fix macros and layouts once, benefit everywhere!
