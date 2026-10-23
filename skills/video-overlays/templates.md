# Composition skeletons (render-proven on hyperframes 0.8.4)

Build pattern: keep timeline + card markup in `index-template.html` /
`public/cards/*.html`, and generate both files below with a small python script so
revisions stay one-line edits.

Replace `DUR` with clamped media duration, `WxH` with canvas (1080×1920 for
9:16), `COMPID` with a project slug. Stage input as `public/input-video.mp4`:

```bash
ffmpeg -y -i "$SRC" -vf scale=1080:1920 -c:v libx264 -crf 18 -g 30 -keyint_min 30 \
  -pix_fmt yuv420p -movflags +faststart -c:a aac public/input-video.mp4
cp <skill or project woff2 fonts> public/fonts/   # e.g. DM Sans
cp <gsap.min.js> public/vendor/                   # gsap 3.14.x works
```

## public/index.html — parent (NO animation here)

```html
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"/>
<style>
  * { box-sizing: border-box; }
  html,body { margin:0; width:100%; height:100%; overflow:hidden; background:#000;
    font-family:"DM Sans",ui-sans-serif,system-ui,sans-serif; }   /* concrete names, no var() */
  #stage { position:relative; width:100%; height:100%; overflow:hidden; }
  .video-wrapper { position:absolute; left:0; top:0; width:1080px; height:1920px;
    overflow:hidden; z-index:1; }
  .video-wrapper video { width:100%; height:100%; object-fit:cover; }
</style>
</head>
<body>
<div id="stage" data-composition-id="COMPID" data-start="0" data-duration="DUR"
     data-fps="30" data-width="1080" data-height="1920">
  <div class="video-wrapper" id="video-wrap">
    <video id="bg-video" src="input-video.mp4" muted playsinline
           data-start="0" data-duration="DUR" data-track-index="1"></video>
  </div>
  <!-- separate audio track preserves the speaker's voice -->
  <audio id="source-audio" src="input-video.mp4"
         data-start="0" data-duration="DUR" data-track-index="10" data-volume="1"></audio>

  <div class="scene" id="overlays-scene" data-composition-id="overlays"
       data-composition-src="compositions/overlays.html"
       data-start="0" data-duration="DUR" data-track-index="2"
       style="position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:40;"></div>

  <script src="vendor/gsap.min.js"></script>
  <script>
    window.__timelines = window.__timelines || {};
    window.__timelines["COMPID"] = window.gsap.timeline({ paused: true }); // EMPTY on purpose
  </script>
</div>
</body>
</html>
```

## public/compositions/overlays.html — ALL animation lives here

```html
<template>
  <style>
    @font-face { font-family: "DM Sans";
      src: url(data:font/woff2;base64,<BASE64 OF THE WOFF2>) format("woff2");
      font-weight: 100 1000; font-display: block; }
    #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; }
    #root .card-host { position: absolute; pointer-events: none; overflow: hidden; }
    #root .card-host .card { position: relative; width: 100%; height: 100%; overflow: hidden; }
    /* per-card styles scoped as .card[data-card-id="..."] ... ; elements that will
       animate start at opacity:0 in CSS; NEVER give them a CSS transform */
  </style>
  <div id="root" data-composition-id="overlays" data-width="1080" data-height="1920">

    <div class="card-host clip" data-card-id="card-globe" data-start="3.3667"
         data-duration="1.5667" data-track-index="2"
         style="left:0;top:0;width:1080px;height:1920px;visibility:hidden;opacity:0;">
      <div class="card" data-card-id="card-globe"><!-- card markup --></div>
    </div>
    <!-- one host per overlay moment; data-start/duration = its window -->

  </div>
  <script src="vendor/gsap.min.js"></script>   <!-- INSIDE template: cloned+executed -->
  <script>
    (function () {
      var tl = window.gsap.timeline({ paused: true });

      // static transforms via gsap.set so later tweens compose with them
      window.gsap.set('#cp-1', { rotation: -2 });

      // EVERY call fully literal: literal selector, literal vars, literal time.
      // No helpers, no loops, no concatenation — static analysis must resolve all.
      tl.set('.card-host[data-card-id="card-globe"]', { visibility:'visible', opacity:1 }, 3.3667);
      tl.fromTo('#cg-globe', { opacity:0, scale:0.3 },
        { opacity:1, scale:1, duration:0.4333, ease:'back.out(1.8)' }, 3.3667);
      tl.to('#cg-globe', { opacity:0, scale:0.55, duration:0.2667, ease:'power2.in' }, 4.6333);
      tl.set('.card-host[data-card-id="card-globe"]', { visibility:'hidden' }, 4.9333);
      // hard-kill after any exit that ends at a clip boundary:
      //   tl.set('#el', { opacity: 0 }, boundaryTime);

      // draw-path: precompute length numerically, hardcode it
      //   window.gsap.set('#path1', { strokeDasharray: 485, strokeDashoffset: 485 });
      //   tl.to('#path1', { strokeDashoffset: 0, duration: 0.5 }, 10.4333);

      // punch-ins target the PARENT's #video-wrap — works from here
      //   window.gsap.set('#video-wrap', { transformOrigin: '50% 32%' });
      //   tl.to('#video-wrap', { scale: 1.07, duration: 0.2 }, 17.0333);

      window.__timelines = window.__timelines || {};
      window.__timelines['overlays'] = tl;
    })();
  </script>
</template>
```

Quantize times to 1/fps (30fps → multiples of 0.0333, 4 decimals fine).

Path length precompute (quadratic bezier):

```python
import math
def qlen(p0,p1,p2,n=2000):
    L=0; px,py=p0
    for i in range(1,n+1):
        t=i/n
        x=(1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t**2*p2[0]
        y=(1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t**2*p2[1]
        L+=math.hypot(x-px,y-py); px,py=x,y
    return L
```

Render:

```bash
find . -name '._*' -delete
PRODUCER_BROWSER_GPU_MODE=hardware npx hyperframes render public -o output.mp4 --fps 30
```
