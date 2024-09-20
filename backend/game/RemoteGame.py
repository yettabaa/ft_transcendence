import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .game import Game, Enum
import uuid
from asgiref.sync import sync_to_async
from users.utils import get_relation, UserRelation
# from users.user_actions import getUserData
# from users.models import MatchInvitation
from src.logger import log

class RemoteGame(AsyncWebsocketConsumer):
    games = {}
    async def connect(self):
        try:
            # self.user =  self.scope['user']
            self.game_type = self.scope['url_route']['kwargs']['game_type']
            # self.username = self.user.username
            # ERROR: in get_level
            # self.data = await sync_to_async(lambda: getUserData(self.user,self.user))()
            # log.info(' is connect')
            self.username = self.scope['url_route']['kwargs']['username']
            panding_game = self.search_panding_game(self.username)
            print(f'username {self.username} pand {panding_game}')
            if panding_game:
                self.group_name = panding_game
                await self.accept()
                data = {Enum.TYPE:Enum.DISCONNECT, Enum.STATUS:Enum.LOSE, Enum.XP:0}
                await self.send(text_data=json.dumps(data))
                del RemoteGame.games[self.group_name]
                return 
            print(RemoteGame.games)
            if self.game_type == 'random':
                return await self.random_matchmaking()
            await self.invitation()
        except Exception as e:
            print(f'exeption in connect: {e}')


    async def disconnect(self, close_code):
        # print(f'{self.username} disconnect')
        try:
            if self.group_name in RemoteGame.games:
                group = RemoteGame.games[self.group_name]
                if Enum.TASK in group:
                    group[Enum.TASK].cancel()
                if Enum.GAME in group and group[Enum.GAME].state == Enum.RUNNING:
                    data = {Enum.TYPE:Enum.DISCONNECT, Enum.STATUS:Enum.WIN, Enum.XP:80}
                    await self.send_update(data, self.username)
                    # await sync_to_async(lambda: group[Enum.GAME].save_game(disconnect=True, user=self.user))()
                    print('running')
                    del RemoteGame.games[self.group_name][Enum.GAME]
                    # print(RemoteGame.games)
                elif Enum.GAME not in group or (Enum.GAME in group and group[Enum.GAME].state == Enum.END):
                    print('end')
                    del RemoteGame.games[self.group_name]
            await self.channel_layer.group_discard( # type: ignore
                self.group_name,
                self.channel_name
            )
            await self.close()
        except Exception as e:
            print(f'exeption in disconnect: {e}')

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            type = text_data_json[Enum.TYPE]
            if self.group_name in RemoteGame.games:
                group = RemoteGame.games[self.group_name]
                if type == 'start' and Enum.TASK not in group:
                    game = group[Enum.GAME]
                    group[Enum.TASK] = asyncio.create_task (
                        game.run_game(goals=10, time_limite=300)
                    )
                elif type == 'update' and Enum.GAME in group:
                    self.paddlePos = float(text_data_json['y'])
                    data = {Enum.TYPE: 'paddle', 'pos': self.paddlePos}
                    await self.send_update(data, self.username)
                elif type == 'end' and Enum.TASK in group: # after start
                    group[Enum.TASK].cancel()
                    del group[Enum.TASK]
                    game = group[Enum.GAME]
                    game.state = Enum.END
                    await game.broadcast_result()
        except Exception as e:
            print(f'exeption in receive: {e}')

    async def random_matchmaking(self):
        try:
            waiting_game = await self.search_random_match()
            if not waiting_game:
                self.id = uuid.uuid4()
                # print(f'user1 {self.username} id {self.id} user {self.user} ')
                self.group_name = 'random_' + str(self.id)
                RemoteGame.games[self.group_name] = {
                    Enum.USERNAME1: self.username,
                    Enum.USERNAME2: self,
                }
                return await self.connect_socket()
            room = RemoteGame.games[waiting_game]
            socket1 = room[Enum.USERNAME2]
            self.group_name = socket1.group_name
            self.id = socket1.id
            # print(f'user2 {self.username} id {self.id} user {self.user}')
            game = Game(socket1, self)
            room[Enum.USERNAME2] = self.username
            room[Enum.GAME] = game
            data={
                Enum.TYPE:Enum.OPPONENTS,
                'user1':socket1.username,
                'user2':self.username,
            }
            # data={
            #     Enum.TYPE:Enum.OPPONENTS,
            #     'user1':socket1.data,
            #     'user2':self.data,
            # }
            await self.connect_socket()
            await self.send_update(data)
        except Exception as e:
            print(f'exeption in random matchmaking: {e}')
    
    async def invitation(self):
        try:
            # from users.notification import NotificationManager
            # self.group_name = 'invitation_' + self.game_type
            # self.id = uuid.UUID(self.game_type)
            # match = await sync_to_async(lambda: MatchInvitation.objects.get(match_id=self.id))()
            # relation = await sync_to_async(lambda: get_relation(user1=match.receiver, user2=match.sender))()
            # if self.user != match.receiver or relation == UserRelation.BLOCKED or relation == UserRelation.BLOCKER:
            #     pass
            # username oppenent
            if self.group_name not in RemoteGame.games:
                print(f'user1 {self.user} id {self.id} user ')
                RemoteGame.games[self.group_name] = {
                    Enum.USERNAME1: self.username,
                    Enum.USERNAME2: self,
                }
                # await sync_to_async(lambda:
                #     NotificationManager.wait_to_play(sender=match.receiver, receiver=match.sender,game_id=str(self.id))
                # )()
                return await self.connect_socket()

            # print(f'user2 {self.username} connect')
            # match.delete()
            room = RemoteGame.games[self.group_name]
            socket1 = room[Enum.USERNAME2]
            game = Game(socket1, self)
            room[Enum.USERNAME2] = self.username
            room[Enum.GAME] = game
            data={
                Enum.TYPE:Enum.OPPONENTS,
                'user1':socket1.username,
                'user2':self.username,
            }
            # data = {
            #     Enum.TYPE:'opponents',
            #     'user1':socket1.data,
            #     'user2':self.data,
            # }
            await self.connect_socket()
            await self.send_update(data)
        except Exception as e:
            print(f'exeption invitation: {e}')

    async def search_random_match(self):
        try:
            search= {
                key for key, value in RemoteGame.games.items() 
                if len(value) == 2 and key[:7] == 'random_'
            }
            if not search:
                return None
            waiting_game = list(search)[0]
            # socket1 = RemoteGame.games[waiting_game][Enum.USERNAME2]
            # relation = await sync_to_async(lambda: get_relation(user1=socket1.user, user2=self.user))()
            # if relation == UserRelation.BLOCKED or relation == UserRelation.BLOCKER:
            #     return None
            return waiting_game
        except Exception as e:
            print(f'exeption search_random_match: {e}')
    
    def search_panding_game(self, username):
        try:
            search = {key:value for key, value in RemoteGame.games.items() 
                if (Enum.USERNAME1 in value and value[Enum.USERNAME1] == username )
                or (Enum.USERNAME2 in value and value[Enum.USERNAME2] == username )
            }
            if not search:
                return None
            key = list(search)[0]
            return key
        except Exception as e:
            print(f'exeption search_panding_game: {e}')

    async def connect_socket(self):
        try:
            await self.channel_layer.group_add( # type: ignore
                self.group_name,
                self.channel_name
            )
            await self.accept()
        except Exception as e:
            print(f'exeption in connect_socket: {e}')

    async def send_update(self, data=None, sender=''):
        try:
            if not data:
                return
            await self.channel_layer.group_send( # type: ignore
                self.group_name,
                {
                    Enum.TYPE: 'game.update',
                    'data': data,
                    'sender_channel': sender
                }
            )
        except Exception as e:
            print(f'exeption in send_update: {e}')

    async def game_update(self, event):
        if event['sender_channel'] == self.username:
            return
        data = event['data']
        await self.send(text_data=json.dumps(data))
