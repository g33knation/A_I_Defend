<script setup>
import { RouterLink, RouterView } from 'vue-router';
import { ref, onMounted } from 'vue';
import { useDefenseStore } from './stores/defense';

const store = useDefenseStore();
const isMenuOpen = ref(false);

onMounted(() => {
  store.fetchDetections();
  store.fetchEvents();
  // Refresh data every 30 seconds
  setInterval(() => {
    store.fetchDetections();
    store.fetchEvents();
  }, 30000);
});
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Mobile menu button -->
    <div class="lg:hidden bg-indigo-700 p-4 flex justify-between items-center">
      <h1 class="text-white text-xl font-bold">AI Defense Dashboard</h1>
      <button 
        @click="isMenuOpen = !isMenuOpen"
        class="text-white focus:outline-none"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path v-if="!isMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path>
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>

    <div class="flex h-screen overflow-hidden">
      <!-- Sidebar -->
      <div 
        :class="{'translate-x-0': isMenuOpen, '-translate-x-full': !isMenuOpen}" 
        class="fixed inset-y-0 left-0 z-40 w-64 bg-indigo-800 text-white transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0"
      >
        <div class="p-4 border-b border-indigo-700">
          <h1 class="text-xl font-bold">AI Defense</h1>
          <p class="text-indigo-300 text-sm">Security Monitoring Dashboard</p>
        </div>
        
        <nav class="mt-6">
          <RouterLink 
            to="/" 
            class="flex items-center px-6 py-3 text-indigo-200 hover:bg-indigo-700"
            active-class="bg-indigo-900 text-white"
          >
            <span class="mr-3">📊</span>
            <span>Dashboard</span>
          </RouterLink>
          
          <RouterLink 
            to="/events" 
            class="flex items-center px-6 py-3 text-indigo-200 hover:bg-indigo-700"
            active-class="bg-indigo-900 text-white"
          >
            <span class="mr-3">🔔</span>
            <span>Events</span>
          </RouterLink>
          
          <RouterLink 
            to="/detections" 
            class="flex items-center px-6 py-3 text-indigo-200 hover:bg-indigo-700"
            active-class="bg-indigo-900 text-white"
          >
            <span class="mr-3">🚨</span>
            <span>Detections</span>
            <span v-if="store.stats.openDetections > 0" 
                  class="ml-auto px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
              {{ store.stats.openDetections }}
            </span>
          </RouterLink>
          
          <RouterLink 
            to="/agents" 
            class="flex items-center px-6 py-3 text-indigo-200 hover:bg-indigo-700"
            active-class="bg-indigo-900 text-white"
          >
            <span class="mr-3">🐙</span>
            <span>Scanner Agents</span>
          </RouterLink>
          
          <RouterLink 
            to="/ask" 
            class="flex items-center px-6 py-3 text-indigo-200 hover:bg-indigo-700"
            active-class="bg-indigo-900 text-white"
          >
            <span class="mr-3">💬</span>
            <span>Ask AI</span>
          </RouterLink>
        </nav>
        
        <div class="absolute bottom-0 w-full p-4 text-xs text-indigo-400">
          <div v-if="store.isLoading" class="flex items-center">
            <div class="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-2"></div>
            <span>Updating...</span>
          </div>
          <div v-else>
            Last updated: {{ new Date().toLocaleTimeString() }}
          </div>
        </div>
      </div>

      <!-- Main content -->
      <div class="flex-1 overflow-auto">
        <main class="p-6">
          <RouterView v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </RouterView>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
