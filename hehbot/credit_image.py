from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np

import aiohttp
import aiogram, discord
from discord.ext import commands

import asyncio, requests

from io import BytesIO
import os
from hehbot.discord_integration import discord_repo, DiscordPerson
from hehbot.hehbot_utils import person_by_msg_async, target_in_replied_msg_async
from hehbot.client import repo_user, Person
from hehbot.env_service import bot

def is_similar_to_green(color: tuple[int, int, int]) -> bool:
    green_rgb = (0, 255, 0)
    threshold = 100  # Поріг схожості, може бути налаштований
    distance = sum((c1 - c2) ** 2 for c1, c2 in zip(color, green_rgb)) ** 0.5
    return distance < threshold

def is_similar_to_red(color: tuple[int, int, int]) -> bool:
    red_rgb = (255, 0, 0)
    threshold = 100  # Поріг схожості, може бути налаштований
    distance = sum((c1 - c2) ** 2 for c1, c2 in zip(color, red_rgb)) ** 0.5
    return distance < threshold


def is_bg_dark(color):
    r, g, b = map(int, color)  # Переконайтесь, що r, g, b є цілими числами

    # Використання формули для визначення яскравості кольору
    luminance = 0.299 * r + 0.587 * g + 0.114 * b

    # Якщо яскравість менше 128, фон темний і текст повинен бути білим
    # В іншому випадку, фон світлий і текст повинен бути чорним
    return False if luminance < 128 else True

async def adjust_brightness(image, factor):
    def blocking_adjust_brightness():
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)
    return await asyncio.to_thread(blocking_adjust_brightness)

async def get_dominant_color_async(image_bytes, brightness_adjustment=False) -> tuple[int, int, int]:
    async def blocking_operations(img):
        if brightness_adjustment:
            img = await adjust_brightness(img, 0.75)  # Зменшуємо яскравість
        img = img.resize((140, 140))
        img = img.convert('RGB')

        pixels = np.array(img)

        def is_not_gray_or_white(color):
            return True
            #r, g, b = map(int, color)  # Переконайтесь, що r, g, b є цілими числами
            #gray_threshold = 10
            #white_threshold = 200
            ## Використання np.abs для уникнення переповнення при відніманні
            #if np.abs(r - g) < gray_threshold and np.abs(g - b) < gray_threshold and np.abs(r - b) < gray_threshold:
            #    return False
            #if r > white_threshold and g > white_threshold and b > white_threshold:
            #    return False
            #return True

        colors, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
        filtered_colors = [(color, count) for color, count in zip(colors, counts) if is_not_gray_or_white(color)]

        if filtered_colors:
            dominant_color = max(filtered_colors, key=lambda x: x[1])[0]
            return (dominant_color[0], dominant_color[1], dominant_color[2])
        else:
            return (0, 0, 0)

    with Image.open(image_bytes) as img:
        return await blocking_operations(img)



        
async def get_avatar_id_async(person: Person) -> str | None:
    try:
        photos = await bot.get_user_profile_photos(person.id)
        if photos.photos:
            # Вибираємо останню фотографію (найновішу)
            photo = photos.photos[0][0]
            return photo.file_id
    except Exception as e:
        print(f"Error fetching user profile photos: {e}")
    return None

async def download_profile_photo_async(person: Person) -> BytesIO | None:
    async def get_file_content(file_content: bytes) -> BytesIO:
        bytes_io = BytesIO()
        bytes_io.write(file_content)
        bytes_io.seek(0)
        return bytes_io

    async def get_default_avatar() -> BytesIO | None:
        try:
            with open('img/no_avatar.jpg', 'rb') as f:
                return await get_file_content(f.read())
        except FileNotFoundError:
            return None

    if isinstance(person, DiscordPerson):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(person.ava) as response:
                    if response.status == 200:
                        file_content = await response.read()
                        return await get_file_content(file_content)
        except (discord.errors.NotFound, discord.errors.HTTPException):
            return await get_default_avatar()
        except Exception as e:
            print(f"Error retrieving user: {e}")
            return await get_default_avatar()

    # Telegram logic, assuming similar structure and error handling
    else:
        ava = await get_avatar_id_async(person)
        if ava:
            # Отримуємо файл
            try:
                file = await bot.get_file(ava)
                print('file: ' + str(file))
            except:
                return await get_default_avatar()
            # Завантажуємо файл
            file_path = file.file_path
            print('file path: ' + file_path)
            file_content = await bot.download_file(file_path)
            print('file content: ' + str(file_content))
            if isinstance(file_content, BytesIO):  # Перевіряємо, чи це об'єкт BytesIO
                file_content = file_content.getvalue()  # Якщо так, читаємо байти
                return await get_file_content(file_content)

    return await get_default_avatar()

