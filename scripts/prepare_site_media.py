"""Make responsive WebP copies without retouching or changing image content."""
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image, ImageOps
import hashlib
import json
import re
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'source'
OUTPUT = ROOT / 'site/assets/media'
OUTPUT.mkdir(exist_ok=True)
raw = {r['url']: r for r in json.loads((SOURCE / 'media-manifest.json').read_text()) if 'file' in r}
selected = set(url for url in raw if '/common/img/' in url)
for row in json.loads((SOURCE / 'page-manifest.json').read_text()):
    if 'file' not in row:
        continue
    soup = BeautifulSoup((ROOT / row['file']).read_text(encoding='utf-8'), 'html.parser')
    for img in soup.select('#blogLeft .wp-post img'):
        url = urljoin(row['url'], img['src']).replace('http://', 'https://')
        parent = img.find_parent('a')
        full = urljoin(row['url'], parent['href']).replace('http://', 'https://') if parent and parent.get('href') else url
        selected.add(full if full in raw else url)

manifest_path = SOURCE / 'derivatives-manifest.json'
cached = {r['url']: r for r in json.loads(manifest_path.read_text())} if manifest_path.exists() else {}
records = []
started = time.monotonic()
read_bytes = 0
for index, url in enumerate(sorted(selected)):
    item = raw[url]
    if url in cached and cached[url]['original_sha256'] == item['sha256'] and all((ROOT / variant['file']).exists() for variant in cached[url]['variants']):
        records.append(cached[url])
        continue
    source = ROOT / item['file']
    read_bytes += source.stat().st_size
    delay = read_bytes / (16 * 1024 * 1024) - (time.monotonic() - started)
    if delay > 0:
        time.sleep(delay)
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA' if 'transparency' in image.info else 'RGB')
        width, height = image.size
        widths = sorted(set([min(width, value) for value in (480, 960, 1600)]))
        variants = []
        for output_width in widths:
            out = OUTPUT / (hashlib.sha256(url.encode()).hexdigest()[:12] + f'-{output_width}.webp')
            copy = image.copy()
            copy.thumbnail((output_width, round(height * output_width / width)), Image.Resampling.LANCZOS)
            copy.save(out, 'WEBP', quality=89 if '/common/img/' in url else 82, method=4)
            variants.append({'file': str(out.relative_to(ROOT)), 'width': copy.width, 'height': copy.height, 'bytes': out.stat().st_size})
            copy.close()
        record = {'url': url, 'original_file': item['file'], 'original_sha256': item['sha256'], 'width': width, 'height': height, 'variants': variants}
        records.append(record)
        image.close()
    if index % 20 == 0:
        manifest_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
        print(f'Prepared {index + 1}/{len(selected)} originals', flush=True)
manifest_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'originals_used': len(records), 'webp_files': sum(len(r['variants']) for r in records), 'webp_bytes': sum(v['bytes'] for r in records for v in r['variants'])}), flush=True)
