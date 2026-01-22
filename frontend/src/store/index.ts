import { create } from 'zustand';
import type { Stats, RecentScan } from '../types';

interface AppState {
    stats: Stats | null;
    recentScans: RecentScan[];
    isLoading: boolean;
    error: string | null;
    setStats: (stats: Stats) => void;
    setRecentScans: (scans: RecentScan[]) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
    stats: null,
    recentScans: [],
    isLoading: false,
    error: null,
    setStats: (stats) => set({ stats }),
    setRecentScans: (recentScans) => set({ recentScans }),
    setLoading: (isLoading) => set({ isLoading }),
    setError: (error) => set({ error }),
}));
