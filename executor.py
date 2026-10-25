import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
import uuid

"""
events is js hanging out, i want to give it structure, esp for line 144
"""

def executor(message: str, run_dir, run_id):
    # PROJECT_DIR = Path.home() / "cua-learning"
    # RUN_ID = (
    #     datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    # )
    # RUN_DIR = PROJECT_DIR / "runs" / RUN_ID
    # RUN_DIR.mkdir(parents=True, exist_ok=True)
    RUN_ID = run_id
    RUN_DIR = run_dir
    OUTPUT = RUN_DIR / "document.odt"
    MESSAGE = message
    # MESSAGE = "Hello from my Python computer-use executor!"    
    try:
        record("start", RUN_ID)
        
        # Open LibreOffice Writer
        subprocess.Popen(
            ["libreoffice", "--writer"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for Writer window to open (simple polling)
        window_id = None
        
        for _ in range(20):
            try:
                # Finds windows that contain the name xxx"LibreOffice Writer"xxx
                windows = execute("xdotool", "search", "--onlyvisible", "--name", "LibreOffice Writer").splitlines()
                
                if windows:
                    # windows var will look like this: windows = ["6291458", "6291512", "6291578"]
                    window_id = windows[-1] # We're choosing the last window, generally last window in the list indicates the "latest" one 
                    break
                
            except subprocess.CalledProcessError:
                pass
            
            time.sleep(1)

        if window_id is None:
            raise RuntimeError("LibreOffice Writer window not found")
        
        # Activate Writer and start a new document
        execute("xdotool", "windowactivate", "--sync", window_id)
        time.sleep(1)
        
        # Create a new document
        execute("xdotool", "key", "--clearmodifiers", "ctrl+n")
        time.sleep(2)
        
        screenshot("before.png")

        # Type into the document
        execute(
            "xdotool", "type",
            "--clearmodifiers", "--delay", "40",
            MESSAGE
        )
        
        record("keyboard_type_text", MESSAGE)
        time.sleep(1)
        
        screenshot("after_typing.png")
        record("result", "Actions completed; document not yet evaluated")
        
        # Save As operation through the GUI.
        execute(
            "xdotool", "key",
            "--clearmodifiers", "ctrl+shift+s"
        )
        time.sleep(2)
        
        execute(
            "xdotool", "key", "--clearmodifiers", "ctrl+l"
        )
        
        time.sleep(1)
        
        # type out the path
        execute(
            "xdotool", "type", "--clearmodifiers", "--delay", "20", str(OUTPUT)
        )

        # press the enter key
        execute("xdotool", "key", "Return")
        
        # Wait for the output artifact to save
        # poll for 10 seconds, 20 times.
        for _ in range(20):
            if OUTPUT.is_file() and OUTPUT.stat().st_size > 0:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Output document not created or not saved")
        
        time.sleep(1)
        screenshot("after_save.png")
        
        # record("task_end", )
        print("Execution completed.")
        
    except Exception as error:
        record("error", str(error))
        print(f"Execution failed: {error}")
    
    finally:
        log_path = RUN_DIR / "events.json"
        log_path.write_text(json.dumps(events.get_events(), indent=2))
        print(f"Artifacts saved to: {RUN_DIR}")


class EventManager:
    def __init__(self):
        self.events = []
    
    def record_event(self, action, detail=""):
        self.events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "detail": detail
            }
        )
    
    def get_events(self):
        return self.events.copy()

# events = []
events = EventManager()

# Previously used this prior to evaluator.py
# result = {
#     "run_directory": RUN_DIR,
#     "run_id": RUN_ID,
#     "success": False
# }

def record(action, detail=""):
    events.record_event(action, detail)
    # events.append(
    #     {
    #         "timestamp": datetime.now(timezone.utc).isoformat(),
    #         "action": action,
    #         "detail": detail
    #     }
    # )

def execute(*args):
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    record("command", " ".join(args))
    return result.stdout.strip()

def screenshot(name):
    path = RUN_DIR / name
    execute("scrot", str(path))
    record("screenshot", name)
