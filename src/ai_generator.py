import json
import re
import random
from typing import List, Optional, Dict, Any, Tuple
from google import genai
from google.genai import types
import config

X_UNHINGED_SYSTEM_PROMPT = """You are a chronically online, razor-sharp, witty, and culturally observant commentator on X (Twitter).
Your persona is completely unfiltered, witty, sarcastic, and engaging—commenting on whatever is the talk of the town: mega cinema and blockbuster buzz (e.g. Ramayana, Bollywood, Hollywood), internet trends, viral cultural discourse, corporate absurdities, everyday human realities, sports, and tech drama.

KEY PRINCIPLES:
1. TONE: Sarcastic, razor-witted, hilarious, perceptive, and deeply relatable. Zero corporate cringe, zero forced politeness.
2. SCOPE: Jump on whatever is trending or talk of the town—cinema & epic films (Ramayana, big releases), viral memes, pop culture debates, tech innovations, and life absurdities.
3. FORMAT: Short, punchy, punchline-heavy tweets (under 240 chars). Write like a real human typing on their phone.
4. HASHTAGS: ALWAYS include 1 or 2 relevant, high-reach hashtags at the end of the tweet (e.g. #Ramayana, #Bollywood, #Cinema, #AI, #TechTrends, #Cricket). Keep them punchy and organic to boost algorithmic reach.
5. ENGAGEMENT: Make it impossible not to quote-tweet, argue with, or retweet.
"""

CASUAL_SYSTEM_PROMPT = X_UNHINGED_SYSTEM_PROMPT
SYSTEM_PROMPT = X_UNHINGED_SYSTEM_PROMPT

PROFESSIONAL_TECH_SYSTEM_PROMPT = """You are a distinguished Principal Software Engineer and AI Systems Architect writing authoritative, high-signal technical content.
Target Audience: Developers, tech leads, students, and engineers ranging from school level to senior architects.
Tone: Highly professional, crystal clear, pedagogically brilliant, zero buzzwords, grounded in real-world systems engineering.
Niche: Software engineering fundamentals, AI & ML architectures, daily terminology breakdowns (e.g. Git rebase vs merge, LLM vs SLM, KV cache, RAG vs Fine-tuning), and breaking tech news.
Mission: Demystify complex concepts so a student understands the intuition and a senior engineer appreciates the architectural nuance.
"""

BLUESKY_SYSTEM_PROMPT = """You are a distinguished AI systems architect writing on Bluesky (AT Protocol).
Audience: Elite software engineers, distributed systems builders, and AI researchers.
Tone: Highly professional, collegial, technically rigorous, and deeply grounded in engineering principles.
Values: Real-world latency, inference economics, memory hierarchies, reproducibility, and transparent evaluations.
Formatting: Clear, concise (under 280 characters), accompanied by technical hashtags (#SoftwareEngineering #SystemDesign #AI #Programming). Zero corporate fluff, zero hype.
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


_REVERSE_BOLD = {value: key for key, value in _UNICODE_BOLD_MAP.items()}


def _plain_linkedin_text(value: object, strip_urls: bool = True) -> str:
    if value is None:
        return ""
    text = str(value)
    text = "".join(_REVERSE_BOLD.get(ch, ch) for ch in text)
    text = text.replace("\u2014", ", ").replace("\u2013", "-").replace("\u2011", "-").replace("\u00a0", " ")
    if strip_urls:
        text = re.sub(r"https?://\S+", "", text)
    text = text.replace("**", "").replace("__", "").replace("`", "").replace("*", "")
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clamp_text(value: object, limit: int, strip_urls: bool = True) -> str:
    text = _plain_linkedin_text(value, strip_urls=strip_urls)
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0].rstrip(".,;:")
    return clipped or text[:limit]


FALLBACK_MODELS = [
    config.GEMINI_MODEL,
    "gemini-3.5-flash",
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
        """Generates a razor-sharp, hilarious, sarcastic, or culturally observant tweet for X with mandatory 1-2 hashtags."""
        prompt = f"""
Topic / Debate / Talk of the Town: "{topic}"
Context: "{context}"

