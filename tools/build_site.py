#!/usr/bin/env python3
"""Главная vegavit.eu на 22 языках — по образцу ai-digest-1.com.

Английский — корень сайта, остальные языки — /<код>/. У каждой страницы
свой адрес, взаимные hreflang и меню языков (глобус), как у соседа.
Язык больше не переключается скриптом: адрес и есть язык.

Тексты: i18n/<код>.json (этот репозиторий). Надписи плашки lambit2FA и
подписи QR — из store/site/site_strings.json проекта приложения.

Ссылка на политику ведёт на политику того же языка: политика есть на всех 22
(английская — та, что вписана в кабинет Apple, не трогается; остальные
собирает tools/build_privacy.py из переводов i18n/privacy/).

Запуск: python3 tools/build_site.py --src ~/lambit2FAlinux/AEFauthentic/store
"""
import argparse
import html
import json
from pathlib import Path

DEFAULT_LANG = 'en'
NAMES = {
    'en': 'English', 'ru': 'Русский', 'es': 'Español', 'ar': 'العربية',
    'de': 'Deutsch', 'pt': 'Português', 'zh': '简体中文', 'fi': 'Suomi',
    'fr': 'Français', 'nl': 'Nederlands', 'id': 'Bahasa Indonesia', 'hi': 'हिन्दी',
    'ja': '日本語', 'ko': '한국어', 'tr': 'Türkçe', 'vi': 'Tiếng Việt',
    'it': 'Italiano', 'pl': 'Polski', 'ro': 'Română', 'el': 'Ελληνικά',
    'hu': 'Magyar', 'bg': 'Български',
}
TAG = {'zh': 'zh-Hans'}
RTL = {'ar'}
PRIVACY = {'ru': '/lambit2fa/privacy/', 'bg': '/lambit2fa/privacy/bg/',
           'en': '/lambit2fa/privacy/en/'}
QRS = [('iphone-app-store', 'p_iphone'), ('mac-app-store', 'p_mac'),
       ('android-google-play', 'p_android')]
# QR на APK показывается только когда сам файл APK лежит в store/build/site:
# пока его нет, Android — только через Google Play (хозяин, 10.10.2026).
QR_APK = ('android-apk', 'p_apk')
# Проекты: адреса не переводятся, тексты — ключами из i18n.
# Ключи, которые обязан дать перевод сайта. Надписи плашки и подписи QR
# сюда не входят: они приходят из site_strings.json проекта приложения.
SITE_KEYS = ('heroTitle', 'heroText', 'projTitle', 'p1', 'p2', 'p3', 'p4', 'p5', 'plat',
             'mfgTitle', 'mfgName', 'mfgText', 'aboutTitle', 'foot', 'privLink',
             'fName', 'fReg', 'fVat', 'fAddr', 'fDir', 'fMail', 'fPhone')

PROJECTS = [
    ('AI World Digest', 'https://ai-digest-1.com', 'ai-digest-1.com', 'p1', None),
    ('TokenDryer', 'https://tokendryer.com', 'tokendryer.com', 'p2', 'plat'),
    ('FMCheck', 'https://fmcheck.online', 'fmcheck.online', 'p3', 'plat'),
    ('MoreMoreIdea', None, '—', 'p4', 'plat'),
    ('Fish &amp; Mushrooms', None, None, 'p5', 'plat'),
]


def esc(s):
    return html.escape(s, quote=False)


def url_for(code):
    return '/' if code == DEFAULT_LANG else f'/{code}/'


def privacy_for(code):
    # у каждого языка своя страница политики; русская — корень /lambit2fa/privacy/
    return '/lambit2fa/privacy/' if code == 'ru' else f'/lambit2fa/privacy/{code}/'


