import json
import asyncio
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from .game import Game
import uuid

class RemoteGame(AsyncWebsocketConsumer):
    games = {}
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.room_name = f"room_{self.scope['url_route']['kwargs']['game_id']}"
        # panding_game
        waiting_room = self.search()
        if not waiting_room :
            print(f'user1 {self.username} connect')
            self.room_name = 'room_' + str(uuid.uuid4())
            self.userId = 'username1'
            RemoteGame.games[self.room_name] = {
                'username1': self.username,
                'username2': self,
            }
            await self.channel_layer.group_add( # type: ignore
                self.room_name,
                self.channel_name
            )
            await self.accept()
        else:
            print(f'user2 {self.username} connect')

            room = RemoteGame.games[list(waiting_room)[0]]
            self.userId = 'username2'
            socket1 = room['username2']
            self.room_name = socket1.room_name
            await self.channel_layer.group_add( # type: ignore
                self.room_name,
                self.channel_name
            )
            await self.accept()
            game = Game(socket1, self)
            room['username2'] = self.username
            room['game'] = game
            data={
                'type':'opponents',
                'user1':room['username1'],
                'user2':self.username,
            }
            await self.send_update(data)
            #there is a match then creat task when front need
            # room['task'] = asyncio.create_task(game.runMatch())

        # if self.room_name in GameConsumer.games and 'game' in GameConsumer.games[self.room_name]:
        #     await self.accept()
        #     await self.channel_layer.group_add( # type: ignore
        #     self.room_name,
        #     self.channel_name
        #     )
        #     game = GameConsumer.games[self.room_name]['game']
        #     game.lef
        #     # await self.close(4001)
        #     return

        # if self.room_name not in GameConsumer.games:
        #     # self.room_name = 'room_' + str(uuid.uuid4())
        #     print(f'user1 {self.username} connect')
        #     GameConsumer.games[self.room_name] = {
        #         'username1': self.username,
        #         'username2': self,
        #     }
        # else:
        #     print(f'user2 {self.username} connect')
        #     # room = GameConsumer.games[list(waiting_room)[0]]
        #     room = GameConsumer.games[self.room_name]
        #     socket1 = room['username2']
        #     # self.room_name = socket1.room_name
        #     game = Game(socket1, self)
        #     room['username2'] = self.username
        #     room['game'] = game
        #     room['task'] = asyncio.create_task(game.runMatch())


    async def disconnect(self, close_code):
        print(f'{self.username} disconnect')
        await self.channel_layer.group_discard( # type: ignore
            self.room_name,
            self.channel_name
        )
        await self.close()
        # TODO - NOTIFIY PLAYERS THAT CONNECTION HAS BEEN CLOSED !!!
        if RemoteGame.games.get(self.room_name):
            if 'game' in RemoteGame.games[self.room_name].values():
                task = RemoteGame.games[self.room_name]['task']
                task.cancel()
            del RemoteGame.games[self.room_name]

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type = text_data_json['type']
        if type == 'start':
            asyncio.create_task(RemoteGame.games[self.room_name]['game'].runMatch())
        if type == 'update':
            self.paddlePos = float(text_data_json['y'])
            if 'game' in RemoteGame.games[self.room_name]:
                game = RemoteGame.games[self.room_name]['game']
                game.paddlePos = self.paddlePos
                data = {
                    'type': 'paddle',
                    'pos': self.paddlePos,
                }
                await self.send_update(data, self.username)

    async def send_update(self, data, sender=''):
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
        return {key for key, value in RemoteGame.games.items() if len(value) == 2}