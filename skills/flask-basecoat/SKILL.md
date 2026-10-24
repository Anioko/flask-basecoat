---
name: flask-basecoat
description: Build Flask/Jinja pages that look exactly like shadcn/ui with the Flask-Basecoat macros. Use when a project imports flask_basecoat or renders templates with `{% import 'basecoat/index.html' as ui %}`, or when asked for shadcn-style pages, dashboards, forms or charts in Flask. Covers choosing the nearest shadcn original, the dashboard-01 frame, the macro reference, chart specs, and the page check that proves a page is shadcn.
---

# Flask-Basecoat

Follow `AGENTS.md` at the repository root; it is the full procedure. In short:

1. Pick the nearest shadcn original (dashboard-01 for signed-in pages, a login or signup block, a sidebar block, a
   component example or one of the 70 charts) and name it with `<meta name="shadcn-nearest" content="...">`.
2. Reuse its frame (`examples/reference/_shell.html` for dashboard-01) and change only content; lay rows out
   with the recipes in `docs/LAYOUT.md`.
3. Write every visible part with a macro from `docs/MACROS.md`; wrappers carry layout and type classes only; colours
   are theme tokens only; charts come from `ui.chart_from_spec` with a shipped spec.
4. Run `python compliance/scripts/check_page.py <page> --nearest <original> --browser` and fix the page until it
   prints `SHADCN COMPOSED` at 100%.

Start from `flask_basecoat/templates/examples/reference/portfolio.html`, which passes the check.
