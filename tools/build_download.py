#!/usr/bin/env python3
"""Сборка страницы скачивания lambit2FA для vegavit.eu — 22 языка.

Источник (ничего не сочиняем, всё берётся готовым):
  store/site/site_strings.json      надписи плашки и страницы, 22 языка
  store/listing-linux/<язык>.txt    текст про Linux целиком, 22 языка
  store/site/qr/*.svg               QR-коды (ссылки в магазины уже внутри)
  store/build/site/                 файлы для скачивания и .sha256

Выход:
  lambit2fa/download/index.html        английский
  lambit2fa/download/<код>/index.html  остальные 21
  lambit2fa/download/qr/*.svg          копии QR-кодов

Сами файлы программы (AppImage и прочее) в репозиторий НЕ кладутся: они
десятки мегабайт. Их место — /var/www/vegavit/lambit2fa/download/files/,
кладёт хозяин. Строка файла, подпись и QR для APK и Windows ZIP рисуются только если файл
реально есть в store/build/site — чтобы на сайте не было ни ссылок в пустоту,
ни обещаний «файл с сайта» без файла (решение хозяина 10.10.2026: пока файлов
нет, Android и Windows — только через магазины).

Запуск:  python3 tools/build_download.py --src ~/lambit2FAlinux/AEFauthentic/store
"""
import argparse
import html
import json
import re
import shutil
from pathlib import Path

DEFAULT_LANG = 'en'
STORE_IPHONE = 'https://apps.apple.com/app/id6810931003'
STORE_MAC = 'https://apps.apple.com/app/id6810931003?platform=mac'
STORE_PLAY = 'https://play.google.com/store/apps/details?id=com.lambit.keys2fa'
STORE_MS = 'https://apps.microsoft.com/detail/9PK7LTD3L3NJ'
FILES_URL = '/lambit2fa/download/files/'
PRIVACY = {'ru': '/lambit2fa/privacy/', 'bg': '/lambit2fa/privacy/bg/', 'en': '/lambit2fa/privacy/en/'}

# Самоназвания языков для переключателя.
NAMES = {
    'en': 'English', 'ru': 'Русский', 'es': 'Español', 'ar': 'العربية',
    'de': 'Deutsch', 'pt': 'Português', 'zh': '简体中文', 'fi': 'Suomi',
    'fr': 'Français', 'nl': 'Nederlands', 'id': 'Bahasa Indonesia', 'hi': 'हिन्दी',
    'ja': '日本語', 'ko': '한국어', 'tr': 'Türkçe', 'vi': 'Tiếng Việt',
    'it': 'Italiano', 'pl': 'Polski', 'ro': 'Română', 'el': 'Ελληνικά',
    'hu': 'Magyar', 'bg': 'Български',
}
TAG = {'zh': 'zh-Hans'}          # для lang/hreflang
RTL = {'ar'}


