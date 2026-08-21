"""
load_model.py

このファイルは、LightGBMモデルの読み込みと前処理パイプラインのインポートを行います。
Django設定からモデルパスを取得し、joblibを用いて学習済みモデルをロードします。
"""
import os  # OS操作用モジュール

import joblib  # モデルの保存・読み込み用
from django.conf import settings  # Django設定のインポート

model_path = os.path.join(settings.BASE_DIR, 'prediction', 'model', 'kuma_analysis_LGBM.joblib')  # モデルファイルのパスをDjango設定から取得
pipemodel = joblib.load(model_path)  # 学習済みモデルのロード
