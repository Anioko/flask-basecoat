"""
Automated Screenshot Capture Script for Basecoat Component Gallery & Examples.
Uses Playwright to capture high-res desktop (light/dark), mobile, and ported shadcn application screens.
"""
import os
import sys
import time
import threading
from pathlib import Path
from flask import Flask
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright

from flask_basecoat import Basecoat

OUTPUT_DIR = Path("C:/flask-basecoat/readme_media")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ServerThread(threading.Thread):
    def __init__(self, app, host='127.0.0.1', port=5055):
        super().__init__()
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


def create_gallery_app():
    app = Flask(
        __name__,
        static_folder=r'C:\flask-basecoat\app\static',
        static_url_path='/static'
    )
    app.config['SECRET_KEY'] = 'gallery-screenshot-secret'
    app.config['BASECOAT_GALLERY_ENABLED'] = True
    app.config['BASECOAT_EXAMPLES_ENABLED'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    Basecoat(app)
    return app


def capture_screenshots():
    app = create_gallery_app()
    server = ServerThread(app, port=5055)
    server.start()
    print("Test server started at http://127.0.0.1:5055")
    time.sleep(1)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # 1. Desktop Light Mode Gallery (1440x900)
            page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
            page.goto("http://127.0.0.1:5055/basecoat/gallery", wait_until="networkidle")
            page.wait_for_timeout(1000)
            light_path = OUTPUT_DIR / "gallery-light-1440.png"
            page.screenshot(path=str(light_path), full_page=True)
            print(f"Captured: {light_path}")

            # 2. Desktop Dark Mode Gallery (1440x900)
            page.evaluate("document.documentElement.classList.add('dark')")
            page.wait_for_timeout(500)
            dark_path = OUTPUT_DIR / "gallery-dark-1440.png"
            page.screenshot(path=str(dark_path), full_page=True)
            print(f"Captured: {dark_path}")

            # 3. Interactive Modal Dialog
            page.evaluate("document.documentElement.classList.remove('dark')")
            page.evaluate("window.scrollTo(0, 0)")
            page.evaluate("document.getElementById('demo-dialog').showModal()")
            page.wait_for_timeout(600)
            dialog_path = OUTPUT_DIR / "dialog-modal.png"
            page.screenshot(path=str(dialog_path))
            print(f"Captured: {dialog_path}")
            page.evaluate("document.getElementById('demo-dialog').close()")
            page.wait_for_timeout(300)

            # 4. Form Validation Errors
            page.evaluate("document.querySelector('form').scrollIntoView()")
            page.wait_for_timeout(300)
            page.click("button:has-text('Submit Form')")
            page.wait_for_timeout(800)
            form_path = OUTPUT_DIR / "form-validation.png"
            page.screenshot(path=str(form_path))
            print(f"Captured: {form_path}")
            page.close()

            # 5. Mobile Viewport (390x844)
            mobile_page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
            mobile_page.goto("http://127.0.0.1:5055/basecoat/gallery", wait_until="networkidle")
            mobile_page.wait_for_timeout(1000)
            mobile_path = OUTPUT_DIR / "gallery-mobile-390.png"
            mobile_page.screenshot(path=str(mobile_path), full_page=True)
            print(f"Captured: {mobile_path}")
            mobile_page.close()

            # 6. Examples Index Screen (1440x900)
            ex_page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
            ex_page.goto("http://127.0.0.1:5055/examples/", wait_until="networkidle")
            ex_page.wait_for_timeout(800)
            ex_index_path = OUTPUT_DIR / "examples-index-1440.png"
            ex_page.screenshot(path=str(ex_index_path), full_page=True)
            print(f"Captured: {ex_index_path}")

            # 7. Authentication Example Screen (1440x900)
            ex_page.goto("http://127.0.0.1:5055/examples/authentication", wait_until="networkidle")
            ex_page.wait_for_timeout(800)
            auth_path = OUTPUT_DIR / "examples-auth-1440.png"
            ex_page.screenshot(path=str(auth_path))
            print(f"Captured: {auth_path}")

            # 8. Dashboard Example Screen (1440x900)
            ex_page.goto("http://127.0.0.1:5055/examples/dashboard", wait_until="networkidle")
            ex_page.wait_for_timeout(800)
            dash_path = OUTPUT_DIR / "examples-dashboard-1440.png"
            ex_page.screenshot(path=str(dash_path), full_page=True)
            print(f"Captured: {dash_path}")

            # 9. Tasks Example Screen (1440x900)
            ex_page.goto("http://127.0.0.1:5055/examples/tasks", wait_until="networkidle")
            ex_page.wait_for_timeout(800)
            tasks_path = OUTPUT_DIR / "examples-tasks-1440.png"
            ex_page.screenshot(path=str(tasks_path), full_page=True)
            print(f"Captured: {tasks_path}")

            # Additional 13 Application Categories
            screens = [
                ("pricing", "examples-pricing-1440.png", True),
                ("profile", "examples-profile-1440.png", True),
                ("projects", "examples-projects-1440.png", True),
                ("changelog", "examples-changelog-1440.png", True),
                ("coming-soon", "examples-coming-soon-1440.png", True),
                ("blog", "examples-blog-1440.png", True),
                ("onboarding", "examples-onboarding-1440.png", True),
                ("chat", "examples-chat-1440.png", False),
                ("ai-chat", "examples-ai-chat-1440.png", False),
                ("playground", "examples-playground-1440.png", True),
                ("product-list", "examples-product-list-1440.png", True),
                ("product-detail", "examples-product-detail-1440.png", True),
                ("kanban", "examples-kanban-1440.png", True),
            ]

            for endpoint, filename, full in screens:
                url = f"http://127.0.0.1:5055/examples/{endpoint}"
                ex_page.goto(url, wait_until="networkidle")
                ex_page.wait_for_timeout(800)
                out_file = OUTPUT_DIR / filename
                ex_page.screenshot(path=str(out_file), full_page=full)
                print(f"Captured: {out_file}")

            ex_page.close()

            browser.close()
            print("All screenshots captured successfully!")

    finally:
        server.shutdown()
        server.join()
        print("Test server stopped.")


if __name__ == "__main__":
    capture_screenshots()