async def create_credit_image_async(person) -> str:
    # Встановлення розмірів зображення
    image_width = 600
    image_height = 140

    # Виконуємо блокуючі операції з PIL в окремому потоці
    def create_image(person: Person, avatar: BytesIO, discord_nick: str = None):
        MAX_INT_VALUE = 9223372036854775807
        MIN_INT_VALUE = -9223372036854775808
        # Створення нового зображення з чорним фоном

        image = Image.new('RGB', (image_width, image_height), color=person.color)
        draw = ImageDraw.Draw(image)

        # Відкриття та вставка аватара
        avatar = Image.open(avatar).resize((140, 140))
        image.paste(avatar, (0, 0))  # Вставка зліва зверху

        # Налаштування шрифту
        font_path = "font/DejaVuSans.ttf"
        font = ImageFont.truetype(font_path, 24)
        grey_font = ImageFont.truetype(font_path, 20)
        bg_darker = not is_bg_dark(person.color)

        dark_color = (24, 27, 33)
        credit_text_color = (255,255,255) if bg_darker else dark_color
        fullname_color = (255,255,255) if bg_darker else dark_color
        nickname_color = (200,200,200) if bg_darker else (50, 50, 50)


        # Якщо треба центрувати текст горизонтально
        #text_width = draw.textlength(balance_text, font=font)
        #draw.text(((image_width - text_width) / 2, 70), balance_text, fill="white", font=font)

        # Додавання інформації про користувача

        if person.score > MAX_INT_VALUE / 1000 or person.score < MIN_INT_VALUE / 1000:
            font = ImageFont.truetype(font_path, 20)

        score = person.score
        if score == MAX_INT_VALUE or score == MIN_INT_VALUE:
            draw.text(
                (160, 80), 
                '(максимально)' if score == MAX_INT_VALUE else '(мінімально)', 
                fill=credit_text_color, 
                font=font
            )
        else:
            if score > 10000000000:
                score = '∞'
            elif score < -10000000000:
                score = '-∞'

        balance_text = f"Соц. кредитів: {score}"

        draw.text((160, 80), balance_text, fill=credit_text_color, font=font)
        draw.text((160, 10), person.fullname, fill=fullname_color, font=font)

        nicks_offset = 160

        def paste_logo(logo_path, position):
            logo = Image.open(logo_path)
            logo = logo.resize((25, 25), Image.BILINEAR).convert('RGBA')  # Змінюємо розмір та зберігаємо альфа-канал
            image.paste(logo, position, logo)

        def draw_nickname(nickname, position):
            draw.text(position, nickname, fill=nickname_color, font=grey_font)
            return position[0] + draw.textlength(nickname, font=grey_font)

        if person.id and person.name:
            paste_logo('img/telegram.png', (nicks_offset, 40))
            name_length = draw_nickname(person.name, (nicks_offset + 30, 40))
            nicks_offset = name_length + 25

        if discord_nick:
            # Перевірка, чи потрібно вставити нижче
            if nicks_offset + draw.textlength(discord_nick, font=grey_font) + 55 > image.width:
                discord_offset = 20  # Повернення до початкового відступу
                vertical_offset = 65  # На 25 пікселів нижче
            else:
                discord_offset = nicks_offset
                vertical_offset = 40

            paste_logo('img/discord.png', (discord_offset, vertical_offset))
            draw_nickname(discord_nick, (discord_offset + 30, vertical_offset))            
            

        # Збереження зображення
        output_path = f"img/credits/{str(person.number)}.jpeg"
        image.save(output_path, format='JPEG')

        return output_path
    
    
    discord_nick = None
    print('person: ' + str(person))
    ava = await download_profile_photo_async(person)
    
    color = await get_dominant_color_async(ava)
    person.color = color
    print('dominant color: ' + str(person.color))

    if isinstance(person, DiscordPerson):
        await discord_repo.update_person_async(person)
        person = await repo_user.by_discord_async(person.id)
    elif isinstance(person, Person):
        await repo_user.update_person_async(number=person.number, color=person.color)

    if person.discord:
        discord_person = await discord_repo.by_number_async(person.number)
        discord_nick = discord_person.nickname

    person.color = color
    output_path = await asyncio.to_thread(create_image, person, ava, discord_nick)

    return output_path

