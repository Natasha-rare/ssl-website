from django.db import models
from django.contrib.auth import get_user_model
import datetime
from django.utils.translation import gettext_lazy as _

User = get_user_model()
# Create your models here.
GAME_TYPES = (
    ("CONFLICT", _("Conflict")),
    ("DISCUSSION", _("Discussion"))
)
def get_closest_game():
    today = datetime.date.today()
    closest_sat = today + datetime.timedelta(6 -(today.weekday() + 1) % 7)
    return closest_sat

class Attendance(models.TextChoices):
    PLAYED = "Сыграл"
    SKIP = "Не пришел"
    LATE = "Опоздал"

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

class Game(models.Model):
    date = models.DateField(null=False, default=get_closest_game())
    case_number = models.IntegerField("Номер кейса", default=0, null=False)
    player_1 = models.ForeignKey(GameRegister, related_name="player_1", on_delete=models.CASCADE)
    player_1_score = models.IntegerField("Счет 1 игрока", default=0, null=False)
    player_2 = models.ForeignKey(GameRegister, related_name="player_2", on_delete=models.CASCADE)
    player_2_score = models.IntegerField("Счет 2 игрока", default=0, null=False)
    table_number = models.IntegerField("Стол", default=0, null=False)
    game_type = models.CharField(
        max_length=15,
        choices=GAME_TYPES,
        default="CONFLICT",
        verbose_name="Тип игры",
    )


class Referee(models.Model):
    referee = models.ForeignKey(to=User, on_delete=models.CASCADE)
    game_info = models.ManyToManyField(Game)