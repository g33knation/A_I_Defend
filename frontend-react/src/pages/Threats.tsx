

export default function Threats() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Threat Monitor</h1>
                    <p className="text-slate-400 mt-1">Real-time threat detection and analysis</p>
                </div>
                <div className="glass px-4 py-2 rounded-lg border border-cyan-500/20 text-cyan-400 text-sm font-mono">
                    Live Monitoring Active
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Threat Level Card */}
                <div className="glass-panel p-6 rounded-xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <div className="w-24 h-24 bg-red-500 rounded-full blur-2xl"></div>
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium mb-2">Current Threat Level</h3>
                    <div className="text-4xl font-bold text-red-400 font-mono">HIGH</div>
                    <div className="mt-4 text-xs text-slate-500 font-mono">
                        Elevated activity detected in network sector 4
                    </div>
                </div>

                {/* Active Threats Card */}
                <div className="glass-panel p-6 rounded-xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <div className="w-24 h-24 bg-orange-500 rounded-full blur-2xl"></div>
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium mb-2">Active Threats</h3>
                    <div className="text-4xl font-bold text-orange-400 font-mono">12</div>
                    <div className="mt-4 text-xs text-slate-500 font-mono">
                        3 critical, 9 warning
                    </div>
                </div>

                {/* Blocked Attacks Card */}
                <div className="glass-panel p-6 rounded-xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <div className="w-24 h-24 bg-emerald-500 rounded-full blur-2xl"></div>
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium mb-2">Blocked Attacks</h3>
                    <div className="text-4xl font-bold text-emerald-400 font-mono">1,248</div>
                    <div className="mt-4 text-xs text-slate-500 font-mono">
                        Last 24 hours
                    </div>
                </div>
            </div>

            {/* Recent Threats List */}
            <div className="glass-panel rounded-xl p-6">
                <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                    Recent Detected Threats
                </h2>

                <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="glass-hover p-4 rounded-lg border border-white/5 flex items-center justify-between group">
                            <div className="flex items-center gap-4">
                                <div className="p-2 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20">
                                    <span className="font-mono text-xs">MALWARE</span>
                                </div>
                                <div>
                                    <h4 className="text-slate-200 font-medium">Suspicious Binary Execution</h4>
                                    <p className="text-xs text-slate-500 font-mono mt-1">Host: WORKSTATION-{i}0{i}</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-slate-400 text-xs font-mono">{new Date().toLocaleTimeString()}</div>
                                <div className="text-red-400 text-xs mt-1">Critical</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
