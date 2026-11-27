// Motor de Video v2.0 — «Estilo C · Animado élite».
// Tema azul editorial (Estilo B) por defecto y tema "club" (negro/dorado) opcional; superficies por escena (claro, azul,
// oscuro, barro); escenas re-animadas con el kit AE (lib/ae.js); tipografía cinética sincronizada palabra por palabra;
// transiciones que conectan con motion blur; dither final. Se carga ANTES del script del motor y solo usa sus globales
// (W, H, TH, P, starts, project, font, F, fitLines, imgCache, proc, world, …) cuando se llama, nunca al cargar.
(function () {
  'use strict';
  const A = window.AE;
  const cl = A.cl, ramp = A.ramp;

  /* ============================================================ TEMAS Y SUPERFICIES ============================== */
  const SURF = {
    // Estilo B: tarjeta clara (blanco → azul suave)
    light: { bg: ['#FFFFFF', '#DCE6FF'], glowRGB: '92,150,255', ink: '#0A1222', muted: '#5B6B88', accent: '#2F6BFF', accentRGB: '47,107,255', key: '#2F6BFF',
      card: '#FFFFFF', tint: '255,255,255', tintA: .55, dark: false, sea: '#E4ECFF', land: '#FFFFFF', landEdge: '#B9CBF4', slab: 'rgba(47,107,255,.22)',
      hi: '#2F6BFF', hiRGB: '47,107,255', loss: '#E4572E', lossRGB: '228,87,46', part: '47,107,255', partOp: .16, grid: false, shadow: '20,40,100', track: 'rgba(10,18,34,.08)' },
    // Estilo B: azul intenso
    blue: { bg: ['#1A47E0', '#4F8CFF'], glowRGB: '255,255,255', ink: '#FFFFFF', muted: 'rgba(255,255,255,.78)', accent: '#FFFFFF', accentRGB: '255,255,255', key: '#FFFFFF',
      card: 'rgba(255,255,255,.14)', tint: '255,255,255', tintA: .12, dark: true, sea: '#2457EA', land: 'rgba(255,255,255,.2)', landEdge: 'rgba(255,255,255,.45)', slab: 'rgba(5,20,80,.35)',
      hi: '#FFFFFF', hiRGB: '255,255,255', loss: '#FFB199', lossRGB: '255,177,153', part: '255,255,255', partOp: .3, grid: false, shadow: '5,15,70', track: 'rgba(255,255,255,.16)' },
    // Estilo B: oscuro con rejilla en perspectiva
    dark: { bg: ['#030713', '#0C1B3D'], glowRGB: '47,107,255', ink: '#F4F7FF', muted: '#8C9EC4', accent: '#5C96FF', accentRGB: '92,150,255', key: '#5C96FF',
      card: 'rgba(255,255,255,.06)', tint: '160,190,255', tintA: .07, dark: true, sea: '#040A1A', land: '#13234A', landEdge: '#2D4D92', slab: 'rgba(0,0,0,.55)',
      hi: '#5C96FF', hiRGB: '92,150,255', loss: '#FF6A4D', lossRGB: '255,106,77', part: '92,150,255', partOp: .45, grid: true, shadow: '0,0,0', track: 'rgba(255,255,255,.1)' },
    // Acento cálido (terracota / dorado) para lo prehispánico
    clay: { bg: ['#0D0705', '#2B160C'], glowRGB: '232,163,75', ink: '#FFF5EA', muted: '#C8A385', accent: '#E8A34B', accentRGB: '232,163,75', key: '#F0B45E',
      card: 'rgba(255,220,180,.07)', tint: '255,214,170', tintA: .07, dark: true, sea: '#0B0604', land: '#3A2216', landEdge: '#80502E', slab: 'rgba(0,0,0,.55)',
      hi: '#E8A34B', hiRGB: '232,163,75', loss: '#D9542E', lossRGB: '217,84,46', part: '240,180,94', partOp: .4, grid: false, shadow: '0,0,0', track: 'rgba(255,230,200,.12)' },
    // tema oscuro: negro / dorado
    club: { bg: ['#050505', '#1A1A1A'], glowRGB: '226,179,77', ink: '#F4EFE6', muted: '#A39E94', accent: '#E2B34D', accentRGB: '226,179,77', key: '#F5CF5C',
      card: 'rgba(255,255,255,.05)', tint: '255,235,200', tintA: .06, dark: true, sea: '#070707', land: '#1E1E1E', landEdge: '#4A4232', slab: 'rgba(0,0,0,.6)',
      hi: '#E2B34D', hiRGB: '226,179,77', loss: '#E5484D', lossRGB: '229,72,77', part: '226,179,77', partOp: .35, grid: true, shadow: '0,0,0', track: 'rgba(255,255,255,.08)' },
    gold: { bg: ['#C9962F', '#F5CF5C'], glowRGB: '255,255,255', ink: '#140F05', muted: 'rgba(20,15,5,.7)', accent: '#140F05', accentRGB: '20,15,5', key: '#140F05',
      card: 'rgba(255,255,255,.22)', tint: '255,255,255', tintA: .25, dark: false, sea: '#E8BD55', land: 'rgba(20,15,5,.18)', landEdge: 'rgba(20,15,5,.4)', slab: 'rgba(80,50,0,.3)',
      hi: '#140F05', hiRGB: '20,15,5', loss: '#8E1B10', lossRGB: '142,27,16', part: '255,255,255', partOp: .3, grid: false, shadow: '80,50,0', track: 'rgba(20,15,5,.12)' },
    charcoal: { bg: ['#0B0B0B', '#242424'], glowRGB: '226,179,77', ink: '#F4EFE6', muted: '#A39E94', accent: '#E2B34D', accentRGB: '226,179,77', key: '#F5CF5C',
      card: 'rgba(255,255,255,.06)', tint: '255,240,215', tintA: .07, dark: true, sea: '#0B0B0B', land: '#262626', landEdge: '#5A4E36', slab: 'rgba(0,0,0,.6)',
      hi: '#E2B34D', hiRGB: '226,179,77', loss: '#E5484D', lossRGB: '229,72,77', part: '226,179,77', partOp: .3, grid: false, shadow: '0,0,0', track: 'rgba(255,255,255,.08)' }
  };
  const THEMES = {
    editorial: { name: 'editorial', fontTitle: 'Inter', fontBody: 'Inter', fontSerif: 'Instrument Serif', surfaces: ['dark', 'light', 'blue'], logo: '', logoSize: 70, logoOpacity: .92,
      accent: '#2F6BFF', ink: '#F4F7FF', muted: '#8C9EC4', bg: '#030713', bg2: '#0C1B3D', accent2: '#E4572E', accent2b: '#5C96FF', sea: '#040A1A', land: '#13234A', landStroke: '#2D4D92',
      paper: '#FFFFFF', paperInk: '#0A1222', kitRules: true, camera: false, drift: 0, grain: 0, film: false, captions: true, blockTransition: 'swipe' },
    club: { name: 'club', fontTitle: 'Inter', fontBody: 'Inter', fontSerif: 'Instrument Serif', surfaces: ['club', 'charcoal', 'gold'], logo: '', logoSize: 70, logoOpacity: .92,
      accent: '#E2B34D', ink: '#F4EFE6', muted: '#A39E94', bg: '#050505', bg2: '#1A1A1A', accent2: '#E5484D', accent2b: '#F5CF5C', sea: '#070707', land: '#1E1E1E', landStroke: '#4A4232',
      paper: '#F3EEE3', paperInk: '#1B1405', kitRules: true, camera: false, drift: 0, grain: 0, film: false, captions: true, blockTransition: 'swipe' }
  };
  function resolveTheme(pj, DEFAULT) {
    const t = pj.theme || {}, eng = pj.engine === 'v1' ? 'v1' : 'v2';
    if (eng === 'v1') return Object.assign({}, DEFAULT, t, { engine: 'v1' });
    const base = THEMES[t.name === 'club' ? 'club' : 'editorial'];
    return Object.assign({}, DEFAULT, base, t, { engine: 'v2', name: base.name, surfaceMap: Object.assign({}, t.surfaceMap || {}) });
  }

  /* ============================================================ PREPARACIÓN DEL PROYECTO =========================== */
  const V = { words: null, pw: [], beats: [], surf: [], trans: [] };
  const PREF = { map: ['dark', 'club'], photo: ['dark', 'club'], image: ['dark', 'club'], people: ['dark', 'charcoal'], stat: ['blue', 'gold'], title: ['blue', 'gold'],
    date: ['light', 'charcoal'], timeline: ['light', 'charcoal'], bars: ['light', 'charcoal'], chart: ['dark', 'club'], donut: ['light', 'charcoal'], compare: ['blue', 'gold'],
    list: ['light', 'charcoal'], flow: ['dark', 'club'], quote: ['blue', 'gold'], doc: ['light', 'charcoal'], gallery: ['dark', 'club'], screen: ['dark', 'club'], motion: ['dark', 'club'], montage: ['dark', 'club'] };
  const norm = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9ñ]+/g, '');

  function prepare() {
    if (TH.engine !== 'v2') return;
    // superficie de cada escena: la pedida o la preferida por tipo, sin repetir la anterior (regla del estilo B)
    const allowed = TH.surfaces || ['dark', 'light', 'blue']; let prev = null; V.surf = [];
    P.forEach((p, j) => {
      if (!p.scene) { V.surf[j] = prev; return; }
      const S = p.scene; let s = S.surface && SURF[S.surface] ? S.surface : null;
      if (!s) {
        const pr = (PREF[S.type] || allowed).filter(x => allowed.includes(x));
        s = pr.find(x => x !== prev) || allowed.find(x => x !== prev) || allowed[0];
        if (S.type === 'photo' || S.type === 'image') s = pr[0] || s;   // las fotos a sangre no necesitan alternar
      }
      V.surf[j] = s; prev = s;
    });
    // transiciones por defecto: que conecten y no se repitan
    const cyc = ['whip', 'card', 'zoom', 'mask', 'whip', 'zoom', 'card'], hist = []; V.trans = [];
    P.forEach((p, j) => {
      if (!p.scene || j === 0) return; const S = p.scene;
      let ty = S.transition ? (V2MAP[S.transition] || S.transition) : null;
      if (!ty) ty = P[j].b !== P[j - 1].b ? (TH.blockTransition || 'swipe') : cyc[(j * 7 + hist.length) % cyc.length];
      if (!S.transition && ty === hist[hist.length - 1]) ty = cyc[(cyc.indexOf(ty) + 1) % cyc.length];
      hist.push(ty); V.trans[j] = { ty, d: TRD[ty] ?? .6, dir: (hist.length % 2 ? 1 : -1) };
    });
    buildBeats();
  }
  const TRD = { cut: 0, whip: .5, card: .7, zoom: .55, mask: .7, swipe: .8, morph: .8 };
  const V2MAP = { fade: 'card', dip: 'swipe', blur: 'zoom', slide: 'whip', push: 'whip', cover: 'card', pushthrough: 'zoom', liquid: 'mask', shapes: 'swipe', wipe: 'mask', leak: 'zoom', flash: 'cut' };
  function transOf(k) { return V.trans[k] || { ty: 'cut', d: 0, dir: 1 }; }

  /* ---------- palabras (Whisper / ElevenLabs with-timestamps) ---------- */
  function setWords(words) { V.words = Array.isArray(words) && words.length ? words.map(w => ({ w: w.w, s: +w.s, e: +w.e, n: norm(w.w) })) : null; }
  /** Asigna a cada frase su tramo de palabras y fija los inicios de frase en la primera palabra (sincronía exacta). */
  function syncByWords(lead = .1) {
    if (!V.words) return false; const Wd = V.words; let ptr = 0; const out = []; V.pw = [];
    for (let i = 0; i < P.length; i++) {
      const toks = P[i].text.split(/\s+/).map(norm).filter(Boolean); let k = -1;
      for (let q = ptr; q < Math.min(Wd.length, ptr + 12); q++) { if (toks.length && (Wd[q].n === toks[0] || (toks[0].length > 2 && Wd[q].n.startsWith(toks[0].slice(0, 3))))) { k = q; break; } }
      if (k < 0) k = Math.min(ptr, Wd.length - 1);
      V.pw[i] = [k, Math.min(Wd.length, k + toks.length)]; out.push(Math.max(0, Wd[k].s - lead)); ptr = k + toks.length;
    }
    out[0] = 0; for (let i = 1; i < out.length; i++) if (out[i] <= out[i - 1]) out[i] = out[i - 1] + .05;
    starts = out; buildBeats(); return true;
  }
  /** Palabras de la frase i con tiempos (reales o estimados por caracteres). */
  function phraseWords(i) {
    const toks = P[i].text.split(/\s+/).filter(Boolean);
    if (V.words && V.pw[i]) { const [a, b] = V.pw[i]; const ws = V.words.slice(a, b); if (ws.length) return ws.map((w, k) => ({ w: toks[k] || w.w, s: w.s, e: w.e })); }
    const t0 = starts[i] + .12, t1 = (i + 1 < P.length ? starts[i + 1] : voiceEnd()) - .25, tot = toks.reduce((s, w) => s + w.length + 1, 0); let acc = 0;
    return toks.map(w => { const s = t0 + (t1 - t0) * acc / tot; acc += w.length + 1; return { w, s, e: t0 + (t1 - t0) * acc / tot }; });
  }
  const STOP = new Set('el la los las un una unos unas de del al a y e o u en con por para que se su sus es era fue mas más muy hasta como cómo pero ni lo le les mi tu te nos ya hoy cada'.split(' '));
  /** Beats de la tipografía cinética: contexto chico + UNA palabra clave grande (estilo B). */
  function buildBeats() {
    V.beats = P.map((p, i) => {
      const ph = project.blocks[p.b].phrases[+p.id.split('.')[1] - 1]; const o = typeof ph === 'object' ? ph : {};
      const own = P[ownerOf(i)].scene || {}; if (o.cap === false || (o.cap == null && own.cap === false)) return [];
      const ws = phraseWords(i); if (!ws.length) return [];
      let keys = o.keys || (o.key ? [o.key] : null);
      if (!keys) { const c = ws.map((w, k) => [k, w.w.replace(/[^\p{L}\p{N}]/gu, '')]).filter(([, w]) => w.length > 3 && !STOP.has(w.toLowerCase()) || /\d/.test(w)); keys = c.length ? [ws[c[c.length - 1][0]].w] : [ws[ws.length - 1].w]; }
      const beats = []; let from = 0;
      keys.forEach(kRaw => {
        const serif = String(kRaw).startsWith('*'), kw = String(kRaw).replace(/^\*/, ''), kn = kw.split(/\s+/).map(norm);
        let idx = -1; for (let q = from; q < ws.length; q++) if (norm(ws[q].w) === kn[0] || norm(ws[q].w).startsWith(kn[0])) { idx = q; break; }
        if (idx < 0) return; const kEnd = Math.min(ws.length, idx + kn.length);
        const ctxW = ws.slice(Math.max(from, idx - (o.ctxMax || 4)), idx);
        const label = o.labels && o.labels[beats.length]; // texto alternativo para la clave (p. ej. "130 millones")
        beats.push({ pi: i, ctx: o.ctx && beats.length === 0 ? [{ w: o.ctx, s: (ctxW[0] || ws[idx]).s }] : ctxW, key: { w: label || ws.slice(idx, kEnd).map(w => w.w).join(' ').replace(/[.,;:…]+$/, ''), s: ws[idx].s, e: ws[kEnd - 1].e }, serif, t0: (ctxW[0] || ws[idx]).s - .05, tEnd: ws[kEnd - 1].e });
        from = kEnd;
      });
      return beats;
    });
  }

  /* ============================================================ FONDOS ============================================ */
  let K = SURF.dark;
  function surfOf(j) { return SURF[V.surf[j]] || SURF[(TH.surfaces || ['dark'])[0]] || SURF.dark; }
  function withSurface(j, fn) {
    const saved = TH, s = surfOf(j); K = s;
    TH = Object.assign({}, saved, { bg: s.bg[0], bg2: s.bg[1], ink: s.ink, muted: s.muted, accent: s.accent, accent2: s.loss, accent2b: s.key, sea: s.sea, land: s.land, landStroke: s.landEdge, paperInk: '#0A1222' });
    try { return fn(s); } finally { TH = saved; }
  }
  function drawSurface(x, s, t, cam) {
    const g = x.createLinearGradient(0, 0, W * .55, H * 1.15); g.addColorStop(0, s.bg[0]); g.addColorStop(1, s.bg[1]); x.fillStyle = g; x.fillRect(-60, -60, W + 120, H + 120);
    x.save(); if (cam) cam.apply(x, 3);
    // luces que derivan despacio (capa lejana)
    const o1x = W * (.22 + .05 * Math.sin(t * .11)), o1y = H * (.18 + .04 * Math.cos(t * .09)), o2x = W * (.82 + .04 * Math.cos(t * .07)), o2y = H * (.86 + .03 * Math.sin(t * .1));
    const big = (X, Y, R, a) => { const r = x.createRadialGradient(X, Y, 0, X, Y, R); r.addColorStop(0, `rgba(${s.glowRGB},${a})`); r.addColorStop(1, `rgba(${s.glowRGB},0)`); x.fillStyle = r; x.fillRect(X - R, Y - R, 2 * R, 2 * R); };
    big(o1x, o1y, 900, s.dark ? .16 : .35); big(o2x, o2y, 800, s.dark ? .12 : .22);
    if (s.grid) A.gridFloor(x, t, { color: s.accentRGB, op: .32, horizon: .6 });
    x.restore();
    if (s.dark) { const v = x.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, W * .78); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,.45)'); x.fillStyle = v; x.fillRect(0, 0, W, H); }
  }

  /* ============================================================ DIBUJO DE ESCENA ================================== */
  const SC = {};          // escenas v2
  const MOT = {};         // animaciones "motion" nuevas
  function drawScene(x, j, t) {
    const si = sceneInfo(j), S = si.S, lt = t - si.s0, step = Math.max(0, Math.min(si.stepStarts.length - 1, phraseAt(t) - j));
    withSurface(j, s => {
      const v2 = SC[S.type], camOn = !(v2 && v2.cam === false);
      const cam = new A.Camera(W, H);
      // vida continua: deriva lenta + empuje con resorte en cada frase de la escena (nada estático > 3 s)
      const kz = [[0, 1], ...si.stepStarts.slice(1).map((st, k) => [st, 1 + .018 * (k + 1)])];
      cam.zoom = (window.Motion ? Motion.track(lt, kz, 'heavy') : 1) + .03 * A.easeInOutSine(lt / Math.max(2, si.dur)) + (camOn ? 0 : 0);
      cam.cx = W / 2 + 14 * Math.sin(lt * .37 + j); cam.cy = H / 2 + 8 * Math.cos(lt * .29 + j * 1.7);
      x.save(); drawSurface(x, s, t, cam);
      if (S.bg) { const im = proc(S.bg, `brightness(${S.bgBright ?? .45}) saturate(.9)`); if (im) { x.save(); cam.apply(x, 1.6); kenBurns(x, im, lt, si.dur, { move: S.bgMove || 'in', amount: .1, focus: S.bgFocus }); x.restore(); x.fillStyle = s.dark ? 'rgba(3,7,19,.35)' : 'rgba(255,255,255,.55)'; x.fillRect(0, 0, W, H); } }
      let capOff = true; for (let q = j; q < j + si.stepStarts.length; q++) if ((V.beats[q] || []).length) capOff = false;
      const c = { ctx: x, S, lt, dur: si.dur, step, stepStarts: si.stepStarts, lead: starts[j] - si.s0, j, K: s, cam, t, s0: si.s0, capOff };
      x.save();
      if (camOn) cam.apply(x, 1);
      if (v2) v2.draw ? v2.draw(c) : v2(c); else if (SCENES[S.type]) { x.save(); SCENES[S.type](c); x.restore(); }
      x.restore();
      if (S.counter) counterCard(c, S.counter);
      if (s.dark && S.particles !== false) A.particles(x, t, { color: s.part, op: s.partOp * .55, n: 36, seed: j + 3, vel: 14 });
      x.restore();
      if (S.bg) credit(x, S.bgCredit || creditOf(S.bg), prog(lt, .4, .8));
    });
  }

  /* ============================================================ HERRAMIENTAS DE TEXTO ============================ */
  const FW = (w, size) => `${w} ${size}px "${TH.fontBody}", system-ui, -apple-system, sans-serif`;
  const FS = (size, w = 500) => `italic ${w} ${size}px "${TH.fontSerif}", Georgia, serif`;
  function setF(x, spec, ls = 0) { x.font = spec; x.letterSpacing = ls + 'px'; }
  function fitSize(x, text, specFn, maxW, size, min = 24) { for (let s = size; s >= min; s -= 2) { x.font = specFn(s); if (x.measureText(text).width <= maxW) return s; } return min; }
  /** Entrada estándar: opacidad en ≤ 4 cuadros, movimiento con resorte. */
  const ent = (lt, at, preset = 'default') => ({ a: cl((lt - at) / .07), e: lt <= at ? 0 : Motion.step(lt - at, preset) });
  /** Palabras que suben a través de su máscara, escalonadas. */
  function riseText(x, text, X, Y, lt, at, o = {}) {
    const words = String(text).split(' '), sp = x.measureText(' ').width, size = o.size || 80, align = o.align || 'left';
    const tw = x.measureText(text).width; let px = align === 'center' ? X - tw / 2 : align === 'right' ? X - tw : X;
    x.save(); x.textAlign = 'left'; x.textBaseline = 'alphabetic';
    words.forEach((w, k) => {
      const t0 = at + k * (o.stagger ?? .06), { a, e } = ent(lt, t0, o.preset || 'default'), ww = x.measureText(w).width;
      if (lt > t0) { x.save(); x.beginPath(); x.rect(px - 20, Y - size * 1.15, ww + 40, size * 1.5); x.clip(); x.globalAlpha *= a; x.fillText(w, px, Y + (1 - e) * size * 1.1); x.restore(); }
      px += ww + sp;
    });
    x.restore(); return tw;
  }
  /** Píldora de vidrio con texto (etiquetas de mapa, rótulos). */
  function pill(x, text, X, Y, o = {}) {
    const s = o.size || 30, padX = s * .75, h = s * 1.9; setF(x, FW(o.w || 600, s)); const tw = x.measureText(text).width, w = tw + padX * 2 + (o.dot ? s * .9 : 0);
    const bx = o.align === 'center' ? X - w / 2 : o.align === 'right' ? X - w : X, by = Y - h / 2, a = o.a ?? 1; if (a <= 0) return w;
    x.save(); x.globalAlpha *= a;
    if (o.solid) { A.softShadow(x, bx, by, w, h, h / 2, { alpha: .25, color: K.shadow, blur: 30, dy: 10 }); A.rrectPath(x, bx, by, w, h, h / 2); x.fillStyle = o.solid; x.fill(); }
    else A.glassCard(x, bx, by, w, h, { r: h / 2, dark: K.dark, tint: K.tint, tintA: K.dark ? .14 : .7, blur: 18, shadowA: K.dark ? .35 : .12 });
    if (o.dot) { x.beginPath(); x.arc(bx + padX + s * .25, Y, s * .22, 0, 6.29); x.fillStyle = o.dotColor || K.accent; x.fill(); }
    x.fillStyle = o.color || K.ink; x.textAlign = 'left'; x.textBaseline = 'middle'; setF(x, FW(o.w || 600, s)); x.fillText(text, bx + padX + (o.dot ? s * .9 : 0), Y + s * .05);
    x.restore(); return w;
  }
  function kicker(c, text, at = 0) {
    if (!text) return; const { ctx: x, lt } = c, { a, e } = ent(lt, at, 'snappy');
    x.save(); x.translate(-30 * (1 - e), 0); pill(x, String(text).toUpperCase(), 120, 112, { size: 24, w: 700, dot: true, a }); x.restore();
  }

  /** Pinta fn en una capa y le pasa un destello que solo toca lo pintado (texto, cifras): nunca un rectángulo visible. */
  function sweepLayer(x, fn, u, o = {}) {
    if (!(u > 0 && u < 1)) { fn(x); return; }
    const s = A.scratch('sweep', x.canvas.width, x.canvas.height); s.setTransform(x.getTransform()); s.globalAlpha = x.globalAlpha; fn(s);
    s.setTransform(1, 0, 0, 1, 0, 0); s.globalAlpha = 1; s.globalCompositeOperation = 'source-atop';
    const Wc = x.canvas.width, c0 = -Wc * .3 + A.easeInOutCubic(u) * Wc * 1.6, g = s.createLinearGradient(c0 - 220, 0, c0 + 220, Wc * .25);
    const col = o.color || '255,255,255'; g.addColorStop(0, `rgba(${col},0)`); g.addColorStop(.5, `rgba(${col},${o.alpha ?? .6})`); g.addColorStop(1, `rgba(${col},0)`); s.fillStyle = g; s.fillRect(0, 0, Wc, x.canvas.height);
    x.save(); x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.drawImage(s.canvas, 0, 0); x.restore();
  }
  /* ---------- odómetro: cada dígito rueda como un contador mecánico (con desenfoque vertical si va rápido) ---------- */
  function odometer(x, value, X, Y, size, o = {}) {
    const dec = o.decimals || 0, neg = value < 0, v = Math.abs(value) * Math.pow(10, dec), fin = Math.abs(o.final ?? value) * Math.pow(10, dec);
    const nd = Math.max(1, String(Math.floor(Math.max(fin, v))).length), sep = o.sep ?? ',', ch = [];
    for (let p = nd - 1; p >= 0; p--) { ch.push({ p }); if (p > 0 && p % 3 === 0 && sep) ch.push({ s: sep, after: p }); }
    if (dec) ch.splice(ch.length - dec, 0, { s: '.' });
    setF(x, o.font || FW(700, size), o.ls ?? -size * .03); const cw = x.measureText('0').width * 1.0, sw = x.measureText(sep || ',').width;
    const pre = (neg ? '−' : '') + (o.prefix || ''), suf = o.suffix || '', prw = x.measureText(pre).width;
    let sfw = 0; if (suf) { x.font = o.sufFont || o.font || FW(700, size); sfw = x.measureText(suf).width; setF(x, o.font || FW(700, size), o.ls ?? -size * .03); }
    const lead = Math.floor(v).toString().length; // dígitos visibles (los de la izquierda aparecen cuando hacen falta)
    const vis = c => c.s ? (c.after == null || c.after < Math.max(lead, 1) || o.pad) : (c.p < Math.max(lead, 1) || o.pad);
    let tw = prw; ch.forEach(c => { if (vis(c)) tw += c.s ? sw : cw; }); tw += sfw;
    let px = o.align === 'left' ? X : o.align === 'right' ? X - tw : X - tw / 2;
    x.save(); x.textBaseline = 'alphabetic'; x.textAlign = 'left'; x.fillStyle = o.color || K.ink;
    if (pre) { x.fillText(pre, px, Y); } px += prw;
    const speed = o.speed || 0;
    ch.forEach(c => {
      if (!vis(c)) return; if (c.s) { x.fillText(c.s, px, Y); px += sw; return; }
      const p = c.p, pw = Math.pow(10, p), d = Math.floor(v / pw) % 10, lower = v % pw;
      let f = p === 0 ? v - Math.floor(v) : Math.max(0, lower - (pw - 1));
      x.save(); x.beginPath(); x.rect(px - 4, Y - size * .95, cw + 8, size * 1.18); x.clip();
      const n2 = (d + 1) % 10, off = f * size * 1.08, blurN = speed > 0 && p <= 1 ? Math.min(4, Math.ceil(speed * (p === 0 ? 1 : .3))) : 1;
      for (let q = 0; q < blurN; q++) {
        const dy = (q / Math.max(1, blurN - 1) - .5) * size * .25 * (blurN > 1 ? 1 : 0); x.globalAlpha = (o.alpha ?? 1) / (q + 1);
        const dw = x.measureText(String(d)).width, nw = x.measureText(String(n2)).width;
        x.fillText(String(d), px + (cw - dw) / 2, Y - off + dy); x.fillText(String(n2), px + (cw - nw) / 2, Y - off + size * 1.08 + dy);
      }
      x.restore(); px += cw;
    });
    if (suf) { x.font = o.sufFont || o.font || FW(700, size); x.fillStyle = o.sufColor || o.color || K.ink; x.fillText(suf, px, Y); }
    x.restore(); return tw;
  }
  /** Tarjeta-contador superpuesta a cualquier escena: { value, from, prefix, suffix, label, at, dur, pos } */
  function counterCard(c, o) {
    const { ctx: x, lt } = c, at = o.at ?? .2, dur = o.dur ?? 1.6, u = A.easeOutExpo(ramp(lt, at, at + dur)), from = o.from ?? 0, v = from + (o.value - from) * u;
    const sp = Math.abs(A.vel(A.easeOutExpo, ramp(lt, at, at + dur)) * (o.value - from) / dur / 60);
    const { a, e } = ent(lt, at - .15, 'default'); if (a <= 0) return;
    const size = o.size || 150, pos = o.pos || 'right', cw = o.w || 640, ch = size * 1.25 + (o.label ? 70 : 0) + 40;
    const X = pos === 'left' ? 110 : pos === 'center' ? W / 2 - cw / 2 : W - 110 - cw, Y = (o.y ?? 470) - ch / 2;
    x.save(); x.globalAlpha *= a; x.translate(0, 40 * (1 - e));
    A.glassCard(x, X, Y, cw, ch, { r: 36, dark: K.dark, tint: K.tint, tintA: K.dark ? .1 : .65, blur: 30 });
    odometer(x, v, X + cw / 2, Y + 30 + size * .95, size, { prefix: o.prefix, suffix: o.suffix, final: o.value, speed: sp, color: K.ink, sufColor: K.key, sufFont: FS(size * .8, 500) });
    if (o.label) { setF(x, FW(600, 34)); x.fillStyle = K.muted; x.textAlign = 'center'; x.textBaseline = 'alphabetic'; x.fillText(o.label, X + cw / 2, Y + ch - 34); }
    A.lightSweep(x, q => A.rrectPath(q, X, Y, cw, ch, 36), [X, Y, cw, ch], ramp(lt, at + dur - .3, at + dur + .7), { alpha: K.dark ? .25 : .5 });
    x.restore();
  }

  /* ============================================================ ESCENAS ============================================ */
  // ---------- title: título editorial con UNA palabra clave en cursiva de acento ----------
  SC.title = function (c) {
    const { ctx: x, S, lt } = c, key = S.key ? norm(S.key) : null, words = String(S.text || '').split(' '), cy = S.logo ? 560 : (c.capOff ? 520 : 470);
    if (S.logo) { const im = imgCache(S.logo === true ? TH.logo : S.logo); if (im) { const { a, e } = ent(lt, 0, 'heavy'), k = 260 / Math.max(im.width, im.height); x.save(); x.globalAlpha *= a; x.translate(W / 2, 270); x.scale(.86 + .14 * e, .86 + .14 * e); A.halo(x, 0, 0, 300, K.glowRGB, .35 * a); x.drawImage(im, -im.width * k / 2, -im.height * k / 2, im.width * k, im.height * k); x.restore(); } }
    kicker(c, S.kicker, 0);
    // tamaño que cabe en 1 o 2 líneas
    let size = S.size || 132, lines;
    for (; size >= 64; size -= 4) { setF(x, FW(700, size), -size * .025); lines = wrapMixed(x, words, key, size, 1640); if (lines.length <= (S.lines || 2)) break; }
    const lh = size * 1.06, top = cy - (lines.length - 1) * lh / 2 + size * .35;
    let k = 0;
    lines.forEach((L, li) => {
      let px = W / 2 - L.w / 2; const y = top + li * lh;
      L.items.forEach(it => {
        const t0 = .15 + k * (S.stagger ?? .07), { a, e } = ent(lt, t0, it.key ? 'heavy' : 'default'); k++;
        x.save(); x.font = it.font; x.letterSpacing = it.ls + 'px'; x.beginPath(); x.rect(px - 30, y - size * 1.2, it.w + 60, size * 1.55); x.clip();
        x.globalAlpha *= a; x.fillStyle = it.key ? K.key : K.ink; x.textAlign = 'left'; x.textBaseline = 'alphabetic';
        if (it.key && K.dark) { x.shadowColor = `rgba(${K.accentRGB},.45)`; x.shadowBlur = 40; }
        x.fillText(it.w0, px, y + (1 - e) * size * 1.15); x.restore();
        if (it.key) { const ue = A.easeInOutExpo(ramp(lt, t0 + .25, t0 + .85)); x.save(); x.fillStyle = K.key; x.globalAlpha *= .9; x.fillRect(px, y + size * .16, it.w * ue, Math.max(4, size * .045)); x.restore(); }
        px += it.w + it.sp;
      });
    });
    if (S.sub) { setF(x, FW(500, 40)); x.fillStyle = K.muted; riseText(x, S.sub, W / 2, top + lines.length * lh + 30, lt, .7, { size: 40, align: 'center', stagger: .04 }); }
  };
  function wrapMixed(x, words, key, size, maxW) {
    const items = words.map(w => { const isK = key && norm(w).startsWith(key); const font = isK ? FS(size * 1.08, 500) : FW(700, size), ls = isK ? 0 : -size * .025;
      x.font = font; x.letterSpacing = ls + 'px'; const ww = x.measureText(w).width; x.font = FW(700, size); return { w0: w, key: isK, font, ls, w: ww, sp: size * .26 }; });
    const lines = []; let cur = { items: [], w: 0 };
    items.forEach(it => { if (cur.items.length && cur.w + it.w > maxW) { lines.push(cur); cur = { items: [], w: 0 }; } cur.w += (cur.items.length ? it.sp : 0) + it.w; cur.items.push(it); });
    if (cur.items.length) lines.push(cur);
    lines.forEach(L => { L.items.forEach((it, i) => { if (i === L.items.length - 1) it.sp = 0; }); L.w = L.items.reduce((s, it) => s + it.w + it.sp, 0); });
    return lines;
  }

  // ---------- date: la cámara viaja por una regla de años mientras el número rueda ----------
  SC.date = function (c) {
    const { ctx: x, S, lt, dur } = c, y1 = S.year ?? parseInt(String(S.text).replace(/[^\d-−]/g, '').replace('−', '-'), 10), y0 = S.from ?? (isFinite(y1) ? y1 - 40 : 0);
    const tdur = S.travel ?? Math.min(1.6, Math.max(.8, dur * .45)), at = S.at ?? .05, u = A.easeInOutExpo(ramp(lt, at, at + tdur)), yr = y0 + (y1 - y0) * u;
    const span = Math.abs(y1 - y0), unit = S.unit || (span > 600 ? 100 : span > 120 ? 25 : span > 30 ? 5 : 1), px = S.px || (span > 600 ? 260 : span > 120 ? 220 : 160);
    const ry = 660, cx = W / 2;
    // regla (capa de la cámara): marcas que pasan con desenfoque cuando la cámara corre
    const vpx = Math.abs(A.vel(A.easeInOutExpo, ramp(lt, at, at + tdur)) * (y1 - y0) / unit * px / tdur / 60);
    const { a: ra } = ent(lt, 0, 'snappy');
    x.save(); x.globalAlpha *= ra;
    const g = x.createLinearGradient(0, 0, W, 0); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(.12, '#000'); g.addColorStop(.88, '#000'); g.addColorStop(1, 'rgba(0,0,0,0)');
    const s = A.scratch('ruler', W, 260); s.translate(0, -ry + 130);
    s.strokeStyle = K.ink; s.fillStyle = K.ink; const first = Math.floor((yr - (W / 2) / px * unit) / unit) - 1, last = Math.ceil((yr + (W / 2) / px * unit) / unit) + 1;
    s.globalAlpha = .9; s.fillStyle = K.track; s.fillRect(0, ry - 2, W, 4); s.fillStyle = K.ink;
    for (let q = first; q <= last; q++) {
      const yv = q * unit, X = cx + (yv - yr) / unit * px, major = (q % (unit >= 25 ? 4 : 5)) === 0;
      for (let m = 1; m < 5; m++) { const xm = X + px * m / 5; s.globalAlpha = .35; s.fillRect(xm - 1, ry - 10, 2, 20); }
      s.globalAlpha = major ? .95 : .6; s.fillRect(X - 1.5, ry - (major ? 34 : 20), 3, major ? 68 : 40);
      if (major || px >= 200) { s.globalAlpha = major ? .85 : .5; setF(s, FW(600, major ? 34 : 26)); s.textAlign = 'center'; s.textBaseline = 'top'; s.fillText(yearLabel(yv), X, ry + 46); }
    }
    s.globalCompositeOperation = 'destination-in'; s.setTransform(1, 0, 0, 1, 0, 0); s.fillStyle = g; s.globalAlpha = 1; s.fillRect(0, 0, W, 260);
    A.whip(x, s.canvas, 0, ry - 130, W, 260, Math.min(160, vpx * .8), 0);
    // marcador central
    x.fillStyle = K.key; x.beginPath(); x.moveTo(cx - 16, ry - 58); x.lineTo(cx + 16, ry - 58); x.lineTo(cx, ry - 36); x.closePath(); x.fill();
    A.halo(x, cx, ry, 160, K.accentRGB, .25);
    x.restore();
    // año grande: rueda con el viaje
    const big = S.size || 250, label = S.text && !/^\s*[−-]?\d+\s*$/.test(String(S.text)) && u >= 1 ? null : null;
    const { a, e } = ent(lt, 0, 'heavy');
    x.save(); x.globalAlpha *= a; x.translate(0, 50 * (1 - e));
    const disp = Math.round(yr);
    sweepLayer(x, q => odometer(q, Math.abs(disp), cx, 440, big, { final: Math.abs(y1), sep: '', speed: vpx / 40, color: K.ink, suffix: disp < 0 ? ' a. C.' : (S.suffix || ''), sufFont: FS(big * .42, 500), sufColor: K.key }), ramp(lt, at + tdur - .1, at + tdur + .8), { alpha: K.dark ? .7 : .6, color: K.dark ? '255,255,255' : '150,190,255' });
    x.restore();
    if (S.sub) { setF(x, FW(600, 46)); x.fillStyle = K.muted; riseText(x, S.sub, cx, 200, lt, .25, { size: 46, align: 'center', stagger: .05 }); }
    if (S.chip) { const ce = ent(lt, at + tdur * .75, 'snappy'); x.save(); x.translate(0, 18 * (1 - ce.e)); pill(x, S.chip, cx, 548, { size: 30, w: 600, align: 'center', dot: true, a: ce.a, dotColor: K.key }); x.restore(); }
    kicker(c, S.kicker, .1);
  };
  function yearLabel(y) { return y < 0 ? `${Math.abs(y)} a. C.` : String(y); }

  // ---------- stat: cifra gigante que cuenta con odómetro + anillo + tarjeta de foto opcional ----------
  SC.stat = function (c) {
    const { ctx: x, S, lt } = c, at = S.at ?? .15, dur = S.countTime ?? 1.6, u = A.easeOutExpo(ramp(lt, at, at + dur)), from = S.from || 0, v = from + (S.value - from) * u;
    const sp = Math.abs(A.vel(A.easeOutExpo, ramp(lt, at, at + dur)) * (S.value - from) / dur / 60);
    const side = !!S.photo, cx = side ? 1240 : W / 2, cy = side ? 500 : (S.ring ? 500 : c.capOff ? 540 : 470), size = S.size || (side ? 210 : 230);
    if (side) photoCard(c, S.photo, 120, 140, 620, 640, { focus: S.focus });
    if (S.ring) { const r = 340, re = A.easeInOutExpo(ramp(lt, at, at + dur)); x.save(); x.lineWidth = 14; x.strokeStyle = K.track; x.beginPath(); x.arc(cx, cy - size * .32, r, 0, 6.283); x.stroke();
      x.strokeStyle = K.key; x.lineCap = 'round'; x.shadowColor = `rgba(${K.accentRGB},.6)`; x.shadowBlur = K.dark ? 24 : 0; x.beginPath(); x.arc(cx, cy - size * .32, r, -Math.PI / 2, -Math.PI / 2 + 6.283 * re * (S.ringValue ?? 1)); x.stroke(); x.restore(); }
    // ondas al aterrizar
    const land = at + dur * .55; for (let k = 0; k < 3; k++) { const q = ramp(lt, land + k * .18, land + k * .18 + 1.2); if (q <= 0 || q >= 1) continue; x.save(); x.globalAlpha = (1 - q) * .35; x.strokeStyle = K.key; x.lineWidth = 3; x.beginPath(); x.ellipse(cx, cy - size * .32, 380 + q * 260, 200 + q * 140, 0, 0, 6.283); x.stroke(); x.restore(); }
    A.halo(x, cx, cy - size * .3, 520, K.glowRGB, K.dark ? .22 : .3);
    kicker(c, S.kicker, 0);
    const { a, e } = ent(lt, at - .12, 'heavy');
    x.save(); x.globalAlpha *= a; x.translate(0, 60 * (1 - e));
    const fs = fitSize(x, (S.prefix || '') + fmtNum(S.value, S.decimals || 0) + (S.suffix || ''), q => FW(700, q), side ? 1000 : S.ring ? 560 : 1650, size, 80);
    sweepLayer(x, q => odometer(q, v, cx, cy, fs, { prefix: S.prefix, suffix: S.suffix, final: S.value, decimals: S.decimals, speed: sp, color: K.ink, sufColor: K.key, sufFont: FS(fs * .62, 500) }), ramp(lt, at + dur * .75, at + dur * .75 + .9), { alpha: K.dark ? .7 : .55, color: K.dark ? '255,255,255' : '160,200,255' });
    x.restore();
    if (S.label) { setF(x, FW(600, 48)); x.fillStyle = K.muted; riseText(x, S.label, cx, cy + 110, lt, at + .35, { size: 48, align: 'center', stagger: .05 }); }
  };

  // ---------- foto: tarjeta flotante con 2.5D dentro ----------
  function photoCard(c, src, X, Y, w, h, o = {}) {
    const { ctx: x, lt, dur } = c, im = imgCache(src), at = o.at ?? .05, { a, e } = ent(lt, at, 'default'); if (a <= 0) return;
    const rot = (o.rot ?? -2.5) * (1 - e) * Math.PI / 180;
    x.save(); x.globalAlpha *= a; x.translate(X + w / 2, Y + h / 2 + 70 * (1 - e)); x.rotate(rot); x.scale(.94 + .06 * e, .94 + .06 * e); x.translate(-(X + w / 2), -(Y + h / 2));
    A.softShadow(x, X, Y, w, h, 30, { alpha: K.dark ? .55 : .25, color: K.shadow, blur: 80, dy: 34 });
    x.save(); A.rrectPath(x, X, Y, w, h, 30); x.clip(); x.fillStyle = '#111'; x.fillRect(X, Y, w, h);
    if (im) parallaxPhoto(x, im, lt, dur, [X, Y, w, h], { focus: o.focus || [.5, .4], amount: .1, subject: o.subject });
    x.restore();
    x.save(); A.rrectPath(x, X, Y, w, h, 30); x.lineWidth = 1.5; x.strokeStyle = K.dark ? 'rgba(255,255,255,.22)' : 'rgba(255,255,255,.9)'; x.stroke(); x.restore();
    A.lightSweep(x, q => A.rrectPath(q, X, Y, w, h, 30), [X, Y, w, h], ramp(lt, at + .35, at + 1.4), { alpha: .28 });
    x.restore();
    credit(x, creditOf(src), prog(lt, .6, .8));
  }
  /** Ken Burns con paralaje 2.5D: fondo + sujeto separado con máscara suave elíptica que se mueve/escala distinto. */
  function parallaxPhoto(x, im, lt, dur, box, o = {}) {
    const [X, Y, w, h] = box, f = o.focus || [.5, .45], A0 = o.amount ?? .12, u = A.easeInOutSine((lt + .4) / (dur + .8));
    const base = Math.max(w / im.width, h / im.height), mv = o.move || 'in';
    const z0 = mv === 'out' ? 1 + A0 : 1.02, z1 = mv === 'out' ? 1.02 : 1 + A0, z = z0 + (z1 - z0) * u;
    const pan = mv === 'left' ? -1 : mv === 'right' ? 1 : 0, panX = pan * w * .04 * (u - .5), panY = -h * .012 * (u - .5);
    const layer = (zz, k) => { const iw = im.width * base * zz, ih = im.height * base * zz, cx = X + w / 2 - (f[0] - .5) * iw * .35 + panX * k, cy = Y + h / 2 - (f[1] - .5) * ih * .35 + panY * k;
      return [Math.min(X, Math.max(X + w - iw, cx - iw / 2)), Math.min(Y, Math.max(Y + h - ih, cy - ih / 2)), iw, ih]; };
    const [ax, ay, aw, ah] = layer(z, 1); x.drawImage(im, ax, ay, aw, ah);
    if (o.subject !== false) {
      // capa del sujeto: 4–7 % más cerca, se mueve 1.8× → sensación de profundidad
      const sz = z * (1.035 + .035 * u), [bx, by, bw, bh] = layer(sz, 1.8), sub = o.subject || [f[0], f[1], .3, .4];
      const s = A.scratch('subj', Math.ceil(w), Math.ceil(h)); s.drawImage(im, bx - X, by - Y, bw, bh);
      s.globalCompositeOperation = 'destination-in'; s.save(); s.translate(sub[0] * w, sub[1] * h); s.scale(1, sub[3] / sub[2]);
      const R = sub[2] * w, g = s.createRadialGradient(0, 0, R * .55, 0, 0, R); g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)'); s.fillStyle = g; s.fillRect(-R, -R, 2 * R, 2 * R); s.restore();
      x.drawImage(s.canvas, X, Y);
    }
  }
  SC.photo = {
    cam: false, draw(c) {
      const { ctx: x, S, lt, dur, j } = c, raw = imgCache(S.src);
      if (!raw) { setF(x, FW(500, 30)); x.fillStyle = K.muted; x.textAlign = 'center'; x.fillText('Cargando foto…', W / 2, H / 2); return; }
      const im = S.filter && typeof FILTERS !== 'undefined' && FILTERS[S.filter] ? proc(S.src, FILTERS[S.filter]) : raw, ar = im.width / im.height, style = S.style || (ar < 1.1 ? 'card' : 'full');
      if (style === 'full') {
        // cámara propia: un poco de giro 2.5D al entrar
        x.save(); const e = Motion.step(lt, 'heavy'); x.translate(W / 2, H / 2); x.scale(1.06 - .06 * e, 1.06 - .06 * e); x.translate(-W / 2, -H / 2);
        parallaxPhoto(x, im, lt, dur, [-20, -20, W + 40, H + 40], { focus: S.focus, amount: S.amount ?? .14, move: S.move, subject: S.subject });
        x.restore();
        if (S.rings) soundRings(x, S.rings[0] * W, S.rings[1] * H, lt, S.ringsAt ?? .3);
        if (S.hud) hud(c, S.hud, 0, 0, W, H);
        if (S.tint !== false) { const g = x.createLinearGradient(0, H * .45, 0, H); g.addColorStop(0, 'rgba(3,7,19,0)'); g.addColorStop(1, 'rgba(3,7,19,.78)'); x.fillStyle = g; x.fillRect(0, H * .45, W, H * .55);
          const g2 = x.createLinearGradient(0, 0, 0, 300); g2.addColorStop(0, 'rgba(3,7,19,.5)'); g2.addColorStop(1, 'rgba(3,7,19,0)'); x.fillStyle = g2; x.fillRect(0, 0, W, 300); }
        A.lightSweep(x, q => { q.beginPath(); q.rect(0, 0, W, H); }, [0, 0, W, H], ramp(lt, .25, 1.6), { alpha: .14, width: .3 });
      } else {
        // tarjeta flotante + bloque de texto editorial a la derecha
        const ch = 640, cw = Math.min(900, ch * ar), X = S.name ? 150 : W / 2 - cw / 2, Y = 130;
        x.save(); const bgc = proc(S.src, 'blur(40px) brightness(.45) saturate(1.2)'); if (bgc && K.dark) { x.globalAlpha = .55; kenBurns(x, bgc, lt, dur, { move: 'in', amount: .08 }); x.globalAlpha = 1; } x.restore();
        // empuje de cámara hacia un detalle de la tarjeta, pegado a una palabra (p. ej. el águila del códice)
        const pu = S.push ? A.easeInOutCubic(ramp(lt, stepAt(c, S.push), stepAt(c, S.push) + (S.push.dur ?? 1.2))) : 0;
        x.save(); if (pu > 0) { const px = X + (S.push.to || [.5, .5])[0] * cw, py = Y + (S.push.to || [.5, .5])[1] * ch, z = 1 + ((S.push.scale ?? 1.6) - 1) * pu; x.translate(px, py); x.scale(z, z); x.translate(-px + (W * .5 - px) * .35 * pu / z, -py + (H * .38 - py) * .35 * pu / z); }
        photoCard(c, S.src, X, Y, cw, ch, { focus: S.focus, subject: S.subject });
        if (S.hud) hud(c, S.hud, X, Y, cw, ch);
        x.restore();
        if (S.rings) soundRings(x, X + S.rings[0] * cw, Y + S.rings[1] * ch, lt, S.ringsAt ?? .3);
        if (S.name) {
          const tx = X + cw + 110, { a, e } = ent(lt, .35, 'default'); x.save(); x.globalAlpha *= a * (1 - pu); x.translate(60 * pu, 0);
          x.fillStyle = K.key; x.fillRect(tx, 300, 90 * A.easeInOutExpo(ramp(lt, .35, 1)), 6);
          const fs = fitSize(x, S.name, q => FW(700, q), W - tx - 110, 96, 50); setF(x, FW(700, fs), -fs * .02); x.fillStyle = K.ink;
          riseText(x, S.name, tx, 300 + fs + 30, lt, .4, { size: fs, stagger: .07, preset: 'heavy' });
          if (S.role) { setF(x, FS(46, 500)); x.fillStyle = K.key; riseText(x, S.role, tx, 300 + fs + 110, lt, .6, { size: 46, stagger: .05 }); }
          x.restore();
        }
      }
      if (S.place) { const { a, e } = ent(lt, .3, 'snappy'); x.save(); x.translate(-30 * (1 - e), 0); pill(x, S.place, 110, 112, { size: 26, w: 600, dot: true, a, dotColor: K.key }); x.restore(); }
      if (S.name && style === 'full') { const { a, e } = ent(lt, S.nameAt ?? .45, 'default'); x.save(); x.translate(0, 30 * (1 - e)); const w = pill(x, S.name, 110, 196, { size: 34, w: 700, a }); if (S.role) pill(x, S.role, 110 + w + 14, 196, { size: 26, w: 500, a: ent(lt, (S.nameAt ?? .45) + .15, 'snappy').a, color: K.muted }); x.restore(); }
      if (S.date) { const { a, e } = ent(lt, S.dateAt ?? .2, 'heavy'); x.save(); x.globalAlpha *= a; x.translate(0, 50 * (1 - e)); setF(x, FW(800, 200), -6); x.fillStyle = '#fff'; x.textAlign = 'right'; x.shadowColor = 'rgba(0,0,0,.5)'; x.shadowBlur = 40;
        odometer(x, Math.round((S.dateFrom ?? S.date - 30) + (S.date - (S.dateFrom ?? S.date - 30)) * A.easeOutExpo(ramp(lt, S.dateAt ?? .2, (S.dateAt ?? .2) + 1.1))), W - 120, 330, 200, { sep: '', align: 'right', color: '#fff', final: S.date }); x.restore(); }
      credit(x, S.credit || creditOf(S.src), prog(lt, .5, .8));
    }
  };
  SC.image = SC.photo;
  /** Contorno tipo HUD con esquinas que se dibujan alrededor de un objeto de la foto + rótulo de vidrio. box normalizada. */
  function hud(c, o, X, Y, w, h) {
    const { ctx: x, lt } = c, at = stepAt(c, o), u = A.easeOutCubic(ramp(lt, at, at + .6)); if (u <= 0) return;
    const bx = X + o.box[0] * w, by = Y + o.box[1] * h, bw = o.box[2] * w, bh = o.box[3] * h, col = K.dark || true ? '140,185,255' : K.accentRGB;
    x.save(); x.globalAlpha *= cl(u * 3); A.holoOutline(x, bx, by, bw, bh, u, { color: '255,255,255', width: 5, corner: .22 }); A.holoOutline(x, bx, by, bw, bh, u, { color: col, width: 2, corner: .22 });
    if (u > .6) { x.globalAlpha = cl((u - .6) / .2) * .5; x.strokeStyle = `rgba(${col},.6)`; x.lineWidth = 1.2; x.setLineDash([6, 8]); x.strokeRect(bx, by, bw, bh); x.setLineDash([]); }
    x.restore();
    if (o.label) { const { a, e } = ent(lt, at + .3, 'snappy'); x.save(); x.translate(0, 14 * (1 - e)); pill(x, o.label, o.side === 'l' ? bx - 18 : bx + bw + 18, by + 34, { size: 30, w: 600, a, align: o.side === 'l' ? 'right' : 'left', dot: true }); if (o.sub) pill(x, o.sub, o.side === 'l' ? bx - 18 : bx + bw + 18, by + 100, { size: 26, w: 500, a: ent(lt, at + .5, 'snappy').a, align: o.side === 'l' ? 'right' : 'left', color: K.muted }); x.restore(); }
  }
  function soundRings(x, X, Y, lt, at) {
    for (let k = 0; k < 6; k++) { const q = ((lt - at - k * .28) % 1.7) / 1.7; if (lt - at - k * .28 < 0 || q < 0) continue;
      x.save(); x.globalCompositeOperation = 'lighter'; x.globalAlpha = (1 - q) * .55; x.strokeStyle = '#fff'; x.lineWidth = 6 * (1 - q) + 1; x.beginPath(); x.arc(X, Y, 60 + q * 520, 0, 6.283); x.stroke(); x.restore(); }
  }

  // ---------- gallery: carrusel 2.5D de fotos que pasa rápido (montaje del gancho) ----------
  SC.gallery = {
    cam: false, draw(c) {
      const { ctx: x, S, lt, dur } = c, items = S.items || [], n = items.length; if (!n) return;
      const speed = S.speed ?? (n / Math.max(1.2, dur)), pos = A.easeInOutSine(ramp(lt, 0, dur)) * (n - 1) * (S.span ?? 1) + .0, cw = S.w || 760, ch = S.h || 520;
      const v = Math.abs(A.vel(A.easeInOutSine, ramp(lt, 0, dur)) * (n - 1) / dur) * (cw + 80) / 60;
      const order = items.map((src, i) => ({ src, i, d: i - pos })).sort((a, b) => Math.abs(b.d) - Math.abs(a.d));
      order.forEach(o => {
        const d = o.d; if (Math.abs(d) > 2.6) return; const z = 1 / (1 + Math.abs(d) * .32), X = W / 2 + d * (cw * .72) * z, Y = 440 + Math.abs(d) * 26, rot = -d * .06;
        const im = imgCache(o.src); x.save(); x.translate(X, Y); x.rotate(rot); x.scale(z, z); x.globalAlpha = cl(1.6 - Math.abs(d) * .55);
        A.softShadow(x, -cw / 2, -ch / 2, cw, ch, 28, { alpha: .5, color: '0,0,0', blur: 70, dy: 30 });
        x.save(); A.rrectPath(x, -cw / 2, -ch / 2, cw, ch, 28); x.clip(); x.fillStyle = '#111'; x.fillRect(-cw / 2, -ch / 2, cw, ch);
        if (im) { const s = A.scratch('gal', cw, ch); parallaxPhoto(s, im, lt + o.i, dur + 2, [0, 0, cw, ch], { focus: (S.focus || [])[o.i] || [.5, .42], amount: .08, subject: false }); A.whip(x, s.canvas, -cw / 2, -ch / 2, cw, ch, Math.min(90, v * .7) * (Math.abs(d) < 1.2 ? 1 : .6), 0); }
        if (Math.abs(d) > .5) { x.fillStyle = `rgba(3,7,19,${Math.min(.6, (Math.abs(d) - .5) * .5)})`; x.fillRect(-cw / 2, -ch / 2, cw, ch); }
        x.restore();
        x.save(); A.rrectPath(x, -cw / 2, -ch / 2, cw, ch, 28); x.lineWidth = 1.5; x.strokeStyle = 'rgba(255,255,255,.25)'; x.stroke(); x.restore();
        x.restore();
      });
      const cr = [...new Set(items.map(creditOf).filter(Boolean))].slice(0, 3).join(' · '); credit(x, cr, prog(lt, .3, .6));
    }
  };

  // ---------- map: d3-geo con vuelos de cámara, países que se dibujan, áreas, rutas con partículas ----------
  const mapCacheV2 = new WeakMap();
  function mapPrep(S) {
    let m = mapCacheV2.get(S); if (m) return m;
    const bList = [S.bounds, S.from, ...(S.cams || []).map(k => k.bounds)].filter(Boolean);
    const all = bList.reduce((u, b) => [[Math.min(u[0][0], b[0][0]), Math.min(u[0][1], b[0][1])], [Math.max(u[1][0], b[1][0]), Math.max(u[1][1], b[1][1])]], bList[0] || [[-120, 10], [-80, 35]]);
    const R = mapRect(S), proj = d3.geoMercator().fitExtent([[R[0], R[1]], [R[0] + R[2], R[1] + R[3]]], { type: 'MultiPoint', coordinates: all });
    const path = d3.geoPath(proj), hlNames = (S.highlight || []).map(s => s.toLowerCase());
    const feats = world.countries.filter(f => hlNames.includes(String(f.properties.name).toLowerCase()));
    m = { proj, R, land: new Path2D(path(world.land)), borders: new Path2D(path(world.borders)), grat: new Path2D(path(d3.geoGraticule().step([10, 10])())),
      hl: feats.map(f => ({ p: new Path2D(path(f)), len: path.measure(f) })),
      P: Object.fromEntries((S.points || []).map(p => [p.name, proj([p.lon, p.lat])])),
      areas: (S.areas || []).map(a => { const pts = a.coords.map(q => proj(q)); const p = new Path2D(); pts.forEach((q, i) => i ? p.lineTo(q[0], q[1]) : p.moveTo(q[0], q[1])); p.closePath();
        let len = 0; for (let i = 1; i <= pts.length; i++) { const p0 = pts[i - 1], p1 = pts[i % pts.length]; len += Math.hypot(p1[0] - p0[0], p1[1] - p0[1]); }
        const cx = pts.reduce((s, q) => s + q[0], 0) / pts.length, cy = pts.reduce((s, q) => s + q[1], 0) / pts.length; return { p, len, cx, cy, pts, o: a }; }) };
    // fotogramas clave de cámara (en píxeles de la proyección base)
    const camOf = b => { const p0 = proj([b[0][0], b[1][1]]), p1 = proj([b[1][0], b[0][1]]), bw = Math.abs(p1[0] - p0[0]), bh = Math.abs(p1[1] - p0[1]);
      return { z: Math.min(R[2] / bw, R[3] / bh), cx: (p0[0] + p1[0]) / 2, cy: (p0[1] + p1[1]) / 2 }; };
    const target = camOf(S.bounds || all);
    m.keys = [];
    if (S.from) m.keys.push(Object.assign({ t: -1 }, camOf(S.from)));
    else if (S.fly !== false) m.keys.push({ t: -1, z: target.z / (S.flyZoom ?? 2.4), cx: target.cx + (S.flyDx ?? 0), cy: target.cy + (S.flyDy ?? 0) });
    m.keys.push(Object.assign({ t: S.fly === false && !S.from ? -1 : (S.flyAt ?? 0), d: S.flyDur ?? 1.5 }, target));
    (S.cams || []).forEach(k => m.keys.push(Object.assign({ t: k.at, d: k.dur ?? 1.4, step: k.step }, camOf(k.bounds))));
    mapCacheV2.set(S, m); return m;
  }
  function mapRect(S) { return S.rect || [90, 120, W - 180, (S.full ? 960 : 680)]; }
  function mapCam(m, lt, stepStarts) {
    let cur = m.keys[0]; let z = cur.z, cx = cur.cx, cy = cur.cy, speed = 0;
    for (let i = 1; i < m.keys.length; i++) {
      const k = m.keys[i], t0 = k.step != null ? (stepStarts[k.step] ?? 1e9) + (k.t || 0) : k.t; if (lt <= t0) break;
      const u = ramp(lt, t0, t0 + k.d), e = A.easeInOutExpo(u);
      // vuelo: zoom en escala logarítmica, centro interpolado con la misma curva
      z = Math.exp(Math.log(z) + (Math.log(k.z) - Math.log(z)) * e); cx = cx + (k.cx - cx) * e; cy = cy + (k.cy - cy) * e;
      speed = Math.max(speed, A.vel(A.easeInOutExpo, u) / k.d);
    }
    return { z, cx, cy, speed };
  }
  SC.map = {
    cam: false, draw(c) {
      const { ctx: x, S, lt, dur } = c;
      x.fillStyle = K.sea; x.globalAlpha = S.sea === false ? 0 : (K.dark ? .55 : .9); x.fillRect(0, 0, W, H); x.globalAlpha = 1;
      if (!world) { loadWorld(); setF(x, FW(500, 30)); x.fillStyle = K.muted; x.textAlign = 'center'; x.fillText('Cargando mapa…', W / 2, H / 2); return; }
      const m = mapPrep(S), cam = mapCam(m, lt, c.stepStarts), R = m.R, CX = R[0] + R[2] / 2, CY = R[1] + R[3] / 2;
      const drift = 1 + .025 * A.easeInOutSine(lt / Math.max(2, dur));
      const T = (q, dt = 0) => { const k = dt ? mapCam(m, lt + dt, c.stepStarts) : cam; q.translate(CX, CY); q.scale(k.z * drift, k.z * drift); q.translate(-k.cx, -k.cy); return k.z * drift; };
      const paint = (q, dt) => { q.save(); const z = T(q, dt); drawMapLayers(q, c, m, z, lt + dt); q.restore(); };
      // motion blur real en los vuelos rápidos (acumulación de subcuadros)
      const fps = window.__fps || 60, n = cam.speed > 1.2 ? 5 : cam.speed > .5 ? 3 : 1;
      if (n > 1) A.accumulate(x, n, .6, fps, (q, dt) => paint(q, dt)); else paint(x, 0);
      // capa de etiquetas (no se escalan) y puntos
      const zz = cam.z * drift, toS = p => [CX + (p[0] - cam.cx) * zz, CY + (p[1] - cam.cy) * zz];
      drawMapPoints(x, c, m, toS);
      if (S.title) { kicker(c, S.title, .1); }
      (S.labels || []).forEach(L => { const at = stepAt(c, L), { a, e } = ent(lt, at, 'snappy'); if (a <= 0) return; const p = toS(m.proj([L.lon, L.lat])); x.save(); x.translate(0, 16 * (1 - e)); pill(x, L.text, p[0], p[1], { size: L.size || 28, w: 600, align: 'center', a, color: L.color }); x.restore(); });
      m.areas.forEach(ar => { const o = ar.o; if (!o.label) return; const at = (o.lossWord ? wordT(c, o.lossWord) : stepAt(c, o)) + (o.labelAt ?? .8), { a, e } = ent(lt, at, 'default'); if (a <= 0) return;
        const p = toS([ar.cx + (o.labelDx || 0), ar.cy + (o.labelDy || 0)]); x.save(); x.translate(0, 20 * (1 - e)); pill(x, o.label, p[0], p[1], { size: o.labelSize || 32, w: 700, align: 'center', a, solid: o.loss ? K.loss : K.hi, color: o.loss || !K.dark ? '#fff' : '#03132E' }); x.restore(); });
    }
  };
  function stepAt(c, o) { if (o.word) return wordT(c, o.word) + (o.at || 0); return (o.at != null ? o.at : 0) + (o.step ? (c.stepStarts[o.step] ?? 1e9) : 0); }
  /** Tiempo local (lt) en que se dice una palabra dentro de la escena (para sincronizar elementos a la voz). */
  function wordT(c, w) {
    const n = norm(w); let k = c.j + 1; while (k < P.length && !P[k].scene) k++;
    for (let i = c.j; i < k; i++) { const ws = phraseWords(i); for (const q of ws) if (norm(q.w) === n || norm(q.w).startsWith(n)) return q.s - c.s0; }
    return 1e9;
  }
  function drawMapLayers(x, c, m, z, lt) {
    const S = c.S;
    x.lineJoin = 'round';
    // retícula
    x.strokeStyle = K.dark ? 'rgba(140,170,255,.07)' : 'rgba(47,107,255,.08)'; x.lineWidth = 1.2 / z; x.stroke(m.grat);
    // tierra como losa 2.5D: sombra/canto + relleno con degradado + bordes finos
    x.save(); x.translate(0, 9 / z); x.fillStyle = K.slab; x.fill(m.land); x.restore();
    x.save(); x.fillStyle = K.land; x.fill(m.land); x.restore();
    x.strokeStyle = K.landEdge; x.lineWidth = 1.1 / z; x.globalAlpha = .85; x.stroke(m.borders); x.globalAlpha = 1;
    // países resaltados: el contorno se dibuja (trim path) y el relleno se enciende con brillo
    const hAt = S.highlightAt ?? .15, hd = S.highlightDur ?? 1.3;
    m.hl.forEach(h => {
      const u = A.easeInOutCubic(ramp(lt, hAt, hAt + hd)), f = A.easeOutCubic(ramp(lt, hAt + hd * .55, hAt + hd + .5)); if (u <= 0) return;
      x.save(); x.fillStyle = K.hi; x.globalAlpha = .82 * f;
      if (K.dark) { x.shadowColor = `rgba(${K.hiRGB},.75)`; x.shadowBlur = 40; }
      x.fill(h.p); x.restore();
      x.save(); x.strokeStyle = K.dark ? '#fff' : K.hi; x.lineWidth = 3 / z; x.setLineDash([h.len * u, h.len]); x.globalAlpha = .95; x.stroke(h.p); x.setLineDash([]);
      if (K.dark) { x.shadowColor = `rgba(${K.hiRGB},1)`; x.shadowBlur = 18; x.stroke(h.p); } x.restore();
      // destello que recorre el país encendido
      const su = ramp(lt, hAt + hd, hAt + hd + 1.3); if (su > 0 && su < 1) { x.save(); x.clip(h.p); x.globalCompositeOperation = 'lighter'; const tr = x.getTransform(); x.setTransform(1, 0, 0, 1, 0, 0);
        const cx0 = -400 + su * (W + 800), g = x.createLinearGradient(cx0 - 260, 0, cx0 + 260, H * .3); g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(.5, 'rgba(255,255,255,.42)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, W, H); x.setTransform(tr); x.restore(); }
      if (S.pulse !== false && f >= 1) { const q = ((lt - hAt - hd - .5) % 2.4) / 2.4; x.save(); x.globalAlpha = .25 * (1 - q); x.fillStyle = '#fff'; x.globalCompositeOperation = K.dark ? 'lighter' : 'source-over'; x.fill(h.p); x.restore(); }
    });
    // áreas (territorios): se dibujan y, si son pérdida, se separan del país
    m.areas.forEach(ar => {
      const o = ar.o, at = stepAt(c, o), u = A.easeInOutCubic(ramp(lt, at, at + (o.dur ?? 1))); if (u <= 0) return;
      const lossT = o.lossWord ? wordT(c, o.lossWord) + (o.lossAt || 0) : o.lossAt != null ? stepAt(c, { at: o.lossAt, step: o.lossStep }) : null, L = lossT != null ? A.easeInOutCubic(ramp(lt, lossT, lossT + 1.1)) : (o.loss ? 1 : 0);
      x.save(); if (o.clipLand !== false) x.clip(m.land);
      x.translate((o.dx || 0) * L / z, (o.dy ?? -26) * L / z);
      const col = L > 0 ? mixRGB(K.hiRGB, K.lossRGB, L) : K.hiRGB;
      x.fillStyle = `rgba(${col},${(.75 - .25 * L) * A.easeOutCubic(ramp(lt, at + .3, at + 1.2))})`; if (K.dark) { x.shadowColor = `rgba(${col},.7)`; x.shadowBlur = 30; } x.fill(ar.p); x.shadowBlur = 0;
      if (L > 0) { x.save(); x.clip(ar.p); x.strokeStyle = `rgba(255,255,255,${.35 * L})`; x.lineWidth = 3 / z; x.beginPath(); const b = 4000 / z; for (let s = -b; s < b; s += 26 / z) { x.moveTo(ar.cx + s - b, ar.cy - b); x.lineTo(ar.cx + s + b, ar.cy + b); } x.stroke(); x.restore(); }
      x.strokeStyle = '#fff'; x.lineWidth = 2.6 / z; x.setLineDash(L > 0 ? [10 / z, 8 / z] : [ar.len * u, ar.len]); x.stroke(ar.p); x.setLineDash([]);
      x.restore();
    });
    // rutas: se trazan con cometa y luego corren partículas
    const routes = S.routes || [];
    routes.forEach(r => {
      const A0 = m.P[r.from] || (r.fromLL && m.proj(r.fromLL)), B0 = m.P[r.to] || (r.toLL && m.proj(r.toLL)); if (!A0 || !B0) return;
      const at = stepAt(c, r), d = r.dur || 1.4, u = A.easeInOutCubic(ramp(lt, at, at + d)); if (u <= 0) return;
      const mx = (A0[0] + B0[0]) / 2, my = (A0[1] + B0[1]) / 2, dx = B0[0] - A0[0], dy = B0[1] - A0[1], bend = r.bend ?? .22, C = [mx - dy * bend, my + dx * bend];
      const pt = s => [(1 - s) * (1 - s) * A0[0] + 2 * (1 - s) * s * C[0] + s * s * B0[0], (1 - s) * (1 - s) * A0[1] + 2 * (1 - s) * s * C[1] + s * s * B0[1]];
      x.save(); x.lineCap = 'round'; x.beginPath(); for (let s = 0; s <= 1.0001; s += 1 / 80) { if (s > u) break; const p = pt(s); s ? x.lineTo(p[0], p[1]) : x.moveTo(p[0], p[1]); } const tip = pt(u); x.lineTo(tip[0], tip[1]);
      x.strokeStyle = r.color || K.key; x.lineWidth = (r.width || 4) / z; if (r.dashed) x.setLineDash([14 / z, 10 / z]); if (K.dark) { x.shadowColor = `rgba(${K.accentRGB},.9)`; x.shadowBlur = 16; } x.stroke(); x.setLineDash([]); x.shadowBlur = 0;
      if (u < 1) { A.halo(x, tip[0], tip[1], 40 / z, K.dark ? K.accentRGB : K.hiRGB, .9); x.beginPath(); x.arc(tip[0], tip[1], 7 / z, 0, 6.283); x.fillStyle = '#fff'; x.fill(); }
      else if (r.particles !== false) { for (let k = 0; k < 6; k++) { const s = ((lt - at - d) * .45 + k / 6) % 1, p = pt(s); x.globalAlpha = Math.sin(Math.PI * s); x.beginPath(); x.arc(p[0], p[1], 4.5 / z, 0, 6.283); x.fillStyle = '#fff'; x.fill(); } x.globalAlpha = 1; }
      x.restore();
    });
    // destellos de ciudades encendidas (S.lights: [[lon,lat],...])
    (S.lights || []).forEach((q, i) => { const p = m.proj(q), at = (S.lightsAt ?? .4) + i * .045; const { a } = ent(lt, at, 'snappy'); if (a <= 0) return; const tw = .65 + .35 * Math.sin(lt * 3 + i);
      x.save(); x.globalAlpha = a * tw; A.halo(x, p[0], p[1], 26 / z, K.dark ? '255,220,150' : K.hiRGB, .8); x.beginPath(); x.arc(p[0], p[1], 2.6 / z, 0, 6.283); x.fillStyle = '#fff'; x.fill(); x.restore(); });
  }
  function mixRGB(a, b, k) { const A1 = a.split(',').map(Number), B1 = b.split(',').map(Number); return A1.map((v, i) => Math.round(v + (B1[i] - v) * k)).join(','); }
  function drawMapPoints(x, c, m, toS) {
    const { S, lt } = c;
    (S.points || []).forEach((p, i) => {
      const at = stepAt(c, p) + (p.at == null && !p.step ? .35 + i * .12 : 0), { a, e } = ent(lt, at, 'snappy'); if (a <= 0) return;
      const [px, py] = toS(m.P[p.name]), col = (p.lossWord && lt >= wordT(c, p.lossWord)) || (p.lossAt != null && lt >= p.lossAt) ? K.loss : (p.color || (K.dark ? '#fff' : K.hi));
      for (let k = 0; k < 2; k++) { const q = ((lt - at + k * .9) % 1.8) / 1.8; x.save(); x.globalAlpha = a * (1 - q) * .6; x.strokeStyle = col; x.lineWidth = 3; x.beginPath(); x.arc(px, py, 10 + q * 46, 0, 6.283); x.stroke(); x.restore(); }
      x.save(); x.globalAlpha = a; x.translate(px, py); x.scale(.4 + .6 * e, .4 + .6 * e); if (K.dark) A.halo(x, 0, 0, 50, K.accentRGB, .55);
      x.beginPath(); x.arc(0, 0, 11, 0, 6.283); x.fillStyle = col; x.fill(); x.lineWidth = 4; x.strokeStyle = K.dark ? K.sea : '#fff'; x.stroke(); x.restore();
      if (p.label !== false) { const pos = p.pos || 'r', lab = p.label || p.name, off = 30, la = ent(lt, at + .12, 'snappy');
        x.save(); x.translate(pos === 'l' ? 10 * (1 - la.e) : -10 * (1 - la.e), 0);
        pill(x, lab, px + (pos === 'r' ? off : pos === 'l' ? -off : 0), py + (pos === 't' ? -54 : pos === 'b' ? 54 : 0), { size: p.size || 28, w: 600, a: la.a, align: pos === 'r' ? 'left' : pos === 'l' ? 'right' : 'center' }); x.restore(); }
    });
  }

  // ---------- timeline: la cámara recorre una línea de tiempo larga ----------
  SC.timeline = {
    cam: false, draw(c) {
      const { ctx: x, S, lt, dur } = c, ev = S.events || [], yrs = ev.map(e => +String(e.date).replace(/[^\d-]/g, '')), y0 = Math.min(...yrs), y1 = Math.max(...yrs);
      const pxy = S.pxPerYear || 9, X0 = 0, xOf = y => (y - y0) * pxy, total = xOf(y1);
      const tAt = S.travelAt ?? .3, tD = S.travel ?? Math.min(2.4, dur * .6), u = A.easeInOutCubic(ramp(lt, tAt, tAt + tD)), camX = total * u;
      const vel = Math.abs(A.vel(A.easeInOutCubic, ramp(lt, tAt, tAt + tD)) * total / tD / 60);
      const ly = 560, ox = W / 2 - camX - (S.anchor ?? 0);
      if (S.title) kicker(c, S.title, 0);
      // capa de la línea con desenfoque por velocidad
      const s = A.scratch('tl', W, 600); s.translate(ox, -ly + 300);
      s.fillStyle = K.track; s.fillRect(xOf(y0) - 4000, ly - 3, total + 8000, 6);
      const g = s.createLinearGradient(0, 0, total, 0); g.addColorStop(0, K.key); g.addColorStop(1, K.key); s.fillStyle = g; s.fillRect(0, ly - 4, camX, 8);
      const step = S.tick || 10;
      for (let yv = Math.floor((y0 - 200) / step) * step; yv <= y1 + 200; yv += step) { const X = xOf(yv), major = yv % (step * 5) === 0; s.fillStyle = K.ink; s.globalAlpha = major ? .7 : .3; s.fillRect(X - 1, ly + 16, 2, major ? 26 : 14);
        if (major) { setF(s, FW(600, 24)); s.textAlign = 'center'; s.textBaseline = 'top'; s.globalAlpha = .55; s.fillText(String(yv), X, ly + 50); } }
      s.globalAlpha = 1; s.setTransform(1, 0, 0, 1, 0, 0); s.globalCompositeOperation = 'destination-in'; const fg = s.createLinearGradient(0, 0, W, 0); fg.addColorStop(0, 'rgba(0,0,0,0)'); fg.addColorStop(.1, '#000'); fg.addColorStop(.9, '#000'); fg.addColorStop(1, 'rgba(0,0,0,0)'); s.fillStyle = fg; s.fillRect(0, 0, W, 600);
      A.whip(x, s.canvas, 0, ly - 300, W, 600, Math.min(120, vel * .7), 0);
      // eventos: nodos en la línea + rótulo debajo
      ev.forEach((e, i) => {
        const X = ox + xOf(yrs[i]), near = cl(1 - Math.abs(X - W / 2) / 700), at = (e.at ?? (i === 0 ? .1 : tAt + tD * (xOf(yrs[i]) / Math.max(1, total)) - .25)), { a, e: ee } = ent(lt, at, 'default'); if (a <= 0 || X < -400 || X > W + 400) return;
        x.save(); x.globalAlpha *= a;
        A.halo(x, X, ly, 120, K.accentRGB, (K.dark ? .55 : .35) * near);
        x.beginPath(); x.arc(X, ly, (14 + 10 * near) * (.5 + .5 * ee), 0, 6.283); x.fillStyle = K.key; x.fill(); x.lineWidth = 5; x.strokeStyle = K.dark ? K.sea : '#fff'; x.stroke();
        x.translate(0, 16 * (1 - ee)); pill(x, `${yearLabel(yrs[i])} · ${e.label || ''}`, X, ly + 118, { size: 30, w: 600, align: 'center', a: cl(.35 + near), dot: true, dotColor: K.key });
        x.restore();
      });
      // año actual gigante: rueda mientras la cámara viaja
      { const yr = Math.round(y0 + (y1 - y0) * u), { a, e } = ent(lt, 0, 'heavy'); x.save(); x.globalAlpha *= a; x.translate(0, 40 * (1 - e));
        sweepLayer(x, q => odometer(q, yr, W / 2, 440, 190, { final: y1, sep: '', speed: vel / 25, color: K.ink }), ramp(lt, tAt + tD - .1, tAt + tD + .8), { alpha: .6, color: K.dark ? '255,255,255' : '150,190,255' }); x.restore(); }
      // contador del tramo ("300 años")
      if (S.span) { const v = Math.round((S.span.value ?? (y1 - y0)) * u), { a, e } = ent(lt, tAt, 'snappy'); x.save(); x.globalAlpha *= a; x.translate(0, 20 * (1 - e));
        odometer(x, v, W / 2, 230, 78, { final: S.span.value ?? (y1 - y0), suffix: ' ' + (S.span.suffix || 'años'), sufFont: FS(70, 500), sufColor: K.key, color: K.key, speed: vel / 30, sep: '' });
        x.restore(); }
    }
  };

  // ---------- bars: crecen con resorte y escalonado; valores que cuentan; el dato clave con destello ----------
  SC.bars = function (c) {
    const { ctx: x, S, lt } = c, items = S.items || [], n = items.length, max = Math.max(...items.map(i => i.value), 1);
    kicker(c, S.title, 0);
    const top = 190, rowH = Math.min(140, 560 / Math.max(n, 1)), L = 560, Rr = W - 300, bh = Math.min(70, rowH * .56);
    // eje que se dibuja
    const ax = A.easeInOutExpo(ramp(lt, .05, .6)); x.fillStyle = K.track; x.fillRect(L - 2, top - 20, 3, (rowH * n + 20) * ax);
    items.forEach((it, i) => {
      const at = .15 + i * (S.stagger ?? .12), { a, e } = ent(lt, at, 'snappy'), g = A.easeOutBack(ramp(lt, at + .05, at + .95), 1.2), y = top + i * rowH + rowH / 2; if (a <= 0) return;
      const hl = !!it.highlight, bw = Math.max(bh, (Rr - L) * it.value / max * g);
      x.save(); x.globalAlpha *= a;
      setF(x, FW(hl ? 700 : 600, 42)); x.fillStyle = hl ? K.ink : K.muted; x.textAlign = 'right'; x.textBaseline = 'middle'; x.fillText(it.label, L - 34 - 20 * (1 - e), y);
      A.rrectPath(x, L, y - bh / 2, bw, bh, bh / 2);
      if (hl) { const gr = x.createLinearGradient(L, 0, L + bw, 0); gr.addColorStop(0, K.key); gr.addColorStop(1, K.dark ? '#9CC0FF' : '#5C96FF'); x.fillStyle = gr; if (K.dark || K === SURF.light) { x.shadowColor = `rgba(${K.accentRGB},.55)`; x.shadowBlur = 30; } }
      else x.fillStyle = K.track.replace(/[\d.]+\)$/, K.dark ? '.22)' : '.12)');
      x.fill(); x.shadowBlur = 0;
      if (hl) A.lightSweep(x, q => A.rrectPath(q, L, y - bh / 2, bw, bh, bh / 2), [L, y - bh / 2, bw, bh], ramp(lt, at + .9, at + 1.8), { alpha: .5 });
      const vv = it.value * A.easeOutExpo(ramp(lt, at + .05, at + 1.0));
      setF(x, FW(700, 44)); x.fillStyle = hl ? K.key : K.ink; x.textAlign = 'left'; x.fillText((S.prefix || '') + fmtNum(vv, S.decimals || 0) + (S.suffix || ''), L + bw + 26, y + 2);
      x.restore();
    });
    if (S.source) { setF(x, FW(500, 24)); x.fillStyle = K.muted; x.textAlign = 'right'; x.textBaseline = 'alphabetic'; x.globalAlpha = prog(lt, .8, .6) * .9; x.fillText(S.source, W - 120, top + rowH * n + 40); x.globalAlpha = 1; }
  };

  // ---------- quote: tipografía cinética editorial, palabras clave en cursiva de acento ----------
  SC.quote = function (c) {
    const { ctx: x, S, lt, dur } = c, hasPh = !!S.photo, X0 = hasPh ? 860 : 200, maxW = hasPh ? 920 : 1520;
    if (hasPh) photoCard(c, S.photo, 140, 150, 600, 620, { focus: S.focus });
    const key = S.key ? norm(S.key) : null, words = String(S.text || '').split(' ');
    let size = S.size || (hasPh ? 96 : 128), lines; for (; size >= 44; size -= 4) { x.font = FW(700, size); lines = wrapMixed(x, words, key, size, maxW); if (lines.length <= 3) break; }
    const lh = size * 1.14, top = (c.capOff ? 560 : 430) - (lines.length - 1) * lh / 2 + size * .3; let k = 0;
    const { a: qa, e: qe } = ent(lt, 0, 'heavy'); x.save(); x.globalAlpha *= qa; setF(x, FS(300, 500)); x.fillStyle = K.key; x.textBaseline = 'alphabetic'; x.textAlign = 'left';
    if (K.dark) { x.shadowColor = `rgba(${K.accentRGB},.5)`; x.shadowBlur = 50; } x.translate(X0 - 30, top - size * .9); x.scale(.7 + .3 * qe, .7 + .3 * qe); x.fillText('“', 0, 0); x.restore();
    sweepLayer(x, q => { lines.forEach((L, li) => { let px = X0; const y = top + li * lh; L.items.forEach(it => { const t0 = .2 + k * (S.stagger ?? .055), { a, e } = ent(lt, t0, 'default'); k++;
      q.save(); q.font = it.font; q.letterSpacing = it.ls + 'px'; q.beginPath(); q.rect(px - 20, y - size * 1.2, it.w + 40, size * 1.55); q.clip(); q.globalAlpha *= a; q.fillStyle = it.key ? K.key : K.ink; q.textAlign = 'left'; q.textBaseline = 'alphabetic'; q.fillText(it.w0, px, y + (1 - e) * size * 1.1); q.restore(); px += it.w + it.sp; }); }); },
      ramp(lt, .2 + words.length * .055 + .2, .2 + words.length * .055 + 1.1), { alpha: K.dark ? .5 : .45, color: K.dark ? '255,255,255' : '150,190,255' });
    if (S.author) { const { a, e } = ent(lt, .5 + words.length * .055, 'snappy'); x.save(); x.translate(-20 * (1 - e), 0); x.fillStyle = K.key; x.globalAlpha *= a; x.fillRect(X0, top + lines.length * lh - 10, 70 * e, 4); pill(x, S.author, X0 + 90, top + lines.length * lh - 8, { size: 28, w: 600, a, color: K.muted }); x.restore(); }
  };

  // ---------- list: filas de vidrio escalonadas; la del momento se resalta y las anteriores se atenúan ----------
  SC.list = function (c) {
    const { ctx: x, S, lt } = c, items = (S.items || []).map(it => typeof it === 'string' ? { text: it } : it), n = items.length; kicker(c, S.title, 0);
    const sc = schedule(c, items, .35, .25), rowH = Math.min(124, 580 / Math.max(n, 1)), gap = 18, rw = S.photo ? 980 : 1240, X = S.photo ? 120 : W / 2 - rw / 2, top = 455 - (n * rowH + (n - 1) * gap) / 2;
    if (S.photo) photoCard(c, S.photo, 1180, 150, 620, 620, { focus: S.focus });
    let cur = -1; sc.forEach((t0, i) => { if (lt >= t0) cur = i; });
    items.forEach((it, i) => {
      const t0 = sc[i]; if (!(lt >= t0)) return; const { a, e } = ent(lt, t0, 'default'), y = top + i * (rowH + gap), active = i === cur, dim = !active && cur > i ? .62 : 1;
      x.save(); x.globalAlpha *= a * dim; x.translate(80 * (1 - A.easeOutBack(cl((lt - t0) / .55), 1.3)), 0);
      A.glassCard(x, X, y, rw, rowH, { r: rowH / 2.4, dark: K.dark, tint: active ? K.accentRGB : K.tint, tintA: active ? (K.dark ? .22 : .16) : (K.dark ? .08 : .7), blur: 20, shadowA: K.dark ? .35 : .1 });
      if (active) { x.save(); A.rrectPath(x, X, y, rw, rowH, rowH / 2.4); x.lineWidth = 2.5; x.strokeStyle = K.key; x.globalAlpha *= .9; x.stroke(); x.restore(); }
      const cx = X + rowH * .55, cy = y + rowH / 2, r = rowH * .28, bad = it.icon === 'x';
      x.beginPath(); x.arc(cx, cy, r, 0, 6.283); x.fillStyle = bad ? K.loss : K.key; x.fill();
      const du = A.easeOutCubic(ramp(lt, t0 + .15, t0 + .5)); x.strokeStyle = K.key === '#FFFFFF' && !bad ? '#1A47E0' : '#fff'; x.lineWidth = r * .22; x.lineCap = 'round'; x.lineJoin = 'round'; x.beginPath();
      if (bad) { x.setLineDash([r * 2.3 * du, 99]); x.moveTo(cx - r * .4, cy - r * .4); x.lineTo(cx + r * .4, cy + r * .4); x.moveTo(cx + r * .4, cy - r * .4); x.lineTo(cx - r * .4, cy + r * .4); }
      else if (it.icon === 'check') { x.setLineDash([r * 1.8 * du, 99]); x.moveTo(cx - r * .45, cy); x.lineTo(cx - r * .1, cy + r * .35); x.lineTo(cx + r * .48, cy - r * .35); }
      x.stroke(); x.setLineDash([]);
      if (!bad && it.icon !== 'check') { setF(x, FW(700, r * 1.1)); x.fillStyle = K.key === '#FFFFFF' ? '#1A47E0' : '#fff'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(it.num || String(i + 1), cx, cy + 2); }
      const fs = fitSize(x, it.text, q => FW(active ? 700 : 600, q), rw - rowH * 1.4, Math.min(52, rowH * .42), 26); setF(x, FW(active ? 700 : 600, fs)); x.fillStyle = K.ink;
      riseText(x, it.text, X + rowH * 1.05, cy + fs * .36, lt, t0 + .08, { size: fs, stagger: .035, preset: 'snappy' });
      x.restore();
    });
  };

  // ---------- flow: nodos de vidrio, conectores curvos que se dibujan y por los que corren partículas ----------
  SC.flow = function (c) {
    const { ctx: x, S, lt } = c, nodes = S.nodes || [], n = nodes.length; kicker(c, S.title, 0); if (!n) return;
    const bw = Math.min(440, (W - 260) / n - 80), bh = 230, gap = (W - 240 - bw * n) / Math.max(n - 1, 1), y = 455 - bh / 2;
    const sc = schedule(c, nodes, .5, .15);
    nodes.forEach((nd, i) => { if (i === 0) return; const t0 = Math.max(sc[i], sc[i - 1]) - .05; if (!(lt >= t0)) return;
      const x0 = 120 + (i - 1) * (bw + gap) + bw, x1 = x0 + gap, yy = y + bh / 2, u = A.easeInOutCubic(ramp(lt, t0, t0 + .5));
      const pt = q => [x0 + (x1 - x0) * q, yy - Math.sin(Math.PI * q) * 40];
      x.save(); x.strokeStyle = K.key; x.lineWidth = 5; x.lineCap = 'round'; x.beginPath(); for (let q = 0; q <= u + 1e-6; q += .02) { const p = pt(Math.min(q, u)); q ? x.lineTo(p[0], p[1]) : x.moveTo(p[0], p[1]); }
      if (K.dark) { x.shadowColor = `rgba(${K.accentRGB},.8)`; x.shadowBlur = 16; } x.stroke(); x.restore();
      if (u >= 1) for (let k = 0; k < 4; k++) { const q = ((lt - t0) * .7 + k / 4) % 1, p = pt(q); x.save(); x.globalAlpha = Math.sin(Math.PI * q); A.halo(x, p[0], p[1], 22, K.accentRGB, .8); x.beginPath(); x.arc(p[0], p[1], 5, 0, 6.283); x.fillStyle = '#fff'; x.fill(); x.restore(); }
      const lab = (S.arrows || [])[i - 1]; if (lab) pill(x, lab, (x0 + x1) / 2, yy - 90, { size: 26, w: 600, align: 'center', a: ent(lt, t0 + .3, 'snappy').a, color: K.muted });
    });
    nodes.forEach((nd, i) => { const t0 = sc[i]; if (!(lt >= t0)) return; const { a, e } = ent(lt, t0, 'default'), bx = 120 + i * (bw + gap), by = y + 50 * (1 - A.easeOutBack(cl((lt - t0) / .6), 1.4)), hl = !!nd.highlight;
      x.save(); x.globalAlpha *= a;
      if (hl) { A.softShadow(x, bx, by, bw, bh, 34, { alpha: .35, color: K.shadow, blur: 60, dy: 24 }); A.rrectPath(x, bx, by, bw, bh, 34); const g = x.createLinearGradient(bx, by, bx + bw, by + bh); g.addColorStop(0, '#2F6BFF'); g.addColorStop(1, '#6FA2FF'); x.fillStyle = g; x.fill();
        const pq = ((lt - t0) % 2) / 2; x.strokeStyle = `rgba(92,150,255,${.6 * (1 - pq)})`; x.lineWidth = 3; A.rrectPath(x, bx - pq * 18, by - pq * 18, bw + pq * 36, bh + pq * 36, 34 + pq * 18); x.stroke();
        A.lightSweep(x, q => A.rrectPath(q, bx, by, bw, bh, 34), [bx, by, bw, bh], ramp(lt, t0 + .5, t0 + 1.5), { alpha: .45 }); }
      else A.glassCard(x, bx, by, bw, bh, { r: 34, dark: K.dark, tint: K.tint, tintA: K.dark ? .1 : .75, blur: 22 });
      x.textAlign = 'center'; x.textBaseline = 'middle'; const fs = fitSize(x, nd.label, q => FW(700, q), bw - 50, 54, 30); setF(x, FW(700, fs)); x.fillStyle = hl ? '#fff' : K.ink; x.fillText(nd.label, bx + bw / 2, by + bh / 2 - (nd.sub ? 22 : 0));
      if (nd.sub) { setF(x, FS(34, 500)); x.fillStyle = hl ? 'rgba(255,255,255,.85)' : K.key; x.fillText(nd.sub, bx + bw / 2, by + bh / 2 + 34); }
      x.restore(); });
  };

  // ---------- doc: hoja que flota, líneas que se revelan con máscara y marcador sobre la frase clave ----------
  SC.doc = function (c) {
    const { ctx: x, S, lt, dur } = c, cw = 1180, pad = 80; setF(x, `500 50px "${TH.fontSerif}", Georgia, serif`); const lines = wrap(x, S.text || '', cw - pad * 2), ch = 230 + lines.length * 70 + (S.note ? 70 : 0);
    const { a, e } = ent(lt, 0, 'heavy'), X = W / 2 - cw / 2, Y = 455 - ch / 2;
    x.save(); x.globalAlpha *= a; x.translate(W / 2, 455 + 80 * (1 - e)); x.rotate((-1.2 + .6 * A.easeInOutSine(lt / Math.max(2, dur))) * Math.PI / 180 * (1 + 1.5 * (1 - e))); x.translate(-W / 2, -455);
    A.softShadow(x, X, Y, cw, ch, 18, { alpha: K.dark ? .6 : .2, color: K.shadow, blur: 90, dy: 40 });
    A.rrectPath(x, X, Y, cw, ch, 18); const pg = x.createLinearGradient(0, Y, 0, Y + ch); pg.addColorStop(0, '#FFFFFF'); pg.addColorStop(1, '#F3F6FC'); x.fillStyle = pg; x.fill();
    setF(x, FW(700, 26), 4); x.fillStyle = '#2F6BFF'; x.textAlign = 'left'; x.textBaseline = 'alphabetic'; x.fillText((S.source || 'DOCUMENTO').toUpperCase(), X + pad, Y + 84);
    x.fillStyle = 'rgba(10,18,34,.12)'; x.fillRect(X + pad, Y + 108, (cw - pad * 2) * A.easeInOutExpo(ramp(lt, .2, .8)), 2);
    const per = Math.max(.25, Math.min(.7, (dur * .6) / Math.max(1, lines.length))), hlTxt = S.highlight ? String(S.highlight) : null;
    lines.forEach((l, i) => { const t0 = .45 + i * per, u = A.easeInOutCubic(ramp(lt, t0, t0 + per * 1.1)), yy = Y + 190 + i * 70;
      if (hlTxt && l.includes(hlTxt.split(' ')[0])) { setF(x, `500 50px "${TH.fontSerif}", Georgia, serif`); const i0 = l.indexOf(hlTxt.split(' ')[0]), pre = x.measureText(l.slice(0, i0)).width, hw = x.measureText(l.slice(i0, i0 + hlTxt.length)).width, hu = A.easeInOutCubic(ramp(lt, t0 + per + .2, t0 + per + .8));
        x.fillStyle = 'rgba(47,107,255,.22)'; x.fillRect(X + pad + pre - 6, yy - 42, (hw + 12) * hu, 56); }
      A.maskReveal(x, u, [X + pad - 10, yy - 60, cw - pad * 2 + 20, 80], q => { setF(q, `500 50px "${TH.fontSerif}", Georgia, serif`); q.fillStyle = '#0A1222'; q.textAlign = 'left'; q.textBaseline = 'alphabetic'; q.fillText(l, X + pad, yy); }, { soft: .15 }); });
    if (S.note) { setF(x, FW(600, 28)); x.fillStyle = 'rgba(10,18,34,.55)'; x.globalAlpha *= ent(lt, .45 + lines.length * per, 'snappy').a; x.fillText(S.note, X + pad, Y + ch - 50); }
    x.restore();
  };

  // ---------- compare: dos tarjetas que llegan de lados opuestos; la ganadora en acento con destello ----------
  SC.compare = function (c) {
    const { ctx: x, S, lt } = c; kicker(c, S.title, 0);
    const sides = [S.left || {}, S.right || {}], sc = schedule(c, sides, .45, .15), pw = 690, ph = 470, gap = 140, x0 = (W - pw * 2 - gap) / 2, y0 = 455 - ph / 2;
    sides.forEach((sd, i) => { const t0 = sc[i]; if (!(lt >= t0)) return; const { a, e } = ent(lt, t0, 'default'), dir = i ? 1 : -1, bx = x0 + i * (pw + gap) + dir * 140 * (1 - A.easeOutBack(cl((lt - t0) / .6), 1.2)), by = y0, hl = S.highlight === (i ? 'right' : 'left');
      const u = A.easeOutExpo(ramp(lt, t0 + .1, t0 + 1.3)), sp = Math.abs(A.vel(A.easeOutExpo, ramp(lt, t0 + .1, t0 + 1.3)) * (sd.value || 0) / 1.2 / 60);
      x.save(); x.globalAlpha *= a;
      if (hl) { A.softShadow(x, bx, by, pw, ph, 40, { alpha: .35, color: K.shadow, blur: 70, dy: 28 }); A.rrectPath(x, bx, by, pw, ph, 40); const g = x.createLinearGradient(bx, by, bx + pw, by + ph); g.addColorStop(0, '#2F6BFF'); g.addColorStop(1, '#6FA2FF'); x.fillStyle = g; x.fill(); }
      else A.glassCard(x, bx, by, pw, ph, { r: 40, dark: K.dark, tint: K.tint, tintA: K.dark ? .08 : .7, blur: 24 });
      const ink = hl ? '#fff' : K.ink, mut = hl ? 'rgba(255,255,255,.8)' : K.muted;
      setF(x, FW(700, 30), 6); x.fillStyle = mut; x.textAlign = 'center'; x.textBaseline = 'alphabetic'; x.fillText((sd.label || '').toUpperCase(), bx + pw / 2, by + 92);
      const big = sd.value != null ? null : (sd.big || ''); if (big) { const fs = fitSize(x, big, q => FW(700, q), pw - 80, 140, 50); setF(x, FW(700, fs), -fs * .02); x.fillStyle = ink; x.fillText(big, bx + pw / 2, by + 290); }
      else { const fs = fitSize(x, (sd.prefix || '') + fmtNum(sd.value, sd.decimals || 0) + (sd.suffix || ''), q => FW(700, q), pw - 80, 150, 60); sweepLayer(x, q => odometer(q, sd.value * u, bx + pw / 2, by + 290, fs, { prefix: sd.prefix, suffix: sd.suffix, final: sd.value, decimals: sd.decimals, speed: sp, color: ink, sufColor: hl ? '#fff' : K.key, sufFont: FS(fs * .6, 500) }), hl ? ramp(lt, t0 + 1.1, t0 + 2) : 0, { alpha: .5 }); }
      if (sd.sub) { setF(x, FW(500, 34)); const L = wrap(x, sd.sub, pw - 100).slice(0, 2); x.fillStyle = mut; L.forEach((l, k) => x.fillText(l, bx + pw / 2, by + 370 + k * 44)); }
      x.restore(); });
    const vt = Math.min(sc[0], sc[1] === Infinity ? sc[0] : sc[1]) + .25; if (S.vs !== false && lt >= vt) { const g = A.easeOutBack(cl((lt - vt) / .45), 2); x.save(); x.translate(W / 2, 455); x.scale(g, g);
      x.beginPath(); x.arc(0, 0, 62, 0, 6.283); x.fillStyle = K.dark ? '#0A1222' : '#fff'; x.shadowColor = 'rgba(0,0,0,.3)'; x.shadowBlur = 30; x.fill(); x.shadowBlur = 0; x.lineWidth = 3; x.strokeStyle = K.key; x.stroke();
      setF(x, FS(54, 500)); x.fillStyle = K.key === '#FFFFFF' ? '#1A47E0' : K.key; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(S.vs || 'vs', 0, 2); x.restore(); }
    if (S.note) { setF(x, FW(500, 26)); x.fillStyle = K.muted; x.textAlign = 'center'; x.textBaseline = 'alphabetic'; x.globalAlpha = ent(lt, 1.2, 'snappy').a; x.fillText(S.note, W / 2, y0 + ph + 60); x.globalAlpha = 1; }
  };

  // ---------- donut: anillo que crece con resorte, cifra que cuenta, brillo que gira ----------
  SC.donut = function (c) {
    const { ctx: x, S, lt } = c, cx = 640, cy = 455, r = 250, lw = 64, at = .25, g = cl(A.spring(lt - at, 1.6, 4.2), 0, 1.025), val = S.value / 100;
    kicker(c, S.title, 0);
    const { a } = ent(lt, 0, 'snappy'); x.save(); x.globalAlpha *= a;
    x.lineWidth = lw; x.strokeStyle = K.track.replace(/[\d.]+\)$/, K.dark ? '.12)' : '.08)'); x.beginPath(); x.arc(cx, cy, r, 0, 6.283); x.stroke();
    const end = -Math.PI / 2 + 6.283 * val * g;
    x.lineCap = 'round'; const grd = x.createConicGradient ? x.createConicGradient(-Math.PI / 2, cx, cy) : null;
    if (grd) { grd.addColorStop(0, K.key === '#FFFFFF' ? '#BFD4FF' : '#5C96FF'); grd.addColorStop(Math.max(.01, val), K.key); grd.addColorStop(1, K.key); x.strokeStyle = grd; } else x.strokeStyle = K.key;
    if (K.dark || K.key === '#FFFFFF') { x.shadowColor = `rgba(${K.accentRGB},.6)`; x.shadowBlur = 30; }
    if (g > .002) { x.beginPath(); x.arc(cx, cy, r, -Math.PI / 2, end); x.stroke(); }
    x.shadowBlur = 0; A.halo(x, cx + Math.cos(end) * r, cy + Math.sin(end) * r, 70, K.accentRGB, .6 * cl(g * 2));
    const pct = Math.round(S.value * A.easeOutExpo(ramp(lt, at, at + 1.4)));
    odometer(x, pct, cx, cy + 50, 150, { suffix: ' %', sufFont: FS(100, 500), sufColor: K.key, color: K.ink, final: S.value, sep: '' });
    x.restore();
    const tx = 1060; if (S.label) { const fs = fitSize(x, S.label, q => FW(700, q), 760, 70, 40); setF(x, FW(700, fs), -fs * .02); x.fillStyle = K.ink; riseText(x, S.label, tx, 430, lt, .9, { size: fs, stagger: .05, preset: 'heavy' }); }
    if (S.rest) { setF(x, FS(44, 500)); x.fillStyle = K.key; riseText(x, S.rest, tx, 520, lt, 1.3, { size: 44, stagger: .04 }); }
  };

  // ---------- chart: ejes que se dibujan, línea con cometa luminoso, área, valor que sigue la punta ----------
  SC.chart = function (c) {
    const { ctx: x, S, lt, dur } = c, d = S.data || []; if (d.length < 2) return; kicker(c, S.title, 0);
    const L = 230, R = W - 200, T = 200, B = 730, xs = d.map(p => p[0]), ys = d.map(p => p[1]), xmin = Math.min(...xs), xmax = Math.max(...xs);
    const ymin = S.yFrom0 === false ? Math.min(...ys) : Math.min(0, ...ys), ymax = Math.max(...ys) * 1.12, X = v => L + (v - xmin) / (xmax - xmin) * (R - L), Y = v => B - (v - ymin) / (ymax - ymin) * (B - T);
    const ax = A.easeInOutExpo(ramp(lt, 0, .7));
    x.save(); x.fillStyle = K.track; x.fillRect(L, B, (R - L) * ax, 2); x.fillRect(L, B - (B - T) * ax, 2, (B - T) * ax);
    for (let k = 1; k <= 4; k++) { const u = A.easeOutCubic(ramp(lt, .1 + k * .06, .6 + k * .06)), yy = Y(ymin + (ymax - ymin) * k / 4.4); x.globalAlpha = u * .6; x.setLineDash([4, 10]); x.strokeStyle = K.track; x.beginPath(); x.moveTo(L, yy); x.lineTo(L + (R - L) * u, yy); x.stroke(); x.setLineDash([]);
      setF(x, FW(500, 24)); x.fillStyle = K.muted; x.textAlign = 'right'; x.textBaseline = 'middle'; x.fillText((S.prefix || '') + fmtNum(ymin + (ymax - ymin) * k / 4.4, 0), L - 18, yy); }
    x.globalAlpha = 1; const every = Math.ceil(d.length / 10); d.forEach((p, i) => { if (i % every && i !== d.length - 1) return; setF(x, FW(600, 26)); x.fillStyle = K.muted; x.textAlign = 'center'; x.textBaseline = 'top'; x.globalAlpha = ent(lt, .2 + i * .03, 'snappy').a; x.fillText(String(p[0]), X(p[0]), B + 16); });
    x.restore();
    if (S.band) { const bs = schedule(c, [S.band], 0)[0], bu = A.easeOutBack(cl((lt - bs) / .6), 1.2); if (bu > 0) { const bx0 = X(S.band.from), bx1 = X(S.band.to), mx = (bx0 + bx1) / 2, hw = (bx1 - bx0) / 2 * bu; x.fillStyle = `rgba(${K.lossRGB},.14)`; x.fillRect(mx - hw, T - 20, hw * 2, B - T + 20); pill(x, S.band.label || '', mx, T - 40, { size: 24, w: 700, align: 'center', a: cl(bu), solid: K.loss, color: '#fff' }); } }
    const pts = d.map(p => [X(p[0]), Y(p[1])]), pr = A.easeInOutCubic(ramp(lt, .4, .4 + (S.drawTime || Math.min(2.6, Math.max(1.2, dur * .45))))), segs = pts.length - 1, fpos = pr * segs, k = Math.min(segs - 1, Math.floor(fpos)), f = fpos - k;
    const tip = [pts[k][0] + (pts[k + 1][0] - pts[k][0]) * f, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * f];
    if (pr > 0) {
      x.save(); x.beginPath(); x.moveTo(pts[0][0], B); for (let i = 0; i <= k; i++) x.lineTo(pts[i][0], pts[i][1]); x.lineTo(tip[0], tip[1]); x.lineTo(tip[0], B); x.closePath();
      const g = x.createLinearGradient(0, T, 0, B); g.addColorStop(0, `rgba(${K.accentRGB},.32)`); g.addColorStop(1, `rgba(${K.accentRGB},0)`); x.fillStyle = g; x.fill();
      x.beginPath(); for (let i = 0; i <= k; i++) i ? x.lineTo(pts[i][0], pts[i][1]) : x.moveTo(pts[i][0], pts[i][1]); x.lineTo(tip[0], tip[1]); x.strokeStyle = K.key; x.lineWidth = 6; x.lineJoin = 'round'; x.lineCap = 'round'; if (K.dark) { x.shadowColor = `rgba(${K.accentRGB},.8)`; x.shadowBlur = 18; } x.stroke(); x.restore();
      A.halo(x, tip[0], tip[1], 60, K.accentRGB, .8); x.beginPath(); x.arc(tip[0], tip[1], 9, 0, 6.283); x.fillStyle = '#fff'; x.fill();
      const v = d[k][1] + (d[k + 1][1] - d[k][1]) * f; if (pr < 1) pill(x, (S.prefix || '') + fmtNum(v, S.decimals ?? 1) + (S.suffix || ''), tip[0] + (tip[0] > R - 260 ? -24 : 24), tip[1] - 50, { size: 30, w: 700, align: tip[0] > R - 260 ? 'right' : 'left', solid: K.key === '#FFFFFF' ? '#fff' : K.key, color: K.key === '#FFFFFF' ? '#1A47E0' : '#fff' });
    }
    const marks = S.marks || [], ms = schedule(c, marks, .5);
    marks.forEach((m, i) => { const p = d.find(q => q[0] === m.x); if (!p || !(lt >= ms[i])) return; const g = A.easeOutBack(cl((lt - ms[i]) / .4), 2), mx = X(p[0]), my = Y(p[1]);
      for (let q2 = 0; q2 < 2; q2++) { const q = ((lt - ms[i] + q2 * .8) % 1.6) / 1.6; x.save(); x.globalAlpha = (1 - q) * .6; x.strokeStyle = K.loss; x.lineWidth = 3; x.beginPath(); x.arc(mx, my, 14 + q * 40, 0, 6.283); x.stroke(); x.restore(); }
      x.save(); x.translate(mx, my); x.scale(g, g); x.beginPath(); x.arc(0, 0, 14, 0, 6.283); x.fillStyle = K.loss; x.fill(); x.lineWidth = 4; x.strokeStyle = '#fff'; x.stroke(); x.restore();
      pill(x, m.label || ((S.prefix || '') + fmtNum(p[1], S.decimals ?? 1) + (S.suffix || '')), mx, my - 70, { size: 28, w: 700, align: 'center', a: cl(g), solid: K.loss, color: '#fff' }); });
    if (S.source) { setF(x, FW(500, 22)); x.fillStyle = K.muted; x.textAlign = 'right'; x.textBaseline = 'alphabetic'; x.globalAlpha = ent(lt, .8, 'snappy').a * .9; x.fillText(S.source, R, B + 70); x.globalAlpha = 1; }
  };

  // ---------- people: retratos flotantes que suben con giro que se asienta; el que habla se acerca ----------
  SC.people = function (c) {
    const { ctx: x, S, lt, dur } = c, items = S.items || [], n = items.length; kicker(c, S.title, 0); if (!n) return;
    const gap = 60, cw = Math.min(420, (W - 260 - gap * (n - 1)) / n), ch = Math.min(cw * 1.3, c.capOff ? 560 : 470), x0 = (W - (n * cw + (n - 1) * gap)) / 2, top = 150;
    const sc = schedule(c, items, .3, .05); let cur = -1; if (S.focus) S.focus.forEach(f => { if (lt >= f.at) cur = f.i; });
    items.forEach((it, i) => { const t0 = sc[i]; if (!(lt >= t0)) return; const { a, e } = ent(lt, t0, 'default'), rot = ((i % 2 ? 3 : -3) * (1 - e) + (i - (n - 1) / 2) * .6) * Math.PI / 180;
      const foc = cur < 0 ? 1 : cur === i ? 1.06 : .94, bx = x0 + i * (cw + gap), by = top + 90 * (1 - e);
      x.save(); x.globalAlpha *= a * (cur < 0 || cur === i ? 1 : .55); x.translate(bx + cw / 2, by + ch / 2); x.rotate(rot); x.scale(foc, foc); x.translate(-(bx + cw / 2), -(by + ch / 2));
      A.softShadow(x, bx, by, cw, ch, 30, { alpha: K.dark ? .55 : .22, color: K.shadow, blur: 70, dy: 30 });
      x.save(); A.rrectPath(x, bx, by, cw, ch, 30); x.clip(); x.fillStyle = '#111'; x.fillRect(bx, by, cw, ch); const im = imgCache(it.src); if (im) parallaxPhoto(x, im, lt - t0, dur, [bx, by, cw, ch], { focus: it.focus || [.5, .3], amount: .08, subject: false }); x.restore();
      A.lightSweep(x, q => A.rrectPath(q, bx, by, cw, ch, 30), [bx, by, cw, ch], ramp(lt, t0 + .4, t0 + 1.3), { alpha: .3 });
      setF(x, FW(700, 40)); x.fillStyle = K.ink; x.textAlign = 'center'; x.textBaseline = 'alphabetic'; x.fillText(it.name || '', bx + cw / 2, by + ch + 60);
      if (it.role) { setF(x, FS(32, 500)); x.fillStyle = K.key; x.fillText(it.role, bx + cw / 2, by + ch + 102); }
      x.restore(); });
    credit(x, [...new Set(items.map(it => it.credit || creditOf(it.src)).filter(Boolean))].join('   ·   '), prog(lt, .6, .8));
  };

  // ---------- motion: animaciones nuevas (lago, cielo) o las de v1 dentro de la superficie ----------
  SC.motion = {
    cam: false, draw(c) { const m = MOT[c.S.anim]; if (m) return m(c); c.cam.apply(c.ctx, 1); const o = MOTION[c.S.anim]; if (!o) return; const z = c.S.zoom || o.zoom || 1; if (z !== 1) scaleAt(c.ctx, W / 2, z < 1 ? 300 : H / 2 - 40, z, () => o.draw(c)); else o.draw(c); }
  };
  // lago con una ciudad-isla que se dibuja (textos en lakeLabel / cityLabel / kicker)
  const LAKE = [[-560, -40], [-520, -170], [-430, -250], [-300, -270], [-180, -230], [-60, -260], [60, -300], [190, -270], [300, -210], [420, -200], [520, -120], [560, 10], [520, 130], [420, 210], [290, 250], [150, 230], [40, 270], [-80, 300], [-210, 280], [-330, 230], [-450, 170], [-530, 80]];
  MOT.texcoco = function (c) {
    const { ctx: x, S, lt, dur } = c, cx = 960, cy = 450, zc = 1 + .1 * A.easeInOutSine(lt / Math.max(2, dur)), isl = [-120, 30];
    x.save(); x.translate(cx, cy); x.scale(zc, zc); x.translate(-isl[0] * (zc - 1) / zc * 1.2, -isl[1] * (zc - 1) / zc);
    // orilla (tierra) y lago con trazo que se dibuja
    const lp = new Path2D(); const sm = LAKE.map(([a, b]) => [a * 1.18, b * 1.05]); sm.forEach((q, i) => { const n = sm[(i + 1) % sm.length], mx = (q[0] + n[0]) / 2, my = (q[1] + n[1]) / 2; i ? lp.quadraticCurveTo(q[0], q[1], mx, my) : lp.moveTo(mx, my); }); lp.closePath();
    const u = A.easeInOutCubic(ramp(lt, 0, 1.1)), f = A.easeOutCubic(ramp(lt, .5, 1.5));
    x.save(); x.globalAlpha = f; const wg = x.createLinearGradient(0, -320, 0, 320); wg.addColorStop(0, K.dark ? '#1A4FD0' : '#7FAAFF'); wg.addColorStop(1, K.dark ? '#0A2A80' : '#3D7BFF'); x.fillStyle = wg; x.shadowColor = `rgba(${K.accentRGB},.6)`; x.shadowBlur = K.dark ? 60 : 30; x.fill(lp); x.restore();
    // brillos del agua
    x.save(); x.clip(lp); x.globalCompositeOperation = 'lighter'; x.strokeStyle = 'rgba(255,255,255,.12)'; x.lineWidth = 2;
    for (let k = 0; k < 18; k++) { const yy = -300 + k * 34, ph = lt * .8 + k; x.beginPath(); for (let xx = -700; xx <= 700; xx += 20) { const yv = yy + Math.sin(xx * .012 + ph) * 6; xx === -700 ? x.moveTo(xx, yv) : x.lineTo(xx, yv); } x.globalAlpha = f * (.4 + .3 * Math.sin(k + lt)); x.stroke(); }
    x.restore();
    x.save(); x.strokeStyle = K.dark ? 'rgba(255,255,255,.9)' : '#1A47E0'; x.lineWidth = 3; x.setLineDash([4200 * u, 4200]); x.stroke(lp); x.restore();
    // calzadas hacia tierra firme (Tepeyac, Tlacopan, Iztapalapa) con partículas
    const cz = [[isl, [-130, -300], 'Tepeyac'], [isl, [-640, 10], 'Tlacopan'], [isl, [60, 300], 'Iztapalapa']];
    cz.forEach(([a, b], i) => { const at = 1.0 + i * .18, q = A.easeInOutCubic(ramp(lt, at, at + .8)); if (q <= 0) return;
      x.save(); x.strokeStyle = K.dark ? '#F4E3C3' : '#0A1222'; x.lineWidth = 7; x.lineCap = 'round'; x.beginPath(); x.moveTo(a[0], a[1]); x.lineTo(a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q); x.stroke();
      if (q >= 1) for (let k = 0; k < 4; k++) { const s = ((lt - at) * .35 + k / 4) % 1; x.beginPath(); x.arc(a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s, 4, 0, 6.283); x.fillStyle = K.key; x.fill(); }
      x.restore(); });
    // la isla-ciudad: manzanas y chinampas que aparecen en espiral desde el centro
    const ip = new Path2D(); ip.ellipse(isl[0], isl[1], 150, 120, -.2, 0, 6.283);
    x.save(); x.globalAlpha = A.easeOutCubic(ramp(lt, .7, 1.2)); x.fillStyle = K.dark ? '#E9D9B8' : '#F7F1E4'; x.shadowColor = 'rgba(0,0,0,.35)'; x.shadowBlur = 20; x.shadowOffsetY = 6; x.fill(ip); x.restore();
    x.save(); x.clip(ip); const cells = [];
    for (let gy = -6; gy <= 6; gy++) for (let gx = -8; gx <= 8; gx++) { const px = isl[0] + gx * 19, py = isl[1] + gy * 19, d = Math.hypot(gx, gy); cells.push([px, py, d]); }
    cells.sort((p, q) => p[2] - q[2]).forEach(([px, py, d], i) => { const at = .9 + d * .09, g = A.easeOutBack(ramp(lt, at, at + .35)); if (g <= 0) return; const s = 13 * g;
      x.fillStyle = (Math.abs(px - isl[0]) < 30 && Math.abs(py - isl[1]) < 30) ? K.key : (K.dark ? 'rgba(60,40,20,.55)' : 'rgba(10,18,34,.35)'); x.fillRect(px - s / 2, py - s / 2, s, s); });
    x.restore();
    // recinto ceremonial y Templo Mayor (pirámide doble escalonada)
    const tg = A.easeOutBack(ramp(lt, 1.6, 2.1)); if (tg > 0) { x.save(); x.translate(isl[0], isl[1] - 6); x.scale(tg, tg); A.halo(x, 0, 0, 120, K.accentRGB, .5);
      x.fillStyle = K.dark ? '#FFE2A8' : '#1A47E0'; for (let k = 0; k < 4; k++) { const w = 64 - k * 13, h = 9; x.fillRect(-w / 2, 10 - k * h, w, h); } x.fillRect(-14, -28, 11, 10); x.fillRect(3, -28, 11, 10); x.restore(); }
    x.restore();
    // etiquetas
    const lab = (t, X, Y, at, o = {}) => { const { a, e } = ent(lt, at, 'snappy'); if (a <= 0) return; x.save(); x.translate(0, 16 * (1 - e)); pill(x, t, X, Y, Object.assign({ size: 30, w: 600, align: 'center', a }, o)); x.restore(); };
    lab(S.lakeLabel || '', 1360, 260, .6);
    lab(S.cityLabel || '', 960 + isl[0] * zc, 450 + isl[1] * zc + 170, 1.5, { solid: K.key, color: K.dark ? '#03132E' : '#fff', w: 700, size: 34 });
    if (S.pop) lab(S.pop, 960 + isl[0] * zc, 450 + isl[1] * zc + 236, 1.9, { size: 26 });
    kicker(c, S.kicker || '', .2);
  };
  // Cielo maya: estrellas, constelaciones que se trazan y numerales mayas (puntos y barras) en un calendario que gira
  MOT.cielo = function (c) {
    const { ctx: x, S, lt, dur } = c;
    x.save(); x.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 260; i++) { const r1 = A.hash(i * 3 + 11), r2 = A.hash(i * 7 + 5), r3 = A.hash(i * 13 + 2), sx = r1 * W, sy = r2 * 800; const tw = .5 + .5 * Math.sin(lt * (1 + r3 * 2) + i);
      x.globalAlpha = (.25 + .75 * r3) * tw * cl(lt / .4); x.fillStyle = '#fff'; x.beginPath(); x.arc(sx - lt * 6 * r3, sy, .6 + r3 * 1.6, 0, 6.283); x.fill(); }
    x.restore();
    const cons = S.constellations || [[[260, 260], [380, 200], [470, 290], [610, 240], [720, 330]], [[300, 520], [420, 440], [540, 500], [480, 620], [360, 640], [300, 520]], [[760, 520], [860, 430], [980, 480], [1020, 600]]];
    cons.forEach((pts, ci) => { const at = .3 + ci * .45, u = A.easeInOutCubic(ramp(lt, at, at + 1.1)); if (u <= 0) return; let len = 0; for (let i = 1; i < pts.length; i++) len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      x.save(); x.strokeStyle = `rgba(${K.accentRGB},.9)`; x.lineWidth = 2.5; x.shadowColor = `rgba(${K.accentRGB},1)`; x.shadowBlur = 12; x.setLineDash([len * u, len]); x.beginPath(); pts.forEach((p, i) => i ? x.lineTo(p[0], p[1]) : x.moveTo(p[0], p[1])); x.stroke(); x.restore();
      pts.forEach((p, i) => { const g = A.easeOutBack(ramp(lt, at + i * .12, at + i * .12 + .4)); if (g <= 0) return; A.halo(x, p[0], p[1], 34, '255,240,210', .7 * g); x.beginPath(); x.arc(p[0], p[1], 4.5 * g, 0, 6.283); x.fillStyle = '#fff'; x.fill(); }); });
    // calendario: anillos concéntricos que giran + numerales mayas 0–19
    const cx = 1400, cy = 440, R = 300, e = Motion.step(lt - .2, 'heavy'), rot = lt * .12;
    x.save(); x.translate(cx, cy); x.scale(.85 + .15 * e, .85 + .15 * e); x.globalAlpha = cl((lt - .2) / .1);
    [R, R * .78, R * .52].forEach((r, k) => { x.save(); x.rotate(rot * (k % 2 ? -1 : 1) * (1 + k * .3)); x.strokeStyle = `rgba(${K.accentRGB},${.75 - k * .15})`; x.lineWidth = k ? 2 : 3; x.beginPath(); x.arc(0, 0, r, 0, 6.283); x.stroke();
      const n = k === 0 ? 20 : k === 1 ? 13 : 0; for (let i = 0; i < n; i++) { const a = i / n * 6.283; x.save(); x.rotate(a); x.translate(0, -r + (k === 0 ? 34 : 22)); if (k === 0) mayaNum(x, i, 9, K.ink); else { x.fillStyle = K.key; x.beginPath(); x.arc(0, -8, 5, 0, 6.283); x.fill(); } x.restore(); } x.restore(); });
    const big = Math.round(584 * A.easeOutExpo(ramp(lt, .6, 2.4)));
    setF(x, FW(700, 92), -2); x.fillStyle = K.ink; x.textAlign = 'center'; x.textBaseline = 'alphabetic'; x.fillText(fmtNum(big), 0, 20);
    setF(x, FS(38, 500)); x.fillStyle = K.key; x.fillText(S.ringLabel || 'días · ciclo de Venus', 0, 72);
    x.restore();
    kicker(c, S.kicker || 'Astronomía maya', .1);
  };
  function mayaNum(x, n, s, col) {
    const bars = Math.floor(n / 5), dots = n % 5; x.fillStyle = col;
    if (n === 0) { x.beginPath(); x.ellipse(0, 0, s * 1.2, s * .6, 0, 0, 6.283); x.lineWidth = 2; x.strokeStyle = col; x.stroke(); return; }
    for (let b = 0; b < bars; b++) x.fillRect(-s * 1.4, s * .9 - b * s * .7, s * 2.8, s * .42);
    const y = s * .9 - bars * s * .7 - s * .2; for (let d = 0; d < dots; d++) { x.beginPath(); x.arc((d - (dots - 1) / 2) * s * .7, y, s * .25, 0, 6.283); x.fill(); }
  }

  /* ============================================================ TRANSICIONES ====================================== */
  function composite(x, ty, p, a, b, t, info) {
    const dir = (info && info.dir) || 1, d = (info && info.d) || .6, fps = window.__fps || 60;
    x.fillStyle = '#000'; x.fillRect(-4, -4, W + 8, H + 8);
    switch (ty) {
      case 'whip': { // barrido rápido con desenfoque direccional proporcional a la velocidad
        const e = A.easeInOutExpo(p), v = A.vel(A.easeInOutExpo, p) / d * W / fps * .9;
        A.whip(x, a, -dir * W * e, 0, W, H, -dir * v, 0); A.whip(x, b, dir * W * (1 - e), 0, W, H, -dir * v, 0); break; }
      case 'card': { // la nueva escena sube como tarjeta (match cut de rectángulo) y la anterior retrocede
        const e = A.easeInOutExpo(p), r = A.rectMorph([W * .17, H * .9, W * .66, H * .66, 46], [0, 0, W, H, 0], p);
        x.save(); x.translate(W / 2, H / 2); x.scale(1 - .08 * e, 1 - .08 * e); x.drawImage(a, -W / 2, -H / 2, W, H); x.restore(); x.fillStyle = `rgba(0,0,0,${.45 * e})`; x.fillRect(0, 0, W, H);
        const vy = A.vel(A.easeInOutExpo, p) / d * (H * .9) / fps * .6;
        x.save(); A.softShadow(x, r[0], r[1], r[2], r[3], r[4], { alpha: .55, color: '0,0,0', blur: 80, dy: 30 }); A.rrectPath(x, r[0], r[1], r[2], r[3], r[4]); x.clip(); A.whip(x, b, r[0], r[1], r[2], r[3], 0, -vy * (1 - e)); x.restore(); break; }
      case 'zoom': { // la escena pasa de largo hacia la cámara (desenfoque radial) y la nueva llega desde lejos
        const zb = (img, s0, s1, al) => { const n = Math.abs(s1 - s0) > .01 ? 6 : 1; for (let k = 0; k < n; k++) { const s = s0 + (s1 - s0) * k / Math.max(1, n - 1); x.save(); x.globalAlpha = al / (k + 1); x.translate(W / 2, H / 2); x.scale(s, s); x.drawImage(img, -W / 2, -H / 2, W, H); x.restore(); } };
        const v = A.vel(A.easeInOutExpo, p) / d / fps;
        if (p < .5) { const e = A.easeInOutExpo(p); zb(a, 1 + .9 * e, 1 + .9 * e + v * .5, 1); }
        else { const e = A.easeInOutExpo(p); zb(b, 1.35 - .35 * e, 1.35 - .35 * e + v * .3, 1); }
        const fl = Math.pow(Math.sin(Math.PI * p), 6) * .18; if (fl > .01) { x.fillStyle = `rgba(255,255,255,${fl})`; x.fillRect(0, 0, W, H); } break; }
      case 'mask': { // revelado circular con anillo de acento
        const e = A.easeInOutExpo(p), R = Math.hypot(W, H) * .6 * e, cx = W / 2, cy = H * .45;
        x.save(); x.translate(W / 2, H / 2); x.scale(1 + .05 * e, 1 + .05 * e); x.drawImage(a, -W / 2, -H / 2, W, H); x.restore();
        x.save(); A.circleClip(x, cx, cy, R); x.translate(W / 2, H / 2); x.scale(1.08 - .08 * e, 1.08 - .08 * e); x.drawImage(b, -W / 2, -H / 2, W, H); x.restore();
        if (e > 0 && e < 1) { x.save(); x.strokeStyle = TH.accent || '#2F6BFF'; x.lineWidth = 10 * (1 - e) + 2; x.shadowColor = 'rgba(92,150,255,.9)'; x.shadowBlur = 30; x.beginPath(); x.arc(cx, cy, R, 0, 6.283); x.stroke(); x.restore(); } break; }
      case 'swipe': { // barrido de un panel de acento (como el «barrido azul» del estilo B)
        const e1 = A.easeInOutCubic(cl(p / .72)), e2 = A.easeInOutCubic(cl((p - .28) / .72)), sk = 260, col = (info && info.col) || '#2F6BFF';
        const lead = -sk + (W + 2 * sk) * e1, tail = -sk + (W + 2 * sk) * e2;
        x.drawImage(p < .5 ? a : b, 0, 0, W, H);
        if (p >= .5) { x.save(); x.beginPath(); x.moveTo(lead + sk, 0); x.lineTo(W + 10, 0); x.lineTo(W + 10, H); x.lineTo(lead - sk, H); x.closePath(); x.clip(); x.drawImage(a, 0, 0, W, H); x.restore(); }
        else { x.save(); x.beginPath(); x.moveTo(-10, 0); x.lineTo(tail + sk, 0); x.lineTo(tail - sk, H); x.lineTo(-10, H); x.closePath(); x.clip(); x.drawImage(b, 0, 0, W, H); x.restore(); }
        x.save(); x.beginPath(); x.moveTo(tail + sk, 0); x.lineTo(lead + sk, 0); x.lineTo(lead - sk, H); x.lineTo(tail - sk, H); x.closePath();
        const g = x.createLinearGradient(tail, 0, lead, H); g.addColorStop(0, col); g.addColorStop(1, '#6FA2FF'); x.fillStyle = g; x.shadowColor = 'rgba(0,0,0,.4)'; x.shadowBlur = 50; x.fill(); x.restore();
        x.save(); x.globalCompositeOperation = 'lighter'; x.fillStyle = 'rgba(255,255,255,.25)'; x.beginPath(); x.moveTo(lead + sk - 18, 0); x.lineTo(lead + sk, 0); x.lineTo(lead - sk, H); x.lineTo(lead - sk - 18, H); x.closePath(); x.fill(); x.restore(); break; }
      case 'cut': default: x.drawImage(p < .5 ? a : b, 0, 0, W, H);
    }
  }

  /* ============================================================ CAPA SUPERIOR: tipografía cinética, logo, dither === */
  function overlay(x, t, opt = {}) {
    if (TH.captions !== false) captions(x, t);
    logo(x, t);
    A.dither(x, .03);
  }
  function captions(x, t) {
    const i = phraseAt(t), cands = [];
    for (const q of [i - 1, i, i + 1]) if (q >= 0 && q < P.length) (V.beats[q] || []).forEach(b => cands.push(b));
    cands.sort((a, b) => a.t0 - b.t0);
    let cur = null, next = null; for (let k = 0; k < cands.length; k++) { if (cands[k].t0 <= t) { cur = cands[k]; next = cands[k + 1] || null; } }
    if (!cur) return;
    // salida: 3 cuadros antes del siguiente beat, o 1.2 s después de la clave si no viene nada pronto
    let sceneEnd = 1e9; { let k = cur.pi + 1; while (k < P.length && !P[k].scene) k++; if (k < P.length) sceneEnd = starts[k] - transOf(k).d * .35; }
    const hardEnd = Math.min(next ? next.t0 - .02 : 1e9, cur.tEnd + 1.6, sceneEnd, voiceEnd() + .3), out = cl((hardEnd - t) / .07);
    if (out <= 0) return;
    const j = ownerOf(phraseAt(t)), s = surfOf(j), Sx = P[j].scene || {}, isFull = (Sx.type === 'photo' || Sx.type === 'image') && Sx.style !== 'card' && !(Sx.src && imgCache(Sx.src) && imgCache(Sx.src).width / imgCache(Sx.src).height < 1.1 && !Sx.style), onPhoto = isFull || Sx.type === 'gallery';
    const keySz0 = 124, maxW = 1560, ctxSz = 46;
    x.save(); x.globalAlpha = out; x.textBaseline = 'alphabetic';
    const keyFont = q => cur.serif ? FS(q * 1.07, 500) : FW(700, q);
    let ks = keySz0; for (; ks > 60; ks -= 4) { x.font = keyFont(ks); x.letterSpacing = (cur.serif ? 0 : -ks * .025) + 'px'; if (x.measureText(cur.key.w).width <= maxW) break; }
    const baseY = 958, ctxY = baseY - ks * .86 - 28;
    if (onPhoto || s.dark) { x.shadowColor = 'rgba(0,0,0,.45)'; x.shadowBlur = 30; x.shadowOffsetY = 4; }
    // contexto: palabra por palabra con la voz (diseño final fijo: nada se mueve cuando entra la siguiente)
    if (cur.ctx.length) {
      setF(x, FW(600, ctxSz), -.5); const sp = x.measureText(' ').width, ws = cur.ctx.map(w => ({ w: w.w, s: w.s, ww: x.measureText(w.w).width })), tw = ws.reduce((q, w) => q + w.ww, 0) + sp * (ws.length - 1);
      let px = W / 2 - tw / 2; ws.forEach(w => { const t0 = w.s - .05, { a, e } = ent(t, t0, 'snappy'); if (a > 0) { x.save(); x.globalAlpha *= a; x.fillStyle = onPhoto ? '#fff' : s.ink; x.textAlign = 'left'; x.fillText(w.w, px, ctxY + (1 - e) * 22); x.restore(); } px += w.ww + sp; });
    }
    // clave grande en acento
    const t0 = cur.key.s - .04, { a, e } = ent(t, t0, 'heavy'); if (a > 0) {
      x.save(); x.font = keyFont(ks); x.letterSpacing = (cur.serif ? 0 : -ks * .025) + 'px'; const kw = x.measureText(cur.key.w).width; x.globalAlpha *= a;
      x.translate(W / 2, baseY + (1 - e) * 34); x.scale(.94 + .06 * e, .94 + .06 * e);
      const col = onPhoto && !s.dark ? '#5C96FF' : (onPhoto ? '#7FB0FF' : s.key);
      if (s.dark || onPhoto) { x.shadowColor = `rgba(${s.accentRGB},.45)`; x.shadowBlur = 36; x.shadowOffsetY = 0; }
      x.fillStyle = col; x.textAlign = 'center'; x.fillText(cur.key.w, 0, 0); x.restore();
    }
    x.restore();
  }
  function logo(x, t) {
    if (!TH.logo) return; const im = imgCache(TH.logo); if (!im) return;
    const j = ownerOf(phraseAt(t)), big = P[j] && P[j].scene && P[j].scene.logo ? 1 : 0, a = cl((t - .5) / .4) * (1 - big); if (a <= 0) return;
    const s = TH.logoSize || 70, k = s / Math.max(im.width, im.height), w = im.width * k, h = im.height * k;
    x.save(); x.globalAlpha = a * (TH.logoOpacity ?? .9); x.shadowColor = 'rgba(0,0,0,.35)'; x.shadowBlur = 14; x.drawImage(im, W - 56 - w, 44, w, h); x.restore();
  }

  /* ============================================================ SONIDO (efectos que nacen de las transiciones) ===== */
  function sfxEvents() {
    const ev = [], wordsBusy = (a, b) => V.words ? V.words.some(w => w.s < b && w.e > a) : false; let last = -9;
    P.forEach((p, j) => { if (!p.scene || j === 0) return; const tr = transOf(j); if (tr.ty === 'cut' || !tr.d) return; const tt = starts[j] - tr.d * .45;
      // nunca sobre palabras y con moderación (≤ 1 cada 3.5 s)
      if (tt - last < 3.5) return; if (wordsBusy(tt + .05, tt + .35)) return; ev.push({ t: tt, s: tr.ty === 'swipe' || tr.ty === 'zoom' ? 'whoosh_bajo' : 'whoosh' }); last = tt; });
    return ev;
  }

  window.V2 = { SURF, THEMES, resolveTheme, prepare, transOf, setWords, syncByWords, phraseWords, drawScene, composite, overlay, sfxEvents, SC, MOT, odometer, pill, surfOf, state: V };
})();
