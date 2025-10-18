import os
import sys
import pytest

# --- Ensure app.py can be imported ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


@pytest.fixture
def client():
    """Setup test client for Flask app"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()
    yield client


def test_home_page(client):
    """Test that home page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    # Check a word that actually exists (like in your footer)
    assert b"Cake World" in response.data


def test_add_recipe_page(client):
    """Test Add Recipe page route (follows redirects if login required)"""
    response = client.get('/add', follow_redirects=True)
    assert response.status_code == 200
    # Check that the page contains a form element (universal check)
    assert b"<form" in response.data


def test_login_page(client):
    """Test login page route"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Login" in response.data
