import requests
import time
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

session = requests.Session()
#最大3回のリトライ(1秒、2秒、4秒のバックオフ)を設定し、
# サーバーエラー(500, 502, 503, 504)に対してリトライするようにします。
retries = Retry(total=3, backoff_factor=2, 
                status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount('http://', adapter)
session.mount('https://', adapter)

def predict_kuma(lat, lon, date):
    payload = {
        'lat': lat,
        'lon': lon,
        'date': date.isoformat(),
    }
    
    try:

        #初回接続
        r = session.post(settings.FASTAPI_KUMA_URL,
                         json=payload,
                         timeout=10
                         )
        #失敗したらリトライする(heroku起動待ち)
        if r.status_code != 200:
            time.sleep(3)
            r = session.post(settings.FASTAPI_KUMA_URL,
                         json=payload,
                         timeout=10
                         )
        r.raise_for_status()  # エラーが発生した場合に例外をスロー
        return r.json()
    except requests.exceptions.RequestException as e:
        return {'result': None, 'error': "APIサーバが起動中です。数秒後に再試行してください。"}

    except Exception as e:
        return {'result': None, 'error': str(e)}
    
    
        
        