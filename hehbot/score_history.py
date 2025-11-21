import sqlite3
from datetime import datetime
from typing import List
from abc import ABC, abstractmethod
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import MaxNLocator
import numpy as np

import io
from collections import defaultdict, Counter
from datetime import timedelta
from hehbot.env_service import env


def make_gradient(axis, color1, color2, direction='vertical'):
    """
    Функція для створення градієнту на осі.

    Args:
    - axis: об'єкт осі matplotlib.
    - color1: початковий колір у форматі RGB.
    - color2: кінцевий колір у форматі RGB.
    - direction: напрямок градієнту ('vertical' або 'horizontal').
    """
    # Створення кольорової мапи з ваших кольорів
    cmap = LinearSegmentedColormap.from_list('grad', [color1, color2])
    
    # Створення даних для градієнту
    if direction == 'vertical':
        gradient = np.linspace(0, 1, 256)
        gradient = np.vstack((gradient, gradient))
    else: # для горизонтального градієнту
        gradient = np.linspace(0, 1, 256)
        gradient = np.vstack((gradient, gradient)).T
    
    # Відображення градієнту як зображення на фоні
    axis.imshow(gradient, aspect='auto', cmap=cmap, origin='lower',
                extent=[axis.get_xlim()[0], axis.get_xlim()[1], axis.get_ylim()[0], axis.get_ylim()[1]])

def normalize_rgb(rgb):
    try:
        return tuple(channel / 255.0 for channel in rgb)
    except:
        return (0, 0, 0)

async def find_common_colors_async(image_data):
    # Завантажуємо зображення з BytesIO або PIL.Image
    if isinstance(image_data, io.BytesIO):
        image = Image.open(image_data)
    else:
        image = image_data

    # Конвертуємо зображення у numpy масив
    pixels = np.array(image)

    # Розраховуємо яскравість для кожного пікселя
    # Вважаємо, що зображення в RGB
    brightness = np.sqrt(0.299 * pixels[:,:,0]**2 + 0.587 * pixels[:,:,1]**2 + 0.114 * pixels[:,:,2]**2)

    # Класифікуємо пікселі
    dark_threshold = np.percentile(brightness, 33)  # Нижня третина яскравості
    light_threshold = np.percentile(brightness, 66) # Верхня третина яскравості

    dark_pixels = pixels[brightness < dark_threshold]
    mid_pixels = pixels[(brightness >= dark_threshold) & (brightness < light_threshold)]
    light_pixels = pixels[brightness >= light_threshold]

    # Знаходимо найпоширеніші кольори
    def most_common_color(pixels):
        if len(pixels) == 0:
            return None
        count = Counter(map(tuple, pixels))
        return count.most_common(1)[0][0]

    result = {
        'dark': normalize_rgb(most_common_color(dark_pixels)),
        'mid': normalize_rgb(most_common_color(mid_pixels)),
        'light': normalize_rgb(most_common_color(light_pixels))
    }

    result = {
        'dark': result['dark'] if result['dark'] != (0,0,0) else (0.1, 0.1, 0.15),
        'mid': result['mid'] if result['mid'] != (0,0,0) else (0.5, 0.5, 0.55),
        'light': result['light'] if result['light'] != (0,0,0) else (1, 1, 1)
    }

    return result

class ScoreHistory:
    def __init__(self, number: int, score: int, date: datetime = None) -> None:
        self.number = number
        self.score = score
        self.date = date

class IScoreHistoryRepository(ABC):
    @abstractmethod
    def add(self, score_history: ScoreHistory) -> None:
        pass
    
    @abstractmethod
    def get_history_for_user(self, number: int, days: int) -> List[ScoreHistory]:
        pass

    @abstractmethod
    def get_all_users_history(self) -> List[ScoreHistory]:
        pass

