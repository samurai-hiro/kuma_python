import time
import requests
from datetime import datetime
from django.conf import settings


#キャッシュの時限チェック
def check_cache_time(cache_dict: dict, mydate: str) -> None:
    """
    キャッシュの時限チェックを行い、必要に応じてクリアします。

    Args:
        cache_dict (dict): キャッシュ辞書。
        mydate (str): 現在の年月日時（キー）。

    Returns:
        None
    """
    
    #キャッシュのキーに現在の年月日時がなければクリア
    if mydate not in cache_dict:
        cache_dict.clear()
        #現在の年月日時をキャッシュに追加
        cache_dict[mydate] = {}
  



#緯度経度から市区町村コードを取得
_city_code = {}
def get_city_code(lat: float, lon: float) -> int:
    """
    緯度経度から市区町村コードを取得します。

    Args:
        lat (float): 緯度。
        lon (float): 経度。

    Returns:
        int: 市区町村コード。

    Raises:
        ValueError: 日本のエリア外の場合。
        requests.RequestException: API通信エラー時。
    """
    kokudo_API = "https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress"
    key = (round(lat,5),round(lon,5))
    #キャッシュの時限チェック
    current_time = time.time()
    mydate = datetime.fromtimestamp(current_time).strftime('%Y%m%d%H')
    check_cache_time(_city_code,mydate)

    #キャッシュにあればそれを返す
    if key in _city_code[mydate]:
        return _city_code[mydate][key]
    
    params = {
        "lat": lat,
        "lon": lon
    }
    r = requests.get(kokudo_API,params=params)
    r.raise_for_status()
    #sleepを入れる
    time.sleep(0.5)
    
    #値が取得できているかチェック
    if 'results' not in r.json() or 'muniCd' not in r.json()['results']:
        raise ValueError("日本のエリアを選択してください")
    municd = r.json()['results']['muniCd']

    #キャッシュに保存
    _city_code[mydate][key] = municd

    return municd



#e-statから情報を取得
_estat_value = {}
def fetch_estat_value(STATS_DATA_ID: str, muni_cd: int, cat_code: str, date: 'datetime') -> float:
    """
    e-stat APIから指定した統計情報を取得します。

    Args:
        STATS_DATA_ID (str): 統計データID。
        muni_cd (int): 市区町村コード。
        cat_code (str): カテゴリコード。
        date (datetime): 日付。

    Returns:
        float: 統計値。

    Raises:
        requests.RequestException: API通信エラー時。
        ValueError: データ取得失敗時。
    """
    ESTAT_API = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
    #APIキーは環境変数から取得
    app_id = settings.ESTAT_API_ID
    
    key = (cat_code,muni_cd)
    #キャッシュの時限チェック
    current_time = time.time()
    mydate = datetime.fromtimestamp(current_time).strftime('%Y%m%d%H')
    check_cache_time(_estat_value,mydate)

    if key in _estat_value[mydate]:
        return _estat_value[mydate][key]
    
    year = int(date.year)
    params = {'appId':app_id,
            'statsDataId':STATS_DATA_ID,
            'cdArea':muni_cd,
            'cdCat01':cat_code,
            'time':year}

    r = requests.get(ESTAT_API,params=params)
    r.raise_for_status()

    values = (r.json()['GET_STATS_DATA']['STATISTICAL_DATA']['DATA_INF']['VALUE'])
    time.sleep(0.5)
    #キャッシュに保存
    estat_val = float(values[-1]['$'])
    _estat_value[mydate][key] = estat_val

    #入力したyearの直近の国勢調査の人口を取得（配列の最後が直近）
    return estat_val

#緯度経度から標高を取得
_elevation = {}
def get_elevation(lat: float, lon: float) -> float:
    """
    緯度経度から標高を取得します。

    Args:
        lat (float): 緯度。
        lon (float): 経度。

    Returns:
        float: 標高（m）。

    Raises:
        requests.RequestException: API通信エラー時。
        ValueError: 標高取得失敗時。
    """
    elevation_api = "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php"
    
    key = (round(lat,5),round(lon,5))
    #キャッシュの時限チェック
    current_time = time.time()
    mydate = datetime.fromtimestamp(current_time).strftime('%Y%m%d%H')
    check_cache_time(_elevation,mydate)

    #キャッシュにあればそれを返す
    if key in _elevation[mydate]:
        return _elevation[mydate][key]
    params = {
        "lat": lat,
        "lon": lon,
        'outtype':'JSON'
    }
    r = requests.get(elevation_api, params=params)
    r.raise_for_status()
    time.sleep(0.5)
    elevation = round(r.json()['elevation'],0)
    #キャッシュに保存
    _elevation[mydate][key] = elevation
    return (elevation)

def get_days_from_start(date: 'datetime.date') -> int:
    """
    基準日（2023/4/1）からの経過日数を計算します。

    Args:
        date (datetime.date): 対象日。

    Returns:
        int: 基準日からの経過日数。
    """
    base_daet = '2023/4/1'
    base_daet_obj = datetime.strptime(base_daet, '%Y/%m/%d').date()
    days_from_start = (date - base_daet_obj).days
    return (days_from_start)