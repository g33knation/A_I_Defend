import { create } from 'zustand';

export interface Event {
  id: string;
  type: string;
  source: string;
  created_at: string;
  payload?: any;
}

export interface Detection {
  id: string;
  summary: string;
  type: string;
  status: string;
  timestamp: string;
  created_at: string;
  feedback?: string;
  ai_output?: any;
  category?: string;
}

export interface Stats {
  totalEvents: number;
  openDetections: number;
  threatsBlocked: number;
  falsePositives: number;
}

export interface DefenseAction {
  id: number;
  action_type: string;
  target: string;
  reason: string;
  executed_by: string;
  status: string;
  created_at: string;
  rolled_back_at?: string | null;
  event_type?: string;
  detection_summary?: string;
  metadata?: any;
}

export interface DefenseStats {
  actions_last_24h: number;
  active_ip_blocks: number;
  by_type_status: Array<{
    action_type: string;
    status: string;
    count: number;
  }>;
}

export interface Scan {
  scan_id: string;
  status: string;
  start_time: string;
  end_time?: string;
  results?: any;
  error?: string;
}

export interface Agent {
  agent_id: string;
  hostname: string;
  ip_address: string;
  capabilities: string[];
  status: string;
  health: 'online' | 'stale' | 'offline';
  latency: number;
  last_heartbeat: string;
  last_scan_time?: string;
  registered_at: string;
  current_assignment?: string;
  metrics?: any;
  metadata?: any;
}

interface DefenseState {
  events: Event[];
  detections: Detection[];
  scans: Scan[];
  agents: Agent[];
  defenseActions: DefenseAction[];
  defenseStats: DefenseStats | null;
  defenseConfig: Record<string, any>;
  isLoading: boolean;
  error: string | null;
  stats: Stats;
  fetchEvents: () => Promise<void>;
  fetchDetections: () => Promise<void>;
  submitFeedback: (detectionId: string, feedback: string) => Promise<void>;
  purgeDetections: () => Promise<void>;
  startScan: (scanners: string[], config?: any) => Promise<string>;
  fetchScans: () => Promise<void>;
  getScanResult: (scanId: string) => Promise<Scan>;
  fetchAgents: () => Promise<void>;
  fetchDefenseActions: (status?: string) => Promise<void>;
  fetchDefenseStats: () => Promise<void>;
  fetchDefenseConfig: () => Promise<void>;
  updateDefenseConfig: (key: string, value: any) => Promise<void>;
  rollbackDefenseAction: (actionId: number) => Promise<void>;
  deployScan: (agentId: string, target: string, scanners: string[], paths?: string[]) => Promise<void>;
  registerAgent: (agentId: string, type: string, capabilities: string[]) => Promise<void>;
  purgeEvents: () => Promise<void>;
  models: string[];
  selectedModel: string;
  fetchModels: () => Promise<void>;
  setSelectedModel: (model: string) => void;
  askAI: (query: string, model: string) => Promise<string>;
  // Threat Monitor Stats
  getThreatLevel: () => 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  getActiveThreatsCount: () => number;
  getThreatStats: () => { critical: number; warning: number; info: number };
}

const API_BASE_URL = import.meta.env.VITE_API_URL || (window.location.port === '8002'
  ? 'http://localhost:8000'
  : window.location.origin);

// Nervous System Security: Formalize trust between Brain and Legs/Frontend
const BRAIN_API_KEY = "octopus-nervous-system-secret";
const AUTH_HEADERS = {
  'X-API-Key': BRAIN_API_KEY,
  'Content-Type': 'application/json'
};

