from django.contrib import admin
from .models import Post

class PostAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "content", "created_ts"]

admin.site.register(Post, PostAdmin)