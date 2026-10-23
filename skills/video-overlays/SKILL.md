---
name: video-overlays
description: Use when the user has an already-edited or recorded video (talking-head, vlog, reel, promo) and wants motion-graphic elements added that match what's being said — "add a globe when I say world", word-synced stickers, location chips, logo pops, store badges, text stamps — or asks to make an existing video punchier/more viral with animated overlays while keeping the footage untouched.
---

# Video Overlays (word-synced motion elements)

## Overview

Layer word-synced animated graphics over an existing video without changing the
footage: transcribe → map what's already on screen → design overlay moments on
exact word timestamps → build a HyperFrames composition using the ONE
architecture that actually renders → verify pixels in the rendered MP4.

**Core principle: snapshots and previews lie; only frames extracted from the
rendered MP4 prove the overlays exist.** The default root-timeline composition
pattern (including the one in `talking-head-recut`'s own template) renders
opacity but SILENTLY DROPS all transform tweens (x / scale / rotation) on
hyperframes ≥0.8.x. Overlays that pop, slide, or spin will look perfect in
`snapshot` and vanish in `render` unless you use the sub-composition
architecture below.

## When to Use

- "Add elements that match what I'm saying" / "add a globe when I say world"
- "Make this video I edited more viral / dynamic / animated"
- Sticker chips, brand lockups, store badges, kinetic stamps over real footage
- NOT plain subtitles (→ `embedded-captions`), NOT building a video from
  scratch (→ `/hyperframes` intent layer), NOT cutting/retiming footage
  (→ `/general-video`)

## Reference recipes

- `effects.md` — render-verified shader looks (glow, dissolve, mask reveal, sheen).
- `reel-effects-17.md` — build recipes for 17 talking-head effects (orbit, couch wall, paper
  cut, vertigo, cover story, glass type…) on a shared matte+sandwich primitive. For any "add
  effect X to my video" ask, start from the matching recipe and the shared primitives there.

## Workflow

1. **Watch the video first** (`video-perception` skill: `video_info`,
   `video_watch`, then `video_detail`/ffmpeg `-ss` probes). Map with
   timestamps: burned-in caption zone, existing panels/inserts, transitions
   (whip-pans), end cards, where the speaker's face and hands travel. Overlays
   must dodge all of it; never cover an existing end card.
2. **Transcribe word-level.** Work dir `videos/<name>/` (needs Node 22+):
   `ffprobe` metadata → `ffmpeg -vn` audio.mp3 →
   `npx hyperframes transcribe audio.mp3 -d . --json --model small.en`
   → flat word array with start/end. Clamp everything to media duration.
3. **Design 4–7 overlay moments** keyed to exact word starts. One dominant
   element at a time. Pull palette/typography from the video's own end card or
   the project's brand so overlays feel native. Apple emoji (flags ✈️ ⚜️ )
   render fine in headless renders on macOS — use them over hand-drawn SVG
   flags. Never put unverifiable claims (user counts, stats) on screen.
   Nice-to-haves: quick punch-in zooms (scale on the video wrapper) on the
   brand name and CTA words; re-bump an element when the speaker repeats the line.
   For shader-style looks — glow pulses, noise dissolves, mask reveals,
   iridescent/shimmer text, sheen sweeps, liquid wipes — use the
   render-verified recipes in `effects.md` (this skill directory); they list
   which GSAP properties are proven to animate in renders and the per-recipe
   traps (sheen needs `overflow:hidden` on the card itself; clip-path morphs
   need equal vertex counts; one SVG filter id per dissolving element).
4. **Build with the sub-composition architecture** — read `templates.md` in
   this skill directory and copy its two skeletons exactly:
   - `public/index.html`: video wrapper + separate `<audio>` (same src, keeps
     voice), an EMPTY root timeline keyed to the stage's composition id, and a
     scene mount `data-composition-src="compositions/overlays.html"`.
   - `public/compositions/overlays.html`: ONE `<template>` containing style
     (with base64 @font-face), `#root` with `data-composition-id` +
     `data-width`/`data-height`, the timed `.clip` card hosts, **and BOTH
     `<script>` tags (gsap loader + timeline) INSIDE the `<template>`** —
     scripts after `</template>` are never executed (silent total failure).
   - Re-encode the source with dense keyframes
     (`-g <fps> -keyint_min <fps>`, scale to canvas) or seeks freeze.
   - Keep an `index-template.html` + small regen script so revisions are edits,
     not rebuilds.
5. **Verify — every gate, in order** (load `hyperframes-quality-gates`):
   1. `npx hyperframes check public` → 0 errors (fix `gsap_exit_missing_hard_kill`
      by adding `tl.set(..., {opacity:0}, t)` after exits).
   2. `npx hyperframes keyframes public --runtime gsap --json` → zero
      `__unresolved__` targets. Any unresolved = a helper function, loop, or
      concatenated selector; unroll to literal calls.
   3. `snapshot` at every overlay moment; READ the contact sheet.
   4. Short test render first (sed the stage/video/audio/scene `data-duration`
      down to ~5s), extract frames with ffmpeg, LOOK. Then full render.
   5. From the final MP4: extract a frame per overlay moment + the end card,
      LOOK at all of them, and `ffprobe` the audio stream exists.
6. **Deliver** the MP4; keep the work dir for revisions.

## Trap Table (each one cost real debugging time)

| Trap | Symptom | Fix |
|---|---|---|
| Timeline in root index.html | snapshot fine; render shows opacity fades but no pops/slides/spins | All animation lives in a sub-composition |
| `<script>` outside `</template>` in sub-comp | Nothing animates anywhere, even snapshots | Scripts go INSIDE the template |
| Helper fns / loops / string-built selectors in timeline | `keyframes --json` shows `__unresolved__`; render ignores those tweens | Fully literal `tl.to('#id', {...}, 1.2333)` calls only |
| `getTotalLength()` for draw-path | Unresolvable at static-analysis time | Precompute path length (numeric bezier sampling) and hardcode `strokeDasharray` |
| CSS `transform:` on a GSAP-animated element | Offset clobbered on first tween | Position with left/top; transforms belong to GSAP (`gsap.set` for static rotation) |
| Sub-comp missing own `@font-face` | `font_family_without_font_face` lint error | Base64-embed the woff2 in the template's style |
| Sub-comp .html at public root | `multiple_root_compositions` error | Put it in `compositions/` |
| id starting with a digit | SyntaxError silently kills timeline | Letter-prefixed ids |
| `._*` AppleDouble files (external volumes) | Broken builds/renders | `find . -name '._*' -delete` before check/render |
| Scene mount without an `id` attribute | Snapshot + keyframes fine; render silently drops EVERY sub-comp overlay composited over video. Elements timed after the video track ends still render — which misdirects the diagnosis toward the timeline | The parent's `<div class="scene" ...>` MUST carry `id="overlays-scene"` exactly as in templates.md. Cost a 10-render bisect |
| `npx hyperframes` version drift mid-project | Same composition renders differently between runs; bisects lie because each render may resolve a different version | Read the version from `keyframes --json` `_meta`; pin `npx hyperframes@<ver>` for all renders in a session |
| Element gated only by `visibility` (no `opacity:0` default) | Snapshot correct; RENDER shows it from frame 0 — a full-bleed card covers the whole video | Every timed element starts at `opacity:0` in CSS/inline; host sets are `{visibility:'visible', opacity:1}` / `{visibility:'hidden', opacity:0}`. The render's static analysis honors opacity, not visibility |
| Re-extracting frames after a failed render | You review stale frames from the previous MP4 and think it passed | Render to a NEW filename, or delete the old MP4 first; never let ffmpeg silently read the previous file |
| hyperframes ≥0.8.30: `tl.set(host,{visibility:...})` | `gsap_animates_clip_element` lint error on every `.card-host.clip` | Gate hosts by opacity only: inline `opacity:0`, `tl.set(host,{opacity:1})` / `{opacity:0}`; the framework owns clip visibility. |
| iPhone/HLG footage (`arib-std-b67`) re-encoded without SDR conversion | Render log `hasHdrContent:true`; transparent webm alpha dropped, colors washed, renders ~4x slower | Convert with `colorspace=all=bt709:iall=bt2020` + bt709 tags first (details in `reel-effects-17.md`) |
| `window.gsap.set(wrapper,{transformOrigin})` at authoring time | Last effect's origin wins globally; video and cut-out speaker scale about different points → ghost double | `tl.set(wrapper,{transformOrigin},t0)` on the timeline per effect |
| Trusting snapshots as final proof | Shipped MP4 missing overlays | Extract and view frames from the rendered MP4 |

## Red Flags — STOP

- "Check passed, so it rendered correctly" → check doesn't see dropped tweens. Extract MP4 frames.
- "Snapshot showed it, skip the test render" → snapshot uses the live page; render uses static analysis. Test render.
- "I'll write the timeline with a loop to save tokens" → that's the `__unresolved__` trap.
- "Snapshot and render disagree, so the render is broken" → usually YOUR bug: an element
  visible in the render but not the snapshot is missing its `opacity:0` default; an element
  visible in snapshot but not render over video = missing scene-mount `id`.
- "I'll write the parent from memory, it's simple" → copy templates.md verbatim. Two of its
  attributes (scene `id`, host `opacity:0`) look cosmetic and are load-bearing.
- Full render is slow (~0.5s/frame at 1080x1920). To test a gating/architecture fix
  cheaply, cap every `data-duration` to ~4s and render that first — but remember any
  element whose `data-start` is past the cap simply won't appear, which is itself the
  proof that gating works.
- "The talking-head-recut template is canonical, use it as-is" → its root-timeline pattern is the exact broken path.
