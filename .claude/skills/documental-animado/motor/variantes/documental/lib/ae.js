// AE — kit tipo After Effects para Canvas 2D (Motor de Video v2.0 · Estilo C · Animado élite).
// Port de herramientas/motion_ae.py (estilo B · Azul editorial). Cada función es pura del tiempo: cualquier cuadro se
// puede pintar en cualquier orden (export por tramos, revisión cuadro a cuadro).
//
//   Curvas ........ easeOutBack, easeOutElastic, spring, easeInOutExpo, easeOutExpo, easeOutCubic, stagger
//   Cámara 2.5D ... Camera: zoom/paneo/giro + apply(ctx, z) con paralaje por profundidad
//   Luz ........... glow (bloom aditivo sin quemar), lightSweep (destello que recorre), particles, gridFloor
//   Vidrio ........ glassCard (desenfoca lo de atrás, tinte, borde con luz cenital, sombra suave)
//   Revelados ..... maskReveal (barrido con borde suave), circleReveal, rectMorph (match cut)
//   Transiciones .. whip (desenfoque direccional por velocidad), accumulate (motion blur real por subcuadros)
//   Falla / HUD ... glitch, holoOutline
//   Calidad ....... dither (rompe las bandas de los degradados)
(function (root) {
  'use strict';
  const cl = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
  const ramp = (t, a, b) => (b > a ? cl((t - a) / (b - a)) : t >= a ? 1 : 0);
  const mix = (a, b, k) => a + (b - a) * k;

  // ---------------------------------------------------------------- curvas (nada lineal)
  function easeOutBack(u, s = 1.70158) { u = cl(u) - 1; return 1 + (s + 1) * u * u * u + s * u * u; }
  function easeOutElastic(u, p = 0.32) { u = cl(u); if (u === 0 || u === 1) return u; return Math.pow(2, -10 * u) * Math.sin((u - p / 4) * 2 * Math.PI / p) + 1; }
  /** Resorte físico 0→1, t en segundos desde que arranca (freq Hz, damping 1/s). */
  function spring(t, freq = 4.5, damping = 6.0) { if (t <= 0) return 0; return 1 - Math.exp(-damping * t) * Math.cos(2 * Math.PI * freq * t); }
  function easeInOutExpo(u) { u = cl(u); if (u === 0 || u === 1) return u; return u < 0.5 ? Math.pow(2, 20 * u - 10) / 2 : (2 - Math.pow(2, -20 * u + 10)) / 2; }
  function easeOutExpo(u) { u = cl(u); return u === 1 ? 1 : 1 - Math.pow(2, -10 * u); }
  function easeOutCubic(u) { u = cl(u); return 1 - Math.pow(1 - u, 3); }
  function easeInOutCubic(u) { u = cl(u); return u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; }
  function easeInOutSine(u) { u = cl(u); return -(Math.cos(Math.PI * u) - 1) / 2; }
  /** Progreso del elemento i de una serie escalonada: arranca en t0 + i·paso y dura dur. */
  function stagger(t, i, t0, paso = 0.06, dur = 0.45, curva = easeOutBack) { return curva(ramp(t, t0 + i * paso, t0 + i * paso + dur)); }
  /** Velocidad numérica de una curva (para decidir cuánto motion blur aplicar). */
  function vel(f, u, h = 1 / 240) { if (!(u > 0 && u < 1)) return 0; return (f(Math.min(1, u + h)) - f(Math.max(0, u - h))) / (Math.min(1, u + h) - Math.max(0, u - h)); }

  // ---------------------------------------------------------------- lienzos internos
  const mk = (w, h) => (typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(w, h) : Object.assign(document.createElement('canvas'), { width: w, height: h }));
  const pool = new Map();
  /** Lienzo de trabajo reutilizable (no se realoca en cada cuadro). */
  function scratch(name, w, h) {
    let c = pool.get(name);
    if (!c || c.width !== w || c.height !== h) { c = mk(w, h); pool.set(name, c); }
    const x = c.getContext('2d'); x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.filter = 'none'; x.shadowBlur = 0; x.clearRect(0, 0, w, h);
    return x;
  }

  // ---------------------------------------------------------------- cámara 2.5D
  /** Cámara virtual. (cx, cy) = punto del mundo al que mira, zoom, rot (grados). Una capa con z > 1 está más lejos:
   *  se mueve y escala menos (paralaje). z < 1 = primer plano (se mueve más). */
  class Camera {
    constructor(W, H, o = {}) { this.W = W; this.H = H; this.cx = o.cx ?? W / 2; this.cy = o.cy ?? H / 2; this.zoom = o.zoom ?? 1; this.rot = o.rot ?? 0; }
    apply(x, z = 1) {
      const k = 1 + (this.zoom - 1) / z, dx = (this.cx - this.W / 2) / z, dy = (this.cy - this.H / 2) / z;
      x.translate(this.W / 2, this.H / 2); if (this.rot) x.rotate(this.rot * Math.PI / 180 / z); x.scale(k, k); x.translate(-this.W / 2 - dx, -this.H / 2 - dy);
    }
    toScreen(px, py, z = 1) {
      const k = 1 + (this.zoom - 1) / z, dx = (this.cx - this.W / 2) / z, dy = (this.cy - this.H / 2) / z;
      return [this.W / 2 + (px - this.W / 2 - dx) * k, this.H / 2 + (py - this.H / 2 - dy) * k, k];
    }
  }

  // ---------------------------------------------------------------- formas
  function rrectPath(x, X, Y, w, h, r) { x.beginPath(); x.roundRect(X, Y, w, h, Math.max(0, Math.min(r, w / 2, h / 2))); }

  /** Sombra suave en dos capas (contacto + ambiente), como las tarjetas de Apple/Stripe. */
  function softShadow(x, X, Y, w, h, r, o = {}) {
    const a = o.alpha ?? 0.22, col = o.color || '10,20,50';
    x.save();
    x.shadowColor = `rgba(${col},${a})`; x.shadowBlur = o.blur ?? 70; x.shadowOffsetY = o.dy ?? 28; rrectPath(x, X, Y, w, h, r); x.fillStyle = `rgba(${col},${a})`; x.fill();
    x.shadowColor = `rgba(${col},${a * .9})`; x.shadowBlur = 10; x.shadowOffsetY = 4; x.fill();
    x.restore();
  }

  /** Tarjeta de vidrio: desenfoca lo que ya está pintado detrás, tiñe, borde fino con luz cenital y sombra suave. */
  function glassCard(x, X, Y, w, h, o = {}) {
    const r = o.r ?? 34, op = o.op ?? 1, blur = o.blur ?? 26, tint = o.tint || '255,255,255', ta = o.tintA ?? .10, dark = !!o.dark;
    if (op <= 0.003 || w < 2 || h < 2) return;
    x.save(); x.globalAlpha *= op;
    if (o.shadow !== false) softShadow(x, X, Y, w, h, r, { alpha: (o.shadowA ?? (dark ? .45 : .16)), color: dark ? '0,0,0' : '20,40,100', blur: 60, dy: 24 });
    // fondo desenfocado: se copia la región de atrás y se pinta con filtro dentro de la máscara
    const cv = x.canvas, tr = x.getTransform(), sx = Math.hypot(tr.a, tr.b);
    const pad = blur * 2, bx = Math.floor(tr.a * X + tr.c * Y + tr.e - pad), by = Math.floor(tr.b * X + tr.d * Y + tr.f - pad), bw = Math.ceil(w * sx + pad * 2), bh = Math.ceil(h * sx + pad * 2);
    if (o.backdrop !== false && bw > 0 && bh > 0) {
      const s = scratch('glass', Math.min(4096, bw), Math.min(4096, bh)); s.filter = `blur(${blur * sx}px) saturate(1.3)`; s.drawImage(cv, -bx, -by); s.filter = 'none';
      rrectPath(x, X, Y, w, h, r); x.save(); x.clip(); x.setTransform(1, 0, 0, 1, 0, 0); x.drawImage(s.canvas, bx, by); x.restore();
    }
    rrectPath(x, X, Y, w, h, r);
    const g = x.createLinearGradient(X, Y, X + w * .4, Y + h);
    g.addColorStop(0, `rgba(${tint},${ta * 1.6})`); g.addColorStop(1, `rgba(${tint},${ta * .7})`); x.fillStyle = g; x.fill();
    // borde: brillante arriba (luz cenital) y tenue abajo
    const e = x.createLinearGradient(0, Y, 0, Y + h); e.addColorStop(0, `rgba(255,255,255,${dark ? .32 : .9})`); e.addColorStop(.5, `rgba(255,255,255,${dark ? .08 : .35})`); e.addColorStop(1, `rgba(255,255,255,${dark ? .04 : .2})`);
    x.lineWidth = o.border ?? 1.5; x.strokeStyle = e; x.stroke();
    x.restore();
  }

  // ---------------------------------------------------------------- luz
  /** Bloom: vuelve a pintar lo que dibuje fn con desenfoque y modo aditivo. Fuerza baja = brillo sin quemar. */
  function glow(x, fn, o = {}) {
    const radius = o.radius ?? 18, k = o.strength ?? .55;
    x.save(); x.globalCompositeOperation = 'lighter';
    x.globalAlpha *= k; x.filter = `blur(${radius}px)`; fn(x);
    x.globalAlpha *= .6; x.filter = `blur(${radius * .35}px)`; fn(x);
    x.restore();
  }
  /** Halo radial aditivo (luz). */
  function halo(x, X, Y, R, color, a = .5) {
    const g = x.createRadialGradient(X, Y, 0, X, Y, R); g.addColorStop(0, `rgba(${color},${a})`); g.addColorStop(.4, `rgba(${color},${a * .35})`); g.addColorStop(1, `rgba(${color},0)`);
    x.save(); x.globalCompositeOperation = 'lighter'; x.fillStyle = g; x.fillRect(X - R, Y - R, 2 * R, 2 * R); x.restore();
  }
  /** Destello especular que cruza una forma (clip con path()). u 0→1. */
  function lightSweep(x, path, bbox, u, o = {}) {
    if (u <= 0 || u >= 1) return;
    const [X, Y, w, h] = bbox, ancho = (o.width ?? .22) * (w + h), a = o.alpha ?? .55, ang = (o.angle ?? 20) * Math.PI / 180;
    const c = -ancho + easeInOutCubic(u) * (w + h + 2 * ancho), dx = Math.cos(ang), dy = Math.sin(ang);
    x.save(); path(x); x.clip(); x.globalCompositeOperation = o.mode || 'lighter';
    const g = x.createLinearGradient(X + (c - ancho / 2) * dx, Y + (c - ancho / 2) * dy * .3, X + (c + ancho / 2) * dx, Y + (c + ancho / 2) * dy * .3);
    const col = o.color || '255,255,255';
    g.addColorStop(0, `rgba(${col},0)`); g.addColorStop(.5, `rgba(${col},${a})`); g.addColorStop(1, `rgba(${col},0)`); x.fillStyle = g; x.fillRect(X - 10, Y - 10, w + 20, h + 20);
    x.restore();
  }
  // generador determinista
  function hash(n) { n = (n ^ 61) ^ (n >>> 16); n = n + (n << 3); n ^= n >>> 4; n = Math.imul(n, 0x27d4eb2d); n ^= n >>> 15; return (n >>> 0) / 4294967296; }
  /** Partículas sutiles (polvo de luz) deterministas. */
  function particles(x, t, o = {}) {
    const n = o.n ?? 60, seed = o.seed ?? 7, [x0, y0, x1, y1] = o.area || [0, 0, 1920, 1080], v = o.vel ?? 16, col = o.color || '92,150,255', op = o.op ?? .5;
    x.save(); x.globalCompositeOperation = o.mode || 'lighter';
    for (let i = 0; i < n; i++) {
      const r1 = hash(seed * 997 + i * 13), r2 = hash(seed * 31 + i * 7 + 1), r3 = hash(i * 17 + seed), r4 = hash(i * 23 + seed * 3);
      const sp = .4 + .6 * r4, px = x0 + r1 * (x1 - x0) + Math.sin(t * .7 + r3 * 6.28) * 12;
      let py = y0 + ((r2 * (y1 - y0) - t * v * sp) % (y1 - y0) + (y1 - y0)) % (y1 - y0);
      const s = (o.size ?? 2.2) * (.5 + r3), tw = .45 + .55 * Math.sin(t * 2.1 + r1 * 6.28);
      x.globalAlpha = op * tw; x.fillStyle = `rgb(${col})`; x.beginPath(); x.arc(px, py, s, 0, 6.283); x.fill();
    }
    x.restore();
  }
  /** Rejilla en perspectiva que avanza (look técnico). */
  function gridFloor(x, t, o = {}) {
    const W = o.W ?? 1920, H = o.H ?? 1080, hy = H * (o.horizon ?? .52), col = o.color || '92,150,255', op = o.op ?? .5, n = o.cells ?? 16;
    x.save(); x.lineWidth = 1.2;
    const fade = x.createLinearGradient(0, hy, 0, H); fade.addColorStop(0, `rgba(${col},0)`); fade.addColorStop(1, `rgba(${col},${op})`);
    x.strokeStyle = fade;
    x.beginPath();
    for (let i = -n; i <= n; i++) { x.moveTo(W / 2 + i * W / n * .12, hy); x.lineTo(W / 2 + i * W / n * 2.2, H); }
    const off = (t * (o.speed ?? .22)) % 1;
    for (let k = 0; k < 18; k++) { const z = (k + off) / 18, y = hy + (H - hy) * Math.pow(z, 2.2); x.moveTo(0, y); x.lineTo(W, y); }
    x.stroke();
    // resplandor del horizonte
    const g = x.createLinearGradient(0, hy - 120, 0, hy + 60); g.addColorStop(0, `rgba(${col},0)`); g.addColorStop(.7, `rgba(${col},${op * .25})`); g.addColorStop(1, `rgba(${col},0)`);
    x.fillStyle = g; x.fillRect(0, hy - 120, W, 180);
    x.restore();
  }

  // ---------------------------------------------------------------- revelados
  /** Pinta fn dentro de un barrido con borde suave (ángulo en grados). u 0→1. */
  function maskReveal(x, u, bbox, fn, o = {}) {
    if (u <= 0) return; if (u >= 1) { fn(x); return; }
    const [X, Y, w, h] = bbox, ang = (o.angle ?? 0) * Math.PI / 180, soft = o.soft ?? 0.12;
    const L = Math.abs(w * Math.cos(ang)) + Math.abs(h * Math.sin(ang)), cx = X + w / 2, cy = Y + h / 2, dx = Math.cos(ang), dy = Math.sin(ang);
    const s = scratch('mask', Math.ceil(x.canvas.width), Math.ceil(x.canvas.height)); s.setTransform(x.getTransform()); fn(s);
    s.globalCompositeOperation = 'destination-in';
    const a0 = -L / 2 - soft * L, a1 = -L / 2 + u * (L * (1 + soft * 2));
    const g = s.createLinearGradient(cx + dx * a0, cy + dy * a0, cx + dx * a1, cy + dy * a1);
    g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(Math.max(0, 1 - soft * 2), 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    s.fillStyle = g; s.fillRect(X - w, Y - h, w * 3, h * 3);
    x.save(); x.setTransform(1, 0, 0, 1, 0, 0); x.drawImage(s.canvas, 0, 0); x.restore();
  }
  /** Revelado circular con borde suave. */
  function circleClip(x, cx, cy, R) { x.beginPath(); x.arc(cx, cy, Math.max(0, R), 0, 6.2832); x.clip(); }
  /** Match cut: interpola un rectángulo [x, y, w, h, r] hacia otro. */
  function rectMorph(r0, r1, u, curva = easeInOutExpo) { const k = curva(u); return r0.map((a, i) => a + (r1[i] - a) * k); }

  // ---------------------------------------------------------------- motion blur
  /** Desenfoque direccional de un lienzo ya pintado: n copias a lo largo del vector (dx, dy). */
  function whip(x, img, X, Y, w, h, dx, dy, o = {}) {
    const d = Math.hypot(dx, dy), n = d < 1.5 ? 1 : Math.min(o.max ?? 24, Math.ceil(d / 3) + 2);
    if (n === 1) { x.drawImage(img, X, Y, w, h); return; }
    const a0 = x.globalAlpha;
    for (let k = 0; k < n; k++) { const f = k / (n - 1) - .5; x.globalAlpha = a0 / (k + 1); x.drawImage(img, X + dx * f, Y + dy * f, w, h); }
    x.globalAlpha = a0;
  }
  /** Motion blur REAL por acumulación de subcuadros: drawAt(ctx, dt) pinta la capa en el instante t + dt (capa transparente).
   *  Se promedian n subcuadros repartidos en el obturador (fracción de cuadro) con suma aditiva premultiplicada. */
  function accumulate(x, n, shutter, fps, drawAt) {
    if (n <= 1) { drawAt(x, 0); return; }
    const W = x.canvas.width, H = x.canvas.height, acc = scratch('acc', W, H), tr = x.getTransform();
    acc.globalCompositeOperation = 'lighter';
    for (let k = 0; k < n; k++) {
      const s = scratch('sub', W, H); s.setTransform(tr); drawAt(s, (k / (n - 1) - .5) * shutter / fps);
      acc.globalAlpha = 1 / n; acc.drawImage(s.canvas, 0, 0);
    }
    x.save(); x.setTransform(1, 0, 0, 1, 0, 0); x.drawImage(acc.canvas, 0, 0); x.restore();
  }

  // ---------------------------------------------------------------- falla / HUD
  function glitch(x, t, k = 1, seed = 3) {
    const W = x.canvas.width, H = x.canvas.height, s = scratch('gl', W, H); s.drawImage(x.canvas, 0, 0);
    x.save(); x.setTransform(1, 0, 0, 1, 0, 0);
    x.globalCompositeOperation = 'lighter'; x.globalAlpha = .35 * k; x.drawImage(s.canvas, 8 * k, 0); x.drawImage(s.canvas, -8 * k, 0);
    x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1;
    const f = Math.floor(t * 30);
    for (let i = 0; i < 6 * k; i++) { const y = hash(f * 7 + i + seed) * H, h = 6 + hash(f * 11 + i) * 40, dx = (hash(f * 13 + i) - .5) * 120 * k; x.drawImage(s.canvas, 0, y, W, h, dx, y, W, h); }
    x.restore();
  }
  function holoOutline(x, X, Y, w, h, u, o = {}) {
    const col = o.color || '92,150,255', L = Math.min(w, h) * (o.corner ?? .18) * cl(u * 1.4);
    x.save(); x.strokeStyle = `rgba(${col},1)`; x.lineWidth = o.width ?? 3; x.lineCap = 'round'; x.beginPath();
    for (const [cx, cy, sx, sy] of [[X, Y, 1, 1], [X + w, Y, -1, 1], [X, Y + h, 1, -1], [X + w, Y + h, -1, -1]]) { x.moveTo(cx + sx * L, cy); x.lineTo(cx, cy); x.lineTo(cx, cy + sy * L); }
    x.shadowColor = `rgba(${col},.9)`; x.shadowBlur = 14; x.stroke(); x.restore();
  }

  // ---------------------------------------------------------------- calidad
  let ditherPat = null;
  /** Ruido de ±1 LSB que rompe las bandas de los degradados (se aplica al final del cuadro). */
  function dither(x, amount = .028) {
    if (!ditherPat) {
      const c = mk(256, 256), g = c.getContext('2d'), id = g.createImageData(256, 256);
      for (let i = 0; i < id.data.length; i += 4) { const v = 128 + (hash(i * 2654435761) - .5) * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
      g.putImageData(id, 0, 0); ditherPat = c;
    }
    x.save(); x.setTransform(1, 0, 0, 1, 0, 0); x.globalCompositeOperation = 'overlay'; x.globalAlpha = amount;
    x.fillStyle = x.createPattern(ditherPat, 'repeat'); x.fillRect(0, 0, x.canvas.width, x.canvas.height); x.restore();
  }

  root.AE = { cl, ramp, mix, easeOutBack, easeOutElastic, spring, easeInOutExpo, easeOutExpo, easeOutCubic, easeInOutCubic, easeInOutSine, stagger, vel,
    mk, scratch, Camera, rrectPath, softShadow, glassCard, glow, halo, lightSweep, hash, particles, gridFloor, maskReveal, circleClip, rectMorph,
    whip, accumulate, glitch, holoOutline, dither };
})(typeof globalThis !== 'undefined' ? globalThis : this);
