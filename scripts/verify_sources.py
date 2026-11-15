"""Compare the saved, unmodified source images with their live public originals."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sources = [
    ('company-logo.png', 'common/img/logo.png', '既存の会社ロゴ'),
    ('foot-image.jpg', 'common/img/foot_image.jpg', '元ページに掲載された外観写真と施設案内'),
    ('careplan-illustration.png', 'common/img/careplan/img_care.png', '元ページのイラスト。保存のみ'),
    ('facility-original.png', 'common/img/img_section01.png', '現行トップページに掲載された施設内の写真'),
    ('access-map.png', 'common/img/company/map.png', '会社概要に掲載された案内図'),
]

def verify(item):
    name, remote_path, role = item
    url = 'https://waraku-f.jp/' + remote_path
    saved = (ROOT / 'site/assets/original' / name).read_bytes()
    live = urllib.request.urlopen(url, timeout=30).read()
    expected_signature = b'\x89PNG\r\n\x1a\n' if name.endswith('.png') else b'\xff\xd8'
    if not saved.startswith(expected_signature) or not live.startswith(expected_signature):
        raise RuntimeError(f'Expected an image rather than an HTML response: {name}')
    record = {'file': 'site/assets/original/' + name, 'url': url, 'role': role, 'bytes': len(saved), 'sha256': hashlib.sha256(saved).hexdigest(), 'matches_live_original': saved == live}
    if not record['matches_live_original']:
        raise RuntimeError(f'Source changed or download mismatch: {name}')
    return record

with ThreadPoolExecutor(max_workers=3) as executor:
    records = list(executor.map(verify, sources))

manifest = {'verified_date': '2026-11-15', 'original_page': 'https://waraku-f.jp/careplan', 'files': records, 'note': '原本は未編集。配信用サムネイルはリサイズ・WebP変換のみ。出典記録は第三者への利用許諾を意味しません。'}
(ROOT / 'source/assets-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'originals': len(records), 'all_bytes_match_live': all(record['matches_live_original'] for record in records)}, ensure_ascii=False))
