import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S")
RUN_DIR = Path.home() / "cua-learning" / "runs" / RUN_ID
RUN_DIR.mkdir(parents=True, exist_ok=True)

events = []

def execute(*args):
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return result.stdout.strip()

def record(action, detail):
    events.append(
        {
            "action": action,
            "detail": detail
        }
    )

def screenshot(name):
    path = RUN_DIR / name
    execute("scrot", str(path))
    record("screenshot", str(path))

def main():
    try:
        # Open LibreOffice Writer
        subprocess.Popen(
            ["libreoffice", "--writer"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for Writer window to open
        window_id = None
        for _ in range(20):
            try:
                windows = execute("xdotool", "search", "--onlyvisible", "--name", "LibreOffice Writer").splitlines()
                
                if windows:
                    window_id = windows[-1]
                    break
                
            except subprocess.CalledProcessError:
                pass
            
            time.sleep(1)

        if window_id is None:
            raise RuntimeError("LibreOffice window not found")
        
        # Activate Writer and start a new document
        execute("xdotool", "windowactivate", "--sync", window_id)
        time.sleep(1)
        execute("xdotool", "key", "--clearmodifiers", "ctrl+n")
        time.sleep(2)
        
        screenshot("before.png")

        # Type into the document
        
        message = "Hello from my Python computer-use executor!"
        
        execute(
            "xdotool", "type",
            "--clearmodifiers", "--delay", "50",
            message
        )
        
        record("keyboard", message)

        time.sleep(1)
        screenshot("after.png")
        record("result", "Actions completed; document not yet evaluated")
        print("Execution completed.")
        
        
    except Exception as error:
        record("error", str(error))
        print(f"Execution failed: {error}")
    
    finally:
        log_path = RUN_DIR / "events.json"
        log_path.write_text(json.dumps(events, indent=2))
        print(f"Artifacts saved to: {RUN_DIR}")
        
main()