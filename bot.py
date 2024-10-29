from telebot import TeleBot, types
import json
import os

# Initialize the bot with the token
bot = TeleBot('token')

# Track started users
started_users = []

# Command handler for /start
@bot.message_handler(commands=['start'])
def handle_start_command(message: types.Message):
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

# Handle messages for Instagram links
@bot.message_handler(func=lambda message: True)
def handle_incoming_messages(message: types.Message):
    if message.text.startswith('https://www.instagram.com'):
        # Modify link for demonstration purposes
        sanitized_link = "www.dd" + message.text[12:]
        
        # Inline buttons
        button_channel = types.InlineKeyboardButton('کانال ما 📢', url='https://t.me/CodeCyborg')
        button_report = types.InlineKeyboardButton('گزارش باگ 🐞', callback_data='report')
        markup = types.InlineKeyboardMarkup(row_width=2).add(button_channel, button_report)
        
        # Send link with reply buttons
        bot.send_message(message.chat.id, f'<a href="{sanitized_link}"> ⁪ </a>', parse_mode='HTML', reply_markup=markup)
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
    admin_chat_id = 6235006088  # Replace with your admin chat ID
    report_message = f"گزارش جدید دریافت شد! ⚠️\n\n📝 گزارش: {report_content}\n👤 کاربر: {message.from_user.username}\n🆔 Chat ID: {message.chat.id}"
    
    # Send the report to admin and confirm with the user
    bot.send_message(admin_chat_id, report_message)
    bot.reply_to(message, 'گزارش شما با موفقیت ثبت شد! 🙏 ممنون از همکاری شما!')

# Start the bot
print('🤖 Bot started and running...')
bot.infinity_polling()
