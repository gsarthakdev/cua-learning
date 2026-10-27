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
from exceptions import ExecutorError, EvaluationError
import json
from typing import TypedDict, Literal



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
            - executor successful but eval didn't pass: evaluation_failed
            - executor + eval successful: passed
            - executor failed: executor_failed
            - evaluation code broke: evaluation_error
            - something else: harness_failure
    - If exception: add relevant error keys: error_type, error_message
    
    - If evaluation runs, then we simply result.update({evaluation_result}) to the `result` dict. Centralize location for result to aid in deduplication of data in multiple places. 
    
    Then write that result dict into results.json for RUN_DIR / RUN_ID / results.json
    
    Need to return 0 if run successful else 1
"""

class ResultDict(TypedDict):
    run_id: str
    executor_ran: bool
    evaluation_success: bool
    end_to_end_success: bool
    error_type: str
    error_message: str
    status: Literal["not_started", "started_execution", "started_evaluation", "executor_failed", "evaluation_failed", "harness_failed", "completed"]
    
    
"""
result = {
    run_id:,
    executor_success: ,
    evaluation_success,
    error_type:
    error_message:
    status:
    end_to_end_success
}
"""

def main():
    try:
        PROJECT_DIR = Path.home() / "cua-learning"
        RUN_ID = (
            datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:6]
        )
        RUN_DIR = PROJECT_DIR / "runs" / RUN_ID
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        DOCUMENT_PATH = RUN_DIR / "document.odt"
        

        result: ResultDict = {
            "run_id": RUN_ID,
            "executor_ran": False,
            "evaluation_success": False,
            "end_to_end_success": False,
            "status": "not_started"
        }   
        
        # ---------    
        MESSAGE = "Hello from my Python computer-use executor!"
        result["status"] = "started_execution"    
        execute_task(MESSAGE, RUN_DIR, RUN_ID)
        result["status"] = "started_evalution"    
        evaluation_result = evaluate("UsingDoc", DOCUMENT_PATH, MESSAGE)
        """
                result = {
                "task_name": task_name,
                "file_exists": DOCUMENT.is_file(),
                "content_matches": False,
                "success": False # if content_matches==True, success=True
            }
        """
        # If we are still in this block here, then the execution worked
        result["executor_ran"] = True
        result["evaluation_success"] = evaluation_result["success"]
        result["end_to_end_success"] = result["executor_ran"] and result["evaluation_success"]
        # print(evaluation_result)    
        result["status"] = "completed"
        
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
    except ExecutorError as error:
        # We know the executor for some reason failed
        result["status"] = "executor_failed"
        result["error_type"] = type(error).__name__
        result["error_message"] = str(error)
        
    except EvaluationError as error:
        # We know the evalaution hit an error
        result["status"] = "evaluation_failed"
        result["error_type"] = type(error).__name__
        result["error_message"] = str(error)    
        
    except Exception as error:
        # something from the harness failed
        result["status"] = "harness_failed"
        result["error_type"] = type(error).__name__
        result["error_message"] = str(error)    
        print(f"Error: {error}")
        
    finally:
        # write the result.json file here
        # need a path
        result_path = RUN_DIR / "results.json"
        result_path.write_text(
            json.dumps(result, indent=2)
        )
        print(json.dumps(result, indent=2))
        print(f"Artifacts saved to: {RUN_DIR}")

    return 0 if result["end_to_end_success"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

