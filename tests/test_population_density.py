from datetime import date
from datetime import datetime
import requests
import time
import pytest
import services.population_density as pop_density

def test_get_elevation_http_error(monkeypatch, disable_sleep):
    pop_density._elevation.clear()

    monkeypatch.setattr(time, "time", lambda: 1706755200)

    class MockResponse:
        def raise_for_status(self):
            raise requests.HTTPError("500 Server Error")

    def mock_get(url, params):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    with pytest.raises(requests.HTTPError):
        pop_density.get_elevation(35.0, 139.0)



def test_get_elevation_cache_hit(monkeypatch, disable_sleep):
    pop_density._elevation.clear()

    fixed_time = 1706755200
    monkeypatch.setattr(time, "time", lambda: fixed_time)

    mydate = datetime.fromtimestamp(fixed_time).strftime("%Y%m%d%H")
    key = (35.0, 139.0)

    pop_density._elevation[mydate] = {key: 456.0}

    def mock_get(*args, **kwargs):
        raise AssertionError("API should not be called on cache hit")

    monkeypatch.setattr(requests, "get", mock_get)

    result = pop_density.get_elevation(35.0, 139.0)

    assert result == 456.0

def test_get_elevation_first_call(monkeypatch, disable_sleep):
    pop_density._elevation.clear()

    # 時刻固定（2024-02-01 09:00）
    monkeypatch.setattr(time, "time", lambda: 1706755200)

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"elevation": 123.4}

    def mock_get(url, params):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    result = pop_density.get_elevation(35.0, 139.0)

    assert result == 123.0

    mydate = datetime.fromtimestamp(1706755200).strftime("%Y%m%d%H")
    key = (35.0, 139.0)

    assert key in pop_density._elevation[mydate]
    assert pop_density._elevation[mydate][key] == 123.0

def test_fetch_estat_value_cache_hit(monkeypatch):
    # --- 固定時刻 ---
    fixed_time = 1706787600  # 2024-02-01 09:00

    monkeypatch.setattr(pop_density.time, "time", lambda: fixed_time)
    
    # --- キャッシュを事前投入 ---
    mydate = datetime.fromtimestamp(fixed_time).strftime('%Y%m%d%H')
    key = ("A1101", "13101")
    pop_density._estat_value.clear()
    pop_density._estat_value[mydate] = {key: 999.0}

    # --- API が呼ばれたら失敗 ---
    def mock_get(*args, **kwargs):
        raise AssertionError("API should not be called on cache hit")

    monkeypatch.setattr(pop_density.requests, "get", mock_get)

    # --- 実行 ---
    result = pop_density.fetch_estat_value(
        STATS_DATA_ID="0000010101",
        muni_cd="13101",
        cat_code="A1101",
        date=date(2024, 1, 1),
    )

    # --- 検証 ---
    assert result == 999.0



def test_fetch_estat_value_first_call(monkeypatch):
    # --- グローバルキャッシュ初期化 ---
    pop_density._estat_value.clear()

    # --- 固定時刻 ---
    fixed_time = 1706787600  # 2024-02-01 09:00:00

    monkeypatch.setattr(pop_density.time, "time", lambda: fixed_time)

    # --- sleep 無効化 ---
    monkeypatch.setattr(pop_density.time, "sleep", lambda x: None)

    # --- requests.get のモック ---
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "GET_STATS_DATA": {
                    "STATISTICAL_DATA": {
                        "DATA_INF": {
                            "VALUE": [
                                {"$": "100"},
                                {"$": "200"},  # ←最後が使われる
                            ]
                        }
                    }
                }
            }

    def mock_get(url, params):
        return MockResponse()

    monkeypatch.setattr(pop_density.requests, "get", mock_get)

    # --- 実行 ---
    result = pop_density.fetch_estat_value(
        STATS_DATA_ID="0000010101",
        muni_cd="13101",
        cat_code="A1101",
        date=date(2024,1,1),
    )

    # --- 検証 ---
    assert result == 200.0



def test_check_cache_time_clear():
    cache = {
        "2024020109": {"a": 1}
    }

    # 別の時刻 → クリアされる
    pop_density.check_cache_time(cache, "2024020110")

    assert cache == {"2024020110": {}}

def test_check_cache_time_keep():
    cache = {
        "2024020109": {"a": 1}
    }

    # 同じ時刻 → クリアされない
    pop_density.check_cache_time(cache, "2024020109")

    assert "2024020109" in cache

def test_get_city_code_first_call(monkeypatch, disable_sleep):

    pop_density._city_code.clear()

    # 時刻固定
    monkeypatch.setattr(time, "time", lambda: 1706755200)  # 2024-02-01 09:00

    class MockResponse:
        def raise_for_status(self): pass
        def json(self):
            return {"results": {"muniCd": "13101"}}

    monkeypatch.setattr(
        requests,
        "get",
        lambda url, params: MockResponse()
    )

    result = pop_density.get_city_code(35.0, 139.0)

    assert result == "13101"
    assert len(pop_density._city_code) == 1

def test_get_city_code_cache_hit(monkeypatch, disable_sleep):

    pop_density._city_code.clear()

    # 時刻固定（2024-02-01 09:00）
    fixed_time = 1706755200
    monkeypatch.setattr(time, "time", lambda: fixed_time)
    mydate = datetime.fromtimestamp(fixed_time).strftime('%Y%m%d%H')
    key = (round(35.0, 5), round(139.0, 5))

    # キャッシュを正しく仕込む
    pop_density._city_code[mydate] = {key: "13101"}
    # APIが呼ばれたら即失敗させる
    def mock_get(*args, **kwargs):
        raise AssertionError("API should not be called on cache hit")

    monkeypatch.setattr(requests, "get", mock_get)
    result = pop_density.get_city_code(35.0, 139.0)

    assert result == "13101"

def test_get_city_code_cache_expired(monkeypatch, disable_sleep):

    pop_density._city_code.clear()

    # 古いキャッシュ
    pop_density._city_code["2024020108"] = {
        (35.0, 139.0): "OLD"
    }

    # 新しい時刻
    monkeypatch.setattr(time, "time", lambda: 1706755200)
    class MockResponse:
        def raise_for_status(self): pass
        def json(self):
            return {"results": {"muniCd": "NEW"}}

    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse())

    result = pop_density.get_city_code(35.0, 139.0)

    assert result == "NEW"
    assert "2024020108" not in pop_density._city_code


 

   
