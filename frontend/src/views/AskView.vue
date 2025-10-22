<script setup>
import { ref, onMounted } from 'vue';
import { useDefenseStore } from '@/stores/defense';

const store = useDefenseStore();
const query = ref('');
const response = ref('');
const isLoading = ref(false);
const error = ref('');
const chatHistory = ref([]);

const askAI = async () => {
  if (!query.value.trim()) return;
  
  const userMessage = { role: 'user', content: query.value };
  chatHistory.value = [...chatHistory.value, userMessage];
  
  const currentQuery = query.value;
  query.value = '';
  isLoading.value = true;
  error.value = '';
  
  try {
    const aiResponse = await store.askAI(currentQuery);
    chatHistory.value = [
      ...chatHistory.value, 
      { role: 'assistant', content: aiResponse.response || 'No response from AI' }
    ];
  } catch (err) {
    error.value = 'Failed to get response from AI. Please try again.';
    console.error('AI request failed:', err);
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
};

const scrollToBottom = () => {
  const chatContainer = document.getElementById('chat-container');
  if (chatContainer) {
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
};

const handleKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    askAI();
  }
};

onMounted(() => {
  // Load initial greeting
  chatHistory.value = [
    {
      role: 'assistant',
      content: 'Hello! I\'m your AI security assistant. How can I help you with your security monitoring today?'
    }
  ];
});
</script>

<template>
  <div class="flex flex-col h-full p-2">
    <div class="mb-2">
      <h1 class="text-lg font-bold text-gray-800">Ask AI Assistant</h1>
      <p class="text-[10px] text-gray-500">Get insights and recommendations about your security events</p>
    </div>

    <div class="flex-1 flex flex-col bg-white rounded-lg shadow overflow-hidden">
      <!-- Chat messages -->
      <div 
        id="chat-container"
        class="flex-1 p-2 overflow-y-auto"
      >
        <div class="space-y-2">
          <div 
            v-for="(message, index) in chatHistory" 
            :key="index"
            :class="{
              'flex justify-end': message.role === 'user',
              'flex justify-start': message.role === 'assistant'
            }"
          >
            <div 
              :class="{
                'bg-indigo-100 text-gray-800': message.role === 'assistant',
                'bg-indigo-600 text-white': message.role === 'user'
              }"
              class="max-w-3xl rounded-lg px-2 py-1 shadow-sm text-xs"
            >
              <div v-if="message.role === 'assistant'" class="flex items-start">
                <div class="flex-shrink-0 h-4 w-4 rounded-full bg-indigo-200 flex items-center justify-center mr-1">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-2.5 w-2.5 text-indigo-600" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="whitespace-pre-wrap">{{ message.content }}</div>
              </div>
              <div v-else class="whitespace-pre-wrap">{{ message.content }}</div>
            </div>
          </div>
          
          <div v-if="isLoading" class="flex justify-start">
            <div class="bg-indigo-100 rounded-lg px-2 py-1 shadow-sm">
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                <div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input area -->
      <div class="border-t border-gray-200 p-2">
        <div class="flex items-end space-x-1">
          <div class="flex-1 relative">
            <textarea
              v-model="query"
              @keydown="handleKeyDown"
              rows="1"
              class="block w-full rounded border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 resize-none text-xs py-1 px-2"
              placeholder="Ask me about security events..."
            ></textarea>
            <div class="absolute right-1 bottom-1 text-[9px] text-gray-400">
              <span>Enter</span>
            </div>
          </div>
          <button
            @click="askAI"
            :disabled="isLoading || !query.trim()"
            :class="{
              'bg-indigo-600 hover:bg-indigo-700': query.trim(),
              'bg-gray-300 cursor-not-allowed': !query.trim() || isLoading
            }"
            class="inline-flex items-center px-2 py-1 border border-transparent text-[10px] font-medium rounded shadow-sm text-white focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-indigo-500"
          >
            <svg v-if="isLoading" class="animate-spin -ml-1 mr-1 h-2.5 w-2.5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ isLoading ? 'Thinking...' : 'Send' }}</span>
          </button>
        </div>
        <p v-if="error" class="mt-1 text-[10px] text-red-600">{{ error }}</p>
      </div>
    </div>

    <!-- Suggested questions -->
    <div class="mt-2">
      <h3 class="text-[10px] font-medium text-gray-500 mb-1">SUGGESTED QUESTIONS</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-1.5">
        <button
          v-for="(question, index) in [
            'Show me recent high severity threats',
            'What\'s the most common detection type?',
            'How many false positives today?'
          ]"
          :key="index"
          @click="query = question; askAI()"
          class="text-left p-1.5 bg-white border border-gray-200 rounded shadow-sm hover:bg-gray-50 transition-colors text-[10px] text-gray-700"
        >
          {{ question }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar for chat container */
#chat-container::-webkit-scrollbar {
  width: 6px;
}

#chat-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

#chat-container::-webkit-scrollbar-thumb {
  background: #c7d2fe;
  border-radius: 3px;
}

#chat-container::-webkit-scrollbar-thumb:hover {
  background: #a5b4fc;
}
</style>
