import { useEffect } from 'react';
import { useDefenseStore } from '../store/defenseStore';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Server,
  Database,
  Clock,
  ChevronDown,
  ChevronUp,
  FileText
} from 'lucide-react';
import { useState } from 'react';

const DetectionItem = ({ detection, getBadgeClass, formatTime }: { detection: any, getBadgeClass: any, formatTime: any }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Parse ai_output if it's a string
  let details = detection.ai_output;
  if (typeof details === 'string') {
    try {
      details = JSON.parse(details);
    } catch (e) {
      // keep as string
    }
  }

  return (
    <div className="border-b border-slate-800/50 last:border-0">
      <div
        className="p-4 hover:bg-slate-800/30 transition-colors cursor-pointer group"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between mb-1">
          <div className="flex items-center gap-2">
            {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
            <p className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">
              {detection.summary || 'Suspicious activity detected'}
            </p>
          </div>
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border uppercase tracking-wider ${getBadgeClass(detection.type)}`}>
            {detection.type || 'unknown'}
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-500 pl-6">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatTime(detection.timestamp || detection.created_at)}
          </div>
          {detection.category && (
            <div className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              <span className="capitalize">{detection.category}</span>
            </div>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="px-4 pb-4 pl-10 animate-in fade-in slide-in-from-top-1 duration-200">
          <div className="bg-slate-950/50 rounded-lg p-3 border border-slate-800/50 text-xs font-mono text-slate-300 overflow-x-auto">
            <pre>{JSON.stringify(details, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

const EventItem = ({ event, formatTime }: { event: any, formatTime: any }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Parse payload if it's a string
  let details = event.payload;
  if (typeof details === 'string') {
    try {
      details = JSON.parse(details);
    } catch (e) {
      // keep as string
    }
  }

  return (
    <div className="border-b border-slate-800/50 last:border-0">
      <div
        className="p-4 hover:bg-slate-800/30 transition-colors cursor-pointer group"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between mb-1">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-full bg-slate-800 border border-slate-700 group-hover:border-slate-600 transition-colors mt-1">
              {event.type === 'threat_detected' ? (
                <AlertTriangle className="w-4 h-4 text-red-400" />
              ) : event.type === 'scan_completed' ? (
                <CheckCircle className="w-4 h-4 text-emerald-400" />
              ) : (
                <Database className="w-4 h-4 text-blue-400" />
              )}
            </div>
            <div className="flex items-center gap-2">
              {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
              <div>
                <p className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">
                  {event.type.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                </p>
                <p className="text-xs text-slate-400 font-mono mt-0.5">{event.source}</p>
              </div>
            </div>
          </div>
          <div className="flex items-center text-xs text-slate-500 font-mono">
            <Clock className="w-3 h-3 mr-1" />
            {formatTime(event.created_at)}
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="px-4 pb-4 pl-14 animate-in fade-in slide-in-from-top-1 duration-200">
          <div className="bg-slate-950/50 rounded-lg p-3 border border-slate-800/50 text-xs font-mono text-slate-300 overflow-x-auto">
            <pre>{JSON.stringify(details, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default function Dashboard() {
  const { stats, events, detections, agents, fetchEvents, fetchDetections, fetchAgents, purgeEvents } = useDefenseStore();

  useEffect(() => {
    fetchEvents();
    fetchDetections();
    fetchAgents();
    const interval = setInterval(() => {
      fetchEvents();
      fetchDetections();
      fetchAgents();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchEvents, fetchDetections, fetchAgents]);

  const recentDetections = detections.slice(0, 5);
  const recentEvents = events.slice(0, 5);

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

  const getDetectionBadgeClass = (type: string) => {
    const typeMap: Record<string, string> = {
      critical: 'bg-red-500/20 text-red-400 border-red-500/30',
      high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      info: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    };
    return typeMap[type?.toLowerCase()] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  return (
    <div className="max-w-[1600px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Security Dashboard</h1>
          <p className="text-slate-400 text-sm">Real-time system monitoring and threat analysis</p>
        </div>
        <button
          onClick={() => { fetchEvents(); fetchDetections(); fetchAgents(); }}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm font-medium border border-slate-700"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* System Status */}
      <div className="glass rounded-xl p-6 border border-slate-800/50">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Server className="w-5 h-5 text-violet-500" />
          System Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Static Infrastructure */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/30 border border-slate-800/30">
            <div className="flex items-center gap-3">
              <Server className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-medium text-slate-200">Control Plane</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]"></span>
              <span className="text-xs text-emerald-400 font-medium uppercase tracking-wider">Operational</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/30 border border-slate-800/30">
            <div className="flex items-center gap-3">
              <Database className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-medium text-slate-200">Database</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]"></span>
              <span className="text-xs text-emerald-400 font-medium uppercase tracking-wider">Operational</span>
            </div>
          </div>

          {/* Dynamic Agents */}
          {agents.map((agent) => {
            let displayName = agent.hostname;
            if (agent.hostname.includes('network-intel')) displayName = 'Network Intel';
            else if (agent.hostname.includes('malware')) displayName = 'Malware Specialist';
            else if (agent.hostname.includes('security')) displayName = 'Security Specialist';

            const isOnline = (new Date().getTime() - new Date(agent.last_heartbeat).getTime()) < 60000; // 1 min threshold
            const statusColor = agent.status === 'scanning' ? 'text-blue-400' : (agent.status === 'error' || !isOnline ? 'text-red-400' : 'text-emerald-400');
            const dotColor = agent.status === 'scanning' ? 'bg-blue-500' : (agent.status === 'error' || !isOnline ? 'bg-red-500' : 'bg-emerald-500');
            const statusText = !isOnline ? 'OFFLINE' : agent.status.toUpperCase();

            return (
              <div key={agent.agent_id} className="flex items-center justify-between p-3 rounded-lg bg-slate-950/30 border border-slate-800/30">
                <div className="flex items-center gap-3">
                  <Server className="w-4 h-4 text-slate-400" />
                  <span className="text-sm font-medium text-slate-200">{displayName}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${dotColor} shadow-[0_0_8px_rgba(var(--tw-shadow-color),0.4)]`}></span>
                  <span className={`text-xs ${statusColor} font-medium uppercase tracking-wider`}>{statusText}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass p-4 rounded-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Activity className="w-16 h-16 text-blue-500" />
          </div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                <Activity className="w-5 h-5" />
              </div>
              <span className="text-slate-400 text-sm font-medium">Total Events</span>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); if (confirm('Clear all events?')) purgeEvents(); }}
              className="text-xs text-slate-500 hover:text-red-400 transition-colors"
              title="Purge all events"
            >
              Purge
            </button>
          </div>
          <p className="text-3xl font-bold text-white font-mono">{stats.totalEvents || 0}</p>
        </div>

        <div className="glass p-4 rounded-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <AlertTriangle className="w-16 h-16 text-yellow-500" />
          </div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-yellow-500/10 text-yellow-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <span className="text-slate-400 text-sm font-medium">False Positives</span>
          </div>
          <p className="text-3xl font-bold text-white font-mono">{stats.falsePositives || 0}</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass rounded-xl overflow-hidden border border-slate-800/50">
          <div className="p-4 border-b border-slate-800/50 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              Recent Detections
            </h2>
          </div>
          <div className="divide-y divide-slate-800/50">
            {recentDetections.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                <p className="text-sm">No recent detections found</p>
              </div>
            ) : (
              recentDetections.map((detection) => (
                <DetectionItem key={detection.id} detection={detection} getBadgeClass={getDetectionBadgeClass} formatTime={formatTimeAgo} />
              ))
            )}
          </div>
        </div>

        <div className="glass rounded-xl overflow-hidden border border-slate-800/50">
          <div className="p-4 border-b border-slate-800/50 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              Recent Events
            </h2>
          </div>
          <div className="divide-y divide-slate-800/50">
            {recentEvents.length === 0 ? (
              <div className="text-center py-12 text-slate-50">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p>No recent activity recorded</p>
              </div>
            ) : (
              recentEvents.map((event) => (
                <EventItem key={event.id} event={event} formatTime={formatTimeAgo} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

