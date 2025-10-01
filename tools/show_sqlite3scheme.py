import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime 

# Load variables from .env
load_dotenv()

BASE_PATH = os.getenv("BASE_PATH")
DB_FILES = os.getenv("DB_FILES").split(",")


import sqlite3
import json
import os

def export_users(db_path, out_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM person")
    rows = cur.fetchall()

    result = []

    for row in rows:
        # Будуємо JSON під Person
        user = {
            "telegramId": row["id"],            # id → telegramId
            "telegramName": row["fullname"] or row["name"],
            "telegramUsername": None,           # нема в схемі user.db
            "discordId": row["discord"],
            "discordName": None,
            "discordUsername": None,
            "role": "user",                     # дефолт
            "other": {                          # можна покласти решту
                "avatar": row["avatar"],
                "color": row["color"],
                "cooldown": row["cooldown"],
            },
            "_socialCredits": row["score"] or 0,
            "state": "neutral",                 # дефолт
            "_lastSocialCreditNotice": None,
            "_lastSocialCreditNoticeDate": None,
            "_dailySocialCreditsLeft": 5000,
            "_dailySocialCreditsLimit": 5000,
            "lastUsedCasinoDate": None,
            "lastUsedPersonaDate": None,
            "hasGeneratedImageBySystem": False,
            "_fuckUpsPerWeek": ["none"] * 7,
            "userStatusText": None,
            "casinoStreak": 0,
        }
        result.append(user)

    conn.close()

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Exported users → {out_path}")


def export_score_history(db_path, out_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM score_history ORDER BY number, date")
    rows = cur.fetchall()

    history_map = {}

    for row in rows:
        num = row["number"]
        entry = {
            "score": row["score"],
            "date": row["date"],
            "count": row["count"]
        }
        if num not in history_map:
            history_map[num] = []
        history_map[num].append(entry)

    conn.close()

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(history_map, f, ensure_ascii=False, indent=2)

    print(f"Exported score history → {out_path}")


if __name__ == "__main__":
    export_users(
        os.path.join(BASE_PATH, "user.db"),
        os.path.join(BASE_PATH, "user.json")
    )
    export_score_history(
        os.path.join(BASE_PATH, "score_history.db"),
        os.path.join(BASE_PATH, "score_history.json")
    )
