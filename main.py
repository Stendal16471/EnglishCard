"""
English Learning Telegram Bot with Difficulty Levels

This bot helps users learn English words with features:
- Personal dictionary
- Knowledge testing with difficulty levels
- Progress statistics

The module interacts with PostgreSQL database and implements:
1. User dictionary management
2. Testing system with 3 difficulty levels
3. Statistics collection

Example usage:
    python main.py
"""

import random

import psycopg2
import telebot
from telebot import types

# Database connection settings
DB_CONFIG = {
    'dbname': 'learning_english_db',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': '5432',
    'client_encoding': 'UTF8'
}

# Difficulty levels configuration
DIFFICULTY_LEVELS = {
    'easy': {'name': '🍏 Легкий', 'words_limit': 10,
             'description': 'Только простые слова (цвета, числа)'},
    'medium': {'name': '🍊 Средний', 'words_limit': 20,
               'description': 'Смесь простых и сложных слов'},
    'hard': {'name': '🌶️ Сложный', 'words_limit': 50,
             'description': 'Все слова, включая редкие'}
}

# Initialize bot
bot = telebot.TeleBot('TOKEN')


def create_main_keyboard():
    """Create the main menu keyboard with difficulty level button.

    Returns:
        types.ReplyKeyboardMarkup: Keyboard with buttons:
            - Start test
            - My dictionary
            - Add/Remove word
            - Statistics
            - Difficulty level
            - Help
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🎯 Начать тест"))
    markup.row(types.KeyboardButton("📖 Мой словарь"))
    markup.row(types.KeyboardButton("➕ Добавить слово"),
               types.KeyboardButton("➖ Удалить слово"))
    markup.row(types.KeyboardButton("📊 Статистика"),
               types.KeyboardButton("⚙️ Уровень сложности"))
    markup.row(types.KeyboardButton("❓ Помощь"))
    return markup


def safe_connect():
    """Establish secure database connection with error handling.

    Returns:
        psycopg2.connection or None: Connection object or None if error occurs.

    Raises:
        psycopg2.OperationalError: If connection to database fails.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None


