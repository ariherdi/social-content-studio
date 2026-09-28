# Social Content Studio — POC V1

URL artikel → ekstraksi artikel/foto → caption → rewrite lokal → edit → preview → download PNG.

## Jalankan lokal

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Buka http://localhost:8765

## Deploy ke Render

1. Push folder ini ke repository GitHub.
2. Di Render pilih **New > Web Service**.
3. Connect repository GitHub tersebut.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
6. Deploy.

`render.yaml` sudah disediakan sehingga Render dapat membaca konfigurasi tersebut.

## Catatan POC

- Belum ada login/authentication.
- Belum ada integrasi sosial media.
- Rewrite masih rule-based sebagai placeholder AI.
- Beberapa website memakai Cloudflare/JavaScript/lazy loading sehingga ekstraksi dapat berbeda-beda.
- Export PNG dari browser dapat gagal untuk gambar dari domain yang tidak mengizinkan CORS. Ini akan diperbaiki pada versi berikutnya dengan image proxy/server-side processing.