def page(code, t, s, css):
    tag = TAG.get(code, code)
    dir_attr = ' dir="rtl"' if code in RTL else ''
    alts = '\n'.join(f'<link rel="alternate" hreflang="{TAG.get(c, c)}" href="https://vegavit.eu{url_for(c)}">'
                     for c in NAMES)
    alts += '\n<link rel="alternate" hreflang="x-default" href="https://vegavit.eu/">'
    menu = ''.join(
        f'<a href="{url_for(c)}" lang="{TAG.get(c, c)}" hreflang="{TAG.get(c, c)}"'
        f'{" class=\"cur\"" if c == code else ""}>'
        f'<span class="langcode" dir="ltr">{c.upper()}</span> {esc(n)}</a>'
        for c, n in NAMES.items())

    qrs = ''.join(
        f'<div class="qr"><img src="/lambit2fa/download/qr/{name}.svg" alt="{esc(s[key])}" '
        f'width="104" height="104"><span>{esc(s[key])}</span></div>'
        for name, key in QRS)

    cards = []
    for title, href, dom, textkey, platkey in PROJECTS:
        dom_html = (f'<a class="dom" href="{href}" target="_blank" rel="noopener">{dom}</a>'
                    if href else (f'<span class="dom">{dom}</span>' if dom else ''))
        plat = f'<p class="plat">{esc(t[platkey])}</p>' if platkey else ''
        cards.append(f"""      <div class="card">
        <h3>{title}</h3>
        {dom_html}
        <p>{esc(t[textkey])}</p>
        {plat}
      </div>""")

    return f"""<!DOCTYPE html>
<html lang="{tag}"{dir_attr} data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VEGAVIT EOOD — {esc(t['heroTitle'])}</title>
<meta name="description" content="{esc(t['heroText'][:180])}">
<link rel="canonical" href="https://vegavit.eu{url_for(code)}">
{alts}
<meta name="color-scheme" content="light dark">
<style>{css}</style>
</head>
<body data-theme="light">

<header class="site-head">
  <div class="wrap head-in">
    <a class="logo" href="{url_for(code)}" dir="ltr">VEGAVIT<span>.</span></a>
    <div class="head-sp"></div>
    <div class="ctrl">
      <div class="langsw">
        <button type="button" class="langbtn" aria-haspopup="true">🌐 <span dir="ltr">{code.upper()}</span> ▾</button>
        <div class="langmenu">{menu}</div>
      </div>
      <button id="themeBtn" title="day / night">☾</button>
    </div>
  </div>
</header>

<main class="wrap">

  <div class="hero">
    <h1>{esc(t['heroTitle'])}</h1>
    <p>{esc(t['heroText'])}</p>
  </div>

  <section>
    <h2>{esc(t['projTitle'])}</h2>
    <div class="cards">

      <!-- lambit2FA: плашка со скачиванием, собирает tools/build_site.py -->
      <div class="card" id="lambit2fa">
        <a class="plaque-main" href="/lambit2fa/download/{'' if code == DEFAULT_LANG else code + '/'}">
          <h3>{esc(s['plaque_title'])}</h3>
          <p>{esc(s['plaque_text'])}</p>
          <span class="dl-btn">{esc(s['plaque_button'])}</span>
        </a>
        <div class="qrs">{qrs}</div>
        <div class="scan-hint">{esc(s['scan_hint'])}</div>
        <a class="priv" href="{privacy_for(code)}">{esc(t['privLink'])}</a>
      </div>

{chr(10).join(cards)}

    </div>
  </section>

  <section>
    <h2>{esc(t['mfgTitle'])}</h2>
    <div class="cards">
      <div class="card">
        <h3>{esc(t['mfgName'])}</h3>
        <a class="dom" href="https://www.aeftrade.eu" target="_blank" rel="noopener">www.aeftrade.eu</a>
        <p>{esc(t['mfgText'])}</p>
      </div>
    </div>
  </section>

  <section>
    <h2>{esc(t['aboutTitle'])}</h2>
    <dl class="facts">
      <dt>{esc(t['fName'])}</dt><dd>VEGAVIT EOOD</dd>
      <dt>{esc(t['fReg'])}</dt><dd>207380781</dd>
      <dt>{esc(t['fVat'])}</dt><dd>BG207380781</dd>
      <dt>{esc(t['fAddr'])}</dt><dd><bdi>ul. Pleven 6, Plovdiv 4000, Bulgaria</bdi></dd>
      <dt>{esc(t['fDir'])}</dt><dd><bdi>Dmitry Balabolin</bdi></dd>
      <dt>{esc(t['fMail'])}</dt><dd><bdi><a href="mailto:dbalabolin@vegavit.eu">dbalabolin@vegavit.eu</a></bdi></dd>
      <dt>{esc(t['fPhone'])}</dt><dd><bdi>+359 88 483 6662</bdi></dd>
    </dl>
  </section>

</main>

<footer class="wrap">
  <span>{esc(t['foot'])}</span>
</footer>

<script>
// Язык задаётся адресом страницы — скрипт его не трогает.
const m = document.querySelector('.langmenu');
document.querySelector('.langbtn').onclick = e => {{ e.stopPropagation(); m.classList.toggle('open'); }};
document.addEventListener('click', e => {{ if (!m.contains(e.target)) m.classList.remove('open'); }});
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') m.classList.remove('open'); }});

const themeBtn = document.getElementById('themeBtn');
try {{ if (localStorage.getItem('theme') === 'dark') {{
  document.body.dataset.theme = 'dark'; document.documentElement.dataset.theme = 'dark'; themeBtn.textContent = '☀';
}} }} catch (e) {{}}
themeBtn.addEventListener('click', () => {{
  const next = document.body.dataset.theme === 'light' ? 'dark' : 'light';
  document.body.dataset.theme = next;
  document.documentElement.dataset.theme = next;
  themeBtn.textContent = next === 'light' ? '☾' : '☀';
  try {{ localStorage.setItem('theme', next); }} catch (e) {{}}
}});
</script>

</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', default='.')
    a = ap.parse_args()
    src, out = Path(a.src).expanduser(), Path(a.out).expanduser()
    strings = json.loads((src / 'site' / 'site_strings.json').read_text(encoding='utf-8'))
    if list((src / 'build' / 'site').glob('*.apk')):
        QRS.append(QR_APK)
    css = (out / 'tools' / 'site.css').read_text(encoding='utf-8')
    base = json.loads((out / 'i18n' / 'en.json').read_text(encoding='utf-8'))

    done, missing = [], []
    for code in NAMES:
        f = out / 'i18n' / f'{code}.json'
        if not f.exists():
            missing.append(code)
            continue
        t = json.loads(f.read_text(encoding='utf-8'))
        gaps = [k for k in SITE_KEYS if not str(t.get(k, '')).strip()]
        if gaps:
            missing.append(f'{code}({",".join(gaps[:3])}…)')
            continue
        d = out / ('' if code == DEFAULT_LANG else code)
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(page(code, t, strings[code], css), encoding='utf-8')
        done.append(code)
    print('собрано:', ' '.join(done))
    if missing:
        print('ЖДУТ ПЕРЕВОДА:', ' '.join(missing))


if __name__ == '__main__':
    main()
