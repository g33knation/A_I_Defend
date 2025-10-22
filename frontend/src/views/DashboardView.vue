<script setup>
import { ref, onMounted, computed } from 'vue';
import { useDefenseStore } from '@/stores/defense';
import SecurityScanner from '@/components/SecurityScanner.vue';

const store = useDefenseStore();

// API Base URL - dynamically determine based on current location
const getApiBaseUrl = () => {
  if (window.location.port === '8001') {
    return 'http://localhost:8000';
  }
  return window.location.origin;
};

const apiBaseUrl = getApiBaseUrl();

// System status data
const systemStatus = ref([
  { name: 'Web Server', status: 'operational' },
  { name: 'Database', status: 'operational' },
  { name: 'File Scanner', status: 'running' },
  { name: 'NMAP Scanner', status: 'idle' },
  { name: 'Lynis Scanner', status: 'idle' },
  { name: 'ClamAV', status: 'idle' },
  { name: 'RKHunter', status: 'idle' },
  { name: 'YARA', status: 'idle' },
  { name: 'Suricata', status: 'idle' },
]);

const lastScanTime = ref('Just now');
const activeTab = ref('dashboard'); // 'dashboard' or 'scanner'

// Sample data for charts
const chartData = ref({
  labels: Array.from({ length: 24 }, (_, i) => `${i}:00`),
  datasets: [
    {
      label: 'Events',
      data: Array.from({ length: 24 }, () => Math.floor(Math.random() * 50)),
      backgroundColor: 'rgba(99, 102, 241, 0.2)',
      borderColor: 'rgba(99, 102, 241, 1)',
      borderWidth: 2,
      tension: 0.4,
      fill: true
    },
    {
      label: 'Threats',
      data: Array.from({ length: 24 }, () => Math.floor(Math.random() * 10)),
      backgroundColor: 'rgba(239, 68, 68, 0.2)',
      borderColor: 'rgba(239, 68, 68, 1)',
      borderWidth: 2,
      tension: 0.4,
      fill: true
    }
  ]
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    },
    tooltip: {
      mode: 'index',
      intersect: false,
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        drawBorder: false
      }
    },
    x: {
      grid: {
        display: false
      }
    }
  }
};

const recentDetections = computed(() => {
  return [...store.detections].slice(0, 5);
});

const recentEvents = computed(() => {
  return [...store.events].slice(0, 5);
});

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString();
};

const formatTimeAgo = (dateString) => {
  if (!dateString) return 'Just now';
  const seconds = Math.floor((new Date() - new Date(dateString)) / 1000);
  
  let interval = Math.floor(seconds / 31536000);
  if (interval >= 1) return `${interval} year${interval === 1 ? '' : 's'} ago`;
  
  interval = Math.floor(seconds / 2592000);
  if (interval >= 1) return `${interval} month${interval === 1 ? '' : 's'} ago`;
  
  interval = Math.floor(seconds / 86400);
  if (interval >= 1) return `${interval} day${interval === 1 ? '' : 's'} ago`;
  
  interval = Math.floor(seconds / 3600);
  if (interval >= 1) return `${interval} hour${interval === 1 ? '' : 's'} ago`;
  
  interval = Math.floor(seconds / 60);
  if (interval >= 1) return `${interval} minute${interval === 1 ? '' : 's'} ago`;
  
  return 'Just now';
};

const getDetectionBadgeClass = (type) => {
  const typeMap = {
    'critical': 'bg-red-100 text-red-800',
    'high': 'bg-orange-100 text-orange-800',
    'medium': 'bg-yellow-100 text-yellow-800',
    'low': 'bg-blue-100 text-blue-800',
    'info': 'bg-gray-100 text-gray-800'
  };
  return typeMap[type?.toLowerCase()] || 'bg-gray-100 text-gray-800';
};

const getDetectionIcon = (type) => {
  const typeMap = {
    'critical': 'text-red-500',
    'high': 'text-orange-500',
    'medium': 'text-yellow-500',
    'low': 'text-blue-500',
    'info': 'text-gray-500'
  };
  return typeMap[type?.toLowerCase()] || 'text-gray-500';
};

const statusColor = (status) => {
  const statusMap = {
    'operational': 'bg-green-500',
    'running': 'bg-blue-500',
    'idle': 'bg-yellow-500',
    'error': 'bg-red-500',
    'warning': 'bg-yellow-500'
  };
  return statusMap[status?.toLowerCase()] || 'bg-gray-500';
};

