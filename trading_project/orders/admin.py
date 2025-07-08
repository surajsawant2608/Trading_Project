from django.contrib import admin
from .models import OpenPosition

@admin.register(OpenPosition)
class OpenPositionAdmin(admin.ModelAdmin):
    list_display = [
        'user_id',
        'order_id',
        'status_code',
        'order_status',
        'error_message',
        'variety',
        'ordertype',
        'ordertag',
        'producttype',
        'price',
        'triggerprice',
        'quantity',
        'disclosedquantity',
        'duration',
        'squareoff',
        'stoploss',
        'trailingstoploss',
        'tradingsymbol',
        'transactiontype',
        'exchange',
        'symboltoken',
        'instrumenttype',
        'strikeprice',
        'optiontype',
        'expirydate',
        'lotsize',
        'cancelsize',
        'averageprice',
        'filledshares',
        'unfilledshares',
        'status',
        'orderstatus',
        'text',
        'updatetime',
        'exchtime',
        'exchorderupdatetime',
        'fillid',
        'filltime',
        'parentorderid',
        'created_at',
    ]

    search_fields = ['order_id', 'user_id', 'tradingsymbol', 'symboltoken']
    list_filter = ['order_status', 'transactiontype', 'exchange', 'ordertype', 'producttype']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
