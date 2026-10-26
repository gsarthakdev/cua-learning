class ExecutorError(Exception):
    def __init__(self, error_message, run_dir):
        super().__init__(f"Execution error: {error_message}\n\n View Logs from events.json inside {run_dir} ")