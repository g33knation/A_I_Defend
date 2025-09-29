<script setup>
import { ref, onMounted, computed } from 'vue';
import { useDefenseStore } from '@/stores/defense';

const store = useDefenseStore();

// Sample data for charts (you can replace with real data)
const chartData = ref({
  labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  datasets: [
    {
      label: 'Events',
      data: [12, 19, 3, 5, 2, 3, 8],
      backgroundColor: 'rgba(99, 102, 241, 0.2)',
      borderColor: 'rgba(99, 102, 241, 1)',
      borderWidth: 1,
      tension: 0.4
    },
    {
      label: 'Threats',
      data: [2, 3, 1, 4, 1, 0, 2],
      backgroundColor: 'rgba(239, 68, 68, 0.2)',
      borderColor: 'rgba(239, 68, 68, 1)',
      borderWidth: 1,
      tension: 0.4
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
  },
  scales: {
    y: {
      beginAtZero: true
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
  return new Date(dateString).toLocaleString();
};

onMounted(() => {
  store.fetchDetections();
  store.fetchEvents();
});
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Security Dashboard</h1>
    
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-indigo-100 text-indigo-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div class="ml-4">
            <h3 class="text-gray-500 text-sm font-medium">Total Events</h3>
            <p class="text-2xl font-bold text-gray-900">{{ store.stats.totalEvents }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-red-100 text-red-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div class="ml-4">
            <h3 class="text-gray-500 text-sm font-medium">Open Detections</h3>
            <p class="text-2xl font-bold text-gray-900">{{ store.stats.openDetections }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-green-100 text-green-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div class="ml-4">
            <h3 class="text-gray-500 text-sm font-medium">Threats Blocked</h3>
            <p class="text-2xl font-bold text-gray-900">{{ store.stats.threatsBlocked }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-yellow-100 text-yellow-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="ml-4">
            <h3 class="text-gray-500 text-sm font-medium">False Positives</h3>
            <p class="text-2xl font-bold text-gray-900">{{ store.stats.falsePositives }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Chart -->
    <div class="bg-white rounded-lg shadow p-6 mb-8">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">Activity Overview</h2>
      <div class="h-64">
        <!-- Chart will be rendered here -->
        <div class="h-full flex items-center justify-center bg-gray-50 rounded">
          <p class="text-gray-500">Chart visualization will appear here</p>
        </div>
      </div>
    </div>
    
    <!-- Recent Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Detections -->
      <div class="bg-white rounded-lg shadow">
        <div class="p-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-800">Recent Detections</h2>
        </div>
        <div class="divide-y divide-gray-200">
          <div v-for="(detection, index) in recentDetections" :key="index" class="p-4 hover:bg-gray-50">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-medium text-gray-900">Suspicious Activity Detected</h3>
                <p class="text-sm text-gray-500">{{ detection.type || 'Unknown' }}</p>
              </div>
              <span class="px-2 py-1 text-xs font-medium rounded-full" 
                    :class="{
                      'bg-red-100 text-red-800': !detection.feedback,
                      'bg-green-100 text-green-800': detection.feedback === 'confirmed_threat',
                      'bg-yellow-100 text-yellow-800': detection.feedback === 'false_positive'
                    }">
                {{ !detection.feedback ? 'New' : detection.feedback === 'confirmed_threat' ? 'Threat' : 'False Positive' }}
              </span>
            </div>
            <div class="mt-2 text-sm text-gray-500">
              {{ formatDate(detection.created_at) }}
            </div>
          </div>
          <div v-if="recentDetections.length === 0" class="p-4 text-center text-gray-500">
            No recent detections
          </div>
        </div>
        <div class="p-4 border-t border-gray-200 text-right">
          <router-link to="/detections" class="text-sm font-medium text-indigo-600 hover:text-indigo-500">
            View all detections →
          </router-link>
        </div>
      </div>
      
      <!-- Recent Events -->
      <div class="bg-white rounded-lg shadow">
        <div class="p-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-800">Recent Events</h2>
        </div>
        <div class="divide-y divide-gray-200">
          <div v-for="(event, index) in recentEvents" :key="index" class="p-4 hover:bg-gray-50">
            <div class="flex items-start">
              <div class="flex-shrink-0 h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                <span class="text-indigo-600">🔔</span>
              </div>
              <div class="ml-4">
                <h3 class="font-medium text-gray-900">{{ event.type || 'Event' }}</h3>
                <p class="text-sm text-gray-500">{{ event.source || 'Unknown source' }}</p>
                <div class="mt-1 text-xs text-gray-500">
                  {{ formatDate(event.created_at) }}
                </div>
              </div>
            </div>
          </div>
          <div v-if="recentEvents.length === 0" class="p-4 text-center text-gray-500">
            No recent events
          </div>
        </div>
        <div class="p-4 border-t border-gray-200 text-right">
          <router-link to="/events" class="text-sm font-medium text-indigo-600 hover:text-indigo-500">
            View all events →
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
