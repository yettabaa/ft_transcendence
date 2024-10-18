import asyncio
import json
import math
import random
import time
import datetime
from users.models import Match
from asgiref.sync import sync_to_async
from src.logger import log

class Enum:
    LEFT = 'left'
    RIGHT = 'right'
    WIN = 'win'
    LOSE = 'lose'
    INITIALIZED = 'initialized'
    RUNNING = 'running'
    END = 'end'
    TYPE = 'type'
    STATUS = 'status'
    XP = 'xp' 
    EQUAL = 'equal'
    QUALIFIED = 'qualified'
    ELIMINATED = 'eliminated'
    GAME = 'game'
    TASK = 'task'
    INITIALIZED = 'initialized'
    OPPONENTS = 'opponents'
    DISCONNECT = 'disconnect'
    COMPETITORS = 'competitors'
    QUALIFYBOARD ='qualifyboard'
    SOCKET = 'socket'
    ALIAS = 'alias'
    GLOBALROUND = 'globalround'
    ROUND = 'round'
    WINER = 'winer'
    PLAYERSNUM = 'playersNum'
    INGAME = 'ingame'
    TIMING1 = 'timing1'
    TIMING2 = 'timing2'
    TIME = 'time'
 
class Ball:
    # height = 1.5 * width ()
    RADUISTOWIDTH = 3 / 2
    RADUISTOHEIGHT = 1.6 * RADUISTOWIDTH
    def __init__(self, firstDir) -> None:
        self.reset(firstDir)

    def reset(self, dir):
        self.x = 50.
        self.y = 50.
        choice = random.randint(0, 1)
        if dir == Enum.LEFT:
            angle_degrees = random.randint(100, 170) if choice else random.randint(190, 260)
        else:
            angle_degrees = random.randint(10, 80) if choice else random.randint(280, 350)
        # angle_degrees = 305
        angle_radians = math.radians( angle_degrees)
        self.xOrt = math.cos(angle_radians)
        self.yOrt = math.sin(angle_radians)
        self.xDelta = self.xOrt
        self.yDelta = self.yOrt

class Paddle:
    WIDTH = 2
    HEIGHT = 20
    HALFHIEGHT = HEIGHT / 2
    HALFWIDTH = WIDTH / 2
    MIN_TIME = 0.02
    MOVE_STEP = 5
    def __init__(self, socket, position) -> None:
        self.socket = socket
        self.position = position
        self.dx = 0.
        self.dy = 0.
        self.y = 50.
        self.x = 97 if position == Enum.RIGHT else 1
        self.last_update_time = time.time()

    async def init_paddel(self):
        opponent_x = 1 if self.position == Enum.RIGHT else 97
        data = {
            Enum.TYPE:'init_paddle',
            'my': self.x,
            'side': opponent_x,
        }
        self.x += 1
        await self.socket.send(text_data=json.dumps(data))
    
    async def update(self, moves):
        current_time = time.time()
        delta = current_time - self.last_update_time
        if delta < Paddle.MIN_TIME or abs(moves) != 1 :  # Protect against spam
            return
        new_y = self.y + moves * Paddle.MOVE_STEP
        new_y = max(10, min(new_y, 90))
        data1 = {Enum.TYPE: 'myPaddle', 'pos': new_y}
        data2 = {Enum.TYPE: 'sidePaddle', 'pos': new_y}
        await asyncio.gather(   
            self.socket.send(text_data=json.dumps(data1)),
            self.socket.opponent.send(text_data=json.dumps(data2))
        )
        self.y = new_y
        self.last_update_time = current_time

    def collision(self, ball):
        self.dx = abs(ball.x - self.x)
        self.dy = abs(ball.y - self.y)
        return self.dx <= Ball.RADUISTOWIDTH + Paddle.HALFWIDTH and self.dy <= Ball.RADUISTOWIDTH + Paddle.HALFHIEGHT

