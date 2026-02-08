import { useState, useEffect } from 'react';

const PINNED_RUNS_KEY = 'codegen-pinned-runs';

const usePinnedRuns = () => {
  const [pinnedRuns, setPinnedRuns] = useState(new Set());

  // Load pinned runs from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(PINNED_RUNS_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setPinnedRuns(new Set(parsed));
      }
    } catch (error) {
      console.error('Failed to load pinned runs:', error);
    }
  }, []);

  // Save pinned runs to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(PINNED_RUNS_KEY, JSON.stringify([...pinnedRuns]));
    } catch (error) {
      console.error('Failed to save pinned runs:', error);
    }
  }, [pinnedRuns]);

  const togglePin = (runId) => {
    setPinnedRuns(prev => {
      const newSet = new Set(prev);
      if (newSet.has(runId)) {
        newSet.delete(runId);
      } else {
        newSet.add(runId);
      }
      return newSet;
    });
  };

  const isPinned = (runId) => {
    return pinnedRuns.has(runId);
  };

  const clearAllPins = () => {
    setPinnedRuns(new Set());
  };

  return {
    pinnedRuns,
    togglePin,
    isPinned,
    clearAllPins
  };
};

export default usePinnedRuns;

