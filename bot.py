from telebot import TeleBot, types
from datetime import datetime
import instaloader
import os
import shutil
import time
import threading
from queue import Queue
import sqlite3

# Initialize the bot with the token
bot = TeleBot('toekn')

# Initialize Instaloader
loader = instaloader.Instaloader()

# Semaphore to limit concurrent downloads
download_semaphore = threading.Semaphore(3)
# Queue to handle download requests
download_queue = Queue()

# Create or connect to the database
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():

    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS started_users (
            id INTEGER PRIMARY KEY
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            id INTEGER PRIMARY KEY
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT,
            target_id INTEGER,
            timestamp TEXT
        )
    ''')
    conn.commit()

def log_action(admin_id, action, target_id=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('INSERT INTO admin_logs (admin_id, action, target_id, timestamp) VALUES (?, ?, ?, ?)', 
                (admin_id, action, target_id, timestamp))
    conn.commit()

def add_user(user_id, username):
    cursor.execute('INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)', (user_id, username)) 
    conn.commit()

def add_admin(admin_id, by_admin):
    cursor.execute('INSERT OR IGNORE INTO admins (id) VALUES (?)', (admin_id,))
    log_action(by_admin, "Add Admin", admin_id)
    conn.commit()

def remove_admin(admin_id, by_admin):
    # Remove from the admins table and log the action
    cursor.execute('DELETE FROM admins WHERE id = ?', (admin_id,))
    log_action(by_admin, "Remove Admin", admin_id)
    conn.commit()

# Command to display the list of admins
@bot.message_handler(commands=['admins'])
def list_admins(message: types.Message):
    # Check if the user is an admin by querying the database
    cursor.execute("SELECT id FROM admins WHERE id = ?", (message.from_user.id,))
    admin_check = cursor.fetchone()

    if admin_check:
        # Query the database to retrieve the list of admins
        cursor.execute("SELECT id FROM admins")
        admins = cursor.fetchall()
        
        if admins:
            admins_list = "\n".join([str(admin[0]) for admin in admins])
            bot.reply_to(message, f"👥 لیست ادمین‌ها:\n{admins_list}")
        else:
            bot.reply_to(message, "⚠️ لیست ادمین‌ها خالی است.")
        
        # Log the action of viewing the admin list
        log_action(message.from_user.id, "View Admin List")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")


# Command to remove an admin
@bot.message_handler(commands=['removeadmin'])
def remove_admin_command(message: types.Message):
    # Check if the user is an admin by querying the database
    cursor.execute("SELECT id FROM admins WHERE id = ?", (message.from_user.id,))
    admin_check = cursor.fetchone()

    if admin_check:
        try:
            remove_admin_id = int(message.text.split()[1])
            # Check if the admin to be removed exists in the database
            cursor.execute("SELECT id FROM admins WHERE id = ?", (remove_admin_id,))
            admin_exists = cursor.fetchone()

            if admin_exists:
                # Prevent removing the last admin or oneself
                if remove_admin_id == message.from_user.id:
                    bot.reply_to(message, "⚠️ نمی‌توانید خودتان را از ادمین‌ها حذف کنید.")
                else:
                    # Remove from database
                    remove_admin(remove_admin_id, message.from_user.id)
                    bot.reply_to(message, f"❌ کاربر {remove_admin_id} از لیست ادمین‌ها حذف شد.")
            else:
                bot.reply_to(message, "⚠️ این کاربر در لیست ادمین‌ها نیست.")
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ دستور اشتباه است. لطفاً آیدی عددی کاربر را وارد کنید.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")


# Command to add admin
@bot.message_handler(commands=['addadmin'])
def add_admin_command(message: types.Message):
    # Check if the user is an admin by querying the database
    cursor.execute("SELECT id FROM admins WHERE id = ?", (message.from_user.id,))
    admin_check = cursor.fetchone()

    if admin_check:
        try:
            new_admin_id = int(message.text.split()[1])

            # Check if the new admin already exists in the database
            cursor.execute("SELECT id FROM admins WHERE id = ?", (new_admin_id,))
            existing_admin = cursor.fetchone()

            if existing_admin is None:  # If the user is not already an admin
                add_admin(new_admin_id, message.from_user.id)  # Register in database
                bot.reply_to(message, f"✅ کاربر {new_admin_id} به ادمین‌ها اضافه شد.")
            else:
                bot.reply_to(message, "⚠️ این کاربر قبلاً ادمین بوده است.")
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ دستور اشتباه است. لطفاً آیدی عددی کاربر را وارد کنید.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")


@bot.message_handler(commands=['adminlogs'])
def show_admin_logs(message: types.Message):
    if message.from_user.id == 6235006088:
        cursor.execute('SELECT * FROM admin_logs ORDER BY timestamp DESC LIMIT 10')
        logs = cursor.fetchall()
        log_text = "\n".join([f"{log[3]} - Admin {log[1]}: {log[2]} (Target: {log[2]})" for log in logs])
        bot.reply_to(message, f"📜 لاگ‌های اخیر ادمین:\n\n{log_text}")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")


# Command to ban user
@bot.message_handler(commands=['ban'])
def ban_user(message: types.Message):
    # Check if the user is an admin by querying the database
    cursor.execute("SELECT id FROM admins WHERE id = ?", (message.from_user.id,))
    admin_check = cursor.fetchone()

    if admin_check:
        try:
            user_id = int(message.text.split()[1])
            
            # Check if the user is already banned
            cursor.execute("SELECT id FROM banned_users WHERE id = ?", (user_id,))
            if cursor.fetchone():
                bot.reply_to(message, "⚠️ این کاربر قبلاً بن شده است.")
            else:
                # Add user to banned_users table in the database
                cursor.execute("INSERT INTO banned_users (id) VALUES (?)", (user_id,))
                conn.commit()
                bot.reply_to(message, f"🚫 کاربر {user_id} بن شد.")
                
                # Log the ban action
                log_action(message.from_user.id, f"Banned user {user_id}")
                
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ دستور اشتباه است. لطفاً آیدی عددی کاربر را وارد کنید.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")


# Command to unban user
@bot.message_handler(commands=['unban'])
def unban_user(message: types.Message):
    # Check if the user is an admin by querying the database
    cursor.execute("SELECT id FROM admins WHERE id = ?", (message.from_user.id,))
    admin_check = cursor.fetchone()

    if admin_check:
        try:
            user_id = int(message.text.split()[1])

            # Check if the user is banned
            cursor.execute("SELECT id FROM banned_users WHERE id = ?", (user_id,))
            if cursor.fetchone():
                # Remove user from banned_users table in the database
                cursor.execute("DELETE FROM banned_users WHERE id = ?", (user_id,))
                conn.commit()
                bot.reply_to(message, f"✅ کاربر {user_id} آنبن شد.")

                # Log the unban action
                log_action(message.from_user.id, f"Unbanned user {user_id}")
            else:
                bot.reply_to(message, "⚠️ این کاربر بن نیست.")
                
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ دستور اشتباه است. لطفاً آیدی عددی کاربر را وارد کنید.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")


# Command to broadcast message
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message: types.Message):
    # Check if the user is an admin by querying the database
    cursor.execute("SELECT id FROM admins WHERE id = ?", (message.from_user.id,))
    admin_check = cursor.fetchone()

    if admin_check:
        try:
            broadcast_text = message.text.split(maxsplit=1)[1]
            sent_count = 0  # Counter for successfully sent messages

            # Query to get all started users who are not banned
            cursor.execute("SELECT id FROM started_users WHERE id NOT IN (SELECT id FROM banned_users)")
            active_users = cursor.fetchall()

            for user in active_users:
                user_id = user[0]
                bot.send_message(user_id, f"📢 Announcement\n\n{broadcast_text}")
                sent_count += 1

            bot.reply_to(message, f"✅ پیام همگانی به {sent_count} کاربر ارسال شد.")

            # Log the broadcast action
            log_action(message.from_user.id, f"Broadcasted message: {broadcast_text[:50]}... to {sent_count} users")
        
        except IndexError:
            bot.reply_to(message, "⚠️ دستور اشتباه است. لطفاً متن پیام را وارد کنید.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")



# Function for sending message to a specific user
@bot.message_handler(commands=['send'])
def send_message_to_user(message: types.Message):
    # Check if the user is an admin by querying the database
    cursor.execute("SELECT id FROM admins WHERE id = ?", (message.from_user.id,))
    admin_check = cursor.fetchone()

    if admin_check:
        try:
            user_id = int(message.text.split()[1])
            text = message.text.split(maxsplit=2)[2]

            # Check if user exists and is not banned
            cursor.execute("SELECT id FROM started_users WHERE id = ? AND id NOT IN (SELECT id FROM banned_users)", (user_id,))
            user_check = cursor.fetchone()

            if user_check:
                bot.send_message(user_id, f"📬 پیام از ادمین:\n\n{text}")
                bot.reply_to(message, f"✅ پیام به کاربر {user_id} ارسال شد.")

                # Log the send action
                log_action(message.from_user.id, f"Sent message to user {user_id}: {text[:50]}...")
            else:
                bot.reply_to(message, "⚠️ کاربر موردنظر وجود ندارد یا بن شده است.")
        except IndexError:
            bot.reply_to(message, "⚠️ دستور اشتباه است. لطفاً آیدی عددی و پیام را وارد کنید.")
        except ValueError:
            bot.reply_to(message, "⚠️ آیدی کاربر باید عددی باشد.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")

# Command handler for /start
@bot.message_handler(commands=['start'])
def handle_start_command(message: types.Message):
    # Check if the user is banned
    cursor.execute("SELECT id FROM banned_users WHERE id = ?", (message.from_user.id,))
    if cursor.fetchone():
        bot.reply_to(message, "⛔ شما دسترسی استفاده از این ربات را ندارید.")
        return

    user_name = message.from_user.first_name
    welcome_text = f"سلام {user_name} عزیز! 👋\n" \
                   f"لطفاً لینک پست اینستاگرامی که می‌خواهید را ارسال کنید تا ویدیو را برای شما بفرستم. 📲"

    # Inline buttons
    button_about = types.InlineKeyboardButton("درباره ما 🧑‍💼", callback_data="about")
    button_help = types.InlineKeyboardButton("راهنما 🆘", callback_data="help")
    markup = types.InlineKeyboardMarkup().add(button_about, button_help)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

    # Add user to started list if not already there
    cursor.execute("SELECT id FROM started_users WHERE id = ?", (message.from_user.id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO started_users (id) VALUES (?)", (message.from_user.id,))
        conn.commit()

        # Log the user start action
        log_action(message.from_user.id, "User started the bot.")




# Function to download the Instagram reel and handle response
def download_instagram_reel(url, unique_folder):
    try:
        # Extract shortcode from URL
        shortcode = url.split("/")[-2]
        
        # Download the post into a unique folder
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=unique_folder)
        
        # Find the video file and description file
        video_file = None
        description_file = None
        
        for filename in os.listdir(unique_folder):
            if filename.endswith(".mp4"):
                video_file = os.path.join(unique_folder, filename)
            elif filename.endswith(".txt"):
                description_file = os.path.join(unique_folder, filename)
        
        # Read the description if available
        description = ""
        if description_file:
            with open(description_file, 'r', encoding='utf-8') as f:
                description = f.read()
        
        return video_file, description
    except Exception as e:
        print(f"Error downloading reel: {e}")
        return None, None

# Handle messages for Instagram links
@bot.message_handler(func=lambda message: True)
def handle_incoming_messages(message: types.Message):
    if message.text.startswith('https://www.instagram.com'):
        reel_url = message.text
        bot.send_message(message.chat.id, "⬇️ در حال دانلود ویدیو... لطفاً صبر کنید.")
        
        # Unique folder for each user's request (based on chat ID and timestamp)
        unique_folder = f"downloads{message.chat.id}_{int(time.time())}"
        os.makedirs(unique_folder, exist_ok=True)
        
        # Download the video and description
        video_path, description = download_instagram_reel(reel_url, unique_folder)
        
        if video_path and os.path.exists(video_path):
            # Send the video file
            with open(video_path, 'rb') as video:
                bot.send_video(message.chat.id, video)
            
            # Send the description if available
            if description:
                bot.send_message(message.chat.id, f"📝 توضیحات:\n\n{description}")
            
            # Add "ارسال گزارش" button
            report_button = types.InlineKeyboardButton("ارسال گزارش 🐞", callback_data="report")
            markup = types.InlineKeyboardMarkup().add(report_button)
            bot.send_message(message.chat.id, "آیا می‌خواهید گزارشی ارسال کنید؟", reply_markup=markup)
        
        else:
            bot.reply_to(message, '❌ دانلود ویدیو با خطا مواجه شد. لطفاً لینک را بررسی کنید یا بعداً دوباره امتحان کنید.')
        
        # Clean up: Remove the unique folder after sending files
        shutil.rmtree(unique_folder)
    else:
        bot.reply_to(message, '🚫 لطفاً یک لینک معتبر اینستاگرامی ارسال کنید.')


# Handle callback queries
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_queries(call: types.CallbackQuery):
    if call.data == 'report':
        bot.answer_callback_query(call.id, 'در حال گزارش باگ... 🐞')
        prompt_text = "لطفاً دلیل گزارش خود را بنویسید:"
        report_message = bot.send_message(call.message.chat.id, prompt_text)
        bot.register_next_step_handler(report_message, process_bug_report)
    elif call.data == "about":
        about_text = "این یک ربات برای دریافت ویدیوهای اینستاگرام است! 🧐\nما اینجا هستیم تا کمک کنیم."
        bot.send_message(call.message.chat.id, about_text)
    elif call.data == "help":
        help_text = "برای استفاده از ربات، کافیست لینک پست اینستاگرام خود را ارسال کنید. 📩"
        bot.send_message(call.message.chat.id, help_text)

# Process bug report messages
def process_bug_report(message: types.Message):
    report_content = message.text
    admin_chat_id = -1002255904289    # Replace with your channel chat ID
    report_message = f"گزارش جدید دریافت شد! ⚠️\n\n📝 گزارش: {report_content}\n👤 کاربر: {message.from_user.username}\n🆔 چت آیدی: {message.chat.id}\n📅 تاریخ: {datetime.now()}"
    # Send the report to admin and confirm with the user
    bot.send_message(admin_chat_id, report_message)
    bot.reply_to(message, 'گزارش شما با موفقیت ثبت شد! 🙏 ممنون از همکاری شما!')

# Start the bot
init_db()
print('🤖 Bot started and running...')
bot.infinity_polling()