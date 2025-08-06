"""Клавиатуры для администраторов"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Any
from utils.texts import TICKET_STATUSES


def get_admin_panel() -> InlineKeyboardMarkup:
    """Главная панель администратора"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📋 Новые обращения", callback_data="admin_new_tickets")
    )
    keyboard.row(
        InlineKeyboardButton(text="⏳ В работе", callback_data="admin_active_tickets"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    keyboard.row(
        InlineKeyboardButton(text="👥 Управление", callback_data="admin_manage"),
        InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_search")
    )
    keyboard.row(
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings"),
        InlineKeyboardButton(text="💾 Экспорт", callback_data="admin_export")
    )
    
    return keyboard.as_markup()


def get_agent_panel() -> InlineKeyboardMarkup:
    """Главная панель агента поддержки (упрощённая)"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📋 Новые обращения", callback_data="admin_new_tickets"),
        InlineKeyboardButton(text="⏳ В работе", callback_data="admin_active_tickets")
    )
    keyboard.row(
        InlineKeyboardButton(text="⏰ Ожидают ответа", callback_data="admin_active_tickets"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_search")
    )
    
    return keyboard.as_markup()


def get_quick_ticket_actions(ticket_id: int, context: str = "default") -> InlineKeyboardMarkup:
    """Быстрые действия для обращения в уведомлениях"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(
            text="👁 Посмотреть", 
            callback_data=f"admin_ticket_{ticket_id}"
        ),
        InlineKeyboardButton(
            text="💬 Ответить", 
            callback_data=f"admin_respond_{ticket_id}"
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="✅ Взять в работу", 
            callback_data=f"admin_status_{ticket_id}_in_progress"
        ),
        InlineKeyboardButton(
            text="🔍 Найти по ID", 
            callback_data=f"search_ticket_{ticket_id}"
        )
    )
    
    return keyboard.as_markup()


def get_admin_tickets_keyboard(tickets: List[Dict[str, Any]], 
                              ticket_type: str = "new",
                              user_role: str = "admin") -> InlineKeyboardMarkup:
    """Клавиатура для просмотра обращений (для админов и агентов)"""
    keyboard = InlineKeyboardBuilder()
    
    # Кнопки обращений
    for ticket in tickets:
        priority_emoji = "🔴" if ticket.get('priority') == 'high' else "🟡" if ticket.get('priority') == 'medium' else "🟢"
        user_name = ticket.get('first_name', 'Пользователь')
        button_text = f"{priority_emoji} #{ticket['id']} - {user_name} - {ticket['subject'][:25]}..."
        
        keyboard.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"admin_ticket_{ticket['id']}"
            )
        )
    
    # Навигация
    navigation_buttons = []
    if ticket_type == "new":
        navigation_buttons.extend([
            InlineKeyboardButton(text="⏳ В работе", callback_data="admin_active_tickets"),
            InlineKeyboardButton(text="✅ Закрытые", callback_data="admin_closed_tickets")
        ])
    elif ticket_type == "active":
        navigation_buttons.extend([
            InlineKeyboardButton(text="🆕 Новые", callback_data="admin_new_tickets"),
            InlineKeyboardButton(text="✅ Закрытые", callback_data="admin_closed_tickets")
        ])
    else:
        navigation_buttons.extend([
            InlineKeyboardButton(text="🆕 Новые", callback_data="admin_new_tickets"),
            InlineKeyboardButton(text="⏳ В работе", callback_data="admin_active_tickets")
        ])
    
    if navigation_buttons:
        keyboard.row(*navigation_buttons)
    
    # Разная навигация для ролей
    if user_role == "admin":
        keyboard.row(
            InlineKeyboardButton(text="🔄 Обновить", callback_data=f"admin_{ticket_type}_tickets"),
            InlineKeyboardButton(text="👨‍💼 Админ панель", callback_data="admin_panel")
        )
    else:
        # Для агентов - только обновить
        keyboard.row(
            InlineKeyboardButton(text="🔄 Обновить", callback_data=f"admin_{ticket_type}_tickets")
        )
    
    return keyboard.as_markup()


