import string
import random
import sqlite3
import time
import hashlib

class PlatformVerifier:
    def __init__(self, telegram_name: str, discord_name: str) -> None:
        self.telegram_name = telegram_name
        self.discord_name = discord_name
        self.password = self.generate_password()

    def generate_password(self) -> str:
        password_length = 17
        characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(characters) for _ in range(password_length))
        return password

    def save(self):
        repo_platform.save(self.telegram_name, self.discord_name, self.password)

    def parse_command(command: str):
        platform, name, password = command.split(':')
        return platform, name, password
    
    @staticmethod
    def encrypt(password: str) -> str:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return hashed_password

class PlatformDatabase:
    def __init__(self):
        self.connection = sqlite3.connect('data/verification.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS verifications (
                hash TEXT,
                telegram_name TEXT,
                discord_name TEXT,
                password TEXT,
                timestamp REAL
            )
        ''')
        self.connection.commit()
        self.update_database()

    def get_discord_name(self, hashed_password: str):
        discord_name = self.cursor.execute('''
            SELECT discord_name FROM verifications WHERE password = ?
        ''', (hashed_password,)).fetchone()
        if discord_name:
            return discord_name[0]
        return None
    
    def get_telegram_name(self, hashed_password: str):
        telegram_name = self.cursor.execute('''
            SELECT telegram_name FROM verifications WHERE password = ?
        ''', (hashed_password,)).fetchone()
        if telegram_name:
            return telegram_name[0]
        return None

    def verify_with_telegram(self, telegram_name: str, hashed_password: str):
        verified = self.cursor.execute('''
            SELECT * FROM verifications
            WHERE telegram_name = ? AND password = ?
        ''', (telegram_name, hashed_password)).fetchone() is not None

        if verified: 
            repo_platform.delete_with_telegram(telegram_name)
            return True
        return False
    
    def verify_with_discord(self, discord_name: str, hashed_password: str):
        verified = self.cursor.execute('''
            SELECT * FROM verifications
            WHERE discord_name = ? AND password = ?
        ''', (discord_name, hashed_password)).fetchone() is not None
        
        if verified:
            repo_platform.delete_with_discord(discord_name)
            return True
        return False
        


    def save(self, telegram_name: str, discord_name: str, password: str):
        self.update_database()
        current_time = time.time()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Хешування пароля

        self.cursor.execute('''
            SELECT telegram_name, discord_name FROM verifications WHERE telegram_name = ? OR discord_name = ?
        ''', (telegram_name, discord_name))
        result = self.cursor.fetchone()

        if result:
            self.cursor.execute('''
                UPDATE verifications
                SET password = ?, timestamp = ?
                WHERE telegram_name = ? OR discord_name = ?
            ''', (hashed_password, current_time, telegram_name, discord_name))
        else:
            self.cursor.execute('''
                INSERT INTO verifications (telegram_name, discord_name, password, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (telegram_name, discord_name, hashed_password, current_time))
        self.connection.commit()


    def update_database(self):
        expiration_time = 600  # Entries expire after 600 seconds (10 minutes)
        current_time = time.time()
        self.cursor.execute('''
            DELETE FROM verifications WHERE (? - timestamp) > ?
        ''', (current_time, expiration_time))
        self.connection.commit()

    def delete_with_telegram(self, telegram_name: str):
        self.cursor.execute('''
            DELETE FROM verifications WHERE telegram_name = ?
        ''', (telegram_name,))
        self.connection.commit()

    def delete_with_discord(self, discord_name: str):
        self.cursor.execute('''
            DELETE FROM verifications WHERE discord_name = ?
        ''', (discord_name,))
        self.connection.commit()

    def close(self):
        self.connection.close()

repo_platform = PlatformDatabase()