<script setup>
import { ref, computed, onMounted } from 'vue';
import { useDefenseStore } from '@/stores/defense';

const store = useDefenseStore();
const searchQuery = ref('');
const selectedStatus = ref('all');
const currentPage = ref(1);
const itemsPerPage = 10;
const expandedDetections = ref(new Set());

const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'new', label: 'New' },
  { value: 'confirmed_threat', label: 'Confirmed Threat' },
  { value: 'false_positive', label: 'False Positive' }
];

const filteredDetections = computed(() => {
  return store.detections.filter(detection => {
    const matchesSearch = JSON.stringify(detection).toLowerCase().includes(searchQuery.value.toLowerCase());
    
    let matchesStatus = true;
    if (selectedStatus.value === 'new') {
      matchesStatus = !detection.feedback;
    } else if (selectedStatus.value !== 'all') {
      matchesStatus = detection.feedback === selectedStatus.value;
    }
    
    return matchesSearch && matchesStatus;
  });
});

const paginatedDetections = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return filteredDetections.value.slice(start, end);
});

const totalPages = computed(() => {
  return Math.ceil(filteredDetections.value.length / itemsPerPage);
});

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
};

const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
  }
};

const submitFeedback = async (detectionId, feedback) => {
  await store.submitFeedback(detectionId, feedback);
  await store.fetchDetections();
};

const purgeDetections = async () => {
  if (!confirm('Are you sure you want to delete ALL detections? This cannot be undone.')) {
    return;
  }
  try {
    const response = await fetch('http://localhost:8000/detections', {
      method: 'DELETE'
    });
    if (response.ok) {
      await store.fetchDetections();
      alert('All detections have been purged');
    }
  } catch (err) {
    console.error('Error purging detections:', err);
    alert('Failed to purge detections');
  }
};

const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'confirmed_threat':
      return 'bg-red-100 text-red-800';
    case 'false_positive':
      return 'bg-yellow-100 text-yellow-800';
      return 'bg-blue-100 text-blue-800';
  }
};

const getStatusLabel = (status) => {
  switch (status) {
    case 'confirmed_threat':
      return 'Threat';
    case 'false_positive':
      return 'False Positive';
    default:
      return 'New';
  }
};

const toggleDetails = (detectionId) => {
  if (expandedDetections.value.has(detectionId)) {
    expandedDetections.value.delete(detectionId);
  } else {
    expandedDetections.value.add(detectionId);
  }
};

const isExpanded = (detectionId) => {
  return expandedDetections.value.has(detectionId);
};

onMounted(() => {
  store.fetchDetections();
});
</script>

