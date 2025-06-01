import pytest
import os
# Add project root to sys.path to allow importing app
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app, db as sqlalchemy_db # Assuming app and db are importable from app.py

@pytest.fixture(scope='session')
def app():
    # Configure app for testing
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", # Use in-memory SQLite for tests
        # "JWT_SECRET_KEY": "test-secret-key", # Already configured in app.py to use env var or default
    })
    # Other test-specific configurations can go here

    with flask_app.app_context():
        sqlalchemy_db.create_all() # Create tables for in-memory db

    yield flask_app

    # Teardown: No explicit teardown needed for in-memory db normally,
    # but if using a file-based test DB, clean it up here.
    # with flask_app.app_context():
    #     sqlalchemy_db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

@pytest.fixture(scope='function') # Use function scope for db to reset between tests
def db(app): # The app fixture already creates the schema for the session.
    # This fixture primarily ensures that operations are within an app context if needed directly by a test,
    # and provides access to the db object.
    # For tests modifying data, they should ideally manage their own transactions or ensure clean state.
    # The in-memory DB is clean per session. If tests within a session need stricter isolation,
    # one might consider function-scoped database recreation here, but it can be slow.
    with app.app_context():
        pass # Schema is created by the 'app' fixture.
    return sqlalchemy_db
