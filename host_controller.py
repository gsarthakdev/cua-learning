import subprocess
from pathlib import Path

UTMCTL = Path("/Applications/UTM.app/Contents/MacOS/utmctl")

# Got this ID by running `/Applications/UTM.app/Contents/MacOS/utmctl list`
VM_ID = "DF61C72B-5135-4708-A5C4-C8C512F0B568"

def run_utm(*args):
    """Execute a UTM CLI command from the macOS host."""
    
    result = subprocess.run(
        [str(UTMCTL), *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    
    return result.stdout.strip()

def execute_in_vm(*command):
    """Run a command inside the Ubuntu guest via QEMU Guest Agent."""
    
    return run_utm(
        "exec",
        VM_ID,
        "--cmd",
        *command
    )
    

GUEST_USERNAME = "sarthak"
def execute_as_user(*command):
    """Execute a command in Ubuntu as the unprivileged user."""
    return execute_in_vm(
        "/usr/sbin/runuser",
        "-u",
        GUEST_USERNAME,
        "--",
        *command,
    )


def execute_in_gui_session(*command):
    """Execute a command in the Ubuntu user's X11 session."""
    return execute_in_vm(
        "/usr/sbin/runuser",
        "-u",
        "sarthak",
        "--",
        "/usr/bin/env",
        "DISPLAY=:0",
        "XAUTHORITY=/run/user/1000/gdm/Xauthority",
        "XDG_RUNTIME_DIR=/run/user/1000",
        *command,
    )


def main():
    # Verify the VM is running
    status = run_utm("status", VM_ID)
    print(f"VM status: {status}")
    
    if status != "started":
        raise RuntimeError("Ubuntu VM is not running")
    
    # Verify which OS the VM is running
    os_name = execute_in_vm("/usr/bin/uname", "-s")
    print(f"Guest OS: {os_name}")

    # Identify which use executes guest-agent cmds
    username = execute_in_vm("/usr/bin/id", "-un")
    print(f"Guest execution user: {username}")

    guest_user = execute_as_user("/usr/bin/id", "-un")
    print(f"Unprivileged execution user: {guest_user}")
    
    for i in range(1,5+1):
        print(f"\n=====Attempt {i}")
        resolution = execute_in_gui_session(
            "/usr/bin/xdotool",
            "getdisplaygeometry",
        )
        
        print(f"Remote GUI resolution: {resolution}")
        
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())