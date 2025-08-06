"""Дополнительные callback обработчики для админов"""

import asyncio
import json
import csv
import io
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from database import db
from keyboards.admin import (
    get_admin_manage_keyboard, get_admin_settings_keyboard, 
    get_admin_export_keyboard, get_admin_panel
)
from utils.texts import PERMISSION_DENIED

router = Router()

async def check_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    user_role = await db.get_user_role(user_id)
    return user_role == 'admin'


# ===== УПРАВЛЕНИЕ =====

@router.callback_query(F.data == "admin_manage")
async def show_admin_manage(callback: CallbackQuery):
    """Показать меню управления"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_manage_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_list_users")
async def list_users(callback: CallbackQuery):
    """Показать список пользователей"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        users = await db.get_all_users(limit=50)
        total_users = await db.count_total_users()
        
        text = f"👥 <b>Пользователи системы</b> (показано {len(users)} из {total_users})\n\n"
        
        for user in users:
            role_emoji = {"admin": "👑", "agent": "🛡️", "client": "👤"}.get(user['role'], "❓")
            status = "🟢" if user['is_active'] else "🔴"
            text += f"{role_emoji} {status} <b>{user.get('first_name', 'N/A')}</b> (@{user.get('username', 'N/A')})\n"
            text += f"   ID: <code>{user['user_id']}</code> | Роль: {user['role']}\n\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_manage_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer("❌ Ошибка при загрузке пользователей", show_alert=True)


@router.callback_query(F.data == "admin_roles_stats")
async def show_roles_stats(callback: CallbackQuery):
    """Статистика по ролям"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        admin_count = await db.count_users_by_role('admin')
        agent_count = await db.count_users_by_role('agent')
        client_count = await db.count_users_by_role('client')
        total = await db.count_total_users()
        
        text = f"""
📊 <b>Статистика по ролям</b>

👑 <b>Администраторы:</b> {admin_count}
🛡️ <b>Агенты:</b> {agent_count}
👤 <b>Клиенты:</b> {client_count}

📈 <b>Всего пользователей:</b> {total}
"""
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_manage_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer("❌ Ошибка при загрузке статистики", show_alert=True)


# ===== НАСТРОЙКИ =====

@router.callback_query(F.data == "admin_settings")
async def show_admin_settings(callback: CallbackQuery):
    """Показать настройки системы"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    text = """
⚙️ <b>Настройки системы</b>

<b>Текущие настройки:</b>
• Максимальный размер обращения: 1000 символов
• Обращений на страницу: 5
• Автоуведомления: Включены
• Время ответа: 24 часа

<b>Выберите раздел для настройки:</b>
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_settings_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_backup")
async def create_backup(callback: CallbackQuery):
    """Создать резервную копию"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        # Получаем все данные
        users = await db.get_all_users(limit=1000)
        tickets = await db.get_all_tickets(limit=1000)
        stats = await db.get_ticket_stats()
        
        backup_data = {
            "created_at": datetime.now().isoformat(),
            "users": users,
            "tickets": tickets,
            "stats": stats,
            "version": "1.0"
        }
        
        # Создаем JSON файл
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        # Отправляем файл
        filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file = BufferedInputFile(backup_json.encode('utf-8'), filename=filename)
        
        await callback.message.answer_document(
            file,
            caption=f"💾 <b>Резервная копия создана</b>\n\n"
                   f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                   f"👥 Пользователей: {len(users)}\n"
                   f"📋 Обращений: {len(tickets)}",
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Резервная копия создана")
        
    except Exception as e:
        await callback.answer("❌ Ошибка при создании резервной копии", show_alert=True)


# ===== ЭКСПОРТ =====

@router.callback_query(F.data == "admin_export")
async def show_export_menu(callback: CallbackQuery):
    """Показать меню экспорта"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    await callback.message.edit_text(
        "💾 <b>Экспорт данных</b>\n\n"
        "Выберите тип данных для экспорта:",
        reply_markup=get_admin_export_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_export_stats")
