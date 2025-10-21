from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import admin_guard, get_db
from ..models import NFTGift
from ..telegram_client import telegram_client
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory=settings.templates_dir)
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(admin_guard)])


@router.get("/", response_class=HTMLResponse)
def admin_index(request: Request, db: Session = Depends(get_db)):
    gifts: List[NFTGift] = db.query(NFTGift).order_by(NFTGift.created_at.desc()).all()
    return templates.TemplateResponse("admin_list.html", {"request": request, "gifts": gifts})


@router.get("/new", response_class=HTMLResponse)
def admin_new(request: Request):
    return templates.TemplateResponse("admin_form.html", {"request": request, "gift": None})


@router.post("/new")
def admin_create(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    price_cents: int = Form(0),
    gif_url: Optional[str] = Form(None),
    telegram_file_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if not gif_url and not telegram_file_id:
        raise HTTPException(status_code=400, detail="Provide a GIF URL or Telegram file_id")
    gift = NFTGift(
        title=title.strip(),
        description=(description or "").strip(),
        price_cents=price_cents or 0,
        gif_url=(gif_url or None),
        telegram_file_id=(telegram_file_id or None),
    )
    db.add(gift)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/{gift_id}/edit", response_class=HTMLResponse)
def admin_edit(gift_id: int, request: Request, db: Session = Depends(get_db)):
    gift = db.query(NFTGift).filter(NFTGift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    return templates.TemplateResponse("admin_form.html", {"request": request, "gift": gift})


@router.post("/{gift_id}/edit")
def admin_update(
    gift_id: int,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    price_cents: int = Form(0),
    gif_url: Optional[str] = Form(None),
    telegram_file_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    gift = db.query(NFTGift).filter(NFTGift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    gift.title = title.strip()
    gift.description = (description or "").strip()
    gift.price_cents = price_cents or 0
    gift.gif_url = gif_url or None
    gift.telegram_file_id = telegram_file_id or None
    db.add(gift)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/{gift_id}/delete")
def admin_delete(gift_id: int, db: Session = Depends(get_db)):
    gift = db.query(NFTGift).filter(NFTGift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    db.delete(gift)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/telegram", response_class=HTMLResponse)
def admin_telegram(request: Request):
    # Render a page that fetches GIFs via JS from /api/telegram/gifs
    return templates.TemplateResponse("admin_telegram.html", {"request": request})
