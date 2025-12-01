import axios from 'axios';
import type { 
  AuthResponse, 
  User, 
  UserProfile, 
  ScoringCriteria, 
  Job, 
  BlacklistEntry,
  Application
} from '../types';
import { useAuthStore } from '../store/authStore';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Use zustand logout to clear both token AND isAuthenticated state
      // This prevents the redirect loop caused by persisted isAuthenticated=true
      useAuthStore.getState().logout();
      // No hard redirect needed - React Router will handle it
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  register: async (data: { 
    email: string; 
    password: string; 
    first_name: string; 
    last_name: string; 
  }): Promise<AuthResponse> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },
  
  login: async (data: { email: string; password: string }): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', data);
    return response.data;
  },
  
  me: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Profile API
export const profileApi = {
  get: async (): Promise<UserProfile | null> => {
    const response = await api.get('/profile/');
    return response.data;
  },
  
  uploadCV: async (file: File, description?: string): Promise<{ profile: UserProfile }> => {
    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('user_description', description);
    }
    const response = await api.post('/profile/upload-cv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  update: async (data: Partial<UserProfile>): Promise<UserProfile> => {
    const response = await api.put('/profile/', data);
    return response.data;
  },
  
  updateDescription: async (description: string): Promise<UserProfile> => {
    const response = await api.put('/profile/description', null, {
      params: { ai_description: description },
    });
    return response.data;
  },
  
  regenerateDescription: async (): Promise<UserProfile> => {
    const response = await api.post('/profile/regenerate-description');
    return response.data;
  },
  
  confirm: async (): Promise<{ message: string; next_step: string }> => {
    const response = await api.post('/profile/confirm');
    return response.data;
  },
};

// Criteria API
export const criteriaApi = {
  getAll: async (): Promise<{ criteria: ScoringCriteria[]; total: number }> => {
    const response = await api.get('/criteria/');
    return response.data;
  },
  
  get: async (type: string): Promise<ScoringCriteria> => {
    const response = await api.get(`/criteria/${type}`);
    return response.data;
  },
  
  update: async (type: string, data: Partial<ScoringCriteria>): Promise<ScoringCriteria> => {
    const response = await api.put(`/criteria/${type}`, data);
    return response.data;
  },
  
  updateAll: async (updates: Partial<ScoringCriteria>[]): Promise<{ criteria: ScoringCriteria[] }> => {
    const response = await api.put('/criteria/', updates);
    return response.data;
  },
  
  addSubCriteria: async (type: string, name: string, importance: number): Promise<ScoringCriteria> => {
    const response = await api.post(`/criteria/${type}/sub`, { name, importance });
    return response.data;
  },
  
  removeSubCriteria: async (type: string, subName: string): Promise<ScoringCriteria> => {
    const response = await api.delete(`/criteria/${type}/sub/${subName}`);
    return response.data;
  },
  
  reset: async (): Promise<{ message: string }> => {
    const response = await api.post('/criteria/reset');
    return response.data;
  },
};

// Jobs API
export const jobsApi = {
  list: async (params?: { 
    skip?: number; 
    limit?: number; 
    search?: string;
  }): Promise<Job[]> => {
    const response = await api.get('/jobs/', { params });
    return response.data;
  },
  
  get: async (id: number): Promise<Job> => {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },
  
  search: async (data: {
    keywords: string;
    location?: string;
    platforms?: string[];
    remote_only?: boolean;
    experience_level?: string;
    save_results?: boolean;
  }): Promise<{ jobs: Job[]; total: number; platforms_searched: string[] }> => {
    const response = await api.post('/search/jobs', data);
    return response.data;
  },
  
  generateCoverLetter: async (jobId: number): Promise<{ cover_letter: string }> => {
    const response = await api.post(`/jobs/${jobId}/cover-letter`);
    return response.data;
  },
};

// Blacklist API
export const blacklistApi = {
  list: async (): Promise<{ items: BlacklistEntry[]; total: number }> => {
    const response = await api.get('/blacklist/');
    return response.data;
  },
  
  add: async (data: { 
    company_name: string; 
    company_id?: number; 
    reason?: string; 
  }): Promise<BlacklistEntry> => {
    const response = await api.post('/blacklist/', data);
    return response.data;
  },
  
  remove: async (id: number): Promise<{ message: string }> => {
    const response = await api.delete(`/blacklist/${id}`);
    return response.data;
  },
  
  check: async (companyName: string): Promise<{ 
    company_name: string; 
    is_blacklisted: boolean; 
    reason?: string; 
  }> => {
    const response = await api.get(`/blacklist/check/${companyName}`);
    return response.data;
  },
};

// Applications API
export const applicationsApi = {
  list: async (params?: { status?: string }): Promise<{ applications: Application[]; total: number }> => {
    const response = await api.get('/applications/', { params });
    return response.data;
  },
  
  get: async (id: number): Promise<Application> => {
    const response = await api.get(`/applications/${id}`);
    return response.data;
  },
  
  create: async (data: { job_id: number; status?: string; notes?: string }): Promise<Application> => {
    const response = await api.post('/applications/', data);
    return response.data;
  },
  
  update: async (id: number, data: Partial<Application>): Promise<Application> => {
    const response = await api.put(`/applications/${id}`, data);
    return response.data;
  },
  
  delete: async (id: number): Promise<void> => {
    await api.delete(`/applications/${id}`);
  },
  
  markApplied: async (id: number): Promise<Application> => {
    const response = await api.post(`/applications/${id}/apply`);
    return response.data;
  },
  
  getStats: async (): Promise<{ [key: string]: number }> => {
    const response = await api.get('/applications/stats');
    return response.data;
  },
};

