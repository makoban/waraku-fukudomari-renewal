"""Validate local routes, all referenced assets, original article text and photo counts."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
from PIL import Image
import json
import re

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
issues=[]
image_files=set()
html_files=list(SITE.rglob('*.html'))
for file in html_files:
    soup=BeautifulSoup(file.read_text(),'html.parser')
    if not soup.select_one('meta[name="viewport"]'):issues.append({'file':str(file.relative_to(SITE)),'issue':'missing viewport'})
    if not soup.select_one('meta[name="robots"][content*="noindex"]'):issues.append({'file':str(file.relative_to(SITE)),'issue':'missing noindex'})
    if not soup.select_one('meta[name="description"]'):issues.append({'file':str(file.relative_to(SITE)),'issue':'missing description'})
    for element in soup.find_all(True):
        references=[]
        for attribute in ['src','href','data-image']:
            if element.get(attribute):references.append(element[attribute])
        if element.get('srcset'):references.extend(part.strip().split()[0] for part in element['srcset'].split(','))
        for url in references:
            parsed=urlsplit(url)
            if parsed.scheme or parsed.netloc:continue
            path=(file.parent/unquote(parsed.path)).resolve() if parsed.path else file.resolve()
            if path.is_dir():path=path/'index.html'
            if not path.exists():issues.append({'file':str(file.relative_to(SITE)),'issue':'missing local target','url':url});continue
            if path.suffix.lower() in ['.webp','.jpg','.jpeg','.png']:image_files.add(path)
            if parsed.fragment and path.suffix=='.html':
                target=soup if path==file.resolve() else BeautifulSoup(path.read_text(),'html.parser')
                if not target.find(id=parsed.fragment):issues.append({'file':str(file.relative_to(SITE)),'issue':'missing anchor','url':url})
    for nav in soup.select('.global-site-nav,.footer-nav,.menu-whole-site'):
        if any('waraku-f.jp' in a.get('href','') for a in nav.select('a')):issues.append({'file':str(file.relative_to(SITE)),'issue':'main navigation links to old site'})
for path in image_files:
    try:
        with Image.open(path) as im:im.verify()
    except Exception as error:issues.append({'file':str(path.relative_to(SITE)),'issue':'invalid image','error':str(error)})
qa=json.loads((ROOT/'qa/content-migration.json').read_text())
for post in qa['articles']:
    soup=BeautifulSoup((SITE/post['file']).read_text(),'html.parser')
    photos=len(soup.select('.post-body [data-image]'))
    if photos!=post['photos']:issues.append({'file':post['file'],'issue':'article photo count differs','source':post['photos'],'rendered':photos})
    if not post['matches']:issues.append({'file':post['file'],'issue':'article text differs'})
report={'html_pages':len(html_files),'referenced_image_files':len(image_files),'article_texts_checked':len(qa['articles']),'article_photos_checked':sum(post['photos'] for post in qa['articles']),'issues':issues,'passed':not issues}
(ROOT/'qa/static-whole-site.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(issues))
