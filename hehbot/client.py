import sqlite3, aiogram, asyncio
from abc import ABC, abstractmethod
from typing import List
import discord.ext
import discord.ext.commands
from hehbot.admin import repo_staff
from enum import Enum

from hehbot.discord_integration import discord_repo, DiscordPerson
import discord

class Person:
    def __init__(self, 
                 id: int = None, 
                 fullname: str = None, 
                 avatar: str = None, 
                 name: str = None, 
                 number: int = None, 
                 score: int = 1000, 
                 cooldown: str = None, 
                 discord: int = None, 
                 color: str = None) -> None:
        self.id = id
        self.fullname = fullname
        self.avatar = avatar
        self.name = name
        self.number = number
        self.score = score
        self.cooldown = cooldown
        self.discord = discord

        from hehbot.hehbot_utils import hex_to_rgb
        self.color = hex_to_rgb(color)

class CooldownType(Enum):
    SLOTS = 'slots'
    BET = 'bet'
    IDI = 'idi'
    GPT = 'gpt'
    RATE = 'rate'

class Cooldown:
    def __init__(self, person: Person) -> None:
        self.cooldowns = person.cooldown.split() if person.cooldown else []

    async def get_cooldown(self, cooldown_type: CooldownType) -> str:
        # Для SLOTS визначаємо, чи є кулдаун
        if cooldown_type == CooldownType.SLOTS:
            return 'slots' if 'slots' in self.cooldowns else None
        
        # Для IDI визначаємо, чи є кулдаун
        elif cooldown_type == CooldownType.IDI:
            return 'idi' if 'idi' in self.cooldowns else None
        
        # Для BET визначаємо, який з кулдаунів відповідає
        elif cooldown_type == CooldownType.BET:
            for i in range(1, 4):
                if f'bet{i}' in self.cooldowns:
                    return f'bet{i}'
            return None
        
        # Для GPT визначаємо, який з кулдаунів відповідає
        elif cooldown_type == CooldownType.GPT:
            for i in range(1, 30):
                if f'gpt{i}' in self.cooldowns:
                    return f'gpt{i}'
            return None
        
        # Для RATE визначаємо, чи є кулдаун
        elif cooldown_type == CooldownType.RATE:
            return 'rate' if 'rate' in self.cooldowns else None

    async def update_cooldown(self, cooldown_type: CooldownType, usage_count: int) -> None:
        # Створюємо значення кулдауну. Для SLOTS і IDI кількість використань не враховуємо.
        cooldown_value = f'{cooldown_type.value}'
        if cooldown_type == CooldownType.BET:
            # Для BET додаємо кількість використань, якщо вона більше 1
            cooldown_value += f'{"" if usage_count == 1 else usage_count}'

        if cooldown_type == CooldownType.GPT:
            # Для GPT додаємо кількість використань, якщо вона більше 1
            cooldown_value += f'{"" if usage_count == 1 else usage_count}'
        
        # Видаляємо попередні кулдауни того ж типу
        self.cooldowns = [cd for cd in self.cooldowns if not cd.startswith(cooldown_type.value)]
        
        # Додаємо новий кулдаун
        self.cooldowns.append(cooldown_value)

    async def get_usage_count(self, cooldown_type: CooldownType) -> int:
        for cooldown in self.cooldowns:
            if cooldown.startswith(cooldown_type.value):
                # Для SLOTS повертаємо 1
                if cooldown_type == CooldownType.SLOTS:
                    return 1
                
                if cooldown_type == CooldownType.RATE:
                    return 1
                
                # Для BET визначаємо кількість використань
                if cooldown_type == CooldownType.BET and len(cooldown) > 3:
                    return int(cooldown[3:])
                
                if cooldown_type == CooldownType.GPT and len(cooldown) > 3:
                    return int(cooldown[3:])
                return 1
        return 0
    

class IPersonRepository(ABC):
    @abstractmethod
    def add(self, person: Person) -> None:
        pass

    @abstractmethod
    def by_telegram(self, tg_id: int) -> Person:
        pass

    @abstractmethod
    def by_number_async(self, number: int) -> Person:
        pass

    @abstractmethod
    async def update_person_async(self, id: int, fullname: str = None, avatar: str = None, name: str = None, score: int = None, cooldown: str = None) -> None:
        pass

    @abstractmethod
    def delete(self, tg_id: int) -> None:
        pass

    @abstractmethod
    def with_lowest_scores(self, limit: int) -> List[Person]:
        pass

    @abstractmethod
    def with_highest_scores(self, limit: int) -> List[Person]:
        pass

    @abstractmethod
    async def update_by_telegram_async(self, msg: aiogram.types.Message) -> Person:
        pass

    @abstractmethod
    def by_name_async(self, name: str) -> Person:
        pass

    @abstractmethod
    async def update_cooldown_async(self, person_number: int, cooldown: Cooldown) -> None:
        pass

