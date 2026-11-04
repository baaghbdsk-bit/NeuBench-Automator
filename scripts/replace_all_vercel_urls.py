import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {".git", "venv", "browser_session", "linkedin_session", "threads_session", "reddit_session", "twitter_session", "__pycache__", ".system_generated"}

replaced_count = 0
for root, dirs, files in os.walk(BASE_DIR):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for file in files:
        if file.endswith((".py", ".html", ".md", ".json", ".bat", ".txt", ".js")):
            p = Path(root) / file
            try:
                content = p.read_text(encoding="utf-8")
                if "app.neubench.workers.dev" in content:
                    new_content = content.replace("app.neubench.workers.dev", "app.neubench.workers.dev")
                    p.write_text(new_content, encoding="utf-8")
                    print(f"Updated: {p.relative_to(BASE_DIR)}")
                    replaced_count += 1
            except Exception as e:
                pass

print(f"Total files updated: {replaced_count}")