def initialize_database():
    """Initialize database structure with difficulty level column.

    Creates all necessary tables if they don't exist:
        - users: user information with difficulty level
        - common_words: common vocabulary
        - user_words: personal user words
        - user_stats: answer statistics

    Returns:
        bool: True if initialization successful, False otherwise.

    Raises:
        psycopg2.DatabaseError: For SQL query execution errors.
    """
    conn = safe_connect()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            # Create users table with difficulty column
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(100),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    difficulty VARCHAR(10) DEFAULT 'medium'
                )
            """)

            # Creating a table of common words
            cur.execute("""
                CREATE TABLE IF NOT EXISTS common_words (
                    word_id SERIAL PRIMARY KEY,
                    english_word VARCHAR(100) NOT NULL,
                    russian_translation VARCHAR(100) NOT NULL,
                    word_type VARCHAR(50)
                )
            """)

            # Creating a table of custom words
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_words (
                    user_word_id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    english_word VARCHAR(100) NOT NULL,
                    russian_translation VARCHAR(100) NOT NULL,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)

            # Creating a statistics table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    stat_id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    word_id INTEGER,
                    is_correct BOOLEAN,
                    attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Checking the availability of data in common_words
            cur.execute("SELECT COUNT(*) FROM common_words")
            if cur.fetchone()[0] == 0:
                # Adding the initial set of words
                common_words = [
                    # Colors
                    ('red', 'красный', 'цвет'), ('blue', 'синий', 'цвет'),
                    ('green', 'зеленый', 'цвет'), ('yellow', 'желтый', 'цвет'),
                    ('black', 'черный', 'цвет'), ('white', 'белый', 'цвет'),
                    ('orange', 'оранжевый', 'цвет'), ('purple', 'фиолетовый', 'цвет'),
                    ('pink', 'розовый', 'цвет'), ('brown', 'коричневый', 'цвет'),

                    # Pronouns
                    ('I', 'я', 'местоимение'), ('you', 'ты', 'местоимение'),
                    ('he', 'он', 'местоимение'), ('she', 'она', 'местоимение'),
                    ('it', 'оно', 'местоимение'), ('we', 'мы', 'местоимение'),
                    ('they', 'они', 'местоимение'), ('my', 'мой', 'местоимение'),
                    ('your', 'твой', 'местоимение'), ('our', 'наш', 'местоимение'),

                    # Numbers (1-10)
                    ('one', 'один', 'число'), ('two', 'два', 'число'),
                    ('three', 'три', 'число'), ('four', 'четыре', 'число'),
                    ('five', 'пять', 'число'), ('six', 'шесть', 'число'),
                    ('seven', 'семь', 'число'), ('eight', 'восемь', 'число'),
                    ('nine', 'девять', 'число'), ('ten', 'десять', 'число'),

                    # Animals
                    ('cat', 'кошка', 'животное'), ('dog', 'собака', 'животное'),
                    ('bird', 'птица', 'животное'), ('fish', 'рыба', 'животное'),
                    ('horse', 'лошадь', 'животное'), ('cow', 'корова', 'животное'),
                    ('pig', 'свинья', 'животное'), ('rabbit', 'кролик', 'животное'),
                    ('lion', 'лев', 'животное'), ('tiger', 'тигр', 'животное'),

                    # Family
                    ('mother', 'мать', 'семья'), ('father', 'отец', 'семья'),
                    ('brother', 'брат', 'семья'), ('sister', 'сестра', 'семья'),
                    ('son', 'сын', 'семья'), ('daughter', 'дочь', 'семья'),
                    ('grandmother', 'бабушка', 'семья'), ('grandfather', 'дедушка', 'семья'),

                    # Basic verbs
                    ('go', 'идти', 'глагол'), ('eat', 'есть', 'глагол'),
                    ('drink', 'пить', 'глагол'), ('sleep', 'спать', 'глагол'),
                    ('read', 'читать', 'глагол'), ('write', 'писать', 'глагол'),
                    ('speak', 'говорить', 'глагол'), ('listen', 'слушать', 'глагол'),
                    ('love', 'любить', 'глагол'), ('learn', 'учить', 'глагол'),

                    # Difficult words
                    ('abundance', 'изобилие', 'сложное'),
                    ('benevolent', 'доброжелательный', 'сложное'),
                    ('conundrum', 'головоломка', 'сложное'),
                    ('diligent', 'усердный', 'сложное'),
                    ('ephemeral', 'эфемерный', 'сложное'),
                    ('fastidious', 'привередливый', 'сложное')
                ]
                for word in common_words:
                    cur.execute(
                        "INSERT INTO common_words (english_word, russian_translation, word_type) "
                        "VALUES (%s, %s, %s)",
                        word
                    )
                print("Добавлен базовый набор слов")

            conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        return False
    finally:
        if conn:
            conn.close()


# Initializing the database at startup
if not initialize_database():
    print("Не удалось инициализировать базу данных. "
          "Проверьте настройки подключения.")
    exit(1)


@bot.message_handler(commands=['start'])
def start(message):
    """Handle /start command with difficulty level initialization.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Checks if user exists in database
        - Registers new user if not exists
        - Sets default difficulty level ('medium')
        - Sends welcome message with instructions
        - Shows main menu keyboard
    """
    user = message.from_user

    # Add user to database with existence check
    conn = safe_connect()
    if not conn:
        return

    with conn, conn.cursor() as cur:
        # First check if user exists
        cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user.id,))
        exists = cur.fetchone()

        if not exists:
            # Insert new user if doesn't exist
            cur.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, difficulty) "
                "VALUES (%s, %s, %s, %s, %s)",
                (user.id, user.username, user.first_name, user.last_name, 'medium')
            )
            print(f"New user added: {user.id} {user.username}")
        else:
            print(f"User already exists: {user.id} {user.username}")

    # Send welcome message
    welcome_message = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Меня зовут Коннор. Помогу тебе с изучением английских слов. "
        "Вот что я умею:\n\n"
        "🎯 Начать тест - Проведу тест на знание слов\n"
        "⚙️ Уровень сложности - Изменю сложность тестов\n"
        "📖 Мой словарь - Покажу твой словарь\n"
        "➕ Добавить слово - Добавлю новое слово\n"
        "📊 Статистика - Покажу твою статистику\n"
        "❓ Помощь - Дам справку по всем командам\n\n"
        "Начни с добавления слов или сразу пройди тест!"
    )
    bot.send_message(message.chat.id, welcome_message,
                     reply_markup=create_main_keyboard())


@bot.message_handler(commands=['help'])
def show_help(message):
    """Show help information about available commands.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Sends formatted help message with HTML formatting
        - Shows main menu keyboard
    """
    help_text = """
