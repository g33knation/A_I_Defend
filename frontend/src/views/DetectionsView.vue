<script setup>
import { ref, computed, onMounted } from 'vue';
import { useDefenseStore } from '@/stores/defense';

const store = useDefenseStore();
const searchQuery = ref('');
const selectedStatus = ref('all');
const currentPage = ref(1);
const itemsPerPage = 10;
const isScanning = ref(false);
const scanStatus = ref('');

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

const runManualScan = async () => {
  try {
    isScanning.value = true;
    scanStatus.value = 'Starting manual scan...';
    
    const response = await fetch(`${store.API_BASE}/scans/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        scanners: ["nmap", "lynis", "clamav", "chkrootkit", "rkhunter", "yara", "suricata"]
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to start scan');
    }
    
    const { scan_id } = await response.json();
    scanStatus.value = 'Scan in progress...';
    
    // Poll for scan completion
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes max (5 seconds * 60 = 300 seconds)
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 5000)); // Check every 5 seconds
      
      const statusResponse = await fetch(`${store.API_BASE}/scans/${scan_id}`);
      const statusData = await statusResponse.json();
      
      if (statusData.status === 'completed') {
        scanStatus.value = 'Scan completed! Refreshing detections...';
        await store.fetchDetections();
        break;
      } else if (statusData.status === 'failed') {
        throw new Error(statusData.error || 'Scan failed');
      }
      
      attempts++;
    }
    
    if (attempts >= maxAttempts) {
      throw new Error('Scan timed out');
    }
    
  } catch (error) {
    console.error('Error running manual scan:', error);
    scanStatus.value = `Error: ${error.message}`;
  } finally {
    isScanning.value = false;
    // Clear status after 5 seconds
    setTimeout(() => {
      scanStatus.value = '';
    }, 5000);
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

onMounted(() => {
  store.fetchDetections();
});
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-800">Threat Detections</h1>
        <p class="text-gray-600 mt-1">{{ filteredDetections.length }} detections</p>
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
          @click="runManualScan"
          :disabled="isScanning"
          class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
        >
          <svg v-if="isScanning" class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ isScanning ? 'Scanning...' : 'Run Scan' }}
        </button>
      </div>
    </div>

    <!-- Detections Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="detection in paginatedDetections" 
        :key="detection.id" 
        class="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <h3 class="font-semibold text-gray-900 text-sm mb-1">{{ detection.summary || detection.type || 'Detection' }}</h3>
            <p class="text-xs text-gray-500">{{ formatDate(detection.created_at) }}</p>
          </div>
          <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getStatusBadgeClass(detection.feedback)">
            {{ getStatusLabel(detection.feedback) }}
          </span>
        </div>
        
        <!-- Detection details -->
        <div class="text-xs text-gray-600 space-y-1 mb-3">
          <div v-if="detection.category">
            <span class="font-medium">Category:</span> {{ detection.category }}
          </div>
          <div v-if="detection.score">
            <span class="font-medium">Score:</span> {{ (detection.score * 100).toFixed(0) }}%
          </div>
        </div>
        
        <!-- Actions -->
        <div v-if="!detection.feedback" class="flex gap-2">
          <button
            @click="submitFeedback(detection.id, 'confirmed_threat')"
            class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700 transition-colors"
          >
            Confirm
          </button>
          <button
            @click="submitFeedback(detection.id, 'false_positive')"
            class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            False Positive
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
