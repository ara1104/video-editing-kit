# 17 talking-head reel effects (studied from a public Instagram reel)

Source: @tenfoldmarc "17 video effects Claude can create" (27s, 1080x1920/30fps, 0 hard cuts).
Format of the reel itself: handheld talking head + a phone mockup showing one ~1s sample per
effect, numbered `NN/17` in a pill, sidebar list with the current effect highlighted yellow.
Order (from the VO): orbit, couch wall, UI world, frame break, digital zoom, phone mockup,
checklist, headline wall, zoom-through cut, chart grow, pull-back reveal, green screen, paper
cut, doodle boil, vertigo, cover story, glass type.

STATUS: the 3 effects below were render-verified (cover story, paper cut, vertigo). The
other 14 are build plans from watching the reel; test-render before promising one.
Matte trap: burned-in captions + dark backlit clothes punch holes in the u2net mask (white
blotches on sticker/outline effects) — fix with a morphological close on the alpha.
Known limits: vertigo keeps a faint seam at the head on big scales (needs an inpainted plate);
glass type reads as frosted white and is subtle on bright skies.

First test — 3 of 17 on a 6s porch clip:
- **16 Cover story — VERIFIED.** Masthead sits behind the speaker's head, front chrome on top.
- **13 Paper cut — VERIFIED (partial look).** Sticker border, grid paper, torn yellow tape, scribbles
  draw on, ransom letters stamp + red circle all render. Missing vs reel: torn/wobbly sticker edge
  (displacement on the subject wrapper would warp the face; needs a separate outline layer), and
  the matte can leak bits of background objects at the sticker's edge.
- **15 Vertigo — PARTIAL.** Bg-only scale works (background grows, speaker holds size). The hole the
  matte leaves grows with the scale, leaving a faint glass-edge arc around the head. At 1.16x it is
  subtle; at 1.3x obvious; blurring the fill made it worse. Real fix = inpainted clean plate.

### Traps found by the test (each cost a render)

| Trap | Symptom | Fix |
|---|---|---|
| **iPhone footage is HLG/BT2020** (`ffprobe color_transfer=arib-std-b67`) | Re-encoding keeps the tag → render log `hasHdrContent:true`, `capture_hdr_layered`; transparent webm **loses its alpha** (matte renders as a full opaque frame, everything "behind" is hidden), washed colors, 3m11s render | Cut the clip with `-vf "colorspace=all=bt709:iall=bt2020:fast=1,format=yuv420p" -color_primaries bt709 -color_trc bt709 -colorspace bt709` BEFORE `remove-background`; confirm `hasHdrContent:false`. Render dropped to 44s. |
| Behind-subject text invisible | "Cover story" masthead missing in the first render | Same HDR cause (opaque subject layer), not a layering bug |
| `check` layout errors on intentional layering | `text_occluded` / `text_box_overflow` | Add `data-layout-allow-occlusion` (and `-overflow`) on the behind text; a 4-letter Playfair 900 word is ~4.6x font-size wide, so size it to fit |
| Two sub-comps | duplicate `#root` ids | Give each comp its own root id (`rootB`, `rootF`) and scene mount id `<comp>-scene` |
| Stale transcode cache | old footage reused after re-encode | Move `public/.transcode-cache` and `public/.hyperframes` aside before re-rendering |

### Verified sandwich skeleton (hyperframes 0.8.162)

Parent: `video-wrap`(clip.mp4, z1) < `plate-wrap`(bgplate.webm, z2, opacity 0) < `behind-scene`
(sub-comp, z10) < `subject-wrap`(subject.webm, z20) < `front-scene`(sub-comp, z40). All three videos
`data-start=0 data-media-start=0`, wrappers have NO data-* attrs and are tweened from the front
comp's timeline (`#subject-wrap` scale/filter, `#plate-wrap` scale). Sticker = chained
`drop-shadow(±3px 0 0 #fff)` list on `#subject-wrap` (verified in render). Matte: `npx
hyperframes@0.8.162 remove-background clip.mp4 -o subject.webm -b bgplate.webm` ≈ 60s for 6s
on CoreML (u2net_human_seg, 168 MB download first run), clean edges on a hand-held mic shot.
Burned-in captions in the source stay in the pixels and sit on top of every layer; use a
caption-free source for real work.

## Shared primitives (almost every effect is one of these)

