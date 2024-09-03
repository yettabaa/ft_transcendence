import React, { useEffect, useState, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { BrowserRouter as Router, Route, Routes, useParams } from 'react-router-dom';
import { Link, useNavigate } from "react-router-dom";

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
    const { username } = useParams<{ username: string }>();
    const { type } = useParams<{ type: string }>();
    const navigate = useNavigate();
    
    if (username == undefined || username === '' || username == null)
        return;
    
    const handelMouse = (e: any) => {
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
    }

    const handleResize = () => {
        if (table.current) {
            const tableWidth = table.current.offsetWidth;
            const radius = tableWidth * 0.03; // 3% of table width
            setBallSize(radius);
        }
    }

    // show a notification bar with "Accept" or "Reject"
    const [notificationVisible, setNotificationVisible] = useState<boolean>(false);
    const [notificationMessage, setNotificationMessage] = useState<string>('');
    const handleAccept = () => {
        ws.current.send(JSON.stringify({ type: 'handshake' }));
        setNotificationVisible(false);
    };
    const handleReject = () => {
        ws.current.send(JSON.stringify({ type: 'reject' }));
        setNotificationVisible(false);
    };

    // switch between game and dashboard
    const [data, setData] = useState<any>(null);
    const [ingame, setIngame] = useState<boolean>(false)

    useEffect(() => {
        ws.current = new WebSocket(`ws://127.0.0.1:8000/ws/game_tournament/${type}/${username}`);
        ws.current.onopen = () => { console.log('WebSocket connection established'); };

        ws.current.onmessage = (event: any) => {
            const jsondata = JSON.parse(event.data);
            if (jsondata.type == 'disconnect') {
                console.log(jsondata)
            } if (jsondata.type == 'end') {
                console.log(jsondata)
                setIngame(false)
                setNotificationVisible(false);
                if (jsondata.status == 'im the winer')
                    return
                console.log('qualifyboard')
                ws.current.send(JSON.stringify({ type: 'qualifyboard' }));
                // if (jsondata.status == 'qualified') {
                // }
            } if (jsondata.type == 'opponents') {
                // handleResize()
                setNotificationMessage(`${jsondata.user1} vs ${jsondata.user2}`);
                setNotificationVisible(true);
                console.log(jsondata)
            } if (jsondata.type == 'ready') {
                ws.current.send(JSON.stringify({
                    type: 'start',
                }));
            } if (jsondata.type == 'dashboard') {
                setData(jsondata.rounds)
                console.log(jsondata.rounds[0])
            } if (jsondata.type == 'waiting') {
                console.log(jsondata)
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
                // console.log(jsondata)
                ball.current.style.top = `${jsondata.y}%`;
                ball.current.style.left = `${jsondata.x}%`;
            }
            if (jsondata.type == 'score') {
                rightScore.current.innerText = jsondata.right;
                leftScore.current.innerText = jsondata.left;
            }
            if (jsondata.type == 'paddle') {
                paddle.current.style.top = `${jsondata.pos}%`
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
            {notificationVisible && (
                <div className="notification-bar bg-blue-600 text-white p-4 rounded flex justify-between items-center">
                    <span>{notificationMessage}</span>
                    <div className="flex gap-2">
                        <button className="bg-green-500 p-2 rounded" onClick={handleAccept}>Accept</button>
                        <button className="bg-red-500 p-2 rounded" onClick={handleReject}>Reject</button>
                    </div>
                </div>
            )}
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