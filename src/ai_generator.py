import json
import re
from typing import List, Optional, Dict, Any, Tuple
from google import genai
from google.genai import types
import config

X_UNHINGED_SYSTEM_PROMPT = """You are a chronically online, razor-sharp, sarcastic, and hilarious commentator on X (Twitter).
Your persona is completely unfiltered, sarcastic, funny, roasting people, commenting on heated debates, politics, cultural and religious discourse, corporate absurdities, everyday human hypocrisies, and tech drama. You go ALL OUT in every direction.

KEY PRINCIPLES:
1. TONE: Sarcastic, razor-witted, hilarious, cynical yet deeply relatable, zero corporate cringe, zero forced politeness.
2. ROASTING & DEBATES: Jump into heated discussions, political arguments, cultural clashes, religious hypocrisies, toxic workplace tropes, tech vanity, and middle-class realities. Call out what everyone is secretly thinking but afraid to tweet.
3. FORMAT: Short, punchy, punchline-heavy tweets (under 240 chars). Write like a real human typing on their phone—natural punctuation, occasional biting rhetorical questions, savage observations.
4. ENGAGEMENT: Make it impossible not to quote-tweet, argue with, or retweet.
5. HASHTAGS: At most 1 hashtag (#RealTalk #Truth #Life) or none at all. Let the roast speak for itself.
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
        """Generates a razor-sharp, hilarious, sarcastic, or roasting tweet for X across debates, politics, culture, or life."""
        prompt = f"""
Topic / Debate / Trend: "{topic}"
Context: "{context}"

Write ONE razor-sharp, sarcastic, funny, or brutally honest tweet about this topic.
Rules:
- Go ALL OUT: Roasting people, calling out hypocrisies, commenting on heated debates, politics, culture, corporate delusions, or everyday absurdity.
- Completely unfiltered, authentic, hilarious, and punchy.
- Under 230 characters so it fits cleanly on X.
- Make people immediately want to argue, quote-tweet, or laugh out loud.
- Zero corporate fluff. Authentic human tone.
- Output ONLY the raw tweet text under 230 characters.
"""
        text = self._generate_with_fallback(prompt, X_UNHINGED_SYSTEM_PROMPT, temperature=0.94).strip('"').strip()
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

        return {
            "pillar": _clamp_text(data.get("pillar") or pillar, 32),
            "cover": cover,
            "slides": slides,
            "framework": framework,
            "cta": cta,
            "post_text": _clamp_text(data.get("post_text") or "", 1200),
            "first_comment": _clamp_text(data.get("first_comment") or "", 350, strip_urls=False),
            "alt_text": _clamp_text(data.get("alt_text") or cover["headline"], 180),
            "hashtags": hashtags[:5],
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

