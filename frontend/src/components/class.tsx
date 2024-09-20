enum Enum {
    LEFT = 'LEFT',
    RIGHT = 'RIGHT',
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
    private _rightScore: number;
    private _leftScore: number;
    private speed: number;

    constructor(ballElem: any, rightPaddel: any, lefttPaddel: any) {
        this.ball = new Ball(Enum.RIGHT, ballElem);
        this.rightPaddle = new Paddle(Enum.RIGHT, rightPaddel);
        this.leftPaddle = new Paddle(Enum.LEFT, lefttPaddel);
        this._leftScore = 0;
        this._rightScore = 0;
        this.speed = Game.initialSpeed;
    }

    get rightScore(): number { return this._rightScore; }

    get leftScore(): number { return this._leftScore; }

    edgesCollision() {
        if (this.ball.y <= 0 + Ball.reduisHeight) {
            this.ball.yOrt *= this.ball.yOrt < 0 ? -1 : 1;
        } if (this.ball.y >= 100 - Ball.reduisHeight) {
            this.ball.yOrt *= this.ball.yOrt > 0 ? -1 : 1;
        } if (this.ball.x > 100 - Ball.reduisWidth || this.ball.x < 0 + Ball.reduisWidth) {
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
}

export { Game };
