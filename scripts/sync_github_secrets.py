import sys
import subprocess
import json
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

secrets_file = Path("cloud_exports/github_secrets.json")
data = json.loads(secrets_file.read_text(encoding="utf-8"))

for k, v in data.items():
    print(f"Setting GitHub Secret {k} ({len(v)} chars)...")
    proc = subprocess.run(["gh", "secret", "set", k], input=v.encode("utf-8"), capture_output=True)
    if proc.returncode == 0:
        print(f"  OK: Secret {k} set successfully!")
    else:
        print(f"  ERR setting {k}:", proc.stderr.decode("utf-8", errors="ignore"))

print("\nListing active GitHub secrets:")
subprocess.run(["gh", "secret", "list"])
