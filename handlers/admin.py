"""Обработчики для администраторов"""

import math
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from keyboards.admin import (
    get_admin_panel, get_admin_tickets_keyboard, get_admin_ticket_actions,
    get_admin_stats_keyboard, get_admin_manage_keyboard, get_admin_search_keyboard,
    get_confirm_action_keyboard, get_admin_quick_responses
)
from keyboards.user import get_cancel_keyboard, get_main_menu
from keyboards.reply import (
    get_admin_main_keyboard, get_admin_user_management_keyboard,
    get_cancel_keyboard as get_reply_cancel_keyboard, get_confirmation_keyboard
)
from database import db
from utils.texts import (
    ADMIN_TICKETS_MESSAGE, TICKET_DETAILS_MESSAGE, TICKET_CATEGORIES,
    TICKET_STATUSES, TICKET_RESPONSE_MESSAGE, ERROR_MESSAGE, PERMISSION_DENIED
)
from handlers.common import AdminStates
from config import ADMINS, TICKETS_PER_PAGE


# Импорт функции проверки прав агентов
async def check_agent_or_admin(user_id: int) -> bool:
    """Проверка прав агента или администратора"""
    user_role = await db.get_user_role(user_id)
    return user_role in ['agent', 'admin']


router = Router()


async def check_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    user_role = await db.get_user_role(user_id)
    return user_role == 'admin'


# ===== ОБРАБОТЧИКИ REPLY КНОПОК АДМИНА =====

@router.message(F.text == "👥 Пользователи", StateFilter(None))
async def handle_admin_users_button(message: Message):
    """Обработка кнопки управления пользователями"""
    if not await check_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_admin_main_keyboard())
        return
    
    await message.answer(
        "👥 <b>Управление пользователями</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_user_management_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "⚙️ Настройки", StateFilter(None))
async def handle_admin_settings_button(message: Message):
    """Обработка кнопки настроек"""
    if not await check_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_admin_main_keyboard())
        return
    
    from keyboards.admin import get_admin_settings_keyboard
    
    settings_text = """
⚙️ <b>Настройки системы</b>

<b>Текущие настройки:</b>
• Максимальный размер обращения: 1000 символов
• Обращений на страницу: 5
• Автоуведомления: Включены

<b>Доступные действия:</b>
• Управление ролями пользователей
• Настройка уведомлений
• Экспорт статистики
• Резервное копирование данных
"""
    
    await message.answer(
        settings_text,
        reply_markup=get_admin_settings_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "👥 Список пользователей", StateFilter(None))
async def handle_list_users_button(message: Message):
    """Показать список всех пользователей"""
    if not await check_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_admin_main_keyboard())
        return
    
    await show_users_list(message)


@router.message(F.text == "👨‍💼 Список агентов", StateFilter(None))
async def handle_list_agents_button(message: Message):
    """Показать список агентов"""
    if not await check_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_admin_main_keyboard())
        return
    
    await show_agents_list(message)


@router.message(F.text == "📊 Статистика ролей", StateFilter(None))
async def handle_roles_stats_button(message: Message):
    """Показать статистику по ролям"""
    if not await check_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_admin_main_keyboard())
        return
    
    await show_roles_statistics(message)


@router.message(F.text == "🏠 Админ меню", StateFilter(None))
async def handle_admin_menu_button(message: Message):
    """Возврат в админ меню"""
    if not await check_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_admin_main_keyboard())
        return
    
    # Получаем статистику
    stats = await db.get_ticket_stats()
    
    stats_text = f"""
📊 <b>Общая статистика:</b>
• Всего обращений: {stats.get('total', 0)}
• Новых: {stats.get('status_new', 0)}
• В работе: {stats.get('status_in_progress', 0)}
• Ожидают ответа: {stats.get('status_waiting_response', 0)}
• Решено: {stats.get('status_resolved', 0)}
• Закрыто: {stats.get('status_closed', 0)}
"""
    
    from utils.texts import ADMIN_PANEL_MESSAGE
    await message.answer(
        ADMIN_PANEL_MESSAGE.format(stats=stats_text),
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text.in_(["🆕 Новые", "⏳ Активные", "📊 Статистика"]), StateFilter(None))
async def handle_admin_quick_buttons(message: Message):
    """Обработка быстрых кнопок админа"""
    if not await check_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_admin_main_keyboard())
        return
    
    if message.text == "🆕 Новые":
        await show_new_tickets_admin(message)
    elif message.text == "⏳ Активные":
        await show_active_tickets_admin(message)
    elif message.text == "📊 Статистика":
        await show_admin_stats_detailed(message)