class Game:
    initial_speed = 12.
    acceleration = .1
    def __init__(self, socket1, socket2=False) -> None:
        self.ball = Ball(Enum.RIGHT)
        self.rightpaddle = Paddle(socket1, Enum.RIGHT)
        self.leftPaddle = Paddle(socket2, Enum.LEFT)
        self.leftScore = 0
        self.rightScore = 0
        self.rightPlayer = socket1
        self.leftPlayer = socket2
        self.speed = Game.initial_speed
        self.state = Enum.INITIALIZED
        self.id = 0
        self.time = 0

    async def edges_collision(self):
        if self.ball.y <= Ball.RADUISTOHEIGHT:
            self.ball.yOrt *= -1 if self.ball.yOrt < 0 else 1
            self.ball.x -= self.ball.xDelta
            self.ball.y = Ball.RADUISTOHEIGHT
        if self.ball.y >= 100 - Ball.RADUISTOHEIGHT:
            self.ball.yOrt *= -1 if self.ball.yOrt > 0 else 1
            self.ball.x -= self.ball.xDelta
            self.ball.y = 100 - Ball.RADUISTOHEIGHT
        # if (self.ball.xOrt < 0 and self.ball.x < 80) or self.ball.x > 100 - 2:
        # if (self.ball.xOrt > 0 and self.ball.x > 30) or self.ball.x < 2:
        if self.ball.x >= 100 - (Paddle.WIDTH + Ball.RADUISTOWIDTH) or self.ball.x <= Paddle.WIDTH + Ball.RADUISTOWIDTH:
            # print(f'right {self.rightpaddle.y} left {self.leftPaddle.y}')
            if self.ball.x > 50:
                self.leftScore += 1
            else:
                self.rightScore += 1
            self.speed = Game.initial_speed
            self.ball.reset(Enum.RIGHT if self.ball.x > 50 else Enum.LEFT)
            data = {
                Enum.TYPE: 'score',
                Enum.RIGHT: self.rightScore,
                Enum.LEFT: self.leftScore,
            }
            await self.broadcast(data)

    def paddles_collision(self):
        if self.rightpaddle.collision(self.ball):
            self.ball.xOrt *= -1 if self.ball.xOrt > 0 else 1
            if self.ball.x > 97 - Ball.RADUISTOWIDTH:
                self.ball.x = 97 - Ball.RADUISTOWIDTH
                self.ball.y -= self.ball.yDelta
        if self.leftPaddle.collision(self.ball):
            self.ball.xOrt *= -1 if self.ball.xOrt < 0 else 1
            if self.ball.x < 3 + Ball.RADUISTOWIDTH:
                self.ball.x = 3 + Ball.RADUISTOWIDTH
                self.ball.y -= self.ball.yDelta

    async def game(self, goals=10, time_limite=-1):
        await self.game_init()
        start_time = time.time()
        previous_time = start_time
        while self.rightScore < goals and self.leftScore < goals:
            current_time = time.time()
            self.time = current_time - start_time
            if time_limite != -1 and self.time > time_limite:
                break
            data = {
                Enum.TYPE: 'ball',
                'x': round(self.ball.x, 2),
                'y': round(self.ball.y, 2),
                Enum.TIME: round(self.time)
            }
            await self.broadcast(data)
            delta_time = current_time - previous_time
            previous_time = current_time
            self.speed += Game.acceleration
            self.ball.xDelta = self.ball.xOrt * self.speed * delta_time
            self.ball.yDelta = self.ball.yOrt * self.speed * delta_time
            self.ball.x += self.ball.xDelta
            self.ball.y += self.ball.yDelta
            self.paddles_collision()
            await self.edges_collision()
            await asyncio.sleep(0.025) # Prevent the loop from running too fast and hang
        self.state = Enum.END

    async def run_game(self, goals, time_limite):
        try:
            await self.game(goals, time_limite)
            self.rightPlayer.game = self.rightPlayer.task = None
            self.leftPlayer.game = self.leftPlayer.task = None
            await sync_to_async(lambda: self.save_game())()
            if self.rightScore == self.leftScore:
                await self.broadcast({Enum.TYPE:Enum.END, Enum.STATUS:Enum.EQUAL,Enum.XP: 50})
                return
            status = Enum.WIN if self.rightScore > self.leftScore else Enum.LOSE
            xp = 80 if status == Enum.WIN else 0
            data1 = {Enum.TYPE:Enum.END, Enum.STATUS:status,Enum.XP: xp}
            status = Enum.WIN if self.leftScore > self.rightScore else Enum.LOSE
            xp = 80 if status == Enum.WIN else 0
            data2 = {Enum.TYPE:Enum.END, Enum.STATUS:status,Enum.XP: xp}
            await asyncio.gather(   
                self.rightPlayer.send(text_data=json.dumps(data1)),
                self.leftPlayer.send(text_data=json.dumps(data2))
            )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error(f'exeption in run_game: {e}')

    async def run_game_tournament(self, goals):
        try:
            await self.countdown(0, Enum.TIMING1)
            await self.game(goals)
            self.rightPlayer.handshake = False
            self.leftPlayer.handshake = False
            self.rightPlayer.game = self.rightPlayer.task = None
            self.leftPlayer.game = self.leftPlayer.task = None
            status = Enum.QUALIFIED if self.rightScore > self.leftScore else Enum.ELIMINATED
            self.rightPlayer.state = status
            data1 = {Enum.TYPE:Enum.END, Enum.STATUS:status, 'debug':'end_game'}
            status = Enum.QUALIFIED if self.leftScore > self.rightScore else Enum.ELIMINATED
            self.leftPlayer.state = status
            data2 = {Enum.TYPE:Enum.END, Enum.STATUS:status, 'debug':'end_game'}
            await asyncio.gather(   
                self.rightPlayer.send(text_data=json.dumps(data1)),
                self.leftPlayer.send(text_data=json.dumps(data2))
            )
            await asyncio.gather(   
                self.rightPlayer.qualifyboard(),
                self.leftPlayer.qualifyboard()
            )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error(f'exeption in run_game_tournament: {e}')

    def save_game(self, disconnect=False, user=None):
        self.rightPlayer.user.total_matches += 1
        self.leftPlayer.user.total_matches += 1
        if self.rightScore > self.leftScore:
            _winner = self.rightPlayer.user
            self.rightPlayer.user.wins += 1
            self.leftPlayer.user.losses += 1
        elif self.rightScore < self.leftScore:
            _winner = self.leftPlayer.user
            self.leftPlayer.user.wins += 1
            self.rightPlayer.user.losses += 1
        else:
            _winner = None
        _is_draw = self.rightScore == self.leftScore
        if disconnect:
            _is_draw = False
            _winner = self.rightPlayer.user if user == self.leftPlayer.user else self.leftPlayer.user
            if user == self.rightPlayer.user:
                self.rightPlayer.user.losses += 1
                self.leftPlayer.user.wins += 1
            else:
                self.rightPlayer.user.wins += 1
                self.leftPlayer.user.losses += 1
        self.rightPlayer.user.save()
        self.leftPlayer.user.save()
        Match.objects.create (
            time = self.time,
            date = datetime.datetime.now().strftime('%H:%M'),
            winner = _winner,
            is_draw =  _is_draw,
            player1 = self.rightPlayer.user,
            player2 = self.leftPlayer.user,
            player1_goals = self.rightScore,
            player2_goals = self.leftScore,
            match_id = self.rightPlayer.uuid
        )

    async def game_init(self):
        await self.broadcast({Enum.TYPE:Enum.OPPONENTS, 
        'user1':self.leftPlayer.alias,'user2':self.rightPlayer.alias})
        await asyncio.sleep(0.5)
        await self.countdown(1, Enum.TIMING2)
        await asyncio.gather( self.rightpaddle.init_paddel(),
        self.leftPaddle.init_paddel(),)
        await asyncio.sleep(0.2)
        await self.broadcast({Enum.TYPE: 'score', Enum.RIGHT: 0, Enum.LEFT: 0})

    async def countdown(self, time, tag):
        for i in range(time, -1, -1):
            await self.broadcast({Enum.TYPE:tag, Enum.TIME: i})
            await asyncio.sleep(1)

    async def update_paddle(self, socket, moves):
        if socket == self.rightPlayer:
            await self.rightpaddle.update(moves=moves)
        else:
            await self.leftPaddle.update(moves=moves)

    async def broadcast(self, data):
        await asyncio.gather(
            self.rightPlayer.send(text_data=json.dumps(data)),
            self.leftPlayer.send(text_data=json.dumps(data))
        )
