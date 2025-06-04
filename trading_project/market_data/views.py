from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from smart_api_integration.models import UserApiCredentials, UserApiTokens
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json, http.client

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

@csrf_exempt
@login_required
def place_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(data)
            
            token = data.get("symboltoken")
            symbol = data.get("tradingsymbol")
            quantity = int(data.get("quantity"))
            price = float(data.get("price", 0))
            order_type = data.get("order_type").upper()
            transactiontype = data.get("transactiontype").upper()

            # 🧠 Get user credentials and tokens
            
            user_cred = UserApiCredentials.objects.get(user=request.user)
            user_tokens = UserApiTokens.objects.get(user=request.user)

            # 🛡️ Prepare headers
            headers = {
                "Authorization": user_tokens.jwt_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "192.168.0.1",  # Optional: Replace dynamically if needed
                "X-ClientPublicIP": "49.207.123.101",  # Optional
                "X-MACAddress": "00:1B:44:11:3A:B7",  # Optional
                "X-PrivateKey": user_cred.api_key
            }

            if order_type == "STOPLOSS_LIMIT":
                # 📦 Prepare the payload
                payload = json.dumps({
                    "variety":"STOPLOSS",
                    "exchange":"NFO",
                    "tradingsymbol": symbol,
                    "symboltoken": token,
                    "quantity": quantity *75,
                    "transactiontype": transactiontype,
                    "ordertype": order_type,
                    "variety": "STOPLOSS",
                    "producttype": "CARRYFORWARD",
                    "duration": "DAY",
                    "price": float(data.get("price", 0)) if order_type in ["LIMIT", "STOPLOSS_LIMIT"] else 0,
                    "triggerprice": float(data.get("triggerprice", 0)) if order_type == "STOPLOSS_LIMIT" else 0
                })

            else:
                payload = json.dumps({
                    "variety":"NORMAL",
                    "tradingsymbol":symbol,
                    "symboltoken":token,
                    "transactiontype":transactiontype,
                    "exchange":"NFO",
                    "ordertype":order_type,
                    "producttype":"CARRYFORWARD",
                    "duration":"DAY",
                    "price": data.get("triggerprice", 0),
                    "quantity": quantity *75,
                    })
            print('Place order :- ' +payload)

            # 🌐 Make the request to Angel One
            conn = http.client.HTTPSConnection("apiconnect.angelone.in")
            conn.request("POST", "/rest/secure/angelbroking/order/v1/placeOrder", payload, headers)
            res = conn.getresponse()
            response_data = res.read().decode("utf-8")
            print(response_data)

            return JsonResponse({
                "status": "success",
                "message": "Order placed successfully",
                "response": json.loads(response_data)
            })

        except (UserApiCredentials.DoesNotExist, UserApiTokens.DoesNotExist):
            return JsonResponse({"status": "error", "message": "API credentials or tokens not found."}, status=403)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


@csrf_exempt
@login_required
def get_order_book(request):
    # Fetch the logged-in user's token
    user_cred = UserApiCredentials.objects.get(user=request.user)
    user_tokens = UserApiTokens.objects.get(user=request.user)

    conn = http.client.HTTPSConnection("apiconnect.angelone.in")

    payload = ""

    headers = {
        'Authorization': user_tokens.jwt_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': '127.0.0.1',                        
        'X-ClientPublicIP': '123.123.123.123',                 
        'X-MACAddress': '00:0a:95:9d:68:16',                   
        'X-PrivateKey': user_cred.api_key,
    }

    try:
        conn.request("GET", "/rest/secure/angelbroking/order/v1/getOrderBook", payload, headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        # print('Order Book :- '+json_data)
        return JsonResponse(json_data, safe=False)

    except Exception as e:
        return JsonResponse({"status": False, "message": "Error fetching order book", "error": str(e)})

@csrf_exempt
@login_required
def get_trade_book(request):
    # Fetch the logged-in user's credentials and tokens
    user_cred = UserApiCredentials.objects.get(user=request.user)
    user_tokens = UserApiTokens.objects.get(user=request.user)

    conn = http.client.HTTPSConnection("apiconnect.angelone.in")
    payload = ""

    headers = {
        'Authorization': user_tokens.jwt_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': '127.0.0.1',
        'X-ClientPublicIP': '123.123.123.123',
        'X-MACAddress': '00:0a:95:9d:68:16',
        'X-PrivateKey': user_cred.api_key,
    }

    try:
        conn.request("GET", "/rest/secure/angelbroking/order/v1/getTradeBook", payload, headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        # print('Trade Book :- ' + json_data)
        return JsonResponse(json_data, safe=False)

    except Exception as e:
        return JsonResponse({"status": False, "message": "Error fetching trade book", "error": str(e)})

