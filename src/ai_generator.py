import json
from google import genai
from google.genai import types
import config

SYSTEM_PROMPT = """You are a real, sharp, chronically online human commentator on X (Twitter).
You write like a real person typing on their phone — witty, opinionated, skeptical, and slightly contrarian.

CRITICAL RULES TO SOUND 100% HUMAN:
1. NEVER use hashtags (#) or robotic emojis at the start of sentences.
2. NEVER use AI buzzwords: "Delving into", "In conclusion", "Game-changer", "Tapestry", "Fascinating", "Buckle up", "Here is why".
3. Write casually. It's okay to use occasional lowercase starts, natural contractions (don't, can't, honestly, bro, idk), and blunt 1-liners.
4. For Indian context topics: Sound like a sharp Indian tech/internet native (e.g. relatable work culture, Bengaluru traffic/rents, startup drama, corporate irony, "make it make sense").
5. Your goal is to trigger people into arguing or replying. People reply to:
   - Strong unpopular opinions ("Hot take:", "Most people are blind to this...")
   - Calling out corporate or internet hypocrisy
   - Sarcastic or witty observations
6. Keep replies ULTRA-CONCISE (under 120 characters). The shorter and sharper the reply, the more likes and quote-tweets it gets.
"""

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
        """Generates an original high-engagement polarizing hot take or debate starter."""
        prompt = f"""
Trending topic: "{topic}"
Context: "{context}"

Write ONE punchy, controversial or thought-provoking tweet about this topic.
The tweet must trigger people to reply in the comments (either to agree strongly or disagree passionately).
Output ONLY the raw tweet text. No quotes, no hashtags, no introductory filler.
"""
        text = self._generate_with_fallback(prompt, SYSTEM_PROMPT, temperature=0.9)
        return text.strip('"')

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
        """Generates sharp, opinionated Quote-Tweet commentary ('masala on top') to quote a viral tweet."""
        prompt = f"""
Viral Tweet by @{target_tweet_author}:
"{target_tweet_text}"

Generate a punchy, sharp, or witty 1-2 sentence Quote-Tweet commentary.
It must:
- Add a unique, polarizing, or cynical angle to the quoted tweet.
- Make followers want to quote-tweet or debate in your thread.
- Sound 100% human, confident, and concise (under 160 characters).
- Output ONLY the commentary text. No quotes, no hashtags.
"""
        text = self._generate_with_fallback(prompt, SYSTEM_PROMPT, temperature=0.88)
        return text.strip('"')

    def generate_poll_tweet(self, topic: str) -> dict:
        """Generates a poll question and 2-4 options."""
        prompt = f"""
Topic: "{topic}"
Create an interactive poll that people on X won't resist voting on.
Return a valid JSON object with:
- "question": string (under 120 chars)
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
                "question": f"What's your honest take on {topic}?",
                "options": ["Agree 100%", "Completely wrong", "Too early to tell", "Results"]
            }

    def generate_neubench_take(self, title: str, summary: str = "", company: str = "", include_link: bool = True) -> str:
        """Generates a viral take on a NeuBench AI news story or benchmark model, driving engagement & traffic."""
        link_instruction = "End naturally with 'Tracking benchmarks on neubench.vercel.app' or similar subtle nod." if include_link else "Do not include URLs."
        prompt = f"""
AI News / Model: "{title}"
Developer/Company: "{company}"
Context / Summary: "{summary}"

Write a punchy, opinionated, high-engagement X tweet about this AI update.
Rules:
- Sound 100% like a sharp tech-native commentator (contrarian, witty, zero corporate PR fluff).
- NO hashtags (#). No robotic emojis like 🚀🤖 at start.
- Provoke discussion in the replies.
- {link_instruction}
- Total length under 260 characters.
- Output ONLY the tweet text.
"""
        text = self._generate_with_fallback(prompt, SYSTEM_PROMPT, temperature=0.88)
        return text.strip('"')


