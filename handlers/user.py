"""Обработчики для пользователей"""

import math
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from keyboards.user import (
    get_main_menu, get_ticket_categories, get_cancel_keyboard,
    get_my_tickets_keyboard, get_ticket_details_keyboard,
    get_faq_keyboard, get_faq_item_keyboard, get_ticket_created_keyboard
)
from keyboards.reply import (
    get_client_main_keyboard, get_ticket_categories_keyboard,
    get_cancel_keyboard as get_reply_cancel_keyboard
)
from database import db
from utils.texts import (
    NEW_TICKET_MESSAGE, TICKET_CATEGORIES, TICKET_SUBJECT_MESSAGE,
    TICKET_DESCRIPTION_MESSAGE, TICKET_CREATED_MESSAGE, MY_TICKETS_MESSAGE,
    NO_TICKETS_MESSAGE, TICKET_DETAILS_MESSAGE, TICKET_STATUSES,
    FAQ_MESSAGE, FAQ_ITEMS, PLEASE_WAIT, ERROR_MESSAGE, TICKET_NOT_FOUND,
    CONTACTS_MESSAGE, CANCEL_MESSAGE
)
from handlers.common import TicketStates
from config import MAX_TICKET_TEXT_LENGTH, TICKETS_PER_PAGE


router = Router()


# ===== ОБРАБОТЧИКИ REPLY КНОПОК КЛИЕНТА =====

@router.message(F.text == "📝 Создать обращение", StateFilter(None))
async def handle_new_ticket_button(message: Message, state: FSMContext):
    """Обработка кнопки создания обращения"""
    await start_new_ticket_process(message, state)


@router.message(F.text == "📋 Мои обращения", StateFilter(None))
async def handle_my_tickets_button(message: Message):
    """Обработка кнопки просмотра обращений"""
    await show_user_tickets_process(message, 0)