CSS = """*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#f4f6f9;--surface:#fff;--text:#14181f;--text-soft:#5b6472;--line:#e3e7ee;--accent:#1a5fd0;--accent-soft:#e8f0fe;--shadow:0 1px 2px rgba(15,23,42,.06),0 8px 24px rgba(15,23,42,.07)}
@media (prefers-color-scheme:dark){:root{--bg:#10141b;--surface:#1a2029;--text:#e8ecf2;--text-soft:#97a1af;--line:#29313d;--accent:#6ea8ff;--accent-soft:#1f2c42;--shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.35)}}
body{font-family:-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}
:lang(zh){font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif}
:lang(ja){font-family:"Hiragino Sans","Yu Gothic","Meiryo","Noto Sans CJK JP",sans-serif}
:lang(ko){font-family:"Apple SD Gothic Neo","Malgun Gothic","Noto Sans CJK KR",sans-serif}
:lang(hi){font-family:"Kohinoor Devanagari","Nirmala UI","Noto Sans Devanagari",sans-serif}
:lang(ar){font-family:"SF Arabic","Geeza Pro","Tahoma","Noto Sans Arabic",sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:900px;margin:0 auto;padding:0 20px}
.site-head{background:var(--surface);border-bottom:1px solid var(--line)}
.head-in{display:flex;align-items:center;gap:12px 16px;padding:14px 0;flex-wrap:wrap}
.logo{font-size:20px;font-weight:700;letter-spacing:.5px;color:var(--text)}
.logo span{color:var(--accent)}
.head-sp{flex:1}
.langs{display:flex;gap:4px;flex-wrap:wrap;max-width:560px}
.langs a{border:1px solid var(--line);border-radius:14px;padding:3px 9px;font-size:12px;color:var(--text-soft)}
.langs a:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.langs a.on{background:var(--accent);border-color:var(--accent);color:#fff}
main{padding:34px 0 60px}
h1{font-size:28px;line-height:1.25;margin-bottom:10px}
.intro{color:var(--text-soft);max-width:640px;margin-bottom:8px}
.hint{color:var(--text-soft);font-size:13px;margin-bottom:26px}
section.plat{background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);padding:20px 22px;margin-bottom:16px;scroll-margin-top:16px}
section.plat h2{font-size:18px;margin-bottom:12px}
.row{display:flex;gap:18px;align-items:flex-start;flex-wrap:wrap}
.qr{text-align:center;font-size:12px;color:var(--text-soft);max-width:140px}
.qr img{display:block;width:124px;height:124px;background:#fff;border:1px solid var(--line);border-radius:8px;padding:6px}
.qr span{display:block;margin-top:6px}
.col{flex:1 1 320px;min-width:260px}
.store{display:inline-block;background:var(--accent);color:#fff;border-radius:9px;padding:9px 16px;font-size:14px;margin-bottom:10px}
.store:hover{text-decoration:none;opacity:.9}
.files{list-style:none;font-size:14px}
.files li{padding:8px 0;border-top:1px solid var(--line);overflow-wrap:anywhere}
.files .sha{display:block;color:var(--text-soft);font-size:12px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.note{font-size:13px;color:var(--text-soft);margin-top:10px}
pre.plain{white-space:pre-wrap;font-family:inherit;font-size:14px;color:var(--text-soft);margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}
footer{border-top:1px solid var(--line);padding:22px 0 40px;font-size:13px;color:var(--text-soft)}
@media(max-width:560px){h1{font-size:23px}.qr img{width:104px;height:104px}}"""


def esc(s):
    return html.escape(s, quote=False)


def url_for(code):
    return '/lambit2fa/download/' if code == DEFAULT_LANG else f'/lambit2fa/download/{code}/'


def qr_block(name, caption):
    return (f'<div class="qr"><img src="/lambit2fa/download/qr/{name}.svg" alt="{esc(caption)}" '
            f'width="124" height="124"><span>{esc(caption)}</span></div>')


def files_block(files, sha_hint):
    if not files:
        return ''
    items = ''.join(
        f'<li><a href="{FILES_URL}{n}">{esc(n)}</a> <span class="sha">SHA-256: {h}</span></li>'
        for n, h in files)
    return f'<p class="note">{esc(sha_hint)}</p><ul class="files">{items}</ul>'


