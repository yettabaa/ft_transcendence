// const BALLSPEED = .025;
// const BOOTSPEED = .025;
// const randomBetw = (min: number, max: number) => {
//     return Math.random() * (max - min) + min;
// }

// export class Ball {
//     private DirX: number;
//     private DirY: number;
//     private _x: number;
//     private _y: number;
//     private Vi: number;
//     private ballElem: any;
//     private tableElem: any;
//     private ballRect: any;
//     private tableRect: any;

//     constructor(ballElem: any, tableElem: any) {
//         this.DirX = 0;
//         this.DirY = 0;
//         this.Vi = BALLSPEED;
//         this.ballElem = ballElem;
//         this.tableElem = tableElem;
//         this._x = 50;
//         this._y = 50;
//         this.reset()
//     }

//     get x(): number { return this._x; }

//     get y(): number { return this._y; }

//     set x(value: number) { this._x = value; }

//     set y(value: number) { this._y = value; }

//     reset() {
//         this.x = 50;
//         this.y = 50;
//         this.Vi = BALLSPEED;
//         while (Math.abs(this.DirX) <= 0.2 || Math.abs(this.DirX) >= 0.9) {
//             const angle: number = randomBetw(0, 2 * Math.PI);
//             this.DirX = Math.cos(angle);
//             this.DirY = Math.sin(angle);
//         }
//     }

//     update(delta: number, controlledPaddle: any, paddle: any) {
//         this.Vi += .0001 * delta * BALLSPEED;
//         this.ballRect = this.ballElem.getBoundingClientRect();
//         this.tableRect = this.tableElem.getBoundingClientRect();
//         // if (this.isBound())
//         //     this.DirY *= -1;
//         // if ((this.ballRect.left <= controlledPaddle.Dimention.right &&
//         //     this.y > controlledPaddle.begin && this.y < controlledPaddle.end) ||
//         //     (this.ballRect.right > paddle.Dimention.left &&
//         //     this.y >= paddle.begin && this.y <= paddle.end)) {
//         //     this.DirX *= -1;
//         // }

//         if (0 >= this.y || this.y >= 100)
//             this.DirY *= -1;
//         if (0 >= this.x || this.x >= 100)
//             this.DirX *= -1;
//         let dx = Math.abs(this.x - 3)
//         let dy = Math.abs(this.y - controlledPaddle.pos)
//         // if (dx <= 10 && dy <= )
//         // if (this.x <= 1 + 2 && (this.y >= controlledPaddle.pos - 20 && this.y <= controlledPaddle.pos + 20))
//         //     this.DirX *= (this.DirX < 0) ? -1 : 1;
//         // else if (this.x <= 1 + 2)
//         // if (this.x >= 97 && (this.y >= paddle.pos - 20 && this.y <= paddle.pos + 20))
//         //     this.DirX *= (this.DirX > 0) ? -1 : 1;
//         this.x += this.DirX * delta * this.Vi;
//         this.y += this.DirY * delta * this.Vi;
//         this.ballElem.style.left = `${this.x}%`;
//         this.ballElem.style.top = `${this.y}%`;
//     }
// }

// export class Paddle {
//     private _pos: number;
//     private _height: number;
//     private _width: number;
//     private paddleElem: any;
//     // private _paddleDimention: any;

//     constructor(paddleElem: any, tableElem: any) {
//         this.paddleElem = paddleElem;
//         // this._paddleDimention = paddleElem.getBoundingClientRect();
//         this._pos = 50;
//         this._height = (paddleElem.getBoundingClientRect().height
//             / tableElem.getBoundingClientRect().height) * 100;
//         this._width = (paddleElem.getBoundingClientRect().width
//             / tableElem.getBoundingClientRect().width) * 100;
//     }

//     get pos(): number { return this._pos; }

//     set pos(value: number) { this.paddleElem.style.top = `${value}%`; this._pos = value }

