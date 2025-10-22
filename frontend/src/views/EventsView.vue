<script setup>
import { ref, computed, onMounted } from 'vue';
import { useDefenseStore } from '@/stores/defense';

const store = useDefenseStore();
const searchQuery = ref('');
const selectedType = ref('all');
const currentPage = ref(1);
const itemsPerPage = 10;

const eventTypes = computed(() => {
  const types = new Set(store.events.map(event => event.type));
  return ['all', ...Array.from(types)];
});

const filteredEvents = computed(() => {
  return store.events.filter(event => {
    const matchesSearch = JSON.stringify(event).toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesType = selectedType.value === 'all' || event.type === selectedType.value;
    return matchesSearch && matchesType;
  });
});

const paginatedEvents = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return filteredEvents.value.slice(start, end);
});

const totalPages = computed(() => {
  return Math.ceil(filteredEvents.value.length / itemsPerPage);
});

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
};

const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
};

onMounted(() => {
  store.fetchEvents();
});
</script>

<template>
  <div class="p-4 max-w-[1600px] mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Security Events</h1>
        <p class="text-xs text-gray-600 mt-0.5">{{ filteredEvents.length }} events</p>
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
          v-model="selectedType"
          class="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option v-for="type in eventTypes" :key="type" :value="type">
            {{ type === 'all' ? 'All Types' : type }}
          </option>
        </select>
      </div>
    </div>

    <!-- Events Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
      <div 
        v-for="event in paginatedEvents" 
        :key="event.id" 
        class="bg-white rounded-lg border border-gray-200 p-2 hover:shadow-md transition-shadow cursor-pointer"
      >
        <div class="flex items-start justify-between mb-1.5">
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-gray-900 text-[10px] mb-0.5 truncate">{{ event.type || 'Unknown Event' }}</h3>
            <p class="text-[9px] text-gray-500">{{ formatDate(event.created_at) }}</p>
          </div>
          <span class="px-1.5 py-0.5 text-[9px] font-medium rounded-full bg-blue-100 text-blue-800 shrink-0">
            {{ event.source || 'Unknown' }}
          </span>
        </div>
        
        <!-- Compact payload summary -->
        <div class="text-[9px] text-gray-600 space-y-0.5">
          <div v-if="event.payload?.details?.address" class="truncate">
            <span class="font-medium">Target:</span> {{ event.payload.details.address }}
          </div>
          <div v-if="event.payload?.details?.ports?.length">
            <span class="font-medium">Ports:</span> {{ event.payload.details.ports.length }}
          </div>
          <div v-if="event.payload?.severity">
            <span class="font-medium">Severity:</span> {{ event.payload.severity }}
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="filteredEvents.length === 0" class="text-center py-12 bg-white rounded-lg border border-gray-200">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No events found</h3>
      <p class="mt-1 text-sm text-gray-500">
        {{ searchQuery || selectedType !== 'all' ? 'Try adjusting your search or filter' : 'No events have been recorded yet' }}
      </p>
    </div>

    <!-- Pagination -->
    <nav v-if="totalPages > 1" class="mt-6 flex items-center justify-between">
      <div class="text-sm text-gray-700">
        Showing <span class="font-medium">{{ (currentPage - 1) * itemsPerPage + 1 }}</span>
        to <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredEvents.length) }}</span>
        of <span class="font-medium">{{ filteredEvents.length }}</span> results
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