export const useDefenseStore = create<DefenseState>((set, get) => ({
  events: [],
  detections: [],
  scans: [],
  agents: [],
  defenseActions: [],
  defenseStats: null,
  defenseConfig: {},
  isLoading: false,
  error: null,
  stats: {
    totalEvents: 0,
    openDetections: 0,
    threatsBlocked: 0,
    falsePositives: 0,
  },

  fetchEvents: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE_URL}/events`, {
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to fetch events');
      const data = await response.json();
      set({
        events: data,
        isLoading: false,
        stats: {
          ...get().stats,
          totalEvents: data.length,
        }
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Unknown error',
        isLoading: false
      });
    }
  },

  fetchDetections: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE_URL}/detections`, {
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to fetch detections');
      const data = await response.json();

      const openDetections = data.filter((d: any) => !d.feedback).length;
      const threatsBlocked = data.filter((d: any) => d.feedback === 'confirmed_threat').length;
      const falsePositives = data.filter((d: any) => d.feedback === 'false_positive').length;

      set({
        detections: data,
        isLoading: false,
        stats: {
          ...get().stats,
          openDetections,
          threatsBlocked,
          falsePositives,
        }
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Unknown error',
        isLoading: false
      });
    }
  },

  submitFeedback: async (detectionId: string, feedback: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/feedback`, {
        method: 'POST',
        headers: AUTH_HEADERS,
        body: JSON.stringify({ detection_id: parseInt(detectionId), feedback }),
      });
      if (!response.ok) throw new Error('Failed to submit feedback');
      await get().fetchDetections();
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  purgeDetections: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/detections`, {
        method: 'DELETE',
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to purge detections');
      await get().fetchDetections();
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  startScan: async (scanners: string[], config: any = {}) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/scans/start`, {
        method: 'POST',
        headers: AUTH_HEADERS,
        body: JSON.stringify({ scanners, config }),
      });
      if (!response.ok) throw new Error('Failed to start scan');
      const data = await response.json();
      return data.scan_id;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
      throw error;
    }
  },

  fetchScans: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/scans/`, {
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to fetch scans');
      const data = await response.json();
      set({ scans: data });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  getScanResult: async (scanId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/scans/${scanId}`, {
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to fetch scan result');
      return await response.json();
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
      throw error;
    }
  },

  fetchAgents: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/`, {
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to fetch agents');
      const data = await response.json();
      set({ agents: data });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  fetchDefenseActions: async (status?: string) => {
    try {
      const url = status && status !== 'all'
        ? `${API_BASE_URL}/api/defense/actions?status=${status}`
        : `${API_BASE_URL}/api/defense/actions`;
      const response = await fetch(url, {
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to fetch defense actions');
      const data = await response.json();
      set({ defenseActions: data });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  fetchDefenseStats: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/defense/stats`, {
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to fetch defense stats');
      const data = await response.json();
      set({ defenseStats: data });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  fetchDefenseConfig: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/defense/config`, {
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to fetch defense config');
      const data = await response.json();
      set({ defenseConfig: data });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  updateDefenseConfig: async (key: string, value: any) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/defense/config`, {
        method: 'PUT',
        headers: AUTH_HEADERS,
        body: JSON.stringify({ key, value }),
      });
      if (!response.ok) throw new Error('Failed to update defense config');
      await get().fetchDefenseConfig();
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  rollbackDefenseAction: async (actionId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/defense/actions/${actionId}/rollback`, {
        method: 'POST',
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to rollback defense action');
      await Promise.all([
        get().fetchDefenseActions(),
        get().fetchDefenseStats()
      ]);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  deployScan: async (agentId: string, target: string, scanners: string[], paths: string[] = []) => {
    try {
      // For malware scanner, we might have multiple paths
      // If paths are provided, use them. Otherwise use target as a single item list if present
      let targets = paths.length > 0 ? paths : (target ? [target] : []);

      // If we have both target input AND paths (e.g. custom path + checkboxes), combine them
      if (target && paths.length > 0 && !paths.includes(target)) {
        targets.push(target);
      }

      const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/assign`, {
        method: 'POST',
        headers: AUTH_HEADERS,
        body: JSON.stringify({
          targets: targets,
          scanners: scanners,
          config: {
            // We can pass extra config here if needed
          },
          priority: 5 // Default priority
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to assign task');
      }

      // Refresh agents to show updated status
      await get().fetchAgents();
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
      throw error;
    }
  },

  registerAgent: async (agentId: string, type: string, capabilities: string[]) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/register`, {
        method: 'POST',
        headers: AUTH_HEADERS,
        body: JSON.stringify({
          agent_id: agentId,
          hostname: agentId, // Use agentId as hostname for manual registration
          ip_address: '127.0.0.1',
          capabilities: capabilities,
          metadata: { type }
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to register agent');
      }

      await get().fetchAgents();
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
      throw error;
    }
  },

  purgeEvents: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/events`, {
        method: 'DELETE',
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (!response.ok) throw new Error('Failed to purge events');
      await get().fetchEvents();
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  models: [],
  selectedModel: 'hermes3:latest', // Default
  fetchModels: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/models`, {
        headers: { 'X-API-Key': BRAIN_API_KEY }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.models && data.models.length > 0) {
          set({ models: data.models });

          // Auto-select first model if current selection is invalid or empty
          const current = get().selectedModel;
          if (!current || !data.models.includes(current)) {
            set({ selectedModel: data.models[0] });
          }
        } else {
          // If no models available, empty the list and clear selection
          set({ models: [], selectedModel: '' });
        }
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  },
  setSelectedModel: (model: string) => set({ selectedModel: model }),

  askAI: async (query: string, model: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: AUTH_HEADERS,
        body: JSON.stringify({ query, model }),
      });
      if (!response.ok) throw new Error('Failed to get AI response');
      const data = await response.json();
      return data.response;
    } catch (error) {
      console.error('AI Error:', error);
      throw error;
    }
  },

  // Threat Monitor Statistics
  getThreatLevel: () => {
    const detections = get().detections;
    if (detections.length === 0) return 'LOW';

    // Calculate average score from detections with scores
    const scores = detections
      .map(d => d.ai_output?.score || 0)
      .filter(s => s > 0);

    if (scores.length === 0) return 'LOW';

    const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    const maxScore = Math.max(...scores);

    // Determine threat level based on max score and count of high-score detections
    const highScoreCount = scores.filter(s => s >= 0.7).length;

    if (maxScore >= 0.8 && highScoreCount >= 3) return 'CRITICAL';
    if (maxScore >= 0.7 || (avgScore >= 0.5 && detections.length >= 5)) return 'HIGH';
    if (maxScore >= 0.5 || avgScore >= 0.3) return 'MEDIUM';
    return 'LOW';
  },

  getActiveThreatsCount: () => {
    const detections = get().detections;
    // Count detections without feedback (unresolved) with score > 0.5
    return detections.filter(d => !d.feedback && (d.ai_output?.score || 0) > 0.5).length;
  },

  getThreatStats: () => {
    const detections = get().detections;
    return {
      critical: detections.filter(d => (d.ai_output?.score || 0) >= 0.7 && !d.feedback).length,
      warning: detections.filter(d => {
        const score = d.ai_output?.score || 0;
        return score >= 0.4 && score < 0.7 && !d.feedback;
      }).length,
      info: detections.filter(d => (d.ai_output?.score || 0) < 0.4 && !d.feedback).length,
    };
  },
}));
