import asyncio

class Game:
    speedBall = .025
    def __init__(self, socket) -> None:
        self.ballx = 50
        self.bally = 50
        self.socket = socket

    async def runMatch(self):
        while True:
            dataTosSend = {
                'ballx': self.ballx,
                'bally': self.bally,
            }
            await self.socket.channel_layer.group_send(
                self.socket.room_name,
                {
                    'type': 'game.update',
                    'data': dataTosSend
                }
            )
            self.ballx += .7 * Game.speedBall
            self.bally += .7 * Game.speedBall
            await asyncio.sleep(0.003)

