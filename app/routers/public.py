from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import Base, engine
from ..deps import get_db
from ..models import NFTGift, Purchase
from ..telegram_client import telegram_client
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory=settings.templates_dir)
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    gifts: List[NFTGift] = db.query(NFTGift).order_by(NFTGift.created_at.desc()).all()
    success = request.query_params.get("success")
    error = request.query_params.get("error")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "gifts": gifts, "title": settings.app_title, "success": success, "error": error},
    )


@router.post("/purchase/{gift_id}")
def purchase_gift(
    gift_id: int,
    request: Request,
    recipient_chat_id: str = Form(..., description="Telegram chat id or @username"),
    message: Optional[str] = Form(None),
    buyer_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    gift: Optional[NFTGift] = db.query(NFTGift).filter(NFTGift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift not found")

    caption = message or f"You've received a NFT Gift: {gift.title}!"

    # Prefer Telegram file_id if available, else direct gif URL (Telegram supports URLs)
    animation_ref = gift.telegram_file_id or gift.gif_url
    if not animation_ref:
        return RedirectResponse(url=f"/?error=missing_animation", status_code=303)

    try:
        telegram_client.send_animation(chat_id=recipient_chat_id, animation=animation_ref, caption=caption)
        purchase = Purchase(
            gift_id=gift.id,
            buyer_name=buyer_name,
            recipient_chat_id=recipient_chat_id,
            message=message,
            status="sent",
        )
        db.add(purchase)
        db.commit()
        return RedirectResponse(url=f"/?success=1", status_code=303)
    except Exception:
        return RedirectResponse(url=f"/?error=send_failed", status_code=303)