def get_admin_ticket_actions(ticket_id: int, current_status: str, 
                           assigned_admin: int = None, 
                           current_admin: int = None,
                           user_role: str = 'admin') -> InlineKeyboardMarkup:
    """Клавиатура действий с обращением (для админов и агентов)"""
    keyboard = InlineKeyboardBuilder()
    
    # Кнопка ответа
    keyboard.row(
        InlineKeyboardButton(
            text="💬 Отправить ответ", 
            callback_data=f"admin_respond_{ticket_id}"
        )
    )
    
    # Кнопки изменения статуса
    status_buttons = []
    if current_status == 'new':
        status_buttons.extend([
            InlineKeyboardButton(text="🔄 Взять в работу", callback_data=f"admin_status_{ticket_id}_in_progress"),
            InlineKeyboardButton(text="✅ Решить", callback_data=f"admin_status_{ticket_id}_resolved")
        ])
    elif current_status == 'in_progress':
        status_buttons.extend([
            InlineKeyboardButton(text="⏰ Ожидает ответа", callback_data=f"admin_status_{ticket_id}_waiting_response"),
            InlineKeyboardButton(text="✅ Решить", callback_data=f"admin_status_{ticket_id}_resolved")
        ])
    elif current_status == 'waiting_response':
        status_buttons.extend([
            InlineKeyboardButton(text="🔄 Вернуть в работу", callback_data=f"admin_status_{ticket_id}_in_progress"),
            InlineKeyboardButton(text="✅ Решить", callback_data=f"admin_status_{ticket_id}_resolved")
        ])
    elif current_status == 'resolved':
        status_buttons.append(
            InlineKeyboardButton(text="🔒 Закрыть", callback_data=f"admin_status_{ticket_id}_closed")
        )
    
    if status_buttons:
        if len(status_buttons) == 1:
            keyboard.row(status_buttons[0])
        else:
            keyboard.row(*status_buttons)
    
    # Кнопки приоритета
    keyboard.row(
        InlineKeyboardButton(text="🔴 Высокий", callback_data=f"admin_priority_{ticket_id}_high"),
        InlineKeyboardButton(text="🟡 Средний", callback_data=f"admin_priority_{ticket_id}_medium"),
        InlineKeyboardButton(text="🟢 Низкий", callback_data=f"admin_priority_{ticket_id}_low")
    )
    
    # Кнопка назначения админа (ТОЛЬКО для админов)
    if user_role == 'admin' and (not assigned_admin or assigned_admin == current_admin):
        keyboard.row(
            InlineKeyboardButton(
                text="👤 Назначить админа", 
                callback_data=f"admin_assign_{ticket_id}"
            )
        )
    
    # Навигация (разная для ролей)
    if user_role == 'admin':
        keyboard.row(
            InlineKeyboardButton(text="📋 К обращениям", callback_data="admin_new_tickets"),
            InlineKeyboardButton(text="👨‍💼 Админ панель", callback_data="admin_panel")
        )
    else:
        # Для агентов - упрощённая навигация
        keyboard.row(
            InlineKeyboardButton(text="📋 К обращениям", callback_data="admin_new_tickets")
        )
    
    return keyboard.as_markup()


def get_admin_stats_keyboard(stats: Dict[str, int]) -> InlineKeyboardMarkup:
    """Клавиатура статистики для админа"""
    keyboard = InlineKeyboardBuilder()
    
    # Кнопки быстрого перехода к типам обращений
    if stats.get('status_new', 0) > 0:
        keyboard.row(
            InlineKeyboardButton(
                text=f"🆕 Новые ({stats['status_new']})", 
                callback_data="admin_new_tickets"
            )
        )
    
    if stats.get('status_in_progress', 0) > 0:
        keyboard.row(
            InlineKeyboardButton(
                text=f"⏳ В работе ({stats['status_in_progress']})", 
                callback_data="admin_active_tickets"
            )
        )
    
    keyboard.row(
        InlineKeyboardButton(text="📊 Подробная статистика", callback_data="admin_detailed_stats"),
        InlineKeyboardButton(text="📈 Экспорт отчета", callback_data="admin_export_report")
    )
    
    keyboard.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats"),
        InlineKeyboardButton(text="👨‍💼 Админ панель", callback_data="admin_panel")
    )
    
    return keyboard.as_markup()


def get_admin_manage_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления пользователями"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_list_users"),
        InlineKeyboardButton(text="📊 Статистика ролей", callback_data="admin_roles_stats")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔧 Изменить роль", callback_data="admin_change_role"),
        InlineKeyboardButton(text="🚫 Заблокировать", callback_data="admin_block_user")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    )
    
    return keyboard.as_markup()


