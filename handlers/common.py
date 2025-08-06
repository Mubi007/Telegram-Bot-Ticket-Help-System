"""Общие обработчики"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.user import get_main_menu, get_contacts_keyboard
from keyboards.admin import get_admin_panel
from keyboards.reply import (
    get_client_main_keyboard, get_agent_main_keyboard, get_admin_main_keyboard,
    remove_keyboard, get_cancel_keyboard
)
from database import db
from utils.texts import START_MESSAGE, CONTACTS_MESSAGE, CANCEL_MESSAGE
from config import ADMINS, AGENTS, USER_ROLES


router = Router()


class TicketStates(StatesGroup):
    """Состояния для создания обращения"""
    waiting_category = State()
    waiting_subject = State() 
    waiting_description = State()
    waiting_response = State()


class AdminStates(StatesGroup):
    """Состояния для админа"""
    waiting_response = State()
    waiting_search = State()
    waiting_admin_id = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start"""
    await state.clear()
    
    # Добавляем пользователя в базу данных
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Получаем роль пользователя из базы данных
    user_role = await db.get_user_role(message.from_user.id)
    
    # Определяем правильную роль из конфигов
    if message.from_user.id in ADMINS:
        correct_role = 'admin'
    elif message.from_user.id in AGENTS:
        correct_role = 'agent'
    else:
        correct_role = 'client'
    
    # Если пользователя нет в БД или роль неправильная, обновляем
    if not user_role or user_role != correct_role:
        user_role = correct_role
        # Устанавливаем/обновляем роль в базе данных
        await db.set_user_role(message.from_user.id, user_role)
    
    # Каждая роль в СВОЁМ интерфейсе
    if user_role == 'admin':
        # Админ в админ панели
        role_name = USER_ROLES.get(user_role, 'Администратор')
        welcome_text = f"{START_MESSAGE}\n\n👤 <b>Режим:</b> {role_name}"
        reply_keyboard = get_admin_main_keyboard()
        inline_keyboard = get_admin_panel()
    elif user_role == 'agent':
        # Агент в агентской панели (БЕЗ админских функций)
        role_name = USER_ROLES.get(user_role, 'Агент поддержки')
        welcome_text = f"{START_MESSAGE}\n\n👤 <b>Режим:</b> {role_name}"
        reply_keyboard = get_agent_main_keyboard(show_admin_return=False)  # БЕЗ кнопки админки
        from keyboards.admin import get_agent_panel
        inline_keyboard = get_agent_panel()
    else:
        # Клиент в клиентском интерфейсе
        welcome_text = START_MESSAGE
        reply_keyboard = get_client_main_keyboard()  # Упрощаем
        inline_keyboard = get_main_menu()
    
    await message.answer(
        welcome_text,
        reply_markup=reply_keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext):
    """Показать главное меню соответственно роли"""
    await state.clear()
    
    user_role = await db.get_user_role(callback.from_user.id)
    
    if user_role == 'admin':
        # Админ возвращается в админ панель
        inline_keyboard = get_admin_panel()
        text = f"{START_MESSAGE}\n\n👤 <b>Режим:</b> Администратор"
    elif user_role == 'agent':
        # Агент возвращается в агентскую панель
        from keyboards.admin import get_agent_panel
        inline_keyboard = get_agent_panel()
        text = f"{START_MESSAGE}\n\n👤 <b>Режим:</b> Агент поддержки"
    else:
        # Клиент в обычное меню
        inline_keyboard = get_main_menu()
        text = START_MESSAGE
    
    await callback.message.edit_text(
        text,
        reply_markup=inline_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery, state: FSMContext):
    """Показать админ панель"""
    await state.clear()
    
    # Проверяем права агента или админа
    user_role = await db.get_user_role(callback.from_user.id)
    if user_role not in ['agent', 'admin']:
        from utils.texts import PERMISSION_DENIED
        await callback.answer(PERMISSION_DENIED, show_alert=True)
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
    await callback.message.edit_text(
        ADMIN_PANEL_MESSAGE.format(stats=stats_text),
        reply_markup=get_admin_panel(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery):
    """Показать контакты"""
    await callback.message.edit_text(
        CONTACTS_MESSAGE,
        reply_markup=get_contacts_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отменить текущее действие"""
    await state.clear()
    await callback.message.edit_text(
        CANCEL_MESSAGE,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "refresh")
async def refresh_menu(callback: CallbackQuery):
    """Обновить главное меню"""
    await callback.message.edit_text(
        START_MESSAGE,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer("🔄 Обновлено!")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда помощи"""
    help_text = """
<b>🤖 Справка по боту поддержки</b>

<b>Основные команды:</b>
/start - Запуск бота
/help - Эта справка

<b>Возможности:</b>
📝 Создание обращений в поддержку
📋 Просмотр статуса обращений
❓ Часто задаваемые вопросы
📞 Контактная информация

<b>Как создать обращение:</b>
1. Нажмите "Создать обращение"
2. Выберите категорию
3. Укажите тему
4. Опишите проблему подробно

<b>Статусы обращений:</b>
🆕 Новое - обращение только создано
⏳ В работе - специалист работает над проблемой
⏰ Ожидает ответа - нужна информация от вас
✅ Решено - проблема решена
🔒 Закрыто - обращение закрыто

💡 <i>Чем подробнее вы опишете проблему, тем быстрее мы сможем помочь!</i>
"""
    
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_menu())


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Команда для админов"""
    user_role = await db.get_user_role(message.from_user.id)
    if user_role != 'admin':
        await message.answer("🚫 У вас нет прав администратора.")
        return
    
    # Получаем статистику
    stats = await db.get_ticket_stats()
    
    stats_text = f"""
📊 <b>Статистика обращений:</b>
• Всего: {stats.get('total', 0)}
• Новых: {stats.get('status_new', 0)}
• В работе: {stats.get('status_in_progress', 0)}
• Решено: {stats.get('status_resolved', 0)}
"""
    
    from utils.texts import ADMIN_PANEL_MESSAGE
    await message.answer(
        ADMIN_PANEL_MESSAGE.format(stats=stats_text),
        reply_markup=get_admin_panel(),
        parse_mode="HTML"
    )


# ===== ОБРАБОТЧИКИ REPLY КНОПОК =====

@router.message(F.text.in_(["🏠 Главное меню", "🔄 Обновить"]))
async def handle_main_menu_button(message: Message, state: FSMContext):
    """Обработка кнопки главного меню"""
    await state.clear()
    
    user_role = await db.get_user_role(message.from_user.id)
    
    # Каждая роль в СВОЁМ интерфейсе 
    if user_role == 'admin':
        # Админ в админ панели
        role_name = USER_ROLES.get(user_role, 'Администратор')
        welcome_text = f"{START_MESSAGE}\n\n👤 <b>Режим:</b> {role_name}"
        reply_keyboard = get_admin_main_keyboard()
        inline_keyboard = get_admin_panel()
    elif user_role == 'agent':
        # Агент в агентской панели (БЕЗ админских функций)
        role_name = USER_ROLES.get(user_role, 'Агент поддержки') 
        welcome_text = f"{START_MESSAGE}\n\n👤 <b>Режим:</b> {role_name}"
        reply_keyboard = get_agent_main_keyboard(show_admin_return=False)  # БЕЗ кнопки админки
        from keyboards.admin import get_agent_panel
        inline_keyboard = get_agent_panel()
    else:
        # Клиент в клиентском интерфейсе
        welcome_text = START_MESSAGE
        reply_keyboard = get_client_main_keyboard()  # Упрощаем без дополнительных проверок
        inline_keyboard = get_main_menu()
    
    await message.answer(
        welcome_text,
        reply_markup=reply_keyboard,
        parse_mode="HTML"
    )


@router.message(F.text == "ℹ️ Помощь")
async def handle_help_button(message: Message):
    """Обработка кнопки помощи"""
    help_text = """
<b>🤖 Справка по боту поддержки</b>

<b>Основные команды:</b>
/start - Запуск бота
/help - Эта справка  
/role - Просмотр текущей роли

<b>Возможности для клиентов:</b>
📝 Создание обращений в поддержку
📋 Просмотр статуса обращений
❓ Часто задаваемые вопросы
📞 Контактная информация

<b>Возможности для агентов:</b>
🎫 Обработка обращений клиентов
📊 Просмотр статистики работы
🔍 Поиск по обращениям

<b>Возможности для админов:</b>
👥 Управление пользователями и агентами
📈 Полная статистика системы
⚙️ Настройки бота

💡 <i>Используйте кнопки для удобной навигации!</i>
"""
    
    user_role = await db.get_user_role(message.from_user.id)
    if user_role == 'admin':
        keyboard = get_admin_main_keyboard()
    elif user_role == 'agent':
        keyboard = get_agent_main_keyboard()
    else:
        keyboard = get_client_main_keyboard()
    
    await message.answer(help_text, parse_mode="HTML", reply_markup=keyboard)


# УБРАЛИ ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ - каждая роль работает в своём интерфейсе


@router.message(Command("role"))
async def cmd_role(message: Message):
    """Показать информацию о текущей роли (только для персонала)"""
    user_role = await db.get_user_role(message.from_user.id)
    
    if user_role == 'client':
        # Для клиентов показываем справку вместо роли
        help_text = """
<b>🤖 Справка по боту поддержки</b>

<b>Ваши возможности:</b>
• 📝 Создание обращений в поддержку
• 📋 Просмотр статуса ваших обращений  
• 💬 Переписка со службой поддержки
• ❓ Поиск ответов в FAQ
• 📞 Просмотр контактной информации

<b>Как создать обращение:</b>
1. Нажмите "📝 Создать обращение"
2. Выберите категорию вопроса
3. Укажите тему проблемы
4. Опишите ситуацию подробно

💡 <i>Чем подробнее вы опишете проблему, тем быстрее мы сможем помочь!</i>
"""
        keyboard = get_client_main_keyboard()
    else:
        # Для персонала показываем информацию о роли
        role_name = USER_ROLES.get(user_role, 'Неизвестно')
        
        permissions_text = ""
        if user_role == 'agent':
            permissions_text = """
<b>Ваши возможности:</b>
• Обработка обращений клиентов
• Изменение статусов обращений
• Ответы клиентам
• Просмотр статистики работы
• Все возможности клиента
"""
        elif user_role == 'admin':
            permissions_text = """
<b>Ваши возможности:</b>
• Полное управление системой
• Назначение и удаление агентов
• Просмотр полной статистики
• Управление настройками
• Все возможности агентов и клиентов
"""
        
        help_text = f"""
👤 <b>Информация о роли</b>

<b>Текущий режим:</b> {role_name}
<b>ID сотрудника:</b> {message.from_user.id}

{permissions_text}

<i>Используйте кнопки меню для переключения между режимами работы.</i>
"""
        
        keyboard = get_admin_main_keyboard() if user_role == 'admin' else get_agent_main_keyboard()
    
    await message.answer(help_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(StateFilter(None))
async def unknown_message(message: Message):
    """Обработка неизвестных сообщений"""
    user_role = await db.get_user_role(message.from_user.id)
    
    if user_role == 'admin':
        keyboard = get_admin_main_keyboard()
    elif user_role == 'agent':
        keyboard = get_agent_main_keyboard()
    else:
        keyboard = get_client_main_keyboard()
    
    await message.answer(
        "🤔 Я не понимаю эту команду. Используйте кнопки меню для навигации:",
        reply_markup=keyboard
    )