//     get height(): number { return this._height }

//     get width(): number { return this._width }

//     get begin(): number { return this.pos - (this.height / 2) }

//     get end(): number { return this.pos + (this.height / 2) }

//     get Dimention(): any { return this.paddleElem.getBoundingClientRect(); }

//     update(delta: number, ballHeight: number) {
//         this._pos += BOOTSPEED * delta * (ballHeight - this._pos);
//         this.pos = this._pos;
//     }
// }

const REDUIS_WIDTH = 3 / 2;
const REDUIS_HEIGHT = 1.6 * REDUIS_WIDTH;


// Helper function to get a random integer between two values
const getRandomInt = (min: number, max: number): number => {
    return Math.floor(Math.random() * (max - min + 1)) + min;
};

// Helper function to convert degrees to radians
const degreesToRadians = (degrees: number): number => {
    return degrees * (Math.PI / 180);
};

enum Enum {
    LEFT = 'LEFT',
    RIGHT = 'RIGHT',
}

export class Ball {
    static reduisWidth: number = 3 / 2;
    static reduisHeight: number = 1.6 * Ball.reduisWidth;
    private _x: number = 50;
    private _y: number = 50;
    private _xOrt: number = 0;
    private _yOrt: number = 0;
    private _xDelta: number = 0;
    private _yDelta: number = 0;
    private ballElem: any;

    constructor(firstDir: Enum, ballElem:any) {
        this.ballElem = ballElem;
        this.reset(firstDir);
    }

    get x(): number { return this._x; }

    set x(value: number) { this.ballElem.style.left = `${value}%`; this._x = value }

    get y(): number { return this._y; }

    set y(value: number) { this.ballElem.style.top = `${value}%`; this._y = value }

    get xOrt(): number { return this._xOrt; }

    set xOrt(value: number) { this._xOrt = value }

    get yOrt(): number { return this._yOrt; }

    set yOrt(value: number) { this._yOrt = value }

    get xDelta(): number { return this._xDelta; }

    set xDelta(value: number) { this._xDelta = value }

    get yDelta(): number { return this._yDelta; }

    set yDelta(value: number) { this._yDelta = value }

    reset(dir: Enum) {
        this.x = 50;
        this.y = 50;
        const choice = Math.random() < 0.5;
        let angleDegrees: number;

        if (dir === Enum.LEFT) {
            angleDegrees = choice ? getRandomInt(100, 170) : getRandomInt(190, 260);
        } else {
            angleDegrees = choice ? getRandomInt(10, 80) : getRandomInt(280, 350);
        }

        const angleRadians = degreesToRadians(angleDegrees);
        this.xOrt = Math.cos(angleRadians);
        this.yOrt = Math.sin(angleRadians);
        this.xDelta = this.xOrt;
        this.yDelta = this.yOrt;
    }
}

export class Paddle {
    static width: number = 2;
    static height: number = 20;
    static halfHeight: number = Paddle.height / 2;
    static halfWidth: number = Paddle.width / 2;

    private _x: number = 0;
    private _y: number = 50;
    private paddelElem: any;
    
    constructor(position: Enum, paddelElem: any) {
        this.paddelElem = paddelElem
        this.y = 50;
        this.x = position === Enum.RIGHT ? 98 : 2;
    }

    get x(): number { return this._x; }

    set x(value: number) { this.paddelElem.style.left = `${value}%`; this._x = value }

    get y(): number { return this._y; }

    set y(value: number) { this.paddelElem.style.top = `${value}%`; this._y = value }

    collision(ball: any): boolean {
        const dx = Math.abs(ball.x - this.x);
        const dy = Math.abs(ball.y - this.y);
        console.log(dx <= ball.reduisWidth + Paddle.halfWidth &&
            dy <= ball.reduisHeight + Paddle.halfHeight)
        return (
            dx <= Ball.reduisWidth + Paddle.halfWidth &&
            dy <= Ball.reduisHeight + Paddle.halfHeight
        );
    }
}

