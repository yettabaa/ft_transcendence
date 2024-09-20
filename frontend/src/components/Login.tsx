import React, { useState } from 'react';
import axios from 'axios';
import Cookies from 'js-cookie';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const navigate = useNavigate();
    
    const handleLogin = async () => {
        try {
            const response = await axios.post('http://localhost:8000/api/login/', {
                type: "normal",
                data: {
                    identity: {
                        type: "username",
                        value: username,
                    },
                    password: password,
                },
                refer: "/game/101123542145",
            });

            if (response.status === 200) {
                const token = response.data.access_token; // Assuming token is returned in the response
                Cookies.set('auth_token', token, { expires: 7, sameSite: 'Lax' }); // Store token in cookies for 7 days
                console.log('token in login', token)
                localStorage.setItem('token',token)
                setErrorMessage(null);  // Clear error message if login is successful
                console.log('Login successful');
                navigate('/choices'); 
            }
        } catch (error:any) {
            if (error.response && error.response.data.error) {
                const { message } = error.response.data.error;
                setErrorMessage(message);
            } else {
                setErrorMessage('Login failed due to an unknown error.');
            }
        }
    };

    return (
        <div className="flex flex-col gap-[2rem] justify-center items-center h-screen bg-bg">
            <input 
                className="bg-slate-500 p-2 rounded text-white"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
            />
            <input 
                className="bg-slate-500 p-2 rounded text-white"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
            />
            <button 
                className="bg-blue-500 w-[10rem] py-2 px-4 rounded text-white"
                onClick={handleLogin}
            >
                Login
            </button>
            {errorMessage && (
                <div 
                    className="mt-4 p-2 rounded w-[20rem] text-center bg-red-500 text-white"
                >
                    {errorMessage}
                </div>
            )}
        </div>
    );
};

export default Login;
