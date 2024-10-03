enum Enum {
    LEFT = 'LEFT',
    RIGHT = 'RIGHT',
    EASY = 'easy',
    MEDIUM = 'medium',
    HARD = 'hard',
}

const _random = (min: number, max: number): number => {
    return Math.floor(Math.random() * (max - min + 1)) + min;
};

const toRad = (degrees: number): number => {
    return degrees * (Math.PI / 180);
};

class Ball {
    static reduisWidth: number = 3 / 2;
    static reduisHeight: number = 1.6 * Ball.reduisWidth;
    private _x: number = 50;
    private _y: number = 50;
    private _xOrt: number = 0;
    private _yOrt: number = 0;
    private _xDelta: number = 0;
    private _yDelta: number = 0;
    private ballElem: any;

    constructor(firstDir: Enum, ballElem: any) {
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
            angleDegrees = choice ? _random(100, 170) : _random(190, 260);
        } else {
            angleDegrees = choice ? _random(10, 80) : _random(280, 350);
        }
        const angleRadians = toRad(angleDegrees);
        this.xOrt = Math.cos(angleRadians);
        this.yOrt = Math.sin(angleRadians);
        this.xDelta = this.xOrt;
        this.yDelta = this.yOrt;
    }
}

class Paddle {
    static MIN_TIME = 50;
    static MOVE_STEP = 5;
    static WIDTH: number = 2;
    static HEIGHT: number = 20;
    static HALFHIEGHT: number = Paddle.HEIGHT / 2;
    static HALFWIDTH: number = Paddle.WIDTH / 2;
    private _x: number = 0;
    private _y: number = 50;
    private paddelElem: any;
    private _reactionDelay: number = 50;
    private gap: number = 15;
    private predictedY: number = 50;
    private errorMargin: number = 0;
    private lastUpdateTime: number;

    constructor(paddelElem: any, position: Enum, type: Enum = Enum.EASY) {
        this.paddelElem = paddelElem
        this.y = 50;
        this.x = position === Enum.RIGHT ? 98 : 2;
        this.lastUpdateTime = performance.now();
        switch (type) {
            case Enum.EASY:
                this._reactionDelay = 100;
                this.gap = 40;
                break;
            case Enum.MEDIUM:
                this._reactionDelay = 40;
                this.gap = 10;
                break;
            case Enum.HARD:
                this._reactionDelay = 30;
                this.gap = 1;
                break;
        }
    }
    get x(): number { return this._x; }

    set x(value: number) { this.paddelElem.style.left = `${value}%`; this._x = value }

    get y(): number { return this._y; }

    set y(value: number) { this.paddelElem.style.top = `${value}%`; this._y = value }

    get reactionDelay(): number { return this._reactionDelay; }

    collision(ball: any): boolean {
        const dx = Math.abs(ball.x - this.x);
        const dy = Math.abs(ball.y - this.y);
        return (
            dx <= Ball.reduisWidth + Paddle.HALFWIDTH &&
            dy <= Ball.reduisHeight + Paddle.HALFHIEGHT
        );
    }

    update(moves: number) {
        const currentTime = performance.now();
        const delta = currentTime - this.lastUpdateTime;
        if (delta < Paddle.MIN_TIME || Math.abs(moves) !== 1) {
            return;
        }
        let newY = this.y + moves * Paddle.MOVE_STEP;
        newY = Math.max(10, Math.min(newY, 90));
        this.y = newY;
        this.lastUpdateTime = currentTime;
    }

    AI_update(): void {
        let moves = 0;
        if (this.y < this.predictedY && Math.abs(this.y - this.predictedY) > 10) {
            moves = 1;
        } else if (this.y > this.predictedY && Math.abs(this.y - this.predictedY) > 10) {
            moves = -1;
        }
        this.update(moves);
    }

