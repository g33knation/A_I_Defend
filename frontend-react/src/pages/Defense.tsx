import { useEffect, useState } from 'react';
import {
    Shield,
    Ban,
    FileX,
    Skull,
    RefreshCw,
    Clock,
    ChevronDown,
    ChevronUp,
    RotateCcw,
    AlertTriangle,
    CheckCircle,
    Settings,
    Power,
    Activity
} from 'lucide-react';

import { useDefenseStore } from '../store/defenseStore';
import type { DefenseAction } from '../store/defenseStore';

// API_URL removed - using store BASE_URL

const ActionItem = ({ action, onRollback, formatTime }: {
    action: DefenseAction;
    onRollback: (id: number) => void;
    formatTime: (date: string) => string;
}) => {
    const [isExpanded, setIsExpanded] = useState(false);

    const getActionIcon = (type: string) => {
        switch (type) {
            case 'block_ip':
            case 'unblock_ip':
                return <Ban className="w-4 h-4" />;
            case 'quarantine_file':
            case 'restore_file':
                return <FileX className="w-4 h-4" />;
            case 'kill_process':
                return <Skull className="w-4 h-4" />;
            default:
                return <AlertTriangle className="w-4 h-4" />;
        }
    };

    const getStatusBadge = (status: string) => {
        const styles: Record<string, string> = {
            active: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
            pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
            assigned: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
            rolled_back: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
            failed: 'bg-red-500/20 text-red-400 border-red-500/30',
        };
        return styles[status] || styles.pending;
    };

    const getActionColor = (type: string) => {
        switch (type) {
            case 'block_ip':
                return 'text-red-400 bg-red-500/10';
            case 'unblock_ip':
                return 'text-emerald-400 bg-emerald-500/10';
            case 'quarantine_file':
                return 'text-orange-400 bg-orange-500/10';
            case 'restore_file':
                return 'text-blue-400 bg-blue-500/10';
            case 'kill_process':
                return 'text-purple-400 bg-purple-500/10';
            default:
                return 'text-slate-400 bg-slate-500/10';
        }
    };

    return (
        <div className="border-b border-slate-800/50 last:border-0">
            <div
                className="p-4 hover:bg-slate-800/30 transition-colors cursor-pointer group"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-start justify-between mb-1">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${getActionColor(action.action_type)}`}>
                            {getActionIcon(action.action_type)}
                        </div>
                        <div className="flex items-center gap-2">
                            {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                            <div>
                                <p className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">
                                    {action.action_type.replace(/_/g, ' ').toUpperCase()}
                                </p>
                                <p className="text-xs text-slate-400 font-mono mt-0.5">{action.target}</p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border uppercase tracking-wider ${getStatusBadge(action.status)}`}>
                            {action.status}
                        </span>
                        {action.status === 'active' && (action.action_type === 'block_ip' || action.action_type === 'quarantine_file') && (
                            <button
                                onClick={(e) => { e.stopPropagation(); onRollback(action.id); }}
                                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
                                title="Rollback this action"
                            >
                                <RotateCcw className="w-3.5 h-3.5" />
                            </button>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-500 pl-12">
                    <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(action.created_at)}
                    </div>
                    {action.executed_by && (
                        <span className="capitalize">by {action.executed_by}</span>
                    )}
                </div>
            </div>

            {isExpanded && (
                <div className="px-4 pb-4 pl-14 animate-in fade-in slide-in-from-top-1 duration-200">
                    <div className="bg-slate-950/50 rounded-lg p-3 border border-slate-800/50 text-xs space-y-2">
                        {action.reason && (
                            <div>
                                <span className="text-slate-500">Reason:</span>
                                <span className="text-slate-300 ml-2">{action.reason}</span>
                            </div>
                        )}
                        {action.detection_summary && (
                            <div>
                                <span className="text-slate-500">Detection:</span>
                                <span className="text-slate-300 ml-2">{action.detection_summary}</span>
                            </div>
                        )}
                        {action.rolled_back_at && (
                            <div>
                                <span className="text-slate-500">Rolled back:</span>
                                <span className="text-slate-300 ml-2">{formatTime(action.rolled_back_at)}</span>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

// ... (ActionItem interface and constants remain)

export default function Defense() {
    const {
        defenseActions: actions,
        defenseStats: stats,
        defenseConfig: config,
        fetchDefenseActions,
        fetchDefenseStats,
        fetchDefenseConfig,
        updateDefenseConfig,
        rollbackDefenseAction
    } = useDefenseStore();

    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');

    const rollbackAction = async (actionId: number) => {
        if (!confirm('Are you sure you want to rollback this action?')) return;
        await rollbackDefenseAction(actionId);
    };

    const toggleAutonomousDefense = async () => {
        const currentValue = config.autonomous_defense_enabled?.value;
        await updateDefenseConfig('autonomous_defense_enabled', !currentValue);
    };

    useEffect(() => {
        const loadAll = async () => {
            setLoading(true);
            await Promise.all([
                fetchDefenseActions(filter),
                fetchDefenseStats(),
                fetchDefenseConfig()
            ]);
            setLoading(false);
        };
        loadAll();

        const interval = setInterval(() => {
            fetchDefenseActions(filter);
            fetchDefenseStats();
        }, 10000);

        return () => clearInterval(interval);
    }, [filter, fetchDefenseActions, fetchDefenseStats, fetchDefenseConfig]);

    const formatTimeAgo = (dateString: string) => {
        if (!dateString) return 'Just now';
        const seconds = Math.floor((new Date().getTime() - new Date(dateString).getTime()) / 1000);
        if (seconds < 60) return 'Just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    };

    const isDefenseEnabled = config.autonomous_defense_enabled?.value === true ||
        config.autonomous_defense_enabled?.value === 'true';
    const threshold = config.severity_threshold?.value || '0.9';

    return (
        <div className="max-w-[1600px] mx-auto space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                        <Shield className="w-7 h-7 text-violet-500" />
                        Defense Center
                    </h1>
                    <p className="text-slate-400 text-sm">Autonomous defense actions and threat response</p>
                </div>
                <button
                    onClick={() => { fetchDefenseActions(filter); fetchDefenseStats(); fetchDefenseConfig(); }}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm font-medium border border-slate-700"
                >
                    <RefreshCw className="w-4 h-4" />
                    <span>Refresh</span>
                </button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Autonomous Defense Toggle */}
                <div className="glass p-4 rounded-xl relative overflow-hidden">
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${isDefenseEnabled ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-500/10 text-slate-400'}`}>
                                <Power className="w-5 h-5" />
                            </div>
                            <span className="text-slate-400 text-sm font-medium">Auto Defense</span>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className={`text-lg font-bold ${isDefenseEnabled ? 'text-emerald-400' : 'text-slate-500'}`}>
                            {isDefenseEnabled ? 'ENABLED' : 'DISABLED'}
                        </span>
                        <button
                            onClick={toggleAutonomousDefense}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${isDefenseEnabled
                                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'
                                }`}
                        >
                            {isDefenseEnabled ? 'Disable' : 'Enable'}
                        </button>
                    </div>
                </div>

                {/* Threshold */}
                <div className="glass p-4 rounded-xl relative overflow-hidden">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-violet-500/10 text-violet-400">
                            <Settings className="w-5 h-5" />
                        </div>
                        <span className="text-slate-400 text-sm font-medium">Threshold</span>
                    </div>
                    <p className="text-3xl font-bold text-white font-mono">{(parseFloat(threshold) * 100).toFixed(0)}%</p>
                    <p className="text-xs text-slate-500 mt-1">Minimum confidence for auto-action</p>
                </div>

                {/* Active Blocks */}
                <div className="glass p-4 rounded-xl relative overflow-hidden">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
                            <Ban className="w-5 h-5" />
                        </div>
                        <span className="text-slate-400 text-sm font-medium">Active Blocks</span>
                    </div>
                    <p className="text-3xl font-bold text-white font-mono">{stats?.active_ip_blocks || 0}</p>
                    <p className="text-xs text-slate-500 mt-1">IPs currently blocked</p>
                </div>

                {/* 24h Actions */}
                <div className="glass p-4 rounded-xl relative overflow-hidden">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                            <Activity className="w-5 h-5" />
                        </div>
                        <span className="text-slate-400 text-sm font-medium">24h Activity</span>
                    </div>
                    <p className="text-3xl font-bold text-white font-mono">{stats?.actions_last_24h || 0}</p>
                    <p className="text-xs text-slate-500 mt-1">Actions in last 24 hours</p>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2">
                {['all', 'active', 'pending', 'rolled_back'].map((f) => (
                    <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === f
                            ? 'bg-violet-500/20 text-violet-400 border border-violet-500/30'
                            : 'bg-slate-800/50 text-slate-400 hover:text-slate-300 border border-slate-700/50'
                            }`}
                    >
                        {f.replace('_', ' ').charAt(0).toUpperCase() + f.slice(1).replace('_', ' ')}
                    </button>
                ))}
            </div>

            {/* Actions List */}
            <div className="glass rounded-xl overflow-hidden border border-slate-800/50">
                <div className="p-4 border-b border-slate-800/50 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Shield className="w-5 h-5 text-violet-500" />
                        Defense Actions
                    </h2>
                    <span className="text-xs text-slate-500">{actions.length} actions</span>
                </div>

                {loading ? (
                    <div className="p-8 text-center text-slate-500">
                        <RefreshCw className="w-6 h-6 mx-auto mb-2 animate-spin" />
                        <p className="text-sm">Loading defense actions...</p>
                    </div>
                ) : actions.length === 0 ? (
                    <div className="p-8 text-center text-slate-500">
                        <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p className="text-sm">No defense actions recorded</p>
                        <p className="text-xs mt-1">Actions will appear here when threats are detected</p>
                    </div>
                ) : (
                    <div className="divide-y divide-slate-800/50">
                        {actions.map((action) => (
                            <ActionItem
                                key={action.id}
                                action={action}
                                onRollback={rollbackAction}
                                formatTime={formatTimeAgo}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
