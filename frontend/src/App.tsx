import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Choices from './components/Choices';
import Game from './components/Game';
import Game_boot from './components/Index';
import GameTournament from './components/GameTournament';
import Login from './components/Login';
import Signup from './components/Signup';
import Invitation from './components/Invitation'

const App: React.FC = () => {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
                <Route path="/Choices" element={<Choices />} />
                <Route path="/game/:game_id" element={<Invitation />} />
                <Route path="/game/random" element={<Game />} />
                <Route path="/game/:username/:game_id" element={<Game />} />
                <Route path="/game_tournament/:playersNum/:alias" element={<GameTournament />} />
                <Route path="/game-boot" element={<Game_boot />} />

            </Routes>
        </Router >
    );
};

export default App;

