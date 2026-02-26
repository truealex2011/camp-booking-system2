"""Tests for admin login navigation feature (Requirement 10)."""
import pytest
from flask import url_for


def test_admin_login_has_back_to_home_button(client):
    """
    Test that the admin login page displays a "Back to Home" button.
    
    Validates: Requirements 10.1, 10.2
    """
    response = client.get('/admin/login')
    
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    
    # Check that the button exists
    assert 'Вернуться на главную' in html
    
    # Check that it links to the public index
    assert 'href="/"' in html or 'url_for(\'public.index\')' in html
    
    # Check that it uses the btn-secondary class for consistent styling
    assert 'btn btn-secondary' in html


def test_back_to_home_button_navigation(client):
    """
    Test that clicking the "Back to Home" button navigates to the main page.
    
    Validates: Requirements 10.2
    """
    # First, get the admin login page
    response = client.get('/admin/login')
    assert response.status_code == 200
    
    # Then verify the home page is accessible
    response = client.get('/')
    assert response.status_code == 200


def test_admin_login_page_structure(client):
    """
    Test that the admin login page has proper structure with navigation.
    
    Validates: Requirements 10.3, 10.4
    """
    response = client.get('/admin/login')
    html = response.data.decode('utf-8')
    
    # Check that the navigation section exists
    assert 'login-navigation' in html
    
    # Check that the button appears before the login form
    nav_pos = html.find('login-navigation')
    form_pos = html.find('<form method="POST">')
    assert nav_pos < form_pos, "Navigation should appear before the login form"