def get_admin_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек системы"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🔔 Уведомления", callback_data="admin_notifications"),
        InlineKeyboardButton(text="📝 Лимиты", callback_data="admin_limits")
    )
    keyboard.row(
        InlineKeyboardButton(text="💾 Резервное копирование", callback_data="admin_backup"),
        InlineKeyboardButton(text="🗑️ Очистка данных", callback_data="admin_cleanup")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    )
    
    return keyboard.as_markup()


def get_admin_export_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура экспорта данных"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_export_stats"),
        InlineKeyboardButton(text="📋 Обращения", callback_data="admin_export_tickets")
    )
    keyboard.row(
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_export_users"),
        InlineKeyboardButton(text="📈 Отчёт", callback_data="admin_export_report")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    )
    
    return keyboard.as_markup()


def get_priority_keyboard_admin(ticket_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора приоритета администратором"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🔴 Высокий", callback_data=f"admin_priority_{ticket_id}_high"),
        InlineKeyboardButton(text="🟡 Средний", callback_data=f"admin_priority_{ticket_id}_medium")
    )
    keyboard.row(
        InlineKeyboardButton(text="🟢 Низкий", callback_data=f"admin_priority_{ticket_id}_low")
    )
    keyboard.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_ticket_{ticket_id}")
    )
    
    return keyboard.as_markup()


def get_confirm_action_keyboard(action: str, ticket_id: int = None, 
                               user_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия администратором"""
    keyboard = InlineKeyboardBuilder()
    
    confirm_data = f"admin_confirm_{action}"
    cancel_data = "admin_cancel"
    
    if ticket_id:
        confirm_data += f"_{ticket_id}"
        cancel_data = f"admin_ticket_{ticket_id}"
    elif user_id:
        confirm_data += f"_{user_id}"
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_data),
        InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_data)
    )
    
    return keyboard.as_markup()


def get_admin_search_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура поиска для администратора"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🔍 По номеру обращения", callback_data="admin_search_id"),
        InlineKeyboardButton(text="👤 По пользователю", callback_data="admin_search_user")
    )
    keyboard.row(
        InlineKeyboardButton(text="📝 По тексту", callback_data="admin_search_text"),
        InlineKeyboardButton(text="📅 По дате", callback_data="admin_search_date")
    )
    keyboard.row(
        InlineKeyboardButton(text="👨‍💼 Админ панель", callback_data="admin_panel")
    )
    
    return keyboard.as_markup()


def get_admin_quick_responses() -> InlineKeyboardMarkup:
    """Клавиатура быстрых ответов для администратора"""
    keyboard = InlineKeyboardBuilder()
    
    quick_responses = [
        ("✅ Проблема решена", "quick_resolved"),
        ("⏳ Работаем над проблемой", "quick_in_progress"),
        ("❓ Нужна дополнительная информация", "quick_need_info"),
        ("📋 Переадресовано в другой отдел", "quick_forwarded"),
        ("🔧 Проблема на стороне разработчиков", "quick_dev_issue")
    ]
    
    for text, callback_data in quick_responses:
        keyboard.row(
            InlineKeyboardButton(text=text, callback_data=callback_data)
        )
    
    keyboard.row(
        InlineKeyboardButton(text="✏️ Написать свой ответ", callback_data="admin_custom_response")
    )
    
    return keyboard.as_markup()


def get_ticket_status_keyboard(ticket_id: int, current_status: str) -> InlineKeyboardMarkup:
    """Клавиатура изменения статуса обращения"""
    keyboard = InlineKeyboardBuilder()
    
    # Показываем только доступные переходы статусов
    available_statuses = []
    
    if current_status == 'new':
        available_statuses = ['in_progress', 'resolved']
    elif current_status == 'in_progress':
        available_statuses = ['waiting_response', 'resolved']
    elif current_status == 'waiting_response':
        available_statuses = ['in_progress', 'resolved']
    elif current_status == 'resolved':
        available_statuses = ['closed', 'in_progress']  # Можно переоткрыть
    
    for status in available_statuses:
        keyboard.row(
            InlineKeyboardButton(
                text=TICKET_STATUSES[status],
                callback_data=f"admin_status_{ticket_id}_{status}"
            )
        )
    
    keyboard.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_ticket_{ticket_id}")
    )
    
    return keyboard.as_markup()