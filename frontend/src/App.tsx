import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './components/Login';
import Game from './components/Game';
import Game_boot from './components/Index';

const App: React.FC = () => {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/game/:username/:game_id" element={<Game />} />
                <Route path="/game-boot" element={<Game_boot />} />
            </Routes>
        </Router >
    );
};

export default App;

