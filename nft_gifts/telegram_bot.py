"""
Telegram бот для отправки NFT подарков
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import async_session_maker, User, NFTGift, NFTPurchase
import hashlib
import time

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class NFTGiftBot:
    """Класс для управления Telegram ботом NFT подарков"""
    
    def __init__(self):
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Сохраняем пользователя в БД
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == user.id)
            )
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                db_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                session.add(db_user)
                await session.commit()
        
        keyboard = [
            [InlineKeyboardButton("🎁 Просмотреть подарки", callback_data="view_gifts")],
            [InlineKeyboardButton("📦 Мои подарки", callback_data="my_gifts")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            "🎁 Добро пожаловать в NFT Gift Shop!\n\n"
            "Здесь вы можете:\n"
            "• Просматривать коллекцию NFT подарков\n"
            "• Покупать анимированные NFT\n"
            "• Отправлять подарки друзьям в Telegram\n\n"
            "Выберите действие:"
        )
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def view_gifts_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать доступные NFT подарки"""
        query = update.callback_query
        await query.answer()
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(NFTGift).where(NFTGift.is_active == True).order_by(NFTGift.id)
            )
            gifts = result.scalars().all()
        
        if not gifts:
            await query.edit_message_text(
                "😔 К сожалению, сейчас нет доступных подарков.\n"
                "Попробуйте позже!"
            )
            return
        
        # Показываем первый подарок
        context.user_data['current_gift_index'] = 0
        context.user_data['gifts'] = [g.id for g in gifts]
        await self.show_gift(query, context, gifts[0])
    
    async def show_gift(self, query, context: ContextTypes.DEFAULT_TYPE, gift: NFTGift):
        """Показать конкретный NFT подарок"""
        gift_text = (
            f"🎁 <b>{gift.title}</b>\n\n"
            f"{gift.description}\n\n"
            f"💰 Цена: {gift.price} TON\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("💳 Купить", callback_data=f"buy_{gift.id}")],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data="prev_gift"),
                InlineKeyboardButton("➡️ Далее", callback_data="next_gift")
            ],
            [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            # Отправляем GIF
            if gift.file_id:
                await query.message.reply_animation(
                    animation=gift.file_id,
                    caption=gift_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.message.reply_animation(
                    animation=gift.gif_url,
                    caption=gift_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            # Удаляем старое сообщение
            await query.message.delete()
        except Exception as e:
            logger.error(f"Ошибка отправки GIF: {e}")
            await query.edit_message_text(gift_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def navigate_gifts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Навигация по подаркам"""
        query = update.callback_query
        await query.answer()
        
        direction = query.data
        current_index = context.user_data.get('current_gift_index', 0)
        gift_ids = context.user_data.get('gifts', [])
        
        if not gift_ids:
            await query.edit_message_text("Нет доступных подарков")
            return
        
        if direction == "next_gift":
            current_index = (current_index + 1) % len(gift_ids)
        elif direction == "prev_gift":
            current_index = (current_index - 1) % len(gift_ids)
        
        context.user_data['current_gift_index'] = current_index
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(NFTGift).where(NFTGift.id == gift_ids[current_index])
            )
            gift = result.scalar_one_or_none()
        
        if gift:
            await self.show_gift(query, context, gift)
    
    async def buy_gift(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Покупка NFT подарка"""
        query = update.callback_query
        await query.answer()
        
        gift_id = int(query.data.split("_")[1])
        user = query.from_user
        
        async with async_session_maker() as session:
            # Получаем подарок
            result = await session.execute(
                select(NFTGift).where(NFTGift.id == gift_id)
            )
            gift = result.scalar_one_or_none()
            
            if not gift:
                await query.edit_message_text("❌ Подарок не найден")
                return
            
            # Получаем пользователя
            result = await session.execute(
                select(User).where(User.telegram_id == user.id)
            )
            db_user = result.scalar_one_or_none()
            
            # Создаем покупку
            purchase = NFTPurchase(
                user_id=db_user.id,
                nft_gift_id=gift.id,
                status="completed",
                transaction_hash=self.generate_transaction_hash(user.id, gift.id)
            )
            session.add(purchase)
            await session.commit()
        
        keyboard = [
            [InlineKeyboardButton("🎁 Отправить подарок", callback_data=f"send_{purchase.id}")],
            [InlineKeyboardButton("📦 Мои подарки", callback_data="my_gifts")],
            [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        success_text = (
            f"✅ Поздравляем!\n\n"
            f"Вы успешно приобрели NFT подарок:\n"
            f"🎁 <b>{gift.title}</b>\n\n"
            f"💰 Цена: {gift.price} TON\n"
            f"🔗 Transaction: <code>{purchase.transaction_hash[:16]}...</code>\n\n"
            f"Теперь вы можете отправить его другу!"
        )
        
        await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def my_gifts_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать подарки пользователя"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == user.id)
            )
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                await query.edit_message_text("❌ Пользователь не найден")
                return
            
            # Получаем покупки пользователя
            result = await session.execute(
                select(NFTPurchase).where(
                    NFTPurchase.user_id == db_user.id,
                    NFTPurchase.status != "sent"
                ).order_by(NFTPurchase.created_at.desc())
            )
            purchases = result.scalars().all()
            
            # Получаем полученные подарки
            result = await session.execute(
                select(NFTPurchase).where(
                    NFTPurchase.recipient_telegram_id == user.id,
                    NFTPurchase.status == "sent"
                ).order_by(NFTPurchase.sent_at.desc())
            )
            received = result.scalars().all()
        
        text = f"📦 <b>Ваши NFT подарки</b>\n\n"
        
        if purchases:
            text += "🛍️ <b>Купленные:</b>\n"
            for p in purchases:
                async with async_session_maker() as session:
                    result = await session.execute(
                        select(NFTGift).where(NFTGift.id == p.nft_gift_id)
                    )
                    gift = result.scalar_one_or_none()
                    if gift:
                        text += f"• {gift.title}\n"
        else:
            text += "У вас пока нет купленных подарков\n\n"
        
        if received:
            text += "\n🎁 <b>Полученные:</b>\n"
            for p in received:
                async with async_session_maker() as session:
                    result = await session.execute(
                        select(NFTGift).where(NFTGift.id == p.nft_gift_id)
                    )
                    gift = result.scalar_one_or_none()
                    if gift:
                        text += f"• {gift.title}\n"
        
        keyboard = [[InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def send_gift_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс отправки подарка"""
        query = update.callback_query
        await query.answer()
        
        purchase_id = int(query.data.split("_")[1])
        context.user_data['sending_purchase_id'] = purchase_id
        
        await query.edit_message_text(
            "🎁 Чтобы отправить подарок, перешлите мне любое сообщение от получателя\n"
            "или отправьте его @username"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        if 'sending_purchase_id' in context.user_data:
            # Обрабатываем отправку подарка
            await self.process_gift_sending(update, context)
    
    async def process_gift_sending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка отправки подарка"""
        purchase_id = context.user_data.get('sending_purchase_id')
        
        # Определяем получателя
        recipient_id = None
        if update.message.forward_from:
            recipient_id = update.message.forward_from.id
        elif update.message.text and update.message.text.startswith('@'):
            # Здесь нужна логика поиска по username
            await update.message.reply_text("❌ Отправка по username пока не поддерживается. Перешлите сообщение от пользователя.")
            return
        else:
            await update.message.reply_text("❌ Не удалось определить получателя")
            return
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(NFTPurchase).where(NFTPurchase.id == purchase_id)
            )
            purchase = result.scalar_one_or_none()
            
            if not purchase:
                await update.message.reply_text("❌ Подарок не найден")
                return
            
            # Обновляем покупку
            purchase.recipient_telegram_id = recipient_id
            purchase.status = "sent"
            purchase.sent_at = datetime.utcnow()
            await session.commit()
            
            # Получаем данные подарка
            result = await session.execute(
                select(NFTGift).where(NFTGift.id == purchase.nft_gift_id)
            )
            gift = result.scalar_one_or_none()
        
        # Отправляем подарок получателю
        try:
            gift_message = (
                f"🎁 <b>Вы получили NFT подарок!</b>\n\n"
                f"От: {update.effective_user.first_name}\n"
                f"Подарок: <b>{gift.title}</b>\n"
                f"🔗 TX: <code>{purchase.transaction_hash[:16]}...</code>"
            )
            
            if gift.file_id:
                await context.bot.send_animation(
                    chat_id=recipient_id,
                    animation=gift.file_id,
                    caption=gift_message,
                    parse_mode='HTML'
                )
            else:
                await context.bot.send_animation(
                    chat_id=recipient_id,
                    animation=gift.gif_url,
                    caption=gift_message,
                    parse_mode='HTML'
                )
            
            await update.message.reply_text(
                f"✅ Подарок успешно отправлен!\n"
                f"🎁 {gift.title}"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки подарка: {e}")
            await update.message.reply_text(
                "❌ Не удалось отправить подарок. "
                "Возможно, получатель не начал общение с ботом."
            )
        
        # Очищаем состояние
        del context.user_data['sending_purchase_id']
    
    async def help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Помощь"""
        query = update.callback_query
        await query.answer()
        
        help_text = (
            "❓ <b>Помощь</b>\n\n"
            "<b>Как использовать бота:</b>\n\n"
            "1️⃣ Просмотрите каталог NFT подарков\n"
            "2️⃣ Выберите понравившийся подарок\n"
            "3️⃣ Купите его (оплата через TON)\n"
            "4️⃣ Отправьте другу в Telegram\n\n"
            "<b>Команды:</b>\n"
            "/start - Главное меню\n"
            "/gifts - Каталог подарков\n"
            "/my - Мои подарки\n\n"
            "По вопросам: @support"
        )
        
        keyboard = [[InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возврат в главное меню"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🎁 Просмотреть подарки", callback_data="view_gifts")],
            [InlineKeyboardButton("📦 Мои подарки", callback_data="my_gifts")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏠 <b>Главное меню</b>\n\nВыберите действие:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    def generate_transaction_hash(self, user_id: int, gift_id: int) -> str:
        """Генерация хеша транзакции (имитация blockchain)"""
        data = f"{user_id}_{gift_id}_{time.time()}".encode()
        return hashlib.sha256(data).hexdigest()
    
    async def run(self):
        """Запуск бота"""
        self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        
        # Регистрация обработчиков
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.view_gifts_callback, pattern="^view_gifts$"))
        self.application.add_handler(CallbackQueryHandler(self.my_gifts_callback, pattern="^my_gifts$"))
        self.application.add_handler(CallbackQueryHandler(self.help_callback, pattern="^help$"))
        self.application.add_handler(CallbackQueryHandler(self.main_menu_callback, pattern="^main_menu$"))
        self.application.add_handler(CallbackQueryHandler(self.navigate_gifts, pattern="^(next_gift|prev_gift)$"))
        self.application.add_handler(CallbackQueryHandler(self.buy_gift, pattern="^buy_"))
        self.application.add_handler(CallbackQueryHandler(self.send_gift_callback, pattern="^send_"))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Запуск бота
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("NFT Gift Bot запущен")


# Глобальный экземпляр бота
nft_bot = NFTGiftBot()
