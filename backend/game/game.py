import asyncio

class Ball:
    def __init__(self) -> None:
        self.x = 50
        self.y = 50
        self.xOrt = .4
        self.yOrt = .3

class Paddle:
    def __init__(self, socket) -> None:
        self.socket = socket

    def pos(self):
        return self.socket.paddlePos


class Game:
    speedBall = .025
    def __init__(self, socket1, socket2) -> None:
        self.ball = Ball()
        self.paddle1 = Paddle(socket1)
        self.paddle2 = Paddle(socket2)
        self.socket = socket1

        # self.paddleP2 = 50

    async def runMatch(self):
        while True:
            dataTosSend = {
                'update': 'ball',
                'ballx': self.ball.x,
                'bally': self.ball.y,
            }
            await self.socket.send_update(dataTosSend, '')
            if not 0 <= self.ball.x <= 100:
                self.ball.xOrt *= -1
            if not 0 <= self.ball.y <= 100:
                self.ball.yOrt *= -1
            # if 1 + 2 <= self.ballx <= 97 - 2 and self. paddlePos -10 <= self.bally <= self.paddlePos +10: # x position in frontend
            #     self.directy *= -1
            self.ball.x += self.ball.xOrt * Game.speedBall
            self.ball.y += self.ball.yOrt * Game.speedBall
            await asyncio.sleep(0.001)

