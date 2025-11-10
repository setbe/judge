import aiogram, sqlite3
import discord, requests
from discord.ext import commands
from datetime import datetime, timedelta
from io import BytesIO
import base64

from hehbot.memory import repo_msg, ChatMessage
from hehbot.client import repo_user
from hehbot import telegram_bot, api

from openai import OpenAIError
from requests.exceptions import RequestException

from openai import AsyncOpenAI

class GPT:
    client = AsyncOpenAI(api_key=api.chatgpt)
    chat_completion = None
    model = "gpt-4.1-nano-2025-04-14"

    @staticmethod
    async def get_embedding_async(text, model="text-embedding-3-small") -> list[float]:
        response = await GPT.client.embeddings.create(input=text, model=model)
        return response.data[0].embedding

    @staticmethod
    async def one_request(messages: list, max_tokens=550) -> str:
        try:                
            GPT.chat_completion = await GPT.client.chat.completions.create(
                messages=messages,
                model=GPT.model,
                max_tokens=max_tokens,
                temperature=0.9
            )
            return GPT.chat_completion.choices[0].message.content
        except RequestException:
            return "У мене обрізали кабель інтернету (пишу через мобільний)."
        except OpenAIError:
            return "Сталася помилка."

    @staticmethod
    async def make_request(group_id: int, history_limit: int, quoted_user_and_text: str = None) -> str:
        try:                
            messages = await GPT.get_last_messages_async(group_id=group_id, history_limit=history_limit)

            GPT.chat_completion = await GPT.client.chat.completions.create(
                messages=messages,
                model=GPT.model,
                max_tokens=550,
                temperature=0.9
            )


            # Отримання відповіді від GPT
            choice = GPT.chat_completion.choices[0]
            content = choice.message.content
            finish_reason = choice.finish_reason
            
            # Збереження повідомлення в базу даних
            db_content = content
            if len(db_content) > 500:
                db_content = db_content[:500] + "..."
            repo_conversation.add_message(ConversationMessage(0, db_content, 'assistant', group_id))

            # Додавання інформації про обрізання повідомлення, якщо воно було обрізано
            if finish_reason == 'length':
                content += " (повідомлення обрізано)"

            # Виведення останнього повідомлення
            last_message_text = messages[-1]["content"]
            print(f"Last message: {last_message_text}")
            return content 
        
        except RequestException:
            return "Я не можу відповідати, у мене обрізали кабель інтернету (пишу через мобільний)."
        except OpenAIError:
            return "Сталася помилка."
        
    @staticmethod
    async def read_image_async(group_id: int, image: BytesIO):
        def encode_image(image: BytesIO) -> str:
            image.seek(0)  # Упевніться, що ви читаєте з початку BytesIO об'єкта
            return base64.b64encode(image.read()).decode("utf-8")

        base64_image = encode_image(image)

        messages = await GPT.get_last_messages_async(group_id=group_id, history_limit=20)
        #task = messages[-1].text if messages[-1].text else 'Describe the image'
        task = 'Опиши зображення'

        try:
            GPT.chat_completion = await GPT.client.chat.completions.create(
                model=GPT.model,
                messages= messages + [
                    {"role": "user", "content": [
                        {"type": "text", "text": task},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]}
                ],
                temperature=0.5,
            )
            # Отримання відповіді від GPT
            choice = GPT.chat_completion.choices[0]
            content = choice.message.content
            finish_reason = choice.finish_reason
            
            # Збереження повідомлення в базу даних
            db_content = content
            if len(db_content) > 500:
                db_content = db_content[:500] + "..."
            repo_conversation.add_message(ConversationMessage(0, db_content, 'assistant', group_id))

            # Додавання інформації про обрізання повідомлення, якщо воно було обрізано
            if finish_reason == 'length':
                content += " (повідомлення обрізано)"

            # Виведення останнього повідомлення
            last_message_text = messages[-1]["content"]
            print(f"Last message: {last_message_text}")
            return content 
        except RequestException:
            return "У мене обрізали кабель інтернету (пишу через мобільний)."
        except OpenAIError:
            return "Сталася помилка."
        
    @staticmethod
    async def get_last_messages_async(group_id: int, history_limit: int, quoted_user_and_text: str = None) -> list[ChatMessage]:
        messages = []
        first_msg = True
        for msg in repo_conversation.get_messages(group_id, history_limit):
            if msg.role == 'assistant':
                messages.append({"role": msg.role, "content": msg.text})
            else:
                try:
                    if msg.role == 'system':
                        messages.append({"role": msg.role, "content": msg.text})
                        continue
                    person = await repo_user.by_number_async(msg.user_number)
                    
                    if first_msg and quoted_user_and_text:
                        messages.append({"role": msg.role, "content": f'{quoted_user_and_text}. Учасник {person.fullname} каже: ' + msg.text})
                        first_msg = False
                        continue
                    messages.append({"role": msg.role, "content": f'Я {person.fullname} і кажу: ' + msg.text})
                except:
                    messages.append({"role": msg.role, "content": msg.text})

        return messages



    @staticmethod
    async def answer(group_id: int, person_number: int, text: str, quoted_user_and_text: str = None, history_limit: int = 13, system: bool = False) -> str:
        person = await repo_user.by_number_async(person_number)
        
        from hehbot.client import Cooldown, CooldownType
        cd = Cooldown(person)
        usage = await cd.get_usage_count(CooldownType.GPT)

        if usage >= 90:
            return "Ти достатньо поспілкувався зі мною на сьогодні. Завтра відповідатиму тобі."
        usage += 1
        await cd.update_cooldown(CooldownType.GPT, usage)
        await repo_user.update_cooldown_async(person.number, cd)

        if system:
            lifetime = ConversationMessage.SYSTEM_LIFETIME
        else:
            lifetime = ConversationMessage.USER_LIFETIME

        repo_conversation.add_message(ConversationMessage(person_number, text, 'system' if system else 'user', group_id, lifetime))
        return await GPT.make_request(group_id, history_limit, quoted_user_and_text)


