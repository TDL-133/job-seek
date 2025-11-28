import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, UserProfile } from '../types';
import { authApi, profileApi } from '../services/api';

interface AuthState {
  user: User | null;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  setProfile: (profile: UserProfile) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      profile: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login({ email, password });
          localStorage.setItem('access_token', response.access_token);
          set({ 
            user: response.user, 
            isAuthenticated: true, 
            isLoading: false 
          });
          // Fetch profile after login
          await get().fetchProfile();
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Login failed', 
            isLoading: false 
          });
          throw error;
        }
      },
      
      register: async (email: string, password: string, fullName: string) => {
        set({ isLoading: true, error: null });
        try {
          // Split full name into first and last name
          const nameParts = fullName.trim().split(' ');
          const firstName = nameParts[0] || '';
          const lastName = nameParts.slice(1).join(' ') || '';
          
          const response = await authApi.register({
            email,
            password,
            first_name: firstName,
            last_name: lastName,
          });
          localStorage.setItem('access_token', response.access_token);
          set({ 
            user: response.user, 
            isAuthenticated: true, 
            isLoading: false 
          });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Registration failed', 
            isLoading: false 
          });
          throw error;
        }
      },
      
      logout: () => {
        localStorage.removeItem('access_token');
        set({ 
          user: null, 
          profile: null, 
          isAuthenticated: false, 
          error: null 
        });
      },
      
      fetchUser: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ isAuthenticated: false });
          return;
        }
        
        set({ isLoading: true });
        try {
          const user = await authApi.me();
          set({ user, isAuthenticated: true, isLoading: false });
          await get().fetchProfile();
        } catch (error) {
          localStorage.removeItem('access_token');
          set({ 
            user: null, 
            isAuthenticated: false, 
            isLoading: false 
          });
        }
      },
      
      fetchProfile: async () => {
        try {
          const profile = await profileApi.get();
          set({ profile });
        } catch (error) {
          set({ profile: null });
        }
      },
      
      setProfile: (profile: UserProfile) => {
        set({ profile });
      },
      
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);
