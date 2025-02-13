# from django.contrib import admin
# from .models import MarketTokenSubscription, MarketData

# class MarketDataInline(admin.TabularInline):
#     model = MarketData
#     extra = 0

# class MarketTokenSubscriptionAdmin(admin.ModelAdmin):
#     list_display = ('user', 'token', 'exchange', 'mode', 'created_at')
#     search_fields = ('user__username', 'token', 'exchange')
#     inlines = [MarketDataInline]

# admin.site.register(MarketTokenSubscription, MarketTokenSubscriptionAdmin)
# admin.site.register(MarketData)
