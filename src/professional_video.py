from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
AUDIO_SCRIPT = ROOT / "scripts" / "topic_video_audio.py"
MANIM_SCRIPT = ROOT / "scripts" / "topic_video_manim.py"
DEFAULT_OUTPUT_ROOT = ROOT / "generated_visuals" / "manim" / "topic_videos"


def _clean(value: Any) -> str:
    text = str(value or "")
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\ufffd", "")
    return re.sub(r"\s+", " ", text).strip()


def _first_sentence(value: str, limit: int = 110) -> str:
    text = _clean(value)
    match = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
    sentence = match[0] if match else text
    if len(sentence) > limit:
        sentence = sentence[: limit - 1].rstrip(" ,;:") + "."
    return sentence


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return (slug or "ai_topic")[:48]


class ProfessionalVideoGenerator:
    def __init__(self, output_root: Optional[Path] = None) -> None:
        self.output_root = Path(output_root or DEFAULT_OUTPUT_ROOT)

    def build_spec(self, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        title = _clean(topic_data.get("title") or "AI Systems")
        category = _clean(topic_data.get("category") or "AI ENGINEERING").upper()
        tagline = _clean(topic_data.get("tagline") or "A plain English AI explainer")
        summary = _clean(topic_data.get("summary") or f"{title} is a core AI engineering concept.")
        problem = _clean(
            topic_data.get("problem")
            or "Traditional systems hit a practical limit that this approach is designed to address."
        )
        solution = _clean(
            topic_data.get("solution")
            or "The mechanism changes how the system handles the hard part of the workload."
        )
        pro_tip = _clean(
            topic_data.get("pro_tip")
            or "Benchmark the real workload before committing to an architecture."
        )

        takeaways = [
            _clean(item)
            for item in (topic_data.get("key_takeaways") or [])
            if _clean(item)
        ][:3]
        while len(takeaways) < 3:
            fallback = [tagline, problem, solution][len(takeaways)]
            takeaways.append(fallback)

        recap_items = [
            tagline,
            _first_sentence(summary),
            _first_sentence(pro_tip),
        ]

        sections = [
            {
                "kind": "cover",
                "kicker": category,
                "heading": title,
                "body": tagline,
                "narration": f"{title}. {tagline}. Here is the plain English version.",
            },
            {
                "kind": "statement",
                "kicker": "WHAT IT IS",
                "heading": "The short definition",
                "body": summary,
                "narration": summary,
            },
            {
                "kind": "compare",
                "kicker": "WHY IT MATTERS",
                "heading": "The problem and the fix",
                "left_title": "Without it",
                "left_body": problem,
                "right_title": "With it",
                "right_body": solution,
                "narration": f"The problem: {problem} The fix: {solution}",
            },
            {
                "kind": "steps",
                "kicker": "WHAT CHANGES",
                "heading": "Three things to remember",
                "items": takeaways,
                "narration": "Three things to remember. "
                + " ".join(f"{index}. {item}" for index, item in enumerate(takeaways, 1)),
            },
            {
                "kind": "quote",
                "kicker": "PRODUCTION RULE",
                "heading": "Use it well",
                "body": pro_tip,
                "narration": pro_tip,
            },
            {
                "kind": "recap",
                "kicker": "RECAP",
                "heading": "The short version",
                "items": recap_items,
                "narration": f"To recap: {title}. {tagline}. Follow for plain English AI.",
            },
        ]

        return {
            "title": title,
            "slug": _slug(title),
            "category": category,
            "sections": sections,
        }

    def generate_dynamic_video(
        self,
        topic_data: Dict[str, Any],
        dry_run: bool = False,
        force: bool = False,
    ) -> Dict[str, Optional[str]]:
        spec = self.build_spec(topic_data)
        spec_hash = hashlib.sha256(
            json.dumps(spec, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:10]
        work_dir = self.output_root / f"{spec['slug']}_{spec_hash}"
        final_path = work_dir / f"{spec['slug']}_final.mp4"
        silent_path_planned = work_dir / "silent.mp4"
        srt_path = work_dir / "captions.srt"
        audio_path = work_dir / "narration_norm.wav"

        if dry_run:
            return {
                "video_path": str(final_path),
                "srt_path": str(srt_path),
                "audio_path": str(audio_path),
                "dry_run": "1",
                "duration": None,
            }

        if final_path.exists() and final_path.stat().st_size > 500_000 and not force:
            info = self._probe(final_path)
            return {
                "video_path": str(final_path),
                "srt_path": str(srt_path) if srt_path.exists() else None,
                "audio_path": str(audio_path) if audio_path.exists() else None,
                "dry_run": None,
                "duration": info.get("duration"),
            }

        try:
            work_dir.mkdir(parents=True, exist_ok=True)
            spec_path = work_dir / "spec.json"
            spec_path.write_text(
                json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            self._run(
                [sys.executable, str(AUDIO_SCRIPT), "--spec", str(spec_path)],
                cwd=ROOT,
            )

            timings_path = work_dir / "timings.json"
            if not timings_path.exists():
                raise RuntimeError("Audio pipeline did not produce timings.json")
            timings = json.loads(timings_path.read_text(encoding="utf-8"))
            total = float(timings.get("total") or 0)
            if total < 60:
                print(f"[ProfessionalVideo] Warning: video is only {total:.1f}s")
            if total > 180:
                print(f"[ProfessionalVideo] Warning: video exceeds 3 minutes ({total:.1f}s)")

            media_dir = work_dir / "render"
            if silent_path_planned.exists() and silent_path_planned.stat().st_size > 100_000:
                print(f"[ProfessionalVideo] Reusing silent render: {silent_path_planned}")
            else:
                env = os.environ.copy()
                env["TOPIC_VIDEO_SPEC"] = str(spec_path)
                env["TOPIC_VIDEO_MEDIA_DIR"] = str(media_dir)
                env["PYTHONIOENCODING"] = "utf-8"
                quality = os.getenv("TOPIC_VIDEO_QUALITY", "-qh")
                self._run(
                    [
                        sys.executable,
                        "-m",
                        "manim",
                        "render",
                        quality,
                        "-r",
                        "1080,1920",
                        "--fps",
                        "30",
                        str(MANIM_SCRIPT),
                        "TopicVideo",
                    ],
                    cwd=ROOT,
                    env=env,
                )

                renders = sorted(
                    (media_dir / "videos").rglob(f"{spec['slug']}.mp4"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if not renders:
                    raise RuntimeError("Manim did not produce a silent render")
                silent_path = renders[0]
                if silent_path != silent_path_planned:
                    silent_path_planned.write_bytes(silent_path.read_bytes())

            ass_path = work_dir / "captions.ass"
            if not ass_path.exists():
                raise RuntimeError("Captions were not generated")

            try:
                ass_filter = ass_path.relative_to(ROOT).as_posix()
            except ValueError:
                ass_filter = ass_path.as_posix().replace(":", "\\:")

            self._run(
                [
                    "ffmpeg", "-y",
                    "-i", str(silent_path_planned),
                    "-i", str(audio_path),
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-vf", f"ass={ass_filter}",
                    "-c:v", "libx264",
                    "-crf", "18",
                    "-preset", "medium",
                    "-pix_fmt", "yuv420p",
                    "-r", "30",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    "-movflags", "+faststart",
                    "-shortest",
                    "-sn",
                    str(final_path),
                ],
                cwd=ROOT,
            )

            info = self._probe(final_path)
            if not final_path.exists() or final_path.stat().st_size < 500_000:
                raise RuntimeError("Final video is missing or too small")
            if info.get("has_subtitle_stream"):
                raise RuntimeError("Final video contains a separate subtitle stream")

            return {
                "video_path": str(final_path),
                "srt_path": str(srt_path) if srt_path.exists() else None,
                "audio_path": str(audio_path) if audio_path.exists() else None,
                "dry_run": None,
                "duration": info.get("duration"),
            }
        except Exception as error:
            print(f"[ProfessionalVideo] Render error: {error}")
            return {
                "video_path": None,
                "srt_path": None,
                "audio_path": None,
                "dry_run": None,
                "duration": None,
            }

    def _run(
        self,
        cmd: list[str],
        cwd: Path,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "")[-3000:]
            raise RuntimeError(f"Command failed: {' '.join(cmd[:3])}\n{tail}")

    def _probe(self, path: Path) -> Dict[str, Any]:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-show_entries", "stream=codec_type",
                "-of", "json", str(path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            return {}
        data = json.loads(proc.stdout or "{}")
        streams = data.get("streams", [])
        return {
            "duration": float(data.get("format", {}).get("duration") or 0),
            "has_subtitle_stream": any(
                stream.get("codec_type") == "subtitle" for stream in streams
            ),
        }
