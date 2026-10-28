"""
Autonomous LinkedIn AI Network Builder.
Follows top AI thought leaders, researchers, and frontier AI labs on LinkedIn
with humanized pacing and safety checks.
"""
import sys
import os
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from playwright.sync_api import sync_playwright
import config

NETWORK_LOG_FILE = BASE_DIR / "linkedin_network.json"

TOP_AI_TARGETS = [
    # Top AI Companies & Research Labs
    {"name": "Anthropic", "url": "https://www.linkedin.com/company/anthropic/"},
    {"name": "OpenAI", "url": "https://www.linkedin.com/company/openai/"},
    {"name": "Google DeepMind", "url": "https://www.linkedin.com/company/googledeepmind/"},
    {"name": "Hugging Face", "url": "https://www.linkedin.com/company/huggingface/"},
    {"name": "Perplexity AI", "url": "https://www.linkedin.com/company/perplexity-ai/"},
    {"name": "Cohere", "url": "https://www.linkedin.com/company/cohere-ai/"},
    {"name": "Mistral AI", "url": "https://www.linkedin.com/company/mistralai/"},
    {"name": "Scale AI", "url": "https://www.linkedin.com/company/scaleai/"},
    {"name": "NVIDIA", "url": "https://www.linkedin.com/company/nvidia/"},
    {"name": "LangChain", "url": "https://www.linkedin.com/company/langchain/"},
    {"name": "Pinecone", "url": "https://www.linkedin.com/company/pinecone-io/"},
    {"name": "Together AI", "url": "https://www.linkedin.com/company/together-ai/"},
    {"name": "LlamaIndex", "url": "https://www.linkedin.com/company/llamaindex/"},
    {"name": "Groq", "url": "https://www.linkedin.com/company/groq/"},
    {"name": "Weights & Biases", "url": "https://www.linkedin.com/company/wandb/"},
    {"name": "ElevenLabs", "url": "https://www.linkedin.com/company/elevenlabs/"},
    {"name": "RunPod", "url": "https://www.linkedin.com/company/runpod/"},
    {"name": "Modal", "url": "https://www.linkedin.com/company/modal-labs/"},
    {"name": "Databricks", "url": "https://www.linkedin.com/company/databricks/"},
    {"name": "Weaviate", "url": "https://www.linkedin.com/company/weaviate-io/"},

    # Top AI Pioneers, Researchers & Thought Leaders (Personal Profiles)
    {"name": "Andrew Ng", "url": "https://www.linkedin.com/in/andrewyng/"},
    {"name": "Yann LeCun", "url": "https://www.linkedin.com/in/yann-lecun/"},
    {"name": "Sam Altman", "url": "https://www.linkedin.com/in/samaltman/"},
    {"name": "Satya Nadella", "url": "https://www.linkedin.com/in/satyanadella/"},
    {"name": "Demis Hassabis", "url": "https://www.linkedin.com/in/demishassabis/"},
    {"name": "Fei-Fei Li", "url": "https://www.linkedin.com/in/fei-fei-li-4541910/"},
    {"name": "Sebastian Raschka", "url": "https://www.linkedin.com/in/sebastianraschka/"},
    {"name": "Jim Fan", "url": "https://www.linkedin.com/in/dr-jim-fan/"},
    {"name": "Allie K. Miller", "url": "https://www.linkedin.com/in/alliekmiller/"},
    {"name": "Cassie Kozyrkov", "url": "https://www.linkedin.com/in/kozyrkov/"},
    {"name": "Chip Huyen", "url": "https://www.linkedin.com/in/chiphuyen/"},
    {"name": "Clement Delangue", "url": "https://www.linkedin.com/in/clementdelangue/"},
    {"name": "Harrison Chase", "url": "https://www.linkedin.com/in/harrison-chase-961287118/"},
    {"name": "Jerry Liu", "url": "https://www.linkedin.com/in/jerry-liu-64390711/"},
    {"name": "Aravind Srinivas", "url": "https://www.linkedin.com/in/aravind-srinivas-14a84976/"},
    {"name": "Alexandr Wang", "url": "https://www.linkedin.com/in/alexandr-wang/"},
    {"name": "Arthur Mensch", "url": "https://www.linkedin.com/in/arthur-mensch/"},
    {"name": "Aidan Gomez", "url": "https://www.linkedin.com/in/aidan-gomez-7a269299/"},
    {"name": "Mustafa Suleyman", "url": "https://www.linkedin.com/in/mustafa-suleyman-093845/"},
    {"name": "Greg Brockman", "url": "https://www.linkedin.com/in/thegregbrockman/"},
    {"name": "Ethan Mollick", "url": "https://www.linkedin.com/in/emollick/"},
    {"name": "Swyx (Shawn Wang)", "url": "https://www.linkedin.com/in/shawnswyxwang/"},
    {"name": "Linus Ekenstam", "url": "https://www.linkedin.com/in/linusekenstam/"},
    {"name": "Matt Wolfe", "url": "https://www.linkedin.com/in/maboris/"},
    {"name": "Rowan Cheung", "url": "https://www.linkedin.com/in/rowancheung/"},
    {"name": "Zain Kahn", "url": "https://www.linkedin.com/in/zainkahn/"},
    {"name": "Julien Chaumond", "url": "https://www.linkedin.com/in/julien-c/"},
    {"name": "Thomas Wolf", "url": "https://www.linkedin.com/in/thomas-wolf-5390748/"},
    {"name": "Francois Chollet", "url": "https://www.linkedin.com/in/fchollet/"},
    {"name": "Jeremy Howard", "url": "https://www.linkedin.com/in/howardjeremy/"},
    {"name": "Lex Fridman", "url": "https://www.linkedin.com/in/lexfridman/"},
    {"name": "Pedro Domingos", "url": "https://www.linkedin.com/in/pedro-domingos-80a568/"},
    {"name": "Percy Liang", "url": "https://www.linkedin.com/in/percyliang/"},
    {"name": "Dan Hendrycks", "url": "https://www.linkedin.com/in/dan-hendrycks/"},
    {"name": "Richard Socher", "url": "https://www.linkedin.com/in/richard-socher/"},
    {"name": "Ilya Sutskever", "url": "https://www.linkedin.com/in/ilyasutskever/"},
]