    predictBallPosition(ball: Ball): void {
        this.errorMargin = this.randomChoice([-this.gap, this.gap]);
        if (ball.xDelta < 0) {
            const distance = Math.abs(this.x - ball.x);
            const steps = distance / Math.abs(ball.xDelta);
            let _predictedY = ball.y + ball.yDelta * steps;
            
            while (_predictedY < 0 || _predictedY > 100) {
                if (_predictedY < 0) _predictedY = -_predictedY;
                if (_predictedY > 100) _predictedY = 200 - _predictedY;
            }
            if (Math.random() > 0.5) { // 50% probability 
                _predictedY += this.errorMargin;
            }
            this.predictedY = _predictedY;
            return
        }
        this.predictedY = this.y; // No change if ball isn't moving toward AI 
    }

    private randomChoice<T>(arr: T[]): T {
        return arr[Math.floor(Math.random() * arr.length)];
    }
}

class Game {
    static initialSpeed: number = .01;
    static acceleration: number = 0.0001;
    private ball: Ball;
    private rightPaddle: Paddle;
    private leftPaddle: Paddle;
    private _rightScore: number;
    private _leftScore: number;
    private speed: number;
    private lastCallTime: number = 0;
    private lastCallTime1: number = 0;

    constructor(ballElem: any, rightPaddel: any, lefttPaddel: any,
        type: Enum = Enum.LEFT) {
        this.ball = new Ball(Enum.RIGHT, ballElem);
        this.rightPaddle = new Paddle(rightPaddel, Enum.RIGHT);
        this.leftPaddle = new Paddle(lefttPaddel, Enum.LEFT, type)
        this._leftScore = 0;
        this._rightScore = 0;
        this.speed = Game.initialSpeed;
    }

    get rightScore(): number { return this._rightScore; }

    get leftScore(): number { return this._leftScore; }

    edgesCollision() {
        if (this.ball.y <= Ball.reduisHeight) {
            this.ball.yOrt *= this.ball.yOrt < 0 ? -1 : 1;
            this.ball.x = this.ball.x - this.ball.xDelta
            this.ball.y = Ball.reduisHeight
        } if (this.ball.y >= 100 - Ball.reduisHeight) {
            this.ball.yOrt *= this.ball.yOrt > 0 ? -1 : 1;
            this.ball.x = this.ball.x - this.ball.xDelta
            this.ball.y = 100 - Ball.reduisHeight
        } if (this.ball.x > 100 - (Paddle.WIDTH + Ball.reduisWidth)
            || this.ball.x < Paddle.WIDTH + Ball.reduisWidth) {
            // console.log(Paddle.WIDTH + Ball.reduisWidth, this.ball.x)
            if (this.ball.x > 50) {
                this._leftScore++;
            } else {
                this._rightScore++;
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

    updateGame(deltaTime: number) {
        this.speed += Game.acceleration;
        this.ball.xDelta = this.ball.xOrt * this.speed * deltaTime;
        this.ball.yDelta = this.ball.yOrt * this.speed * deltaTime;
        this.ball.x = this.ball.x + this.ball.xDelta;
        this.ball.y = this.ball.y + this.ball.yDelta;
        this.paddlesCollision();
        this.edgesCollision();
    }

    updateAIGame(deltaTime: number) {
        this.speed += Game.acceleration;
        this.ball.xDelta = this.ball.xOrt * this.speed * deltaTime;
        this.ball.yDelta = this.ball.yOrt * this.speed * deltaTime;
        this.ball.x = this.ball.x + this.ball.xDelta;
        this.ball.y = this.ball.y + this.ball.yDelta;
        const currentTime = performance.now();
        if (currentTime - this.lastCallTime >= 1000) { // Check if 1 second has passed
            this.leftPaddle.predictBallPosition(this.ball);
            this.lastCallTime = currentTime;
        }
        if (currentTime - this.lastCallTime1 >= this.leftPaddle.reactionDelay) {
            this.leftPaddle.AI_update()
            this.lastCallTime1 = currentTime;
        }
        this.paddlesCollision();
        this.edgesCollision();
    }
}

export { Game, Enum };
