---
name: setup
description: One-time setup for the video editing kit. Installs and checks everything the video skills need (ffmpeg, Node, local Whisper, the HyperFrames and claude-video-vision plugins, and optionally the Adobe Premiere Pro bridge). Use right after installing this plugin, when the user says "set up my video kit" or "get me ready to edit videos", or whenever a video skill fails because a tool is missing.
---

# Video Editing Kit — Setup

The person you're helping is new to Claude Code. Explain each step in one plain
sentence before you run it, ask before installing anything, and never paste
long logs at them — summarize what worked and what didn't.

Work through the checklist in order. Skip anything that's already installed.
At the end, give a short status list (installed / skipped / needs her action).

## 1. Detect the machine

```bash
uname -s; sw_vers 2>/dev/null; node -v 2>/dev/null; ffmpeg -version 2>/dev/null | head -1; brew -v 2>/dev/null | head -1
```

These instructions assume macOS (the common case). On Windows, use `winget`
equivalents (`winget install Gyan.FFmpeg`, `winget install OpenJS.NodeJS.LTS`)
and skip Homebrew. Linux: use the system package manager.

## 2. Base tools

| Tool | Why | macOS install |
|---|---|---|
| Homebrew | Installs everything else | Installing Homebrew needs her password, so she has to run its official one-line installer from https://brew.sh in her own Terminal. Give her the command and wait. |
| Node.js 22+ | Runs HyperFrames and the video MCP | `brew install node` |
| ffmpeg | Reads, cuts and re-encodes video | `brew install ffmpeg` |
| whisper-cpp | Free, offline transcription (captions) | `brew install whisper-cpp` |

If `node -v` is below 22, upgrade it: `brew upgrade node`.

## 3. Plugins

Install these from their official sources, so they stay updated by their authors:

```bash
# HyperFrames (HeyGen): renders videos from HTML. Powers talking-head-recut and
# video-overlays, plus its own captions, footage-editing and motion-graphics workflows.
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes

# claude-video-vision: lets Claude watch videos (frames + transcript).
claude plugin marketplace add jordanrendric/claude-video-vision
claude plugin install claude-video-vision@claude-video-vision
```

Then set claude-video-vision to the free local backend, so it never needs an
API key. If `~/.claude-video-vision/config.json` doesn't exist yet, create it:

```json
{ "backend": "local", "whisper_engine": "cpp", "whisper_model": "auto" }
```

If it already exists, change only those three keys.

The first transcription downloads a Whisper model (a few hundred MB). That's
expected.

## 4. Adobe Premiere Pro (optional)

Only if she has Premiere Pro installed (check `/Applications` for
"Adobe Premiere Pro*"). Without it, skip this. The kit still works through
HyperFrames, and `edit-video` routes around Premiere.

```bash
npm install -g adobe-premiere-pro-mcp
premiere-pro-mcp --install-cep
premiere-pro-mcp --doctor
claude mcp add premiere-pro --scope user -e PREMIERE_MCP_TOOLSET=full -- premiere-pro-mcp
```

Then she has to do this part by hand. Tell her clearly:
1. Quit and reopen Premiere Pro.
2. Menu: **Window → Extensions → MCP Bridge (CEP)**.
3. In the panel, set the bridge folder the installer printed, then click **Start**.

Premiere has to be open, with that panel started, every time she edits with it.

## 5. Restart and verify

New plugins and MCP servers load only in a new session. Tell her:
"Close this Claude Code session and open a new one, then say *check my video kit*."

In the new session, verify:
- `npx hyperframes doctor` passes (ffmpeg, headless browser).
- The `video_info` tool from claude-video-vision exists. Run it on any short
  video she has to confirm it works.
- If Premiere is set up: run the premiere-pro `verify_premiere_connection` tool
  (read-only).

## 6. Hand-off

Finish with a short, friendly message:
- what's ready;
- how to use it: "Put your raw clips in a folder, then tell me *edit this video
  for Instagram: <drag the file or folder in>*";
- anything left for her to do.
