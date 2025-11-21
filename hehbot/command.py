
from hehbot.client import repo_user, Person, CooldownType, Cooldown
from hehbot.admin import repo_staff, StaffPerson
from hehbot.discord_integration import DiscordPerson, discord_repo
from hehbot.score_history import plot_user_history, plot_top_history
from hehbot.credit_image import send_credit_image, send_highscore_image, send_lowscore_image, send_changed_credit_image
from hehbot.env_service import bot, dp
from hehbot.heh_config import heh_config
from hehbot.hehbot_utils import find_username, find_number, target_in_replied_msg_async, person_by_msg_async

from hehbot.base_command import BotCommand

import aiogram, discord, asyncio, math
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.utils.markdown import hbold
from aiogram.utils.keyboard import InlineKeyboardBuilder

from random import randint



def safe_telegram_request(retry_seconds=5.0):
    """
    Декоратор для обгортання асинхронних функцій, який дозволяє безпечно виконувати запити до Telegram API.
    У випадку помилки TelegramRetryAfter автоматично затримує виконання на вказану кількість секунд і повторює спробу.
    При інших помилках TelegramAPIError виводить повідомлення про помилку і припиняє виконання.

    :param retry_seconds: Час очікування перед повторною спробою виконання запиту, у секундах.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            while True:
                try:
                    return await func(*args, **kwargs)
                except TelegramRetryAfter as e:
                    print(f"Попередження: контроль за частотою запитів від Telegram, чекаємо {e.retry_after} секунди.")
                    await asyncio.sleep(e.retry_after)
                except TelegramAPIError as e:
                    print(f"Помилка Telegram API: {e}")
                    break  # or raise e to propagate the error after logging
        return wrapper
    return decorator






class ConnectCommand(BotCommand):
    """
    Команда для приєднання іншої платформи (telegram/discord).
    """
    
    ignore = True
    
    @classmethod
    def command_name(cls) -> str:
        return "connect"
    
    @classmethod
    async def execute(cls, msg, args, by_str: str = None):

        from hehbot.verify_platform import PlatformVerifier
        from hehbot.discord_integration import discord_repo, DiscordPerson

        nickname = by_str.strip()

        if len(nickname) > 32:
            return 'Нікнейм занадто довгий. Максимальна довжина - 32 символи.'
        elif len(nickname) < 2:
            return 'Нікнейм занадто короткий. Мінімальна довжина - 2 символи.'
        
        if isinstance(msg, aiogram.types.Message):
            tg_person = (await person_by_msg_async(msg)).result
            ds_person = await discord_repo.by_name_async(nickname)
            
            if not ds_person:
                return 'Такого користувача в Discord не знайдено. Ти повинен бути на сервері Платона і написати боту щось хоч один раз.'

            current_platform = 'telegram'
            other_platform = 'discord'
        elif isinstance(msg, discord.Message):
            ds_person = (await person_by_msg_async(msg)).result
            tg_person = await repo_user.by_name_async(nickname)

            if not tg_person:
                return 'Такого користувача в Telegram не знайдено. Ти писав боту в тґ хоч раз?'

            current_platform = 'discord'
            other_platform = 'telegram'
        else:
            return 'Невідома платформа.'

        verifier = PlatformVerifier(telegram_name=tg_person.name, discord_name=ds_person.nickname)
        verifier.save()

        return (f'У вас є 10 хвилин для підтвердження. Відправте в приватні в {other_platform}:\n'
                f'/verify {PlatformVerifier.encrypt(verifier.password)}')

class VerifyCommand(BotCommand):
    """
    Команда для підтвердження підключення іншої платформи (telegram/discord).
    """
    
    ignore = True
    
    @classmethod
    def command_name(cls) -> str:
        return "verify"
    
    @classmethod
    async def execute(cls, msg, args, by_str: str = None):
        if not args:
            return 'Отримайте хеш через "/connect". Потім введіть для верифікації у форматі: /verify <хеш>'
        
        from hehbot.verify_platform import repo_platform, PlatformVerifier
        from hehbot.discord_integration import discord_repo, DiscordPerson

        def merge_accounts(person1: Person, person2: Person, ds_person: DiscordPerson):
            score = max(abs(person1.score), abs(person2.score))
            if not person1.id or not person2.id:
                return False
            if person1.id == person2.id:
                return False
            
            def delete_n_add(to_delete: Person, to_modify: Person, score: int, discord_id: int):
                repo_user.delete(to_delete.number)
                repo_user.delete(to_modify.number)
                to_modify.score = score
                to_modify.discord = discord_id
                repo_user.add(to_modify.number)
            
            if not person1.id:
                delete_n_add(person1, person2, score, ds_person.id)
            return True

        hashed_password = by_str.strip()
        if len(hashed_password) != 64:
            return 'Невірний формат хешу. Повинен бути 64 символи, надано: ' + str(len(hashed_password))

        if isinstance(msg, aiogram.types.Message):
            discord_target = await discord_repo.by_name_async(repo_platform.get_discord_name(hashed_password))
            telegram_person = (await person_by_msg_async(msg)).result
            tg_target = await repo_user.by_discord_async(discord_target.user_number)

            if not telegram_person:
                return 'Користувача в Telegram не знайдено.'
            if not discord_target:
                return 'Цільового користувача в Discord не знайдено.'
            if not tg_target:
                return 'Користувача в Telegram не знайдено.'

            verified = repo_platform.verify_with_telegram(telegram_person.name, hashed_password)
            if verified:
                verified = merge_accounts(telegram_person, tg_target, discord_target)

        elif isinstance(msg, discord.Message):
            tg_target = await repo_user.by_name_async(repo_platform.get_telegram_name(hashed_password))
            discord_person = (await person_by_msg_async(msg)).result
            telegram_person = await repo_user.by_discord_async(discord_person.user_number)

            if not tg_target:
                return 'Цільового користувача в Telegram не знайдено.'
            if not discord_person:
                return 'Користувача в Discord не знайдено.'
            if not telegram_person:
                return 'Користувача в Telegram не знайдено.'

            verified = repo_platform.verify_with_discord(discord_person.nickname, hashed_password)
            if verified:
                verified = merge_accounts(tg_target, telegram_person, discord_person)
        else:
            return 'Невідома платформа.'
        
        if not verified:
            return 'Верифікація не пройшла. Перевірте, будь ласка, правильність введеного хешу або зверніться до Архітектора.'
        return 'Ваша ідентифікація пройшла успішно. Ви підключені.'


class SetCreditCommand(BotCommand):
    """
    Команда для встановлення кредитів користувача.
    """
    description = "видати 300"

    @classmethod
    def command_name(cls) -> str:
        return "give"

    @classmethod
    async def execute(cls, msg, args, by_str: str = None) -> str:
        MAX_INT_VALUE = 9223372036854775807
        MIN_INT_VALUE = -9223372036854775808
        
        # Задаємо користуча та інспектора з цього користувача
        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return cls.execute_stopped(result_person.error)
        person = result_person.result

        if isinstance(person, Person):
            staff = repo_staff.get_by_number(person.number)
        else:
            staff = repo_staff.get_by_number(person.user_number)
        amount = None

        # Перевіряємо, чи користувач має права на виконання команди
        if not staff:
            return cls.execute_stopped(f'через відсутність прав')
        
        # Перевіряємо наявність аргументів
        if by_str:
            amount = find_number(by_str)
        else:
            return cls.execute_stopped('не вказано суму')

        # Шукаємо користувача
        result_target = await target_in_replied_msg_async(msg=msg, by_str=by_str)
        if result_target.error:
            return result_target.error
        target = result_target.result
        target_number = target.number if isinstance(target, Person) else target.user_number

        # Перевіряємо формат числа кредитів
        if amount:
            tg_target = await repo_user.by_number_async(target_number)
            new_score = tg_target.score + amount

            if new_score > MAX_INT_VALUE:
                new_score = MAX_INT_VALUE
            elif new_score < MIN_INT_VALUE:
                new_score = MIN_INT_VALUE
            
        else:
            return cls.execute_stopped(f'через неправильний формат числа кредитів')
        
        # Віднімаємо кредити у інспектора
        if not staff.admin:
            if staff.credits <= 0:
                return f'Насьогодні твоя особиста роздача кредитів вичерпана 😢'
            if staff.credits < amount:
                return f'Сьогодні тобі можна задати кредитів на: {staff.credits}. Зменш кількість видачі.'
            if repo_staff.get_by_number(target_number):
                return f'Не можна видавати сошіал кредити іншим інспекторам сошіал кредиту! 😡😡😡'
            
            staff.credits -= abs(amount)
            repo_staff.update(staff)

        # Відправляємо зображення зі зміненим балансом
        await send_changed_credit_image(msg, target, amount)
        # Оновлюємо баланс користувача
        await repo_user.update_person_async(number=target_number, score=new_score)

        return None







class MyCreditCommand(BotCommand):
    """
    Команда для показу власних кредитів.
    """

    description = "баланс кредитів"
    info = "Баланс; можна дізнатися чужий."

    @classmethod
    def command_name(cls) -> str:
        return "credit"

    @classmethod
    async def execute(cls, msg, args, by_str: str = None):
        person = await target_in_replied_msg_async(msg=msg, by_str=by_str)
        if person.error:
            person = await person_by_msg_async(msg)
        person = person.result

        return await send_credit_image(msg, person)



class HighscoreCommand(BotCommand):
    """
    Команда для показу ТОП користувачів з найвищим рейтингом.
    """

    description = "Кращі: ТОП користувачів з найвищим рейтингом."
    info = "Кращі: ними пишається партія."

    @classmethod
    def command_name(cls) -> str:
        return "best"

    @classmethod
    async def execute(self, msg, args, by_str: str = None):
        
        try:
            limit = int(args[0])
        except:
            try:
                limit = int(find_number(by_str))
            except:
                limit = 9

        if limit > 9:
            result_person = await person_by_msg_async(msg)
            if result_person.error:
                return self.execute_stopped(result_person.error)
            p = result_person.result
            highscore = repo_user.with_highest_scores(10)
            if p.number != highscore[9].number:
                return 'Не можна більше 9-ти користувачів'
            else:
                return 'Не можна більше 9-ти користувачів, але ти мій єдиний займаєш там, останнє, 10 місце ❤️ з кількістю: ' + str(p.score)
        elif limit < 1:
            return 'Не можна менше одного користувача.'

        result = await send_highscore_image(msg, limit=limit)
        if isinstance(result, str):
            return result
        return None
        #p_list = repo_user.with_highest_scores(10)
        #best_str = '\n'.join(f'{i + 1}. {p.name}: {p.score}' for i, p in enumerate(p_list))
        #return self.execute_finished(best_str)
    







class LowscoreCommand(BotCommand):
    """
    Команда для показу ТОП користувачів з найгіршим рейтингом.
    """

    description = "Гірші: ТОП користувачів з найгіршим рейтингом."
    info = "Гірші: перешкоди партії"

    @classmethod
    def command_name(cls) -> str:
        return "lowscore"

    @classmethod
    async def execute(self, msg, args, by_str: str = None):
                                    # Перевіряємо наявність аргументів
        try:                            # Спробуємо визначити ліміт з аргументів
            limit = int(args[0])            # Визначаємо ліміт користувачів
        except:                     # Якщо аргументів немає, або вони неправильні
            try:                        # Спробуємо визначити ліміт з тексту повідомлення
                limit = int(find_number(by_str))  # Визначаємо ліміт користувачів
            except:                     # Якщо ліміт не вказано або він неправильний
                limit = 9               # Встановлюємо ліміт на 9 користувачів

        # Перевіряємо, чи ліміт користувачів відповідає вимогам
        if limit > 9:
            # Отримуємо користувача, який викликав команду
            result_person = await person_by_msg_async(msg)
            if result_person.error:
                return self.execute_stopped(result_person.error)
            p = result_person.result

            # Отримуємо список користувачів з найвищим рейтингом
            lowscore = repo_user.with_lowest_scores(10)

            # Перевіряємо, чи користувач займає місце в ТОП-10
            if p.number != lowscore[9].number:
                return 'Не можна більше 9-ти користувачів'
            else:
                # Якщо користувач займає місце в ТОП-10
                return 'Не можна більше 9-ти користувачів, але ти мій другий єдиний, і займаєш там, останнє, 10 місце ❤️ з кількістю: ' + str(p.score)
        
        # Якщо ліміт менше одного користувача
        elif limit < 1:
            return 'Не можна менше одного користувача.'
        
        # Відправляємо зображення з користувачами з найгіршим рейтингом
        result = await send_lowscore_image(msg, limit=limit)
        if isinstance(result, str):
            return result
        # Повертаємо None, якщо виконання команди успішне
        return None
    




    
class IdiNakhuyCommand(BotCommand):
    """
    Команда для відправлення користувача нахуй.
    """

    description = "іді нахуй"
    min_similarity = 0.52


    @classmethod
    def command_name(cls) -> str:
        return "idi_nakhuy"

    @classmethod
    async def execute(self, msg, args, by_str: str = None):
        # Отримуємо користувача, якому потрібно відправити нахуй
        from hehbot.discord_integration import DiscordPerson
        person = (await person_by_msg_async(msg)).result
        if isinstance(person, DiscordPerson):
            person = await repo_user.by_discord_async(person.user_number)
        cooldown = Cooldown(person)

        # Перевіряємо, чи користувач може використовувати команду
        if await cooldown.get_usage_count(CooldownType.IDI):
            # Якщо користувач вже використовував команду, відправляємо відповідне повідомлення
            return 'Сам ІдІ'
        
        # Оновлюємо кулдаун
        await cooldown.update_cooldown(CooldownType.IDI, 1)
        
        # Відправляємо користувача нахуй
        NAKHUI_WIN = 10000
        amount = NAKHUI_WIN if person.score < 0 else -NAKHUI_WIN
        half = int(amount / 2)
        randomized_amount = amount + randint(-abs(half), abs(half))

        # Оновлюємо рейтинг користувача
        await send_changed_credit_image(msg, person, randomized_amount, caption='Сам ІдІ')
        await repo_user.update_person_async(person.number, score=person.score+randomized_amount)
        await repo_user.update_cooldown_async(person.number, cooldown)



class AddAdminCommand(BotCommand):
    """
    Команда для додавання нового адміністратора.
    """

    ignore = True

    @classmethod
    def command_name(cls) -> str:
        return "new_admin"

    @classmethod
    async def execute(self, msg, args, by_str: str = None):

        # Функція для виведення повідомлення про помилку
        async def get_error() -> str:
            return '''через неправильні аргументи. Очікувалось: 
/new_admin @username число_прав(0 - для інспектора, 1 - для голови) максимальна_щоденна_видача_кредитів(якщо інспектор)
(особа також повинна бути в БД бота)'''

        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return self.execute_stopped(result_person.error)
        p = result_person.result
        # Перевіряємо, чи користувач є адміністратором
        staff = repo_staff.get_by_number(p.number)
        if staff and staff.admin:

            # Перевіряємо наявність аргументів
            if args and len(args) >= 3:
                # Визначаємо ім'я користувача
                username = find_username(args[0])
                if not username:
                    return self.execute_stopped('через невірне або неіснуюче ім\'я')
                
                # Визначаємо права користувача
                try:
                    perm = int(args[1]) # 0 - інспектор, 1 - голова
                    if perm < 0 or perm > 1: # Перевіряємо, чи права вказані правильно
                        raise ValueError # Якщо ні, генеруємо помилку
                except:
                    # Якщо права вказані неправильно, виводимо повідомлення про помилку
                    return self.execute_stopped('через невірний формат числа прав (0 або 1)')
                
                # Визначаємо щоденну видачу кредитів
                try:
                    change = int(args[2]) # Щоденна видача кредитів
                    if change < 1 or change > 100000: # Перевіряємо, чи вказана видача кредитів відповідає вимогам
                        raise ValueError # Якщо ні, генеруємо помилку
                except:
                    # Якщо видача кредитів вказана неправильно, виводимо повідомлення про помилку
                    return self.execute_stopped('через невірний формат числа щоденної видачі кредитів (від 1 до 100000)')
                
                # Шукаємо користувача за ім'ям
                new_person = await repo_user.by_name_async(username)

                # Перевіряємо наявність користувача
                if not new_person:
                    # Якщо користувач не знайдений, виводимо повідомлення про помилку
                    return self.execute_stopped(f'користувач {username} відсутній в БД. Нехай щось напише мені')

                # Перевіряємо, чи користувач вже є адміністратором
                new_staff = StaffPerson(number=new_person.number, telegram=new_person.id, admin=perm, credits=change, max_credit=change)
                # Якщо користувач не є адміністратором, додаємо його до списку адміністраторів
                repo_staff.add(new_staff)

                # Повідомляємо про успішне додавання адміністратора
                if perm:
                    return f'Голова @{new_person.name} ({new_person.fullname}) успішно доданий.'
                else:
                    return f'Інспектор @{new_person.name} ({new_person.fullname}) успішно доданий.'
            else:
                # Якщо аргументи відсутні або їх кількість неправильна, виводимо повідомлення про помилку
                return self.execute_stopped(await get_error())
        else:
            # Якщо користувач не є адміністратором
            return None
        





class DeleteAdminCommand(BotCommand):
    """
    Команда для видалення адміністратора.
    """

    ignore = True

    @classmethod
    def command_name(cls) -> str:
        return "delete_admin"

    @classmethod
    async def execute(cls, msg, args, by_str: str = None):

        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return cls.execute_stopped(result_person.error)
        p = result_person.result
        # Перевіряємо, чи користувач є адміністратором
        staff_sender = repo_staff.get_by_number(p.number)
        if not staff_sender:
            return
        
        # Функція для виведення повідомлення про помилку
        async def get_error() -> str:
            return '''через неправильні аргументи. Очікувалось: 
/delete_admin @username'''


        # Перевіряємо наявність аргументів
        if not args or len(args) != 1:
            return cls.execute_stopped(await get_error())

        # Визначаємо користувача
        user = await repo_user.by_name_async(find_username(by_str)) 
        # Перевіряємо наявність користувача
        if not user:
            return cls.execute_stopped('користувач не знайдений в БД.')
        number_to_delete = user.number

        # Шукаємо користувача за ID
        staff_member = repo_staff.get_by_number(number_to_delete)
        if staff_member:
            # Якщо користувач знайдений, видаляємо його
            repo_staff.delete(number_to_delete)
            return f'Голова/інспектор @{user.name} з айді {number_to_delete} успішно видалений.'
        else:
            return cls.execute_stopped('Голова не знайдений.')
        







class GetAdminListCommand(BotCommand):
    """
    Команда для виведення списку адміністраторів.
    """

    ignore = True

    @classmethod
    def command_name(cls) -> str:
        return "admin_list"

    @classmethod
    async def execute(cls, msg, args, by_str: str = None):

        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return cls.execute_stopped(result_person.error)

        # Перевіряємо, чи користувач є адміністратором
        staff_sender = repo_staff.get_by_number(result_person.result.number if isinstance(result_person.result, Person) else result_person.result.user_number)
        if staff_sender:
            # Формуємо список адміністраторів
            member_list = []

            # Функція для визначення інформації про адміністратора
            def staff_info(member: StaffPerson) -> str:
                if not member.admin:
                    return f'інспектор {member.credits}/{member.max_credits}'
                else:
                    return 'голова'

            # Отримуємо список адміністраторів
            members = repo_staff.get_all()
            for member in members:
                person = await repo_user.by_number_async(member.number)
                number = person.number
                fullname = person.fullname
                name = person.name
                platform_id = person.id 

                # Додаємо інформацію про адміністратора до списку
                member_list.append(f'{fullname} (@{name}) - {staff_info(member)}')
            # Повертаємо список адміністраторів у вигляді рядка
            return '\n'.join(member_list)
        return None
    






    
class DeleteUserCommand(BotCommand):
    """
    Команда для видалення користувача.
    """

    ignore = True

    @classmethod
    def command_name(cls) -> str:
        return "delete_user"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None):

        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return cls.execute_stopped(result_person.error)
        p = result_person.result
        # Перевіряємо, чи користувач є адміністратором
        staff_sender = repo_staff.get_by_number(p.number)
        if not staff_sender or not staff_sender.admin:
            return
        
        # Функція для виведення повідомлення про помилку
        async def get_error() -> str:
            return '''через неправильні аргументи. Очікувалось: 
/delete_user @username (або айді особи)'''

        # Перевіряємо наявність аргументів
        if not args or len(args) != 1:
            return cls.execute_stopped(await get_error())

        # Визначаємо ідентифікатор користувача
        identifier = args[0]

        # Шукаємо користувача за ідентифікатором
        if identifier.startswith('@'):
            user = await repo_user.by_name_async(identifier[1:])  # Видалення символу '@' з імені користувача
            if not user:
                return cls.execute_stopped('користувач не знайдений в БД.')
            id_to_delete = user.id
        else:
            # Якщо ідентифікатор не починається з '@', спробуємо визначити його як числовий ID
            try:
                id_to_delete = int(identifier)
            except ValueError:
                return cls.execute_stopped('ID має бути числом.')

        # Шукаємо користувача за ID
        ex_member = repo_user.by_telegram(id_to_delete)
        if ex_member:
            # Якщо користувач знайдений, видаляємо його
            repo_user.delete(id_to_delete)
            return f'користувач @{user.name} з ID {id_to_delete} успішно видалений.'
        else:
            return cls.execute_stopped('Користувач не знайдений.')
        





class JackpotChanceCommand(BotCommand):
    """
    Команда для зміни шансу виграшу джекпоту.
    """

    ignore = True

    @classmethod
    def command_name(cls) -> str:
        return "jackpot"

    @classmethod
    async def execute(cls, msg, args, by_str: str = None):

        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return cls.execute_stopped(result_person.error)
        p = result_person.result
        # Перевіряємо, чи користувач є адміністратором
        staff_sender = repo_staff.get_by_number(p.number)
        if not staff_sender or not staff_sender.admin:
            return

        # Якщо аргументи відсутні, виводимо поточне значення шансу виграшу джекпоту
        n = find_number(by_str)
        if not n:
            return f'Зараз "1 на {heh_config.get('jackpot_chance')}" випадок отримати джекпот, коли всі елементи в автоматі однакові.'
        if n < 1 or n > 1000: # Перевіряємо, чи число в діапазоні [1, 1000]
            return 'Число повинно бути в діапазоні [1, 1000].'
        
        # Змінюємо значення шансу виграшу джекпоту
        heh_config.set('jackpot_chance', n)

        # Повідомляємо про зміну значення
        return f'Нове значення "1 на {n}" задано для джекпоту.'
        






class ScoreHistoryCommand(BotCommand):
    """
    Команда для відображення історії рейтингу користувача.
    """

    description = "Історія: статистика кращих/гірших"
    info = "Історія: 1-ше число — кількість днів. 'кращі' або 'гірші' виведе топ. 2-ге число — кількість учасників."

    @classmethod
    def command_name(cls) -> str:
        return "history"

    @classmethod
    async def execute(cls, msg, args, by_str: str = None):
        
        result_target = await target_in_replied_msg_async(msg, by_str)
        if result_target.error:
            result_person = await person_by_msg_async(msg)
            if result_person.error:
                return cls.execute_stopped(result_person.error)
            target = result_person.result
        else:
            target = result_target.result

        # Шукаємо кількість днів та учасників
        amount_days = find_number(by_str)
        amount_persons = find_number(by_str, 1)

        # Якщо не вказано кількість днів, виводимо історію за 366 днів
        if not amount_days or amount_days < 1:
            amount_days = 366
            
        if not amount_persons:
            amount_persons = 10 # Якщо не вказано кількість учасників, виводимо топ-10
        elif amount_persons > 10: # Максимальна кількість учасників — 10
            return 'Не можна більше 10-ти користувачів.'
        elif amount_persons < 1: # Мінімальна кількість учасників — 1
            amount_persons = 1 # Якщо вказано менше 1, виводимо тільки одного користувача

        from hehbot.hehbot_utils import compare_words
        # Перевіряємо на наявність аргументів "кращі" або "гірші"
        if compare_words(['кращі', 'плюс', 'топ', 'best', 'кращих', 'краще'], by_str.split()):
            photo_path = await plot_top_history(amount_persons, amount_days, show_highscore=True)
        elif compare_words(['гірші', 'мінус', 'lowscore', 'гірших', 'гірше'], by_str.split()):
            photo_path = await plot_top_history(amount_persons, amount_days, show_highscore=False)
        else:
            # Якщо не вказано "кращі" або "гірші", виводимо історію користувача
            photo_path = await plot_user_history(target.number, amount_days)

        # Відправляємо фото з історією користувача
        if photo_path:
            photo = aiogram.types.FSInputFile(path=photo_path)
            await msg.reply_photo(photo=photo)
            return None
        
        # Якщо фото не знайдено, повертаємо відповідне повідомлення
        return 'Замало активності для малювання історії.'








class HelpCommand(BotCommand):
    """
    Команда для інструкції.
    """

    description = 'Допомога'
    info = "Допомога/команди у ПП."
    min_similarity = 0.42

    @classmethod
    def command_name(cls) -> str:
        return 'help'

    @classmethod
    async def execute(cls, msg, args, by_str: str = None):
        # Шукаємо користувача
        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return cls.execute_stopped(result_person.error)
        person = result_person.result
        staff = repo_staff.get_by_number(person.number if isinstance(person, Person) else person.user_number)
        
        inspector_text = None
        if staff:
            inspector_text = f'''
Інструкція для інспекторів:
/give <число> - дати кредити ({staff.credits} з {staff.max_credits})

ШІ:
/rate - оцінити повідомлення користувача (один раз на день);
/system <текст> - системне повідомлення: як діятиме Суддя (використовуй з розумом);
/system - останні системні повідомлення;
/забудь - почистити спогади і системні повідомлення Судді;'''

        text = f'''🔍 Магія Слова "Суд"
Використовуй слово "суд" перед командою, щоб зробити її більш захопливою. 
Наприклад, "суд кращі 9" покаже топ-9 переможців. 
Можна впорядковувати аргументи як тобі зручно, 
наприклад, "суд історія за 7 днів 4 гірших" для історії твоїх гірших моментів.
                               
🔗 Зв'язок через Відповідь
А ще ти можеш взаємодіяти з іншими гравцями, відповідаючи на їхні повідомлення з командою. 
Так, якщо хочеш кинути виклик або показати баланс не вводячи їх нікнейм, 
просто відповідай на їхнє повідомлення з потрібною командою!

🎰 Захоплюючий Ігровий Автомат
Відчуй азарт! Просто надішли 🎰 і дай шанс своїй удачі засяяти.

/credit - 💰 соціальний Статус.

/best - 🏆 Хто тут Чемпіон? Додай цифру від 1 до 9, і ми покажемо саме стільки гравців.
/lowscore - 👎 А хто на дні? Ну і, звісно, покаже тих, хто не мав такого везіння. 
Працює як і /best, тільки для топу... найгірших.

/bet <кількість/"все"> - 🎲 Ставимо Все на Кон!
👥 Хочеш гру з другом? Просто вкажи його після команди.

/history <366 днів кращі 5> - 📚 Історія твоїх Пригод
Вкажи кількість днів для перегляду, 
а також "best" чи "lowscore" для створення топу до 10 осіб. 
Друге число означає кількість учасників у топі. 
Можна вказати іншого користувача, щоб побачити його історію. 
Порядок елементів у команді неважливий, 
головне це порядок "кількість_днів, кількість_учасників".

{inspector_text if inspector_text else ''}'''
        
        if isinstance(msg, aiogram.types.Message):
            try:
                await bot.send_message(msg.from_user.id, text)
            except:
                await msg.reply('Відпиши мені в ПП, я туди кину.')

        elif isinstance(msg, discord.Message):
            discord_user = await discord_bot.fetch_user(msg.author.id)
            try:
                if discord_user:
                    # Спроба відправити приватне повідомлення
                    await discord_user.send(text)
                else:
                    pass
            except discord.Forbidden:
                # Якщо користувач має заблоковані приватні повідомлення від ботів
                await msg.channel.send(f'{discord_user.mention}, Відпиши мені в ПП, я туди кину.')
        return None




        



class SystemTextCommand(BotCommand):
    """
    Команда для системного тексту.
    """
    ignore = True


    @classmethod
    def command_name(cls) -> str:
        ignore = True

        return "system"

    @classmethod
    async def execute(cls, msg, args, by_str: str = None):
        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return cls.execute_stopped(result_person.error)
        target = result_person.result
        # Перевіряємо, чи користувач є адміністратором
        staff_sender = repo_staff.get_by_number(target.number if isinstance(target, Person) else target.user_number)
        if not staff_sender:
            return 'Лише інспектори так можуть.'
        
        # Генерація тексту
        from hehbot.gpt import GPT, repo_conversation, ConversationMessage
        from hehbot.hehbot_utils import remove_court_and_username
        by_str = by_str.replace('/system', '')
        group_id = msg.chat.id if isinstance(msg, aiogram.types.Message) else msg.channel.id

        prompt = remove_court_and_username(by_str)
        prompt = prompt.strip()

        max_system_text_len = 500
        if len(prompt) > max_system_text_len:
            return 'Текст занадто довгий. Максимальна довжина - {} символів.'.format(max_system_text_len)

        if len(prompt) < 7:
            latest_system_msgs = repo_conversation.get_messages(group_id)
            ret = []
            for m in latest_system_msgs:
                if m.lifetime < 100:
                    ret.append(m.text)

            if not ret:
                return 'Системні повідомлення відсутні.'
            return 'Системні повідомлення: ' + '\n\n'.join(ret)

        # Відправляємо системне повідомлення
        repo_conversation.add_message(ConversationMessage(user_number=target.number if (isinstance(target, Person)) else target.user_number, text=prompt, role='system', group_id=group_id))
        
        if prompt:
            return 'Напиши мені тепер щось щоб перевірити.'
        else:
            return 'Щось пішло не так під час генерації тексту.'
        




class RateUserCommand(BotCommand):
    """
    Команда для оцінки користувача.
    """
    ignore = True


    @classmethod
    def command_name(cls) -> str:
        return "rate"

    @classmethod
    async def execute(cls, msg, args, by_str: str = None):
        
        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return cls.execute_stopped(result_person.error)
        person = result_person.result
        # Перевіряємо, чи користувач є адміністратором
        staff_sender = repo_staff.get_by_number(person.number if isinstance(person, Person) else person.user_number)
        if not staff_sender:
            return 'Лише інспектори так можуть.'
        
        result_target = await target_in_replied_msg_async(msg, by_str)
        if result_target.error:
            return result_target.error
        target = result_target.result
        
        # Генерація тексту
        from hehbot.gpt import GPT, repo_conversation, ConversationMessage
        from hehbot.client import Cooldown, CooldownType
         
        # Якщо користувач вже оцінив сьогодні, виводимо відповідне повідомлення
        if not staff_sender.admin:
            cd = Cooldown(person)
            usage_count = await cd.get_usage_count(CooldownType.RATE)
            if usage_count > 0:
                return 'Оцінка сьогодні вже була проведена.'
            usage_count += 1
            await cd.update_cooldown(CooldownType.RATE, usage_count)
            await repo_user.update_cooldown_async(person.number, cd)
        
        async def process_message(msg):
            prompt_body = ''
            if isinstance(msg, aiogram.types.Message):
                # Обробка для Telegram
                if msg.reply_to_message:
                    if not msg.reply_to_message.text and not msg.reply_to_message.caption:
                        return 'Твоя відповідь повинна бути саме на текстове повідомлення щоб оцінити.'
                    prompt_body = msg.reply_to_message.text if msg.reply_to_message.text else msg.reply_to_message.caption
                else:
                    return 'Треба відповіддю на повідомлення для оцінки.'
            elif isinstance(msg, discord.Message):
                # Обробка для Discord
                if msg.reference:
                    ref_msg = await msg.channel.fetch_message(msg.reference.message_id)
                    if not ref_msg.content:
                        return 'Твоя відповідь повинна бути саме на текстове повідомлення щоб оцінити.'
                    prompt_body = ref_msg.content
                else:
                    return 'Треба відповіддю на повідомлення для оцінки.'
            return prompt_body
        

        
        prompt_start = f'Оціни текст і напиши бал від -10000 до 10000, а потім пояснення. як би ти оцінив текст: '
        prompt_body = await process_message(msg)

        prompt = prompt_start + prompt_body

        from hehbot import repo_msg
        from hehbot.memory import ChatMessage, repo_msg
        
        if isinstance(msg, aiogram.types.Message):
            group_id = msg.chat.id 
        elif isinstance(msg, discord.Message):
            group_id = msg.channel.id
        user_number = target.number if isinstance(target, Person) else target.user_number
        chat_messages = repo_msg.get_all_messages_by_group(group_id, 10)
        

        if isinstance(chat_messages, list):
            for message in chat_messages:
                repo_conversation.add_message(ConversationMessage(user_number=user_number, text=message.text, role='user', group_id=group_id, date=message.date))

        messages = []

        for m in repo_conversation.get_messages(group_id=group_id):
            if m.role == 'assistant':
                messages.append({"role": m.role, "content": m.text})
            else:
                try:
                    if m.role == 'system':
                        messages.append({"role": m.role, "content": m.text})
                        continue
                    person = await repo_user.by_number_async(m.number)
                    
                    messages.append({"role": m.role, "content": f'{person.fullname} каже: ' + m.text})
                except:
                    messages.append({"role": m.role, "content": m.text})
        
        messages.append({"role": "system", "content": prompt})

        result = await GPT.one_request(messages, 700)    
        
        if result:
            amount = find_number(result)
            if not amount:
                return result

            await send_changed_credit_image(msg, target, amount, caption=result)

            await repo_user.update_person_async(number=user_number, score=target.score+amount)

            return None
        else:
            return 'Щось пішло не так під час генерації тексту.'







class ResetConversionCommand(BotCommand):
    """
    Команда для скидання розмови.
    """
    ignore = True


    @classmethod
    def command_name(cls) -> str:
        return "забудь"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None):
        
        # Шукаємо користувача
        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return cls.execute_stopped(result_person.error)
        person = result_person.result
        staff = repo_staff.get_by_number(person.number if isinstance(person, Person) else person.user_number)
        if not staff:
            return 'Лише інспектори так можуть.'
        
        from hehbot.gpt import GPT, repo_conversation
        repo_conversation.delete_messages_by_group(msg)

        return 'Тойво, забув.'










class MakebetCommand(BotCommand):
    """
    Команда для зроблення ставки.
    """

    description = "ставлю"
    info = '''Зробити ставку і зіграти.
Якщо без вказаної особи, то будь-хто може прийняти.'''
    min_similarity = 0.75

    @classmethod
    def command_name(cls) -> str:
        return "bet"

    @classmethod
    async def execute(cls, msg, args, by_str: str = None):
        if not isinstance(msg, aiogram.types.Message):
            return 'Ця команда поки не підтримується в Discord.'
        if heh_config.get('tg_bet_active') == True:
            return 'Ставка вже активна. Почекай, поки вона закінчиться.'
        
        person = repo_user.by_telegram(msg.from_user.id)

        MAX_BET = 500
        
        target = None # Особа, на яку ставиться
        target_username = find_username(by_str) # Пошук користувача за ім'ям
        amount = find_number(by_str) # Пошук числа в рядку

        if amount and amount > MAX_BET and person.score == amount:
            return f'Використовуй в команді "всі" для ставки всіх кредитів, а не як ти зробив.'

        # Пошук користувача за ім'ям
        if target_username:
            target = await repo_user.by_name_async(target_username)
        if not target:
            target_msg = msg.reply_to_message # Пошук користувача за відповіддю на повідомлення
        
            if target_msg:  # Якщо знайдено користувача за відповіддю на повідомлення
                target = await repo_user.update_by_telegram_async(target_msg)
            
                if not target: # Якщо користувача не знайдено
                    return cls.execute_stopped(f'щось пішло не так під час додавання {target_msg.from_user.full_name if target_msg.from_user else "(Не можу вимовити ім'я)"} в мою базу даних')

        if not amount: # Якщо не знайдено числа в рядку
            from hehbot.hehbot_utils import compare_words
            # Перевірка на наявність слів "всі", "все", "всьо", "all" та відсутність слів "ні", "не", "нє", "not"
            if compare_words(['всі', 'все', 'всьо', 'all'], by_str.split()) and not compare_words(['ні', 'не', 'нє', 'not'], by_str.split()):
                amount = person.score
                if amount < MAX_BET:
                    amount = MAX_BET
            else: # Якщо не знайдено числа в рядку, а також слів "всі", "все", "всьо", то повідомлення про помилку
                return cls.execute_stopped(f'через неправильний формат числа кредитів')

        # Перевірка на мінімальну ставку
        if amount < 100:
            return f'Давай нормально грати: які ще {amount} кредитів? Я приймаю лише 100 і більше'

        # Перевірка на максимальну ставку
        
        if amount > MAX_BET:
            if person.score < amount:
                return f'В тебе зараз {person.score} кредитів' + (' які можна поставити.' if person.score > MAX_BET else f', максимум ставки: {MAX_BET}.')
            elif target and target.score < amount:
                return f'Ти ставиш {amount}, а у {target.fullname} зараз {target.score} кредитів' + (' які можна поставити.' if target.score > MAX_BET else f', максимум ставки: {MAX_BET}.')
            
            
        # Перевірка на кількість ставок
        cd = Cooldown(person)
        bet_count = await cd.get_usage_count(CooldownType.BET)

        if bet_count >= 3:
            return f'Сьогодні ти не можеш укладати парі, лише приймати.'
        
        # Додавання кулдауну ставки
        bet_count += 1
        await cd.update_cooldown(CooldownType.BET, bet_count)
        await repo_user.update_cooldown_async(person.number, cd)
        
        # Логіка для приватної гри
        if target:
            bet_message = await msg.answer(f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nі запрошує {target.fullname} (@{target.name})", parse_mode='html')
            
            keyboard = InlineKeyboardBuilder()

            # Створення кнопок для відповіді на ставку

            # Кнопка "Ігнорувати" для відмови від ставки
            keyboard.button(text="Ігнорувати",
                callback_data=f"ignore:{person.id}:{target.id}:{msg.chat.id}:{bet_message.message_id}"),
            
            # Кнопка "Прийняти" для прийняття ставки
            keyboard.button(text="Прийняти",
                callback_data=f"accept:{amount}:{person.id}:{target.id}:{msg.chat.id}:{bet_message.message_id}")

            # Оновлення повідомлення з текстом ставки та кнопками
            await bet_message.edit_text(f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nі запрошує {target.fullname} (@{target.name})", 
                reply_markup=keyboard.as_markup(), 
                parse_mode='html')
            
            # Функція для оновлення повідомлення з таймером
            async def update_message():
                for remaining in range(60, -1, -5):  # хвилина з оновленням кожні 5 секунд
                    if remaining % 15 == 0:  # Оновлення тексту повідомлення кожні 15 секунд для зменшення навантаження на API
                        try:
                            # Оновлення тексту повідомлення з таймером
                            await bet_message.edit_text(
                                f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nі запрошує {target.fullname} (@{target.name})\nЗалишилося: {remaining} секунд", 
                                reply_markup=keyboard.as_markup(), 
                                parse_mode='html')
                        except:
                            return                
                    await asyncio.sleep(5) # Очікування 5 секунд
                try:
                    heh_config.set('tg_bet_active', False)
                    await bet_message.edit_text(text=f'Час вичерпано: {target.fullname} не хоче грати :\'(')  # після завершення часу очікування

                    await cd.update_cooldown(CooldownType.BET, bet_count-1) # Видалення кулдауну ставки
                    await repo_user.update_cooldown_async(person.number, cd) # Оновлення кулдауну користувача
                except:
                    pass   # it's okay
            
            # Запуск функції оновлення повідомлення з таймером
            asyncio.create_task(update_message())



        else: # Логіка для публічної гри
            disclaimer_text = f'Можуть приймати ті, в кого є {amount} кредитів.\n' if amount > MAX_BET else ''

            bet_message = await msg.answer(f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nЧи хтось хоче прийняти виклик?{disclaimer_text}", parse_mode='html')
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="Прийняти виклик", 
                callback_data=f"accept:{amount}:{person.id}:0:{msg.chat.id}:{bet_message.message_id}")

            await bet_message.edit_text(f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nЧи хтось хоче прийняти виклик?{disclaimer_text}", 
                reply_markup=keyboard.as_markup(), 
                parse_mode='html')
            
            # Функція для оновлення повідомлення з таймером
            async def update_message():
                for remaining in range(60, -1, -5):  # хвилина з оновленням кожні 5 секунд
                    if remaining % 15 == 0:  # Оновлення тексту повідомлення кожні 15 секунд для зменшення навантаження на API
                        try:
                            # Оновлення тексту повідомлення з таймером
                            await bet_message.edit_text(
                                f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nЧи хтось хоче прийняти виклик?\n{disclaimer_text}Залишилося: {remaining} секунд", 
                                reply_markup=keyboard.as_markup(), 
                                parse_mode='html')
                        except:
                            return # Вихід з функції при помилці
                    await asyncio.sleep(5) # Очікування 5 секунд
                try:
                    heh_config.set('tg_bet_active', False)
                    await bet_message.edit_text(text=f'Час вичерпано: ніхто не хоче грати :(')  # після завершення часу очікування

                    await cd.update_cooldown(CooldownType.BET, bet_count-1)
                    await repo_user.update_cooldown_async(person.number, cd)
                except:
                    pass   # it's okay
            
            # Запуск функції оновлення повідомлення з таймером
            asyncio.create_task(update_message())
        return None # Вихід без повідомлення про помилку
    
async def safe_send_dice(chat_id: int, emoji: str):
    """Функція для безпечної відправки кубика."""

    try:
        msg = await bot.send_dice(chat_id, emoji=emoji)
        return msg
    except TelegramRetryAfter as e:
        print(f"Спроба перевищила ліміт, чекаємо {e.retry_after} секунд.")
        await asyncio.sleep(e.retry_after)  # Чекаємо рекомендований час
        await safe_send_dice(chat_id, emoji)  # Спроба відправити ще раз після паузи
    except TelegramAPIError as e:
        print(f"Сталася помилка Telegram API: {e}")

async def safe_send_text(chat_id: int, text: str, parse_mode = None):
    """Функція для безпечної відправки тексту."""

    try:
        msg = await bot.send_message(chat_id, text=text)
        return msg
    
    except TelegramRetryAfter as e:
        print(f"Спроба перевищила ліміт, чекаємо {e.retry_after} секунд.")
        await asyncio.sleep(e.retry_after)  # Чекаємо рекомендований час
        await safe_send_text(chat_id, text, parse_mode)  # Спроба відправити ще раз після паузи

    except TelegramAPIError as e:
        print(f"Сталася помилка Telegram API: {e}")

async def safe_answer_callback_query(callback_query_id):
    """Функція для безпечної відповіді на запит зворотного виклику."""

    try:
        callback = await bot.answer_callback_query(callback_query_id)
        return callback
    
    except TelegramRetryAfter as e:
        print(f"Спроба перевищила ліміт, чекаємо {e.retry_after} секунд.")
        await asyncio.sleep(e.retry_after)  # Чекаємо рекомендований час
        await safe_answer_callback_query(callback_query_id)  # Спроба відправити ще раз після паузи

    except TelegramAPIError as e:
        print(f"Сталася помилка Telegram API: {e}")

@dp.callback_query(lambda c: c.data and c.data.startswith('accept'))
async def handle_accept(callback_query: aiogram.types.CallbackQuery):
    """Обробник для прийняття ставки."""

    if heh_config.get('tg_bet_active') == True:
        return None

    await safe_answer_callback_query(callback_query.id)

    # Розбивка даних зворотного виклику
    _, amount, user_id, target_id, chat_id, bet_message_id = callback_query.data.split(':')
    # Перетворення даних у числа
    amount, user_id, target_id, chat_id, bet_message_id = int(amount), int(user_id), int(target_id), int(chat_id), int(bet_message_id)
    
    if target_id == 0:
        pass
    elif not target_id == callback_query.from_user.id:
        return None
    
    # Отримання користувача з бази даних
    target = repo_user.by_telegram(callback_query.from_user.id)
    if target:
        if target.id == user_id:
            return None
    else:
        t = callback_query.from_user
        target = Person(t.id, t.full_name, name=t.username)
        repo_user.add(target)
    
    if amount > 500 and target.score < amount:
        return None
    
    # Початок ставки
    heh_config.set('tg_bet_active', True)
    
    person = repo_user.by_telegram(user_id)

    # Оновлення тексту повідомлення ставки, повідомляючи, що ставку прийнято
    await bot.delete_message(chat_id=chat_id, message_id=bet_message_id)

    await safe_send_text(chat_id=chat_id, text=f"Ставку прийнято користувачем {target.fullname} (@{target.name}).", parse_mode='HTML')
    
    # Тут логіка обробки прийняття ставки...
    # Відправка кубиків
    await asyncio.sleep(3)  # Затримка перед відправленням першого кубика
    msg1 = await safe_send_dice(chat_id, emoji="🎲")
    await asyncio.sleep(3)  # Затримка перед відправленням другого кубика
    msg2 = await safe_send_dice(chat_id, emoji="🎲")
    await asyncio.sleep(4)
        
    #await cd.update_cooldown(CooldownType.BET, bet_count+1)

    heh_config.set('tg_bet_active', False)

    target_credits = 0
    person_credits = 0

    if amount > 500:
        not_enough = None
        if person.score < amount:
            not_enough = person
        elif target.score < amount:
            not_enough = target
        
        if not_enough:
            await safe_send_text(chat_id=chat_id, text=f'Кредити не переписані. {not_enough.name} не вистачає, бо має {not_enough.score} кредитів \n(Ставка {amount})')
            return None
        

    #await repo_user.update_cooldown(cd)
    # msg1 > msg2
    if msg1.dice.value > msg2.dice.value:
        person_credits = amount
        target_credits = -amount

    # msg1 < msg2
    elif msg1.dice.value < msg2.dice.value:
        person_credits = -amount
        target_credits = amount

    # msg1 == msg2
    else:
        n = msg1.dice.value

        def scale_value(x) -> int:
            """Функція для масштабування значення.
            Приймає значення x, повертає масштабоване значення.
            Інтерполяція логарифмічною функцією.
            """
            return math.ceil(200 + math.log(x, 10) * 50)

        if n == 1:
            target_credits = person_credits = -scale_value(amount)
        elif n == 6:
            target_credits = person_credits = scale_value(amount)
        else:
            await safe_send_text(chat_id=chat_id, text='Ніхто не переміг: кредити не переписані.')
            return None

    # Функція для переписування кредитів
    async def give(person: Person, credits: int):
        await repo_user.update_person_async(person.number, score=person.score+credits)
        
    await give(person, person_credits)
    await give(target, target_credits)

    if person.score > 10000000000:
        person.score = '∞'
    elif person.score < -10000000000:
        person.score = '-∞'
    if target.score > 10000000000:
        target.score = '∞'
    elif target.score < -10000000000:
        target.score = '-∞'


    await safe_send_text(chat_id=chat_id, text=f'''
Результат:
{person.fullname} має {person.score} і отримує {person_credits}
{target.fullname} має {target.score} і отримує {target_credits}''', parse_mode='html')

@dp.callback_query(lambda c: c.data and c.data.startswith('ignore'))
async def handle_ignore(callback_query: aiogram.types.CallbackQuery):
    await safe_answer_callback_query(callback_query.id)
    _, user_id, target_id, chat_id, bet_message_id = callback_query.data.split(':')
    user_id, target_id, chat_id, bet_message_id = int(user_id), int(target_id), int(chat_id), int(bet_message_id)

    if target_id == 0 or not callback_query.from_user.id == target_id:
        return None
    
    try:
        await safe_send_text(chat_id, text=f"Ставку проігноровано користувачем.", parse_mode='HTML')
        # Оновлення тексту повідомлення ставки, повідомляючи, що ставку ігнорують
        await bot.delete_message(chat_id=chat_id, message_id=bet_message_id)

    except TelegramRetryAfter as e:
        print(f"Спроба перевищила ліміт, чекаємо {e.retry_after} секунд.")
        await asyncio.sleep(e.retry_after)  # Чекаємо рекомендований час
        await bot.edit_message_text(chat_id=chat_id, message_id=bet_message_id,
            text=f"Ставку проігноровано користувачем.", parse_mode='HTML')

class AdminCommand(BotCommand):
    """
    Команда допомоги для адмінів (список команд).
    """

    ignore = True

    @classmethod
    def command_name(cls) -> str:
        return "admin"

    @classmethod
    async def execute(self, msg, args, by_str: str = None):

        result_person = await person_by_msg_async(msg)
        if result_person.error:
            return self.execute_stopped(result_person.error)
        p = result_person.result
        # Перевіряємо, чи користувач є адміністратором
        staff = repo_staff.get_by_number(p.number)
        if not (staff and staff.admin):
            return None
        
        return '''
число_прав (0 - для інспектора, 1 - для голови)
новий:  /new_admin  @username  число_прав  максимальна_щоденна_видача_кредитів(якщо інспектор)
видалити:  /delete_admin  @username
список:  /admin_list
видалити користувача назовсім з БД:  /delete_user  @username(або айді особи)

інші команди:
/забудь
/rate
/system
/system <текст>
'''


# Ініціалізація команд
    
# client commands
help_command = HelpCommand()
check_credit_command = MyCreditCommand()
highscore_command = HighscoreCommand()
lowscore_command = LowscoreCommand()
makebet_command = MakebetCommand()
idi_nakhuy_command = IdiNakhuyCommand()
jackpot_chance_command = JackpotChanceCommand()
score_history_command = ScoreHistoryCommand()

# connect_command = ConnectCommand()
# verify_command = VerifyCommand()

# mod command
change_credit_command = SetCreditCommand()
reset_conversion_command = ResetConversionCommand()
system_text_command = SystemTextCommand()
rate_user_command = RateUserCommand()

# admin commands
add_admin_command = AddAdminCommand()
delete_admin_command = DeleteAdminCommand()
admin_list_command = GetAdminListCommand()
delete_user_command = DeleteUserCommand()
admin_command = AdminCommand() # довідка-допомога