import io, json, os, re
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from flask import Flask, jsonify, render_template, request, send_file
from bs4 import BeautifulSoup

app = Flask(__name__)
MAX_HTML = 5_000_000

def clean(s):
    return re.sub(r'\s+', ' ', (s or '')).strip()

def fetch_url(url):
    p = urlparse(url)
    if p.scheme not in ('http', 'https'):
        raise ValueError('URL harus diawali http:// atau https://')
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 SocialContentStudio/1.0'})
    with urlopen(req, timeout=20) as r:
        data = r.read(MAX_HTML)
        charset = r.headers.get_content_charset() or 'utf-8'
        return data.decode(charset, errors='replace'), r.geturl()

def shorten_caption(text, title=''):
    text = clean(text)
    if not text:
        return ''
    text = re.sub(r'\s*\(?Foto:\s*[^)]*\)?\s*$', '', text, flags=re.I)
    text = re.sub(r'\s*\(?Dok:\s*[^)]*\)?\s*$', '', text, flags=re.I)
    first = re.split(r'(?<=[.!?])\s+', text)[0].rstrip('.!?')
    words = first.split()
    if len(words) <= 9:
        return first
    for marker in [' yang ', ' saat ', ' ketika ', ' dalam ', ' setelah ', ' karena ']:
        pos = first.lower().find(marker)
        if 0 < pos < 70:
            cand = first[:pos].strip(' ,:-')
            if 3 <= len(cand.split()) <= 9:
                return cand
    return ' '.join(words[:9]).rstrip(',:;')

def extract(url):
    raw, final_url = fetch_url(url)
    soup = BeautifulSoup(raw, 'html.parser')
    for x in soup(['script', 'style', 'noscript', 'svg', 'iframe']):
        x.decompose()
    og = soup.find('meta', property='og:title')
    title = clean(og.get('content')) if og else ''
    if not title and soup.title:
        title = clean(soup.title.get_text())
    desc_meta = soup.find('meta', attrs={'name': 'description'})
    desc = clean(desc_meta.get('content', '')) if desc_meta else ''
    root = soup.find('article') or soup.find('main') or soup.body or soup
    imgs, seen = [], set()
    for img in root.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-original') or img.get('data-lazy-src')
        if not src:
            continue
        src = urljoin(final_url, src)
        if src.startswith('data:') or src in seen:
            continue
        seen.add(src)
        fig = img.find_parent('figure')
        cap = fig.find('figcaption') if fig else None
        caption = clean(cap.get_text(' ', strip=True) if cap else '')
        if not caption:
            caption = clean(img.get('alt') or img.get('title') or '')
        if not caption and img.parent:
            txt = clean(img.parent.get_text(' ', strip=True))
            if txt and len(txt) < 500:
                caption = txt
        imgs.append({'src': src, 'caption': caption, 'short': shorten_caption(caption, title), 'alt': clean(img.get('alt', ''))})
    paragraphs = []
    for p in root.find_all(['p', 'h2', 'h3']):
        t = clean(p.get_text(' ', strip=True))
        if len(t) >= 30:
            paragraphs.append(t)
    return {'url': final_url, 'title': title, 'description': desc, 'image_count': len(imgs), 'images': imgs[:30], 'context': ' '.join(paragraphs[:25])[:6000]}

@app.get('/')
def index():
    return render_template('index.html')

@app.post('/api/analyze')
def analyze():
    try:
        url = (request.get_json(silent=True) or {}).get('url', '').strip()
        if not url:
            raise ValueError('URL belum diisi.')
        return jsonify(extract(url))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.get('/healthz')
def healthz():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8765'))
    app.run(host='0.0.0.0', port=port)
