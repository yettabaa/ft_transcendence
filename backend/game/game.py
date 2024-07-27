import asyncio
import json
import math
import random
import time

LEFT = 'left'
RIGHT = 'right'
WIN = 'win'
LOSE = 'lose'
RUNNING = 'running'
END = 'end'
TYPE = 'type'
STATUS = 'status'
XP = 'xp' 
EQUAL = 'equal'
 
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
        if dir == LEFT:
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
        self.myPos = 97 if self.position == RIGHT else 1
        sidePos = 1 if self.position == RIGHT else 97
        data = {
            TYPE:'init_paddle',
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
        self.ball = Ball(RIGHT)
        self.rightpaddle = Paddle(socket1, RIGHT)
        self.leftPaddle = Paddle(socket2, LEFT)
        self.leftScore = 0
        self.rightScore = 0
        self.rightPlayer = socket1
        self.leftPlayer = socket2
        self.speed = Game.speedBall
        self.stats = True
    
    async def broadcast(self, data):
        await self.rightPlayer.send(text_data=json.dumps(data))
        await self.leftPlayer.send(text_data=json.dumps(data))

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
            self.ball.reset(RIGHT if self.ball.x > 50 else LEFT)
            data = {
                TYPE: 'score',
                RIGHT: self.rightScore,
                LEFT: self.leftScore,
            }
            await self.broadcast(data)

    def paddles_collision(self):
        if self.rightpaddle.collision(self.ball):
            self.ball.xOrt *= -1 if self.ball.xOrt > 0 else 1
        if self.leftPaddle.collision(self.ball):
            self.ball.xOrt *= -1 if self.ball.xOrt < 0 else 1

    async def broadcast_result(self):
        if self.rightScore == self.leftScore:
            data = {TYPE:END, STATUS:EQUAL,XP: 90}
            await self.broadcast(data)
            return
        status = WIN if self.rightScore > self.leftScore else LOSE
        xp = 180 if status == WIN else 0
        data = {TYPE:END, STATUS:status,XP: xp}
        await self.rightPlayer.send(text_data=json.dumps(data))
        status = WIN if self.leftScore > self.rightScore else LOSE
        xp = 180 if status == WIN else 0
        data = {TYPE:END, STATUS:status,XP: xp}
        await self.leftPlayer.send(text_data=json.dumps(data))

    async def runMatch(self):
        try:
            await self.leftPaddle.init_paddel()
            await self.rightpaddle.init_paddel()
            previous_time = time.time()
            # while True:
            self.stats = RUNNING
            while self.rightScore < 2 and self.leftScore < 2:
                await asyncio.sleep(0.029)
                data = {
                    TYPE: 'ball',
                    'x': self.ball.x,
                    'y': self.ball.y,
                }
                await self.broadcast(data)
                current_time = time.time()
                delta_time = current_time - previous_time
                previous_time = current_time
                self.speed += Game.acceleration        
                self.ball.x += self.ball.xOrt * self.speed * delta_time
                self.ball.y += self.ball.yOrt * self.speed * delta_time
                await self.edges_collision()
                self.paddles_collision()
            self.stats = END
            await self.broadcast_result()
        except asyncio.CancelledError:
            pass
