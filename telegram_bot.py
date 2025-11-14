from random import choice
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
import telebot
import os

token = os.getenv('TELEGRAM_TOKEN', '8315061997:AAFEeHeoS16xB119HDNk5AMQwCKeZ64Y1ek')
bot = telebot.TeleBot(token)

GUI_APP_PATH = 'http://158.160.203.139:5000/, http://127.0.0.1:5000, http://192.168.1.105:5000'

RANDOM_TASKS_PLAYERS = [
    {'name': 'Erling Haaland', 'goals': 36, 'assists': 8, 'clean_sheets': 0},
    {'name': 'Giovanni Di Lorenzo', 'goals': 2, 'assists': 5, 'clean_sheets': 12},
    {'name': 'Kylian Mbappé', 'goals': 44, 'assists': 10, 'clean_sheets': 0},
    {'name': 'Lionel Messi', 'goals': 20, 'assists': 15, 'clean_sheets': 0},
    {'name': 'Cristiano Ronaldo', 'goals': 35, 'assists': 3, 'clean_sheets': 0},
    {'name': 'Virgil van Dijk', 'goals': 1, 'assists': 2, 'clean_sheets': 20},
    {'name': 'Kevin De Bruyne', 'goals': 10, 'assists': 16, 'clean_sheets': 0},
    {'name': 'Robert Lewandowski', 'goals': 48, 'assists': 9, 'clean_sheets': 0}
]

RANDOM_TASKS_CLUBS = [
    {'name': 'Manchester City', 'super_cups': 1, 'cups': 2, 'championships': 2, 'champions_leagues': 1},
    {'name': 'Real Madrid', 'super_cups': 1, 'cups': 2, 'championships': 1, 'champions_leagues': 1},
    {'name': 'Bayern Munich', 'super_cups': 1, 'cups': 1, 'championships': 0, 'champions_leagues': 0},
    {'name': 'Paris Saint-Germain', 'super_cups': 1, 'cups': 1, 'championships': 1, 'champions_leagues': 0},
    {'name': 'Liverpool', 'super_cups': 0, 'cups': 0, 'championships': 0, 'champions_leagues': 0},
    {'name': 'Juventus', 'super_cups': 2, 'cups': 1, 'championships': 2, 'champions_leagues': 1},
    {'name': 'Chelsea', 'super_cups': 2, 'cups': 2, 'championships': 2, 'champions_leagues': 2},
    {'name': 'Barcelona', 'super_cups': 1, 'cups': 0, 'championships': 1, 'champions_leagues': 0}
]

WELCOME = '''
Добро пожаловать в Футбольный бот!!!
Этот бот предназначен для голосования в номинации "Золотой мяч".
Он нужен для отслеживания и управления статистикой футболистов и клубов.
Вы можете добавлять данные о голах, ассистах, сухих матчах для игроков, а также о трофеях (суперкубки, кубки, чемпионаты, лиги чемпионов) для клубов, привязывая их к конкретным датам.
Основные возможности:
- Добавление данных вручную или с помощью случайных примеров известных игроков/клубов.
- Просмотр всех записей или по выбранной дате.
- Сохраниение данных в файл.
- Открытие GUI приложения "БД футбол" для просмотра и продолжения регистрации данных в графическом интерфейсе.
Используйте только кнопки меню!!!
'''

players = dict()  # date -> list of {'name': str, 'goals': int, 'assists': int, 'clean_sheets': int}
clubs = dict()    # date -> list of {'name': str, 'super_cups': int, 'cups': int, 'championships': int, 'champions_leagues': int}

user_states = {}

MAIN_MENU = ReplyKeyboardMarkup(resize_keyboard=True)
MAIN_MENU.add(KeyboardButton('⚽️ Добавить игрока'), KeyboardButton('🏟️ Добавить клуб'))
MAIN_MENU.add(KeyboardButton('👕 Случайный игрок'), KeyboardButton('🥅 Случайный клуб'))
MAIN_MENU.add(KeyboardButton('🥇 Показать игроков'), KeyboardButton('🥇 Показать клуб'))
MAIN_MENU.add(KeyboardButton('💾 Сохранить'), KeyboardButton('📱 Открыть приложение'))
MAIN_MENU.add(KeyboardButton('🆘 Помощь'))