def page(code, t, linux_text, have, priv_label):
    tag = TAG.get(code, code)
    dir_attr = ' dir="rtl"' if code in RTL else ''
    alts = '\n'.join(
        f'<link rel="alternate" hreflang="{TAG.get(c, c)}" href="https://vegavit.eu{url_for(c)}">'
        for c in NAMES)
    alts += '\n<link rel="alternate" hreflang="x-default" href="https://vegavit.eu/lambit2fa/download/">'
    langs = ''.join(
        f'<a href="{url_for(c)}" lang="{TAG.get(c, c)}"{" class=\"on\"" if c == code else ""}>{esc(n)}</a>'
        for c, n in NAMES.items())

    blocks = []
    # iPhone, iPad, Apple Watch
    blocks.append(f"""<section class="plat" id="iphone">
  <h2>{esc(t['p_iphone'])}</h2>
  <div class="row">
    {qr_block('iphone-app-store', t['p_iphone'])}
    <div class="col">
      <a class="store" href="{STORE_IPHONE}">App Store</a>
      <p class="note">{esc(t['scan_hint'])}</p>
    </div>
  </div>
</section>""")
    # Mac
    blocks.append(f"""<section class="plat" id="mac">
  <h2>{esc(t['p_mac'])}</h2>
  <div class="row">
    {qr_block('mac-app-store', t['p_mac'])}
    <div class="col">
      <a class="store" href="{STORE_MAC}">Mac App Store</a>
      <p class="note">{esc(t['scan_hint'])}</p>
    </div>
  </div>
</section>""")
    # Android: Google Play + APK
    apk = files_block(have.get('apk', []), t['sha_hint'])
    blocks.append(f"""<section class="plat" id="android">
  <h2>{esc(t['p_android'])}</h2>
  <div class="row">
    {qr_block('android-google-play', t['p_android'])}
    {qr_block('android-apk', t['p_apk']) if have.get('apk') else ''}
    <div class="col">
      <a class="store" href="{STORE_PLAY}">Google Play</a>
      <p class="note">{esc(t['scan_hint'])}</p>
      {apk}
    </div>
  </div>
</section>""")
    # Windows: магазин + архивы
    win = files_block(have.get('win', []), t['sha_hint'])
    blocks.append(f"""<section class="plat" id="windows">
  <h2>{esc(t['p_winstore'])}</h2>
  <div class="row">
    {qr_block('windows-store', t['p_winstore'])}
    {qr_block('windows-zip', t['p_winzip']) if have.get('win') else ''}
    <div class="col">
      <a class="store" href="{STORE_MS}">Microsoft Store</a>
      {('<p class="note">' + esc(t['p_winzip']) + '</p>') if have.get('win') else ''}
      {win}
    </div>
  </div>
</section>""")
    # Linux
    lin = files_block(have.get('linux', []), t['sha_hint'])
    blocks.append(f"""<section class="plat" id="linux">
  <h2>{esc(t['p_linux'])}</h2>
  <div class="row">
    {qr_block('linux', t['p_linux'])}
    <div class="col">
      {lin}
    </div>
  </div>
  <pre class="plain">{esc(linux_text.strip())}</pre>
</section>""")

    return f"""<!DOCTYPE html>
<html lang="{tag}"{dir_attr}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(t['download_title'])} — VEGAVIT EOOD</title>
<meta name="description" content="{esc(t['plaque_text'])}">
<link rel="canonical" href="https://vegavit.eu{url_for(code)}">
{alts}
<meta name="color-scheme" content="light dark">
<style>{CSS}</style>
</head>
<body>

<header class="site-head">
  <div class="wrap head-in">
    <a class="logo" href="/" dir="ltr">VEGAVIT<span>.</span></a>
    <div class="head-sp"></div>
    <div class="langs">{langs}</div>
  </div>
</header>

<main class="wrap">
  <h1>{esc(t['download_title'])}</h1>
  <p class="intro">{esc(t['download_intro'])}</p>
  <p class="hint">{esc(t['plaque_text'])}</p>

{chr(10).join(blocks)}
</main>

<footer>
  <div class="wrap">© 2026 VEGAVIT EOOD · <a href="/">vegavit.eu</a> · <a href="{'/lambit2fa/privacy/' if code == 'ru' else '/lambit2fa/privacy/' + code + '/'}">{esc(priv_label)}</a></div>
</footer>

</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='папка store/ проекта lambit2FA')
    ap.add_argument('--out', default='.', help='корень репозитория сайта')
    a = ap.parse_args()
    src, out = Path(a.src).expanduser(), Path(a.out).expanduser()

    strings = json.loads((src / 'site' / 'site_strings.json').read_text(encoding='utf-8'))
    assert set(strings) == set(NAMES), 'набор языков разошёлся с site_strings.json'

    # Какие файлы реально собраны: ссылку рисуем только на существующий файл.
    build = src / 'build' / 'site'
    have = {'linux': [], 'apk': [], 'win': []}
    for f in sorted(build.glob('*')):
        if f.suffix == '.sha256' or not f.is_file():
            continue
        sha_file = f.with_name(f.name + '.sha256')
        if not sha_file.exists():
            print(f'  ! {f.name}: нет .sha256 — пропускаю')
            continue
        sha = re.split(r'\s+', sha_file.read_text(encoding='utf-8').strip())[0]
        key = 'linux' if f.suffix == '.AppImage' else ('apk' if f.suffix == '.apk' else 'win')
        have[key].append((f.name, sha))
    print('файлы для скачивания:', {k: [n for n, _ in v] for k, v in have.items()})

    qr_out = out / 'lambit2fa' / 'download' / 'qr'
    qr_out.mkdir(parents=True, exist_ok=True)
    for q in sorted((src / 'site' / 'qr').glob('*.svg')):
        shutil.copy2(q, qr_out / q.name)
    print('QR-кодов скопировано:', len(list(qr_out.glob('*.svg'))))

    for code in NAMES:
        linux_text = (src / 'listing-linux' / f'{code}.txt').read_text(encoding='utf-8')
        # подпись ссылки на политику — из перевода сайта, на языке страницы
        site_t = json.loads((out / 'i18n' / f'{code}.json').read_text(encoding='utf-8'))
        d = out / 'lambit2fa' / 'download' / ('' if code == DEFAULT_LANG else code)
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(page(code, strings[code], linux_text, have, site_t['privLink']), encoding='utf-8')
    print(f'собрано страниц: {len(NAMES)}')


if __name__ == '__main__':
    main()
