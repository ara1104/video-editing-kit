---
name: edit-video
description: Front door for editing videos for social media. Use whenever the user hands over a raw clip or folder of clips and says anything like "edit this", "make this postable", "make this a reel/TikTok", "clean this up", "add captions", "make it more engaging", or "add graphics". Watches the footage, asks what she wants in plain language, then routes to the right workflow (Premiere edit, HyperFrames edit, graphic overlays, or word-synced effects).
---

# Edit Video (front door)

The user is a beginner. Keep questions short, offer sensible defaults, and
show progress in plain language ("Cutting the pauses now…"). Never delete or
overwrite her original files. Write all outputs to an `edited/` folder next
to the source.

## 1. Look before you decide

1. Get the file path(s). If she drags a file into the chat, use that path.
2. Use claude-video-vision (`video_info`, then `video_watch`) to see what the
   footage is: talking to camera, a montage/B-roll, a screen recording, or a
   mix. Note how long it is, whether it's vertical, and whether it already has
   captions burned in.
3. If those tools are missing, run the `setup` skill from this kit first.

## 2. Ask (one message, with defaults)

- **Where is it going?** Default: Instagram Reels / TikTok, so 9:16 vertical,
  1080×1920, 30–60s.
- **What should it feel like?** Clean and natural (default), punchy/viral, or
  aesthetic/calm.
- **Captions?** Default: yes, for anything with talking.
- **Any brand, handle, logo, or music** to include? Never invent one.

## 3. Route

| What she has / wants | Use |
|---|---|
| Raw footage that needs cutting (pauses, filler words, best takes), color, captions, export, **and Premiere Pro is set up** | `premiere-clean-edit` (this kit) |
| Same job, **no Premiere** | The ffmpeg path below |
| A talking-head video that should get designed title cards, lower-thirds, quotes, or callouts | `talking-head-recut` (this kit; needs the HyperFrames plugin) |
| An already-edited video that should get word-synced stickers, emojis, location chips, logo pops, or "viral" effects | `video-overlays` (this kit) |
| Several of the above | Do them in order: cut and clean first, then captions or cards, then overlays. Each step's output is the next step's input. |

## ffmpeg path (clean cut without Premiere)

Reuse `premiere-clean-edit`'s analysis, then render with ffmpeg instead of Premiere:

1. Follow `premiere-clean-edit` steps 2–4: ffprobe, `video_analyze` (silence +
   transcription), then `scripts/build_cutlist.py ... --srt-out captions.srt`.
   It prints `keep_segments` and writes captions already re-timed to the cut.
2. Cut: build one `trim`/`atrim` pair per keep segment and `concat` them in a
   single `-filter_complex`. Write a small Python script that generates the
   filter from `keep_segments`; never hand-type the timestamps.
3. Frame and caption in one pass: scale/crop to 1080×1920
   (`scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`), then
   burn captions with `subtitles=captions.srt:force_style='Fontname=Arial,Bold=1,FontSize=14,Alignment=2,MarginV=90,Outline=2'`.
   Keep captions out of the bottom ~15% so platform UI doesn't cover them.
4. Light color fix only if the footage needs it, for example
   `eq=contrast=1.04:saturation=1.06`. Check a frame before and after.
5. Encode: `-c:v libx264 -crf 18 -preset medium -r 30 -c:a aac -b:a 192k -movflags +faststart`.

## 4. Before calling it done

- Extract 3–5 frames from the final MP4 with ffmpeg and look at them yourself.
- `ffprobe` the file to confirm it has audio and the right size.
- Tell her where the file is, how long it is, and what you changed. Offer one
  or two easy tweaks ("want it shorter?", "different caption style?").
