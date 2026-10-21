import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.trend_hunter import TrendHunter
from src.ai_generator import AIGenerator

def test_pipeline():
    print("\n" + "="*60)
    print("🔥 TESTING TREND HUNTER & AI CONTENT GENERATION")
    print("="*60 + "\n")
    
    hunter = TrendHunter()
    ai = AIGenerator()
    
    print("🔍 Fetching trending topics...")
    trends = hunter.get_curated_trending_topics()
    print(f"✅ Found {len(trends)} trending discussions.\n")
    
    if not trends:
        print("❌ No trends found. Using fallback topic.")
        sample_topic = "Will AI agents replace 90% of software engineers by 2027?"
        sample_context = "Massive debate in tech Twitter regarding autonomous coding agents and junior developer job prospects."
    else:
        sample = trends[0]
        sample_topic = sample["title"]
        sample_context = sample.get("summary", "")
        print(f"📌 Sample Topic: {sample_topic}")
        print(f"🌐 Source: {sample.get('source')} | Traffic/Score: {sample.get('traffic', sample.get('score', 'High'))}\n")

    print("🤖 Generating High-Engagement Polarizing Hot Take...")
    tweet = ai.generate_hot_take(sample_topic, sample_context)
    print(f"\n[Generated Tweet ({len(tweet)} chars)]:\n👉 {tweet}\n")

    print("-" * 50)
    print("🎯 Generating Sniper Reply to a Viral Tweet...")
    reply = ai.generate_sniper_reply("elonmusk", "AI will be smarter than any single human by next year.")
    print(f"\n[Sniper Reply ({len(reply)} chars)]:\n👉 {reply}\n")

    print("-" * 50)
    print("📊 Generating Interactive Poll...")
    poll = ai.generate_poll_tweet(sample_topic)
    print(f"\nQuestion: {poll.get('question')}")
    for idx, opt in enumerate(poll.get("options", []), 1):
        print(f"  Option {idx}: {opt}")
    
    print("\n" + "="*60)
    print("✨ TEST COMPLETED SUCCESSFULLY!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_pipeline()
