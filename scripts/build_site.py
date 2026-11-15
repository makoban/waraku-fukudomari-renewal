"""Build every content page and blog archive using the saved public source."""
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, NavigableString
from html import escape
from collections import defaultdict
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
SOURCE = ROOT / 'source'
ORIGIN = 'https://waraku-f.jp/'
PAGE_ROWS = json.loads((SOURCE / 'page-manifest.json').read_text())
SOURCES = {row['url'].rstrip('/'): row for row in PAGE_ROWS if 'file' in row}
DERIVATIVES = {row['url']: row for row in json.loads((SOURCE / 'derivatives-manifest.json').read_text())}
NAV = [('ホーム', ''), ('充実のリハビリ', 'rehabilitation/'), ('デイサービス福泊', 'dayservice/'), ('福泊カフェ', 'cafe/'), ('ケアプラン福泊', 'careplan/'), ('求人情報', 'recruit/'), ('スタッフブログ', 'blog/'), ('会社概要', 'company/')]
PROTECTED = ['認知症対応型', 'デイサービス福泊', 'ケアプラン福泊', '福泊カフェ', 'WARAKU福泊', '株式会社和楽', 'ケアマネジャー', '介護福祉士', '岡山市中区', '岡山市東区', 'ケン君', '高齢者', '機能訓練', 'レクリエーション', 'リハビリテーション', 'リハビリ体操', 'バイタルチェック', '生活機能', '日常生活', 'ストレスケア', '認知症', 'ご利用者様', 'ご家族様', 'デイサービス', 'ケアプラン', 'スタッフ']
BUILT = []

def source(slug=''):
    row = SOURCES[(ORIGIN + slug).rstrip('/')]
    return BeautifulSoup((ROOT / row['file']).read_text(encoding='utf-8'), 'html.parser')

def compact(element):
    return re.sub(r'\s+', '', element.get_text()) if element else ''

def prose(text):
    pattern = '(' + '|'.join(re.escape(word) for word in PROTECTED) + ')'
    return ''.join(f'<span class="keep">{escape(piece)}</span>' if piece in PROTECTED else escape(piece) for piece in re.split(pattern, text))

def icon(name):
    return f'<svg aria-hidden="true"><use href="#icon-{name}"/></svg>'

def link(text, href, cls='text-link', arrow='↗'):
    return f'<a class="{cls}" href="{href}">{text} <span aria-hidden="true">{arrow}</span></a>'

def image(url, alt, sizes='(min-width:1000px) 45vw, calc(100vw - 40px)', cls='', eager=False):
    row = DERIVATIVES[url.replace('http://', 'https://')]
    variants = row['variants']
    initial = min(variants, key=lambda v: abs(v['width'] - 800))
    src = initial['file'].removeprefix('site/')
    srcset = ', '.join(v['file'].removeprefix('site/') + ' ' + str(v['width']) + 'w' for v in variants)
    return f'<img class="{cls}" src="{src}" srcset="{srcset}" sizes="{sizes}" width="{row["width"]}" height="{row["height"]}" alt="{escape(alt, quote=True)}" {"fetchpriority=high" if eager else "loading=lazy"} decoding="async">'

def zoom_image(url, alt, caption=None, cls='', sizes='(min-width:1000px) 28vw, 43vw'):
    row = DERIVATIVES[url.replace('http://', 'https://')]
    full = row['variants'][-1]['file'].removeprefix('site/')
    caption = caption or alt
    return f'<figure class="source-figure {cls}"><button type="button" class="photo-button" data-image="{full}" data-caption="{escape(caption, quote=True)}" aria-label="{escape(alt, quote=True)}を拡大する">{image(url, alt, sizes)}<span class="zoom-mark" aria-hidden="true">{icon("expand")}</span></button><figcaption>{prose(caption)}</figcaption></figure>'

def generated(name, alt, eager=False):
    return f'<figure class="hero-visual"><img src="assets/generated/{name}-800.webp" srcset="assets/generated/{name}-480.webp 480w, assets/generated/{name}-800.webp 800w, assets/generated/{name}-1280.webp 1280w" sizes="(min-width:1000px) 52vw, (min-width:720px) 650px, calc(100vw - 40px)" width="1536" height="1024" alt="{alt}" {"fetchpriority=high" if eager else "loading=lazy"} decoding="async"><figcaption>日々の暮らしのイメージ / AI生成イラスト</figcaption></figure>'

def section_heading(kicker, first, second='', centered=False):
    return f'<div class="section-heading {"centered" if centered else ""}"><p class="section-kicker">{kicker}</p><h2><span class="phrase">{first}</span>{f"<span class=phrase>{second}</span>" if second else ""}</h2></div>'

