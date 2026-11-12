import shlex
import subprocess
from pathlib import Path
import re

GUEST_RUNS_DIR = "/home/sarthak/cua-learning/runs"
COLLECTED_RUNS_DIR = Path(__file__).resolve().parent / "collected_runs"

UTMCTL = Path("/Applications/UTM.app/Contents/MacOS/utmctl")

# Got this ID by running `/Applications/UTM.app/Contents/MacOS/utmctl list`
VM_ID = "DF61C72B-5135-4708-A5C4-C8C512F0B568"

SSH_KEY = Path.home() / ".ssh/cua_learning_ed25519"
SSH_TARGET = "sarthak@192.168.64.4"

GUEST_RUNNER = "/home/sarthak/cua-learning/run_task.py"

GUI_ENV = [
    "env",
    "DISPLAY=:0",
    "XAUTHORITY=/run/user/1000/gdm/Xauthority",
    "XDG_RUNTIME_DIR=/run/user/1000",
    "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus",
]

def run_utm(*args):
    """Execute a UTM lifecycle command on host machine."""
    
    result = subprocess.run(
        [str(UTMCTL), *args],
        capture_output=True,
        text=True,
        # check=True, # If this were to be True, an exception with vague message would be raised immediately
        timeout=30,
    )
    
    # We do this to get a clear error message.
    if result.returncode != 0:
        raise RuntimeError(
            f"utmctl {' '.join(args)} failed (exit code {result.returncode}): {result.stderr.strip()}" 
        )
    
    return result.stdout.strip()

