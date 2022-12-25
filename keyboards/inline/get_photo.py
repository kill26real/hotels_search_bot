from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_photo() -> InlineKeyboardMarkup:
    photo_markup = InlineKeyboardMarkup()
    key_yes = InlineKeyboardButton(text='Да', callback_data='yes')
    key_no = InlineKeyboardButton(text='Нет', callback_data='no')
    photo_markup.add(key_yes, key_no)
    return photo_markup

def photo_amount() -> InlineKeyboardMarkup:

    photos_markup = InlineKeyboardMarkup(row_width=3)

    h_1 = InlineKeyboardButton(text='1', callback_data='1')
    h_2 = InlineKeyboardButton(text='2', callback_data='2')
    h_3 = InlineKeyboardButton(text='3', callback_data='3')
    h_4 = InlineKeyboardButton(text='4', callback_data='4')
    h_5 = InlineKeyboardButton(text='5', callback_data='5')
    h_6 = InlineKeyboardButton(text='6', callback_data='6')

    photos_markup.add(h_1, h_2, h_3)
    photos_markup.add(h_4, h_5, h_6)

    return photos_markup
