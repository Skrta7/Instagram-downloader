from telebot import TeleBot, types
import json
import os

# Initialize the bot with the token
bot = TeleBot('7506752402:AAGCkbsKMzl11psl-CJrfAdGF_bmmLHKUtE')

# Global variable to track started users
started = []

# Command handler for /start
@bot.message_handler(commands=['start'])
def welcome(message: types.Message):
    name = message.from_user.first_name
    text = f'سلام {name} عزیز! لطفاً لینک پست اینستاگرامی که می‌خواهید را ارسال کنید تا ویدیو را برای شما ارسال کنم.'
    button_about = types.InlineKeyboardButton("About Us", callback_data="about")
    button_help = types.InlineKeyboardButton("Help", callback_data="help")
    markup = types.InlineKeyboardMarkup()
    markup.add(button_about, button_help)
    bot.send_message(message.chat.id, text, reply_markup=markup)
    if message.chat.id not in started:
        started.append(message.chat.id)

# Handler for incoming messages
@bot.message_handler(func=lambda m: True)
def send_video(message: types.Message):
    if message.text.startswith('https://www.instagram.com'):
        link = message.text[12:]
        link = f"www.dd{link}"
        channel = types.InlineKeyboardButton('کانال کتیستا', url='https://t.me/CatIstaChannel')
        report = types.InlineKeyboardButton('گزارش باگ', callback_data='report')
        btn = types.InlineKeyboardMarkup(row_width=2).add(channel, report)
        bot.send_message(message.chat.id, f'<a href="{link}">⁪</a>', parse_mode='HTML', reply_markup=btn)
    else:
        bot.reply_to(message, 'لطفاً یک لینک معتبر اینستاگرامی ارسال کنید.')

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def get_call(call: types.CallbackQuery):
    if call.data == 'report':
        bot.answer_callback_query(call.id, 'شما در حال گزارش باگ هستید.')
        report_message = bot.send_message(call.message.chat.id, 'لطفاً دلیل گزارش خود را بنویسید:')
        bot.register_next_step_handler(report_message, get_report)
    elif call.data == "about":
        bot.send_message(call.id, 'This is About Page')
    elif call.data == "help":
        bot.send_message(call.id, 'this is help')

# Function to handle report messages
def get_report(message: types.Message):
    text = message.text
    bot.send_message(6235006088, f"گزارش جدید:\n{text}\n\nChat ID: {message.chat.id}\n\nUser ID: {message.from_user.username}")
    bot.reply_to(message, 'گزارش شما با موفقیت ثبت شد. ممنون از شما!')

# Start the bot
print('Bot started')
bot.infinity_polling()
