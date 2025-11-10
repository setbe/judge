import sqlite3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_PATH = os.getenv("BASE_PATH")
HIVE_DATA_PATH = os.getenv("HIVE_DATA_PATH")  # JSON з Hive даними


def load_hive_data(path):
    """Завантажує дані з Hive (JSON файл)"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_sqlite_with_hive(db_path, hive_data):
    """Оновлює існуючих користувачів або додає нових у SQLite"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    for user in hive_data:
        telegram_id = user.get("telegramId")
        fullname = user.get("telegramName")
        score = user.get("_socialCredits", 0)
        avatar = user.get("other", {}).get("avatar", "")
        color = user.get("other", {}).get("color", "")
        discord_id = user.get("discordId")

        # Перевіряємо, чи користувач вже є
        cur.execute("SELECT id FROM person WHERE id = ?", (telegram_id,))
        existing = cur.fetchone()

        if existing:
            # Оновлюємо score
            cur.execute(
                "UPDATE person SET score = ?, fullname = ?, avatar = ?, color = ?, discord = ? WHERE id = ?",
                (score, fullname, avatar, color, discord_id, telegram_id)
            )
            print(f"Updated user {telegram_id}")
        else:
            # Додаємо нового користувача
            cur.execute(
                "INSERT INTO person (fullname, avatar, name, id, score, cooldown, discord, color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (fullname, avatar, fullname, telegram_id, score, "", discord_id, color)
            )
            print(f"Inserted new user {telegram_id}")

    conn.commit()
    conn.close()
    print("SQLite database updated from Hive.")


if __name__ == "__main__":
    hive_data = load_hive_data(os.path.join(BASE_PATH, HIVE_DATA_PATH))
    update_sqlite_with_hive(
        os.path.join(BASE_PATH, "user.db"),
        hive_data
    )
