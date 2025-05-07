from django.contrib import admin
from .models import Feed


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ('name', 'rss_url', 'is_active', 'last_fetched_at', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'rss_url')
