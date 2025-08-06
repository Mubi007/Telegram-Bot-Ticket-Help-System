"""Reply клавиатуры для удобного управления"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# УБРАЛИ СЛОЖНУЮ ЛОГИКУ - упростили интерфейсы


def get_client_main_keyboard(show_admin_return: bool = False, show_agent_return: bool = False) -> ReplyKeyboardMarkup:
    """Основная клавиатура для клиентов"""
    keyboard = ReplyKeyboardBuilder()
    
    # Первый ряд - основные функции
    keyboard.row(
        KeyboardButton(text="📝 Создать обращение"),
        KeyboardButton(text="📋 Мои обращения")
    )
    
    # Второй ряд - справочная информация
    keyboard.row(
        KeyboardButton(text="❓ FAQ"),
        KeyboardButton(text="📞 Контакты")
    )
    
    # Третий ряд - основные функции (БЕЗ переключения режимов)
    keyboard.row(
        KeyboardButton(text="🔄 Обновить"),
        KeyboardButton(text="ℹ️ Помощь")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие или напишите сообщение..."
    )


def get_agent_main_keyboard(show_admin_return: bool = False) -> ReplyKeyboardMarkup:
    """Упрощённая клавиатура для агентов поддержки"""
    keyboard = ReplyKeyboardBuilder()
    
    # Первый ряд - основные функции (убрали дублирование с inline)
    keyboard.row(
        KeyboardButton(text="🔄 Обновить"),
        KeyboardButton(text="ℹ️ Помощь")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Все функции доступны в меню выше ↑"
    )


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура для администраторов"""
    keyboard = ReplyKeyboardBuilder()
    
    # Первый ряд - управление обращениями
    keyboard.row(
        KeyboardButton(text="🆕 Новые"),
        KeyboardButton(text="⏳ Активные"),
        KeyboardButton(text="📊 Статистика")
    )
    
    # Второй ряд - управление системой
    keyboard.row(
        KeyboardButton(text="👥 Пользователи"),
        KeyboardButton(text="🔍 Поиск"),
        KeyboardButton(text="⚙️ Настройки")
    )
    
    # Третий ряд - основные функции (БЕЗ переключения режимов)
    keyboard.row(
        KeyboardButton(text="🔄 Обновить"),
        KeyboardButton(text="ℹ️ Помощь")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Администрирование..."
    )


def get_ticket_categories_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора категории обращения"""
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.row(
        KeyboardButton(text="🔧 Техподдержка"),
        KeyboardButton(text="💳 Оплата")
    )
    keyboard.row(
        KeyboardButton(text="👤 Аккаунт"),
        KeyboardButton(text="💬 Общие вопросы")
    )
    keyboard.row(
        KeyboardButton(text="😡 Жалоба"),
        KeyboardButton(text="💡 Предложение")
    )
    keyboard.row(
        KeyboardButton(text="❌ Отмена")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите категорию обращения..."
    )


def get_agent_actions_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура действий агента с обращением"""
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.row(
        KeyboardButton(text="💬 Ответить"),
        KeyboardButton(text="🔄 Взять в работу")
    )
    keyboard.row(
        KeyboardButton(text="✅ Решить"),
        KeyboardButton(text="⏰ Ожидает ответа")
    )
    keyboard.row(
        KeyboardButton(text="📋 К обращениям"),
        KeyboardButton(text="🏠 Главное меню")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие с обращением..."
    )


def get_admin_user_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления пользователями для админа"""
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.row(
        KeyboardButton(text="👥 Список пользователей"),
        KeyboardButton(text="👨‍💼 Список агентов")
    )
    keyboard.row(
        KeyboardButton(text="➕ Добавить агента"),
        KeyboardButton(text="➖ Удалить агента")
    )
    keyboard.row(
        KeyboardButton(text="🔍 Найти пользователя"),
        KeyboardButton(text="📊 Статистика ролей")
    )
    keyboard.row(
        KeyboardButton(text="🏠 Главное меню")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Управление пользователями..."
    )


def get_priority_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора приоритета"""
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.row(
        KeyboardButton(text="🔴 Высокий"),
        KeyboardButton(text="🟡 Средний"),
        KeyboardButton(text="🟢 Низкий")
    )
    keyboard.row(
        KeyboardButton(text="❌ Отмена")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите приоритет..."
    )


def get_quick_responses_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура быстрых ответов"""
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.row(
        KeyboardButton(text="✅ Решено"),
        KeyboardButton(text="⏳ В работе")
    )
    keyboard.row(
        KeyboardButton(text="❓ Нужна информация"),
        KeyboardButton(text="📋 Переадресовано")
    )
    keyboard.row(
        KeyboardButton(text="✏️ Свой ответ"),
        KeyboardButton(text="❌ Отмена")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите быстрый ответ или напишите свой..."
    )


def get_search_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для поиска"""
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.row(
        KeyboardButton(text="🔢 По номеру"),
        KeyboardButton(text="👤 По пользователю")
    )
    keyboard.row(
        KeyboardButton(text="📝 По тексту"),
        KeyboardButton(text="📅 По дате")
    )
    keyboard.row(
        KeyboardButton(text="❌ Отмена")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите тип поиска..."
    )


def get_confirmation_keyboard(action_text: str = "действие") -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.row(
        KeyboardButton(text="✅ Подтвердить"),
        KeyboardButton(text="❌ Отмена")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=f"Подтвердите {action_text}..."
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура только с кнопкой отмены"""
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.row(
        KeyboardButton(text="❌ Отмена")
    )
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Напишите сообщение или отмените..."
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Удаление клавиатуры"""
    return ReplyKeyboardRemove()


def get_role_switch_keyboard(current_role: str) -> ReplyKeyboardMarkup:
    """Клавиатура переключения ролей"""
    keyboard = ReplyKeyboardBuilder()
    
    if current_role != 'client':
        keyboard.row(KeyboardButton(text="👤 Режим клиента"))
    
    if current_role == 'admin':
        keyboard.row(KeyboardButton(text="👨‍💼 Режим агента"))
    
    if current_role in ['client', 'agent']:
        keyboard.row(KeyboardButton(text="🏠 Главное меню"))
    else:
        keyboard.row(KeyboardButton(text="⚙️ Админ панель"))
    
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите режим работы..."
    )