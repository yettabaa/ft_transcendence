import React, { useEffect, useState, useRef } from 'react';
import { Link, useNavigate } from "react-router-dom";

const Login: React.FC = () => {
    const [name, setName] = useState('')
    const [id, setId] = useState('')
    const navigate = useNavigate();
    const handelrandom = () => {
        navigate(`/game/${name}/random`)
    }
    const handelButton = () => {
        navigate(`/game/${name}/${id}`)
    }
    const handeltournament = () => {
        navigate(`/game_tournament/8/${name}`)
    }
    return (
        <div className="flex flex-col gap-[2rem] justify-center items-center h-screen bg-bg">
            <input className='bg-slate-500' 
                onChange={(e) => setName(e.target.value)}
                placeholder='name'  
                />
            <input className='bg-slate-500' 
                onChange={(e) => setId(e.target.value)}
                placeholder='id'         
            />
            <button className=" bg-blue-500 w-[10rem] py-2 px-4 rounded"
            onClick={handelrandom}
            >
                random
            </button>
            <button className=" bg-blue-500 w-[10rem] py-2 px-4 rounded"
            onClick={handeltournament}
            >
                tournament
            </button>
            <button className=" bg-blue-500 w-[10rem] py-2 px-4 rounded"
            onClick={handelButton}
            >
                vs friend
            </button>
        </div>
    );
};

export default Login;
