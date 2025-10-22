import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useDefenseStore = defineStore('defense', () => {
  const events = ref([]);
  const detections = ref([]);
  const isLoading = ref(false);
  const error = ref(null);
  const stats = ref({
    totalEvents: 0,
    openDetections: 0,
    threatsBlocked: 0,
    falsePositives: 0
  });

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  async function fetchEvents() {
    try {
      isLoading.value = true;
      const response = await fetch(`${API_BASE}/events`);
      const data = await response.json();
      events.value = data;
    } catch (err) {
      error.value = err.message;
      console.error('Error fetching events:', err);
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchDetections() {
    try {
      isLoading.value = true;
      const response = await fetch(`${API_BASE}/detections`);
      const data = await response.json();
      detections.value = data;
      updateStats(data);
    } catch (err) {
      error.value = err.message;
      console.error('Error fetching detections:', err);
    } finally {
      isLoading.value = false;
    }
  }

  async function submitFeedback(detectionId, feedback) {
    try {
      await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          detection_id: detectionId,
          feedback: feedback
        })
      });
      await fetchDetections(); // Refresh detections
    } catch (err) {
      error.value = err.message;
      console.error('Error submitting feedback:', err);
    }
  }

  async function askAI(query) {
    try {
      const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      return await response.json();
    } catch (err) {
      error.value = err.message;
      console.error('Error querying AI:', err);
      throw err;
    }
  }

  function updateStats(detections) {
    const openDets = detections.filter(d => !d.feedback || d.feedback === null);
    const confirmedThreats = detections.filter(d => d.feedback === 'confirmed_threat');
    const falsePos = detections.filter(d => d.feedback === 'false_positive');
    
    stats.value = {
      totalEvents: events.value.length,
      openDetections: openDets.length,
      threatsBlocked: confirmedThreats.length,
      falsePositives: falsePos.length
    };
  }

  return {
    events,
    detections,
    stats,
    isLoading,
    error,
    API_BASE,
    fetchEvents,
    fetchDetections,
    submitFeedback,
    askAI
  };
});
