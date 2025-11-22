import { useState, useEffect } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useDefenseStore } from '../store/defenseStore';

export default function Layout() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const { fetchEvents, fetchDetections, fetchModels } = useDefenseStore();

  useEffect(() => {
    fetchDetections();
    fetchEvents();
    fetchModels();
    const interval = setInterval(() => {
      fetchDetections();
      fetchEvents();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchDetections, fetchEvents, fetchModels]);

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/threats', label: 'Threat Monitor' },
    { path: '/events', label: 'Security Events' },
    { path: '/detections', label: 'Detections' },
    { path: '/analysis', label: 'AI Analysis' },
    { path: '/chat', label: 'Security Assistant' },
    { path: '/agents', label: 'Scanner Agents' },
    { path: '/ask', label: 'Ask AI' },
  ];

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black text-slate-200 font-sans selection:bg-cyan-500/30">
      {/* Mobile menu button */}
      <div className="lg:hidden glass sticky top-0 z-50 p-4 flex justify-between items-center border-b border-slate-800/50">
        <div className="flex items-center gap-2">
          <h1 className="text-white text-lg font-bold tracking-tight">AI Defense</h1>
        </div>
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="text-cyan-400 hover:text-cyan-300 font-mono text-sm border border-cyan-500/30 px-3 py-1 rounded bg-cyan-500/10 transition-colors"
        >
          {isMenuOpen ? 'CLOSE' : 'MENU'}
        </button>
      </div>

      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <div
          className={`
            fixed inset-y-0 left-0 z-40 w-64 glass border-r border-slate-800/50 
            transform transition-transform duration-300 ease-in-out 
            lg:translate-x-0 lg:static lg:inset-auto lg:block
            ${isMenuOpen ? 'translate-x-0' : '-translate-x-full'}
          `}
        >
          <div className="p-6 border-b border-slate-800/50 flex items-center gap-3">
            <div className="p-2 bg-cyan-500/10 rounded-lg border border-cyan-500/20">
              <div className="w-6 h-6 bg-cyan-500/20 rounded-sm"></div>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">AI Defense</h1>
              <div className="flex items-center gap-2">
                <p className="text-slate-500 text-xs font-mono">Security Monitor</p>
                <select
                  value={useDefenseStore(state => state.selectedModel)}
                  onChange={(e) => useDefenseStore.getState().setSelectedModel(e.target.value)}
                  className="bg-slate-900/50 border border-slate-800 text-xs text-slate-400 rounded px-1 py-0.5 focus:outline-none focus:border-cyan-500/50"
                >
                  {useDefenseStore(state => state.models).map(model => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <nav className="mt-6 px-3 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMenuOpen(false)}
                className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 ${isActive(item.path)
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
                  }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="absolute bottom-0 w-full p-4 border-t border-slate-800/50 bg-slate-900/30 backdrop-blur-sm">
            <div className="text-xs text-slate-500 font-mono">
              <div className="flex items-center gap-2">
                <span className="text-emerald-500">●</span>
                <span>System Online</span>
              </div>
              <div className="mt-1 opacity-50">
                Last update: {new Date().toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 overflow-auto relative w-full">
          {/* Background effects */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-cyan-500/5 rounded-full blur-3xl"></div>
            <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-violet-500/5 rounded-full blur-3xl"></div>
          </div>

          <main className="p-4 lg:p-8 relative z-10">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
