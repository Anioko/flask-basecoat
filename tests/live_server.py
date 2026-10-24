import os
import tempfile
from threading import Thread

from werkzeug.serving import make_server

from app import create_app, db
from app.models import Role, User

TEST_SERVER_HOST = "127.0.0.1"
TEST_SERVER_PORT = int(os.environ.get("BASECOAT_TEST_PORT", "5100"))  # worktrees running at once each set their own
TEST_SERVER_BASE_URL = f"http://{TEST_SERVER_HOST}:{TEST_SERVER_PORT}"
TEST_ADMIN_EMAIL = "admin@admin.com"
TEST_ADMIN_PASSWORD = "admin"


class LiveServerManager:
    """Manage a lightweight HTTP server for browser-based tests."""

    def __init__(self):
        self._thread = None
        self._server = None
        self._ctx = None
        self._db_path = None

    def is_running(self):
        return self._thread is not None

    def start(self):
        if self.is_running():
            return

        previous_db_url = os.environ.get("TEST_DATABASE_URL")
        fd, db_path = tempfile.mkstemp(prefix="browser-tests-", suffix=".sqlite")
        os.close(fd)
        os.environ["TEST_DATABASE_URL"] = f"sqlite:///{db_path}"
        # TestingConfig reads TEST_DATABASE_URL when config.py is imported, so the environment variable alone
        # does not isolate this server: point the config at the temporary database for the duration of create_app,
        # otherwise the browser tests share data-test.sqlite with every other `create_app('testing')` on the machine.
        from config import TestingConfig
        previous_uri = TestingConfig.SQLALCHEMY_DATABASE_URI
        TestingConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        try:
            app = create_app("testing")
        finally:
            TestingConfig.SQLALCHEMY_DATABASE_URI = previous_uri
        if previous_db_url is None:
            os.environ.pop("TEST_DATABASE_URL", None)
        else:
            os.environ["TEST_DATABASE_URL"] = previous_db_url

        self._ctx = app.app_context()
        self._ctx.push()

        db.create_all()
        Role.insert_roles()
        admin_role = Role.query.filter_by(name="Administrator").first()
        if admin_role is None:
            raise RuntimeError("Administrator role could not be initialized for browser tests")
        if User.query.filter_by(email=TEST_ADMIN_EMAIL).first() is None:
            user = User(
                first_name="Admin",
                last_name="User",
                email=TEST_ADMIN_EMAIL,
                password=TEST_ADMIN_PASSWORD,
                confirmed=True,
                role=admin_role,
            )
            db.session.add(user)
            db.session.commit()

        self._server = make_server(TEST_SERVER_HOST, TEST_SERVER_PORT, app)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self._db_path = db_path

    def stop(self):
        if not self.is_running():
            return
        self._server.shutdown()
        self._thread.join(timeout=5.0)
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self._ctx.pop()
        self._thread = None
        self._server = None
        if self._db_path:
            try:
                os.remove(self._db_path)
            except OSError:
                pass
            self._db_path = None


_live_server = LiveServerManager()


def ensure_server():
    """Start the live server if it is not already running."""
    _live_server.start()
    return _live_server


def stop_server():
    """Stop the live server if it is running."""
    _live_server.stop()