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

"""
10/26:
Intentionally test adding 2 bugs and seeing how CU (Computer Use) behaves.

1. (executor): Write incorrect message in document.odt. Evaluation should return content_matches: false

2. Inside executor, introduce any kind of bug, that should trigger a ExecutorError
-----

ChatGPT (GPT-6 High) suggests an amazing paradigm for the `result` var.
My write-up based on its suggestions and my techincal judgement:
    - Keep result dict in run_task.py with run_id, task_name, success, status.
        - status alone can indicate different success(s)/failure modes:
            - executor successful but eval failed: evaluation_failed
            - executor + eval successful: passed
            - executor failed: executor_failed
            - evaluation code broke: evaluation_error
            - something else: harness_failure
    - If exception: add relevant error keys: error_type, error_message
    
    - If evaluation runs, then we simply result.update({evaluation_result}) to the `result` dict. Centralize location for result to aid in deduplication of data in multiple places. 
    
    Then write that result dict into results.json for RUN_DIR / RUN_ID / results.json
    
    Need to return 0 if run successful else 1
"""

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