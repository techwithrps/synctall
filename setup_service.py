import os
import sys
import subprocess
import getpass

def setup_launch_agent():
    # 1. Paths resolution
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(workspace_dir, ".venv", "bin", "python3")
    
    if not os.path.exists(venv_python):
        print(f"ERROR: Virtualenv python not found at {venv_python}")
        print("Please make sure the virtual environment (.venv) is set up in the workspace root.")
        sys.exit(1)
        
    username = getpass.getuser()
    plist_label = "com.synctal.syncagent"
    plist_filename = f"{plist_label}.plist"
    user_home = os.path.expanduser("~")
    launch_agents_dir = os.path.join(user_home, "Library", "LaunchAgents")
    dest_plist_path = os.path.join(launch_agents_dir, plist_filename)
    
    # Ensure logs directory exists
    logs_dir = os.path.join(workspace_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    stdout_log = os.path.join(logs_dir, "sync_agent_stdout.log")
    stderr_log = os.path.join(logs_dir, "sync_agent_stderr.log")
    
    # 2. Plist Content
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{plist_label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{venv_python}</string>
        <string>-u</string>
        <string>-m</string>
        <string>sync_agent.main</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{workspace_dir}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{stdout_log}</string>
    <key>StandardErrorPath</key>
    <string>{stderr_log}</string>
</dict>
</plist>
"""
    
    # Ensure LaunchAgents directory exists
    os.makedirs(launch_agents_dir, exist_ok=True)
    
    # Unload if already loaded to avoid cache/state issues
    print("Checking for existing service to unload...")
    subprocess.run(["launchctl", "unload", dest_plist_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Write the plist file
    print(f"Writing LaunchAgent plist to: {dest_plist_path}")
    with open(dest_plist_path, "w", encoding="utf-8") as f:
        f.write(plist_content)
        
    # Correct file permissions (LaunchAgents plists should not be writable by group/other)
    os.chmod(dest_plist_path, 0o644)
    
    # Load the agent
    print("Loading and starting the LaunchAgent service...")
    result = subprocess.run(["launchctl", "load", dest_plist_path], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\nSUCCESS: macOS LaunchAgent service installed and loaded successfully!")
        print(f"Service Label: {plist_label}")
        print(f"Log files are available at:\n  - Stdout: {stdout_log}\n  - Stderr: {stderr_log}")
        print("\nUseful launchctl commands:")
        print(f"  Start:   launchctl load {dest_plist_path}")
        print(f"  Stop:    launchctl unload {dest_plist_path}")
        print(f"  Status:  launchctl list | grep {plist_label}")
    else:
        print(f"\nERROR: Failed to load LaunchAgent service. launchctl output:\n{result.stderr}")

if __name__ == "__main__":
    setup_launch_agent()
