#!/usr/bin/env python3
"""Политика lambit2FA на остальных языках — из английского шаблона.

Английская страница /lambit2fa/privacy/en/ — та, что вписана в кабинет Apple;
она НЕ трогается и служит шаблоном: её разметка, стили и порядок блоков.
Русская и болгарская написаны руками раньше и тоже не пересобираются.
Остальные 19 языков собираются отсюда: каждый блок статьи (заголовок, абзац,
строка таблицы, пункт списка) переведён в i18n/privacy/<код>.json под своим
номером; встроенные теги <strong>, <a>, <br>, <code> в переводе сохраняются.

Запуск:  python3 tools/build_privacy.py            — собрать все, для которых есть перевод
         python3 tools/build_privacy.py --dump     — показать блоки английского шаблона
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / 'lambit2fa' / 'privacy' / 'en' / 'index.html'
I18N = ROOT / 'i18n' / 'privacy'
MANUAL = {'en', 'ru', 'bg'}          # написаны руками, не собираются
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


def privacy_url(code):
    return '/lambit2fa/privacy/' if code == 'ru' else f'/lambit2fa/privacy/{code}/'


def split_blocks(article_html):
    """Блоки верхнего уровня статьи: (тег, внутренний HTML). <hr> — пустой."""
    blocks = []
    pat = re.compile(r'<(h1|h2|p|ul|table|hr)(?:\s[^>]*)?>(.*?)</\1>|<hr>', re.S)
    for m in pat.finditer(article_html):
        if m.group(0) == '<hr>':
            blocks.append(('hr', ''))
        else:
            blocks.append((m.group(1), m.group(2).strip()))
    return blocks


def leaves(blocks):
    """Переводимые единицы: для ul — каждый <li>, для table — каждая ячейка."""
    out = []
    for i, (tag, inner) in enumerate(blocks):
        if tag == 'hr':
            continue
        if tag == 'ul':
            for j, li in enumerate(re.findall(r'<li>(.*?)</li>', inner, re.S)):
                out.append((f'b{i}.{j}', li.strip()))
        elif tag == 'table':
            cells = re.findall(r'<t[hd]>(.*?)</t[hd]>', inner, re.S)
            for j, c in enumerate(cells):
                out.append((f'b{i}.{j}', c.strip()))
        else:
            out.append((f'b{i}', inner))
    return out


def rebuild(blocks, tr):
    """Собирает статью, подставляя переводы по ключам."""
    out = []
    for i, (tag, inner) in enumerate(blocks):
        if tag == 'hr':
            out.append('<hr>')
        elif tag == 'ul':
            items = re.findall(r'<li>(.*?)</li>', inner, re.S)
            out.append('<ul>\n' + '\n'.join(f'<li>{tr[f"b{i}.{j}"]}</li>' for j in range(len(items))) + '\n</ul>')
        elif tag == 'table':
            cells = re.findall(r'<t[hd]>(.*?)</t[hd]>', inner, re.S)
            n = len(cells)
            rows = ['<table>', '<thead><tr><th>' + tr[f'b{i}.0'] + '</th><th>' + tr[f'b{i}.1'] + '</th></tr></thead>', '<tbody>']
            for j in range(2, n, 2):
                rows.append(f'<tr><td>{tr[f"b{i}.{j}"]}</td><td>{tr[f"b{i}.{j+1}"]}</td></tr>')
            rows += ['</tbody>', '</table>']
            out.append('\n'.join(rows))
        else:
            cls = ' class="meta"' if (tag == 'p' and i == 1) else ''
            out.append(f'<{tag}{cls}>{tr[f"b{i}"]}</{tag}>')
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dump', action='store_true')
    a = ap.parse_args()

    src = EN.read_text(encoding='utf-8')
    head = src[:src.index('<body>')]
    article = re.search(r'<article class="doc">(.*?)</article>', src, re.S).group(1)
    blocks = split_blocks(article)
    units = leaves(blocks)

    if a.dump:
        for k, v in units:
            print(f'{k}\t{v}')
        print(f'# блоков: {len(blocks)}, переводимых единиц: {len(units)}', flush=True)
        return

    done, missing = [], []
    for code in NAMES:
        if code in MANUAL:
            continue
        f = I18N / f'{code}.json'
        if not f.exists():
            missing.append(code); continue
        tr = json.loads(f.read_text(encoding='utf-8'))
        gaps = [k for k, _ in units if not str(tr.get(k, '')).strip()]
        if gaps:
            missing.append(f'{code}({len(gaps)} пусто)'); continue

        tag = TAG.get(code, code)
        h = head.replace('<html lang="en">', f'<html lang="{tag}"{" dir=\"rtl\"" if code in RTL else ""}>')
        h = re.sub(r'<title>.*?</title>', f'<title>{tr["title"]}</title>', h)
        h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{tr["desc"]}">', h)
        langs = ''.join(f'<a href="{privacy_url(c)}"{" class=\"on\"" if c == code else ""}>{c.upper()}</a>' for c in NAMES)
        page = h + f"""<body>

<header class="site-head">
  <div class="wrap head-in">
    <a class="logo" href="/{code}/" dir="ltr">VEGA<span>VIT</span></a>
    <div class="head-sp"></div>
    <nav class="langs">{langs}</nav>
  </div>
</header>
<main class="wrap">
<article class="doc">
{rebuild(blocks, tr)}
</article>
</main>

<footer>
  <div class="wrap">{tr["foot"]} · <a href="/{code}/">vegavit.eu</a></div>
</footer>

</body>
</html>
"""
        d = ROOT / 'lambit2fa' / 'privacy' / code
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(page, encoding='utf-8')
        done.append(code)
    print('собрано:', ' '.join(done) or '—')
    if missing:
        print('ЖДУТ ПЕРЕВОДА:', ' '.join(missing))


if __name__ == '__main__':
    main()