📚 <b>Вот мои функции:</b>

🎯 Начать тест - Проверить знание слов
⚙️ Уровень сложности - Изменить сложность тестов
📖 Мой словарь - Показать все слова
➕ Добавить слово - Добавить новое слово
➖ Удалить слово - Удалить слово из словаря
📊 Статистика - Показать прогресс обучения

<b>Формат добавления слов:</b>
<code>английское_слово - русский_перевод</code>
Пример: <code>apple - яблоко</code>
"""
    bot.send_message(message.chat.id, help_text, parse_mode='HTML',
                     reply_markup=create_main_keyboard())


@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def handle_help_button(message):
    """Handle help button press.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Calls show_help() function
    """
    show_help(message)


@bot.message_handler(
    func=lambda message: message.text == "⚙️ Уровень сложности"
)
def show_difficulty_menu(message):
    """Show difficulty level selection menu.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Gets current user's difficulty level from database
        - Shows menu with available levels (marks current with ✓)
        - Provides back to main menu button
    """
    user_id = message.from_user.id
    conn = safe_connect()
    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.",
                         reply_markup=create_main_keyboard())
        return

    try:
        with conn.cursor() as cur:
            # Getting the user's current difficulty level
            cur.execute("SELECT difficulty FROM users WHERE user_id = %s", (user_id,))
            current_difficulty = cur.fetchone()
            current_level = current_difficulty[0] if current_difficulty else 'medium'

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                               one_time_keyboard=True)
            for level in DIFFICULTY_LEVELS.values():
                # Add a "✓" mark to the current level
                prefix = (
                    "✓ "
                    if level['name'] == DIFFICULTY_LEVELS[current_level]['name']
                    else ""
                )
                markup.add(types.KeyboardButton(f"{prefix}{level['name']}"))
            markup.add(types.KeyboardButton("🔙 Главное меню"))

            bot.send_message(
                message.chat.id,
                "📊 <b>Выберите уровень сложности тестов:</b>\n\n" +
                "\n".join([f"{level['name']} - {level['description']}"
                           for level in DIFFICULTY_LEVELS.values()]),
                parse_mode='HTML',
                reply_markup=markup
            )
    except Exception as e:
        print(f"Ошибка при получении уровня сложности: {e}")
        bot.send_message(message.chat.id,
                         "Произошла ошибка при получении уровня сложности.",
                         reply_markup=create_main_keyboard())
    finally:
        conn.close()


@bot.message_handler(
    func=lambda message: any(message.text.replace("✓ ", "") == level['name']
                             for level in DIFFICULTY_LEVELS.values()))
def set_difficulty_level(message):
    """Set the selected difficulty level for the user.

    Args:
        message (telebot.types.Message): Message containing selected difficulty level.

    Behavior:
        - Extracts difficulty level from button text (removes ✓ mark if present)
        - Updates user's difficulty setting in database
        - Sends confirmation message with new level info
        - Returns to main menu
    """
    user_id = message.from_user.id
    # Remove the "✓" mark if it is present
    difficulty_text = message.text.replace("✓ ", "")
    # Find the key of the difficulty level by name
    difficulty = next(key for key, level in DIFFICULTY_LEVELS.items()
                      if level['name'] == difficulty_text)

    conn = safe_connect()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET difficulty = %s WHERE user_id = %s
                """, (difficulty, user_id))
                conn.commit()

                bot.send_message(
                    message.chat.id,
                    f"✅ Уровень сложности установлен: {DIFFICULTY_LEVELS[difficulty]['name']}\n"
                    f"{DIFFICULTY_LEVELS[difficulty]['description']}",
                    reply_markup=create_main_keyboard()
                )
        except Exception as e:
            print(f"Ошибка при установке уровня сложности: {e}")
            bot.send_message(message.chat.id,
                             "Произошла ошибка при изменении уровня сложности.",
                             reply_markup=create_main_keyboard())
        finally:
            conn.close()
    else:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.",
                         reply_markup=create_main_keyboard())


