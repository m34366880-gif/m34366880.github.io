"""
База данных и модели для NFT подарков
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from config import settings


class Base(DeclarativeBase):
    """Базовый класс для моделей"""
    pass


class NFTGift(Base):
    """Модель NFT подарка"""
    __tablename__ = "nft_gifts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    gif_url = Column(String(500), nullable=False)
    file_id = Column(String(255))  # Telegram file_id для GIF
    price = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с покупками
    purchases = relationship("NFTPurchase", back_populates="nft_gift")


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с покупками
    purchases = relationship("NFTPurchase", back_populates="user")
    received_gifts = relationship("NFTPurchase", 
                                   foreign_keys="NFTPurchase.recipient_telegram_id",
                                   back_populates="recipient")


class NFTPurchase(Base):
    """Модель покупки/передачи NFT подарка"""
    __tablename__ = "nft_purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nft_gift_id = Column(Integer, ForeignKey("nft_gifts.id"), nullable=False)
    recipient_telegram_id = Column(Integer, ForeignKey("users.telegram_id"))
    
    status = Column(String(50), default="pending")  # pending, completed, sent
    transaction_hash = Column(String(255))  # Для имитации blockchain
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    
    # Связи
    user = relationship("User", back_populates="purchases", foreign_keys=[user_id])
    nft_gift = relationship("NFTGift", back_populates="purchases")
    recipient = relationship("User", back_populates="received_gifts", 
                            foreign_keys=[recipient_telegram_id])


# Создание движка базы данных
engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Получение сессии базы данных"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
