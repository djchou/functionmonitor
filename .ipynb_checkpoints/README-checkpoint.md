# functionmonitor

![Demo](demo.gif)

Python's standard function calls are **synchronous** and **blocking**, executing each function sequentially and waiting for each to complete before moving on. This design can be a limitation, especially with I/O-bound or long-running operations.

**`functionmonitor`** is designed specifically for use in **Jupyter notebooks** to enable easy, asynchronous function execution. By running functions in separate threads, you can manage multiple tasks concurrently within the interactive Jupyter environment, allowing for:

- **Concurrent function execution**, freeing up the main thread to continue processing other tasks.
- **Real-time monitoring** of each function's progress.
- **Automatic result assignment** to variables in the global namespace for easy access as soon as functions complete.

## Key Features

- **Execute Functions Concurrently**: Run functions in separate threads, improving efficiency by enabling asynchronous execution.
- **Easy Result Access**: Results are assigned to global variables with the same name as the task key if the `create_variables` parameter is enabled.
- **Supports Any Callable**: Works with any callable (function, lambda, etc.), allowing for flexible function management.


## Installation

To install `functionmonitor`, simply use pip:

```bash
pip install functionmonitor
```

## Usage Overview

1. **Basic Structure**  
   `functionmonitor` behaves similarly to a dictionary, where each task is stored with a task name as the key and the result as the value. Once a task completes, its result is directly accessible.

2. **Using Callables**  
   Any callable can be assigned to `functionmonitor`, allowing functions, lambda expressions, and more to run asynchronously. Prefixing the callable with `lambda` prevents immediate execution, enabling background processing.

```python
import functionmonitor
fm = functionmonitor.get_fm(create_variables=True)
fm[{var}] = lambda: {func()}
```
