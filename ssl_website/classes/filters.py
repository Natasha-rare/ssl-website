from datetime import date
from django.contrib import admin
from django.contrib.admin.utils import reverse_field_path
from django.contrib.admin import FieldListFilter, SimpleListFilter
from django.utils.translation import gettext_lazy as _
class CaseLabelFilter(admin.SimpleListFilter):
    # list_separator = '|'
    title = "Категория"
    parameter_name = 'label'
    # family, job, business, other
    def lookups(self, request, model_admin):
        return [
            ('1', 'Бытовые'),
            ('2', 'Корпоративные'),
            ('3', 'Бизнес'),
            ('4', 'Другое')
        ]

    def queryset(self, request, queryset):
        if self.value() in ['1', '2', '3', '4']:
            return queryset.filter(label__id__exact=int(self.value()))
