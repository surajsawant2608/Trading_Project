from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from smart_api_integration.models import UserApiCredentials, UserApiTokens
from smart_api_integration.utils import SmartApiClientFactory
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json, http.client
from django.conf import settings
import os, csv


# ============================================================
# SYMBOL-INDEXED SCRIP MASTER (LOAD ONCE)
# ============================================================
SYMBOL_MASTER = {}

try:
    with open("/home/suraj/Suraj/Django/Trading_Project/trading_project/market_data/static/OpenAPIScripMaster.json") as f:
        for item in json.load(f):
            # Index by symbol (e.g., 'SBIN-EQ') for fast lookup
            SYMBOL_MASTER[item["symbol"]] = item
except Exception as e:
    print(f"Failed to load Scrip Master for Quotes: {e}")


# ============================================================
# MARKET QUOTE API
# ============================================================
@csrf_exempt
def get_market_quote(request):
    if request.method != "GET":
        return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "Unauthenticated"}, status=401)

    # 1. Obtain an authenticated client via the gateway
    try:
        smart_client = SmartApiClientFactory.get_client(request.user)
    except PermissionError as e:
        return JsonResponse({"status": False, "message": str(e), "redirect_url": "/smart-api/api-details/"}, status=403)
    except Exception as e:
        return JsonResponse({"status": False, "message": f"Auth error: {str(e)}"}, status=500)

    # 2. Parse & resolve exchange tokens
    symbols_param = request.GET.get("symbols", "")
    if not symbols_param:
        return JsonResponse({"status": False, "message": "Missing symbols parameter"}, status=400)

    requested_symbols = [s.strip() for s in symbols_param.split(",") if s.strip()][:50]
    exchange_tokens = {}

    for sym in requested_symbols:
        scrip = SYMBOL_MASTER.get(sym)
        if scrip:
            exch = scrip.get("exch_seg", "NSE")
            token = str(scrip.get("token")).strip()
            if exch not in exchange_tokens:
                exchange_tokens[exch] = []
            exchange_tokens[exch].append(token)

    if not exchange_tokens:
        return JsonResponse({"status": False, "message": "No symbols resolved."}, status=404)

    # 3. Call endpoint directly using smart_client
    try:
        data = smart_client.getMarketData(mode="FULL", exchangeTokens=exchange_tokens)

        # Self-healing check: if broker reports invalid token, flag in DB for next request
        if data and data.get("errorCode") in ["AG8001", "AB8050", "AB8051"]:
            SmartApiClientFactory.flag_token_failed(request.user)
            return JsonResponse({"status": False, "message": "Session invalidated, re-trying..."}, status=401)

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({"status": False, "message": f"Quote fetch error: {str(e)}"}, status=500)
# @login_required
def market_data_page(request):
    """ Render the market data page where WebSocket will connect. """
    return render(request, "dashboard.html")

def fo_stocks_view(request):
    stocks = []
    
    # Ensure FO_STOCK_LIST.txt is placed in a known directory, e.g., your app's static folder or root.
    file_path = os.path.join(settings.BASE_DIR, 'static/FO_STOCK_LIST.txt')
    print(file_path)
    
    try:
        with open(file_path, 'r') as f:
            # The file uses tab separation based on the provided sample
            reader = csv.reader(f, delimiter='\t')
            next(reader) # Skip the header row (S. NO. UNDERLYING SYMBOL)
            
            for row in reader:
                if len(row) >= 3:
                    stocks.append({
                        'sno': row[0].strip(),
                        'name': row[1].strip(),
                        'symbol': row[2].strip(),
                        # Mock data placeholders for columns present in the UI but missing in the txt file
                        'ltp': '0.00',
                        'mcap': '0.00',
                        'pe': '0.00',
                        'high52': '0.00',
                        'low52': '0.00'
                    })
    except FileNotFoundError:
        pass # Handle gracefully in production

    context = {
        'stocks': stocks
    }
    
    # Optional: allow HTMX partial swaps if you want to load this directly into the workspace
    if request.headers.get('HX-Request'):
        return render(request, "fo_stocks_content.html", context)
        
    return render(request, "fo_stocks_content.html", context)

