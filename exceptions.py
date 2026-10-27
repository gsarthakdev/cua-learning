from pathlib import Path

class ExecutorError(Exception):
    def __init__(self, error_message, run_dir):
        super().__init__(f"Execution error: {error_message} (View Logs from events.json inside {run_dir})")
        
class EvaluationError(Exception):
    def __init__(self, error_message, document_path: Path):
        super().__init__(f"Evaluation error: {error_message} (For this document: {document_path})")