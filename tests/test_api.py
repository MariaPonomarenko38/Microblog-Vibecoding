import json
from fastapi_app import main


def test_signup_and_login(client):
    # Signup
    payload = {"username": "alice", "email": "alice@example.com", "password": "secret123"}
    r = client.post('/signup', json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body['username'] == 'alice'
    assert body['email'] == 'alice@example.com'
    # User should exist in DB
    user = main.get_user_by_username('alice')
    assert user is not None

    # Duplicate signup fails
    r2 = client.post('/signup', json=payload)
    assert r2.status_code == 400

    # Login
    r3 = client.post('/token', data={'username': 'alice', 'password': 'secret123'})
    assert r3.status_code == 200
    token_body = r3.json()
    assert 'access_token' in token_body
    user_id = token_body['access_token']

    # Profile with correct token
    headers = {'Authorization': f'Bearer {user_id}'}
    r4 = client.get(f'/profile/{user_id}', headers=headers)
    assert r4.status_code == 200
    profile = r4.json()
    assert profile['username'] == 'alice'
    assert profile['email'] == 'alice@example.com'

    # Profile with wrong token is forbidden
    fake_token = '000000000000000000000000'
    r5 = client.get(f'/profile/{user_id}', headers={'Authorization': f'Bearer {fake_token}'})
    assert r5.status_code == 403


def test_all_users_endpoint(client):
    # Create two users directly in DB
    u1 = {'username': 'bob', 'email': 'bob@example.com', 'password': 'x'}
    u2 = {'username': 'carol', 'email': 'carol@example.com', 'password': 'x'}
    main.users_collection.insert_one(u1)
    main.users_collection.insert_one(u2)
    r = client.get('/all_users')
    assert r.status_code == 200
    users = r.json()
    assert any(u['username'] == 'bob' for u in users)
    assert any(u['username'] == 'carol' for u in users)