def execute_in_vm(*command, gui=False, timeout=30):
    """Execute a command in Ubuntu via SSH.
    
    Returns CompletedProcess so callers can inspect stdout, stderr, and the guest command's exit code.
    """
    remote_command = [
        *(GUI_ENV if gui else []),
        *command
    ]
    return subprocess.run(
        [
            "ssh",
            "-i", str(SSH_KEY),
            "-o", "IdentitiesOnly=yes",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            SSH_TARGET,
            shlex.join(remote_command),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    

def extract_run_id(output: str) -> str:
    """Extract the experiement's unique run ID from stdout."""
    match = re.search(
        r"^CUA_RUN_ID=([0-9]{8}-[0-9]{6}-[0-9a-f]{6})$",
        output,
        re.MULTILINE
    )
    if match is None:
        raise RuntimeError("Experiment did not report a valid run ID")

    return match.group(1)

def collect_artifacts(run_id: str):
    """Copy an experiment's artifacts from Ubuntu to macOS (host)."""
    COLLECTED_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    
    remote_path = f"{SSH_TARGET}:{GUEST_RUNS_DIR}/{run_id}"
    
    result = subprocess.run(
        [
            "scp",
            "-i", str(SSH_KEY),
            "-o", "IdentitiesOnly=yes",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            "-r",
            remote_path,
            str(COLLECTED_RUNS_DIR),
        ],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        raise RuntimeError(
            f"Artifact collection failed: {result.stderr}"
        )
        
    return COLLECTED_RUNS_DIR / run_id

# GUEST_USERNAME = "sarthak"
# def execute_as_user(*command):
#     """Execute a command in Ubuntu as the unprivileged user."""
#     return execute_in_vm(
#         "/usr/sbin/runuser",
#         "-u",
#         GUEST_USERNAME,
#         "--",
#         *command,
#     )

# def execute_in_gui_session(*command):
#     """Execute a command in the Ubuntu user's X11 session."""
#     return execute_in_vm(
#         "/usr/sbin/runuser",
#         "-u",
#         "sarthak",
#         "--",
#         "/usr/bin/env",
#         "DISPLAY=:0",
#         "XAUTHORITY=/run/user/1000/gdm/Xauthority",
#         "XDG_RUNTIME_DIR=/run/user/1000",
#         *command,
#     )

def _to_text(output):
    return output.decode("utf-8", errors="replace") if isinstance(output, bytes) else output

def main():
    # Verify the VM is running
    status = run_utm("status", VM_ID)
    print(f"VM status: {status}")
    
    if status != "started":
        raise RuntimeError("Ubuntu VM is not running")
    
    # Verify which OS the VM is running
    os_name = execute_in_vm("/usr/bin/uname", "-s")
    if os_name.returncode != 0:
        raise RuntimeError(f"SSH connectivity check failed: {os_name.stderr}")
    
    print(f"Guest OS: {os_name.stdout.strip()}")
    
    # Identify which use executes guest-agent cmds
    identity = execute_in_vm("/usr/bin/id", "-un")
    if identity.returncode != 0:
        raise RuntimeError(f"SSH identity check failed: {identity.stderr}")
    
    print(f"SSH user executing cmds: {identity.stdout.strip()}")
    
    geometry = execute_in_vm(
        "/usr/bin/xdotool",
        "getdisplaygeometry",
        gui=True
    )
    
    if geometry.returncode != 0 or not geometry.stdout.strip():
        raise RuntimeError(
            f"GUI access check failed: {geometry.stderr}"
        )
        
    print(f"Remote GUI resolution: {geometry.stdout.strip()}")
    
    # Execute our existing CUA evaluation harness.
    print("\nStarting remote CUA experiment...\n")
    try:

        """
        2 very important key concepts to note here:
        
        1. (Guest timeout) Linux VM receives X amount of seconds to perform the task. If not completed within X seconds, task is forcefully terminated.
        
        2. (Host timeout) MacOS (Host) is allocated a maximum of X seconds via `timeout=X` param to keep the SSH process open. After that, the local SSH process is terminated.
        
        This is to protect both the host and the guest from infinite running.
        """
        
        
        experiment = execute_in_vm(
            "/usr/bin/timeout", # Linux utility that runs a command with a maximum execution time.
            "--signal=TERM", # Send SIGTERM to request graceful termination when the time limit is reached.
            "--kill-after=5s", # If the process hasn't terminated after 5 more seconds, send SIGKILL to force termination.
            "170s",# Maximum time (170 seconds) the guest experiment can run before SIGTERM is sent.
            "/usr/bin/python3",
            "-u", # Unbuffered output so experiment logs reach SSH immediately.
            GUEST_RUNNER,
            gui=True,
            timeout=200,
        )
        
        # If this doesn't return something within 200 seconds (because of `timeout=200`), it throws a subprocess.TimeoutExpired error.
        
    except subprocess.TimeoutExpired as error:
        print(f"Host-side SSH timeout after {error.timeout}s")
        
        # Preserve any stdout captured before the SSH process timed out.
        # TimeoutExpired output may be bytes, even with text=True.
        if error.stdout:
            output = error.stdout
            output = _to_text(output)
            # if isinstance(output, bytes):
            #     output = output.decode("utf-8", errors="replace")
            print(f"stdout:\n{output}")
            # todo: in the near future we should be logging this into a log.json file.
            
        if error.stderr:
            output = error.stderr
            output = _to_text(output)
            # if isinstance(output, bytes):
            #     output = output.decode("utf-8", errors="replace")
            
            print(f"stderr:\n{output}")
            # todo: in the near future we should be logging this into a log.json file.
        
        print("Remote experiment termination is not confirmed.")
        # Return exit code 124 because command timed out (the host-side SSH subprocess exceeded its timeout).
        return 124

    
    # SSH returned *something*, print it:
    print(experiment.stdout)
    
    if experiment.stderr:
        print(f"stderr:\n{experiment.stderr}")
    
    """
    Return codes verified through offical GNU docs:
    https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html
    """
    
    # CHECK FOR GUEST TIMEOUT: Linux VM (Guest-side) timeout. 137 addresses SIGKILL exit code. Regular timeout is code 124.
    if experiment.returncode == 124:
        print("Guest experiment exceeded its 170-second time limit.")
    
    elif experiment.returncode == 137:
        print("Guest experiment terminated by SIGKILL (possibly timeout escalation).")
    
    # Check for potential SSH connection or auth error
    elif experiment.returncode == 255:
        print("Possible SSH failure. Remote experiment state is unknown.")

    
    run_id = extract_run_id(experiment.stdout)
    print(f"Experiment run ID: {run_id}")
    
    artifact_path = collect_artifacts(run_id)
    print(f"Artifacts collected at: {artifact_path}")
    
    print(f"Experiment exit code: {experiment.returncode}")
    
    return experiment.returncode


if __name__ == "__main__":
    raise SystemExit(main())