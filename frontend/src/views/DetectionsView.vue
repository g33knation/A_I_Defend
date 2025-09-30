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
  <div>
    <div class="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
      <div class="flex-1">
        <h1 class="text-2xl font-bold text-gray-800">Threat Detections</h1>
        <p class="mt-1 text-sm text-gray-500">Review and respond to potential security threats</p>
        {scanStatus && <p class="text-sm text-blue-600 mt-1">{{ scanStatus }}</p>}
      </div>
      <div>
        <button
          @click="runManualScan"
          :disabled="isScanning"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg v-if="isScanning" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ isScanning ? 'Scanning...' : 'Run Manual Scan' }}
        </button>
      </div>
      <div class="mt-4 md:mt-0 flex flex-col sm:flex-row gap-3">
        <div class="relative">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg class="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
            </svg>
          </div>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search detections..."
            class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <select
          v-model="selectedStatus"
          class="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
        >
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>

    <div class="bg-white shadow overflow-hidden sm:rounded-md">
      <ul class="divide-y divide-gray-200">
        <li v-for="detection in paginatedDetections" :key="detection.id" class="hover:bg-gray-50">
          <div class="px-4 py-4 sm:px-6">
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <div class="flex-shrink-0 h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
                  <svg class="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div class="ml-4">
                  <p class="text-sm font-medium text-gray-900">
                    {{ detection.type || 'Suspicious Activity Detected' }}
                  </p>
                  <p class="text-sm text-gray-500">
                    {{ detection.source || 'Unknown source' }}
                  </p>
                </div>
              </div>
              <div class="ml-4 flex-shrink-0">
                <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getStatusBadgeClass(detection.feedback)">
                  {{ getStatusLabel(detection.feedback) }}
                </span>
              </div>
            </div>
            
            <div class="mt-2 sm:flex sm:justify-between">
              <p class="flex items-center text-sm text-gray-500">
                <svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
                </svg>
                {{ formatDate(detection.created_at) }}
              </p>
            </div>
            
            <div class="mt-2">
              <div class="bg-gray-50 p-3 rounded-md">
                <pre class="text-xs text-gray-700 overflow-x-auto">{{ JSON.stringify(detection.details || {}, null, 2) }}</pre>
              </div>
            </div>
            
            <div v-if="!detection.feedback" class="mt-4 flex space-x-3">
              <button
                @click="submitFeedback(detection.id, 'confirmed_threat')"
                class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Confirm Threat
              </button>
              <button
                @click="submitFeedback(detection.id, 'false_positive')"
                class="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Mark as False Positive
              </button>
            </div>
          </div>
        </li>
      </ul>

      <!-- Empty state -->
      <div v-if="filteredDetections.length === 0" class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No detections found</h3>
        <p class="mt-1 text-sm text-gray-500">
          {{ searchQuery || selectedStatus !== 'all' ? 'Try adjusting your search or filter' : 'No detections have been recorded yet' }}
        </p>
      </div>

      <!-- Pagination -->
      <nav v-if="totalPages > 1" class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
        <div class="hidden sm:block">
          <p class="text-sm text-gray-700">
            Showing <span class="font-medium">{{ (currentPage - 1) * itemsPerPage + 1 }}</span>
            to <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredDetections.length) }}</span>
            of <span class="font-medium">{{ filteredDetections.length }}</span> results
          </p>
        </div>
        <div class="flex-1 flex justify-between sm:justify-end">
          <button
            @click="changePage(currentPage - 1)"
            :disabled="currentPage === 1"
            :class="{
              'opacity-50 cursor-not-allowed': currentPage === 1,
              'hover:bg-gray-50': currentPage > 1
            }"
            class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white"
          >
            Previous
          </button>
          <button
            @click="changePage(currentPage + 1)"
            :disabled="currentPage >= totalPages"
            :class="{
              'opacity-50 cursor-not-allowed': currentPage >= totalPages,
              'hover:bg-gray-50': currentPage < totalPages
            }"
            class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white"
          >
            Next
          </button>
        </div>
      </nav>
    </div>
  </div>
</template>
