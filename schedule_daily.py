#!/usr/bin/env python3
"""
schedule_daily.py
=================
Schedule main.py to run automatically every day at a set time.
Uses Windows Task Scheduler — set it once, forget it forever.

Usage:
    python schedule_daily.py          # schedules at 09:00 AM
    python schedule_daily.py 10:30    # schedules at 10:30 AM
"""
import sys
import os
import subprocess
from datetime import datetime


def schedule_windows(hour: int, minute: int, python_exe: str, script_path: str):
    """Register a Windows Task Scheduler task."""
    task_name = "YouTubeKidsShortsAI"
    time_str  = f"{hour:02d}:{minute:02d}"

    cmd = [
        "schtasks", "/Create",
        "/TN",       task_name,
        "/TR",       f'"{python_exe}" "{script_path}"',
        "/SC",       "DAILY",
        "/ST",       time_str,
        "/F",        # overwrite if exists
        "/RL",       "HIGHEST",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅  Task '{task_name}' scheduled daily at {time_str}")
        print(f"   Python : {python_exe}")
        print(f"   Script : {script_path}")
        print(f"\nTo remove it later: schtasks /Delete /TN {task_name} /F")
    else:
        print(f"❌  Scheduling failed: {result.stderr}")
        print("Try running this script as Administrator.")


def main():
    # Parse time argument
    time_arg = sys.argv[1] if len(sys.argv) > 1 else "09:00"
    try:
        h, m = map(int, time_arg.split(":"))
    except ValueError:
        print(f"Invalid time format '{time_arg}' — use HH:MM (e.g. 09:00)")
        sys.exit(1)

    python_exe  = sys.executable
    script_path = os.path.abspath("main.py")

    print("=" * 60)
    print("  YouTube Shorts — Daily Auto-Scheduler")
    print("=" * 60)
    print(f"\nScheduling: python main.py   every day at {h:02d}:{m:02d}\n")

    schedule_windows(h, m, python_exe, script_path)


if __name__ == "__main__":
    main()
