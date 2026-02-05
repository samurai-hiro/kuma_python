from django.urls import path
from prediction.views import prediction_view


urlpatterns = [
    path('', prediction_view, name='prediction'),
]
