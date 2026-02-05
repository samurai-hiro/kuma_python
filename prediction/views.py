from django.shortcuts import render
from .forms import PredictionForm
from services.population_density import get_city_code,fetch_estat_value,get_elevation,get_days_from_start
from src.preprocess import xTrainPrePro
import traceback
import joblib
from django.conf import settings
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from lightgbm import LGBMRegressor


# model_path = os.path.join(settings.BASE_DIR, 'prediction', 'model', 'kuma_analysis.joblib')
model_path = os.path.join(settings.BASE_DIR, 'prediction', 'model', 'kuma_analysis_LGBM.joblib')
pipemodel = joblib.load(model_path)

def prediction_view(request):
   
    
    if request.method == 'GET':
        form = PredictionForm()
        return render(request, 'home.html', {'form': form})
    elif request.method == 'POST':
        form = PredictionForm(request.POST)
        if form.is_valid():
            # Process the form data
            lat = form.cleaned_data['lat']
            lon = form.cleaned_data['lon']
            address = form.cleaned_data['address']
            place_name = form.cleaned_data['place_name']
            date = form.cleaned_data['date']

            #緯度経度から予測に必要な特徴量を取得して、
            #予測モデルに入れて予測を行う
            try:
                #緯度経度から市区町村コードを取得
                muni_cd = get_city_code(lat, lon)

                #市区町村コードから人口を取得
                population = fetch_estat_value(
                    STATS_DATA_ID='0000020201',
                    muni_cd=muni_cd,
                    cat_code='A1101',
                    date=date
                )
                
                #市区町村コードから土地面積を取得
                land_area = fetch_estat_value(
                    STATS_DATA_ID='0000020102',
                    muni_cd=muni_cd,
                    cat_code='B1101',
                    date=date
                )
                #人口密度を計算
                #人/km2
                population_density = round((population / land_area) *100, 8)
                # population_density = round(population / land_area, 8)
                #対数変換
                population_density = np.log(population_density)

                #標高を取得
                elevation = get_elevation(lat, lon)
                
                #基準日からの経過日数を特徴量に追加
                # days_from_start = get_days_from_start(date)
                
                #予測モデルに入れる特徴量をDataFrameにまとめる
                #prefecture,muninameは予測モデルでは使用しないので空文字で埋める
                feature_df = pd.DataFrame([{
                    'lat':lat,
                    'lon':lon,
                    'date':date,
                    'elevation':elevation,
                    'prefecture':'',
                    'municd':muni_cd,
                    'populationdensity':population_density,
                    'muniname':'',
                }])
                
                #特徴量の型を予測モデルに合わせる
                feature_df['municd'] = feature_df['municd'].astype(int)

                #予測を実行
                targetVal = pipemodel.predict(feature_df)
                targetVal = round(targetVal[0], 8)
                predict_result = f"{targetVal}"
                input_info = f"lat:{lat} lon:{lon} address:{address} place_name:{place_name} date:{date}"
                return render(request, 'home.html', {'form': form, 'predict_result': predict_result, 'input_info': input_info})
            except Exception as e:
                tb = traceback.format_exc()
                error_message = f"データ取得時にエラーが発生しました: {e}\n詳細:\n{tb}"
                input_info = f"lat:{lat} lon:{lon} address:{address} place_name:{place_name} date:{date}"
                return render(request, 'home.html',
                               {'form': form,'error_message': error_message,
                                'input_info': input_info})
        else:
            return render(request, 'home.html', {'form': form})