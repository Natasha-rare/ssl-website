import datetime

from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.db import models
from multiselectfield import MultiSelectField

User = get_user_model()
# Тип игр
class GameTypes(models.TextChoices):
    CONFLICT = "Конфликт"
    DISCUSSION = "Переговоры"

# Метки для игры, описывающие тип ситуации
class GameLabels(models.TextChoices):
    FAMILY = "Бытовые"
    JOB = 'Корпоративные'
    BUSINESS = 'Бизнес'
    DEFAULT = 'Другое'

# посещаемость игрока – отметка пришел/опоздал/пропустил игру
class Attendance(models.TextChoices):
    PLAYED = "Сыграл"
    SKIP = "Не пришел"
    LATE = "Опоздал"

def get_closest_game():
    today = datetime.date.today()
    closest_sat = today + datetime.timedelta(6 -(today.weekday() + 1) % 7)
    return closest_sat

'''
Модель для регистрации игрока на игру
Хранит в себе данные об игре
Отображается в лк пользователя
'''
class GameRegister(models.Model):
    date = models.DateField(null=False, default=get_closest_game())
    player = models.ForeignKey(to=User, on_delete=models.CASCADE, to_field="id")
    conflict_score = models.IntegerField("Счет конфликты", default=0, null=False)
    discuss_score = models.IntegerField("Счет переговоры", default=0, null=False)
    begin_time = models.TimeField(default=datetime.time(16, 30))
    finish_time = models.TimeField(default=datetime.time(21))
    attendance = models.CharField(
        max_length=30,
        choices=Attendance.choices,
        default=Attendance.PLAYED,
        verbose_name="Посещаемость",
    )


'''
Модель для создании игры
Хранит в данные об игроках (связь с таблицей case) и конкретном кейсе (связь с таблицей Cases)
Отображается в сетке
(В дальнейшем будет использована для просмотра во вкладке "прошедшие игры")
'''
class Game(models.Model):
    date = models.DateField(null=False, default=get_closest_game())
    case_number = models.IntegerField("Номер кейса", default=0, null=False)  # сделать связь с моделью Cases – ?
    player_1 = models.ForeignKey(GameRegister, related_name="player_1", on_delete=models.CASCADE)
    player_1_score = models.IntegerField("Счет 1 игрока", default=0, null=False)
    player_2 = models.ForeignKey(GameRegister, related_name="player_2", on_delete=models.CASCADE)
    player_2_score = models.IntegerField("Счет 2 игрока", default=0, null=False)
    table_number = models.IntegerField("Стол", default=0, null=False)
    game_type = models.CharField(
        max_length=15,
        choices=GameTypes.choices,
        default=GameTypes.CONFLICT,
        verbose_name="Тип игры",
    )

'''
Модель для хранении информации о судье
Судья привязан к столу, дате и типу игры
Связан с пользователями через поле referee
'''
class Referee(models.Model):
    referee = models.ForeignKey(to=User, on_delete=models.CASCADE)
    # game_info = models.ManyToManyField(Game)
    date = models.DateField(null=False, default=get_closest_game())
    table_number = models.IntegerField("Стол", default=0, null=False)
    game_type = models.CharField(
        max_length=15,
        choices=GameTypes.choices,
        default=GameTypes.CONFLICT,
        verbose_name="Тип игры",
    )


'''
Модель для хранения кейсов
(тип, название и текст кейса)
'''
class Cases(models.Model):
    case_type = models.CharField(
        max_length=15,
        choices=GameTypes.choices,
        default=GameTypes.CONFLICT,
        verbose_name="Тип игры",
    )
    name = models.CharField("Название кейса", max_length=250, null=True)
    text = models.TextField("Текст кейса", null=False, validators=[MinLengthValidator(10)])
    number = models.IntegerField("Номер кейса", null=False)
    case_label = MultiSelectField(
        choices=GameLabels.choices,
        default=GameLabels.DEFAULT,
        verbose_name="Тип игры",
        max_length=100,
    )