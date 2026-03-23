import pytest
from django.test import Client
from unittest.mock import patch
from pytest_django.asserts import assertTemplateUsed, assertContains
import datetime


@pytest.mark.django_db
def test_prediction_view_get():
    client = Client()
    response = client.get('/')
    assert response.status_code == 200
    assertTemplateUsed(response, 'home.html')


@pytest.mark.django_db
@patch('prediction.views.predict_kuma')
def test_prediction_view_post_success(mock_predict):
    client = Client()
    data = {
        'lat': 35.0,
        'lon': 139.0,
        'address': '東京都',
        'place_name': '新宿',
        'date': '2026-03-12',
    }
    mock_predict.return_value = {'result': 123.45678901, 'error': None}

    response = client.post('/', data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'home.html')
    # 丸められた結果文字列がHTML内に含まれていることを確認
    assertContains(response, '123.45678901')


@pytest.mark.django_db
@patch('prediction.views.predict_kuma')
def test_prediction_view_post_error(mock_predict):
    client = Client()
    data = {
        'lat': 35.0,
        'lon': 139.0,
        'address': '東京都',
        'place_name': '新宿',
        'date': '2026-03-12',
    }
    mock_predict.return_value = {'result': None, 'error': '予測エラー'}

    response = client.post('/', data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'home.html')
    assertContains(response, '予測エラー')


@pytest.mark.django_db
def test_prediction_view_post_invalid_form():
    client = Client()
    data = {'lat': '', 'lon': '', 'address': '', 'place_name': '', 'date': ''}
    response = client.post('/', data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'home.html')


@pytest.mark.django_db
def test_disclaimer_view():
    client = Client()
    response = client.get('/disclaimer/')
    assert response.status_code == 200
    assertTemplateUsed(response, 'disclaimer.html')
