#!/usr/bin/env python3
"""Страница «Как настроить ваше облако lambit2FA» — 22 языка.

ТЗ: store/site/ТЗ_облако_lambit2FA.md. Адреса зашиты в приложение:
/lambit2fa/cloud/ (en) и /lambit2fa/cloud/<код>/ — менять нельзя.

Источник — store/site/cloud/<язык>.md, ровно как есть: тексты не переводятся
и не правятся (названия кнопок сверены с приложением). Разметка md простая:
  # …        заголовок страницы
  ## …       подзаголовок
  {IMG:имя}  снимок store/site/cloud/img/<язык>/имя.png — по центру, ~300 px,
             клик открывает полный размер
  прочее     абзацы
Внизу — ссылка на /lambit2fa/download/<код>/ с download_title из site_strings.json.

Запуск: python3 tools/build_cloud.py --src ~/lambit2FAlinux/AEFauthentic/store
"""
import argparse
import html
import json
import re
import shutil
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

CSS = """*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#f4f6f9;--panel:#fff;--ink:#14181f;--dim:#5c6675;--accent:#1a5fd0;--accent-sub:#e8f0fe;--line:#e0e5ee;--shadow:0 1px 2px rgba(20,24,31,.05),0 3px 12px rgba(20,24,31,.07)}
@media (prefers-color-scheme:dark){:root{--bg:#10141b;--panel:#1a2029;--ink:#e8ecf2;--dim:#93a0b4;--accent:#6ea8ff;--accent-sub:#1f2c42;--line:#28303d;--shadow:0 1px 2px rgba(0,0,0,.35),0 3px 12px rgba(0,0,0,.35)}}
body{font-family:-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.6}
:lang(zh){font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif}
:lang(ja){font-family:"Hiragino Sans","Yu Gothic","Meiryo","Noto Sans CJK JP",sans-serif}
:lang(ko){font-family:"Apple SD Gothic Neo","Malgun Gothic","Noto Sans CJK KR",sans-serif}
:lang(hi){font-family:"Kohinoor Devanagari","Nirmala UI","Noto Sans Devanagari",sans-serif}
:lang(ar){font-family:"SF Arabic","Geeza Pro","Tahoma","Noto Sans Arabic",sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:780px;margin:0 auto;padding:0 20px}
.site-head{background:var(--panel);border-bottom:1px solid var(--line)}
.head-in{display:flex;align-items:center;gap:12px 16px;padding:14px 0;flex-wrap:wrap}
.logo{font-size:20px;font-weight:700;letter-spacing:.5px;color:var(--ink)}
.logo span{color:var(--accent)}
.head-sp{flex:1}
.langs{display:flex;gap:4px;flex-wrap:wrap;max-width:560px;justify-content:flex-end}
.langs a{border:1px solid var(--line);border-radius:14px;padding:3px 9px;font-size:12px;color:var(--dim)}
.langs a:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.langs a.on{background:var(--accent);border-color:var(--accent);color:#fff}
main{padding:34px 0 60px}
article{background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);padding:28px 30px}
h1{font-size:28px;line-height:1.25;margin-bottom:14px}
h2{font-size:19px;margin:28px 0 10px}
p{margin:0 0 12px;font-size:16px}
p.intro{font-size:17px;color:var(--dim)}
figure.shot{margin:18px auto 22px;text-align:center}
figure.shot a{display:inline-block}
figure.shot img{display:block;width:300px;max-width:100%;height:auto;border-radius:16px;border:1px solid var(--line);box-shadow:var(--shadow);background:#fff}
.more{margin-top:30px;padding-top:18px;border-top:1px solid var(--line)}
.more a{display:inline-block;background:var(--accent);color:#fff;border-radius:9px;padding:9px 16px;font-size:14px}
.more a:hover{text-decoration:none;opacity:.9}
footer{border-top:1px solid var(--line);padding:22px 0 40px;font-size:13px;color:var(--dim)}
@media(max-width:560px){h1{font-size:23px}article{padding:20px 18px}figure.shot img{width:100%}}"""


