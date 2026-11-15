"""Create responsive, compressed delivery copies; keep source images unchanged."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import re
import subprocess
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'site/assets'

def webp(source, target, width=None, quality=83):
    command = ['cwebp', '-quiet', '-q', str(quality), '-metadata', 'none']
    if width:
        command += ['-resize', str(width), '0']
    subprocess.run(command + [str(source), '-o', str(target)], check=True)

for source_name, output_name in [('consultation-hero', 'consultation'), ('family-consultation', 'family')]:
    for width in (480, 800, 1280):
        webp(ROOT / f'design/generated/{source_name}.png', ASSETS / f'generated/{output_name}-{width}.webp', width)
webp(ROOT / 'design/generated/desktop-design-concept.png', ASSETS / 'generated/design-concept.webp', quality=90)
for source, output, widths in [
    ('facility-original.png', 'facility', (360, 603)),
    ('foot-image.jpg', 'footer', (360, 527)),
]:
    for width in widths:
        webp(ASSETS / 'original' / source, ASSETS / f'original/{output}-{width}.webp', width, 90)

class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        self.parts.extend(value for key, value in attrs if key == 'data-caption' and value)

collector = TextCollector()
for page in (ROOT / 'site').glob('*.html'):
    collector.feed(page.read_text())
characters = ''.join(sorted(set(''.join(collector.parts) + 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789×＋↓↑↗/.,:;!?-〜©（） ')))
font_folder = ASSETS / 'fonts'
font_folder.mkdir(exist_ok=True)
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
for family, filename in [
    ('Noto Sans JP:wght@400..700', 'noto-sans-jp.woff2'),
    ('Zen Old Mincho:wght@600', 'zen-old-mincho.woff2'),
]:
    query = urllib.parse.urlencode({'family': family, 'display': 'swap', 'text': characters})
    css_url = 'https://fonts.googleapis.com/css2?' + query
    request = urllib.request.Request(css_url, headers={'User-Agent': user_agent})
    css = urllib.request.urlopen(request, timeout=30).read().decode()
    font_url = re.search(r'url\((https://[^)]+)\)', css).group(1)
    font = urllib.request.urlopen(font_url, timeout=30).read()
    if not font.startswith(b'wOF2'):
        raise RuntimeError(f'Expected WOFF2 for {family}')
    (font_folder / filename).write_bytes(font)

sizes = [{'file': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(ASSETS.rglob('*')) if path.is_file()]
(ROOT / 'qa/asset-sizes.json').write_text(json.dumps(sizes, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'delivery_files': len(sizes), 'fonts_bytes': sum(p.stat().st_size for p in font_folder.glob('*.woff2')), 'sizes': {item['file']: item['bytes'] for item in sizes}}, ensure_ascii=False, indent=2))