def page_intro(title, subtitle, label='', visual='', identifier=''):
    return f'<section class="page-intro {"with-visual" if visual else ""}" {f"id={identifier}" if identifier else ""}><div class="container"><nav class="breadcrumbs" aria-label="現在地"><a href="index.html">ホーム</a><span aria-hidden="true">/</span><span>{title}</span></nav><div class="page-intro-grid"><div><p class="section-kicker">{label or "WARAKU 福泊"}</p><h1>{prose(title)}</h1><p class="page-lead">{prose(subtitle)}</p></div>{visual}</div></div></section>'

def contact(service='WARAKU福泊'):
    return f'<section class="contact" id="contact" aria-labelledby="contact-heading"><div class="container contact-inner"><p class="section-kicker">{service}へのお問い合わせ</p><h2 id="contact-heading"><span class="phrase">まずは、お気軽に</span><span class="phrase">ご相談ください。</span></h2><div class="contact-methods"><a class="contact-phone" href="tel:0862014133">{icon("phone")}<span><span class="contact-label">お電話でのご相談・見学</span><span class="contact-number">086-201-4133</span></span></a><a class="contact-email" href="mailto:waraku@able.ocn.ne.jp">{icon("mail")}<span><span class="contact-label">メールでのお問い合わせ</span><span class="email-address">waraku@able.ocn.ne.jp</span></span><span aria-hidden="true">↗</span></a></div><p class="contact-note">メールのリンクを押すと、<span class="phrase">お使いのメールアプリが開きます。</span></p></div></section>'

def header(active):
    nav = ''.join(f'<a href="{path or "index.html"}" {"aria-current=page" if path==active else ""}>{name}</a>' for name, path in NAV)
    return f'<a class="skip-link" href="#main">本文へ移動</a><div class="preview-bar"><div class="container preview-inner"><span><span class="preview-dot" aria-hidden="true"></span>リニューアル確認用</span><a href="design.html">生成デザイン案を見る ↗</a></div></div><header class="site-header"><div class="container header-inner"><a class="brand" href="index.html" aria-label="WARAKU福泊 ホーム"><span class="brand-main"><span class="brand-letters"><span>W</span><span>A</span><span>R</span><span>A</span><span>K</span><span>U</span></span><span class="brand-place">福泊</span></span><span class="brand-sub">株式会社 和楽</span></a><nav class="primary-nav" aria-label="主なご案内"><a href="index.html#services">サービス</a><a href="index.html#facility">施設・アクセス</a><a href="#contact">ご相談・見学</a></nav><div class="header-actions"><a class="button button-solid header-call" href="tel:0862014133">{icon("phone")}電話で相談する</a><button class="menu-toggle" type="button" data-open-menu aria-haspopup="dialog" aria-controls="site-menu"><span class="menu-lines" aria-hidden="true"></span><span>メニュー</span></button></div></div><nav class="global-site-nav container" aria-label="サイトメニュー">{nav}</nav></header>'

def footer(active, original_url=None):
    nav = ''.join(f'<a href="{path or "index.html"}" {"aria-current=page" if path==active else ""}>{name}</a>' for name, path in NAV)
    original = f'<a href="{original_url}" target="_blank" rel="noopener noreferrer">元の掲載ページを見る ↗</a>' if original_url else '<a href="https://waraku-f.jp/" target="_blank" rel="noopener noreferrer">現行サイトを見る ↗</a>'
    # Symbols are taken from the previous, verified shared icon set.
    icons = (SOURCE / 'templates/icons.html').read_text()
    return f'<footer class="site-footer"><div class="container footer-grid"><div class="footer-brand"><a href="index.html"><span class="footer-wordmark">WARAKU 福泊</span></a><img src="assets/original/company-logo.png" width="147" height="28" alt="株式会社 和楽" loading="lazy" decoding="async"><p class="footer-address">〒703-8262<span class="address-line">岡山市中区福泊263-1</span></p></div><nav class="footer-nav" aria-label="サイトメニュー">{nav}</nav><a class="instagram-link" href="https://www.instagram.com/day_fukudomari_waraku/" target="_blank" rel="noopener noreferrer">{icon("instagram")}<span>Instagram<span class="instagram-account">@day_fukudomari_waraku</span></span><span aria-hidden="true">↗</span></a></div><div class="container footer-bottom"><p>{link("サイトマップ", "sitemap/", "footer-small-link")}　{original}</p><small>Copyright © WARAKU福泊 All Rights Reserved.</small><a href="#top" class="back-top" aria-label="ページの先頭へ">↑</a></div></footer><nav class="mobile-contact" aria-label="お問い合わせのショートカット"><a href="tel:0862014133">{icon("phone")}電話で相談</a><a href="mailto:waraku@able.ocn.ne.jp">{icon("mail")}メールで相談</a></nav><dialog id="site-menu" class="menu-dialog" aria-labelledby="menu-heading"><div class="dialog-top"><h2 id="menu-heading">メニュー</h2><button class="close-button" type="button" data-close-dialog aria-label="メニューを閉じる">×</button></div><nav class="menu-whole-site" aria-label="全ページ">{nav}</nav><a class="button button-solid menu-contact" href="tel:0862014133">{icon("phone")}086-201-4133</a></dialog><dialog id="image-dialog" class="image-dialog" aria-labelledby="image-caption"><div class="dialog-top"><p>写真・案内図</p><button class="close-button" type="button" data-close-dialog aria-label="拡大表示を閉じる">×</button></div><figure><img id="enlarged-image" alt=""><figcaption id="image-caption"></figcaption></figure></dialog>{icons}'

