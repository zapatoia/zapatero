"""Renderizador moderngl (EGL sin ventana, Mesa llvmpipe por software).

Pipeline al estilo de un MMO de 2003:
  1. mapa de sombras ortográfico del sol (bordes duros, PCF de 4 tomas)
  2. cielo: degradado cenit→horizonte + halo del sol
  3. geometría opaca: color por vértice × textura sin filtrar, luz por cara
     (sol cálido + hemisferio cielo/suelo), recorte alfa, niebla lineal
  4. post: brillo suave de zonas claras, viñeta y gradación ligera
"""
import numpy as np
import moderngl
from PIL import Image

from .mathutil import look_at, perspective, ortho, normalize
from .style import LIGHT, SKY, FOG, RENDER
from . import textures as T

VS = """
#version 330
in vec3 in_pos; in vec3 in_nrm; in vec2 in_uv; in vec4 in_col;
uniform mat4 u_model; uniform mat3 u_nmat; uniform mat4 u_vp; uniform mat4 u_lvp;
uniform vec4 u_uvrect;
out vec3 v_wpos; out vec3 v_nrm; out vec2 v_uv; out vec4 v_col; out vec4 v_lpos;
void main(){
  vec4 w = u_model * vec4(in_pos, 1.0);
  v_wpos = w.xyz;
  v_nrm = normalize(u_nmat * in_nrm);
  v_uv = u_uvrect.xy + in_uv * (u_uvrect.zw - u_uvrect.xy);
  v_col = in_col;
  v_lpos = u_lvp * w;
  gl_Position = u_vp * w;
}
"""

FS = """
#version 330
in vec3 v_wpos; in vec3 v_nrm; in vec2 v_uv; in vec4 v_col; in vec4 v_lpos;
uniform sampler2D u_tex; uniform sampler2D u_tex2; uniform sampler2D u_shadow;
uniform int u_blend; uniform int u_flip; uniform float u_alpha_test; uniform float u_emissive; uniform int u_unlit;
uniform vec4 u_tint; uniform vec3 u_eye; uniform vec3 u_sun; uniform vec3 u_sun_col;
uniform vec3 u_sky_amb; uniform vec3 u_gnd_amb; uniform vec3 u_fog_col; uniform vec3 u_glow_col;
uniform vec3 u_fog; uniform float u_shadow_k; uniform vec2 u_shadow_texel; uniform float u_fog_k;
out vec4 f_col;

float shadow_at(){
  vec3 p = v_lpos.xyz / v_lpos.w * 0.5 + 0.5;
  if (p.x <= 0.0 || p.x >= 1.0 || p.y <= 0.0 || p.y >= 1.0 || p.z >= 1.0) return 1.0;
  float ndl = dot(normalize(v_nrm), u_sun);
  float bias = 0.0012 + 0.0025 * (1.0 - clamp(ndl, 0.0, 1.0));
  float s = 0.0;
  for (int i = 0; i < 4; i++){
    vec2 o = vec2((i & 1) == 0 ? -0.5 : 0.5, (i & 2) == 0 ? -0.5 : 0.5) * u_shadow_texel * 1.5;
    float d = texture(u_shadow, p.xy + o).r;
    s += (p.z - bias > d) ? 0.0 : 1.0;
  }
  return s * 0.25;
}

void main(){
  vec4 t = texture(u_tex, v_uv);
  vec4 alb;
  if (u_blend == 1){
    vec4 t2 = texture(u_tex2, v_uv);
    alb = vec4(mix(t.rgb, t2.rgb, clamp(v_col.a, 0.0, 1.0)) * v_col.rgb, 1.0);
  } else {
    alb = t * vec4(v_col.rgb, 1.0);
    alb.a = t.a * v_col.a;
  }
  alb *= u_tint;
  if (alb.a < u_alpha_test) discard;
  vec3 n = normalize(v_nrm);
  if (!gl_FrontFacing && u_flip == 1) n = -n;
  vec3 col;
  if (u_unlit == 1){
    col = alb.rgb;
  } else {
    float ndl = clamp((dot(n, u_sun) + 0.08) / 1.08, 0.0, 1.0);
    float sh = shadow_at();
    sh = mix(1.0, sh, u_shadow_k);
    vec3 hemi = mix(u_gnd_amb, u_sky_amb, n.z * 0.5 + 0.5);
    col = alb.rgb * (hemi + u_sun_col * ndl * sh);
  }
  col += alb.rgb * u_emissive;
  // niebla lineal, más cálida en la dirección del sol
  vec3 vd = v_wpos - u_eye;
  float dist = length(vd);
  float f = clamp((dist - u_fog.x) / (u_fog.y - u_fog.x), 0.0, 1.0) * u_fog.z * u_fog_k;
  float sg = pow(max(dot(normalize(vd), u_sun), 0.0), 6.0);
  vec3 fc = mix(u_fog_col, u_glow_col, sg * 0.55);
  col = mix(col, fc, f);
  f_col = vec4(col, 1.0);
}
"""

