import sqlite3
import discord, requests
from discord.ext import commands
from hehbot.hehbot_utils import rgb_to_hex

class DiscordPerson():
    def __init__(self, 
                 user_number: int, 
                 id: int, 
                 nickname: str = None,
                 full_name: str = None,
                 ava: str = None, 
                 banner: str = None, 
                 color: str = None,
                 use_banner = False,
                 use_avatar = False
                 ):
        self.user_number = user_number
        self.id = id
        self.nickname = nickname
        self.full_name = full_name
        self.ava = ava
        self.banner = banner
        self.use_banner = use_banner
        self.use_avatar = use_avatar

        from hehbot.hehbot_utils import hex_to_rgb
        self.color = hex_to_rgb(color)

class IDiscordPersonRepository():
    async def add_person_async(self, person: DiscordPerson) -> None:
        raise NotImplementedError

    async def by_discord_async(self, discord: int) -> DiscordPerson:
        raise NotImplementedError

    async def update_person_async(self, person: DiscordPerson) -> None:
        raise NotImplementedError

class DiscordPersonRepository(IDiscordPersonRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()

    def _create_table(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS person (
                user_number INTEGER PRIMARY KEY NOT NULL UNIQUE,
                discord INTEGER UNIQUE,
                nickname TEXT,
                full_name TEXT,
                avatar TEXT,
                banner TEXT,
                color TEXT,
                use_banner INTEGER,
                use_avatar INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    async def add_person_async(self, person: DiscordPerson) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        color = person.color
        if isinstance(color, tuple):
            color = rgb_to_hex(color)
        cursor.execute('''
            INSERT INTO person (user_number, discord, nickname, full_name, avatar, banner, color, use_banner, use_avatar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (person.user_number, person.id, person.nickname, person.full_name, person.ava, person.banner, color, person.use_banner, person.use_avatar))
        conn.commit()
        conn.close()

    async def by_discord_async(self, discord: int) -> DiscordPerson:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM person WHERE discord = ?', (discord,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return DiscordPerson(*row)
        else:
            return None
        
    async def by_number_async(self, user_number: int) -> DiscordPerson:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM person WHERE user_number = ?', (user_number,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return DiscordPerson(*row)
        else:
            return None
        
    async def by_name_async(self, nickname: str) -> DiscordPerson:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM person WHERE nickname = ?', (nickname,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return DiscordPerson(*row)
        else:
            return None

    async def update_person_async(self, person: DiscordPerson) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Підготування динамічного запиту та даних для оновлення
        updates = []
        data = []

        if person.nickname is not None:
            updates.append("nickname = ?")
            data.append(person.nickname)
        if person.full_name is not None:
            updates.append("full_name = ?")
            data.append(person.full_name)
        if person.ava is not None:
            updates.append("avatar = ?")
            data.append(person.ava)
        if person.banner is not None:
            updates.append("banner = ?")
            data.append(person.banner)
        if person.color is not None:
            updates.append("color = ?")
            color = person.color
            if isinstance(color, tuple):
                color = rgb_to_hex(color)
            data.append(color)
        if person.use_banner is not None:
            updates.append("use_banner = ?")
            data.append(int(person.use_banner))
        if person.use_avatar is not None:
            updates.append("use_avatar = ?")
            data.append(int(person.use_avatar))

        # Створення запиту, якщо є що оновлювати
        if updates:
            query = "UPDATE person SET " + ", ".join(updates) + " WHERE discord = ?"
            data.append(person.id)
            cursor.execute(query, data)
            conn.commit()

        conn.close()

discord_repo = DiscordPersonRepository('data/discord.db')