| Primitive | How |
|---|---|
| **Subject matte** | `npx hyperframes remove-background` (check `--help` for flags) → alpha video of the speaker. Unlocks 8 of 17 effects. Run once per clip, reuse. |
| **Sandwich** | z0 original video → z1 "behind" graphics → z2 matte video (same src, same start, dense keyframes `-g 30 -keyint_min 30`) → z3 front graphics + captions. Text/cards "behind the person" = z1. |
| **Literal tweens only** | No loops/helpers in the timeline (`__unresolved__` trap). For effects with many items (orbit, walls, scribbles) write a small Python generator that emits the literal `tl.fromTo(...)` lines . |
| **Word-synced** | Cue everything on `npx hyperframes transcribe` word starts: caption words, checklist ticks, wall cards. |
| **Caption system** | Bold grotesque (Inter/Poppins ExtraBold) lower-third, word-by-word pop, key word in yellow `#E8F26B`; serif italic + script for "aesthetic" beats; letter-spaced small caps for the wide shot. |
| **Wobble ("boil")** | `feTurbulence` + `feDisplacementMap`, animate `baseFrequency`/`seed` in 3–4 discrete steps per second (`ease:'steps(1)'`), never smooth. Gives hand-drawn jitter. |
| **Blur-in** | tween `filter:'blur(14px)'`→`'blur(0px)'` (same function list) + opacity; verified property in effects.md. |

## The 17

1. **Orbit** — Observed: small phone/screenshot cards circle the speaker in a tilted ellipse, passing
   behind and in front of him; gold script caption ("cool girl") with sparkles. Build: matte
   sandwich; ellipse math in the generator, cards split into back ring (z1) and front ring (z3) —
   swap a card's layer when sin θ changes sign (two copies, crossfade at the crossing). Scale
   0.7→1.1 and opacity 0.6→1 with depth.
2. **Couch wall** — Observed: dense grid of tweet/video-thumb tiles (view counts visible) fills the
   wall behind him, each blurring in; huge bold "selling a course" blur-in at lower third.
   Build: z1 tiles masked to the wall area, staggered `blur→0, scale .85→1`, 60–80 ms apart.
