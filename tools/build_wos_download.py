#!/usr/bin/env python3
"""Сборка страницы скачивания WakeOnStop для vegavit.eu — 22 языка.

Образец — tools/build_download.py (lambit2FA); оформление то же, CSS берётся
оттуда. Источник — папка docs/сайт/ репозитория idimalab25/lambitTrainExit:
  site_strings.json   надписи плашки и страницы, 22 языка
  qr/*.svg            QR-коды (ссылки в магазины уже внутри)
  shots/<язык>/*.jpg  три картинки на языке страницы
  icon/*.png          иконка приложения

Выход:
  wakeonstop/download/index.html        английский
  wakeonstop/download/<код>/index.html  остальные 21
  wakeonstop/download/qr/, shots/, ../icon/ — копии

Файлов для скачивания с сайта у WakeOnStop нет: только App Store и Google
Play (ТЗ_сайт_WakeOnStop.md, 26.10.2026).

Запуск:  python3 tools/build_wos_download.py --src ~/lambitTrainExit/docs/сайт
"""
import argparse
import html
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_download import CSS, NAMES, TAG, RTL, DEFAULT_LANG

STORE_IPHONE = 'https://apps.apple.com/app/id6826948667'
STORE_PLAY = 'https://play.google.com/store/apps/details?id=com.lambit.trainexit'
BASE = '/wakeonstop/download/'

EXTRA_CSS = """
.title{display:flex;align-items:center;gap:16px;margin-bottom:10px}
.title img{width:72px;height:72px;border-radius:16px;flex:0 0 auto}
.title h1{margin:0}"""


def esc(s):
    return html.escape(s, quote=False)


def url_for(code):
    return BASE if code == DEFAULT_LANG else f'{BASE}{code}/'


def privacy_for(code):
    # политика на трёх языках: русский → корень, болгарский → /bg/, остальные → английская
    return {'ru': '/wakeonstop/privacy/', 'bg': '/wakeonstop/privacy/bg/'}.get(code, '/wakeonstop/privacy/en/')


def qr_block(name, caption):
    return (f'<div class="qr"><img src="{BASE}qr/{name}.svg" alt="{esc(caption)}" '
            f'width="124" height="124"><span>{esc(caption)}</span></div>')


def page(code, t, shots):
    tag = TAG.get(code, code)
    dir_attr = ' dir="rtl"' if code in RTL else ''
    alts = '\n'.join(
        f'<link rel="alternate" hreflang="{TAG.get(c, c)}" href="https://vegavit.eu{url_for(c)}">'
        for c in NAMES)
    alts += f'\n<link rel="alternate" hreflang="x-default" href="https://vegavit.eu{BASE}">'
    langs = ''.join(
        f'<a href="{url_for(c)}" lang="{TAG.get(c, c)}"{" class=\"on\"" if c == code else ""}>{esc(n)}</a>'
        for c, n in NAMES.items())
    gallery = ''.join(f'<img src="{BASE}shots/{shots[0]}/{n}" alt="">' for n in shots[1])

    return f"""<!DOCTYPE html>
<html lang="{tag}"{dir_attr}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(t['download_title'])} — VEGAVIT EOOD</title>
<meta name="description" content="{esc(t['plaque_text'])}">
<link rel="canonical" href="https://vegavit.eu{url_for(code)}">
{alts}
<link rel="icon" href="/wakeonstop/icon/wakeonstop-180.png">
<link rel="apple-touch-icon" href="/wakeonstop/icon/wakeonstop-180.png">
<meta name="color-scheme" content="light dark">
<style>{CSS}{EXTRA_CSS}</style>
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
  <div class="title">
    <img src="/wakeonstop/icon/wakeonstop-180.png" srcset="/wakeonstop/icon/wakeonstop-512.png 2x" alt="WakeOnStop" width="72" height="72">
    <h1>{esc(t['download_title'])}</h1>
  </div>
  <p class="intro">{esc(t['download_intro'])}</p>
  <p class="hint">{esc(t['plaque_text'])}</p>

<section class="plat" id="shots">
  <div class="gallery">{gallery}</div>
</section>

<section class="plat" id="iphone">
  <h2>{esc(t['p_iphone'])}</h2>
  <div class="row">
    {qr_block('iphone-app-store', t['p_iphone'])}
    <div class="col">
      <a class="store" href="{STORE_IPHONE}">App Store</a>
      <p class="note">{esc(t['scan_hint'])}</p>
    </div>
  </div>
</section>

<section class="plat" id="android">
  <h2>{esc(t['p_android'])}</h2>
  <div class="row">
    {qr_block('android-google-play', t['p_android'])}
    <div class="col">
      <a class="store" href="{STORE_PLAY}">Google Play</a>
      <p class="note">{esc(t['scan_hint'])}</p>
    </div>
  </div>
</section>
</main>

<footer>
  <div class="wrap">© 2026 VEGAVIT EOOD · <a href="/">vegavit.eu</a> · <a href="{privacy_for(code)}">{esc(t['privacy'])}</a></div>
</footer>

</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='папка docs/сайт проекта WakeOnStop')
    ap.add_argument('--out', default='.', help='корень репозитория сайта')
    a = ap.parse_args()
    src, out = Path(a.src).expanduser(), Path(a.out).expanduser()

    strings = json.loads((src / 'site_strings.json').read_text(encoding='utf-8'))
    assert set(strings) == set(NAMES), 'набор языков разошёлся с site_strings.json'

    root = out / 'wakeonstop'
    (root / 'icon').mkdir(parents=True, exist_ok=True)
    for n in ('wakeonstop-180.png', 'wakeonstop-512.png'):
        shutil.copy2(src / 'icon' / n, root / 'icon' / n)
    qr_out = root / 'download' / 'qr'
    qr_out.mkdir(parents=True, exist_ok=True)
    for q in sorted((src / 'qr').glob('*.svg')):
        shutil.copy2(q, qr_out / q.name)
    shots_out = root / 'download' / 'shots'
    for d in sorted((src / 'shots').iterdir()):
        (shots_out / d.name).mkdir(parents=True, exist_ok=True)
        for f in d.glob('*.jpg'):
            shutil.copy2(f, shots_out / d.name / f.name)

    for code in NAMES:
        lang_dir = code if any((shots_out / code).glob('*.jpg')) else 'en'
        shots = (lang_dir, sorted(f.name for f in (shots_out / lang_dir).glob('*.jpg')))
        d = root / 'download' / ('' if code == DEFAULT_LANG else code)
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(page(code, strings[code], shots), encoding='utf-8')
    print(f'собрано страниц: {len(NAMES)}')


if __name__ == '__main__':
    main()
