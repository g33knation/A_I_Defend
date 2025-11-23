import { useEffect, useState } from 'react';
import { useDefenseStore } from '../store/defenseStore';

export default function Agents() {
  const { agents, fetchAgents, deployScan } = useDefenseStore();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [targetInput, setTargetInput] = useState('');
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>([]);
  const [isDeploying, setIsDeploying] = useState(false);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, [fetchAgents]);

  const showNotification = (message: string, type: 'success' | 'error') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const [selectedPaths, setSelectedPaths] = useState<string[]>([]);

  const MALWARE_PATHS = [
    '/host_windows/Windows',
    '/host_windows/Users',
    '/host_windows/Program Files',
    '/host_wsl/usr/bin',
    '/host_wsl/etc',
    '/host_wsl/tmp'
  ];

  const handleDeployScan = async (agentId: string) => {
    const agent = agents.find(a => a.agent_id === agentId);
    const isFileScanner = agent ? (
      agent.hostname.includes('malware') ||
      agent.hostname.includes('security') ||
      agent.capabilities.includes('clamav') ||
      agent.capabilities.includes('rkhunter')
    ) : false;

    // DEBUG: Alert to see what's happening
    // alert(`Debug: FileScanner=${isFileScanner}, Paths=${selectedPaths.length}, Input=${targetInput}, Caps=${selectedCapabilities.length}`);
    console.log('Deploying scan:', { agentId, isFileScanner, selectedPaths, targetInput, selectedCapabilities });

    if (!isFileScanner && !targetInput) {
      showNotification('Please enter a target IP or Domain', 'error');
      return;
    }

    if (isFileScanner && selectedPaths.length === 0 && !targetInput) {
      showNotification('Please select a path or enter a custom one', 'error');
      return;
    }

    if (selectedCapabilities.length === 0) {
      showNotification('Please select at least one capability', 'error');
      return;
    }

    setIsDeploying(true);
    try {
      // For file scanners, combine selected paths and custom input
      let finalTarget = targetInput;
      let finalPaths = [...selectedPaths];

      if (agentId.includes('malware') || isFileScanner) {
        // If we have a custom input, add it to the paths list for the backend
        if (targetInput) {
          finalPaths.push(targetInput);
        }
      }

      // deployScan signature: (agentId, target, scanners, paths)
      await deployScan(agentId, finalTarget, selectedCapabilities, finalPaths);
      showNotification('Scan task deployed successfully', 'success');
      setTargetInput('');
      setSelectedPaths([]);
      setSelectedCapabilities([]);
      setSelectedAgent(null);
    } catch (error) {
      console.error('Failed to deploy scan:', error);
      // Show the actual error message in the notification
      showNotification(`Failed: ${error instanceof Error ? error.message : String(error)}`, 'error');
    } finally {
      setIsDeploying(false);
    }
  };

  const togglePath = (path: string) => {
    setSelectedPaths(prev =>
      prev.includes(path)
        ? prev.filter(p => p !== path)
        : [...prev, path]
    );
  };

  const toggleCapability = (cap: string) => {
    if (selectedCapabilities.includes(cap)) {
      setSelectedCapabilities(selectedCapabilities.filter(c => c !== cap));
    } else {
      setSelectedCapabilities([...selectedCapabilities, cap]);
    }
  };

  const getAgentDisplayName = (hostname: string) => {
    if (hostname.includes('network-intel')) return 'Network Intel';
    if (hostname.includes('malware')) return 'Malware Specialist';
    if (hostname.includes('security')) return 'Security Specialist';
    return hostname; // Fallback
  };

  return (
    <div className="space-y-6 relative">
      {notification && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-lg shadow-lg border animate-in fade-in slide-in-from-top-2 ${notification.type === 'success'
          ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
          : 'bg-red-500/10 border-red-500/20 text-red-400'
          }`}>
          {notification.message}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Scanner Agents</h1>
          <p className="text-slate-400 mt-1">Manage and monitor active security agents</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => fetchAgents()}
            className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition-colors border border-slate-700"
          >
            Refresh
          </button>
          <div className="px-3 py-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm font-mono flex items-center">
            v1.2 Host Access
          </div>
          <div className="glass px-4 py-2 rounded-lg border border-emerald-500/20 text-emerald-400 text-sm font-mono flex items-center">
            {agents.length} Online
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <div key={agent.agent_id} className="glass-panel p-6 rounded-xl group hover:border-cyan-500/30 transition-colors relative overflow-hidden">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 group-hover:bg-cyan-500/10 group-hover:border-cyan-500/20 transition-colors">
                <div className="w-6 h-6 bg-slate-400/20 rounded-full flex items-center justify-center text-xs font-mono">
                  {agent.hostname.substring(0, 2).toUpperCase()}
                </div>
              </div>
              <span className={`px-2 py-1 rounded text-xs font-mono border ${agent.status === 'scanning'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : agent.status === 'error'
                  ? 'bg-red-500/10 text-red-400 border-red-500/20'
                  : 'bg-slate-500/10 text-slate-400 border-slate-500/20'
                }`}>
                {agent.status}
              </span>
            </div>

            <h3 className="text-lg font-bold text-white mb-1">{getAgentDisplayName(agent.hostname)}</h3>
            <p className="text-sm text-slate-400 mb-4 font-mono">{agent.ip_address}</p>

            {/* Scan Progress Display */}
            {agent.status === 'scanning' && agent.metrics?.scan_progress && (
              <div className="mb-4 p-3 rounded-lg bg-cyan-500/5 border border-cyan-500/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-cyan-400">
                    {agent.metrics.scan_progress.current_scanner || 'Scanning...'}
                  </span>
                  <span className="text-xs text-cyan-300">
                    {agent.metrics.scan_progress.progress || 0}%
                  </span>
                </div>
                <div className="w-full bg-slate-800/50 rounded-full h-1.5 mb-2">
                  <div
                    className="bg-cyan-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${agent.metrics.scan_progress.progress || 0}%` }}
                  ></div>
                </div>
                {agent.metrics.scan_progress.scan_details && (
                  <div className="text-xs text-slate-400 space-y-1">
                    {agent.metrics.scan_progress.scan_details.targets && (
                      <div>Target: <span className="text-slate-300 font-mono">{agent.metrics.scan_progress.scan_details.targets?.join(', ')}</span></div>
                    )}
                    {agent.metrics.scan_progress.scan_details.target && (
                      <div>Target: <span className="text-slate-300 font-mono">{agent.metrics.scan_progress.scan_details.target}</span></div>
                    )}
                    <div className="flex gap-4">
                      <span>Results: <span className="text-emerald-400">{agent.metrics.scan_progress.results_count || 0}</span></span>
                      {agent.metrics.scan_progress.errors_count > 0 && (
                        <span>Errors: <span className="text-red-400">{agent.metrics.scan_progress.errors_count}</span></span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="space-y-2 mb-4">
              <div className="flex flex-wrap gap-2">
                {agent.capabilities.map((cap, i) => (
                  <span key={i} className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    {cap}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/50">
              {selectedAgent === agent.agent_id ? (
                <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
                  {/* Check if agent is file scanner (malware or security) based on hostname or capabilities */}
                  {(agent.hostname.includes('malware') || agent.hostname.includes('security') || agent.capabilities.includes('clamav') || agent.capabilities.includes('rkhunter')) && (
                    <div className="mb-3">
                      <label className="text-xs text-slate-400 mb-2 block">Select Scan Targets:</label>
                      <div className="grid grid-cols-2 gap-2 mb-3">
                        {MALWARE_PATHS.map(path => (
                          <label key={path} className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer hover:text-white bg-slate-800/30 p-2 rounded border border-slate-700/50 hover:border-cyan-500/30 transition-colors">
                            <input
                              type="checkbox"
                              checked={selectedPaths.includes(path)}
                              onChange={() => togglePath(path)}
                              className="rounded border-slate-700 bg-slate-900/50 text-cyan-500 focus:ring-offset-0 focus:ring-cyan-500/20"
                            />
                            <span className="font-mono">{path}</span>
                          </label>
                        ))}
                      </div>
                      <div className="text-xs text-slate-500 mb-1">Or enter custom path:</div>
                    </div>
                  )}

                  <input
                    type="text"
                    value={targetInput}
                    onChange={(e) => setTargetInput(e.target.value)}
                    placeholder={
                      (agent.hostname.includes('malware') || agent.hostname.includes('security') || agent.capabilities.includes('clamav') || agent.capabilities.includes('rkhunter'))
                        ? "Optional: Enter custom path (e.g. /opt/app)"
                        : "Enter Target IP or Domain"
                    }
                    className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors font-mono"
                  />
                  <div className="flex flex-wrap gap-2">
                    {agent.capabilities.map(cap => (
                      <label key={cap} className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer hover:text-white">
                        <input
                          type="checkbox"
                          checked={selectedCapabilities.includes(cap)}
                          onChange={() => toggleCapability(cap)}
                          className="rounded border-slate-700 bg-slate-900/50 text-cyan-500 focus:ring-offset-0 focus:ring-cyan-500/20"
                        />
                        <span>{cap}</span>
                      </label>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDeployScan(agent.agent_id)}
                      disabled={isDeploying ||
                        (((agent.hostname.includes('malware') || agent.hostname.includes('security') || agent.capabilities.includes('clamav') || agent.capabilities.includes('rkhunter'))
                          ? (!targetInput && selectedPaths.length === 0)
                          : !targetInput) || selectedCapabilities.length === 0)
                      }
                      className={`flex-1 text-xs py-2 rounded border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${((agent.hostname.includes('malware') || agent.hostname.includes('security') || agent.capabilities.includes('clamav') || agent.capabilities.includes('rkhunter'))
                        ? (!targetInput && selectedPaths.length === 0)
                        : !targetInput) || selectedCapabilities.length === 0
                        ? 'bg-slate-800 text-slate-500 border-slate-700 cursor-not-allowed'
                        : 'bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border-cyan-500/20'
                        }`}
                    >
                      {isDeploying ? 'Deploying...' : 'Confirm Scan'}
                    </button>
                    <button
                      onClick={() => setSelectedAgent(null)}
                      className="px-3 bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs py-2 rounded border border-slate-700 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex justify-between items-center">
                  <div className="text-xs font-mono">
                    {agent.last_scan_time ? (
                      <>
                        <span className="text-slate-500">Last Scan </span>
                        <span className="text-slate-300">{new Date(agent.last_scan_time).toLocaleTimeString()}</span>
                      </>
                    ) : (
                      <>
                        <span className="text-slate-500">Last Seen </span>
                        <span className="text-slate-300">{new Date(agent.last_heartbeat).toLocaleTimeString()}</span>
                      </>
                    )}
                  </div>
                  <button
                    onClick={() => {
                      setSelectedAgent(agent.agent_id);
                      // Auto-select all capabilities by default
                      setSelectedCapabilities(agent.capabilities);
                    }}
                    disabled={agent.status !== 'idle'}
                    className="text-xs bg-slate-800 hover:bg-slate-700 text-white px-3 py-1.5 rounded border border-slate-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Deploy Scan
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {agents.length === 0 && (
          <div className="col-span-full glass-panel p-12 rounded-xl text-center border border-dashed border-slate-700/50">
            <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-700">
              <div className="w-8 h-8 bg-slate-600 rounded-full animate-pulse"></div>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">No Agents Connected</h3>
            <p className="text-slate-400 max-w-md mx-auto mb-6">
              Deploy scanner agents to start monitoring your infrastructure.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
