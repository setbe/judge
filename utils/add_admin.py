import sys
import asyncio
import sys
from pathlib import Path

# Визначення поточного шляху програми
current_path = Path(__file__).parent

# Перехід на одну директорію назад
parent_path = current_path.parent

# Додавання шляху до системних шляхів
sys.path.append(str(parent_path))

from hehbot import repo_user, repo_staff, Person, StaffPerson

class PersonNotFound(Exception):
    pass

async def add_admin_by_name(name: str):
    try:
        # Пошук персони за іменем в базі користувачів
        person = repo_user.by_name(name)
        if person is None:
            raise PersonNotFound(f"Person with name {name} not found.")
        
        # Створення нового об'єкта StaffPerson як адміністратор
        new_admin = StaffPerson(
            number=person.number, 
            admin=True, 
            telegram=person.id, 
            discord=person.discord, 
            credits=1,
            max_credit=1)
        
        # Додавання адміністратора в базу staff
        repo_staff.add(new_admin)
        print(f"Person {name} added as admin successfully.")
    except PersonNotFound as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: add_admin.py <name>")
        sys.exit(1)

    name = sys.argv[1]
    asyncio.run(add_admin_by_name(name))