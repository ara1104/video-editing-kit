#!/usr/bin/env python3
"""
Turn a claude-video-vision `video_analyze` result (silence intervals + word-level
transcript) into a cut list Premiere can execute, plus a caption file timed to
the POST-CUT timeline.

Why this exists as a script instead of ad-hoc reasoning: cut segments have to be
merged/padded so a cut never lands mid-word, and every downstream caption
timestamp has to be shifted by the cumulative duration of everything removed
before it. That's easy to get subtly wrong by eyeballing it, and getting it
wrong means captions drift out of sync with the audio. Doing it in code makes
it deterministic and checkable.

Usage:
    python3 build_cutlist.py analysis.json --duration 47.2 \
        [--min-gap 0.35] [--pad 0.08] [--srt-out captions.srt]

Input JSON shape (subset of whisper-style output; extra keys are ignored):
{
  "silence": [{"start": 4.1, "end": 4.6}, ...],
  "segments": [
    {"start": 0.0, "end": 2.3, "text": "So here's the thing.",
     "words": [{"word": "So", "start": 0.0, "end": 0.2}, ...]},
    ...
  ]
}

Output JSON (printed to stdout):
{
  "cuts": [{"start": ..., "end": ..., "reason": "silence|filler|stutter"}, ...],
  "keep_segments": [{"start": ..., "end": ...}, ...],
  "flagged_for_review": [{"word": "like", "start": ..., "end": ..., "context": "..."}],
  "caption_cues": [{"start": ..., "end": ..., "text": "..."}, ...],   # post-cut timeline
  "original_duration": ...,
  "new_duration": ...
}
"""

import argparse
import json
import sys

# "Hard" fillers get auto-cut — they never carry meaning on their own.
HARD_FILLERS = {"um", "umm", "uh", "uhh", "uhm", "er", "erm"}

# "Soft" fillers often ARE the personality/voice (e.g. "you know what I'm
# saying?" as a sign-off). Never auto-cut these — flag them so a human decides.
SOFT_FILLERS = {"like", "so", "right", "i mean", "you know", "basically", "actually"}


def merge_intervals(intervals, gap_tolerance=0.05):
    """Merge overlapping/adjacent (start,end) intervals, sorted by start."""
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda iv: iv["start"])
    merged = [dict(ordered[0])]
    for iv in ordered[1:]:
        last = merged[-1]
        if iv["start"] <= last["end"] + gap_tolerance:
            last["end"] = max(last["end"], iv["end"])
        else:
            merged.append(dict(iv))
    return merged


def find_stutters(words):
    """Immediate word repeats ('the the', 'I I') — cut the first occurrence."""
    cuts = []
    for i in range(len(words) - 1):
        a, b = words[i], words[i + 1]
        if a["word"].strip().lower() == b["word"].strip().lower() and (b["start"] - a["end"]) < 0.6:
            cuts.append({"start": a["start"], "end": a["end"], "reason": "stutter"})
    return cuts


def build(analysis, duration, min_gap, pad):
    silence = analysis.get("silence", [])
    segments = analysis.get("segments", [])
    words = [w for seg in segments for w in seg.get("words", [])]
    words.sort(key=lambda w: w["start"])

    cuts = []

    # 1. Silence gaps worth cutting (padded so we don't eat the tail/head of speech)
    for gap in silence:
        span = gap["end"] - gap["start"]
        if span >= min_gap:
            cuts.append({
                "start": min(gap["start"] + pad, gap["end"]),
                "end": max(gap["end"] - pad, gap["start"]),
                "reason": "silence",
            })

    # 2. Hard filler words
    flagged = []
    for w in words:
        token = w["word"].strip().lower().strip(".,!?")
        if token in HARD_FILLERS:
            cuts.append({"start": w["start"], "end": w["end"], "reason": "filler"})
        elif token in SOFT_FILLERS:
            flagged.append({
                "word": w["word"], "start": w["start"], "end": w["end"],
                "context": _context(words, w),
            })

    # 3. Stutters / false starts
    cuts.extend(find_stutters(words))

    cuts = merge_intervals(cuts)

    # Complement -> keep_segments
    keep = []
    cursor = 0.0
    for c in cuts:
        if c["start"] > cursor:
            keep.append({"start": cursor, "end": c["start"]})
        cursor = max(cursor, c["end"])
    if cursor < duration:
        keep.append({"start": cursor, "end": duration})

    removed_before = _removed_before_fn(cuts)

    caption_cues = []
    for seg in segments:
        kept_words = [w for w in seg.get("words", []) if not _inside_any(w, cuts)]
        if not kept_words:
            continue
        new_start = kept_words[0]["start"] - removed_before(kept_words[0]["start"])
        new_end = kept_words[-1]["end"] - removed_before(kept_words[-1]["end"])
        text = " ".join(w["word"].strip() for w in kept_words)
        caption_cues.append({"start": round(new_start, 3), "end": round(new_end, 3), "text": text})

    new_duration = sum(k["end"] - k["start"] for k in keep)

    return {
        "cuts": [_round(c) for c in cuts],
        "keep_segments": [_round(k) for k in keep],
        "flagged_for_review": flagged,
        "caption_cues": caption_cues,
        "original_duration": duration,
        "new_duration": round(new_duration, 3),
    }


def _context(words, target, radius=3):
    idx = words.index(target)
    lo, hi = max(0, idx - radius), min(len(words), idx + radius + 1)
    return " ".join(w["word"].strip() for w in words[lo:hi])


def _inside_any(word, cuts):
    mid = (word["start"] + word["end"]) / 2
    return any(c["start"] <= mid <= c["end"] for c in cuts)


def _removed_before_fn(cuts):
    ordered = sorted(cuts, key=lambda c: c["start"])

    def _fn(t):
        total = 0.0
        for c in ordered:
            if c["end"] <= t:
                total += c["end"] - c["start"]
            elif c["start"] < t:
                total += t - c["start"]
            else:
                break
        return total
    return _fn


def _round(d, ndigits=3):
    return {k: (round(v, ndigits) if isinstance(v, float) else v) for k, v in d.items()}


def to_srt(cues):
    def ts(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int(round((t - int(t)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, cue in enumerate(cues, start=1):
        lines.append(str(i))
        lines.append(f"{ts(cue['start'])} --> {ts(cue['end'])}")
        lines.append(cue["text"])
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("analysis_json", help="Path to the video_analyze result JSON")
    ap.add_argument("--duration", type=float, required=True, help="Original clip duration in seconds (ffprobe it)")
    ap.add_argument("--min-gap", type=float, default=0.35, help="Minimum silence duration to cut (seconds)")
    ap.add_argument("--pad", type=float, default=0.08, help="Seconds of silence to leave around speech when cutting a gap")
    ap.add_argument("--srt-out", help="If set, also write an SRT file of the post-cut captions here")
    args = ap.parse_args()

    with open(args.analysis_json) as f:
        analysis = json.load(f)

    result = build(analysis, args.duration, args.min_gap, args.pad)
    print(json.dumps(result, indent=2))

    if args.srt_out:
        with open(args.srt_out, "w") as f:
            f.write(to_srt(result["caption_cues"]))
        print(f"\nWrote {len(result['caption_cues'])} caption cues to {args.srt_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
