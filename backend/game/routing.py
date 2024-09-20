from django.urls import path, re_path

from .GameWebsocket import  SystemSocket
from .RemoteGame import RemoteGame
from .RemoteTournament import  RemoteTournament

websocket_urlpatterns =[ 
	re_path(r'ws/game/(?P<game_type>\w+)/(?P<username>\w+)', RemoteGame.as_asgi()),
	re_path(r'ws/game_tournament/(?P<playersNum>\w+)/(?P<alias>\w+)', RemoteTournament.as_asgi()),
	path('ws/sys/', SystemSocket.as_asgi())
] 
