import time
import requests
from datetime import datetime

#緯度経度から市区町村コードを取得
_city_code = {}

def get_city_code(lat, lon):
    kokudo_API = "https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress"
    key = (round(lat,5),round(lon,5))
    if key in _city_code:
        return _city_code[key]
    
    params = {
        "lat": lat,
        "lon": lon
    }
    r = requests.get(kokudo_API,params=params)
    r.raise_for_status()
    #sleepを入れる
    time.sleep(0.5)
    municd = r.json()['results']['muniCd']

    #キャッシュに保存
    _city_code[key] = municd

    return municd



#e-statから情報を取得
_estat_value = {}
def fetch_estat_value(STATS_DATA_ID,muni_cd,cat_code,date):
    ESTAT_API = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
    app_id = '1c35de1de48f42f93f15a503ef1e7e7c6261c7a2'
    
    key = (cat_code,muni_cd)
    if key in _estat_value:
        return _estat_value[key]
    
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
    _estat_value[key] = estat_val

    #入力したyearの直近の国勢調査の人口を取得（配列の最後が直近）
    return estat_val

#緯度経度から標高を取得
_elevation = {}
def get_elevation(lat, lon):
    elevation_api = "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php"
    
    key = (round(lat,5),round(lon,5))
    if key in _elevation:
        return _elevation[key]
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
    _elevation[key] = elevation
    return (elevation)

def get_days_from_start(date):
    base_daet = '2023/4/1'
    base_daet_obj = datetime.strptime(base_daet, '%Y/%m/%d').date()
    days_from_start = (date - base_daet_obj).days
    return (days_from_start)