HELP = '''
Список доступных действий (используйте кнопки):
- Добавить Игрока /add_player: шаговый ввод через кнопки или команда /add_player <date> <player_name> <goals> <assists> <clean_sheets>
- Добавить Клуб /add_club: шаговый ввод через кнопки или команда /add_club <date> <club_name> <super_cups> <cups> <championships> <champions_leagues>
- Случайный Игрок /random_player
- Случайный Клуб /random_club
- Показать Игроков /print_player [<date>]
- Показать Клубы /print_club [<date>]
- Сохранить в файл /save
- Открыть приложение /open_app (откроет ссылку на GUI "БД футбол" в браузере)
'''

def add_player(date, player_name, goals, assists, clean_sheets):
    date = date.lower().strip()
    if not date:
        raise ValueError("Дата не может быть пустой")
    if date not in players:
        players[date] = []
    players[date].append({'name': player_name, 'goals': goals, 'assists': assists, 'clean_sheets': clean_sheets})

def add_club(date, club_name, super_cups, cups, championships, champions_leagues):
    date = date.lower().strip()
    if not date:
        raise ValueError("Дата не может быть пустой")
    if date not in clubs:
        clubs[date] = []
    clubs[date].append({'name': club_name, 'super_cups': super_cups, 'cups': cups, 'championships': championships, 'champions_leagues': champions_leagues})

def parse_name_and_params(parts, num_params):
    if len(parts) < 2 + num_params:
        return None, None
    params = parts[-num_params:]
    name_parts = parts[2:-num_params]
    name = ' '.join(name_parts).strip()
    if not name:
        return None, None
    try:
        param_values = [int(p) for p in params]
        if any(param < 0 for param in param_values):
            return None, None
    except ValueError:
        return None, None
    return name, param_values

def get_user_state(user_id):
    return user_states.get(user_id, {})

def set_user_state(user_id, state):
    user_states[user_id] = state

def clear_user_state(user_id):
    if user_id in user_states:
        del user_states[user_id]

@bot.message_handler(commands=['start', 'help'])
def start_help_command(message):
    bot.send_message(message.chat.id, WELCOME, reply_markup=MAIN_MENU)
    bot.send_message(message.chat.id, HELP, reply_markup=MAIN_MENU)

