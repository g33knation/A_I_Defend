import { useEffect, useState } from 'react';
import { useDefenseStore } from '../store/defenseStore';

interface ScanProgressBubbleProps {
    assignmentId: string;
    target: string;
    scanner: string;
    onComplete: (scanId: string) => void;
}

export default function ScanProgressBubble({ assignmentId, target, scanner, onComplete }: ScanProgressBubbleProps) {
    const { agents } = useDefenseStore();
    const [status, setStatus] = useState<'pending' | 'scanning' | 'completed' | 'failed'>('pending');
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        // Find the agent working on this assignment
        const agent = agents.find(a => a.current_assignment === assignmentId);

        if (agent) {
            // Case 1: Agent is actively working on it
            if (agent.status === 'scanning') {
                setStatus('scanning');
                setProgress(agent.metrics?.scan_progress?.progress || 0);
            }
            // Case 2: Agent reports idle but still has the assignment ID (rare race condition or transition)
            else if (agent.status === 'idle' && status === 'scanning') {
                setStatus('completed');
                setProgress(100);
                setTimeout(() => onComplete(assignmentId), 1000);
            }
        } else {
            // Case 3: Assignment disappeared! 
            // This usually means the agent finished efficiently and the backend cleared the state.
            // If we were "scanning" or "pending" and now it's gone, assume success.
            if (status === 'scanning' || status === 'pending') {
                // Determine if we should treat this as success or failure?
                // For now, assume success if it disappears. A failure typically leaves logs or error state, 
                // but our current backend wipes assignment on idle regardless of result.

                // Only trigger if we haven't already completed
                setStatus('completed');
                setProgress(100);
                setTimeout(() => onComplete(assignmentId), 1000);
            }
        }
    }, [agents, assignmentId, status, onComplete]);

    return (
        <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-4 w-full max-w-md my-2">
            <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-3">
                    {status === 'scanning' ? (
                        <div className="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
                            <div className="w-4 h-4 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin"></div>
                        </div>
                    ) : status === 'completed' ? (
                        <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                            <div className="text-emerald-500">✓</div>
                        </div>
                    ) : (
                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center">
                            <div className="w-2 h-2 rounded-full bg-slate-500"></div>
                        </div>
                    )}
                    <div>
                        <div className="text-sm font-bold text-white">Running {scanner} Scan</div>
                        <div className="text-xs text-slate-400 font-mono">{target}</div>
                    </div>
                </div>
                <div className="text-xs font-mono text-cyan-400">
                    {status === 'completed' ? 'DONE' : `${progress}%`}
                </div>
            </div>

            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                    className={`h-full transition-all duration-500 ease-out ${status === 'completed' ? 'bg-emerald-500' : 'bg-cyan-500'
                        }`}
                    style={{ width: `${progress}%` }}
                ></div>
            </div>

            <div className="mt-2 flex justify-between text-[10px] text-slate-500 font-mono">
                <span>ID: {assignmentId.slice(0, 8)}...</span>
                <span>{status.toUpperCase()}</span>
            </div>
        </div>
    );
}
