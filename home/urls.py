from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name="home"),
    path("monetize/", monetize, name="monetize"),
    path("channel_id/", channel_id, name="channel_id"),
    path("thumb_fetch/", thumb_fetch, name="thumb_fetch"),
    path("tag_extractor/", tag_extractor, name="tag_extractor"),
    path("transcript/", transcript, name="transcript"),
    path("aboutus/", aboutus, name="aboutus"),
    path("contact_us/", contact_us, name="contact_us"),

    path("disclaimer/", disclaimer, name="disclaimer"),
    path("privacy/", privacy, name="privacy"),
    path("tnc/", tnc, name="tnc"),

    path('test-404/', test_404),
    path("test-500/", test_500),

]