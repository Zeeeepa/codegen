import { useEffect, useRef } from 'react';
import { getAgentRun } from '../services/apiService';

const useAutoRefresh = (activeRuns, onUpdate, interval = 30000) => {
  const intervalRef = useRef(null);
  const isRefreshingRef = useRef(false);

  useEffect(() => {
    const refreshActiveRuns = async () => {
      if (isRefreshingRef.current || activeRuns.length === 0) {
        return;
      }

      isRefreshingRef.current = true;

      try {
        const updatedRuns = [];

        // Refresh each active run
        for (const run of activeRuns) {
          try {
            const updatedRun = await getAgentRun(run.id);
            updatedRuns.push(updatedRun);
          } catch (error) {
            console.error(`Failed to refresh run ${run.id}:`, error);
            // Keep the old run data if refresh fails
            updatedRuns.push(run);
          }
        }

        // Only call onUpdate if there are actual changes
        const hasChanges = updatedRuns.some((updatedRun, index) => {
          const originalRun = activeRuns[index];
          return JSON.stringify(updatedRun) !== JSON.stringify(originalRun);
        });

        if (hasChanges) {
          onUpdate(updatedRuns);
        }
      } catch (error) {
        console.error('Error refreshing active runs:', error);
      } finally {
        isRefreshingRef.current = false;
      }
    };

    // Clear existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Set up new interval if there are active runs
    if (activeRuns.length > 0) {
      intervalRef.current = setInterval(refreshActiveRuns, interval);

      // Do an immediate refresh
      refreshActiveRuns();
    }

    // Cleanup on unmount or when activeRuns changes
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [activeRuns, onUpdate, interval]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);
};

export default useAutoRefresh;

