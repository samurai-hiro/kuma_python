from datetime import date
import requests
import time
import pytest
from prediction.src.population_density import get_days_from_start,get_city_code,fetch_estat_value,get_elevation

def test_get_elevation_missing(monkeypatch,disable_sleep):
    class MockResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {}
        
    def mock_get(url,params):
        return MockResponse()

    monkeypatch.setattr(requests,'get',mock_get)
    with pytest.raises(KeyError):
        get_elevation(35.6895,139.6917)

def test_fetch_estat_value_empty(monkeypatch,disable_sleep):
    class MockResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                'GET_STATS_DATA': {
                    'STATISTICAL_DATA': {
                        'DATA_INF': {
                            'VALUE': []
                        }
                    }
                }
            }
    def mock_get(url,params):
        return MockResponse()
    monkeypatch.setattr(requests,'get',mock_get)
    with pytest.raises(IndexError):
        fetch_estat_value('dummy_id','dummy_id','dummy_id',date(2020,1,1))


def test_get_city_code_missing_municd(monkeypatch,disable_sleep):
    class MockResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                'results':{}
            }
    
    def mock_get(url,params):
        return MockResponse()
    monkeypatch.setattr(requests,'get',mock_get)

    with pytest.raises(KeyError):
        get_city_code(35.6895,139.6917)


def test_get_city_code_http_error(monkeypatch,disable_sleep):
    class MockResponse:
        def raise_for_status(self):
            raise requests.HTTPError("500 Server Error")
        
    def mock_get(url,params):
        return MockResponse()
    
    monkeypatch.setattr(requests,'get',mock_get)

    with pytest.raises(requests.HTTPError):
        get_city_code(35.6895,139.6917)

        

def test_get_elevation(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {'elevation':123.45}
    
    def mock_get(url,params):
        return MockResponse()
    
    monkeypatch.setattr(requests,'get',mock_get)
    monkeypatch.setattr(time,'sleep',lambda x: None)

    result = get_elevation(35.6895,139.6917)
    assert result == 123.0


def test_fetch_estat_value(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                'GET_STATS_DATA': {
                    'STATISTICAL_DATA': {
                        'DATA_INF': {
                            'VALUE': [
                                {'$': '1000'},
                                {'$': '2000'},
                                {'$': '3000'}
                            ]
                        }
                    }
                }
            }
    def mock_get(url, params):
        return MockResponse()
    
    monkeypatch.setattr(requests,'get',mock_get)
    monkeypatch.setattr(time,'sleep',lambda x: None)

    result = fetch_estat_value('dummy_id','dummy_cd','dummy_cat',date(2020,1,1))
    assert result == 3000.0

@pytest.mark.parametrize("input_date,expected_days",[(date(2023,3,31),-1),
                                                     (date(2023,4,1),0),
                                                     (date(2023,4,2),1)])
def test_get_days_from_start(input_date,expected_days):
    result = get_days_from_start(input_date)
    assert result == expected_days

def test_get_city_code(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                'results': {
                    'muniCd': '13101'
                }
            }
    def mock_get(url, params):
        return MockResponse()
    
    monkeypatch.setattr(requests,'get',mock_get)
    monkeypatch.setattr(time,'sleep',lambda x: None)

    result = get_city_code(35.6895,139.6917)
    assert result == '13101'