// Scoring API
export const scoringApi = {
  scoreJob: async (jobId: number): Promise<{ score: number; breakdown: Record<string, number> }> => {
    const response = await api.post(`/scoring/job/${jobId}`);
    return response.data;
  },
};

// V2 Scoring Preferences API
export interface ScoringPreferences {
  id: number;
  preferred_city: string;
  min_salary: number;
  target_seniority: 'junior' | 'mid' | 'senior' | 'head';
  priority_skills: string[];
  trusted_sources: Record<string, boolean>;
  attractiveness_keywords: {
    high: string[];
    medium: string[];
    custom: string[];
  };
}

export interface ScoreBreakdown {
  role: { points: number; max: number; level: string; label: string; details: string };
  geography: { points: number; max: number; type: string; details: string };
  salary: { points: number; max: number; salary: number | null; details: string };
  skills: { points: number; max: number; matched: number; matched_skills: string[]; details: string };
  attractiveness: { points: number; max: number; level: string; matched_keywords: string[]; details: string };
  penalties: { points: number; max: number; reasons: string[]; details: string };
}

export interface ScoredJob {
  job: Record<string, any>;
  score: number;
  breakdown: ScoreBreakdown;
}

export const scoringPreferencesApi = {
  get: async (): Promise<ScoringPreferences> => {
    const response = await api.get('/criteria/preferences/v2');
    return response.data;
  },
  
  update: async (data: Partial<Omit<ScoringPreferences, 'id'>>): Promise<ScoringPreferences> => {
    const response = await api.put('/criteria/preferences/v2', data);
    return response.data;
  },
  
  toggleSource: async (source: string, trusted: boolean): Promise<ScoringPreferences> => {
    const response = await api.put(`/criteria/preferences/v2/sources/${source}`, { trusted });
    return response.data;
  },
  
  addSkill: async (name: string): Promise<ScoringPreferences> => {
    const response = await api.post('/criteria/preferences/v2/skills', { name, importance: 50 });
    return response.data;
  },
  
  removeSkill: async (skillName: string): Promise<ScoringPreferences> => {
    const response = await api.delete(`/criteria/preferences/v2/skills/${encodeURIComponent(skillName)}`);
    return response.data;
  },
  
  reset: async (): Promise<ScoringPreferences> => {
    const response = await api.post('/criteria/preferences/v2/reset');
    return response.data;
  },
};

// V2 Scored Jobs API
export const scoredJobsApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    title?: string;
    location?: string;
    remote_type?: string;
    min_score?: number;
  }): Promise<{ jobs: ScoredJob[]; total: number; skip: number; limit: number }> => {
    const response = await api.get('/jobs/scored/v2', { params });
    return response.data;
  },
  
  getScore: async (jobId: number): Promise<{ job_id: number; job_title: string; score: number; breakdown: ScoreBreakdown }> => {
    const response = await api.get(`/jobs/${jobId}/score/v2`);
    return response.data;
  },
};

// Cover Letter API
export const coverLetterApi = {
  generate: async (jobId: number): Promise<{ cover_letter: string }> => {
    const response = await api.post(`/cover-letter/generate/${jobId}`);
    return response.data;
  },
};

// Saved Searches API
export interface SavedSearch {
  id: number;
  name: string;
  keywords: string;
  location: string;
  created_at: string;
  last_used_at: string;
}

export const savedSearchesApi = {
  list: async (): Promise<{ searches: SavedSearch[]; total: number }> => {
    const response = await api.get('/saved-searches/');
    return response.data;
  },
  
  save: async (data: { name: string; keywords: string; location: string }): Promise<SavedSearch> => {
    const response = await api.post('/saved-searches/', data);
    return response.data;
  },
  
  delete: async (id: number): Promise<void> => {
    await api.delete(`/saved-searches/${id}`);
  },
  
  markUsed: async (id: number): Promise<SavedSearch> => {
    const response = await api.put(`/saved-searches/${id}/use`);
    return response.data;
  },
};

// Combined API object for convenient imports
export const apiClient = {
  auth: authApi,
  profile: {
    getProfile: profileApi.get,
    uploadCV: profileApi.uploadCV,
    updateProfile: profileApi.update,
  },
  criteria: {
    list: async () => {
      const response = await criteriaApi.getAll();
      return response.criteria;
    },
    update: criteriaApi.update,
  },
  jobs: {
    list: jobsApi.list,
    get: jobsApi.get,
  },
  search: {
    search: async (params: { keywords: string; location?: string; remote_only?: boolean }) => {
      const response = await jobsApi.search(params);
      return response.jobs;
    },
  },
  blacklist: {
    list: async () => {
      const response = await blacklistApi.list();
      return response.items;
    },
    add: blacklistApi.add,
    remove: blacklistApi.remove,
  },
  scoring: scoringApi,
  coverLetter: coverLetterApi,
};

// Export both for flexibility
export { apiClient as api };
export default api;