SHADOW_VS = """
#version 330
in vec3 in_pos; in vec2 in_uv;
uniform mat4 u_model; uniform mat4 u_lvp; uniform vec4 u_uvrect;
out vec2 v_uv;
void main(){ v_uv = u_uvrect.xy + in_uv * (u_uvrect.zw - u_uvrect.xy); gl_Position = u_lvp * u_model * vec4(in_pos, 1.0); }
"""
SHADOW_FS = """
#version 330
in vec2 v_uv; uniform sampler2D u_tex; uniform float u_alpha_test;
void main(){ if (texture(u_tex, v_uv).a < u_alpha_test) discard; }
"""

SKY_VS = """
#version 330
in vec2 in_pos; out vec2 v_ndc;
void main(){ v_ndc = in_pos; gl_Position = vec4(in_pos, 0.9999, 1.0); }
"""
SKY_FS = """
#version 330
in vec2 v_ndc; uniform mat4 u_inv_vp; uniform vec3 u_eye; uniform vec3 u_sun;
uniform vec3 u_zen; uniform vec3 u_mid; uniform vec3 u_hor; uniform vec3 u_glow;
out vec4 f_col;
void main(){
  vec4 p = u_inv_vp * vec4(v_ndc, 1.0, 1.0);
  vec3 d = normalize(p.xyz / p.w - u_eye);
  float h = d.z;
  vec3 c;
  if (h < 0.0) c = u_hor;
  else if (h < 0.18) c = mix(u_hor, u_mid, smoothstep(0.0, 0.18, h));
  else c = mix(u_mid, u_zen, smoothstep(0.18, 0.75, h));
  float s = max(dot(d, u_sun), 0.0);
  c += u_glow * (pow(s, 10.0) * 0.45 + pow(s, 120.0) * 0.8);
  // bandas suaves (degradado «de 16 bits») para un cielo menos digital
  c = floor(c * 64.0 + 0.5) / 64.0;
  f_col = vec4(c, 1.0);
}
"""

POST_VS = SKY_VS
POST_FS = """
#version 330
in vec2 v_ndc; uniform sampler2D u_img; out vec4 f_col;
void main(){
  vec2 uv = v_ndc * 0.5 + 0.5;
  vec3 c = texture(u_img, uv).rgb;
  vec3 b = textureLod(u_img, uv, 5.0).rgb + textureLod(u_img, uv, 6.5).rgb;
  c += max(b * 0.5 - 0.72, 0.0) * 0.55;          // brillo suave
  float l = dot(c, vec3(0.299, 0.587, 0.114));
  c = mix(vec3(l), c, 1.06);                       // +saturación
  c = (c - 0.5) * 1.04 + 0.5;                       // +contraste
  vec2 q = uv - 0.5;
  c *= 1.0 - dot(q * vec2(0.9, 0.7), q * vec2(0.9, 0.7)) * 0.75;  // viñeta
  f_col = vec4(clamp(c, 0.0, 1.0), 1.0);
}
"""


class Camera:
    def __init__(self, eye=(0, -8, 3), target=(0, 0, 1), fov=40.0, roll=0.0):
        self.eye = np.asarray(eye, "f8")
        self.target = np.asarray(target, "f8")
        self.fov = fov
        self.roll = roll

    def view(self):
        up = np.array([np.sin(self.roll), 0, np.cos(self.roll)])
        return look_at(self.eye, self.target, up)

    def proj(self, aspect):
        return perspective(np.radians(self.fov), aspect, 0.08, 220.0)

    def basis(self):
        f = normalize(self.target - self.eye)
        r = normalize(np.cross(f, (0, 0, 1)))
        u = np.cross(r, f)
        return f, r, u


