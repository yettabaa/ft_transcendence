import React, { useEffect, useState, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { BrowserRouter as Router, Route, Routes, useParams } from 'react-router-dom';
import { Link, useNavigate } from "react-router-dom";
import Cookies from 'js-cookie';

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
    const [isVesible, setIsVesible] = useState<boolean>(false)
    const leftScore: any = useRef()
    const rightScore: any = useRef()
    const table: any = useRef();
    const myPaddle: any = useRef();
    const paddle: any = useRef();
    const ball: any = useRef();
    const time: any = useRef();
    const ws: any = useRef();
    const [ballSize, setBallSize] = useState<number>(0);
    const { username } = useParams<{ username: string }>();
    const { game_id } = useParams<{ game_id: string }>();
    const navigate = useNavigate();
    
    const handelMouse = (e: any) => {
        // if (isVesible) {
            const tableDimention: any = table.current.getBoundingClientRect();
            let posPaddle: number = ((e.y - tableDimention.top)
            / tableDimention.height) * 100;
            (posPaddle < 10) && (posPaddle = 10);
            (posPaddle > 90) && (posPaddle = 90);
            myPaddle.current.style.top = `${posPaddle}%`;
            ws.current.send(JSON.stringify({
                type: 'update',
                y: posPaddle
            }));
        // }
    }

    const handleResize = () => {
        if (table.current) {
            const tableWidth = table.current.offsetWidth;
            const radius = tableWidth * 0.03; // 3% of table width
            setBallSize(radius);
        }
    }
    
    // const token = Cookies.get('auth_token');
    const token = localStorage.getItem('token');
    useEffect(() => {
        console.log('Token:', token);  // Check if the token is available
        if (token && !username) {
            ws.current = new WebSocket(`ws://127.0.0.1:8000/ws/aigame/medium/10/300/?token=${token}`);
            // ws.current = new WebSocket(`ws://127.0.0.1:8000/ws/game/random/?token=${token}`);
        } else {
            ws.current = new WebSocket(`ws://127.0.0.1:8000/ws/game/${username}/${game_id}`);
            console.error('Token is undefined or missing.');
        }


        ws.current.onopen = () => { console.log('WebSocket connection established'); };

        ws.current.onmessage = (event: any) => {
            const data = JSON.parse(event.data);
            if (data.type == 'disconnect') {
                console.log(data)
            } else if (data.type == 'end') {
                console.log(data)
                navigate('/login')
            } else if(data.type == 'opponents') {
                console.log(data)
                ws.current.send(JSON.stringify({
                    type: 'start',
                }));
            } else if (data.type == 'init_paddle') {
                
                console.log(data)
                setIsVesible(true)
                setPositions((prevPositions) => ({
                    ...prevPositions,
                    paddle1: {
                        ...prevPositions.paddle1,
                        x: data.my,
                    },
                    paddle2: {
                        ...prevPositions.paddle2,
                        x: data.side,
                    },
                }))
            }
            if (data.type == 'ball') {
                ball.current.style.top = `${data.y}%`;
                ball.current.style.left = `${data.x}%`;
                time.current.innerText = parseInt(data.time)
            }
            if (data.type == 'score') {
                rightScore.current.innerText = data.right;
                leftScore.current.innerText = data.left;
            }
            if (data.type == 'paddle') {
                // console.log(data)
                paddle.current.style.top = `${data.pos}%`
            }
        };


        ws.current.onclose = (event: any) => {
            if (event.wasClean) {
                console.log(`Connection closed cleanly, code=${event.code} reason=${event.reason}`);
            } else {
                console.error('WebSocket connection died');
            }
        };

        ws.current.onerror = (error: any) => { console.error(`WebSocket error: ${error.message}`); };
        
        handleResize()
        window.addEventListener('mousemove', handelMouse);
        window.addEventListener('resize', handleResize);
        return () => { 
            if (ws.current)
                ws.current.close();
            window.removeEventListener('mousemove', handelMouse); 
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    return (
        <div className="bg-bg h-[100vh] flex flex-col gap-8 justify-center items-center">
            <div className="h-[10%] flex flex-row justify-center items-center">
                <div ref={time} className="p-[0.5rem]"> 0 </div>
            </div>
            <div className="h-[10%] flex flex-row justify-center items-center">
                <div ref={leftScore} className="p-[0.5rem] border-r"> 0 </div>
                <div ref={rightScore} className="p-[0.5rem] " > 0 </div>
            </div>
            <div className="relative flex flex-row bg-green-700 w-[64vw] h-[40vw] rounded-md self-center overflow-hidden"
                ref={table} >
                {isVesible && (
                    <>
                        <div ref={myPaddle}
                            className="absolute text-cyan-700 w-[2%] h-[20%] bg-white translate-y-[-50%]"
                            style={{ left: `${positions.paddle1.x}%`, top: `${positions.paddle1.y}%` }}
                        />
                        <div ref={paddle}
                            className="absolute w-[2%] h-[20%] bg-white translate-y-[-50%]"
                            style={{ left: `${positions.paddle2.x}%`, top: `${positions.paddle2.y}%` }}
                        />
                    </>
                )}
                <div ref={ball}
                    className="absolute  bg-white rounded-full translate-y-[-50%] translate-x-[-50%]"
                    style={{ left: `${positions.ball.x}%`, top: `${positions.ball.y}%`,
                            width: `${ballSize}px`, height: `${ballSize}px` }}
                />
            </div>
        </div>
    );
};

export default PingPongTable;