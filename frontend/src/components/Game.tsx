// src/components/PingPongTable.tsx
import React, { useEffect, useState, useRef } from 'react';


interface Position {
    x: number;
    y: number;
}

interface Positions {
    paddle1: Position;
    paddle2: Position;
    ball: Position;
}

const PingPongTable: React.FC = () => {
    const [positions, setPositions] = useState<Positions>({
        paddle1: { x: 1, y: 50 },
        paddle2: { x: 97, y: 50 },
        ball: { x: 50, y: 50 },
    });
    const table: any = useRef();
    const paddle: any = useRef();
    const ws: any = useRef();

    useEffect(() => {
        ws.current = new WebSocket('ws://127.0.0.1:8000/ws/game/');

        ws.current.onopen = () => { console.log('WebSocket connection established'); };

        ws.current.onmessage = (event: any) => {
            console.log(event.data)
            // const data = JSON.parse(event.data);
            // setPositions(data);
        };

        ws.current.onclose = (event: any) => {
            if (event.wasClean) {
                console.log(`Connection closed cleanly, code=${event.code} reason=${event.reason}`);
            } else {
                console.error('WebSocket connection died');
            }
        };

        ws.current.onerror = (error: any) => { console.error(`WebSocket error: ${error.message}`); };

        const handelMouse = (e: any) => {
            const tableDimention: any = table.current.getBoundingClientRect();
            let posPaddle: number = ((e.y - tableDimention.top)
            / tableDimention.height) * 100;
            (posPaddle < 10) && (posPaddle = 10);
            (posPaddle > 90) && (posPaddle = 90);
            // ws.current.send(posPaddle);
            paddle.current.style.top = `${posPaddle}%`;
        }

        window.addEventListener('mousemove', handelMouse);

        return () => { ws.current.close(); window.removeEventListener('mousemove', handelMouse); };
    }, []);

    // useEffect(() => {
    //   }, []);

    return (
        <div className="bg-bg h-[100vh] flex  justify-center">
            <div className="relative flex flex-row bg-green-700 w-[60vw] h-[30vh] rounded-md self-center overflow-hidden"
                ref={table} >
                <div
                    ref={paddle}
                    className="absolute w-[2%] h-[20%] bg-white translate-y-[-50%]"
                    style={{ left: `${positions.paddle1.x}%`, top: `${positions.paddle1.y}%` }}
                />
                <div
                    className="absolute w-[2%] h-[20%] bg-white translate-y-[-50%]"
                    style={{ left: `${positions.paddle2.x}%`, top: `${positions.paddle2.y}%` }}
                />
                <div
                    className="absolute w-5 h-5 bg-white rounded-full translate-y-[-50%] translate-x-[-50%]"
                    style={{ left: `${positions.ball.x}%`, top: `${positions.ball.y}%` }}
                />
            </div>
        </div>
    );
};

export default PingPongTable;