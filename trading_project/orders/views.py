from django.http import JsonResponse
from orders.ws.order_manager import start_order_update_ws
from django.contrib.auth.decorators import login_required


# @login_required
def start_order_ws(request):
    user_id = request.user.id
    if not user_id:
        return JsonResponse({"status": "error", "message": "Missing user_id"})

    start_order_update_ws(user_id)
    return JsonResponse({"status": "success", "message": f"Started order update WebSocket for user {user_id}"})
