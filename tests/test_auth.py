import json
# Assuming app and User model are accessible after sys.path modification in conftest.py
from app import User

def test_register_user(client, db): # db fixture is available if needed
    # Test successful registration
    response = client.post('/auth/register', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    assert response.status_code == 201
    assert response.json['msg'] == 'User created successfully'

    # Verify user in database
    # The 'app' fixture in conftest.py already creates an app_context for the session.
    # For db operations in tests, ensure an app context is active.
    # client.application provides the app instance.
    with client.application.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.check_password('testpassword')

    # Test duplicate username registration
    response_dup = client.post('/auth/register', json={
        'username': 'testuser',
        'password': 'anotherpassword'
    })
    assert response_dup.status_code == 400
    assert response_dup.json['msg'] == 'Username already exists'

def test_login_user(client, db): # db fixture available
    # First, register a user to test login
    # This makes the test self-contained.
    register_response = client.post('/auth/register', json={
        'username': 'loginuser',
        'password': 'loginpassword'
    })
    assert register_response.status_code == 201 # Ensure registration was successful

    # Test successful login
    response = client.post('/auth/login', json={
        'username': 'loginuser',
        'password': 'loginpassword'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

    # Test login with wrong password
    response_wrong_pass = client.post('/auth/login', json={
        'username': 'loginuser',
        'password': 'wrongpassword'
    })
    assert response_wrong_pass.status_code == 401
    assert response_wrong_pass.json['msg'] == 'Bad username or password'

    # Test login with non-existent user
    response_no_user = client.post('/auth/login', json={
        'username': 'nonexistentuser',
        'password': 'somepassword'
    })
    assert response_no_user.status_code == 401
    assert response_no_user.json['msg'] == 'Bad username or password'
