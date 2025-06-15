# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class NewsArticles(models.Model):
    title = models.TextField()
    cn_title = models.TextField()
    original_content = models.TextField()
    source_url = models.TextField()
    source_name = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    publish_date = models.DateTimeField()
    crawl_date = models.DateTimeField(blank=True, null=True)
    result = models.TextField()
    translated_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'news_articles'