@router.message(F.text == "🔍 Поиск", StateFilter(None))
async def handle_admin_search_button(message: Message, state: FSMContext):
    """Обработка кнопки поиска админом"""
    if not await check_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_admin_main_keyboard())
        return
    
    await message.answer(
        "🔍 <b>Поиск обращений</b>\n\n"
        "Введите номер обращения для поиска:",
        reply_markup=get_reply_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_search)


@router.message(AdminStates.waiting_search)
async def process_admin_search(message: Message, state: FSMContext):
    """Обработка поиска обращения админом или агентом"""
    if not await check_agent_or_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED)
        await state.clear()
        return
        
    if message.text == "❌ Отмена":
        await state.clear()
        user_role = await db.get_user_role(message.from_user.id)
        if user_role == 'admin':
            keyboard = get_admin_main_keyboard()
        else:
            keyboard = get_agent_main_keyboard(show_admin_return=True)
        await message.answer(
            "❌ Поиск отменен.",
            reply_markup=keyboard
        )
        return
    
    try:
        ticket_id = int(message.text.strip())
        ticket = await db.get_ticket(ticket_id)
        
        if not ticket:
            user_role = await db.get_user_role(message.from_user.id)
            if user_role == 'admin':
                keyboard = get_admin_main_keyboard()
            else:
                keyboard = get_agent_main_keyboard(show_admin_return=True)
            await message.answer(
                f"❌ Обращение #{ticket_id} не найдено.",
                reply_markup=keyboard
            )
            await state.clear()
            return
        
        # Показываем найденное обращение
        await show_ticket_for_admin(message, ticket)
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Введите корректный номер обращения (только цифры).",
            reply_markup=get_reply_cancel_keyboard()
        )


async def show_ticket_for_admin(message: Message, ticket: dict):
    """Показать обращение админу"""
    try:
        # Получаем информацию о пользователе
        user = await db.get_user(ticket['user_id'])
        user_name = user['first_name'] if user else "Неизвестно"
        
        status_emoji = get_status_emoji(ticket['status'])
        category_name = TICKET_CATEGORIES.get(ticket['category'], ticket['category'])
        status_name = TICKET_STATUSES.get(ticket['status'], ticket['status'])
        
        created_at = datetime.fromisoformat(ticket['created_at']).strftime("%d.%m.%Y %H:%M")
        
        details_text = f"""
🎫 <b>Найдено обращение #{ticket['id']}</b>

👤 <b>Клиент:</b> {user_name}
📋 <b>Тема:</b> {ticket['subject']}
📂 <b>Категория:</b> {category_name}
📊 <b>Статус:</b> {status_emoji} {status_name}
⏰ <b>Создано:</b> {created_at}

📝 <b>Описание:</b>
{ticket['description'][:300]}...
"""
        
        await message.answer(
            details_text,
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )
        
        # Показываем inline меню для действий с обращением
        from keyboards.admin import get_admin_ticket_actions
        user_role = await db.get_user_role(message.from_user.id)
        await message.answer(
            "🎯 <b>Действия с обращением:</b>",
            reply_markup=get_admin_ticket_actions(
                ticket['id'], 
                ticket['status'],
                ticket.get('assigned_admin'),
                message.from_user.id,
                user_role=user_role
            ),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_admin_main_keyboard()
        )


async def show_new_tickets_admin(message: Message):
    """Показать новые обращения для админа"""
    await show_admin_tickets(message, "new")


async def show_active_tickets_admin(message: Message):
    """Показать активные обращения для админа"""
    await show_admin_tickets(message, "active")


