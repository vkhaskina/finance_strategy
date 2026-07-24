from django.urls import path
from .views import strategy_data, strategy_test

app_name = "api"

urlpatterns = [
    path('get_signals/', strategy_data, name='signals'),
    path('test_strategy/', strategy_test, name='test')
]
