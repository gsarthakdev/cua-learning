import shlex
import subprocess
from pathlib import Path
import re
import argparse
import time

GUEST_RUNS_DIR = "/home/sarthak/cua-learning/runs"
COLLECTED_RUNS_DIR = Path(__file__).resolve().parent / "collected_runs"

UTMCTL = Path("/Applications/UTM.app/Contents/MacOS/utmctl")

# Got this ID by running `/Applications/UTM.app/Contents/MacOS/utmctl list`
VM_ID = "DF61C72B-5135-4708-A5C4-C8C512F0B568"
BASELINE_SNAPSHOT = "cua-gui-ssh-baseline"

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

def reset_vm():
    """Restore the baseline snapshot and start Ubuntu."""
    status = run_utm("status", VM_ID)
    if status != "stopped":
        # todo: after experiment is ran, we should poweroff vm by default. Part of VM experiment lifecycle work.
        raise RuntimeError(
            "VM must be stopped before restoring the baseline."
            f"Current status: {status}"
        )
    
    print(f"Restoring snapshot: {BASELINE_SNAPSHOT}")
    
    run_utm(
        "snapshot", "restore", VM_ID, "--snapshot", BASELINE_SNAPSHOT
    )

    print("Snapshot restored successfully.")
    run_utm("start", VM_ID)
    print("VM start requested.") # need to implement guest readiness checks.
    
    
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
    

def wait_for_ssh(timeout_seconds=90):
    """Wait until Ubuntu accepts and executes SSH commands."""
    
    deadline = time.monotonic() + timeout_seconds
    last_error = "No SSH attempts completed"
    
    print("Waiting for SSH readiness...")
    
    while time.monotonic() < deadline:
        try:
            result = execute_in_vm(
                "/usr/bin/id",
                "-un",
                timeout=8
            )
            
            if result.returncode == 0 and result.stdout.strip() == "sarthak":
                print("SSH ready.")
                return

            last_error = (
                f"Exit code: {result.returncode}; "
                f"stderr: {result.stderr.strip()}"
            )
        except subprocess.TimeoutExpired:
            last_error = "SSH command timed out"
        
        time.sleep(2)
        
    raise RuntimeError(
        f"SSH readiness failed after {timeout_seconds}s. "
        f"Last error: {last_error}"
    )

def wait_for_gui(timeout_seconds=120):
    """Wait until the Ubuntu X11 desktop accepts GUI commands."""
    
    deadline = time.monotonic() + timeout_seconds
    last_error = "No GUI attempts completed"
    
    print("Waiting for X11 GUI readiness...")
    
    while time.monotonic() < deadline:
        try:
            result = execute_in_vm(
                "/usr/bin/xdotool",
                "getdisplaygeometry",
                gui=True,
                timeout=8
            )
            
            resolution = result.stdout.strip()
            dimensions = resolution.split()
            
            if (
                result.returncode == 0
                and len(dimensions) == 2
                and all(value.isdigit() and int(value) > 0 for value in dimensions)
            ):
                print(f"GUI ready. Resolution: {resolution}")
                return resolution
            
            last_error = (
                f"Exit code: {result.returncode}; "
                f"stderr: {result.stderr.strip()}"
            )

        except subprocess.TimeoutExpired:
            last_error = "GUI readiness check timed out."
        
        time.sleep(2)
        
    raise RuntimeError(
        f"GUI readiness failed after {timeout_seconds}s. "
        f"Last error: {last_error}"
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

    
def run_from_clean():
    """Restore a clean VM, boot it, and run a CUA experiment."""
    
    print("Starting clean-state CUA experiment...")
    
    # Restore snapshot and start the VM
    reset_vm()
    
    return main()

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
    # Can't run this anymore since VM might not be fully on when we reach this LOC.
    # os_name = execute_in_vm("/usr/bin/uname", "-s")
    # if os_name.returncode != 0:
    #     raise RuntimeError(f"SSH connectivity check failed: {os_name.stderr}")
    
    # print(f"Guest OS: {os_name.stdout.strip()}")
    
    # Identify which use executes guest-agent cmds
    wait_for_ssh()
    # identity = execute_in_vm("/usr/bin/id", "-un")
    # if identity.returncode != 0:
    #     raise RuntimeError(f"SSH identity check failed: {identity.stderr}")
    
    # print(f"SSH user executing cmds: {identity.stdout.strip()}")
    wait_for_gui() 
    # geometry = execute_in_vm(
    #     "/usr/bin/xdotool",
    #     "getdisplaygeometry",
    #     gui=True
    # )
    
    # if geometry.returncode != 0 or not geometry.stdout.strip():
    #     raise RuntimeError(
    #         f"GUI access check failed: {geometry.stderr}"
    #     )
        
    # print(f"Remote GUI resolution: {geometry.stdout.strip()}")
    
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
    parser = argparse.ArgumentParser()

    actions = parser.add_mutually_exclusive_group()

    actions.add_argument(
        "--reset-vm",
        action="store_true",
        help="Restore the baseline snapshot and start Ubuntu.",
    )

    actions.add_argument(
        "--run-from-clean",
        action="store_true",
        help="Restore the baseline and execute a CUA experiment.",
    )

    args = parser.parse_args()

    if args.reset_vm:
        reset_vm()
        exit_code = 0

    elif args.run_from_clean:
        exit_code = run_from_clean()

    else:
        exit_code = main()

    raise SystemExit(exit_code)