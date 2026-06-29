"""Scanner module: 1C product/stock lookup, now behind authentication."""
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..config import settings
from ..deps import require_permission

router = APIRouter(
    prefix="/api/modules/scanner",
    tags=["module:scanner"],
    dependencies=[Depends(require_permission("module:scanner"))],
)


def _onec_auth_header() -> str:
    if settings.onec_auth:
        return settings.onec_auth
    if settings.onec_user and settings.onec_password:
        import base64

        creds = f"{settings.onec_user}:{settings.onec_password}".encode("utf-8")
        return "Basic " + base64.b64encode(creds).decode("utf-8")
    return ""


@router.get("/lookup")
async def lookup(barcode: str = Query(..., min_length=1)):
    headers = {"Content-Type": "application/json"}
    auth = _onec_auth_header()
    if auth:
        headers["Authorization"] = auth

    params = {"barcode": barcode}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(settings.onec_base_url, params=params, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Ошибка обращения к 1С: {exc}")

    if resp.status_code >= 400:
        raise HTTPException(resp.status_code, f"1С вернула ошибку: {resp.text[:200]}")

    try:
        return resp.json()
    except ValueError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "1С вернула некорректный JSON")
