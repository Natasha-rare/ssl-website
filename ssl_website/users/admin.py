from django.contrib import admin

# Register your models here.
from .models import User, EmailVerification

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'telegram', 'role', 'is_accepted', 'hse_pass', 'is_verified_email')
    fieldsets = (
        ('Личная информация', {
            'fields': (('first_name', 'last_name'), 'father_name', 'email', 'telegram', 'image', 'hse_pass','tg_bot_id', 'is_verified_email')
        }),
        ('Роль в клубе', {
            'fields': ('role', 'is_accepted')
        })
    )
    search_fields = ['role', 'telegram', 'email', 'hse_pass', 'is_accepted']
    list_filter = ['role', 'hse_pass', 'is_accepted', 'telegram', 'email']
    list_display_links = ('first_name', 'last_name', 'email', 'telegram', 'role', 'is_accepted', 'hse_pass')
    list_per_page = 25

admin.site.register(EmailVerification)