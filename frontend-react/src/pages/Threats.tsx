import { useEffect } from 'react';
import { useDefenseStore } from '../store/defenseStore';

export default function Threats() {
    const {
        events,
        detections,
        agents,
        fetchEvents,
        fetchDetections,
        fetchAgents,
        getThreatLevel,
        getActiveThreatsCount,
        getThreatStats
    } = useDefenseStore();

    useEffect(() => {
        // Initial fetch
        fetchEvents();
        fetchDetections();
        fetchAgents();

        // Poll for updates every 5 seconds
        const interval = setInterval(() => {
            fetchEvents();
            fetchDetections();
            fetchAgents();
        }, 5000);

        return () => clearInterval(interval);
    }, [fetchEvents, fetchDetections, fetchAgents]);

    const threatLevel = getThreatLevel();
    const activeThreats = getActiveThreatsCount();
    const threatStats = getThreatStats();

    // Calculate threat level color and animation
    const getThreatLevelColor = () => {
        switch (threatLevel) {
            case 'CRITICAL': return { bg: 'bg-red-500', text: 'text-red-400', border: 'border-red-500/20' };
            case 'HIGH': return { bg: 'bg-orange-500', text: 'text-orange-400', border: 'border-orange-500/20' };
            case 'MEDIUM': return { bg: 'bg-yellow-500', text: 'text-yellow-400', border: 'border-yellow-500/20' };
            default: return { bg: 'bg-emerald-500', text: 'text-emerald-400', border: 'border-emerald-500/20' };
        }
    };

    const colors = getThreatLevelColor();

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Threat Monitor</h1>
                    <p className="text-slate-400 mt-1">Real-time threat detection and analysis</p>
                </div>
                <div className="glass px-4 py-2 rounded-lg border border-cyan-500/20 text-cyan-400 text-sm font-mono">
                    {agents.length} Agents Active
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Threat Level Card */}
                <div className="glass-panel p-6 rounded-xl relative overflow-hidden group">
                    <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity`}>
                        <div className={`w-24 h-24 ${colors.bg} rounded-full blur-2xl`}></div>
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium mb-2">Current Threat Level</h3>
                    <div className={`text-4xl font-bold ${colors.text} font-mono`}>{threatLevel}</div>
                    <div className="mt-4 text-xs text-slate-500 font-mono">
                        Based on {detections.length} detection{detections.length !== 1 ? 's' : ''}
                    </div>
                </div>

                {/* Active Threats Card */}
                <div className="glass-panel p-6 rounded-xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <div className="w-24 h-24 bg-orange-500 rounded-full blur-2xl"></div>
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium mb-2">Active Threats</h3>
                    <div className="text-4xl font-bold text-orange-400 font-mono">{activeThreats}</div>
                    <div className="mt-4 text-xs text-slate-500 font-mono">
                        {threatStats.critical} critical, {threatStats.warning} warning
                    </div>
                </div>

                {/* Total Events Card */}
                <div className="glass-panel p-6 rounded-xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <div className="w-24 h-24 bg-cyan-500 rounded-full blur-2xl"></div>
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium mb-2">Scanner Events</h3>
                    <div className="text-4xl font-bold text-cyan-400 font-mono">{events.length}</div>
                    <div className="mt-4 text-xs text-slate-500 font-mono">
                        From active security scanners
                    </div>
                </div>
            </div>

            {/* Recent Threats List */}
            <div className="glass-panel rounded-xl p-6">
                <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                    Recent Detected Threats
                </h2>

                {detections.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="text-emerald-400 text-lg font-mono mb-2">All Clear</div>
                        <p className="text-slate-500 text-sm">No active threats detected</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {detections.slice(0, 10).map((detection) => {
                            const score = detection.ai_output?.score || 0;
                            const severity = score >= 0.7 ? 'Critical' : score >= 0.4 ? 'Warning' : 'Info';
                            const severityColor = score >= 0.7 ? 'red' : score >= 0.4 ? 'yellow' : 'blue';

                            return (
                                <div key={detection.id} className="glass-hover p-4 rounded-lg border border-white/5 flex items-center justify-between group">
                                    <div className="flex items-center gap-4">
                                        <div className={`p-2 rounded-lg bg-${severityColor}-500/10 text-${severityColor}-400 border border-${severityColor}-500/20`}>
                                            <span className="font-mono text-xs">{detection.category?.toUpperCase() || 'UNKNOWN'}</span>
                                        </div>
                                        <div>
                                            <h4 className="text-slate-200 font-medium">{detection.summary}</h4>
                                            <p className="text-xs text-slate-500 font-mono mt-1">Score: {score.toFixed(2)}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-slate-400 text-xs font-mono">
                                            {new Date(detection.created_at).toLocaleTimeString()}
                                        </div>
                                        <div className={`text-${severityColor}-400 text-xs mt-1`}>{severity}</div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
