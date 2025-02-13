from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User 
from django.contrib.auth.decorators import login_required
from .models import UserApiCredentials, UserProfile, UserApiTokens
from .forms import UserLoginForm,ApiDetailsForm
from django.utils import timezone
from SmartApi import SmartConnect  # Assuming SmartConnect is the API client
import pyotp

def user_login(request):
    """
    Handle user login with username and passcode.
    If the user doesn't exist, redirect to api_details page to save credentials.
    """
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            passcode = form.cleaned_data['passcode']
            
            # Check if user exists
            try:
                user = User.objects.get(username=username)

                try:
                    user_credentials = UserApiCredentials.objects.get(user=user)
                    
                    # Authenticate user with passcode (assuming simple passcode matching)
                    if user_credentials.passcode == passcode:
                        
                        login(request, user)
                        # Proceed to token check and dashboard
                        return redirect('smart_api_integration:check_token_and_dashboard')
                        
                    else:
                        messages.error(request, "Incorrect passcode.")
                except UserApiCredentials.DoesNotExist:
                    messages.error(request, "User not found. Please provide API credentials.")
                    return redirect('smart_api_integration:api_details')
            except User.DoesNotExist:
                # Redirect admin to add the user
                messages.info(request, "User not found. Please contact admin.")            

    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def api_details(request):
    """
    Handle the page to input API credentials (username, passcode, api_key, otp_secret_key).
    """
    if request.method == "POST":
        form = ApiDetailsForm(request.POST)
        if form.is_valid():
            # Save the credentials in the UserApiCredentials model
            user_credentials = form.save(commit=False)
            user_credentials.user = request.user  # Associate with the current user
            user_credentials.save()

            # Generate OTP (just for verification)
            otp = pyotp.TOTP(user_credentials.otp_secret_key).now()

            messages.success(request, "API credentials saved successfully.")
            return redirect('smart_api_integration:login_page')  # Redirect to login page

        else:
            messages.error(request, "There was an error in the form. Please try again.")
    else:
        form = ApiDetailsForm()

    return render(request, 'api_details.html', {'form': form})

@login_required
def check_token_and_dashboard(request):
    """
    Check if the tokens are valid. If expired, reconnect to generate new tokens.
    Fetch and display the user's profile on the dashboard.
    """
    try:
        # Fetch user credentials
        user_credentials = UserApiCredentials.objects.get(user=request.user)

        # Check if the tokens are valid (if tokens exist)
        try:
            user_tokens = UserApiTokens.objects.get(user=user_credentials.user)
            if user_tokens.expires_at < timezone.now():  # Token expired
                messages.warning(request, "Tokens expired. Reconnecting...")
                # Call to regenerate tokens
                return redirect('smart_api_integration:reconnect_and_fetch_profile')
            else:
                # Tokens are valid, move to dashboard
                return redirect('smart_api_integration:profile')
        except UserApiTokens.DoesNotExist:
            # No tokens found, reconnect to generate tokens
            return redirect('smart_api_integration:reconnect_and_fetch_profile')

    except UserApiCredentials.DoesNotExist:
        messages.error(request, "User credentials not found. Please provide API details.")
        return redirect('smart_api_integration:api_details')

@login_required
def reconnect_and_fetch_profile(request):
    """
    Reconnect to the API, generate new tokens, fetch profile, and redirect to dashboard.
    """
    try:
        user_credentials = UserApiCredentials.objects.get(user=request.user)
        otp = pyotp.TOTP(user_credentials.otp_secret_key).now()
        connection_object = SmartConnect(api_key=user_credentials.api_key)
        session_data = connection_object.generateSession(
            user_credentials.client_id,
            user_credentials.passcode,
            otp
        )
        
        # Save new tokens
        jwt_token = session_data['data']['jwtToken']
        refresh_token = session_data['data']['refreshToken']
        feed_token = connection_object.getfeedToken()

        # Correctly associate user_credentials and update existing record if found
        user_tokens, created = UserApiTokens.objects.update_or_create(
            user_credentials=user_credentials,
            defaults={
                "user": user_credentials.user,
                "jwt_token": jwt_token,
                "refresh_token": refresh_token,
                "feed_token": feed_token,
                "expires_at": timezone.now() + timezone.timedelta(hours=24)
            }
        )

        # Fetch and update profile
        profile_response = connection_object.getProfile(refresh_token)
        if profile_response.get('status'):
            profile_data = profile_response.get('data', {})
            UserProfile.objects.update_or_create(
                user=user_credentials.user,
                defaults={
                    "client_code": profile_data.get("clientcode", ""),
                    "name": profile_data.get("name", ""),
                    "email": profile_data.get("email", ""),
                    "mobile_no": profile_data.get("mobileno", ""),
                    "exchanges": profile_data.get("exchanges", []),
                    "products": profile_data.get("products", []),
                },
            )
        
        messages.success(request, "Successfully reconnected and fetched profile.")
        return redirect('smart_api_integration:profile')

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('smart_api_integration:api_details')

@login_required
def profile(request):
    """
    Display the user profile data on the dashboard.
    """
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None  # Handle case where profile doesn't exist yet

    return render(request, 'profile.html', {'user_profile': user_profile})