async def create_changed_credit_image_async(msg, person, added_credits: int) -> str:
    # Встановлення розмірів зображення
    image_width = 600
    image_height = 140

    # Виконуємо блокуючі операції з PIL в окремому потоці
    def create_image(person, added_credits: int, avatar: BytesIO, discord_nick: str = None):
        # Створення нового зображення з чорним фоном
        image = Image.new('RGB', (image_width, image_height), color=person.color)
        draw = ImageDraw.Draw(image)

        # Відкриття та вставка аватара
        avatar = Image.open(avatar).resize((140, 140))
        image.paste(avatar, (0, 0))  # Вставка зліва зверху

        # Налаштування шрифту
        font_path = "font/DejaVuSans.ttf"
        font_size = 24
        font = ImageFont.truetype(font_path, font_size)
        grey_font = ImageFont.truetype(font_path, 20)

        bg_darker = not is_bg_dark(person.color)

        dark_color = (24, 27, 33)
        credit_text_color = (255,255,255) if bg_darker else dark_color
        fullname_color = (255,255,255) if bg_darker else dark_color
        nickname_color = (200,200,200) if bg_darker else (50, 50, 50)

        # Якщо треба центрувати текст горизонтально
        #text_width = draw.textlength(balance_text, font=font)
        #draw.text(((image_width - text_width) / 2, 70), balance_text, fill="white", font=font)

        # Додавання інформації про користувача
        score = person.score
        if score > 10000000000:
            score = '∞'
        elif score < -10000000000:
            score = '-∞'
        balance_text = f"{score}"

        draw.text((160, 80), balance_text, fill=credit_text_color, font=font)
        pos_for_changed_credits = draw.textlength(balance_text)
        
    
        credit_str = str(added_credits)
        if added_credits >= 0:

            credit_str_color = (0, 255, 0)
            if is_similar_to_green(person.color):
                credit_str_color = credit_text_color
            
            credit_str = f'+{added_credits}'
            draw.text((180 + pos_for_changed_credits * 2.5, 80), f'↑ {credit_str}', fill=credit_str_color, font=font)
        else:
            credit_str_color = (255, 0, 0)
            if is_similar_to_red(person.color):
                credit_str_color = credit_text_color

            draw.text((180 + pos_for_changed_credits * 2.5, 80), f'↓ {credit_str}', fill=credit_str_color, font=font)

        draw.text((160, 10), person.fullname, fill=fullname_color, font=font)
        
        nicks_offset = 160

        def paste_logo(logo_path, position):
            logo = Image.open(logo_path)
            logo = logo.resize((25, 25), Image.BILINEAR).convert('RGBA')  # Змінюємо розмір та зберігаємо альфа-канал
            image.paste(logo, position, logo)

        def draw_nickname(nickname, position):
            draw.text(position, nickname, fill=nickname_color, font=grey_font)
            return position[0] + draw.textlength(nickname, font=grey_font)

        if person.id and person.name:
            paste_logo('img/telegram.png', (nicks_offset, 40))
            name_length = draw_nickname(person.name, (nicks_offset + 30, 40))
            nicks_offset = name_length + 25

        if discord_nick:
            # Перевірка, чи потрібно вставити нижче
            if nicks_offset + draw.textlength(discord_nick, font=grey_font) + 55 > image.width:
                discord_offset = 20  # Повернення до початкового відступу
                vertical_offset = 65  # На 25 пікселів нижче
            else:
                discord_offset = nicks_offset
                vertical_offset = 40

            paste_logo('img/discord.png', (discord_offset, vertical_offset))
            draw_nickname(discord_nick, (discord_offset + 30, vertical_offset))

        # Збереження зображення
        output_path = f"img/changed_credit/{str(person.number)}.jpeg"
        image.save(output_path, format='JPEG')

        return output_path
    
    discord_nick = None
    ava = await download_profile_photo_async(person)
    color = await get_dominant_color_async(ava)
    person.color = color

    if isinstance(person, DiscordPerson):
        await discord_repo.update_person_async(person)
        person = await repo_user.by_discord_async(person.id)
    elif isinstance(person, Person):
        await repo_user.update_person_async(number=person.number, color=person.color)

    if person.discord:
        discord_person = await discord_repo.by_number_async(person.number)
        discord_nick = discord_person.nickname

    person.color = color
    output_path = await asyncio.to_thread(create_image, person, added_credits, ava, discord_nick)
    print('generated user image')
    return output_path