def load_network_log() -> Dict[str, Any]:
    if NETWORK_LOG_FILE.exists():
        try:
            return json.loads(NETWORK_LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"followed": [], "last_run": 0}

def save_network_log(data: Dict[str, Any]):
    try:
        NETWORK_LOG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Error saving network log: {e}")

def follow_top_network(max_count: int = 50, headless: bool = True) -> int:
    """Follows target AI leaders and organizations on LinkedIn."""
    log_data = load_network_log()
    already_followed = set(log_data.get("followed", []))

    targets = [t for t in TOP_AI_TARGETS if t["url"] not in already_followed]
    if not targets:
        print("All predefined targets have already been followed!")
        return 0

    to_follow = targets[:max_count]
    print(f"🚀 Starting LinkedIn Network Expansion: Target = {len(to_follow)} profiles/companies")

    followed_count = 0

    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(config.LINKEDIN_USER_DATA_DIR),
            "headless": headless,
            "viewport": {"width": 1280, "height": 800},
            "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        }
        context = p.chromium.launch_persistent_context(**launch_kwargs)
        page = context.pages[0] if context.pages else context.new_page()

        for idx, target in enumerate(to_follow):
            name = target["name"]
            url = target["url"]
            print(f"[{idx+1}/{len(to_follow)}] Navigating to {name} ({url}) ...")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(random.randint(2200, 3200))

                if "unavailable" in page.url.lower():
                    print(f"  ⚠️ Page unavailable: {url}")
                    continue

                # Locate Follow button on profile or company page
                follow_btn = None
                candidates = page.locator('main button:has-text("Follow"), button[aria-label^="Follow"]').all()
                for c in candidates:
                    try:
                        if c.is_visible():
                            txt = c.inner_text().strip().lower()
                            aria = (c.get_attribute("aria-label") or "").lower()
                            if "following" not in txt and "following" not in aria:
                                if "follow" in txt or "follow" in aria:
                                    follow_btn = c
                                    break
                    except Exception:
                        continue

                if follow_btn:
                    try:
                        follow_btn.click(force=True, timeout=5000)
                    except Exception:
                        follow_btn.dispatch_event("click")
                    followed_count += 1
                    already_followed.add(url)
                    log_data["followed"] = list(already_followed)
                    log_data["last_run"] = time.time()
                    save_network_log(log_data)
                    print(f"  ✅ Successfully Followed {name}! (Total: {followed_count})")
                    time.sleep(random.uniform(2.5, 4.0))

                    # Also click 1 recommended follow button on this page if available
                    recommended_btns = page.locator('button[aria-label^="Follow "]').all()
                    for rb in recommended_btns[:2]:
                        try:
                            if rb.is_visible():
                                r_aria = (rb.get_attribute("aria-label") or "").strip()
                                r_name = r_aria.replace("Follow ", "").strip()
                                if r_name and r_name.lower() not in [n.lower() for n in log_data.get("followed_names", [])]:
                                    try:
                                        rb.click(force=True, timeout=3000)
                                    except Exception:
                                        rb.dispatch_event("click")
                                    followed_count += 1
                                    log_data.setdefault("followed_names", []).append(r_name)
                                    save_network_log(log_data)
                                    print(f"    ➕ Also Followed Recommended AI Peer: {r_name}!")
                                    time.sleep(random.uniform(2.0, 3.5))
                                    break
                        except Exception:
                            pass
                else:
                    is_already_following = False
                    following_indicators = page.locator('button:has-text("Following"), button[aria-label*="Following"]').all()
                    for f in following_indicators:
                        try:
                            if f.is_visible():
                                is_already_following = True
                                break
                        except Exception:
                            pass

                    if is_already_following:
                        print(f"  ℹ️ Already following {name}.")
                        already_followed.add(url)
                        log_data["followed"] = list(already_followed)
                        save_network_log(log_data)
                    else:
                        print(f"  ⚠️ Follow button not located for {name}.")

            except Exception as e:
                print(f"  ❌ Error interacting with {name}: {e}")
                time.sleep(2)

        context.close()

    print(f"\n🎉 Network Expansion Complete! Successfully followed {followed_count} AI leaders/labs on LinkedIn.")
    return followed_count

if __name__ == "__main__":
    count = 35
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
    follow_top_network(max_count=count, headless=True)
