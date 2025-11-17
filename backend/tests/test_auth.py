"""
Tests for authentication endpoints.
"""

import pytest
from models import db, User


class TestAuth:
    """Test authentication endpoints"""

    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post('/auth/register', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpassword123'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Registration successful'
        assert data['user']['username'] == 'testuser'
        assert data['user']['email'] == 'test@example.com'

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post('/auth/register', json={
            'email': test_user.email,
            'username': 'newuser',
            'password': 'testpassword123'
        })

        assert response.status_code == 409
        data = response.get_json()
        assert 'already registered' in data['error'].lower()

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""
        response = client.post('/auth/register', json={
            'email': 'newemail@example.com',
            'username': test_user.username,
            'password': 'testpassword123'
        })

        assert response.status_code == 409
        data = response.get_json()
        assert 'already taken' in data['error'].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post('/auth/register', json={
            'email': 'invalid-email',
            'username': 'testuser',
            'password': 'testpassword123'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'email' in data['error'].lower()

    def test_register_short_password(self, client):
        """Test registration with too short password"""
        response = client.post('/auth/register', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'short'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'password' in data['error'].lower()

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post('/auth/login', json={
            'login': test_user.username,
            'password': 'testpassword'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Login successful'
        assert data['user']['username'] == test_user.username

    def test_login_with_email(self, client, test_user):
        """Test login with email instead of username"""
        response = client.post('/auth/login', json={
            'login': test_user.email,
            'password': 'testpassword'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['email'] == test_user.email

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        response = client.post('/auth/login', json={
            'login': test_user.username,
            'password': 'wrongpassword'
        })

        assert response.status_code == 401
        data = response.get_json()
        assert 'invalid credentials' in data['error'].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post('/auth/login', json={
            'login': 'nonexistent',
            'password': 'password123'
        })

        assert response.status_code == 401

    def test_logout(self, client, auth_client):
        """Test logout"""
        response = auth_client.post('/auth/logout')

        assert response.status_code == 200
        data = response.get_json()
        assert 'logged out' in data['message'].lower()

    def test_profile_authenticated(self, client, auth_client, test_user):
        """Test profile endpoint when authenticated"""
        response = auth_client.get('/auth/profile')

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['username'] == test_user.username

    def test_profile_unauthenticated(self, client):
        """Test profile endpoint when not authenticated"""
        response = client.get('/auth/profile')

        assert response.status_code == 401

    def test_check_auth_authenticated(self, client, auth_client):
        """Test auth check when authenticated"""
        response = auth_client.get('/auth/check')

        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is True

    def test_check_auth_unauthenticated(self, client):
        """Test auth check when not authenticated"""
        response = client.get('/auth/check')

        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is False
