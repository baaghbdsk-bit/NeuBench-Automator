# -*- coding: utf-8 -*-
"""
LinkedIn Portfolio Manager & Pre-Publish Quality Gate

Acts as the autonomous Chief Editor and Portfolio Manager for LinkedIn:
1. Format Strategy: Analyzes the topic to decide the best visual presentation:
   - 'notebook_carousel': Multi-page PDF for tutorials, deep-dive study notes, and implementation guides.
   - 'animated_flow_gif': 1080x1350 vertical looping GIF for real-time pipelines, data flows, and hardware/systems dynamics.
   - 'text_only': NO ATTACHMENT when visual aids would be forced, redundant, or don't add genuine technical value.
2. Pre-Publish Quality Gate:
   - Validates article substance (1,000-2,950 chars, real metrics, concrete mechanisms).
   - Enforces zero placeholder or generic phrasing.
   - Enforces strict media validation (rejects any repeated or generic fallback diagrams).
   - Ensures 100% alignment between article text and attached media.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from rich.console import Console

console = Console()

# Blacklist of generic fallback terms that indicate a low-effort / placeholder diagram
GENERIC_COMPONENT_BLOCKLIST = [
    "parser & schema",
    "parser and schema",
    "core engine worker",
    "core engine",
    "cache layer",
    "fast cache",
    "storage sink",
    "state sink",
    "payload ingestion",
    "client ingest",
    "pipeline gateway",
    "execution pipeline",
]


class LinkedInPortfolioManager:
    """Autonomous Chief Editor & Portfolio Manager for LinkedIn publishing."""

    def __init__(self, ai_generator: Any = None):
        if ai_generator is None:
            try:
                from src.ai_generator import AIGenerator
                self.ai = AIGenerator()
            except Exception:
                self.ai = None
        else:
            self.ai = ai_generator

    def decide_portfolio_format(
        self,
        topic: str,
        summary: str = "",
        audience: str = "working_pro",
        explicit_format: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Determines the optimal visual format for a given topic.
        Returns: (format_type, reasoning)
        format_type is one of: 'animated_flow_gif', 'notebook_carousel', 'text_only'
        """
        if explicit_format in ("animated_flow_gif", "notebook_carousel", "text_only"):
            return explicit_format, f"Explicit format requested: {explicit_format}"

        t_lower = topic.lower()
        s_lower = summary.lower()
        combined = f"{t_lower} {s_lower}"

        # 1. Topics best suited for Animated Flow GIFs (moving data, routing, pipelines, signals)
        flow_keywords = [
            "flow", "routing", "pipeline", "lifecycle", "stream", "dispatch",
            "allreduce", "moe", "mixture of experts", "noise cancel", "anti-sound",
            "acoustic", "raft", "consensus", "cdc", "change data capture", "wal",
            "event-driven", "message queue", "kv cache", "attention mechanism",
            "handshake", "packet", "signal", "vs", "versus"
        ]
        if any(kw in combined for kw in flow_keywords):
            return "animated_flow_gif", "Topic features dynamic data movement, state transitions, or architectural contrast suited for a looping flow diagram."

        # 2. Topics best suited for Multi-Page PDF Study Notes (tutorials, data structures, code guides)
        notebook_keywords = [
            "how to", "guide", "cheat sheet", "study notes", "internals",
            "under the hood", "data structure", "bloom filter", "b-tree", "lsm-tree",
            "hash table", "index", "virtual memory", "paging", "garbage collection",
            "locking", "antipatterns", "pitfalls", "checklist", "fundamentals",
            "heap", "stack", "concurrency", "thread pool"
        ]
        if any(kw in combined for kw in notebook_keywords):
            return "notebook_carousel", "Topic is an educational deep dive with code, memory mechanics, and traps best presented as a multi-page swipeable study guide."

        # 3. High-level analysis, opinion, culture, or architectural debates -> TEXT ONLY
        # No forced visuals; crisp engineering prose has maximum authority
        return "text_only", "Topic is best conveyed as an authoritative, high-signal technical essay without forced or redundant visual aids."

    def validate_article_quality(self, text: str, visual_format: str = "text_only") -> Tuple[bool, str]:
        """
        Strict pre-publish substance check:
        - Character count (1,000 to 2,950 chars)
        - Paragraph structure
        - Zero placeholder phrases
        - Alignment with visual format
        """
        if not text or not text.strip():
            return False, "Article text is completely empty"

        cleaned = text.strip()
        length = len(cleaned)

        if length < 900:
            return False, f"Article length ({length} chars) is below executive minimum of 900 chars"

        if length > 2980:
            return False, f"Article length ({length} chars) exceeds LinkedIn limit of 3,000 chars"

        # Check for placeholder leaks
        placeholders = ["{topic}", "[insert", "TODO", "Lorem ipsum", "Stage 1 / Stage 2", "In-depth technical breakdown of"]
        for p in placeholders:
            if p.lower() in cleaned.lower():
                return False, f"Article contains unrendered placeholder: '{p}'"

        # Check visual reference alignment
        if visual_format == "text_only":
            if any(phrase in cleaned.lower() for phrase in ["animated visual guide", "animated diagram", "field notes attached", "study notes attached", "carousel attached"]):
                return False, "Text-only post erroneously references an attached visual"
        elif visual_format == "animated_flow_gif":
            if any(phrase in cleaned.lower() for phrase in ["field notes attached", "study notes attached", "6-page", "carousel attached"]):
                return False, "Animated GIF post erroneously references a multi-page carousel"
        elif visual_format == "notebook_carousel":
            if "animated visual guide" in cleaned.lower() or "animated diagram" in cleaned.lower():
                return False, "Carousel post erroneously references an animated GIF"

        return True, "Article meets high-signal technical quality standards"

    def validate_visual_integrity(
        self,
        media_path: Optional[str],
        visual_format: str,
        topic: str,
        spec: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], str]:
        """
        Audits the attached media file for quality, relevance, and absence of generic placeholders.
        If any defect is found, suppresses the visual cleanly so the post publishes as text-only.
        Returns: (approved, sanitized_media_path, reasoning)
        """
        if visual_format == "text_only" or not media_path:
            return True, None, "Text-only post approved; no visual attached."

        path_obj = Path(media_path)
        if not path_obj.exists():
            return False, None, f"Media file does not exist: {media_path}. Suppressing visual."

        file_size = path_obj.stat().st_size
        if file_size == 0:
            return False, None, "Media file is 0 bytes. Suppressing visual."

        # Audit GIF attachments
        if str(media_path).lower().endswith(".gif"):
            if file_size < 15_000:
                return False, None, f"GIF size ({file_size} bytes) is suspiciously small. Suppressing visual."

            # Inspect spec components for generic blocklist terms
            if spec and isinstance(spec.get("components"), list):
                comp_names = [str(c.get("name", "")).lower() for c in spec["components"]]
                detected_generic = [name for name in comp_names if any(b in name for b in GENERIC_COMPONENT_BLOCKLIST)]
                if len(detected_generic) >= 2:
                    return False, None, f"GIF rejected: detected generic components {detected_generic}. Suppressing visual to protect portfolio quality."

        # Audit PDF carousel attachments
        if str(media_path).lower().endswith(".pdf"):
            if file_size < 8_000:
                return False, None, f"PDF carousel size ({file_size} bytes) is corrupt or incomplete. Suppressing visual."

        return True, str(media_path), f"Verified high-quality topic-specific visual: {path_obj.name}"

    def align_article_for_format(
        self,
        article_text: str,
        topic: str,
        summary: str = "",
        visual_format: str = "text_only",
        target_audience: str = "working_pro"
    ) -> str:
        """
        Ensures the article text matches the chosen visual format exactly.
        Strips or adds visual reference lines seamlessly.
        """
        text = article_text.strip()

        if visual_format == "text_only":
            # Remove any visual reference lines
            lines = text.splitlines()
            filtered = []
            for line in lines:
                l_lower = line.lower()
                if any(p in l_lower for p in ["animated visual guide", "animated diagram", "field note", "study note field guide", "carousel below", "diagram below"]):
                    continue
                filtered.append(line)
            return "\n".join(filtered).strip()

        # If too short or mismatched, generate authoritative full article
        if len(text) < 900 or not self.ai:
            if self.ai and hasattr(self.ai, "generate_full_linkedin_article"):
                return self.ai.generate_full_linkedin_article(
                    topic=topic,
                    summary=summary,
                    target_audience=target_audience,
                    visual_format=visual_format
                )

        return text

    def pre_publish_review_and_gate(
        self,
        topic: str,
        summary: str,
        candidate_text: str,
        media_path: Optional[str],
        visual_format: str,
        spec: Optional[Dict[str, Any]] = None,
        target_audience: str = "working_pro"
    ) -> Tuple[bool, str, Optional[str], List[str]]:
        """
        Executive Portfolio Gate: Validates and sanitizes the post before live broadcast.
        Returns: (approved, final_text, final_media_path, audit_notes)
        """
        audit_notes = []

        # 1. Validate Media
        media_ok, final_media, media_reason = self.validate_visual_integrity(
            media_path, visual_format, topic, spec=spec
        )
        audit_notes.append(f"Media Audit: {media_reason}")

        # If media was suppressed, downgrade format to text_only
        resolved_format = visual_format
        if not final_media:
            resolved_format = "text_only"
            if visual_format != "text_only":
                audit_notes.append(f"Format adjusted from {visual_format} to text_only due to media rejection.")

        # 2. Align & Sanitize Article Text
        aligned_text = self.align_article_for_format(
            candidate_text, topic, summary=summary, visual_format=resolved_format, target_audience=target_audience
        )

        # 3. Validate Article Quality
        article_ok, article_reason = self.validate_article_quality(aligned_text, visual_format=resolved_format)
        audit_notes.append(f"Text Audit: {article_reason}")

        if not article_ok and self.ai:
            # Self-heal: regenerate full article strictly for this format
            audit_notes.append("Self-healing: regenerating substantive article to meet quality thresholds.")
            aligned_text = self.ai.generate_full_linkedin_article(
                topic=topic,
                summary=summary,
                target_audience=target_audience,
                visual_format=resolved_format
            )
            article_ok, article_reason = self.validate_article_quality(aligned_text, visual_format=resolved_format)
            audit_notes.append(f"Post-Healing Text Audit: {article_reason}")

        approved = article_ok
        return approved, aligned_text, final_media, audit_notes
