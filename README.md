# Bookmarklet Selector Manager

A small web app to manage bookmarklet entries and generate a final selector bookmarklet URL.

## Stack
- Backend/API server: Python, `aiohttp`, `aiosqlite`
- Frontend server: static HTML + JavaScript from `frontend/index.html`
- Minifier: `terser` loaded from CDN in the browser (no Node.js required)

## Run
```bash
pip install -r requirements.txt
python backend/app.py --api-port 8080 --frontend-port 8081 --frontend-origin http://localhost:8081
```

- Database file defaults to repository root: `./bookmarklets.db`.
- You can override it with `--db-path /path/to/bookmarklets.db`.

## URLs
- Frontend UI: `http://localhost:8081`
- API/bookmarklet server: `http://localhost:8080`

The two services are intentionally split so the frontend and bookmarklet API run on different origins.


## Cross-domain setup
- Frontend can use a custom backend address from the **Backend API** card (saved in browser localStorage).
- You can also inject `window.BOOKMARKLET_API_ORIGIN` before the app script to hardcode an API origin.
- Backend CORS accepts one or more origins via `--frontend-origin` (comma-separated), for example:

```bash
python backend/app.py --frontend-origin http://localhost:8081,https://admin.example.com
```

- To allow all origins during development, pass `--frontend-origin '*'`.
