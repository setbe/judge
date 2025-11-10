import sys, sqlite3
from pathlib import Path

# Визначення поточного шляху програми
current_path = Path(__file__).parent

# Перехід на одну директорію назад
parent_path = current_path.parent

# Додавання шляху до системних шляхів
sys.path.append(str(parent_path))

user_db_path = str(parent_path)+'/data/user.db'
staff_db_path = str(parent_path)+'/data/staff.db'

def reset_cooldowns() -> None:
    print('user db: ', user_db_path)
    conn = sqlite3.connect(user_db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE person
        SET cooldown = ''
    ''')
    conn.commit()
    conn.close()

def reset_credits_for_non_admins() -> None:
    print('staff db: ', staff_db_path)
    conn = sqlite3.connect(staff_db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE staff
        SET credit_left = max_credit
        WHERE admin = 0
    ''')
    conn.commit()
    conn.close()

reset_cooldowns()
reset_credits_for_non_admins()
