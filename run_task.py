"""
executor.py & evaluator.py
will continue to be modules.

run_task.py bundles their capabilities into an end-to-end repeatable experiment.
"""

from evaluator import evaluate
from executor import executor
from pathlib import Path
from datetime import datetime
from uuid import uuid4
PROJECT_DIR = Path.home() / "cua-learning"
RUN_ID = (
    datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:6]
)
RUN_DIR = PROJECT_DIR / "runs" / RUN_ID
RUN_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENT_PATH = RUN_DIR / "document.odt"

try:
    MESSAGE = "Hello from my Python computer-use executor!"    
    executor(MESSAGE, RUN_DIR, RUN_ID)
    evaluation_result = evaluate("UsingDoc", DOCUMENT_PATH, MESSAGE)
    print(evaluation_result)
    
except Exception as error:
    print(f"Error: {error}")