from django.urls import path
from requests import api
from .views import api_market_movers, market_data_page, option_chain_page, api_search_contracts, api_trending_stocks, fo_stocks_view, get_credentials, get_market_quote

app_name = 'smart_api_integration'

urlpatterns = [
    path("market_data/", market_data_page, name="market_data_page"),
    path("option_chain/", option_chain_page, name="option_chain_page"),
    path("api/search_contracts/", api_search_contracts, name="api_search_contracts"),
    path("api/market_movers/", api_market_movers, name="api_market_movers"),
    path("api/trending_stocks/", api_trending_stocks, name="api_trending_stocks"),
    path('fo-stocks/', fo_stocks_view, name='fo_stocks'),
    path("api/get_credentials/", get_credentials, name="get_credentials"),
    path('api/quote/', get_market_quote, name='api_market_quote'),
    # path("place-order/", place_order, name="place_order"),
    # path("get-order-book", get_order_book, name="get_order_book"),
    # path('get-trade-book/', get_trade_book, name='get_trade_book'),
    # path('get-rms/', get_rms, name='get_rms'),

]
