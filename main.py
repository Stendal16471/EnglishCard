"""
English Learning Telegram Bot with Difficulty Levels (SQLite version)

This bot helps users learn English words with features:
- Personal dictionary
- Knowledge testing with difficulty levels
- Progress statistics

The module uses SQLite database and implements:
1. User dictionary management
2. Testing system with 3 difficulty levels
3. Statistics collection
"""

import random
import sqlite3
import os
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'learning_english.db')

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
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

def get_db_connection():
    """Return a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize database tables and populate with common words if empty."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            difficulty TEXT DEFAULT 'medium'
        )
    ''')

    # Common words table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS common_words (
            word_id INTEGER PRIMARY KEY AUTOINCREMENT,
            english_word TEXT NOT NULL,
            russian_translation TEXT NOT NULL,
            word_type TEXT
        )
    ''')

    # User words table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_words (
            user_word_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            english_word TEXT NOT NULL,
            russian_translation TEXT NOT NULL,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Statistics table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            word_id INTEGER,
            is_correct INTEGER,
            attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Populate common words if empty
    cur.execute("SELECT COUNT(*) FROM common_words")
    if cur.fetchone()[0] == 0:
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
        cur.executemany(
            "INSERT INTO common_words (english_word, russian_translation, word_type) VALUES (?, ?, ?)",
            common_words
        )
        print("Added base word set")

    conn.commit()
    conn.close()
    print("Database initialized")

# Initialize database on startup
init_db()

def create_main_keyboard():
    """Create the main menu keyboard."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🎯 Начать тест"))
    markup.row(types.KeyboardButton("📖 Мой словарь"))
    markup.row(types.KeyboardButton("➕ Добавить слово"), types.KeyboardButton("➖ Удалить слово"))
    markup.row(types.KeyboardButton("📊 Статистика"), types.KeyboardButton("⚙️ Уровень сложности"))
    markup.row(types.KeyboardButton("❓ Помощь"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user.id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user_id, username, first_name, last_name, difficulty) VALUES (?, ?, ?, ?, ?)",
            (user.id, user.username, user.first_name, user.last_name, 'medium')
        )
        conn.commit()
        print(f"New user added: {user.id} {user.username}")

    conn.close()

    welcome_message = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Меня зовут Коннор. Помогу тебе с изучением английских слов.\n\n"
        "🎯 Начать тест\n"
        "⚙️ Уровень сложности\n"
        "📖 Мой словарь\n"
        "➕ Добавить слово\n"
        "📊 Статистика\n"
        "❓ Помощь"
    )
    bot.send_message(message.chat.id, welcome_message, reply_markup=create_main_keyboard())