async def show_admin_tickets(message: Message, ticket_type: str):
    """Показать обращения для админа"""
    try:
        if ticket_type == "new":
            tickets = await db.get_pending_tickets(20)
            tickets = [t for t in tickets if t['status'] == 'new']
            title = "🆕 Новые обращения"
        elif ticket_type == "active":
            tickets = await db.get_pending_tickets(20)
            tickets = [t for t in tickets if t['status'] in ['in_progress', 'waiting_response']]
            title = "⏳ Активные обращения"
        else:  # closed
            tickets = []
            title = "✅ Закрытые обращения"
        
        if not tickets:
            message_text = f"<b>{title}</b>\n\n📭 Обращений не найдено."
            keyboard = get_admin_main_keyboard()
        else:
            tickets_list = ""
            for i, ticket in enumerate(tickets, 1):
                status_emoji = get_status_emoji(ticket['status'])
                priority_emoji = get_priority_emoji(ticket.get('priority', 'medium'))
                user_name = ticket.get('first_name', 'Неизвестно')
                created_date = datetime.fromisoformat(ticket['created_at']).strftime("%d.%m")
                
                tickets_list += f"{i}. {priority_emoji}{status_emoji} <b>#{ticket['id']}</b>\n"
                tickets_list += f"   👤 {user_name} | 📅 {created_date}\n"
                tickets_list += f"   📝 {ticket['subject'][:50]}...\n\n"
            
            message_text = f"<b>{title}</b>\n\n{tickets_list}"
            keyboard = get_admin_main_keyboard()
        
        await message.answer(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # Отправляем inline меню если есть обращения
        if tickets:
            from keyboards.admin import get_admin_tickets_keyboard
            user_role = await db.get_user_role(message.from_user.id)
            await message.answer(
                "🎯 <b>Выберите обращение:</b>",
                reply_markup=get_admin_tickets_keyboard(tickets, ticket_type, user_role),
                parse_mode="HTML"
            )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )


def get_status_emoji(status: str) -> str:
    """Получить эмодзи для статуса"""
    emojis = {
        'new': '🆕',
        'in_progress': '⏳',
        'waiting_response': '⏰',
        'resolved': '✅',
        'closed': '🔒'
    }
    return emojis.get(status, '❓')


def get_priority_emoji(priority: str) -> str:
    """Получить эмодзи для приоритета"""
    emojis = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }
    return emojis.get(priority, '🟡')


async def show_admin_stats_detailed(message: Message):
    """Показать детальную статистику для админа"""
    try:
        stats = await db.get_ticket_stats()
        
        stats_text = f"""
📊 <b>Подробная статистика</b>

<b>📈 Текущие обращения:</b>
• 🆕 Новые: {stats.get('status_new', 0)}
• ⏳ В работе: {stats.get('status_in_progress', 0)}
• ⏰ Ожидают ответа: {stats.get('status_waiting_response', 0)}

<b>📋 Завершенные:</b>
• ✅ Решенные: {stats.get('status_resolved', 0)}
• 🔒 Закрытые: {stats.get('status_closed', 0)}

<b>📊 Общая статистика:</b>
• Всего обращений: {stats.get('total', 0)}
• Требуют внимания: {stats.get('status_new', 0) + stats.get('status_waiting_response', 0)}

<i>Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>
"""
        
        await message.answer(
            stats_text,
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )


# ===== ФУНКЦИИ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ =====

async def show_users_list(message: Message):
    """Показать список всех пользователей"""
    try:
        # Получаем всех пользователей из базы (нужно добавить метод в database.py)
        # Пока покажем заглушку
        users_text = """
👥 <b>Список пользователей</b>

<b>Администраторы:</b>
"""
        
        # Показываем админов
        from config import ADMINS
        for admin_id in ADMINS:
            user = await db.get_user(admin_id)
            if user:
                name = user.get('first_name', 'Неизвестно')
                users_text += f"• {name} (ID: {admin_id})\n"
        
        users_text += "\n<b>Агенты:</b>\n"
        
        # Показываем агентов
        agents = await db.get_agents()
        if agents:
            for agent in agents:
                users_text += f"• {agent.get('first_name', 'Неизвестно')} (ID: {agent['user_id']})\n"
        else:
            users_text += "• Агенты не назначены\n"
        
        users_text += f"\n<i>Всего пользователей в системе: {await count_total_users()}</i>"
        
        await message.answer(
            users_text,
            reply_markup=get_admin_user_management_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_admin_user_management_keyboard()
        )


