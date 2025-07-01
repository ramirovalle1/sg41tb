from django.contrib import admin
from moodle.models import UserAuth, EvaVirtual


class MoodleUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'city' )
    ordering = ('username',)
    search_fields = ('username',)
    raw_id_fields = ('user',)


class EvaVirtualAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_key', 'url', 'is_active')
    ordering = ('name',)
    search_fields = ('name', 'name_key', 'url',)


admin.site.register(UserAuth, MoodleUserAdmin)
admin.site.register(EvaVirtual, EvaVirtualAdmin)

