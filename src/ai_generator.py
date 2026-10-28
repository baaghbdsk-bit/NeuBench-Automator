import json
import re
from typing import List, Optional
from google import genai
from google.genai import types
import config

SYSTEM_PROMPT = """You are a real, sharp, chronically online human commentator on X (Twitter).
You write like a real person typing on their phone — witty, opinionated, skeptical, and slightly contrarian.

CRITICAL RULES TO SOUND 100% HUMAN & MAXIMIZE REACH:
1. Never place hashtags (#) or robotic emojis at the beginning of sentences. Always append 1-3 targeted hashtags at the very end of original posts to maximize search discovery.
2. NEVER use AI buzzwords: "Delving into", "In conclusion", "Game-changer", "Tapestry", "Fascinating", "Buckle up", "Here is why".
3. Write casually. It's okay to use occasional lowercase starts, natural contractions (don't, can't, honestly, bro, idk), and blunt 1-liners.
4. For Indian context topics: Sound like a sharp Indian tech/internet native (e.g. relatable work culture, Bengaluru traffic/rents, startup drama, corporate irony, "make it make sense").
5. Your goal is to trigger people into arguing or replying. People reply to:
   - Strong unpopular opinions ("Hot take:", "Most people are blind to this...")
   - Calling out corporate or internet hypocrisy
   - Sarcastic or witty observations
6. Keep replies concise. For standalone posts, append 1-3 hashtags (#AI, #Tech) at the very end.
"""

def append_hashtags(text: str, default_tags: List[str], max_len: int = 280) -> str:
    """Ensures relevant hashtags are included at the end of the post without exceeding platform character limits."""
    if not text:
        return text
    
    current_text = text.strip()
    
    # If the text already has 2 or more hashtags, keep it as is
    existing_tags = re.findall(r'#\w+', current_text)
    if len(existing_tags) >= 2:
        return current_text
        
    tags_to_add = []
    for tag in default_tags:
        clean_tag = tag if tag.startswith("#") else f"#{tag}"
        if clean_tag.lower() not in [t.lower() for t in existing_tags]:
            # Test length with tag added
            tentative_tags = " ".join(tags_to_add + [clean_tag])
            if len(f"{current_text} {tentative_tags}") <= max_len:
                tags_to_add.append(clean_tag)
            else:
                break
                
    if tags_to_add:
        tag_str = " ".join(tags_to_add)
        if max_len > 350 and len(f"{current_text}\n\n{tag_str}") <= max_len:
            return f"{current_text}\n\n{tag_str}"
        elif len(f"{current_text} {tag_str}") <= max_len:
            return f"{current_text} {tag_str}"
            
    return current_text

FALLBACK_MODELS = [
    config.GEMINI_MODEL,
    "gemini-3.5-flash-lite",
    "gemini-flash-latest"
]

class AIGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)

    def _generate_with_fallback(self, prompt: str, system_instruction: str, temperature: float = 0.85) -> str:
        """Tries models sequentially in case of 503 high demand spikes."""
        last_error = None
        for model in FALLBACK_MODELS:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                    )
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                last_error = e
                continue
        raise RuntimeError(f"All Gemini models failed: {last_error}")

    def generate_hot_take(self, topic: str, context: str = "") -> str:
        """Generates an original high-engagement polarizing hot take with relevant hashtags."""
        prompt = f"""
Trending topic: "{topic}"
Context: "{context}"

Write ONE punchy, controversial or thought-provoking tweet about this topic.
The tweet must trigger people to reply in the comments (either to agree strongly or disagree passionately).
Include 1-2 relevant, high-traffic hashtags at the end (e.g. #AI #Tech) to maximize reach.
Output ONLY the raw tweet text. Total length strictly under 260 characters.
"""
        text = self._generate_with_fallback(prompt, SYSTEM_PROMPT, temperature=0.9).strip('"').strip()
        return append_hashtags(text, ["#AI", "#Tech"], max_len=275)

    def generate_sniper_reply(self, target_tweet_author: str, target_tweet_text: str) -> str:
        """Generates a sharp, witty or contrarian reply to a viral tweet."""
        prompt = f"""
Viral Tweet by @{target_tweet_author}:
"{target_tweet_text}"

Generate a sharp, witty, or insightful 1-2 sentence reply.
It must:
- Stand out in a crowded comment section.
- Feel 100% human and casual.
- Provoke users reading the thread to like or reply to your comment.
- Output ONLY the reply text. Do NOT include @mention or quotes.
"""
        text = self._generate_with_fallback(prompt, SYSTEM_PROMPT, temperature=0.85)
        return text.strip('"')

    def generate_quote_tweet_commentary(self, target_tweet_author: str, target_tweet_text: str) -> str:
        """Generates sharp, opinionated Quote-Tweet commentary with hashtag for reach."""
        prompt = f"""
Viral Tweet by @{target_tweet_author}:
"{target_tweet_text}"

Generate a punchy, sharp, or witty 1-2 sentence Quote-Tweet commentary.
It must:
- Add a unique, polarizing, or cynical angle to the quoted tweet.
- Make followers want to quote-tweet or debate in your thread.
- Sound 100% human, confident, and concise (under 160 characters).
- Include 1 relevant hashtag at the end (e.g. #AI) if space allows.
- Output ONLY the commentary text. No quotes.
"""
        text = self._generate_with_fallback(prompt, SYSTEM_PROMPT, temperature=0.88).strip('"').strip()
        return append_hashtags(text, ["#AI"], max_len=180)

    def generate_poll_tweet(self, topic: str) -> dict:
        """Generates a poll question and 2-4 options."""
        prompt = f"""
Topic: "{topic}"
Create an interactive poll that people on X won't resist voting on.
Return a valid JSON object with:
- "question": string (under 120 chars, can include 1 hashtag like #AI)
- "options": list of 2 to 4 concise options (each under 25 chars)

Return ONLY valid JSON.
"""
        text = self._generate_with_fallback(prompt, "You output ONLY valid JSON.", temperature=0.8)
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:-3].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:-3].strip()
            return json.loads(cleaned)
        except Exception:
            return {
                "question": f"What's your honest take on {topic}? #AI",
                "options": ["Agree 100%", "Completely wrong", "Too early to tell", "Results"]
            }

    def generate_neubench_take(self, title: str, summary: str = "", company: str = "", include_link: bool = True) -> str:
        """Generates a viral take on a NeuBench AI news story or benchmark model with hashtags & backlinks."""
        link_instruction = (
            "Creatively and naturally include our platform URL 'https://neubench.netlify.app' at the end or within the take "
            "(e.g., 'Tracked the latency & cost live on https://neubench.netlify.app' or 'Full eval breakdown on https://neubench.netlify.app'). "
            "Make it relevant to the topic."
        ) if include_link else "Do not include URLs."
        prompt = f"""
AI News / Model: "{title}"
Developer/Company: "{company}"
Context / Summary: "{summary}"

Write a punchy, opinionated, high-engagement X tweet about this AI update.
Rules:
- Sound 100% like a sharp tech-native commentator (contrarian, witty, zero corporate PR fluff).
- Include 1-2 high-traffic hashtags at the end (e.g., #AI #LLMs #Tech) to maximize search reach.
- Provoke discussion in the replies.
- {link_instruction}
- Total length strictly under 250 characters so hashtags and link fit within 280 chars.
- Output ONLY the raw tweet text.
"""
        text = self._generate_with_fallback(prompt, SYSTEM_PROMPT, temperature=0.88).strip('"').strip()
        if include_link and "neubench.netlify.app" not in text:
            suffix = " Live evals: https://neubench.netlify.app"
            if len(text) + len(suffix) <= 245:
                text = f"{text}{suffix}"
            else:
                text = f"{text[:245 - len(suffix) - 1]}…{suffix}"
        return append_hashtags(text, ["#AI", "#LLMs", "#Tech"], max_len=278)

    def generate_bluesky_take(self, title: str, summary: str = "", company: str = "", include_link: bool = True) -> str:
        """Generates a technical, developer-friendly post for Bluesky with custom-feed hashtags (under 300 chars)."""
        link_instruction = (
            "Include 'https://neubench.netlify.app' creatively at the end (e.g. 'Live benchmarks: https://neubench.netlify.app' or 'Comparing 260+ models on https://neubench.netlify.app')."
        ) if include_link else "Do not include URLs."
        prompt = f"""
Topic: "{title}"
Company/Developer: "{company}"
Context: "{summary}"

Write a Bluesky post about this AI development.
Rules:
- Audience: Open-source developers, researchers, tech builders.
- Tone: Curious, technical, direct, respectful of open standards, zero corporate cringe.
- Include 2-3 targeted technical hashtags at the end (e.g. #AI #MachineLearning #OpenSource) so the post is indexed by Bluesky algorithmic feeds.
- {link_instruction}
- Length: strictly under 255 characters so hashtags and links fit within Bluesky's 300-char limit.
- Output ONLY the post text.
"""
        text = self._generate_with_fallback(prompt, "You write for tech-savvy developers on Bluesky.", temperature=0.8).strip('"').strip()
        if include_link and "neubench.netlify.app" not in text:
            suffix = " | Benchmarks: https://neubench.netlify.app"
            if len(text) + len(suffix) <= 255:
                text = f"{text}{suffix}"
            else:
                text = f"{text[:255 - len(suffix) - 1]}…{suffix}"
        return append_hashtags(text, ["#AI", "#MachineLearning", "#OpenSource"], max_len=295)

    def generate_linkedin_take(self, title: str, summary: str = "", company: str = "", include_link: bool = True) -> str:
        """Generates an in-depth, long-form creative B2B thought-leadership and breaking analysis post for LinkedIn (1,200 to 2,000 characters)."""
        link_instruction = (
            "Seamlessly integrate a benchmark breakdown and call-to-action mentioning https://neubench.netlify.app "
            "(e.g., '📊 Tracking real-time latency, cost-efficiency, and throughput benchmarks across 260+ models on NeuBench: https://neubench.netlify.app')."
        ) if include_link else ""
        prompt = f"""
Topic / Breaking AI News: "{title}"
Company / Ecosystem: "{company}"
Context / Story: "{summary}"

Write a comprehensive, authoritative, and engaging long-form LinkedIn thought-leadership post (1,200 - 1,800 characters).
LinkedIn rewards in-depth analysis, structured storytelling, and tangible insights for engineering leaders, AI founders, and enterprise builders.

Structure:
1. 🔥 BREAKING / INDUSTRY SHIFT HOOK: A bold, curiosity-inducing opening 1-2 lines that stops the scroll in the LinkedIn feed.
2. 💡 THE CONTEXT & WHAT HAPPENED: Unpack the news clearly — explain what actually launched or changed, removing marketing hype and exposing the real mechanics.
3. ⚙️ ARCHITECTURAL & ECONOMIC BREAKDOWN:
   - Provide 3-4 deep-dive bullet points with bold subheadings (e.g. • **Inference Unit Economics:** ..., • **Latency vs Throughput Tradeoffs:** ..., • **Developer & Enterprise Impact:** ...).
   - Explain how this impacts production software, token costs, or system architecture.
4. 📊 BENCHMARK PERSPECTIVE:
   - Relate this to real-world evaluations: how benchmark claims in PR often diverge from live enterprise workloads.
   {link_instruction}
5. 💬 OPEN COMMUNITY QUESTION:
   - End with a thought-provoking, debate-starting question that encourages founders and engineers to share their perspective in the comments.
6. 🏷️ HASHTAGS:
   - Include 4-5 relevant, high-reach professional hashtags on a new line (e.g. #ArtificialIntelligence #MachineLearning #LLM #TechInnovation #GenerativeAI).

Rules:
- High intellectual density, structured with clean spacing and bullet points for effortless mobile reading.
- No corporate platitudes, buzzword soup, or shallow summaries. Provide genuine technical commentary.
- Output ONLY the raw post text.
"""
        text = self._generate_with_fallback(
            prompt,
            "You are a respected AI systems architect and tech executive writing deep-dive analyses on LinkedIn.",
            temperature=0.78
        ).strip('"').strip()
        if include_link and "neubench.netlify.app" not in text:
            text = f"{text}\n\n📊 Tracking real-time frontier benchmarks across 260+ models on NeuBench: https://neubench.netlify.app"
        return append_hashtags(text, ["#ArtificialIntelligence", "#MachineLearning", "#LLM", "#TechTrends", "#GenerativeAI"], max_len=2900)

    def generate_threads_take(self, title: str, summary: str = "", company: str = "", include_link: bool = True) -> str:
        """Generates a casual, conversational discussion post for Threads with hashtags."""
        link_instruction = (
            "Creatively add 'https://neubench.netlify.app' below the post (e.g. 'Ran the evals on https://neubench.netlify.app' or 'Full comparison on https://neubench.netlify.app')."
        ) if include_link else ""
        prompt = f"""
Topic: "{title}"
Context: "{summary}"

Write a casual, conversational post for Threads that invites people to share their experience or opinion.
- Friendly, curiosity-driven, easy to read on mobile.
- Include 2-3 popular hashtags at the bottom (e.g. #AI #Tech #Developers #Coding) to boost algorithmic discovery on Threads.
- {link_instruction}
- Under 380 characters.
- Output ONLY the post text.
"""
        text = self._generate_with_fallback(prompt, "You are an authentic mobile creator writing for Threads.", temperature=0.85).strip('"').strip()
        if include_link and "neubench.netlify.app" not in text:
            suffix = "\n\nChecked the evals on https://neubench.netlify.app"
            if len(text) + len(suffix) <= 400:
                text = f"{text}{suffix}"
        return append_hashtags(text, ["#AI", "#Tech", "#Developers"], max_len=480)

    def generate_reddit_post(self, title: str, summary: str = "", company: str = "", subreddit: str = "r/LocalLLaMA", include_link: bool = True) -> dict:
        """Generates a high-value, community-tailored Reddit post with markdown formatting."""
        link_str = "\n\n*Benchmarks tracked on [NeuBench](https://neubench.netlify.app) • Open source engine on [GitHub](https://github.com/baaghbdsk-bit/NeuBench-Automator)*" if include_link else ""
        prompt = f"""
Topic: "{title}"
Developer/Company: "{company}"
Context: "{summary}"
Target Subreddit: "{subreddit}"

Write an authentic, highly engaging Reddit post for this subreddit.
Format:
Return a JSON object with:
1. "title": An informative, natural Reddit post title (no buzzwords, no clickbait, fits {subreddit} style).
2. "body": Markdown formatted body with:
   - **TL;DR:** 1-2 sentence core takeaway.
   - **Key Findings & Benchmark Analysis:** 2-3 clear analytical paragraphs or bullet points explaining what this means for developers/builders.
   - **Community Discussion:** 1 provocative question asking the community about their experience or real-world benchmarks.
   {link_str}

Rules:
- Sound like an active, genuine technical community member. Zero corporate PR fluff.
- Output ONLY valid JSON with keys "title" and "body".
"""
        raw = self._generate_with_fallback(prompt, "You are a respected technical developer writing on Reddit. Output ONLY valid JSON.", temperature=0.75)
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:-3].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:-3].strip()
            return json.loads(cleaned)
        except Exception:
            return {
                "title": f"[Discussion] {title}: Benchmark analysis & takeaways",
                "body": f"**TL;DR:** {summary}\n\nKey analysis on {title} by {company}.\n\nWhat are you seeing in your real-world workloads?{link_str}"
            }
