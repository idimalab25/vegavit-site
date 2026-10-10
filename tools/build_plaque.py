#!/usr/bin/env python3
"""Блок lambit2FA с четырьмя QR на страницах ПОЛИТИКИ.

Главную собирает tools/build_site.py — там плашка встроена в шаблон,
и этот скрипт её больше не трогает. Здесь остаются только три страницы
политики (ru, en, bg): перед подвалом появляется короткий блок со ссылкой
на страницу скачивания того же языка и четырьмя QR — Mac, Google Play,
iPhone, APK.

Надписи берутся из store/site/site_strings.json для трёх языков сайта
(en, bg, ru) — ничего не сочиняется. Скрипт идемпотентен: повторный
запуск ничего не удваивает.

Запуск:  python3 tools/build_plaque.py --src ~/lambit2FAlinux/AEFauthentic/store
"""
import argparse
import html
import json
import re
from pathlib import Path

QRS = [('iphone-app-store', 'p_iphone'), ('mac-app-store', 'p_mac'),
       ('android-google-play', 'p_android')]
# QR на APK показывается только когда сам файл APK лежит в store/build/site:
# пока его нет, Android — только через Google Play (хозяин, 10.10.2026).
QR_APK = ('android-apk', 'p_apk')
LANGS = 'en ru es ar de pt zh fi fr nl id hi ja ko tr vi it pl ro el hu bg'.split()
# Английская политика — та, что вписана в кабинет Apple: её не трогаем вовсе.
SKIP = {'en'}


def download_url(code):
    return '/lambit2fa/download/' if code == 'en' else f'/lambit2fa/download/{code}/'


def privacy_path(code):
    return 'lambit2fa/privacy/index.html' if code == 'ru' else f'lambit2fa/privacy/{code}/index.html'
MARK = '<!-- lambit2FA: плашка и QR, собирает tools/build_plaque.py -->'

_UNUSED_HOME_CSS = """
  /* плашка lambit2FA со скачиванием */
  .card#lambit2fa { grid-column: 1 / -1; display: flex; gap: 20px; flex-wrap: wrap; align-items: flex-start; }
  .card#lambit2fa .plaque-main { flex: 1 1 320px; min-width: 260px; color: inherit; text-decoration: none; display: block; }
  .card#lambit2fa .plaque-main:hover { text-decoration: none; }
  .card#lambit2fa .plaque-main:hover h3 { color: var(--accent); }
  .card#lambit2fa .dl-btn {
    display: inline-block; margin-top: 12px; background: var(--accent); color: #fff;
    border-radius: 9px; padding: 9px 18px; font-size: 14px; font-weight: 600;
  }
  .qrs { display: flex; gap: 12px; flex-wrap: wrap; }
  .qr { width: 104px; text-align: center; font-size: 11.5px; color: var(--text-soft); line-height: 1.3; }
  .qr img { display: block; width: 104px; height: 104px; background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: 5px; }
  .qr span { display: block; margin-top: 5px; }
  .scan-hint { font-size: 12px; color: var(--text-soft); flex-basis: 100%; }
"""

PRIV_CSS = """
.getapp{background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);padding:20px 22px;margin:30px 0 10px}
.getapp h2{font-size:17px;margin-bottom:6px}
.getapp p{color:var(--text-soft);font-size:14px;margin-bottom:12px}
.getapp .qrs{display:flex;gap:12px;flex-wrap:wrap}
.getapp .qr{width:104px;text-align:center;font-size:11.5px;color:var(--text-soft);line-height:1.3}
.getapp .qr img{display:block;width:104px;height:104px;background:#fff;border:1px solid var(--line);border-radius:8px;padding:5px}
.getapp .qr span{display:block;margin-top:5px}
.getapp .dl-btn{display:inline-block;margin-top:12px;background:var(--accent);color:#fff;border-radius:9px;padding:9px 18px;font-size:14px;font-weight:600}
.getapp .dl-btn:hover{text-decoration:none;opacity:.9}
"""


def esc(s):
    return html.escape(s, quote=False)


def qr_html(t, indent='        ', i18n=False):
    out = []
    for name, key in QRS:
        # на главной подпись переключается вместе с языком страницы
        attr = f' data-i18n="qr_{key}"' if i18n else ''
        out.append(f'{indent}<div class="qr"><img src="/lambit2fa/download/qr/{name}.svg" '
                   f'alt="{esc(t[key])}" width="104" height="104">'
                   f'<span{attr}>{esc(t[key])}</span></div>')
    return '\n'.join(out)



def patch_privacy(path, t, code):
    s = path.read_text(encoding='utf-8')
    # убрать прошлую вставку целиком, вместе с пустой строкой перед ней,
    # иначе повторный запуск не находит места вставки
    s = re.sub(r'\n*<section class="getapp">.*?</section>\n', '\n', s, flags=re.S)
    block = f"""
<section class="getapp">
  {MARK}
  <h2><a href="{download_url(code)}">{esc(t['plaque_title'])}</a></h2>
  <p>{esc(t['plaque_text'])}</p>
  <div class="qrs">
{qr_html(t, indent='    ')}
  </div>
  <p style="margin:12px 0 0">{esc(t['scan_hint'])}</p>
  <a class="dl-btn" href="{download_url(code)}">{esc(t['plaque_button'])}</a>
</section>
"""
    assert '</article>\n</main>' in s, f'{path}: не нашёл конец статьи'
    s = s.replace('</article>\n</main>', '</article>\n' + block + '</main>', 1)
    if '.getapp{' not in s:
        s = s.replace('</style>', PRIV_CSS + '</style>', 1)
    path.write_text(s, encoding='utf-8')
    print(f'  политика {code}: блок QR и ссылка на скачивание')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', default='.')
    a = ap.parse_args()
    src, out = Path(a.src).expanduser(), Path(a.out).expanduser()
    S = json.loads((src / 'site' / 'site_strings.json').read_text(encoding='utf-8'))
    if list((src / 'build' / 'site').glob('*.apk')):
        QRS.append(QR_APK)
    for code in LANGS:
        if code in SKIP:
            continue
        f = out / privacy_path(code)
        if not f.exists():
            print(f'  политика {code}: страницы нет, пропускаю')
            continue
        patch_privacy(f, S[code], code)


if __name__ == '__main__':
    main()
