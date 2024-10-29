from telebot import TeleBot, types
from datetime import datetime
import instaloader
import os
import shutil
import time
import threading
from queue import Queue

# Initialize the bot with the token
bot = TeleBot('7506752402:AAGCkbsKMzl11psl-CJrfAdGF_bmmLHKUtE')

# Track started users
started_users = []

# Admins list (default admin ID included)
admin_ids = [6235006088]
# Banned users list
banned_users = []

# Initialize Instaloader
loader = instaloader.Instaloader()

# Semaphore to limit concurrent downloads
download_semaphore = threading.Semaphore(3)
# Queue to handle download requests
download_queue = Queue()

# Command to add admin
@bot.message_handler(commands=['addadmin'])
def add_admin(message: types.Message):
    if message.from_user.id in admin_ids:
        try:
            new_admin_id = int(message.text.split()[1])
            if new_admin_id not in admin_ids:
                admin_ids.append(new_admin_id)
                bot.reply_to(message, f"✅ کاربر {new_admin_id} به ادمین‌ها اضافه شد.")
            else:
                bot.reply_to(message, "⚠️ این کاربر قبلاً ادمین بوده است.")
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ دستور اشتباه است. لطفاً آیدی عددی کاربر را وارد کنید.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")

# Command to ban user
@bot.message_handler(commands=['ban'])
def ban_user(message: types.Message):
    if message.from_user.id in admin_ids:
        try:
            user_id = int(message.text.split()[1])
            if user_id not in banned_users:
                banned_users.append(user_id)
                bot.reply_to(message, f"🚫 کاربر {user_id} بن شد.")
            else:
                bot.reply_to(message, "⚠️ این کاربر قبلاً بن شده است.")
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ دستور اشتباه است. لطفاً آیدی عددی کاربر را وارد کنید.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")

# Command to unban user
@bot.message_handler(commands=['unban'])
def unban_user(message: types.Message):
    if message.from_user.id in admin_ids:
        try:
            user_id = int(message.text.split()[1])
            if user_id in banned_users:
                banned_users.remove(user_id)
                bot.reply_to(message, f"✅ کاربر {user_id} آنبن شد.")
            else:
                bot.reply_to(message, "⚠️ این کاربر بن نیست.")
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ دستور اشتباه است. لطفاً آیدی عددی کاربر را وارد کنید.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")

# Command to broadcast message
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message: types.Message):
    if message.from_user.id in admin_ids:
        broadcast_text = message.text.split(maxsplit=1)[1]
        for user_id in started_users:
            if user_id not in banned_users:
                bot.send_message(user_id, f"📢 Announcement\n\n{broadcast_text}")
        bot.reply_to(message, "✅ پیام همگانی ارسال شد.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")

# Function for sending message to a specific user
@bot.message_handler(commands=['send'])
def send_message_to_user(message: types.Message):
    if message.from_user.id in admin_ids:
        try:
            user_id = int(message.text.split()[1])
            text = message.text.split(maxsplit=2)[2]
            if user_id in started_users and user_id not in banned_users:
                bot.send_message(user_id, f"📬 پیام از ادمین:\n\n{text}")
                bot.reply_to(message, f"✅ پیام به کاربر {user_id} ارسال شد.")
            else:
                bot.reply_to(message, "⚠️ کاربر موردنظر وجود ندارد یا بن شده است.")
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ دستور اشتباه است. لطفاً آیدی عددی و پیام را وارد کنید.")
    else:
        bot.reply_to(message, "⛔ شما دسترسی ادمین ندارید.")

# Command handler for /start
@bot.message_handler(commands=['start'])
def handle_start_command(message: types.Message):
    if message.from_user.id in banned_users:
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
    if message.chat.id not in started_users:
        started_users.append(message.chat.id)


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
print('🤖 Bot started and running...')
bot.infinity_polling()
