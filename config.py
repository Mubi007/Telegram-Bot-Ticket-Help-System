import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ID администраторов (замени на реальные ID)
ADMINS = [5445415064]  # Добавь сюда ID админов

# ID агентов поддержки (замени на реальные ID)  
AGENTS = [790972448]  # Добавь сюда ID агентов

# Функция для проверки админа (обратная совместимость)
def is_admin(user_id: int) -> bool:
    """Проверить является ли пользователь админом по статическому списку"""
    return user_id in ADMINS

# Функция для проверки агента (обратная совместимость)
def is_agent(user_id: int) -> bool:
    """Проверить является ли пользователь агентом по статическому списку"""
    return user_id in AGENTS

# Роли пользователей
USER_ROLES = {
    'client': 'Клиент',
    'agent': 'Агент поддержки', 
    'admin': 'Администратор'
}

# База данных
DATABASE_PATH = 'data/support.db'

# Настройки
MAX_TICKET_TEXT_LENGTH = 1000
TICKETS_PER_PAGE = 5