<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';

const agents = ref([]);
const isLoading = ref(false);
const error = ref(null);
const selectedAgent = ref(null);
const showAssignModal = ref(false);

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Assignment form
const assignmentForm = ref({
  targets: '',
  scanners: ['nmap'],
  ports: '1-65535',
  priority: 5,
  remoteHost: '',  // For malware/security agents: user@host
  paths: '/tmp'     // For malware/security agents: paths to scan
});

const allScannerOptions = [
  { value: 'nmap', label: 'Nmap (Port Scanner)', type: 'network' },
  { value: 'suricata', label: 'Suricata (IDS/IPS)', type: 'network' },
  { value: 'tshark', label: 'Tshark (Packet Capture)', type: 'network_intel' },
  { value: 'masscan', label: 'Masscan (Fast Port Scanner)', type: 'network_intel' },
  { value: 'arp-scan', label: 'ARP Scan (Host Discovery)', type: 'network_intel' },
  { value: 'dns-enum', label: 'DNS Enumeration', type: 'network_intel' },
  { value: 'ping-sweep', label: 'Ping Sweep (Live Hosts)', type: 'network_intel' },
  { value: 'clamav', label: 'ClamAV (Antivirus)', type: 'malware' },
  { value: 'yara', label: 'YARA (Pattern Matching)', type: 'malware' },
  { value: 'lynis', label: 'Lynis (Security Audit)', type: 'security' },
  { value: 'chkrootkit', label: 'chkrootkit (Rootkit Detection)', type: 'security' },
  { value: 'rkhunter', label: 'rkhunter (Rootkit Hunter)', type: 'security' }
];

const availableScanners = computed(() => {
  if (!selectedAgent.value) return [];
  
  // Filter scanners based on agent's capabilities
  return allScannerOptions.filter(scanner => 
    selectedAgent.value.capabilities.includes(scanner.value)
  );
});

const getAgentBadge = (agent) => {
  const name = agent.hostname?.toLowerCase() || '';
  if (name.includes('network-intel') || name.includes('network_intel')) {
    return {
      label: 'Network Intel',
      classes: 'border-cyan-400/40 bg-cyan-500/15 text-cyan-100'
    };
  }
  if (name.includes('network')) {
    return {
      label: 'Network',
      classes: 'border-blue-400/40 bg-blue-500/15 text-blue-100'
    };
  }
  if (name.includes('malware')) {
    return {
      label: 'Malware',
      classes: 'border-rose-400/40 bg-rose-500/15 text-rose-100'
    };
  }
  if (name.includes('security')) {
    return {
      label: 'Security',
      classes: 'border-purple-400/40 bg-purple-500/15 text-purple-100'
    };
  }
  return {
    label: 'Agent',
    classes: 'border-slate-500/40 bg-slate-600/20 text-slate-100'
  };
};

const getAgentAccent = (agent) => {
  const name = agent.hostname?.toLowerCase() || '';
  if (name.includes('network-intel') || name.includes('network_intel')) {
    return 'from-cyan-500/80 via-blue-500/70 to-purple-500/70';
  }
  if (name.includes('network')) {
    return 'from-blue-500/80 via-indigo-500/70 to-cyan-500/70';
  }
  if (name.includes('malware')) {
    return 'from-rose-500/80 via-orange-500/70 to-amber-500/70';
  }
  if (name.includes('security')) {
    return 'from-purple-500/80 via-fuchsia-500/70 to-indigo-500/70';
  }
  return 'from-slate-600/80 via-slate-500/70 to-slate-700/70';
};

const fetchAgents = async () => {
  try {
    isLoading.value = true;
    const response = await fetch(`${API_BASE}/api/agents/`);
    const allAgents = await response.json();
    
    // Filter out stale agents (no heartbeat in last 5 minutes)
    const now = new Date();
    const staleThreshold = 5 * 60 * 1000; // 5 minutes in milliseconds
    
    agents.value = allAgents.filter(agent => {
      const lastHeartbeat = new Date(agent.last_heartbeat);
      const timeSinceHeartbeat = now - lastHeartbeat;
      return timeSinceHeartbeat < staleThreshold;
    });
  } catch (err) {
    error.value = err.message;
    console.error('Error fetching agents:', err);
  } finally {
    isLoading.value = false;
  }
};

