import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import aiosqlite
from aiohttp import web

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DEFAULT_DB_PATH = REPO_ROOT / "bookmarklets.db"
DB_PATH = DEFAULT_DB_PATH
FRONTEND_DIR = REPO_ROOT / "frontend"
INDEX_PATH = FRONTEND_DIR / "index.html"

DEFAULT_ITEMS = [
    {
        "title": "Sample: Alert",
        "match_js": "function (url) { return true; }",
        "code_js": "function () { alert('hello'); }",
        "position": 0,
    },
    {
        "title": "Example.com Only",
        "match_js": "function (url) { return url.hostname === 'example.com'; }",
        "code_js": "function () { alert('example.com page'); }",
        "position": 1,
    },
    {
        "title": "Admin Path Only",
        "match_js": "function (url) { return url.pathname.startsWith('/admin'); }",
        "code_js": "function () { alert('admin page'); }",
        "position": 2,
    },
]


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS bookmarklets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                match_js TEXT NOT NULL,
                code_js TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()

        async with db.execute("SELECT COUNT(*) FROM bookmarklets") as cursor:
            row = await cursor.fetchone()
        if row and row[0] == 0:
            for item in DEFAULT_ITEMS:
                await db.execute(
                    """
                    INSERT INTO bookmarklets (title, match_js, code_js, position)
                    VALUES (?, ?, ?, ?)
                    """,
                    (item["title"], item["match_js"], item["code_js"], item["position"]),
                )
            await db.commit()


async def list_items() -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, title, match_js, code_js, position FROM bookmarklets ORDER BY position, id"
        ) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]


def js_string(value: str) -> str:
    return json.dumps(value)


