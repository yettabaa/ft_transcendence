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

class RemoteTournament(AsyncWebsocketConsumer):
    games = {} # move it outside classe
    async def connect(self):
        try:
            # self.user =  self.scope['user']
            # self.username = self.user.username
            self.alias = self.scope['url_route']['kwargs']['alias']
            self.playersNum = int(self.scope['url_route']['kwargs']['playersNum'])
            # TODO the user can't participe in same tournament two time
            pending_tournament = self.search_pending_tournament()
            if not pending_tournament:
                self.group_name = 'tournament_' + str(uuid.uuid4())
                self.id = 1
                RemoteTournament.games[self.group_name] = {Enum.COMPETITORS:{self.id:{Enum.SOCKET:self,
                Enum.ALIAS:self.alias, Enum.ROUND:0}}}
                RemoteTournament.games[self.group_name][Enum.GLOBALROUND] = 0
                RemoteTournament.games[self.group_name][Enum.PLAYERSNUM] = self.playersNum
            else:
                competitors = RemoteTournament.games[pending_tournament][Enum.COMPETITORS]
                self.group_name = pending_tournament
                self.id = len(competitors) + 1
                competitors[self.id]= {Enum.SOCKET:self,
                Enum.ALIAS:self.alias, Enum.ROUND:0}
            await self.connect_socket()
            if len(RemoteTournament.games[self.group_name][Enum.COMPETITORS]) == self.playersNum:
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
                    # print(f"round {self.round}    {socket1.username} vs {socket2.username}")
                    socket1.opponent_socket = socket2
                    socket2.opponent_socket = socket1
                    game = Game(socket1, socket2)
                    game.id = i +1
                    socket1.game = socket2.game = game
                    await game.broadcast({Enum.TYPE:Enum.OPPONENTS, 
                    'user1':socket1.alias,'user2':socket2.alias})
        except Exception as e:
            print(f'exeption in connect tournament: {e}')

    async def disconnect(self, code):
        try:
            self.connected = False
            if self.group_name in RemoteTournament.games:
                RemoteTournament.games[self.group_name][Enum.COMPETITORS][self.id][Enum.SOCKET] = None
                await self.broadcast_dashboard()
                if hasattr(self, 'game') and self.game.state != Enum.END:
                    if hasattr(self, 'task'):
                        self.task.cancel()
                    data = {Enum.TYPE:Enum.END, Enum.STATUS:Enum.QUALIFIED, 'debug':'disconnect'}
                    await self.opponent_socket.send(text_data=json.dumps(data))
                # competitors = RemoteTournament.games[self.group_name][COMPETITORS]
                if len(RemoteTournament.games[self.group_name][Enum.COMPETITORS]) == self.playersNum:
                    count = 0
                    for i in range(self.playersNum):
                        if not RemoteTournament.games[self.group_name][Enum.COMPETITORS][i +1][Enum.SOCKET]:
                            count += 1
                    if count == self.playersNum:
                        del RemoteTournament.games[self.group_name]
            # print(RemoteTournament.games)
            await self.close()
            await self.channel_layer.group_discard( # type: ignore
                self.group_name,
                self.channel_name
            )
        except Exception as e:
            print(f'exeption in disconnect tournament: {e}')

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            type = text_data_json[Enum.TYPE]
            if hasattr(self, 'game') and type == 'update': # after opnents
                self.paddlePos = float(text_data_json['y'])
                data = {Enum.TYPE: 'paddle', 'pos': self.paddlePos}
                await self.opponent_socket.send(text_data=json.dumps(data))
            elif hasattr(self, Enum.GAME) and type == 'handshake' and self.game.state == Enum.INITIALIZED:
                self.handshake = True
                if self.opponent_socket.handshake == True:
                    await self.game.broadcast({Enum.TYPE:'ready'})
            elif type == 'start' and hasattr(self, 'game') and self.game.state == Enum.INITIALIZED:
                self.game.state = Enum.RUNNING
                self.task = self.opponent_socket.task = asyncio.create_task(
                        self.game.run_game_tournament(1) )
            elif type == Enum.QUALIFYBOARD:
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
                    qualify_socket.opponent_socket = self
                    self.opponent_socket = qualify_socket
                    game = Game(qualify_socket, self)
                    game.id = math.ceil(self.game.id / 2)
                    self.game = qualify_socket.game = game
                    await game.broadcast({Enum.TYPE:Enum.OPPONENTS, 
                    'user1':qualify_socket.alias,'user2':self.alias})
        except Exception as e:
            print(f'exeption in receive tournament: {e}')

    async def qualify_game(self):
        try:
            if self.state == Enum.WINER:
                return None
            competitors = RemoteTournament.games[self.group_name][Enum.COMPETITORS]
            potential_nubmber = 2 * self.round
            virtual_id = math.ceil(self.id / potential_nubmber)
            start_id = ((virtual_id -1) *2) -1 if virtual_id % 2 == 0 else (virtual_id *potential_nubmber) +1
            count = 0
            #\ print(f'in qualify_game username {self.username} roud {self.round} start {start_id}')
            # print(f"len {len(RemoteTournament.games[self.group_name][COMPETITORS])} potential_nubmber {potential_nubmber}")
            for i in range(potential_nubmber):
                potential_id = start_id + i
                if competitors[potential_id][Enum.SOCKET] == None:
                    count += 1
                if self.round == competitors[potential_id][Enum.ROUND]:
                    if competitors[potential_id][Enum.SOCKET] == None:
                        count = potential_nubmber
                        break
                    else:
                        return competitors[potential_id][Enum.SOCKET]
            print(f'in qualify_game username {self.alias} count {count} start {potential_nubmber}')
            if count == potential_nubmber:
                await self.send(text_data=json.dumps({
                    Enum.TYPE:Enum.END, Enum.STATUS:Enum.QUALIFIED, 'debug':'qualify_game'}))
            return None
        except Exception as e:
            print(f'exeption in qualify_game tournament: {e}')

    async def broadcast_dashboard(self):
        try:
            max = RemoteTournament.games[self.group_name][Enum.GLOBALROUND]
            _value = RemoteTournament.games[self.group_name][Enum.COMPETITORS]
            dashboard = []
            for j in range(max +1):
                # print(f"j {j} max {max +1}")
                dashboard.append ({ 
                    # f"username{i +1}": {key: True if value else False}
                    f"username{key}": value[Enum.ALIAS]
                    for key, value in _value.items() #get by id
                    if value[Enum.ROUND] >= j
                })
            # print(_value)
            # print({TYPE:'dashboard', 'rounds':dashboard})
            await self.send_group({Enum.TYPE:'dashboard', 'rounds':dashboard})
        except Exception as e:
            print(f'exeption in broadcast_dashboard tournament: {e}')

    async def connect_socket(self):
        try:
            self.round = 0
            self.state = Enum.QUALIFIED
            self.handshake = False
            self.connected = True
            await self.channel_layer.group_add( # type: ignore
                self.group_name,
                self.channel_name
            )
            await self.accept()
            await self.broadcast_dashboard()

            # debug
            for key, com in RemoteTournament.games.items():
                l = []
                for id, value in com[Enum.COMPETITORS].items():
                    l.append(value[Enum.ALIAS])
                    # print(value)
                print(f"{key} {l}")
        except Exception as e:
            print(f'exeption in connect_socket tournament: {e}')

    def search_pending_tournament(self):
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
            for key, value in competitors.items():
                if value[Enum.ALIAS] == self.alias:
                    return None
            return waiting_tournament
        except Exception as e:
            print(f'exeption in search_pending_tournament tournament: {e}')

    async def send_group(self, data=None, sender=''):
        try:
            if not data:
                return
            await self.channel_layer.group_send( # type: ignore
                self.group_name,
                {
                    Enum.TYPE: 'send.channel',
                    'data': data,
                    'sender_channel': sender
                }
            )
        except Exception as e:
            print(f'exeption in send_group tournament: {e}')

    async def send_channel(self, event):
        if event['sender_channel'] == self.alias:
            return
        data = event['data']
        await self.send(text_data=json.dumps(data))
