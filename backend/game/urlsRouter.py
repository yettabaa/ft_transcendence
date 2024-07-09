from django.urls import path, re_path
from .consumers import GameConsumer

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<uuid>[a-f0-9\-]+)/$', GameConsumer.as_asgi())
]