async def show_agents_list(message: Message):
    """Показать список агентов"""
    try:
        agents = await db.get_agents()
        
        if not agents:
            agents_text = """
👨‍💼 <b>Список агентов</b>

📭 Агенты не назначены.

Используйте кнопку "➕ Добавить агента" для назначения.
"""
        else:
            agents_text = "👨‍💼 <b>Список агентов</b>\n\n"
            for i, agent in enumerate(agents, 1):
                name = agent.get('first_name', 'Неизвестно')
                username = f"@{agent['username']}" if agent.get('username') else "без username"
                created = datetime.fromisoformat(agent['created_at']).strftime("%d.%m.%Y")
                
                agents_text += f"{i}. <b>{name}</b>\n"
                agents_text += f"   ID: {agent['user_id']} | {username}\n"
                agents_text += f"   Добавлен: {created}\n\n"
        
        await message.answer(
            agents_text,
            reply_markup=get_admin_user_management_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_admin_user_management_keyboard()
        )


async def show_roles_statistics(message: Message):
    """Показать статистику по ролям"""
    try:
        # Подсчитываем пользователей по ролям
        from config import ADMINS
        
        admins_count = len(ADMINS)
        agents = await db.get_agents()
        agents_count = len(agents)
        
        total_users = await count_total_users()
        clients_count = total_users - admins_count - agents_count
        
        stats_text = f"""
📊 <b>Статистика по ролям</b>

<b>👑 Администраторы:</b> {admins_count}
<b>👨‍💼 Агенты поддержки:</b> {agents_count}
<b>👤 Клиенты:</b> {clients_count}

<b>📈 Общая статистика:</b>
• Всего пользователей: {total_users}
• Персонал поддержки: {admins_count + agents_count}
• Активных пользователей: {total_users}

<i>Последнее обновление: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>
"""
        
        await message.answer(
            stats_text,
            reply_markup=get_admin_user_management_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_admin_user_management_keyboard()
        )


async def count_total_users() -> int:
    """Подсчитать общее количество пользователей"""
    try:
        return await db.count_total_users()
    except:
        return 0


@router.callback_query(F.data == "admin_new_tickets")
async def show_new_tickets(callback: CallbackQuery):
    """Показать новые обращения"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    await show_admin_tickets(callback, "new")


@router.callback_query(F.data == "admin_active_tickets")
async def show_active_tickets(callback: CallbackQuery):
    """Показать активные обращения"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    await show_admin_tickets(callback, "active")


