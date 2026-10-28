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
from typing import TypedDict, Literal, NotRequired



# My goal is, if an Exception is hit in executor.py, we shall trigger the except in the block below


"""
10/27:
Intentionally test adding 2 bugs and seeing how CU (Computer Use) behaves.

1. (executor): Write incorrect message in document.odt. Evaluation should return content_matches: false

2. Inside executor, introduce any kind of bug, that should trigger a ExecutorError
-----
"""

class ResultDict(TypedDict):
    run_id: str
    task_name: str
    executor_completed: bool
    evaluation_completed: bool
    evaluation_success: bool
    end_to_end_success: bool
    error_type: NotRequired[str]
    error_message: NotRequired[str]
    status: Literal["not_started", "started_execution", "execution_completed", "started_evaluation","evaluation_completed", "executor_failed", "evaluation_failed", "harness_failed", "completed"]
    


def main():
    try:
        # need to modularize this file path loading stuff into a function task_setup()
        PROJECT_DIR = Path.home() / "cua-learning"
        RUN_ID = (
            datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:6]
        )
        RUN_DIR = PROJECT_DIR / "runs" / RUN_ID
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        DOCUMENT_PATH = RUN_DIR / "document.odt"
        TASK_NAME = "UsingDoc"

        result: ResultDict = {
            "run_id": RUN_ID,
            "task_name": TASK_NAME,
            "executor_completed": False,
            "evaluation_completed": False,
            "evaluation_success": False,
            "end_to_end_success": False,
            "status": "not_started"
        }   
        
        # ---------    
        MESSAGE = "Hello from my Python computer-use executor!"
        
        result["status"] = "started_execution"    
        execute_task(MESSAGE, RUN_DIR, RUN_ID)
        result["status"] = "execution_completed"
        
        result["executor_completed"] = True
        
        result["status"] = "started_evalution"    
        evaluation_result = evaluate(TASK_NAME, DOCUMENT_PATH, MESSAGE)
        result["status"] = "evaluation_completed"
        result["evaluation_completed"] = True
        """
                result = {
                "task_name": task_name,
                "file_exists": DOCUMENT.is_file(),
                "content_matches": False,
                "success": False # if content_matches==True, success=True
            }
        """

        # If we are still in this block here, then the execution worked
        result["evaluation_success"] = evaluation_result["success"]
        result["end_to_end_success"] = result["executor_completed"] and result["evaluation_success"]
        result["status"] = "completed"
        
        
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

        # If the executor failed, then it's Exception is triggered, but we still reach the finally block and should not attempt to safe `evaluation_result` since it wouldn't have ran.
        if not result["status"] == "executor_failed":
            # Write the evaluation_result dict to evaluation_log.json
            evaluation_log_path = RUN_DIR / "evaluation_log.json"
            evaluation_log_path.write_text(
                json.dumps(evaluation_result, indent=2)
            )
            print(f"\n{json.dumps(evaluation_result, indent=2)}")
        
        print(f"Artifacts saved to: {RUN_DIR}")

    return 0 if result["end_to_end_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

