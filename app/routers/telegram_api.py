from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from ..telegram_client import telegram_client


router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.get("/gifs")
def list_gifs():
    try:
        data = telegram_client.get_updates(limit=100)
        gifs = telegram_client.extract_gif_animations(data)
        return JSONResponse(content={"ok": True, "gifs": gifs})
    except Exception as ex:
        return JSONResponse(content={"ok": False, "error": str(ex)}, status_code=500)


@router.get("/file/{file_id}")
def proxy_file(file_id: str):
    try:
        resp = telegram_client.download_file_stream(file_id)
        # Try to preserve Telegram content type; default to video/mp4 for animations
        content_type = resp.headers.get("Content-Type", "video/mp4")
        return StreamingResponse(resp.iter_content(chunk_size=8192), media_type=content_type)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
