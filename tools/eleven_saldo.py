#!/usr/bin/env python3
"""Saldo REAL de ElevenLabs → publicaciones/creditos_eleven.json (lo usa la tarea diaria antes de generar voz).

  python3 tools/eleven_saldo.py          imprime el saldo y actualiza el JSON
Necesita que la clave (ELEVENLABS_API_KEY, nunca se imprime) tenga el permiso «User: Read» (user_read).
Si no lo tiene (401), sale con código 2 y la tarea sigue con la cuenta estimada del JSON.
"""
import datetime as dt, json, os, sys, urllib.error, urllib.request
from pathlib import Path

F = Path(__file__).resolve().parents[1] / "publicaciones" / "creditos_eleven.json"
k = os.environ.get("ELEVENLABS_API_KEY")
if not k: sys.exit("Falta ELEVENLABS_API_KEY en el entorno")
try:
    with urllib.request.urlopen(urllib.request.Request("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": k}), timeout=30) as r:
        d = json.loads(r.read())
except urllib.error.HTTPError as e:
    print(f"ElevenLabs {e.code}: la clave no puede leer el saldo (falta el permiso «User: Read»). Se usa la cuenta estimada.", file=sys.stderr)
    sys.exit(2)
usados, limite = int(d.get("character_count", 0)), int(d.get("character_limit", 0))
reset = d.get("next_character_count_reset_unix")
j = json.loads(F.read_text()) if F.exists() else {"gastos": []}
j.update(restantes_estimados=limite - usados, restantes_reales=limite - usados, usados_mes=usados, mensual=limite, plan=d.get("tier", j.get("plan")),
         fecha_dato=dt.date.today().isoformat(), fuente="API (saldo real)",
         renovacion=dt.datetime.fromtimestamp(reset, dt.timezone.utc).date().isoformat() if reset else j.get("renovacion"))
F.write_text(json.dumps(j, ensure_ascii=False, indent=1))
print(f"Saldo real: {limite - usados:,} de {limite:,} créditos (usados {usados:,}); se renuevan el {j['renovacion']}".replace(",", "."))
