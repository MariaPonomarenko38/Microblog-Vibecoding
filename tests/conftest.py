import os
import sys
import pytest
from fastapi.testclient import TestClient
# Ensure project root is on sys.path so tests can import `fastapi_app`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi_app import main

@pytest.fixture(scope='session')
def client():
    # Ensure tests use a clean users collection
    main.users_collection.delete_many({})
    with TestClient(main.app) as c:
        yield c

@pytest.fixture(autouse=True)
def cleanup_db():
    # Runs before each test
    main.users_collection.delete_many({})
    yield
    # Runs after each test
    main.users_collection.delete_many({})
