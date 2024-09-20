import React, { useEffect, useRef, useState } from 'react';
import { Game } from './class';


const BallComp = () => {
    const ballElem: any = useRef();
    const tableElem: any = useRef();
    const rightPaddel: any = useRef();
    const leftPaddel: any = useRef();
    const game: any = useRef();
    const posPaddle = useRef(0);
    const animationRef: any = useRef(); // To store the animation frame id
    const lastTime: any = useRef<FrameRequestCallback>();

    const handelMouse = (e: any) => {
        const tableDimention = tableElem.current.getBoundingClientRect();
        posPaddle.current = ((e.y - tableDimention.top)
        / tableDimention.height) * 100;
        (posPaddle.current < 10) && (posPaddle.current = 10);
        (posPaddle.current > 90) && (posPaddle.current = 90);
        game.current.rightPaddle.y = posPaddle.current;
        game.current.leftPaddle.y = posPaddle.current;
    }

    const [ballSize, setBallSize] = useState<number>(0);
    const handleResize = () => {
        if (tableElem.current) {
            const tableWidth = tableElem.current.offsetWidth;
            const radius = tableWidth * 0.03; // 3% of table width
            setBallSize(radius);
        }
    }
    
    useEffect(() => {
        if (ballElem.current && tableElem.current &&
            rightPaddel.current && leftPaddel.current) {
            game.current = new Game(ballElem.current, rightPaddel.current, leftPaddel.current)
            if (!animationRef.current)
                animationRef.current = requestAnimationFrame(loop_hook);
        }
        handleResize()
        document.addEventListener("mousemove", handelMouse)
        window.addEventListener('resize', handleResize);
        return () => {
            document.removeEventListener("mousemove", handelMouse)
            window.removeEventListener('resize', handleResize);
        }
    }, [])

    const loop_hook = (time: number) => {
        if (lastTime.current != undefined) {
            const delta: number = time - lastTime.current
            if (ballElem.current && tableElem.current &&
                rightPaddel.current && leftPaddel.current) {
                game.current.game(delta,10, 300)
            }
        }
        lastTime.current = time
        animationRef.current = requestAnimationFrame(loop_hook);
    }
    return (
        <div ref={tableElem}
            className="relative flex flex-row bg-green-700 w-[64vw] h-[40vw] rounded-md self-center overflow-hidden">
            <div ref={ballElem}
                className="absolute  bg-white rounded-full translate-y-[-50%] translate-x-[-50%]"
                style={{
                    left: `50%`, top: `50%`, width: `${ballSize}px`,
                    height: `${ballSize}px`,
                }}>
            </div>
            <div ref={rightPaddel}
                className="absolute w-[2%] h-[20%] bg-white translate-y-[-50%] translate-x-[-50%]">
            </div>
            <div ref={leftPaddel}
                className="absolute w-[2%] h-[20%] bg-white translate-y-[-50%] translate-x-[-50%]">
            </div>
        </div>
    );
}

export default BallComp;