@bot.message_handler(func=lambda message: True)
def handle_menu_buttons(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text == '🆘 Помощь':
        bot.send_message(message.chat.id, HELP, reply_markup=MAIN_MENU)
        return

    if text == '⚽️ Добавить игрока':
        set_user_state(user_id, {'action': 'add_player', 'step': 'date'})
        bot.send_message(message.chat.id, 'Введите дату (например, "сегодня" или "01.01.2024"):')
        return

    if text == '🏟️ Добавить клуб':
        set_user_state(user_id, {'action': 'add_club', 'step': 'date'})
        bot.send_message(message.chat.id, 'Введите дату (например, "сегодня" или "01.01.2024"):')
        return

    if text == '👕 Случайный игрок':
        player_data = choice(RANDOM_TASKS_PLAYERS)
        add_player('сегодня', player_data['name'], player_data['goals'], player_data['assists'], player_data['clean_sheets'])
        bot.send_message(message.chat.id, f'Футболист {player_data["name"]} добавлен на сегодня ({player_data["goals"]} голов, {player_data["assists"]} ассистов, {player_data["clean_sheets"]} сухих матчей)', reply_markup=MAIN_MENU)
        return

    if text == '🥅 Случайный клуб':
        club_data = choice(RANDOM_TASKS_CLUBS)
        add_club('сегодня', club_data['name'], club_data['super_cups'], club_data['cups'], club_data['championships'], club_data['champions_leagues'])
        bot.send_message(message.chat.id, f'Клуб {club_data["name"]} добавлен на сегодня ({club_data["super_cups"]} суперкубков, {club_data["cups"]} кубков, {club_data["championships"]} чемпионатов, {club_data["champions_leagues"]} лиг чемпионов)', reply_markup=MAIN_MENU)
        return

    if text == '🥇 Показать игроков':
        if not players:
            output = 'Футболистов нет'
        else:
            output = "Все футболисты по датам:\n\n"
            for date in sorted(players.keys()):
                output += f"Дата: {date}\n"
                for p in players[date]:
                    output += f'{p["name"]}: {p["goals"]} голов, {p["assists"]} ассистов, {p["clean_sheets"]} сухих матчей\n'
                output += '\n'
        bot.send_message(message.chat.id, output, reply_markup=MAIN_MENU)
        return

    if text == '🥇 Показать клуб':
        if not clubs:
            output = 'Клубов нет'
        else:
            output = "Все клубы по датам:\n\n"
            for date in sorted(clubs.keys()):
                output += f"Дата: {date}\n"
                for c in clubs[date]:
                    output += f'{c["name"]}: {c["super_cups"]} суперкубков, {c["cups"]} кубков, {c["championships"]} чемпионатов, {c["champions_leagues"]} лиг чемпионов\n'
                output += '\n'
        bot.send_message(message.chat.id, output, reply_markup=MAIN_MENU)
        return

    if text == '💾 Сохранить':
        save_to_file(message)
        return

    if text == '📱 Открыть приложение':
        bot.send_message(message.chat.id, "⚠️ <b>ВНИМАНИЕ: Ссылка на приложение</b> ⚠️", parse_mode='HTML')
        bot.send_message(message.chat.id, f"🔗 {GUI_APP_PATH}", reply_markup=MAIN_MENU)
        return

    state = get_user_state(user_id)
    if not state:
        bot.send_message(message.chat.id, 'Неизвестная команда. Используйте кнопки меню.', reply_markup=MAIN_MENU)
        return

    if state['action'] == 'add_player':
        handle_add_player_step(message, state)
    elif state['action'] == 'add_club':
        handle_add_club_step(message, state)

def handle_add_player_step(message, state):
    user_id = message.from_user.id
    text = message.text.strip()

    if state['step'] == 'date':
        if not text:
            bot.send_message(message.chat.id, 'Дата не может быть пустой. Введите дату:')
            return
        state['date'] = text.lower()
        state['step'] = 'name'
        bot.send_message(message.chat.id, 'Введите имя футболиста (может содержать пробелы):')
    elif state['step'] == 'name':
        if not text:
            bot.send_message(message.chat.id, 'Имя не может быть пустым. Введите имя:')
            return
        state['name'] = text
        state['step'] = 'goals'
        bot.send_message(message.chat.id, 'Введите количество голов (неотрицательное целое число):')
    elif state['step'] == 'goals':
        try:
            goals = int(text)
            if goals < 0:
                raise ValueError
            state['goals'] = goals
            state['step'] = 'assists'
            bot.send_message(message.chat.id, 'Введите количество ассистов (неотрицательное целое число):')
        except ValueError:
            bot.send_message(message.chat.id, 'Неверное значение. Введите неотрицательное целое число для голов:')
            return
    elif state['step'] == 'assists':
        try:
            assists = int(text)
            if assists < 0:
                raise ValueError
            state['assists'] = assists
            state['step'] = 'clean_sheets'
            bot.send_message(message.chat.id, 'Введите количество сухих матчей (неотрицательное целое число):')
        except ValueError:
            bot.send_message(message.chat.id, 'Неверное значение. Введите неотрицательное целое число для ассистов:')
            return
    elif state['step'] == 'clean_sheets':
        try:
            clean_sheets = int(text)
            if clean_sheets < 0:
                raise ValueError
            add_player(state['date'], state['name'], state['goals'], state['assists'], clean_sheets)
            bot.send_message(message.chat.id, f'Футболист "{state["name"]}" добавлен на дату {state["date"]} ({state["goals"]} голов, {state["assists"]} ассистов, {clean_sheets} сухих матчей)', reply_markup=MAIN_MENU)
            clear_user_state(user_id)
        except ValueError as e:
            bot.send_message(message.chat.id, f'Ошибка: {str(e)}')
            clear_user_state(user_id)

def handle_add_club_step(message, state):
    user_id = message.from_user.id
    text = message.text.strip()

    if state['step'] == 'date':
        if not text:
            bot.send_message(message.chat.id, 'Дата не может быть пустой. Введите дату:')
            return
        state['date'] = text.lower()
        state['step'] = 'name'
        bot.send_message(message.chat.id, 'Введите имя клуба (может содержать пробелы):')
    elif state['step'] == 'name':
        if not text:
            bot.send_message(message.chat.id, 'Имя не может быть пустым. Введите имя:')
            return
        state['name'] = text
        state['step'] = 'super_cups'
        bot.send_message(message.chat.id, 'Введите количество суперкубков (неотрицательное целое число):')
    elif state['step'] == 'super_cups':
        try:
            super_cups = int(text)
            if super_cups < 0:
                raise ValueError
            state['super_cups'] = super_cups
            state['step'] = 'cups'
            bot.send_message(message.chat.id, 'Введите количество кубков (неотрицательное целое число):')
        except ValueError:
            bot.send_message(message.chat.id, 'Неверное значение. Введите неотрицательное целое число для суперкубков:')
            return
    elif state['step'] == 'cups':
        try:
            cups = int(text)
            if cups < 0:
                raise ValueError
            state['cups'] = cups
            state['step'] = 'championships'
            bot.send_message(message.chat.id, 'Введите количество чемпионатов (неотрицательное целое число):')
        except ValueError:
            bot.send_message(message.chat.id, 'Неверное значение. Введите неотрицательное целое число для кубков:')
            return
    elif state['step'] == 'championships':
        try:
            championships = int(text)
            if championships < 0:
                raise ValueError
            state['championships'] = championships
            state['step'] = 'champions_leagues'
            bot.send_message(message.chat.id, 'Введите количество лиг чемпионов (неотрицательное целое число):')
        except ValueError:
            bot.send_message(message.chat.id, 'Неверное значение. Введите неотрицательное целое число для чемпионатов:')
            return
    elif state['step'] == 'champions_leagues':
        try:
            champions_leagues = int(text)
            if champions_leagues < 0:
                raise ValueError
            add_club(state['date'], state['name'], state['super_cups'], state['cups'], state['championships'], champions_leagues)
            bot.send_message(message.chat.id, f'Клуб "{state["name"]}" добавлен на дату {state["date"]} ({state["super_cups"]} суперкубков, {state["cups"]} кубков, {state["championships"]} чемпионатов, {champions_leagues} лиг чемпионов)', reply_markup=MAIN_MENU)
            clear_user_state(user_id)
        except ValueError as e:
            bot.send_message(message.chat.id, f'Ошибка: {str(e)}')
            clear_user_state(user_id)

@bot.message_handler(commands=['random_player'])
def random_player(message):
    player_data = choice(RANDOM_TASKS_PLAYERS)
    add_player('сегодня', player_data['name'], player_data['goals'], player_data['assists'], player_data['clean_sheets'])
    bot.send_message(message.chat.id, f'Футболист {player_data["name"]} добавлен на сегодня ({player_data["goals"]} голов, {player_data["assists"]} ассистов, {player_data["clean_sheets"]} сухих матчей)', reply_markup=MAIN_MENU)

@bot.message_handler(commands=['random_club'])
def random_club(message):
    club_data = choice(RANDOM_TASKS_CLUBS)
    add_club('сегодня', club_data['name'], club_data['super_cups'], club_data['cups'], club_data['championships'], club_data['champions_leagues'])
    bot.send_message(message.chat.id, f'Клуб {club_data["name"]} добавлен на сегодня ({club_data["super_cups"]} суперкубков, {club_data["cups"]} кубков, {club_data["championships"]} чемпионатов, {club_data["champions_leagues"]} лиг чемпионов)', reply_markup=MAIN_MENU)

@bot.message_handler(commands=['add_player'])
def add_player_handler(message):
    parts = message.text.split()
    if len(parts) < 6:
        bot.send_message(message.chat.id, "Неправильный формат. Используйте: /add_player <date> <player_name> <goals> <assists> <clean_sheets>")
        return
    date = parts[1].lower().strip()
    if not date:
        bot.send_message(message.chat.id, "Дата не может быть пустой!")
        return
    name, params = parse_name_and_params(parts, 3)
    if name is None or len(params) != 3:
        bot.send_message(message.chat.id, "Неправильный формат. Укажите имя, затем три неотрицательных целых числа (goals, assists, clean_sheets).")
        return
    goals, assists, clean_sheets = params
    try:
        add_player(date, name, goals, assists, clean_sheets)
        bot.send_message(message.chat.id, f'Футболист "{name}" добавлен на дату {date} ({goals} голов, {assists} ассистов, {clean_sheets} сухих матчей)', reply_markup=MAIN_MENU)
    except ValueError as e:
        bot.send_message(message.chat.id, f'Ошибка: {str(e)}')

@bot.message_handler(commands=['add_club'])
def add_club_handler(message):
    parts = message.text.split()
    if len(parts) < 7:
        bot.send_message(message.chat.id, "Неправильный формат. Используйте: /add_club <date> <club_name> <super_cups> <cups> <championships> <champions_leagues>")
        return
    date = parts[1].lower().strip()
    if not date:
        bot.send_message(message.chat.id, "Дата не может быть пустой!")
        return
    name, params = parse_name_and_params(parts, 4)
    if name is None or len(params) != 4:
        bot.send_message(message.chat.id, "Неправильный формат. Укажите имя, затем четыре неотрицательных целых числа (super_cups, cups, championships, champions_leagues).")
        return
    super_cups, cups, championships, champions_leagues = params
    try:
        add_club(date, name, super_cups, cups, championships, champions_leagues)
        bot.send_message(message.chat.id, f'Клуб "{name}" добавлен на дату {date} ({super_cups} суперкубков, {cups} кубков, {championships} чемпионатов, {champions_leagues} лиг чемпионов)', reply_markup=MAIN_MENU)
    except ValueError as e:
        bot.send_message(message.chat.id, f'Ошибка: {str(e)}')

@bot.message_handler(commands=['print_player'])
def print_player_handler(message):
    parts = message.text.split()
    date_input = parts[1].lower().strip() if len(parts) > 1 else None
    if date_input is not None and not date_input:
        bot.send_message(message.chat.id, "Дата не может быть пустой!")
        return
    is_specific_date = date_input is not None

    if is_specific_date:
        date = date_input
        if date in players and players[date]:
            output = f"Футболисты на дату {date}:\n"
            for p in players[date]:
                output += f'{p["name"]}: {p["goals"]} голов, {p["assists"]} ассистов, {p["clean_sheets"]} сухих матчей\n'
        else:
            output = f'Футболистов на дату {date} нет'
    else:
        if not players:
            output = 'Футболистов нет'
        else:
            output = "Все футболисты по датам:\n\n"
            for date in sorted(players.keys()):
                output += f"Дата: {date}\n"
                for p in players[date]:
                    output += f'{p["name"]}: {p["goals"]} голов, {p["assists"]} ассистов, {p["clean_sheets"]} сухих матчей\n'
                output += '\n'
    bot.send_message(message.chat.id, output, reply_markup=MAIN_MENU)

@bot.message_handler(commands=['print_club'])
def print_club_handler(message):
    parts = message.text.split()
    date_input = parts[1].lower().strip() if len(parts) > 1 else None
    if date_input is not None and not date_input:
        bot.send_message(message.chat.id, "Дата не может быть пустой!")
        return
    is_specific_date = date_input is not None

    if is_specific_date:
        date = date_input
        if date in clubs and clubs[date]:
            output = f"Клубы на дату {date}:\n"
            for c in clubs[date]:
                output += f'{c["name"]}: {c["super_cups"]} суперкубков, {c["cups"]} кубков, {c["championships"]} чемпионатов, {c["champions_leagues"]} лиг чемпионов\n'
        else:
            output = f'Клубов на дату {date} нет'
    else:
        if not clubs:
            output = 'Клубов нет'
        else:
            output = "Все клубы по датам:\n\n"
            for date in sorted(clubs.keys()):
                output += f"Дата: {date}\n"
                for c in clubs[date]:
                    output += f'{c["name"]}: {c["super_cups"]} суперкубков, {c["cups"]} кубков, {c["championships"]} чемпионатов, {c["champions_leagues"]} лиг чемпионов\n'
                output += '\n'
    bot.send_message(message.chat.id, output, reply_markup=MAIN_MENU)

def save_to_file(message):
    try:
        with open('Football.txt', 'w', encoding='utf-8') as f:
            f.write("=== Players ===\n")
            for date, plist in sorted(players.items()):
                f.write(f"\n{date}:\n")
                for p in plist:
                    f.write(f" - {p['name']}: {p['goals']} голов, {p['assists']} ассистов, {p['clean_sheets']} сухих матчей\n")
            f.write("\n=== Clubs ===\n")
            for date, clist in sorted(clubs.items()):
                f.write(f"\n{date}:\n")
                for c in clist:
                    f.write(f" - {c['name']}: {c['super_cups']} суперкубков, {c['cups']} кубков, {c['championships']} чемпионатов, {c['champions_leagues']} лиг чемпионов\n")

        if os.path.exists('Football.txt') and os.path.getsize('Football.txt') > 0:
            with open('Football.txt', 'rb') as file:
                try:
                    document = InputFile(file, filename='Football.txt')
                    bot.send_document(message.chat.id, document, caption='Данные о футболистах и клубах сохранены. Вот файл для скачивания!')
                except Exception:
                    file.seek(0)
                    bot.send_document(message.chat.id, file, caption='Данные о футболистах и клубах сохранены. Вот файл для скачивания!')
            bot.send_message(message.chat.id, 'Файл успешно сохранён и отправлен вам!', reply_markup=MAIN_MENU)
        else:
            bot.send_message(message.chat.id, 'Ошибка: файл не создался корректно.', reply_markup=MAIN_MENU)

    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка при сохранении: {str(e)}', reply_markup=MAIN_MENU)

def start_bot():
    """Функция для запуска polling. Вызывайте ее только в основном скрипте."""
    bot.polling(none_stop=True, timeout=60)  # timeout для стабильности

if __name__ == '__main__':
    start_bot()
