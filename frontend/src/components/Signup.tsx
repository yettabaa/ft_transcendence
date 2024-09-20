import React, { useState } from 'react';
import axios from 'axios';

const Signup: React.FC = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [retypePassword, setRetypePassword] = useState('');
    const [message, setMessage] = useState<{ type: string, text: string } | null>(null);

    const handleSignup = async () => {
        try {
            const response = await axios.post('http://localhost:8000/api/register/', {
                type: "normal",
                data: {
                    username: username,
                    email: email,
                    password: password,
                    retype_password: retypePassword,
                },
            });

            if (response.status === 201) {
                setMessage({ type: 'success', text: 'User registered successfully' });
            }
        } catch (error) {
            if (error.response && error.response.data.error) {
                const { message } = error.response.data.error;
                const errorMsg = `Username: ${message.username || ''} Email: ${message.email || ''}`;
                setMessage({ type: 'error', text: errorMsg.trim() });
            } else {
                setMessage({ type: 'error', text: 'Signup failed due to an unknown error.' });
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
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
            />
            <input 
                className="bg-slate-500 p-2 rounded text-white"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
            />
            <input 
                className="bg-slate-500 p-2 rounded text-white"
                type="password"
                value={retypePassword}
                onChange={(e) => setRetypePassword(e.target.value)}
                placeholder="Retype Password"
            />
            <button 
                className="bg-blue-500 w-[10rem] py-2 px-4 rounded text-white"
                onClick={handleSignup}
            >
                Signup
            </button>
            {message && (
                <div 
                    className={`mt-4 p-2 rounded w-[20rem] text-center ${message.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`}
                >
                    {message.text}
                </div>
            )}
        </div>
    );
};

export default Signup;