def write_page(path, title, main, active='', original_url=None, description='', include_contact=True):
    prefix = '../' * (len(Path(path).parts) - 1)
    service = {'dayservice/':'デイサービス福泊','cafe/':'福泊カフェ','careplan/':'ケアプラン福泊','recruit/':'求人情報'}.get(active, 'WARAKU福泊')
    html = f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow, noarchive"><meta name="theme-color" content="#fbf8f2"><meta name="description" content="{escape(description or title + "をご案内します。WARAKU福泊のサイト全体リニューアル確認用ページです。", quote=True)}"><title>{title}｜WARAKU福泊 リニューアル案</title><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="preload" href="assets/fonts/noto-sans-jp.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="assets/fonts/fonts.css"><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="sitewide.css"><script src="main.js" defer></script></head><body id="top" class="page-{active.strip("/") or "home"}">{header(active)}{main}{contact(service) if include_contact else ""}{footer(active, original_url)}</body></html>'
    soup = BeautifulSoup(html, 'html.parser')
    for element in soup.find_all(True):
        for attribute in ['href', 'src', 'data-image']:
            value = element.get(attribute)
            if value and not value.startswith(('#', 'http:', 'https:', 'tel:', 'mailto:', 'data:')):
                element[attribute] = prefix + value
        if element.get('srcset'):
            element['srcset'] = ', '.join(prefix + part.strip() for part in element['srcset'].split(','))
    target = SITE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    rendered = re.sub(r'<meta content="([^"]*)" name="description"\s*/>', r'<meta name="description" content="\1"/>', str(soup))
    target.write_text(rendered + '\n')
    BUILT.append({'file': str(target.relative_to(ROOT)), 'title': title, 'type': 'article' if original_url and re.search(r'/(?:blog/)?\d+$', original_url) else 'page', 'original_url': original_url})

def source_figure(name, alt, cls=''):
    return zoom_image(ORIGIN + 'common/img/' + name, alt, cls=cls)

