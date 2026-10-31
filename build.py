"""Costruisce il sito "Area clienti" di Matteo D'Avolio.

Per ogni file in data/*.json ({"slug", "source", "data"}) crea <slug>/index.html
partendo da template.html, con i dati del cliente incorporati (con email).
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
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png?v=5">
<link rel="icon" type="image/png" href="../assets/favicon-32.png?v=5">
<link rel="manifest" href="manifest.webmanifest">
<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0;font:14px system-ui,sans-serif}}img{{max-width:100%}}[hidden]{{display:none!important}}html,body{{background:#F2F4F3}}@media (prefers-color-scheme:dark){{html,body{{background:#0F1413}}}}.splash{{position:fixed;inset:0;z-index:50;background:#F2F4F3;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;padding:24px;text-align:center;transition:opacity .45s ease}}@media (prefers-color-scheme:dark){{.splash{{background:#0F1413}}}}.splash.out{{opacity:0;pointer-events:none}}.splash .logo{{width:96px;height:auto;fill:#2397A9;stroke:#2397A9;stroke-width:22;stroke-linejoin:round;overflow:visible}}.splash .s-name{{font:800 30px/1 'Barlow Condensed','Arial Narrow',Arial,sans-serif;letter-spacing:.05em;text-transform:uppercase;color:#141C1A}}.splash .s-role{{font:600 clamp(9px,2.9vw,12px)/1.3 system-ui,sans-serif;letter-spacing:.1em;white-space:nowrap;text-transform:uppercase;color:#5D6B67}}@media (prefers-color-scheme:dark){{.splash .logo{{fill:#3FB4C5;stroke:#3FB4C5}}.splash .s-name{{color:#E8EEEC}}.splash .s-role{{color:#93A29E}}}}</style>
</head>
<body>
{splash}'''

LOGO = re.search(r"var LOGO = '(<svg.*?</svg>)';", (ROOT / 'template.html').read_text(encoding='utf-8')).group(1)
SPLASH = '<div class="splash" id="splash0" aria-hidden="true">' + LOGO + '<div class="s-name">Matteo D’Avolio</div><div class="s-role">Personal Trainer &amp; Massaggiatore sportivo</div></div>\n'
FONTS_RE = re.compile(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/[^"]+)">')
def nonblock(s):
    return FONTS_RE.sub(lambda m: '<link rel="stylesheet" href="' + m.group(1) + '" media="print" onload="this.media=\'all\'">', s, count=1)

def page(entry):
    d = dict(entry['data'])
    d['client'] = dict(d.get('client', {}))
    d['pkg'] = {k: v for k, v in (d.get('pkg') or {}).items() if k not in ('price', 'paidAmt', 'recapTs')}
    d['pkgHist'] = [{k: v for k, v in x.items() if k not in ('price', 'paidAmt')} for x in (d.get('pkgHist') or [])]
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
    return HEAD.format(title=html.escape('Area riservata · ' + name), short=html.escape(first), splash=SPLASH) + boot + nonblock(body) + '\n</body>\n</html>\n', first

def manifest(first):
    return json.dumps({
        "name": "Area riservata " + first, "short_name": first,
        "start_url": "./", "scope": "./", "display": "standalone",
        "background_color": "#0F1413", "theme_color": "#1B7D8D", "lang": "it",
        "icons": [{"src": "../assets/icon-192.png?v=5", "sizes": "192x192", "type": "image/png"},
                  {"src": "../assets/icon-512.png?v=5", "sizes": "512x512", "type": "image/png"}]
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
    panel = CONFIG.get('panel')
    if panel and (ROOT / 'pannello.html').exists():
        assert re.fullmatch(r'[a-z0-9-]+', panel), panel
        clients = []
        for f in sorted((ROOT / 'data').glob('*.json')):
            e = json.loads(f.read_text(encoding='utf-8')); d = e['data']; c = d.get('client', {})
            clients.append({'name': c.get('name', ''), 'url': e.get('source', ''), 'site': 'https://matteodavoliopt.github.io/area-clienti/' + e['slug'] + '/',
                            'g': c.get('g', 'm'), 'start': c.get('start', ''), 'end': c.get('end', ''), 'pkg': d.get('pkg') or {}, 'pkgHist': d.get('pkgHist') or [],
                            'appts': [{'d': a.get('d', ''), 't': a.get('t', ''), 'what': a.get('what', '')} for a in d.get('appts', [])]})
        clients.sort(key=lambda x: x['name'].lower())
        upd = max([json.loads(f.read_text(encoding='utf-8'))['data'].get('updated', '') for f in (ROOT / 'data').glob('*.json')] or [''])
        js = json.dumps({'updated': upd, 'clients': clients}, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
        body = (ROOT / 'pannello.html').read_text(encoding='utf-8')
        body, n = re.subn(r'(<script type="application/json" id="data">).*?(</script>)', lambda m: m.group(1) + js + m.group(2), body, count=1, flags=re.S)
        assert n == 1
        body = body.replace('<script>', '<script>window.PFORM=' + json.dumps(CONFIG.get('form') or {}) + ';</script>\n<script>', 1)
        out = ROOT / panel; out.mkdir(exist_ok=True)
        head = HEAD.format(title='Pannello clienti', short='Pannello', splash=SPLASH).replace('<meta name="apple-mobile-web-app-status-bar-style" content="default">', '<meta name="apple-mobile-web-app-status-bar-style" content="default">')
        (out / 'index.html').write_text(head + nonblock(body) + '\n</body>\n</html>\n', encoding='utf-8')
        (out / 'manifest.webmanifest').write_text(json.dumps({"name": "Pannello clienti", "short_name": "Pannello", "start_url": "./", "scope": "./", "display": "standalone",
            "background_color": "#0F1413", "theme_color": "#1B7D8D", "lang": "it",
            "icons": [{"src": "../assets/icon-192.png?v=5", "sizes": "192x192", "type": "image/png"}, {"src": "../assets/icon-512.png?v=5", "sizes": "512x512", "type": "image/png"}]}, ensure_ascii=False, indent=1), encoding='utf-8')
        print('Pannello creato:', panel)
    print('Pagine create:', len(slugs))

if __name__ == '__main__':
    main()
