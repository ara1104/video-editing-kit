# Video Editing Kit for Claude Code

Turn raw phone or camera footage into finished social-media videos with Claude:
clean cuts, captions, color, designed title cards, word-synced stickers and effects,
and vertical exports for Reels and TikTok.

## Install (the easy way)

Open **Claude Code** and paste this message:

> Install the video editing kit from https://github.com/ONIKOSIOLA/video-editing-kit and set it up for me. Follow the "Instructions for Claude" section in its README.

Claude does the rest and tells you whenever it needs you to click something.

## What's inside

| Skill | What it does |
|---|---|
| `setup` | One-time setup. Installs ffmpeg, Node, free offline transcription, and the helper plugins. |
| `edit-video` | The front door. Hand it a clip, and it watches the footage, asks what you want, and picks the right workflow. |
| `premiere-clean-edit` | Cuts pauses and filler words, color-corrects, adds captions, and exports vertical and horizontal versions in **Adobe Premiere Pro** (optional; only if you have Premiere). |
| `talking-head-recut` | Adds designed title cards, lower-thirds, quotes and callouts to talking-to-camera videos. |
| `video-overlays` | Adds word-synced stickers, emojis, logo pops and "viral" effects to a video that's already edited. |
| `hyperframes-quality-gates` | Checks the rendered video frame by frame before calling it done. |

It also installs two free plugins from their official authors:
[HyperFrames](https://github.com/heygen-com/hyperframes), which renders the video, and
[claude-video-vision](https://github.com/jordanrendric/claude-video-vision), which lets Claude watch your footage.

## Using it

Put your clips in a folder, then tell Claude something like:

> Edit this video for Instagram Reels: *(drag the file or folder into the chat)*

Your original files are never changed. Finished videos go into an `edited/` folder next to them.

---

## Instructions for Claude

You are installing this kit for someone who is new to Claude Code. Explain each step in a
sentence, ask before installing software, and keep logs out of the chat.

1. Add this marketplace and install the plugin:
   ```bash
   claude plugin marketplace add ONIKOSIOLA/video-editing-kit
   claude plugin install video-editing-kit@video-editing-kit
   ```
2. Read `skills/setup/SKILL.md` from this repo (after step 1 it's also on disk under
   `~/.claude/plugins/marketplaces/video-editing-kit/`) and follow it end to end in this
   session. It installs the tools and the HyperFrames and claude-video-vision plugins.
3. When setup tells her to restart Claude Code, stop there. Tell her that in the new session
   she should say: **"check my video kit"**.

## Credits

`talking-head-recut` is adapted from [vtake-skills](https://github.com/notedit/vtake-skills)
(MIT) via the HyperFrames project (Apache-2.0); see its `NOTICE.md`.
