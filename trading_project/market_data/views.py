from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from smart_api_integration.models import UserApiCredentials, UserApiTokens
from django.http import JsonResponse

@login_required
def market_data_page(request):
    """ Render the market data page where WebSocket will connect. """
    return render(request, "market_data.html")

@login_required
def get_credentials(request):
    """ Fetch SmartAPI credentials for the logged-in user. """
    try:
        user_cred = UserApiCredentials.objects.get(user=request.user)
        user_tokens = UserApiTokens.objects.get(user=request.user)
        
        return JsonResponse({
            "api_key": user_cred.api_key,
            "auth_token": user_tokens.jwt_token,
            "client_code": user_cred.client_id,
            "feed_token": user_tokens.feed_token
        })

    except (UserApiCredentials.DoesNotExist, UserApiTokens.DoesNotExist):
        return JsonResponse({"error": "Credentials not found"}, status=404)
