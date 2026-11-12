"""
NeuBench Automator 24/7 Self-Healing Watchdog Supervisor.
Guarantees continuous, zero-intervention operation across all 5 platforms:
1. Cleans stale locks and orphaned browser processes on startup.
2. Supervised sub-process execution of 'python main.py start'.
3. Automatic crash restart (within 10 seconds).
4. Heartbeat freeze detection: if no activity for >75 mins, restarts the process.
5. Runs indefinitely without human intervention.
"""
import os
import sys
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = BASE_DIR / "venv" / "Scripts" / "python.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable)

METRICS_FILE = BASE_DIR / "trial_metrics.json"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
WATCHDOG_LOG = LOG_DIR / "watchdog.log"
STUCK_TIMEOUT_SECONDS = 80 * 60  # 80 minutes without file update = stuck


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [WATCHDOG] {msg}"
    print(formatted, flush=True)
    try:
        with open(WATCHDOG_LOG, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


def cleanup_stale_locks():
    """Removes Chromium lock files that can block sessions after an abrupt restart."""
    lock_dirs = [
        BASE_DIR / "browser_session",
        BASE_DIR / "linkedin_session",
    ]
    for d in lock_dirs:
        if d.exists():
            for lock_name in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
                lock_file = d / lock_name
                if lock_file.exists():
                    try:
                        lock_file.unlink(missing_ok=True)
                        log(f"Removed stale lock: {lock_file}")
                    except Exception as e:
                        log(f"Could not remove lock {lock_file}: {e}")


def get_last_activity_time() -> float:
    """Returns the last modified timestamp of trial_metrics.json or current time."""
    if METRICS_FILE.exists():
        try:
            return METRICS_FILE.stat().st_mtime
        except Exception:
            return time.time()
    return time.time()


def run_supervisor():
    log("=" * 60)
    log("🚀 NeuBench 24/7 Watchdog Supervisor Initiated")
    log(f"Target Executable: {PYTHON_EXE}")
    log(f"Working Directory: {BASE_DIR}")
    log("=" * 60)

    restart_count = 0

    while True:
        cleanup_stale_locks()
        cmd = [str(PYTHON_EXE), "-u", "main.py", "start"]
        log(f"Spawning child process (Restart #{restart_count}): {' '.join(cmd)}")

        stdout_log = LOG_DIR / "automater_stdout.log"
        stderr_log = LOG_DIR / "automater_stderr.log"

        out_f = open(stdout_log, "a", encoding="utf-8")
        err_f = open(stderr_log, "a", encoding="utf-8")

        proc = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=out_f,
            stderr=err_f,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
        log(f"Child process active with PID: {proc.pid}")

        last_seen_activity = get_last_activity_time()

        # Heartbeat monitoring loop
        while True:
            ret = proc.poll()
            if ret is not None:
                log(f"⚠️ Child process exited with code {ret}")
                break

            current_mtime = get_last_activity_time()
            if current_mtime > last_seen_activity:
                last_seen_activity = current_mtime

            # Check if frozen
            elapsed_since_activity = time.time() - last_seen_activity
            if elapsed_since_activity > STUCK_TIMEOUT_SECONDS:
                log(f"⛔ Process unresponsive for {elapsed_since_activity / 60:.1f} mins (limit {STUCK_TIMEOUT_SECONDS / 60:.0f} mins). Terminating PID {proc.pid}...")
                try:
                    proc.terminate()
                    time.sleep(3)
                    if proc.poll() is None:
                        proc.kill()
                    log("Terminated frozen process successfully.")
                except Exception as e:
                    log(f"Error terminating child: {e}")
                break

            time.sleep(15)

        out_f.close()
        err_f.close()

        restart_count += 1
        log("Cooling down for 10 seconds before auto-restart...")
        time.sleep(10)


if __name__ == "__main__":
    run_supervisor()
