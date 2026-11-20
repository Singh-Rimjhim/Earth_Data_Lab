"""
Integration tests for Flask application routes.
"""

import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'healthy'
    assert 'nasa_gistemp' in data['available_datasets']


def test_get_datasets(client):
    res = client.get('/api/datasets')
    assert res.status_code == 200
    data = res.get_json()
    assert 'datasets' in data
    assert 'nasa_gistemp' in data['datasets']


def test_get_data_nasa(client):
    res = client.get('/api/data?dataset_id=nasa_gistemp')
    assert res.status_code == 200
    data = res.get_json()
    assert 'records' in data
    assert len(data['records']) > 100
    assert 'summary' in data
    assert 'trend' in data
    assert 'insights' in data


def test_get_data_filtered(client):
    res = client.get('/api/data?dataset_id=nasa_gistemp&start_year=1990&end_year=2010')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data['records']) == 21
    assert data['records'][0]['year'] == 1990
    assert data['records'][-1]['year'] == 2010


def test_assistant_query_api(client):
    res = client.post('/api/query', json={
        'query': 'What is the rate of warming per decade?',
        'dataset_id': 'nasa_gistemp'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['intent'] == 'TREND_ANALYSIS'
    assert 'metrics' in data


def test_assistant_empty_query(client):
    res = client.post('/api/query', json={'query': ''})
    assert res.status_code == 400


def test_export_csv_endpoint(client):
    res = client.get('/api/export?dataset_id=nasa_gistemp&start_year=2000&end_year=2020')
    assert res.status_code == 200
    assert res.content_type.startswith('text/csv')
    csv_text = res.data.decode('utf-8')
    assert '# Earth Data Lab Export' in csv_text
    assert 'year,annual_anomaly,five_year_smooth,uncertainty' in csv_text
