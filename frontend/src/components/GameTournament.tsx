import React, { useEffect, useState, useRef } from 'react';
import { BrowserRouter as Router, Route, Routes, useParams } from 'react-router-dom';

interface Position {
    x: number;
    y: number;
}

interface Positions {
    paddle1: Position;
    paddle2: Position;
    ball: Position;
}

const GameTournament: React.FC = () => {
    const [positions, setPositions] = useState<Positions>({
        paddle1: { x: 1, y: 50 },
        paddle2: { x: 97, y: 50 },
        ball: { x: 50, y: 50 },
    });
    const leftScore: any = useRef()
    const rightScore: any = useRef()
    const table: any = useRef();
    const myPaddle: any = useRef();
    const paddle: any = useRef();
    const ball: any = useRef();
    const ws: any = useRef();
    const [ballSize, setBallSize] = useState<number>(0);
    const { alias } = useParams<{ alias: string }>();
    const { playersNum } = useParams<{ playersNum: string }>();
    
    if (alias == undefined || alias === '' || alias == null)
        return;
    const moveDirection = useRef<number>(0);
    const moveInterval = useRef<NodeJS.Timeout | null>(null);
    const handleKeyDown = (e: KeyboardEvent) => {
        if (moveDirection.current !== 0) return; // Avoid multiple intervals

        if (e.key === 'ArrowUp') {
            moveDirection.current = -1; // Paddle moving up
        } else if (e.key === 'ArrowDown') {
            moveDirection.current = 1; // Paddle moving down
        }

        if (moveDirection.current !== 0) {
            // Start sending updates every 50ms
            moveInterval.current = setInterval(() => {
                if (moveDirection.current == 0) return;
                ws.current.send(JSON.stringify({
                    type: 'update',
                    y: moveDirection.current // Send the movement direction (-1 or 1)
                }));
            }, 50); // Update every 50ms
        }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
        if ((e.key === 'ArrowUp' && moveDirection.current === -1) || (e.key === 'ArrowDown' && moveDirection.current === 1)) {
            moveDirection.current = 0; // Stop moving
        }
    };

    const handleResize = () => {
        if (table.current) {
            const tableWidth = table.current.offsetWidth;
            const radius = tableWidth * 0.03; // 3% of table width
            setBallSize(radius);
        }
    }

    const [data, setData] = useState<any>(null);
    const [ingame, setIngame] = useState<boolean>(false)

    useEffect(() => {
        if (!ws.current) {
            ws.current = new WebSocket(`ws://127.0.0.1:8000/ws/game_tournament/${playersNum}/${alias}`);
            ws.current.onopen = () => { console.log('WebSocket connection established'); };
            
            ws.current.onmessage = (event: any) => {
            const jsondata = JSON.parse(event.data);
            if (jsondata.type != 'ball' && jsondata.type != 'myPaddle' && jsondata.type != 'sidePaddle')
                console.log(jsondata)
            if (jsondata.type == 'end') {
                setIngame(false)
                // setNotificationVisible(false);
                if (jsondata.status == 'im the winer')
                    return
                ws.current.send(JSON.stringify({ type: 'qualifyboard' }));
            } if (jsondata.type == 'opponents') {
                // setNotificationMessage(`${jsondata.user1} vs ${jsondata.user2}`);
                // setNotificationVisible(true);
                    
            } if (jsondata.type == 'dashboard') {
                setData(jsondata.rounds)
                console.log(jsondata.rounds[0])
            } if (jsondata.type == 'init_paddle') {
                setIngame(true)
                handleResize()
                setPositions((prevPositions) => ({
                    ...prevPositions,
                    paddle1: {
                        ...prevPositions.paddle1,
                        x: jsondata.my,
                    },
                    paddle2: {
                        ...prevPositions.paddle2,
                        x: jsondata.side,
                    },
                    
                }))
            }
            if (jsondata.type == 'ball') {
                ball.current.style.top = `${jsondata.y}%`;
                ball.current.style.left = `${jsondata.x}%`;
            }
            if (jsondata.type == 'score') {
                rightScore.current.innerText = jsondata.right;
                leftScore.current.innerText = jsondata.left;
            }
            if (jsondata.type == 'sidePaddle') {
                paddle.current.style.top = `${jsondata.pos}%`
            }
            if (jsondata.type == 'myPaddle') {
                myPaddle.current.style.top = `${jsondata.pos}%`
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
    }
        handleResize()
        
        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);
        window.addEventListener('resize', handleResize);
        return () => {
            if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                ws.current.close();
                ws.current = null; // Clean up the reference
            }
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
            window.removeEventListener('resize', handleResize);
        };
    }, []);
    
    return (
        <div className="bg-bg h-[100vh] flex flex-col gap-8 justify-center items-center">
            {/* {notificationVisible && (
                <div className="notification-bar bg-blue-600 text-white p-4 rounded flex justify-between items-center">
                    <span>{notificationMessage}</span>
                    <div className="flex gap-2">
                        <button className="bg-green-500 p-2 rounded" onClick={handleAccept}>Accept</button>
                        <button className="bg-red-500 p-2 rounded" onClick={handleReject}>Reject</button>
                    </div>
                </div>
            )} */}
            {ingame && (
                <>
                    <div className="h-[10%] flex flex-row justify-center items-center">
                        <div ref={leftScore} className="p-[0.5rem] border-r"> 0 </div>
                        <div ref={rightScore} className="p-[0.5rem] " > 0 </div>
                    </div>
                    <div ref={table}
                        className="relative flex flex-row bg-green-700 w-[64vw] h-[40vw] rounded-md self-center overflow-hidden">
                        <div ref={myPaddle}
                            className="absolute text-cyan-700 w-[2%] h-[20%] bg-white translate-y-[-50%]"
                            style={{ left: `${positions.paddle1.x}%`, top: `${positions.paddle1.y}%` }}
                        />
                        <div ref={paddle}
                            className="absolute w-[2%] h-[20%] bg-white translate-y-[-50%]"
                            style={{ left: `${positions.paddle2.x}%`, top: `${positions.paddle2.y}%` }}
                        />
                        <div ref={ball}
                            className="absolute top-[50%] left-[50%] bg-white rounded-full translate-y-[-50%] translate-x-[-50%]"
                            style={{

                                width: `${ballSize}px`, height: `${ballSize}px`
                            }}
                        />
                    </div>
                </>
            )}
            {!ingame && (
                <div className="bg-gray-100 mb-4 tournament-bracket">
                    {data && (data.map((round, roundIndex) => (
                        <div key={roundIndex} className="round p-4">
                            <h2 className="text-gray-950 text-xl font-bold mb-2 round-title">Round {roundIndex + 1}</h2>
                            <div className="p-4 bg-gray-50 rounded">
                                {Object.entries(round).map(([username, value]) => (
                                    <p className="text-gray-700 username" key={username}>{username}: {value}</p>
                                ))}
                            </div>
                        </div>
                    )))}
                </div>
            )}
        </div>
    );
}

export default GameTournament;