
import concurrent.futures
import threading
import IPython.display
import IPython
import time
import logging
import inspect  # Import inspect to access caller's globals
import keyword
import builtins

# Configure logging
logging.basicConfig(level=logging.INFO)
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
    def __init__(self, create_variables=False):
        self.futures = {}
        self._results_lock = threading.Lock()
        self.pool = concurrent.futures.ThreadPoolExecutor()
        self.futures_monitor = None
        self.create_variables = create_variables
        self.start()

    def start(self):
        """Start monitoring the futures and updating the display."""
        output_cell = IPython.display.display(IPython.display.Markdown(""), display_id=True)
        output_cell_id = output_cell.display_id
        self.futures_monitor = DisplayFunctionThread(
            name='display_futures_status',
            input_function=self.display_futures_status,
            function_params={'futures': self.futures},
            display_id=output_cell_id,
            refresh_rate=1
        )
        self.futures_monitor.start()

    def stop(self):
        """Stop the futures monitor thread and shutdown the executor."""
        if self.futures_monitor:
            self.futures_monitor.stop()
        self.pool.shutdown(wait=False)
        logger.info("FuturesMonitor stopped.")

    def display_futures_status(self, futures):
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

    def __getitem__(self, key):
        """Get the result of a future, blocking until it completes."""
        return self.futures[key].result()

    def __setitem__(self, key, func):
        if not callable(func):
            raise ValueError("Value must be a callable function.")
        # Capture the caller's global namespace
        caller_globals = inspect.currentframe().f_back.f_globals
        future = self.pool.submit(func)
        if self.create_variables:
            # Pass the caller_globals to the callback
            future.add_done_callback(lambda f, k=key, g=caller_globals: self._assign_variable(k, f, g))
        self.futures[key] = future
        logger.info(f"Future '{key}' added.")

    def _assign_variable(self, key, future, caller_globals):
        """Assign the result to a variable in the caller's global namespace."""
        with self._results_lock:
            try:
                result = future.result()
                # Check for invalid variable names
                if not key.isidentifier():
                    logger.error(f"Cannot assign to '{key}': invalid identifier.")
                    return
                if keyword.iskeyword(key):
                    logger.error(f"Cannot assign to '{key}': it is a Python keyword.")
                    return
                if key in vars(builtins):
                    logger.error(f"Cannot assign to '{key}': it is a built-in name.")
                    return
                if key in caller_globals:
                    logger.warning(f"Variable '{key}' already exists in the global namespace. It will be overwritten.")
                caller_globals[key] = result
                logger.info(f"Variable '{key}' assigned with result.")
            except Exception as e:
                logger.error(f"Error in future '{key}': {e}")
                caller_globals[key] = e

def get_fm(create_variables=False):
    global fm
    if 'fm' not in globals():
        fm = FunctionMonitor(create_variables=create_variables)
    else:
        fm.start()
    return fm
