import pytest
from fastapi.testclient import TestClient

from main import app
from app.services.suno_service import suno_service

from app.config import settings

@pytest.fixture(autouse=True)
def stub_suno_service(monkeypatch):
    # Disable secret-token auth for tests
    settings.secret_token = ''
    # Stub SunoService methods for testing
    monkeypatch.setattr(suno_service, 'submit_song', lambda params: 'test-music-id')
    monkeypatch.setattr(suno_service, 'submit_lyrics', lambda params: 'test-lyrics-id')
    monkeypatch.setattr(suno_service, 'fetch_by_id', lambda tid: {'task_id': tid, 'status': 'SUCCESS', 'data': {}})
    monkeypatch.setattr(suno_service, 'fetch_tasks', lambda ids, action: [{'task_id': t, 'status': 'SUCCESS', 'data': {}} for t in ids])
    monkeypatch.setattr(suno_service, 'get_account_info', lambda: {
        'session_id': 'sid', 'cookie': 'ck', 'jwt': 'jwt',
        'last_update': 123, 'credits_left': 10, 'monthly_limit': 100,
        'monthly_usage': 5, 'period': '2024-01', 'is_active': True
    })
    yield

client = TestClient(app)

def test_submit_music():
    payload = {'prompt': 'hello', 'tags': 'pop', 'make_instrumental': False}
    response = client.post('/suno/submit/music', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 'success'
    assert body['data'] == 'test-music-id'

def test_submit_lyrics():
    payload = {'prompt': 'lyrics'}
    response = client.post('/suno/submit/lyrics', json=payload)
    assert response.status_code == 200
    assert response.json()['data'] == 'test-lyrics-id'

def test_fetch_by_id():
    tid = 'abc123'
    response = client.get(f'/suno/fetch/{tid}')
    assert response.status_code == 200
    data = response.json()['data']
    assert data['task_id'] == tid

def test_fetch_many():
    payload = {'ids': ['a', 'b'], 'action': 'MUSIC'}
    response = client.post('/suno/fetch', json=payload)
    assert response.status_code == 200
    items = response.json()['data']
    assert isinstance(items, list) and len(items) == 2

def test_get_account():
    response = client.get('/suno/account')
    assert response.status_code == 200
    info = response.json()['data']
    assert info['session_id'] == 'sid'