---
name: premiere-clean-edit
description: Turn raw footage into a finished, postable video in Adobe Premiere Pro — both talking-head/screen-recording clips AND no-dialogue montage/B-roll (room tours, walkthroughs, trip footage, property/product showcases). Use whenever the user has recorded video and wants it edited, cleaned up, color graded, cut together, or made ready to post — even if they just say "edit this video," "cut this together," "make this postable," or hand over a raw clip/folder of clips without further instruction. Drives the premiere-pro MCP tools directly (project/sequence creation, cutting, transitions, color, captions, export) plus claude-video-vision for audio analysis and clip review — do not attempt this by hand-waving through Premiere's GUI.
---

# Premiere Clean Edit

Take one or more raw video files and turn them into finished, exportable videos:
cut the dead air and filler words, correct the color, add burned-in-ready
captions, and export both a horizontal and vertical version — all by driving
Adobe Premiere Pro through the `premiere-pro` MCP tools, with `claude-video-vision`
doing the audio analysis Premiere itself can't do headlessly.

Premiere Pro must already be open on the machine with the `premiere-pro` MCP
server connected and the **MCP Bridge (CEP)** panel started (Window → Extensions)
— this skill can't launch the app. Run the kit's `setup` skill if the server isn't
installed. If tools like `create_sequence` aren't listed directly, the server is
hiding them behind `search_tools` / `invoke_tool`: use those, or re-register the
server with `PREMIERE_MCP_TOOLSET=full`. If any `mcp__premiere-pro__*`
tool call fails with a connection error, tell the user to open Premiere Pro and
retry rather than working around it.

## Why this is two MCPs, not one

`premiere-pro` can cut, grade, and export — but it has no way to *decide where*
to cut. There's no silence-detection or transcription tool in that server.
`claude-video-vision`'s `video_analyze` fills that gap: it runs ffmpeg silence
detection and local whisper transcription (word-level timestamps) on the raw
file *before* it ever touches Premiere. The cut list gets computed once, in
plain data, then executed as a sequence of MCP calls. Don't try to eyeball cut
points by scrubbing the Premiere timeline — you don't have frame-accurate
hearing, the analysis pass does.

## Two edit types — pick before starting

- **Speech-driven** (talking-head, screen recording, voiceover): follow the
  Pipeline below — silence/filler cutting and captions are the work.
- **Montage / B-roll** (room tour, walkthrough, trip footage — no dialogue
  driving the cut): skip the silence/filler steps and follow the Montage
  pipeline further down. Captions optional; music and pacing are the work.

Both types finish in the House Style below. When in doubt which type it is:
if the audio doesn't carry the story, it's a montage.

## House style (default social-media look)

These defaults came from comparing an automated assembly against a hand-made
final cut. A first cut that ignores them usually gets redone by hand. If the
user has her own style or a reference video she likes, her taste wins: ask,
and adjust these rules to match.

- **Bookend with the strongest brand/establishing shot** — open on it like a
  title card AND close on it. Story order beats chronological order; a
  branded sign or hero shot outranks "the clip that happened first."
- **Cut ruthlessly.** One beat per scene, ~3–6 seconds each, best moment
  only — never the full clip. A good reference cut kept 46s from 80s of usable
  footage. Target ~45–60s total for social deliverables.
- **Drop weak footage entirely** — shaky handheld walk-ins, fumbling starts.
  If a clip needs an apology, it doesn't make the cut.
- **Alternate wides with detail close-ups** — room wide → stovetop knobs,
  bedroom wide → headboard texture. Details between establishing shots.
- **Cross-dissolves between scenes, not hard cuts.** Hard cuts only for
  deliberate emphasis (a good reference cut has one, maybe two).
- **Music-first audio for montages.** Continuous music bed (~-11 LUFS), no
  silence; original camera/ambient audio removed or fully buried, not just
  ducked. If no track is provided, ask for one or leave a muted timeline and
  flag it — never ship raw ambient audio.
- **Vertical-first delivery:** 1080×1920, 30fps, H.264 ~12 Mbps is the
  primary deliverable even from 4K60 source. Horizontal is the optional
  extra, not the other way around.

For **storytime/UGC clips** (a real moment with dialogue — an encounter, a
reaction, a candid interaction), add four rules on top of the above:

- **Cold-open on the viral moment.** Put the single most arresting 2–4s
  close-up from the *middle* of the encounter at 0:00, then rewind and tell
  the story from the beginning. Chronological order is the baseline failure
  mode here — never open on setup/context.
- **Leave room for a narrated hook.** Creators often record a direct-address voiceover
  line over the cold open ("I know y'all probably wondering why…"). The
  edit can't generate this — build the cold open, then flag that the hook
  VO needs recording (or ask for it) rather than shipping without one.
- **End on the brand card.** If the user has a brand, product, or handle to
  promote, close on a short end card (~3–5s) with it. Ask for her logo or
  handle; never invent one.
- **Level the dialogue** (~-16 LUFS, narrow range) instead of laying a
  music bed — for storytime, speech carries; for montage, music carries.

## Pipeline

