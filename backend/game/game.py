import asyncio
import json
import math
import random
import time
import datetime
from users.models import Match
from asgiref.sync import sync_to_async

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
    USERNAME1 = 'username1'
    USERNAME2 = 'username2'
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
 
class Ball:
    # height = 1.5 * width ()
    reduisWidth = 3 / 2
    reduisHeight = 1.6 * reduisWidth
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
        angle_radians = math.radians( angle_degrees)
        self.xOrt = math.cos(angle_radians)
        self.yOrt = math.sin(angle_radians)

class Paddle:
    width = 2
    height = 20
    halfHieght = height / 2
    halfWidth = width / 2
    def __init__(self, socket, position) -> None:
        self.socket = socket
        self.position = position

    async def init_paddel(self):
        self.socket.paddlePos = 50.
        self.myPos = 97 if self.position == Enum.RIGHT else 1
        sidePos = 1 if self.position == Enum.RIGHT else 97
        data = {
            Enum.TYPE:'init_paddle',
            'my': self.myPos,
            'side': sidePos,
        }
        self.myPos += 1
        await self.socket.send(text_data=json.dumps(data))

    def collision(self, ball):
        dx = abs(ball.x - self.myPos)
        dy = abs(ball.y - self.socket.paddlePos)
        return dx <= ball.reduisWidth + Paddle.halfWidth and dy <= ball.reduisHeight + Paddle.halfHieght


class Game:
    speedBall = 4.
    acceleration = .1
    def __init__(self, socket1, socket2) -> None:
        self.ball = Ball(Enum.RIGHT)
        self.rightpaddle = Paddle(socket1, Enum.RIGHT)
        self.leftPaddle = Paddle(socket2, Enum.LEFT)
        self.leftScore = 0
        self.rightScore = 0
        self.rightPlayer = socket1
        self.leftPlayer = socket2
        self.speed = Game.speedBall
        self.state = Enum.INITIALIZED
        self.id = 0
    
    async def broadcast(self, data):
        await asyncio.gather (
            self.rightPlayer.send(text_data=json.dumps(data)),
            self.leftPlayer.send(text_data=json.dumps(data))
        )

    async def edges_collision(self):
        if self.ball.y <= 0 + Ball.reduisHeight:
            self.ball.yOrt *= -1 if self.ball.yOrt < 0 else 1
        if self.ball.y >= 100 - Ball.reduisHeight:
            self.ball.yOrt *= -1 if self.ball.yOrt > 0 else 1
        # if not 0 + Ball.reduisWidth <= self.ball.x <= 100 - Ball.reduisWidth:
        #         self.ball.xOrt *= -1
        if self.ball.x > 100 - Ball.reduisWidth or self.ball.x < 0 + Ball.reduisWidth:
            if self.ball.x > 50:
                self.leftScore += 1
            else:
                self.rightScore += 1
            self.speed = Game.speedBall
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
        if self.leftPaddle.collision(self.ball):
            self.ball.xOrt *= -1 if self.ball.xOrt < 0 else 1

    async def game(self, goals=10, time_limite=-1):
        await asyncio.gather(
            self.rightpaddle.init_paddel(),
            self.leftPaddle.init_paddel(),
        )
        await self.broadcast({Enum.TYPE: 'score', Enum.RIGHT: 0, Enum.LEFT: 0})
        start_time = time.time()
        previous_time = start_time
        # while True:
        while self.rightScore < goals and self.leftScore < goals:
            current_time = time.time()
            _time = current_time - start_time
            if time_limite != -1 and _time > time_limite:
                break
            await asyncio.sleep(0.029)
            data = {
                Enum.TYPE: 'ball',
                'x': self.ball.x,
                'y': self.ball.y,
                'time': _time
            }
            await self.broadcast(data)
            delta_time = current_time - previous_time
            previous_time = current_time
            self.speed += Game.acceleration        
            self.ball.x += self.ball.xOrt * self.speed * delta_time
            self.ball.y += self.ball.yOrt * self.speed * delta_time
            await self.edges_collision()
            self.paddles_collision()
        self.state = Enum.END

    async def run_game(self, goals, time_limite):
        try:
            self.state = Enum.RUNNING
            await self.game(goals, time_limite)
            await sync_to_async(lambda: self.save_game())()
            if self.rightScore == self.leftScore:
                data = {Enum.TYPE:Enum.END, Enum.STATUS:Enum.EQUAL,Enum.XP: 50}
                await self.broadcast(data)
                return
            status = Enum.WIN if self.rightScore > self.leftScore else Enum.LOSE
            xp = 80 if status == Enum.WIN else 0
            data = {Enum.TYPE:Enum.END, Enum.STATUS:status,Enum.XP: xp}
            await self.rightPlayer.send(text_data=json.dumps(data))
            status = Enum.WIN if self.leftScore > self.rightScore else Enum.LOSE
            xp = 80 if status == Enum.WIN else 0
            data = {Enum.TYPE:Enum.END, Enum.STATUS:status,Enum.XP: xp}
            await self.leftPlayer.send(text_data=json.dumps(data))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f'exeption in run_game: {e}')

    def save_game(self, disconnect=False, user=None):
        if self.rightScore > self.leftScore:
            _winner = self.rightPlayer.user
        elif self.rightScore < self.leftScore:
            _winner = self.leftPlayer.user
        else:
            _winner = None
        _is_draw = self.rightScore == self.leftScore
        if disconnect:
            _is_draw = False
            _winner = self.rightPlayer.user if user == self.leftPlayer.user else self.leftPlayer.user
        Match.objects.create (
            time = 0,
            date = datetime.datetime.now().strftime('%H:%M'),
            winner = _winner,
            is_draw =  _is_draw,
            player1 = self.rightPlayer.user,
            player2 = self.leftPlayer.user,
            player1_goals = self.rightScore,
            player2_goals = self.leftScore,
            match_id = self.rightPlayer.id
        )

    async def run_game_tournament(self, goals):
        try:
            await self.game(goals)
            self.rightPlayer.handshake = False
            self.leftPlayer.handshake = False
            status = Enum.QUALIFIED if self.rightScore > self.leftScore else Enum.ELIMINATED
            self.rightPlayer.state = status
            data = {Enum.TYPE:Enum.END, Enum.STATUS:status, 'debug':'end_game'}
            await self.rightPlayer.send(text_data=json.dumps(data))
            status = Enum.QUALIFIED if self.leftScore > self.rightScore else Enum.ELIMINATED
            self.leftPlayer.state = status
            data = {Enum.TYPE:Enum.END, Enum.STATUS:status, 'debug':'end_game'}
            await self.leftPlayer.send(text_data=json.dumps(data))
            print(f'username {self.rightPlayer.username} {self.rightPlayer.state} username {self.leftPlayer.username} {self.leftPlayer.state}')
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f'exeption in run_game_tournament: {e}')