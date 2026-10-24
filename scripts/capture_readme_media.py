"""Capture the README screenshots into readme_media/ from a local app with the gallery and examples registered.

    python scripts/capture_readme_media.py
"""
import pathlib
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'readme_media'
PORT = 5420

SHOTS = [
    # name, path, theme, viewport, action
    ('gallery-light-1440', '/basecoat/', 'light', (1440, 900), None),
    ('dashboard-01-light-1440', '/basecoat/blocks/dashboard-01', 'light', (1440, 900), None),
    ('dashboard-01-dark-1440', '/basecoat/blocks/dashboard-01', 'dark', (1440, 900), None),
    ('charts-1440', '/basecoat/charts/', 'light', (1440, 900), 'scroll-charts'),
    ('compare-1440', '/basecoat/compare/chart-area-interactive', 'light', (1440, 900), None),
    ('example-admin-dashboard-1440', '/examples/admin-dashboard', 'light', (1440, 900), None),
    ('example-mail-dark-1440', '/examples/mail-app', 'dark', (1440, 900), None),
    ('reference-portfolio-1440', '/examples/reference/portfolio', 'light', (1440, 900), None),
    ('dashboard-01-mobile-390', '/basecoat/blocks/dashboard-01', 'light', (390, 844), None),
    ('dialog-modal', '/basecoat/components/dialog', 'light', (1440, 900), 'open-dialog'),
    ('form-validation', '/basecoat/gallery', 'light', (1440, 900), 'submit-form'),
]


def run_app():
    from flask_basecoat.testing import make_app
    from flask_basecoat.examples import examples_bp
    app = make_app()
    if 'basecoat_examples' not in app.blueprints:
        app.register_blueprint(examples_bp, url_prefix='/examples')
    app.run(port=PORT, use_reloader=False)


def main():
    from playwright.sync_api import sync_playwright
    threading.Thread(target=run_app, daemon=True).start()
    time.sleep(2)
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, path, theme, (w, h), action in SHOTS:
            pg = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
            pg.goto(f'http://127.0.0.1:{PORT}{path}')
            pg.evaluate(f"() => {{ try {{ localStorage.setItem('flask-basecoat-theme', '{theme}'); }} catch (e) {{}} "
                        f"document.documentElement.classList.toggle('dark', {str(theme == 'dark').lower()}); }}")
            pg.add_style_tag(content='*,*::before,*::after{transition:none!important;animation:none!important}')
            pg.wait_for_timeout(900)
            if action == 'open-dialog':
                pg.locator('[data-slot="dialog-trigger"]').first.click()
                pg.wait_for_timeout(500)
            elif action == 'submit-form':
                # Skip the browser's own required-field popups so the server-side validation messages render.
                pg.evaluate("() => document.querySelectorAll('form').forEach(f => f.noValidate = true)")
                pg.fill('input[name="name"]', 'Al')
                pg.fill('input[name="email"]', 'not-an-email')
                pg.locator('form button[type="submit"], form [data-slot="button"][type="submit"]').first.click()
                pg.wait_for_load_state()
                pg.evaluate("() => document.documentElement.classList.remove('dark')")
                pg.evaluate("() => { const f = document.querySelector('form'); if (f) f.scrollIntoView(); window.scrollBy(0, -40); }")
                pg.wait_for_timeout(700)
            elif action == 'scroll-charts':
                pg.evaluate("() => { const g = document.querySelector('[class~=\"lg:grid-cols-3\"]'); if (g) g.scrollIntoView(); window.scrollBy(0, -80); }")
                pg.wait_for_timeout(700)
            pg.screenshot(path=str(OUT / f'{name}.png'))
            pg.close()
            print('saved', name)
        b.close()


if __name__ == '__main__':
    main()
