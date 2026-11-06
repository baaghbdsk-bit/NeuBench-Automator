from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
from pathlib import Path

import edge_tts

CAPTION_FONT = os.getenv("TOPIC_VIDEO_CAPTION_FONT", "Segoe UI")
VOICE = "en-US-AndrewMultilingualNeural"
RATE = "+3%"
PAD_SECONDS = 0.45
WORDS_PER_LINE = 5


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])


def duration(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", str(path),
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    )
    return float(json.loads(proc.stdout)["format"]["duration"])


def fmt_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_ass_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def norm_word(value: str) -> str:
    return re.sub(r"[^a-z0-9']", "", value.lower())


def restore_punctuation(words: list[dict], text: str) -> list[dict]:
    tokens = text.split()
    result: list[dict] = []
    token_index = 0
    for word in words:
        target = norm_word(word["text"])
        match_index = None
        for candidate in range(token_index, min(token_index + 4, len(tokens))):
            if norm_word(tokens[candidate]) == target:
                match_index = candidate
                break
        if match_index is None:
            result.append(word)
            continue
        result.append({**word, "text": tokens[match_index]})
        token_index = match_index + 1
    return result


async def synthesize(text: str, path: Path, words_path: Path) -> list[dict]:
    if path.exists() and path.stat().st_size > 0 and words_path.exists():
        return json.loads(words_path.read_text(encoding="utf-8"))

    communicate = edge_tts.Communicate(
        text, VOICE, rate=RATE, boundary="WordBoundary"
    )
    audio = bytearray()
    words: list[dict] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            start = chunk["offset"] / 10_000_000
            end = (chunk["offset"] + chunk["duration"]) / 10_000_000
            words.append({"text": chunk["text"], "start": start, "end": end})

    if not audio:
        raise RuntimeError(f"No audio returned for: {text[:60]}")

    path.write_bytes(bytes(audio))
    words_path.write_text(json.dumps(words, indent=2), encoding="utf-8")
    return words


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, help="Path to the topic video spec JSON")
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    out = spec_path.parent
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    sections = spec["sections"]
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "audio_raw"
    raw_dir.mkdir(exist_ok=True)

    parts: list[Path] = []
    durations: list[float] = []
    captions: list[str] = []
    all_words: list[dict] = []

    for i, section in enumerate(sections, 1):
        text = section["narration"]
        raw = raw_dir / f"section_{i:02d}.mp3"
        words_path = raw_dir / f"section_{i:02d}.words.json"
        padded = raw_dir / f"section_{i:02d}.wav"
        words = asyncio.run(synthesize(text, raw, words_path))
        words = restore_punctuation(words, text)
        run([
            "ffmpeg", "-y", "-i", str(raw),
            "-af", f"apad=pad_dur={PAD_SECONDS}",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(padded),
        ])
        parts.append(padded)
        durations.append(round(duration(padded), 3))
        captions.append(section.get("heading", ""))
        for word in words:
            all_words.append({
                "text": word["text"],
                "start": word["start"],
                "end": word["end"],
                "section": i,
            })

    concat = raw_dir / "concat.txt"
    concat.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in parts),
        encoding="utf-8",
    )
    narration = out / "narration.wav"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c:a", "pcm_s16le", str(narration),
    ])

    normalized = out / "narration_norm.wav"
    run([
        "ffmpeg", "-y", "-i", str(narration),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(normalized),
    ])

    offsets: list[float] = []
    total = 0.0
    for d in durations:
        offsets.append(total)
        total += d

    entries: list[tuple[float, float, str]] = []
    for section_index, section in enumerate(sections):
        offset = offsets[section_index]
        section_words = [w for w in all_words if w["section"] == section_index + 1]
        if not section_words:
            section_words = [{
                "text": section.get("caption", ""),
                "start": 0.0,
                "end": max(0.5, durations[section_index] - PAD_SECONDS),
            }]

        chunks: list[list[dict]] = []
        current: list[dict] = []
        for word in section_words:
            current.append(word)
            ends_sentence = word["text"].endswith((".", "!", "?", ":", ";"))
            if len(current) >= WORDS_PER_LINE or ends_sentence:
                chunks.append(current)
                current = []
        if current:
            chunks.append(current)

        for chunk in chunks:
            text = " ".join(w["text"] for w in chunk).strip()
            start = offset + chunk[0]["start"]
            end = offset + max(chunk[-1]["end"], chunk[0]["start"] + 0.12)
            end = min(end, offset + durations[section_index] - 0.02)
            if end <= start:
                end = start + 0.12
            entries.append((start, end, text))

    srt_lines = [
        f"{i}\n{fmt_ts(start)} --> {fmt_ts(end)}\n{text}\n"
        for i, (start, end, text) in enumerate(entries, 1)
    ]
    (out / "captions.srt").write_text("\n".join(srt_lines), encoding="utf-8")

    ass_header = f"""[Script Info]
Title: Plain AI topic video
ScriptType: v4.00+
WrapStyle: 2
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{CAPTION_FONT},64,&H00FFFFFF,&H00FFFFFF,&H00141414,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,2,80,80,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass_lines = [
        f"Dialogue: 0,{fmt_ass_ts(start)},{fmt_ass_ts(end)},Caption,,0,0,0,,{text}"
        for start, end, text in entries
    ]
    (out / "captions.ass").write_text(
        ass_header + "\n".join(ass_lines) + "\n", encoding="utf-8"
    )

    timings = {
        "durations": durations,
        "total": round(total, 3),
        "captions": captions,
        "word_count": len(all_words),
        "srt_lines": len(entries),
        "audio": str(normalized),
        "srt": str(out / "captions.srt"),
        "ass": str(out / "captions.ass"),
    }
    (out / "timings.json").write_text(json.dumps(timings, indent=2), encoding="utf-8")
    print(json.dumps(timings, indent=2))


if __name__ == "__main__":
    main()
