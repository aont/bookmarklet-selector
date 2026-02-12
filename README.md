# Bookmarklet Selector Manager

A small web app to manage bookmarklet entries and generate a final selector bookmarklet URL.

## Stack
- Backend: Python, `aiohttp`, `aiosqlite`
- Frontend: HTML + JavaScript
- Minifier: `terser` loaded from CDN in the browser (no Node.js required)

## Run
```bash
pip install -r requirements.txt
python app.py --port 8080
```

Open `http://localhost:8080` (or your chosen port).
