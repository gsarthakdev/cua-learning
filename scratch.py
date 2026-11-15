
import logging
# Configure logging to show INFO and above
logging.basicConfig(
    level=logging.INFO,
    # format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.debug("This will NOT print")
logging.info("Program started")
logging.warning("Low disk space")
logging.error("Connection failed")

# from agent_probe import execute_model_action

# action = {
#     "key": "ctrl+shift+s",
#     "action": "keypress",
#     "x": 0, "y": 0, "text": ""
# }
# execute_model_action(action)



from host_controller import collect_artifacts
from evaluator import evaluate

RUN_ID = "20261114-172440-c3fa71"

# Copy the agent's run directory from Ubuntu to macOS.
run_dir = collect_artifacts(RUN_ID)

document_path = run_dir / "document.odt"

print(f"Document exists: {document_path.is_file()}")

if document_path.is_file():
    result = evaluate(
        "UsingDoc",
        document_path,
        "Hello from my Python computer-use executor!",
    )

    print(f"Evaluation result: {result}")
else:
    print("Evaluation failed: Agent did not save the expected document.")

