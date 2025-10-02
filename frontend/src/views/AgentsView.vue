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
  ports: '1-1000',
  priority: 5
});

const scannerOptions = [
  { value: 'nmap', label: 'Nmap (Network Scanner)' },
  { value: 'lynis', label: 'Lynis (Security Audit)' },
  { value: 'clamav', label: 'ClamAV (Antivirus)' }
];

const fetchAgents = async () => {
  try {
    isLoading.value = true;
    const response = await fetch(`${API_BASE}/api/agents/`);
    agents.value = await response.json();
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
    const targets = assignmentForm.value.targets.split(',').map(t => t.trim());
    
    const response = await fetch(`${API_BASE}/api/agents/${selectedAgent.value.agent_id}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        targets,
        scanners: assignmentForm.value.scanners,
        config: {
          ports: assignmentForm.value.ports
        },
        priority: assignmentForm.value.priority
      })
    });
    
    if (response.ok) {
      showAssignModal.value = false;
      await fetchAgents();
      alert('Scan assigned successfully!');
    } else {
      const data = await response.json();
      alert(`Failed to assign scan: ${data.detail}`);
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};

const openAssignModal = (agent) => {
  selectedAgent.value = agent;
  showAssignModal.value = true;
};

const getStatusColor = (status) => {
  const colors = {
    'idle': 'bg-green-100 text-green-800',
    'scanning': 'bg-blue-100 text-blue-800',
    'error': 'bg-red-100 text-red-800',
    'offline': 'bg-gray-100 text-gray-800'
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
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-800">Scanner Agents</h1>
        <p class="text-gray-600 mt-1">{{ agents.length }} agents registered</p>
      </div>
      <button
        @click="fetchAgents"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
      >
        Refresh
      </button>
    </div>

    <!-- Agents Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="agent in agents" 
        :key="agent.agent_id" 
        class="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <h3 class="font-semibold text-gray-900 text-sm mb-1">{{ agent.hostname }}</h3>
            <p class="text-xs text-gray-500">{{ agent.ip_address }}</p>
          </div>
          <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getStatusColor(agent.status)">
            {{ agent.status }}
          </span>
        </div>
        
        <!-- Agent details -->
        <div class="text-xs text-gray-600 space-y-1 mb-3">
          <div>
            <span class="font-medium">Agent ID:</span> {{ agent.agent_id.substring(0, 8) }}...
          </div>
          <div>
            <span class="font-medium">Capabilities:</span> {{ agent.capabilities.join(', ') }}
          </div>
          <div>
            <span class="font-medium">Last Heartbeat:</span> {{ getTimeSinceHeartbeat(agent.last_heartbeat) }}
          </div>
          <div v-if="agent.current_assignment">
            <span class="font-medium">Current Task:</span> {{ agent.current_assignment.substring(0, 8) }}...
          </div>
        </div>
        
        <!-- Actions -->
        <div class="flex gap-2">
          <button
            @click="openAssignModal(agent)"
            :disabled="agent.status !== 'idle'"
            :class="agent.status === 'idle' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'"
            class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md text-white transition-colors"
          >
            Assign Scan
          </button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="agents.length === 0 && !isLoading" class="text-center py-12 bg-white rounded-lg border border-gray-200">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No agents registered</h3>
      <p class="mt-1 text-sm text-gray-500">Scanner agents will appear here once they register with the control plane</p>
    </div>

    <!-- Assignment Modal -->
    <div v-if="showAssignModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 class="text-xl font-bold mb-4">Assign Scan to {{ selectedAgent?.hostname }}</h2>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Targets (comma-separated)</label>
            <input
              v-model="assignmentForm.targets"
              type="text"
              placeholder="192.168.1.0/24, 10.0.0.1"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Scanners</label>
            <div class="space-y-2">
              <label v-for="scanner in scannerOptions" :key="scanner.value" class="flex items-center">
                <input
                  type="checkbox"
                  :value="scanner.value"
                  v-model="assignmentForm.scanners"
                  class="mr-2"
                />
                <span class="text-sm">{{ scanner.label }}</span>
              </label>
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Ports</label>
            <input
              v-model="assignmentForm.ports"
              type="text"
              placeholder="1-1000"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Priority (1-10)</label>
            <input
              v-model.number="assignmentForm.priority"
              type="number"
              min="1"
              max="10"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        
        <div class="flex gap-3 mt-6">
          <button
            @click="assignScan"
            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            Assign
          </button>
          <button
            @click="showAssignModal = false"
            class="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
