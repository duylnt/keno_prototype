class SessionTrackingMiddleware:
    """Ensure every visitor has a session key for funnel analytics."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, "session") and not request.session.session_key:
            request.session.save()
        return self.get_response(request)