const statusBadgeColor = (status) => {
  const statusMap = {
    'operational': 'bg-green-100 text-green-800',
    'running': 'bg-blue-100 text-blue-800',
    'idle': 'bg-yellow-100 text-yellow-800',
    'error': 'bg-red-100 text-red-800',
    'warning': 'bg-yellow-100 text-yellow-800'
  };
  return statusMap[status?.toLowerCase()] || 'bg-gray-100 text-gray-800';
};

const refreshData = async () => {
  await Promise.all([
    store.fetchDetections(),
    store.fetchEvents()
  ]);
  lastScanTime.value = 'Just now';
};

const runQuickScan = async () => {
  try {
    // Call the backend to start a quick scan with default scanners
    const response = await fetch(`${apiBaseUrl}/api/scans/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        scanners: ['nmap', 'lynis', 'clamav'],
        config: {}
      })
    });
    if (response.ok) {
      const data = await response.json();
      console.log('Scan started:', data);
      lastScanTime.value = 'Just now';
      // Refresh data after a short delay to get scan results
      setTimeout(refreshData, 3000);
    }
  } catch (error) {
    console.error('Failed to start quick scan:', error);
  }
};

onMounted(() => {
  refreshData();
  
  // Refresh data every 30 seconds
  const interval = setInterval(refreshData, 30000);
  
  // Cleanup interval on component unmount
  return () => clearInterval(interval);
});
</script>

<template>
  <div class="p-3 max-w-[1600px] mx-auto">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-2">
      <div>
        <h1 class="text-xl font-bold text-gray-800">Security Dashboard</h1>
        <p class="text-xs text-gray-600">Overview of your system's security status</p>
      </div>
      <button 
        @click="refreshData" 
        class="inline-flex items-center px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors shadow-sm"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 mr-1" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
        </svg>
        Refresh Data
      </button>
    </div>
    
    <!-- Navigation Tabs -->
    <div class="border-b border-gray-200 mb-3">
      <nav class="-mb-px flex space-x-4">
        <button 
          @click="activeTab = 'dashboard'" 
          :class="[activeTab === 'dashboard' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300', 'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs']"
        >
          Dashboard
        </button>
        <button 
          @click="activeTab = 'scanner'" 
          :class="[activeTab === 'scanner' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300', 'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs']"
        >
          Security Scanner
        </button>
      </nav>
    </div>

    <!-- Scanner View -->
    <div v-if="activeTab === 'scanner'" class="mb-8">
      <SecurityScanner />
    </div>

    <!-- Dashboard View -->
    <div v-else>
      <!-- Stats Cards -->
      <div class="flex gap-2 mb-4">
        <!-- Total Events -->
        <div class="flex-1 bg-white rounded shadow-sm p-2 border border-gray-100 hover:shadow-md transition-shadow">
          <div class="flex items-center">
            <div class="p-1 rounded-full bg-blue-50 text-blue-600">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div class="ml-2">
              <p class="text-[9px] font-medium text-gray-500">Total Events</p>
              <p class="text-sm font-semibold text-gray-900">{{ store.stats.totalEvents || 0 }}</p>
            </div>
          </div>
        </div>
        
        <!-- Open Detections -->
        <div class="flex-1 bg-white rounded shadow-sm p-2 border border-gray-100 hover:shadow-md transition-shadow">
          <div class="flex items-center">
            <div class="p-1 rounded-full bg-yellow-50 text-yellow-600">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div class="ml-2">
              <p class="text-[9px] font-medium text-gray-500">Open Detections</p>
              <p class="text-sm font-semibold text-gray-900">{{ store.stats.openDetections || 0 }}</p>
            </div>
          </div>
        </div>
        
        <!-- Threats Blocked -->
        <div class="flex-1 bg-white rounded shadow-sm p-2 border border-gray-100 hover:shadow-md transition-shadow">
          <div class="flex items-center">
            <div class="p-1 rounded-full bg-red-50 text-red-600">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div class="ml-2">
              <p class="text-[9px] font-medium text-gray-500">Threats Blocked</p>
              <p class="text-sm font-semibold text-gray-900">{{ store.stats.threatsBlocked || 0 }}</p>
            </div>
          </div>
        </div>
        
        <!-- False Positives -->
        <div class="flex-1 bg-white rounded shadow-sm p-2 border border-gray-100 hover:shadow-md transition-shadow">
          <div class="flex items-center">
            <div class="p-1 rounded-full bg-green-50 text-green-600">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div class="ml-2">
              <p class="text-[9px] font-medium text-gray-500">False Positives</p>
              <p class="text-sm font-semibold text-gray-900">{{ store.stats.falsePositives || 0 }}</p>
            </div>
          </div>
        </div>
      </div>

    <!-- Activity and System Status -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-4">
      <!-- Activity Chart -->
      <div class="bg-white rounded shadow-sm p-3 border border-gray-100 lg:col-span-2">
        <div class="flex justify-between items-center mb-2">
          <h2 class="text-sm font-semibold text-gray-800">Activity Overview</h2>
          <div class="flex space-x-2">
            <button class="px-2 py-0.5 text-[10px] rounded-full bg-blue-50 text-blue-600">24h</button>
            <button class="px-2 py-0.5 text-[10px] rounded-full text-gray-500 hover:bg-gray-50">7d</button>
            <button class="px-2 py-0.5 text-[10px] rounded-full text-gray-500 hover:bg-gray-50">30d</button>
          </div>
        </div>
        <div class="h-32 flex items-center justify-center bg-gray-50 rounded">
          <p class="text-xs text-gray-400">Activity chart will be displayed here</p>
        </div>
      </div>

      <!-- System Status -->
      <div class="bg-white rounded shadow-sm p-3 border border-gray-100">
        <h2 class="text-sm font-semibold text-gray-800 mb-2">System Status</h2>
        <div class="space-y-2">
          <div v-for="service in systemStatus" :key="service.name" class="flex items-center justify-between">
            <div class="flex items-center">
              <span :class="statusColor(service.status)" class="w-1.5 h-1.5 rounded-full mr-2"></span>
              <span class="text-[10px] font-medium text-gray-700">{{ service.name }}</span>
            </div>
            <span class="text-[9px] px-1 py-0.5 rounded-full" :class="statusBadgeColor(service.status)">
              {{ service.status }}
            </span>
          </div>
        </div>
        <div class="mt-3 pt-2 border-t border-gray-100">
          <div class="flex items-center justify-between text-[10px]">
            <span class="text-gray-500">Last Scan</span>
            <span class="font-medium">{{ lastScanTime || 'Never' }}</span>
          </div>
          <button @click="runQuickScan" class="mt-2 w-full px-2 py-1 bg-blue-600 text-white rounded text-[10px] hover:bg-blue-700 transition-colors flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-2.5 w-2.5 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
            </svg>
            Run Quick Scan
          </button>
        </div>
      </div>
    </div>

    <!-- Detections and Events -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <!-- Recent Detections -->
      <div class="bg-white rounded shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-3 py-2 border-b border-gray-100">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-semibold text-gray-800">Recent Detections</h2>
            <router-link to="/detections" class="text-[10px] text-blue-600 hover:underline">View All</router-link>
          </div>
        </div>
        <div class="divide-y divide-gray-100">
          <div v-if="recentDetections.length === 0" class="p-3 text-center text-gray-500">
            <p class="text-xs">No recent detections found</p>
          </div>
          <div v-else>
            <div v-for="detection in recentDetections" :key="detection.id" class="p-2 hover:bg-gray-50 transition-colors">
              <div class="flex items-start">
                <div :class="getDetectionIcon(detection.type)" class="flex-shrink-0 mt-0.5">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h2a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="ml-2 flex-1">
                  <div class="flex items-center justify-between">
                    <p class="text-[10px] font-medium text-gray-900">{{ detection.message || 'Suspicious activity detected' }}</p>
                    <span class="inline-flex items-center px-1 py-0.5 rounded-full text-[9px] font-medium" :class="getDetectionBadgeClass(detection.type)">
                      {{ detection.type || 'unknown' }}
                    </span>
                  </div>
                  <p class="mt-0.5 text-[9px] text-gray-500">
                    {{ formatTimeAgo(detection.timestamp || detection.created_at) }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Events -->
      <div class="bg-white rounded shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-3 py-2 border-b border-gray-100">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-semibold text-gray-800">Recent Events</h2>
            <router-link to="/events" class="text-[10px] text-blue-600 hover:underline">View All</router-link>
          </div>
        </div>
        <div class="divide-y divide-gray-100">
          <div v-if="recentEvents.length === 0" class="p-3 text-center text-gray-500">
            <p class="text-xs">No recent events found</p>
          </div>
          <div v-else>
            <div v-for="event in recentEvents" :key="event.id" class="p-2 hover:bg-gray-50 transition-colors">
              <div class="flex items-start">
                <div class="flex-shrink-0 mt-0.5 text-gray-400">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="ml-2 flex-1">
                  <div class="flex items-center justify-between">
                    <p class="text-[10px] font-medium text-gray-900">{{ event.source || 'System' }}</p>
                    <span class="text-[9px] text-gray-500">{{ formatTimeAgo(event.timestamp || event.created_at) }}</span>
                  </div>
                  <p class="mt-0.5 text-[9px] text-gray-500">
                    {{ event.type || 'Event' }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<style scoped>
/* Add any component-specific styles here */
</style>
