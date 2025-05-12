import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_ping():
    """GET /ping should return a pong message"""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}