def build_selector_source(items: list[dict[str, Any]]) -> str:
    item_literals = []
    for item in items:
        item_literals.append(
            """    {
      title: %s,
      match: %s,
      code: %s,
    }"""
            % (
                js_string(item["title"]),
                item["match_js"],
                item["code_js"],
            )
        )

    items_source = ",\n".join(item_literals)

    return f"""!(function () {{
  'use strict';

  var items = [
{items_source}
  ];

  var ROOT_ID = 'bookmarklet-selector';
  var old = document.getElementById(ROOT_ID);
  if (old) old.remove();

  var prevOverflow = document.documentElement.style.overflow;
  document.documentElement.style.overflow = 'hidden';

  var currentUrl = null;
  try {{
    currentUrl = new URL(location.href);
  }} catch (e) {{}}

  function isMatch(item, urlObj) {{
    if (!urlObj) return false;
    if (typeof item.match !== 'function') return true;
    try {{
      return item.match(urlObj) === true;
    }} catch (e) {{
      return false;
    }}
  }}

  // --- UI: minimal ---
  var overlay = document.createElement('div');
  overlay.id = ROOT_ID;
  overlay.style.position = 'fixed';
  overlay.style.inset = '0';
  overlay.style.zIndex = '2147483647';
  overlay.style.background = 'rgba(0,0,0,0.25)';
  overlay.style.display = 'flex';
  overlay.style.alignItems = 'center';
  overlay.style.justifyContent = 'center';
  overlay.style.padding = '16px';
  overlay.style.boxSizing = 'border-box';

  var panel = document.createElement('div');
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-modal', 'true');
  panel.style.width = 'min(560px, 100%)';
  panel.style.maxHeight = 'min(520px, 100%)';
  panel.style.background = '#fff';
  panel.style.color = '#111';
  panel.style.border = '1px solid #ddd';
  panel.style.borderRadius = '10px';
  panel.style.boxShadow = '0 10px 30px rgba(0,0,0,0.15)';
  panel.style.display = 'flex';
  panel.style.flexDirection = 'column';
  panel.style.overflow = 'hidden';
  panel.style.font =
    '14px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif';
  overlay.appendChild(panel);

  var header = document.createElement('div');
  header.style.display = 'flex';
  header.style.alignItems = 'center';
  header.style.justifyContent = 'space-between';
  header.style.padding = '10px 12px';
  header.style.borderBottom = '1px solid #eee';

  var hTitle = document.createElement('div');
  hTitle.textContent = 'Bookmarklets';
  hTitle.style.fontWeight = '600';

  var closeBtn = document.createElement('button');
  closeBtn.type = 'button';
  closeBtn.textContent = '×';
  closeBtn.setAttribute('aria-label', 'Close');
  closeBtn.style.width = '32px';
  closeBtn.style.height = '32px';
  closeBtn.style.border = '1px solid #ddd';
  closeBtn.style.borderRadius = '8px';
  closeBtn.style.background = '#fff';
  closeBtn.style.cursor = 'pointer';
  closeBtn.style.fontSize = '18px';
  closeBtn.style.lineHeight = '1';
  closeBtn.style.color = '#333';

  header.appendChild(hTitle);
  header.appendChild(closeBtn);
  panel.appendChild(header);

  var body = document.createElement('div');
  body.style.padding = '12px';
  body.style.display = 'flex';
  body.style.flexDirection = 'column';
  body.style.gap = '10px';
  panel.appendChild(body);

  var input = document.createElement('input');
  input.type = 'text';
  input.placeholder = 'Search...';
  input.style.width = '100%';
  input.style.boxSizing = 'border-box';
  input.style.padding = '10px';
  input.style.borderRadius = '8px';
  input.style.border = '1px solid #ddd';
  input.style.background = '#fff';
  input.style.color = '#111';
  input.style.outline = 'none';
  body.appendChild(input);

  var list = document.createElement('div');
  list.style.border = '1px solid #ddd';
  list.style.borderRadius = '8px';
  list.style.overflow = 'auto';
  list.style.maxHeight = '320px';
  body.appendChild(list);

  var footer = document.createElement('div');
  footer.style.display = 'flex';
  footer.style.gap = '8px';
  footer.style.padding = '10px 12px';
  footer.style.borderTop = '1px solid #eee';

  function btn(label, primary) {{
    var b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    b.style.flex = '1';
    b.style.padding = '10px';
    b.style.borderRadius = '8px';
    b.style.border = '1px solid #ddd';
    b.style.background = primary ? '#111' : '#fff';
    b.style.color = primary ? '#fff' : '#111';
    b.style.cursor = 'pointer';
    return b;
  }}

  var runBtn = btn('Run', true);
  var cancelBtn = btn('Cancel', false);
  footer.appendChild(runBtn);
  footer.appendChild(cancelBtn);
  panel.appendChild(footer);

  // --- list logic ---
  var filtered = [];
  var active = 0;
  var optionEls = [];

  function rebuildFiltered(query) {{
    var q = (query || '').toLowerCase();
    filtered = items
      .map(function (it, i) {{
        return {{ index: i, title: it.title }};
      }})
      .filter(function (x) {{
        var item = items[x.index];
        return isMatch(item, currentUrl) && x.title.toLowerCase().includes(q);
      }});
    active = 0;
  }}

  function setActive(pos) {{
    if (!filtered.length) return;
    active = Math.max(0, Math.min(pos, filtered.length - 1));
    optionEls.forEach(function (el, i) {{
      el.style.background = i === active ? '#f3f4f6' : '#fff';
      el.style.outline = i === active ? '2px solid #111' : 'none';
      el.style.outlineOffset = '-2px';
    }});
    var el = optionEls[active];
    if (el) el.scrollIntoView({{ block: 'nearest' }});
  }}

  function render() {{
    list.innerHTML = '';
    optionEls = [];

    if (!filtered.length) {{
      var empty = document.createElement('div');
      empty.textContent = 'No matching items';
      empty.style.padding = '10px';
      empty.style.color = '#666';
      list.appendChild(empty);
      return;
    }}

    filtered.forEach(function (item, pos) {{
      var row = document.createElement('div');
      row.textContent = item.title;
      row.style.padding = '10px';
      row.style.cursor = 'pointer';
      row.style.userSelect = 'none';
      row.style.borderBottom = '1px solid #eee';
      row.onmouseenter = function () {{
        setActive(pos);
      }};
      row.onclick = function () {{
        setActive(pos);
        runSelected();
      }};
      list.appendChild(row);
      optionEls.push(row);
    }});

    // last divider cleanup
    var last = list.lastElementChild;
    if (last && last.style) last.style.borderBottom = 'none';

    setActive(active);
  }}

  function cleanup() {{
    document.documentElement.style.overflow = prevOverflow;
    document.removeEventListener('keydown', onKey, true);
    overlay.remove();
  }}

  function runSelected() {{
    if (!filtered.length) return;
    var item = items[filtered[active].index];
    cleanup();
    try {{
      item.code.call(window);
    }} catch (e) {{
      alert('Bookmarklet error: ' + e.message);
    }}
  }}

  function onKey(e) {{
    if (e.key === 'Escape') {{
      e.preventDefault();
      cleanup();
    }} else if (e.key === 'Enter') {{
      e.preventDefault();
      runSelected();
    }} else if (e.key === 'ArrowDown') {{
      e.preventDefault();
      setActive(active + 1);
    }} else if (e.key === 'ArrowUp') {{
      e.preventDefault();
      setActive(active - 1);
    }}
  }}

  input.oninput = function () {{
    rebuildFiltered(input.value);
    render();
  }};

  runBtn.onclick = runSelected;
  cancelBtn.onclick = cleanup;
  closeBtn.onclick = cleanup;
  cancelBtn.onclick = cleanup;

  document.addEventListener('keydown', onKey, true);

  rebuildFiltered('');
  render();

  document.documentElement.appendChild(overlay);
  input.focus();
}})();"""



