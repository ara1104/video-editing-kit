---
name: hyperframes-quality-gates
description: Use when building, editing, retiming, or rendering HyperFrames compositions or frame sub-compositions — especially multi-frame promo/launch videos, when a frame "passed checks" but hasn't been looked at, when retiming GSAP tweens, or when output quality feels below a previous run. Also use when debugging blank frames, dead-air gaps, buried/overlapping cards, or timelines that never register.
---

# HyperFrames Quality Gates

## Overview

The gap between a great HyperFrames run and a mediocre one is not creativity — it is **verification discipline**. Great runs treat every frame as unproven until its pixels have been looked at, at multiple seek times. Mediocre runs trust the checker and ship the first thing that lints clean.

**Core principle: the linter checks rects and attributes; only rendered pixels tell the truth. Never declare a frame done without seeing it.**

## Non-negotiable gates

Work through these IN ORDER for every frame you build or edit. Skipping a gate because "it's a small change" is how quality drops.

1. **Read the storyboard's own `## Video direction` block and obey it over preset boilerplate.** When the storyboard says sentence case and the preset's frame.md says uppercase, the storyboard wins. Project direction > preset defaults.
2. **One dominant move per frame.** If your frame has two elements resolving at once, cut one. Front-loading everything then freezing ("slideshow mode") and everything-floating ("screensaver mode") are both failures.
3. **Self-check the mechanical traps** (table below) by grepping your own file before calling it done.
4. **Seek-test in a browser before reporting done.** Clone the `<template>`, register the timeline, and `timeline.seek(t, false)` at: t=0, each scene boundary ±0.05s, and the final frame. Screenshot each. LOOK at them. A frame report without a seek-test is an unverified claim.
   - `suppressEvents` trap: bare `.seek(t)` suppresses `onUpdate` callbacks — counters/typing look broken in your harness but fine in the renderer. Always pass `false`.
5. **After ANY retime, re-derive `data-start`/`data-duration` on the affected clips.** GSAP tween times and clip visibility windows are two separate systems; retiming one without the other creates invisible elements or dead-air gaps. This is the #1 regression source.
6. **After assembly, snapshot the full video at every cut boundary and each frame's midpoint, and read the contact sheet image yourself.** Fix what looks wrong, re-snapshot, only then render.

## Mechanical trap table (grep these in your own file)

| Trap | Symptom | Fix |
|---|---|---|
| id starts with digit + `querySelector("#...")` | SyntaxError silently kills timeline registration → blank frame | Prefix ids with a letter, or `getElementById` first |
| CSS `transform:` on a GSAP-animated element | GSAP clobbers the CSS offset on first tween | Bake offset into `left/top`; transforms belong to GSAP only |
| Missing `box-sizing: border-box` on padded cards | Widths inflate, centering drifts, cards collide | Set it on every padded card |
| `@font-face` pointing at fonts.gstatic.com / any CDN | Non-deterministic render; breaks offline | Local files under `assets/fonts/`, project-root-relative |
| Overlap math by eye | Later cards bury earlier cards' text | Compute rects with `getBoundingClientRect()` at the hold time; verify key text of EVERY stacked element is visible in a screenshot |
| Checker overlap findings on clipped/tight-leading text | False positive (rects overlap, glyphs don't) | Verify pixels first, then `data-layout-allow-overlap` — never blind-suppress |
| Screenshot stretched/recolored in phone mockup | Uncanny device | Native aspect ratio always; crop with `overflow:hidden`, never scale non-uniformly |
| `._*` AppleDouble files on external volumes | Breaks builds/renders | `find . -name '._*' -delete` before assemble/render |
| Node < 22 | CLI fails | Prefix: `export PATH="$HOME/.nvm/versions/node/v22*/bin:$PATH"` (or nvm use 22) |

## Orchestration pattern (multi-frame builds)

- One worker per frame, one file per worker; workers never touch shared files.
- Stage shared assets (fonts, logos, screenshots) BEFORE dispatching workers; packets name exact paths.
- Every packet carries: the frame's storyboard block verbatim, the global Video direction block, the trap table above, and the seek-test requirement.
- Orchestrator re-runs lint + check + contact-sheet inspection after assembly regardless of what workers reported — worker self-reports are claims, not proof.

## Red flags — stop and verify

- "Lint and check passed, so the frame is correct" → checks don't see buried text or dead air. Look at pixels.
- "I retimed the tweens; done" → did you retime the clip `data-*` windows too?
- "I'll skip the seek-test, the code is straightforward" → the blank-frame bug (digit-id selector) was in straightforward code and only a seek-test caught it.
- "The card probably doesn't cover the other one" → compute the rects; then screenshot.
- "CDN font is fine just this once" → it isn't; renders must be network-free.

**All of these mean: run the gate you were about to skip.**
