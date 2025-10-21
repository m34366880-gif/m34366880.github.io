from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class NFTGift(Base):
    __tablename__ = "nft_gifts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    # Either a direct GIF URL or Telegram file_id (for animation)
    gif_url = Column(String(1000), nullable=True)
    telegram_file_id = Column(String(255), nullable=True)
    price_cents = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    purchases = relationship("Purchase", back_populates="gift", cascade="all, delete-orphan")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    gift_id = Column(Integer, ForeignKey("nft_gifts.id", ondelete="CASCADE"), nullable=False)
    buyer_name = Column(String(200), nullable=True)
    recipient_chat_id = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    status = Column(String(50), default="sent", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    gift = relationship("NFTGift", back_populates="purchases")
