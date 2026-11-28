#!/usr/bin/env python3
"""Shorts en español que más están funcionando (YouTube Data API v3) → fuente de ideas virales.

  python3 tools/ideas/yt_shorts.py [--dias 10] [--top 40] [--region ES] [--consultas "a|b|c"]

La clave NO se pasa aquí: la inyecta el proxy del entorno (Network secret del host youtube.googleapis.com,
cabecera X-Goog-Api-Key). Si falta, el script lo dice y sale con código 2.
Coste de cuota: 100 unidades por consulta de búsqueda + 1 por cada 50 vídeos (cuota gratis: 10.000/día).
Salida: ideas/fuentes/yt-AAAA-MM-DD.json (todo) y tabla markdown por pantalla (top por visitas/día).
Solo Shorts: duración ≤ 180 s (los Shorts pueden durar hasta 3 min).
"""
import argparse, datetime as dt, json, re, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

API = "https://youtube.googleapis.com/youtube/v3/"
RAIZ = Path(__file__).resolve().parents[2]
CONSULTAS = ["curiosidades", "sabías que", "datos curiosos", "qué pasaría si", "por qué", "ciencia explicada",
             "cuerpo humano curiosidades", "historia curiosa", "explicado en 1 minuto", "#shorts curiosidades"]


def get(ruta, **q):
    url = API + ruta + "?" + urllib.parse.urlencode(q, doseq=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ideas-shorts"}), timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", "replace")[:400]
        if e.code in (400, 401, 403):
            sys.exit(f"YouTube API {e.code}: falta o no vale la clave (Network secret de youtube.googleapis.com, cabecera X-Goog-Api-Key) "
                     f"o se agotó la cuota.\n{cuerpo}") if "quota" not in cuerpo.lower() else sys.exit(f"Cuota agotada: {cuerpo}")
        raise
    except urllib.error.URLError as e:
        print(f"Sin acceso a youtube.googleapis.com ({e.reason}). Hay que guardar la clave como Network secret del entorno.", file=sys.stderr)
        sys.exit(2)


def segundos(iso):
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m: return 9999
    h, mi, s = (int(x or 0) for x in m.groups()); return h * 3600 + mi * 60 + s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=10); ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--region", default="ES"); ap.add_argument("--consultas", default="")
    a = ap.parse_args()
    consultas = [c for c in a.consultas.split("|") if c] or CONSULTAS
    desde = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=a.dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids, origen = [], {}
    for q in consultas:
        r = get("search", part="snippet", q=q, type="video", videoDuration="short", order="viewCount", maxResults=25,
                publishedAfter=desde, regionCode=a.region, relevanceLanguage="es", safeSearch="moderate")
        for it in r.get("items", []):
            v = it["id"]["videoId"]
            if v not in origen: ids.append(v); origen[v] = q
    vids = []
    for i in range(0, len(ids), 50):
        r = get("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))
        for it in r.get("items", []):
            dur = segundos(it["contentDetails"].get("duration"))
            if dur > 180: continue
            st, sn = it.get("statistics", {}), it["snippet"]
            pub = dt.datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
            dias = max((dt.datetime.now(dt.timezone.utc) - pub).total_seconds() / 86400, .25)
            vistas = int(st.get("viewCount", 0))
            vids.append(dict(id=it["id"], titulo=sn["title"], canal=sn["channelTitle"], publicado=sn["publishedAt"][:10],
                             duracion_s=dur, vistas=vistas, vistas_dia=round(vistas / dias), likes=int(st.get("likeCount", 0)),
                             comentarios=int(st.get("commentCount", 0)), consulta=origen[it["id"]],
                             url=f"https://www.youtube.com/shorts/{it['id']}", tags=sn.get("tags", [])[:8]))
    vids.sort(key=lambda v: -v["vistas_dia"])
    out = RAIZ / "ideas" / "fuentes" / f"yt-{dt.date.today().isoformat()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(fecha=dt.date.today().isoformat(), dias=a.dias, region=a.region, consultas=consultas,
                                   shorts=vids), ensure_ascii=False, indent=1))
    print(f"{len(vids)} Shorts (≤180 s, últimos {a.dias} días, {a.region}) → {out.relative_to(RAIZ)}\n")
    print("| # | vistas/día | vistas | s | título | canal |\n|---|---|---|---|---|---|")
    for k, v in enumerate(vids[:a.top], 1):
        print(f"| {k} | {v['vistas_dia']:,} | {v['vistas']:,} | {v['duracion_s']} | {v['titulo'][:80]} | {v['canal'][:30]} |".replace(",", "."))


if __name__ == "__main__":
    main()
