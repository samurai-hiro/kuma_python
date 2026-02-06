from django.urls import path
from prediction.views import prediction_view, disclaimer_view


urlpatterns = [
    path('', prediction_view, name='prediction'),
    path('disclaimer/', disclaimer_view, name='disclaimer'),
]
