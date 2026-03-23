from django.shortcuts import render
from .forms import PredictionForm
from services.fastapi_client import predict_kuma
import traceback

def prediction_view(request) -> 'HttpResponse':
    """
    予測フォームの表示と予測処理を行うビュー。

    Args:
        request: DjangoのHttpRequestオブジェクト。

    Returns:
        HttpResponse: home.htmlテンプレートのレンダリング結果。

    Raises:
        ValueError: データ取得時の値エラー。
        Exception: その他の予測処理中の例外。
    """
   
    
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
                result = predict_kuma(lat, lon, date)
                input_info = f"lat:{lat} lon:{lon} address:{address} place_name:{place_name} date:{date}"

                #予測結果にエラーが含まれているか、結果がNoneの場合はエラーメッセージを表示し、
                #そうでない場合は予測結果を表示する
                if result.get('error') or result.get('result') is None:
                    return render(request, 'home.html',
                               {'form': form,'error_message': result.get('error'),
                                'input_info': input_info})
                else:
                    targetVal = round(result.get('result'), 8)
                    predict_result = f"{targetVal}"
                    return render(request, 'home.html', {'form': form, 'predict_result': predict_result, 'input_info': input_info})               
            
            except Exception as e:
                error_message = f"データ取得時にエラーが発生しました: {e}"
                input_info = f"lat:{lat} lon:{lon} address:{address} place_name:{place_name} date:{date}"
            
                return render(request, 'home.html',
                               {'form': form,'error_message': error_message,
                                'input_info': input_info})
        else:
            return render(request, 'home.html', {'form': form})

def disclaimer_view(request) -> 'HttpResponse':
    """
    免責事項ページを表示するビュー。

    Args:
        request: DjangoのHttpRequestオブジェクト。

    Returns:
        HttpResponse: disclaimer.htmlテンプレートのレンダリング結果。
    """
    return render(request,'disclaimer.html')