@bot.message_handler(commands=['quiz'])
def start_quiz(message):
    """Start knowledge test considering user's difficulty level.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        1. Gets user's current difficulty level from database
        2. Selects random word according to difficulty:
           - Easy: only simple words (colors, pronouns, numbers)
           - Medium: all words except complex ones
           - Hard: all words without restrictions
        3. Creates 4 answer options (1 correct + 3 random wrong)
        4. Shows question with answer options
        5. Registers answer handler check_quiz_answer()
    """
    user_id = message.from_user.id
    conn = safe_connect()
    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.",
                         reply_markup=create_main_keyboard())
        return

    try:
        with conn.cursor() as cur:
            # Getting the user's current difficulty level
            cur.execute("SELECT difficulty FROM users WHERE user_id = %s", (user_id,))
            difficulty_row = cur.fetchone()
            difficulty = (
                difficulty_row[0] if difficulty_row and difficulty_row[0] else 'medium'
            )
            words_limit = DIFFICULTY_LEVELS[difficulty]['words_limit']

            # Form a request depending on the level of complexity
            if difficulty == 'easy':
                # Only simple words (colors, pronouns, numbers)
                cur.execute("""
                    SELECT source, word_id, english_word, russian_translation FROM (
                        (SELECT 'common' AS source, word_id, english_word, russian_translation 
                         FROM common_words 
                         WHERE word_type IN ('цвет', 'местоимение', 'число')
                         ORDER BY RANDOM() LIMIT %s)
                        UNION ALL
                        (SELECT 'user' AS source, user_word_id, english_word, russian_translation 
                         FROM user_words 
                         WHERE user_id = %s AND is_active = TRUE
                         ORDER BY RANDOM() LIMIT %s)
                    ) AS combined_words ORDER BY RANDOM() LIMIT 1
                """, (words_limit, user_id, words_limit))
            elif difficulty == 'medium':
                # All words except complex ones
                cur.execute("""
                    SELECT source, word_id, english_word, russian_translation FROM (
                        (SELECT 'common' AS source, word_id, english_word, russian_translation 
                         FROM common_words 
                         WHERE word_type != 'сложное' OR word_type IS NULL
                         ORDER BY RANDOM() LIMIT %s)
                        UNION ALL
                        (SELECT 'user' AS source, user_word_id, english_word, russian_translation 
                         FROM user_words 
                         WHERE user_id = %s AND is_active = TRUE
                         ORDER BY RANDOM() LIMIT %s)
                    ) AS combined_words ORDER BY RANDOM() LIMIT 1
                """, (words_limit, user_id, words_limit))
            else:
                # All words without restrictions
                cur.execute("""
                    SELECT source, word_id, english_word, russian_translation FROM (
                        (SELECT 'common' AS source, word_id, english_word, russian_translation 
                         FROM common_words 
                         ORDER BY RANDOM() LIMIT %s)
                        UNION ALL
                        (SELECT 'user' AS source, user_word_id, english_word, russian_translation 
                         FROM user_words 
                         WHERE user_id = %s AND is_active = TRUE
                         ORDER BY RANDOM() LIMIT %s)
                    ) AS combined_words ORDER BY RANDOM() LIMIT 1
                """, (words_limit, user_id, words_limit))

            word_data = cur.fetchone()
            if not word_data:
                bot.send_message(message.chat.id,
                                 "Нет слов для тестирования. Добавь слова через /add_word",
                                 reply_markup=create_main_keyboard())
                return

            source_type, word_id, english_word, correct_translation = word_data

            # Get 3 random incorrect options
            cur.execute("""
                SELECT russian_translation FROM (
                    (SELECT russian_translation FROM common_words WHERE russian_translation != %s)
                    UNION ALL
                    (SELECT russian_translation FROM user_words 
                     WHERE user_id = %s AND russian_translation != %s AND is_active = TRUE)
                ) AS wrong_options ORDER BY RANDOM() LIMIT 3
            """, (correct_translation, user_id, correct_translation))

            wrong_answers = [row[0] for row in cur.fetchall()]
            options = [correct_translation] + wrong_answers
            random.shuffle(options)

            # Creating a keyboard with options
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                               one_time_keyboard=True)
            for option in options:
                markup.add(types.KeyboardButton(option))
            markup.add(types.KeyboardButton("🔙 Главное меню"))

            # Saving the data for verification
            msg = bot.send_message(
                message.chat.id,
                f"Уровень: {DIFFICULTY_LEVELS[difficulty]['name']}\n"
                f"Как переводится слово: <b>{english_word}</b>?",
                parse_mode='HTML',
                reply_markup=markup
            )

            # Registering the response handler
            bot.register_next_step_handler(
                msg,
                lambda m: check_quiz_answer(m, correct_translation, source_type, word_id)
            )

    except Exception as e:
        print(f"Ошибка при запуске теста: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при запуске теста.",
                         reply_markup=create_main_keyboard())
    finally:
        conn.close()


