"""Build display-size GIFs without changing original art or combat timelines."""
from pathlib import Path
from PIL import Image, GifImagePlugin
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent.parent
html_path = ROOT / 'index.html'
html = html_path.read_text()
assets_block = html[html.index('const ASSETS ='):html.index('const BOOT_CACHE_NAME')]
assets = dict(re.findall(r"\b(\w+):'(assets/[^']+\.gif)'", assets_block))
output = ROOT / 'assets/runtime'
output.mkdir(parents=True, exist_ok=True)
args = argparse.ArgumentParser()
args.add_argument('--keys', nargs='+', help='Verify a subset without changing the game manifests')
options = args.parse_args()
if options.keys:
    assets = {key: assets[key] for key in options.keys}
mapping = {}
report = []
for key, source in assets.items():
    original_path = ROOT / source
    if not original_path.is_file():
        raise RuntimeError('Missing original: ' + source)
    target = output / (key + '.gif')
    with Image.open(original_path) as image:
        width, height = image.size
        # Body sprites display around 100-300 pixels. Keep a little extra
        # resolution for zoom; wide flame/wave effects get a larger budget.
        longest = 512 if any(word in key.lower() for word in ('power', 'wave')) else 384
        scale = min(1.0, longest / max(width, height))
        size = (max(1, round(width * scale)), max(1, round(height * scale)))
        durations, frames = [], []
        loop = image.info.get('loop', 0)
        for index in range(image.n_frames):
            image.seek(index)
            durations.append(max(20, int(image.info.get('duration', 100))))
            rgba = image.convert('RGBA').resize(size, Image.Resampling.LANCZOS)
            # GIF has one transparent palette entry. Keep alpha separate from
            # colour quantization to avoid a dark or opaque rectangle at edges.
            alpha = rgba.getchannel('A')
            palette_frame = rgba.convert('RGB').quantize(colors=255, method=Image.Quantize.FASTOCTREE)
            # Native Pillow operations keep this build linear without Python
            # iterating through hundreds of millions of individual pixels.
            frame = palette_frame.point([min(255, value + 1) for value in range(256)])
            palette = palette_frame.getpalette()[:765]
            frame.putpalette([0, 0, 0] + palette + [0] * (765 - len(palette)))
            frame.paste(0, mask=alpha.point([255 if value < 128 else 0 for value in range(256)]))
            frame.info['transparency'] = 0
            frames.append(frame)
        # Write each original frame explicitly. The normal save_all encoder
        # merges identical frames; that would change combat animation indexes.
        with target.open('wb') as stream:
            header, _ = GifImagePlugin.getheader(frames[0], info={'loop': loop, 'background': 0})
            for block in header:
                stream.write(block)
            for frame, duration in zip(frames, durations):
                for block in GifImagePlugin.getdata(frame, duration=duration, transparency=0,
                                                   disposal=2, include_color_table=True):
                    stream.write(block)
            stream.write(b';')
        with Image.open(target) as verified:
            actual_durations = []
            for index in range(verified.n_frames):
                verified.seek(index)
                actual_durations.append(int(verified.info.get('duration', 100)))
            if actual_durations != durations:
                raise RuntimeError('Animation frame/timing changed: ' + source)
        mapping[key] = target.relative_to(ROOT).as_posix()
        report.append({'key': key, 'original': source, 'runtime': mapping[key],
                       'originalSize': [width, height], 'runtimeSize': list(size), 'frames': len(frames),
                       'durationMs': sum(durations), 'originalBytes': original_path.stat().st_size,
                       'runtimeBytes': target.stat().st_size})
        for frame in frames:
            frame.close()
        print(key, source, size, len(frames), target.stat().st_size, flush=True)

if options.keys:
    raise SystemExit(0)

start = '// BEGIN GENERATED DISPLAY SPRITES'
end = '// END GENERATED DISPLAY SPRITES'
display_code = start + '\nconst ORIGINAL_ASSETS=Object.freeze({...ASSETS});\nObject.assign(ASSETS,' + json.dumps(mapping, separators=(',', ':')) + ');\n' + end + '\n'
if start in html:
    html = re.sub(re.escape(start) + r'[\s\S]*?' + re.escape(end) + r'\n?', display_code, html, count=1)
else:
    html = html.replace('const BOOT_CACHE_NAME=', display_code + '\nconst BOOT_CACHE_NAME=', 1)
manifest_match = re.search(r'const BOOT_ASSET_MANIFEST=Object.freeze\((\{.*?\})\);', html)
manifest = json.loads(manifest_match[1])
# Native flame alpha frames remain the source of collision truth, independently
# of the display-size visual GIF. Other full-size GIFs remain as fallback files.
native_collision = {assets.get('magePower'), assets.get('egyptMagePower')}
for key, source in assets.items():
    if source not in native_collision:
        manifest.pop(source, None)
    path = mapping[key]
    manifest[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:20]
encoded = json.dumps(manifest, separators=(',', ':'))
html = html[:manifest_match.start(1)] + encoded + html[manifest_match.end(1):]
html_path.write_text(html)
sw = ROOT / 'sw.js'
sw.write_text(re.sub(r'const ASSET_REVISIONS=Object.freeze\(\{.*?\}\);',
                     'const ASSET_REVISIONS=Object.freeze(' + encoded + ');', sw.read_text()))
(output / 'sprite-report.json').write_text(json.dumps(report, indent=2) + '\n')
print('Total original bytes:', sum(r['originalBytes'] for r in report))
print('Total runtime bytes:', sum(r['runtimeBytes'] for r in report))
