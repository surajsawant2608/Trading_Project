from django.db import models
from django.contrib.auth.models import User  # Assuming you're using Django's built-in User model
from django.utils.timezone import now


# Model to store API credentials for each user
class UserApiCredentials(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('locked', 'Locked'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=100, unique=True)
    passcode = models.CharField(max_length=100)
    api_key = models.CharField(max_length=255)
    otp_secret_key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"API Credentials for {self.user.username}"


# Model to store API tokens for each user
class UserApiTokens(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_credentials = models.ForeignKey(UserApiCredentials, on_delete=models.CASCADE)
    jwt_token = models.TextField()
    refresh_token = models.TextField()
    feed_token = models.TextField()
    last_connected = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"API Tokens for {self.user.username}"


# Model to store the user profile data
class UserProfile(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('not_fetched', 'Not Fetched'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    client_code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    mobile_no = models.CharField(max_length=20)
    exchanges = models.JSONField()
    products = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_fetched')  # Increased max_length

    def __str__(self):
        return f"Profile for {self.user.username}"