"""
Deterministic rule-based video edit agent.

Replaces Claude Code's role: reads transcripts, applies scoring rules,
generates a deterministic EDL, then hands off to render.py.

Usage:
    python helpers/agent.py --edit-dir <dir> --sources <video1> <video2> --template podcast

Pipeline:
    1. transcribe.py      → word-level transcripts (already run, cached)
    2. pack_transcripts.py → takes_packed.md (already run, cached)
    3. THIS SCRIPT         → reads packed transcripts, applies rules, writes edl.json
    4. render.py           → renders edl.json → final.mp4
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ── Filler words to strip ──────────────────────────────────────────────────
FILLER_WORDS = {
    "um", "uh", "er", "ah", "hmm", "mmm",
    "like", "you know", "i mean", "sort of", "kind of",
    "basically", "literally", "actually", "honestly",
    "right", "okay so", "so yeah",
}

# ── Templates: per-content-type editing presets ─────────────────────────────
TEMPLATES = {
    "podcast": {
        "description": "Podcast: remove fillers, tighten silences, keep speaker variety",
        "grade": "neutral_punch",
        "remove_fillers": True,
        "silence_pad_before_ms": 30,
        "silence_pad_after_ms": 80,
        "min_silence_for_cut_ms": 400,
        "target_duration_s": None,
        "keep_audio_events": True,
        "caption_style": "bold-overlay",
    },
    "rap": {
        "description": "Rap video: preserve beat energy, cut on transitions, kinetic captions",
        "grade": "warm_cinematic",
        "remove_fillers": False,
        "silence_pad_before_ms": 20,
        "silence_pad_after_ms": 30,
        "min_silence_for_cut_ms": 200,
        "target_duration_s": None,
        "keep_audio_events": True,
        "caption_style": "bold-overlay",
    },
    "interview": {
        "description": "Interview: keep Q&A structure, clean speaker gaps, remove dead air",
        "grade": "neutral_punch",
        "remove_fillers": True,
        "silence_pad_before_ms": 100,
        "silence_pad_after_ms": 200,
        "min_silence_for_cut_ms": 600,
        "target_duration_s": None,
        "keep_audio_events": True,
        "caption_style": "natural-sentence",
    },
    "tutorial": {
        "description": "Tutorial: preserve instructional clarity, remove ums, tighten",
        "grade": "neutral_punch",
        "remove_fillers": True,
        "silence_pad_before_ms": 50,
        "silence_pad_after_ms": 100,
        "min_silence_for_cut_ms": 500,
        "target_duration_s": None,
        "keep_audio_events": False,
        "caption_style": "natural-sentence",
    },
    "talking_head": {
        "description": "Talking head: minimal cuts, natural pacing, social-friendly trim",
        "grade": "neutral_punch",
        "remove_fillers": True,
        "silence_pad_before_ms": 40,
        "silence_pad_after_ms": 80,
        "min_silence_for_cut_ms": 300,
        "target_duration_s": 60,
        "keep_audio_events": True,
        "caption_style": "bold-overlay",
    },
}

# ── Audio event markers that should be preserved ────────────────────────────
AUDIO_EVENTS = {"(laughter)", "(applause)", "(sigh)", "(music)", "(cheering)", "(cough)"}


def load_sources_from_dir(sources_dir: Path) -> list[Path]:
    """Find all video files in a directory."""
    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
    return sorted([p for p in sources_dir.iterdir() if p.suffix.lower() in video_exts and p.is_file()])


def parse_packed_transcript(path: Path) -> dict[str, list[dict]]:
    """Parse takes_packed.md into {source_stem: [phrases]}.

    Each phrase has: start, end, speaker, text
    """
    if not path.exists():
        raise FileNotFoundError(f"Packed transcript not found: {path}")

    text = path.read_text()
    sources: dict[str, list[dict]] = {}
    current_source = None

    for line in text.split("\n"):
        # Header line: "## C0103  (duration: 43.0s, 8 phrases)"
        m = re.match(r"^##\s+(\S+)\s+\(duration:", line)
        if m:
            current_source = m.group(1)
            sources[current_source] = []
            continue

        # Phrase line: "  [002.52-005.36] S0 Ninety percent of what a web agent does is completely wasted."
        if current_source and line.startswith("  [") and "]" in line:
            m2 = re.match(r"^\s+\[(\d+\.\d+)-(\d+\.\d+)\]\s+(S\d+)\s+(.*)", line)
            if m2:
                start = float(m2.group(1))
                end = float(m2.group(2))
                speaker = m2.group(3)
                phrase_text = m2.group(4).strip()
                sources[current_source].append({
                    "start": start,
                    "end": end,
                    "speaker": speaker,
                    "text": phrase_text,
                    "duration": end - start,
                })

    return sources


def score_phrase(phrase: dict) -> float:
    """Score a phrase 0.0-1.0. Higher = more likely to keep."""
    score = 0.5  # neutral

    text = phrase["text"].lower()
    dur = phrase["duration"]

    # Audio events are keepers
    if any(ev in text for ev in AUDIO_EVENTS):
        score += 0.4

    # Filler detection lowers score
    word_count = len(text.split())
    if word_count <= 2 and any(fw in text.lower() for fw in FILLER_WORDS):
        score -= 0.6

    # Very short phrases with no substance
    if dur < 0.3 and word_count <= 1:
        score -= 0.3

    # Long phrases with substance
    if dur > 2.0 and word_count > 5:
        score += 0.15

    # Punctuation signals deliberate speech
    if text.endswith(".") or text.endswith("!") or text.endswith("?"):
        score += 0.1

    return max(0.0, min(1.0, score))


def is_filler(phrase: dict) -> bool:
    """Check if a phrase is pure filler to be removed."""
    text = phrase["text"].lower().strip()
    # Single filler word
    if text in FILLER_WORDS:
        return True
    # Very short with filler
    if phrase["duration"] < 0.5 and len(text.split()) <= 2:
        for fw in FILLER_WORDS:
            if fw in text:
                return True
    return False


def is_silence_gap(prev_end: float, next_start: float, threshold_ms: float) -> bool:
    """Check if gap between phrases exceeds silence threshold."""
    return (next_start - prev_end) * 1000 >= threshold_ms


def generate_edl(
    sources: dict[str, list[dict]],
    template: dict,
    source_paths: dict[str, str],
    output_path: Path,
) -> dict:
    """Generate a deterministic EDL from scored phrases.

    Rules applied in order:
    1. Remove filler phrases (if template.remove_fillers)
    2. Group consecutive phrases from same speaker
    3. Split groups at silence gaps exceeding threshold
    4. Apply padding to cut boundaries
    5. Output EDL JSON
    """
    ranges = []
    current_group = None  # {source, start, end, speaker, text_parts}
    group_id = 0

    for src_name, phrases in sources.items():
        if not phrases:
            continue

        phrases = sorted(phrases, key=lambda p: p["start"])

        for i, phrase in enumerate(phrases):
            # 1. Filter fillers
            if template.get("remove_fillers", True) and is_filler(phrase):
                if current_group:
                    _flush_group(current_group, ranges, template, group_id)
                    group_id += 1
                    current_group = None
                continue

            # 2. Check silence gap from previous phrase end
            if current_group and is_silence_gap(
                current_group["end"], phrase["start"],
                template["min_silence_for_cut_ms"]
            ):
                _flush_group(current_group, ranges, template, group_id)
                group_id += 1
                current_group = None

            # 3. Start or extend group
            if not current_group:
                current_group = {
                    "source": src_name,
                    "start": phrase["start"],
                    "end": phrase["end"],
                    "speaker": phrase["speaker"],
                    "text_parts": [phrase["text"]],
                }
            elif current_group["speaker"] == phrase["speaker"] and \
                 phrase["start"] - current_group["end"] < 1.0:
                current_group["end"] = phrase["end"]
                current_group["text_parts"].append(phrase["text"])
            else:
                _flush_group(current_group, ranges, template, group_id)
                group_id += 1
                current_group = {
                    "source": src_name,
                    "start": phrase["start"],
                    "end": phrase["end"],
                    "speaker": phrase["speaker"],
                    "text_parts": [phrase["text"]],
                }

    # Flush final group
    if current_group:
        _flush_group(current_group, ranges, template, group_id)

    total_duration = sum(r["end"] - r["start"] for r in ranges)
    edl = {
        "version": 1,
        "sources": source_paths,
        "ranges": ranges,
        "grade": template.get("grade", ""),
        "overlays": [],
        "subtitles": "master.srt",
        "total_duration_s": round(total_duration, 2),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(edl, indent=2))
    print(f"EDL written: {output_path}")
    print(f"  Segments: {len(ranges)}")
    print(f"  Total duration: {total_duration:.1f}s")
    print(f"  Template: {template.get('description', 'custom')}")
    print(f"  Grade: {template.get('grade', 'none')}")

    return edl


def _flush_group(group, ranges, template, group_id):
    """Add a padded group to the ranges list."""
    pad_before = template["silence_pad_before_ms"] / 1000
    pad_after = template["silence_pad_after_ms"] / 1000
    start = max(0.0, group["start"] - pad_before)
    end = group["end"] + pad_after
    text = " ".join(group["text_parts"])
    # Trim for quote
    quote = text[:120] + ("..." if len(text) > 120 else "")

    ranges.append({
        "source": group["source"],
        "start": round(start, 3),
        "end": round(end, 3),
        "beat": f"seg_{group_id:02d}",
        "note": f"S{group['speaker']}: {quote[:60]}",
        "quote": quote,
    })


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(description="Deterministic rule-based video edit agent")
    ap.add_argument("--edit-dir", type=Path, required=True,
                    help="Edit directory containing takes_packed.md and transcripts/")
    ap.add_argument("--sources-dir", type=Path, default=None,
                    help="Directory with source video files (for EDL source mapping)")
    ap.add_argument("--template", type=str, default="podcast",
                    choices=list(TEMPLATES.keys()),
                    help="Editing template/preset to use")
    ap.add_argument("--out", type=Path, default=None,
                    help="Output EDL path (default: <edit-dir>/edl.json)")
    ap.add_argument("--auto-render", action="store_true",
                    help="Auto-render after generating EDL")
    args = ap.parse_args()

    edit_dir = args.edit_dir.resolve()
    template = TEMPLATES[args.template]
    packed_path = edit_dir / "takes_packed.md"

    if not packed_path.exists():
        sys.exit(f"takes_packed.md not found in {edit_dir}. Run pack_transcripts.py first.")

    print(f"=== video-use Deterministic Edit Agent ===")
    print(f"  Template: {args.template} — {template['description']}")
    print(f"  Edit dir: {edit_dir}")

    # Parse packed transcript
    print(f"\nReading packed transcript: {packed_path}")
    sources = parse_packed_transcript(packed_path)

    if not sources:
        sys.exit("No phrases found in packed transcript.")

    total_phrases = sum(len(v) for v in sources.values())
    print(f"  Sources: {len(sources)} ({total_phrases} phrases)")

    # Build source path mapping
    source_paths = {}
    if args.sources_dir and args.sources_dir.exists():
        for p in load_sources_from_dir(args.sources_dir):
            source_paths[p.stem] = str(p.resolve())
    else:
        # Build from edit dir context
        for src in sources:
            source_paths[src] = str(edit_dir.parent.parent / f"{src}.mp4")

    # Generate EDL
    out_path = args.out or (edit_dir / "edl.json")
    edl = generate_edl(sources, template, source_paths, out_path)

    # Auto-render if requested
    if args.auto_render:
        print("\n--- Auto-rendering ---")
        import subprocess
        render_script = Path(__file__).resolve().parent / "render.py"
        output_video = edit_dir / "final.mp4"
        cmd = [
            sys.executable, str(render_script),
            str(out_path), "-o", str(output_video),
            "--build-subtitles",
        ]
        subprocess.run(cmd, check=True)
        print(f"\nDone! Output: {output_video}")

    return edl


if __name__ == "__main__":
    main()
