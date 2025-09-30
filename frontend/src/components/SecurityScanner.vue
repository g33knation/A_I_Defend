<template>
  <div class="scanner-container">
    <div class="scanner-header">
      <h2>Security Scanner</h2>
      <div class="scanner-actions">
        <button 
          @click="startScan" 
          :disabled="isScanning" 
          class="btn btn-primary"
        >
          {{ isScanning ? 'Scanning...' : 'Run Security Scan' }}
        </button>
        
        <div class="scanner-options">
          <label>
            <input type="checkbox" v-model="scanOptions.nmap" :disabled="isScanning">
            Nmap
          </label>
          <label>
            <input type="checkbox" v-model="scanOptions.lynis" :disabled="isScanning">
            Lynis
          </label>
          <label>
            <input type="checkbox" v-model="scanOptions.clamav" :disabled="isScanning">
            ClamAV
          </label>
          <label>
            <input type="checkbox" v-model="scanOptions.chkrootkit" :disabled="isScanning">
            Chkrootkit
          </label>
          <label>
            <input type="checkbox" v-model="scanOptions.rkhunter" :disabled="isScanning">
            RKHunter
          </label>
          <label>
            <input type="checkbox" v-model="scanOptions.yara" :disabled="isScanning">
            YARA
          </label>
          <label>
            <input type="checkbox" v-model="scanOptions.suricata" :disabled="isScanning">
            Suricata
          </label>
        </div>
      </div>
    </div>
    
    <div v-if="activeScan" class="scan-details">
      <div class="scan-header">
        <h3>Scan #{{ activeScan.id }}</h3>
        <span :class="['status-badge', activeScan.status]">
          {{ activeScan.status }}
        </span>
        <span class="scan-time">
          Started: {{ formatTime(activeScan.startTime) }}
          <span v-if="activeScan.endTime">
            | Duration: {{ formatDuration(activeScan.startTime, activeScan.endTime) }}
          </span>
        </span>
      </div>
      
      <div v-if="activeScan.error" class="error-message">
        <h4>Error:</h4>
        <pre>{{ activeScan.error }}</pre>
      </div>
      
      <div v-if="activeScan.results" class="scan-results">
        <div class="results-summary">
          <div class="summary-item">
            <span class="summary-count">{{ activeScan.results.length }}</span>
            <span class="summary-label">Total Findings</span>
          </div>
          <div class="summary-item" v-if="activeScan.results.critical > 0">
            <span class="summary-count critical">{{ activeScan.results.critical }}</span>
            <span class="summary-label">Critical</span>
          </div>
          <div class="summary-item" v-if="activeScan.results.high > 0">
            <span class="summary-count high">{{ activeScan.results.high }}</span>
            <span class="summary-label">High</span>
          </div>
          <div class="summary-item" v-if="activeScan.results.medium > 0">
            <span class="summary-count medium">{{ activeScan.results.medium }}</span>
            <span class="summary-label">Medium</span>
          </div>
          <div class="summary-item" v-if="activeScan.results.low > 0">
            <span class="summary-count low">{{ activeScan.results.low }}</span>
            <span class="summary-label">Low</span>
          </div>
        </div>
        
        <div class="findings-list">
          <div v-for="(finding, index) in activeScan.results" :key="index" class="finding-item">
            <div class="finding-header" @click="toggleFinding(index)">
              <span class="finding-severity" :class="finding.severity">
                {{ finding.severity }}
              </span>
              <span class="finding-title">{{ finding.title }}</span>
              <span class="finding-scanner">{{ finding.scanner }}</span>
              <span class="finding-time">{{ formatTime(finding.timestamp) }}</span>
              <span class="finding-toggle">
                {{ expandedFindings.includes(index) ? '−' : '+' }}
              </span>
            </div>
            <div v-if="expandedFindings.includes(index)" class="finding-details">
              <pre>{{ JSON.stringify(finding.details, null, 2) }}</pre>
              <div class="finding-actions">
                <button class="btn btn-sm" @click="dismissFinding(finding.id)">
                  Dismiss
                </button>
                <button class="btn btn-sm btn-primary" @click="investigateFinding(finding)">
                  Investigate
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else-if="activeScan.status === 'completed'" class="no-results">
        No security issues found.
      </div>
      
      <div v-else class="scan-progress">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: scanProgress + '%' }"
          ></div>
        </div>
        <div class="progress-text">
          Scanning... {{ scanProgress }}%
        </div>
      </div>
    </div>
    
    <div v-if="scanHistory.length > 0" class="scan-history">
      <h3>Scan History</h3>
      <table class="history-table">
        <thead>
          <tr>
            <th>Scan ID</th>
            <th>Status</th>
            <th>Started</th>
            <th>Duration</th>
            <th>Findings</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="scan in scanHistory" :key="scan.id">
            <td>{{ scan.id.substring(0, 8) }}...</td>
            <td>
              <span :class="['status-badge', scan.status]">
                {{ scan.status }}
              </span>
            </td>
            <td>{{ formatTime(scan.startTime) }}</td>
            <td>
              {{ scan.endTime ? formatDuration(scan.startTime, scan.endTime) : 'In progress' }}
            </td>
            <td>
              <span v-if="scan.results">
                {{ scan.results.length }} findings
              </span>
              <span v-else>-</span>
            </td>
            <td>
              <button 
                class="btn btn-sm" 
                @click="viewScan(scan.id)"
                :disabled="scan.status === 'running'"
              >
                View
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'vue-toastification';

