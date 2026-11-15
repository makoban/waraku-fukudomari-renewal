"""Collect public source HTML and exact source media for the whole-site renewal."""
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import hashlib
import json
import re
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'source'
PAGES = SOURCE / 'pages'
MEDIA = ROOT / 'site/assets/source'
PAGES.mkdir(exist_ok=True)
MEDIA.mkdir(exist_ok=True)
HEADERS = {'User-Agent': 'BANTEX-Website-Renewal/1.0', 'Accept-Encoding': 'identity'}

def read(url):
    with urlopen(Request(url, headers=HEADERS), timeout=45) as response:
        data = bytearray()
        while chunk := response.read(262144):
            data.extend(chunk)
            time.sleep(.032)  # one request at a time, at most about 8 MiB/s
        return bytes(data), response.headers.get_content_type(), response.geturl()

def canonical(url):
    parsed = urlparse(urljoin('https://waraku-f.jp/', url))
    return 'https://waraku-f.jp' + parsed.path.rstrip('/') if parsed.path.rstrip('/') else 'https://waraku-f.jp/'

urls = json.loads((SOURCE / 'sitemap-urls.json').read_text())
urls = sorted(set(urls + ['https://waraku-f.jp/blog']))
records = []
for index, url in enumerate(urls):
    name = hashlib.sha256(url.encode()).hexdigest()[:16] + '.html'
    target = PAGES / name
    if target.exists():
        data = target.read_bytes()
        status = 'cached'
    else:
        try:
            data, content_type, final_url = read(url)
            if content_type != 'text/html':
                raise ValueError(f'Expected HTML: {content_type}')
            target.write_bytes(data)
            status = 'downloaded'
        except Exception as error:
            records.append({'url': url, 'error': str(error)})
            print(f'PAGE ERROR {url}: {error}', flush=True)
            continue
    soup = BeautifulSoup(data, 'html.parser')
    records.append({'url': url, 'file': str(target.relative_to(ROOT)), 'title': soup.title.get_text() if soup.title else '', 'sha256': hashlib.sha256(data).hexdigest()})
    if index % 20 == 0:
        print(f'Pages {index + 1}/{len(urls)} ({status})', flush=True)
(SOURCE / 'page-manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')

assets = {}
for item in records:
    if 'file' not in item:
        continue
    soup = BeautifulSoup((ROOT / item['file']).read_bytes(), 'html.parser')
    regions = soup.select('#blogLeft .wp-post, #section01, #section02, #section03, #section04, #dayservice, #dayService, #cafe, #flowDay, #carePlan, #company, #rehabili')
    for region in regions:
        for tag in region.select('img[src], a[href]'):
            raw = tag.get('src') if tag.name == 'img' else tag.get('href')
            full = urljoin(item['url'], raw)
            if not re.search(r'\.(?:jpe?g|png|gif|webp)(?:\?|$)', full, re.I):
                continue
            if urlparse(full).netloc not in ['waraku-f.jp', 'www.waraku-f.jp']:
                continue
            full = full.replace('http://', 'https://')
            assets.setdefault(full, set()).add(item['url'])

# Main-page images which are embedded in CSS or have an empty alt attribute.
extra = ['common/img/img_section01.png', 'common/img/map.png', 'common/img/map_list.png', 'common/img/bg_top.jpg', 'common/img/banner_work.png', 'common/img/adopt_ttl.png', 'common/img/adopt_text.png', 'common/img/adopt_contact-message.png', 'common/img/adopt_table.png', 'common/img/dayservice/img_day.png', 'common/img/dayservice/img_flow.jpg', 'common/img/cafe/img_cafe.png', 'common/img/cafe/flow.jpg', 'common/img/company/map.png']
extra += [f'common/img/reha/bg_reha{i:02}.jpg' for i in range(1, 7)]
for path in extra:
    assets.setdefault('https://waraku-f.jp/' + path, set()).add('https://waraku-f.jp/')

existing_path = SOURCE / 'media-manifest.json'
existing = {item['url']: item for item in json.loads(existing_path.read_text())} if existing_path.exists() else {}
media_records = []
for index, (url, pages) in enumerate(sorted(assets.items())):
    parsed = urlparse(url)
    filename = hashlib.sha256(url.encode()).hexdigest()[:12] + '-' + parsed.path.rsplit('/', 1)[-1]
    target = MEDIA / filename
    try:
        if target.exists() and url in existing:
            record = existing[url]
            record['source_pages'] = sorted(pages)
        else:
            data, content_type, final_url = read(url)
            if not content_type.startswith('image/'):
                raise ValueError(f'Expected image, received {content_type}')
            target.write_bytes(data)
            record = {'url': url, 'file': str(target.relative_to(ROOT)), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'content_type': content_type, 'source_pages': sorted(pages)}
        media_records.append(record)
    except Exception as error:
        media_records.append({'url': url, 'error': str(error), 'source_pages': sorted(pages)})
        print(f'IMAGE ERROR {url}: {error}', flush=True)
    if index % 30 == 0:
        print(f'Media {index + 1}/{len(assets)}', flush=True)
        existing_path.write_text(json.dumps(media_records, ensure_ascii=False, indent=2) + '\n')
existing_path.write_text(json.dumps(media_records, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'pages': len(records), 'page_errors': sum('error' in r for r in records), 'images': len(media_records), 'image_errors': sum('error' in r for r in media_records), 'image_bytes': sum(r.get('bytes', 0) for r in media_records)}, ensure_ascii=False), flush=True)