<template>
  <div class="p-4 max-w-[1600px] mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Threat Detections</h1>
        <p class="text-xs text-gray-600 mt-0.5">{{ filteredDetections.length }} detections</p>
        <p v-if="scanStatus" class="text-sm text-blue-600 mt-1">{{ scanStatus }}</p>
      </div>
      <div class="flex gap-3">
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search..."
            class="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg class="absolute left-3 top-2.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
          </svg>
        </div>
        <select
          v-model="selectedStatus"
          class="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <button
          @click="purgeDetections"
          class="px-4 py-2 text-sm font-medium rounded-lg text-white bg-red-600 hover:bg-red-700 transition-colors"
        >
          Purge All
        </button>
      </div>
    </div>

    <!-- Detections Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
      <div 
        v-for="detection in paginatedDetections" 
        :key="detection.id" 
        class="bg-white rounded-lg border border-gray-200 p-2 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between mb-1.5">
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-gray-900 text-[10px] mb-0.5 truncate">{{ detection.summary || detection.type || 'Detection' }}</h3>
            <p class="text-[9px] text-gray-500">{{ formatDate(detection.detected_at || detection.created_at) }}</p>
          </div>
          <span class="px-1 py-0.5 text-[9px] font-medium rounded-full shrink-0" :class="getStatusBadgeClass(detection.feedback)">
            {{ getStatusLabel(detection.feedback) }}
          </span>
        </div>
        
        <!-- Detection details -->
        <div class="text-[9px] text-gray-600 space-y-0.5 mb-1.5">
          <div v-if="detection.category">
            <span class="font-medium">Category:</span> {{ detection.category }}
          </div>
          <div v-if="detection.score">
            <span class="font-medium">Threat Score:</span> {{ (detection.score * 100).toFixed(0) }}%
          </div>
          
          <!-- Show port details if available -->
          <div v-if="detection.ai_output?.details?.ports" class="mt-0.5 pt-0.5 border-t border-gray-200">
            <div class="font-medium mb-0.5 text-[8px]">Ports:</div>
            <div class="flex flex-wrap gap-0.5">
              <span 
                v-for="(port, idx) in detection.ai_output.details.ports.slice(0, 5)" 
                :key="idx"
                class="px-0.5 py-0.5 bg-blue-50 text-blue-700 rounded text-[8px]"
              >
                {{ typeof port === 'object' ? `${port.port}` : port }}
              </span>
              <span v-if="detection.ai_output.details.ports.length > 5" class="text-gray-500 text-[8px]">
                +{{ detection.ai_output.details.ports.length - 5 }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- Collapsible Statistics/Details Section -->
        <div class="mb-1.5">
          <button
            @click="toggleDetails(detection.id)"
            class="w-full flex items-center justify-between px-1.5 py-0.5 text-[9px] font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded transition-colors"
          >
            <span class="flex items-center gap-0.5">
              <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Details
            </span>
            <svg 
              :class="{ 'rotate-180': isExpanded(detection.id) }" 
              class="w-2.5 h-2.5 transition-transform" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          <!-- Expanded Details -->
          <div v-if="isExpanded(detection.id)" class="mt-1 p-2 bg-gray-50 rounded border border-gray-200">
            <div class="space-y-2">
              <!-- Scanner Information -->
              <div v-if="detection.ai_output?.scanner">
                <div class="text-[9px] font-semibold text-gray-700 mb-0.5">Scanner</div>
                <div class="text-[10px] text-gray-600 bg-white px-1.5 py-0.5 rounded border border-gray-200">
                  {{ detection.ai_output.scanner }}
                </div>
              </div>
              
              <!-- Target Information -->
              <div v-if="detection.ai_output?.target || detection.ai_output?.details?.address">
                <div class="text-[9px] font-semibold text-gray-700 mb-0.5">Target</div>
                <div class="text-[10px] text-gray-600 bg-white px-1.5 py-0.5 rounded border border-gray-200 truncate">
                  {{ detection.ai_output.target || detection.ai_output.details?.address }}
                </div>
              </div>
              
              <!-- Detailed Port Information -->
              <div v-if="detection.ai_output?.details?.ports && detection.ai_output.details.ports.length > 0">
                <div class="text-xs font-semibold text-gray-700 mb-1">
                  Port Details ({{ detection.ai_output.details.ports.length }} total)
                </div>
                <div class="max-h-48 overflow-y-auto bg-white rounded border border-gray-200">
                  <table class="w-full text-xs">
                    <thead class="bg-gray-100 sticky top-0">
                      <tr>
                        <th class="px-2 py-1 text-left font-medium text-gray-700">Port</th>
                        <th class="px-2 py-1 text-left font-medium text-gray-700">Protocol</th>
                        <th class="px-2 py-1 text-left font-medium text-gray-700">Service</th>
                        <th class="px-2 py-1 text-left font-medium text-gray-700">Version</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(port, idx) in detection.ai_output.details.ports" :key="idx" class="border-t border-gray-100">
                        <td class="px-2 py-1 font-mono">{{ port.port || port }}</td>
                        <td class="px-2 py-1">{{ port.protocol || 'tcp' }}</td>
                        <td class="px-2 py-1">{{ port.service || '-' }}</td>
                        <td class="px-2 py-1 text-gray-500">{{ port.version || '-' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              
              <!-- Live Hosts (for ping sweep/arp scan) -->
              <div v-if="detection.ai_output?.details?.live_hosts">
                <div class="text-xs font-semibold text-gray-700 mb-1">
                  Live Hosts ({{ detection.ai_output.details.live_hosts.length }})
                </div>
                <div class="max-h-32 overflow-y-auto bg-white px-2 py-1 rounded border border-gray-200">
                  <div class="flex flex-wrap gap-1">
                    <span v-for="(host, idx) in detection.ai_output.details.live_hosts" :key="idx" class="text-xs font-mono text-gray-700">
                      {{ host }}{{ idx < detection.ai_output.details.live_hosts.length - 1 ? ',' : '' }}
                    </span>
                  </div>
                </div>
              </div>
              
              <!-- ARP Scan Hosts -->
              <div v-if="detection.ai_output?.details?.hosts">
                <div class="text-xs font-semibold text-gray-700 mb-1">
                  Discovered Hosts ({{ detection.ai_output.details.hosts.length }})
                </div>
                <div class="max-h-48 overflow-y-auto bg-white rounded border border-gray-200">
                  <table class="w-full text-xs">
                    <thead class="bg-gray-100 sticky top-0">
                      <tr>
                        <th class="px-2 py-1 text-left font-medium text-gray-700">IP Address</th>
                        <th class="px-2 py-1 text-left font-medium text-gray-700">MAC Address</th>
                        <th class="px-2 py-1 text-left font-medium text-gray-700">Vendor</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(host, idx) in detection.ai_output.details.hosts" :key="idx" class="border-t border-gray-100">
                        <td class="px-2 py-1 font-mono">{{ host.ip }}</td>
                        <td class="px-2 py-1 font-mono text-gray-600">{{ host.mac }}</td>
                        <td class="px-2 py-1 text-gray-500">{{ host.vendor || '-' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              
              <!-- Statistics Summary -->
              <div v-if="detection.ai_output?.details" class="pt-2 border-t border-gray-200">
                <div class="text-xs font-semibold text-gray-700 mb-2">Statistics</div>
                <div class="grid grid-cols-2 gap-2">
                  <div v-if="detection.ai_output.details.total_open_ports" class="bg-white px-2 py-1 rounded border border-gray-200">
                    <div class="text-xs text-gray-500">Open Ports</div>
                    <div class="text-sm font-semibold text-gray-900">{{ detection.ai_output.details.total_open_ports }}</div>
                  </div>
                  <div v-if="detection.ai_output.details.total_live_hosts" class="bg-white px-2 py-1 rounded border border-gray-200">
                    <div class="text-xs text-gray-500">Live Hosts</div>
                    <div class="text-sm font-semibold text-gray-900">{{ detection.ai_output.details.total_live_hosts }}</div>
                  </div>
                  <div v-if="detection.ai_output.details.total_unique_ips" class="bg-white px-2 py-1 rounded border border-gray-200">
                    <div class="text-xs text-gray-500">Unique IPs</div>
                    <div class="text-sm font-semibold text-gray-900">{{ detection.ai_output.details.total_unique_ips }}</div>
                  </div>
                  <div v-if="detection.ai_output.details.total_packets" class="bg-white px-2 py-1 rounded border border-gray-200">
                    <div class="text-xs text-gray-500">Packets</div>
                    <div class="text-sm font-semibold text-gray-900">{{ detection.ai_output.details.total_packets }}</div>
                  </div>
                </div>
              </div>
              
              <!-- Raw JSON (for debugging) -->
              <details class="text-xs">
                <summary class="cursor-pointer text-gray-600 hover:text-gray-800 font-medium">Raw Data (JSON)</summary>
                <pre class="mt-2 p-2 bg-gray-900 text-green-400 rounded text-xs overflow-x-auto">{{ JSON.stringify(detection.ai_output, null, 2) }}</pre>
              </details>
            </div>
          </div>
        </div>
        
        <!-- Actions -->
        <div v-if="!detection.feedback" class="flex gap-0.5">
          <button
            @click="submitFeedback(detection.id, 'confirmed_threat')"
            class="flex-1 px-1.5 py-0.5 text-[9px] font-medium rounded text-white bg-red-600 hover:bg-red-700 transition-colors"
          >
            Threat
          </button>
          <button
            @click="submitFeedback(detection.id, 'false_positive')"
            class="flex-1 px-1.5 py-0.5 text-[9px] font-medium rounded text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            False
          </button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="filteredDetections.length === 0" class="text-center py-12 bg-white rounded-lg border border-gray-200">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No detections found</h3>
      <p class="mt-1 text-sm text-gray-500">
        {{ searchQuery || selectedStatus !== 'all' ? 'Try adjusting your search or filter' : 'No detections have been recorded yet' }}
      </p>
    </div>

    <!-- Pagination -->
    <nav v-if="totalPages > 1" class="mt-6 flex items-center justify-between">
      <div class="text-sm text-gray-700">
        Showing <span class="font-medium">{{ (currentPage - 1) * itemsPerPage + 1 }}</span>
        to <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredDetections.length) }}</span>
        of <span class="font-medium">{{ filteredDetections.length }}</span> results
      </div>
      <div class="flex gap-2">
        <button
          @click="changePage(currentPage - 1)"
          :disabled="currentPage === 1"
          :class="currentPage === 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'"
          class="px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white transition-colors"
        >
          Previous
        </button>
        <button
          @click="changePage(currentPage + 1)"
          :disabled="currentPage >= totalPages"
          :class="currentPage >= totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'"
          class="px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white transition-colors"
        >
          Next
        </button>
      </div>
    </nav>
  </div>
</template>
