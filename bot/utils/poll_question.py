from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MSK = ZoneInfo("Europe/Moscow")

def get_training_poll_question(position: str) -> str:
    """
    Формирует вопрос динамического опроса по логике тренировки.

    position – OL, QB, WR и т.д. (для подстановки в вопрос)
    """
    now = datetime.now(MSK)
    weekday = now.weekday()  # 0 = ПН ... 6 = ВС
    hour = now.hour

    # Определяем ближайшую тренировку
    if (weekday == 6 and hour >= 18) or (weekday in [0, 1]) or (weekday == 2 and hour < 21):
        # Следующая тренировка — среда 18:00
        next_training_weekday = 2  # среда
    else:
        # Следующая тренировка — воскресенье 18:00
        next_training_weekday = 6  # воскресенье

    # Вычисляем дату ближайшей тренировки
    days_ahead = (next_training_weekday - weekday) % 7
    training_date = now + timedelta(days=days_ahead)
    training_date_str = training_date.strftime("%d.%m.%Y")

    if next_training_weekday == 2:
        return f"Тренировка в среду {training_date_str} в 20:30 {position}"
    else:
        return f"Тренировка в воскресенье {training_date_str} в 17:15 {position}"