def option_chain_page(request):
    spot_price = 22776.10

    # Structured strike data matching the screenshot
    strikes_data = [
        {
            "strike": 22400, "call_oi": "9,85,855", "call_oi_chg": "-57.28%", "call_vol": "293.35 L", "call_vol_bar": 15, "call_ltp": 376.15, "call_ltp_pct": "+103.49%",
            "put_ltp": 0.05, "put_ltp_pct": "-99.84%", "put_vol": "4301.36 L", "put_vol_bar": 35, "put_oi": "83,21,300", "put_oi_chg": "-27.35%", "put_oi_badge": None
        },
        {
            "strike": 22450, "call_oi": "5,95,660", "call_oi_chg": "-66.74%", "call_vol": "407.66 L", "call_vol_bar": 20, "call_ltp": 326.15, "call_ltp_pct": "+122.55%",
            "put_ltp": 0.05, "put_ltp_pct": "-99.88%", "put_vol": "4312.89 L", "put_vol_bar": 36, "put_oi": "61,47,375", "put_oi_chg": "+1.44%", "put_oi_badge": None
        },
        {
            "strike": 22500, "call_oi": "11,59,210", "call_oi_chg": "-85.28%", "call_vol": "1639.68 L", "call_vol_bar": 35, "call_ltp": 276.20, "call_ltp_pct": "+146.83%",
            "put_ltp": 0.05, "put_ltp_pct": "-99.92%", "put_vol": "8400.09 L", "put_vol_bar": 50, "put_oi": "1,05,45,535", "put_oi_chg": "-13.78%", "put_oi_badge": None
        },
        {
            "strike": 22550, "call_oi": "13,40,365", "call_oi_chg": "-79.30%", "call_vol": "2361.32 L", "call_vol_bar": 42, "call_ltp": 226.05, "call_ltp_pct": "+173.67%",
            "put_ltp": 0.05, "put_ltp_pct": "-99.94%", "put_vol": "9142.10 L", "put_vol_bar": 55, "put_oi": "94,05,955", "put_oi_chg": "+80.31%", "put_oi_badge": None
        },
        {
            "strike": 22600, "call_oi": "26,73,775", "call_oi_chg": "-74.89%", "call_vol": "7201.20 L", "call_vol_bar": 65, "call_ltp": 176.10, "call_ltp_pct": "+198.47%",
            "put_ltp": 0.05, "put_ltp_pct": "-99.95%", "put_vol": "15351.49 L", "put_vol_bar": 70, "put_oi": "1,45,21,195", "put_oi_chg": "+186.31%", "put_oi_badge": "OI 4"
        },
        {
            "strike": 22650, "call_oi": "28,17,295", "call_oi_chg": "-56.69%", "call_vol": "9345.36 L", "call_vol_bar": 75, "call_ltp": 126.30, "call_ltp_pct": "+217.74%",
            "put_ltp": 0.05, "put_ltp_pct": "-99.96%", "put_vol": "14241.74 L", "put_vol_bar": 68, "put_oi": "1,55,87,260", "put_oi_chg": "+1,253.52%", "put_oi_badge": "OI 3"
        },
        {
            "strike": 22700, "call_oi": "1,07,46,060", "call_oi_chg": "-3.43%", "call_oi_badge": "OI 4", "call_vol": "18751.26 L", "call_vol_bar": 90, "call_ltp": 75.95, "call_ltp_pct": "+188.24%",
            "put_ltp": 0.05, "put_ltp_pct": "-99.97%", "put_vol": "16643.52 L", "put_vol_bar": 78, "put_oi": "2,64,65,660", "put_oi_chg": "+1,106.34%", "put_oi_badge": "OI 1"
        },
        {
            "strike": 22750, "call_oi": "1,03,91,225", "call_oi_chg": "+68.85%", "call_oi_badge": "OI 5", "call_vol": "16739.21 L", "call_vol_bar": 85, "call_ltp": 26.05, "call_ltp_pct": "+54.60%",
            "put_ltp": 0.05, "put_ltp_pct": "-99.98%", "put_vol": "6612.90 L", "put_vol_bar": 45, "put_oi": "1,84,80,150", "put_oi_chg": "+2,503.09%", "put_oi_badge": "OI 2"
        },
        # --- SPOT PRICE LEVEL: 22,776.10 ---
        {
            "strike": 22800, "call_oi": "2,20,79,330", "call_oi_chg": "+53.57%", "call_oi_badge": "OI 1", "call_vol": "14909.16 L", "call_vol_bar": 80, "call_ltp": 0.05, "call_ltp_pct": "-99.54%",
            "put_ltp": 23.85, "put_ltp_pct": "-90.76%", "put_vol": "3001.32 L", "put_vol_bar": 28, "put_oi": "54,39,720", "put_oi_chg": "+316.98%", "put_oi_badge": None
        },
        {
            "strike": 22850, "call_oi": "83,95,920", "call_oi_chg": "+33.97%", "call_vol": "6516.48 L", "call_vol_bar": 52, "call_ltp": 0.05, "call_ltp_pct": "-99.32%",
            "put_ltp": 73.75, "put_ltp_pct": "-75.74%", "put_vol": "609.48 L", "put_vol_bar": 15, "put_oi": "10,22,970", "put_oi_chg": "+347.99%", "put_oi_badge": None
        },
        {
            "strike": 22900, "call_oi": "1,13,12,275", "call_oi_chg": "+1.01%", "call_oi_badge": "OI 3", "call_vol": "5707.39 L", "call_vol_bar": 48, "call_ltp": 0.05, "call_ltp_pct": "-99.04%",
            "put_ltp": 123.70, "put_ltp_pct": "-64.92%", "put_vol": "354.44 L", "put_vol_bar": 10, "put_oi": "8,87,445", "put_oi_chg": "+75.47%", "put_oi_badge": None
        },
        {
            "strike": 22950, "call_oi": "47,85,430", "call_oi_chg": "+1.50%", "call_vol": "2826.61 L", "call_vol_bar": 30, "call_ltp": 0.05, "call_ltp_pct": "-98.75%",
            "put_ltp": 173.55, "put_ltp_pct": "-56.52%", "put_vol": "71.18 L", "put_vol_bar": 5, "put_oi": "2,68,710", "put_oi_chg": "-25.75%", "put_oi_badge": None
        },
        {
            "strike": 23000, "call_oi": "1,31,36,370", "call_oi_chg": "-10.41%", "call_oi_badge": "OI 2", "call_vol": "2379.92 L", "call_vol_bar": 26, "call_ltp": 0.05, "call_ltp_pct": "-98.39%",
            "put_ltp": 223.45, "put_ltp_pct": "-50.24%", "put_vol": "102.49 L", "put_vol_bar": 6, "put_oi": "7,83,185", "put_oi_chg": "-25.15%", "put_oi_badge": None
        },
        {
            "strike": 23050, "call_oi": "49,37,725", "call_oi_chg": "+8.79%", "call_vol": "807.17 L", "call_vol_bar": 12, "call_ltp": 0.05, "call_ltp_pct": "-97.87%",
            "put_ltp": 273.40, "put_ltp_pct": "-44.88%", "put_vol": "13.64 L", "put_vol_bar": 3, "put_oi": "1,92,205", "put_oi_chg": "-17.38%", "put_oi_badge": None
        },
    ]

    context = {
        "spot_price": spot_price,
        "strikes_data": strikes_data,
    }

    # Support HTMX partial swap without wrapping in base.html
    if request.headers.get('HX-Request'):
        return render(request, "market/option_chain_content.html", context)
    return render(request, "option_chain_content.html", context)

