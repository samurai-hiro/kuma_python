from django.urls import path

from prediction.views import disclaimer_view, prediction_view

urlpatterns = [
    path('', prediction_view, name='prediction'),
    path('disclaimer/', disclaimer_view, name='disclaimer'),
]
