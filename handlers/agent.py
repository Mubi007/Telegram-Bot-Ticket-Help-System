"""Обработчики для агентов поддержки"""

import math
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from keyboards.user import get_main_menu
from keyboards.admin import get_admin_ticket_actions
from keyboards.reply import (
    get_agent_main_keyboard, get_agent_actions_keyboard, 
    get_quick_responses_keyboard, get_cancel_keyboard,
    get_client_main_keyboard
)
from database import db
from utils.texts import (
    TICKET_DETAILS_MESSAGE, TICKET_CATEGORIES, TICKET_STATUSES,
    ERROR_MESSAGE, PERMISSION_DENIED, TICKET_RESPONSE_MESSAGE
)
from handlers.common import AdminStates
from config import TICKETS_PER_PAGE


router = Router()


async def check_agent_or_admin(user_id: int) -> bool:
    """Проверка прав агента или администратора"""
    user_role = await db.get_user_role(user_id)
    return user_role in ['agent', 'admin']


# ===== ОБРАБОТЧИКИ REPLY КНОПОК АГЕНТА =====

@router.message(F.text.in_(["🆕 Новые", "⏳ В работе", "⏰ Ожидают"]), StateFilter(None))
async def handle_agent_tickets_button(message: Message):
    """Обработка кнопок просмотра обращений агентом"""
    if not await check_agent_or_admin(message.from_user.id):
        await message.answer(
            PERMISSION_DENIED,
            reply_markup=get_client_main_keyboard()
        )
        return
    
    # Определяем тип обращений по кнопке
    if message.text == "🆕 Новые":
        status_filter = ['new']
        title = "🆕 Новые обращения"
    elif message.text == "⏳ В работе":
        status_filter = ['in_progress']
        title = "⏳ Обращения в работе"
    else:  # "⏰ Ожидают"
        status_filter = ['waiting_response']
        title = "⏰ Ожидают ответа"
    
    await show_agent_tickets(message, status_filter, title)


@router.message(F.text == "🔍 Поиск", StateFilter(None))
async def handle_agent_search_button(message: Message, state: FSMContext):
    """Обработка кнопки поиска агентом"""
    if not await check_agent_or_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_client_main_keyboard())
        return
    
    await message.answer(
        "🔍 <b>Поиск обращений</b>\n\n"
        "Введите номер обращения для поиска:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_search)


@router.message(F.text == "📊 Моя статистика", StateFilter(None))
async def handle_agent_stats_button(message: Message):
    """Обработка кнопки статистики агента"""
    if not await check_agent_or_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_client_main_keyboard())
        return
    
    await show_agent_stats(message)


# ===== ФУНКЦИИ ПОКАЗА ДАННЫХ =====

async def show_agent_tickets(message: Message, status_filter: list, title: str):
    """Показать обращения для агента"""
    try:
        # Получаем все обращения с нужными статусами
        all_tickets = await db.get_pending_tickets(50)
        tickets = [t for t in all_tickets if t['status'] in status_filter]
        
        if not tickets:
            await message.answer(
                f"<b>{title}</b>\n\n📭 Обращений не найдено.",
                reply_markup=get_agent_main_keyboard(),
                parse_mode="HTML"
            )
            return
        
        # Формируем список обращений
        tickets_list = ""
        for i, ticket in enumerate(tickets[:10], 1):  # Показываем первые 10
            status_emoji = get_status_emoji(ticket['status'])
            priority_emoji = get_priority_emoji(ticket.get('priority', 'medium'))
            user_name = ticket.get('first_name', 'Неизвестно')
            created_date = datetime.fromisoformat(ticket['created_at']).strftime("%d.%m")
            
            tickets_list += f"{i}. {priority_emoji}{status_emoji} <b>#{ticket['id']}</b>\n"
            tickets_list += f"   👤 {user_name} | 📅 {created_date}\n"
            tickets_list += f"   📝 {ticket['subject'][:50]}...\n\n"
        
        message_text = f"<b>{title}</b>\n\n{tickets_list}"
        
        if len(tickets) > 10:
            message_text += f"\n<i>И еще {len(tickets) - 10} обращений...</i>"
        
        await message.answer(
            message_text,
            reply_markup=get_agent_main_keyboard(),
            parse_mode="HTML"
        )
        
        # Отправляем inline меню для выбора обращения
        from keyboards.admin import get_admin_tickets_keyboard
        inline_keyboard = get_admin_tickets_keyboard(tickets[:10], "agent", user_role="agent")
        
        await message.answer(
            "🎯 <b>Выберите обращение для обработки:</b>",
            reply_markup=inline_keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_agent_main_keyboard(),
            parse_mode="HTML"
        )


async def show_agent_stats(message: Message):
    """Показать персональную статистику агента"""
    try:
        # Получаем общую статистику
        stats = await db.get_ticket_stats()
        
        # Здесь можно добавить персональную статистику агента
        # Пока показываем общую статистику
        
        stats_text = f"""
📊 <b>Статистика службы поддержки</b>

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
"""
        
        await message.answer(
            stats_text,
            reply_markup=get_agent_main_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_agent_main_keyboard(),
            parse_mode="HTML"
        )


# ===== ОБРАБОТЧИКИ INLINE CALLBACK =====
# 
# Обработчик admin_ticket_ перенесен в handlers/admin.py 
# для унификации обработки обращений админами и агентами


# ===== ОБРАБОТКА ОТВЕТОВ И ДЕЙСТВИЙ =====

@router.message(F.text == "💬 Ответить", AdminStates.waiting_response)
async def handle_agent_response_button(message: Message, state: FSMContext):
    """Обработка кнопки ответа агентом"""
    if not await check_agent_or_admin(message.from_user.id):
        await message.answer(PERMISSION_DENIED, reply_markup=get_client_main_keyboard())
        return
    
    await message.answer(
        "💬 <b>Быстрые ответы</b>\n\n"
        "Выберите подходящий ответ или напишите свой:",
        reply_markup=get_quick_responses_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_search)
async def process_agent_search(message: Message, state: FSMContext):
    """Обработка поиска обращения агентом"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Поиск отменен.",
            reply_markup=get_agent_main_keyboard()
        )
        return
    
    try:
        ticket_id = int(message.text.strip())
        ticket = await db.get_ticket(ticket_id)
        
        if not ticket:
            await message.answer(
                f"❌ Обращение #{ticket_id} не найдено.",
                reply_markup=get_agent_main_keyboard()
            )
            await state.clear()
            return
        
        # Показываем найденное обращение
        await show_ticket_for_agent(message, ticket)
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Введите корректный номер обращения (только цифры).",
            reply_markup=get_cancel_keyboard()
        )


async def show_ticket_for_agent(message: Message, ticket: dict):
    """Показать обращение агенту"""
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
{ticket['description'][:200]}...
"""
        
        await message.answer(
            details_text,
            reply_markup=get_agent_main_keyboard(),
            parse_mode="HTML"
        )
        
        # Если обращение можно обработать, показываем действия
        if ticket['status'] in ['new', 'in_progress', 'waiting_response']:
            from keyboards.admin import get_admin_ticket_actions
            await message.answer(
                "🎯 <b>Доступные действия:</b>",
                reply_markup=get_admin_ticket_actions(
                    ticket['id'], 
                    ticket['status'],
                    ticket.get('assigned_admin'),
                    message.from_user.id,
                    user_role='agent'
                ),
                parse_mode="HTML"
            )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_agent_main_keyboard()
        )


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

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