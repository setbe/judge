import sqlite3, aiogram, aiosqlite
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import discord

from functools import singledispatchmethod
from dateutil import parser

from hehbot.env_service import env, bot
from hehbot.client import Person, repo_user

class ChatMessage:
    def __init__(self, text, date, tg_group, tg, user_number):
        self.text = text
        self.date = date
        self.tg_group = tg_group
        self.tg = tg
        self.user_number = user_number

    @classmethod
    async def from_telegram_async(cls, msg: aiogram.types.Message):
        # Асинхронна ініціалізація з Telegram
        text = msg.text
        date = msg.date
        tg_group = msg.chat.id
        tg = msg.from_user.id
        user = await repo_user.update_by_telegram_async(msg, update=False)
        user_number = user.number if user else 0

        return cls(text, date, tg_group, tg, user_number)

    @classmethod
    async def from_discord_async(cls, msg: discord.Message):
        # Ініціалізація з Discord
        text = msg.content
        date = msg.created_at
        tg_group = msg.channel.id # fix Тут неправильно, але піхуй
        tg = msg.author.id # fix Тут неправильно, але піхуй

        from hehbot.discord_integration import discord_repo
        user = await discord_repo.by_discord_async(msg.author.id)

        user_number = user.user_number if user else 0

        return cls(text, date, tg_group, tg, user_number)

    @classmethod
    def from_dict(cls, msg: dict):
        # Ініціалізація зі словника
        text = msg.get('text')
        date = datetime.now()
        tg = msg.get('tg')
        user_number = msg.get('number', 0)
        tg_group = msg.get('tg_group')

        return cls(text, date, tg_group, tg, user_number)


    
class ChatMessageRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    user_number INTEGER NOT NULL,
                    user_id INTEGER DEFAULT -1,
                    message_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_text TEXT,
                    group_id INTEGER DEFAULT -1
                )
            ''')
            conn.commit()
        

    async def add(self, msg: ChatMessage):
        n = msg.user_number
        tg = msg.tg if hasattr(msg, 'tg') else -1
        tg_group = msg.tg_group if hasattr(msg, 'tg_group') else -1

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                    INSERT INTO chat_messages (user_number, user_id, message_date, message_text, group_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (n, tg, msg.date, msg.text, tg_group))
        conn.commit()
        conn.close()

    def get_last_messages_by_user(self, user_number: int, group_id: int, limit: int = 10) -> list[ChatMessage]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_number, user_id, group_id, message_text, message_date FROM chat_messages
                WHERE user_number = ? AND group_id = ?
                ORDER BY message_date DESC
                LIMIT ?
            ''', (user_number, group_id, limit))
            messages = []
            for row in cursor.fetchall():
                messages.append(ChatMessage(text=row[3], date=row[4], tg_group=row[2], tg=row[1], user_number=row[0]))
            return messages

    def get_all_messages_by_group(self, group_id: int, limit: int = 10) -> list[ChatMessage]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_number, user_id, group_id, message_text, message_date FROM chat_messages
                WHERE group_id = ?
                ORDER BY message_date DESC
                LIMIT ?
            ''', (group_id, limit))
            messages = []
            for row in cursor.fetchall():
                messages.append(ChatMessage(text=row[3], date=row[4], tg_group=row[2], tg=row[1], user_number=row[0]))
            return messages
        
    async def can_send(self, user_number: int, group_id: int, sec_cooldown: int) -> bool:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute('''
                SELECT message_date FROM chat_messages
                WHERE user_number = ? AND group_id = ?
                ORDER BY message_date DESC
                LIMIT 1
            ''', (user_number, group_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Припустимо, row[0] містить часову мітку у форматі 'YYYY-MM-DD HH:MM:SS+00:00'
                    last_message_time = parser.parse(row[0])  # Розбір дати і часу із часовим поясом

                    # Для порівняння з поточним часом, вам потрібно або конвертувати last_message_time до поточного часового поясу,
                    # або використати час у UTC для порівняння. Тут ми використовуємо datetime.now() з конвертацією в UTC:
                    current_time = datetime.now(parser.parse(row[0]).tzinfo)

                    if current_time - last_message_time < timedelta(seconds=sec_cooldown):
                        return False
        return True
        

repo_msg = ChatMessageRepository('{}/msg.db'.format(env.data_path))