from pathlib import Path

files = [
    Path("src/ai_generator.py"),
    Path("src/bluesky_client.py"),
    Path("src/linkedin_client.py"),
    Path("src/trend_hunter.py"),
    Path("src/web/app.py"),
    Path("README.md")
]

for f in files:
    if f.exists():
        content = f.read_text(encoding="utf-8")
        if "neubench.vercel.app" in content:
            new_content = content.replace("neubench.vercel.app", "neubench.netlify.app")
            f.write_text(new_content, encoding="utf-8")
            print(f"Updated URL in {f}")
        else:
            print(f"No match in {f}")
