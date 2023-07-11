from django.contrib import admin
from .models import Game, GameRegister, Referee, Cases, GameLabel
from .filters import CaseLabelFilter
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
    list_display = ('trim100', 'number', 'case_type',  'game_labels')
    list_display_links = ('trim100', 'number', 'case_type', 'game_labels')
    search_fields = ('text', 'number', )
    list_filter = ('case_type',  CaseLabelFilter)
    def trim100(self, obj):
        return u"%s..." % (obj.text[:100],)

    def game_labels(self, obj):
        return ', '.join([x.type for x in obj.label.all()])

@admin.register(GameLabel)
class GameLabelAdmin(admin.ModelAdmin):
    list_display = ('id', 'type')
    list_display_links = ('id', 'type')


# admin.site.register(GameLabel)
admin.site.register(Referee)
# (Cases)
