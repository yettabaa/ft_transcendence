import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .game import Game
import uuid
import math

USERNAME1 = 'username1'
USERNAME2 = 'username2'
GAME = 'game'
TASK = 'task'
INITIALIZED = 'initialized'
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
OPPONENTS = 'opponents'
DISCONNECT = 'disconnect'

class RemoteGame(AsyncWebsocketConsumer):
    games = {}
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        # print(f"room_name {self.game_id}")
        panding_game = self.search_panding_game(self.username)
        if panding_game:
            self.group_name = panding_game
            await self.accept()
            await self.send(text_data=json.dumps({
                TYPE:DISCONNECT, STATUS:LOSE, XP:0
            }))
            del RemoteGame.games[self.group_name]
            return

        if self.game_id == 'random':
            return await self.random_matchmaking()
        await self.invitation()

    async def disconnect(self, close_code):
        # print(f'{self.username} disconnect')
        if self.group_name in RemoteGame.games:
            group = RemoteGame.games[self.group_name]
            if TASK in group:
                group[TASK].cancel()
                game = group[GAME] 
                if game.state == RUNNING:
                    data = {TYPE:DISCONNECT, STATUS:WIN, XP:180}
                    await self.send_update(data, self.username)
                if game.state == END:
                    del RemoteGame.games[self.group_name]
            elif GAME in group:
                data = {TYPE:DISCONNECT, STATUS:WIN, XP:180}
                await self.send_update(data, self.username)
                del RemoteGame.games[self.group_name]
            else:
                del RemoteGame.games[self.group_name]
        await self.channel_layer.group_discard( # type: ignore
            self.group_name,
            self.channel_name
        )
        await self.close()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type = text_data_json[TYPE]
        if self.group_name in RemoteGame.games:
            group = RemoteGame.games[self.group_name]
            if type == 'start' and TASK not in group:
                game = group[GAME]
                group[TASK] = asyncio.create_task(game.run_game(10))
            elif type == 'update' and GAME in group:
                self.paddlePos = float(text_data_json['y'])
                data = {TYPE: 'paddle', 'pos': self.paddlePos}
                await self.send_update(data, self.username)
            elif type == 'end' and TASK in group: # after start
                group[TASK].cancel()
                del group[TASK]
                game = group[GAME]
                game.state = END
                await game.broadcast_result()

    async def connect_socket(self):
        await self.channel_layer.group_add( # type: ignore
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def send_update(self, data=None, sender=''):
        if not data:
            return
        await self.channel_layer.group_send( # type: ignore
            self.group_name,
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
            self.group_name = 'random_' + str(uuid.uuid4())
            RemoteGame.games[self.group_name] = {
                USERNAME1: self.username,
                USERNAME2: self,
            }
            return await self.connect_socket()
        # print(f'user2 {self.username} connect')
        room = RemoteGame.games[list(waiting_room)[0]]
        socket1 = room[USERNAME2]
        self.group_name = socket1.group_name
        game = Game(socket1, self)
        room[USERNAME2] = self.username
        room[GAME] = game
        data={
            TYPE:OPPONENTS,
            'user1':room[USERNAME1],
            'user2':self.username,
        }
        await self.connect_socket()
        await self.send_update(data)
    
    async def invitation(self):
        self.group_name = 'invitation_' + self.game_id
        if self.group_name not in RemoteGame.games:
            # print(f'user1 {self.username} connect')
            RemoteGame.games[self.group_name] = {
                USERNAME1: self.username,
                USERNAME2: self,
            }
            return await self.connect_socket()
        # print(f'user2 {self.username} connect')
        room = RemoteGame.games[self.group_name]
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
        return key if GAME in value else None

NBPLAYER = 8
TOURNAMENT = 'tournament'
FIRSTROUND = 0
SEMIFINAL =  1
FINAL = 2
COMPETITORS = 'competitors'
QUALIFYBOARD ='qualifyboard'
QUALIFIED = 'qualified'
ELIMINATED = 'eliminated'
SOCKET = 'socket'
ALIAS = 'alias'
ROUND = 'round'
TYPE = 'type'
WINER = 'winer'
PLAYERSNUM = 'playersNum'
class RemoteTournament(AsyncWebsocketConsumer):
    games = {} # move it outside classe
    async def connect(self):
        self.alias = self.scope['url_route']['kwargs']['alias']
        self.playersNum = int(self.scope['url_route']['kwargs']['playersNum'])
        # if self.in_tournament():
        #     await self.connect_socket()
        #     return
        # TODO the user can't participe in same tournament two time
        pending_tournament = self.search_pending_tournament()
        if not pending_tournament:
            self.group_name = 'tournament_' + str(uuid.uuid4())
            self.id = 1
            RemoteTournament.games[self.group_name] = {COMPETITORS:{self.id:{SOCKET:self,
            ALIAS:self.alias, ROUND:0}}}
            RemoteTournament.games[self.group_name][TOURNAMENT] = FIRSTROUND
            RemoteTournament.games[self.group_name][PLAYERSNUM] = self.playersNum
        else:
            competitors = RemoteTournament.games[pending_tournament][COMPETITORS]
            self.group_name = pending_tournament
            self.id = len(competitors) + 1
            competitors[self.id]= {SOCKET:self,
            ALIAS:self.alias, ROUND:0}
        await self.connect_socket()
        if len(RemoteTournament.games[self.group_name][COMPETITORS]) == self.playersNum:
            for i in range(int(self.playersNum / 2)):
                socket1 = competitors[1 + i*2][SOCKET]
                socket2 = competitors[2 + i*2][SOCKET]
                if not socket1 and not socket2:
                    continue
                if not socket1:
                    data = {TYPE:END, STATUS:QUALIFIED, 'debug':'start'}
                    await socket2.send(text_data=json.dumps(data))
                    continue
                if not socket2:
                    data = {TYPE:END, STATUS:QUALIFIED, 'debug':'start'}
                    await socket1.send(text_data=json.dumps(data))
                    continue
                # print(f"round {self.round}    {socket1.username} vs {socket2.username}")
                socket1.opponent_socket = socket2
                socket2.opponent_socket = socket1
                game = Game(socket1, socket2)
                game.id = i +1
                socket1.game = socket2.game = game
                await game.broadcast({TYPE:OPPONENTS, 
                'user1':socket1.alias,'user2':socket2.alias})

    async def disconnect(self, code):
        self.connected = False
        if self.group_name in RemoteTournament.games:
            RemoteTournament.games[self.group_name][COMPETITORS][self.id][SOCKET] = None
            await self.broadcast_dashboard()
            if hasattr(self, 'game') and self.game.state != END:
                if hasattr(self, 'task'):
                    self.task.cancel()
                data = {TYPE:END, STATUS:QUALIFIED, 'debug':'disconnect'}
                await self.opponent_socket.send(text_data=json.dumps(data))
            # competitors = RemoteTournament.games[self.group_name][COMPETITORS]
            if len(RemoteTournament.games[self.group_name][COMPETITORS]) == self.playersNum:
                count = 0
                for i in range(self.playersNum):
                    if not RemoteTournament.games[self.group_name][COMPETITORS][i +1][SOCKET]:
                        count += 1
                if count == self.playersNum:
                    del RemoteTournament.games[self.group_name]
        # print(RemoteTournament.games)
        await self.close()
        await self.channel_layer.group_discard( # type: ignore
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type = text_data_json[TYPE]
        if hasattr(self, 'game') and type == 'update': # after opnents
            self.paddlePos = float(text_data_json['y'])
            data = {TYPE: 'paddle', 'pos': self.paddlePos}
            await self.opponent_socket.send(text_data=json.dumps(data))
        elif hasattr(self, GAME) and type == 'handshake' and self.game.state == INITIALIZED:
            self.handshake = True
            if self.opponent_socket.handshake == True:
                await self.game.broadcast({TYPE:'ready'})
        elif type == 'start' and hasattr(self, 'game') and self.game.state == INITIALIZED:
            self.game.state = RUNNING
            self.task = self.opponent_socket.task = asyncio.create_task(
                    self.game.run_game_tournament(1) )
        elif type == QUALIFYBOARD:
            if self.state == ELIMINATED or self.state == WINER:
                return await self.broadcast_dashboard()
            competitors = RemoteTournament.games[self.group_name][COMPETITORS]
            self.round += 1
            if (self.round == 2 and self.playersNum == 4) or (self.round == 3 and self.playersNum == 8):
                self.state = WINER
                self.round = 2 if self.playersNum == 4 else 3
                await self.send(text_data=json.dumps({
                TYPE:END, STATUS:"im the winer" }))
            competitors[self.id][ROUND] = self.round
            RemoteTournament.games[self.group_name][TOURNAMENT] = self.round
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
                await game.broadcast({TYPE:OPPONENTS, 
                'user1':qualify_socket.alias,'user2':self.alias})

    async def qualify_game(self):
        if self.state == WINER:
            return None
        competitors = RemoteTournament.games[self.group_name][COMPETITORS]
        potential_nubmber = 2 * self.round
        virtual_id = math.ceil(self.id / potential_nubmber)
        start_id = ((virtual_id -1) *2) -1 if virtual_id % 2 == 0 else (virtual_id *potential_nubmber) +1
        count = 0
        #\ print(f'in qualify_game username {self.username} roud {self.round} start {start_id}')
        # print(f"len {len(RemoteTournament.games[self.group_name][COMPETITORS])} potential_nubmber {potential_nubmber}")
        for i in range(potential_nubmber):
            potential_id = start_id + i
            if competitors[potential_id][SOCKET] == None:
                count += 1
            if self.round == competitors[potential_id][ROUND]:
                if competitors[potential_id][SOCKET] == None:
                    count = potential_nubmber
                    break
                else:
                    return competitors[potential_id][SOCKET]
        print(f'in qualify_game username {self.alias} count {count} start {potential_nubmber}')
        if count == potential_nubmber:
            await self.send(text_data=json.dumps({
                TYPE:END, STATUS:QUALIFIED, 'debug':'qualify_game'}))
        return None

    def in_tournament(self):
        for key,value in RemoteTournament.games.items():
            competitors = value[COMPETITORS]
            for subkey, subValue in competitors.items():
                if subValue[ALIAS] == self.alias:
                    self.id = subkey
                    self.group_name = key
                    return True
        return False

    async def broadcast_dashboard(self):
        max = RemoteTournament.games[self.group_name][TOURNAMENT]
        _value = RemoteTournament.games[self.group_name][COMPETITORS]
        dashboard = []
        for j in range(max +1):
            # print(f"j {j} max {max +1}")
            dashboard.append ({ 
                # f"username{i +1}": {key: True if value else False}
                f"username{key}": value[ALIAS]
                for key, value in _value.items() #get by id
                if value[ROUND] >= j
            })
        # print(_value)
        # print({TYPE:'dashboard', 'rounds':dashboard})
        await self.send_group({TYPE:'dashboard', 'rounds':dashboard})

    async def connect_socket(self):
        self.round = FIRSTROUND
        self.state = QUALIFIED
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
            for id, value in com[COMPETITORS].items():
                l.append(value[ALIAS])
                # print(value)
            print(f"{key} {l}")

    def search_pending_tournament(self):
        pending = {
            key for key, value in RemoteTournament.games.items() 
            if PLAYERSNUM in value and value[PLAYERSNUM] == self.playersNum
            and COMPETITORS in value and len(value[COMPETITORS]) < self.playersNum
        }
        return list(pending)[0] if pending else None

    async def send_group(self, data=None, sender=''):
        if not data:
            return
        await self.channel_layer.group_send( # type: ignore
            self.group_name,
            {
                TYPE: 'send.channel',
                'data': data,
                'sender_channel': sender
            }
        )

    async def send_channel(self, event):
        if event['sender_channel'] == self.alias:
            return
        data = event['data']
        await self.send(text_data=json.dumps(data))

        