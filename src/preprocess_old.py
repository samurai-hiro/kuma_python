from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.preprocessing import OrdinalEncoder
import pandas as pd
import numpy as np


#データ前処理のクラス
class xTrainPrePro(BaseEstimator,TransformerMixin):
    def __init__(self):
        self.OrdinalEncoder = OrdinalEncoder(handle_unknown='use_encoded_value',
                                             unknown_value=-1)
        self.base_date = None #基準日に使用する

    def fit(self,x,y=None):

        #OrdinalEncoderのインスタンスを学習データで事前にfitしておく
        self.OrdinalEncoder.fit(x[['municd']])

         #dateをdatetimeに変換
        x['date'] = pd.to_datetime(x['date'])
        self.base_date = x['date'].min()

        return self

    def transform(self,x):
        x = x.copy()

        #municdをOrdinalEncoding
        x.loc[:,'municd'] = self.OrdinalEncoder.transform(x[['municd']])[:,0]
    
        #monthの列を追加(予測の時はfitが事前に呼ばれないので、ここでdatetimeに変換)
        if x['date'].dtypes == 'object':
            x['date'] = pd.to_datetime(x['date'])

        x['month'] = x['date'].dt.month

        #monthWeight
        month_weight = {'1':0,'2':0,'3':0,'4':1,'5':2,'6':4,'7':3,'8':3,'9':3,'10':4,'11':3,'12':2}
        x['monthWeight'] = x['month'].replace(month_weight).astype(int)

        #基準日からの経過日数を特徴量に追加
        x['days_from_start'] = (x['date'] - self.base_date).dt.days

        #populationdensityが正規分布になっていないので、対数計算を実施
        x['populationdensity'] = np.log(x['populationdensity'])

        #不要な特徴量を削除
        x = x.drop(['date','prefecture','muniname','month'],axis=1)

        return x

