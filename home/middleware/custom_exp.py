from django.shortcuts import render
from django.conf import settings

class CustomExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            if response.status_code == 404:
                return render(request, '404.html', status=404)
            return response
        except Exception:
            if settings.DEBUG:
                return render(request, '500.html', status=500)
            raise  # Let Django handle it if not debug