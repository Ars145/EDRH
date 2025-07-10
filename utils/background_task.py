"""
Background task management for EDRH
"""

import threading
import queue
import time
import traceback
from typing import Callable, Any, Optional, Dict, List, Tuple

class BackgroundTask:
    """
    A task that runs in the background
    
    This class allows running tasks in background threads while providing
    callbacks for completion, progress updates, and error handling.
    """
    
    def __init__(self, task_func, on_complete=None, on_error=None, on_progress=None):
        """
        Initialize a background task
        
        Args:
            task_func: Function to run in the background
                       Can return a value which will be passed to on_complete
            on_complete: Function to call when the task completes successfully
                         Signature: on_complete(result)
            on_error: Function to call when the task fails
                      Signature: on_error(exception)
            on_progress: Function to call to report progress
                         Signature: on_progress(progress, message)
                         Where progress is a float between 0 and 1
        """
        self.task_func = task_func
        self.on_complete = on_complete
        self.on_error = on_error
        self.on_progress = on_progress
        self.thread = None
        self.is_running = False
        self.is_cancelled = False
        self.result = None
        self.error = None
        
    def start(self, root=None):
        """
        Start the task in a background thread
        
        Args:
            root: Optional Tkinter root widget for scheduling callbacks
                 If provided, callbacks will be scheduled on the main thread
        """
        if self.is_running:
            return
            
        self.is_running = True
        self.is_cancelled = False
        self.result = None
        self.error = None
        
        def run():
            try:
                # Check if task has progress reporting capability
                if hasattr(self.task_func, '__code__') and 'progress_callback' in self.task_func.__code__.co_varnames:
                    # Create progress callback
                    def progress_callback(progress, message=""):
                        if self.is_cancelled:
                            raise CancelledError("Task was cancelled")
                            
                        if self.on_progress:
                            if root:
                                root.after(0, lambda: self.on_progress(progress, message))
                            else:
                                self.on_progress(progress, message)
                                
                    # Call task with progress callback
                    self.result = self.task_func(progress_callback=progress_callback)
                else:
                    # Call task without progress callback
                    self.result = self.task_func()
                    
                # Handle completion
                if not self.is_cancelled and self.on_complete:
                    if root:
                        root.after(0, lambda: self.on_complete(self.result))
                    else:
                        self.on_complete(self.result)
                        
            except Exception as e:
                if not self.is_cancelled:
                    self.error = e
                    print(f"Error in background task: {e}")
                    traceback.print_exc()
                    
                    if self.on_error:
                        if root:
                            root.after(0, lambda: self.on_error(e))
                        else:
                            self.on_error(e)
            finally:
                self.is_running = False
                
        # Start thread
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        
    def cancel(self):
        """Cancel the task if it's running"""
        self.is_cancelled = True
        
    def is_done(self):
        """Check if the task is done (completed or failed)"""
        return not self.is_running
        
    def wait(self, timeout=None):
        """
        Wait for the task to complete
        
        Args:
            timeout: Maximum time to wait in seconds
                    
        Returns:
            True if the task completed, False if it timed out
        """
        if not self.thread:
            return True
            
        self.thread.join(timeout)
        return not self.thread.is_alive()


class CancelledError(Exception):
    """Error raised when a task is cancelled"""
    pass


class TaskQueue:
    """
    A queue of background tasks
    
    This class manages a queue of tasks that run in the background,
    with a configurable number of worker threads.
    """
    
    def __init__(self, max_workers=3, root=None):
        """
        Initialize a task queue
        
        Args:
            max_workers: Maximum number of worker threads
            root: Optional Tkinter root widget for scheduling callbacks
        """
        self.queue = queue.Queue()
        self.workers = []
        self.max_workers = max_workers
        self.root = root
        self.running = False
        self.tasks = {}  # task_id -> (task, priority)
        self.next_task_id = 0
        self.lock = threading.Lock()
        
    def start(self):
        """Start the task queue"""
        if self.running:
            return
            
        self.running = True
        
        # Start worker threads
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)
            
    def stop(self):
        """Stop the task queue"""
        self.running = False
        
        # Clear queue
        with self.lock:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                except queue.Empty:
                    break
                    
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(0.1)
            
        self.workers = []
        
    def add_task(self, task_func, on_complete=None, on_error=None, on_progress=None, priority=0):
        """
        Add a task to the queue
        
        Args:
            task_func: Function to run in the background
            on_complete: Function to call when the task completes
            on_error: Function to call when the task fails
            on_progress: Function to call to report progress
            priority: Task priority (higher values run first)
            
        Returns:
            Task ID that can be used to cancel the task
        """
        with self.lock:
            task_id = self.next_task_id
            self.next_task_id += 1
            
            task = BackgroundTask(task_func, on_complete, on_error, on_progress)
            self.tasks[task_id] = (task, priority)
            
            # Add to queue with priority
            self.queue.put((-priority, task_id))
            
            return task_id
            
    def cancel_task(self, task_id):
        """
        Cancel a task
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if the task was cancelled, False if it wasn't found
        """
        with self.lock:
            if task_id in self.tasks:
                task, _ = self.tasks[task_id]
                task.cancel()
                return True
            return False
            
    def cancel_all_tasks(self):
        """Cancel all tasks"""
        with self.lock:
            for task_id in list(self.tasks.keys()):
                task, _ = self.tasks[task_id]
                task.cancel()
                
    def _worker_loop(self):
        """Worker thread loop"""
        while self.running:
            try:
                # Get task from queue
                try:
                    _, task_id = self.queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                    
                # Get task
                with self.lock:
                    if task_id not in self.tasks:
                        self.queue.task_done()
                        continue
                        
                    task, _ = self.tasks[task_id]
                    
                # Run task
                task.start(self.root)
                
                # Wait for task to complete
                while task.is_running:
                    time.sleep(0.1)
                    if not self.running:
                        task.cancel()
                        break
                        
                # Remove task
                with self.lock:
                    if task_id in self.tasks:
                        del self.tasks[task_id]
                        
                # Mark task as done
                self.queue.task_done()
                
            except Exception as e:
                print(f"Error in task queue worker: {e}")
                traceback.print_exc()


# Global task queue
_task_queue = None

def init_task_queue(max_workers=3, root=None):
    """Initialize the global task queue"""
    global _task_queue
    _task_queue = TaskQueue(max_workers, root)
    _task_queue.start()
    return _task_queue
    
def get_task_queue():
    """Get the global task queue"""
    if _task_queue is None:
        raise ValueError("Task queue not initialized. Call init_task_queue first.")
    return _task_queue
    
def add_task(task_func, on_complete=None, on_error=None, on_progress=None, priority=0):
    """Add a task to the global queue"""
    return get_task_queue().add_task(task_func, on_complete, on_error, on_progress, priority)
    
def cancel_task(task_id):
    """Cancel a task in the global queue"""
    return get_task_queue().cancel_task(task_id)
    
def cancel_all_tasks():
    """Cancel all tasks in the global queue"""
    get_task_queue().cancel_all_tasks()
    
def run_in_background(on_complete=None, on_error=None, on_progress=None, priority=0):
    """
    Decorator to run a function in the background
    
    Example:
        @run_in_background(on_complete=lambda result: print(f"Result: {result}"))
        def my_task():
            # Long-running operation
            return "Done"
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create a wrapper function that calls the original function with args
            def task_func():
                return func(*args, **kwargs)
                
            # Add to task queue
            return add_task(task_func, on_complete, on_error, on_progress, priority)
            
        return wrapper
        
    return decorator