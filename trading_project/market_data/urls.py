from django.urls import path
from .views import market_data_page, get_credentials, place_order, get_order_book, get_trade_book

urlpatterns = [
    path("market_data/", market_data_page, name="market_data_page"),
    path("api/get_credentials/", get_credentials, name="get_credentials"),
    path("place-order/", place_order, name="place_order"),
    path("get-order-book", get_order_book, name="get_order_book"),
    path('get-trade-book/', get_trade_book, name='get_trade_book'),

]
