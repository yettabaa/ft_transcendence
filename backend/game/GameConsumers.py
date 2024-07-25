import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .game import Game
import uuid

class RemoteGame(AsyncWebsocketConsumer):
    games = {}
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        # print(f"room_name {self.game_id}")
        if self.game_id == 'random':
            return await self.random_matchmaking()
        await self.invitation()

    async def disconnect(self, close_code):
        # print(f'{self.username} disconnect')
        data = {
	        'type':'end',
	        'status':'disconnect',
	        'xp':'.....',
        }
        await self.send_update(data)
        if RemoteGame.games.get(self.room_name):
            if 'task' in RemoteGame.games[self.room_name]:
                task = RemoteGame.games[self.room_name]['task']
                task.cancel()
            del RemoteGame.games[self.room_name]
        await self.channel_layer.group_discard( # type: ignore
            self.room_name,
            self.channel_name
        )
        await self.close()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type = text_data_json['type']
        if type == 'start' :
            if RemoteGame.games.get(self.room_name) and 'task' not in RemoteGame.games[self.room_name]:
                game = RemoteGame.games[self.room_name]['game']
                RemoteGame.games[self.room_name]['task'] = asyncio.create_task(game.runMatch())
        elif type == 'update':
            self.paddlePos = float(text_data_json['y'])
            if RemoteGame.games.get(self.room_name) and 'game' in RemoteGame.games[self.room_name]:
                game = RemoteGame.games[self.room_name]['game']
                game.paddlePos = self.paddlePos
                data = {'type': 'paddle', 'pos': self.paddlePos}
                await self.send_update(data, self.username)

    async def connect_socket(self):
        await self.channel_layer.group_add( # type: ignore
            self.room_name,
            self.channel_name
        )
        await self.accept()

    async def send_update(self, data=None, sender=''):
        if not data:
            return
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
    
    async def random_matchmaking(self):
        waiting_room = self.search_random_match()
        if not waiting_room :
            # print(f'user1 {self.username} connect')
            self.room_name = 'random_' + str(uuid.uuid4())
            RemoteGame.games[self.room_name] = {
                'username1': self.username,
                'username2': self,
            }
            return await self.connect_socket()
        # print(f'user2 {self.username} connect')
        room = RemoteGame.games[list(waiting_room)[0]]
        socket1 = room['username2']
        self.room_name = socket1.room_name
        game = Game(socket1, self)
        room['username2'] = self.username
        room['game'] = game
        data={
            'type':'opponents',
            'user1':room['username1'],
            'user2':self.username,
        }
        await self.connect_socket()
        await self.send_update(data)
    
    async def invitation(self):
        self.room_name = 'invitation_' + self.game_id
        if self.room_name not in RemoteGame.games:
            # print(f'user1 {self.username} connect')
            RemoteGame.games[self.room_name] = {
                'username1': self.username,
                'username2': self,
            }
            return await self.connect_socket()
        # print(f'user2 {self.username} connect')
        room = RemoteGame.games[self.room_name]
        socket1 = room['username2']
        game = Game(socket1, self)
        room['username2'] = self.username
        room['game'] = game
        data={
            'type':'opponents',
            'user1':room['username1'],
            'user2':self.username,
        }
        await self.connect_socket()
        await self.send_update(data)

    def search_random_match(self):
        return {
            key for key, value in RemoteGame.games.items() 
            if len(value) == 2 and key[:7] == 'random_'
        }