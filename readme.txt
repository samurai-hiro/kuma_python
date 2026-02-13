# 東京 クマ出没予測アプリ

## 開発の目的
各自治体は、クマの出没情報をデータとして公開しているが、
未来の出没の予測はしていません。
過去の出没情報を元に、日付と場所を入力して、
東京のクマ出没の危険性がどの程度なのかを可視化する
アプリケーションを開発したいと考えました。

## 概要
本アプリは、東京・埼玉・山梨エリアにおけるクマ出没の可能性を予測するWebアプリです。地図上で地点を選択し、日付を入力することで、機械学習モデルによる出没予測結果を表示します。

## 主な機能
- 地図上のクリックによる地点選択
- 緯度・経度・住所・場所名・日付の入力
- 予測結果の表示（1.0以上で出没可能性高）
- 入力情報の確認
- 免責事項ページの表示

## ディレクトリ構成
- `kuma/`  
  - `prediction/`：Djangoアプリ（フォーム、ビュー、テンプレート、モデル等）
  - `services/`：人口密度・標高等の取得サービス
  - `src/`：データ前処理
  - `model/`：機械学習モデルや学習済みモデルファイルを格納
  - `tests/`：ユニットテスト
- `Lib/`, `Scripts/`, `Include/`：仮想環境関連

## セットアップ方法

1. 仮想環境の有効化  
   Windows:
   ```sh
   .\kumavenv\Scripts\activate
   ```
   Mac/Linux:
   ```sh
   source kumavenv/bin/activate
   ```

2. 必要なパッケージのインストール
   ```sh
   pip install -r kuma/requirements.txt
   ```

3. データベースのマイグレーション
   ```sh
   cd kuma
   python manage.py migrate
   ```

4. サーバーの起動
   ```sh
   python manage.py runserver
   ```

## 使い方
1. ブラウザで `http://127.0.0.1:8000/` にアクセスします。
2. マップ上をクリックし、必要な情報を入力して「予測」ボタンを押します。
3. 予測結果と入力情報が表示されます。

## 注意事項
- 本アプリの予測結果は参考情報です。実際の行動判断は自治体・公的機関の情報をご確認ください。
- 詳細は[免責事項](http://127.0.0.1:8000/disclaimer/)をご覧ください。

## テスト
ユニットテストは以下で実行できます。
```sh
pytest kuma/tests/
```

## ライセンス
このアプリケーションはMITライセンスです。

---

### 主要ファイルリンク
- [kuma/prediction/views.py](kuma/prediction/views.py)
- [kuma/prediction/templates/home.html](kuma/prediction/templates/home.html)
- [kuma/services/population_density.py](kuma/services/population_density.py)
- [kuma/src/preprocess.py](kuma/src/preprocess.py)