import pytest
from unittest.mock import patch, MagicMock
from services import fastapi_client
import datetime

@patch('services.fastapi_client.session.post')
def test_predict_kuma_success(mock_post):
    # モックレスポンスの設定
    mock_response = MagicMock()
    mock_response.json.return_value = {'result': 'ok'}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    lat, lon = 35.0, 139.0
    date = datetime.date(2026, 3, 12)
    result = fastapi_client.predict_kuma(lat, lon, date)
    assert result == {'result': 'ok'}
    mock_post.assert_called_once()

@patch('services.fastapi_client.session.post')
def test_predict_kuma_http_error(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception('HTTP Error')
    mock_post.return_value = mock_response

    lat, lon = 35.0, 139.0
    date = datetime.date(2026, 3, 12)
    result = fastapi_client.predict_kuma(lat, lon, date)
    assert result['result'] is None
    assert 'HTTP Error' in result['error']

@patch('services.fastapi_client.session.post')
def test_predict_kuma_request_exception(mock_post):
    mock_post.side_effect = Exception('Request Exception')

    lat, lon = 35.0, 139.0
    date = datetime.date(2026, 3, 12)
    result = fastapi_client.predict_kuma(lat, lon, date)
    assert result['result'] is None
    assert 'Request Exception' in result['error']
