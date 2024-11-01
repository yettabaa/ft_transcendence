import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .game import Game, Enum
import uuid
import math
from asgiref.sync import sync_to_async
from users.utils import get_relation, UserRelation
# from users.user_actions import getUserData
# from users.models import MatchInvitation
from src.logger import log

class RemoteTournament(AsyncWebsocketConsumer):
    games = {}
    async def connect(self):
        try:
            # self.user =  self.scope['user']
            # self.data = await sync_to_async(lambda: getUserData(self.user,self.user))()
            self.alias = self.scope['url_route']['kwargs'][Enum.ALIAS]
            # self.data[Enum.ALIAS] = self.alias
            self.playersNum = int(self.scope['url_route']['kwargs']['playersNum'])
            # log.info(f'{self.user.username} ({self.alias}) is connect')
            self.data = {'username':self}
            log.info(f'({self.alias}) is connect')
            pending_tournament = await self.search_pending_tournament()
            if not pending_tournament:
                self.group_name = 'tournament_' + str(uuid.uuid4())
                self.id = 1
                RemoteTournament.games[self.group_name] = {Enum.COMPETITORS:{self.id:{Enum.SOCKET:self,
                Enum.ALIAS:self.alias, Enum.ROUND:0}}}
                RemoteTournament.games[self.group_name][Enum.PLAYERSNUM] = self.playersNum
            else:
                competitors = RemoteTournament.games[pending_tournament][Enum.COMPETITORS]
                self.group_name = pending_tournament
                self.id = len(competitors) + 1
                competitors[self.id]= {Enum.SOCKET:self,
                Enum.ALIAS:self.alias, Enum.ROUND:0}
            await self.connect_socket()
            if len(RemoteTournament.games[self.group_name][Enum.COMPETITORS]) == self.playersNum:
                RemoteTournament.games[self.group_name][Enum.GLOBALROUND] = 0
                await asyncio.sleep(1)
                for i in range(int(self.playersNum / 2)):
                    socket1 = competitors[1 + i*2][Enum.SOCKET]
                    socket2 = competitors[2 + i*2][Enum.SOCKET]
                    if not socket1 and not socket2:
                        continue
                    if not socket1:
                        data = {Enum.TYPE:Enum.END, Enum.STATUS:Enum.QUALIFIED, 'debug':'start'}
                        await socket2.send(text_data=json.dumps(data))
                        continue
                    if not socket2:
                        data = {Enum.TYPE:Enum.END, Enum.STATUS:Enum.QUALIFIED, 'debug':'start'}
                        await socket1.send(text_data=json.dumps(data))
                        continue
                    socket1.opponent = socket2
                    socket2.opponent = socket1
                    await self.start_game(socket1=socket1, socket2=socket2)
        except Exception as e:
            log.error(f'exeption in connect tournament: {e}')
    
    async def disconnect(self, close_code=1000):
        try:
            if self.group_name in RemoteTournament.games:
                self.isConnect = False
                if self.task and self.game and self.game.state != Enum.END:
                    self.task.cancel()
                    self.task = None
                    self.game.state = Enum.END
                if Enum.GLOBALROUND not in RemoteTournament.games[self.group_name]:# when tournament don't start yet
                    del RemoteTournament.games[self.group_name][Enum.COMPETITORS][self.id]
                    if len(RemoteTournament.games[self.group_name][Enum.COMPETITORS]) == 0:
                        del RemoteTournament.games[self.group_name]
                else: # when all compet disconnect
                    count = 0
                    for i in range(self.playersNum):
                        if not RemoteTournament.games[self.group_name][Enum.COMPETITORS][i +1][Enum.SOCKET].isConnect:
                            count += 1
                    if count == self.playersNum:
                        del RemoteTournament.games[self.group_name]
                await self.broadcast_dashboard()
            await self.close()
            await self.channel_layer.group_discard( # type: ignore
                self.group_name,
                self.channel_name
            )
            log.info(f'({self.alias}) is disconnect')
            self.debug()
        except Exception as e:
            log.error(f'exeption in disconnect tournament: {e}')

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            type = text_data_json[Enum.TYPE]
            if type == 'update' and self.game and self.task:
                await self.game.update_paddle(socket=self, moves=float(text_data_json['y']))
        except Exception as e:
            log.error(f'exeption in receive tournament: {e}')

    async def qualifyboard(self):
        if self.state == Enum.ELIMINATED or self.state == Enum.WINER:
            return await self.broadcast_dashboard()
        competitors = RemoteTournament.games[self.group_name][Enum.COMPETITORS]
        self.round += 1
        if (self.round == 2 and self.playersNum == 4) or (self.round == 3 and self.playersNum == 8):
            self.state = Enum.WINER
            self.round = 2 if self.playersNum == 4 else 3
            await self.send(text_data=json.dumps({
            Enum.TYPE:Enum.END, Enum.STATUS:"im the winer" }))
        competitors[self.id][Enum.ROUND] = self.round
        if self.round >= RemoteTournament.games[self.group_name][Enum.GLOBALROUND]:
            RemoteTournament.games[self.group_name][Enum.GLOBALROUND] = self.round
        await self.broadcast_dashboard()
        qualify_socket = await self.qualify_game()
        if not qualify_socket:
            return
        else:
            qualify_socket.opponent = self
            self.opponent = qualify_socket
            await self.start_game(socket1=qualify_socket, socket2=self)

    async def qualify_game(self):
        try:
            if self.state == Enum.WINER:
                return None
            competitors = RemoteTournament.games[self.group_name][Enum.COMPETITORS]
            possible_games = 2 * self.round
            virtual_id = math.ceil(self.id / possible_games)
            startSearchID = ((virtual_id -1) *2) -1 if virtual_id % 2 == 0 else (virtual_id *possible_games) +1
            for i in range(possible_games):
                j = startSearchID + i
                if self.round == competitors[j][Enum.ROUND]:
                    return competitors[j][Enum.SOCKET]
            return None
        except Exception as e:
            log.error(f'exeption in qualify_game tournament: {e}')

    async def start_game(self, socket1, socket2):
        try:
            game = socket1.game = socket2.game = Game(socket1, socket2)
            game.state = Enum.RUNNING
            socket1.task = socket2.task = asyncio.create_task (
                game.run_game_tournament(goals=5)
            )
        except Exception as e:
            log.error(f'exeption start_game tournament: {e}')

    async def broadcast_dashboard(self):
        try:
            if self.group_name in RemoteTournament.games:
                max = 0
                if Enum.GLOBALROUND in RemoteTournament.games[self.group_name]:
                    max = RemoteTournament.games[self.group_name][Enum.GLOBALROUND]
                _value = RemoteTournament.games[self.group_name][Enum.COMPETITORS]
                dashboard = []
                for j in range(max +1):
                    dashboard.append ({ 
                        # f"username{i +1}": {key: True if value else False}
                        f"username{key}": value[Enum.ALIAS]
                        for key, value in _value.items() #get by id
                        if value[Enum.ROUND] >= j
                    })
                await self.send_group({Enum.TYPE:'dashboard', 'rounds':dashboard})
        except Exception as e:
            log.error(f'exeption in broadcast_dashboard tournament: {e}')

    async def connect_socket(self):
        try:
            self.round = 0
            # Assigned once; if you're eliminated, you will not be re-qualified.
            self.state = Enum.QUALIFIED 
            self.game = None
            self.task = None
            self.isConnect = True
            await self.channel_layer.group_add( # type: ignore
                self.group_name,
                self.channel_name
            )
            await self.accept()
            await self.broadcast_dashboard()
            self.debug()
        except Exception as e:
            log.error(f'exeption in connect_socket tournament: {e}')

    async def search_pending_tournament(self):
        try:
            pending = {
                key for key, value in RemoteTournament.games.items() 
                if Enum.PLAYERSNUM in value and value[Enum.PLAYERSNUM] == self.playersNum
                and Enum.COMPETITORS in value and len(value[Enum.COMPETITORS]) < self.playersNum
            }
            if not pending:
                return None
            waiting_tournament = list(pending)[0]
            competitors = RemoteTournament.games[waiting_tournament][Enum.COMPETITORS]
            for value in competitors.values():
                if value[Enum.ALIAS] == self.alias:
                    return None
                # user  = value[Enum.SOCKET].user
                # relation = await sync_to_async(lambda: get_relation(user1=self.user, user2=user))()
                # if relation == UserRelation.BLOCKED or relation == UserRelation.BLOCKER:
                #     return None
            return waiting_tournament
        except Exception as e:
            log.error(f'exeption in search_pending_tournament tournament: {e}')
    
    def debug(self):
        try:
            str = '\n'
            for key, com in RemoteTournament.games.items():
                list = []
                for id, value in com[Enum.COMPETITORS].items():
                    list.append(value[Enum.ALIAS])
                str += f'{key}\n{list}\n'
            log.info(str)
        except Exception as e:
            log.error(f'exeption in debug tournament: {e}')


    async def send_group(self, data=None):
        try:
            if not data:
                return
            await self.channel_layer.group_send( # type: ignore
                self.group_name,
                {
                    Enum.TYPE: 'send.channel',
                    'data': data
                }
            )
        except Exception as e:
            log.error(f'exeption in send_group tournament: {e}')

    async def send_channel(self, event):
        data = event['data']
        await self.send(text_data=json.dumps(data))
