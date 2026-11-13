import json, subprocess, sys
from pathlib import Path
from uuid import uuid4
from host_controller import (
    VM_ID,
    SSH_KEY,
    SSH_TARGET,
    run_utm,
    execute_in_vm,
    wait_for_ssh,
    wait_for_gui
)

MODEL = "sonnet"


ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["type", "keypress", "click", "done"],
        },
        "text": {"type": "string"},
        "key": {"type": "string"},
        "x": {"type": "integer"},
        "y": {"type": "integer"},
    },
    "required": ["action", "text", "key", "x", "y"],
    "additionalProperties": False,
}


def observe_with_claude(screenshot_path: Path) -> str:
    """Ask Claude to inspect a screenshot and recommend one GUI action."""
    
    screenshot_path = screenshot_path.resolve(strict=True)
    
    prompt = f"""
    You are observing an Ubuntu desktop for a computer-use task.
    
    Use the Read tool to view this screenshot:
    {screenshot_path}
    
    Task:
    Create a LibreOffice Writer document containing the exact sentence "Hello from my Python computer-use executor!" and save it as an ODT document.
    
    Describe what you actually see and recommend the next single GUI action.
    
    Do not execute actions. Do not modify any files.
    If you cannot view the image, explicitly say so.
    """
    
    result = subprocess.run(
        [
            "claude",
            "-p", prompt,
            "--model", MODEL,
            "--output-format", "json",
            "--tools", "Read",
            "--allowedTools", "Read",
            "--disallowedTools", "mcp__*",
            "--max-turns", "3",            
        ],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed: {result.stderr or result.stdout}"
        )

    response = json.loads(result.stdout)

    if isinstance(response, list):
        # Claude returned multiple events.
        # Find the final result event.
        final_result = next(
            (
                event
                for event in reversed(response)
                if isinstance(event, dict)
                and event.get("type") == "result"
            ),
            None,
        )
    else:
        # Standard JSON output: one dictionary.
        final_result = response

    if not isinstance(final_result, dict):
        raise RuntimeError("Claude did not return a final result")

    if final_result.get("is_error") or not final_result.get("result"):
        raise RuntimeError(
            f"Claude failed. Status: {final_result.get('subtype')}"
        )

    return final_result["result"]

    # if response.get("is_error") or not response.get("result"):
    #     raise RuntimeError(f"Claude returned an error: {response}")
    
    # return response
    # return response["result"]

OBSERVATIONS_DIR = Path(__file__).resolve().parent / "observations"

def capture_live_screenshot() -> Path:
    """Capture the current Ubuntu desktop and copy it to macOS."""

    if run_utm("status", VM_ID) != "started":
        raise RuntimeError("Linux/Ubuntu VM is not running!")
    
    wait_for_ssh()
    wait_for_gui()
    
    OBSERVATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    screenshot_id = uuid4().hex
    
    guest_path = f"/tmp/cua-{screenshot_id}.png"
    host_path = OBSERVATIONS_DIR / f"{screenshot_id}.png"
    
    # Capture the screenshot
    capture = execute_in_vm(
        "/usr/bin/scrot",
        guest_path,
        gui=True,
        timeout=15,
    )

    if capture.returncode != 0:
        raise RuntimeError(f"Screenshot capture failed: {capture.stderr}")
    
    # Transfer the screenshot from Guest to Host (macOS)
    try:
        transfer = subprocess.run(
            [
                "scp",
                "-i", str(SSH_KEY),
                "-o", "IdentitiesOnly=yes",
                "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=5",
                f"{SSH_TARGET}:{guest_path}",
                str(host_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if transfer.returncode != 0:
            raise RuntimeError(f"Screenshot transfer failed: {transfer.stderr}")
        
        if not host_path.is_file() or host_path.stat().st_size == 0:
            raise RuntimeError("Screenshot missing or empty.")
        
    finally:
        # Remove the temporary screenshot from Ubuntu.
        cleanup = execute_in_vm(
            "/usr/bin/rm",
            "-f",
            guest_path,
        )
        
        if cleanup.returncode != 0:
            print("Warning: Could not remove guest screenshot")

    return host_path

def choose_action_with_claude(screenshot_path: Path) -> dict:
    """Ask Claude to select one structured GUI action."""
    
    screenshot_path = screenshot_path.resolve(strict=True)
    
    # Doesn't LLM need to know Display Dimensions to give near-accurate coordinates for click?
    
    prompt = f"""
    You are a computer-use agent operating an Ubuntu desktop.
    
    Use the Read tool to inspect this screenshot:
    {screenshot_path}
    
    Task:
    Create a LibreOffice Writer document containing exactly:
    "Hello from my Python computer-use executor!"
    
    Save the document in ODT format.
    
    Select the SINGLE next GUI action needed to make progress.
    
    Available actions:
    - type: Type text into the currently focused field.
    - keypress: Press a keyboard key or shortcut.
    - click: Click a coordinate on the screen.
    - done: Indicate that the task appears complete.

    Return one action matching the required JSON schema.
    
    For unused string fields, return "".
    For unused coordinate fields, return 0.
    
    Do not modify files or execute GUI actions yourself.
    """
    

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 agent_probe.py <screenshot_path|--live>")
        return 1
    
    if sys.argv[1] == "--live":
        screenshot_path = capture_live_screenshot()
    else:
        screenshot_path = Path(sys.argv[1])

    observation = observe_with_claude(screenshot_path)
    print("\nClaude's observation:")
    print(observation)
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())