Run these steps in order. For a batch of clips (e.g. a week's worth of
recordings), repeat steps 2–8 per clip inside one shared Premiere project.

### 1. Confirm inputs

Ask (or infer from context) for: the raw file path(s), and whether this is a
single deliverable or needs both a horizontal (LinkedIn-style, 16:9) and
vertical (Threads/TikTok/Reels, 9:16) export. If the user doesn't say, default
to exporting both — reframing is cheap once the edit is locked.

### 2. Get source facts with ffprobe

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate \
  -show_entries format=duration -of json "<raw-file>"
```

You need `width`, `height`, `r_frame_rate` (parse the fraction, e.g. `30000/1001` ≈ 29.97),
and `duration`. The sequence you create in Premiere should match these —
mismatched sequence settings cause silent scaling/frame-rate conforming that
degrades quality.

### 3. Analyze audio — silence + transcript

Call `mcp__claude-video-vision__video_analyze` on the raw file with
`filters: {silence: true, transcription: true}`. This returns silence
intervals and a word-level transcript (whisper runs locally via whisper.cpp —
no API key needed, first run may take a minute to load the model).

Save the result to a JSON file — you'll feed it to the cut-list script next.

### 4. Compute the cut list

Run `scripts/build_cutlist.py` on the analysis JSON:

```bash
python3 "<skill-path>/scripts/build_cutlist.py" analysis.json \
  --duration <ffprobe-duration> --srt-out captions.srt
