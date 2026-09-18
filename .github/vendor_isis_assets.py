from pathlib import Path
from urllib.request import Request, urlopen
import time

FILES = {
    "https://i.postimg.cc/mDmVgsh8/card-isis.png": "assets/egypt/isis/card.png",
    "https://i.postimg.cc/j5xZT5qc/isis-do-egito-andando.gif": "assets/egypt/isis/walk.gif",
    "https://i.postimg.cc/LX9NSX4x/isis-do-egito-parada.gif": "assets/egypt/isis/idle.gif",
    "https://i.postimg.cc/NMsptMGm/isis-do-egito-ataque-normal.gif": "assets/egypt/isis/attack-normal.gif",
    "https://i.postimg.cc/63MzpXTk/isis-do-egito-especial.gif": "assets/egypt/isis/special.gif",
    "https://i.postimg.cc/tTq2bTRz/isis-poder-do-especial.gif": "assets/egypt/isis/power-special.gif",
}

def download(url, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(4):
        try:
            req = Request(url, headers={
                "User-Agent": "Mozilla/5.0 Rampage-asset-vendor/1.0",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            })
            with urlopen(req, timeout=60) as response:
                data = response.read()
            if path.suffix.lower() == ".gif":
                if not (data.startswith(b"GIF87a") or data.startswith(b"GIF89a")):
                    raise RuntimeError(f"{url} did not return a GIF")
            elif path.suffix.lower() == ".png":
                if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise RuntimeError(f"{url} did not return a PNG")
            if len(data) < 128:
                raise RuntimeError(f"{url} returned an implausibly small file")
            path.write_bytes(data)
            print(f"saved {path} ({len(data)} bytes)")
            return
        except Exception as exc:
            last = exc
            if attempt < 3:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to download {url}: {last}")

for source, target in FILES.items():
    download(source, target)

index = Path("index.html")
text = index.read_text(encoding="utf-8")
for source, target in FILES.items():
    if source not in text:
        raise SystemExit(f"Expected Isis source URL not found in index.html: {source}")
    text = text.replace(source, target)
if "i.postimg.cc/" in text:
    raise SystemExit("Postimg reference still remains in index.html")
index.write_text(text, encoding="utf-8")

validator = Path(".github/rebalance_war_units_v3.py")
v = validator.read_text(encoding="utf-8")
for source, target in FILES.items():
    v = v.replace(source, target)
validator.write_text(v, encoding="utf-8")

for target in FILES.values():
    if target not in text:
        raise SystemExit(f"Local Isis asset is not referenced: {target}")

print("Isis assets vendored locally and runtime references rewritten.")
