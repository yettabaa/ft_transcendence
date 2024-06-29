import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import ReadyToPlay
from django.core.serializers import serialize
# Create your views here.

class GameConsumer(WebsocketConsumer):
    players = {}
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.username = self.scope['user'].username
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        if self.username not in GameConsumer.players:
            GameConsumer.players[self.username] = 'client'
            ReadyToPlay(username=self.username).save()
            self.send_players_list()
        # print(f"players {GameConsumer.players}" ) 
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        if self.username in GameConsumer.players:
            del GameConsumer.players[self.username]
            ReadyToPlay.objects.get(username=self.username).delete()
            self.send_players_list()

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        pass


    def send_players_list(self):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'update_players_list',
                'players': ReadyToPlay.objects.all()
            }
        )

    def update_players_list(self, event):
        data = serialize('json',event['players'])
        self.send(data)