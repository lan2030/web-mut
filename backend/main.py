"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import PROJECT_DIR
from .routers import admin_roles, admin_users, auth, scanner
from .seed import init_db

DIST_DIR = PROJECT_DIR / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="OmniScan Platform", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(admin_users.router)
app.include_router(admin_roles.router)
app.include_router(scanner.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- Serve the built SPA (production) --------------------------------------
# In dev the Vite server runs separately and proxies /api to this backend.
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        # Never let the SPA fallback shadow the API.
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")