@bot.message_handler(commands=['help'])
def show_help(message):
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
    bot.send_message(message.chat.id, help_text, parse_mode='HTML', reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def handle_help_button(message):
    show_help(message)

@bot.message_handler(func=lambda message: message.text == "⚙️ Уровень сложности")
def show_difficulty_menu(message):
    user_id = message.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT difficulty FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    current_level = row[0] if row else 'medium'
    conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for level in DIFFICULTY_LEVELS.values():
        prefix = "✓ " if level['name'] == DIFFICULTY_LEVELS[current_level]['name'] else ""
        markup.add(types.KeyboardButton(f"{prefix}{level['name']}"))
    markup.add(types.KeyboardButton("🔙 Главное меню"))

    bot.send_message(
        message.chat.id,
        "📊 <b>Выберите уровень сложности тестов:</b>\n\n" +
        "\n".join([f"{level['name']} - {level['description']}" for level in DIFFICULTY_LEVELS.values()]),
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: any(message.text.replace("✓ ", "") == level['name'] for level in DIFFICULTY_LEVELS.values()))
def set_difficulty_level(message):
    user_id = message.from_user.id
    difficulty_text = message.text.replace("✓ ", "")
    difficulty = next(key for key, level in DIFFICULTY_LEVELS.items() if level['name'] == difficulty_text)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET difficulty = ? WHERE user_id = ?", (difficulty, user_id))
    conn.commit()
    conn.close()

    bot.send_message(
        message.chat.id,
        f"✅ Уровень сложности установлен: {DIFFICULTY_LEVELS[difficulty]['name']}\n{DIFFICULTY_LEVELS[difficulty]['description']}",
        reply_markup=create_main_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "🎯 Начать тест")
def start_quiz(message):
    user_id = message.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT difficulty FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    difficulty = row[0] if row and row[0] else 'medium'
    words_limit = DIFFICULTY_LEVELS[difficulty]['words_limit']

    if difficulty == 'easy':
        cur.execute("""
            SELECT 'common' as source, word_id, english_word, russian_translation FROM common_words 
            WHERE word_type IN ('цвет', 'местоимение', 'число')
            ORDER BY RANDOM() LIMIT ?
        """, (words_limit,))
    elif difficulty == 'medium':
        cur.execute("""
            SELECT 'common' as source, word_id, english_word, russian_translation FROM common_words 
            WHERE word_type != 'сложное' OR word_type IS NULL
            ORDER BY RANDOM() LIMIT ?
        """, (words_limit,))
    else:
        cur.execute("""
            SELECT 'common' as source, word_id, english_word, russian_translation FROM common_words 
            ORDER BY RANDOM() LIMIT ?
        """, (words_limit,))

    words = cur.fetchall()

    # Add user words
    cur.execute("""
        SELECT 'user' as source, user_word_id, english_word, russian_translation FROM user_words 
        WHERE user_id = ? AND is_active = 1
        ORDER BY RANDOM() LIMIT ?
    """, (user_id, words_limit))
    user_words = cur.fetchall()
    words.extend(user_words)

    if not words:
        bot.send_message(message.chat.id, "Нет слов для тестирования. Добавь слова через меню.", reply_markup=create_main_keyboard())
        conn.close()
        return

    random.shuffle(words)
    word = words[0]
    source_type, word_id, english_word, correct_translation = word

    # Get wrong answers
    cur.execute("""
        SELECT russian_translation FROM common_words WHERE russian_translation != ?
        ORDER BY RANDOM() LIMIT 3
    """, (correct_translation,))
    wrong_answers = [row[0] for row in cur.fetchall()]
    conn.close()

    options = [correct_translation] + wrong_answers
    random.shuffle(options)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for option in options:
        markup.add(types.KeyboardButton(option))
    markup.add(types.KeyboardButton("🔙 Главное меню"))

    msg = bot.send_message(
        message.chat.id,
        f"Уровень: {DIFFICULTY_LEVELS[difficulty]['name']}\nКак переводится слово: <b>{english_word}</b>?",
        parse_mode='HTML',
        reply_markup=markup
    )

    bot.register_next_step_handler(msg, lambda m: check_quiz_answer(m, correct_translation, source_type, word_id))

def check_quiz_answer(message, correct_answer, source_type, word_id):
    user_answer = message.text
    user_id = message.from_user.id

    if user_answer == "🔙 Главное меню":
        bot.send_message(message.chat.id, "Выбери действие:", reply_markup=create_main_keyboard())
        return

    is_correct = user_answer == correct_answer
    response = "✅ Правильно! Молодец :)" if is_correct else "❌ Неправильно :( Попробуй еще раз."

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_stats (user_id, word_id, is_correct) VALUES (?, ?, ?)",
        (user_id, word_id if source_type == 'common' else -word_id, 1 if is_correct else 0)
    )
    conn.commit()
    conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🎯 Следующий вопрос"))
    markup.add(types.KeyboardButton("🔙 Главное меню"))
    bot.send_message(message.chat.id, response, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🎯 Следующий вопрос")
def handle_next_question(message):
    start_quiz(message)

@bot.message_handler(func=lambda message: message.text in ["🔙 Главное меню", "Главное меню"])
def handle_back_button(message):
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "📖 Мой словарь")
def show_my_words(message):
    user_id = message.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT english_word, russian_translation FROM user_words WHERE user_id = ? AND is_active = 1 ORDER BY english_word", (user_id,))
    words = cur.fetchall()
    conn.close()

    if not words:
        bot.send_message(message.chat.id, "Твой словарь пуст. Добавь слова через меню.", reply_markup=create_main_keyboard())
        return

    word_list = "📚 <b>Твой словарь:</b>\n" + "\n".join([f"• {en} - {ru}" for en, ru in words])
    bot.send_message(message.chat.id, word_list, parse_mode='HTML', reply_markup=create_main_keyboard())
    bot.send_message(message.chat.id, f"Всего слов: {len(words)}", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "➕ Добавить слово")
