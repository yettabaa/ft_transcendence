import React, { useEffect, useRef } from 'react';
import { LoopHook } from './LoopHook';
import { Ball, Paddle } from './class';


const BallComp = () => {
    const ballElem: any = useRef();
    const tableElem: any = useRef();
    const controlledPaddleElem: any = useRef();
    const paddleBootElem: any = useRef();

    const ball: any = useRef();
    const paddleBoot: any = useRef();
    const controlledPaddle: any = useRef();
    const posPaddle = useRef(0);

    useEffect(() => {
        if (ballElem.current && tableElem.current &&
            controlledPaddleElem.current && paddleBootElem.current) {
            ball.current = new Ball(ballElem.current, tableElem.current);
            paddleBoot.current = new Paddle(paddleBootElem.current, tableElem.current);
            controlledPaddle.current = new Paddle(controlledPaddleElem.current, tableElem.current);

            const handelMouse = (e: any) => {
                const tableDimention = tableElem.current.getBoundingClientRect();
                posPaddle.current = ((e.y - tableDimention.top)
                / tableDimention.height) * 100;
                (posPaddle.current < 0) && (posPaddle.current = 0);
                (posPaddle.current > 100) && (posPaddle.current = 100);
                controlledPaddle.current.pos = posPaddle.current;
            }
            document.addEventListener("mousemove", handelMouse)
            return () => {
                document.removeEventListener("mousemove", handelMouse)
            }
        }
    }, [ballElem, tableElem, controlledPaddleElem, paddleBootElem])

    LoopHook((delta: number) => {
        if (ballElem.current && tableElem.current &&
            controlledPaddleElem.current && paddleBootElem.current) {
            ball.current.update(delta, controlledPaddle.current, paddleBoot.current);
            paddleBoot.current.update(delta, ball.current.y);
            if (ball.current.isFailure()) {
                ball.current.reset();
            }
        }
    });
    return (
        <div ref={tableElem}
            className="relative overflow-hidden rounded-[10px] border-[1px] border-[#2b2d30]
				 bg-red-700 h-[90%] min-w-[500px] w-full">
            <div ref={ballElem}
                className="absolute h-[2.5vh] w-[2.5vh] top-[0%] left-[0%] rounded-[50%] translate-x-[-50%] translate-y-[-50%] bg-white"
                style={{ left: `50%`, top: `50%` }}>
            </div>
            <div ref={controlledPaddleElem}
                className="absolute  top-[50%] left-[1%] rounded-[1rem]
                translate-y-[-50%] h-[20%] w-[2%] bg-white">
            </div>
            <div ref={paddleBootElem}
                className="absolute top-[50%] right-[1%] rounded-[1rem]
                translate-y-[-50%] h-[20%] w-[2%] bg-white">
            </div>
        </div>
    );
}

export default BallComp;