const toast = useToast();
const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// State
const isScanning = ref(false);
const activeScan = ref(null);
const scanHistory = ref([]);
const expandedFindings = ref([]);
const scanProgress = ref(0);
const scanOptions = ref({
  nmap: true,
  lynis: true,
  clamav: true,
  chkrootkit: true,
  rkhunter: true,
  yara: true,
  suricata: true
});

// Computed
const selectedScanners = computed(() => {
  return Object.entries(scanOptions.value)
    .filter(([_, isSelected]) => isSelected)
    .map(([scanner]) => scanner);
});

// Methods
const startScan = async () => {
  if (isScanning.value) return;
  
  try {
    isScanning.value = true;
    scanProgress.value = 0;
    
    const response = await fetch(`${apiBaseUrl}/api/scans/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        scanners: selectedScanners.value,
        config: {
          // Add any additional scan configuration here
        }
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to start scan');
    }
    
    const data = await response.json();
    
    // Create a new scan entry
    const newScan = {
      id: data.scan_id,
      status: 'running',
      startTime: new Date().toISOString(),
      endTime: null,
      results: null,
      error: null
    };
    
    // Add to history and set as active
    scanHistory.value.unshift(newScan);
    activeScan.value = newScan;
    
    // Poll for updates
    pollScanStatus(data.scan_id);
    
    toast.success('Security scan started');
    
  } catch (error) {
    console.error('Error starting scan:', error);
    toast.error(`Failed to start scan: ${error.message}`);
    isScanning.value = false;
  }
};

const pollScanStatus = async (scanId) => {
  try {
    const response = await fetch(`${apiBaseUrl}/api/scans/${scanId}`);
    const data = await response.json();
    
    // Update scan status
    const scanIndex = scanHistory.value.findIndex(s => s.id === scanId);
    if (scanIndex !== -1) {
      const updatedScan = {
        ...scanHistory.value[scanIndex],
        status: data.status,
        endTime: data.end_time || null,
        results: data.results || null,
        error: data.error || null
      };
      
      scanHistory.value[scanIndex] = updatedScan;
      
      if (activeScan.value?.id === scanId) {
        activeScan.value = updatedScan;
      }
      
      // Update progress
      if (data.status === 'running') {
        // Simple progress simulation - in a real app, you'd get this from the API
        const progress = Math.min(scanProgress.value + 10, 90);
        scanProgress.value = progress;
        
        // Continue polling if still running
        if (progress < 90) {
          setTimeout(() => pollScanStatus(scanId), 2000);
        } else {
          // Final check after a delay
          setTimeout(() => pollScanStatus(scanId), 1000);
        }
      } else if (data.status === 'completed') {
        scanProgress.value = 100;
        isScanning.value = false;
        toast.success('Security scan completed');
      } else if (data.status === 'failed') {
        isScanning.value = false;
        scanProgress.value = 0;
        toast.error('Security scan failed');
      }
    }
  } catch (error) {
    console.error('Error polling scan status:', error);
    // Retry after a delay
    setTimeout(() => pollScanStatus(scanId), 2000);
  }
};

const viewScan = (scanId) => {
  const scan = scanHistory.value.find(s => s.id === scanId);
  if (scan) {
    activeScan.value = { ...scan };
    expandedFindings.value = [];
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
};

const toggleFinding = (index) => {
  const idx = expandedFindings.value.indexOf(index);
  if (idx === -1) {
    expandedFindings.value.push(index);
  } else {
    expandedFindings.value.splice(idx, 1);
  }
};

const dismissFinding = (findingId) => {
  // In a real app, you would send this to the backend
  console.log('Dismiss finding:', findingId);
  toast.info('Finding dismissed');
};

const investigateFinding = (finding) => {
  // In a real app, you would navigate to an investigation page
  console.log('Investigate finding:', finding);
  toast.info('Opening investigation...');
};

const formatTime = (timestamp) => {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleString();
};

const formatDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return 'N/A';
  
  const start = new Date(startTime);
  const end = new Date(endTime);
  const diffMs = end - start;
  
  const seconds = Math.floor((diffMs / 1000) % 60);
  const minutes = Math.floor((diffMs / (1000 * 60)) % 60);
  const hours = Math.floor((diffMs / (1000 * 60 * 60)) % 24);
  
  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  parts.push(`${seconds}s`);
  
  return parts.join(' ');
};

// Load scan history on component mount
onMounted(async () => {
  try {
    const response = await fetch(`${apiBaseUrl}/api/scans`);
    if (response.ok) {
      const data = await response.json();
      scanHistory.value = data.map(scan => ({
        id: scan.scan_id,
        status: scan.status,
        startTime: scan.start_time,
        endTime: scan.end_time,
        results: scan.results ? scan.results.results || [] : null,
        error: scan.error
      }));
      
      // Set the most recent scan as active if there is one
      if (scanHistory.value.length > 0) {
        activeScan.value = { ...scanHistory.value[0] };
      }
    }
  } catch (error) {
    console.error('Error loading scan history:', error);
    toast.error('Failed to load scan history');
  }
});
</script>

<style scoped>
.scanner-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.scanner-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.scanner-actions {
  display: flex;
  gap: 20px;
  align-items: center;
}

.scanner-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  font-size: 14px;
}

.scanner-options label {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  padding: 5px 10px;
  background: #f5f5f5;
  border-radius: 4px;
  user-select: none;
}

.scanner-options input[type="checkbox"] {
  margin: 0;
}

.scan-details, .scan-history {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 30px;
}

.scan-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
}

.status-badge.running {
  background-color: #ffc107;
  color: #000;
}

.status-badge.completed {
  background-color: #4caf50;
  color: white;
}

.status-badge.failed {
  background-color: #f44336;
  color: white;
}

.scan-time {
  margin-left: auto;
  color: #666;
  font-size: 14px;
}

.results-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 6px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 80px;
}

.summary-count {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.summary-count.critical { color: #f44336; }
.summary-count.high { color: #ff9800; }
.summary-count.medium { color: #ffc107; }
.summary-count.low { color: #4caf50; }

.summary-label {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.findings-list {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.finding-item {
  border-bottom: 1px solid #eee;
}

.finding-item:last-child {
  border-bottom: none;
}

.finding-header {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  background: #fafafa;
  cursor: pointer;
  transition: background 0.2s;
}

.finding-header:hover {
  background: #f0f0f0;
}

.finding-severity {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
  min-width: 70px;
  text-align: center;
}

.finding-severity.critical { background-color: #ffebee; color: #c62828; }
.finding-severity.high { background-color: #fff3e0; color: #e65100; }
.finding-severity.medium { background-color: #fffde7; color: #f57f17; }
.finding-severity.low { background-color: #e8f5e9; color: #2e7d32; }
.finding-severity.info { background-color: #e3f2fd; color: #1565c0; }

.finding-title {
  flex: 1;
  margin: 0 15px;
  font-weight: 500;
}

.finding-scanner {
  padding: 2px 8px;
  background: #e0e0e0;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.finding-time {
  margin: 0 15px;
  color: #666;
  font-size: 12px;
  white-space: nowrap;
}

.finding-toggle {
  width: 20px;
  text-align: center;
  font-weight: bold;
  color: #666;
}

.finding-details {
  padding: 15px;
  background: white;
  border-top: 1px solid #eee;
}

.finding-details pre {
  margin: 0 0 15px 0;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
}

.finding-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
  margin-top: 10px;
}

.scan-progress {
  margin-top: 20px;
  text-align: center;
}

.progress-bar {
  height: 10px;
  background: #e0e0e0;
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: #4caf50;
  width: 0%;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: #666;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.history-table th,
.history-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.history-table th {
  font-weight: 600;
  color: #333;
  background: #f5f5f5;
}

.history-table tbody tr:hover {
  background: #f9f9f9;
}

.history-table .status-badge {
  padding: 2px 8px;
  font-size: 12px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #2196f3;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #1976d2;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 13px;
}

.error-message {
  padding: 15px;
  background: #ffebee;
  border-left: 4px solid #f44336;
  margin-bottom: 20px;
  border-radius: 0 4px 4px 0;
}

.error-message h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #c62828;
}

.error-message pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: monospace;
  font-size: 13px;
}

.no-results {
  text-align: center;
  padding: 30px;
  color: #666;
  font-style: italic;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .scanner-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .scanner-actions {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .scanner-options {
    width: 100%;
    overflow-x: auto;
    padding-bottom: 10px;
  }
  
  .scan-header {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .scan-time {
    margin-left: 0;
    width: 100%;
  }
  
  .results-summary {
    overflow-x: auto;
    padding: 10px 5px;
  }
  
  .summary-item {
    min-width: 60px;
  }
  
  .finding-header {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .finding-time {
    margin-left: auto;
  }
  
  .history-table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }
}
</style>
