from loader import bot
import sqlite3 as sq
from telebot.types import Message
import os


@bot.message_handler(commands=['history'])
def history(message: Message) -> None:
    """Функция-хэндлер. Обрабатывает команду с историей поиска и выводит историю, если она есть."""
    full_name = str(message.from_user.full_name).replace(' ', '_')
    db_path = os.path.abspath('history.db')
    with sq.connect(db_path) as base:
        cur = base.cursor()
        cur.execute(f"SELECT command,date,city,hotels_names FROM history WHERE user_name = '{full_name}' ORDER BY date DESC LIMIT 10")

        all_result = cur.fetchall()
        if all_result:
            bot.send_message(message.from_user.id, "Ваша история поиска: ")
            for i_result in all_result:
                hotels = i_result[3].replace('_', ' ').replace('!', ';\n') + ' .'
                text = f'Комманда: {i_result[0]}\n' \
                       f'Дата и время: {str(i_result[1])[:-6]}\n' \
                       f'Локация: {i_result[2]}\n' \
                       f'Имена найденных отелей:\n{hotels}'
                bot.send_message(message.from_user.id, f"{text}")
        else:
            bot.send_message(message.from_user.id, "В вашей истории поиска пока что ничего нет")
