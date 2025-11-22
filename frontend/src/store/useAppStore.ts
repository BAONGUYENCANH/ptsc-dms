import { create } from 'zustand';

export interface FilterState {
  discipline: string | null;
  status: string | null;
  isOverdue: boolean | null;
  picPtsc: Set<string>; // Multiple PIC selection
  searchQuery: string;
}

interface AppState {
  filters: FilterState;
  setFilter: (key: keyof FilterState, value: any) => void;
  resetFilters: () => void;
  setSearchQuery: (query: string) => void;
  setPicFilter: (pics: Set<string>) => void;
}

export const useAppStore = create<AppState>((set) => ({
  filters: {
    discipline: null,
    status: null,
    isOverdue: null,
    picPtsc: new Set<string>(),
    searchQuery: '',
  },
  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value },
    })),
  resetFilters: () =>
    set(() => ({
      filters: {
        discipline: null,
        status: null,
        isOverdue: null,
        picPtsc: new Set<string>(),
        searchQuery: '',
      },
    })),
  setSearchQuery: (query) =>
    set((state) => ({
      filters: { ...state.filters, searchQuery: query },
    })),
  setPicFilter: (pics) =>
    set((state) => ({
      filters: { ...state.filters, picPtsc: pics },
    })),
}));
