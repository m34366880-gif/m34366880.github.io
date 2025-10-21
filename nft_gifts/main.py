"""
Главное приложение FastAPI для NFT Gift Shop
"""
import asyncio
import hashlib
import secrets
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import init_db, get_db, NFTGift, User, NFTPurchase, async_session_maker
from telegram_bot import nft_bot


# Lifespan context manager для запуска и остановки бота
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    await init_db()
    
    # Запускаем Telegram бота в отдельной задаче
    bot_task = asyncio.create_task(nft_bot.run())
    
    yield
    
    # Остановка
    if nft_bot.application:
        await nft_bot.application.updater.stop()
        await nft_bot.application.stop()
        await nft_bot.application.shutdown()
    
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass


# Создание приложения FastAPI
app = FastAPI(
    title="NFT Gift Shop",
    description="Магазин NFT подарков с интеграцией Telegram",
    version="1.0.0",
    lifespan=lifespan
)

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# === Middleware для проверки IP админа ===
def check_admin_ip(request: Request) -> bool:
    """Проверка IP адреса для доступа к админ-панели"""
    client_ip = request.client.host
    # В продакшене использовать X-Forwarded-For для получения реального IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    
    return client_ip == settings.ADMIN_IP or client_ip == "127.0.0.1"


# === Аутентификация для админ-панели ===
async def verify_admin_session(request: Request):
    """Проверка сессии администратора"""
    if not check_admin_ip(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен с вашего IP адреса"
        )
    
    session_token = request.cookies.get("admin_session")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    
    # Простая проверка сессии (в продакшене использовать Redis/DB)
    expected_token = hashlib.sha256(
        f"{settings.ADMIN_USERNAME}:{settings.ADMIN_PASSWORD}".encode()
    ).hexdigest()
    
    if session_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверная сессия"
        )
    
    return True


# === Публичные маршруты ===
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    """Главная страница с каталогом NFT подарков"""
    result = await db.execute(
        select(NFTGift).where(NFTGift.is_active == True).order_by(NFTGift.created_at.desc())
    )
    gifts = result.scalars().all()
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "gifts": gifts}
    )


@app.get("/gift/{gift_id}", response_class=HTMLResponse)
async def gift_detail(gift_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """Детальная страница NFT подарка"""
    result = await db.execute(
        select(NFTGift).where(NFTGift.id == gift_id)
    )
    gift = result.scalar_one_or_none()
    
    if not gift:
        raise HTTPException(status_code=404, detail="Подарок не найден")
    
    return templates.TemplateResponse(
        "gift_detail.html",
        {"request": request, "gift": gift}
    )


@app.get("/api/gifts", response_class=JSONResponse)
async def api_get_gifts(db: AsyncSession = Depends(get_db)):
    """API для получения списка подарков"""
    result = await db.execute(
        select(NFTGift).where(NFTGift.is_active == True).order_by(NFTGift.created_at.desc())
    )
    gifts = result.scalars().all()
    
    return [
        {
            "id": g.id,
            "title": g.title,
            "description": g.description,
            "gif_url": g.gif_url,
            "price": g.price
        }
        for g in gifts
    ]


# === Админ-панель ===
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Страница входа в админ-панель"""
    if not check_admin_ip(request):
        return templates.TemplateResponse(
            "access_denied.html",
            {"request": request, "message": "Доступ разрешен только с IP: " + settings.ADMIN_IP}
        )
    
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Обработка входа администратора"""
    if not check_admin_ip(request):
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        # Создаем токен сессии
        session_token = hashlib.sha256(f"{username}:{password}".encode()).hexdigest()
        
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(key="admin_session", value=session_token, httponly=True)
        return response
    
    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": "Неверные учетные данные"}
    )


@app.get("/admin/logout")
async def admin_logout():
    """Выход из админ-панели"""
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_session)
):
    """Главная страница админ-панели"""
    # Получаем статистику
    gifts_result = await db.execute(select(NFTGift))
    gifts = gifts_result.scalars().all()
    
    users_result = await db.execute(select(User))
    users_count = len(users_result.scalars().all())
    
    purchases_result = await db.execute(select(NFTPurchase))
    purchases = purchases_result.scalars().all()
    
    stats = {
        "total_gifts": len(gifts),
        "active_gifts": len([g for g in gifts if g.is_active]),
        "total_users": users_count,
        "total_purchases": len(purchases),
        "total_sent": len([p for p in purchases if p.status == "sent"])
    }
    
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "stats": stats}
    )


