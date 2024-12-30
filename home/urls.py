from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name="home"),
    path("monetize/", monetize, name="monetize"),
    path("channel_id/", channel_id, name="channel_id"),
    path("thumb_fetch/", thumb_fetch, name="thumb_fetch"),
]