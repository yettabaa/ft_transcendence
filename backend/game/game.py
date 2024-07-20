import asyncio
import json
import math
import random
import time

class Ball:
    # height = 1.5 * width ()
    reduisWidth = 3 / 2
    reduisHeight = 1.5 * reduisWidth
    def __init__(self, firstDir) -> None:
        self.reset(firstDir)

    def reset(self, dir):
        self.x = 50.
        self.y = 50.
        choice = random.randint(0, 1)
        if dir == 'left':
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
        self.myPos = 97 if self.position == 'right' else 1
        sidePos = 1 if self.position == 'right' else 97
        data = {
            'type':'init_paddle',
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
        self.ball = Ball('right')
        self.rightpaddle = Paddle(socket1, 'right')
        self.leftPaddle = Paddle(socket2, 'left')
        self.leftScore = 0
        self.rightScore = 0
        self.socket = socket1
        self.speed = Game.speedBall
        self.ingame = True

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
            self.ball.reset('right' if self.ball.x > 50 else 'left')
            data = {
                'type': 'score',
                'right': self.rightScore,
                'left': self.leftScore,
            }
            await self.socket.send_update(data)

    def paddles_collision(self):
        if self.rightpaddle.collision(self.ball):
            self.ball.xOrt *= -1 if self.ball.xOrt > 0 else 1
        if self.leftPaddle.collision(self.ball):
            self.ball.xOrt *= -1 if self.ball.xOrt < 0 else 1

    async def runMatch(self):
        try:
            await self.leftPaddle.init_paddel()
            await self.rightpaddle.init_paddel()
            previous_time = time.time()
            while self.rightScore < 5 and self.leftScore < 5:
                data = {
                    'type': 'ball',
                    'x': self.ball.x,
                    'y': self.ball.y,
                }
                await self.socket.send_update(data)
                current_time = time.time()
                delta_time = current_time - previous_time
                previous_time = current_time
                self.speed += Game.acceleration        
                self.ball.x += self.ball.xOrt * self.speed * delta_time
                self.ball.y += self.ball.yOrt * self.speed * delta_time
                await self.edges_collision()
                self.paddles_collision()
                await asyncio.sleep(0.029)
            data = {
                'type':'end',
            }
            await self.socket.send_update(data)
        except asyncio.CancelledError:
            pass