class ScoreHistoryRepository(IScoreHistoryRepository):
    def __init__(self, db_path: str = '{}/score_history.db'.format(env.data_path)):
        self.db_path = db_path
        self._create_table()

    def _create_table(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS score_history (
                count INTEGER PRIMARY KEY AUTOINCREMENT,
                number INTEGER NOT NULL,
                score INTEGER NOT NULL,
                date TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def add(self, score_history: ScoreHistory) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO score_history (number, score, date)
            VALUES (?, ?, ?)
        ''', (score_history.number, score_history.score, score_history.date.isoformat() if score_history.date else datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_history_for_user(self, number: int, last_days: int) -> List[ScoreHistory]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Розрахунок дати, яка була 'last_days' днів назад
        date_limit = datetime.now() - timedelta(days=last_days)
        date_limit_str = date_limit.strftime('%Y-%m-%d')  # Форматування дати до строки
        # Модифікація запиту для вибірки лише тих записів, що підпадають під вказаний період
        cursor.execute('''
            SELECT number, score, date FROM score_history
            WHERE number = ? AND date >= ?
        ''', (number, date_limit_str))
        rows = cursor.fetchall()
        conn.close()
        # Конвертація отриманих результатів у список об'єктів ScoreHistory
        return [ScoreHistory(row[0], row[1], datetime.fromisoformat(row[2])) for row in rows]

    def get_all_users_history(self) -> List[ScoreHistory]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT number, score, date FROM score_history
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [ScoreHistory(row[0], row[1], datetime.fromisoformat(row[2])) for row in rows]
    
repo_score_history = ScoreHistoryRepository()







def reduce_brightness(color, factor):
        # Забезпечуємо, що кожен компонент не виходить за межі 0-255
        return tuple(max(0, min(int(comp * factor), 255)) for comp in color)
    
def adjust_brightness(color):
    sum_color = sum(color)
    if sum_color < 12:
        sum_color = 12
        color = (3, 4, 5)
    if sum_color < 100:
        # Лінійне масштабування
        factor = 200 / (sum_color + 1)
        return tuple(min(int(comp * factor), 255) for comp in color)
    return color


async def plot_top_history(limit=9, days=7, show_highscore: bool=True):
    min_date = datetime.now() - timedelta(days=days)
    found_min_date = None

    data = defaultdict(lambda: defaultdict(list))
    min_score, max_score = float('inf'), float('-inf')

    user_colors = []

    from hehbot import repo_user
    from credit_image import is_bg_dark, get_dominant_color_async

    if show_highscore:
        users = repo_user.with_highest_scores(limit)
        out_path = 'img/history/highscore.png'
    else:
        users = repo_user.with_lowest_scores(limit)
        out_path = 'img/history/lowscore.png'

    for u in users:
        user_histories = repo_score_history.get_history_for_user(u.number, days)
        for h in user_histories:
            if h.date < min_date:
                continue
            if found_min_date is not None:
                # Перетворення кількості днів назад у datetime для порівняння
                current_min_date = datetime.now() - timedelta(days=found_min_date)
                new_min_date = min(current_min_date, h.date)
                found_min_date = (datetime.now() - new_min_date).days
            else:
                found_min_date = (datetime.now() - h.date).days
            min_score, max_score = min(min_score, h.score), max(max_score, h.score)
            timestamp = h.date.timestamp()
            data[u.fullname][h.date.date()].append((timestamp, h.score))

        user_colors.append(normalize_rgb(adjust_brightness(u.color)))

    main_color = adjust_brightness(users[0].color)

    main_dominant = normalize_rgb(main_color)
    main_center = normalize_rgb(reduce_brightness(main_color, 0.5))
    main_line = main_text = normalize_rgb(reduce_brightness(main_color, 2))

    if not data:
        return None
    
    plt.figure(figsize=(14, 7))  # Розміри в дюймах, згідно з вашим запитом (1100x500 pixels при DPI=100)
    ax = plt.gca()

    plt.gcf().set_facecolor(color=main_center)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m %d'))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))

    for name, dates in data.items():
        all_scores = []
        for date, scores in dates.items():
            all_scores.extend(scores)
                
        all_scores.sort()
        x, y = zip(*all_scores)
        x = [mdates.date2num(datetime.fromtimestamp(ts)) for ts in x]
        main_line = main_text = normalize_rgb(reduce_brightness(main_color, 2))
        plt.plot_date(x, y, '-', label=name, lw = 4)
        plt.text(x[-1], y[-1], name, color=plt.gca().lines[-1].get_color(), fontsize=18, verticalalignment='center')

    legend = plt.legend(framealpha=0)
    plt.setp(legend.get_texts(), color='white')
    # Налаштування осей і тексту
    plt.tick_params(axis='x', which='both', length=0, colors=main_text, labelsize=20)  
    plt.tick_params(axis='y', which='both', length=0, colors=main_text, labelsize=20)  
    ax.spines['top'].set_visible(False)    
    ax.spines['right'].set_visible(False)  
    ax.spines['bottom'].set_visible(False) 
    ax.spines['left'].set_visible(False)   
    plt.xlabel('Дата', fontsize=18, color=main_text)
    plt.ylabel('Кредити', fontsize=18, color=main_text)
    plt.title(label=f'{'Кращі' if show_highscore else 'Гірші'} за {days if not found_min_date else found_min_date} днів', fontsize=22, color=main_text)

    make_gradient(ax, main_dominant, main_center, 'horizontal')

    # Вставка зображення
    #img_ax = inset_axes(ax, width="50%", height="50%", loc='lower left',
    #                    bbox_to_anchor=(0, 0, 1, 1), bbox_transform=ax.transAxes, borderpad=0)

    #img_ax.imshow(img)
    #img_ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(out_path, format='png', dpi=200)
    return out_path


async def plot_user_history(number: int, days: int) -> str | None:
    """
    Plot the user's credit score history.

    Args:
        number (int): The user's number.
        days (int): The number of days to include in the history.

    Returns:
        str | None: The file path of the generated plot image, or None if no data is available.

    Raises:
        None

    """
    from hehbot import repo_user
    from credit_image import is_bg_dark, get_dominant_color_async

    user = await repo_user.by_number_async(number)
    found_min_date = None

    user.color = adjust_brightness(user.color)

    dominant_color = normalize_rgb(user.color)
    center_color = normalize_rgb(reduce_brightness(user.color, 0.3))
    line_color = color_text = normalize_rgb(reduce_brightness(user.color, 2))

    # Визначення мінімальної дати, віднявши кількість днів від поточної дати
    min_date = datetime.now() - timedelta(days=days)
    data = defaultdict(list)  # Змінено на список кортежів (timestamp, score)
    min_score, max_score = float('inf'), float('-inf')

    user_histories = repo_score_history.get_history_for_user(user.number, days)
    for h in user_histories:
        # Пропускаємо записи, які старіші за визначений ліміт days
        if h.date < min_date:
            continue

        if found_min_date is not None:
            # Перетворення кількості днів назад у datetime для порівняння
            current_min_date = datetime.now() - timedelta(days=found_min_date)
            new_min_date = min(current_min_date, h.date)
            found_min_date = (datetime.now() - new_min_date).days
        else:
            found_min_date = (datetime.now() - h.date).days

        min_score, max_score = min(min_score, h.score), max(max_score, h.score)
        timestamp = h.date.timestamp()
        data[user.fullname].append((timestamp, h.score))

    if not data:
        return

    plt.figure(figsize=(12, 6))  # Розміри в дюймах (1200x600 pixels при DPI=100)
    ax = plt.gca()

    plt.gcf().set_facecolor(color=center_color)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m %d'))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))

    # Налаштування основного графіка
    for name, scores in data.items():
        scores.sort()  # Сортування за timestamp
        x, y = zip(*scores)
        x = [mdates.date2num(datetime.fromtimestamp(ts)) for ts in x]

        plt.plot_date(x, y, '-', lw=5, label=name, color=line_color)
        #plt.text(x[-1], y[-1], name, color=color_text, fontsize=18, verticalalignment='center')

    # Налаштування осей і тексту
    plt.tick_params(axis='x', which='both', length=0, colors=color_text, labelsize=20)
    plt.tick_params(axis='y', which='both', length=0, colors=color_text, labelsize=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    plt.xlabel('Дата', fontsize=18, color=color_text)
    plt.ylabel('Кредити', fontsize=18, color=color_text)
    plt.title(label=f'{user.fullname} за {days if not found_min_date else found_min_date} днів', fontsize=22, color=color_text)

    make_gradient(ax, dominant_color, center_color, 'horizontal')

    # Вставка зображення
    #img_ax = inset_axes(ax, width="50%", height="50%", loc='lower left',
    #                    bbox_to_anchor=(0, 0, 1, 1), bbox_transform=ax.transAxes, borderpad=0)

    #img_ax.imshow(img)
    #img_ax.axis('off')

    plt.tight_layout()
    out_path = f'img/history/users/{str(number)}.png'
    plt.savefig(out_path, format='png', dpi=100)
    return out_path