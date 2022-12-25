from datetime import date
import datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP


my_translation_months = ['Янв', 'Фев', 'Март', 'Апр', 'Май', 'Июнь', 'Июль', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
my_translation_days_of_week = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']


class MyTranslationCalendar(DetailedTelegramCalendar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.days_of_week['yourtransl'] = my_translation_days_of_week
        self.months['yourtransl'] = my_translation_months
        self.locale = 'ru'

def calendar():

    calendar_2, step = MyTranslationCalendar(min_date=date.today(), max_date=datetime.date(2024, 12, 31)).build()

    return calendar_2

def calendar_1(res_date):
    dates = str(res_date).split('-')

    calendar_3, step_1 = MyTranslationCalendar(min_date=datetime.date(int(dates[0]), int(dates[1]), int(dates[2])),
                                                  max_date=datetime.date(2024, 12, 31)).build()

    return calendar_3
