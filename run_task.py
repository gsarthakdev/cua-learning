"""
executor.py & evaluator.py
will continue to be modules.

run_task.py bundles their capabilities into an end-to-end repeatable experiment.
"""

from evaluator import evaluate
from executor import execute_task
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from exceptions import ExecutorError
PROJECT_DIR = Path.home() / "cua-learning"
RUN_ID = (
    datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:6]
)
RUN_DIR = PROJECT_DIR / "runs" / RUN_ID
RUN_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENT_PATH = RUN_DIR / "document.odt"

# My goal is, if an Exception is hit in executor.py, we shall trigger the except in the block below

try:
    MESSAGE = "Hello from my Python computer-use executor!"    
    # run_overview = execute_task(MESSAGE, RUN_DIR, RUN_ID)
    execute_task(MESSAGE, RUN_DIR, RUN_ID)
    evaluation_result = evaluate("UsingDoc", DOCUMENT_PATH, MESSAGE)
    print(evaluation_result)    
    # executor_result meaning executor did *something*
    # if run_overview["error"]:
        # raise ExecutorError(run_overview["error_message"], RUN_DIR)
    # else:
    #     evaluation_result = evaluate("UsingDoc", DOCUMENT_PATH, MESSAGE)
    #     print(evaluation_result)
    """
    2 cases of executor() failing:
        1. Exception occurs ("Execution failed: ...")
            - We don't want to trigger the evaluator
            - Simply return result with task_failed
            - print a global "result" with task_failed
            - events.json stores the error
        2. No exception but task didn't completed as planned
            - In this case we can run the evalautor
    
    """
      
except Exception as error:
    print(f"Error: {error}")