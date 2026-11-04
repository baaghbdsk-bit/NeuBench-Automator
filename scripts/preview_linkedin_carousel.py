import argparse
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ai_generator import AIGenerator
from src.linkedin_visuals import (
    render_linkedin_carousel,
    render_linkedin_hero,
    render_linkedin_loop_gif,
)
from src.trend_hunter import LINKEDIN_PILLAR_ROTATION, TrendHunter

SAMPLE_PLAN = {
    "pillar": "NEWS",
    "cover": {
        "kicker": "SECURITY BRIEF",
        "headline": "What the Binance breach should change about your API keys",
        "subhead": "A major crypto exchange incident forces teams to review custodial access.",
    },
    "slides": [
        {
            "kicker": "01 / WHAT HAPPENED",
            "title": "A major security incident",
            "body": "A prominent crypto exchange reports a security incident affecting user funds. Developers and finance teams are now reviewing how they connect to exchanges and custodial APIs.",
            "takeaway": "Custodial API connections face renewed scrutiny.",
        },
        {
            "kicker": "02 / WHY IT MATTERS",
            "title": "Unbounded operational access",
            "body": "Many integration setups rely on broad permissions that remain active indefinitely. When an edge service or token leaks, the blast radius includes direct fund access.",
            "takeaway": "Static keys grant excessive operational power.",
        },
        {
            "kicker": "03 / WHAT TO DO",
            "title": "Restrict permissions immediately",
            "body": "Audit every active integration. Disable withdrawal capabilities on keys that only require read or trade execution access, and shorten token lifespans.",
            "takeaway": "Enforce the principle of least privilege.",
        },
    ],
    "framework": {
        "kicker": "THE CHECKLIST",
        "title": "API Key Audit Protocol",
        "steps": [
            {"label": "Revoke unused keys", "detail": "Delete any token without active traffic over the past thirty days."},
            {"label": "Isolate withdrawals", "detail": "Separate financial transfer permissions from standard workflows."},
            {"label": "Bind IP addresses", "detail": "Restrict key usage to specific, known server addresses."},
        ],
    },
    "cta": {
        "kicker": "ONE MORE THING",
        "headline": "Audit one key today",
        "subtext": "Pick your highest privilege token and remove one permission it does not need.",
        "website": "app.neubench.workers.dev",
    },
    "post_text": "A major crypto exchange reports a security incident affecting user funds. Most integration setups still rely on broad permissions that never expire. That combination turns a single leaked token into direct fund access. Audit every active integration today. Disable withdrawal access on keys that only need read or trade permissions. Shorten token lifespans. Which of your keys still has permissions it has never used?",
    "first_comment": "Start with the key that has withdrawal access. Remove it if the integration does not need it.\n\nhttps://app.neubench.workers.dev",
    "alt_text": "A technical carousel outlining API key security steps after a major exchange breach.",
    "hashtags": ["#CyberSecurity", "#DevOps", "#Engineering"],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a LinkedIn carousel preview.")
    parser.add_argument("--pillar", choices=LINKEDIN_PILLAR_ROTATION + ["NEWS", "EXPLAINER", "SURVIVAL", "BENCHMARK"], default="NEWS")
    parser.add_argument("--topic", default="", help="Override the discovered topic title.")
    parser.add_argument("--summary", default="", help="Context passed to the plan generator.")
    parser.add_argument("--sample", action="store_true", help="Render the built-in sample without calling Gemini.")
    parser.add_argument("--gif", action="store_true", help="Also render the loop GIF.")
    args = parser.parse_args()

    if args.sample:
        plan = SAMPLE_PLAN
        topic = plan["cover"]["headline"]
    else:
        topic = args.topic.strip()
        summary = args.summary.strip()
        if not topic:
            trends = TrendHunter().get_linkedin_topics(pillar=args.pillar)
            if not trends:
                raise SystemExit(f"No LinkedIn topics discovered for pillar {args.pillar}")
            trend = trends[0]
            topic = str(trend.get("title", "")).strip()
            summary = str(trend.get("summary", ""))
        print(f"Topic: {topic}")
        plan = AIGenerator().generate_linkedin_carousel_plan(topic, summary, pillar=args.pillar)

    assets = render_linkedin_carousel(plan)
    hero = render_linkedin_hero(plan, base_name=assets["base"])
    plan_path = Path(assets["folder"]) / "plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(plan, ensure_ascii=False, indent=2))
    print(f"PLAN: {plan_path}")
    print(f"PDF:  {assets['pdf_path']}")
    print(f"HERO: {hero}")
    print(f"PNG:  {assets['folder']}")
    if args.gif:
        print(f"GIF:  {render_linkedin_loop_gif(plan, base_name=assets['base'])}")


if __name__ == "__main__":
    main()
