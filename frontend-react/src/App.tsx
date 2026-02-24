import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Events from './pages/Events';
import Detections from './pages/Detections';
import Agents from './pages/Agents';
import AskAI from './pages/AskAI';
import Threats from './pages/Threats';
import Analysis from './pages/Analysis';
import Chat from './pages/Chat';
import Defense from './pages/Defense';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="threats" element={<Threats />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="chat" element={<Chat />} />
          <Route path="events" element={<Events />} />
          <Route path="detections" element={<Detections />} />
          <Route path="agents" element={<Agents />} />
          <Route path="defense" element={<Defense />} />
          <Route path="ask" element={<AskAI />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