def api_search_contracts(request):
    query = request.GET.get('query', '').strip().upper()
    if not query:
        return HttpResponse("")

    # Simulated matching list from exchange master / contract file
    sample_contracts = [
        {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "token": "2885", "exch": "NSE", "segment": "EQ"},
        {"symbol": "TCS", "name": "Tata Consultancy Services", "token": "11536", "exch": "NSE", "segment": "EQ"},
        {"symbol": "INFY", "name": "Infosys Ltd", "token": "1594", "exch": "NSE", "segment": "EQ"},
        {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "token": "1333", "exch": "NSE", "segment": "EQ"},
        {"symbol": "NIFTY26OCT22400CE", "name": "NIFTY 22400 CALL", "token": "45201", "exch": "NFO", "segment": "OPT"},
    ]

    results = [c for c in sample_contracts if query in c["symbol"] or query in c["name"].upper()][:8]

    return render(request, "components/search_results_partial.html", {"results": results})

def api_market_movers(request):
    mover_type = request.GET.get('type', 'gainers')
    
    # In a real app, query your TimescaleDB or cache here.
    if mover_type == 'gainers':
        data = [
            {"name": "Orient Cables", "symbol": "O", "color": "bg-white text-black", "ltp": 405.00, "chg": 133.00, "pct": 48.90, "trend": "up"},
            {"name": "Sharp Chucks", "symbol": "S", "color": "bg-red-800 text-white", "ltp": 100.20, "chg": 16.70, "pct": 20.00, "trend": "up"},
        ]
    elif mover_type == 'losers':
        data = [
            {"name": "Paytm", "symbol": "P", "color": "bg-blue-400 text-white", "ltp": 412.00, "chg": -28.00, "pct": -6.36, "trend": "down"},
        ]
        
    return render(request, "components/partials/market_movers_list.html", {"movers": data})

