"""Create locally served, Unicode-ranged Japanese font subsets for all pages."""
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json
import re

ROOT=Path(__file__).resolve().parents[1]
FONTS=ROOT/'site/assets/fonts'
main_pages=['index.html','rehabilitation/index.html','dayservice/index.html','cafe/index.html','careplan/index.html','recruit/index.html','company/index.html','blog/index.html','design.html']
core_text=''
all_text=''
serif_text=''
for page in (ROOT/'site').rglob('*.html'):
    soup=BeautifulSoup(page.read_text(),'html.parser')
    text=soup.get_text()
    all_text+=text
    if str(page.relative_to(ROOT/'site')) in main_pages:
        core_text+=text
    serif_text+=''.join(e.get_text() for e in soup.select('h1,h2,h3,.keep,.contact-number,.brand,.footer-wordmark,.service-number,.nav-number'))
latin=''.join(chr(c) for c in range(32,127))+'©×＋〜↗↓↑〒、。・「」“”'
faces=[]
metadata=[]
user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
def ranges(text):
    points=sorted(set(map(ord,text))); groups=[]
    start=last=points[0]
    for point in points[1:]:
        if point==last+1:last=point
        else:
            groups.append((start,last));start=last=point
    groups.append((start,last))
    return ','.join('U+'+format(a,'X')+('-'+format(b,'X') if b!=a else '') for a,b in groups)

for family,query,name,weight,text in [
    ('Noto Sans JP','Noto Sans JP:wght@400..700','noto-sans-jp','400 700',all_text),
    ('Zen Old Mincho','Zen Old Mincho:wght@600','zen-old-mincho','500 600',serif_text),
]:
    allowed=set(text+latin)
    core=[char for char,count in Counter(core_text+latin*50).most_common() if char in allowed and not char.isspace()]
    extra=sorted(set(text+latin)-set(core)-set('\n\r\t'))
    ordered=list(dict.fromkeys(latin+''.join(core)+''.join(extra)))
    chunks=[''.join(ordered[i:i+500]) for i in range(0,len(ordered),500)]
    for index,chunk in enumerate(chunks):
        filename=name+('' if index==0 else '-'+str(index+1))+'.woff2'
        css_url='https://fonts.googleapis.com/css2?'+urlencode({'family':query,'display':'swap','text':chunk})
        css=urlopen(Request(css_url,headers={'User-Agent':user_agent}),timeout=30).read().decode()
        font_url=re.search(r'url\((https://[^)]+)\)',css).group(1)
        font=urlopen(font_url,timeout=30).read()
        if not font.startswith(b'wOF2'):raise ValueError('Expected WOFF2')
        (FONTS/filename).write_bytes(font)
        faces.append(f'@font-face{{font-family:"{family}";src:url("{filename}") format("woff2");font-weight:{weight};font-style:normal;font-display:swap;unicode-range:{ranges(chunk)}}}')
        metadata.append({'file':filename,'bytes':len(font),'characters':len(chunk)})
(FONTS/'fonts.css').write_text('\n'.join(faces)+'\n')
(ROOT/'qa/font-subsets.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(json.dumps({'subsets':len(metadata),'bytes':sum(r['bytes'] for r in metadata),'metadata':metadata},ensure_ascii=False))