async def selector_payload() -> dict[str, str]:
    items = await list_items()
    source = build_selector_source(items)
    return {
        "javascript_source": source,
        "bookmarklet_url": f"javascript:{source}",
    }


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        response = await handler(request)

    allowed_origins = request.app["allowed_origins"]
    request_origin = request.headers.get("Origin")
    if "*" in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    elif request_origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = request_origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


async def index(_: web.Request) -> web.FileResponse:
    return web.FileResponse(INDEX_PATH)


async def api_get_bookmarklets(_: web.Request) -> web.Response:
    return web.json_response({"items": await list_items()})


async def api_create_bookmarklet(request: web.Request) -> web.Response:
    payload = await request.json()
    title = (payload.get("title") or "").strip()
    match_js = (payload.get("match_js") or "").strip()
    code_js = (payload.get("code_js") or "").strip()
    if not (title and match_js and code_js):
        return web.json_response({"error": "title, match_js, code_js are required"}, status=400)

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM bookmarklets") as cursor:
            row = await cursor.fetchone()
            position = int(row[0])
        cur = await db.execute(
            """
            INSERT INTO bookmarklets (title, match_js, code_js, position, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (title, match_js, code_js, position),
        )
        await db.commit()
    return web.json_response({"id": cur.lastrowid}, status=201)


async def api_update_bookmarklet(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    payload = await request.json()
    title = (payload.get("title") or "").strip()
    match_js = (payload.get("match_js") or "").strip()
    code_js = (payload.get("code_js") or "").strip()
    if not (title and match_js and code_js):
        return web.json_response({"error": "title, match_js, code_js are required"}, status=400)

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            UPDATE bookmarklets
            SET title = ?, match_js = ?, code_js = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, match_js, code_js, item_id),
        )
        await db.commit()
    if cur.rowcount == 0:
        return web.json_response({"error": "not found"}, status=404)
    return web.json_response({"ok": True})


async def api_delete_bookmarklet(request: web.Request) -> web.Response:
    item_id = request.match_info["item_id"]
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM bookmarklets WHERE id = ?", (item_id,))
        await db.commit()
    if cur.rowcount == 0:
        return web.json_response({"error": "not found"}, status=404)
    return web.json_response({"ok": True})


async def api_selector(_: web.Request) -> web.Response:
    payload = await selector_payload()
    return web.json_response(payload)


async def api_options(_: web.Request) -> web.Response:
    return web.Response(status=204)


def create_api_app(frontend_origin: str) -> web.Application:
    app = web.Application(middlewares=[cors_middleware])
    app["allowed_origins"] = {
        origin.strip() for origin in frontend_origin.split(",") if origin.strip()
    } or {"http://localhost:8081"}
    app.router.add_route("OPTIONS", "/api/{tail:.*}", api_options)
    app.router.add_get("/api/bookmarklets", api_get_bookmarklets)
    app.router.add_post("/api/bookmarklets", api_create_bookmarklet)
    app.router.add_put("/api/bookmarklets/{item_id}", api_update_bookmarklet)
    app.router.add_delete("/api/bookmarklets/{item_id}", api_delete_bookmarklet)
    app.router.add_get("/api/selector", api_selector)
    return app


def create_frontend_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_static("/frontend", FRONTEND_DIR)
    return app


async def run_servers(
    api_port: int,
    frontend_port: int,
    frontend_origin: str,
    serve_frontend: bool,
) -> None:
    await init_db()

    api_app = create_api_app(frontend_origin)

    api_runner = web.AppRunner(api_app)
    await api_runner.setup()

    api_site = web.TCPSite(api_runner, host="0.0.0.0", port=api_port)
    await api_site.start()

    frontend_runner = None
    if serve_frontend:
        frontend_app = create_frontend_app()
        frontend_runner = web.AppRunner(frontend_app)
        await frontend_runner.setup()
        frontend_site = web.TCPSite(frontend_runner, host="0.0.0.0", port=frontend_port)
        await frontend_site.start()

    print(f"API server running on http://localhost:{api_port}")
    if serve_frontend:
        print(f"Frontend server running on http://localhost:{frontend_port}")
    else:
        print("Frontend server disabled (--no-frontend)")

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await api_runner.cleanup()
        if frontend_runner is not None:
            await frontend_runner.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run bookmarklet selector manager")
    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_DB_PATH),
        help="SQLite database path (default: repository-root bookmarklets.db)",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8080,
        help="Port for API/bookmarklet server (default: 8080)",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=8081,
        help="Port for frontend server (default: 8081)",
    )
    parser.add_argument(
        "--frontend-origin",
        default="http://localhost:8081",
        help="Allowed frontend origin for CORS (default: http://localhost:8081)",
    )
    parser.add_argument(
        "--no-frontend",
        action="store_true",
        help="Disable serving frontend files and run API server only",
    )
    args = parser.parse_args()

    DB_PATH = Path(args.db_path).expanduser()

    asyncio.run(
        run_servers(
            args.api_port,
            args.frontend_port,
            args.frontend_origin,
            serve_frontend=not args.no_frontend,
        )
    )
