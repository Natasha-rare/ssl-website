from django.contrib import admin

class CaseLabelFilter(admin.SimpleListFilter):
    title = "Категория"
    parameter_name = 'label'
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