```

This script exists because getting this right by hand is error-prone in a
specific way: every caption timestamp after a cut has to shift by the
cumulative duration of everything removed before it, or captions drift out of
sync. The script handles that plus the merge/padding logic for silence gaps so
a cut never lands mid-word.

It auto-cuts three things: silence gaps ≥0.35s (padded 0.08s so speech isn't
clipped), hard filler words (um, uh, er and variants), and stutters/false
starts (immediate word repeats like "the the"). It deliberately does **not**
auto-cut soft fillers (like, so, right, you know, actually) — those are often
someone's actual speaking voice, not noise. Real feedback from past UGC edits: an ad-lib like "you know what I'm saying?" was flagged as *the
most authentic thing in the batch* and explicitly kept, not trimmed. The
script surfaces these in `flagged_for_review` with context — skim that list
and only escalate to the user if something looks like genuine filler rather
than voice/personality; when in doubt, leave it in.

### 5. Build the Premiere project and rough cut

1. `create_project` (or `open_project` if reusing one) and `create_sequence`
   with settings matching ffprobe's output (step 2).
2. `import_media` the raw file, `add_to_timeline` at time 0 on track 0.
3. Walk the cut list's `cuts` array **in descending order of `start` time** and
   for each: `razor_timeline_at_time` at the cut's start and end, then
   `remove_from_timeline` on the resulting middle clip with
   `deleteMode: "ripple"`. Descending order matters — ripple-deleting an
   earlier cut shifts every later timestamp, so if you go forward the
   remaining cut points from step 4 no longer line up with anything.
4. Confirm the sequence duration now roughly matches `new_duration` from the
   cut-list JSON.

### 6. Color correct

Default look (the user asked for clean/natural, not a stylized grade): fix
white balance, roll off harsh highlights, lift crushed shadows slightly,
modest saturation. You can't do this blind — `color_correct`'s parameters are
manual sliders with no auto-detection behind them. So:

1. `export_frame` a representative frame (a few seconds into the clip, past
   any intro).
2. Look at it. Judge white balance (skin tones shouldn't read orange or blue),
   exposure (is anything clipped/crushed), and contrast.
3. Apply modest `color_correct` adjustments on the timeline clip — small
   nudges (single-digit values), not dramatic swings. Natural correction
   should be barely noticeable as "correction," just as "this looks right."
4. `export_frame` again and compare. Iterate once or twice if something's
   still off; don't loop indefinitely chasing perfection on a single frame.

If the user has a `.cube`/`.3dl` LUT they want applied instead of/in addition
to manual correction, use `apply_lut` with a low-to-moderate `intensity`
(0.5–0.8) on top of the base correction rather than instead of it — a LUT
alone won't fix an actual white-balance problem, it'll just recolor it.

### 7. Captions

1. `import_media` the `captions.srt` written in step 4.
2. `create_caption_track` on the sequence, pointing `projectItemId` at the
   imported SRT.

This only works because step 4 already re-timed the SRT to the *post-cut*
timeline — if you regenerate captions from the original (pre-cut) transcript
timestamps here, they'll be out of sync with the edited video.

### 8. Reframe for the second aspect ratio

Reframing crops *into* existing frame using motion tracking — it works well
going from wider to narrower (16:9 → 9:16) but there's no real frame data to
invent going narrower to wider (9:16 → 16:9 would require generative
expansion Premiere's auto-reframe doesn't do). So:

- Shot horizontal → `auto_reframe_sequence` with `numerator: 9, denominator: 16`
  for the vertical export. This is the common case and works well.
- Shot vertical → if a horizontal version is genuinely needed, say so to the
  user rather than silently padding/blurring the sides; a reshoot or a
  letterboxed pillarbox export is usually the better call than a bad AI
  reframe.

### 9. Export

Final social deliverables are H.264 1080p, not ProRes — this is a finished
export, not a Premiere-to-Premiere handoff. `export_sequence` each version:

- Horizontal: `format: "h264"` (or `"mp4"`), `resolution` matching source,
  `quality: "high"`.
- Vertical (from the reframed sequence): same settings, 1080×1920.

Output convention when the user hasn't specified a path: create an `edited/`
folder next to the raw source file(s) and name outputs
`<source-name>-final.mp4` (horizontal) and `<source-name>-vertical.mp4`.
`save_project` before finishing.

### 10. Report back

Tell the user: what got cut (counts by reason — silence/filler/stutter),
anything from `flagged_for_review` you left in and why, what the color
correction changed, and where the exported files landed. Don't just say
"done" — this is footage of them; they should know what was touched.

## Montage pipeline (no-dialogue footage)

1. **Watch every source clip before it touches the timeline** —
   `video_watch` at 1fps minimum. Do not infer content from filenames,
   thumbnails, or earlier folder summaries: a "room only" clip can end with
   the person visible in a mirror (this happened — two bathroom clips were
   clean until the final seconds). While watching, note each clip's best
   3–6s beat and the exact trim points.
2. ffprobe all clips (Pipeline step 2). Create the sequence to match the
   *source* fps — 60fps clips get a 60fps sequence. Sequence settings cannot
   be changed after creation (see MCP bugs), so get this right first.
3. Assemble in **story order per the House Style**: brand shot → wides
   alternating with details → hero view shots → brand shot again.
4. Trim each clip to its noted beat: add the full clip at its slot, razor at
   the keep-boundary, ripple-delete the remainder — passing **both**
   `videoTrackIndices` and `audioTrackIndices`, then `list_sequence_tracks`
   to confirm video and audio track lengths still match. Orphaned audio
   tails silently desync everything after them.
5. Add cross-dissolves at every scene boundary (`add_transition_to_clip`).
6. Music bed per House Style; kill the camera audio.
7. Export vertical-first (1080×1920, 30fps, h264, high quality). Only make a
   horizontal version if asked.

## Known premiere-pro MCP bugs (verified Aug 2026)

- **`trim_clip` silently no-ops** — returns success, changes nothing (with
  or without `duration`). Never use it; razor + ripple-delete instead.
- **`export_frame` ignores `time`** — always returns the first frame of the
  sequence, whatever timecode you ask for. Useless for checking a specific
  moment or grading a mid-sequence clip; pull frames from the *source file*
  with claude-video-vision instead. It also appends its own extension
  (`x.png` → `x.png.png`), so pass an extensionless outputPath.
- **`razor_timeline_at_time` with only `videoTrackIndices` still cuts every
  audio track** — and video-only ripple-deletes leave orphaned audio behind.
  Always pass `audioTrackIndices` explicitly and verify sync afterward.
- **`set_sequence_settings` cannot change fps/size after creation** — create
  a new sequence with the right settings and delete the old one.
- **MCP calls can time out yet still succeed** (`create_sequence` did).
  On a timeout, check `get_project_info`/`list_sequences` before retrying —
  blind retries create duplicates.
- **`export_sequence` can report success and write nothing** — confirmed
  twice (with and without a file extension in `outputPath`); it also echoes
  `format: "ProRes"` while ignoring the requested h264. After any export,
  verify the file exists on disk with ffprobe before reporting it done. If
  no file appears within ~a minute, stop retrying: tell the user the
  sequence is built and saved, and to run File → Export from Premiere's UI
  (their manual export takes seconds and always works).

## Batch runs

For a week's worth of clips, do steps 3–4 (analysis + cut list) for all clips
first — they're independent and don't need Premiere open yet — then do steps
5–9 per clip inside one Premiere project (one bin/sequence per clip is cleaner
than one project per clip). Report on the whole batch at the end, not clip by
clip, so the user gets one summary instead of a stream of updates.

## Mistakes to avoid

- **Don't apply cuts in ascending time order.** Ripple-deleting shifts
  everything after it; ascending order means your second cut's timestamp is
  already wrong by the time you get to it.
- **Don't auto-cut soft fillers.** They're often the personality that makes
  the content feel real, not noise. Flag, don't silently remove.
- **Don't regenerate captions from the pre-cut transcript.** They'll drift out
  of sync with every cut. Always use the `caption_cues` the script already
  re-timed.
- **Don't chase a "perfect" grade by looping `color_correct` indefinitely.**
  Two passes against an exported frame is enough for a natural-correction
  look; more than that is diminishing returns on a single-frame judgment call.
- **Don't reframe vertical footage to horizontal** and call it done — there's
  no real image data on the sides to invent. Flag it instead.
- **Don't assemble clips you haven't watched.** Filenames and folder
  summaries lie; mirrors catch people; the "obvious" opener may be the clip
  the user considers unusable. Watch first, then cut.
- **Don't stitch full-length clips in chronological order and call it an
  edit.** That's an assembly, not a cut — the user will redo it by hand.
  Story order, one 3–6s beat per clip, transitions, music (House Style).