def home():
    intro = compact(source().select_one('#section01 p'))
    services = [('dayservice/', 'デイサービス福泊', '日帰りの生活支援・機能訓練', 'dayservice/img_day.png'), ('cafe/', '福泊カフェ', '認知症対応型デイサービス', 'cafe/img_cafe.png'), ('careplan/', 'ケアプラン福泊', '介護のご相談・ケアプランのご提案', None)]
    cards = ''
    for number, (href, title, text, photo) in enumerate(services, 1):
        visual = image(ORIGIN+'common/img/'+photo, '現行サイトに掲載された'+title+'の画像', '(min-width:1200px) 350px, (min-width:720px) 27vw, 120px') if photo else '<img src="assets/generated/consultation-480.webp" width="1536" height="1024" alt="相談のイメージ・AI生成イラスト" loading="lazy" decoding="async">'
        cards += f'<a class="service-card" href="{href}"><div class="service-card-visual">{visual}</div><p class="service-card-label">{number:02} / {"AI生成イラスト" if not photo else "現行サイト掲載画像"}</p><h3>{title}</h3><p>{text}</p><span class="service-card-more">詳しく見る <span aria-hidden="true">↗</span></span></a>'
    reha_names = [('reha01','回想法'), ('reha02','ドッグセラピー'), ('reha03','音楽セラピー'), ('reha04','生活リハビリ'), ('reha06','機能訓練'), ('reha05','学習療法')]
    reha_links = ''.join(f'<a href="rehabilitation/#{id}"><span class="small-index">{i:02}</span>{title}<span aria-hidden="true">↗</span></a>' for i,(id,title) in enumerate(reha_names,1))
    features = ['昼食は新鮮な食材をご利用者様と一緒にお料理。', '日常生活の助けとなるリハビリ各種を実施。', '少人数定員制で手厚い対応。', '近隣の環境を生かしたレクリエーション。', 'ドッグセラピーやアロマテラピー等を採用し、ストレスケアや身体機能回復に。']
    return '<main id="main">' + f'<section class="hero home-hero"><div class="container hero-grid"><div class="hero-copy"><p class="eyebrow"><span class="tiny-leaf" aria-hidden="true"></span>岡山市中区のデイサービス</p><p class="hero-service">WARAKU 福泊</p><h1><span class="phrase">“おかえりなさい”が</span><span class="phrase">似合う場所。</span></h1><p class="hero-description">住み慣れた地域で、我が家のように。ご利用者様とご家族に寄り添うサービスをお届けします。</p><div class="hero-actions">{link("サービスを見る", "#services", "button button-solid", "↓")}{link("ご相談・見学", "#contact")}</div></div>{generated("home-daily", "日々の暮らしを表す、会話と折り紙のイメージイラスト",True)}</div><nav class="container section-nav" aria-label="トップページのご案内"><a href="#services"><span class="nav-number">01</span>サービス<span class="nav-arrow">↓</span></a><a href="#facility"><span class="nav-number">02</span>施設・アクセス<span class="nav-arrow">↓</span></a><a href="#journal"><span class="nav-number">03</span>福泊の日々<span class="nav-arrow">↓</span></a></nav></section>' + f'<section id="services" class="section-space white-section"><div class="container">{section_heading("サービスのご案内", "その方らしい毎日を、", "支える。",True)}<div class="service-card-grid">{cards}</div></div></section>' + f'<section class="section-space"><div class="container home-intro-grid"><div>{section_heading("私たちの想い", "我が家で過ごすような、", "心地よさを。")}<p class="body-copy">{prose(intro)}</p></div><div>{source_figure("img_section01.png", "現行サイト掲載の施設内写真", "intro-facility-photo")}</div></div></section>' + f'<section class="section-space white-section"><div class="container two-column-editorial"><div>{section_heading("デイサービス福泊・福泊カフェの特長", "暮らしの中に、", "楽しみを。")}<ul class="check-list">{"".join("<li>"+prose(item)+"</li>" for item in features)}</ul></div><div>{section_heading("充実のリハビリ", "無理なく、楽しく。")}<div class="rehab-link-grid">{reha_links}</div>{link("リハビリの内容を見る", "rehabilitation/")}</div></div></section>' + f'<section class="section-space" id="facility"><div class="container">{section_heading("施設・アクセス", "いつもの地域で、", "これからも。")}<div class="facility-summary"><div><p class="body-copy">小規模・ワンフロアのメリットを活かし、施設の隅々にまでスタッフの目と声が行き渡ります。</p><div class="floor-gallery">{source_figure("map.png", "現行サイト掲載のフロア案内図")}{source_figure("map_list.png", "現行サイト掲載の施設写真と各部屋のご案内")}</div></div><div class="facility-address"><h3>WARAKU 福泊</h3><p>〒703-8262<span class="address-line">岡山市中区福泊263-1</span></p><p><span class="keep">TEL.086-201-4133</span><span class="address-line">FAX.086-201-4132</span></p>{link("会社概要・アクセス", "company/", "button button-outline")}</div></div></div></section>' + f'<section class="section-space white-section" id="journal"><div class="container"><div class="section-title-row">{section_heading("スタッフブログ", "福泊の日々")}{link("ブログ一覧を見る", "blog/")}</div><div class="journal-teasers">{"".join(blog_card(post) for post in POSTS[:3])}</div></div></section>' + f'<section class="recruit-band"><div class="container"><div><p class="section-kicker">求人情報</p><h2><span class="phrase">笑顔がつながる職場で、</span><span class="phrase">一緒に働きませんか。</span></h2></div>{link("求人情報を見る", "recruit/", "button button-outline")}</div></section></main>'

