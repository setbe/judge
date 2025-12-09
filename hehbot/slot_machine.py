from hehbot.heh_config import heh_config
from hehbot.score_gamedesign import update_users_scores_if_inactive
from hehbot import repo_user

from random import randint
from collections import Counter
from PIL import Image, ImageFont, ImageDraw

from hehbot.env_service import dp
import aiogram, asyncio
from aiogram import F
from aiogram.enums import DiceEmoji
from aiogram.types import Message

slot_machine_path = 'img/slot_machine/'

# bar, grape, lemon, seven
CASINO_EMOJI = ["🅱️", "🍇", "🍋", "7️⃣"]
CASINO_WIN0 = 2000
CASINO_WIN1 = 5000
CASINO_WIN2 = 10000
CASINO_WIN3 = 25000 # 25k
CASINO_WIN4 = 100000 # 100k

async def draw_slot_machine_image_async(user_id: int, reward: int, randomized_reward: int):        
    # Виконуємо блокуючі операції з PIL в окремому потоці
    def create_animated_gif(user_id: int, reward: int):
        if reward < 0:
            reward_str = 'm' + str(abs(reward))
            color = (200, 50, 50)
        else:
            reward_str = str(reward)
            color = (50, 200, 50)

        image_path = f"{slot_machine_path}{reward_str}.jpg"
        base_image = Image.open(image_path)
        
        text = str(randomized_reward) if randomized_reward < 0 else '+' + str(randomized_reward)
        font_path = "font/impact.ttf"
        font_size = 128
        
        outline_thickness, outline_color = 5, (0, 0, 0)
      
        draw = ImageDraw.Draw(base_image)
        font = ImageFont.truetype(font_path, font_size)
        text_width = draw.textlength(text, font=font)
        text_position = ((base_image.width - text_width) // 1.5, (base_image.height - font_size) // 2.6)

        for x in range(-outline_thickness, outline_thickness + 1):
            for y in range(-outline_thickness, outline_thickness + 1):
                draw.text((text_position[0] + x, text_position[1] + y), text, font=font, fill=outline_color)
            
        draw.text(text_position, text, font=font, fill=color)

        output_path = f"{slot_machine_path}users/{user_id}.jpeg"
        base_image.save(output_path, format='JPEG', optimize=True)

        return output_path

    return await asyncio.to_thread(create_animated_gif, user_id, reward)
    #except:
        #return None

async def is_jackpot() -> bool:
    return randint(1, heh_config.get('jackpot_chance')) == 1

# Перевірка на наявність двох однакових емодзі в ряду
def has_two_in_a_row(slots, emojis):
    for emoji in emojis:
        if slots.count(emoji) >= 2 and (slots[0] == slots[1] == emoji or slots[1] == slots[2] == emoji):
            return True
    return False

async def check_reward(reward: int) -> bool:
    if reward == 100 or reward == 500 or reward == 1000 or reward >= 5000:
        return True
    return False

async def send_slot_machine(msg: aiogram.types.Message, slots: list[str]):    
    # Ініціалізація зміни балансу
    amount = 0
    # Перевірка на спеціальні комбінації
    if slots == ["🍋", "🍋", "🍋"] or slots == ["🅱️", "🅱️", "🅱️"]:
        amount = -CASINO_WIN3 # -25k
        if await is_jackpot():
            amount = -CASINO_WIN4 # -100k
    elif slots == ["🍇", "🍇", "🍇"] or slots == ["7️⃣", "7️⃣", "7️⃣"]:
        amount = CASINO_WIN3 # 25k
        if await is_jackpot():
            amount = CASINO_WIN4 # 100k
    elif has_two_in_a_row(slots, ["🍋", "🅱️"]):
        amount = -CASINO_WIN2
    elif has_two_in_a_row(slots, ["🍇", "7️⃣"]):
        amount = CASINO_WIN2
    else:
        counts = Counter(slots)
        # Додаткові умови для двох однакових емодзі
        if counts["🍋"] == 2 or counts["🅱️"] == 2:
            amount = -CASINO_WIN1
        elif counts["🍇"] == 2 or counts["7️⃣"] == 2:
            amount = CASINO_WIN1
        else:
            await asyncio.sleep(2)
            # Врахування інших комбінацій
            if counts["🍋"] > 0 and counts["🅱️"] > 0:
                amount = -CASINO_WIN0
            else:
                amount = CASINO_WIN1

    async def randomize(reward: int):
        half = int(reward / 2)
        if reward == 0:
            return 0
        elif reward >= CASINO_WIN4:
            return CASINO_WIN4
        elif reward <= -CASINO_WIN4:
            return -CASINO_WIN4
        elif reward > 0:
            return reward + randint(-half, half)
        else:
            return reward + randint(half, -half)

    user = repo_user.by_telegram(msg.from_user.id)
    randomized_score = await randomize(amount)
    balance_str = f'\n(Новий баланс: {str(user.score + randomized_score)})'

    if amount == CASINO_WIN4:
        await msg.reply_photo(photo=aiogram.types.FSInputFile(slot_machine_path+'jackpot.jpg'), caption='Це — скарб!')
    elif amount == -CASINO_WIN4:
        await msg.reply_photo(photo=aiogram.types.FSInputFile(slot_machine_path+'mjackpot.jpg'), 
                              caption='''Ви програли. Ваші кредити вже в моїй кишені.''')
    elif amount == 0:
        return 'Отакої! Отримано 0 кредитів! Нова спроба завтра'
    
    # Якщо виграш або програш менше 5000 -> просто пишемо текст
    if abs(amount) < CASINO_WIN1:
        await msg.reply(
            f"Отримано {randomized_score} соціальних кредитів! Нова спроба завтра.\n"
            f"(Новий баланс: {user.score + randomized_score})"
        )
        await repo_user.update_person_async(user.number, score=user.score + randomized_score)
        return
    
    # Якщо >= 5000 -> малюємо картинку
    img_path = await draw_slot_machine_image_async(user.id, amount, randomized_score)
    if img_path:
        await msg.reply_photo(
            aiogram.types.FSInputFile(img_path),
            caption=f'Нова спроба завтра. {balance_str}'
        )
        await repo_user.update_person_async(user.number, score=user.score + randomized_score)
        return

    await msg.reply(f'Отримано {randomized_score} соціальних кредитів за вашу гру! Нова спроба завтра. {balance_str}')
        
    await repo_user.update_person_async(user.number, score=user.score + randomized_score)

    msg_inactive = await update_users_scores_if_inactive(repo_user.with_highest_scores(9))
    if msg_inactive:
        await msg.reply(msg_inactive)
    return None

def decode_slot_machine_value(value: int) -> list[str]:
    value -= 1
    result = []
    for _ in range(3):
        result.append(CASINO_EMOJI[value % 4])
        value //= 4
    return result

@dp.message(
    F.dice[F.emoji == DiceEmoji.SLOT_MACHINE].value.cast(decode_slot_machine_value).as_("slots")
)
async def handle_slot_machine(msg: Message, slots: list[str]):
    person = await repo_user.update_by_telegram_async(msg)
    if person and not msg.is_automatic_forward and not msg.forward_origin:
        try:
            cooldowns = person.cooldown.split()
        except:
            cooldowns = []

        if not 'slots' in cooldowns:
            result = await send_slot_machine(msg, slots)
            if result:
                await msg.reply(result)
            await repo_user.update_person_async(person.number, cooldown='slots '+person.cooldown)
        else:
            await msg.reply('Почекаєш до наступної доби (до 06:00)')
    else:
        if not person:
            await msg.reply('Я не можу тебе додати в базу даних через внутрішню помилку.')