Write ONE razor-sharp, sarcastic, witty, or culturally observant tweet about this topic.
Rules:
- Scope: Whatever is the talk of the town—cinema, Ramayana, movies, pop culture, sports, internet drama, tech, everyday life.
- Tone: Sarcastic, razor-witted, hilarious, or perceptive. Zero corporate cringe.
- Length: Punchy and strictly under 235 characters so hashtags fit cleanly.
- HASHTAGS: ALWAYS include 1 or 2 high-reach, relevant trending hashtags at the end (e.g. #Ramayana, #Bollywood, #Cinema, #AI, #TechTrends, #Cricket, or specific topic tags).
- Output ONLY the raw tweet text.
"""
        text = self._generate_with_fallback(prompt, X_UNHINGED_SYSTEM_PROMPT, temperature=0.94).strip('"').strip()

        # Enforce at least 1-2 hashtags for reach
        if "#" not in text:
            # Extract high-signal hashtag from topic words
            clean_words = [re.sub(r'[^a-zA-Z0-9]', '', w.title()) for w in topic.split() if len(w) > 3]
            fallback_tags = [f"#{w}" for w in clean_words[:2]] if clean_words else ["#Trending", "#TalkOfTheTown"]
            text = append_hashtags(text, fallback_tags, max_len=275)
        return text

    def generate_casual_x_take(self, topic: str = "", context: str = "") -> str:
        """Sarcastic & funny hot take generator for X."""
        return self.generate_hot_take(topic, context)

    def generate_sniper_reply(self, target_tweet_author: str, target_tweet_text: str) -> str:
        """Generates a sharp, sarcastic, witty, or roasting reply to a viral tweet on X."""
        prompt = f"""
Tweet by @{target_tweet_author}:
"{target_tweet_text}"

Generate a sharp, sarcastic, funny, or roasting 1-sentence reply.
Rules:
- Stand out instantly in a crowded thread with savage wit or devastating humor.
- Unfiltered, funny, taking part in the debate without fear.
- Zero corporate speak, zero cringe.
- Output ONLY the reply text. Do NOT include @mention or quotes.
"""
        text = self._generate_with_fallback(prompt, X_UNHINGED_SYSTEM_PROMPT, temperature=0.92)
        return text.strip('"')

    def generate_quote_tweet_commentary(self, target_tweet_author: str, target_tweet_text: str) -> str:
        """Generates sharp, sarcastic, or hilarious Quote-Tweet commentary on X."""
        prompt = f"""
Tweet by @{target_tweet_author}:
"{target_tweet_text}"

Generate a punchy, sarcastic, or hilarious 1-sentence Quote-Tweet reaction.
Rules:
- Brutally funny, roasting the tweet or exposing the absurdity.
- Under 160 characters.
- Output ONLY the commentary text. No quotes.
"""
        text = self._generate_with_fallback(prompt, X_UNHINGED_SYSTEM_PROMPT, temperature=0.92).strip('"').strip()
        return text

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
            "Creatively and naturally include our platform URL 'https://app.neubench.workers.dev' at the end or within the take "
            "(e.g., 'Tracked the latency & cost live on https://app.neubench.workers.dev' or 'Full eval breakdown on https://app.neubench.workers.dev'). "
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
        if include_link and "app.neubench.workers.dev" not in text:
            suffix = " Live evals: https://app.neubench.workers.dev"
            if len(text) + len(suffix) <= 245:
                text = f"{text}{suffix}"
            else:
                text = f"{text[:245 - len(suffix) - 1]}…{suffix}"
        return append_hashtags(text, ["#AI", "#LLMs", "#Tech"], max_len=278)

    def generate_bluesky_take(self, title: str, summary: str = "", company: str = "", include_link: bool = True) -> str:
        """Generates an authoritative, systems/open-weights focused post for Bluesky with AT Protocol custom feed tags (under 300 chars)."""
        link_instruction = (
            "Include 'https://app.neubench.workers.dev' concisely at the end (e.g. 'Benchmarks: https://app.neubench.workers.dev' or 'Compare live: https://app.neubench.workers.dev')."
        ) if include_link else "Do not include URLs."
        prompt = f"""
Topic: "{title}"
Company/Developer: "{company}"
Context: "{summary}"

Write an authoritative, developer-first Bluesky post about this topic.
Rules:
- Audience: engineers, builders, and technical readers.
- Tone: sharp, honest, and focused on the real trade-off, mechanism, or implication in the topic. Zero corporate PR fluff.
- Match the topic: news, research, explainers, comparisons, scenarios, and career advice all need different framing.
- Include 2-3 targeted technical hashtags at the end (#AI #MachineLearning #Engineering) to index into Bluesky's top custom feeds.
- {link_instruction}
- Length: strictly under 250 characters so hashtags and links fit within Bluesky's 300-char limit.
- Output ONLY the post text.
"""
        text = self._generate_with_fallback(prompt, BLUESKY_SYSTEM_PROMPT, temperature=0.72).strip('"').strip()
        if include_link and "app.neubench.workers.dev" not in text:
            suffix = " | Benchmarks: https://app.neubench.workers.dev"
            if len(text) + len(suffix) <= 255:
                text = f"{text}{suffix}"
            else:
                text = f"{text[:255 - len(suffix) - 1]}…{suffix}"
        return append_hashtags(text, ["#AI", "#OpenSource", "#MachineLearning", "#LocalLLMs"], max_len=295)

    def generate_bluesky_sniper_reply(self, target_author: str, target_text: str) -> str:
        """Generates a professional, thoughtful, and technically rigorous reply on Bluesky."""
        prompt = f"""
Bluesky Post by @{target_author}:
"{target_text[:400]}"

Write a professional, technically insightful 1-2 sentence reply.
Guidelines:
- Audience: Open-source engineers, systems builders, AI researchers.
- Tone: Professional, collegial, intellectually curious, and grounded in engineering facts or latency/inference trade-offs.
- Do NOT sound casual or snarky. Maintain high technical standards.
- Output ONLY the reply text. Do NOT include @mentions or quotes.
"""
        text = self._generate_with_fallback(prompt, BLUESKY_SYSTEM_PROMPT, temperature=0.72)
        return text.strip('"').strip()

    def generate_linkedin_concept_article(self, concept: Dict[str, Any]) -> str:
        """
        Generates an authoritative, masterclass LinkedIn educational breakdown article.
        Bridges school-level intuition to senior engineering architecture.
        Covers the mental model, deep technical mechanics, comparison scorecard, production rule of thumb, and pitfall.
        """
        title = concept.get("title", "Software Architecture Breakdown")
        cat = concept.get("category", "SYSTEM DESIGN")
        school_ana = concept.get("school_analogy", "")
        pro_nuance = concept.get("pro_nuance", "")
        golden_rule = concept.get("golden_rule", "")
        ca = concept.get("concept_a", {})
        cb = concept.get("concept_b", {})

        prompt = f"""
CONCEPT TITLE: "{title}"
CATEGORY: "{cat}"
SCHOOL-LEVEL INTUITION: "{school_ana}"
PRO-LEVEL NUANCE: "{pro_nuance}"
GOLDEN ENGINEERING RULE: "{golden_rule}"
CONCEPT A: {ca.get('name')}: {ca.get('how_it_works')} (Analogy: {ca.get('analogy')}, Best for: {ca.get('best_for')})
CONCEPT B: {cb.get('name')}: {cb.get('how_it_works')} (Analogy: {cb.get('analogy')}, Best for: {cb.get('best_for')})

Write an authoritative, viral, high-value LinkedIn Educational Article explaining this concept so clearly that a beginner understands the mental model while a senior engineer saves it for reference.

FORMAT RULES (MOBILE OPTIMIZED):
1. 🪝 THE HOOK (First 2 Lines): Clear, bold contrast or question that stops the scroll.
2. 🧒 THE SIMPLE MENTAL MODEL (Explain like I'm in school): 1-2 sentences with an intuitive everyday analogy that makes the concept click instantly.
3. ⚙️ HOW IT WORKS UNDER THE HOOD (Professional Level): Clear explanation of what actually happens in code, memory, pointers, git commits, or network frames.
4. ⚔️ HEAD-TO-HEAD COMPARISON: Clean vertical scorecard or scannable bullet comparison of tradeoffs (Speed, Complexity, Memory, Best Use Case).
5. 💡 SENIOR ARCHITECT RULE OF THUMB: The practical decision heuristic experienced engineers use in production.
6. ⚠️ THE #1 MISTAKE TO AVOID: The subtle pitfall that trips up developers.
7. 💬 ENGAGEMENT QUESTION: A thoughtful question inviting developers to share their production experience.
8. 🏷️ HASHTAGS: #SoftwareEngineering #SystemDesign #Programming #ComputerScience #Tech #Developers

CRITICAL GUIDELINES:
- Zero corporate fluff, zero generic motivational filler.
- Clean spacing with emojis for visual anchors.
- Do NOT include any external links or URLs in the text (LinkedIn penalizes links). The interactive benchmark tracker is mentioned for the first comment.
- Output ONLY the finished post text.
"""
        text = self._generate_with_fallback(
            prompt,
            PROFESSIONAL_TECH_SYSTEM_PROMPT,
            temperature=0.74
        ).strip('"').strip()
        cleaned_text = clean_linkedin_formatting(text)
        return append_hashtags(cleaned_text, ["#SoftwareEngineering", "#SystemDesign", "#Programming", "#Tech", "#ComputerScience"], max_len=2950)

    def generate_bluesky_concept_post(self, concept: Dict[str, Any]) -> str:
        """
        Generates a crisp, high-signal technical post for Bluesky AT Protocol (under 280 chars)
        highlighting the core architectural difference, golden rule, and benchmark link.
        """
        title = concept.get("title", "Tech Architecture")
        golden_rule = concept.get("golden_rule", "")
        school_ana = concept.get("school_analogy", "")

        prompt = f"""
Topic: "{title}"
Core Rule: "{golden_rule}"
Analogy: "{school_ana}"

Write a concise, professional, high-signal Bluesky post about this technical distinction.
Rules:
- Length: strictly under 240 characters so hashtags fit within Bluesky's 300-char limit.
- Tone: Highly professional, developer-focused, clear contrast or insight.
- Zero buzzwords.
- Output ONLY the post text.
"""
        text = self._generate_with_fallback(prompt, BLUESKY_SYSTEM_PROMPT, temperature=0.70).strip('"').strip()
        return append_hashtags(text, ["#SoftwareEngineering", "#SystemDesign"], max_len=285)

    def generate_linkedin_take(self, title: str, summary: str = "", company: str = "", include_link: bool = False) -> str:
        """Generates a viral, high-save LinkedIn Technical Cheatsheet & Visual Study Note in the style of top tech creators (90k+ reach playbook)."""
        link_instruction = (
            "Naturally mention our real-time benchmark radar at https://app.neubench.workers.dev "
            "(e.g., '📊 Tracking real-time latency, token economics, and reasoning scores across 260+ models live on https://app.neubench.workers.dev')."
        ) if include_link else "CRITICAL: Do NOT include ANY external links, URLs, or domains in the post body. LinkedIn's 360Brew algorithm cuts post reach by 40% when external links are in the body. The interactive benchmark link is dropped in the first comment."
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

4. 💡 2026 RECOMMENDED ARCHITECTURE / STACK (Vertical Flow Only):
   Example:
   [1] 𝗜𝗻𝗰𝗼𝗺𝗶𝗻𝗴 𝗣𝗿𝗼𝗺𝗽𝘁 (Client / User)
     │
     ▼
   [2] 𝗜𝗻𝘁𝗲𝗹𝗹𝗶𝗴𝗲𝗻𝘁 𝗥𝗼𝘂𝘁𝗲𝗿
     ├─► Simple Q&A ➔ Fast Model ($0.14/1M)
     └─► Complex Logic ➔ Heavy Model ($3.00/1M)
     │
     ▼
   [3] 𝗢𝗽𝘁𝗶𝗺𝗶𝘇𝗲𝗱 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 (90% Cost Cut)

5. 📌 SAVE & ENGAGEMENT CTA (Triggers Algorithm Saves & Dwell Time):
   - "📌 **Save this post** to reference during your next system design or benchmark review."
   - "💬 **What is your go-to stack for this?** Drop your thoughts below — and check the first comment for the interactive benchmark tracker! 👇"

6. 🏷️ HASHTAGS:
   - 4-5 high-traffic engineering hashtags (e.g. #MachineLearning #ArtificialIntelligence #SoftwareEngineering #LLM #SystemDesign).

Rules:
- 100% actionable and authentic. Zero corporate fluff, PR marketing buzzwords, or textbook filler.
- Clean spacing with emojis as bullet points for effortless mobile reading.
- Maximum line width: 34 characters for any diagram or box so it NEVER wraps on mobile!
- {link_instruction}
- Output ONLY the raw post text.
"""
        text = self._generate_with_fallback(
            prompt,
            "You are a top technical educator and systems architect crafting viral cheatsheets and notes on LinkedIn.",
            temperature=0.78
        ).strip('"').strip()
        if include_link and "app.neubench.workers.dev" not in text:
            text = f"{text}\n\n📊 Tracking real-time latency, cost, and reasoning benchmarks across 260+ models: https://app.neubench.workers.dev"
        elif not include_link:
            # Strip any accidental URLs to guarantee zero link reach penalty from LinkedIn's 360Brew algorithm
            text = re.sub(r'https?://\S+', '', text).strip()
            text = re.sub(r'\n{3,}', '\n\n', text)
        cleaned_text = clean_linkedin_formatting(text)
        return append_hashtags(cleaned_text, ["#MachineLearning", "#ArtificialIntelligence", "#SoftwareEngineering", "#LLM", "#SystemDesign"], max_len=2950)

    def _generate_json(self, prompt: str, system_instruction: str, temperature: float = 0.72) -> dict:
        last_error = None
        for model in FALLBACK_MODELS:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        response_mime_type="application/json",
                    ),
                )
                if response and response.text:
                    return json.loads(response.text)
            except Exception as error:
                last_error = error
                continue
        raise RuntimeError(f"All Gemini models failed: {last_error}")

    def generate_linkedin_carousel_plan(
        self,
        title: str,
        summary: str = "",
        pillar: str = "NEWS",
        recent_hooks: Optional[List[str]] = None,
    ) -> dict:
        """Builds a slide-by-slide carousel plan plus matching LinkedIn caption."""
        avoided = "; ".join((recent_hooks or [])[:5]) or "none"
        prompt = f"""
Topic: "{title}"
Context: "{summary}"
Content pillar: {pillar}

Write for the pillar above. Do not make the post about a brand.

Recent posts opened with these lines. Do not reuse their opening structure:
{avoided}

You are a technical editor for a live AI benchmark site. Write for engineers, founders, and technical operators. The carousel should be specific, useful, and worth saving. It should not sound like an AI assistant or a growth hacker.

Pillar guidance:
- NEWS: explain what happened, why it matters, and what to do next.
- EXPLAINER: define the mechanism in plain language.
- DIFFERENCE: compare two terms or approaches and when to choose each.
- DID_YOU_KNOW: lead with one surprising but accurate technical fact.
- WHAT_IF: explore one realistic scenario and its engineering consequence.
- SURVIVAL: give practical career or workflow advice.
- BENCHMARK: explain how to measure or compare systems fairly.

Return ONLY valid JSON in this exact shape:
{{
  "pillar": "{pillar}",
  "cover": {{"kicker": "SECURITY BRIEF", "headline": "...", "subhead": "..."}},
  "slides": [
    {{"kicker": "01 / WHAT HAPPENED", "title": "...", "body": "...", "takeaway": "..."}},
    {{"kicker": "02 / WHY IT MATTERS", "title": "...", "body": "...", "takeaway": "..."}},
    {{"kicker": "03 / WHAT TO DO", "title": "...", "body": "...", "takeaway": "..."}}
  ],
  "framework": {{"kicker": "THE CHECKLIST", "title": "...", "steps": [{{"label": "...", "detail": "..."}}, {{"label": "...", "detail": "..."}}, {{"label": "...", "detail": "..."}}]}},
  "cta": {{"kicker": "ONE MORE THING", "headline": "...", "subtext": "...", "website": "app.neubench.workers.dev"}},
  "post_text": "...",
  "first_comment": "...",
  "alt_text": "...",
  "hashtags": ["#MachineLearning", "#ArtificialIntelligence", "#Engineering"]
}}

Rules:
- Use only facts present in the topic or context. Never invent a number, date, name, quote, funding amount, or study result. If a metric is not provided, describe the risk or the action qualitatively instead.
- Use the named company, product, model, or incident from the topic. Do not swap a provided name for a generic label like "a major exchange" or "a leading model".
- Open the caption with the most concrete fact in the context, not a generic statement about the industry.
- Never use em dashes or en dashes. Use a period, comma, or colon.
- Do not open with "I spent", "Here is", "Let us dive in", "In today's", "Game changer", "Unlock", or "The future of".
- Each slide makes one point. Cover headline <= 70 chars, subhead <= 120 chars.
- Slide title <= 60 chars, body <= 240 chars, takeaway <= 120 chars.
- Framework: 3 or 4 steps. Label <= 30 chars, detail <= 90 chars.
- Cover subhead states the consequence for the reader, not a generic industry observation.
- CTA headline <= 60 chars and gives one concrete action tied to this topic that the reader can do today. Do not use a generic "test your systems" or "benchmark your workflows" pitch unless the topic is about benchmarks. Keep the website field as app.neubench.workers.dev.
- post_text: 600 to 1000 chars. Plain text only. No markdown, no bold, no tables, no URLs, no emoji bullets. Short lines. End with one specific question. Do not mention a first comment.
- first_comment: <= 350 chars. Reference one specific step from the framework, then add https://app.neubench.workers.dev. No invented stats.
- alt_text: <= 180 chars, describe what the carousel shows.
- hashtags: 3 to 5 specific tags. Mix one broad tag with two or three topic-specific tags. Avoid generic tags like #Tech or #Business. Do not repeat the same three tags on every post.
"""
        system = "You are a precise LinkedIn technical editor. You write plain, specific English and you never invent facts."
        raw = self._generate_json(prompt, system)
        plan = self._normalize_carousel_plan(raw, title, pillar)
        if (
            len(plan["slides"]) < 3
            or len(plan["framework"]["steps"]) < 3
            or not plan["post_text"]
            or any(not slide["title"] or not slide["body"] for slide in plan["slides"])
            or any(not step["label"] for step in plan["framework"]["steps"])
        ):
            raise RuntimeError("Gemini returned an incomplete carousel plan")
        return plan

    def _normalize_carousel_plan(self, raw: object, title: str, pillar: str) -> dict:
        data = raw if isinstance(raw, dict) else {}
        cover_raw = data.get("cover") if isinstance(data.get("cover"), dict) else {}
        cover = {
            "kicker": _clamp_text(cover_raw.get("kicker") or pillar, 40),
            "headline": _clamp_text(cover_raw.get("headline") or title, 70),
            "subhead": _clamp_text(cover_raw.get("subhead") or "", 120),
        }

        slides = []
        for index, item in enumerate(data.get("slides") or []):
            if not isinstance(item, dict):
                continue
            slides.append(
                {
                    "kicker": _clamp_text(item.get("kicker") or f"0{index + 1} / KEY POINT", 40),
                    "title": _clamp_text(item.get("title") or "", 60),
                    "body": _clamp_text(item.get("body") or "", 240),
                    "takeaway": _clamp_text(item.get("takeaway") or "", 120),
                }
            )
            if len(slides) == 3:
                break

        framework_raw = data.get("framework") if isinstance(data.get("framework"), dict) else {}
        steps = []
        for item in framework_raw.get("steps") or []:
            if not isinstance(item, dict):
                continue
            steps.append(
                {
                    "label": _clamp_text(item.get("label") or "", 30),
                    "detail": _clamp_text(item.get("detail") or "", 90),
                }
            )
            if len(steps) == 4:
                break
        framework = {
            "kicker": _clamp_text(framework_raw.get("kicker") or "THE CHECKLIST", 40),
            "title": _clamp_text(framework_raw.get("title") or "A short checklist", 60),
            "steps": steps,
        }

        cta_raw = data.get("cta") if isinstance(data.get("cta"), dict) else {}
        cta = {
            "kicker": _clamp_text(cta_raw.get("kicker") or "ONE MORE THING", 40),
            "headline": _clamp_text(cta_raw.get("headline") or "Save this for your next review.", 70),
            "subtext": _clamp_text(cta_raw.get("subtext") or "", 150),
            "website": _clamp_text(cta_raw.get("website") or "app.neubench.workers.dev", 48),
        }

        hashtags = [str(tag).strip() for tag in (data.get("hashtags") or []) if str(tag).strip().startswith("#")]
        if len(hashtags) < 3:
            hashtags = ["#MachineLearning", "#ArtificialIntelligence", "#Engineering", "#LLM"]

        post_text = _clamp_text(data.get("post_text") or "", 2900)
        if len(post_text.strip()) < 800:
            post_text = self.generate_full_linkedin_article(
                topic=str(cover.get("headline") or "System Architecture"),
                summary=str(cover.get("subhead") or ""),
                format_type=_clamp_text(data.get("pillar") or pillar, 32)
            )

        res = {
            "pillar": _clamp_text(data.get("pillar") or pillar, 32),
            "cover": cover,
            "slides": slides,
            "framework": framework,
            "cta": cta,
            "post_text": post_text,
            "first_comment": _clamp_text(data.get("first_comment") or "", 350, strip_urls=False),
            "alt_text": _clamp_text(data.get("alt_text") or cover["headline"], 180),
            "hashtags": hashtags[:5],
        }
        if data.get("pages") and isinstance(data["pages"], list):
            res["pages"] = data["pages"]
        return res

    def generate_full_linkedin_article(
        self,
        topic: str,
        summary: str = "",
        concept_a: str = "",
        concept_b: str = "",
        format_type: str = "explainer",
        target_audience: str = "working_pro",
        visual_format: str = "animated_flow_gif"
    ) -> str:
        """
        Generates an authoritative, highly descriptive, multi-paragraph LinkedIn article
        (1,200 to 2,000 characters) with hook, intuition, mechanics, trade-offs, and discussion.
        Matches the visual format (animated flow GIF vs notebook carousel vs hero image).
        """
        audience_notes = {
            "school_kid": "Explain with crystal-clear, relatable everyday analogies so even a curious teenager grasps the intuition.",
            "college_student": "Focus on core algorithms, memory/compute mental models, and software engineering foundations.",
            "working_pro": "Focus on production software trade-offs, architecture choices, and real-world system design.",
            "staff_engineer": "Focus on distributed systems scaling, tail latency (p99), failure domains, and operational invariants.",
            "ai_curious": "Focus on frontier LLM mechanics, inference optimization, memory bandwidth, and GPU compute efficiency."
        }
        aud_note = audience_notes.get(target_audience, audience_notes["working_pro"])

        comp_context = f"\nComparing: '{concept_a}' vs '{concept_b}'" if (concept_a and concept_b) else ""

        if visual_format == "notebook_carousel":
            visual_ref_instruction = 'Include a natural line referencing the attached 6-page field notes: "I broke down the complete mechanics, implementation code, and production traps into a 6-page study note field guide attached below."'
        elif visual_format == "hero_image":
            visual_ref_instruction = 'Include a natural line referencing the attached technical infographic: "I mapped the core architectural trade-offs into the visual blueprint attached below."'
        else:
            visual_ref_instruction = 'Include a natural line referencing the attached animated blueprint: "I created this animated visual guide to map the entire lifecycle step by step."'

        prompt = f"""You are an elite Principal Software Architect and Technical Educator writing an authoritative, highly engaging LinkedIn article.

Topic: "{topic}"
Summary / Context: "{summary}"{comp_context}
Audience Tier: {target_audience} ({aud_note})

STRUCTURE REQUIREMENTS (1,200 to 1,900 characters total):
1. THE SCROLL-STOPPING HOOK:
   Start with an eye-opening metric, striking paradox, or real-world comparison that stops the feed scroll immediately (e.g. parameter count contrast, latency gap, or hidden production bottleneck).
2. PLAIN-ENGLISH INTUITION:
   Explain WHAT this concept is and WHY it exists in simple, visual language. Zero gatekeeping, zero buzzwords without clear definition.
3. UNDER-THE-HOOD EXECUTION LIFECYCLE:
   Walk through the exact step-by-step flow of what happens when a request or token enters the system. Detail the journey from ingestion to routing, execution, and output.
4. THE PRODUCTION CATCH & TRADE-OFFS:
   Address the architectural trade-offs that only experienced engineers know (e.g. memory footprint vs compute, cache invalidation, routing skew, operational overhead, failure modes).
5. VISUAL REFERENCE:
   {visual_ref_instruction}
6. DISCUSSION QUESTION:
   End with one specific, open-ended question that invites software engineers and architects to share their production experiences in the comments.
7. FORMATTING RULES:
   - Use clean, short paragraphs (1 to 3 sentences each) separated by double newlines.
   - Use simple bullet points (- ) where appropriate.
   - NO markdown bolding with asterisks (use plain text for LinkedIn compatibility).
   - NO emojis overload. Keep it clean, editorial, and highly professional.
   - End with 4-5 relevant hashtags.
"""
        system_instruction = (
            "You are a world-class Systems Architect and Technical Educator on LinkedIn. "
            "Write descriptive, high-signal, deeply informative technical articles that engineers love to read and save. "
            "Output ONLY the complete article text."
        )
        try:
            text = self._generate_with_fallback(prompt, system_instruction, temperature=0.7).strip('"').strip()
            if len(text) >= 600:
                return text
        except Exception as e:
            print(f"[AIGenerator] Full article generation notice: {e}")

        comp_str = f" between {concept_a} and {concept_b}" if (concept_a and concept_b) else ""
        fallback_ref = (
            "I broke down the complete mechanics, implementation code, and production traps into a 6-page study note field guide attached below."
            if visual_format == "notebook_carousel"
            else "I mapped out the complete step-by-step architecture and execution lifecycle in the animated diagram below."
        )
        return (
            f"{topic}\n\n"
            f"Understanding the real-world mechanics of {topic}{comp_str} is one of the most critical fundamentals in modern systems design.\n\n"
            f"{summary or 'Most explanations focus only on textbook definitions, but production reality hits hard boundaries around memory, latency, and scaling.'}\n\n"
            f"Here is how it actually works under the hood:\n\n"
            f"1. Ingestion & Invariants: The incoming payload enters the runtime boundary where initial validation occurs.\n"
            f"2. Routing & Dispatch: Instead of processing every path uniformly, the system selectively routes work based on state or probability weights.\n"
            f"3. Execution: Active workers execute the core logic while idle resources remain dormant to preserve compute.\n"
            f"4. Recombination: Results are synthesized, validated, and returned with minimal serialization overhead.\n\n"
            f"The engineering catch:\n"
            f"- Compute efficiency often comes at the cost of memory footprint.\n"
            f"- Load distribution requires active balancing to prevent hotspotting and queue saturation.\n"
            f"- Tail latency (p99) must be continuously measured against synthetic load spikes.\n\n"
            f"{fallback_ref}\n\n"
            f"How are you currently handling this in your production architecture?\n\n"
            f"#SoftwareEngineering #SystemDesign #ComputerScience #Programming #CloudArchitecture"
        )

    def generate_editorial_architecture_spec(
        self,
        title: str,
        summary: str = "",
        category: str = "SYSTEMS ARCHITECTURE",
        target_audience: str = "working_pro"
    ) -> dict:
        """
        Dynamically generates a 100% topic-specific architecture diagram specification
        for the 1080x1350 editorial GIF renderer.
        Never relies on hardcoded generic components or fallbacks.
        """
        clean_title = title.strip()
        prompt = f"""You are an elite Principal Systems Architect and Technical Illustrator.
Topic: "{clean_title}"
Context / Summary: "{summary}"
Category: "{category}"
Audience: "{target_audience}"

Your task is to design an authentic, highly specific technical blueprint / architecture diagram specification for this EXACT topic.
The diagram has:
1. INPUT: What raw data, signal, query, or packet enters this specific system? (e.g. for Active Noise Cancellation: 'EXT MIC ACOUSTIC WAVE'; for Bloom Filter: 'SEARCH KEY / ITEM'; for Raft Consensus: 'CLIENT WRITE COMMAND'; for GPU AllReduce: 'LOCAL GRADIENT TENSOR'; for CDC: 'DATABASE WAL EVENT').
2. ROUTER / GATEWAY: What core processing element or algorithm ingests and routes it? (e.g. for Noise Cancellation: 'DSP ADC & FIR Filter'; for Bloom Filter: 'K Independent Hash Functions'; for Raft: 'Raft Leader Log Engine'; for GPU AllReduce: 'Ring Pipeline Controller'; for CDC: 'WAL Log Reader & Parser').
3. COMPONENTS (Exactly 4 boxes): The 4 real, concrete internal components or workers for THIS SPECIFIC TOPIC (NEVER use generic names like 'Parser & Schema', 'Core Engine', 'Cache Layer', 'Storage Sink'). At least 2 should be active.
4. METRICS (Exactly 3 bars): Real-world engineering benchmarks, latency budgets, or resource consumption for this topic with concrete units (e.g. microseconds, dB attenuation, VRAM, bits/key, FLOPs, or IOPS).
5. LIFECYCLE STEPS (Exactly 4 stages): The 4 chronological stages of execution when a payload moves through this system.

Return valid JSON with this exact schema:
{{
  "title": "{clean_title}",
  "subtitle": "Short 1-line subtitle explaining the core mechanism (under 75 chars)",
  "input_label": "Specific input under 22 chars",
  "router_label": "Specific engine under 24 chars",
  "components": [
    {{"name": "Specific Component 1 (under 20 chars)", "role": "Precise role (under 28 chars)", "active": true, "score": "HOT"}},
    {{"name": "Specific Component 2 (under 20 chars)", "role": "Precise role (under 28 chars)", "active": true, "score": "ACTIVE"}},
    {{"name": "Specific Component 3 (under 20 chars)", "role": "Precise role (under 28 chars)", "active": false}},
    {{"name": "Specific Component 4 (under 20 chars)", "role": "Precise role (under 28 chars)", "active": true, "score": "SYNC"}}
  ],
  "metrics": [
    {{"label": "Specific Metric 1 (under 24 chars)", "val": "Realistic value with units (under 30 chars)", "pct": 0.85, "color": "emerald"}},
    {{"label": "Specific Metric 2 (under 24 chars)", "val": "Realistic value with units (under 30 chars)", "pct": 0.65, "color": "amber"}},
    {{"label": "Specific Metric 3 (under 24 chars)", "val": "Realistic value with units (under 30 chars)", "pct": 0.40, "color": "slate"}}
  ],
  "steps": [
    {{"num": "1", "name": "Stage 1 Name (under 24 chars)", "desc": "Concrete description of stage 1 (under 65 chars)"}},
    {{"num": "2", "name": "Stage 2 Name (under 24 chars)", "desc": "Concrete description of stage 2 (under 65 chars)"}},
    {{"num": "3", "name": "Stage 3 Name (under 24 chars)", "desc": "Concrete description of stage 3 (under 65 chars)"}},
    {{"num": "4", "name": "Stage 4 Name (under 24 chars)", "desc": "Concrete description of stage 4 (under 65 chars)"}}
  ]
}}
"""
        system = "You are an elite Systems Architect. Output strictly valid JSON conforming to the schema. Make all labels, components, and metrics 100% specific to the given topic. Never use generic placeholder names."
        try:
            data = self._generate_json(prompt, system, temperature=0.6)
            if (
                data
                and isinstance(data.get("components"), list)
                and len(data["components"]) >= 4
                and isinstance(data.get("metrics"), list)
                and len(data["metrics"]) >= 3
                and isinstance(data.get("steps"), list)
                and len(data["steps"]) >= 4
            ):
                data["title"] = clean_title
                data.setdefault("subtitle", (summary[:72] if summary else f"How {clean_title[:45]} operates end-to-end").strip())
                return data
        except Exception as e:
            print(f"[AIGenerator] Dynamic architecture spec LLM generation notice: {e}")

        return self._build_deterministic_architecture_spec(clean_title, summary)

    def _build_deterministic_architecture_spec(self, title: str, summary: str = "") -> dict:
        """Topic-aware deterministic fallback that detects domain keywords rather than emitting static placeholders."""
        tl = title.lower()
        if any(w in tl for w in ["noise", "sound", "headphone", "audio", "acoustic"]):
            return {
                "title": title,
                "subtitle": "How anti-sound phase inversion cancels acoustic waves in real time",
                "input_label": "EXT MIC ACOUSTIC",
                "router_label": "DSP Sampling & ADC",
                "components": [
                    {"name": "External Mic ADC", "role": "30µs ambient sampling", "active": True, "score": "HOT"},
                    {"name": "Adaptive FIR Filter", "role": "LMS coefficient tuning", "active": True, "score": "ACTIVE"},
                    {"name": "Feedback Sensor", "role": "In-ear error residual", "active": False},
                    {"name": "180° Inverter DAC", "role": "Anti-sound wave output", "active": True, "score": "PHASE 180°"},
                ],
                "metrics": [
                    {"label": "Algorithmic Latency", "val": "28 microseconds", "pct": 0.88, "color": "emerald"},
                    {"label": "Noise Attenuation", "val": "-28 dB at 250 Hz", "pct": 0.90, "color": "amber"},
                    {"label": "Silicon Power Draw", "val": "< 7.5 mW per earbud", "pct": 0.22, "color": "slate"},
                ],
                "steps": [
                    {"num": "1", "name": "Acoustic Capture", "desc": "External mic samples air pressure fluctuations at 96 kHz"},
                    {"num": "2", "name": "Adaptive Modeling", "desc": "LMS filter estimates transfer function and room acoustics"},
                    {"num": "3", "name": "Phase Inversion", "desc": "DSP synthesizes 180-degree inverted anti-noise signal"},
                    {"num": "4", "name": "Destructive Collision", "desc": "Speaker pushes anti-sound; waves flatten at eardrum"},
                ]
            }
        elif any(w in tl for w in ["bloom", "filter", "hash"]):
            return {
                "title": title,
                "subtitle": "Probabilistic membership testing with guaranteed zero false negatives",
                "input_label": "SEARCH KEY / ITEM",
                "router_label": "K Independent Hash Vector",
                "components": [
                    {"name": "Murmur3 Hashers", "role": "Computes k bit positions", "active": True, "score": "HOT"},
                    {"name": "Shared Bit Array", "role": "In-memory atomic bit probe", "active": True, "score": "ACTIVE"},
                    {"name": "Early-Exit Detector", "role": "Instant false if any bit 0", "active": True, "score": "FAST-PATH"},
                    {"name": "Disk / Storage DB", "role": "Verify bounded false positive", "active": False},
                ],
                "metrics": [
                    {"label": "Query Latency (p99)", "val": "< 120 nanoseconds", "pct": 0.95, "color": "emerald"},
                    {"label": "Space Efficiency", "val": "9.6 bits per stored key", "pct": 0.35, "color": "slate"},
                    {"label": "False Positive Rate", "val": "Bounded strictly at 1.0%", "pct": 0.15, "color": "amber"},
                ],
                "steps": [
                    {"num": "1", "name": "Key Ingestion", "desc": "Receives lookup key and feeds into k independent hash seeds"},
                    {"num": "2", "name": "Bit Index Mapping", "desc": "Computes array indices via modulo bit-array size m"},
                    {"num": "3", "name": "Atomic Bit Probe", "desc": "Tests if all mapped bit positions contain 1s"},
                    {"num": "4", "name": "Verdict Resolution", "desc": "Returns DEFINITELY NO or PROBABLY YES to caller"},
                ]
            }
        elif any(w in tl for w in ["allreduce", "ring", "distributed", "gpu", "training"]):
            return {
                "title": title,
                "subtitle": "Bandwidth-optimal gradient synchronization across GPU clusters",
                "input_label": "LOCAL GRADIENT TENSOR",
                "router_label": "Ring Topology Dispatcher",
                "components": [
                    {"name": "Rank Ingestion Ring", "role": "Peer-to-peer tensor buffer", "active": True, "score": "HOT"},
                    {"name": "Scatter-Reduce Stage", "role": "Accumulates partial chunks", "active": True, "score": "ACTIVE"},
                    {"name": "All-Gather Stage", "role": "Broadcasts reduced values", "active": True, "score": "SYNC"},
                    {"name": "Optimizer Step", "role": "Weight update commit", "active": False},
                ],
                "metrics": [
                    {"label": "Inter-GPU Bandwidth", "val": "900 GB/s via NVLink fabric", "pct": 0.95, "color": "emerald"},
                    {"label": "Ring Network Overhead", "val": "2*(N-1)/N chunks transferred", "pct": 0.30, "color": "slate"},
                    {"label": "Sync Jitter Tolerance", "val": "< 45 microseconds", "pct": 0.80, "color": "amber"},
                ],
                "steps": [
                    {"num": "1", "name": "Tensor Partitioning", "desc": "Splits local gradient tensor into N equal-sized chunks"},
                    {"num": "2", "name": "Scatter-Reduce Phase", "desc": "Sends chunk i to neighbor; accumulates with incoming chunk"},
                    {"num": "3", "name": "All-Gather Phase", "desc": "Circulates fully reduced chunks around the logical ring"},
                    {"num": "4", "name": "Weights Update", "desc": "All GPUs now hold complete reduced gradients for optimizer"},
                ]
            }
        elif any(w in tl for w in ["cdc", "change data", "wal", "debezium", "kafka"]):
            return {
                "title": title,
                "subtitle": "Eliminating dual-write anomalies via transaction log mining",
                "input_label": "DB WRITE COMMIT",
                "router_label": "WAL Engine & Decoder",
                "components": [
                    {"name": "Postgres WAL Log", "role": "Append-only source of truth", "active": True, "score": "SOURCE"},
                    {"name": "Debezium Reader", "role": "Non-blocking log tailing", "active": True, "score": "ACTIVE"},
                    {"name": "Schema Registry", "role": "Avro schema compatibility", "active": False},
                    {"name": "Kafka Event Bus", "role": "Durable ordered consumer log", "active": True, "score": "STREAM"},
                ],
                "metrics": [
                    {"label": "Replication Lag", "val": "< 50 milliseconds", "pct": 0.92, "color": "emerald"},
                    {"label": "Primary DB Overhead", "val": "< 2% CPU footprint", "pct": 0.18, "color": "slate"},
                    {"label": "Data Consistency", "val": "Exactly-once via log sequence", "pct": 0.99, "color": "amber"},
                ],
                "steps": [
                    {"num": "1", "name": "Transaction Commit", "desc": "Primary database writes row modification directly to WAL"},
                    {"num": "2", "name": "Logical Decoding", "desc": "CDC engine intercepts binary stream without query overhead"},
                    {"num": "3", "name": "Event Serialization", "desc": "Transforms binary delta into structured domain event"},
                    {"num": "4", "name": "Downstream Fan-out", "desc": "Pushes to event bus for real-time caches, search, and data lakes"},
                ]
            }
        elif any(w in tl for w in ["context", "kv cache", "llm", "attention", "transformer"]):
            return {
                "title": title,
                "subtitle": "Sliding attention windows and memory complexity in frontier LLMs",
                "input_label": "PROMPT TOKEN STREAM",
                "router_label": "KV Cache Dispatcher",
                "components": [
                    {"name": "FlashAttention V3", "role": "IO-aware tiled attention", "active": True, "score": "HOT"},
                    {"name": "PagedKV Ring Buffer", "role": "Non-contiguous VRAM cache", "active": True, "score": "ACTIVE"},
                    {"name": "Sliding Window Mask", "role": "Truncates distant history", "active": True, "score": "BOUNDED"},
                    {"name": "Disk Offload Pool", "role": "Standby context paging", "active": False},
                ],
                "metrics": [
                    {"label": "KV Cache Footprint", "val": "~1.2 GB per 10k tokens", "pct": 0.75, "color": "amber"},
                    {"label": "Time to First Token", "val": "< 45ms prefill latency", "pct": 0.90, "color": "emerald"},
                    {"label": "Memory Bandwidth", "val": "1.8 TB/s HBM throughput", "pct": 0.95, "color": "slate"},
                ],
                "steps": [
                    {"num": "1", "name": "Prefill Phase", "desc": "Parallel matrix multiplication across all input prompt tokens"},
                    {"num": "2", "name": "KV Tensor Allocation", "desc": "Allocates Key and Value vectors into PagedAttention chunks"},
                    {"num": "3", "name": "Decode Autoregression", "desc": "Generates one token per step using cached KV states"},
                    {"num": "4", "name": "Cache Eviction", "desc": "Prunes expired context tokens beyond attention horizon"},
                ]
            }
        else:
            return {
                "title": title,
                "subtitle": (summary[:72] if summary else f"How {title[:45]} operates under the hood").strip(),
                "input_label": "PAYLOAD DISPATCH",
                "router_label": "Pipeline Gateway",
                "components": [
                    {"name": f"{title[:14]} Ingest", "role": "Enforces state boundaries", "active": True, "score": "ACTIVE"},
                    {"name": "Core Engine Worker", "role": "Executes domain transition", "active": True, "score": "HOT"},
                    {"name": "Auxiliary Index", "role": "Secondary lookup table", "active": False},
                    {"name": "Result Synthesizer", "role": "Serializes response payload", "active": True, "score": "OUT"},
                ],
                "metrics": [
                    {"label": "Pipeline Throughput", "val": "Optimized execution path", "pct": 0.85, "color": "emerald"},
                    {"label": "Resource Overhead", "val": "Strict bounded memory pool", "pct": 0.35, "color": "slate"},
                    {"label": "Tail Latency (p99)", "val": "Sub-millisecond guarantees", "pct": 0.70, "color": "amber"},
                ],
                "steps": [
                    {"num": "1", "name": "Payload Ingestion", "desc": f"Ingests and verifies boundaries for {title[:28]}"},
                    {"num": "2", "name": "State Evaluation", "desc": "Evaluates invariants and selects active processing worker"},
                    {"num": "3", "name": "Execution & Compute", "desc": "Worker processes payload while standby units conserve resources"},
                    {"num": "4", "name": "Downstream Commit", "desc": "Synthesizes final state and streams result with minimal overhead"},
                ]
            }


    def generate_ai_series_lesson(self, day: int, topic: str, level: str, chapter: str, include_link: bool = True) -> str:
        """Generates an authoritative, mobile-first daily lesson for the 'AI Explained: Zero to Advanced' 90-day master curriculum."""
        link_str = "📊 Live frontier benchmarks across 260+ models on NeuBench: https://app.neubench.workers.dev\n\n" if include_link else ""
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

    def generate_threads_take(self, title: str, summary: str = "", company: str = "", include_link: bool = False) -> str:
        """Generates an ultra-casual, highly relatable discussion post for Threads with stacked vertical lines and comment bait."""
        prompt = f"""
Everyday Topic: "{title}"
Context: "{summary}"

Write a viral, ultra-relatable post for Meta Threads designed to generate dozens of replies.
Formatting & Algorithmic Rules:
1. STACKED VERTICAL FORMAT: Write in 2-3 short, clean sentences separated by an empty line (double newline) to maximize mobile dwell time.
2. CONVERSATION HOOK AT THE END: End with a natural, low-barrier question or provocation that invites comments (e.g. "Tell me I'm not the only one.", "What's your version of this?", "Who else does this?", "Be honest.").
3. TONE: Warm, funny, self-deprecating, 100% human. Zero corporate jargon, zero tech talk, zero politics.
4. Clean text strictly under 280 characters.
5. Strictly NO URLs, NO buzzwords.
6. Output ONLY the raw post text.
"""
        text = self._generate_with_fallback(prompt, CASUAL_SYSTEM_PROMPT, temperature=0.94).strip('"').strip()
        import re
        # Strictly remove any URLs and NeuBench branding from casual Threads takes
        clean = re.sub(r'https?://\S+', '', text).strip()
        clean = re.sub(r'(?i)\bneubench(\.netlify\.app)?\b', '', clean).strip()
        clean = re.sub(r'\s+', ' ', clean).strip()
        return append_hashtags(clean, ["#Relatable"], max_len=300)

    def generate_casual_threads_take(self, title: str = "", summary: str = "") -> str:
        """Explicit casual Threads take generator."""
        return self.generate_threads_take(title, summary)




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

You are Vishnu Gupta, Founder & Lead AI Engineer at NeuBench (app.neubench.workers.dev).
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

    def generate_linkedin_congrats_comment(self, post_author: str, post_text: str) -> str:
        """
        Generates a warm, specific congratulation comment for a LinkedIn milestone
        (new role, promotion, launch, funding, certification, graduation, award).
        """
        prompt = f"""
LinkedIn Post by {post_author}:
"{post_text[:600]}..."

You are Vishnu Gupta, Founder & Lead AI Engineer at NeuBench.
Write a genuine, warm congratulation comment for this milestone.
Guidelines:
- Acknowledge the specific achievement mentioned (role, launch, funding, award, certification, graduation).
- Tone: Sincere, professional, and human. No corporate cliches ("Congrats on the well-deserved success!!!") and no over-the-top hype.
- Add one short, thoughtful sentence connecting it to their craft, growth, or the impact they will create.
- Optionally end with a light forward-looking line or question, but do not pitch or share links.
- Length: 2-3 sentences. Output ONLY the comment text.
"""
        system_p = "You are a respected AI systems founder who writes warm, specific, and credible LinkedIn congratulations."
        res = self._generate_with_fallback(prompt, system_p, temperature=0.7)
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

You are Vishnu Gupta, Founder & Lead AI Engineer at NeuBench (https://app.neubench.workers.dev).
Generate a high-value 'first comment' to be posted directly under this LinkedIn post.

Guidelines:
- Goal: Spark meaningful technical discussions in the comments while directing readers to live benchmark tools.
- Structure:
  1. A sharp 1-2 sentence engineering takeaway or code implementation tip.
  2. An open question asking developers how they handle this in production.
  3. A natural pointer to test live LLM latency & cost telemetry on NeuBench: https://app.neubench.workers.dev
- Keep it under 60-80 words. Professional, collegial, and high signal.
- Output ONLY the comment text.
"""
        system_p = "You are a senior AI systems engineer writing an insightful first-comment resource drop on LinkedIn."
        res = self._generate_with_fallback(prompt, system_p, temperature=0.7)
        return res.strip('"').strip()

    def generate_debate_comprehension(self, topic: str, context: str) -> str:
        """Analyzes an ongoing heated debate (political, religious, cultural, tech) and generates a savage contrarian take."""
        prompt = f"""
Debate / Controversial Topic: "{topic}"
Context & Ongoing Arguments: "{context}"

Task:
Analyze the opposing sides of this debate, pinpoint the hypocrisy, absurdity, or unspoken truth, and craft a devastatingly funny, sarcastic, or contrarian hot take.

Rules:
- Be unapologetically unfiltered, funny, and provocative.
- Call out both extremes if applicable, or expose the core absurdity of human behavior.
- Under 270 characters (strict X limit).
- Absolutely NO corporate PR speak, NO disclaimers, NO fence-sitting.
- Output ONLY the tweet text.
"""
        text = self._generate_with_fallback(prompt, X_UNHINGED_SYSTEM_PROMPT, temperature=0.95).strip('"').strip()
        import re
        clean = re.sub(r'https?://\S+', '', text).strip()
        return clean

    def generate_audience_reply(self, mention_author: str, mention_text: str, our_post_context: str = "") -> str:
        """Replies intelligently and wittily to incoming mentions/comments from our audience."""
        prompt = f"""
Our Original Tweet / Context: "{our_post_context[:200]}"
User @{mention_author} replied:
"{mention_text}"

Task:
Reply to @{mention_author}. Keep the conversation alive with sharp wit, sarcasm, playful banter, or agreement with an extra layer of humor.

Rules:
- Tone: Extremely sharp, funny, sarcastic creator who loves debating and roasting.
- 1-2 punchy sentences (under 240 chars).
- Do NOT include their @handle or quotes.
- Output ONLY the reply text.
"""
        text = self._generate_with_fallback(prompt, X_UNHINGED_SYSTEM_PROMPT, temperature=0.92).strip('"').strip()
        return text

    def select_linkedin_content_format(self, topic: str, summary: str = "") -> str:
        """Intelligently determines the ideal content format based on topic properties."""
        return select_linkedin_content_format(topic, summary)

    def validate_educational_plan(self, plan: dict) -> Tuple[bool, str]:
        """Validates that a generated carousel plan meets high information density standards."""
        return validate_educational_plan(plan)

    def generate_educational_notes_plan(self, topic: Any, context: str = "", category: str = "SYSTEMS ARCHITECTURE") -> dict:
        """Generates an authentic, in-depth 6-7 page handwritten engineering study notes plan with diagrams, mechanics, and pitfalls."""
        if isinstance(topic, dict):
            item = topic
            topic = str(item.get("title") or item.get("topic") or "").strip()
            context = str(item.get("summary") or item.get("golden_rule") or context).strip()
            category = str(item.get("category") or item.get("pillar") or category).strip()

        prompt = f"""You are a Principal Systems Architect and Distinguished Educator writing authentic, deeply detailed 6-7 page handwritten engineering study notes for LinkedIn.
Topic: "{topic}"
Context: "{context}"
Category: "{category}"

Produce an authoritative, comprehensive study note package that looks and reads like high-signal notes taken by a senior engineer or professor.
Avoid high-level generic bullet points. Provide real explanations, technical mechanisms, memory/runtime interactions, diagrams, and failure modes.
For AI retrieval systems like RAG, avoid absolute claims of 'deterministic factual grounding' or eliminating all errors; accurately explain that retrieval improves contextual grounding, source traceability, and hallucination mitigation, while remaining probabilistic and bounded by retrieval recall and model comprehension.

Return ONLY valid JSON with this exact schema:
{{
  "pillar": "EXPLAINER",
  "cover": {{
    "kicker": "{category}",
    "headline": "{topic}",
    "subhead": "In-depth engineering study notes on core mechanisms, state boundaries, and production reality.",
    "objectives": [
      "Understand foundational architecture & terminology",
      "Trace under-the-hood execution flow & memory model",
      "Identify critical production latency bottlenecks & failure modes"
    ]
  }},
  "pages": [
    {{
      "type": "cover",
      "kicker": "{category}",
      "headline": "{topic}",
      "subhead": "Comprehensive engineering field guide covering architectural mechanics, runtime execution, and production boundaries.",
      "learning_objectives": [
        "Core primitives & memory representation",
        "Step-by-step transaction / lifecycle mechanics",
        "Production tradeoffs, latency cliffs & antipatterns"
      ]
    }},
    {{
      "type": "concept",
      "kicker": "01 / FOUNDATIONS",
      "title": "Core Architecture & Definitions",
      "body": "Explain fundamental mechanics in 2-3 substantive paragraphs with high technical density.",
      "callout": "Crucial architectural distinction or invariant that engineers often miss.",
      "annotation": "Teacher note: Keep memory footprint in mind during high-concurrency spikes."
    }},
    {{
      "type": "diagram",
      "kicker": "02 / EXECUTION PIPELINE",
      "title": "Runtime Flow & Mechanics",
      "subtitle": "How requests transition across subsystem boundaries",
      "stages": [
        {{"name": "Stage 1", "desc": "Ingestion / Parse"}},
        {{"name": "Stage 2", "desc": "Validation / Index"}},
        {{"name": "Stage 3", "desc": "State Mutation"}},
        {{"name": "Stage 4", "desc": "Commit & Ack"}}
      ],
      "annotation": "End-to-end latency budget is dominated by serialization and disk flush."
    }},
    {{
      "type": "code",
      "kicker": "03 / IMPLEMENTATION",
      "title": "Minimal Reference Pattern",
      "subtitle": "Idiomatic production pattern illustrating correct invariants",
      "language": "python",
      "code": "# Production implementation pattern\nwith state_lock():\n    buffer.write(record)\n    flush_to_storage()",
      "annotation": "Notice explicit boundary validation before memory allocation."
    }},
    {{
      "type": "pitfalls",
      "kicker": "04 / PRODUCTION REALITY",
      "title": "Common Antipatterns & Traps",
      "traps": [
        {{"trap": "Premature buffering without backpressure", "impact": "OOM under traffic surges", "prevention": "Implement bounded channel queues with active load shedding"}},
        {{"trap": "Unindexed lookup in hot path", "impact": "High CPU lock contention", "prevention": "Maintain concurrent hash maps with generational pruning"}}
      ]
    }},
    {{
      "type": "cta",
      "kicker": "05 / REVISION CHECKLIST",
      "title": "Key Engineering Takeaways",
      "golden_rule": "Design for failure domains first; optimize latency second.",
      "checklist": [
        "Audit boundary timeouts across RPC calls",
        "Verify queue depth limits in production telemetry",
        "Benchmark tail latency (p99) against synthetic load"
      ],
      "discussion_prompt": "What unexpected failure mode have you hit when scaling this in production?"
    }}
  ],
  "post_text": "In-depth technical breakdown of {topic} for engineers and architects...\n\nDetailed 6-page field notes attached.\n\n#SoftwareEngineering #SystemDesign #Programming #DevOps #Architecture",
  "first_comment": "⚡ Live systems telemetry and LLM latency benchmarks on NeuBench: https://app.neubench.workers.dev",
  "hashtags": ["#SoftwareEngineering", "#SystemDesign", "#ComputerScience", "#Programming"]
}}
"""
        system_prompt = (
            "You are a Distinguished Systems Architect and Computer Science Professor writing in-depth handwritten engineering field notes. "
            "Return valid JSON only. Never use generic fluff or placeholder text. Ensure explanations are technically substantive."
        )

        try:
            data = self._generate_json(prompt, system_prompt, temperature=0.6)
            if data and data.get("pages") and len(data["pages"]) >= 4:
                return self._normalize_carousel_plan(data, topic, category)
        except Exception as e:
            print(f"[AIGenerator] Educational notes LLM generation notice: {e}. Building deterministic study notes plan...")

        # Deterministic rich fallback plan
        fallback_plan = {
            "pillar": "EXPLAINER",
            "cover": {
                "kicker": category,
                "headline": topic,
                "subhead": "In-depth engineering study notes on core mechanisms, state boundaries, and production reality.",
                "objectives": [
                    "Understand foundational architecture & terminology",
                    "Trace under-the-hood execution flow & memory model",
                    "Identify critical production latency bottlenecks & failure modes"
                ]
            },
            "pages": [
                {
                    "type": "cover",
                    "kicker": category,
                    "headline": topic,
                    "subhead": f"Comprehensive engineering field guide covering architectural mechanics, runtime execution, and production boundaries for {topic}.",
                    "learning_objectives": [
                        "Core primitives & memory representation",
                        "Step-by-step transaction / lifecycle mechanics",
                        "Production tradeoffs, latency cliffs & antipatterns"
                    ]
                },
                {
                    "type": "concept",
                    "kicker": "01 / FOUNDATIONS",
                    "title": "Core Architecture & Definitions",
                    "body": (
                        f"{topic} forms a foundational component of modern production infrastructure. "
                        f"At its core, {context or 'it provides robust state management, deterministic ordering, and predictable resource bounds'}. "
                        "When designing around these constraints, engineers must balance access latency, consistency semantics, and fault tolerance across distributed boundaries."
                    ),
                    "callout": "Architectural Invariant: Retrieved context provides grounding and provenance to mitigate hallucinations, but model synthesis remains probabilistic and bounded by chunk fidelity.",
                    "annotation": "Teacher note: Keep cache hit rates and memory footprint in mind during high-concurrency spikes."
                },
                {
                    "type": "diagram",
                    "kicker": "02 / EXECUTION PIPELINE",
                    "title": "Runtime Flow & Mechanics",
                    "subtitle": "How requests transition across subsystem boundaries",
                    "stages": [
                        {"name": "Stage 1", "desc": "Ingestion / Client Request"},
                        {"name": "Stage 2", "desc": "Validation & Buffer Index"},
                        {"name": "Stage 3", "desc": "State Mutation & Lock"},
                        {"name": "Stage 4", "desc": "Flush Commit & Ack"}
                    ],
                    "annotation": "End-to-end latency budget is dominated by serialization and disk flush."
                },
                {
                    "type": "code",
                    "kicker": "03 / IMPLEMENTATION",
                    "title": "Reference Architecture Pattern",
                    "subtitle": "Idiomatic production pattern illustrating correct invariants",
                    "language": "python",
                    "code": f"# Idiomatic pattern for {topic}\ndef execute_operation(record, session):\n    with session.transaction():\n        session.validate(record)\n        return session.commit(record)",
                    "annotation": "Notice explicit boundary validation before memory allocation."
                },
                {
                    "type": "pitfalls",
                    "kicker": "04 / PRODUCTION REALITY",
                    "title": "Common Antipatterns & Traps",
                    "traps": [
                        {"trap": "Unbounded memory buffer growth", "impact": "OOM cascade during downstream latency spikes", "prevention": "Enforce strict bounded ring buffers with explicit load shedding"},
                        {"trap": "Silent timeout masking", "impact": "Leaked locks and cascading thread pool exhaustion", "prevention": "Use context deadlines and propagate cancellation tokens throughout"}
                    ]
                },
                {
                    "type": "cta",
                    "kicker": "05 / REVISION CHECKLIST",
                    "title": "Key Engineering Takeaways",
                    "golden_rule": f"Master the state transitions of {topic} before scaling traffic.",
                    "checklist": [
                        "Audit boundary timeouts across all RPC and storage calls",
                        "Verify queue depth limits in production telemetry",
                        "Benchmark tail latency (p99) against synthetic load spikes"
                    ],
                    "discussion_prompt": "What unexpected failure mode have you encountered when scaling this in production?"
                }
            ],
            "post_text": (
                f"Engineering Deep Dive: {topic}\n\n"
                f"{context or 'Understanding the architectural boundaries, memory trade-offs, and failure modes.'}\n\n"
                "I broke down the complete mechanics into a 6-page study note field guide below:\n"
                "• Foundational Architecture & Invariants\n"
                "• Step-by-Step Runtime Execution Flow\n"
                "• Implementation Reference Pattern\n"
                "• Production Traps & Latency Pitfalls\n"
                "• Revision Checklist for System Designers\n\n"
                "Save this carousel for your next architectural review.\n\n"
                "#SoftwareEngineering #SystemDesign #ComputerScience #Programming #DevOps"
            ),
            "first_comment": "⚡ Live systems telemetry and LLM latency benchmarks on NeuBench: https://app.neubench.workers.dev",
            "hashtags": ["#SoftwareEngineering", "#SystemDesign", "#ComputerScience", "#Programming", "#Architecture"]
        }
        return self._normalize_carousel_plan(fallback_plan, topic, category)

    def generate_comparison_plan(self, topic: Any, summary: str = "", concept_a: str = "", concept_b: str = "") -> dict:
        """Generates an intelligent 6-page architectural versus/comparison carousel plan with side-by-side matrices."""
        if isinstance(topic, dict):
            item = topic
            topic = str(item.get("title") or item.get("topic") or "").strip()
            summary = str(item.get("summary") or item.get("golden_rule") or summary).strip()

        name_a = concept_a or "Approach A"
        name_b = concept_b or "Approach B"
        if not concept_a or not concept_b:
            if " vs. " in topic:
                parts = topic.split(" vs. ", 1)
                name_a, name_b = parts[0].strip(), parts[1].strip()
            elif " vs " in topic:
                parts = topic.split(" vs ", 1)
                name_a, name_b = parts[0].strip(), parts[1].strip()
            elif " versus " in topic.lower():
                parts = topic.lower().split(" versus ", 1)
                name_a, name_b = parts[0].strip(), parts[1].strip()

        prompt = f"""You are a Principal Software Architect writing an authoritative 6-page comparison carousel for LinkedIn.
Topic: "{topic}"
Option A: "{name_a}"
Option B: "{name_b}"
Context: "{summary}"

Produce an in-depth comparison note that helps senior engineers and architects make the right technical decision.
Explain what each concept means, why both exist, how each works internally, important trade-offs (performance, memory, scalability, cost), and concrete selection rules.
DO NOT declare an arbitrary winner—explain when to choose each.

Return ONLY valid JSON matching this schema:
{{
  "pillar": "DIFFERENCE",
  "cover": {{
    "kicker": "ARCHITECTURAL COMPARISON",
    "headline": "{topic}",
    "subhead": "A side-by-side engineering evaluation of trade-offs, internal mechanics, and decision criteria.",
    "objectives": [
      "Deconstruct internal mechanics of {name_a} vs {name_b}",
      "Compare throughput, memory, and operational complexity",
      "Actionable heuristics for production system selection"
    ]
  }},
  "pages": [
    {{
      "type": "cover",
      "kicker": "ARCHITECTURAL COMPARISON",
      "headline": "{topic}",
      "subhead": "A side-by-side engineering evaluation of trade-offs, internal mechanics, and decision criteria.",
      "learning_objectives": [
        "Deconstruct internal mechanics of {name_a} vs {name_b}",
        "Compare throughput, memory, and operational complexity",
        "Actionable heuristics for production system selection"
      ]
    }},
    {{
      "type": "concept",
      "kicker": "01 / CORE PHILOSOPHY",
      "title": "Foundations & Architectural Intent",
      "body": "Explain why both {name_a} and {name_b} exist. What fundamental engineering problem was each created to solve? Contrast their core paradigms in 2-3 detailed paragraphs.",
      "callout": "Key distinction: How each approach handles state and consistency.",
      "annotation": "Architect note: Choosing the wrong paradigm leads to heavy operational friction."
    }},
    {{
      "type": "comparison",
      "kicker": "02 / TRADE-OFF MATRIX",
      "title": "Side-by-Side Architectural Evaluation",
      "item_a": "{name_a}",
      "item_b": "{name_b}",
      "criteria": [
        {{"criterion": "Data Model", "item_a": "Streaming partitions / log offset", "item_b": "Discrete message queues / exchanges"}},
        {{"criterion": "Throughput", "item_a": "Millions msg/sec (sequential I/O)", "item_b": "Tens of thousands msg/sec (random I/O)"}},
        {{"criterion": "Ordering", "item_a": "Strict per-partition ordering", "item_b": "Best-effort queue ordering"}},
        {{"criterion": "Replayability", "item_a": "Persistent replay via consumer offset", "item_b": "Transient; deleted upon acknowledgment"}}
      ],
      "annotation": "Throughput comes at the cost of partition rebalancing overhead."
    }},
    {{
      "type": "code",
      "kicker": "03 / CODE PATTERNS",
      "title": "Consumer Implementation Patterns",
      "subtitle": "How client ergonomics differ in production code",
      "language": "python",
      "code": "# Option A ({name_a}) vs Option B ({name_b})\n# A: Pull model with consumer groups\nfor msg in consumer.poll(timeout=1.0):\n    process(msg)\n    consumer.commit()\n\n# B: Push model with callback listener\nchannel.basic_consume(queue='jobs', on_message_callback=handle)",
      "annotation": "Pull models provide superior backpressure; push models minimize consumer latency."
    }},
    {{
      "type": "pitfalls",
      "kicker": "04 / PRODUCTION MISTAKES",
      "title": "Common Pitfalls & Failure Modes",
      "traps": [
        {{"trap": "Misjudging scaling bounds", "impact": "Unexpected partition rebalance storms or broker OOM", "prevention": "Pre-provision partition counts based on peak consumer thread capacity"}},
        {{"trap": "Overcomplicating the simple path", "impact": "Excessive operational overhead for small workloads", "prevention": "Start with standard queues until audit log replay becomes a strict requirement"}}
      ]
    }},
    {{
      "type": "cta",
      "kicker": "05 / DECISION MATRIX",
      "title": "Golden Rules: When to Choose Which",
      "golden_rule": "Choose {name_a} for replayable event streaming and analytics; choose {name_b} for complex routing and task queues.",
      "checklist": [
        "Audit data retention requirements (ephemeral vs persistent)",
        "Estimate peak throughput and consumer concurrency limits",
        "Assess operational familiarity within your team"
      ],
      "discussion_prompt": "Which one do you rely on more in your current production stack?"
    }}
  ],
  "post_text": "{topic}: The Ultimate Engineering Comparison Guide\n\nBoth {name_a} and {name_b} are exceptional, but they were built for fundamentally different workloads...\n\nDetailed 6-page architectural matrix attached.\n\n#SystemDesign #SoftwareEngineering #Architecture #DevOps #Programming",
  "first_comment": "⚡ Live systems telemetry and LLM latency benchmarks on NeuBench: https://app.neubench.workers.dev",
  "hashtags": ["#SoftwareEngineering", "#SystemDesign", "#Architecture", "#DevOps"]
}}
"""
        system_prompt = (
            "You are a Distinguished Software Architect and Systems Design Educator. "
            "Return valid JSON only matching the schema exactly. Provide deep, technically nuanced comparisons."
        )

        try:
            data = self._generate_json(prompt, system_prompt, temperature=0.6)
            if data and data.get("pages") and len(data["pages"]) >= 4:
                return self._normalize_carousel_plan(data, topic, "DIFFERENCE")
        except Exception as e:
            print(f"[AIGenerator] Comparison plan LLM generation notice: {e}. Building deterministic comparison plan...")

        # Deterministic rich fallback plan
        fallback_plan = {
            "pillar": "DIFFERENCE",
            "cover": {
                "kicker": "ARCHITECTURAL COMPARISON",
                "headline": topic,
                "subhead": f"A side-by-side engineering evaluation of trade-offs, internal mechanics, and decision criteria for {name_a} vs {name_b}.",
                "objectives": [
                    f"Deconstruct internal mechanics of {name_a} vs {name_b}",
                    "Compare throughput, memory, and operational complexity",
                    "Actionable heuristics for production system selection"
                ]
            },
            "pages": [
                {
                    "type": "cover",
                    "kicker": "ARCHITECTURAL COMPARISON",
                    "headline": topic,
                    "subhead": f"A side-by-side engineering evaluation of trade-offs, internal mechanics, and decision criteria for {name_a} vs {name_b}.",
                    "learning_objectives": [
                        f"Deconstruct internal mechanics of {name_a} vs {name_b}",
                        "Compare throughput, memory, and operational complexity",
                        "Actionable heuristics for production system selection"
                    ]
                },
                {
                    "type": "concept",
                    "kicker": "01 / CORE PHILOSOPHY",
                    "title": "Foundations & Architectural Intent",
                    "body": (
                        f"Engineers frequently debate {name_a} versus {name_b}, but they solve fundamentally different architectural problems. "
                        f"{name_a} was engineered around sequential access, high-throughput batching, and append-only state retention. "
                        f"Conversely, {name_b} prioritizes dynamic message routing, discrete queue isolation, and immediate acknowledgment upon delivery."
                    ),
                    "callout": f"Fundamental Differentiator: {name_a} treats data as an immutable historical log, while {name_b} treats data as transient tasks.",
                    "annotation": "Architect note: Choosing the wrong paradigm leads to heavy operational friction."
                },
                {
                    "type": "comparison",
                    "kicker": "02 / TRADE-OFF MATRIX",
                    "title": "Side-by-Side Architectural Evaluation",
                    "item_a": name_a,
                    "item_b": name_b,
                    "criteria": [
                        {"criterion": "Primary Abstraction", "item_a": "Partitioned commit log", "item_b": "Routing exchange and queues"},
                        {"criterion": "Throughput Scaling", "item_a": "Millions/sec via sequential I/O", "item_b": "Tens of thousands/sec per node"},
                        {"criterion": "Message Retention", "item_a": "Configurable (days/weeks/months)", "item_b": "Deleted immediately after ACK"},
                        {"criterion": "Consumer Pattern", "item_a": "Pull model with partition offsets", "item_b": "Push/Pull with broker ACK tracking"}
                    ],
                    "annotation": "High throughput comes with the cost of client-side offset and partition management."
                },
                {
                    "type": "code",
                    "kicker": "03 / CODE PATTERNS",
                    "title": "Consumer Implementation Patterns",
                    "subtitle": "How client ergonomics differ in production code",
                    "language": "python",
                    "code": f"# Pattern comparison: {name_a} vs {name_b}\n# {name_a}: Offset-based consumer poll\nrecords = consumer.poll(timeout_ms=500)\nfor record in records:\n    process(record)\n\n# {name_b}: Callback-based worker queue\nqueue.subscribe(handle_message, ack_mode='manual')",
                    "annotation": "Pull models provide natural backpressure; push models minimize consumer latency."
                },
                {
                    "type": "pitfalls",
                    "kicker": "04 / PRODUCTION MISTAKES",
                    "title": "Common Pitfalls & Failure Modes",
                    "traps": [
                        {"trap": f"Using {name_a} as a simple work queue", "impact": "Partition head-of-line blocking when slow tasks stall a consumer", "prevention": f"Use {name_b} for independent, heterogeneous task execution"},
                        {"trap": f"Using {name_b} as an analytics event bus", "impact": "High memory pressure and queue broker failure under large backlogs", "prevention": f"Use {name_a} when event stream replay and long retention are required"}
                    ]
                },
                {
                    "type": "cta",
                    "kicker": "05 / DECISION MATRIX",
                    "title": "Golden Rules: When to Choose Which",
                    "golden_rule": f"Choose {name_a} for persistent event streaming and audit replay; choose {name_b} for granular task routing and immediate dispatch.",
                    "checklist": [
                        "Define retention: Do consumers ever need to replay historical messages?",
                        "Evaluate consumer scale: Will slow tasks block peer partitions?",
                        "Factor operational overhead into your infrastructure sizing"
                    ],
                    "discussion_prompt": f"Which one do you rely on more in production—{name_a} or {name_b}?"
                }
            ],
            "post_text": (
                f"{name_a} vs {name_b}: Architectural Comparison\n\n"
                f"{summary or 'A deep dive into trade-offs, internal mechanics, and production decision heuristics.'}\n\n"
                "I summarized the entire decision framework in the 6-page field note below:\n"
                "• Core Architecture & Founding Philosophy\n"
                "• Side-by-Side Trade-off Matrix (Throughput, Retention, Ordering)\n"
                "• Production Code Patterns & Consumer Ergonomics\n"
                "• Critical Pitfalls & Failure Modes\n"
                "• Golden Selection Rules\n\n"
                "Save this guide for your next systems architecture review.\n\n"
                "#SystemDesign #SoftwareEngineering #Architecture #DevOps #Programming"
            ),
            "first_comment": "⚡ Live systems telemetry and LLM latency benchmarks on NeuBench: https://app.neubench.workers.dev",
            "hashtags": ["#SoftwareEngineering", "#SystemDesign", "#Architecture", "#DevOps"]
        }
        return self._normalize_carousel_plan(fallback_plan, topic, "DIFFERENCE")

    def ideate_autonomous_tech_topic(
        self,
        target_audience: Optional[str] = None,
        content_format: Optional[str] = None,
        recent_topics: Optional[List[str]] = None,
        live_news_signals: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Autonomously synthesizes a novel, high-engagement tech or AI topic without any hardcoded lists.
        Behaves as an expert Tech and AI Content Creator producing content tailored across diverse
        demographics—from school kids to working professionals, staff architects, and AI terminology seekers.
        """
        demographics = {
            "school_kid": "School Kids and Curious Beginners (10-16 yrs) - Pure real-world analogies, zero intimidating jargon, focus on the magical intuition behind everyday tech and AI.",
            "college_student": "College Students and Aspiring Coders - Core CS fundamentals, data structures, algorithms, developer tools, interview clarity.",
            "working_pro": "Working Software Professionals and Devs - Production backend architectures, database indexing, caching, microservices, cloud trade-offs, reliability.",
            "staff_engineer": "Senior and Staff Systems Architects - Deep distributed systems, GPU memory bandwidth, consensus, low-level mechanics, high-scale reliability.",
            "ai_curious": "AI-Curious Enthusiasts and Practitioners - Modern AI terminology, LLMs, tokens, embeddings, quantization, context windows, RAG, agentic workflows."
        }
        formats = {
            "versus_comparison": "Versus / Comparison (A vs B) - Contrast two competing tools, frameworks, architectures, or paradigms with clear trade-offs.",
            "terminology_demystified": "Terminology Demystified - Demystify an intimidating tech or AI term with crystal-clear intuition and diagrams.",
            "systems_breakdown": "Systems and How It Works - Deconstruct how a real-world system or algorithm works under the hood.",
            "trend_news": "Live Tech and Research Breakdown - Translate a recent tech development, research paper, or benchmark into practical engineering insight."
        }

        aud_key = target_audience if target_audience in demographics else random.choice(list(demographics.keys()))
        fmt_key = content_format if content_format in formats else random.choice(list(formats.keys()))

        selected_aud_desc = demographics[aud_key]
        selected_fmt_desc = formats[fmt_key]

        recent_sample = [str(t).strip() for t in (recent_topics or [])[-30:] if str(t).strip()]
        recent_block = "\n".join(f"- {t}" for t in recent_sample) if recent_sample else "None recorded yet."

        news_block = ""
        if live_news_signals:
            top_signals = []
            for s in live_news_signals[:6]:
                stitle = str(s.get("title", "")).strip()
                ssummary = str(s.get("summary") or s.get("context") or "")[:150].strip()
                if stitle:
                    top_signals.append(f"• {stitle}: {ssummary}")
            if top_signals:
                news_block = "LIVE TECH NEWS AND RESEARCH SIGNALS FROM TODAY:\n" + "\n".join(top_signals)

        prompt = f"""You are a world-class Tech and AI Content Creator and Educator.
Your mission is to make computing and artificial intelligence fascinating, actionable, and crystal clear.

TARGET AUDIENCE FOR THIS PIECE:
[{aud_key.upper()}] - {selected_aud_desc}

DESIRED CONTENT FORMAT:
[{fmt_key.upper()}] - {selected_fmt_desc}

{news_block}

RECENT TOPICS ALREADY COVERED (CRITICAL: DO NOT REPEAT OR CLOSELY DUPLICATE ANY OF THESE):
{recent_block}

INSTRUCTIONS:
1. Autonomously choose an exciting, educational, and timely Tech or AI topic appropriate for the target audience and format.
2. If format is 'versus_comparison', provide concept_a and concept_b (e.g. 'Docker vs. Podman', 'REST vs. gRPC', 'B-Tree vs. LSM-Tree', 'FP16 vs. INT4', 'Stack vs. Heap').
3. If format is 'terminology_demystified', explain a crucial term (e.g. 'What is a Logit?', 'Vector Embeddings', 'Database Deadlock', 'Paging and Virtual Memory').
4. If format is 'systems_breakdown', explain the inner mechanics of a real system (e.g. 'How DNS Resolves in 20ms', 'How LLM KV Cache Saves VRAM').
5. If format is 'trend_news', translate a contemporary AI/tech breakthrough into an intuitive insight.
6. Create relatable real-world analogies (especially for school_kid and college_student tiers) and sharp technical trade-offs (for working_pro and staff_engineer tiers).

Return valid JSON matching this schema:
{{
  "title": "Engaging, professional topic title",
  "target_audience": "{aud_key}",
  "content_format": "{fmt_key}",
  "category": "e.g. SYSTEMS ARCHITECTURE | AI and ML | DATA STRUCTURES | CLOUD and DEVOPS | NETWORKING",
  "concept_a": "Name of primary concept / tool",
  "concept_b": "Name of secondary concept / tool (if comparison, else empty)",
  "summary": "2-3 punchy sentences explaining the core concept, intuition, and why it matters.",
  "golden_rule": "One memorable, actionable rule of thumb or takeaway.",
  "real_world_analogy": "A relatable real-world analogy suitable for this audience.",
  "school_analogy": "How you would explain this simply to a 14-year-old.",
  "pro_nuance": "The technical caveat or architectural trade-off that only experienced engineers know.",
  "key_takeaways": [
    "First crucial insight",
    "Second crucial insight",
    "Third crucial insight"
  ],
  "flow_steps": [
    {{"label": "Step 1 name", "desc": "What happens in step 1", "icon": "tokens"}},
    {{"label": "Step 2 name", "desc": "What happens in step 2", "icon": "embedding"}},
    {{"label": "Step 3 name", "desc": "What happens in step 3", "icon": "attention"}},
    {{"label": "Step 4 name", "desc": "What happens in step 4", "icon": "predict"}}
  ]
}}
"""
        system_instruction = (
            "You are an elite, world-class Tech and AI Educator and Content Creator. "
            "You invent novel, highly educational, technically sound concepts without repeating recent history. "
            "Return valid JSON only matching the schema exactly."
        )

        try:
            data = self._generate_json(prompt, system_instruction, temperature=0.75)
            if data and data.get("title") and data.get("summary"):
                data["title"] = str(data["title"]).strip()
                data["target_audience"] = aud_key
                data["content_format"] = fmt_key
                return data
        except Exception as e:
            print(f"[AIGenerator] Autonomous topic ideation notice: {e}. Generating dynamic procedural topic...")

        fallback_seeds = {
            "school_kid": [
                ("How the Internet Actually Works", "Like a global highway system for digital packets"),
                ("What Happens When You Press A Key", "From physical membrane switch to OS interrupt and screen buffer"),
                ("Binary: Why Computers Only Speak 0 and 1", "Like millions of microscopic light switches turning on and off"),
                ("How Self-Driving Cars See the Road", "Cameras, LiDAR, and computer vision neural nets working together")
            ],
            "college_student": [
                ("Stack vs. Heap: Where Variables Live", "Fast contiguous execution stack vs dynamic allocated memory heap"),
                ("Recursion vs. Iteration", "Call stack frames and memory limits vs loop pointer arithmetic"),
                ("How Compilers Optimize Code", "From AST parsing to dead code elimination and register allocation"),
                ("HTTP/1.1 vs HTTP/2 vs HTTP/3", "Text pipelines vs binary multiplexing vs UDP QUIC streaming")
            ],
            "working_pro": [
                ("PostgreSQL WAL (Write-Ahead Logging) Deep Dive", "How databases guarantee ACID durability before writing to tables"),
                ("Redis Cache Invalidation Patterns", "Cache-aside vs write-through vs refresh-ahead trade-offs"),
                ("Circuit Breakers in Distributed Microservices", "Failing fast to prevent cascading service downtime"),
                ("Horizontal Pod Autoscaling Mechanics", "Metrics scraping, hysteresis smoothing, and thrashing prevention")
            ],
            "staff_engineer": [
                ("Raft Consensus vs Paxos in High Scale Clusters", "Leader election, log replication quorums, and partition healing"),
                ("Kernel Bypassing with DPDK / io_uring", "Eliminating syscall context-switch overhead for sub-microsecond networking"),
                ("LLM KV Cache Eviction and PagedAttention", "Virtual memory paging applied to transformer attention matrix memory"),
                ("Distributed Deadlock Detection Algorithms", "Wait-for graphs and edge chasing in distributed transactional databases")
            ],
            "ai_curious": [
                ("What Exactly is a Token in Modern LLMs?", "Subword byte-pair encodings and why rare words cost more"),
                ("Temperature vs Top-P: How Sampling Affects Output", "Logit probability scaling vs cumulative nucleus thresholding"),
                ("Vector Embeddings: Mapping Meaning to Geometry", "How high-dimensional cosine similarity measures semantic closeness"),
                ("Speculative Decoding: Accelerating LLM Inference", "Using small draft models to verify tokens in parallel on big models")
            ]
        }
        chosen_pair = random.choice(fallback_seeds.get(aud_key, fallback_seeds["working_pro"]))
        return {
            "title": chosen_pair[0],
            "target_audience": aud_key,
            "content_format": fmt_key,
            "category": "TECH and SYSTEMS ENGINEERING",
            "concept_a": chosen_pair[0].split(" vs ")[0] if " vs " in chosen_pair[0] else chosen_pair[0],
            "concept_b": chosen_pair[0].split(" vs ")[1] if " vs " in chosen_pair[0] else "",
            "summary": chosen_pair[1],
            "golden_rule": "Simplicity and measurable profiling beat premature architectural complexity.",
            "real_world_analogy": chosen_pair[1],
            "school_analogy": chosen_pair[1],
            "pro_nuance": "Always profile production telemetry before committing to architectural restructuring.",
            "key_takeaways": [
                "Fundamental architecture dictates long-term system scaling bounds.",
                "Measure real bottlenecks before applying complex optimizations.",
                "Simplicity in system design reduces operational maintenance burden."
            ]
        }




def select_linkedin_content_format(topic: str, summary: str = "") -> str:
    """Intelligently determines the ideal content format based on topic properties."""
    combined = f"{topic} {summary}".lower()
    if any(vs in combined for vs in [" vs. ", " vs ", " versus ", " compared to ", " or "]):
        return "comparison_carousel"
    if any(term in combined for term in [
        "architecture", "internals", "protocol", "how it works", "data structure",
        "algorithm", "system design", "memory", "deep dive", "under the hood",
        "guide", "explained", "engine", "pipeline", "database"
    ]):
        return "handwritten_notes"
    if any(term in combined for term in ["benchmark", "outage", "security", "breach", "acquisition", "released", "launches"]):
        return "professional_carousel"
    return "handwritten_notes"


def validate_educational_plan(plan: dict) -> Tuple[bool, str]:
    """Validates that a generated carousel plan meets high information density standards."""
    if not isinstance(plan, dict):
        return False, "Plan is not a dictionary"
    if not plan.get("post_text") or len(str(plan.get("post_text")).strip()) < 80:
        return False, "Post text is missing or too short (< 80 chars)"
    if plan.get("pages") and isinstance(plan["pages"], list):
        if len(plan["pages"]) < 4:
            return False, f"Plan has only {len(plan['pages'])} pages (minimum 4 required)"
        for p in plan["pages"]:
            if not isinstance(p, dict):
                return False, "Page item is not a dictionary"
            ptype = p.get("type", "")
            if ptype == "concept" and len(str(p.get("body", "")).strip()) < 80:
                return False, "Concept page body is too short (< 80 chars)"
        return True, "Valid multi-page educational plan"
    slides = plan.get("slides") or []
    if len(slides) < 2 or not plan.get("cover"):
        return False, "Plan has insufficient slides or lacks a cover"
    return True, "Valid legacy carousel plan"
