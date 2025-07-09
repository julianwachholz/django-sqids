from django.contrib import admin

from .models import TestModelWithDifferentConfig


@admin.register(TestModelWithDifferentConfig)
class TestModelAdmin(admin.ModelAdmin):
    list_display = ("sqid",)
    list_display_links = ()
    search_fields = ("sqid__exact",)