class GPUMesh:
    def __init__(self, r, mesh):
        data = mesh.arrays()
        self.count = len(data)
        self.tris = self.count // 3
        if self.count == 0:
            self.vao = self.svao = None
            return
        self.vbo = r.ctx.buffer(data.tobytes())
        self.vao = r.ctx.vertex_array(r.prog, [(self.vbo, "3f 3f 2f 4f", "in_pos", "in_nrm", "in_uv", "in_col")])
        self.svao = r.ctx.vertex_array(r.sprog, [(self.vbo, "3f 12x 2f 16x", "in_pos", "in_uv")])


class Item:
    """Algo que dibujar este fotograma."""
    __slots__ = ("gm", "model", "tex", "tex2", "uvrect", "alpha_test", "emissive", "unlit",
                 "shadow", "tint", "blend", "fog_k", "flip")

    def __init__(self, gm, model, tex="white", tex2=None, uvrect=(0, 0, 1, 1), alpha_test=0.5,
                 emissive=0.0, unlit=False, shadow=True, tint=(1, 1, 1, 1), fog_k=1.0, flip=True):
        self.gm, self.model, self.tex, self.tex2 = gm, model, tex, tex2
        self.uvrect, self.alpha_test, self.emissive = uvrect, alpha_test, emissive
        self.unlit, self.shadow, self.tint, self.fog_k = unlit, shadow, tint, fog_k
        self.blend = tex2 is not None
        self.flip = flip


