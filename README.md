# Bookmarklet Selector Manager

A small web app to manage bookmarklet entries and generate a final selector bookmarklet URL.

## Stack
- Backend/API server: Python, `aiohttp`, `aiosqlite`
- Frontend server: static HTML + JavaScript from `frontend/index.html`
- Minifier: `terser` loaded from CDN in the browser (no Node.js required)

## Run
```bash
pip install -r requirements.txt
python app.py --api-port 8080 --frontend-port 8081 --frontend-origin http://localhost:8081
```

## URLs
- Frontend UI: `http://localhost:8081`
- API/bookmarklet server: `http://localhost:8080`

The two services are intentionally split so the frontend and bookmarklet API run on different origins.
