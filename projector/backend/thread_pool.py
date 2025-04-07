import logging
import threading
import queue
import time
from typing import Callable, Any, List, Dict

class ThreadPool:
    """Thread pool for concurrent task execution."""
    
    def __init__(self, max_threads: int = 10):
        """Initialize the thread pool.
        
        Args:
            max_threads: Maximum number of concurrent threads
        """
        self.max_threads = max(1, min(max_threads, 20))  # Limit between 1 and 20
        self.task_queue = queue.Queue()
        self.threads = []
        self.running = True
        self.logger = logging.getLogger(__name__)
        
        # Start worker threads
        for i in range(self.max_threads):
            thread = threading.Thread(target=self._worker, daemon=True)
            thread.start()
            self.threads.append(thread)
        
        self.logger.info(f"Thread pool initialized with {self.max_threads} workers")
    
    def _worker(self):
        """Worker thread that processes tasks from the queue."""
        while self.running:
            try:
                # Get a task from the queue with a timeout
                task, args, kwargs = self.task_queue.get(timeout=1.0)
                
                try:
                    # Execute the task
                    task(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error executing task: {e}")
                
                # Mark the task as done
                self.task_queue.task_done()
            
            except queue.Empty:
                # Queue is empty, just continue
                continue
            except Exception as e:
                self.logger.error(f"Error in worker thread: {e}")
    
    def submit(self, task: Callable, *args, **kwargs):
        """Submit a task to the thread pool.
        
        Args:
            task: The function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        if not self.running:
            self.logger.warning("Cannot submit task: thread pool is shutting down")
            return
        
        self.task_queue.put((task, args, kwargs))
    
    def wait_completion(self, timeout: float = None):
        """Wait for all tasks to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            True if all tasks completed, False if timeout occurred
        """
        try:
            self.task_queue.join(timeout=timeout)
            return True
        except queue.Empty:
            return False
    
    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool.
        
        Args:
            wait: If True, wait for all tasks to complete
        """
        self.running = False
        
        if wait:
            self.wait_completion()
        
        # Clear the queue
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
            except queue.Empty:
                break
        
        self.logger.info("Thread pool shutdown complete")
    
    def __del__(self):
        """Ensure thread pool is properly shut down."""
        self.shutdown(wait=False)
