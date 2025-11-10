import aiogram, asyncio 
import discord
import re

class ResultAndError:
    def __init__(self, result = None, error = None):
        self.result = result
        self.error = error
    
    def __str__(self):
        return f"Result: {self.result}, Error: {self.error}"
    
    def __repr__(self):
        return f"Result: {self.result}, Error: {self.error}"
    
    def __eq__(self, other):
        return self.result == other.result and self.error == other.error
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __bool__(self):
        return self.result is not None
    
def find_username(text: str) -> str | None:
    """
    Шукає в тексті перше зустрічне ім'я користувача, яке починається з символів "@" або "$",
    або ж перше слово, що відповідає патерну імені користувача (складається з літер та цифр, починається з літери).

    :param text: Рядок тексту, у якому потрібно знайти ім'я.
    :return: Знайдене ім'я користувача або None, якщо ім'я не знайдено.
    """
    # Спочатку шукаємо ім'я, яке починається з "@" або "$"
    special_match = re.search(r'\b[@$][a-zA-Z_][a-zA-Z0-9_]*\b', text)
    if special_match:
        return special_match.group(0)

    # Якщо таке ім'я не знайдено, шукаємо ім'я за існуючим патерном
    match = re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
    return match.group(0) if match else None


def remove_court_and_username(text: str) -> str:
    # Спочатку видаляємо слово "суд"
    text_without_court = re.sub(r'\bсуд,\s*|\bсуд\b', '', text, flags=re.IGNORECASE)

    # Потім шукаємо та видаляємо нікнейм
    # Нікнейм визначаємо як слово, яке починається з "@" або "$"
    text_final = re.sub(r'\b[@$][a-zA-Z_][a-zA-Z0-9_]*\b', '', text_without_court)

    return text_final.strip()


def find_number(text: str, index: int = 0) -> int:
    """
    Шукає у тексті числа і повертає число за вказаним індексом.
    
    :param text: Рядок тексту для пошуку чисел.
    :param index: Індекс числа, яке потрібно повернути (починаючи з 0).
    :return: Число у тексті за вказаним індексом або None, якщо числа за таким індексом немає.
    """
    matches = re.findall(r'(?<!\w)[+-]?\d+', text)
    if matches and len(matches) > index:
        return int(matches[index])
    return None




def compare_words(args1: list[str], args2: list[str]) -> bool:
    """
    Порівнює два списки слів, використовуючи відстань Левенштейна для визначення схожості.
    Якщо знайдено хоча б одну пару слів з схожістю 70% або вище, повертає True.

    :param args1: Перший список слів для порівняння.
    :param args2: Другий список слів для порівняння.
    :return: True, якщо знайдена хоча б одна пара схожих слів; інакше False.
    """

    def levenstein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return levenstein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1 
                deletions = current_row[j] + 1       
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    for d1 in args2:
        for d2 in args1:
            distance = levenstein_distance(d1.lower(), d2)
            similarity = 1 - distance / max(len(d1), len(d2))
            if similarity >= 0.7:
                return True
    return False




def remove_english_words(text: str) -> str:
    """
    Видаляє всі англійські слова з тексту і повертає результат.

    :param text: Рядок тексту, з якого потрібно видалити англійські слова.
    :return: Текст після видалення англійських слів.
    """
    # Визначаємо регулярний вираз для пошуку англійських слів.
    # Слово може починатися і закінчуватися англійською літерою або символом "_",
    # і містити в середині англійські літери та "_".
    pattern = r'\b[a-zA-Z_]+\b'
    
    # Використовуємо re.sub() для заміни всіх знайдених англійських слів на пустий рядок.
    result = re.sub(pattern, '', text)
    
    # Повертаємо результат після видалення англійських слів.
    return result

