"""
Скрипт для добавления демонстрационных NFT подарков
"""
import asyncio
from database import init_db, async_session_maker, NFTGift


async def add_demo_gifts():
    """Добавление демо-подарков в базу данных"""
    print("🎁 Добавление демонстрационных NFT подарков...")
    
    # Инициализация базы данных
    await init_db()
    
    demo_gifts = [
        {
            "title": "🎆 Праздничный фейерверк",
            "description": "Красочный анимированный фейерверк для особых случаев. Яркие цвета и впечатляющая анимация создадут праздничное настроение!",
            "gif_url": "https://media.giphy.com/media/26tOZ42Mg6pbTUPHW/giphy.gif",
            "price": 5.0
        },
        {
            "title": "💝 Романтическое сердце",
            "description": "Пульсирующее сердце с романтичной анимацией. Идеальный подарок для выражения своих чувств.",
            "gif_url": "https://media.giphy.com/media/3o6Zt6KHxJTbXCnSvu/giphy.gif",
            "price": 3.5
        },
        {
            "title": "🌟 Звездная пыль",
            "description": "Магическая звездная пыль с мерцающим эффектом. Подарите немного волшебства!",
            "gif_url": "https://media.giphy.com/media/l0HlMPcbD4jdARjRC/giphy.gif",
            "price": 4.0
        },
        {
            "title": "🎉 Конфетти",
            "description": "Взрыв красочного конфетти для празднования успеха и радостных моментов.",
            "gif_url": "https://media.giphy.com/media/g5R9dok94mrIvplmZd/giphy.gif",
            "price": 2.5
        },
        {
            "title": "🦄 Волшебный единорог",
            "description": "Милый анимированный единорог с радужной гривой. Магия и позитив в одном подарке!",
            "gif_url": "https://media.giphy.com/media/3o7TKP50aGZLAFfHna/giphy.gif",
            "price": 6.0
        },
        {
            "title": "💎 Бриллиант",
            "description": "Сверкающий бриллиант с переливающимися гранями. Символ роскоши и ценности.",
            "gif_url": "https://media.giphy.com/media/lOaf3FHMTVDbO2gLxC/giphy.gif",
            "price": 10.0
        },
        {
            "title": "🌈 Радуга счастья",
            "description": "Яркая радуга с плавной анимацией. Принесите радость и позитив своим друзьям!",
            "gif_url": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
            "price": 3.0
        },
        {
            "title": "🎂 Праздничный торт",
            "description": "Анимированный именинный торт со свечами. Идеально для поздравлений с днем рождения!",
            "gif_url": "https://media.giphy.com/media/5fHY45L9XLzcQ/giphy.gif",
            "price": 4.5
        },
        {
            "title": "🚀 Космическая ракета",
            "description": "Стартующая ракета для мечтателей и покорителей космоса. К звездам!",
            "gif_url": "https://media.giphy.com/media/3og0ItPt8xBuIq8Agg/giphy.gif",
            "price": 5.5
        },
        {
            "title": "🎨 Абстрактное искусство",
            "description": "Гипнотизирующая абстракция с плавными переходами цветов. Для ценителей современного искусства.",
            "gif_url": "https://media.giphy.com/media/xT8qBgvOUl9mj2fe6c/giphy.gif",
            "price": 7.0
        }
    ]
    
    async with async_session_maker() as session:
        for gift_data in demo_gifts:
            gift = NFTGift(
                title=gift_data["title"],
                description=gift_data["description"],
                gif_url=gift_data["gif_url"],
                price=gift_data["price"],
                is_active=True
            )
            session.add(gift)
        
        await session.commit()
    
    print(f"✅ Добавлено {len(demo_gifts)} демонстрационных подарков!")
    print("\n📋 Список добавленных подарков:")
    for i, gift in enumerate(demo_gifts, 1):
        print(f"{i}. {gift['title']} - {gift['price']} TON")


if __name__ == "__main__":
    asyncio.run(add_demo_gifts())
