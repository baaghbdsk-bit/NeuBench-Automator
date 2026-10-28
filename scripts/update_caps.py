import sys
from pathlib import Path

sched_path = Path("src/scheduler.py")
code = sched_path.read_text(encoding="utf-8")

code = code.replace("if today_li >= 2:", "if today_li >= 6:")
code = code.replace("if today_rd >= 1:", "if today_rd >= 6:")
code = code.replace("if today_th >= 2:", "if today_th >= 6:")

sched_path.write_text(code, encoding="utf-8")
print("OK: Updated individual platform caps to 6/day")
