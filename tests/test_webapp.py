"""
Automated unit and integration tests for Flask Web Application (app.py).
Tests all routes, Plotly chart generation, database pagination, filters, and Tableau fallback.
"""

import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app


@pytest.fixture
def client():
    """Provides a test client for the Flask application."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """Verify home page loads and displays executive KPIs."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Electric Vehicle Market Performance & Insights" in html
    assert "299,999" in html
    assert "Avg Driving Range" in html


def test_dashboard_page(client):
    """Verify market dashboard loads with Plotly charts."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Category Sales & Price Comparison" in html
    assert "chart-category-sales" in html
    assert "chart-regional-sales" in html
    assert "chart_category_json" in html or "Plotly.newPlot" in html


def test_dashboard_category_filter(client):
    """Verify dashboard accepts and handles category filters."""
    response = client.get("/dashboard?category=Sedan")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Sedan" in html


def test_manufacturers_page(client):
    """Verify manufacturer competitiveness page and rankings table."""
    response = client.get("/manufacturers")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Top 15 Automakers by Sales Volume" in html
    assert "AmpereWorks" in html or "SurgeWorks" in html
    assert "Market Share" in html


def test_batteries_page(client):
    """Verify battery chemistry page and engineering metrics table."""
    response = client.get("/batteries")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Battery Chemistry & Technology Performance" in html
    assert "LFP" in html
    assert "NMC" in html
    assert "Solid-State" in html
    assert "Sodium-Ion" in html


def test_data_explorer_pagination(client):
    """Verify data explorer queries SQLite and paginates properly."""
    response = client.get("/explorer?page=1")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "EV Fleet Data Explorer" in html
    assert "EV" in html  # Should display vehicle ID codes
    assert "Page 1 of" in html


def test_data_explorer_filtering_and_search(client):
    """Verify search query and dropdown filters."""
    response = client.get("/explorer?q=Sedan&category=Sedan&battery=LFP")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Showing" in html


def test_tableau_embed_fallback_mode(client):
    """Verify that when no Tableau URL is configured, a helpful setup guide is shown instead of a broken iframe."""
    app.config["TABLEAU_EMBED_URL"] = ""
    response = client.get("/tableau")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Tableau Workbook Integration Guide" in html
    assert "Connect Prepared CSV" in html
    assert "<iframe" not in html


def test_tableau_embed_active_mode(client):
    """Verify that when a Tableau URL is configured, an iframe is rendered."""
    test_url = "https://public.tableau.com/views/sample_test_dashboard"
    app.config["TABLEAU_EMBED_URL"] = test_url
    response = client.get("/tableau")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert f'<iframe src="{test_url}"' in html
    # Reset
    app.config["TABLEAU_EMBED_URL"] = ""


def test_about_page(client):
    """Verify about page renders project scope, data dictionary link, and tech stack."""
    response = client.get("/about")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "About the Project" in html
    assert "Python 3.14+" in html
    assert "SQLite 3" in html