@app.get("/admin/gifts", response_class=HTMLResponse)
async def admin_gifts_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_session)
):
    """Список NFT подарков в админке"""
    result = await db.execute(
        select(NFTGift).order_by(desc(NFTGift.created_at))
    )
    gifts = result.scalars().all()
    
    return templates.TemplateResponse(
        "admin_gifts.html",
        {"request": request, "gifts": gifts}
    )


@app.get("/admin/gifts/add", response_class=HTMLResponse)
async def admin_add_gift_page(
    request: Request,
    _: bool = Depends(verify_admin_session)
):
    """Страница добавления NFT подарка"""
    return templates.TemplateResponse("admin_add_gift.html", {"request": request})


@app.post("/admin/gifts/add")
async def admin_add_gift(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    gif_url: str = Form(...),
    price: float = Form(default=0.0),
    file_id: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_session)
):
    """Добавление нового NFT подарка"""
    new_gift = NFTGift(
        title=title,
        description=description,
        gif_url=gif_url,
        file_id=file_id,
        price=price,
        is_active=True
    )
    
    db.add(new_gift)
    await db.commit()
    await db.refresh(new_gift)
    
    return RedirectResponse(url="/admin/gifts", status_code=302)


@app.get("/admin/gifts/edit/{gift_id}", response_class=HTMLResponse)
async def admin_edit_gift_page(
    gift_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_session)
):
    """Страница редактирования NFT подарка"""
    result = await db.execute(select(NFTGift).where(NFTGift.id == gift_id))
    gift = result.scalar_one_or_none()
    
    if not gift:
        raise HTTPException(status_code=404, detail="Подарок не найден")
    
    return templates.TemplateResponse(
        "admin_edit_gift.html",
        {"request": request, "gift": gift}
    )


@app.post("/admin/gifts/edit/{gift_id}")
async def admin_edit_gift(
    gift_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    gif_url: str = Form(...),
    price: float = Form(...),
    file_id: Optional[str] = Form(default=None),
    is_active: bool = Form(default=False),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_session)
):
    """Обновление NFT подарка"""
    result = await db.execute(select(NFTGift).where(NFTGift.id == gift_id))
    gift = result.scalar_one_or_none()
    
    if not gift:
        raise HTTPException(status_code=404, detail="Подарок не найден")
    
    gift.title = title
    gift.description = description
    gift.gif_url = gif_url
    gift.file_id = file_id
    gift.price = price
    gift.is_active = is_active
    gift.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return RedirectResponse(url="/admin/gifts", status_code=302)


@app.post("/admin/gifts/delete/{gift_id}")
async def admin_delete_gift(
    gift_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_session)
):
    """Удаление NFT подарка"""
    result = await db.execute(select(NFTGift).where(NFTGift.id == gift_id))
    gift = result.scalar_one_or_none()
    
    if not gift:
        raise HTTPException(status_code=404, detail="Подарок не найден")
    
    await db.delete(gift)
    await db.commit()
    
    return RedirectResponse(url="/admin/gifts", status_code=302)


@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_session)
):
    """Список пользователей"""
    result = await db.execute(select(User).order_by(desc(User.created_at)))
    users = result.scalars().all()
    
    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "users": users}
    )


@app.get("/admin/purchases", response_class=HTMLResponse)
async def admin_purchases_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_session)
):
    """Список покупок/передач"""
    result = await db.execute(
        select(NFTPurchase).order_by(desc(NFTPurchase.created_at))
    )
    purchases = result.scalars().all()
    
    # Получаем дополнительные данные для каждой покупки
    purchase_data = []
    for purchase in purchases:
        user_result = await db.execute(select(User).where(User.id == purchase.user_id))
        user = user_result.scalar_one_or_none()
        
        gift_result = await db.execute(select(NFTGift).where(NFTGift.id == purchase.nft_gift_id))
        gift = gift_result.scalar_one_or_none()
        
        purchase_data.append({
            "purchase": purchase,
            "user": user,
            "gift": gift
        })
    
    return templates.TemplateResponse(
        "admin_purchases.html",
        {"request": request, "purchases": purchase_data}
    )


# === Обработчики ошибок ===
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Обработчик 404 ошибки"""
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    """Обработчик 403 ошибки"""
    return templates.TemplateResponse(
        "access_denied.html",
        {"request": request, "message": "Доступ запрещен"},
        status_code=403
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
