"""Клавиатуры для пользователей"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Any
from utils.texts import TICKET_CATEGORIES, TICKET_STATUSES, FAQ_ITEMS


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню пользователя"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📝 Создать обращение", callback_data="new_ticket")
    )
    keyboard.row(
        InlineKeyboardButton(text="📋 Мои обращения", callback_data="my_tickets"),
        InlineKeyboardButton(text="❓ FAQ", callback_data="faq")
    )
    keyboard.row(
        InlineKeyboardButton(text="📞 Контакты", callback_data="contacts"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")
    )
    
    return keyboard.as_markup()


def get_ticket_categories() -> InlineKeyboardMarkup:
    """Клавиатура выбора категории обращения"""
    keyboard = InlineKeyboardBuilder()
    
    for category_id, category_name in TICKET_CATEGORIES.items():
        keyboard.row(
            InlineKeyboardButton(
                text=category_name, 
                callback_data=f"category_{category_id}"
            )
        )
    
    keyboard.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    
    return keyboard.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return keyboard.as_markup()


def get_my_tickets_keyboard(tickets: List[Dict[str, Any]], page: int = 0, 
                           total_pages: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра обращений пользователя"""
    keyboard = InlineKeyboardBuilder()
    
    # Кнопки обращений
    for ticket in tickets:
        status_emoji = "🆕" if ticket['status'] == 'new' else "⏳" if ticket['status'] == 'in_progress' else "✅"
        button_text = f"{status_emoji} #{ticket['id']} - {ticket['subject'][:30]}..."
        keyboard.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"ticket_{ticket['id']}"
            )
        )
    
    # Навигация по страницам
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"tickets_page_{page-1}")
            )
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton(text="Вперед ➡️", callback_data=f"tickets_page_{page+1}")
            )
        if nav_buttons:
            keyboard.row(*nav_buttons)
    
    # Основные кнопки
    keyboard.row(
        InlineKeyboardButton(text="📝 Новое обращение", callback_data="new_ticket")
    )
    keyboard.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return keyboard.as_markup()


def get_ticket_details_keyboard(ticket_id: int, status: str, 
                               user_can_respond: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра обращения"""
    keyboard = InlineKeyboardBuilder()
    
    # Кнопка для ответа в обращении (если статус позволяет)
    if user_can_respond and status in ['new', 'in_progress', 'waiting_response']:
        keyboard.row(
            InlineKeyboardButton(
                text="💬 Добавить сообщение", 
                callback_data=f"respond_ticket_{ticket_id}"
            )
        )
    
    # Кнопка для закрытия обращения (если решено)
    if status == 'resolved':
        keyboard.row(
            InlineKeyboardButton(
                text="✅ Закрыть обращение", 
                callback_data=f"close_ticket_{ticket_id}"
            )
        )
    
    keyboard.row(
        InlineKeyboardButton(text="📋 Мои обращения", callback_data="my_tickets"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return keyboard.as_markup()


def get_faq_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура FAQ"""
    keyboard = InlineKeyboardBuilder()
    
    for faq_id, faq_data in FAQ_ITEMS.items():
        keyboard.row(
            InlineKeyboardButton(
                text=faq_data['question'],
                callback_data=f"faq_{faq_id}"
            )
        )
    
    keyboard.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return keyboard.as_markup()


def get_faq_item_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отдельного FAQ элемента"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="❓ Все вопросы", callback_data="faq"),
        InlineKeyboardButton(text="📝 Создать обращение", callback_data="new_ticket")
    )
    keyboard.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return keyboard.as_markup()


def get_contacts_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для страницы контактов"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📝 Создать обращение", callback_data="new_ticket")
    )
    keyboard.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return keyboard.as_markup()


def get_ticket_created_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """Клавиатура после создания обращения"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(
            text="👁️ Посмотреть обращение", 
            callback_data=f"ticket_{ticket_id}"
        )
    )
    keyboard.row(
        InlineKeyboardButton(text="📋 Мои обращения", callback_data="my_tickets"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return keyboard.as_markup()


def get_priority_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора приоритета (опционально)"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🔴 Высокий", callback_data="priority_high"),
        InlineKeyboardButton(text="🟡 Средний", callback_data="priority_medium")
    )
    keyboard.row(
        InlineKeyboardButton(text="🟢 Низкий", callback_data="priority_low")
    )
    keyboard.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    
    return keyboard.as_markup()


def get_confirmation_keyboard(action: str, item_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    keyboard = InlineKeyboardBuilder()
    
    confirm_data = f"confirm_{action}"
    cancel_data = "cancel"
    
    if item_id:
        confirm_data += f"_{item_id}"
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Да", callback_data=confirm_data),
        InlineKeyboardButton(text="❌ Нет", callback_data=cancel_data)
    )
    
    return keyboard.as_markup()


# Клавиатура быстрых ответов для часто задаваемых вопросов
def get_quick_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура быстрых ответов"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📞 Связаться с поддержкой"),
                KeyboardButton(text="❓ FAQ")
            ],
            [
                KeyboardButton(text="📋 Мои обращения"),
                KeyboardButton(text="🏠 Главное меню")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_remove_keyboard() -> ReplyKeyboardMarkup:
    """Удаление клавиатуры"""
    return ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)