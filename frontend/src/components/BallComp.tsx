import React, { useEffect, useRef, useState } from 'react';
import { Game, Enum } from './class';


const BallComp = () => {
    const ballElem: any = useRef();
    const tableElem: any = useRef();
    const rightPaddel: any = useRef();
    const leftPaddel: any = useRef();
    const game: any = useRef();
    const posPaddle = useRef(0);
    const animationRef: any = useRef(); // To store the animation frame id
    const lastTime: any = useRef<FrameRequestCallback>();
    const moves = useRef(0);

    const handelMouse = (e: any) => {
        const tableDimention = tableElem.current.getBoundingClientRect();
        posPaddle.current = ((e.y - tableDimention.top)
        / tableDimention.height) * 100;
        (posPaddle.current < 10) && (posPaddle.current = 10);
        (posPaddle.current > 90) && (posPaddle.current = 90);
        game.current.rightPaddle.y = posPaddle.current;
        // game.current.leftPaddle.y = posPaddle.current;
    }
    const handleKeyDown = (e: KeyboardEvent) => {
        // let moves = 0;
        if (e.key === 'ArrowUp') {
            moves.current = -1; // Move paddle up
        }else if (e.key === 'ArrowDown') {
            moves.current = 1; // Move paddle down
        }
        // game.current.rightPaddle.update(moves.current);
        
    };
    const handleKeyUp = (e: KeyboardEvent) => {
        if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
            moves.current = 0; // Stop moving when key is released
        }
    };

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
            game.current = new Game(ballElem.current, rightPaddel.current, 
                leftPaddel.current, Enum.EASY)
            if (!animationRef.current)
                animationRef.current = requestAnimationFrame(loop_hook);
        }
        handleResize()
        // document.addEventListener("mousemove", handelMouse)
        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);
        window.addEventListener('resize', handleResize);
        return () => {
            // document.removeEventListener("mousemove", handelMouse)
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
            window.removeEventListener('resize', handleResize);
        }
    }, [])

    const loop_hook = (time: number) => {
        if (lastTime.current != undefined) {
            const delta: number = time - lastTime.current
            if (moves.current !== 0) {
                game.current.rightPaddle.update(moves.current); // Update paddle continuously
            }
            game.current.updateAIGame(delta)
            if (game.current.rightScore >= 10 || game.current.leftScore >= 10)
                return
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