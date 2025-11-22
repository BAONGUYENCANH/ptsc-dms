import { describe, it, expect, beforeEach } from 'vitest';
import { useAppStore } from './useAppStore';

describe('useAppStore', () => {
  beforeEach(() => {
    useAppStore.getState().resetFilters();
  });

  it('should set filter values correctly', () => {
    useAppStore.getState().setFilter('discipline', 'EE');
    expect(useAppStore.getState().filters.discipline).toBe('EE');

    useAppStore.getState().setFilter('isOverdue', true);
    expect(useAppStore.getState().filters.isOverdue).toBe(true);
  });

  it('should reset filters', () => {
    useAppStore.getState().setFilter('discipline', 'PL');
    useAppStore.getState().setFilter('status', 'Approved');
    
    useAppStore.getState().resetFilters();
    
    const filters = useAppStore.getState().filters;
    expect(filters.discipline).toBeNull();
    expect(filters.status).toBeNull();
  });

  it('should update search query', () => {
    useAppStore.getState().setSearchQuery('test doc');
    expect(useAppStore.getState().filters.searchQuery).toBe('test doc');
  });
});
