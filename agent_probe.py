import json, subprocess, sys
from pathlib import Path

MODEL = "sonnet"

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

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 agent_probe.py <screenshot_path>")
        return 1
    
    screenshot_path = Path(sys.argv[1])
    observation = observe_with_claude(screenshot_path)
    print("\nClaude's observation:")
    print(observation)
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())