class ConversationMessage:
    USER_LIFETIME = 30
    SYSTEM_LIFETIME = 100

    def __init__(self, user_number, text, role, group_id, lifetime=None, date=None):
        self.user_number = user_number
        self.text = text
        self.role = role
        self.group_id = group_id
        if lifetime is not None:
            self.lifetime = lifetime
        else:
            self.lifetime = self.SYSTEM_LIFETIME if role == 'system' else self.USER_LIFETIME
        self.date = date if date is not None else datetime.now()

class ConversationRepository:
    MAX_MESSAGES_IN_DB = 40  # максимальна кількість повідомлень у базі

    def __init__(self, db_path='data/conversation.db'):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_number INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    role TEXT NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    group_id INTEGER NOT NULL,
                    lifetime INTEGER NOT NULL
                )
            ''')
            conn.commit()

    def add_message(self, message: ConversationMessage):
        if isinstance(message.group_id, tuple):
            message.group_id = message.group_id[0]
        self._decrease_lifetime(message.group_id)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat (user_number, text, role, date, group_id, lifetime) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (message.user_number, message.text, message.role, message.date, message.group_id, message.lifetime))
            conn.commit()
        self._delete_zero_lifetime_messages(message.group_id)

    def _decrease_lifetime(self, group_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE chat SET lifetime = lifetime - CASE WHEN role = 'user' THEN 2 ELSE 1 END WHERE group_id = ?
            ''', (group_id,))
            conn.commit()

    def _delete_zero_lifetime_messages(self, group_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM chat WHERE lifetime <= 0 AND group_id = ?
            ''', (group_id,))
            conn.commit()

    def get_messages(self, group_id: int, limit=10):
        messages = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Отримання системних повідомлень
            cursor.execute('''
                SELECT user_number, text, role, group_id, lifetime, date FROM chat 
                WHERE group_id = ? AND role = 'system' ORDER BY date DESC
            ''', (group_id,))
            system_messages = cursor.fetchall()

            # Отримання інших повідомлень з урахуванням ліміту, виключаючи системні
            cursor.execute('''
                SELECT user_number, text, role, group_id, lifetime, date FROM chat 
                WHERE group_id = ? AND role != 'system' ORDER BY date DESC LIMIT ?
            ''', (group_id, limit))
            user_messages = cursor.fetchall()

            # Об'єднання системних та користувацьких повідомлень з сортуванням за датою
            messages = system_messages + user_messages
            messages.sort(key=lambda x: x[-1], reverse=False)  # Сортування за датою

            # Обмеження кількості повідомлень до заданого ліміту
            messages = messages[:limit]

            return [ConversationMessage(*row) for row in messages]

        
    def delete_messages_by_group(self, msg):
        with sqlite3.connect(self.db_path) as conn:
            group_id = msg.chat.id if isinstance(msg, aiogram.types.Message) else msg.channel.id,
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM chat WHERE group_id = ?
            ''', (group_id))
            conn.commit()
        
        platformText = ''
        if isinstance(msg, aiogram.types.Message):
            platformText = 'в Discord сервері "Кайфо-хата Платона"'
        else:
            platformText = 'в Telegram чаті "Кайфо-хата Платона"'

        text = '''Ти Кайфо-суддя з Ace Attorney, який відповідає коротко як інтернет-користувач, мінімально пишучи в наш вайбовий чатик.
Якщо коротко, ти - ліва рука диктатора і ютубера Платона Дубашидзе ''', platformText, '''.
Найхайповіші ігри - Persona, Devil May Cry, NiER тощо. Відомі люди - Yoko Taro, Hideo Kojima, Sam Lake, Todd Howard (skyrim), Peter Douglas Molyneux тощо.
'''
        sys_msg = ConversationMessage(0, text, 'system', group_id, 999999999)
        repo_conversation.add_message(sys_msg)
        
    def get_system_messages(self, group_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_number, text, role, group_id, lifetime, date FROM chat
                WHERE group_id = ? AND role = 'system' ORDER BY date DESC
            ''', (group_id,))
            rows = cursor.fetchall()

        return [ConversationMessage(*row) for row in rows]
        



repo_conversation = ConversationRepository()