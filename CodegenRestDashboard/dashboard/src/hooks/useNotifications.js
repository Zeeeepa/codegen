import { useEffect, useRef } from 'react';
import toast from 'react-hot-toast';

const useNotifications = (activeRuns) => {
  const previousRunsRef = useRef([]);

  useEffect(() => {
    const previousRuns = previousRunsRef.current;

    // Check for runs that have completed
    activeRuns.forEach(currentRun => {
      const previousRun = previousRuns.find(run => run.id === currentRun.id);

      if (previousRun) {
        // Check if run has transitioned from active to completed
        const wasActive = !previousRun.result && (
          previousRun.status === 'running' ||
          previousRun.status === 'in_progress' ||
          previousRun.status === 'pending'
        );

        const isCompleted = currentRun.result || (
          currentRun.status === 'completed' ||
          currentRun.status === 'success'
        );

        const isFailed = currentRun.status === 'failed';

        if (wasActive && (isCompleted || isFailed)) {
          // Show notification
          const status = isFailed ? 'failed' : 'completed';

          if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(`Agent Run ${currentRun.id} ${status}`, {
              body: `Run ${currentRun.id} has ${status}`,
              icon: '/favicon.ico',
              tag: `run-${currentRun.id}`
            });
          }

          // Show toast notification
          toast.success(`Agent Run ${currentRun.id} has ${status}!`, {
            duration: 5000,
            position: 'top-right',
          });
        }
      }
    });

    // Update previous runs reference
    previousRunsRef.current = [...activeRuns];
  }, [activeRuns]);

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);
};

export default useNotifications;

