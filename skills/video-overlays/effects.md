# Effect recipes (render-verified, hyperframes 0.8.6, headless Chromium, 2026-08-21)

Shader-style looks for overlay cards/stamps, all pure CSS/SVG + GSAP — every
recipe below was verified by extracting mid-animation frames from a rendered
MP4, not just snapshots. Tween lines are literal; copy and retime.

**Properties verified to animate in renders:** `opacity`, `x/y/scale/rotation`
(sub-comp only), `filter` (string→string), `attr:{}` on SVG filter params,
`webkitMaskSize`, `backgroundPosition`, `clipPath` (equal vertex count).

## 1. Glow pulse — two ways

CSS filter string tween (soft bloom around any element, text included):
```js
tl.fromTo('#pill', { filter: 'drop-shadow(0px 0px 0px rgba(229,197,88,0))' },
  { filter: 'drop-shadow(0px 0px 55px rgba(229,197,88,1))', duration: 0.8, ease: 'power2.inOut' }, 1.0);
tl.to('#pill', { filter: 'drop-shadow(0px 0px 8px rgba(229,197,88,0.4))', duration: 0.6 }, 1.9);
```
Both endpoints must be the SAME filter function list (GSAP interpolates the
string). Halo-layer variant (cheaper, tintable): duplicate the element's
shape behind it with `background:<accent>; filter:blur(45px)`, tween only
its `opacity`/`scale`.

## 2. Dissolve — SVG displacement

Noise-eaten edges materializing into a clean card. Hidden SVG in `#root`:
```html
<svg width="0" height="0" style="position:absolute">
  <filter id="dispFx" x="-30%" y="-30%" width="160%" height="160%">
    <feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="3" result="n"/>
    <feDisplacementMap id="dispMap" in="SourceGraphic" in2="n" scale="0"
      xChannelSelector="R" yChannelSelector="G"/>
  </filter>
</svg>
```
Card gets `filter:url(#dispFx)`. Animate the filter PARAM, not the card:
```js
tl.fromTo('#dispMap', { attr: { scale: 220 } }, { attr: { scale: 0 }, duration: 1.2, ease: 'power2.out' }, 2.4);
tl.fromTo('#diss-card', { opacity: 0 }, { opacity: 1, duration: 0.5 }, 2.4);
```
One filter id per dissolving element (shared filters animate together).

## 3. Mask reveal — radial grow

```css
#card { -webkit-mask-image: radial-gradient(circle at 50% 50%, #000 0 40%, transparent 60%);
  mask-image: radial-gradient(circle at 50% 50%, #000 0 40%, transparent 60%);
  -webkit-mask-size: 30% 30%; mask-size: 30% 30%;
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
  -webkit-mask-position: center; mask-position: center; }
```
```js
tl.fromTo('#card', { webkitMaskSize: '30% 30%' }, { webkitMaskSize: '400% 400%', duration: 1.4, ease: 'power2.inOut' }, 2.6);
```
Declare both prefixed and standard in CSS; tween the `webkitMaskSize` form
(verified to apply in headless Chromium).

## 4. Iridescent gradient sweep (shimmer text)

```css
#txt { background: linear-gradient(100deg,#E5C558,#F6EFE3 20%,#63C7B2 40%,#E5C558 60%,#F6EFE3 80%,#E5C558);
  background-size: 300% 100%; -webkit-background-clip: text; background-clip: text; color: transparent; }
```
```js
tl.fromTo('#txt', { backgroundPosition: '0% 50%' }, { backgroundPosition: '200% 50%', duration: 1.8, ease: 'none' }, 4.6);
```

## 5. Sheen / light sweep across a card

Diagonal white gradient strip inside the card, tween `x` across.
**TRAP (seen in render): the card itself needs `overflow:hidden`** — the
host's `overflow:hidden` does NOT clip the strip if the card is the
positioning parent; without it the strip escapes and floats over the video.
```css
#card { overflow:hidden; }
#strip { position:absolute; left:-260px; top:0; width:220px; height:100%;
  background:linear-gradient(75deg,transparent,rgba(255,255,255,.85) 50%,transparent); }
```
```js
tl.fromTo('#strip', { x: 0 }, { x: 1140, duration: 0.9, ease: 'power1.inOut' }, 5.0);
```

## 6. Liquid wipe — clip-path polygon morph

Wavy edge sweeping to reveal. Both polygons MUST have the same vertex count:
```js
tl.set('#card', { opacity: 1, clipPath: 'polygon(0% 100%, 12% 96%, 30% 100%, 52% 95%, 74% 100%, 100% 96%, 100% 100%, 0% 100%)' }, 6.8);
tl.to('#card', { clipPath: 'polygon(0% 0%, 12% 0%, 30% 0%, 52% 0%, 74% 0%, 100% 0%, 100% 100%, 0% 100%)', duration: 1.0, ease: 'power3.out' }, 6.9);
```

## Do NOT

- Unity/WebGL shader thinking: no HLSL/GLSL here — these are the DOM
  equivalents, and they're what the architecture renders deterministically.
- `filter` tweens with mismatched function lists (string interpolation breaks).
- Animating `mask-position` with keywords (`center`) — use explicit sizes.
- Sharing one SVG filter across elements animated at different times.
