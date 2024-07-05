import React, { useEffect, useRef, useState } from 'react';
import Button from '../../components/Button';
import Input from '../../components/Input';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import { Link, useNavigate } from "react-router-dom";
import { LoopHook } from './LoopHook';

const websocket = () => {
    const [receiveData, setReceiveData]: any = useState([]);
    const ws: any = useRef();
    const ball: any = useRef();
    
    const roomName = 'lobby';  // Change this to the desired room name
    ws.current = new WebSocket(`ws://127.0.0.1:8000/ws/game-online/${roomName}/`);
    useEffect(() => {

        ws.current.onmessage = (event: any) => {
            // let objects = JSON.parse(event.data);
            // setReceiveData(objects);
        };
        ws.current.onopen = () => {console.log('WebSocket connection established');};
        ws.current.onclose = (event: any) => {
            if (event.wasClean) {
                console.log(`Connection closed cleanly, code=${event.code} reason=${event.reason}`);
            } else {
                console.error('WebSocket connection died');
            }
        };
        ws.current.onerror = (error: any) => {
            console.error(`WebSocket error: ${error.message}`);
        };
        return () => { ws.current.close(); };
    }, []);
    
    LoopHook((delta: number) => {
        // ws.current.send(delta);
        console.log(delta)
    })

    return (
        <div className="bg-[#0C0D0F] w-full h-[100vh] px-10 flex justify-center items-center">
            <div
                className="relative overflow-hidden rounded-[10px] border-[1px] border-[#2b2d30]
            bg-red-700 h-[90%] min-w-[500px] w-full">
                <div ref={ball}
                    className="absolute h-[2.5vh] w-[2.5vh] top-[0%] left-[0%] rounded-[50%] translate-x-[-50%] translate-y-[-50%] bg-white"
                    style={{ left: `50%`, top: `50%` }}>
                </div>
                <div
                    className="absolute  top-[50%] left-[1%] rounded-[1rem] 
                translate-y-[-50%] h-[20%] w-[2%] bg-white">
                </div>
                <div
                    className="absolute top-[50%] right-[1%] rounded-[1rem]
                translate-y-[-50%] h-[20%] w-[2%] bg-white">
                </div>
            </div>
        </div>
    );
}

export default websocket;