@bot.message_handler(func=lambda message: message.text == "🎯 Начать тест")
def handle_quiz_button(message):
    """Handle quiz start button press.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Calls start_quiz() function
    """
    start_quiz(message)


def check_quiz_answer(message, correct_answer, source_type, word_id):
    """Process user's quiz answer and save result.

    Args:
        message (telebot.types.Message): User's answer message.
        correct_answer (str): Correct translation.
        source_type (str): 'common' or 'user' word source.
        word_id (int): Word ID in corresponding table.

    Behavior:
        - Checks if answer is correct
        - Saves result to database (user_stats table)
        - Provides feedback to user
        - Offers to continue with next question or return to main menu
    """
    user_answer = message.text
    user_id = message.from_user.id

    # If the user has selected the "Main Menu"
    if user_answer == "🔙 Главное меню":
        bot.send_message(message.chat.id, "Выбери действие:",
                         reply_markup=create_main_keyboard())
        return

    # Checking the response
    if user_answer == correct_answer:
        response = "✅ Правильно! Молодец :)"
        is_correct = True
    else:
        response = "❌ Неправильно :( Попробуй еще раз."
        is_correct = False

    # Saving the result
    conn = safe_connect()
    if conn:
        try:
            with conn.cursor() as cur:
                if source_type == 'common':
                    cur.execute(
                        "INSERT INTO user_stats (user_id, word_id, is_correct) VALUES (%s, %s, %s)",
                        (user_id, word_id, is_correct)
                    )
                else:
                    cur.execute(
                        "INSERT INTO user_stats (user_id, word_id, is_correct) VALUES (%s, %s, %s)",
                        (user_id, -word_id, is_correct)
                    )
                conn.commit()
        except Exception as e:
            print(f"Ошибка при сохранении результата: {e}")
        finally:
            conn.close()

    # Suggests continue
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🎯 Следующий вопрос"))
    markup.add(types.KeyboardButton("🔙 Главное меню"))

    bot.send_message(message.chat.id, response, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "🎯 Следующий вопрос")
def handle_next_question(message):
    """Handle next question button press.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Calls start_quiz() function
    """
    start_quiz(message)


@bot.message_handler(func=lambda message: message.text
                                          in ["🔙 Главное меню", "Главное меню"])
def handle_back_button(message):
    """Handle back to main menu button press.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Shows main menu keyboard
    """
    bot.send_message(message.chat.id, "Выбери действие:",
                     reply_markup=create_main_keyboard())