async def export_stats(callback: CallbackQuery):
    """Экспорт статистики"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        stats = await db.get_ticket_stats()
        admin_count = await db.count_users_by_role('admin')
        agent_count = await db.count_users_by_role('agent')
        client_count = await db.count_users_by_role('client')
        
        csv_data = io.StringIO()
        writer = csv.writer(csv_data)
        
        writer.writerow(['Метрика', 'Значение'])
        writer.writerow(['Всего обращений', stats.get('total', 0)])
        writer.writerow(['Новых обращений', stats.get('status_new', 0)])
        writer.writerow(['В работе', stats.get('status_in_progress', 0)])
        writer.writerow(['Ожидают ответа', stats.get('status_waiting_response', 0)])
        writer.writerow(['Решено', stats.get('status_resolved', 0)])
        writer.writerow(['Закрыто', stats.get('status_closed', 0)])
        writer.writerow(['Администраторов', admin_count])
        writer.writerow(['Агентов', agent_count])
        writer.writerow(['Клиентов', client_count])
        
        filename = f"statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file = BufferedInputFile(csv_data.getvalue().encode('utf-8'), filename=filename)
        
        await callback.message.answer_document(
            file,
            caption="📊 <b>Статистика экспортирована</b>",
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Статистика экспортирована")
        
    except Exception as e:
        await callback.answer("❌ Ошибка при экспорте статистики", show_alert=True)


@router.callback_query(F.data == "admin_export_tickets")
async def export_tickets(callback: CallbackQuery):
    """Экспорт обращений в CSV"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        tickets = await db.get_all_tickets(limit=1000)
        
        csv_data = io.StringIO()
        writer = csv.writer(csv_data)
        
        # Заголовки
        writer.writerow([
            'ID', 'User ID', 'Username', 'Category', 'Subject', 
            'Status', 'Priority', 'Created', 'Updated'
        ])
        
        # Данные
        for ticket in tickets:
            writer.writerow([
                ticket.get('id', ''),
                ticket.get('user_id', ''),
                ticket.get('username', ''),
                ticket.get('category', ''),
                ticket.get('subject', ''),
                ticket.get('status', ''),
                ticket.get('priority', ''),
                ticket.get('created_at', ''),
                ticket.get('updated_at', '')
            ])
        
        filename = f"tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file = BufferedInputFile(csv_data.getvalue().encode('utf-8'), filename=filename)
        
        await callback.message.answer_document(
            file,
            caption=f"📋 <b>Обращения экспортированы</b>\n\nВсего: {len(tickets)} обращений",
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Обращения экспортированы")
        
    except Exception as e:
        await callback.answer("❌ Ошибка при экспорте обращений", show_alert=True)


@router.callback_query(F.data == "admin_export_users")
async def export_users(callback: CallbackQuery):
    """Экспорт пользователей в CSV"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        users = await db.get_all_users(limit=1000)
        
        csv_data = io.StringIO()
        writer = csv.writer(csv_data)
        
        # Заголовки
        writer.writerow([
            'User ID', 'Username', 'First Name', 'Last Name', 
            'Role', 'Active', 'Created'
        ])
        
        # Данные
        for user in users:
            writer.writerow([
                user.get('user_id', ''),
                user.get('username', ''),
                user.get('first_name', ''),
                user.get('last_name', ''),
                user.get('role', ''),
                'Да' if user.get('is_active') else 'Нет',
                user.get('created_at', '')
            ])
        
        filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file = BufferedInputFile(csv_data.getvalue().encode('utf-8'), filename=filename)
        
        await callback.message.answer_document(
            file,
            caption=f"👥 <b>Пользователи экспортированы</b>\n\nВсего: {len(users)} пользователей",
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Пользователи экспортированы")
        
    except Exception as e:
        await callback.answer("❌ Ошибка при экспорте пользователей", show_alert=True)


@router.callback_query(F.data == "admin_export_report")
async def export_detailed_report(callback: CallbackQuery):
    """Экспорт подробного отчёта"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    try:
        # Получаем данные за последние 30 дней
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        stats = await db.get_ticket_stats()
        users = await db.get_all_users()
        
        report = f"""
ОТЧЁТ ПО РАБОТЕ СЛУЖБЫ ПОДДЕРЖКИ
Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}
Создан: {datetime.now().strftime('%d.%m.%Y %H:%M')}

=== ОБЩАЯ СТАТИСТИКА ===
Всего обращений: {stats.get('total', 0)}
Новых: {stats.get('status_new', 0)}
В работе: {stats.get('status_in_progress', 0)}
Ожидают ответа: {stats.get('status_waiting_response', 0)}
Решено: {stats.get('status_resolved', 0)}
Закрыто: {stats.get('status_closed', 0)}

=== ПОЛЬЗОВАТЕЛИ ===
Всего пользователей: {len(users)}
Администраторы: {len([u for u in users if u['role'] == 'admin'])}
Агенты: {len([u for u in users if u['role'] == 'agent'])}
Клиенты: {len([u for u in users if u['role'] == 'client'])}

=== ЭФФЕКТИВНОСТЬ ===
Решено обращений: {stats.get('status_resolved', 0)}
Процент решённых: {round(stats.get('status_resolved', 0) / max(stats.get('total', 1), 1) * 100, 1)}%
"""
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file = BufferedInputFile(report.encode('utf-8'), filename=filename)
        
        await callback.message.answer_document(
            file,
            caption="📈 <b>Подробный отчёт создан</b>",
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Отчёт создан")
        
    except Exception as e:
        await callback.answer("❌ Ошибка при создании отчёта", show_alert=True)


# ===== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ =====

@router.callback_query(F.data == "admin_change_role")
async def change_user_role(callback: CallbackQuery, state: FSMContext):
    """Начать процесс смены роли пользователя"""
    if not await check_admin(callback.from_user.id):
        await callback.answer(PERMISSION_DENIED, show_alert=True)
        return
    
    await callback.message.edit_text(
        "🔧 <b>Изменение роли пользователя</b>\n\n"
        "Отправьте ID пользователя для изменения роли:",
        parse_mode="HTML"
    )
    
    # Можно добавить FSM state для обработки ввода ID
    await callback.answer()