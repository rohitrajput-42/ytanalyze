from django.db import models

class Post(models.Model):
    name = models.TextField()
    category = models.CharField(max_length = 150000, null = True, blank = True)
    image = models.ImageField(upload_to = "posts/")
    content = models.TextField()
    created_ts = models.DateTimeField(auto_now_add = True)
    updated_ts = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.name