async def target_in_replied_msg_async(msg, by_str: str) -> ResultAndError:
    from hehbot.client import Person, repo_user
    from hehbot.discord_integration import discord_repo

    target_msg = None
    username = None
    target = None

    # Шукаємо ім'я користувача в тексті
    username = find_username(by_str)
    if username:
        if isinstance(msg, aiogram.types.Message):
            target = await repo_user.by_name_async(username)
        if isinstance(msg, discord.Message):
            target = await discord_repo.by_name_async(username)

        if target:
            return ResultAndError(target, None)
    
    if isinstance(msg, discord.Message):
        if msg.mentions and len(msg.mentions) > 0:
            mentioned = msg.mentions[0]
            target = await discord_repo.by_discord_async(mentioned.id)
            if target:
                return ResultAndError(target, None)

    async def update_telegram_user(target_msg):
        target = await repo_user.update_by_telegram_async(target_msg)
        if not target:
            return ResultAndError(None, f"Щось пішло не так під час додавання {target_msg.from_user.full_name} в мою базу даних")
        return ResultAndError(target, None)

    async def update_discord_user(target_msg):
        await repo_user.update_by_discord_async(target_msg)
        target = await discord_repo.by_discord_async(target_msg.author.id)
        if not target:
            return ResultAndError(None, f"Щось пішло не так під час додавання {target_msg.author.display_name} в мою базу даних")
        return ResultAndError(target, None)
    
    # Якщо ім'я користувача не знайдено в тексті, шукаємо його в повідомленні, на яке відповідають
    if not username:
        if isinstance(msg, aiogram.types.Message):
            # Для aiogram
            target_msg = msg.reply_to_message
            if target_msg and target_msg.from_user.username:
                username = f'${target_msg.from_user.username}'
        elif isinstance(msg, discord.Message):
            # Для discord
            target_msg = msg.reference.resolved if msg.reference else None
            if target_msg and isinstance(target_msg, discord.Message) and target_msg.author.name:
                username = f'${target_msg.author.name}'

    # Якщо ім'я користувача знайдено, шукаємо його в базі даних
    if username:
        target = await repo_user.by_name_async(username)
        if not target:
            if isinstance(msg, aiogram.types.Message):
                return await update_telegram_user(target_msg)
            elif isinstance(msg, discord.Message):
                return await update_discord_user(target_msg)

    # Якщо користувача не знайдено, повідомляємо про це
    if not target:
        if isinstance(msg, aiogram.types.Message):
            # Для aiogram
            target_msg = msg.reply_to_message
            if target_msg:
                return await update_telegram_user(target_msg)
            else:
                return ResultAndError(None, f'Користувача {username} не знайдено в базі даних; можеш відповісти на його повідомлення щоб додати')
        elif isinstance(msg, discord.Message):
            # Для discord
            target_msg = msg.reference.resolved if msg.reference else None
            if target_msg and isinstance(target_msg, discord.Message):
                return await update_discord_user(target_msg)
            else:
                return ResultAndError(None, f'Користувача {username} не знайдено в базі даних; можеш відповісти на його повідомлення щоб додати')

    return ResultAndError(target, None)

async def person_by_msg_async(msg) -> ResultAndError:

    from hehbot.client import repo_user
    from hehbot.discord_integration import discord_repo, DiscordPerson
    person = None

    if isinstance(msg, aiogram.types.Message):
        # Для aiogram
        telegram_id = msg.from_user.id
        person = repo_user.by_telegram(telegram_id)
    elif isinstance(msg, discord.Message):
        # Для discord
        discord_id = msg.author.id
        person = await discord_repo.by_discord_async(discord_id)

    if not person:
        return ResultAndError(None, f'Тебе не знайдено в базі даних')
    return ResultAndError(person, None)



def rgb_to_hex(color: tuple[int, int, int]):
        r, g, b = color
        hex_color = f'#{r:02x}{g:02x}{b:02x}'

        return hex_color

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    try:
        if isinstance(hex_color, bytes):
            hex_color = hex_color.decode('utf-8')  # Декодування байтів у строку
        else:
            return (0,0,0)
        hex_color = hex_color.lstrip('#')  # Видалення символу '#', якщо він є
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        return rgb
    except:
        return (0,0,0)