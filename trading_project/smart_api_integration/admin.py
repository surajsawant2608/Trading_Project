from django.contrib import admin
from .models import UserApiCredentials, UserApiTokens, UserProfile

@admin.register(UserApiCredentials)
class UserApiCredentialsAdmin(admin.ModelAdmin):
    list_display = ('user', 'client_id', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('user__username', 'client_id', 'api_key')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'client_id', 'passcode', 'api_key', 'otp_secret_key', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(UserApiTokens)
class UserApiTokensAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'last_connected', 'expires_at')
    list_filter = ('status', 'last_connected', 'expires_at')
    search_fields = ('user__username', 'jwt_token', 'refresh_token')
    ordering = ('-last_connected',)
    readonly_fields = ('last_connected', 'expires_at')
    fieldsets = (
        ('User and Token Information', {
            'fields': ('user', 'user_credentials', 'jwt_token', 'refresh_token', 'feed_token', 'status')
        }),
        ('Timestamps', {
            'fields': ('last_connected', 'expires_at')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'email', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('user__username', 'name', 'email', 'mobile_no')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'client_code', 'name', 'email', 'mobile_no', 'status')
        }),
        ('Exchanges and Products', {
            'fields': ('exchanges', 'products')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
