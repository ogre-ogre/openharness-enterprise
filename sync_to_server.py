#!/usr/bin/env python3
"""Sync .env to server and restart service."""

import subprocess
import sys

# Server config
HOST = "10.1.7.155"
USER = "ai-app"
PASSWORD = "asb#1234"
REMOTE_PATH = "/home/ai-app/oh-enterprise-1.0.0/.env"
LOCAL_PATH = r"D:\openharness-enterprise\.env"

def main():
    print(f"[*] Uploading {LOCAL_PATH} to {HOST}:{REMOTE_PATH}")
    
    # Use pscp or scp with password
    # Try with plink/pscp if available, otherwise use expect-style approach
    
    # Method 1: Try pscp (PuTTY's scp)
    pscp_cmd = [
        "pscp",
        "-pw", PASSWORD,
        LOCAL_PATH,
        f"{USER}@{HOST}:{REMOTE_PATH}"
    ]
    
    try:
        result = subprocess.run(pscp_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[OK] File uploaded successfully")
        else:
            print(f"[!] pscp failed: {result.stderr}")
            # Try alternative method
            raise FileNotFoundError("pscp not found or failed")
    except FileNotFoundError:
        # Method 2: Use echo with ssh (password will be prompted)
        print("[!] pscp not found, trying ssh with password...")
        print("[*] Please manually run:")
        print(f"    scp {LOCAL_PATH} {USER}@{HOST}:{REMOTE_PATH}")
        print(f"    Password: {PASSWORD}")
        sys.exit(1)
    
    # Restart service
    print(f"[*] Restarting service on {HOST}")
    
    # SSH command to restart
    ssh_cmd = [
        "plink",
        "-pw", PASSWORD,
        f"{USER}@{HOST}",
        "cd /home/ai-app/oh-enterprise-1.0.0 && pkill -f 'oh-enterprise' ; nohup uv run oh-enterprise start --port 8000 > logs/server.log 2>&1 &"
    ]
    
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
        print(f"[OK] Service restarted")
        print(result.stdout)
    except FileNotFoundError:
        print("[!] plink not found")
        print("[*] Please manually run:")
        print(f"    ssh {USER}@{HOST}")
        print(f"    Password: {PASSWORD}")
        print("    Then run: cd /home/ai-app/oh-enterprise-1.0.0 && pkill -f 'oh-enterprise' ; nohup uv run oh-enterprise start --port 8000 > logs/server.log 2>&1 &")
        sys.exit(1)

if __name__ == "__main__":
    main()