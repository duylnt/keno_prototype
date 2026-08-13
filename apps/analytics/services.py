from .models import AnalyticsEvent


def track(request, event_name: str, path: str = "", metadata: dict | None = None):
    session_key = ""
    if hasattr(request, "session"):
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key or ""
    AnalyticsEvent.objects.create(
        event_name=event_name,
        session_key=session_key,
        path=path or getattr(request, "path", ""),
        metadata=metadata or {},
    )
