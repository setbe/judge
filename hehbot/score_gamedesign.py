from datetime import datetime, timedelta
from random import randint
from hehbot.score_history import repo_score_history, ScoreHistory
from hehbot.client import repo_user, Person

def calculate_penalty_days(score: int, days_inactive: int) -> int:
    x = (score // 100) * days_inactive
    return x + randint(1, x // 2)

async def update_users_scores_if_inactive(users: list[Person]) -> str | None:
    if not users:
        return None

    first_user = users[0]
    total_penalty_first_user = 0
    other_users_processed = False

    for user in users:
        # Отримуємо історію балів користувача
        history = repo_score_history.get_history_for_user(user.number, last_days=60)  # дивимось за останні 60 днів
        if not history:
            continue

        last_score_date = max(h.date for h in history)
        days_inactive = (datetime.now() - last_score_date).days

        if days_inactive > 1:
            total_penalty = 0
            for day in range(2, days_inactive + 1):
                total_penalty += calculate_penalty_days(user.score, day)

            new_score = user.score - total_penalty
            if new_score < 0:
                new_score = 0
            await repo_user.update_person_async(user.number, score=new_score)

            if user == first_user:
                total_penalty_first_user = total_penalty
            else:
                other_users_processed = True

    if total_penalty_first_user > 0:
        message = f"Популярність користувача {first_user.fullname} падає на -{total_penalty_first_user} соціальних кредитів."
        if other_users_processed:
            message += " Та ще інших в топі кращих."
        return message
    return None

async def update_users_negative_scores_if_inactive(users: list[Person]) -> str | None:
    if not users:
        return None

    first_user = users[0]
    total_bonus_first_user = 0
    other_users_processed = False

    for user in users:
        # Отримуємо історію балів користувача
        history = repo_score_history.get_history_for_user(user.number, last_days=60)  # дивимось за останні 60 днів
        if not history:
            continue

        last_score_date = max(h.date for h in history)
        days_inactive = (datetime.now() - last_score_date).days

        if days_inactive > 1:
            total_bonus = 0
            for day in range(2, days_inactive + 1):
                total_bonus += calculate_penalty_days(user.score, day)

            new_score = user.score + total_bonus
            if new_score > 0:
                new_score = 0
            await repo_user.update_person_async(user.number, score=new_score)

            if user == first_user:
                total_bonus_first_user = total_bonus
            else:
                other_users_processed = True

    if total_bonus_first_user > 0:
        message = f"Популярність користувача {first_user.fullname} зросла на +{total_bonus_first_user} соціальних кредитів."
        if other_users_processed:
            message += " Та ще інших в топі з найгіршими."
        return message
    return None