@bot.message_handler(commands=['my_words'])
def show_my_words(message):
    """Display the user's personal dictionary.

    Args:
        message (telebot.types.Message): The incoming message object.

    Behavior:
        - Shows all active words from user's dictionary
        - Splits long word lists into multiple messages (3000 char limit)
        - Displays total word count
        - Provides instructions for word removal
    """
    user_id = message.from_user.id
    conn = safe_connect()
    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.",
                         reply_markup=create_main_keyboard())
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT english_word, russian_translation 
                FROM user_words 
                WHERE user_id = %s AND is_active = TRUE
                ORDER BY english_word
            """, (user_id,))

            words = cur.fetchall()

            if not words:
                bot.send_message(message.chat.id,
                                 "Твой словарь пуст. Добавь слова через /add_word",
                                 reply_markup=create_main_keyboard())
                return

            words_list = ["📚 <b>Твой словарь:</b>\n"]
            words_list.extend([f"• {en_word} - {ru_word}" for en_word, ru_word in words])

            max_length = 3000
            current_part = []
            current_length = 0

            for word in words_list:
                word_length = len(word) + 1
                if current_length + word_length > max_length:
                    bot.send_message(message.chat.id, "\n".join(current_part), parse_mode='HTML')
                    current_part = []
                    current_length = 0
                current_part.append(word)
                current_length += word_length

            if current_part:
                bot.send_message(message.chat.id, "\n".join(current_part), parse_mode='HTML')

            bot.send_message(
                message.chat.id,
                f"Всего слов: {len(words)}\n"
                "Используй /remove_word для удаления слов",
                parse_mode='HTML',
                reply_markup=create_main_keyboard()
            )

    except Exception as e:
        print(f"Ошибка при получении слов: {e}")
        bot.send_message(message.chat.id,
                         "Произошла ошибка при получении списка слов.",
                         reply_markup=create_main_keyboard())
    finally:
        conn.close()


@bot.message_handler(func=lambda message: message.text == "📖 Мой словарь")
def handle_my_words_button(message):
    """Handle my dictionary button press.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Calls show_my_words() function
    """
    show_my_words(message)


@bot.message_handler(commands=['add_word'])
def add_word(message):
    """Initiate the word addition process.

    Args:
        message (telebot.types.Message): The incoming message object.

    Behavior:
        - Removes keyboard to allow free text input
        - Sends instructions for word format
        - Registers process_new_word as next step handler
    """
    bot.send_message(
        message.chat.id,
        "Введи новое слово в формате:\n"
        "английское_слово - русский_перевод\n\n"
        "Например: apple - яблоко",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(message, process_new_word)


@bot.message_handler(func=lambda message: message.text == "➕ Добавить слово")
def handle_add_word_button(message):
    """Handle add word button press.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Calls add_word() function
    """
    add_word(message)


def process_new_word(message):
    """Process new word input from user.

    Args:
        message (telebot.types.Message): Message containing word pair.

    Behavior:
        - Validates input format ("eng - rus")
        - Adds word to user's dictionary in database
        - Shows confirmation message with word count
        - Returns to main menu on success
        - Shows error message on failure
    """
    user_id = message.from_user.id
    text = message.text.strip()

    try:
        english, russian = [part.strip() for part in text.split('-', 1)]
        if not english or not russian:
            raise ValueError

        conn = safe_connect()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO user_words (user_id, english_word, russian_translation) "
                        "VALUES (%s, %s, %s)",
                        (user_id, english.lower(), russian.lower())
                    )

                    cur.execute(
                        "SELECT COUNT(*) FROM user_words WHERE user_id = %s AND is_active = TRUE",
                        (user_id,)
                    )
                    word_count = cur.fetchone()[0]

                    conn.commit()

                    bot.send_message(
                        message.chat.id,
                        f"✅ Слово '{english}' добавлено в твой словарь.\n"
                        f"📚 Теперь ты изучаешь {word_count} слов.",
                        reply_markup=create_main_keyboard()
                    )
            except Exception as e:
                print(f"Ошибка при добавлении слова: {e}")
                bot.send_message(message.chat.id, "Произошла ошибка при добавлении слова.",
                                 reply_markup=create_main_keyboard())
            finally:
                conn.close()
    except ValueError:
        bot.send_message(
            message.chat.id,
            "Неправильный формат. Пожалуйста, введи слово в формате:\n"
            "английское_слово - русский_перевод\n\n"
            "Попробуй снова: /add_word",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(commands=['remove_word'])
def remove_word(message):
    """Initiate word removal process.

    Args:
        message (telebot.types.Message): The incoming message object.

    Behavior:
        - Fetches user's active words from database
        - Creates keyboard with word options
        - Registers confirm_remove as next handler
    """
    user_id = message.from_user.id
    conn = safe_connect()
    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.",
                         reply_markup=create_main_keyboard())
        return

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_word_id, english_word FROM user_words "
                "WHERE user_id = %s AND is_active = TRUE",
                (user_id,)
            )
            words = cur.fetchall()

            if not words:
                bot.send_message(message.chat.id, "У тебя нет слов для удаления.",
                                 reply_markup=create_main_keyboard())
                return

            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True,
                                               resize_keyboard=True)
            word_dict = {}
            for word_id, english_word in words:
                markup.add(types.KeyboardButton(english_word))
                word_dict[english_word] = word_id
            markup.add(types.KeyboardButton("🔙 Главное меню"))

            msg = bot.send_message(
                message.chat.id,
                "Выбери слово для удаления:",
                reply_markup=markup
            )

            bot.register_next_step_handler(msg, lambda m: confirm_remove(m, word_dict))

    except Exception as e:
        print(f"Ошибка при получении слов для удаления: {e}")
        bot.send_message(message.chat.id,
                         "Произошла ошибка при получении списка слов.",
                         reply_markup=create_main_keyboard())
    finally:
        conn.close()


@bot.message_handler(func=lambda message: message.text == "➖ Удалить слово")
def handle_remove_word_button(message):
    """Handle remove word button press.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Calls remove_word() function
    """
    remove_word(message)


def confirm_remove(message, word_dict):
    """Confirm and process word removal.

    Args:
        message (telebot.types.Message): Message with word to remove.
        word_dict (dict): Dictionary mapping words to their IDs.

    Behavior:
        - Marks word as inactive in database
        - Shows confirmation message with updated word count
        - Returns to main menu
    """
    user_id = message.from_user.id
    word_to_remove = message.text

    if word_to_remove == "🔙 Главное меню":
        bot.send_message(message.chat.id, "Выбери действие:",
                         reply_markup=create_main_keyboard())
        return

    if word_to_remove not in word_dict:
        bot.send_message(message.chat.id, "Слово не найдено в твоем словаре.",
                         reply_markup=create_main_keyboard())
        return

    conn = safe_connect()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE user_words SET is_active = FALSE "
                    "WHERE user_word_id = %s AND user_id = %s",
                    (word_dict[word_to_remove], user_id)
                )

                cur.execute(
                    "SELECT COUNT(*) FROM user_words "
                    "WHERE user_id = %s AND is_active = TRUE",
                    (user_id,)
                )
                word_count = cur.fetchone()[0]

                conn.commit()

                bot.send_message(
                    message.chat.id,
                    f"🗑️ Слово '{word_to_remove}' удалено из твоего словаря.\n"
                    f"📚 Теперь ты изучаешь {word_count} слов.",
                    reply_markup=create_main_keyboard()
                )
        except Exception as e:
            print(f"Ошибка при удалении слова: {e}")
            bot.send_message(message.chat.id, "Произошла ошибка при удалении слова.",
                             reply_markup=create_main_keyboard())
        finally:
            conn.close()


@bot.message_handler(commands=['stats'])
def show_stats(message):
    """Display user learning statistics.

    Args:
        message (telebot.types.Message): The incoming message object.

    Behavior:
        - Shows current difficulty level
        - Displays total words in dictionary
        - Shows correct/total answers count
        - Calculates and shows accuracy percentage
    """
    user_id = message.from_user.id
    conn = safe_connect()
    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.",
                         reply_markup=create_main_keyboard())
        return

    try:
        with conn.cursor() as cur:
            # Getting the current difficulty level
            cur.execute("SELECT difficulty FROM users WHERE user_id = %s", (user_id,))
            difficulty_row = cur.fetchone()
            difficulty = (
                difficulty_row[0] if difficulty_row and difficulty_row[0] else 'medium'
            )

            cur.execute(
                "SELECT COUNT(*) FROM user_words WHERE user_id = %s AND is_active = TRUE",
                (user_id,)
            )
            total_words = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM user_stats WHERE user_id = %s AND is_correct = TRUE",
                (user_id,)
            )
            correct_answers = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM user_stats WHERE user_id = %s",
                (user_id,)
            )
            total_answers = cur.fetchone()[0]

            accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0

            bot.send_message(
                message.chat.id,
                f"📊 <b>Твоя статистика</b> (уровень: "
                f"{DIFFICULTY_LEVELS[difficulty]['name']}):\n\n"
                f"📚 Слов в словаре: {total_words}\n"
                f"✅ Правильных ответов: {correct_answers}\n"
                f"❌ Всего ответов: {total_answers}\n"
                f"🎯 Точность: {accuracy:.1f}%",
                parse_mode='HTML',
                reply_markup=create_main_keyboard()
            )
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении статистики.",
                         reply_markup=create_main_keyboard())
    finally:
        conn.close()


@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def handle_stats_button(message):
    """Handle statistics button press.

    Args:
        message (telebot.types.Message): Incoming message object.

    Behavior:
        - Calls show_stats() function
    """
    show_stats(message)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Fallback handler for unrecognized text commands.

    Args:
        message (telebot.types.Message): Any text message not handled elsewhere.

    Behavior:
        - Checks if message is not a known command
        - Shows prompt to use menu buttons
        - Restores main keyboard
    """
    if message.text not in ["🎯 Начать тест", "📖 Мой словарь", "➕ Добавить слово",
                            "➖ Удалить слово", "📊 Статистика", "⚙️ Уровень сложности",
                            "❓ Помощь", "🔙 Главное меню", "🎯 Следующий вопрос"]:
        bot.send_message(message.chat.id, "Используй кнопки меню или команды.",
                         reply_markup=create_main_keyboard())


# Launching the bot
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)