def api_trending_stocks(request):
    selected_filter = request.GET.get('filter', 'news')

    # Data dictionary for all filter tabs
    trending_data = {
        'news': [
            {"symbol": "IREDA", "name": "IREDA", "logo": "I", "logo_bg": "bg-[#181818] text-white", "ltp": 109.00, "chg": -2.00, "pct": -1.80, "trend": "down"},
            {"symbol": "ITC", "name": "ITC", "logo": "A", "logo_bg": "bg-[#181818] text-blue-400", "ltp": 268.90, "chg": 13.00, "pct": 5.08, "trend": "up"},
            {"symbol": "BSE", "name": "BSE", "logo": "BSE", "logo_bg": "bg-blue-600 text-white text-[8px]", "ltp": 3179.60, "chg": 133.60, "pct": 4.39, "trend": "up"},
            {"symbol": "HDFCBANK", "name": "HDFC Bank", "logo": "+", "logo_bg": "bg-blue-900 text-red-400", "ltp": 704.80, "chg": -16.40, "pct": -2.27, "trend": "down"},
            {"symbol": "VEDL", "name": "Vedanta", "logo": "V", "logo_bg": "bg-[#181818] text-teal-400", "ltp": 255.05, "chg": 3.00, "pct": 1.19, "trend": "up"},
        ],
        'traded': [
            {"symbol": "RELIANCE", "name": "Reliance Ind.", "logo": "R", "logo_bg": "bg-[#181818] text-blue-500", "ltp": 2980.10, "chg": 24.50, "pct": 0.83, "trend": "up"},
            {"symbol": "TATASTEEL", "name": "Tata Steel", "logo": "T", "logo_bg": "bg-[#181818] text-blue-400", "ltp": 178.14, "chg": 0.14, "pct": 0.08, "trend": "up"},
        ],
        'bought_mtf': [
            {"symbol": "INFY", "name": "Infosys Ltd", "logo": "I", "logo_bg": "bg-[#181818] text-blue-400", "ltp": 1885.00, "chg": -14.20, "pct": -0.75, "trend": "down"},
        ],
        'invested': [
            {"symbol": "TCS", "name": "Tata Consultancy", "logo": "T", "logo_bg": "bg-[#181818] text-white", "ltp": 4210.00, "chg": 39.40, "pct": 0.94, "trend": "up"},
        ],
        'searched': [
            {"symbol": "ZOMATO", "name": "Zomato Ltd", "logo": "Z", "logo_bg": "bg-red-600 text-white", "ltp": 272.50, "chg": 8.20, "pct": 3.10, "trend": "up"},
        ]
    }

    stocks = trending_data.get(selected_filter, trending_data['news'])

    return render(request, "components/partials/trending_stocks_list.html", {
        "stocks": stocks,
        "selected_filter": selected_filter
    })

# @login_required
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

# @csrf_exempt
# @login_required
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
                    "quantity": quantity *65,
                    "transactiontype": transactiontype,
                    "ordertype": order_type,
                    "variety": "STOPLOSS",
                    "producttype": "CARRYFORWARD",
                    "duration": "DAY",
                    "price": float(data.get("price", 0)) if order_type in ["LIMIT", "STOPLOSS_LIMIT"] else 0,
                    "triggerprice": float(data.get("triggerprice", 0)) if order_type == "STOPLOSS_LIMIT" else 0
                })

            elif order_type == "LIMIT":
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
                    "quantity": quantity *65,
                    })

            elif order_type == "MARKET":
                payload = json.dumps({
                    "variety":"NORMAL",
                    "tradingsymbol":symbol,
                    "symboltoken":token,
                    "transactiontype":transactiontype,
                    "exchange":"NFO",
                    "ordertype":order_type,
                    "producttype":"CARRYFORWARD",
                    "duration":"DAY",
                    "quantity": quantity *65,
                })
            else:   
                return JsonResponse({"status": "error", "message": "Invalid order type."}, status=400)
            
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


# @csrf_exempt
# @login_required
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

# @csrf_exempt
# @login_required
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


# @csrf_exempt
# @login_required
def get_rms(request):
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
        conn.request("GET", "https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/getRMS", payload, headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        # print('Trade Book :- ' + json_data)
        return JsonResponse(json_data, safe=False)

    except Exception as e:
        return JsonResponse({"status": False, "message": "Error fetching trade book", "error": str(e)})

