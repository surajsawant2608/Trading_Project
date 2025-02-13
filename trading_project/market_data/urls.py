from django.urls import path
from .views import market_data_page, get_credentials

urlpatterns = [
    path("market_data/", market_data_page, name="market_data_page"),
    path("api/get_credentials/", get_credentials, name="get_credentials"),
]
