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
    
    # Check existing hashtags
    existing_tags = re.findall(r'#\w+', current_text)
    
    # If already exceeding max_len, cleanly clamp/truncate first
    if len(current_text) > max_len:
        primary_tag = default_tags[0] if (default_tags and default_tags[0].startswith("#")) else (f"#{default_tags[0]}" if default_tags else "")
        needed_space = (len(primary_tag) + 1) if (primary_tag and primary_tag.lower() not in [t.lower() for t in existing_tags]) else 0
        cutoff = max_len - needed_space - 4
        current_text = current_text[:cutoff].rsplit(' ', 1)[0].rstrip('.,:;') + '...'
        if needed_space > 0:
            current_text = f"{current_text} {primary_tag}"
        return current_text.strip()
        
    # If the text already has 2 or more hashtags and is within limits, keep it as is
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
            
    return current_text[:max_len]

# Native Unicode bold alphabet mapping for LinkedIn
_UNICODE_BOLD_MAP = {
    'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
    'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
    'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
    'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
    'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
    's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
    '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
}

def to_unicode_bold(text: str) -> str:
    """Converts alphanumeric text to clean Unicode bold characters visible across all devices."""
    return ''.join(_UNICODE_BOLD_MAP.get(c, c) for c in text)

def clean_linkedin_formatting(text: str) -> str:
    """Removes raw markdown artifacts (*, **, #, ```) and formats LinkedIn posts cleanly with native Unicode bold."""
    if not text:
        return text

    # 1. Remove markdown code fences (e.g. ```text or ```)
    text = re.sub(r'```[a-zA-Z]*\n?', '', text)

    # 2. Replace horizontal dividers (***, ---, ___) with a single clean separator
    text = re.sub(r'^\s*[\*\-_]{3,}\s*$', '──────────────────────────────', text, flags=re.MULTILINE)

    # 3. Convert markdown headers (# Header) to bold text
    def replace_headers(match):
        header_text = match.group(2).strip()
        return '\n' + to_unicode_bold(header_text) + '\n'
    text = re.sub(r'^(#{1,6})\s+(.+)$', replace_headers, text, flags=re.MULTILINE)

    # 4. Convert **bold** markdown to native Unicode bold characters (no raw asterisks!)
    def replace_bold(match):
        return to_unicode_bold(match.group(1))
    text = re.sub(r'\*\*(.+?)\*\*', replace_bold, text)

    # 5. Remove italics asterisks (*text* or _text_)
    text = re.sub(r'(?<!\w)\*([^\*\n]+)\*(?!\w)', r'\1', text)
    text = re.sub(r'(?<!\w)_([^\_\n]+)_(?!\w)', r'\1', text)

    # 6. Remove any remaining stray backticks or lone asterisks
    text = text.replace('`', '')
    text = re.sub(r'(?<!\w)\*(?!\w)', '', text)

    # 7. Normalize excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


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
        """Generates a viral, high-save LinkedIn Technical Cheatsheet & Visual Study Note in the style of top tech creators (90k+ reach playbook)."""
        link_instruction = (
            "Naturally mention our real-time benchmark radar at https://neubench.netlify.app "
            "(e.g., '📊 Tracking real-time latency, token economics, and reasoning scores across 260+ models live on https://neubench.netlify.app')."
        ) if include_link else ""
        prompt = f"""
Topic / Technology: "{title}"
Ecosystem / Framework: "{company}"
Context / Findings: "{summary}"

You are a top tech educator and developer who creates viral technical cheatsheets and visual study notes on LinkedIn (the style that gets 50k-100k+ saves like Roshani Kumari or Alex Xu).

Write a high-utility, beautifully formatted LinkedIn Study Note / Cheatsheet post.

CRITICAL MOBILE-FIRST FORMATTING RULES (80%+ OF USERS READ ON PHONES):
- ❌ NEVER use wide multi-column ASCII tables (no "+---+---+", no "| Col1 | Col2 | Col3 |"). On narrow smartphone screens (30-38 characters wide), tables wrap line-by-line and look broken and unreadable.
- ❌ NEVER use long horizontal arrow flows across a line (e.g. "[A] ──> [B] ──> [C]") as they break mid-box on mobile.
- ✅ ALWAYS use VERTICAL MOBILE SCORECARDS and CLEAN VERTICAL PIPELINES (downward arrows ▼ only):

Structure:
1. 🪝 THE HOOK (First 2 Lines):
   - A high-curiosity, high-utility opener promising to save time or money (e.g. "I spent 40+ hours benchmarking 260+ models on [Topic]. Here is the 1-page visual cheatsheet so you don't burn your cloud budget:").

2. 🗺️ MOBILE CHEATSHEET SCORECARDS (Use vertical card boxes, under 32 chars wide):
   Example:
   ┌──────────────────────────────┐
     ⚡ 𝗦𝗣𝗘𝗘𝗗 & 𝗧𝗧𝗙𝗧
     • Model A: 1.2s – 2.4s
     • Model B: 0.35s (Fastest)
     • Winner: Model B (3x faster)
   └──────────────────────────────┘

   ┌──────────────────────────────┐
     💰 𝗜𝗡𝗙𝗘𝗥𝗘𝗡𝗖𝗘 𝗖𝗢𝗦𝗧𝗦 (1M Tokens)
     • Model A: $3.00 In / $15.00 Out
     • Model B: $0.14 In / $0.28 Out
     • Winner: Model B (95% cheaper)
   └──────────────────────────────┘

3. ⚠️ 3 PRODUCTION PITFALLS / COMMON MISTAKES:
   - 3 numbered, high-signal lessons from real-world engineering (bold takeaway + 1 sentence why most developers get it wrong).

4. 💡 2026 RECOMMENDED STACK (Vertical Flow Only):
   Example:
   [1] 𝗜𝗻𝗰𝗼𝗺𝗶𝗻𝗴 𝗣𝗿𝗼𝗺𝗽𝘁 (Client / User)
     │
     ▼
   [2] 𝗡𝗲𝘂𝗕𝗲𝗻𝗰𝗵 𝗜𝗻𝘁𝗲𝗹𝗹𝗶𝗴𝗲𝗻𝘁 𝗥𝗼𝘂𝘁𝗲𝗿
     ├─► Simple Q&A ➔ Fast Model ($0.14/1M)
     └─► Complex Logic ➔ Heavy Model ($3.00/1M)
     │
     ▼
   [3] 𝗢𝗽𝘁𝗶𝗺𝗶𝘇𝗲𝗱 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 (90% Cost Cut)

5. 📌 SAVE & ENGAGEMENT CTA (Triggers Algorithm Saves & Reposts):
   - "📌 **Save this post** to reference during your next system design or benchmark review."
   {link_instruction}
   - "💬 **Comment 'BENCHMARK' or 'CHEATSHEET' below** and I'll send you the raw PDF comparison sheet."

6. 🏷️ HASHTAGS:
   - 4-5 high-traffic hashtags (e.g. #ArtificialIntelligence #MachineLearning #LLM #SoftwareEngineering #Python).

Rules:
- 100% actionable and authentic. Zero corporate fluff, PR marketing buzzwords, or textbook filler.
- Clean spacing with emojis as bullet points for effortless mobile reading.
- Maximum line width: 34 characters for any diagram or box so it NEVER wraps on mobile!
- Output ONLY the raw post text.
"""
        text = self._generate_with_fallback(
            prompt,
            "You are a top technical educator and systems architect crafting viral cheatsheets and notes on LinkedIn.",
            temperature=0.78
        ).strip('"').strip()
        if include_link and "neubench.netlify.app" not in text:
            text = f"{text}\n\n📊 Tracking real-time latency, cost, and reasoning benchmarks across 260+ models: https://neubench.netlify.app"
        cleaned_text = clean_linkedin_formatting(text)
        return append_hashtags(cleaned_text, ["#ArtificialIntelligence", "#MachineLearning", "#LLM", "#TechInnovation", "#GenerativeAI"], max_len=2950)

    def generate_ai_series_lesson(self, day: int, topic: str, level: str, chapter: str, include_link: bool = True) -> str:
        """Generates an authoritative, mobile-first daily lesson for the 'AI Explained: Zero to Advanced' 90-day master curriculum."""
        link_str = "📊 Live frontier benchmarks across 260+ models on NeuBench: https://neubench.netlify.app\n\n" if include_link else ""
        prompt = f"""
Series: AI Explained: Zero to Advanced (90 Days. 90 Concepts. One AI Journey)
Current Day: Day {day:02d} / 90
Level: {level}
Chapter: {chapter}
Topic: "{topic}"

Role & Persona:
You are an elite AI Researcher and Technical Educator crafting a definitive daily lesson on LinkedIn.
Audience: Developers, QA automation engineers, students, and tech enthusiasts.

CRITICAL PEDAGOGY RULES:
1. GO SLOW & EXPLAIN ONLY THIS ONE TOPIC. Do not jump ahead or explain future concepts.
2. Assume the reader is sharp but new to this specific topic. Zero hand-waving, zero jargon without immediate definition.
3. Keep line width under 32 characters for any diagram so it NEVER wraps on mobile phones.

Structure Required:
A. SERIES HEADER & HOOK:
   🎓 [AI Explained: Zero to Advanced — Day {day:02d}/90]
   A 2-line curiosity hook that stops the scroll.

B. THE CORE INTUITION (Plain English & Simple Analogy):
   Explain WHAT this is and WHY it exists in simple terms before any math or technical jargon.

C. HOW IT WORKS (Mobile Card / Vertical Breakdown):
   Use a clean vertical ASCII card (under 30 chars wide) or step-by-step breakdown (downward arrows ▼ only).

D. REAL-WORLD SOFTWARE & ENGINEERING APPLICATION:
   Connect it directly to real software development, automation, or modern machine learning.

E. 3 KEY TAKEAWAYS:
   3 concise bullet points with bold sub-headers.

F. KNOWLEDGE CHECK & DISCUSSION:
   One thought-provoking question for comments to drive discussion.

G. CONTINUITY & RETENTION:
   - "📌 Hit 'Save' so you don't lose Day {day:02d} for your revision."
   - "🔔 Follow Vishnu Gupta for the full 90-day journey."
   - {link_str}"💬 Comment \"AI90\" below to receive the complete 90-day curriculum roadmap sheet."

H. HASHTAGS:
   4-5 relevant hashtags (e.g. #ArtificialIntelligence #MachineLearning #AIEngineering #Coding #TechEducation).

Rules:
- 100% natural, authoritative, conversational engineer tone.
- Output ONLY the raw post text.
"""
        text = self._generate_with_fallback(
            prompt,
            "You are an elite computer science educator crafting the definitive daily AI curriculum on LinkedIn.",
            temperature=0.75
        ).strip('"').strip()
        cleaned_text = clean_linkedin_formatting(text)
        return append_hashtags(cleaned_text, ["#ArtificialIntelligence", "#MachineLearning", "#AIEngineering", "#Coding", "#TechEducation"], max_len=2950)

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


    def generate_linkedin_comment_reply(self, post_text: str, commenter_name: str, comment_text: str) -> str:
        """
        Generates a courteous, authoritative, and professional B2B engineering reply
        to a comment on our own LinkedIn posts.
        """
        prompt = f"""
Our LinkedIn Post Context:
"{post_text[:350]}..."

Commenter: {commenter_name}
Comment: "{comment_text}"

You are Vishnu Gupta, Founder & Lead AI Engineer at NeuBench (neubench.netlify.app).
Write a professional, warm, and technically sharp reply to this comment.
Guidelines:
- Tone: High-caliber B2B engineering professional, courteous, collegial, and insightful.
- If they asked for a PDF or cheatsheet, tell them you appreciate their interest and will send it over via DM, or invite them to test the live benchmarks directly on NeuBench.
- If they asked a technical or skeptical question, provide a concise, respectful engineering clarification with practical nuance.
- If they simply gave praise or agreement, acknowledge them politely with a brief thought-provoking follow-up question or gratitude.
- Length: 1-3 sentences. Never use generic bot phrases ("Thanks for reaching out!", "Great post!").
- Address them by their first name naturally if available.
- Output ONLY the reply text.
"""
        system_p = "You are a senior AI systems founder on LinkedIn. You write courteous, polished, and technically authoritative B2B responses."
        res = self._generate_with_fallback(prompt, system_p, temperature=0.7)
        return res.strip('"').strip()

    def generate_linkedin_peer_comment(self, post_author: str, post_text: str) -> str:
        """
        Generates a high-signal, professional thought-leadership comment on an external industry leader's LinkedIn post.
        """
        prompt = f"""
LinkedIn Post by {post_author}:
"{post_text[:600]}..."

You are Vishnu Gupta, Founder & Lead AI Engineer at NeuBench.
Write a thoughtful, high-value comment adding technical depth to this discussion.
Guidelines:
- Tone: Professional, collegial, thought-provoking, and constructive (Silicon Valley tech founder style).
- Add a concrete perspective or observation relating to real-world latency, inference economics, evaluation benchmarks, or production reliability.
- Be genuinely supportive of their insight while adding a distinct value-add angle or question.
- Length: 2-4 sentences. Do NOT pitch or overtly plug links unless directly relevant to benchmark data.
- Output ONLY the comment text.
"""
        system_p = "You are a recognized AI systems engineer engaging thoughtfully on LinkedIn. Never sound promotional; always add technical substance."
        res = self._generate_with_fallback(prompt, system_p, temperature=0.75)
        return res.strip('"').strip()

    def generate_first_comment_value_drop(self, post_topic: str, post_text: str) -> str:
        """
        Generates an algorithmic high-engagement 'first-comment' value drop
        (clean takeaway, actionable code tip, or open question linking to NeuBench).
        """
        prompt = f"""
Post Topic: "{post_topic}"
Post Content:
"{post_text[:400]}..."

You are Vishnu Gupta, Founder & Lead AI Engineer at NeuBench (https://neubench.netlify.app).
Generate a high-value 'first comment' to be posted directly under this LinkedIn post.

Guidelines:
- Goal: Spark meaningful technical discussions in the comments while directing readers to live benchmark tools.
- Structure:
  1. A sharp 1-2 sentence engineering takeaway or code implementation tip.
  2. An open question asking developers how they handle this in production.
  3. A natural pointer to test live LLM latency & cost telemetry on NeuBench: https://neubench.netlify.app
- Keep it under 60-80 words. Professional, collegial, and high signal.
- Output ONLY the comment text.
"""
        system_p = "You are a senior AI systems engineer writing an insightful first-comment resource drop on LinkedIn."
        res = self._generate_with_fallback(prompt, system_p, temperature=0.7)
        return res.strip('"').strip()
