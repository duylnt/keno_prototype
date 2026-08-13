import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import AnalyticsEvent
from .services import track

ALLOWED = {choice[0] for choice in AnalyticsEvent.EVENT_CHOICES}


@csrf_exempt
@require_POST
def collect(request):
    try:
        payload = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        payload = request.POST.dict()
    name = payload.get("event") or payload.get("event_name")
    if name not in ALLOWED:
        return JsonResponse({"ok": False, "error": "unknown_event"}, status=400)
    track(request, name, path=payload.get("path", request.path), metadata=payload.get("meta") or {})
    return JsonResponse({"ok": True})