class Game {
    static initialSpeed: number = .01;
    static acceleration: number = 0.0001;
    private ball: Ball;
    private rightPaddle: Paddle;
    private leftPaddle: Paddle;
    private leftScore: number;
    private rightScore: number;
    private speed: number;
    // rightPlayer: WebSocket;
    // leftPlayer: WebSocket;
    // state: Enum;
    // id: number;

    constructor(ballElem:any, rightPaddel:any, lefttPaddel:any) {
        this.ball = new Ball(Enum.RIGHT, ballElem);
        this.rightPaddle = new Paddle(Enum.RIGHT, rightPaddel);
        this.leftPaddle = new Paddle(Enum.LEFT, lefttPaddel);
        this.leftScore = 0;
        this.rightScore = 0;
        // this.rightPlayer = socket1;
        // this.leftPlayer = ai_socket2 ? (ai_socket2 as WebSocket) : socket1;
        this.speed = Game.initialSpeed;
        // this.state = Enum.INITIALIZED;
        // this.id = 0;
    }

    edgesCollision() {
        if (this.ball.y <= 0 + Ball.reduisHeight) {
            this.ball.yOrt *= -1;
        }
        if (this.ball.y >= 100 - Ball.reduisHeight) {
            this.ball.yOrt *= -1;
        }
        if (this.ball.x > 100 - Ball.reduisWidth || this.ball.x < 0 + Ball.reduisWidth) {
            if (this.ball.x > 50) {
                this.leftScore++;
            } else {
                this.rightScore++;
            }
            this.speed = Game.initialSpeed;
            this.ball.reset(this.ball.x > 50 ? Enum.RIGHT : Enum.LEFT);
        }
    }

    paddlesCollision() {
        if (this.rightPaddle.collision(this.ball)) {
            this.ball.xOrt *= -1;
            if (this.ball.x > 97 - Ball.reduisWidth) {
                this.ball.x = 97 - Ball.reduisWidth;
                this.ball.y = this.ball.y - this.ball.yDelta;
            }
        }
        if (this.leftPaddle.collision(this.ball)) {
            this.ball.xOrt *= -1;
            if (this.ball.x < 3 + Ball.reduisWidth) {
                this.ball.x = 3 + Ball.reduisWidth;
                this.ball.y = this.ball.y - this.ball.yDelta;
            }
        }
    }
    sleepSync(ms: number): void {
        const end = Date.now() + ms;
        while (Date.now() < end) {
            // Busy wait loop
        }
    }
    game(deltaTime:number, goals: number = 10, timeLimit: number = -1) {
        // const startTime = Date.now();
        // let previousTime = startTime;
        // while (this.rightScore < goals && this.leftScore < goals) {
            // const currentTime = Date.now();
            // const deltaTime = (currentTime - previousTime) / 1000; // in seconds
            // previousTime = currentTime;
            
            // if (timeLimit !== -1 && currentTime - startTime > timeLimit * 1000) {
            //     break;
            // }
            // this.sleepSync(100)
            // await new Promise((r) => setTimeout(r, 29)); // to avoid the loop running too fast
            this.speed += Game.acceleration;
            this.ball.xDelta = this.ball.xOrt * this.speed * deltaTime;
            this.ball.yDelta = this.ball.yOrt * this.speed * deltaTime;
            this.ball.x = this.ball.x + this.ball.xDelta;
            this.ball.y = this.ball.y + this.ball.yDelta;
            // console.log(this.ball.x)

            this.paddlesCollision();
            this.edgesCollision();
        // }

    }

    runGame(deltaTime:number,goals: number, timeLimit: number) {
        try {
            this.game(deltaTime,goals, timeLimit);
        } catch (error) {
            console.error('Exception in runGame:', error);
        }
    }
}

export { Game };
