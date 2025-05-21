# myapp/middleware/block_bots.py
from django.http import HttpResponseForbidden

BAD_BOTS = [
    "curl", "go-http-client", "mj12bot", "ahrefsbot",
    "baiduspider", "yandexbot", "bytespider",
    "apache-httpclient", "scrapy", "applebot"
]

class BlockBadBotsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        for bot in BAD_BOTS:
            if bot.lower() in user_agent:
                return HttpResponseForbidden("Bot access denied.")
        return self.get_response(request)
