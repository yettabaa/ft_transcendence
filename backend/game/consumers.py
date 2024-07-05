import json
import asyncio
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from django.core.serializers import serialize
from .game import Game
# Create your views here.

class GameConsumer(AsyncWebsocketConsumer):
    rooms = {}
    async def connect(self):
        self.room_name = f'room_test'
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        await self.accept()

        # print(GameConsumer.rooms)
        if "player1" not in GameConsumer.rooms.get(self.room_name,{}):
            self.player_name = 'player1'
            GameConsumer.rooms[self.room_name] = {"player1" : self}
            print('here')
        else:
            self.player_name = 'player2'
            room = GameConsumer.rooms[self.room_name]
            room["player2"] = self
            game = Game(room["player1"],self)
            room["game"] = game
            self.task = asyncio.create_task(game.runMatch())
        print(f'{self.player_name} is connect')



    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )
        if hasattr(self, 'task'):
            self.task.cancel()
        self.close()
        del GameConsumer.rooms[self.room_name][self.player_name]
        print(f'{self.player_name} is disconnect')

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        self.paddlePos = float(text_data_json)
        # game = GameConsumer.rooms[self.room_name]["game"]
        # game.paddlePos = self.paddlePos
        data = {
            'update': 'paddle',
            'pos': self.paddlePos,
        }
        await self.send_update(data, self.player_name)

    async def send_update(self, data, sender):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'game.update',
                'data': data,
                'sender_channel': sender
            }
        )

    async def game_update(self, event):
        if event['sender_channel'] == self.player_name:
            return
        data = event['data']
        await self.send(text_data=json.dumps(data))