def add_word(message):
    msg = bot.send_message(
        message.chat.id,
        "Введи новое слово в формате:\nанглийское_слово - русский_перевод\n\nНапример: apple - яблоко",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_new_word)

def process_new_word(message):
    user_id = message.from_user.id
    text = message.text.strip()

    try:
        english, russian = [part.strip() for part in text.split('-', 1)]
        if not english or not russian:
            raise ValueError

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_words (user_id, english_word, russian_translation) VALUES (?, ?, ?)",
            (user_id, english.lower(), russian.lower())
        )
        cur.execute("SELECT COUNT(*) FROM user_words WHERE user_id = ? AND is_active = 1", (user_id,))
        word_count = cur.fetchone()[0]
        conn.commit()
        conn.close()

        bot.send_message(
            message.chat.id,
            f"✅ Слово '{english}' добавлено в твой словарь.\n📚 Теперь ты изучаешь {word_count} слов.",
            reply_markup=create_main_keyboard()
        )
    except Exception:
        bot.send_message(
            message.chat.id,
            "Неправильный формат. Введи слово в формате: английское - русский",
            reply_markup=create_main_keyboard()
        )

@bot.message_handler(func=lambda message: message.text == "➖ Удалить слово")
def remove_word(message):
    user_id = message.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_word_id, english_word FROM user_words WHERE user_id = ? AND is_active = 1", (user_id,))
    words = cur.fetchall()
    conn.close()

    if not words:
        bot.send_message(message.chat.id, "У тебя нет слов для удаления.", reply_markup=create_main_keyboard())
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    word_dict = {}
    for word_id, english_word in words:
        markup.add(types.KeyboardButton(english_word))
        word_dict[english_word] = word_id
    markup.add(types.KeyboardButton("🔙 Главное меню"))

    msg = bot.send_message(message.chat.id, "Выбери слово для удаления:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: confirm_remove(m, word_dict))

def confirm_remove(message, word_dict):
    user_id = message.from_user.id
    word_to_remove = message.text

    if word_to_remove == "🔙 Главное меню":
        bot.send_message(message.chat.id, "Выбери действие:", reply_markup=create_main_keyboard())
        return

    if word_to_remove not in word_dict:
        bot.send_message(message.chat.id, "Слово не найдено.", reply_markup=create_main_keyboard())
        return

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE user_words SET is_active = 0 WHERE user_word_id = ? AND user_id = ?", (word_dict[word_to_remove], user_id))
    cur.execute("SELECT COUNT(*) FROM user_words WHERE user_id = ? AND is_active = 1", (user_id,))
    word_count = cur.fetchone()[0]
    conn.commit()
    conn.close()

    bot.send_message(
        message.chat.id,
        f"🗑️ Слово '{word_to_remove}' удалено.\n📚 Теперь ты изучаешь {word_count} слов.",
        reply_markup=create_main_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def show_stats(message):
    user_id = message.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT difficulty FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    difficulty = row[0] if row else 'medium'

    cur.execute("SELECT COUNT(*) FROM user_words WHERE user_id = ? AND is_active = 1", (user_id,))
    total_words = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM user_stats WHERE user_id = ? AND is_correct = 1", (user_id,))
    correct_answers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM user_stats WHERE user_id = ?", (user_id,))
    total_answers = cur.fetchone()[0]
    conn.close()

    accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0

    bot.send_message(
        message.chat.id,
        f"📊 <b>Твоя статистика</b> (уровень: {DIFFICULTY_LEVELS[difficulty]['name']}):\n\n"
        f"📚 Слов в словаре: {total_words}\n"
        f"✅ Правильных ответов: {correct_answers}\n"
        f"❌ Всего ответов: {total_answers}\n"
        f"🎯 Точность: {accuracy:.1f}%",
        parse_mode='HTML',
        reply_markup=create_main_keyboard()
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text not in ["🎯 Начать тест", "📖 Мой словарь", "➕ Добавить слово", "➖ Удалить слово", "📊 Статистика", "⚙️ Уровень сложности", "❓ Помощь", "🔙 Главное меню", "🎯 Следующий вопрос"]:
        bot.send_message(message.chat.id, "Используй кнопки меню или команды.", reply_markup=create_main_keyboard())

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