async def send_credit_image(msg, person):
    photo = await create_credit_image_async(person)

    if isinstance(msg, aiogram.types.Message):
        await msg.reply_photo(aiogram.types.FSInputFile(photo))
    elif isinstance(msg, discord.Message):
        file = discord.File(photo, filename="credit_image.png")
        await msg.channel.send(file=file)

    return None


async def send_changed_credit_image(msg, person, added_credits, caption=None):
    photo = await create_changed_credit_image_async(msg, person, added_credits)

    if isinstance(msg, aiogram.types.Message):
        await msg.reply_photo(aiogram.types.FSInputFile(photo), caption=caption)
    elif isinstance(msg, discord.Message):
        file = discord.File(photo, filename="changed_credit_image.png")
        await msg.channel.send(file=file, content=caption)

    return None

async def send_highscore_image(msg, limit=5):
    users = repo_user.with_highest_scores(limit)
    image_paths = []

    for u in users:
        print("id: " + str(u.number), "\tname: " + u.fullname, "\tscore: " + str(u.score))
        if os.path.exists(f"img/credits/{str(u.number)}.jpeg"):
            output_path = f"img/credits/{str(u.number)}.jpeg"
            image_paths.append(output_path)

    if not image_paths:
        return 'Немає найкращих, поки що.'
    
    total_height = 140 * len(users)
    combined_image = Image.new('RGB', (600, total_height))
    
    for index, image_path in enumerate(image_paths):
        user_image = Image.open(image_path)
        combined_image.paste(user_image, (0, 140 * index))
    
    output_path = "img/highscore.jpeg"
    combined_image.save(output_path, format='JPEG')

    if isinstance(msg, aiogram.types.Message):
        await msg.reply_photo(aiogram.types.FSInputFile(output_path))
    elif isinstance(msg, discord.Message):
        file = discord.File(output_path, filename="highscore_image.jpeg")
        await msg.channel.send(file=file)

    return None


async def send_lowscore_image(msg: aiogram.types.Message, limit: int = 5):
    users = repo_user.with_lowest_scores(limit)
    image_paths = []

    for u in users:
        if os.path.exists(f"img/credits/{str(u.number)}.jpeg"):
            output_path = f"img/credits/{str(u.number)}.jpeg"
            image_paths.append(output_path)

    if not image_paths:
        return 'Немає гірших, поки що.'
    

    total_height = 140 * len(users)
    combined_image = Image.new('RGB', (600, total_height))
    
    for index, image_path in enumerate(image_paths):
        user_image = Image.open(image_path)
        combined_image.paste(user_image, (0, 140 * index))
    
    output_path = "img/lowscore.jpeg"
    combined_image.save(output_path, format='JPEG')
    
    if isinstance(msg, aiogram.types.Message):
        await msg.reply_photo(aiogram.types.FSInputFile(output_path))
    elif isinstance(msg, discord.Message):
        file = discord.File(output_path, filename="highscore_image.jpeg")
        await msg.channel.send(file=file)

    return None