3. **UI world** — Observed: frame splits — top half becomes a Claude-style app (drop zone, thumbnails
   fly in, "RAW CLIPS" yellow highlighter tag, typed `/video-`, send button lights); speaker stays in
   bottom half; caption words "DROP CLIPS", "TRIGGER THE…". Build: HTML mock UI (own design, not
   Anthropic's logo/branding — reel is theirs, ours must be our own mock), typewriter by clip-path
   on a monospace span, thumbnails `y:-120→0`.
4. **Frame break** — Observed: full-bleed video shrinks into a rounded card on a dark vignette inside
   a social-post UI (like/comment icons, @handle, Follow); hands/head poke OUT past the card edge.
   Build: card = `overflow:hidden` clone; the matte clone sits OUTSIDE the card, scaled in sync;
   only hands/head layer escapes. Vignette = radial-gradient.
5. **Digital zoom** — Observed: slow punch-in on the face + bold word-by-word captions
   ("video" white, "editing" yellow). Build: scale on video wrapper 1→1.18 `power2.inOut`, hit a
   second 1.18→1.3 on the emphasis word (punch-ins, not a crawl).
6. **Phone mockup** — Observed: speaker big and foreground; an iPhone with a chat UI ("Ads Assistant…
   Pause Ad 3, move the budget to Ad 1", Approve button) floats behind his shoulder, slides in with a
   slight tilt. Build: z1 phone (CSS bezel + rounded screen), `x:+200→0, rotation:6→-4`.
7. **Checklist** — Observed: dark translucent card above his head, "ALL YOU NEED TO DO · 0 of 3";
   rows check off exactly as he says them ("Drop your clips", "Trigger the skill"), progress bar
   fills. Build: row i checks on its word timestamp (circle→green check by stroke draw), counter
   text swapped via two stacked spans fading.
8. **Headline wall** — Observed: newspaper-style clippings and social cards ("Claude can edit your
   videos now") stick to the wall behind him in staggered pops, slightly rotated, overlapping.
   Build: generator with seeded random rotation ±5°, `scale .6→1 back.out(1.7)`, 70 ms stagger,
   z1 (behind matte) so his head overlaps the clippings.
9. **Zoom-through cut** — Observed: shot A zooms hard into a blur (radial streak), lands on shot B,
   which settles from blurred+oversized; serif-italic "cool girl aesthetic" caption then letter-spaced
   small caps. Build: A `scale 1→3.2` + blur ramp, hard cut at peak, B `scale 1.5→1`, blur 18→0.
   True radial blur: pre-render the transition with ffmpeg (`zoompan` + `gblur`/`rgbashift`) or stack 4
   scaled copies at 25% opacity. Add a whoosh SFX on the cut.
10. **Chart grow** — Observed: dark grade, weekday axis M T W T F S S, glowing yellow line climbs
    point by point with dashed drop-lines, node dots, "SCALE ↗" chip; his hand sweeps along it.
    Build: SVG polyline with hard-coded `strokeDasharray` length (no `getTotalLength()`), glow via
    `drop-shadow` filter string tween, dots pop on each x tick. Darken base video 25% first.
11. **Pull-back reveal** — Observed: the shot is actually inside an editor window (file tab
    `test-slot.mp4`, "Assistant" panel, rendering timeline with moving playhead, "Working on edit"
    steps tick: Transcribed, Picked the take, Cut 3 shots, Captions added, Rendered). Camera pulls
    back to reveal the app. Build: video wrapper `scale 1→0.55` while editor chrome fades in around it;
    step ticks on timed cues; playhead = linear x tween.
12. **Green screen** — Observed: speaker keyed over a full UI (purple header, focus timer
    `49:57 Write the sales page`, task rows, text "you need edits" with "edits" highlighted); text sits
    behind his chest. Build: matte over HTML UI; countdown digits swapped by stepped opacity; cursor
    glyph moves on a short path.
13. **Paper cut** — Observed: collage on grid paper: speaker as a die-cut sticker with a thick torn
    white border, torn yellow paper strips, blue/pink scribble hatching, × and spiral doodles,
    ransom-note letters spelling "1 0 0 %" that stamp in one by one then get circled in red.
    Build: sticker border = 4 stacked `drop-shadow(0 0 0 #fff)` + displacement for torn edge; paper
    = `feTurbulence` texture; scribbles = SVG paths drawn on with dashoffset, wobbled at 8 fps;
    ransom letters = spans with mixed fonts/backgrounds/±8° rotations, `scale 1.8→1` stamp ease.
14. **Doodle boil** — Observed: white chalky outline traced around his whole body that jitters like
    hand-drawn animation; doodles (clapperboard, heart, empty rectangle) drift and recolor pink/yellow.
    Build: outline from the matte (alpha → dilate → subtract) or the stacked drop-shadow trick, with
    stepped-seed displacement at ~10 fps; doodles are SVG strokes drawn on, color-stepped.
15. **Vertigo (dolly zoom)** — Observed: background visibly stretches/shrinks while he stays the same
    size; bold captions ("SUCK AT DESIGN", DESIGN in yellow). Build with matte: scale ONLY the bg
    layer 1→1.35 while the subject layer holds scale — the Hitchcock look from flat footage.
16. **Cover story** — Observed: giant high-contrast serif masthead "EDIT" in the top third with his
    head overlapping the letters, thin border frame like a magazine cover. Build: z1 text (Playfair
    Display / Didot-style 900, letter-spacing), matte in front, 1px inner border, optional small
    cover-lines at edges.
17. **Glass type** — Observed: huge frosted-glass 3D "DESIGN" behind him with ghost/refraction layers
    and an extruded edge. Build (UNVERIFIED — test `backdrop-filter` in headless render first): 8–12
    stacked copies offset 2px for extrusion, white→transparent gradient fill via
    `background-clip:text`, 1px white `-webkit-text-stroke`, blurred duplicate underneath as caustic.
    Fallback if backdrop-filter fails in render: pre-render the type in a Three.js/R3F scene.

## Reel-level craft worth stealing

- **Index UI as retention device**: persistent list of all 17 names with the current one lit, plus
  `NN/17` counter. Viewers wait for #14 ("my favorite") — that's the comment bait.
- **Hook by number + capability** ("17 video effects X can create"), then show, don't explain.
- **Each sample = 1 second.** Dense, no breathing room; every effect has its own palette so each
  reads as a distinct style, not variations.
- **CTA = comment keyword** ("Comment STUDIO") to drive comments and DMs.
