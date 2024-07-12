import json
import asyncio
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from .game import Game
import uuid

class GameConsumer(AsyncWebsocketConsumer):
    games = {}
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.room_name = f"room_{self.scope['url_route']['kwargs']['game_id']}"
        # panding_game
        # waiting_room = self.search()
        # if not waiting_room :
        if self.room_name in GameConsumer.games and 'game' in GameConsumer.games[self.room_name]:
            await self.accept()
            await self.close(4001)
            return

        if self.room_name not in GameConsumer.games:
            # self.room_name = 'room_' + str(uuid.uuid4())
            print(f'user1 {self.username} connect')
            GameConsumer.games[self.room_name] = {
                'username1': self.username,
                'username2': self,
            }
        else:
            print(f'user2 {self.username} connect')
            # room = GameConsumer.games[list(waiting_room)[0]]
            room = GameConsumer.games[self.room_name]
            socket1 = room['username2']
            # self.room_name = socket1.room_name
            game = Game(socket1, self)
            room['username2'] = self.username
            room['game'] = game
            room['task'] = asyncio.create_task(game.runMatch())

        await self.channel_layer.group_add( # type: ignore
            self.room_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        print(f'{self.username} disconnect')
        await self.channel_layer.group_discard( # type: ignore
            self.room_name,
            self.channel_name
        )
        if 'game' in GameConsumer.games[self.room_name].values():
            del GameConsumer.games[self.room_name]['game']
            task = GameConsumer.games[self.room_name]['task']
            task.cancel()
        del GameConsumer.games[self.room_name]
        await self.close()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        self.paddlePos = float(text_data_json)
        if 'game' in GameConsumer.games[self.room_name]:
            game = GameConsumer.games[self.room_name]['game']
            game.paddlePos = self.paddlePos
            data = {
                'update': 'paddle',
                'pos': self.paddlePos,
            }
            await self.send_update(data, self.username)

    async def send_update(self, data, sender):
        await self.channel_layer.group_send( # type: ignore
            self.room_name,
            {
                'type': 'game.update',
                'data': data,
                'sender_channel': sender
            }
        )

    async def game_update(self, event):
        if event['sender_channel'] == self.username:
            return
        data = event['data']
        await self.send(text_data=json.dumps(data))
    
    def search(self):
        return {key: value for key, value in GameConsumer.games.items() if len(value) == 2}