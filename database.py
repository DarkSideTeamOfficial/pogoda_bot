#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с базой данных подписок пользователей
"""

import sqlite3
import json
from datetime import datetime, time
from typing import List, Dict, Optional

class UserDatabase:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    city TEXT,
                    timezone TEXT DEFAULT 'Europe/Moscow',
                    notification_time TEXT DEFAULT '08:00',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Создаем таблицу настроек уведомлений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_settings (
                    user_id INTEGER PRIMARY KEY,
                    morning_time TEXT DEFAULT '08:00',
                    evening_time TEXT DEFAULT '20:00',
                    send_morning BOOLEAN DEFAULT 1,
                    send_evening BOOLEAN DEFAULT 0,
                    weather_type TEXT DEFAULT 'brief',  -- 'brief' или 'detailed'
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 last_name: str = None, city: str = None) -> bool:
        """Добавление нового пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, city, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, username, first_name, last_name, city))
                
                # Добавляем настройки уведомлений по умолчанию
                cursor.execute("""
                    INSERT OR IGNORE INTO notification_settings (user_id)
                    VALUES (?)
                """, (user_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при добавлении пользователя: {e}")
            return False
    
    def update_user_city(self, user_id: int, city: str) -> bool:
        """Обновление города пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET city = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (city, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при обновлении города: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.*, ns.morning_time, ns.evening_time, 
                           ns.send_morning, ns.send_evening, ns.weather_type
                    FROM users u
                    LEFT JOIN notification_settings ns ON u.user_id = ns.user_id
                    WHERE u.user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Ошибка при получении пользователя: {e}")
            return None
    
    def update_notification_settings(self, user_id: int, **kwargs) -> bool:
        """Обновление настроек уведомлений"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Обновляем основные настройки пользователя
                if 'city' in kwargs:
                    cursor.execute("""
                        UPDATE users SET city = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (kwargs['city'], user_id))
                
                # Обновляем настройки уведомлений
                update_fields = []
                values = []
                
                for key, value in kwargs.items():
                    if key in ['morning_time', 'evening_time', 'send_morning', 
                              'send_evening', 'weather_type']:
                        update_fields.append(f"{key} = ?")
                        values.append(value)
                
                if update_fields:
                    values.append(user_id)
                    cursor.execute(f"""
                        UPDATE notification_settings 
                        SET {', '.join(update_fields)}
                        WHERE user_id = ?
                    """, values)
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при обновлении настроек: {e}")
            return False
    
    def get_users_for_notification(self, current_time: str) -> List[Dict]:
        """Получение пользователей для отправки уведомлений в указанное время"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.*, ns.morning_time, ns.evening_time, 
                           ns.send_morning, ns.send_evening, ns.weather_type
                    FROM users u
                    LEFT JOIN notification_settings ns ON u.user_id = ns.user_id
                    WHERE u.is_active = 1 AND u.city IS NOT NULL
                    AND (
                        (ns.send_morning = 1 AND ns.morning_time = ?) OR
                        (ns.send_evening = 1 AND ns.evening_time = ?)
                    )
                """, (current_time, current_time))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка при получении пользователей для уведомлений: {e}")
            return []
    
    def get_all_active_users(self) -> List[Dict]:
        """Получение всех активных пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.*, ns.morning_time, ns.evening_time, 
                           ns.send_morning, ns.send_evening, ns.weather_type
                    FROM users u
                    LEFT JOIN notification_settings ns ON u.user_id = ns.user_id
                    WHERE u.is_active = 1 AND u.city IS NOT NULL
                """)
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка при получении активных пользователей: {e}")
            return []
    
    def deactivate_user(self, user_id: int) -> bool:
        """Деактивация пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при деактивации пользователя: {e}")
            return False

# Глобальный экземпляр базы данных
db = UserDatabase()