@router.callback_query(F.data == "admin_closed_tickets")
async def show_closed_tickets(callback: CallbackQuery):
    """Показать закрытые обращения"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    await show_admin_tickets(callback, "closed")


async def show_admin_tickets(callback: CallbackQuery, ticket_type: str):
    """Показать обращения для админа"""
    try:
        if ticket_type == "new":
            tickets = await db.get_pending_tickets(20)
            tickets = [t for t in tickets if t['status'] == 'new']
            title = "🆕 Новые обращения"
        elif ticket_type == "active":
            tickets = await db.get_pending_tickets(20)
            tickets = [t for t in tickets if t['status'] in ['in_progress', 'waiting_response']]
            title = "⏳ Активные обращения"
        else:  # closed
            tickets = await db.get_closed_tickets(20)
            title = "✅ Закрытые обращения"
        
        if not tickets:
            message_text = f"<b>{title}</b>\n\n📭 Обращений не найдено."
            keyboard = get_admin_panel()
        else:
            tickets_list = ""
            for i, ticket in enumerate(tickets, 1):
                status_emoji = get_status_emoji(ticket['status'])
                priority_emoji = get_priority_emoji(ticket.get('priority', 'medium'))
                user_name = ticket.get('first_name', 'Неизвестно')
                created_date = datetime.fromisoformat(ticket['created_at']).strftime("%d.%m")
                
                tickets_list += f"{i}. {priority_emoji}{status_emoji} <b>#{ticket['id']}</b>\n"
                tickets_list += f"   👤 {user_name} | 📅 {created_date}\n"
                tickets_list += f"   📝 {ticket['subject'][:50]}...\n\n"
            
            message_text = f"<b>{title}</b>\n\n{tickets_list}"
            user_role = await db.get_user_role(callback.from_user.id)
            keyboard = get_admin_tickets_keyboard(tickets, ticket_type, user_role)
        
        await callback.message.edit_text(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        await callback.message.edit_text(
            ERROR_MESSAGE,
            reply_markup=get_admin_panel(),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data.startswith("admin_ticket_"))
async def show_admin_ticket_details(callback: CallbackQuery):
    """Показать детали обращения для админа или агента"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        ticket_id = int(callback.data.split("_")[-1])
        ticket = await db.get_ticket(ticket_id)
        
        if not ticket:
            await callback.answer("❌ Обращение не найдено", show_alert=True)
            return
        
        # Получаем информацию о пользователе
        user = await db.get_user(ticket['user_id'])
        user_name = user['first_name'] if user else "Неизвестно"
        
        # Получаем сообщения
        messages = await db.get_ticket_messages(ticket_id)
        
        # Формируем информацию о сообщениях
        messages_info = ""
        if messages:
            messages_info = f"\n<b>💬 История переписки:</b>\n"
            for msg in messages[-5:]:  # Последние 5 сообщений
                sender = "👨‍💼 Поддержка" if msg['is_admin'] else f"👤 {msg.get('first_name', 'Пользователь')}"
                msg_date = datetime.fromisoformat(msg['created_at']).strftime("%d.%m %H:%M")
                messages_info += f"• {sender} ({msg_date}):\n  {msg['message'][:150]}...\n\n"
        
        # Форматируем даты
        created_at = datetime.fromisoformat(ticket['created_at']).strftime("%d.%m.%Y %H:%M")
        updated_at = datetime.fromisoformat(ticket['updated_at']).strftime("%d.%m.%Y %H:%M")
        
        status_emoji = get_status_emoji(ticket['status'])
        priority_emoji = get_priority_emoji(ticket.get('priority', 'medium'))
        category_name = TICKET_CATEGORIES.get(ticket['category'], ticket['category'])
        status_name = TICKET_STATUSES.get(ticket['status'], ticket['status'])
        
        details_text = f"""
🎫 <b>Обращение #{ticket_id}</b> {priority_emoji}

👤 <b>Пользователь:</b> {user_name} (ID: {ticket['user_id']})
📋 <b>Тема:</b> {ticket['subject']}
📂 <b>Категория:</b> {category_name}
📊 <b>Статус:</b> {status_emoji} {status_name}
⏰ <b>Создано:</b> {created_at}
🔄 <b>Обновлено:</b> {updated_at}

📝 <b>Описание:</b>
{ticket['description']}

{messages_info}
"""
        
        user_role = await db.get_user_role(callback.from_user.id)
        await callback.message.edit_text(
            details_text,
            reply_markup=get_admin_ticket_actions(
                ticket_id, 
                ticket['status'], 
                ticket.get('assigned_admin'),
                callback.from_user.id,
                user_role=user_role
            ),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except ValueError:
        await callback.answer("❌ Неверный ID обращения", show_alert=True)
    except Exception as e:
        await callback.answer("❌ Ошибка при загрузке обращения", show_alert=True)


@router.callback_query(F.data.startswith("admin_respond_"))
async def start_admin_response(callback: CallbackQuery, state: FSMContext):
    """Начать ответ администратора или агента"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    ticket_id = int(callback.data.split("_")[-1])
    
    await state.update_data(admin_responding_ticket_id=ticket_id)
    await callback.message.edit_text(
        TICKET_RESPONSE_MESSAGE.format(ticket_id=ticket_id),
        reply_markup=get_admin_quick_responses(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("quick_"))
async def quick_response(callback: CallbackQuery, state: FSMContext):
    """Быстрый ответ администратора или агента"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    data = await state.get_data()
    ticket_id = data.get('admin_responding_ticket_id')
    
    if not ticket_id:
        await callback.answer("❌ Ошибка: не найдено обращение", show_alert=True)
        return
    
    quick_type = callback.data.split("_", 1)[1]
    
    # Словарь быстрых ответов
    quick_responses = {
        "resolved": "✅ Ваша проблема решена. Если у вас остались вопросы, создайте новое обращение.",
        "in_progress": "⏳ Мы работаем над вашей проблемой. Ожидайте обновлений в ближайшее время.",
        "need_info": "❓ Для решения вашей проблемы нам нужна дополнительная информация. Пожалуйста, предоставьте более подробные данные.",
        "forwarded": "📋 Ваше обращение переадресовано в соответствующий отдел. Специалист свяжется с вами в течение 24 часов.",
        "dev_issue": "🔧 Проблема связана с техническими работами. Наши разработчики уже работают над исправлением."
    }
    
    response_text = quick_responses.get(quick_type, "Спасибо за обращение. Мы рассмотрим ваш вопрос.")
    
    await send_admin_response(callback, state, ticket_id, response_text, quick_type)


@router.callback_query(F.data == "admin_custom_response")
async def custom_response(callback: CallbackQuery, state: FSMContext):
    """Кастомный ответ администратора или агента"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    await callback.message.edit_text(
        "✏️ <b>Написать свой ответ</b>\n\nВведите текст ответа пользователю:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_response)
    await callback.answer()


@router.message(AdminStates.waiting_response)
async def process_admin_response(message: Message, state: FSMContext):
    """Обработка ответа администратора или агента"""
    if not await check_agent_or_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED)
        return
    
    data = await state.get_data()
    ticket_id = data.get('admin_responding_ticket_id')
    
    if not ticket_id:
        await message.answer("❌ Ошибка: не найдено обращение", reply_markup=get_admin_panel())
        await state.clear()
        return
    
    response_text = message.text.strip()
    
    if len(response_text) < 5:
        await message.answer(
            "❌ Ответ слишком короткий. Минимум 5 символов.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await send_admin_response_message(message, state, ticket_id, response_text)


async def send_admin_response(callback: CallbackQuery, state: FSMContext, ticket_id: int, response_text: str, action_type: str = None):
    """Отправить ответ администратора (из callback)"""
    try:
        # Добавляем сообщение в базу
        await db.add_ticket_message(ticket_id, callback.from_user.id, response_text, True)
        
        # Обновляем статус в зависимости от типа быстрого ответа
        if action_type == "resolved":
            await db.update_ticket_status(ticket_id, 'resolved', callback.from_user.id)
        elif action_type == "in_progress":
            await db.update_ticket_status(ticket_id, 'in_progress', callback.from_user.id)
        else:
            await db.update_ticket_status(ticket_id, 'in_progress', callback.from_user.id)
        
        # Отправляем ответ пользователю
        ticket = await db.get_ticket(ticket_id)
        if ticket:
            await notify_user_response(ticket['user_id'], ticket_id, response_text)
        
        await state.clear()
        
        await callback.message.edit_text(
            f"✅ <b>Ответ отправлен пользователю</b>\n\n"
            f"Обращение #{ticket_id} обновлено.",
            reply_markup=get_admin_panel(),
            parse_mode="HTML"
        )
        await callback.answer("✅ Ответ отправлен!")
        
    except Exception as e:
        await callback.message.edit_text(
            ERROR_MESSAGE,
            reply_markup=get_admin_panel(),
            parse_mode="HTML"
        )
        await callback.answer("❌ Ошибка при отправке ответа", show_alert=True)


async def send_admin_response_message(message: Message, state: FSMContext, ticket_id: int, response_text: str):
    """Отправить ответ администратора (из сообщения)"""
    try:
        # Добавляем сообщение в базу
        await db.add_ticket_message(ticket_id, message.from_user.id, response_text, True)
        
        # Обновляем статус
        await db.update_ticket_status(ticket_id, 'in_progress', message.from_user.id)
        
        # Отправляем ответ пользователю
        ticket = await db.get_ticket(ticket_id)
        if ticket:
            await notify_user_response(ticket['user_id'], ticket_id, response_text)
        
        await state.clear()
        
        await message.answer(
            f"✅ <b>Ответ отправлен пользователю</b>\n\n"
            f"Обращение #{ticket_id} обновлено.",
            reply_markup=get_admin_panel(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_admin_panel(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("admin_status_"))
async def change_ticket_status(callback: CallbackQuery):
    """Изменить статус обращения"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        parts = callback.data.split("_")
        ticket_id = int(parts[2])
        new_status = parts[3]
        
        await db.update_ticket_status(ticket_id, new_status, callback.from_user.id)
        
        status_name = TICKET_STATUSES.get(new_status, new_status)
        
        await callback.answer(f"✅ Статус изменен на: {status_name}")
        
        # Обновляем отображение обращения
        await show_admin_ticket_details(callback)
        
        # Уведомляем пользователя об изменении статуса
        ticket = await db.get_ticket(ticket_id)
        if ticket:
            await notify_user_status_change(ticket['user_id'], ticket_id, new_status)
        
    except Exception as e:
        await callback.answer("❌ Ошибка при изменении статуса", show_alert=True)


@router.callback_query(F.data.startswith("admin_priority_"))
async def change_ticket_priority(callback: CallbackQuery):
    """Изменить приоритет обращения"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        parts = callback.data.split("_")
        ticket_id = int(parts[2])
        priority = parts[3]
        
        # Обновляем приоритет
        await db.update_ticket_priority(ticket_id, priority)
        
        priority_names = {'high': 'Высокий', 'medium': 'Средний', 'low': 'Низкий'}
        priority_name = priority_names.get(priority, priority)
        
        await callback.answer(f"✅ Приоритет изменен на: {priority_name}")
        
        # Обновляем отображение обращения
        await show_admin_ticket_details(callback)
        
    except Exception as e:
        await callback.answer("❌ Ошибка при изменении приоритета", show_alert=True)


@router.callback_query(F.data.startswith("search_ticket_"))
async def quick_search_ticket(callback: CallbackQuery):
    """Быстрый поиск и показ обращения по ID из уведомления"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        ticket_id = int(callback.data.split("_")[-1])
        ticket = await db.get_ticket(ticket_id)
        
        if not ticket:
            await callback.answer("❌ Обращение не найдено", show_alert=True)
            return
        
        # Переходим к показу обращения для любого из ролей
        await show_admin_ticket_details(callback)
        
    except ValueError:
        await callback.answer("❌ Неверный ID обращения", show_alert=True)
    except Exception as e:
        await callback.answer("❌ Ошибка при поиске обращения", show_alert=True)


@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    """Показать статистику для админа или агента"""
    if not await check_agent_or_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        stats = await db.get_ticket_stats()
        
        stats_text = f"""
📊 <b>Статистика поддержки</b>

<b>📈 Общее количество:</b>
• Всего обращений: {stats.get('total', 0)}

<b>📋 По статусам:</b>
• 🆕 Новые: {stats.get('status_new', 0)}
• ⏳ В работе: {stats.get('status_in_progress', 0)}
• ⏰ Ожидают ответа: {stats.get('status_waiting_response', 0)}
• ✅ Решенные: {stats.get('status_resolved', 0)}
• 🔒 Закрытые: {stats.get('status_closed', 0)}

<b>⚡ Активность:</b>
• Требуют внимания: {stats.get('status_new', 0) + stats.get('status_waiting_response', 0)}
"""
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_admin_stats_keyboard(stats),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        await callback.message.edit_text(
            ERROR_MESSAGE,
            reply_markup=get_admin_panel(),
            parse_mode="HTML"
        )
        await callback.answer()


async def notify_user_response(user_id: int, ticket_id: int, response_text: str):
    """Уведомить пользователя об ответе"""
    from bot import bot
    
    try:
        await bot.send_message(
            user_id,
            f"💬 <b>Новый ответ на обращение #{ticket_id}</b>\n\n"
            f"<b>Ответ поддержки:</b>\n{response_text}\n\n"
            f"Вы можете ответить, перейдя к обращению в разделе \"Мои обращения\".",
            parse_mode="HTML"
        )
    except:
        pass


async def notify_user_status_change(user_id: int, ticket_id: int, new_status: str):
    """Уведомить пользователя об изменении статуса"""
    from bot import bot
    
    try:
        status_name = TICKET_STATUSES.get(new_status, new_status)
        status_emoji = get_status_emoji(new_status)
        
        await bot.send_message(
            user_id,
            f"📊 <b>Статус обращения #{ticket_id} изменен</b>\n\n"
            f"Новый статус: {status_emoji} {status_name}\n\n"
            f"Проверьте детали в разделе \"Мои обращения\".",
            parse_mode="HTML"
        )
    except:
        pass


def get_status_emoji(status: str) -> str:
    """Получить эмодзи для статуса"""
    emojis = {
        'new': '🆕',
        'in_progress': '⏳',
        'waiting_response': '⏰',
        'resolved': '✅',
        'closed': '🔒'
    }
    return emojis.get(status, '❓')


def get_priority_emoji(priority: str) -> str:
    """Получить эмодзи для приоритета"""
    emojis = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }
    return emojis.get(priority, '🟡')