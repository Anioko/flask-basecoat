#!/usr/bin/env python
import os
import subprocess
import click
from redis import Redis
from rq import connections, Queue, Worker
from flask_migrate import Migrate
from flask.cli import with_appcontext

from app import create_app, db
from app.models import Role, User
from config import Config

# Create Flask app
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


# ------------------------
# Flask CLI commands
# ------------------------

@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


@app.cli.command("test")
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.cli.command("recreate-db")
def recreate_db():
    """Recreates the local database. Do not use in production."""
    db.drop_all()
    db.create_all()
    db.session.commit()
    click.echo("Database recreated successfully.")


@app.cli.command("add-fake-data")
@click.option(
    '-n', '--number-users', default=10,
    help='Number of each model type to create'
)
def add_fake_data(number_users):
    """Adds fake data to the database."""
    User.generate_fake(count=number_users)
    click.echo(f"Added {number_users} fake users.")


@app.cli.command("setup-dev")
def setup_dev():
    """Sets up local development environment."""
    setup_general()


@app.cli.command("setup-prod")
def setup_prod():
    """Sets up production environment."""
    setup_general()


def setup_general():
    """Common setup tasks for dev and prod, including creating admin user."""
    Role.insert_roles()
    admin_role = Role.query.filter_by(name='Administrator').first()
    if admin_role:
        if User.query.filter_by(email=Config.ADMIN_EMAIL).first() is None:
            user = User(
                first_name='Admin',
                last_name='Account',
                password=Config.ADMIN_PASSWORD,
                confirmed=True,
                email=Config.ADMIN_EMAIL
            )
            db.session.add(user)
            db.session.commit()
            click.echo(f"Added administrator {user.full_name()}")


@app.cli.command("run-worker")
def run_worker():
    """Initializes a slim RQ task queue."""
    listen = ['default']
    conn = Redis(
        host=app.config['RQ_DEFAULT_HOST'],
        port=app.config['RQ_DEFAULT_PORT'],
        db=0,
        password=app.config['RQ_DEFAULT_PASSWORD']
    )
    # Use the modern 'connections.Connection' context manager
    with connections.Connection(conn):
        worker = Worker([Queue(name) for name in listen])
        worker.work()



@app.cli.command("format")
def format_code():
    """Runs yapf and isort formatters over the project."""
    isort_cmd = 'isort -rc *.py app/'
    yapf_cmd = 'yapf -r -i *.py app/'

    click.echo(f"Running {isort_cmd}")
    subprocess.call(isort_cmd, shell=True)

    click.echo(f"Running {yapf_cmd}")
    subprocess.call(yapf_cmd, shell=True)


# ------------------------
# Run Flask app
# ------------------------
if __name__ == '__main__':
    # For development server, use: flask run
    app.run(host="0.0.0.0", port=5100)
