import sys
from pathlib import Path

# Визначення поточного шляху програми
current_path = Path(__file__).parent

# Перехід на одну директорію назад
parent_path = current_path.parent

# Додавання шляху до системних шляхів
sys.path.append(str(parent_path))

from hehbot import repo_user, repo_staff

insert_statements = []


import datetime, random
from datetime import timedelta
from hehbot.admin import TGStaffPersonRepository, StaffPerson

new_s = TGStaffPersonRepository('data/new_staff.db')
all = repo_staff.get_all()
for h in all:
    u = repo_user.by_tg(h.number)
    new_s.add(StaffPerson(u.number, u.id, h.admin, h.credits, h.max_credits, None))
