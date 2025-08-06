import aiosqlite
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from config import DATABASE_PATH


class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
    
    async def create_tables(self):
        """Создание таблиц в базе данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    role TEXT DEFAULT 'client',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица обращений в поддержку
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    subject TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'new',
                    priority TEXT DEFAULT 'medium',
                    assigned_admin INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (assigned_admin) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица сообщений в обращениях
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER,
                    user_id INTEGER,
                    message TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES tickets (id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            await db.commit()
    
    async def add_user(self, user_id: int, username: str = None, 
                      first_name: str = None, last_name: str = None):
        """Добавление пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name) 
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            await db.commit()
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM users WHERE user_id = ?', (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_user_role(self, user_id: int) -> str:
        """Получение роли пользователя"""
        user = await self.get_user(user_id)
        return user.get('role', 'client') if user else 'client'
    
    async def set_user_role(self, user_id: int, role: str):
        """Установка роли пользователя"""
        valid_roles = ['client', 'agent', 'admin']
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'UPDATE users SET role = ? WHERE user_id = ?',
                (role, user_id)
            )
            await db.commit()
    
    async def is_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь админом"""
        role = await self.get_user_role(user_id)
        return role == 'admin'
    
    async def is_agent_or_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь агентом или админом"""
        role = await self.get_user_role(user_id)
        return role in ['agent', 'admin']
    
    async def is_client(self, user_id: int) -> bool:
        """Проверка является ли пользователь клиентом"""
        role = await self.get_user_role(user_id)
        return role == 'client'
    
    async def set_admin(self, user_id: int, is_admin: bool = True):
        """Назначение пользователя админом (совместимость)"""
        role = 'admin' if is_admin else 'client'
        await self.set_user_role(user_id, role)
    
    async def get_agents(self) -> List[Dict[str, Any]]:
        """Получение списка агентов"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE role = 'agent' AND is_active = TRUE"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_admins(self) -> List[Dict[str, Any]]:
        """Получение списка администраторов"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE role = 'admin' AND is_active = TRUE"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def create_ticket(self, user_id: int, category: str, 
                           subject: str, description: str) -> int:
        """Создание нового обращения"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO tickets (user_id, category, subject, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, category, subject, description))
            await db.commit()
            return cursor.lastrowid
    
    async def get_user_tickets(self, user_id: int, limit: int = 10, 
                              offset: int = 0) -> List[Dict[str, Any]]:
        """Получение обращений пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM tickets 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Получение обращения по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM tickets WHERE id = ?', (ticket_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_ticket_status(self, ticket_id: int, status: str, 
                                  admin_id: int = None):
        """Обновление статуса обращения"""
        async with aiosqlite.connect(self.db_path) as db:
            if admin_id:
                await db.execute('''
                    UPDATE tickets 
                    SET status = ?, assigned_admin = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, admin_id, ticket_id))
            else:
                await db.execute('''
                    UPDATE tickets 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, ticket_id))
            await db.commit()
    
    async def add_ticket_message(self, ticket_id: int, user_id: int, 
                                message: str, is_admin: bool = False):
        """Добавление сообщения к обращению"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO ticket_messages (ticket_id, user_id, message, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (ticket_id, user_id, message, is_admin))
            await db.commit()
    
    async def get_ticket_messages(self, ticket_id: int) -> List[Dict[str, Any]]:
        """Получение сообщений обращения"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT tm.*, u.first_name, u.username
                FROM ticket_messages tm
                JOIN users u ON tm.user_id = u.user_id
                WHERE tm.ticket_id = ?
                ORDER BY tm.created_at ASC
            ''', (ticket_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_pending_tickets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение необработанных обращений для админов"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT t.*, u.first_name, u.username
                FROM tickets t
                JOIN users u ON t.user_id = u.user_id
                WHERE t.status IN ('new', 'in_progress')
                ORDER BY t.created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_ticket_stats(self) -> Dict[str, int]:
        """Получение статистики обращений"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Общее количество обращений
            cursor = await db.execute('SELECT COUNT(*) FROM tickets')
            stats['total'] = (await cursor.fetchone())[0]
            
            # По статусам
            cursor = await db.execute('''
                SELECT status, COUNT(*) 
                FROM tickets 
                GROUP BY status
            ''')
            status_counts = await cursor.fetchall()
            for status, count in status_counts:
                stats[f'status_{status}'] = count
            
            return stats
    
    async def update_ticket_priority(self, ticket_id: int, priority: str):
        """Обновление приоритета обращения"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE tickets 
                SET priority = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (priority, ticket_id))
            await db.commit()
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение списка всех пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM users 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def count_users_by_role(self, role: str) -> int:
        """Подсчет пользователей по роли"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT COUNT(*) FROM users WHERE role = ? AND is_active = TRUE',
                (role,)
            )
            return (await cursor.fetchone())[0]
    
    async def count_total_users(self) -> int:
        """Подсчет общего количества пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM users WHERE is_active = TRUE')
            return (await cursor.fetchone())[0]
    
    async def get_closed_tickets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение закрытых обращений"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT t.*, u.first_name, u.username
                FROM tickets t
                JOIN users u ON t.user_id = u.user_id
                WHERE t.status IN ('resolved', 'closed')
                ORDER BY t.updated_at DESC
                LIMIT ?
            ''', (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_all_tickets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить все обращения для экспорта"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT t.*, u.username, u.first_name, u.last_name
                FROM tickets t
                LEFT JOIN users u ON t.user_id = u.user_id
                ORDER BY t.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def block_user(self, user_id: int) -> bool:
        """Заблокировать пользователя"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE users 
                    SET is_active = FALSE 
                    WHERE user_id = ?
                ''', (user_id,))
                await db.commit()
            return True
        except Exception:
            return False

    async def unblock_user(self, user_id: int) -> bool:
        """Разблокировать пользователя"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE users 
                    SET is_active = TRUE 
                    WHERE user_id = ?
                ''', (user_id,))
                await db.commit()
            return True
        except Exception:
            return False


# Глобальный экземпляр базы данных
db = Database()