import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .game import Game
import uuid

USERNAME1 = 'username1'
USERNAME2 = 'username2'
GAME = 'game'
TASK = 'task'
RUNNING = 'running'
END = 'end'
LEFT = 'left'
RIGHT = 'right'
WIN = 'win'
LOSE = 'lose'
TYPE = 'type'
STATUS = 'status'
XP = 'xp' 
EQUAL = 'equal'
DISCONNECT = 'disconnect'


class RemoteGame(AsyncWebsocketConsumer):
    games = {}
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        # print(f"room_name {self.game_id}")
        panding_game = self.search_panding_game(self.username)
        if panding_game:
            self.room_name = panding_game
            await self.accept()
            await self.send(text_data=json.dumps({
                TYPE:DISCONNECT, STATUS:LOSE, XP:0
            }))
            del RemoteGame.games[self.room_name]
            return

        if self.game_id == 'random':
            return await self.random_matchmaking()
        await self.invitation()

    async def disconnect(self, close_code):
        # print(f'{self.username} disconnect')
        if RemoteGame.games.get(self.room_name):
            if TASK in RemoteGame.games[self.room_name]:
                RemoteGame.games[self.room_name][TASK].cancel()
                game = RemoteGame.games[self.room_name][GAME] 
                if game.stats == RUNNING:
                    data = {TYPE:DISCONNECT, STATUS:WIN, XP:180}
                    await self.send_update(data, self.username)
                if game.stats == END:
                    del RemoteGame.games[self.room_name]
        await self.channel_layer.group_discard( # type: ignore
            self.room_name,
            self.channel_name
        )
        await self.close()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type = text_data_json[TYPE]
        if RemoteGame.games.get(self.room_name):
            if type == 'start' and TASK not in RemoteGame.games[self.room_name]:
                game = RemoteGame.games[self.room_name][GAME]
                RemoteGame.games[self.room_name][TASK] = asyncio.create_task(game.runMatch())
            elif type == 'update' and GAME in RemoteGame.games[self.room_name]:
                self.paddlePos = float(text_data_json['y'])
                game = RemoteGame.games[self.room_name][GAME]
                game.paddlePos = self.paddlePos
                data = {TYPE: 'paddle', 'pos': self.paddlePos}
                await self.send_update(data, self.username)
            elif type == 'end' and TASK in RemoteGame.games[self.room_name]:
                RemoteGame.games[self.room_name][TASK].cancel()
                del RemoteGame.games[self.room_name][TASK]
                game = RemoteGame.games[self.room_name][GAME]
                game.stats = END
                await game.broadcast_result()

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
                TYPE: 'game.update',
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
                USERNAME1: self.username,
                USERNAME2: self,
            }
            return await self.connect_socket()
        # print(f'user2 {self.username} connect')
        room = RemoteGame.games[list(waiting_room)[0]]
        socket1 = room[USERNAME2]
        self.room_name = socket1.room_name
        game = Game(socket1, self)
        room[USERNAME2] = self.username
        room[GAME] = game
        data={
            TYPE:'opponents',
            'user1':room[USERNAME1],
            'user2':self.username,
        }
        await self.connect_socket()
        await self.send_update(data)
    
    async def invitation(self):
        self.room_name = 'invitation_' + self.game_id
        if self.room_name not in RemoteGame.games:
            # print(f'user1 {self.username} connect')
            RemoteGame.games[self.room_name] = {
                USERNAME1: self.username,
                USERNAME2: self,
            }
            return await self.connect_socket()
        # print(f'user2 {self.username} connect')
        room = RemoteGame.games[self.room_name]
        socket1 = room[USERNAME2]
        game = Game(socket1, self)
        room[USERNAME2] = self.username
        room[GAME] = game
        data={
            TYPE:'opponents',
            'user1':room[USERNAME1],
            'user2':self.username,
        }
        await self.connect_socket()
        await self.send_update(data)

    def search_random_match(self):
        return {
            key for key, value in RemoteGame.games.items() 
            if len(value) == 2 and key[:7] == 'random_'
        }
    
    def search_panding_game(self, username):
        panding = {key:value for key, value in RemoteGame.games.items() 
            if (USERNAME1 in value and value[USERNAME1] == username )
            or (USERNAME2 in value and value[USERNAME2] == username )
        }
        if not panding:
            return {}
        key = list(panding)[0]
        value =  panding[key]
        return key if TASK in value else None


class RemoteTournament(AsyncWebsocketConsumer):
    games = {}
    async def connect(self):
        pass
    
    async def disconnect(self, code):
        pass
    
    async def receive(self, text_data):
        pass