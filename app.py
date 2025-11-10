import os
import mysql.connector as mysql
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import hashlib
from datetime import datetime
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')

# Конфигурация базы данных
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'Tochankau110574'),
    'database': os.getenv('MYSQL_DATABASE', 'Football')
}

# Папки для загрузки изображений
UPLOAD_FOLDER_PLAYERS = 'static/uploads/players'
UPLOAD_FOLDER_CLUBS = 'static/uploads/clubs'
app.config['UPLOAD_FOLDER_PLAYERS'] = UPLOAD_FOLDER_PLAYERS
app.config['UPLOAD_FOLDER_CLUBS'] = UPLOAD_FOLDER_CLUBS
os.makedirs(UPLOAD_FOLDER_PLAYERS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_CLUBS, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Список разрешенных таблиц
ALLOWED_TABLES = {
    'gentleman_coefficient', 'golden_ball', 'players', 'clubs',
    'personal_stats', 'awards', 'trophies', 'footballers', 'logs', 'users'
}

def get_db_connection():
    try:
        return mysql.connect(**DB_CONFIG)
    except Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

def test_connection():
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            conn.close()
            return True
        return False
    except Error:
        return False

def login_required(role='user'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Требуется авторизация', 'error')
                return redirect(url_for('login'))
            if role == 'admin' and session.get('role') != 'admin':
                flash('Доступ запрещен. Требуются права администратора.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_input(text, max_length=255, pattern=None):
    if not text or len(text.strip()) == 0:
        return False
    if len(text) > max_length:
        return False
    if pattern and not re.match(pattern, text):
        return False
    return True

def validate_number(value, min_val=0, max_val=100):
    try:
        num = int(value)
        return min_val <= num <= max_val
    except (ValueError, TypeError):
        return False

def validate_float(value, min_val=1.0, max_val=5.0):
    try:
        num = float(value)
        return min_val <= num <= max_val
    except (ValueError, TypeError):
        return False

def initialize_database():
    if not test_connection():
        print("Не удалось подключиться к MySQL. Проверьте настройки подключения.")
        return False

    try:
        temp_conn = mysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        with temp_conn.cursor() as temp_cursor:
            temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        temp_conn.close()

        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                tables_sql = [
                    '''CREATE TABLE IF NOT EXISTS gentleman_coefficient (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        coefficient FLOAT NOT NULL,
                        footballer VARCHAR(255) NOT NULL
                    )''',
                    '''CREATE TABLE IF NOT EXISTS golden_ball (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        holder VARCHAR(255) NOT NULL
                    )''',
                    '''CREATE TABLE IF NOT EXISTS players (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        victories INT NOT NULL DEFAULT 0,
                        losses INT NOT NULL DEFAULT 0,
                        draws INT NOT NULL DEFAULT 0,
                        player_name VARCHAR(255) NOT NULL
                    )''',
                    '''CREATE TABLE IF NOT EXISTS clubs (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        champion_league INT NOT NULL DEFAULT 0,
                        national_championship INT NOT NULL DEFAULT 0,
                        cup INT NOT NULL DEFAULT 0,
                        super_cup INT NOT NULL DEFAULT 0,
                        victories INT NOT NULL DEFAULT 0,
                        losses INT NOT NULL DEFAULT 0,
                        draws INT NOT NULL DEFAULT 0,
                        club_name VARCHAR(255) NOT NULL,
                        image_path VARCHAR(255) DEFAULT NULL
                    )''',
                    '''CREATE TABLE IF NOT EXISTS personal_stats (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        player_name VARCHAR(255) NOT NULL,
                        goals INT NOT NULL DEFAULT 0,
                        assists INT NOT NULL DEFAULT 0,
                        clean_sheets INT NOT NULL DEFAULT 0
                    )''',
                    '''CREATE TABLE IF NOT EXISTS awards (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        top_scorer VARCHAR(255) NOT NULL,
                        top_assist VARCHAR(255) NOT NULL
                    )''',
                    '''CREATE TABLE IF NOT EXISTS trophies (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        club_name VARCHAR(255) NOT NULL,
                        trophy_type VARCHAR(100) NOT NULL
                    )''',
                    '''CREATE TABLE IF NOT EXISTS footballers (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        first_name VARCHAR(100) NOT NULL,
                        last_name VARCHAR(100) NOT NULL,
                        age INT NOT NULL,
                        club VARCHAR(255) NOT NULL,
                        image_path VARCHAR(255) DEFAULT NULL
                    )''',
                    '''CREATE TABLE IF NOT EXISTS logs (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        text TEXT NOT NULL
                    )''',
                    '''CREATE TABLE IF NOT EXISTS users (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        login VARCHAR(100) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(50) DEFAULT 'user'
                    )'''
                ]

                for sql in tables_sql:
                    cursor.execute(sql)

                cursor.execute("SELECT COUNT(*) FROM users WHERE login = %s", ('admin',))
                if cursor.fetchone()[0] == 0:
                    admin_password = hashlib.sha256("Админчик".encode()).hexdigest()
                    cursor.execute(
                        "INSERT INTO users(login, password_hash, role) VALUES (%s, %s, %s)",
                        ('admin', admin_password, 'admin')
                    )

                connection.commit()
                print(f"База данных {DB_CONFIG['database']} инициализирована успешно")
                return True

    except Error as e:
        print(f"Ошибка инициализации базы данных: {e}")
        return False

def encrypt_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def write_log(text):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                cursor.execute("INSERT INTO logs(text) VALUES (%s)", (f'{timestamp}: {text}',))
                connection.commit()
    except Error as e:
        print(f"Ошибка записи лога: {e}")

@app.route('/')
def index():
    current_year = datetime.now().year
    return render_template('index.html', current_year=current_year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('login', '').strip()
        password = request.form.get('password', '')

        if not login_input or not password:
            flash('Заполните все поля', 'error')
            return render_template('login.html')

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, password_hash, role FROM users WHERE login = %s",
                        (login_input,)
                    )
                    user = cursor.fetchone()

                    if user and user[1] == encrypt_password(password):
                        session['user_id'] = user[0]
                        session['login'] = login_input
                        session['role'] = user[2]
                        write_log(f"Пользователь {login_input} вошел в систему с ролью {user[2]}")
                        flash('Успешный вход в систему', 'success')
                        return redirect(url_for('index'))
                    else:
                        flash('Неверный логин или пароль', 'error')

        except Error as e:
            flash('Ошибка подключения к базе данных', 'error')
            print(f"Ошибка входа: {e}")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login_input = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([login_input, password, confirm_password]):
            flash('Заполните все поля', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')

        if len(password) < 4:
            flash('Пароль должен быть не менее 4 символов', 'error')
            return render_template('register.html')

        if not validate_input(login_input, max_length=100):
            flash('Некорректный логин', 'error')
            return render_template('register.html')

        hashed_password = encrypt_password(password)

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (login, password_hash) VALUES (%s, %s)",
                        (login_input, hashed_password)
                    )
                    connection.commit()
                    flash('Регистрация успешна. Теперь вы можете войти.', 'success')
                    write_log(f"Зарегистрирован новый пользователь: {login_input}")
                    return redirect(url_for('login'))

        except Error as e:
            if "Duplicate entry" in str(e):
                flash('Пользователь с таким логином уже существует', 'error')
            else:
                flash('Ошибка регистрации', 'error')
                print(f"Ошибка регистрации: {e}")

    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'login' in session:
        write_log(f"Пользователь {session.get('login')} вышел из системы")
    session.clear()
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('index'))

@app.route('/vote/player', methods=['GET', 'POST'])
@login_required()
def vote_player():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        age = request.form.get('age', '').strip()
        club = request.form.get('club', '').strip()

        if not all([first_name, last_name, age, club]):
            flash('Заполните все обязательные поля', 'error')
            return render_template('vote_player.html')

        if not all([
            validate_input(first_name, max_length=100),
            validate_input(last_name, max_length=100),
            validate_input(club, max_length=255),
            validate_number(age, 0, 100)
        ]):
            flash('Некорректные данные в полях', 'error')
            return render_template('vote_player.html')

        numeric_fields = {
            'wins': (0, 100),
            'losses': (0, 100),
            'draws': (0, 100),
            'goals': (0, 100),
            'assists': (0, 100),
            'clean_sheets': (0, 100),
            'gentleman_coef': (1.0, 5.0)
        }

        field_values = {}
        for field, (min_val, max_val) in numeric_fields.items():
            value = request.form.get(field, '0').strip()
            if field == 'gentleman_coef':
                if not validate_float(value, min_val, max_val):
                    flash(f'Некорректное значение для {field}', 'error')
                    return render_template('vote_player.html')
                field_values[field] = float(value) if value else 1.0
            else:
                if not validate_number(value, min_val, max_val):
                    flash(f'Некорректное значение для {field}', 'error')
                    return render_template('vote_player.html')
                field_values[field] = int(value) if value else 0

        # Обработка загрузки изображения игрока
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER_PLAYERS'], filename)
                file.save(filepath)
                image_path = filepath

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM footballers")
                    count = cursor.fetchone()[0]
                    if count >= 30:
                        flash('Достигнуто максимальное количество футболистов (30)', 'error')
                        return render_template('vote_player.html')

                    cursor.execute(
                        "INSERT INTO footballers(first_name, last_name, age, club, image_path) VALUES (%s, %s, %s, %s, %s)",
                        (first_name, last_name, int(age), club, image_path)
                    )

                    cursor.execute(
                        "INSERT INTO personal_stats(player_name, goals, assists, clean_sheets) VALUES (%s, %s, %s, %s)",
                        (last_name, field_values['goals'], field_values['assists'], field_values['clean_sheets'])
                    )

                    cursor.execute(
                        "INSERT INTO players(player_name, victories, losses, draws) VALUES (%s, %s, %s, %s)",
                        (last_name, field_values['wins'], field_values['losses'], field_values['draws'])
                    )

                    cursor.execute(
                        "INSERT INTO gentleman_coefficient(coefficient, footballer) VALUES (%s, %s)",
                        (field_values['gentleman_coef'], f"{first_name} {last_name}")
                    )

                    cursor.execute(
                        "SELECT id, victories, losses, draws FROM clubs WHERE club_name = %s",
                        (club,)
                    )
                    club_data = cursor.fetchone()

                    if club_data:
                        club_id, club_victories, club_losses, club_draws = club_data
                        new_victories = club_victories + field_values['wins']
                        new_losses = club_losses + field_values['losses']
                        new_draws = club_draws + field_values['draws']
                        cursor.execute(
                            "UPDATE clubs SET victories = %s, losses = %s, draws = %s WHERE id = %s",
                            (new_victories, new_losses, new_draws, club_id)
                        )
                    else:
                        cursor.execute(
                            """INSERT INTO clubs(champion_league, national_championship, cup, super_cup, 
                                victories, losses, draws, club_name, image_path) 
                                VALUES (0, 0, 0, 0, %s, %s, %s, %s, NULL)""",
                            (field_values['wins'], field_values['losses'], field_values['draws'], club)
                        )

                    connection.commit()
                    write_log(f"Добавлен футболист: {first_name} {last_name}, клуб: {club}")
                    flash('Футболист успешно добавлен', 'success')

        except Error as e:
            flash(f'Ошибка при добавлении футболиста: {str(e)}', 'error')
            print(f"Ошибка добавления футболиста: {e}")

    return render_template('vote_player.html')

@app.route('/vote/team', methods=['GET', 'POST'])
@login_required()
def vote_team():
    if request.method == 'POST':
        club_name = request.form.get('club_name', '').strip()

        if not club_name:
            flash('Название клуба обязательно для заполнения', 'error')
            return render_template('vote_team.html')

        if not validate_input(club_name, max_length=255):
            flash('Некорректное название клуба', 'error')
            return render_template('vote_team.html')

        trophy_fields = {
            'super_cup': (0, 2),
            'champion_league': (0, 2),
            'national_championship': (0, 2),
            'cup': (0, 2)
        }

        trophy_values = {}
        for field, (min_val, max_val) in trophy_fields.items():
            value = request.form.get(field, '0').strip()
            if not validate_number(value, min_val, max_val):
                flash(f'Количество {field} должно быть от {min_val} до {max_val}', 'error')
                return render_template('vote_team.html')
            trophy_values[field] = int(value) if value else 0

        # Загрузка изображения клуба
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER_CLUBS'], filename)
                file.save(filepath)
                image_path = filepath

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT id FROM clubs WHERE club_name = %s", (club_name,))
                    club_exists = cursor.fetchone()

                    if club_exists:
                        club_id = club_exists[0]
                        # Обновление со вставкой пути к изображению, если есть
                        if image_path:
                            cursor.execute(
                                """UPDATE clubs SET super_cup = super_cup + %s, champion_league = champion_league + %s,
                                national_championship = national_championship + %s, cup = cup + %s, image_path = %s
                                WHERE id = %s""",
                                (trophy_values['super_cup'], trophy_values['champion_league'],
                                trophy_values['national_championship'], trophy_values['cup'], image_path, club_id)
                            )
                        else:
                            cursor.execute(
                                """UPDATE clubs SET super_cup = super_cup + %s, champion_league = champion_league + %s,
                                national_championship = national_championship + %s, cup = cup + %s
                                WHERE id = %s""",
                                (trophy_values['super_cup'], trophy_values['champion_league'],
                                trophy_values['national_championship'], trophy_values['cup'], club_id)
                            )
                    else:
                        cursor.execute(
                            """INSERT INTO clubs(super_cup, champion_league, national_championship, cup,
                            victories, losses, draws, club_name, image_path)
                            VALUES (%s, %s, %s, %s, 0, 0, 0, %s, %s)""",
                            (trophy_values['super_cup'], trophy_values['champion_league'],
                            trophy_values['national_championship'], trophy_values['cup'], club_name, image_path)
                        )
                        club_id = cursor.lastrowid

                    for trophy_type, count in trophy_values.items():
                        for _ in range(count):
                            cursor.execute(
                                "INSERT INTO trophies(club_name, trophy_type) VALUES (%s, %s)",
                                (club_name, trophy_type)
                            )

                    connection.commit()
                    write_log(f"Добавлен/обновлен клуб: {club_name}")
                    flash('Клуб успешно добавлен/обновлен', 'success')

        except Error as e:
            flash(f'Ошибка при работе с клубом: {str(e)}', 'error')
            print(f"Ошибка работы с клубом: {e}")

    return render_template('vote_team.html')

@app.route('/admin')
@login_required('admin')
def admin_panel():
    """Панель администратора."""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users")
                users_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM footballers")
                players_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM clubs")
                clubs_count = cursor.fetchone()[0]

                cursor.execute("SELECT text FROM logs ORDER BY id DESC LIMIT 5")
                logs_data = cursor.fetchall()

        recent_logs = []
        for log in logs_data:
            if ': ' in log[0]:
                timestamp, message = log[0].split(': ', 1)
                recent_logs.append({'timestamp': timestamp, 'message': message})
            else:
                recent_logs.append({'timestamp': 'N/A', 'message': log[0]})

        return render_template('admin_panel.html',
                               users_count=users_count,
                               players_count=players_count,
                               clubs_count=clubs_count,
                               recent_logs=recent_logs)

    except Error as e:
        flash(f'Ошибка загрузки панели: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/admin/users')
@login_required('admin')
def admin_users():
    """Управление пользователями."""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, login, role FROM users")
                users = cursor.fetchall()

        return render_template('admin_users.html', users=users)

    except Error as e:
        flash(f'Ошибка загрузки пользователей: {str(e)}', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/add_user', methods=['POST'])
@login_required('admin')
def admin_add_user():
    """Добавление пользователя."""
    login_input = request.form.get('login', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'user')

    if not all([login_input, password]):
        flash('Введите логин и пароль', 'error')
        return redirect(url_for('admin_users'))

    if len(password) < 4:
        flash('Пароль должен быть не менее 4 символов', 'error')
        return redirect(url_for('admin_users'))

    if not validate_input(login_input, max_length=100):
        flash('Некорректный логин', 'error')
        return redirect(url_for('admin_users'))

    hashed_password = encrypt_password(password)

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users(login, password_hash, role) VALUES (%s, %s, %s)",
                    (login_input, hashed_password, role)
                )
                connection.commit()

        flash('Пользователь успешно добавлен', 'success')
        write_log(f"Администратор добавил пользователя: {login_input}")

    except Error as e:
        if "Duplicate entry" in str(e):
            flash('Такой логин уже существует', 'error')
        else:
            flash(f'Ошибка добавления пользователя: {str(e)}', 'error')

    return redirect(url_for('admin_users'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required('admin')
def admin_delete_user(user_id):
    """Удаление пользователя."""
    if user_id == session.get('user_id'):
        flash('Нельзя удалить самого себя', 'error')
        return redirect(url_for('admin_users'))

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                connection.commit()

        flash('Пользователь удален', 'success')
        write_log(f"Администратор удалил пользователя с ID: {user_id}")

    except Error as e:
        flash(f'Ошибка удаления пользователя: {str(e)}', 'error')

    return redirect(url_for('admin_users'))

@app.route('/admin/awards')
@login_required('admin')
def admin_awards():
    """Расчет наград."""
    calculate_awards_and_winner()
    flash('Награды и победитель Золотого мяча обновлены', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/golden_ball')
@login_required('admin')
def admin_golden_ball():
    """Просмотр Золотого мяча."""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT holder FROM golden_ball")
                holders = cursor.fetchall()

        return render_template('admin_golden_ball.html', holders=holders)

    except Error as e:
        flash(f'Ошибка загрузки Золотого мяча: {str(e)}', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/query', methods=['GET', 'POST'])
@login_required('admin')
def admin_query():
    """Выполнение SQL-запросов."""
    if request.method == 'POST':
        query = request.form.get('query', '').strip()

        if not query:
            flash('Введите SQL-запрос', 'error')
            return render_template('admin_query.html')

        # Запрещенные операции для безопасности
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in query.upper() for keyword in dangerous_keywords):
            flash('Запрещенный тип запроса. Разрешены только SELECT запросы.', 'error')
            return render_template('admin_query.html')

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)

                    if query.upper().strip().startswith('SELECT'):
                        rows = cursor.fetchall()
                        headers = [description[0] for description in cursor.description] if cursor.description else []
                        result = {'headers': headers, 'rows': rows}
                        write_log(f"Администратор выполнил запрос: {query}")
                        return render_template('admin_query.html', result=result)
                    else:
                        connection.commit()
                        flash('Запрос выполнен успешно', 'success')
                        write_log(f"Администратор выполнил запрос: {query}")

        except Error as e:
            flash(f'Ошибка выполнения запроса: {str(e)}', 'error')

    return render_template('admin_query.html')

@app.route('/admin/delete_record', methods=['POST'])
@login_required('admin')
def admin_delete_record():
    """Удаление записи из базы данных."""
    table = request.form.get('table', '').strip()
    record_id = request.form.get('record_id', '').strip()

    # Валидация ввода
    if not table or not record_id:
        flash('Не указана таблица или ID записи', 'error')
        return redirect(url_for('admin_panel'))

    if table not in ALLOWED_TABLES:
        flash('Недопустимое имя таблицы', 'error')
        return redirect(url_for('admin_panel'))

    if not record_id.isdigit():
        flash('ID записи должен быть числом', 'error')
        return redirect(url_for('admin_panel'))

    record_id = int(record_id)

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Проверка существования записи
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE id = %s", (record_id,))
                if cursor.fetchone()[0] == 0:
                    flash(f'Запись с id={record_id} не найдена в таблице {table}', 'error')
                    return redirect(url_for('admin_panel'))

                # Каскадное удаление для связанных данных
                if table == "footballers":
                    cursor.execute("SELECT last_name, first_name, club FROM footballers WHERE id = %s", (record_id,))
                    player_data = cursor.fetchone()
                    if player_data:
                        last_name, first_name, club = player_data
                        cursor.execute("DELETE FROM footballers WHERE id = %s", (record_id,))
                        cursor.execute("DELETE FROM personal_stats WHERE player_name = %s", (last_name,))
                        cursor.execute("DELETE FROM players WHERE player_name = %s", (last_name,))
                        full_name = f"{first_name} {last_name}"
                        cursor.execute("DELETE FROM gentleman_coefficient WHERE footballer = %s", (full_name,))

                elif table == "clubs":
                    cursor.execute("SELECT club_name FROM clubs WHERE id = %s", (record_id,))
                    club_data = cursor.fetchone()
                    if club_data:
                        club_name = club_data[0]
                        cursor.execute("DELETE FROM clubs WHERE id = %s", (record_id,))
                        cursor.execute("DELETE FROM trophies WHERE club_name = %s", (club_name,))
                        cursor.execute("UPDATE footballers SET club='' WHERE club = %s", (club_name,))
                else:
                    cursor.execute(f"DELETE FROM {table} WHERE id = %s", (record_id,))

                connection.commit()
                flash(f'Запись с id={record_id} из таблицы {table} успешно удалена', 'success')
                write_log(f"Удалена запись id={record_id} из таблицы {table}")

    except Error as e:
        flash(f'Не удалось удалить запись: {str(e)}', 'error')

    return redirect(url_for('admin_panel'))

def calculate_awards_and_winner():
    """Расчет наград и победителя Золотого мяча."""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Очистка предыдущих наград
                cursor.execute("DELETE FROM awards")
                cursor.execute("DELETE FROM golden_ball")

                # Лучший бомбардир
                cursor.execute(
                    "SELECT player_name FROM personal_stats WHERE goals = (SELECT MAX(goals) FROM personal_stats) LIMIT 1"
                )
                top_scorer_data = cursor.fetchone()
                top_scorer = top_scorer_data[0] if top_scorer_data else "Не определен"

                # Лучший ассистент
                cursor.execute(
                    "SELECT player_name FROM personal_stats WHERE assists = (SELECT MAX(assists) FROM personal_stats) LIMIT 1"
                )
                top_assist_data = cursor.fetchone()
                top_assist = top_assist_data[0] if top_assist_data else "Не определен"

                # Добавление наград
                cursor.execute(
                    "INSERT INTO awards(top_scorer, top_assist) VALUES (%s, %s)",
                    (top_scorer, top_assist)
                )

                # Расчет Золотого мяча
                query = '''
                    SELECT f.first_name, f.last_name, f.club,
                           ps.goals, ps.assists, ps.clean_sheets,
                           p.victories, p.draws, p.losses,
                           c.victories as club_victories, c.draws as club_draws, c.losses as club_losses,
                           COALESCE(gc.coefficient, 1.0) as gentleman_coef
                    FROM footballers f
                    JOIN personal_stats ps ON ps.player_name = f.last_name
                    JOIN players p ON p.player_name = f.last_name
                    JOIN clubs c ON c.club_name = f.club
                    LEFT JOIN gentleman_coefficient gc ON gc.footballer = CONCAT(f.first_name, ' ', f.last_name)
                '''
                cursor.execute(query)
                players = cursor.fetchall()

                best_score = 0
                best_player = None

                for player in players:
                    (first_name, last_name, club, goals, assists, clean_sheets,
                     p_victories, p_draws, p_losses, c_victories, c_draws, c_losses, gentleman_coef) = player

                    score = (goals + assists + clean_sheets +
                             c_victories + c_draws + p_victories + p_draws -
                             c_losses - p_losses) * gentleman_coef

                    if score > best_score:
                        best_score = score
                        best_player = f"{first_name} {last_name}"

                # Добавление победителя
                if best_player:
                    cursor.execute("INSERT INTO golden_ball(holder) VALUES (%s)", (best_player,))
                    write_log(f"Победитель Золотого мяча: {best_player} с очками {best_score}")

                connection.commit()
                write_log(f"Награды обновлены: лучший бомбардир - {top_scorer}, лучший ассистент - {top_assist}")

    except Error as e:
        print(f"Ошибка расчета наград: {e}")

if __name__ == '__main__':
    if initialize_database():
        print("Flask приложение успешно запущено.")
        app.run(host='0.0.0.0', debug=False)
    else:
        print("Ошибка инициализации базы данных. Приложение не запущено.")
        exit(1)