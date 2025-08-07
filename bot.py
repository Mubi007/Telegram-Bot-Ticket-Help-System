"""
Современный бот поддержки клиентов в Telegram
Основан на aiogram 3 с продуманной архитектурой и удобным интерфейсом
"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import db
from handlers import common, user, admin, agent, admin_callbacks


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()


async def on_startup():
    logger.info("🚀 Запуск бота поддержки...")
    
    # Создаем таблицы в базе данных
    await db.create_tables()
    logger.info("✅ База данных инициализирована")
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"✅ Бот запущен: @{bot_info.username}")
    
    # Уведомляем администраторов о запуске
    from config import ADMINS
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                admin_id,
                "🚀 <b>Бот поддержки запущен!</b>\n\n"
                "Добро пожаловать в тикет систему",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Не удалось уведомить админа {admin_id}: {e}")


async def on_shutdown():
    logger.info("🛑 Завершение работы бота...")
    
    # Уведомляем администраторов о завершении работы
    from config import ADMINS
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                admin_id,
                "🛑 <b>Бот поддержки остановлен</b>\n\n"
                "Система временно недоступна.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Не удалось уведомить админа {admin_id}: {e}")


async def main():
    """Главная функция"""
    try:
        # Регистрируем роутеры (порядок важен!)
        dp.include_router(user.router)
        dp.include_router(agent.router)
        dp.include_router(admin.router)
        dp.include_router(admin_callbacks.router)
        dp.include_router(common.router)  # Последним, так как содержит общий обработчик
        
        # Запускаем бота
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        logger.info("🔄 Начинаем polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал завершения, останавливаем бота...")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)
