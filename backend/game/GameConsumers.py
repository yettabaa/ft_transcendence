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
                if game.stats == RUNNING:
                    data = {TYPE:DISCONNECT, STATUS:WIN, XP:180}
                    await self.send_update(data, self.username)
                if game.stats == END:
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
                game.stats = END
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

NBPLAYER = 4
TOURNAMENT = 'tournament'
FIRSTROUND = 'firstround'
COMPETITORS = 'competitors'
QUALIFYBOARD ='qualifyboard'
QUALIFIED = 'qualified'
ELIMINATED = 'eliminated'

class RemoteTournament(AsyncWebsocketConsumer):
    games = {}
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        pending_tournament = self.search_pending_tournament()
        if not pending_tournament:
            self.group_name = 'tournament_' + str(uuid.uuid4())
            self.id = 1
            RemoteTournament.games[self.group_name] = {COMPETITORS:{'user1':self}}
            return await self.connect_socket()
        competitors = RemoteTournament.games[pending_tournament][COMPETITORS]
        qualifyboard = RemoteTournament.games[pending_tournament][QUALIFYBOARD]
        if self.username in qualifyboard.values(): # there is mistake here
            self.group_name = pending_tournament
            await self.accept()
            return await self.send(text_data=json.dumps({
                TYPE:DISCONNECT, STATUS:ELIMINATED}))
        elif len(competitors) < NBPLAYER -1:
            self.group_name = pending_tournament
            self.id = len(competitors) + 1
            competitors['user' + str(self.id)] = self
        else:
            self.group_name = pending_tournament
            self.id = len(competitors) + 1
            competitors['user' + str(self.id)] = self
            RemoteTournament.games[self.group_name][TOURNAMENT] = False
            await self.connect_socket()
            for i in range(int(NBPLAYER / 2)):
                key1 = 'user' + str(1 + i*2)
                key2 = 'user' + str(2 + i*2)
                if  key1 not in competitors and key2 not in competitors:
                    continue
                if key1 not in competitors:
                    data = {TYPE:DISCONNECT, STATUS:QUALIFIED}
                    await socket2.send(text_data=json.dumps(data))
                    continue
                if key2 not in competitors:
                    data = {TYPE:DISCONNECT, STATUS:QUALIFIED}
                    await socket1.send(text_data=json.dumps(data))
                    continue
                socket1 = competitors[key1]
                socket2 = competitors[key2]
                socket1.opponent_socket = socket2
                socket2.opponent_socket = socket1
                game = Game(socket1, socket2)
                game.id = i +1
                socket1.game = socket2.game = game
                await game.broadcast({TYPE:OPPONENTS, 
                'user1':socket1.username,'user2':socket2.username})
            return 
        await self.connect_socket()

    async def disconnect(self, code):
        # if self.group_name in RemoteTournament.games:
        #     group = RemoteTournament.games[self.group_name]
        # delete player from games with id
        if self.group_name in RemoteTournament.games:
            if hasattr(RemoteTournament, 'game') and self.game.stats != END:
                data = {TYPE:DISCONNECT, STATUS:QUALIFIED}
                await self.opponent_socket.send(text_data=json.dumps(data))
            del RemoteTournament.games[self.group_name][COMPETITORS]['user' + str(self.id)]
            RemoteTournament.games[self.group_name][QUALIFYBOARD][self.round]['username' + str(self.id)] = False

        await self.close()
        await self.channel_layer.group_discard( # type: ignore
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type = text_data_json[TYPE]
        if self.group_name in RemoteTournament.games:
            group = RemoteTournament.games[self.group_name]
            if type == 'update': # after opnents
                self.paddlePos = float(text_data_json['y'])
                data = {TYPE: 'paddle', 'pos': self.paddlePos}
                await self.opponent_socket.send(text_data=json.dumps(data))
            elif type == 'start' and self.game.stats == INITIALIZED:
                self.task = self.opponent_socket.task = asyncio.create_task(
                    self.game.run_game_tournament(2)
                )
                # for i in range(int(NBPLAYER / 2)):
                #     key1 = 'user' + str(1 + i*2)
                #     key2 = 'user' + str(2 + i*2)
                #     if  key1 not in group[COMPETITORS] and key2 not in group[COMPETITORS]:
                #         continue
                #     if key1 not in group[COMPETITORS]:
                #         data = {TYPE:DISCONNECT, STATUS:QUALIFIED}
                #         await socket2.send(text_data=json.dumps(data))
                #         continue
                #     if key2 not in group[COMPETITORS]:
                #         data = {TYPE:DISCONNECT, STATUS:QUALIFIED}
                #         await socket1.send(text_data=json.dumps(data))
                #         continue
                #     socket1 = group[COMPETITORS][key1]
                #     socket2 = group[COMPETITORS][key2]
                #     game = Game(socket1, socket2)
                #     socket1.opponent_socket = socket2
                #     socket2.opponent_socket = socket1
                #     game.id = i +1
                #     socket1.game = socket2.game = game
                #     socket1.task = socket2.task = asyncio.create_task(game.run_game_tournament(10))
                # group[TOURNAMENT] = True
            elif type == QUALIFYBOARD:
                self.Eliminations -= 1
                self.round = 'semi_final' if self.Eliminations == 1 else 'final'
                qualify_board = RemoteTournament.games[self.group_name][QUALIFYBOARD]
                # self.id = math.ceil(self.id / 2)
                #bradcats oppnent and delte add ext ....
                if self.round not in qualify_board:
                    qualify_board[self.round] = {'username'+str(self.id):self.username}
                else:
                    qualify_board[self.round]['username'+str(self.id)] = self.username
                await self.broadcast_qualifyboard()
                if self.Eliminations == -1:
                    await self.send(text_data=json.dumps({
                    TYPE:END, STATUS:"im the winer" }))
                    #delete tournament
                    return
                qualify_game = self.qualify_game()
                if not qualify_game:
                    await self.send(text_data=json.dumps({
                    TYPE:END, STATUS:QUALIFIED}))
                elif qualify_game.stats == END:
                    winer_socket = self.get_winer(qualify_game)
                    print(f"user1 {winer_socket.username} user2 {self.username}")
                    winer_socket.opponent_socket = self
                    self.opponent_socket = winer_socket
                    game = Game(winer_socket, self)
                    game.id = math.ceil(self.game.id / 2)
                    self.game = winer_socket.game = game
                    await game.broadcast({TYPE:OPPONENTS, 
                    'user1':winer_socket.username,'user2':self.username})
                # else:
                #     await self.send(text_data=json.dumps({
                #     TYPE:'waiting' }))
            # elif type == 'start_next':

    def qualify_game(self):
        qualifyboard = RemoteTournament.games[self.group_name][QUALIFYBOARD]
        # qualifyboard = RemoteTournament.games[self.group_name][QUALIFYBOARD][self.round]
        id_qualify_user = self.game.id + (-1 if self.game.id % 2 == 0 else 1)
        qualify_user = 'username' + str(id_qualify_user)
        if qualify_user in qualifyboard[self.round]:
            #
            pass
        id_competitor = 2* (self.game.id + (-1 if self.game.id % 2 == 0 else 1))
        competitors = RemoteTournament.games[self.group_name][COMPETITORS]
        print(f"id {self.id} socket1 {'user' + str(id_competitor -1)} socket2 {'user' + str(id_competitor)}")
        user1 = 'username' + str(id_competitor -1)
        user2 = 'username' + str(id_competitor)
        if user1 not in qualify and user2 not in qualify:
            return None
        for value in competitors.values():
            if value.username == user1 or value.username == user2:
                return value.game

    def get_winer(self, game):
        return game.rightPlayer if game.rightScore > game.leftScore else game.leftPlayer

    def in_qualifyboard(self, username):
        qualifyboard = RemoteTournament.games[self.group_name][QUALIFYBOARD]
        for value in qualifyboard.values():
            if (value == username):
                return True
        return False

    def get_socket(self, username):
        competitors = RemoteTournament.games[self.group_name][COMPETITORS]
        for value in competitors.values():
            if (value.username == username):
                return value
        return None

    def make_board(self, type):
        _value = RemoteTournament.games[self.group_name][COMPETITORS]
        opponents = { 
            f"username{i +1}": {value.username: True}
            for i, (key, value) in enumerate(_value.items())
            if key != TOURNAMENT
        }
        return  {type:opponents}

    async def broadcast_qualifyboard(self):
        _value = RemoteTournament.games[self.group_name][QUALIFYBOARD]
        _value[TYPE] = 'dashboard'
        print(_value)
        await self.send_group(data=_value)

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
        if event['sender_channel'] == self.username:
            return
        data = event['data']
        await self.send(text_data=json.dumps(data))

    def search_pending_tournament(self):
        pending = {
            key for key, value in RemoteTournament.games.items() 
            if TOURNAMENT not in value
        }
        return list(pending)[0] if pending else None

    async def connect_socket(self):
        await self.channel_layer.group_add( # type: ignore
            self.group_name,
            self.channel_name
        )
        await self.accept()
        self.Eliminations = 2 if NBPLAYER == 8 else 1
        self.round = FIRSTROUND
        RemoteTournament.games[self.group_name][QUALIFYBOARD] = self.make_board(FIRSTROUND)
        await self.broadcast_qualifyboard()