def service_page(slug):
    is_cafe = slug == 'cafe'
    name = '福泊カフェ' if is_cafe else 'デイサービス福泊'
    soup = source(slug)
    region = soup.select_one('#cafe' if is_cafe else '#dayService')
    description = compact(region.select_one('.wrapper > p'))
    recommendations = [compact(li) for li in region.select('.wrapper > ul > li')]
    flow_copy = compact(region.select_one('#flowDay p'))
    photo = 'cafe/img_cafe.png' if is_cafe else 'dayservice/img_day.png'
    visual = f'<figure class="page-hero-photo">{image(ORIGIN+"common/img/"+photo,"現行サイト掲載の"+name+"の画像",eager=True)}<figcaption>現行サイト掲載画像</figcaption></figure>'
    timeline = [
        ('8:30','お迎え','ご自宅までお迎えに伺います。車椅子の方でも安心してご利用いただけます。'),
        ('9:00','朝のごあいさつ・水分補給・バイタルチェック','1日の予定や、その他お知らせ。'),
        ('9:00〜11:45','入浴・リハビリ体操・目の体操・レクリエーション',''),
        ('11:45','口腔体操','お食事前にお口の体操をおこないます。'),
        ('12:00','昼食','栄養バランスのとれた美味しい食事をご用意しています。また、趣向をこらしたイベント食で皆さんに楽しんでいただいています。'),
        ('13:00','団らん・リラックスタイム','昭和歌謡の映像や懐かしい映画を流し、ゆったりとお過ごしいただきます。' if is_cafe else '電気を少し暗くして、心地良い音楽を聴いていただきながら、ゆったりとお過ごしいただきます。'),
        ('13:30','リハビリ体操・イベント等' if is_cafe else 'リハビリ体操・レクリエーション','集団リハビリでは音楽に合わせて行う体操やゲームなどを行います。個別リハビリではリハビリマシーンや作業療法士が制作した個別メニューを、スタッフと共に行います。' if is_cafe else '生活リハビリ・個別リハビリでは、生活に密着したリハビリを行います。'),
        ('15:00','脳トレ','' if is_cafe else '個別脳トレでは、クイズや問題集を中心としたトレーニングを行います。'),
        ('16:00','お帰りの準備・ご自宅に向け出発',''),
    ]
    # All times and activities were visually checked against each service's original schedule image.
    flow_name = 'cafe/flow.jpg' if is_cafe else 'dayservice/img_flow.jpg'
    flow = '<ol class="daily-timeline">'+''.join(f'<li><time>{time}</time><div><h3>{prose(heading)}</h3>{"<p>"+prose(text)+"</p>" if text else ""}</div></li>' for time,heading,text in timeline)+'</ol>'+f'<details class="original-flow"><summary>現行サイトの案内画像を見る</summary><div class="flow-document">{source_figure(flow_name, name+"の1日の流れ（現行サイト掲載）")}</div></details>'
    return '<main id="main">' + page_intro(name,description,'認知症対応型デイサービス' if is_cafe else '日帰りの生活支援・機能訓練',visual) + f'<section class="section-space white-section"><div class="container service-detail-grid"><div>{section_heading("こんなご家族におすすめです" if is_cafe else "こんな方におすすめです", "日々の暮らしを、", "もっと心地よく。")}<ul class="check-list">{"".join("<li>"+prose(item)+"</li>" for item in recommendations)}</ul></div><aside class="transport-note"><p class="section-kicker">送迎サービス</p><h2>送迎サービスが<span class="phrase">あります。</span></h2><p>送迎サービスエリア</p><strong>岡山市中区・東区</strong>{link("ご相談・お問い合わせ", "#contact")}</aside></div></section>' + f'<section class="section-space"><div class="container">{section_heading("1日の流れ", "ご自分のペースで、", "お過ごしください。")}<p class="flow-description">{prose(flow_copy)}</p>{flow}</div></section><section class="section-space white-section"><div class="container related-service">{section_heading("リハビリテーション", "無理なく、楽しく。")}<p class="body-copy">ご利用者様が無理なく楽しく実践できる、様々なリハビリテーションを取り入れています。</p>{link("充実のリハビリを見る", "rehabilitation/", "button button-outline")}</div></section></main>'

def rehabilitation():
    soup = source('rehabilitation')
    region = soup.select_one('#rehabili')
    items = []
    for block in region.select('dl[id]'):
        number = int(block['id'].replace('reha',''))
        title = block.select_one('dt img')['alt']
        paragraphs = [re.sub(r'\s+', '', text) for text in re.split(r'<br\s*/?>\s*<br\s*/?>', str(block.dd))]
        text = compact(block.dd)
        items.append((block['id'], number, title, text))
    links = ''.join(f'<a href="#{id}"><span>{i:02}</span>{title}<span aria-hidden="true">↓</span></a>' for i,(id,n,title,text) in enumerate(items,1))
    body = '<main id="main">' + page_intro('充実のリハビリ',compact(region.strong),'無理なく、楽しく。') + f'<div class="container rehabilitation-index">{links}</div><div class="rehabilitation-list">'
    for index,(id,n,title,text) in enumerate(items,1):
        photo = source_figure(f'reha/bg_reha{n:02}.jpg', title+'の現行サイト掲載画像', f'rehab-photo rehab-photo-{n}')
        body += f'<section class="rehabilitation-item" id="{id}"><div class="container rehab-detail-grid"><div><p class="section-kicker">REHABILITATION / {index:02}</p><h2>{title}</h2><p class="body-copy">{prose(text)}</p></div>{photo}</div></section>'
    return body + '</div></main>'

