from django.contrib import admin

# Register your models here.
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'telegram', 'role', 'is_accepted')
    fieldsets = (
        ('Личная информация', {
            'fields': (('first_name', 'last_name'), 'fathername', 'email', 'telegram', 'image', 'tg_bot_id')
        }),
        ('Роль в клубе', {
            'fields': ('role', 'is_accepted')
        })
    )
    search_fields = ['role', 'telegram', 'email']
    list_filter = ['role', 'telegram', 'email']
    list_display_links = ('first_name', 'last_name', 'email', 'telegram', 'role', 'is_accepted')
    list_per_page = 25