const assignScan = async () => {
  if (!selectedAgent.value) return;
  
  try {
    const isNetworkAgent = selectedAgent.value.capabilities.includes('nmap');
    const config = {};
    
    if (isNetworkAgent) {
      // Network agent configuration
      const targets = assignmentForm.value.targets.split(',').map(t => t.trim());
      
      // Configure each selected network scanner
      if (assignmentForm.value.scanners.includes('nmap')) {
        config.nmap = {
          targets: targets,
          ports: assignmentForm.value.ports
        };
      }
      
      if (assignmentForm.value.scanners.includes('masscan')) {
        config.masscan = {
          targets: targets,
          ports: assignmentForm.value.ports
        };
      }
      
      if (assignmentForm.value.scanners.includes('ping-sweep')) {
        config.ping_sweep = {
          network: targets[0] // Use first target as network
        };
      }
      
      if (assignmentForm.value.scanners.includes('arp-scan')) {
        config.arp_scan = {
          interface: 'eth0'
        };
      }
      
      if (assignmentForm.value.scanners.includes('tshark')) {
        config.tshark = {
          interface: 'eth0',
          duration: 30
        };
      }
      
      if (assignmentForm.value.scanners.includes('dns-enum')) {
        config.dns_enum = {
          domains: targets
        };
      }
    } else {
      // Malware/Security agent configuration
      const paths = assignmentForm.value.paths.split(',').map(p => p.trim());
      
      if (assignmentForm.value.remoteHost) {
        config.remote_host = assignmentForm.value.remoteHost;
      }
      
      if (selectedAgent.value.capabilities.includes('clamav')) {
        config.clamav = { paths: paths };
      }
      if (selectedAgent.value.capabilities.includes('yara')) {
        config.yara = { paths: paths };
      }
    }
    
    const response = await fetch(`${API_BASE}/api/agents/${selectedAgent.value.agent_id}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        targets: isNetworkAgent ? assignmentForm.value.targets.split(',').map(t => t.trim()) : [],
        scanners: assignmentForm.value.scanners,
        config: config,
        priority: assignmentForm.value.priority
      })
    });
    
    if (response.ok) {
      showAssignModal.value = false;
      await fetchAgents();
      showToast('Scan assigned successfully');
    } else {
      const data = await response.json();
      showToast(`Failed to assign scan: ${data.detail}`, 'error');
    }
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
};

const openAssignModal = (agent) => {
  selectedAgent.value = agent;
  // Pre-select all available scanners for this agent
  assignmentForm.value.scanners = agent.capabilities;
  // Set default targets based on agent type
  if (agent.capabilities.includes('nmap')) {
    assignmentForm.value.targets = '127.0.0.1';
    assignmentForm.value.ports = '1-65535';
  } else {
    assignmentForm.value.targets = '/tmp';
  }
  showAssignModal.value = true;
};

const getStatusColor = (status) => {
  const colors = {
    'idle': 'bg-emerald-500/15 text-emerald-200 border-emerald-400/30',
    'scanning': 'bg-blue-500/20 text-blue-100 border-blue-400/40',
    'error': 'bg-red-500/20 text-red-100 border-red-400/40',
    'offline': 'bg-slate-700 text-slate-300 border-slate-600'
  };
  return colors[status] || colors.offline;
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
};

const getTimeSinceHeartbeat = (lastHeartbeat) => {
  const seconds = Math.floor((new Date() - new Date(lastHeartbeat)) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
};

const toast = ref({
  message: '',
  type: 'info',
  visible: false
});

const showToast = (message, type = 'info') => {
  toast.value = { message, type, visible: true };
  setTimeout(() => {
    toast.value.visible = false;
  }, 4000);
};

// Auto-refresh every 10 seconds
let refreshInterval;
onMounted(() => {
  fetchAgents();
  refreshInterval = setInterval(fetchAgents, 10000);
});

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval);
});
</script>

<template>
  <div class="relative min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
    <!-- Animated Background Gradient Orbs -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -left-40 w-[600px] h-[600px] bg-gradient-to-br from-blue-600/30 via-cyan-500/20 to-transparent blur-3xl rounded-full animate-pulse" style="animation-duration: 8s;"></div>
      <div class="absolute top-1/4 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-purple-600/25 via-fuchsia-500/15 to-transparent blur-3xl rounded-full" style="animation: float 15s ease-in-out infinite;"></div>
      <div class="absolute bottom-0 left-1/3 w-[400px] h-[400px] bg-gradient-to-br from-cyan-500/20 via-blue-500/15 to-transparent blur-3xl rounded-full" style="animation: float 12s ease-in-out infinite reverse;"></div>
    </div>

    <!-- Grid Pattern Overlay -->
    <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-40 pointer-events-none"></div>

    <div class="relative px-4 py-6 lg:px-8 mx-auto max-w-[1600px]">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 mb-8">
        <div class="space-y-4 max-w-2xl">
          <div class="inline-flex items-center gap-2.5 text-xs font-semibold px-4 py-2 rounded-full bg-gradient-to-r from-blue-500/20 via-cyan-500/20 to-blue-500/20 text-blue-100 border border-blue-400/30 shadow-lg shadow-blue-500/20">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-blue-300"></span>
            </span>
            LIVE CONTROL PLANE
          </div>
          <h1 class="text-3xl lg:text-4xl font-black tracking-tight bg-gradient-to-br from-slate-50 via-slate-100 to-slate-300 bg-clip-text text-transparent drop-shadow-2xl">
            Scanner Agents
          </h1>
          <p class="text-sm text-slate-300 leading-relaxed font-medium">
            Real-time monitoring and orchestration for your defensive sensors. Monitor heartbeats, assign scans, and track progress across your security infrastructure.
          </p>
          <div class="flex flex-wrap items-center gap-5 text-sm font-semibold">
            <div class="flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-400/20">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-lg shadow-emerald-400/50"></span>
              <span class="text-emerald-300">{{ agents.filter(agent => agent.status === 'idle').length }} Idle</span>
            </div>
            <div class="flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-400/20">
              <span class="relative flex h-2.5 w-2.5">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-400 shadow-lg shadow-blue-400/50"></span>
              </span>
              <span class="text-blue-300">{{ agents.filter(agent => agent.status === 'scanning').length }} Scanning</span>
            </div>
            <div class="flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-400/20">
              <span class="w-2.5 h-2.5 rounded-full bg-red-400 shadow-lg shadow-red-400/50 animate-pulse"></span>
              <span class="text-red-300">{{ agents.filter(agent => agent.status === 'error').length }} Issues</span>
            </div>
          </div>
        </div>
        <div class="self-start lg:self-auto flex items-center gap-3">
          <button
            @click="fetchAgents"
            class="group inline-flex items-center gap-2.5 px-5 py-2.5 text-sm font-semibold rounded-xl bg-gradient-to-r from-slate-800/80 to-slate-800/60 backdrop-blur-xl border border-white/10 hover:border-white/30 hover:from-slate-700/80 hover:to-slate-700/60 transition-all duration-300 shadow-lg hover:shadow-xl hover:shadow-blue-500/10"
          >
            <svg class="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582M20 20v-5h-.581m-3.217-5a6 6 0 10-8.246 6.586M6.227 15A6 6 0 0014 20.917" />
            </svg>
            <span class="bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent">Refresh</span>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div class="col-span-2 md:col-span-3">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <div class="group relative overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br from-white/10 via-white/5 to-transparent backdrop-blur-xl p-4 hover:border-white/20 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10">
              <div class="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div class="relative">
                <div class="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Total Agents</div>
                <div class="mt-2 flex items-baseline gap-2">
                  <span class="text-2xl font-black bg-gradient-to-br from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">{{ agents.length }}</span>
                  <span class="text-[10px] font-bold uppercase tracking-wide text-emerald-400">online</span>
                </div>
              </div>
            </div>
            <div class="group relative overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br from-white/10 via-white/5 to-transparent backdrop-blur-xl p-4 hover:border-white/20 transition-all duration-300 hover:shadow-xl hover:shadow-cyan-500/10">
              <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/10 via-transparent to-blue-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div class="relative">
                <div class="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Heartbeat</div>
                <div class="mt-2 text-lg font-bold text-white">
                  {{ agents.length ? getTimeSinceHeartbeat(agents[0].last_heartbeat) : '—' }}
                </div>
                <div class="mt-1 text-[11px] font-semibold text-cyan-400">Auto-refresh: 10s</div>
              </div>
            </div>
            <div class="group relative overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br from-white/10 via-white/5 to-transparent backdrop-blur-xl p-4 hover:border-white/20 transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/10">
              <div class="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-transparent to-fuchsia-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div class="relative">
                <div class="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Status</div>
                <div class="mt-2 text-lg font-bold text-white">
                  {{ agents.some(agent => agent.status === 'scanning') ? 'Active' : 'Idle' }}
                </div>
                <div class="mt-1 text-[11px] font-semibold text-purple-400">Assignment queue</div>
              </div>
            </div>
          </div>
        </div>
        <div class="relative overflow-hidden rounded-xl border border-blue-400/30 bg-gradient-to-br from-blue-500/15 via-cyan-500/10 to-blue-500/15 backdrop-blur-xl p-4 shadow-lg shadow-blue-500/20">
          <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImRvdHMiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjEiIGZpbGw9InJnYmEoMTQ3LCAE5NywgMjU1LCAwLjMpIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2RvdHMpIi8+PC9zdmc+')] opacity-50"></div>
          <div class="relative">
            <div class="flex items-center gap-2 text-xs font-semibold text-blue-100">
              <div class="flex items-center justify-center w-6 h-6 rounded-full bg-blue-400/20 border border-blue-400/30">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span>Health Monitoring</span>
            </div>
            <p class="mt-3 text-xs text-blue-50/90 leading-relaxed font-medium">
              Agents send heartbeats every <span class="font-bold text-blue-200">30 seconds</span>. Missing 2+ cycles triggers alerts for investigation.
            </p>
          </div>
        </div>
      </div>

      <div v-if="agents.length" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-2">
        <article
          v-for="agent in agents"
          :key="agent.agent_id"
          class="group relative overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br from-white/8 via-white/4 to-transparent backdrop-blur-xl hover:border-white/20 transition-all duration-300 hover:shadow-lg"
        >
          <!-- Animated Gradient Background -->
          <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700">
            <div :class="['absolute inset-0 bg-gradient-to-br blur-3xl opacity-30', getAgentAccent(agent)]"></div>
          </div>
          
          <!-- Shimmer Effect -->
          <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
          </div>

          <div class="relative p-2 space-y-1.5">
            <div class="flex items-start justify-between gap-1.5">
              <div class="flex-1 min-w-0">
                <h3 class="text-[10px] font-bold text-white truncate">
                  {{ agent.hostname }}
                </h3>
                <p class="text-[8px] font-medium text-slate-400">{{ agent.ip_address }}</p>
              </div>
              <span
                :class="['inline-flex items-center gap-0.5 px-1 py-0.5 text-[8px] font-bold rounded border transition-all duration-300 shadow-sm', getStatusColor(agent.status)]"
              >
                <span
                  :class="[
                    'relative flex h-1 w-1',
                    agent.status === 'scanning' ? 'animate-pulse' : ''
                  ]"
                >
                  <span
                    v-if="agent.status === 'scanning'"
                    class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"
                  ></span>
                  <span
                    :class="[
                      'relative inline-flex rounded-full h-1 w-1',
                      agent.status === 'scanning' ? 'bg-blue-400 shadow-md shadow-blue-400/50' : '',
                      agent.status === 'idle' ? 'bg-emerald-400 shadow-md shadow-emerald-400/50' : '',
                      agent.status === 'error' ? 'bg-red-400 shadow-md shadow-red-400/50' : '',
                      agent.status === 'offline' ? 'bg-slate-400' : ''
                    ]"
                  ></span>
                </span>
                {{ agent.status }}
              </span>
            </div>

            <div class="flex flex-wrap items-center gap-0.5 text-xs">
              <span
                :class="['inline-flex items-center gap-0.5 px-1 py-0.5 rounded-full border text-[8px] font-bold uppercase tracking-wide shadow-sm', getAgentBadge(agent).classes]"
              >
                {{ getAgentBadge(agent).label }}
              </span>
              <span class="inline-flex items-center gap-0.5 px-1 py-0.5 rounded-full border border-white/10 bg-white/5 text-slate-200 text-[8px] font-semibold shadow-sm">
                <svg class="w-1.5 h-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                {{ agent.capabilities.length }}
              </span>
            </div>

            <div class="space-y-0.5 text-xs">
              <div class="flex items-center justify-between p-1 rounded bg-white/5 border border-white/5">
                <span class="text-slate-400 text-[8px] font-semibold">ID</span>
                <span class="font-mono text-[8px] font-bold text-slate-200">{{ agent.agent_id.substring(0, 6) }}…</span>
              </div>
              <div class="flex items-center justify-between p-1 rounded bg-white/5 border border-white/5">
                <span class="text-slate-400 text-[8px] font-semibold">Heartbeat</span>
                <span class="text-[8px] font-bold text-emerald-300">{{ getTimeSinceHeartbeat(agent.last_heartbeat) }}</span>
              </div>
              <div class="flex items-center justify-between p-1 rounded bg-white/5 border border-white/5">
                <span class="text-slate-400 text-[8px] font-semibold">Task</span>
                <span class="font-mono text-[8px] font-bold text-slate-200">
                  {{ agent.current_assignment ? `${agent.current_assignment.substring(0, 8)}…` : '—' }}
                </span>
              </div>
            </div>

            <!-- Scan Progress Details -->
            <div v-if="agent.status === 'scanning' && agent.metrics?.scan_progress" class="relative overflow-hidden space-y-2.5 rounded-xl border border-blue-400/40 bg-gradient-to-br from-blue-500/20 via-cyan-500/15 to-blue-500/20 p-3 shadow-lg shadow-blue-500/20">
              <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjAuNSIgZmlsbD0icmdiYSgxNDcsIDE5NywgMjU1LCAwLjMpIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-30"></div>
              
              <div class="relative flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-400/30 border border-blue-400/50">
                    <svg class="w-2.5 h-2.5 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <span class="text-[10px] font-black text-blue-50 uppercase tracking-wide">Active Scan</span>
                </div>
                <span class="text-lg font-black bg-gradient-to-br from-blue-100 to-cyan-200 bg-clip-text text-transparent">{{ agent.metrics.scan_progress.progress || 0 }}%</span>
              </div>
              
              <!-- Enhanced Progress Bar -->
              <div class="relative h-2 overflow-hidden rounded-full bg-blue-950/40 border border-blue-400/20 shadow-inner">
                <div 
                  class="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-500 via-cyan-400 to-blue-500 transition-all duration-700 ease-out shadow-lg shadow-blue-500/50"
                  :style="{ width: `${agent.metrics.scan_progress.progress || 0}%` }"
                >
                  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
                </div>
              </div>

              <!-- Current Scanner -->
              <div v-if="agent.metrics.scan_progress.current_scanner" class="relative space-y-2">
                <div class="flex items-center gap-2 p-2 rounded-lg bg-blue-500/20 border border-blue-400/30">
                  <span class="relative flex h-1.5 w-1.5">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-cyan-300 shadow-md shadow-cyan-400/50"></span>
                  </span>
                  <div class="flex-1">
                    <div class="text-[9px] font-bold text-blue-200 uppercase tracking-wide">Running</div>
                    <div class="text-xs font-black text-blue-50">{{ agent.metrics.scan_progress.current_scanner }}</div>
                  </div>
                </div>
                
                <!-- Scan Details -->
                <div v-if="agent.metrics.scan_progress.scan_details" class="space-y-1 p-2 rounded-lg bg-blue-950/30 border border-blue-400/20">
                  <div v-if="agent.metrics.scan_progress.scan_details.targets" class="flex items-start gap-1.5 text-[9px]">
                    <span class="font-bold text-cyan-300 uppercase tracking-wide shrink-0">Targets:</span>
                    <span class="font-semibold text-blue-100 truncate">{{ Array.isArray(agent.metrics.scan_progress.scan_details.targets) ? agent.metrics.scan_progress.scan_details.targets.join(', ') : agent.metrics.scan_progress.scan_details.targets }}</span>
                  </div>
                  <div v-if="agent.metrics.scan_progress.scan_details.target" class="flex items-center gap-1.5 text-[9px]">
                    <span class="font-bold text-cyan-300 uppercase tracking-wide">Target:</span>
                    <span class="font-semibold text-blue-100">{{ agent.metrics.scan_progress.scan_details.target }}</span>
                  </div>
                  <div v-if="agent.metrics.scan_progress.scan_details.ports" class="flex items-center gap-1.5 text-[9px]">
                    <span class="font-bold text-cyan-300 uppercase tracking-wide">Ports:</span>
                    <span class="font-semibold text-blue-100">{{ agent.metrics.scan_progress.scan_details.ports }}</span>
                  </div>
                  <div v-if="agent.metrics.scan_progress.scan_details.interface" class="flex items-center gap-1.5 text-[9px]">
                    <span class="font-bold text-cyan-300 uppercase tracking-wide">Interface:</span>
                    <span class="font-semibold text-blue-100">{{ agent.metrics.scan_progress.scan_details.interface }}</span>
                  </div>
                  <div v-if="agent.metrics.scan_progress.scan_details.duration" class="flex items-center gap-1.5 text-[9px]">
                    <span class="font-bold text-cyan-300 uppercase tracking-wide">Duration:</span>
                    <span class="font-semibold text-blue-100">{{ agent.metrics.scan_progress.scan_details.duration }}s</span>
                  </div>
                  <div v-if="agent.metrics.scan_progress.scan_details.domain" class="flex items-center gap-1.5 text-[9px]">
                    <span class="font-bold text-cyan-300 uppercase tracking-wide">Domain:</span>
                    <span class="font-semibold text-blue-100">{{ agent.metrics.scan_progress.scan_details.domain }}</span>
                  </div>
                </div>
              </div>

              <!-- Results Count -->
              <div class="relative flex items-center justify-between p-2 rounded-lg bg-blue-500/20 border border-blue-400/30">
                <span class="text-[10px] font-bold text-blue-200 uppercase tracking-wide">Findings</span>
                <span class="text-sm font-black bg-gradient-to-br from-cyan-200 to-blue-100 bg-clip-text text-transparent">{{ agent.metrics.scan_progress.results_count || 0 }}</span>
              </div>
            </div>

            <div class="relative overflow-hidden rounded border border-white/10 bg-gradient-to-br from-white/10 to-white/5 p-1.5 shadow-sm">
              <div class="text-[7px] font-bold text-slate-200 uppercase tracking-wider mb-0.5">Capabilities</div>
              <div class="flex flex-wrap gap-0.5">
                <span
                  v-for="capability in agent.capabilities"
                  :key="capability"
                  class="inline-flex items-center px-0.5 py-0.5 rounded bg-slate-900/80 border border-white/10 text-[7px] font-bold tracking-wide text-slate-200 shadow-sm hover:bg-slate-800 hover:border-white/20 transition-all"
                >
                  {{ capability }}
                </span>
              </div>
            </div>

            <div class="flex gap-0.5">
              <button
                @click="openAssignModal(agent)"
                :disabled="agent.status !== 'idle'"
                :class="[
                  'group/btn flex-1 relative inline-flex items-center justify-center gap-0.5 rounded px-1.5 py-1 text-[8px] font-black transition-all duration-300 overflow-hidden',
                  agent.status === 'idle'
                    ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white hover:from-blue-500 hover:to-cyan-500 shadow-md shadow-blue-500/30 hover:shadow-lg hover:shadow-blue-500/50 hover:scale-[1.02]'
                    : 'bg-slate-800/50 text-slate-500 cursor-not-allowed border border-slate-700'
                ]"
              >
                <div v-if="agent.status === 'idle'" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent skew-x-12 -translate-x-full group-hover/btn:translate-x-full transition-transform duration-700"></div>
                <svg class="w-3 h-3 relative" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                <span class="relative">Assign Scan</span>
              </button>
            </div>
          </div>
        </article>
      </div>

      <div v-else-if="!isLoading" class="mt-16 text-center rounded-2xl border border-white/10 bg-white/5 py-14">
        <svg class="mx-auto h-12 w-12 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
        </svg>
        <h3 class="mt-4 text-lg font-semibold text-white">No agents registered</h3>
        <p class="mt-2 text-sm text-slate-400">Scanner agents will appear here once they register with the control plane.</p>
      </div>

      <transition name="fade">
        <div
          v-if="toast.visible"
          :class="[
            'fixed top-6 right-6 z-50 inline-flex items-center gap-3 rounded-xl border px-4 py-3 text-sm shadow-lg backdrop-blur',
            toast.type === 'error'
              ? 'bg-red-500/10 border-red-400/40 text-red-100'
              : 'bg-blue-500/10 border-blue-400/40 text-blue-100'
          ]"
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            v-if="toast.type !== 'error'"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            v-else
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <span>{{ toast.message }}</span>
        </div>
      </transition>
    </div>

    <transition name="fade">
      <div
        v-if="showAssignModal"
        class="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/80 backdrop-blur"
      >
        <div class="mx-4 w-full max-w-xl rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
          <header class="mb-5">
            <div class="text-xs uppercase tracking-wide text-slate-400">Assign Scan</div>
            <h2 class="text-2xl font-semibold text-white mt-1">{{ selectedAgent?.hostname }}</h2>
            <p class="mt-1 text-xs text-slate-500">
              Configure targets and tooling for this run. Capabilities pre-selected based on agent profile.
            </p>
          </header>

          <div class="space-y-4">
            <div v-if="selectedAgent?.capabilities.includes('nmap')">
              <label class="block text-sm font-medium text-slate-200 mb-1">Network targets</label>
              <input
                v-model="assignmentForm.targets"
                type="text"
                placeholder="192.168.1.0/24, 10.0.0.1"
                class="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
              <p class="mt-1 text-xs text-slate-500">IP addresses or CIDR ranges to scan.</p>
            </div>
            <div v-else>
              <label class="block text-sm font-medium text-slate-200 mb-1">Remote host (optional)</label>
              <input
                v-model="assignmentForm.remoteHost"
                type="text"
                placeholder="user@192.168.1.100"
                class="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
              <p class="mt-1 text-xs text-slate-500">SSH target for remote scanning (leave empty for local).</p>

              <label class="mt-4 block text-sm font-medium text-slate-200 mb-1">Paths to scan</label>
              <input
                v-model="assignmentForm.paths"
                type="text"
                placeholder="/tmp, /home, /var/www"
                class="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
              <p class="mt-1 text-xs text-slate-500">Directories or files to scan on target system.</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-200 mb-1">Scanners</label>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <label
                  v-for="scanner in availableScanners"
                  :key="scanner.value"
                  class="flex items-center gap-2 rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-200 hover:border-blue-400/40"
                >
                  <input
                    type="checkbox"
                    :value="scanner.value"
                    v-model="assignmentForm.scanners"
                    class="h-4 w-4 rounded border-slate-600 bg-slate-900 text-blue-500 focus:ring-blue-400"
                  />
                  <span>{{ scanner.label }}</span>
                </label>
              </div>
              <p v-if="availableScanners.length === 0" class="mt-1 text-xs text-amber-300/80">
                No scanners available for this agent.
              </p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-slate-200 mb-1">Ports</label>
                <input
                  v-model="assignmentForm.ports"
                  type="text"
                  placeholder="1-65535"
                  class="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-200 mb-1">Priority</label>
                <input
                  v-model.number="assignmentForm.priority"
                  type="number"
                  min="1"
                  max="10"
                  class="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
                />
              </div>
            </div>
          </div>

          <div class="mt-6 flex gap-3">
            <button
              @click="assignScan"
              class="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-blue-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-400"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Assign
            </button>
            <button
              @click="showAssignModal = false"
              class="flex-1 inline-flex items-center justify-center rounded-lg border border-white/10 bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:bg-slate-700"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
@keyframes float {
  0%, 100% {
    transform: translateY(0) translateX(0);
  }
  33% {
    transform: translateY(-30px) translateX(20px);
  }
  66% {
    transform: translateY(20px) translateX(-15px);
  }
}
</style>
