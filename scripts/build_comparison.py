"""Build a real-screenshot comparison report with untouched PNG originals."""
from pathlib import Path
from PIL import Image
from html import escape
from zipfile import ZipFile, ZIP_STORED
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'site/comparison'
record=json.loads((ROOT/'source/comparison-captures/capture-manifest.json').read_text())
captures=record['captures']
for item in captures:
    source=ROOT/item['capture_file']
    with Image.open(source) as image:
        item['image_width'],item['image_height']=image.size
    expected=(item['viewport']['width']*item['devicePixelRatio'],item['viewport']['height']*item['devicePixelRatio'])
    if item['image_width']!=expected[0] or abs(item['image_height']-expected[1])>1:
        raise ValueError(f'Unexpected screenshot dimensions: {source}')
    item['expected_image_dimensions']=list(expected)
    item['browser_rounding_height_pixels']=item['image_height']-expected[1]
    item['png_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    item['png_bytes']=source.stat().st_size
    name=source.stem
    thumb_width=720 if item['mode']=='desktop' else 390
    item['thumbnail']='assets/'+name+f'-{thumb_width}.webp'
    item['large']='assets/'+name+'.webp'
    item['original']='assets/png/'+source.name
    for filename,width,quality in [(item['thumbnail'],thumb_width,92),(item['large'],item['image_width'],94)]:
        if (OUT/filename).exists() and (OUT/filename).stat().st_mtime>=source.stat().st_mtime:
            continue
        subprocess.run(['cwebp','-quiet','-q',str(quality),'-resize',str(width),'0',str(source),'-o',str(OUT/filename)],check=True)

(OUT/'captures.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
screens=[]
for item in captures:
    if item['id'] not in [screen['id'] for screen in screens]:screens.append({'id':item['id'],'title':item['screen']})

notes={
    'home':'既存は施設外観を大きく見せる構成。現在の案はイラストと見出しを先に置き、サービスへの入口を整理しています。',
    'rehabilitation':'現在の案は、6つのリハビリ内容への入口をページ上部に配置しています。',
    'dayservice':'サービス説明、写真、おすすめの対象、送迎案内を、画面幅に応じて配置しています。',
    'cafe':'認知症対応型デイサービスの説明を見出しの近くに置き、写真と一緒に読み進める構成です。',
    'careplan':'見出し、相談のイメージ、電話ボタンを最初の画面にまとめています。',
    'recruit':'既存はホーム内の求人欄へ移動した状態、現在の案は独立した求人ページの先頭です。ページ構成の違いも含めて比較しています。',
    'blog':'既存は一覧の中に記事本文を掲載。現在の案は写真付きの一覧と検索・月の絞り込みを配置しています。',
    'company':'基本情報、住所、連絡先を区切って掲載し、施設写真と案内図を併記しています。',
    'article':'同じ記事「生産性向上のための取り組み」（2025年3月21日）の画面です。本文・投稿日・掲載写真を引き継いでいます。',
    'archive':'同じ2023年11月の画面です。現在の案は対象月を見出しに表示し、記事の個別ページへ進む構成です。'
}
lookup={(item['id'],item['mode'],item['version']):item for item in captures}

def figure(identifier,version):
    desktop=lookup[(identifier,'desktop',version)]
    mobile=lookup[(identifier,'mobile',version)]
    label='既存サイト' if version=='before' else '現在のリニューアル案'
    attributes=[]
    for mode,item in [('desktop',desktop),('mobile',mobile)]:
        for key in ['thumbnail','large','original']:
            attributes.append(f'data-{mode}-{key}="{item[key]}"')
        attributes.append(f'data-{mode}-width="{item["image_width"]}"')
        attributes.append(f'data-{mode}-height="{item["image_height"]}"')
    return f'<figure class="shot-figure"><button class="shot-button" type="button" data-shot data-screen="{identifier}" data-version="{version}" {" ".join(attributes)} aria-label="{escape(desktop["screen"])}・{label}のスクリーンショットを拡大"><img src="{desktop["thumbnail"]}" srcset="{desktop["thumbnail"]} 720w, {desktop["large"]} 1440w" sizes="(min-width:1000px) 560px, 45vw" width="1440" height="1000" loading="lazy" decoding="async" alt="{escape(desktop["screen"])}の{label}の実画面"><span class="zoom-hint" aria-hidden="true">＋ 拡大</span></button><figcaption><a class="source-link" href="{escape(desktop["url"],quote=True)}" target="_blank" rel="noopener noreferrer">ページを開く ↗<span class="sr-only">（新しいタブ）</span></a><a class="original-link" href="{desktop["original"]}" download>PNG原本を保存 ↓</a></figcaption></figure>'

rows=[]
for index,screen in enumerate(screens,1):
    rows.append(f'<section class="comparison-row" id="{screen["id"]}" data-comparison-row data-page="{screen["id"]}"><div class="row-title"><h2><span class="row-number">{index:02}</span>{screen["title"]}</h2><a href="#{screen["id"]}" class="row-anchor" aria-label="{screen["title"]}の比較へのリンク">#</a></div><table class="shot-table"><caption class="sr-only">{screen["title"]}の既存サイトと現在の案の比較</caption><thead><tr><th scope="col"><span class="version-dot before-dot"></span>既存サイト</th><th scope="col"><span class="version-dot after-dot"></span>現在のリニューアル案</th></tr></thead><tbody><tr><td>{figure(screen["id"],"before")}</td><td>{figure(screen["id"],"after")}</td></tr></tbody></table><p class="comparison-note"><span>見比べるポイント</span>{notes[screen["id"]]}</p></section>')

options=''.join(f'<option value="{screen["id"]}">{screen["title"]}</option>' for screen in screens)
index_links=''.join(f'<button type="button" data-show-screen="{screen["id"]}">{screen["title"]} <span aria-hidden="true">↓</span></button>' for screen in screens)
html=f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow, noarchive"><meta name="description" content="WARAKU福泊の既存サイトと現在のリニューアル案を、同じ画面サイズで撮影した実際のスクリーンショットで比較します。PC・スマホの10画面を掲載しています。"><meta name="theme-color" content="#fbf8f2"><title>既存と現在のスクリーンショット比較｜WARAKU福泊</title><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="comparison.css"><script src="comparison.js" defer></script></head>
<body id="top"><a href="#main" class="skip-link">比較表へ移動</a><header class="report-header"><div class="wrap header-inner"><a class="wordmark" href="../">WARAKU <span>福泊</span></a><a class="return-link" href="../">リニューアル案を見る ↗</a></div></header>
<main id="main"><section class="intro wrap"><p class="eyebrow">WEBSITE RENEWAL / BEFORE &amp; AFTER</p><h1><span class="phrase">既存と現在を、</span><span class="phrase">画面で比較。</span></h1><p class="lead">既存サイトとリニューアル案を、<span class="phrase">同じ画面サイズで撮影しました。</span>主要8ページと、ブログ記事・月別一覧の<span class="phrase">代表2画面を並べています。</span></p><div class="meta-line"><span>撮影：2026年11月15日</span><span>10画面 × PC・スマホ</span><span>実際の表示を使用</span></div><details class="capture-conditions"><summary>撮影条件と比較の範囲</summary><div><p>PCは1440 × 1000px、スマホは390 × 844pxの画面サイズで、同じブラウザー条件で撮影しています。スマホはChromiumのモバイルエミュレーション・DPR 2、PCはDPR 1です。</p><p>各ページの最初の表示を比較しています。求人情報は、既存サイトのホーム内にある求人欄へ移動した状態です。</p><p>旧サイトはスマホでも幅1200pxでレイアウトし、画面に縮小表示されます。現在の案は幅390pxに合わせて表示されます。サイトごとのviewport指定をそのまま反映しています。</p><p>スクリーンショットの内容の修整や、生成画像への置き換えは行っていません。拡大用・配信用のWebPと、撮影したままのPNG原本を保存しています。</p><a href="captures.json">撮影日時・URL・画像の記録を見る ↗</a></div></details><nav class="page-index" aria-label="比較する画面">{index_links}</nav></section>
<div class="toolbar-shell"><div class="wrap toolbar-inner"><fieldset class="device-switch"><legend class="sr-only">表示する画面サイズ</legend><label><input type="radio" name="device" value="desktop" checked><span>PC</span></label><label><input type="radio" name="device" value="mobile"><span>スマホ</span></label></fieldset><label class="page-select"><span class="sr-only">比較するページ</span><select id="page-filter" aria-label="比較するページ"><option value="all">すべての画面</option>{options}</select></label><div class="toolbar-actions"><button id="print-button" type="button">印刷・PDF保存</button><a href="waraku-screenshots-20261115.zip" download>画像をまとめて保存 ↓</a></div><p id="view-status" class="view-status" role="status" aria-live="polite">PC 1440 × 1000 / 10画面</p></div></div>
<div class="wrap comparisons" id="comparisons">{''.join(rows)}</div></main>
<footer class="wrap report-footer"><p>比較画像は撮影時点の表示です。リニューアル案の人物イラストはイメージとして作成したもので、実際のスタッフ・ご利用者様の肖像ではありません。</p><div><a href="../">リニューアル案を見る ↗</a><a href="https://waraku-f.jp/" target="_blank" rel="noopener noreferrer">既存サイトを見る ↗</a><a href="https://github.com/makoban/waraku-fukudomari-renewal">GitHub ↗</a><a href="#top">先頭へ ↑</a></div></footer>
<dialog id="zoom-dialog" aria-labelledby="zoom-title"><div class="zoom-toolbar"><p id="zoom-title"></p><button id="zoom-close" type="button" aria-label="拡大表示を閉じる">×</button></div><img id="zoom-image" alt=""><div class="zoom-footer"><a id="zoom-original" download>PNG原本を保存 ↓</a><a id="zoom-new-tab" target="_blank" rel="noopener noreferrer">原寸画像を別タブで開く ↗</a></div></dialog>
</body></html>'''
(OUT/'index.html').write_text(html+'\n')
readme='WARAKU福泊 既存・現在のスクリーンショット比較\n撮影日: 2026-11-15\n主要8ページと記事・月別一覧の代表2画面、PC/スマホで合計40画像。\nPC: 1440x1000 / DPR1。スマホ: 390x844 / DPR2。\nスマホPNGは幅780px、高さ1687〜1688px。ブラウザーの描画丸めをそのまま保存しています。\n各サイトのviewport指定をそのまま適用したブラウザー表示です。\n求人情報の既存画像はトップページ内の求人欄へ移動した状態です。\nPNG原本の内容に生成や修整は加えていません。\n撮影時点の案のソースコミット: '+record['after_source_commit']+'\n'
with ZipFile(OUT/'waraku-screenshots-20261115.zip','w',compression=ZIP_STORED) as archive:
    archive.writestr('README.txt',readme)
    archive.write(OUT/'captures.json','captures.json')
    for item in captures:
        archive.write(ROOT/item['capture_file'],item['mode']+'/'+Path(item['capture_file']).name)
print(json.dumps({'screens':len(screens),'captures':len(captures),'archive_bytes':(OUT/'waraku-screenshots-20261115.zip').stat().st_size},ensure_ascii=False))
