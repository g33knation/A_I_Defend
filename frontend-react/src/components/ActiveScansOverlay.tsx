import { useDefenseStore } from '../store/defenseStore';

export default function ActiveScansOverlay() {
    const { agents } = useDefenseStore();

    // Filter for agents that are currently scanning
    const scanningAgents = agents.filter(a => a.status === 'scanning');

    if (scanningAgents.length === 0) return null;

    const getAgentDisplayName = (hostname: string) => {
        if (hostname.includes('network-intel')) return 'Network Intel';
        if (hostname.includes('malware')) return 'Malware Specialist';
        if (hostname.includes('security')) return 'Security Specialist';
        return hostname;
    };

    return (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80 animate-in slide-in-from-right fade-in duration-300">
            {scanningAgents.map(agent => (
                <div key={agent.agent_id} className="bg-slate-900/90 backdrop-blur border border-cyan-500/30 rounded-lg p-3 shadow-lg shadow-cyan-900/20">
                    <div className="flex justify-between items-center mb-2">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></div>
                            <span className="text-xs font-bold text-white max-w-[150px] truncate" title={agent.hostname}>
                                {getAgentDisplayName(agent.hostname)}
                            </span>
                        </div>
                        <span className="text-[10px] font-mono text-cyan-400">
                            {agent.metrics?.scan_progress?.progress || 0}%
                        </span>
                    </div>

                    {agent.metrics?.scan_progress && (
                        <>
                            <div className="w-full bg-slate-800 rounded-full h-1 mb-2">
                                <div
                                    className="bg-cyan-500 h-1 rounded-full transition-all duration-500 ease-out"
                                    style={{ width: `${agent.metrics.scan_progress.progress || 0}%` }}
                                ></div>
                            </div>
                            <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                                <span className="truncate max-w-[120px]">
                                    {agent.metrics.scan_progress.current_scanner || 'Scanning...'}
                                </span>
                                {agent.metrics.scan_progress.scan_details?.targets && (
                                    <span className="truncate max-w-[100px]" title={agent.metrics.scan_progress.scan_details.targets.join(', ')}>
                                        {agent.metrics.scan_progress.scan_details.targets[0]}
                                        {agent.metrics.scan_progress.scan_details.targets.length > 1 ? ` +${agent.metrics.scan_progress.scan_details.targets.length - 1}` : ''}
                                    </span>
                                )}
                            </div>
                        </>
                    )}
                </div>
            ))}
        </div>
    );
}
