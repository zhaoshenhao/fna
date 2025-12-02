from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import NewsArticles

# Register your models here.
#@admin.site.register(NewsArticles)
@admin.register(NewsArticles)
class NewsArticlesAdmin(ModelAdmin):
    list_display = ['id', 'source_name', 'cn_title', 'publish_date', 'author', 'created_at']
    list_filter = ['source_name', 'publish_date', 'author']
    search_fields = ['cn_title', 'original_content', 'translated_content', 'result']
    ordering = ['-id', 'source_name', 'cn_title', 'publish_date', 'author']
    fields = ['publish_date', 'cn_title', 'translated_content', 'result', 'author', 'source_name',
              'title', 'original_content', 'source_url', 'crawl_date', 'created_at', 'translator', 'analyzer',]
    conditional_fields = {}