class PersonRepository(IPersonRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        

        self._create_table()

    def _create_table(self) -> None:
        conn = sqlite3.connect(self.db_path)
        

        cursor = conn.cursor()
        

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS person (
                number INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT,
                avatar TEXT,
                name TEXT,
                id INTEGER UNIQUE,
                score INTEGER NOT NULL DEFAULT 0,
                cooldown TEXT DEFAULT '',
                discord INTEGER UNIQUE,
                color TEXT
            )
        ''')
        conn.commit()
        conn.close()

    async def update_person_async(self, 
                            number: int, 
                            fullname: str = None, 
                            avatar: str = None, 
                            name: str = None, 
                            score: int = None, 
                            cooldown: str = None,
                            discord: int = None,
                            telegram: int = None,
                            color: tuple[int, int, int] = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
         
        fields_to_update = []
        values = []
        is_credit_updated = False 
        is_image_updated = False
        #old = await repo_user.by_number_async(number)
        #if not old:
        #    old = Person()
        
        
        if fullname is not None:
            fields_to_update.append("fullname = ?")
            values.append(fullname)

            is_image_updated = True

        if avatar is not None:
            fields_to_update.append("avatar = ?")
            values.append(avatar)

            is_image_updated = True

        if name is not None:
            fields_to_update.append("name = ?")
            values.append(name)

            is_image_updated = True

        if score is not None:
            fields_to_update.append("score = ?")
            values.append(score)

            is_credit_updated = True
            is_image_updated = True

        if cooldown is not None:
            fields_to_update.append("cooldown = ?")
            values.append(cooldown)

        if discord is not None:
            fields_to_update.append("discord = ?")
            values.append(discord)

        if telegram is not None:
            fields_to_update.append("id = ?")
            values.append(discord)

        if color is not None:
            fields_to_update.append("color = ?")
            from hehbot.hehbot_utils import rgb_to_hex
            values.append(rgb_to_hex(color))
        
        values.append(number) # ID для умови WHERE
        
        if fields_to_update:
            update_stmt = f"UPDATE person SET {', '.join(fields_to_update)} WHERE number = ?"
            cursor.execute(update_stmt, values)
            conn.commit()
        conn.close()

        # оновлюємо фотку кредитів користувача
        if is_credit_updated:
            # add score history
            from hehbot import repo_score_history, ScoreHistory
            repo_score_history.add(ScoreHistory(number, score))

            from hehbot.credit_image import create_credit_image_async
            person = await self.by_number_async(number)
            await create_credit_image_async(person)

    def add(self, person: Person) -> int:
        if isinstance(person.color, tuple):
            from hehbot.hehbot_utils import rgb_to_hex
            color = rgb_to_hex(person.color)
        else:
            color = person.color

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO person (fullname, avatar, name, id, score, cooldown, discord, color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(person.fullname), str(person.avatar), str(person.name), person.id, 
              person.score, person.cooldown, person.discord, color))
        conn.commit()
        
        # Отримання user_number, який є значенням AUTOINCREMENT поля number
        user_number = cursor.lastrowid
        conn.close()

        # Повернення user_number
        return user_number
 
    async def update_by_telegram_async(self, msg: aiogram.types.Message, update=True) -> Person | None:
        p = msg.from_user
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, fullname, avatar, name, id, score, cooldown, discord, color FROM person WHERE id = ?', (msg.from_user.id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            person = Person(id=row[4], fullname=row[1], name=row[3], number=row[0], score=row[5], cooldown=row[6], discord=row[7], color=row[8])
            if update:
                await repo_user.update_person_async(
                    number= person.number,
                    fullname = p.full_name, 
                    avatar = None, 
                    name = p.username,
                    score = person.score,
                    cooldown = person.cooldown,
                    discord=person.discord,
                    color=person.color
                    )
        else:
            # Якщо персона не знайдена, створюємо нову з заданим tg_id і дефолтними значеннями
            person = Person(
                id = p.id, 
                fullname = p.full_name, 
                avatar = None, 
                name = p.username,
                score = 1000,
                cooldown = '',
                discord=None,
                color=(0,0,0))
            self.add(person)  # Викликаємо метод add для додавання нової персониs
        return person
    
    async def update_by_discord_async(self, msg: discord.Message, update_all=True) -> Person | None:        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, fullname, avatar, name, id, score, cooldown, discord, color FROM person WHERE discord = ?', (msg.author.id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            person = Person(id=row[4], fullname=row[1], name=row[3], number=row[0], score=row[5], cooldown=row[6], discord=row[7], color=row[8])
            if update_all:
                ds_person = await discord_repo.by_discord_async(msg.author.id)
                ds_person.nickname = msg.author.name
                ds_person.full_name = msg.author.display_name
                ds_person.ava = msg.author.display_avatar.url if msg.author.display_avatar.url else msg.author.default_avatar.url
                await discord_repo.update_person_async(ds_person)
        else:
            # Якщо персона не знайдена, створюємо нову з дефолтними значеннями
            person = Person(
                id = None, 
                fullname = msg.author.display_name, 
                avatar = None, 
                name = msg.author.name,
                score = 1000,
                cooldown = '',
                discord=msg.author.id,
                color=(0,0,0))
            user_number = self.add(person)  # Викликаємо метод add для додавання нової персони
            person.number = user_number

            await discord_repo.add_person_async(
                DiscordPerson(
                    user_number=person.number, 
                    id=msg.author.id, 
                    nickname=msg.author.name, 
                    full_name=msg.author.display_name, 
                    ava=msg.author.display_avatar.url if msg.author.display_avatar.url else msg.author.default_avatar.url, 
                    use_avatar=False, 
                    use_banner=False,
                    color=(0,0,0)))
        return person
    
    def check_for_platon(self, person: Person) -> Person:
        if person.name == 'GroupAnonymousBot' or person.name == 'Channel_Bot' or person.number == 42 or person.name == 'plato_dubashydze':
            person.fullname = 'Платон Дубашидзе'
        else:
            names = ['платон дубашидзе', 'дубашидзе', 'platon', 'платон', 'plato dubashydze', 'plato']
            if person.name.lower() in names:
                person.fullname = 'Ноунейм'
        return person

    def by_telegram(self, tg_id: int) -> Person:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, fullname, avatar, name, id, score, cooldown, discord, color FROM person WHERE id = ?', (tg_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            person = Person(id=row[4], fullname=row[1], avatar=row[2], name=row[3], number=row[0], score=row[5], cooldown=row[6], discord=row[7], color=row[8])
            return self.check_for_platon(person)
        return None
    
    async def by_discord_async(self, discord_id: int) -> Person | None:
        ds_person = await discord_repo.by_discord_async(discord_id)

        if not ds_person:
            return None
        
        tg_like = await repo_user.by_number_async(ds_person.user_number)
        tg_like.discord = discord_id
        tg_like.name = ds_person.nickname
        tg_like.avatar = ds_person.ava
        tg_like.fullname = ds_person.full_name
        tg_like.color = ds_person.color
        return self.check_for_platon(tg_like)
    
        #conn = sqlite3.connect(self.db_path)
        #cursor = conn.cursor()
        #cursor.execute('SELECT number, fullname, avatar, name, id, score, cooldown, discord, color FROM person WHERE discord = ?', (discord_id,))
        #row = cursor.fetchone()
        #conn.close()
        #if row:
        #    person = Person(id=row[4], fullname=row[1], avatar=row[2], name=row[3], number=row[0], score=row[5], cooldown=row[6], discord=row[7], color=row[8])
        #    return self.check_for_platon(person)
        #return None
        
    async def by_number_async(self, number: int) -> Person:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, fullname, avatar, name, id, score, cooldown, discord, color FROM person WHERE number = ?', (number,))
        row = cursor.fetchone()
        conn.close()
        if row:
            person = Person(id=row[4], fullname=row[1], avatar=row[2], name=row[3], number=row[0], score=row[5], cooldown=row[6], discord=row[7], color=row[8])
            return self.check_for_platon(person)
        return None

    async def by_name_async(self, name: str) -> Person | None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, fullname, avatar, name, id, score, cooldown, discord, color FROM person WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            person = Person(id=row[4], fullname=row[1], avatar=row[2], name=row[3], number=row[0], score=row[5], cooldown=row[6], discord=row[7], color=row[8])
            return self.check_for_platon(person)
        
        return None


    def delete(self, user_number: int) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM person WHERE number = ?', (user_number,))

        conn.commit()
        conn.close()

        staff = repo_staff.get_by_number(user_number)
        

        if staff:
            repo_staff.delete(user_number)

    def with_lowest_scores(self, limit: int) -> List[Person]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, fullname, avatar, name, number, score, cooldown, discord, color FROM person 
            WHERE score > -100000000
            ORDER BY score ASC 
            LIMIT ?''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [Person(id=row[0], fullname=row[1], avatar=row[2], name=row[3], number=row[4], score=row[5], cooldown=row[6], discord=row[7], color=row[8]) for row in rows]
        
    def with_highest_scores(self, limit: int) -> List[Person]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, fullname, avatar, name, number, score, cooldown, discord, color FROM person 
            WHERE score < 100000000
            ORDER BY score DESC 
            LIMIT ?''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [Person(id=row[0], fullname=row[1],  avatar=row[2], name=row[3], number=row[4], score=row[5], cooldown=row[6], discord=row[7], color=row[8]) for row in rows]
        

    async def update_cooldown_async(self, person_number: int, cooldown: Cooldown) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''UPDATE person SET cooldown = ? WHERE number = ?''', 
        (' '.join(cooldown.cooldowns), person_number))
        conn.commit()
        conn.close()
    
repo_user = PersonRepository('data/user.db')

