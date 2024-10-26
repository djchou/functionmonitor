# functionmonitor

Overview
Python’s standard behavior for function calls is synchronous and blocking, meaning that each function runs in sequence, waiting for one to finish before starting the next. This can limit efficiency, especially for I/O-bound tasks or long-running operations.

functionmonitor provides an easy way to run functions asynchronously in separate threads, allowing Python programs to execute multiple functions in a non-blocking manner. With functionmonitor, you can:

Execute functions concurrently in separate threads, freeing up the main program flow.
Monitor the progress of each function’s execution in real-time.
Automatically assign results to variables in the global namespace upon completion, making it easy to access results as soon as they’re available.
This tool is ideal for use cases where functions need to run independently without blocking other parts of your application.