from django.contrib import admin
from .models import Game, GameRegister, Referee, Cases
# Register your models here.
@admin.register(GameRegister)
class GameRegisterAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'player', 'attendance')
    list_display_links = ('id', 'date', 'player', 'attendance')
    list_filter = ('date',  'attendance')

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'table_number', 'case_number', 'game_type')
    list_display_links = ('id', 'date', 'table_number', 'case_number', 'game_type')
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        print(db_field.name)
        if 'player' in db_field.name:
            # print(obj.player)
            formfield.label_from_instance = lambda obj: f'{obj.player.email}'
        return formfield

@admin.register(Cases)
class CasesAdmin(admin.ModelAdmin):
    list_display = ('text', 'number', 'case_type')
    list_display_links = ('text', 'number', 'case_type')
    search_fields = ('text', 'number', )
    list_filter = ('case_type',)

# admin.site.register(Game)
admin.site.register(Referee)
# (Cases)
