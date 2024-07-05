import React, { useEffect, useRef, useState } from 'react';
import Button from '../../components/Button';
import Input from '../../components/Input';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import { Link, useNavigate } from "react-router-dom";

const websocket = () => {
    const [receiveData, setReceiveData]: any = useState([]);
    const [message, setMessage] = useState('')
    const navigate = useNavigate();

    useEffect(() => {
        const roomName = 'lobby';  // Change this to the desired room name
        const token = localStorage.getItem('token');
        const ws = new WebSocket(`ws://127.0.0.1:8000/ws/game/${roomName}/?token=${token}`);
        console.log('thread')

        // Handle incoming messages
        ws.onmessage = (event: any) => {
            let objects = JSON.parse(event.data);


            // console.log(typeof(objects), objects[0].fields.username)
            // const mapp = objects.map((obj: any)=> { return obj.fields.username})
            // console.log(mapp)
            setReceiveData(objects);
        };

        // Handle WebSocket open event
        ws.onopen = () => {
            console.log('WebSocket connection established');
        };

        // Handle WebSocket close event
        ws.onclose = (event: any) => {
            if (event.wasClean) {
                console.log(`Connection closed cleanly, code=${event.code} reason=${event.reason}`);
            } else {
                console.error('WebSocket connection died');
            }
        };

        // Handle WebSocket error event
        ws.onerror = (error: any) => {
            console.error(`WebSocket error: ${error.message}`);
        };

        // Cleanup WebSocket connection when component unmounts
        return () => { ws.close(); };
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login')
    };

    const handlelSend = (e: any) => {
        e.preventDefault()
        console.log(message)
    }

    return (
        <div className='bg-bg h-[100vh] flex flex-col justify-center items-center gap-5'>
            <h1 className='text'>Ping Pong Game</h1>

            {receiveData.map((object: any, Index: number) => {
                return (
                    <div key={Index} className='flex gap-5 justify-center'>
                        <div className='font-semibold text-2xl leading-9'>{object.fields.username} :</div>
                        <button className='bg-slate-500 rounded w-[100px]'> challange </button>
                    </div>
                );
            }
            )}
            <Input
                type='text'
                placeholder='message'
                onChange={(e) => setMessage(e.target.value)} />
            <Button onClick={handlelSend}>Send</Button>
            <Button onClick={handleLogout}>Logout</Button>
        </div>
        // <div className="bg-[#0C0D0F] w-full h-[100vh] px-10 flex justify-center items-center">
        //     <div
        //         className="relative overflow-hidden rounded-[10px] border-[1px] border-[#2b2d30]
        //     bg-red-700 h-[90%] min-w-[500px] w-full">
        //         <div
        //             className="absolute h-[2.5vh] w-[2.5vh] top-[0%] left-[0%] rounded-[50%] translate-x-[-50%] translate-y-[-50%] bg-white"
        //             style={{ left: `50%`, top: `50%` }}>
        //         </div>
        //         <div
        //             className="absolute  top-[50%] left-[1%] rounded-[1rem] 
        //         translate-y-[-50%] h-[20%] w-[2%] bg-white">
        //         </div>
        //         <div
        //             className="absolute top-[50%] right-[1%] rounded-[1rem]
        //         translate-y-[-50%] h-[20%] w-[2%] bg-white">
        //         </div>
        //     </div>
        // </div>
    );
}

export default websocket;