def esc(s):
    return html.escape(s, quote=False)


def url_for(code):
    return '/lambit2fa/cloud/' if code == DEFAULT_LANG else f'/lambit2fa/cloud/{code}/'


def download_url(code):
    return '/lambit2fa/download/' if code == DEFAULT_LANG else f'/lambit2fa/download/{code}/'


def render_md(md, code, img_names):
    """md -> HTML; тексты экранируются и не правятся."""
    out, title, para, first_p = [], '', [], True
    def flush():
        nonlocal para, first_p
        if para:
            cls = ' class="intro"' if first_p else ''
            out.append(f'<p{cls}>{esc(" ".join(para))}</p>'); first_p = False; para = []
    for line in md.splitlines():
        s = line.rstrip()
        if not s:
            flush(); continue
        if s.startswith('# ') and not title:
            title = s[2:].strip(); continue
        if s.startswith('## '):
            flush(); out.append(f'<h2>{esc(s[3:].strip())}</h2>'); continue
        m = re.fullmatch(r'\{IMG:([a-z0-9-]+)\}', s)
        if m:
            flush(); name = m.group(1); img_names.append(name)
            src = f'/lambit2fa/cloud/img/{code}/{name}.png'
            out.append(f'<figure class="shot"><a href="{src}"><img src="{src}" alt="" width="300" height="652"></a></figure>')
            continue
        para.append(s)
    flush()
    return title, '\n'.join(out)


def page(code, title, body, dl_title):
    tag = TAG.get(code, code)
    dir_attr = ' dir="rtl"' if code in RTL else ''
    alts = '\n'.join(f'<link rel="alternate" hreflang="{TAG.get(c, c)}" href="https://vegavit.eu{url_for(c)}">' for c in NAMES)
    alts += '\n<link rel="alternate" hreflang="x-default" href="https://vegavit.eu/lambit2fa/cloud/">'
    langs = ''.join(f'<a href="{url_for(c)}" lang="{TAG.get(c, c)}"{" class=\"on\"" if c == code else ""}>{esc(n)}</a>' for c, n in NAMES.items())
    home = '/' if code == DEFAULT_LANG else f'/{code}/'
    return f"""<!DOCTYPE html>
<html lang="{tag}"{dir_attr}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} — VEGAVIT EOOD</title>
<link rel="canonical" href="https://vegavit.eu{url_for(code)}">
{alts}
<meta name="color-scheme" content="light dark">
<style>{CSS}</style>
</head>
<body>

<header class="site-head">
  <div class="wrap head-in">
    <a class="logo" href="{home}" dir="ltr">VEGAVIT<span>.</span></a>
    <div class="head-sp"></div>
    <div class="langs">{langs}</div>
  </div>
</header>

<main class="wrap">
<article>
<h1>{esc(title)}</h1>
{body}
<p class="more"><a href="{download_url(code)}">{esc(dl_title)}</a></p>
</article>
</main>

<footer>
  <div class="wrap">© 2026 VEGAVIT EOOD · <a href="{home}">vegavit.eu</a></div>
</footer>

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
    cloud = src / 'site' / 'cloud'

    for code in NAMES:
        md = (cloud / f'{code}.md').read_text(encoding='utf-8')
        names = []
        title, body = render_md(md, code, names)
        assert title, f'{code}: нет заголовка'
        img_out = out / 'lambit2fa' / 'cloud' / 'img' / code
        img_out.mkdir(parents=True, exist_ok=True)
        for n in names:
            srcf = cloud / 'img' / code / f'{n}.png'
            assert srcf.exists(), f'{code}: нет снимка {n}.png'
            shutil.copy2(srcf, img_out / f'{n}.png')
        d = out / 'lambit2fa' / 'cloud' / ('' if code == DEFAULT_LANG else code)
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(page(code, title, body, strings[code]['download_title']), encoding='utf-8')
    print(f'собрано страниц: {len(NAMES)}')


if __name__ == '__main__':
    main()
