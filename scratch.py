def run(*args):
    print(args)


run("hello", "this", "is")

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

from agent_probe import execute_model_action

action = {
    "key": "ctrl+shift+s",
    "action": "keypress",
    "x": 0, "y": 0, "text": ""
}
execute_model_action(action)