def company():
    rows = source('company').select('#company table tr')
    table = ''
    for row in rows:
        key = compact(row.th)
        cell = BeautifulSoup(str(row.td),'html.parser')
        for a in cell.select('a'):
            if 'Googlemap' in a.get_text(): a.decompose()
        value = compact(cell)
        if key=='称号':key='会社名'
        table += f'<div><dt>{key}</dt><dd>{prose(value)}</dd></div>'
    return '<main id="main">' + page_intro('会社概要','住み慣れた地域で暮らしたいと望まれる皆様のために。株式会社和楽をご紹介します。','株式会社 和楽') + f'<section class="section-space white-section"><div class="container company-grid"><div><h2 class="company-title">株式会社 和楽</h2><dl class="company-table">{table}</dl></div><aside>{source_figure("img_section01.png","現行サイト掲載の施設内写真")}{source_figure("company/map.png","現行サイト掲載のアクセス案内図")}<a class="button button-outline google-map-link" href="https://www.google.com/maps/search/?api=1&amp;query=%E5%B2%A1%E5%B1%B1%E5%B8%82%E4%B8%AD%E5%8C%BA%E7%A6%8F%E6%B3%8A263-1" target="_blank" rel="noopener noreferrer">{icon("pin")}Googleマップで見る ↗</a></aside></div></section></main>'

def recruit():
    salaries = [('無資格者','198,800円〜'),('介護福祉士','223,800円〜'),('看護師','239,400円〜'),('主任・ケアマネジャー','250,000円〜')]
    visual = f'<figure class="page-hero-photo">{image(ORIGIN+"common/img/dayservice/img_day.png", "現行サイトの求人案内にも使用されている画像", eager=True)}<figcaption>現行サイト掲載画像</figcaption></figure>'
    return '<main id="main">'+page_intro('求人情報','笑顔がつながる職場で、ぜひ一緒に働きましょう！まずはお気軽にお問い合わせください。','STAFF RECRUIT',visual)+f'<section class="section-space white-section"><div class="container recruit-grid"><div>{section_heading("一緒に働きたい方へ", "笑顔がつながる、", "福泊の仕事。")}<p class="body-copy">介護系のお仕事を始めてみませんか？アットホームで働きやすい職場です。待遇面も頑張りにより評価してもらえます。評価制度も明確で、安心の環境です。</p><ul class="check-list"><li>子育て支援を推進しています。子供の急病の際は即時帰宅可能。</li><li>お休みがとりやすい環境です。</li></ul></div><div><h2 class="salary-heading">現行サイト掲載の給与</h2><dl class="salary-table">{"".join(f"<div><dt>{role}</dt><dd><span class=keep>{salary}</span></dd></div>" for role,salary in salaries)}</dl><p class="source-caption">現行サイト掲載の金額です。募集状況・条件の詳細は直接お問い合わせください。</p></div></div></section><section class="section-space"><div class="container recruit-contact"><h2>直接、お問い合わせください。</h2><p>紹介会社や紹介型掲示板を通じた応募ではなく、直接お問い合わせください。</p><div class="recruit-details"><p>〒703-8262 岡山市中区福泊263-1</p><p>求人案内の営業日：月曜日〜土曜日<span class="holiday-note">年末年始12月30日〜1月3日を除く</span></p><p>営業時間：8:30〜17:30</p></div>{link("電話で問い合わせる", "tel:0862014133", "button button-solid")}</div></section></main>'

def selected_photo(img, origin):
    thumb = urljoin(origin,img['src']).replace('http://','https://')
    a = img.find_parent('a')
    full = urljoin(origin,a['href']).replace('http://','https://') if a and a.get('href') else thumb
    return full if full in DERIVATIVES else thumb

def read_posts():
    posts = []
    for row in PAGE_ROWS:
        if not re.search(r'/(?:blog/)?\d+$',row['url']):continue
        soup = BeautifulSoup((ROOT/row['file']).read_text(encoding='utf-8'),'html.parser')
        section = soup.select_one('#blogLeft section')
        if not section:continue
        wp = section.select_one('.wp-post')
        title = section.h1.get_text(strip=True)
        date = section.select_one('.date').get_text(strip=True)
        numbers = re.findall(r'\d+',date)
        iso = '-'.join([numbers[0],numbers[1].zfill(2),numbers[2].zfill(2)])
        identifier = row['url'].rsplit('/',1)[-1]
        path = ('blog/' if '/blog/' in row['url'] else 'news/')+identifier+'/index.html'
        photos = [selected_photo(img,row['url']) for img in wp.select('img')]
        posts.append({'title':title,'date':date,'iso':iso,'month':iso[:7],'id':identifier,'path':path,'url':row['url'],'body':wp,'photos':photos,'source_text':' '.join(wp.stripped_strings)})
    return sorted(posts,key=lambda p:(p['iso'],int(p['id'])),reverse=True)

