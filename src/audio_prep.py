"""Recorta pausas largas de la locución y acelera ligeramente; remapea timestamps."""
import json, subprocess, sys, numpy as np, wave
B = sys.argv[1] if len(sys.argv) > 1 else "../build"
SR = 44100; MAXP = 0.30; TEMPO = 1.08
raw = subprocess.run(["ffmpeg","-v","error","-i",f"{B}/voice.mp3","-ac","1","-ar",str(SR),"-f","s16le","-"],capture_output=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32)/32768
win = int(0.02*SR); n = len(x)//win
rms = np.sqrt((x[:n*win].reshape(n,win)**2).mean(1)); quiet = rms < 10**(-40/20)
# silent runs
sil=[]; i=0
while i<n:
    if quiet[i]:
        j=i
        while j<n and quiet[j]: j+=1
        s,e=i*win/SR,j*win/SR
        if e-s>MAXP: sil.append((s,e))
        i=j
    else: i+=1
# remove the middle of each long silence (keeps MAXP total; trailing silence trimmed to 0.6)
cuts=[]
for s,e in sil:
    if e>=len(x)/SR-0.01: cuts.append((s+0.6,len(x)/SR)); continue
    cuts.append((s+MAXP/2, e-MAXP/2))
keep=[]; t=0
for s,e in cuts: keep.append((t,s)); t=e
keep.append((t,len(x)/SR)); keep=[(a,b) for a,b in keep if b>a]
fade=int(0.005*SR); parts=[]
for a,b in keep:
    seg=x[int(a*SR):int(b*SR)].copy()
    if len(seg)>2*fade: seg[:fade]*=np.linspace(0,1,fade); seg[-fade:]*=np.linspace(1,0,fade)
    parts.append(seg)
y=np.concatenate(parts)
with wave.open(f"{B}/tight.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg","-v","error","-y","-i",f"{B}/tight.wav","-af",f"atempo={TEMPO},loudnorm=I=-14:TP=-1.5:LRA=11","-ar","48000","-ac","2",f"{B}/voice_final.wav"],check=True)
def remap(t):
    out=0
    for a,b in keep:
        if t<=a: break
        out+=min(t,b)-a
    return out/TEMPO
d=json.load(open(f"{B}/alignment.json")); a=d["alignment"]
res={"characters":a["characters"],"start":[remap(t) for t in a["character_start_times_seconds"]],"end":[remap(t) for t in a["character_end_times_seconds"]],"duration":len(y)/SR/TEMPO}
json.dump(res,open(f"{B}/timing.json","w"),ensure_ascii=False)
print("silences cut",len(cuts),"new duration",round(res["duration"],2))
