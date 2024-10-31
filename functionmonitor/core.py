
import concurrent.futures
import threading
import IPython.display
import IPython
import time
import logging
import inspect 
import keyword
import builtins

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class BaseThread(threading.Thread):
    threads = []  # Class-level list to track threads

    def __init__(self, *args, **kwargs):
        self._stopevent = threading.Event()
        super().__init__(*args, **kwargs)
        BaseThread.threads.append(self)

    def stop(self, timeout=None):
        self._stopevent.set()
        if timeout is not None:
            self.join(timeout)
        BaseThread.threads.remove(self)

class DisplayFunctionThread(BaseThread):
    """Thread that updates output based on the provided input function at regular intervals."""

    def __init__(self, name, input_function, function_params, display_id, refresh_rate=5):
        self._display_id = display_id
        self._input_function = input_function
        self._function_params = function_params
        self._refresh_rate = refresh_rate
        super().__init__(name=name)

    def run(self):
        while not self._stopevent.is_set():
            # Update the display with the current status
            try:
                content = self._input_function(**self._function_params)
                IPython.display.update_display(content, display_id=self._display_id)
            except Exception as e:
                logger.error(f"Error updating display: {e}")
            time.sleep(self._refresh_rate)

class FunctionMonitor:
    def __init__(self, create_variables=False, caller_globals=None, logging_level=logging.ERROR):
        self.futures = {}
        self._results_lock = threading.Lock()
        self.pool = concurrent.futures.ThreadPoolExecutor()
        self.function_monitor = None
        self.create_variables = create_variables
        # Store the caller's globals for variable assignment
        self.caller_globals = caller_globals or globals()
        
        # Configure the logger with the provided logging level
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging_level)
        
        # Optional: Add a stream handler if no handlers exist
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            handler.setLevel(logging_level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.start()

    def reset(self):
        """Reset the FunctionMonitor by stopping all active threads, shutting down the executor,
        and clearing futures."""
        
        # Stop the monitoring display thread
        if self.function_monitor:
            self.function_monitor.stop()
            self.function_monitor = None  # Clear the reference
        
        # Stop and clear any active threads in BaseThread.threads
        for thread in list(BaseThread.threads):  # Copy to avoid modification during iteration
            thread.stop()
        
        # Shutdown and restart the ThreadPoolExecutor
        self.pool.shutdown(wait=False)
        self.pool = concurrent.futures.ThreadPoolExecutor()
        
        # Clear the futures dictionary
        self.futures.clear()
        
        # Restart the monitoring display
        self.start()
        
        self.logger.info("FunctionMonitor reset and ready for new tasks.")
    
    def display_function_status(self, futures):
        """Generate an HTML table showing the futures status."""
        rows = ['<tr><th>Function</th><th>Status</th></tr>']
        for key, future in futures.items():
            if future.done():
                try:
                    result = future.result(timeout=0)
                    status = f"Finished"
                except Exception as e:
                    status = f"Error: {e}"
            else:
                status = "Running"
            rows.append(f"<tr><td>{key}</td><td>{status}</td></tr>")
        table = f"<table>{''.join(rows)}</table>"
        return IPython.display.Markdown(table)

    def start(self):
        """Start monitoring the futures and updating the display."""
        output_cell = IPython.display.display(IPython.display.Markdown(""), display_id=True)
        output_cell_id = output_cell.display_id
        self.function_monitor = DisplayFunctionThread(
            name='display_function_status',
            input_function=self.display_function_status,
            function_params={'futures': self.futures},
            display_id=output_cell_id,
            refresh_rate=1
        )
        self.function_monitor.start()

    def stop(self):
        """Stop the futures monitor thread and shutdown the executor."""
        if self.function_monitor:
            self.function_monitor.stop()
        self.pool.shutdown(wait=False)
        self.logger.info("FunctionMonitor stopped.")

    def __getitem__(self, key):
        """Get the result of a future, blocking until it completes."""
        return self.futures[key].result()

    def __setitem__(self, key, func):
        if not callable(func):
            raise ValueError("Value must be a callable function.")
        future = self.pool.submit(func)
        if self.create_variables:
            # Pass the caller_globals to the callback
            future.add_done_callback(lambda f, k=key: self._assign_variable(k, f))
        self.futures[key] = future
        self.logger.info(f"Future '{key}' added.")

    def _assign_variable(self, key, future):
        """Assign the result to a variable in the caller's global namespace."""
        with self._results_lock:
            try:
                result = future.result()
                # Check if key is a Python keyword
                if keyword.iskeyword(key):
                    self.logger.error(f"Cannot assign to '{key}': it is a Python keyword.")
                    return
                # Check if key is a built-in name
                if key in vars(builtins):
                    self.logger.error(f"Cannot assign to '{key}': it is a built-in name.")
                    return
                # Use the caller's globals for assignment
                if key in self.caller_globals:
                    self.logger.warning(f"Variable '{key}' already exists in the caller's global namespace. It will be overwritten.")
                self.caller_globals[key] = result
                self.logger.info(f"Variable '{key}' assigned with result.")
            except Exception as e:
                self.logger.error(f"Error in future '{key}': {e}")
                # Assign the exception to indicate failure
                self.caller_globals[key] = e

def get_fm(create_variables=False, logging_level=logging.ERROR):
    # Capture the caller's global namespace by going back one more frame
    caller_globals = inspect.currentframe().f_back.f_globals
    global fm

    # Use the caller's globals for assigning variables if fm is created
    if 'fm' not in globals():
        fm = FunctionMonitor(create_variables=create_variables, caller_globals=caller_globals, logging_level=logging_level)
    else:
        fm.start()
    return fm
