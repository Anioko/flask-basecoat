"""
Local Deployment Runner for flask-basecoat.
Launches the Flask application with all 16 ported shadcn examples and the
Flask-Basecoat component gallery enabled on http://127.0.0.1:5100.
"""
import os
import sys

# Ensure Flask-Basecoat root is in python path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Set environment defaults
os.environ.setdefault('FLASK_CONFIG', 'development')
os.environ.setdefault('SECRET_KEY', 'local-dev-secret-key-basecoat-2026')

from app import create_app, db

app = create_app('development')
app.config['BASECOAT_GALLERY_ENABLED'] = True
app.config['BASECOAT_EXAMPLES_ENABLED'] = True

# Re-register blueprints if not yet registered
from flask_basecoat import Basecoat
basecoat = Basecoat()
basecoat.init_app(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database checked and ready.")

    host = '0.0.0.0'
    port = 5100
    print(f"================================================================")
    print(f"  Flask-Basecoat Local Server Running!")
    print(f"  Applications Directory : http://127.0.0.1:{port}/examples/")
    print(f"  Component Gallery      : http://127.0.0.1:{port}/basecoat/gallery")
    print(f"  Main Application Home  : http://127.0.0.1:{port}/")
    print(f"================================================================")
    app.run(host=host, port=port, debug=False, use_reloader=False)
