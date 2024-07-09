const BALLSPEED = .025;
const BOOTSPEED = .025;
const randomBetw = (min: number, max: number) => {
    return Math.random() * (max - min) + min;
}

export class Ball {
    private DirX: number;
    private DirY: number;
    private _x: number;
    private _y: number;
    private Vi: number;
    private ballElem: any;
    private tableElem: any;
    private ballRect: any;
    private tableRect: any;

    constructor(ballElem: any, tableElem: any) {
        this.DirX = 0;
        this.DirY = 0;
        this.Vi = BALLSPEED;
        this.ballElem = ballElem;
        this.tableElem = tableElem;
        this._x = 50;
        this._y = 50;
        this.reset()
    }

    get x(): number { return this._x; }

    get y(): number { return this._y; }

    set x(value: number) { this._x = value; }

    set y(value: number) { this._y = value; }

    reset() {
        this.x = 50;
        this.y = 50;
        this.Vi = BALLSPEED;
        while (Math.abs(this.DirX) <= 0.2 || Math.abs(this.DirX) >= 0.9) {
            const angle: number = randomBetw(0, 2 * Math.PI);
            this.DirX = Math.cos(angle);
            this.DirY = Math.sin(angle);
        }
    }

    isFailure() {
        return (this.ballRect.right >= this.tableRect.right || this.ballRect.left <= this.tableRect.left);
    }

    isBound() {
        return (this.ballRect.bottom >= this.tableRect.bottom || this.ballRect.top <= this.tableRect.top);
    }

    update(delta: number, controlledPaddle: any, paddle: any) {
        this.Vi += .0001 * delta * BALLSPEED;
        this.ballRect = this.ballElem.getBoundingClientRect();
        this.tableRect = this.tableElem.getBoundingClientRect();
        // if (this.isBound())
        //     this.DirY *= -1;
        // if ((this.ballRect.left <= controlledPaddle.Dimention.right &&
        //     this.y > controlledPaddle.begin && this.y < controlledPaddle.end) ||
        //     (this.ballRect.right > paddle.Dimention.left &&
        //     this.y >= paddle.begin && this.y <= paddle.end)) {
        //     this.DirX *= -1;
        // }

        if (0 >= this.y || this.y >= 100)
            this.DirY *= -1;
        if (0 >= this.x || this.x >= 100)
            this.DirX *= -1;
        let dx = Math.abs(this.x - 3)
        let dy = Math.abs(this.y - controlledPaddle.pos)
        // if (dx <= 10 && dy <= )
        // if (this.x <= 1 + 2 && (this.y >= controlledPaddle.pos - 20 && this.y <= controlledPaddle.pos + 20))
        //     this.DirX *= (this.DirX < 0) ? -1 : 1;
        // else if (this.x <= 1 + 2)
        // if (this.x >= 97 && (this.y >= paddle.pos - 20 && this.y <= paddle.pos + 20))
        //     this.DirX *= (this.DirX > 0) ? -1 : 1;
        this.x += this.DirX * delta * this.Vi;
        this.y += this.DirY * delta * this.Vi;
        this.ballElem.style.left = `${this.x}%`;
        this.ballElem.style.top = `${this.y}%`;
    }
}

export class Paddle {
    private _pos: number;
    private _height: number;
    private _width: number;
    private paddleElem: any;
    // private _paddleDimention: any;

    constructor(paddleElem: any, tableElem: any) {
        this.paddleElem = paddleElem;
        // this._paddleDimention = paddleElem.getBoundingClientRect();
        this._pos = 50;
        this._height = (paddleElem.getBoundingClientRect().height
            / tableElem.getBoundingClientRect().height) * 100;
        this._width = (paddleElem.getBoundingClientRect().width
            / tableElem.getBoundingClientRect().width) * 100;
    }

    get pos(): number { return this._pos; }

    set pos(value: number) { this.paddleElem.style.top = `${value}%`; this._pos = value }

    get height(): number { return this._height }

    get width(): number { return this._width }

    get begin(): number { return this.pos - (this.height / 2) }

    get end(): number { return this.pos + (this.height / 2) }

    get Dimention(): any { return this.paddleElem.getBoundingClientRect(); }

    update(delta: number, ballHeight: number) {
        this._pos += BOOTSPEED * delta * (ballHeight - this._pos);
        this.pos = this._pos;
    }
}