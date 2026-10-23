#!/usr/bin/env python3
"""
Render a title card and a run of big styled captions as transparent PNGs,
full-canvas-sized so each one can be dropped straight onto a Premiere video
track at (0,0) with no clip-position math needed on the Premiere side.

Why full-canvas instead of tight-cropped text boxes: Premiere's MCP tools
expose `set_clip_properties` for position, but reasoning about anchor points
and offsets across many generated images multiplies the chance of a stray
image landing off-frame. Baking the exact position into each PNG at generation
time means every add_to_timeline call is identical (time 0, position 0,0) and
the only thing that varies is duration.

Two things this script does that are easy to get wrong by hand:
1. Re-chunks transcript segments (which arrive as one whole sentence/phrase)
   into shorter caption-card-sized pieces, interpolating timestamps by word
   position — segment-level timing divided into per-chunk windows.
2. Word-wraps and auto-shrinks font size per card so long lines never overflow
   the canvas width, instead of using one fixed size that breaks on long cues.

Usage:
    python3 caption_cards.py transcript.json --out-dir cards/ \
        --canvas-width 2160 --canvas-height 3840 \
        --title-text "MY BRAND" --title-font /path/PlayfairDisplay-Bold.otf \
        --caption-font /path/Montserrat-Bold.otf \
        --skip-before 5.0 --words-per-card 6

transcript.json: [{"start": 0.0, "end": 8.2, "text": "..."}, ...]  (seconds, already offset-merged)

Writes PNGs to --out-dir and prints a manifest JSON to stdout:
{
  "title": {"path": "...", "start": 0, "end": 5},
  "captions": [{"path": "...", "start": ..., "end": ..., "text": "..."}, ...]
}
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

TEAL = (4, 104, 101, 255)
CORAL = (255, 138, 91, 255)
WHITE = (255, 255, 255, 255)
SHADOW = (0, 0, 0, 160)


def wrap_and_fit(draw, text, font_path, max_width, max_font_size, min_font_size=40):
    """Shrink font size until every wrapped line fits max_width."""
    size = max_font_size
    while size >= min_font_size:
        font = ImageFont.truetype(font_path, size)
        words = text.split()
        lines, current = [], ""
        for w in words:
            trial = (current + " " + w).strip()
            if draw.textlength(trial, font=font) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        widest = max((draw.textlength(l, font=font) for l in lines), default=0)
        if widest <= max_width:
            return font, lines, size
        size -= 4
    return ImageFont.truetype(font_path, min_font_size), lines, min_font_size


def render_card(text, font_path, canvas_w, canvas_h, out_path, max_font_size,
                 anchor="upper", text_color=WHITE, accent_color=CORAL,
                 backing_bar=True, side_margin_frac=0.08,
                 stroke_color=None, stroke_width=0):
    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    max_width = canvas_w * (1 - 2 * side_margin_frac)

    font, lines, size = wrap_and_fit(draw, text, font_path, max_width, max_font_size)
    line_height = int(size * 1.25)
    block_height = line_height * len(lines)

    if anchor == "upper":
        block_top = int(canvas_h * 0.10)
    elif anchor == "lower":
        block_top = int(canvas_h * 0.82) - block_height
    else:
        block_top = (canvas_h - block_height) // 2

    if backing_bar:
        pad_x, pad_y = 40, 24
        widest = max((draw.textlength(l, font=font) for l in lines), default=0)
        bar_left = (canvas_w - widest) / 2 - pad_x
        bar_right = (canvas_w + widest) / 2 + pad_x
        draw.rounded_rectangle(
            [bar_left, block_top - pad_y, bar_right, block_top + block_height + pad_y],
            radius=18, fill=SHADOW,
        )

    accent_bar_h = 6
    draw.rectangle(
        [(canvas_w - canvas_w * 0.2) / 2, block_top - 20,
         (canvas_w + canvas_w * 0.2) / 2, block_top - 20 + accent_bar_h],
        fill=accent_color,
    )

    y = block_top
    for line in lines:
        w = draw.textlength(line, font=font)
        x = (canvas_w - w) / 2
        if stroke_width:
            draw.text((x, y), line, font=font, fill=text_color,
                      stroke_width=stroke_width, stroke_fill=stroke_color)
        else:
            draw.text((x, y), line, font=font, fill=text_color)
        y += line_height

    img.save(out_path)
    return out_path


def chunk_transcript(segments, words_per_card, skip_before):
    """Split segments into ~words_per_card-word cards, interpolating timing
    linearly by word position within the segment, and drop/trim anything
    that lands entirely before skip_before (reserved for the title card)."""
    cards = []
    for seg in segments:
        words = seg["text"].split()
        if not words:
            continue
        seg_start, seg_end = seg["start"], seg["end"]
        seg_dur = max(seg_end - seg_start, 0.01)
        n = len(words)
        for i in range(0, n, words_per_card):
            chunk_words = words[i:i + words_per_card]
            frac_start = i / n
            frac_end = min(i + words_per_card, n) / n
            c_start = seg_start + frac_start * seg_dur
            c_end = seg_start + frac_end * seg_dur
            if c_end <= skip_before:
                continue
            if c_start < skip_before < c_end:
                c_start = skip_before
            cards.append({"start": round(c_start, 3), "end": round(c_end, 3),
                           "text": " ".join(chunk_words)})
    return cards


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript_json")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--canvas-width", type=int, required=True)
    ap.add_argument("--canvas-height", type=int, required=True)
    ap.add_argument("--title-text")
    ap.add_argument("--title-font", required=True)
    ap.add_argument("--title-duration", type=float, default=5.0)
    ap.add_argument("--caption-font", required=True)
    ap.add_argument("--skip-before", type=float, default=0.0, help="Captions ending before this time are dropped (reserved for title)")
    ap.add_argument("--words-per-card", type=int, default=6)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    with open(args.transcript_json) as f:
        segments = json.load(f)

    manifest = {"title": None, "captions": []}

    if args.title_text:
        title_path = os.path.join(args.out_dir, "title.png")
        render_card(args.title_text, args.title_font, args.canvas_width, args.canvas_height,
                    title_path, max_font_size=220, anchor="upper",
                    text_color=TEAL, accent_color=CORAL, backing_bar=False,
                    stroke_color=WHITE, stroke_width=4)
        manifest["title"] = {"path": title_path, "start": 0, "end": args.title_duration}

    cards = chunk_transcript(segments, args.words_per_card, args.skip_before)
    for idx, card in enumerate(cards):
        path = os.path.join(args.out_dir, f"caption-{idx:03d}.png")
        render_card(card["text"], args.caption_font, args.canvas_width, args.canvas_height,
                     path, max_font_size=150, anchor="lower",
                     text_color=WHITE, accent_color=TEAL, backing_bar=False,
                     stroke_color=(0, 0, 0, 255), stroke_width=7)
        manifest["captions"].append({"path": path, "start": card["start"], "end": card["end"], "text": card["text"]})

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