class Renderer:
    def __init__(self, width=None, height=None, msaa=None):
        self.W = width or RENDER["width"]
        self.H = height or RENDER["height"]
        ms = RENDER["msaa"] if msaa is None else msaa
        self.ctx = moderngl.create_standalone_context(backend="egl")
        c = self.ctx
        self.prog = c.program(vertex_shader=VS, fragment_shader=FS)
        self.sprog = c.program(vertex_shader=SHADOW_VS, fragment_shader=SHADOW_FS)
        self.skyprog = c.program(vertex_shader=SKY_VS, fragment_shader=SKY_FS)
        self.postprog = c.program(vertex_shader=POST_VS, fragment_shader=POST_FS)
        quad = c.buffer(np.array([-1, -1, 3, -1, -1, 3], "f4").tobytes())
        self.sky_vao = c.vertex_array(self.skyprog, [(quad, "2f", "in_pos")])
        self.post_vao = c.vertex_array(self.postprog, [(quad, "2f", "in_pos")])
        self.fbo_ms = c.framebuffer(
            color_attachments=[c.renderbuffer((self.W, self.H), 4, samples=ms)],
            depth_attachment=c.depth_renderbuffer((self.W, self.H), samples=ms))
        self.resolved_tex = c.texture((self.W, self.H), 4)
        self.resolved_tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        self.fbo_res = c.framebuffer(color_attachments=[self.resolved_tex])
        self.fbo_out = c.simple_framebuffer((self.W, self.H))
        S = RENDER["shadow_size"]
        self.shadow_tex = c.depth_texture((S, S))
        self.shadow_tex.repeat_x = self.shadow_tex.repeat_y = False
        self.shadow_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.shadow_tex.compare_func = ""
        self.fbo_shadow = c.framebuffer(depth_attachment=self.shadow_tex)
        self.textures = {}
        self.add_texture("white", T.white())
        self.shadow_center = np.array([0, 0, 0.0])
        self.shadow_radius = 14.0
        self.sun = normalize(LIGHT["sun_dir"])

    # ------------------------------------------------------------ recursos
    def add_texture(self, name, img, repeat=True):
        img = img.convert("RGBA")
        assert max(img.size) <= RENDER["tex_max"], f"textura {name} demasiado grande {img.size}"
        t = self.ctx.texture(img.size, 4, T.to_rgba_bytes(img))
        t.filter = (moderngl.NEAREST, moderngl.NEAREST)
        t.repeat_x = t.repeat_y = repeat
        self.textures[name] = t
        return name

    def upload(self, mesh):
        return GPUMesh(self, mesh)

    # ------------------------------------------------------------ render
    def _set(self, prog, name, val):
        if name in prog:
            v = np.asarray(val, "f4")
            if v.ndim == 2:
                v = v.T.copy()
            prog[name].write(v.tobytes())

    def render(self, cam, items, extra_post=None):
        c = self.ctx
        aspect = self.W / self.H
        V = cam.view()
        P = cam.proj(aspect)
        VP = P @ V
        # --- sombras
        sc = self.shadow_center
        R = self.shadow_radius
        L = look_at(sc + self.sun * 40, sc, (0, 0, 1))
        LP = ortho(-R, R, -R, R, 1.0, 90.0)
        LVP = LP @ L
        self.fbo_shadow.use()
        c.enable(moderngl.DEPTH_TEST)
        c.disable(moderngl.CULL_FACE)
        self.fbo_shadow.clear(depth=1.0)
        self._set(self.sprog, "u_lvp", LVP)
        for it in items:
            if not it.shadow or it.gm.svao is None:
                continue
            self._set(self.sprog, "u_model", it.model)
            self._set(self.sprog, "u_uvrect", it.uvrect)
            self.sprog["u_alpha_test"].value = it.alpha_test
            self.textures[it.tex].use(0)
            it.gm.svao.render()
        # --- cielo
        self.fbo_ms.use()
        c.viewport = (0, 0, self.W, self.H)
        self.fbo_ms.clear(0, 0, 0, 1, depth=1.0)
        c.disable(moderngl.DEPTH_TEST)
        sp = self.skyprog
        self._set(sp, "u_inv_vp", np.linalg.inv(VP))
        self._set(sp, "u_eye", cam.eye)
        self._set(sp, "u_sun", self.sun)
        for k, n in (("u_zen", "zenith"), ("u_mid", "mid"), ("u_hor", "horizon"), ("u_glow", "sun_glow")):
            self._set(sp, k, SKY[n])
        self.sky_vao.render()
        # --- escena
        c.enable(moderngl.DEPTH_TEST)
        p = self.prog
        self._set(p, "u_vp", VP)
        self._set(p, "u_lvp", LVP)
        self._set(p, "u_eye", cam.eye)
        self._set(p, "u_sun", self.sun)
        self._set(p, "u_sun_col", LIGHT["sun_col"])
        self._set(p, "u_sky_amb", LIGHT["sky_ambient"])
        self._set(p, "u_gnd_amb", LIGHT["ground_ambient"])
        self._set(p, "u_fog_col", FOG["color"])
        self._set(p, "u_glow_col", SKY["sun_glow"])
        self._set(p, "u_fog", (FOG["start"], FOG["end"], FOG["max"]))
        p["u_shadow_k"].value = LIGHT["shadow_strength"]
        S = RENDER["shadow_size"]
        self._set(p, "u_shadow_texel", (1 / S, 1 / S))
        p["u_tex"].value = 0
        p["u_tex2"].value = 1
        p["u_shadow"].value = 2
        self.shadow_tex.use(2)
        for it in items:
            if it.gm.vao is None:
                continue
            self._set(p, "u_model", it.model)
            nm = np.linalg.inv(it.model[:3, :3]).T
            self._set(p, "u_nmat", nm)
            self._set(p, "u_uvrect", it.uvrect)
            self._set(p, "u_tint", it.tint)
            p["u_alpha_test"].value = it.alpha_test
            p["u_emissive"].value = it.emissive
            p["u_unlit"].value = 1 if it.unlit else 0
            p["u_blend"].value = 1 if it.blend else 0
            p["u_fog_k"].value = it.fog_k
            p["u_flip"].value = 1 if it.flip else 0
            self.textures[it.tex].use(0)
            if it.blend:
                self.textures[it.tex2].use(1)
            it.gm.vao.render()
        # --- resolver MSAA + post
        c.copy_framebuffer(self.fbo_res, self.fbo_ms)
        self.resolved_tex.build_mipmaps()
        self.fbo_out.use()
        c.disable(moderngl.DEPTH_TEST)
        self.resolved_tex.use(0)
        self.postprog["u_img"].value = 0
        self.post_vao.render()
        raw = self.fbo_out.read(components=3)
        img = np.frombuffer(raw, np.uint8).reshape(self.H, self.W, 3)[::-1]
        return img

    def project(self, cam, pts):
        """Proyecta puntos de mundo a píxeles (x, y, profundidad w)."""
        VP = cam.proj(self.W / self.H) @ cam.view()
        pts = np.atleast_2d(np.asarray(pts, "f8"))
        h = np.hstack([pts, np.ones((len(pts), 1))]) @ VP.T
        w = h[:, 3:4]
        ndc = h[:, :3] / w
        x = (ndc[:, 0] * 0.5 + 0.5) * self.W
        y = (1 - (ndc[:, 1] * 0.5 + 0.5)) * self.H
        return np.stack([x, y, w[:, 0]], 1)


def save(img, path):
    Image.fromarray(img).save(path)
