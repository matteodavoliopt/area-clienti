"""Costruisce il sito "Area clienti" di Matteo D'Avolio.

Per ogni file in data/*.json ({"slug", "source", "data"}) crea <slug>/index.html
partendo da template.html, con i dati del cliente incorporati (senza email).
Uso: python3 build.py
"""
import json, re, html, pathlib

ROOT = pathlib.Path(__file__).parent
TPL = (ROOT / 'template.html').read_text(encoding='utf-8')
_cfg = ROOT / 'config.json'
CONFIG = json.loads(_cfg.read_text(encoding='utf-8')) if _cfg.exists() else {}

HEAD = '''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<title>{title}</title>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{short}">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#F2F4F3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0F1413" media="(prefers-color-scheme: dark)">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png?v=2">
<link rel="icon" type="image/png" href="../assets/favicon-32.png?v=2">
<link rel="manifest" href="manifest.webmanifest">
<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0;font:14px system-ui,sans-serif}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
'''

def page(entry):
    d = dict(entry['data'])
    d['client'] = {k: v for k, v in d.get('client', {}).items() if k != 'email'}
    name = (d['client'].get('name') or 'Cliente').strip()
    js = json.dumps(d, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    body = re.sub(r'<title>.*?</title>\s*', '', TPL, count=1, flags=re.S)
    body = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\s*', '', body, count=1)
    body, n = re.subn(r'(<script type="application/json" id="data">).*?(</script>)',
                      lambda m: m.group(1) + js + m.group(2), body, count=1, flags=re.S)
    assert n == 1, 'blocco dati non trovato nel template'
    first = name.split()[0]
    site = {'slug': entry['slug'], 'form': CONFIG.get('form')}
    boot = '<script>window.SITE=' + json.dumps(site, ensure_ascii=False).replace('<', '\\u003c') + ';</script>\n'
    return HEAD.format(title=html.escape('Area riservata · ' + name), short=html.escape(first)) + boot + body + '\n</body>\n</html>\n', first

def manifest(first):
    return json.dumps({
        "name": "Area riservata " + first, "short_name": first,
        "start_url": "./", "scope": "./", "display": "standalone",
        "background_color": "#F2F4F3", "theme_color": "#1B7D8D", "lang": "it",
        "icons": [{"src": "../assets/icon-192.png?v=2", "sizes": "192x192", "type": "image/png"},
                  {"src": "../assets/icon-512.png?v=2", "sizes": "512x512", "type": "image/png"}]
    }, ensure_ascii=False, indent=1)

def main():
    slugs = []
    for f in sorted((ROOT / 'data').glob('*.json')):
        entry = json.loads(f.read_text(encoding='utf-8'))
        slug = entry['slug']
        assert re.fullmatch(r'[a-z0-9-]+', slug), slug
        out = ROOT / slug
        out.mkdir(exist_ok=True)
        doc, first = page(entry)
        (out / 'index.html').write_text(doc, encoding='utf-8')
        (out / 'manifest.webmanifest').write_text(manifest(first), encoding='utf-8')
        slugs.append(slug)
    print('Pagine create:', len(slugs))

if __name__ == '__main__':
    main()