def blog_card(post, hidden=False):
    href = post['path'].removesuffix('index.html')
    visual = image(post['photos'][0], '「'+post['title']+'」の記事に掲載された写真', '(min-width:1000px) 27vw, (min-width:720px) 30vw, 43vw') if post['photos'] else '<span class="text-only-post"><span>WARAKU</span><span>福泊の日々</span></span>'
    title = escape(post['title'])
    search = escape(post['title']+' '+post['source_text'],quote=True)
    return f'<article class="journal-card" data-blog-card data-month="{post["month"]}" data-search="{search}" {"hidden" if hidden else ""}><a href="{href}"><div class="journal-photo">{visual}</div><div class="journal-info"><time datetime="{post["iso"]}">{post["iso"].replace("-",".")}</time><h2>{prose(post["title"])}</h2><span class="journal-read">記事を読む <span aria-hidden="true">↗</span></span></div></a></article>'

def article_body(post):
    blocks=[]
    gallery=[]
    def flush():
        if gallery:
            blocks.append('<div class="post-photo-grid">'+''.join(gallery)+'</div>')
            gallery.clear()
    paragraphs=[node for node in post['body'].children if getattr(node,'name',None)]
    if not paragraphs:paragraphs=[post['body']]
    photo_index=0
    for paragraph in paragraphs:
        text=' '.join(paragraph.stripped_strings)
        if text:
            flush()
            blocks.append('<p class="original-text">'+prose(text)+'</p>')
        for img in ([paragraph] if paragraph.name=='img' else paragraph.select('img')):
            photo_index+=1
            url=selected_photo(img,post['url'])
            gallery.append(zoom_image(url, f'「{post["title"]}」の記事に掲載された写真{photo_index}', f'掲載写真 {photo_index}', sizes='(min-width:1000px) 25vw, 43vw'))
    flush()
    return ''.join(blocks)

def article(post,index):
    date=post['iso'].replace('-','.')
    previous=POSTS[index-1] if index>0 else None
    following=POSTS[index+1] if index<len(POSTS)-1 else None
    navigation=''
    for label,p in [('新しい記事',previous),('前の記事',following)]:
        if p:navigation+=f'<a href="{p["path"].removesuffix("index.html")}"><span>{label}</span>{prose(p["title"])}</a>'
    return f'<main id="main"><div class="container article-shell"><nav class="breadcrumbs" aria-label="現在地"><a href="index.html">ホーム</a><span>/</span><a href="blog/">スタッフブログ</a><span>/</span><span>記事</span></nav><article class="blog-article"><header class="article-header"><p class="section-kicker">福泊の日々</p><time datetime="{post["iso"]}">{date}</time><h1>{prose(post["title"])}</h1></header><div class="post-body">{article_body(post)}</div><footer class="article-footer">{link("ブログ一覧へ", "blog/")}{link("この月の記事を見る", "blog/date/"+post["month"].replace("-","/")+"/")}</footer></article><nav class="article-neighbors" aria-label="前後の記事">{navigation}</nav></div></main>'

def archive_links():
    return '<details class="archives"><summary>月別アーカイブ</summary><div class="archive-links">'+''.join(f'<a href="blog/date/{month.replace("-","/")}/">{month[:4]}年{int(month[5:])}月<span>{len(posts)}件</span></a>' for month,posts in MONTHS.items())+'</div></details>'

def blog_index(posts, heading='スタッフブログ', page_number=1, month=None, searchable=False):
    options=''.join(f'<option value="{key}">{key[:4]}年{int(key[5:])}月</option>' for key in MONTHS)
    toolbar=f'<div class="blog-filter"><label>キーワードで探す<input id="blog-search" type="search" placeholder="記事のタイトル・本文" autocomplete="off"></label><label>月で絞り込む<select id="blog-month"><option value="">すべての月</option>{options}</select></label></div><div class="blog-status"><p id="blog-result-count" role="status" aria-live="polite">{len(POSTS)}件の記事</p><button type="button" id="blog-reset">絞り込みを解除</button></div>' if searchable else ''
    if searchable:
        cards=''.join(blog_card(p,i>=12) for i,p in enumerate(posts))
        pagination='<div class="blog-pagination"><button id="blog-prev" type="button">前のページ</button><span id="blog-page-status">1 / '+str(math.ceil(len(posts)/12))+'</span><button id="blog-next" type="button">次のページ</button></div><noscript><p>月別アーカイブやページ番号から、過去の記事をご覧いただけます。</p></noscript>'
    else:
        cards=''.join(blog_card(p) for p in posts)
        pagination=link('すべての記事一覧へ','blog/')
    pages=''.join(f'<a href="blog/{"page/"+str(i)+"/" if i>1 else ""}">{i}</a>' for i in range(1,math.ceil(len(POSTS)/10)+1))
    return '<main id="main">'+page_intro(heading,'福泊の活動や日々のできごとを、スタッフがお届けします。','JOURNAL')+f'<section class="section-space white-section"><div class="container blog-container">{toolbar}<div class="journal-grid" id="blog-results">{cards}</div><p id="blog-empty" hidden>条件に合う記事が見つかりませんでした。</p>{pagination}<details class="blog-page-links"><summary>ページ番号から探す</summary><nav aria-label="記事一覧のページ">{pages}</nav></details>{archive_links()}</div></section></main>'

