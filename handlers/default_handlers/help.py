from telebot.types import Message

from config_data.config import DEFAULT_COMMANDS, COMMANDS
from loader import bot



@bot.message_handler(commands=['help'])
def bot_help(message: Message):
    text = [f'/{command} - {desk}' for command, desk in DEFAULT_COMMANDS]
    for command, desk in COMMANDS:
        text.append(f'/{command} - {desk}')
    bot.reply_to(message, '\n'.join(text))