@router.message(F.text == "❓ FAQ", StateFilter(None))
async def handle_faq_button(message: Message):
    """Обработка кнопки FAQ"""
    user_role = await db.get_user_role(message.from_user.id)
    
    # Выбираем нужную клавиатуру в зависимости от роли
    if user_role == 'admin':
        from keyboards.reply import get_admin_main_keyboard
        keyboard = get_admin_main_keyboard()
    elif user_role == 'agent':
        from keyboards.reply import get_agent_main_keyboard
        keyboard = get_agent_main_keyboard(show_admin_return=False)
    else:
        from keyboards.reply import get_client_keyboard_for_user
        keyboard = await get_client_keyboard_for_user(message.from_user.id)
    
    await message.answer(
        FAQ_MESSAGE,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Отправляем inline клавиатуру для выбора вопроса
    from keyboards.user import get_faq_keyboard
    await message.answer(
        "🔍 <b>Выберите интересующий вопрос:</b>",
        reply_markup=get_faq_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "📞 Контакты", StateFilter(None))
async def handle_contacts_button(message: Message):
    """Обработка кнопки контактов"""
    user_role = await db.get_user_role(message.from_user.id)
    
    # Выбираем нужную клавиатуру в зависимости от роли
    if user_role == 'admin':
        from keyboards.reply import get_admin_main_keyboard
        keyboard = get_admin_main_keyboard()
    elif user_role == 'agent':
        from keyboards.reply import get_agent_main_keyboard
        keyboard = get_agent_main_keyboard(show_admin_return=(user_role == 'admin'))
    else:
        from keyboards.reply import get_client_keyboard_for_user
        keyboard = await get_client_keyboard_for_user(message.from_user.id)
    
    await message.answer(
        CONTACTS_MESSAGE,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

async def start_new_ticket_process(message: Message, state: FSMContext):
    """Начать создание нового обращения"""
    await message.answer(
        NEW_TICKET_MESSAGE,
        reply_markup=get_ticket_categories_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(TicketStates.waiting_category)


async def show_user_tickets_process(message: Message, page: int = 0):
    """Показать обращения пользователя"""
    try:
        tickets = await db.get_user_tickets(
            message.from_user.id, 
            limit=TICKETS_PER_PAGE, 
            offset=page * TICKETS_PER_PAGE
        )
        
        if not tickets and page == 0:
            await message.answer(
                NO_TICKETS_MESSAGE + "\n\n<i>Используйте кнопку выше для создания обращения.</i>",
                reply_markup=get_client_main_keyboard(),
                parse_mode="HTML"
            )
            return
        
        # Подсчитываем общее количество страниц
        total_tickets = len(await db.get_user_tickets(message.from_user.id, limit=1000))
        total_pages = math.ceil(total_tickets / TICKETS_PER_PAGE)
        
        # Формируем список обращений
        tickets_list = ""
        for i, ticket in enumerate(tickets, 1):
            status_emoji = "🆕" if ticket['status'] == 'new' else "⏳" if ticket['status'] == 'in_progress' else "✅"
            created_date = datetime.fromisoformat(ticket['created_at']).strftime("%d.%m.%Y")
            tickets_list += f"{i + page * TICKETS_PER_PAGE}. {status_emoji} <b>#{ticket['id']}</b> - {ticket['subject'][:40]}...\n"
            tickets_list += f"   📅 {created_date} | {TICKET_STATUSES.get(ticket['status'], ticket['status'])}\n\n"
        
        message_text = MY_TICKETS_MESSAGE.format(tickets_list=tickets_list)
        
        await message.answer(
            message_text,
            reply_markup=get_client_main_keyboard(),
            parse_mode="HTML"
        )
        
        # Отправляем inline меню для выбора обращения
        await message.answer(
            "🎯 <b>Выберите обращение:</b>",
            reply_markup=get_my_tickets_keyboard(tickets, page, total_pages),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_client_main_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "new_ticket")
async def start_new_ticket(callback: CallbackQuery, state: FSMContext):
    """Начать создание нового обращения"""
    await callback.message.edit_text(
        NEW_TICKET_MESSAGE,
        reply_markup=get_ticket_categories(),
        parse_mode="HTML"
    )
    await state.set_state(TicketStates.waiting_category)
    await callback.answer()


@router.callback_query(F.data.startswith("category_"), TicketStates.waiting_category)
async def select_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории обращения"""
    category = callback.data.split("_", 1)[1]
    
    if category not in TICKET_CATEGORIES:
        await callback.answer("❌ Неверная категория", show_alert=True)
        return
    
    await state.update_data(category=category)
    
    await callback.message.edit_text(
        TICKET_SUBJECT_MESSAGE,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(TicketStates.waiting_subject)
    await callback.answer()


# Обработчики для Reply кнопок категорий
@router.message(F.text.in_(["🔧 Техподдержка", "💳 Оплата", "👤 Аккаунт", "💬 Общие вопросы", "😡 Жалоба", "💡 Предложение"]), TicketStates.waiting_category)
async def select_category_reply(message: Message, state: FSMContext):
    """Выбор категории через Reply кнопку"""
    # Маппинг текста кнопок на ID категорий
    category_mapping = {
        "🔧 Техподдержка": "technical",
        "💳 Оплата": "billing",
        "👤 Аккаунт": "account",
        "💬 Общие вопросы": "general",
        "😡 Жалоба": "complaint",
        "💡 Предложение": "suggestion"
    }
    
    category = category_mapping.get(message.text)
    if not category:
        await message.answer(
            "❌ Неверная категория. Выберите из предложенных вариантов.",
            reply_markup=get_ticket_categories_keyboard()
        )
        return
    
    await state.update_data(category=category)
    
    await message.answer(
        TICKET_SUBJECT_MESSAGE,
        reply_markup=get_reply_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(TicketStates.waiting_subject)


@router.message(F.text == "❌ Отмена", TicketStates.waiting_category)
async def cancel_category_selection(message: Message, state: FSMContext):
    """Отмена выбора категории"""
    await state.clear()
    
    user_role = await db.get_user_role(message.from_user.id)
    keyboard = get_client_main_keyboard() if user_role == 'client' else None
    
    await message.answer(
        CANCEL_MESSAGE,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(TicketStates.waiting_subject)
async def input_subject(message: Message, state: FSMContext):
    """Ввод темы обращения"""
    if message.text == "❌ Отмена":
        await state.clear()
        user_role = await db.get_user_role(message.from_user.id)
        keyboard = get_client_main_keyboard() if user_role == 'client' else None
        await message.answer(
            CANCEL_MESSAGE,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    subject = message.text.strip()
    
    if len(subject) < 5:
        await message.answer(
            "❌ Тема слишком короткая. Минимум 5 символов.",
            reply_markup=get_reply_cancel_keyboard()
        )
        return
    
    if len(subject) > 100:
        await message.answer(
            "❌ Тема слишком длинная. Максимум 100 символов.",
            reply_markup=get_reply_cancel_keyboard()
        )
        return
    
    await state.update_data(subject=subject)
    
    await message.answer(
        TICKET_DESCRIPTION_MESSAGE,
        reply_markup=get_reply_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(TicketStates.waiting_description)


@router.message(TicketStates.waiting_description)
async def input_description(message: Message, state: FSMContext):
    """Ввод описания обращения"""
    if message.text == "❌ Отмена":
        await state.clear()
        user_role = await db.get_user_role(message.from_user.id)
        keyboard = get_client_main_keyboard() if user_role == 'client' else None
        await message.answer(
            CANCEL_MESSAGE,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    description = message.text.strip()
    
    if len(description) < 10:
        await message.answer(
            "❌ Описание слишком короткое. Минимум 10 символов.",
            reply_markup=get_reply_cancel_keyboard()
        )
        return
    
    if len(description) > MAX_TICKET_TEXT_LENGTH:
        await message.answer(
            f"❌ Описание слишком длинное. Максимум {MAX_TICKET_TEXT_LENGTH} символов.",
            reply_markup=get_reply_cancel_keyboard()
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    category = data.get('category')
    subject = data.get('subject')
    
    try:
        # Создаем обращение
        ticket_id = await db.create_ticket(
            user_id=message.from_user.id,
            category=category,
            subject=subject,
            description=description
        )
        
        # Очищаем состояние
        await state.clear()
        
        # Отправляем подтверждение с Reply клавиатурой
        category_name = TICKET_CATEGORIES.get(category, category)
        success_message = TICKET_CREATED_MESSAGE.format(
            ticket_id=ticket_id,
            category=category_name,
            subject=subject
        )
        
        user_role = await db.get_user_role(message.from_user.id)
        
        # Выбираем нужную клавиатуру в зависимости от роли
        if user_role == 'admin':
            from keyboards.reply import get_admin_main_keyboard
            keyboard = get_admin_main_keyboard()
        elif user_role == 'agent':
            from keyboards.reply import get_agent_main_keyboard
            keyboard = get_agent_main_keyboard()
        else:
            keyboard = get_client_main_keyboard()
        
        await message.answer(
            success_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # Отправляем inline меню для действий с обращением
        await message.answer(
            "🎯 <b>Действия с обращением:</b>",
            reply_markup=get_ticket_created_keyboard(ticket_id),
            parse_mode="HTML"
        )
        
        # Уведомляем админов и агентов о новом обращении
        await notify_support_new_ticket(ticket_id, message.from_user.first_name or "Пользователь")
        
    except Exception as e:
        user_role = await db.get_user_role(message.from_user.id)
        
        # Выбираем нужную клавиатуру в зависимости от роли
        if user_role == 'admin':
            from keyboards.reply import get_admin_main_keyboard
            keyboard = get_admin_main_keyboard()
        elif user_role == 'agent':
            from keyboards.reply import get_agent_main_keyboard
            keyboard = get_agent_main_keyboard()
        else:
            keyboard = get_client_main_keyboard()
            
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await state.clear()


@router.callback_query(F.data == "my_tickets")
async def show_my_tickets(callback: CallbackQuery):
    """Показать обращения пользователя"""
    await show_user_tickets_page(callback, 0)


@router.callback_query(F.data.startswith("tickets_page_"))
async def show_tickets_page(callback: CallbackQuery):
    """Показать страницу обращений"""
    page = int(callback.data.split("_")[-1])
    await show_user_tickets_page(callback, page)


async def show_user_tickets_page(callback: CallbackQuery, page: int = 0):
    """Показать страницу с обращениями пользователя"""
    try:
        tickets = await db.get_user_tickets(
            callback.from_user.id, 
            limit=TICKETS_PER_PAGE, 
            offset=page * TICKETS_PER_PAGE
        )
        
        if not tickets and page == 0:
            await callback.message.edit_text(
                NO_TICKETS_MESSAGE,
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        # Подсчитываем общее количество страниц
        total_tickets = len(await db.get_user_tickets(callback.from_user.id, limit=1000))
        total_pages = math.ceil(total_tickets / TICKETS_PER_PAGE)
        
        # Формируем список обращений
        tickets_list = ""
        for i, ticket in enumerate(tickets, 1):
            status_emoji = "🆕" if ticket['status'] == 'new' else "⏳" if ticket['status'] == 'in_progress' else "✅"
            created_date = datetime.fromisoformat(ticket['created_at']).strftime("%d.%m.%Y")
            tickets_list += f"{i + page * TICKETS_PER_PAGE}. {status_emoji} <b>#{ticket['id']}</b> - {ticket['subject'][:40]}...\n"
            tickets_list += f"   📅 {created_date} | {TICKET_STATUSES.get(ticket['status'], ticket['status'])}\n\n"
        
        message_text = MY_TICKETS_MESSAGE.format(tickets_list=tickets_list)
        
        await callback.message.edit_text(
            message_text,
            reply_markup=get_my_tickets_keyboard(tickets, page, total_pages),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        await callback.message.edit_text(
            ERROR_MESSAGE,
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data.startswith("ticket_"))
async def show_ticket_details(callback: CallbackQuery):
    """Показать детали обращения"""
    try:
        ticket_id = int(callback.data.split("_")[1])
        ticket = await db.get_ticket(ticket_id)
        
        if not ticket or ticket['user_id'] != callback.from_user.id:
            await callback.answer(TICKET_NOT_FOUND, show_alert=True)
            return
        
        # Получаем сообщения обращения
        messages = await db.get_ticket_messages(ticket_id)
        
        # Формируем информацию о сообщениях
        messages_info = ""
        if messages:
            messages_info = f"\n<b>💬 Сообщения ({len(messages)}):</b>\n"
            for msg in messages[-3:]:  # Показываем последние 3 сообщения
                sender = "👨‍💼 Поддержка" if msg['is_admin'] else "👤 Вы"
                msg_date = datetime.fromisoformat(msg['created_at']).strftime("%d.%m %H:%M")
                messages_info += f"• {sender} ({msg_date}): {msg['message'][:100]}...\n"
        
        # Форматируем даты
        created_at = datetime.fromisoformat(ticket['created_at']).strftime("%d.%m.%Y %H:%M")
        updated_at = datetime.fromisoformat(ticket['updated_at']).strftime("%d.%m.%Y %H:%M")
        
        status_emoji = "🆕" if ticket['status'] == 'new' else "⏳" if ticket['status'] == 'in_progress' else "✅"
        category_name = TICKET_CATEGORIES.get(ticket['category'], ticket['category'])
        status_name = TICKET_STATUSES.get(ticket['status'], ticket['status'])
        
        details_text = TICKET_DETAILS_MESSAGE.format(
            ticket_id=ticket_id,
            subject=ticket['subject'],
            category=category_name,
            status_emoji=status_emoji,
            status=status_name,
            created_at=created_at,
            updated_at=updated_at,
            description=ticket['description'],
            messages_info=messages_info
        )
        
        user_can_respond = ticket['status'] in ['new', 'in_progress', 'waiting_response']
        
        await callback.message.edit_text(
            details_text,
            reply_markup=get_ticket_details_keyboard(ticket_id, ticket['status'], user_can_respond),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except ValueError:
        await callback.answer("❌ Неверный ID обращения", show_alert=True)
    except Exception as e:
        await callback.answer("❌ Ошибка при загрузке обращения", show_alert=True)


@router.callback_query(F.data.startswith("respond_ticket_"))
async def start_ticket_response(callback: CallbackQuery, state: FSMContext):
    """Начать ответ на обращение"""
    ticket_id = int(callback.data.split("_")[-1])
    
    await state.update_data(responding_ticket_id=ticket_id)
    await state.set_state(TicketStates.waiting_response)
    
    await callback.message.edit_text(
        f"💬 <b>Добавить сообщение к обращению #{ticket_id}</b>\n\n"
        "Напишите ваше сообщение:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(TicketStates.waiting_response)
async def add_ticket_response(message: Message, state: FSMContext):
    """Добавить ответ к обращению"""
    data = await state.get_data()
    ticket_id = data.get('responding_ticket_id')
    
    if not ticket_id:
        await state.clear()
        await message.answer("❌ Ошибка: не найдено обращение", reply_markup=get_main_menu())
        return
    
    response_text = message.text.strip()
    
    if len(response_text) < 5:
        await message.answer(
            "❌ Сообщение слишком короткое. Минимум 5 символов.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    if len(response_text) > MAX_TICKET_TEXT_LENGTH:
        await message.answer(
            f"❌ Сообщение слишком длинное. Максимум {MAX_TICKET_TEXT_LENGTH} символов.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    try:
        # Добавляем сообщение
        await db.add_ticket_message(ticket_id, message.from_user.id, response_text, False)
        
        # Обновляем статус обращения
        ticket = await db.get_ticket(ticket_id)
        if ticket:
            # Если обращение в работе или новое, переводим в ожидание ответа
            if ticket['status'] in ['in_progress', 'new']:
                await db.update_ticket_status(ticket_id, 'waiting_response')
            # Если было закрыто, переоткрываем
            elif ticket['status'] in ['resolved', 'closed']:
                await db.update_ticket_status(ticket_id, 'waiting_response')
        
        await state.clear()
        
        await message.answer(
            f"✅ <b>Сообщение добавлено к обращению #{ticket_id}</b>\n\n"
            "Специалист поддержки получит уведомление и ответит в ближайшее время.",
            reply_markup=get_ticket_details_keyboard(ticket_id, ticket['status'] if ticket else 'new'),
            parse_mode="HTML"
        )
        
        # Уведомляем службу поддержки о новом сообщении
        await notify_support_ticket_update(ticket_id, message.from_user.first_name or "Пользователь")
        
    except Exception as e:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        await state.clear()


@router.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(callback: CallbackQuery):
    """Закрыть обращение пользователем"""
    ticket_id = int(callback.data.split("_")[-1])
    
    try:
        ticket = await db.get_ticket(ticket_id)
        
        if not ticket or ticket['user_id'] != callback.from_user.id:
            await callback.answer(TICKET_NOT_FOUND, show_alert=True)
            return
        
        if ticket['status'] != 'resolved':
            await callback.answer("❌ Можно закрыть только решенные обращения", show_alert=True)
            return
        
        await db.update_ticket_status(ticket_id, 'closed')
        
        await callback.message.edit_text(
            f"✅ <b>Обращение #{ticket_id} закрыто</b>\n\n"
            "Спасибо за обращение! Мы рады, что смогли помочь.",
            reply_markup=get_my_tickets_keyboard([], 0, 1),  # Вернуться к списку
            parse_mode="HTML"
        )
        await callback.answer("✅ Обращение закрыто!")
        
    except Exception as e:
        await callback.answer("❌ Ошибка при закрытии обращения", show_alert=True)


@router.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery):
    """Показать FAQ"""
    await callback.message.edit_text(
        FAQ_MESSAGE,
        reply_markup=get_faq_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "show_my_tickets_inline")
async def show_my_tickets_inline(callback: CallbackQuery):
    """Показать обращения пользователя через inline"""
    try:
        tickets = await db.get_user_tickets(
            callback.from_user.id, 
            limit=TICKETS_PER_PAGE, 
            offset=0
        )
        
        if not tickets:
            await callback.message.edit_text(
                NO_TICKETS_MESSAGE,
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        # Подсчитываем общее количество страниц
        total_tickets = len(await db.get_user_tickets(callback.from_user.id, limit=1000))
        total_pages = math.ceil(total_tickets / TICKETS_PER_PAGE)
        
        # Формируем список обращений
        tickets_list = ""
        for i, ticket in enumerate(tickets, 1):
            status_emoji = "🆕" if ticket['status'] == 'new' else "⏳" if ticket['status'] == 'in_progress' else "✅"
            created_date = datetime.fromisoformat(ticket['created_at']).strftime("%d.%m.%Y")
            tickets_list += f"{i}. {status_emoji} <b>#{ticket['id']}</b> - {ticket['subject'][:40]}...\n"
            tickets_list += f"   📅 {created_date} | {TICKET_STATUSES.get(ticket['status'], ticket['status'])}\n\n"
        
        message_text = MY_TICKETS_MESSAGE.format(tickets_list=tickets_list)
        
        await callback.message.edit_text(
            message_text,
            reply_markup=get_my_tickets_keyboard(tickets, 0, total_pages),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        await callback.message.edit_text(
            ERROR_MESSAGE,
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data.startswith("faq_"))
async def show_faq_item(callback: CallbackQuery):
    """Показать элемент FAQ"""
    faq_id = callback.data.split("_", 1)[1]
    
    if faq_id not in FAQ_ITEMS:
        await callback.answer("❌ FAQ не найден", show_alert=True)
        return
    
    faq_item = FAQ_ITEMS[faq_id]
    
    await callback.message.edit_text(
        faq_item['answer'],
        reply_markup=get_faq_item_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


async def notify_support_new_ticket(ticket_id: int, user_name: str):
    """Уведомить службу поддержки о новом обращении"""
    from config import ADMINS, AGENTS
    from bot import bot
    
    # Получаем информацию об обращении
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        return
    
    category_name = TICKET_CATEGORIES.get(ticket['category'], ticket['category'])
    
    notification_text = f"""
🆕 <b>Новое обращение #{ticket_id}</b>

👤 <b>От:</b> {user_name}
📂 <b>Категория:</b> {category_name}
📝 <b>Тема:</b> {ticket['subject'][:50]}...
⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

Требует обработки.
"""
    
    # Создаем inline клавиатуру для быстрых действий
    from keyboards.admin import get_quick_ticket_actions
    quick_actions = get_quick_ticket_actions(ticket_id, "new_ticket")
    
    # Уведомляем всех администраторов
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                admin_id,
                notification_text + "\n<i>👆 Используйте кнопки для быстрых действий</i>",
                reply_markup=quick_actions,
                parse_mode="HTML"
            )
        except:
            continue
    
    # Уведомляем всех агентов
    for agent_id in AGENTS:
        try:
            await bot.send_message(
                agent_id,
                notification_text + "\n<i>👆 Используйте кнопки для быстрых действий</i>",
                reply_markup=quick_actions,
                parse_mode="HTML"
            )
        except:
            continue


async def notify_support_ticket_update(ticket_id: int, user_name: str):
    """Уведомить службу поддержки об обновлении обращения"""
    from config import ADMINS, AGENTS
    from bot import bot
    from keyboards.admin import get_quick_ticket_actions
    
    # Получаем детали обращения
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        return
    
    notification_text = f"""
💬 <b>Новое сообщение в обращении #{ticket_id}</b>

👤 <b>От:</b> {user_name}
📝 <b>Тема:</b> {ticket['subject'][:40]}...
📊 <b>Статус:</b> {TICKET_STATUSES.get(ticket['status'], ticket['status'])}
⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

Требует ответа.
"""
    
    # Создаем inline клавиатуру для быстрых действий
    quick_actions = get_quick_ticket_actions(ticket_id, "notification")
    
    # Уведомляем администраторов
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                admin_id,
                notification_text + "\n<i>👆 Используйте кнопки для быстрого ответа</i>",
                reply_markup=quick_actions,
                parse_mode="HTML"
            )
        except:
            continue
    
    # Уведомляем агентов
    for agent_id in AGENTS:
        try:
            await bot.send_message(
                agent_id,
                notification_text + "\n<i>👆 Используйте кнопки для быстрого ответа</i>",
                reply_markup=quick_actions,
                parse_mode="HTML"
            )
        except:
            continue