def sitemap():
    principal=''.join(f'<a href="{path or "index.html"}">{name} <span>↗</span></a>' for name,path in NAV)
    article_links=''.join(f'<li><time>{p["iso"].replace("-",".")}</time><a href="{p["path"].removesuffix("index.html")}">{prose(p["title"])}</a></li>' for p in POSTS)
    return '<main id="main">'+page_intro('サイトマップ','各サービスのご案内と、掲載記事の一覧です。')+f'<section class="section-space white-section"><div class="container"><div class="sitemap-primary">{principal}</div>{archive_links()}<h2 class="sitemap-title">掲載記事一覧</h2><ul class="sitemap-articles">{article_links}</ul></div></section></main>'

POSTS=read_posts()
MONTHS=defaultdict(list)
for post in POSTS:MONTHS[post['month']].append(post)

write_page('index.html','岡山市中区のデイサービス・介護相談',home(),'',ORIGIN)
write_page('rehabilitation/index.html','充実のリハビリ',rehabilitation(),'rehabilitation/',ORIGIN+'rehabilitation')
for slug,name in [('dayservice','デイサービス福泊'),('cafe','福泊カフェ')]:
    write_page(slug+'/index.html',name,service_page(slug),slug+'/',ORIGIN+slug)
write_page('careplan/index.html','ケアプラン福泊',(SOURCE/'templates/careplan-main.html').read_text(),'careplan/',ORIGIN+'careplan')
write_page('company/index.html','会社概要',company(),'company/',ORIGIN+'company')
write_page('recruit/index.html','求人情報',recruit(),'recruit/',ORIGIN+'#section04')
write_page('blog/index.html','スタッフブログ',blog_index(POSTS,searchable=True),'blog/',ORIGIN+'blog')
for index,post in enumerate(POSTS):
    write_page(post['path'],post['title'],article(post,index),'blog/',post['url'])
for month,posts in MONTHS.items():
    write_page('blog/date/'+month.replace('-','/')+'/index.html',f'{month[:4]}年{int(month[5:])}月の記事',blog_index(posts,f'{month[:4]}年{int(month[5:])}月の記事',month=month),'blog/',ORIGIN+'blog/date/'+month.replace('-','/'))
for number in range(2,math.ceil(len(POSTS)/10)+1):
    write_page(f'blog/page/{number}/index.html',f'スタッフブログ {number}ページ',blog_index(POSTS[(number-1)*10:number*10],f'スタッフブログ {number}ページ',page_number=number),'blog/',ORIGIN+'blog')
write_page('sitemap/index.html','サイトマップ',sitemap(),original_url=ORIGIN+'sitemap.html')

original_to_new={}
for row in BUILT:
    if row['original_url']:
        original_to_new.setdefault(row['original_url'],row['file'].removeprefix('site/'))
post_integrity=[]
for post in POSTS:
    rendered=BeautifulSoup((SITE/post['path']).read_text(),'html.parser')
    text=' '.join(element.get_text() for element in rendered.select('.original-text'))
    normalize=lambda value:re.sub(r'\s+','',value).replace('\xa0','')
    post_integrity.append({'original_url':post['url'],'file':post['path'],'title':post['title'],'date':post['iso'],'photos':len(post['photos']),'source_text_sha256':hashlib.sha256(normalize(post['source_text']).encode()).hexdigest(),'rendered_text_sha256':hashlib.sha256(normalize(text).encode()).hexdigest(),'matches':normalize(post['source_text'])==normalize(text)})
(SOURCE/'renewal-pages.json').write_text(json.dumps(BUILT,ensure_ascii=False,indent=2)+'\n')
(SOURCE/'url-mapping.json').write_text(json.dumps(original_to_new,ensure_ascii=False,indent=2)+'\n')
(ROOT/'qa/content-migration.json').write_text(json.dumps({'posts':len(POSTS),'monthly_archives':len(MONTHS),'pages':len(BUILT),'all_post_text_matches':all(r['matches'] for r in post_integrity),'articles':post_integrity,'empty_source_pages':[r['url'] for r in PAGE_ROWS if r.get('file') and (ROOT/r['file']).stat().st_size==0]},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pages':len(BUILT),'articles':len(POSTS),'monthly_archives':len(MONTHS),'post_text_matches':all(r['matches'] for r in post_integrity)},ensure_ascii=False))
