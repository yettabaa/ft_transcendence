from django.urls import path, re_path
from .consumers import RemoteGame

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<username>\w+)/(?P<game_id>\w+)/$', RemoteGame.as_asgi())
]